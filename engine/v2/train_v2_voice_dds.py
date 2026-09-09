"""
MEDHA V2 Step 7 -- Voice DDS Specialist Training Script

Trains independent Voice DDS regression models to predict current-timepoint DDS
using approved Voice-derived features from the regenerated dataset
with victim-level train/val/test split.

Usage:
    python engine/v2/train_v2_voice_dds.py
"""

import os
import sys
import json
import pickle
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V2_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(ENGINE_DIR, '..'))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)
if V2_DIR not in sys.path:
    sys.path.insert(0, V2_DIR)

try:
    from engine.v2.v2_feature_policy import (
        validate_dds_features,
        validate_voice_specialist_features,
        get_all_approved_voice_dds_features,
        V2_DDS_APPROVED_FEATURES,
        V2_VOICE_DDS_FEATURES,
        V2_CORE_VOICE_DDS_FEATURES,
        V2_TEXT_DDS_FEATURES,
        V2_STRUCTURED_DDS_FEATURES,
        V2_DDS_EXCLUDED_FEATURES,
        V2_DDS_QUARANTINED_FEATURES,
        V2_DDS_TARGET_FEATURES,
        V2_DDS_ID_METADATA_FEATURES,
        V2_DDS_POST_HOC_FEATURES,
    )
except ImportError:
    from v2_feature_policy import (
        validate_dds_features,
        validate_voice_specialist_features,
        get_all_approved_voice_dds_features,
        V2_DDS_APPROVED_FEATURES,
        V2_VOICE_DDS_FEATURES,
        V2_CORE_VOICE_DDS_FEATURES,
        V2_TEXT_DDS_FEATURES,
        V2_STRUCTURED_DDS_FEATURES,
        V2_DDS_EXCLUDED_FEATURES,
        V2_DDS_QUARANTINED_FEATURES,
        V2_DDS_TARGET_FEATURES,
        V2_DDS_ID_METADATA_FEATURES,
        V2_DDS_POST_HOC_FEATURES,
    )

SPLIT_CSV    = os.path.join(ENGINE_DIR, "data", "processed", "v2_victim_split.csv")
LONG_CSV     = os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv")
SPLIT_CONFIG = os.path.join(ENGINE_DIR, "data", "processed", "v2_split_config.json")

# Target artifact directories (both root and engine mirror)
MODEL_DIRS = [
    os.path.join(ROOT_DIR, "models", "voice_dds_v2"),
    os.path.join(ENGINE_DIR, "models", "voice_dds_v2"),
]
OUTPUT_DIRS = [
    os.path.join(ROOT_DIR, "outputs", "dds_v2", "voice"),
    os.path.join(ENGINE_DIR, "outputs", "dds_v2", "voice"),
]

for d in MODEL_DIRS + OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

SEED = 42
TARGET = "DDS"

# ===========================================================================
# 1. LOAD DATA
# ===========================================================================
print("=" * 60)
print("MEDHA V2 Step 7 -- Voice DDS Specialist Training")
print("=" * 60)

df = pd.read_csv(LONG_CSV)
split_df = pd.read_csv(SPLIT_CSV)
print(f"\nLoaded longitudinal dataset: {len(df)} rows, {df['Victim_ID'].nunique()} victims")
print(f"Loaded victim split: {len(split_df)} rows")

# ===========================================================================
# 2. VERIFY SPLIT INTEGRITY
# ===========================================================================
print("\n--- Split Integrity Checks ---")
train_vids = set(split_df[split_df["Split"] == "train"]["Victim_ID"])
val_vids   = set(split_df[split_df["Split"] == "validation"]["Victim_ID"])
test_vids  = set(split_df[split_df["Split"] == "test"]["Victim_ID"])

assert len(train_vids) == 700,  f"Train victims: {len(train_vids)}"
assert len(val_vids)   == 150,  f"Val victims: {len(val_vids)}"
assert len(test_vids)  == 150,  f"Test victims: {len(test_vids)}"
assert len(train_vids & val_vids) == 0,  "Train/Val overlap!"
assert len(train_vids & test_vids) == 0, "Train/Test overlap!"
assert len(val_vids & test_vids) == 0,   "Val/Test overlap!"
assert len(train_vids | val_vids | test_vids) == 1000
print("  PASS: 700/150/150, zero overlap")

train_df = df[df["Split"] == "train"].copy()
val_df   = df[df["Split"] == "validation"].copy()
test_df  = df[df["Split"] == "test"].copy()

print(f"  Train rows: {len(train_df)}, Val rows: {len(val_df)}, Test rows: {len(test_df)}")

# ===========================================================================
# 3. FEATURE SELECTION & SPECIALIST BOUNDARY VALIDATION
# ===========================================================================
print("\n--- Voice Specialist Boundary Validation ---")
CORE_FEATURES = list(V2_CORE_VOICE_DDS_FEATURES)
ALL_VOICE_FEATURES = list(V2_VOICE_DDS_FEATURES)

print(f"  Core Voice features ({len(CORE_FEATURES)}): {CORE_FEATURES}")
print(f"  All Voice features ({len(ALL_VOICE_FEATURES)}): {ALL_VOICE_FEATURES}")

# Validate against policy
validate_voice_specialist_features(CORE_FEATURES, allow_extended=False)
validate_voice_specialist_features(ALL_VOICE_FEATURES, allow_extended=True)
print("  PASS: Strict specialist validation passed for both Core and Extended feature sets")

# Purity checks: no Text, no Structured, no target, no lag
for feat_set in [CORE_FEATURES, ALL_VOICE_FEATURES]:
    assert len(set(feat_set) & set(V2_TEXT_DDS_FEATURES)) == 0, "Text feature detected!"
    assert len(set(feat_set) & set(V2_STRUCTURED_DDS_FEATURES)) == 0, "Structured feature detected!"
    assert len(set(feat_set) & set(V2_DDS_EXCLUDED_FEATURES)) == 0, "Excluded leaky feature detected!"
    assert len(set(feat_set) & set(V2_DDS_TARGET_FEATURES)) == 0, "Target feature detected!"
print("  PASS: Zero overlap with Text, Structured, Excluded, or Target features")

# ===========================================================================
# 4. MISSING VOICE REPRESENTATION & PREPROCESSING PIPELINE
# ===========================================================================
print("\n--- Missing Voice Analysis & Preprocessing Pipeline ---")
train_avail_mask = (train_df["Voice_Available"] == 1).values
val_avail_mask   = (val_df["Voice_Available"] == 1).values
test_avail_mask  = (test_df["Voice_Available"] == 1).values

print(f"  Available voice observations (Voice_Available == 1):")
print(f"    Train: {train_avail_mask.sum()}/{len(train_df)} ({train_avail_mask.mean()*100:.2f}%)")
print(f"    Val:   {val_avail_mask.sum()}/{len(val_df)} ({val_avail_mask.mean()*100:.2f}%)")
print(f"    Test:  {test_avail_mask.sum()}/{len(test_df)} ({test_avail_mask.mean()*100:.2f}%)")

# Confirm that missing voice rows have NaN features in raw data (not zero distress)
missing_check = train_df[train_df["Voice_Available"] == 0]
assert missing_check["Voice_Distress"].isna().all(), "Missing voice contains non-NaN values!"
print("  PASS: Missing voice samples are represented as NaN, NOT zero distress")

# Imputers fitted strictly on TRAIN data where voice is available
core_imputer = SimpleImputer(strategy="median")
core_imputer.fit(train_df.loc[train_avail_mask, CORE_FEATURES])

all_imputer = SimpleImputer(strategy="median")
all_imputer.fit(train_df.loc[train_avail_mask, ALL_VOICE_FEATURES])
print("  Imputers fitted strictly on AVAILABLE TRAIN data only")

# Transform datasets
X_train_core = core_imputer.transform(train_df[CORE_FEATURES])
X_val_core   = core_imputer.transform(val_df[CORE_FEATURES])
X_test_core  = core_imputer.transform(test_df[CORE_FEATURES])

X_train_all  = all_imputer.transform(train_df[ALL_VOICE_FEATURES])
X_val_all    = all_imputer.transform(val_df[ALL_VOICE_FEATURES])
X_test_all   = all_imputer.transform(test_df[ALL_VOICE_FEATURES])

y_train = train_df[TARGET].values
y_val   = val_df[TARGET].values
y_test  = test_df[TARGET].values

# ===========================================================================
# 5. MODEL TRAINING
# ===========================================================================
print("\n--- Training Voice DDS Models ---")

# Model 1: Core 5 Ridge Regressor (Canonical Voice Specialist)
ridge_core = Ridge(alpha=1.0, random_state=SEED)
ridge_core.fit(X_train_core[train_avail_mask], y_train[train_avail_mask])
print("  Trained: Ridge Regressor (Canonical Voice Specialist - Core 5)")

# Model 2: Core 5 XGBoost Regressor (Nonlinear Baseline)
xgb_core = xgb.XGBRegressor(
    objective="reg:squarederror",
    n_estimators=100,
    learning_rate=0.05,
    max_depth=4,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=SEED,
    n_jobs=-1,
)
xgb_core.fit(X_train_core[train_avail_mask], y_train[train_avail_mask])
print("  Trained: XGBoost Regressor (Nonlinear Baseline - Core 5)")

# Model 3: All 9 Voice Features XGBoost Regressor (Diagnostic Ablation)
xgb_all = xgb.XGBRegressor(
    objective="reg:squarederror",
    n_estimators=100,
    learning_rate=0.05,
    max_depth=4,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=SEED,
    n_jobs=-1,
)
xgb_all.fit(X_train_all[train_avail_mask], y_train[train_avail_mask])
print("  Trained: XGBoost Regressor (Diagnostic Ablation - All 9)")

# ===========================================================================
# 6. EVALUATION FUNCTIONS
# ===========================================================================
train_mean_avail = float(np.mean(y_train[train_avail_mask]))

def evaluate_metrics(y_true, y_pred):
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))
    pr, _ = pearsonr(y_true, y_pred)
    sr, _ = spearmanr(y_true, y_pred)

    base_preds = np.full_like(y_true, train_mean_avail)
    base_mae = float(mean_absolute_error(y_true, base_preds))
    base_rmse = float(np.sqrt(mean_squared_error(y_true, base_preds)))
    base_r2 = float(r2_score(y_true, base_preds))

    return {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "Pearson": round(float(pr), 4),
        "Spearman": round(float(sr), 4),
        "mean_actual": round(float(np.mean(y_true)), 2),
        "std_actual": round(float(np.std(y_true)), 2),
        "mean_pred": round(float(np.mean(y_pred)), 2),
        "std_pred": round(float(np.std(y_pred)), 2),
        "baseline_MAE": round(base_mae, 4),
        "baseline_RMSE": round(base_rmse, 4),
        "baseline_R2": round(base_r2, 4),
        "mae_improvement_pct": round((1.0 - mae / base_mae) * 100, 2),
    }

print("\n" + "=" * 60)
print("EVALUATION RESULTS -- PRIMARY: AVAILABLE VOICE ROWS (Voice_Available == 1)")
print("=" * 60)

splits_data = {
    "train": (y_train[train_avail_mask], X_train_core[train_avail_mask], X_train_all[train_avail_mask]),
    "validation": (y_val[val_avail_mask], X_val_core[val_avail_mask], X_val_all[val_avail_mask]),
    "test": (y_test[test_avail_mask], X_test_core[test_avail_mask], X_test_all[test_avail_mask]),
}

eval_results = {
    "ridge_core5": {},
    "xgb_core5": {},
    "xgb_all9": {},
}

for split_name, (y_true, X_c, X_a) in splits_data.items():
    p_ridge = ridge_core.predict(X_c)
    p_xgb_c = xgb_core.predict(X_c)
    p_xgb_a = xgb_all.predict(X_a)

    eval_results["ridge_core5"][split_name] = evaluate_metrics(y_true, p_ridge)
    eval_results["xgb_core5"][split_name] = evaluate_metrics(y_true, p_xgb_c)
    eval_results["xgb_all9"][split_name] = evaluate_metrics(y_true, p_xgb_a)

    print(f"\n--- [{split_name.upper()} SET] n={len(y_true)} ---")
    for mname, res in [("Ridge (Core 5) - Canonical", eval_results["ridge_core5"][split_name]),
                       ("XGBoost (Core 5)", eval_results["xgb_core5"][split_name]),
                       ("XGBoost (All 9) - Diagnostic", eval_results["xgb_all9"][split_name])]:
        print(f"  {mname:<30s} | MAE={res['MAE']:6.4f} | RMSE={res['RMSE']:6.4f} | R2={res['R2']:6.4f} | Pearson={res['Pearson']:6.4f} | Spearman={res['Spearman']:6.4f} | MAE Imprv=+{res['mae_improvement_pct']}%")

# ===========================================================================
# 7. FEATURE IMPORTANCE & COEFFICIENTS
# ===========================================================================
print("\n--- Model Coefficients & Feature Importance ---")

# Ridge Coefficients
ridge_coefs = pd.DataFrame({
    "feature": CORE_FEATURES,
    "coefficient": ridge_core.coef_,
}).sort_values("coefficient", ascending=False).reset_index(drop=True)
print("\nRidge Coefficients (Core 5):")
print(f"  Intercept: {ridge_core.intercept_:.4f}")
for _, row in ridge_coefs.iterrows():
    print(f"  {row['feature']:<25s}: {row['coefficient']:.4f}")

# XGBoost Core 5 Importance
xgb_core_imp = pd.DataFrame({
    "feature": CORE_FEATURES,
    "gain_importance": xgb_core.feature_importances_,
}).sort_values("gain_importance", ascending=False).reset_index(drop=True)
print("\nXGBoost Core 5 Feature Importance:")
for _, row in xgb_core_imp.iterrows():
    print(f"  {row['feature']:<25s}: {row['gain_importance']:.4f}")

# XGBoost All 9 Importance
xgb_all_imp = pd.DataFrame({
    "feature": ALL_VOICE_FEATURES,
    "gain_importance": xgb_all.feature_importances_,
}).sort_values("gain_importance", ascending=False).reset_index(drop=True)
print("\nXGBoost All 9 Feature Importance:")
for _, row in xgb_all_imp.iterrows():
    print(f"  {row['feature']:<25s}: {row['gain_importance']:.4f}")

# ===========================================================================
# 8. GENERATE & SAVE PREDICTION ARTIFACTS
# ===========================================================================
print("\n--- Generating and Saving Predictions ---")

def generate_prediction_df(orig_df, X_c, X_a):
    preds_ridge = ridge_core.predict(X_c)
    preds_xgb_c = xgb_core.predict(X_c)
    preds_xgb_a = xgb_all.predict(X_a)

    is_avail = (orig_df["Voice_Available"] == 1).values

    # Clean predictions: when Voice_Available == 0, predicted voice distress is NaN
    clean_ridge = np.where(is_avail, np.round(preds_ridge, 4), np.nan)
    clean_xgb_c = np.where(is_avail, np.round(preds_xgb_c, 4), np.nan)
    clean_xgb_a = np.where(is_avail, np.round(preds_xgb_a, 4), np.nan)

    pred_df = pd.DataFrame({
        "Victim_ID": orig_df["Victim_ID"].values,
        "Timepoint": orig_df["Timepoint"].values,
        "Split": orig_df["Split"].values,
        "Voice_Available": orig_df["Voice_Available"].values,
        "DDS_actual": orig_df["DDS"].values,
        "pred_voice_dds_ridge_core5": clean_ridge,
        "pred_voice_dds_xgb_core5": clean_xgb_c,
        "pred_voice_dds_xgb_all9": clean_xgb_a,
        # Imputed full predictions for downstream pipeline compatibility
        "pred_voice_dds_imputed_full": np.round(preds_ridge, 4),
    })
    return pred_df

test_pred_df = generate_prediction_df(test_df, X_test_core, X_test_all)
val_pred_df  = generate_prediction_df(val_df, X_val_core, X_val_all)

for out_dir in OUTPUT_DIRS:
    test_pred_path = os.path.join(out_dir, "test_voice_dds_predictions.csv")
    val_pred_path  = os.path.join(out_dir, "val_voice_dds_predictions.csv")
    test_pred_df.to_csv(test_pred_path, index=False)
    val_pred_df.to_csv(val_pred_path, index=False)
    print(f"  Saved predictions to: {test_pred_path}")

# ===========================================================================
# 9. SAVE MODELS & METADATA
# ===========================================================================
print("\n--- Saving Model Artifacts & Metrics ---")

for m_dir in MODEL_DIRS:
    # Save Ridge Core 5 (Canonical)
    with open(os.path.join(m_dir, "v2_voice_dds_ridge_core5.pkl"), "wb") as f:
        pickle.dump(ridge_core, f)

    # Save XGBoost Core 5
    xgb_core.save_model(os.path.join(m_dir, "v2_voice_dds_xgb_core5.json"))

    # Save XGBoost All 9 (Diagnostic Ablation)
    xgb_all.save_model(os.path.join(m_dir, "v2_voice_dds_xgb_all9.json"))

    # Save Imputer
    with open(os.path.join(m_dir, "v2_voice_dds_preprocessor.pkl"), "wb") as f:
        pickle.dump(core_imputer, f)

    # Save Features metadata
    with open(os.path.join(m_dir, "v2_voice_dds_features.json"), "w") as f:
        json.dump({
            "specialist": "voice_dds",
            "canonical_model": "ridge_core5",
            "core_features_count": len(CORE_FEATURES),
            "core_features": CORE_FEATURES,
            "all_features_count": len(ALL_VOICE_FEATURES),
            "all_features": ALL_VOICE_FEATURES,
            "target": TARGET,
            "missing_voice_policy": "Preserved as NaN when Voice_Available == 0; evaluated on available voice observations only",
        }, f, indent=2)

    # Save Metrics
    with open(os.path.join(m_dir, "v2_voice_dds_metrics.json"), "w") as f:
        json.dump({
            "specialist": "voice_dds",
            "canonical_model": "ridge_core5",
            "created_at": datetime.now().isoformat(),
            "authoritative_split": "engine/data/processed/v2_victim_split.csv",
            "feature_policy": "engine/v2/v2_feature_policy.py",
            "models_evaluated": {
                "ridge_core5": eval_results["ridge_core5"],
                "xgb_core5": eval_results["xgb_core5"],
                "xgb_all9": eval_results["xgb_all9"],
            },
            "ridge_coefficients": {
                "intercept": round(float(ridge_core.intercept_), 4),
                "weights": {k: round(float(v), 4) for k, v in zip(CORE_FEATURES, ridge_core.coef_)},
            }
        }, f, indent=2)

    # Save Importances
    xgb_core_imp.to_csv(os.path.join(m_dir, "v2_voice_dds_importance.csv"), index=False)

print("\n" + "=" * 60)
print("STEP 7 COMPLETE -- Voice DDS Specialist Trained & Saved")
print("=" * 60)
