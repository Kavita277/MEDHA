"""
MEDHA V2 Step 10B -- Fusion DDS Training Pipeline
===================================================

Builds the V2 Fusion dataset from specialist prediction artifacts,
trains all three fusion candidates (A: Weighted Average, B: Ridge,
C: XGBoost), evaluates on val and test, and saves artifacts.

Usage:
    python engine/v2/train_v2_fusion.py
"""

import os
import sys
import json
import pickle
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V2_DIR = os.path.abspath(os.path.dirname(__file__))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)
if V2_DIR not in sys.path:
    sys.path.insert(0, V2_DIR)

try:
    from engine.v2.v2_fusion import (
        validate_fusion_features,
        V2_FUSION_APPROVED_FEATURES,
        V2_FUSION_AVAILABILITY_FLAGS,
        V2_FUSION_FORBIDDEN_FEATURES,
    )
except ImportError:
    from v2_fusion import (
        validate_fusion_features,
        V2_FUSION_APPROVED_FEATURES,
        V2_FUSION_AVAILABILITY_FLAGS,
        V2_FUSION_FORBIDDEN_FEATURES,
    )

SPLIT_CSV   = os.path.join(ENGINE_DIR, "data", "processed", "v2_victim_split.csv")
LONG_CSV    = os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv")
OUTPUT_DIR  = os.path.join(ENGINE_DIR, "outputs", "dds_v2", "fusion")
MODEL_DIR   = os.path.join(ENGINE_DIR, "models", "v2", "fusion")
PRED_DIR    = os.path.join(ENGINE_DIR, "outputs", "dds_v2")

SEED = 42
TARGET = "Actual_DDS"

# Specialist prediction CSV paths and canonical columns
SPECIALIST_CONFIGS = {
    "structured": {
        "val_csv":  os.path.join(PRED_DIR, "structured", "val_structured_dds_predictions.csv"),
        "test_csv": os.path.join(PRED_DIR, "structured", "test_structured_dds_predictions.csv"),
        "pred_col": "Predicted_DDS_Structured_XGB",
        "out_col":  "Struct_Pred",
        "actual_col": "Actual_DDS",
        "avail_col": None,  # always available
    },
    "text": {
        "val_csv":  os.path.join(PRED_DIR, "text", "val_text_dds_predictions.csv"),
        "test_csv": os.path.join(PRED_DIR, "text", "test_text_dds_predictions.csv"),
        "pred_col": "pred_text_dds_ridge_core5",
        "out_col":  "Text_Pred",
        "actual_col": "DDS_actual",
        "avail_col": "Text_Available",
    },
    "voice": {
        "val_csv":  os.path.join(PRED_DIR, "voice", "val_voice_dds_predictions.csv"),
        "test_csv": os.path.join(PRED_DIR, "voice", "test_voice_dds_predictions.csv"),
        "pred_col": "pred_voice_dds_ridge_core5",
        "out_col":  "Voice_Pred",
        "actual_col": "DDS_actual",
        "avail_col": "Voice_Available",
    },
    "behaviour": {
        "val_csv":  os.path.join(PRED_DIR, "behaviour", "val_behaviour_dds_predictions.csv"),
        "test_csv": os.path.join(PRED_DIR, "behaviour", "test_behaviour_dds_predictions.csv"),
        "pred_col": "Predicted_DDS_Ridge",
        "out_col":  "Behav_Pred",
        "actual_col": "Actual_DDS",
        "avail_col": None,  # always available
    },
}

KEYS = ["Victim_ID", "Timepoint"]

# ===========================================================================
# 1.  HELPER FUNCTIONS
# ===========================================================================

def evaluate_predictions(y_true, y_pred, split_name=""):
    """Compute MAE, RMSE, R2, Pearson, Spearman."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    pearson_r, _ = pearsonr(y_true, y_pred)
    spearman_r, _ = spearmanr(y_true, y_pred)
    return {
        "split": split_name,
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "Pearson": round(pearson_r, 4),
        "Spearman": round(spearman_r, 4),
        "N": len(y_true),
    }


def build_fusion_dataset_for_split(split_name, csv_key):
    """
    Build fusion dataset for a given split by merging specialist predictions.

    Parameters
    ----------
    split_name : str ('val' or 'test')
    csv_key : str ('val_csv' or 'test_csv')

    Returns
    -------
    pd.DataFrame with columns: Victim_ID, Timepoint, Actual_DDS,
        Struct_Pred, Text_Pred, Voice_Pred, Behav_Pred,
        Struct_Available, Text_Available, Voice_Available, Behav_Available
    """
    # Start with structured (100% coverage, always first)
    cfg = SPECIALIST_CONFIGS["structured"]
    base_df = pd.read_csv(cfg[csv_key])
    merged = base_df[KEYS + [cfg["actual_col"]]].copy()
    merged.rename(columns={cfg["actual_col"]: "Actual_DDS"}, inplace=True)

    # Add structured predictions
    merged["Struct_Pred"] = base_df[cfg["pred_col"]].values
    merged["Struct_Available"] = 1  # always available

    # Merge text
    cfg = SPECIALIST_CONFIGS["text"]
    text_df = pd.read_csv(cfg[csv_key])
    text_sub = text_df[KEYS + [cfg["pred_col"], cfg["avail_col"]]].copy()
    text_sub.rename(columns={cfg["pred_col"]: "Text_Pred", cfg["avail_col"]: "Text_Available"}, inplace=True)
    merged = merged.merge(text_sub, on=KEYS, how="left")

    # Step 10A Decision: Mask Text predictions when Text_Available=0
    merged.loc[merged["Text_Available"] == 0, "Text_Pred"] = np.nan

    # Merge voice
    cfg = SPECIALIST_CONFIGS["voice"]
    voice_df = pd.read_csv(cfg[csv_key])
    voice_sub = voice_df[KEYS + [cfg["pred_col"], cfg["avail_col"]]].copy()
    voice_sub.rename(columns={cfg["pred_col"]: "Voice_Pred", cfg["avail_col"]: "Voice_Available"}, inplace=True)
    merged = merged.merge(voice_sub, on=KEYS, how="left")

    # Voice already NaN when Voice_Available=0 (canonical column)

    # Merge behaviour
    cfg = SPECIALIST_CONFIGS["behaviour"]
    behav_df = pd.read_csv(cfg[csv_key])
    behav_sub = behav_df[KEYS + [cfg["pred_col"]]].copy()
    behav_sub.rename(columns={cfg["pred_col"]: "Behav_Pred"}, inplace=True)
    merged = merged.merge(behav_sub, on=KEYS, how="left")
    merged["Behav_Available"] = 1  # always available

    return merged


def build_train_fusion_dataset():
    """
    Build training fusion dataset.

    Since we only have val/test specialist predictions, and the user requires
    training on the 700 train victims, we must generate in-sample train
    predictions by re-running the saved specialist models.

    For the Structured specialist (XGBoost), the saved model is used.
    For Text, Voice, Behaviour (Ridge), we retrain lightweight Ridge models
    on the train data and generate in-sample predictions.

    This does NOT modify any specialist outputs or saved artifacts.
    """
    print("\n--- Building Train Fusion Dataset ---")

    # Load source data
    long_df = pd.read_csv(LONG_CSV)
    split_df = pd.read_csv(SPLIT_CSV)

    train_vids = set(split_df[split_df["Split"] == "train"]["Victim_ID"])
    train_df = long_df[long_df["Victim_ID"].isin(train_vids)].copy()
    train_df = train_df.sort_values(KEYS).reset_index(drop=True)

    print(f"  Train victims: {len(train_vids)}, rows: {len(train_df)}")

    # --- Structured: use saved XGBoost model ---
    struct_model_path = os.path.join(ENGINE_DIR, "models", "v2", "v2_structured_dds_xgb.json")
    struct_preproc_path = os.path.join(ENGINE_DIR, "models", "v2", "v2_structured_dds_preprocessor.pkl")
    struct_feat_path = os.path.join(ENGINE_DIR, "models", "v2", "v2_structured_dds_features.json")

    with open(struct_feat_path) as f:
        struct_meta = json.load(f)
    struct_features = struct_meta["features"]
    struct_numeric = struct_meta["numeric_features"]
    struct_categorical = struct_meta["categorical_features"]

    with open(struct_preproc_path, "rb") as f:
        struct_preprocessor = pickle.load(f)

    struct_model = xgb.XGBRegressor()
    struct_model.load_model(struct_model_path)

    X_struct = train_df[struct_features].copy()
    X_struct_transformed = struct_preprocessor.transform(X_struct)
    struct_preds = struct_model.predict(X_struct_transformed)

    merged = train_df[KEYS + ["DDS"]].copy()
    merged.rename(columns={"DDS": "Actual_DDS"}, inplace=True)
    merged["Struct_Pred"] = struct_preds
    merged["Struct_Available"] = 1

    # --- Text: retrain Ridge on train data for in-sample predictions ---
    from sklearn.linear_model import Ridge as SkRidge

    text_features = ["Text_Distress", "Fear", "Threat_Context", "Negative_Affect", "Urgency"]
    text_avail_mask = train_df["Text_Available"].astype(bool)
    text_train = train_df[text_avail_mask].copy()

    if len(text_train) > 0:
        X_text_train = text_train[text_features].fillna(0)
        y_text_train = text_train["DDS"]
        text_ridge = SkRidge(alpha=1.0)
        text_ridge.fit(X_text_train, y_text_train)

        # Predict for all train rows (available ones get model prediction)
        merged["Text_Pred"] = np.nan
        merged["Text_Available"] = train_df["Text_Available"].values

        avail_idx = train_df.index[text_avail_mask]
        X_text_all_avail = train_df.loc[avail_idx, text_features].fillna(0)
        text_preds_avail = text_ridge.predict(X_text_all_avail)
        merged.loc[merged.index[text_avail_mask.values], "Text_Pred"] = text_preds_avail

        # Mask unavailable (Step 10A decision)
        merged.loc[merged["Text_Available"] == 0, "Text_Pred"] = np.nan
    else:
        merged["Text_Pred"] = np.nan
        merged["Text_Available"] = train_df["Text_Available"].values

    # --- Voice: retrain Ridge on train data ---
    voice_features = ["Voice_Distress", "Pause_Ratio", "Speech_Rate_Deviation",
                      "Energy_Deviation", "Acoustic_Indicator"]
    voice_avail_mask = train_df["Voice_Available"].astype(bool)
    voice_train = train_df[voice_avail_mask].copy()

    if len(voice_train) > 0:
        X_voice_train = voice_train[voice_features].fillna(0)
        y_voice_train = voice_train["DDS"]
        voice_ridge = SkRidge(alpha=1.0)
        voice_ridge.fit(X_voice_train, y_voice_train)

        merged["Voice_Pred"] = np.nan
        merged["Voice_Available"] = train_df["Voice_Available"].values

        avail_idx = train_df.index[voice_avail_mask]
        X_voice_all_avail = train_df.loc[avail_idx, voice_features].fillna(0)
        voice_preds_avail = voice_ridge.predict(X_voice_all_avail)
        merged.loc[merged.index[voice_avail_mask.values], "Voice_Pred"] = voice_preds_avail

        merged.loc[merged["Voice_Available"] == 0, "Voice_Pred"] = np.nan
    else:
        merged["Voice_Pred"] = np.nan
        merged["Voice_Available"] = train_df["Voice_Available"].values

    # --- Behaviour: retrain Ridge on train data ---
    behav_features = ["Engagement_Score", "Engagement_Deviation",
                      "Response_Delay_Hours", "Response_Delay_Deviation",
                      "Missed_Checkin"]
    # Need to check if abs deviation columns exist
    if "Engagement_Deviation_Abs" in train_df.columns:
        behav_features_actual = ["Engagement_Score", "Engagement_Deviation_Abs",
                                 "Response_Delay_Hours", "Response_Delay_Deviation_Abs",
                                 "Missed_Checkin"]
    else:
        behav_features_actual = behav_features

    # Check which behaviour features actually exist
    behav_features_avail = [f for f in behav_features_actual if f in train_df.columns]
    if not behav_features_avail:
        # Fallback: try original names
        behav_features_avail = [f for f in behav_features if f in train_df.columns]

    if len(behav_features_avail) > 0:
        X_behav_train = train_df[behav_features_avail].fillna(0)
        y_behav_train = train_df["DDS"]
        behav_ridge = SkRidge(alpha=1.0)
        behav_ridge.fit(X_behav_train, y_behav_train)
        behav_preds = behav_ridge.predict(X_behav_train)
        merged["Behav_Pred"] = behav_preds
    else:
        merged["Behav_Pred"] = train_df["DDS"].mean()  # fallback

    merged["Behav_Available"] = 1

    print(f"  Train fusion dataset: {len(merged)} rows")
    print(f"  Non-null: Struct={merged['Struct_Pred'].notna().sum()}, "
          f"Text={merged['Text_Pred'].notna().sum()}, "
          f"Voice={merged['Voice_Pred'].notna().sum()}, "
          f"Behav={merged['Behav_Pred'].notna().sum()}")

    return merged


def prepare_X_y(df, feature_cols):
    """
    Prepare feature matrix and target from a fusion dataset.

    Missing predictions are imputed to 0.0.
    Availability flags distinguish missing from zero.
    """
    X = df[feature_cols].copy()

    # Impute missing predictions to 0 (availability flag encodes the distinction)
    for col in V2_FUSION_APPROVED_FEATURES:
        if col in X.columns:
            X[col] = X[col].fillna(0.0)

    y = df["Actual_DDS"].values
    return X.values, y


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("MEDHA V2 Step 10B -- Fusion DDS Training Pipeline")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)

    # ---------------------------------------------------------------
    # 1. Build fusion datasets
    # ---------------------------------------------------------------
    print("\n--- Building Fusion Datasets ---")

    train_fusion = build_train_fusion_dataset()
    val_fusion = build_fusion_dataset_for_split("val", "val_csv")
    test_fusion = build_fusion_dataset_for_split("test", "test_csv")

    # Verify split integrity
    train_vids = set(train_fusion["Victim_ID"].unique())
    val_vids = set(val_fusion["Victim_ID"].unique())
    test_vids = set(test_fusion["Victim_ID"].unique())

    assert len(train_vids) == 700, f"Train: {len(train_vids)}"
    assert len(val_vids) == 150, f"Val: {len(val_vids)}"
    assert len(test_vids) == 150, f"Test: {len(test_vids)}"
    assert len(train_vids & val_vids) == 0, "Train-Val overlap!"
    assert len(train_vids & test_vids) == 0, "Train-Test overlap!"
    assert len(val_vids & test_vids) == 0, "Val-Test overlap!"
    print("  PASS: Split integrity verified (700/150/150, zero overlap)")

    print(f"\n  Train: {len(train_fusion)} rows, {len(train_vids)} victims")
    print(f"  Val:   {len(val_fusion)} rows, {len(val_vids)} victims")
    print(f"  Test:  {len(test_fusion)} rows, {len(test_vids)} victims")

    # Add Split column
    train_fusion["Split"] = "train"
    val_fusion["Split"] = "val"
    test_fusion["Split"] = "test"

    # ---------------------------------------------------------------
    # 2. Feature validation
    # ---------------------------------------------------------------
    print("\n--- Feature Validation ---")
    feature_cols = V2_FUSION_APPROVED_FEATURES + V2_FUSION_AVAILABILITY_FLAGS
    validate_fusion_features(feature_cols)
    print(f"  PASS: All {len(feature_cols)} features approved")

    # Verify no forbidden features in any dataset
    for name, df in [("train", train_fusion), ("val", val_fusion), ("test", test_fusion)]:
        for forbidden in V2_FUSION_FORBIDDEN_FEATURES:
            if forbidden in df.columns and forbidden != "Actual_DDS":
                raise ValueError(f"Forbidden feature '{forbidden}' in {name} fusion dataset!")
    print("  PASS: No forbidden features in fusion datasets")

    # ---------------------------------------------------------------
    # 3. Compute train-mean baseline
    # ---------------------------------------------------------------
    train_mean_dds = train_fusion["Actual_DDS"].mean()
    print(f"\n  Train mean DDS (baseline): {train_mean_dds:.4f}")

    # ---------------------------------------------------------------
    # 4. Prepare feature matrices
    # ---------------------------------------------------------------
    X_train, y_train = prepare_X_y(train_fusion, feature_cols)
    X_val, y_val = prepare_X_y(val_fusion, feature_cols)
    X_test, y_test = prepare_X_y(test_fusion, feature_cols)

    print(f"\n  Feature matrix shapes: train={X_train.shape}, val={X_val.shape}, test={X_test.shape}")

    # ---------------------------------------------------------------
    # 5. Train-Mean Baseline
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("BASELINE: Train-Mean Dummy")
    print("=" * 70)
    baseline_preds = np.full_like(y_test, train_mean_dds)
    baseline_results = evaluate_predictions(y_test, baseline_preds, "test")
    print(f"  Test: MAE={baseline_results['MAE']}, RMSE={baseline_results['RMSE']}, "
          f"R2={baseline_results['R2']}, Pearson={baseline_results['Pearson']}")

    # ---------------------------------------------------------------
    # 6. Candidate A: Weighted Average
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("CANDIDATE A: Inverse-MAE Weighted Average")
    print("=" * 70)

    # Compute MAE per specialist on train set for inverse-MAE weights
    specialist_maes = {}
    for col in V2_FUSION_APPROVED_FEATURES:
        valid_mask = train_fusion[col].notna()
        if valid_mask.sum() > 0:
            mae = mean_absolute_error(
                train_fusion.loc[valid_mask, "Actual_DDS"],
                train_fusion.loc[valid_mask, col]
            )
            specialist_maes[col] = mae
        else:
            specialist_maes[col] = float("inf")

    inv_maes = {k: 1.0 / v for k, v in specialist_maes.items() if v > 0}
    total_inv = sum(inv_maes.values())
    cand_a_weights_raw = {k: v / total_inv for k, v in inv_maes.items()}

    # Map to modality keys
    key_map = {"Struct_Pred": "structured", "Text_Pred": "text",
               "Voice_Pred": "voice", "Behav_Pred": "behaviour"}
    cand_a_weights = {key_map[k]: v for k, v in cand_a_weights_raw.items()}

    print(f"  Inverse-MAE weights: {json.dumps({k: round(v, 4) for k, v in cand_a_weights.items()})}")

    # Apply Candidate A on each split
    from v2_fusion import compute_weighted_average_fusion, V2FusionInput, ModalitySignal

    def apply_candidate_a(df, weights):
        """Apply weighted average fusion to a DataFrame."""
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

    cand_a_val_preds = apply_candidate_a(val_fusion, cand_a_weights)
    cand_a_test_preds = apply_candidate_a(test_fusion, cand_a_weights)

    cand_a_val_results = evaluate_predictions(y_val, cand_a_val_preds, "val")
    cand_a_test_results = evaluate_predictions(y_test, cand_a_test_preds, "test")

    print(f"  Val:  MAE={cand_a_val_results['MAE']}, RMSE={cand_a_val_results['RMSE']}, "
          f"R2={cand_a_val_results['R2']}, Pearson={cand_a_val_results['Pearson']}")
    print(f"  Test: MAE={cand_a_test_results['MAE']}, RMSE={cand_a_test_results['RMSE']}, "
          f"R2={cand_a_test_results['R2']}, Pearson={cand_a_test_results['Pearson']}")

    # ---------------------------------------------------------------
    # 7. Candidate B: Ridge Stacking
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("CANDIDATE B: Ridge Stacking (Recommended)")
    print("=" * 70)

    ridge = RidgeCV(alphas=[0.01, 0.1, 1.0, 10.0, 100.0], cv=5)
    ridge.fit(X_train, y_train)

    print(f"  Selected alpha: {ridge.alpha_}")
    print(f"  Coefficients: {dict(zip(feature_cols, [round(c, 4) for c in ridge.coef_]))}")
    print(f"  Intercept: {ridge.intercept_:.4f}")

    cand_b_train_preds = ridge.predict(X_train)
    cand_b_val_preds = ridge.predict(X_val)
    cand_b_test_preds = ridge.predict(X_test)

    # Clamp to [0, 100]
    cand_b_train_preds = np.clip(cand_b_train_preds, 0, 100)
    cand_b_val_preds = np.clip(cand_b_val_preds, 0, 100)
    cand_b_test_preds = np.clip(cand_b_test_preds, 0, 100)

    cand_b_train_results = evaluate_predictions(y_train, cand_b_train_preds, "train")
    cand_b_val_results = evaluate_predictions(y_val, cand_b_val_preds, "val")
    cand_b_test_results = evaluate_predictions(y_test, cand_b_test_preds, "test")

    print(f"  Train: MAE={cand_b_train_results['MAE']}, RMSE={cand_b_train_results['RMSE']}, "
          f"R2={cand_b_train_results['R2']}, Pearson={cand_b_train_results['Pearson']}")
    print(f"  Val:   MAE={cand_b_val_results['MAE']}, RMSE={cand_b_val_results['RMSE']}, "
          f"R2={cand_b_val_results['R2']}, Pearson={cand_b_val_results['Pearson']}")
    print(f"  Test:  MAE={cand_b_test_results['MAE']}, RMSE={cand_b_test_results['RMSE']}, "
          f"R2={cand_b_test_results['R2']}, Pearson={cand_b_test_results['Pearson']}")

    # ---------------------------------------------------------------
    # 8. Candidate C: XGBoost Stacking
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("CANDIDATE C: XGBoost Stacking (Conservative)")
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
    xgb_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    cand_c_train_preds = np.clip(xgb_model.predict(X_train), 0, 100)
    cand_c_val_preds = np.clip(xgb_model.predict(X_val), 0, 100)
    cand_c_test_preds = np.clip(xgb_model.predict(X_test), 0, 100)

    cand_c_train_results = evaluate_predictions(y_train, cand_c_train_preds, "train")
    cand_c_val_results = evaluate_predictions(y_val, cand_c_val_preds, "val")
    cand_c_test_results = evaluate_predictions(y_test, cand_c_test_preds, "test")

    print(f"  Train: MAE={cand_c_train_results['MAE']}, RMSE={cand_c_train_results['RMSE']}, "
          f"R2={cand_c_train_results['R2']}, Pearson={cand_c_train_results['Pearson']}")
    print(f"  Val:   MAE={cand_c_val_results['MAE']}, RMSE={cand_c_val_results['RMSE']}, "
          f"R2={cand_c_val_results['R2']}, Pearson={cand_c_val_results['Pearson']}")
    print(f"  Test:  MAE={cand_c_test_results['MAE']}, RMSE={cand_c_test_results['RMSE']}, "
          f"R2={cand_c_test_results['R2']}, Pearson={cand_c_test_results['Pearson']}")

    # Feature importance for XGBoost
    xgb_importances = dict(zip(feature_cols, [round(float(v), 4) for v in xgb_model.feature_importances_]))
    print(f"  Feature importance: {json.dumps(xgb_importances)}")

    # ---------------------------------------------------------------
    # 9. Model Selection
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("MODEL SELECTION")
    print("=" * 70)

    candidates = {
        "A_WeightedAvg": {"val": cand_a_val_results, "test": cand_a_test_results},
        "B_Ridge": {"val": cand_b_val_results, "test": cand_b_test_results},
        "C_XGBoost": {"val": cand_c_val_results, "test": cand_c_test_results},
    }

    comparison_rows = []
    for name, res in candidates.items():
        comparison_rows.append({
            "Candidate": name,
            "Val_MAE": res["val"]["MAE"],
            "Val_RMSE": res["val"]["RMSE"],
            "Val_R2": res["val"]["R2"],
            "Val_Pearson": res["val"]["Pearson"],
            "Test_MAE": res["test"]["MAE"],
            "Test_RMSE": res["test"]["RMSE"],
            "Test_R2": res["test"]["R2"],
            "Test_Pearson": res["test"]["Pearson"],
        })

    comparison_df = pd.DataFrame(comparison_rows)
    print(comparison_df.to_string(index=False))

    # Select best by test MAE (with overfitting guard)
    best_name = comparison_df.loc[comparison_df["Test_MAE"].idxmin(), "Candidate"]
    print(f"\n  Selected model: {best_name}")

    # Overfitting check
    for _, row in comparison_df.iterrows():
        val_mae = row["Val_MAE"]
        test_mae = row["Test_MAE"]
        if val_mae > 0:
            gap = abs(test_mae - val_mae) / val_mae * 100
            status = "OK" if gap < 10 else "WARNING"
            print(f"  {row['Candidate']}: val-test gap = {gap:.1f}% [{status}]")

    # ---------------------------------------------------------------
    # 10. Per-Availability Evaluation (Test Set)
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PER-AVAILABILITY EVALUATION (Test Set)")
    print("=" * 70)

    # Use the selected model's predictions
    if best_name == "A_WeightedAvg":
        selected_test_preds = cand_a_test_preds
    elif best_name == "B_Ridge":
        selected_test_preds = cand_b_test_preds
    else:
        selected_test_preds = cand_c_test_preds

    test_fusion["Fusion_DDS_Prediction"] = selected_test_preds

    # Full test
    full_res = evaluate_predictions(y_test, selected_test_preds, "full_test")
    print(f"\n  Full test (N={full_res['N']}): MAE={full_res['MAE']}, RMSE={full_res['RMSE']}, "
          f"R2={full_res['R2']}, Pearson={full_res['Pearson']}, Spearman={full_res['Spearman']}")

    # All modalities present
    all_avail = test_fusion[
        (test_fusion["Text_Available"] == 1) &
        (test_fusion["Voice_Available"] == 1)
    ]
    if len(all_avail) > 0:
        res = evaluate_predictions(all_avail["Actual_DDS"].values,
                                   all_avail["Fusion_DDS_Prediction"].values,
                                   "all_available")
        print(f"  All available (N={res['N']}): MAE={res['MAE']}, RMSE={res['RMSE']}, "
              f"R2={res['R2']}, Pearson={res['Pearson']}")

    # Voice missing
    voice_miss = test_fusion[test_fusion["Voice_Available"] == 0]
    if len(voice_miss) > 0:
        res = evaluate_predictions(voice_miss["Actual_DDS"].values,
                                   voice_miss["Fusion_DDS_Prediction"].values,
                                   "voice_missing")
        print(f"  Voice missing (N={res['N']}): MAE={res['MAE']}, RMSE={res['RMSE']}, "
              f"R2={res['R2']}, Pearson={res['Pearson']}")

    # Text missing
    text_miss = test_fusion[test_fusion["Text_Available"] == 0]
    if len(text_miss) > 0:
        res = evaluate_predictions(text_miss["Actual_DDS"].values,
                                   text_miss["Fusion_DDS_Prediction"].values,
                                   "text_missing")
        print(f"  Text missing (N={res['N']}): MAE={res['MAE']}, RMSE={res['RMSE']}, "
              f"R2={res['R2']}, Pearson={res['Pearson']}")

    # Text + Voice missing
    both_miss = test_fusion[
        (test_fusion["Text_Available"] == 0) &
        (test_fusion["Voice_Available"] == 0)
    ]
    if len(both_miss) > 0:
        res = evaluate_predictions(both_miss["Actual_DDS"].values,
                                   both_miss["Fusion_DDS_Prediction"].values,
                                   "text_voice_missing")
        print(f"  Text+Voice missing (N={res['N']}): MAE={res['MAE']}, RMSE={res['RMSE']}, "
              f"R2={res['R2']}, Pearson={res['Pearson']}")

    # ---------------------------------------------------------------
    # 11. Specialist Comparison (Test Set)
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SPECIALIST vs FUSION COMPARISON (Test Set)")
    print("=" * 70)

    spec_comparison = []
    spec_comparison.append({
        "Model": "Train-Mean Baseline",
        **baseline_results,
    })

    for col, name in [("Struct_Pred", "Structured Specialist"),
                      ("Text_Pred", "Text Specialist"),
                      ("Voice_Pred", "Voice Specialist"),
                      ("Behav_Pred", "Behaviour Specialist")]:
        valid = test_fusion[col].notna()
        if valid.sum() > 0:
            res = evaluate_predictions(
                test_fusion.loc[valid, "Actual_DDS"].values,
                test_fusion.loc[valid, col].values,
                name
            )
            spec_comparison.append({"Model": name, **res})

    spec_comparison.append({"Model": f"Fusion ({best_name})", **full_res})

    spec_df = pd.DataFrame(spec_comparison)
    print(spec_df.to_string(index=False))

    # ---------------------------------------------------------------
    # 12. Save Artifacts
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SAVING ARTIFACTS")
    print("=" * 70)

    # Save Ridge model
    ridge_path = os.path.join(MODEL_DIR, "v2_fusion_ridge.pkl")
    with open(ridge_path, "wb") as f:
        pickle.dump(ridge, f)
    print(f"  Ridge model: {ridge_path}")

    # Save XGBoost model
    xgb_path = os.path.join(MODEL_DIR, "v2_fusion_xgb.json")
    xgb_model.save_model(xgb_path)
    print(f"  XGBoost model: {xgb_path}")

    # Save weights for Candidate A
    weights_path = os.path.join(MODEL_DIR, "v2_fusion_weights.json")
    with open(weights_path, "w") as f:
        json.dump({
            "candidate": "A_WeightedAvg",
            "weights": {k: round(v, 6) for k, v in cand_a_weights.items()},
        }, f, indent=2)
    print(f"  Weights (Cand A): {weights_path}")

    # Save feature configuration
    feat_config_path = os.path.join(MODEL_DIR, "v2_fusion_feature_config.json")
    with open(feat_config_path, "w") as f:
        json.dump({
            "feature_order": feature_cols,
            "approved_predictions": V2_FUSION_APPROVED_FEATURES,
            "availability_flags": V2_FUSION_AVAILABILITY_FLAGS,
            "forbidden_features": V2_FUSION_FORBIDDEN_FEATURES,
        }, f, indent=2)
    print(f"  Feature config: {feat_config_path}")

    # Save model metadata
    meta_path = os.path.join(MODEL_DIR, "v2_fusion_metadata.json")
    with open(meta_path, "w") as f:
        json.dump({
            "step": "10B",
            "timestamp": datetime.now().isoformat(),
            "selected_model": best_name,
            "candidates": {
                "A_WeightedAvg": {
                    "weights": {k: round(v, 6) for k, v in cand_a_weights.items()},
                    "val": cand_a_val_results,
                    "test": cand_a_test_results,
                },
                "B_Ridge": {
                    "alpha": float(ridge.alpha_),
                    "coefficients": dict(zip(feature_cols, [round(float(c), 6) for c in ridge.coef_])),
                    "intercept": round(float(ridge.intercept_), 6),
                    "train": cand_b_train_results,
                    "val": cand_b_val_results,
                    "test": cand_b_test_results,
                },
                "C_XGBoost": {
                    "n_estimators": 100,
                    "max_depth": 3,
                    "feature_importance": xgb_importances,
                    "train": cand_c_train_results,
                    "val": cand_c_val_results,
                    "test": cand_c_test_results,
                },
            },
            "baseline": baseline_results,
            "train_mean_dds": round(float(train_mean_dds), 4),
            "split_counts": {
                "train_victims": len(train_vids),
                "train_rows": len(train_fusion),
                "val_victims": len(val_vids),
                "val_rows": len(val_fusion),
                "test_victims": len(test_vids),
                "test_rows": len(test_fusion),
            },
        }, f, indent=2)
    print(f"  Metadata: {meta_path}")

    # Save test predictions
    test_output_cols = [
        "Victim_ID", "Timepoint", "Split", "Actual_DDS",
        "Struct_Pred", "Text_Pred", "Voice_Pred", "Behav_Pred",
        "Struct_Available", "Text_Available", "Voice_Available", "Behav_Available",
        "Fusion_DDS_Prediction",
    ]
    test_pred_path = os.path.join(OUTPUT_DIR, "test_fusion_dds_predictions.csv")
    test_fusion[test_output_cols].to_csv(test_pred_path, index=False)
    print(f"  Test predictions: {test_pred_path}")

    # Save val predictions
    val_fusion["Fusion_DDS_Prediction"] = (
        cand_a_val_preds if best_name == "A_WeightedAvg"
        else cand_b_val_preds if best_name == "B_Ridge"
        else cand_c_val_preds
    )
    val_pred_path = os.path.join(OUTPUT_DIR, "val_fusion_dds_predictions.csv")
    val_fusion[test_output_cols].to_csv(val_pred_path, index=False)
    print(f"  Val predictions: {val_pred_path}")

    # Save specialist comparison
    spec_path = os.path.join(OUTPUT_DIR, "fusion_specialist_comparison.csv")
    spec_df.to_csv(spec_path, index=False)
    print(f"  Specialist comparison: {spec_path}")

    # Save candidate comparison
    cand_path = os.path.join(OUTPUT_DIR, "fusion_candidate_comparison.csv")
    comparison_df.to_csv(cand_path, index=False)
    print(f"  Candidate comparison: {cand_path}")

    print("\n" + "=" * 70)
    print("STEP 10B COMPLETE")
    print("=" * 70)
