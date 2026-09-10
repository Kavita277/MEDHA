"""
MEDHA V2 Step 10B Correction -- Leakage-Safe Fusion Training and Candidate Selection
===================================================================================

Corrects the preliminary Step 10B experiment by:
1. Using 5-fold victim-level cross-fitting over the 700 training victims to produce
   true Out-of-Fold (OOF) specialist predictions for all 21,000 training rows.
2. Training fusion candidates (A: Inverse-OOF-MAE Weighted Average, B: Ridge Stacking,
   C: XGBoost Stacking) ONLY on the OOF training predictions.
3. Evaluating and selecting the winning fusion candidate strictly on the VALIDATION set
   (150 victims, 4,500 rows).
4. Keeping the TEST set completely UNTOUCHED (no tuning, no selection, no evaluation in Step 10B).

Usage:
    python engine/v2/train_v2_fusion_oof.py
"""

import os
import sys
import json
import pickle
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
import xgboost as xgb

# ---------------------------------------------------------------------------
# Path Setup
# ---------------------------------------------------------------------------
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V2_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(ENGINE_DIR, '..'))

for p in [ROOT_DIR, ENGINE_DIR, V2_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from engine.v2.v2_feature_policy import (
    get_all_approved_structured_dds_features,
    validate_structured_specialist_features,
    validate_text_specialist_features,
    validate_voice_specialist_features,
    validate_behaviour_specialist_features,
    V2_CORE_TEXT_DDS_FEATURES,
    V2_CORE_VOICE_DDS_FEATURES,
    V2_EXTENDED_BEHAVIOUR_DDS_FEATURES,
)
from engine.v2.v2_fusion import (
    validate_fusion_features,
    compute_weighted_average_fusion,
    V2FusionInput,
    ModalitySignal,
    V2_FUSION_APPROVED_FEATURES,
    V2_FUSION_AVAILABILITY_FLAGS,
    V2_FUSION_FORBIDDEN_FEATURES,
    _MODALITY_KEYS,
)

# ---------------------------------------------------------------------------
# Constants & Paths
# ---------------------------------------------------------------------------
SEED = 42
N_FOLDS = 5
TARGET = "DDS"
KEYS = ["Victim_ID", "Timepoint"]

SPLIT_CSV = os.path.join(ENGINE_DIR, "data", "processed", "v2_victim_split.csv")
LONG_CSV  = os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv")
PRED_DIR  = os.path.join(ENGINE_DIR, "outputs", "dds_v2")

MODEL_DIRS = [
    os.path.join(ENGINE_DIR, "models", "v2", "fusion_oof"),
    os.path.join(ROOT_DIR, "models", "v2", "fusion_oof"),
]
OUTPUT_DIRS = [
    os.path.join(ENGINE_DIR, "outputs", "dds_v2", "fusion_oof"),
    os.path.join(ROOT_DIR, "outputs", "dds_v2", "fusion_oof"),
]

for d in MODEL_DIRS + OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

# Specialist validation prediction paths
VAL_SPECIALIST_CONFIGS = {
    "structured": {
        "val_csv": os.path.join(PRED_DIR, "structured", "val_structured_dds_predictions.csv"),
        "pred_col": "Predicted_DDS_Structured_XGB",
        "out_col": "Struct_Pred",
        "actual_col": "Actual_DDS",
        "avail_col": None,
    },
    "text": {
        "val_csv": os.path.join(PRED_DIR, "text", "val_text_dds_predictions.csv"),
        "pred_col": "pred_text_dds_ridge_core5",
        "out_col": "Text_Pred",
        "actual_col": "DDS_actual",
        "avail_col": "Text_Available",
    },
    "voice": {
        "val_csv": os.path.join(PRED_DIR, "voice", "val_voice_dds_predictions.csv"),
        "pred_col": "pred_voice_dds_ridge_core5",
        "out_col": "Voice_Pred",
        "actual_col": "DDS_actual",
        "avail_col": "Voice_Available",
    },
    "behaviour": {
        "val_csv": os.path.join(PRED_DIR, "behaviour", "val_behaviour_dds_predictions.csv"),
        "pred_col": "Predicted_DDS_Ridge",
        "out_col": "Behav_Pred",
        "actual_col": "Actual_DDS",
        "avail_col": None,
    },
}

FEATURE_COLS = V2_FUSION_APPROVED_FEATURES + V2_FUSION_AVAILABILITY_FLAGS


# ===========================================================================
# Metrics Helper
# ===========================================================================
def evaluate_predictions(y_true, y_pred, split_name=""):
    """Compute standard regression metrics."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    pr, _ = pearsonr(y_true, y_pred)
    sr, _ = spearmanr(y_true, y_pred)
    return {
        "split": split_name,
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "Pearson": round(pr, 4),
        "Spearman": round(sr, 4),
        "N": int(len(y_true)),
    }


# ===========================================================================
# 1. 5-Fold Victim-Level Cross-Fitting
# ===========================================================================
def generate_oof_specialist_predictions(train_df, split_df):
    """
    Generate out-of-fold predictions for the 700 train victims using 5-fold cross-fitting.
    
    Returns
    -------
    oof_df : pd.DataFrame
        DataFrame with 21,000 rows containing OOF predictions for all 4 specialists.
    fold_assignments_df : pd.DataFrame
        Mapping of Victim_ID to fold_id (1..5).
    """
    print("\n" + "=" * 70)
    print("STEP 1: 5-FOLD VICTIM-LEVEL CROSS-FITTING OVER 700 TRAIN VICTIMS")
    print("=" * 70)

    train_vids = sorted(list(split_df[split_df["Split"].str.lower() == "train"]["Victim_ID"].unique()))
    assert len(train_vids) == 700, f"Expected 700 train victims, got {len(train_vids)}"

    # Deterministic K-Fold partition at victim level
    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    fold_assignments = {}
    
    for fold_idx, (trn_idx, val_idx) in enumerate(kf.split(train_vids), start=1):
        for idx in val_idx:
            fold_assignments[train_vids[idx]] = fold_idx

    fold_assignments_df = pd.DataFrame([
        {"Victim_ID": vid, "fold_id": fold_assignments[vid]} for vid in train_vids
    ]).sort_values("Victim_ID").reset_index(drop=True)

    # Verification of fold assignments
    print(f"Fold distribution across {len(train_vids)} train victims:")
    for f in range(1, N_FOLDS + 1):
        count = sum(1 for v in train_vids if fold_assignments[v] == f)
        print(f"  Fold {f}: {count} victims ({count * 30} longitudinal rows)")
        assert count == 140, f"Fold {f} does not have exactly 140 victims! Got {count}"

    # Specialist Feature Definitions
    struct_features = get_all_approved_structured_dds_features()
    validate_structured_specialist_features(struct_features)
    struct_cat = ["Case_Type", "Case_Stage", "Episode_Severity"]
    struct_num = [c for c in struct_features if c not in struct_cat]

    text_features = list(V2_CORE_TEXT_DDS_FEATURES)
    validate_text_specialist_features(text_features, allow_extended=False)

    voice_features = list(V2_CORE_VOICE_DDS_FEATURES)
    validate_voice_specialist_features(voice_features, allow_extended=False)

    behav_features = list(V2_EXTENDED_BEHAVIOUR_DDS_FEATURES)
    validate_behaviour_specialist_features(behav_features, allow_extended=True)

    oof_records = []

    for fold_id in range(1, N_FOLDS + 1):
        print(f"\n>>> Running Cross-Fitting Fold {fold_id}/{N_FOLDS} <<<")
        heldout_vids = set(vid for vid, fid in fold_assignments.items() if fid == fold_id)
        train_fold_vids = set(vid for vid, fid in fold_assignments.items() if fid != fold_id)

        assert len(heldout_vids) == 140
        assert len(train_fold_vids) == 560
        assert len(heldout_vids & train_fold_vids) == 0, f"Leakage detected in Fold {fold_id}!"

        fold_train_df = train_df[train_df["Victim_ID"].isin(train_fold_vids)].copy().reset_index(drop=True)
        fold_heldout_df = train_df[train_df["Victim_ID"].isin(heldout_vids)].copy().reset_index(drop=True)

        assert len(fold_train_df) == 560 * 30
        assert len(fold_heldout_df) == 140 * 30

        # -------------------------------------------------------------
        # 1. Structured Specialist (XGBoost, 42 features)
        # -------------------------------------------------------------
        num_transformer = Pipeline([("imputer", SimpleImputer(strategy="median"))])
        cat_transformer = Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value="MISSING")),
            ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
        ])
        struct_preprocessor = ColumnTransformer(
            transformers=[
                ("num", num_transformer, struct_num),
                ("cat", cat_transformer, struct_cat),
            ],
            remainder="drop"
        )
        # FIT PREPROCESSOR ON FOLD TRAIN ONLY
        struct_preprocessor.fit(fold_train_df[struct_features])
        X_struct_train = struct_preprocessor.transform(fold_train_df[struct_features])
        X_struct_heldout = struct_preprocessor.transform(fold_heldout_df[struct_features])
        y_struct_train = fold_train_df[TARGET].values

        struct_model = xgb.XGBRegressor(
            objective="reg:squarederror",
            n_estimators=300,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=SEED,
            n_jobs=-1,
        )
        struct_model.fit(X_struct_train, y_struct_train)
        struct_preds = struct_model.predict(X_struct_heldout)

        # -------------------------------------------------------------
        # 2. Text Specialist (Ridge Core-5, respects Text_Available)
        # -------------------------------------------------------------
        text_avail_train = (fold_train_df["Text_Available"] == 1).values
        text_imputer = SimpleImputer(strategy="median")
        text_imputer.fit(fold_train_df.loc[text_avail_train, text_features])

        X_text_train = text_imputer.transform(fold_train_df.loc[text_avail_train, text_features])
        y_text_train = fold_train_df.loc[text_avail_train, TARGET].values

        text_model = Ridge(alpha=1.0, random_state=SEED)
        text_model.fit(X_text_train, y_text_train)

        # Predict on heldout: mask unavailable
        text_avail_heldout = (fold_heldout_df["Text_Available"] == 1).values
        text_preds = np.full(len(fold_heldout_df), np.nan)
        if text_avail_heldout.sum() > 0:
            X_text_heldout = text_imputer.transform(fold_heldout_df.loc[text_avail_heldout, text_features])
            text_preds[text_avail_heldout] = text_model.predict(X_text_heldout)

        # -------------------------------------------------------------
        # 3. Voice Specialist (Ridge Core-5, respects Voice_Available)
        # -------------------------------------------------------------
        voice_avail_train = (fold_train_df["Voice_Available"] == 1).values
        voice_imputer = SimpleImputer(strategy="median")
        voice_imputer.fit(fold_train_df.loc[voice_avail_train, voice_features])

        X_voice_train = voice_imputer.transform(fold_train_df.loc[voice_avail_train, voice_features])
        y_voice_train = fold_train_df.loc[voice_avail_train, TARGET].values

        voice_model = Ridge(alpha=1.0, random_state=SEED)
        voice_model.fit(X_voice_train, y_voice_train)

        # Predict on heldout: mask unavailable
        voice_avail_heldout = (fold_heldout_df["Voice_Available"] == 1).values
        voice_preds = np.full(len(fold_heldout_df), np.nan)
        if voice_avail_heldout.sum() > 0:
            X_voice_heldout = voice_imputer.transform(fold_heldout_df.loc[voice_avail_heldout, voice_features])
            voice_preds[voice_avail_heldout] = voice_model.predict(X_voice_heldout)

        # -------------------------------------------------------------
        # 4. Behaviour Specialist (Ridge Extended-10, Absolute Deviations)
        # -------------------------------------------------------------
        def prep_behav(df):
            X = df[behav_features].copy()
            if "Engagement_Deviation" in X.columns:
                X["Engagement_Deviation"] = X["Engagement_Deviation"].abs()
            if "Response_Delay_Deviation" in X.columns:
                X["Response_Delay_Deviation"] = X["Response_Delay_Deviation"].abs()
            return X

        behav_imputer = SimpleImputer(strategy="median")
        X_behav_train_raw = prep_behav(fold_train_df)
        behav_imputer.fit(X_behav_train_raw)

        X_behav_train = behav_imputer.transform(X_behav_train_raw)
        y_behav_train = fold_train_df[TARGET].values

        behav_model = Ridge(alpha=1.0, random_state=SEED)
        behav_model.fit(X_behav_train, y_behav_train)

        X_behav_heldout_raw = prep_behav(fold_heldout_df)
        X_behav_heldout = behav_imputer.transform(X_behav_heldout_raw)
        behav_preds = behav_model.predict(X_behav_heldout)

        # -------------------------------------------------------------
        # Assemble Held-out Block
        # -------------------------------------------------------------
        fold_res = pd.DataFrame({
            "Victim_ID": fold_heldout_df["Victim_ID"].values,
            "Timepoint": fold_heldout_df["Timepoint"].values,
            "Actual_DDS": fold_heldout_df[TARGET].values,
            "Struct_Pred": struct_preds,
            "Text_Pred": text_preds,
            "Voice_Pred": voice_preds,
            "Behav_Pred": behav_preds,
            "Struct_Available": np.ones(len(fold_heldout_df), dtype=int),
            "Text_Available": fold_heldout_df["Text_Available"].values.astype(int),
            "Voice_Available": fold_heldout_df["Voice_Available"].values.astype(int),
            "Behav_Available": np.ones(len(fold_heldout_df), dtype=int),
            "fold_id": np.full(len(fold_heldout_df), fold_id, dtype=int),
            "prediction_type": np.full(len(fold_heldout_df), "OOF"),
            "fusion_training_split": np.full(len(fold_heldout_df), "TRAIN"),
        })
        oof_records.append(fold_res)

        print(f"  Fold {fold_id} completed: {len(fold_res)} rows.")

    oof_df = pd.concat(oof_records, axis=0).sort_values(KEYS).reset_index(drop=True)

    # -------------------------------------------------------------
    # Programmatic Verification of OOF Output
    # -------------------------------------------------------------
    print("\n--- Programmatic Verification of OOF Output ---")
    assert len(oof_df) == 21000, f"Expected 21,000 OOF rows, got {len(oof_df)}"
    assert oof_df["Victim_ID"].nunique() == 700, f"Expected 700 victims, got {oof_df['Victim_ID'].nunique()}"
    
    # Assert every victim has exactly 30 timepoints
    v_counts = oof_df.groupby("Victim_ID").size()
    assert (v_counts == 30).all(), "Some train victims do not have exactly 30 rows in OOF dataset!"
    
    # Assert no duplicate (Victim_ID, Timepoint)
    assert not oof_df.duplicated(subset=KEYS).any(), "Duplicate (Victim_ID, Timepoint) found in OOF dataset!"
    
    # Assert no missing predictions where available
    assert oof_df["Struct_Pred"].notna().all(), "Struct_Pred has missing values!"
    assert oof_df["Behav_Pred"].notna().all(), "Behav_Pred has missing values!"
    assert (oof_df.loc[oof_df["Text_Available"] == 1, "Text_Pred"].notna()).all(), "Available text has NaN predictions!"
    assert (oof_df.loc[oof_df["Text_Available"] == 0, "Text_Pred"].isna()).all(), "Unavailable text is not NaN!"
    assert (oof_df.loc[oof_df["Voice_Available"] == 1, "Voice_Pred"].notna()).all(), "Available voice has NaN predictions!"
    assert (oof_df.loc[oof_df["Voice_Available"] == 0, "Voice_Pred"].isna()).all(), "Unavailable voice is not NaN!"

    print("  PASS: Exactly 21,000 OOF rows, 700 victims x 30 timepoints.")
    print("  PASS: Zero duplicate keys, zero leakage across folds.")
    print("  PASS: Modality availability flags and masked predictions strictly verified.")

    return oof_df, fold_assignments_df


# ===========================================================================
# 2. Build Validation Dataset from Canonical Specialists
# ===========================================================================
def build_validation_fusion_dataset():
    """
    Build the validation dataset using predictions from canonical specialists
    trained on ALL 700 train victims.
    """
    print("\n" + "=" * 70)
    print("STEP 2: LOAD VALIDATION PREDICTIONS FROM CANONICAL SPECIALISTS")
    print("=" * 70)

    cfg_struct = VAL_SPECIALIST_CONFIGS["structured"]
    base_df = pd.read_csv(cfg_struct["val_csv"])
    merged = base_df[KEYS + [cfg_struct["actual_col"]]].copy()
    merged.rename(columns={cfg_struct["actual_col"]: "Actual_DDS"}, inplace=True)
    merged["Struct_Pred"] = base_df[cfg_struct["pred_col"]].values
    merged["Struct_Available"] = 1

    # Text
    cfg_text = VAL_SPECIALIST_CONFIGS["text"]
    text_df = pd.read_csv(cfg_text["val_csv"])
    merged = merged.merge(
        text_df[KEYS + [cfg_text["pred_col"], cfg_text["avail_col"]]].rename(
            columns={cfg_text["pred_col"]: "Text_Pred", cfg_text["avail_col"]: "Text_Available"}
        ),
        on=KEYS, how="left"
    )
    merged.loc[merged["Text_Available"] == 0, "Text_Pred"] = np.nan

    # Voice
    cfg_voice = VAL_SPECIALIST_CONFIGS["voice"]
    voice_df = pd.read_csv(cfg_voice["val_csv"])
    merged = merged.merge(
        voice_df[KEYS + [cfg_voice["pred_col"], cfg_voice["avail_col"]]].rename(
            columns={cfg_voice["pred_col"]: "Voice_Pred", cfg_voice["avail_col"]: "Voice_Available"}
        ),
        on=KEYS, how="left"
    )

    # Behaviour
    cfg_behav = VAL_SPECIALIST_CONFIGS["behaviour"]
    behav_df = pd.read_csv(cfg_behav["val_csv"])
    merged = merged.merge(
        behav_df[KEYS + [cfg_behav["pred_col"]]].rename(
            columns={cfg_behav["pred_col"]: "Behav_Pred"}
        ),
        on=KEYS, how="left"
    )
    merged["Behav_Available"] = 1

    merged["Split"] = "val"
    merged["prediction_type"] = "canonical_validation"

    # Integrity verification
    assert len(merged) == 4500, f"Expected 4,500 validation rows, got {len(merged)}"
    assert merged["Victim_ID"].nunique() == 150, f"Expected 150 validation victims, got {merged['Victim_ID'].nunique()}"
    assert not merged.duplicated(subset=KEYS).any(), "Duplicate keys in validation dataset!"
    
    print(f"  PASS: Validation dataset loaded: {len(merged)} rows, 150 victims.")
    return merged


# ===========================================================================
# 3. Feature Preparation
# ===========================================================================
def prepare_feature_matrix(df):
    """
    Prepare feature matrix and target.
    Missing predictions are set to 0.0 with explicit availability flag = 0.
    """
    X = df[FEATURE_COLS].copy()
    for col in V2_FUSION_APPROVED_FEATURES:
        X[col] = X[col].fillna(0.0)
    y = df["Actual_DDS"].values
    return X.values, y


# ===========================================================================
# MAIN PIPELINE
# ===========================================================================
def main():
    print("=" * 80)
    print("MEDHA V2 — STEP 10B CORRECTION: LEAKAGE-SAFE FUSION TRAINING")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    # 1. Load Data
    long_df = pd.read_csv(LONG_CSV)
    split_df = pd.read_csv(SPLIT_CSV)

    train_vids = set(split_df[split_df["Split"].str.lower() == "train"]["Victim_ID"])
    val_vids   = set(split_df[split_df["Split"].str.lower() == "validation"]["Victim_ID"])
    test_vids  = set(split_df[split_df["Split"].str.lower() == "test"]["Victim_ID"])

    assert len(train_vids) == 700
    assert len(val_vids) == 150
    assert len(test_vids) == 150
    assert len(train_vids & val_vids) == 0
    assert len(train_vids & test_vids) == 0
    assert len(val_vids & test_vids) == 0
    print("Authoritative split verified: 700 Train / 150 Val / 150 Test (zero victim overlap).")

    train_df = long_df[long_df["Victim_ID"].isin(train_vids)].copy().reset_index(drop=True)
    assert len(train_df) == 21000

    # 2. Generate OOF Predictions
    oof_train_df, fold_assignments_df = generate_oof_specialist_predictions(train_df, split_df)

    # 3. Compute Specialist OOF Metrics on Train Set
    print("\n" + "=" * 70)
    print("SPECIALIST OOF METRICS ON TRAINING DATA (700 VICTIMS, 21,000 ROWS)")
    print("=" * 70)
    
    specialist_oof_metrics = {}
    for col, name in [
        ("Struct_Pred", "Structured Specialist (XGBoost)"),
        ("Text_Pred", "Text Specialist (Ridge Core-5)"),
        ("Voice_Pred", "Voice Specialist (Ridge Core-5)"),
        ("Behav_Pred", "Behaviour Specialist (Ridge Ext-10)"),
    ]:
        valid_mask = oof_train_df[col].notna()
        res = evaluate_predictions(
            oof_train_df.loc[valid_mask, "Actual_DDS"].values,
            oof_train_df.loc[valid_mask, col].values,
            name
        )
        specialist_oof_metrics[col] = res
        print(f"  {name:38s}: N={res['N']:5d} | MAE={res['MAE']:.4f} | RMSE={res['RMSE']:.4f} | R2={res['R2']:.4f} | Pearson={res['Pearson']:.4f}")

    # 4. Feature Policy Validation
    validate_fusion_features(FEATURE_COLS)
    for forbidden in V2_FUSION_FORBIDDEN_FEATURES:
        if forbidden in oof_train_df.columns and forbidden != "Actual_DDS":
            raise ValueError(f"Forbidden feature {forbidden} in OOF train feature matrix!")
    print(f"\nFeature policy validated: All {len(FEATURE_COLS)} features approved, zero forbidden features.")

    # 5. Build Validation Dataset from Canonical Specialists
    val_df = build_validation_fusion_dataset()

    # 6. Prepare Feature Matrices
    X_train_oof, y_train_oof = prepare_feature_matrix(oof_train_df)
    X_val, y_val = prepare_feature_matrix(val_df)

    print(f"\nMatrix shapes: X_train_oof={X_train_oof.shape}, X_val={X_val.shape}")

    # 7. Candidate A: Inverse-MAE Weighted Average (Derived Strictly from OOF MAE)
    print("\n" + "=" * 70)
    print("CANDIDATE A: MODALITY-AWARE WEIGHTED AVERAGE (DERIVED FROM OOF MAE)")
    print("=" * 70)

    oof_maes = {col: specialist_oof_metrics[col]["MAE"] for col in V2_FUSION_APPROVED_FEATURES}
    inv_maes = {k: 1.0 / v for k, v in oof_maes.items()}
    sum_inv = sum(inv_maes.values())
    raw_weights = {k: v / sum_inv for k, v in inv_maes.items()}

    key_map = {
        "Struct_Pred": "structured",
        "Text_Pred": "text",
        "Voice_Pred": "voice",
        "Behav_Pred": "behaviour",
    }
    cand_a_weights = {key_map[k]: round(raw_weights[k], 6) for k in raw_weights}
    print(f"OOF Training MAEs: {json.dumps({key_map[k]: oof_maes[k] for k in oof_maes}, indent=2)}")
    print(f"Candidate A Derived Weights: {json.dumps(cand_a_weights, indent=2)}")

    train_mean_dds = float(np.mean(y_train_oof))

    def apply_candidate_a(df, weights):
        preds = []
        for _, row in df.iterrows():
            inp = V2FusionInput(
                victim_id=str(row["Victim_ID"]),
                timepoint=int(row["Timepoint"]),
                structured=ModalitySignal(available=bool(row["Struct_Available"]),
                                          dds=row["Struct_Pred"] if pd.notna(row["Struct_Pred"]) else None),
                text=ModalitySignal(available=bool(row.get("Text_Available", 0)),
                                    dds=row["Text_Pred"] if pd.notna(row["Text_Pred"]) else None),
                voice=ModalitySignal(available=bool(row.get("Voice_Available", 0)),
                                     dds=row["Voice_Pred"] if pd.notna(row["Voice_Pred"]) else None),
                behaviour=ModalitySignal(available=bool(row["Behav_Available"]),
                                         dds=row["Behav_Pred"] if pd.notna(row["Behav_Pred"]) else None),
            )
            out = compute_weighted_average_fusion(inp, weights)
            preds.append(out.fused_dds if out.fused_dds is not None else train_mean_dds)
        return np.array(preds)

    cand_a_val_preds = apply_candidate_a(val_df, cand_a_weights)
    cand_a_val_res = evaluate_predictions(y_val, cand_a_val_preds, "Candidate A (Weighted Avg)")
    print(f"  Validation: MAE={cand_a_val_res['MAE']:.4f} | RMSE={cand_a_val_res['RMSE']:.4f} | R2={cand_a_val_res['R2']:.4f} | Pearson={cand_a_val_res['Pearson']:.4f}")

    # 8. Candidate B: Ridge Stacking (Trained strictly on OOF Train)
    print("\n" + "=" * 70)
    print("CANDIDATE B: RIDGE STACKING (TRAINED ON OOF PREDICTIONS)")
    print("=" * 70)

    ridge = RidgeCV(alphas=[0.01, 0.1, 1.0, 10.0, 100.0], cv=5)
    ridge.fit(X_train_oof, y_train_oof)
    print(f"  Ridge selected alpha: {ridge.alpha_}")
    print(f"  Ridge intercept: {ridge.intercept_:.4f}")
    print(f"  Ridge coefficients: {dict(zip(FEATURE_COLS, [round(c, 4) for c in ridge.coef_]))}")

    cand_b_val_preds = np.clip(ridge.predict(X_val), 0, 100)
    cand_b_val_res = evaluate_predictions(y_val, cand_b_val_preds, "Candidate B (Ridge)")
    print(f"  Validation: MAE={cand_b_val_res['MAE']:.4f} | RMSE={cand_b_val_res['RMSE']:.4f} | R2={cand_b_val_res['R2']:.4f} | Pearson={cand_b_val_res['Pearson']:.4f}")

    # 9. Candidate C: XGBoost Stacking (Trained strictly on OOF Train)
    print("\n" + "=" * 70)
    print("CANDIDATE C: XGBOOST STACKING (TRAINED ON OOF PREDICTIONS)")
    print("=" * 70)

    xgb_model = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=10,
        reg_alpha=1.0,
        reg_lambda=5.0,
        random_state=SEED,
    )
    xgb_model.fit(X_train_oof, y_train_oof)
    xgb_importances = dict(zip(FEATURE_COLS, [round(float(v), 4) for v in xgb_model.feature_importances_]))
    print(f"  XGBoost feature importances: {json.dumps(xgb_importances)}")

    cand_c_val_preds = np.clip(xgb_model.predict(X_val), 0, 100)
    cand_c_val_res = evaluate_predictions(y_val, cand_c_val_preds, "Candidate C (XGBoost)")
    print(f"  Validation: MAE={cand_c_val_res['MAE']:.4f} | RMSE={cand_c_val_res['RMSE']:.4f} | R2={cand_c_val_res['R2']:.4f} | Pearson={cand_c_val_res['Pearson']:.4f}")

    # 10. Candidate Selection Strictly on Validation Data
    print("\n" + "=" * 70)
    print("CANDIDATE SELECTION (VALIDATION SET ONLY)")
    print("=" * 70)

    candidates = {
        "A_WeightedAvg": cand_a_val_res,
        "B_Ridge": cand_b_val_res,
        "C_XGBoost": cand_c_val_res,
    }

    metrics_rows = []
    for c_name, res in candidates.items():
        metrics_rows.append({
            "Candidate": c_name,
            "Val_MAE": res["MAE"],
            "Val_RMSE": res["RMSE"],
            "Val_R2": res["R2"],
            "Val_Pearson": res["Pearson"],
            "Val_Spearman": res["Spearman"],
        })
    metrics_df = pd.DataFrame(metrics_rows)
    print(metrics_df.to_string(index=False))

    # Selection rule: candidate with the lowest validation MAE
    best_candidate_name = metrics_df.loc[metrics_df["Val_MAE"].idxmin(), "Candidate"]
    print(f"\n>>> SELECTED MODEL: {best_candidate_name} (Lowest Validation MAE: {metrics_df.loc[metrics_df['Candidate'] == best_candidate_name, 'Val_MAE'].values[0]:.4f}) <<<")
    print("NOTE: Test set was NOT evaluated, inspected, or used in any candidate selection decision.")

    # 11. Attach Selected Predictions to Validation Dataset
    if best_candidate_name == "A_WeightedAvg":
        selected_val_preds = cand_a_val_preds
        selected_model_obj = {"candidate": "A_WeightedAvg", "weights": cand_a_weights}
    elif best_candidate_name == "B_Ridge":
        selected_val_preds = cand_b_val_preds
        selected_model_obj = ridge
    else:
        selected_val_preds = cand_c_val_preds
        selected_model_obj = xgb_model

    val_df["Fusion_DDS_Prediction"] = selected_val_preds

    # 12. Save All Corrected Artifacts
    print("\n" + "=" * 70)
    print("SAVING CORRECTED ARTIFACTS IN OOF NAMESPACE")
    print("=" * 70)

    # Fold assignments
    for d in OUTPUT_DIRS:
        fold_assignments_df.to_csv(os.path.join(d, "fusion_oof_fold_assignments.csv"), index=False)
    print("  Saved: fusion_oof_fold_assignments.csv")

    # OOF Train predictions
    oof_output_cols = [
        "Victim_ID", "Timepoint", "Actual_DDS",
        "Struct_Pred", "Text_Pred", "Voice_Pred", "Behav_Pred",
        "Struct_Available", "Text_Available", "Voice_Available", "Behav_Available",
        "fold_id", "prediction_type", "fusion_training_split"
    ]
    for d in OUTPUT_DIRS:
        oof_train_df[oof_output_cols].to_csv(os.path.join(d, "fusion_oof_train_predictions.csv"), index=False)
    print("  Saved: fusion_oof_train_predictions.csv (21,000 rows)")

    # Validation predictions
    val_output_cols = [
        "Victim_ID", "Timepoint", "Actual_DDS",
        "Struct_Pred", "Text_Pred", "Voice_Pred", "Behav_Pred",
        "Struct_Available", "Text_Available", "Voice_Available", "Behav_Available",
        "Fusion_DDS_Prediction", "prediction_type"
    ]
    for d in OUTPUT_DIRS:
        val_df[val_output_cols].to_csv(os.path.join(d, "fusion_validation_predictions.csv"), index=False)
    print("  Saved: fusion_validation_predictions.csv (4,500 rows)")

    # Candidate metrics CSV
    for d in OUTPUT_DIRS:
        metrics_df.to_csv(os.path.join(d, "fusion_candidate_metrics.csv"), index=False)
    print("  Saved: fusion_candidate_metrics.csv")

    # Feature configuration JSON
    feature_config = {
        "feature_order": FEATURE_COLS,
        "approved_predictions": V2_FUSION_APPROVED_FEATURES,
        "availability_flags": V2_FUSION_AVAILABILITY_FLAGS,
        "forbidden_features": V2_FUSION_FORBIDDEN_FEATURES,
    }
    for d in MODEL_DIRS:
        with open(os.path.join(d, "fusion_feature_config.json"), "w") as f:
            json.dump(feature_config, f, indent=2)
    print("  Saved: fusion_feature_config.json")

    # Selected model description JSON
    selected_model_info = {
        "selected_candidate": best_candidate_name,
        "selection_metric": "Validation MAE",
        "validation_performance": candidates[best_candidate_name],
        "training_protocol": "5-fold victim-level cross-fitting (OOF) over 700 train victims",
        "test_split_status": "UNTOUCHED (frozen for Step 10C final evaluation)",
        "timestamp": datetime.now().isoformat(),
    }
    for d in MODEL_DIRS:
        with open(os.path.join(d, "fusion_selected_model.json"), "w") as f:
            json.dump(selected_model_info, f, indent=2)
    print("  Saved: fusion_selected_model.json")

    # Save models
    for d in MODEL_DIRS:
        # Candidate A weights
        with open(os.path.join(d, "v2_fusion_oof_weights.json"), "w") as f:
            json.dump({
                "candidate": "A_WeightedAvg",
                "derived_from": "OOF Training MAE",
                "weights": cand_a_weights,
            }, f, indent=2)
        # Candidate B model
        with open(os.path.join(d, "v2_fusion_oof_ridge.pkl"), "wb") as f:
            pickle.dump(ridge, f)
        # Candidate C model
        xgb_model.save_model(os.path.join(d, "v2_fusion_oof_xgb.json"))

        # Save selected model to canonical name
        if best_candidate_name == "B_Ridge":
            with open(os.path.join(d, "fusion_model.pkl"), "wb") as f:
                pickle.dump(ridge, f)
        elif best_candidate_name == "C_XGBoost":
            xgb_model.save_model(os.path.join(d, "fusion_model.json"))
        elif best_candidate_name == "A_WeightedAvg":
            with open(os.path.join(d, "fusion_model.json"), "w") as f:
                json.dump({"candidate": "A_WeightedAvg", "weights": cand_a_weights}, f, indent=2)

    print("  Saved: Candidate models and frozen selected fusion model.")

    # Metadata JSON
    metadata = {
        "step": "10B_CORRECTION",
        "methodology": "Leakage-Safe 5-Fold Victim-Level Cross-Fitting OOF Stacking",
        "timestamp": datetime.now().isoformat(),
        "random_seed": SEED,
        "n_folds": N_FOLDS,
        "train_victims": len(train_vids),
        "train_rows": len(oof_train_df),
        "validation_victims": len(val_vids),
        "validation_rows": len(val_df),
        "test_status": "TEST SET UNTOUCHED (NOT USED IN SELECTION OR TUNING)",
        "specialist_oof_metrics": specialist_oof_metrics,
        "candidates": {
            "A_WeightedAvg": {
                "weights": cand_a_weights,
                "val": cand_a_val_res,
            },
            "B_Ridge": {
                "alpha": float(ridge.alpha_),
                "coefficients": dict(zip(FEATURE_COLS, [round(float(c), 6) for c in ridge.coef_])),
                "intercept": round(float(ridge.intercept_), 6),
                "val": cand_b_val_res,
            },
            "C_XGBoost": {
                "n_estimators": 100,
                "max_depth": 3,
                "learning_rate": 0.1,
                "feature_importance": xgb_importances,
                "val": cand_c_val_res,
            },
        },
        "selected_model": best_candidate_name,
    }
    for d in MODEL_DIRS + OUTPUT_DIRS:
        with open(os.path.join(d, "fusion_oof_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
    print("  Saved: fusion_oof_metadata.json")

    # Training Report JSON
    training_report = {
        "status": "SUCCESS",
        "step": "10B_CORRECTION",
        "summary": "Completed leakage-safe 5-fold cross-fitting over 700 train victims. Candidate selection completed on validation set.",
        "preliminary_artifacts_preserved": True,
        "selected_candidate": best_candidate_name,
        "validation_mae": candidates[best_candidate_name]["MAE"],
        "validation_rmse": candidates[best_candidate_name]["RMSE"],
        "validation_r2": candidates[best_candidate_name]["R2"],
        "validation_pearson": candidates[best_candidate_name]["Pearson"],
        "validation_spearman": candidates[best_candidate_name]["Spearman"],
    }
    for d in OUTPUT_DIRS:
        with open(os.path.join(d, "fusion_oof_training_report.json"), "w") as f:
            json.dump(training_report, f, indent=2)
    print("  Saved: fusion_oof_training_report.json")

    print("\n" + "=" * 80)
    print("MEDHA V2 STEP 10B CORRECTION COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
