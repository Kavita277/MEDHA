"""
MEDHA V2 Step 5 -- Structured DDS Regressor Training Script (Clean Structured Specialist)

Trains an XGBoost regression model to predict current-timepoint DDS
using the 42 approved Structured specialist features (excluding Text and Voice)
with victim-level train/val/test split.

Usage:
    python engine/v2/train_v2_structured_dds.py
"""

import os
import sys
import json
import pickle
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
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
    from engine.v2.v2_feature_policy import (
        validate_dds_features,
        validate_structured_specialist_features,
        get_all_approved_structured_dds_features,
        V2_DDS_APPROVED_FEATURES,
        V2_STRUCTURED_DDS_FEATURES,
        V2_TEXT_DDS_FEATURES,
        V2_VOICE_DDS_FEATURES,
        V2_DDS_EXCLUDED_FEATURES,
        V2_DDS_QUARANTINED_FEATURES,
        V2_DDS_TARGET_FEATURES,
        V2_DDS_ID_METADATA_FEATURES,
        V2_DDS_POST_HOC_FEATURES,
    )
except ImportError:
    from v2_feature_policy import (
        validate_dds_features,
        validate_structured_specialist_features,
        get_all_approved_structured_dds_features,
        V2_DDS_APPROVED_FEATURES,
        V2_STRUCTURED_DDS_FEATURES,
        V2_TEXT_DDS_FEATURES,
        V2_VOICE_DDS_FEATURES,
        V2_DDS_EXCLUDED_FEATURES,
        V2_DDS_QUARANTINED_FEATURES,
        V2_DDS_TARGET_FEATURES,
        V2_DDS_ID_METADATA_FEATURES,
        V2_DDS_POST_HOC_FEATURES,
    )

SPLIT_CSV    = os.path.join(ENGINE_DIR, "data", "processed", "v2_victim_split.csv")
LONG_CSV     = os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv")
SPLIT_CONFIG = os.path.join(ENGINE_DIR, "data", "processed", "v2_split_config.json")
MODEL_DIR    = os.path.join(ENGINE_DIR, "models", "v2")

SEED = 42
TARGET = "DDS"

# ===========================================================================
# 1.  LOAD DATA
# ===========================================================================
print("=" * 60)
print("MEDHA V2 Step 5 -- Clean Structured DDS Regressor")
print("=" * 60)

df = pd.read_csv(LONG_CSV)
split_df = pd.read_csv(SPLIT_CSV)
print(f"\nLoaded longitudinal dataset: {len(df)} rows, {df['Victim_ID'].nunique()} victims")
print(f"Loaded victim split: {len(split_df)} rows")

# ===========================================================================
# 2.  VERIFY SPLIT INTEGRITY
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
assert len(train_df) == 21000
assert len(val_df)   == 4500
assert len(test_df)  == 4500

# ===========================================================================
# 3.  STRUCTURED SPECIALIST FEATURE SELECTION & STRICT BOUNDARY VALIDATION
# ===========================================================================
print("\n--- Structured Specialist Boundary Validation ---")
# 1. Obtain approved Structured specialist features (42 features)
FEATURES = get_all_approved_structured_dds_features()
print(f"  Structured feature candidate count: {len(FEATURES)}")

# 2. Strict validation: hard-fails on Text, Voice, Banned, Target, Metadata, Quarantined, Unknown, Duplicates
validate_structured_specialist_features(FEATURES)
print(f"  PASS: Strict specialist validation passed ({len(FEATURES)} approved structured features)")

# 3. Confirm all features exist in dataset
missing_cols = [f for f in FEATURES if f not in df.columns]
assert len(missing_cols) == 0, f"Missing columns in dataset: {missing_cols}"
print("  PASS: All 42 structured features present in dataset")

# 4. Confirm NO Text or Voice features are in FEATURES
text_overlap = set(FEATURES) & set(V2_TEXT_DDS_FEATURES)
voice_overlap = set(FEATURES) & set(V2_VOICE_DDS_FEATURES)
assert len(text_overlap) == 0, f"Text feature leak detected: {text_overlap}"
assert len(voice_overlap) == 0, f"Voice feature leak detected: {voice_overlap}"
print("  PASS: Zero overlap with Text features (0/9)")
print("  PASS: Zero overlap with Voice features (0/9)")

# ===========================================================================
# 4.  FEATURE TYPING & PREPROCESSING
# ===========================================================================
print("\n--- Feature Types ---")
CATEGORICAL_COLS = ["Case_Type", "Case_Stage", "Episode_Severity"]
NUMERIC_COLS = [c for c in FEATURES if c not in CATEGORICAL_COLS]

print(f"  Categorical: {len(CATEGORICAL_COLS)} -> {CATEGORICAL_COLS}")
print(f"  Numeric:     {len(NUMERIC_COLS)}")
assert len(CATEGORICAL_COLS) + len(NUMERIC_COLS) == len(FEATURES) == 42

print("\n--- Building Preprocessing Pipeline ---")
num_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
])

cat_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="constant", fill_value="MISSING")),
    ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", num_transformer, NUMERIC_COLS),
        ("cat", cat_transformer, CATEGORICAL_COLS),
    ],
    remainder="drop"
)

# FIT PREPROCESSOR ON TRAIN DATA ONLY
preprocessor.fit(train_df[FEATURES])
print("  Preprocessor fitted on TRAIN data only")

# Transform splits
X_train = preprocessor.transform(train_df[FEATURES])
y_train = train_df[TARGET].values

X_val = preprocessor.transform(val_df[FEATURES])
y_val = val_df[TARGET].values

X_test = preprocessor.transform(test_df[FEATURES])
y_test = test_df[TARGET].values

print(f"  Final feature matrix shape: train={X_train.shape}, val={X_val.shape}, test={X_test.shape}")
assert X_train.shape == (21000, 42)
assert X_val.shape   == (4500, 42)
assert X_test.shape  == (4500, 42)

# ===========================================================================
# 5.  POST-PREPROCESSING LEAKAGE & PURITY AUDIT
# ===========================================================================
print("\n--- Post-Preprocessing Leakage Audit ---")
banned_all = (
    V2_DDS_EXCLUDED_FEATURES
    + V2_DDS_QUARANTINED_FEATURES
    + V2_DDS_TARGET_FEATURES
    + V2_DDS_ID_METADATA_FEATURES
    + V2_DDS_POST_HOC_FEATURES
    + V2_TEXT_DDS_FEATURES
    + V2_VOICE_DDS_FEATURES
)
banned_in_features = set(FEATURES) & set(banned_all)
assert len(banned_in_features) == 0, f"Banned columns found: {banned_in_features}"
print("  PASS: No banned, text, or voice features in feature matrix")

# ===========================================================================
# 6.  TRAIN XGBOOST REGRESSOR
# ===========================================================================
print("\n--- Training XGBoost Regressor (Structured Specialist) ---")
model = xgb.XGBRegressor(
    objective="reg:squarederror",
    n_estimators=300,
    learning_rate=0.05,
    max_depth=5,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=SEED,
    n_jobs=-1,
)

model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=False,
)
print("  Training complete.")

# ===========================================================================
# 7.  EVALUATION (ROW-LEVEL & VICTIM-LEVEL)
# ===========================================================================
print("\n--- Evaluation Results ---")

train_mean = float(np.mean(y_train))

def evaluate_predictions(y_true, y_pred, name=""):
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))
    r, _ = pearsonr(y_true, y_pred)
    pearson = float(r)

    # Baseline (predict train mean)
    base_preds = np.full_like(y_true, train_mean)
    base_mae = float(mean_absolute_error(y_true, base_preds))
    base_rmse = float(np.sqrt(mean_squared_error(y_true, base_preds)))
    base_r2 = float(r2_score(y_true, base_preds))

    return {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "Pearson": round(pearson, 4),
        "mean_actual": round(float(np.mean(y_true)), 2),
        "std_actual": round(float(np.std(y_true)), 2),
        "mean_pred": round(float(np.mean(y_pred)), 2),
        "std_pred": round(float(np.std(y_pred)), 2),
        "baseline_MAE": round(base_mae, 4),
        "baseline_RMSE": round(base_rmse, 4),
        "baseline_R2": round(base_r2, 4),
    }

train_preds = model.predict(X_train)
val_preds   = model.predict(X_val)
test_preds  = model.predict(X_test)

results = {
    "train": evaluate_predictions(y_train, train_preds, "TRAIN"),
    "validation": evaluate_predictions(y_val, val_preds, "VALIDATION"),
    "test": evaluate_predictions(y_test, test_preds, "TEST"),
}

for split_name in ["train", "validation", "test"]:
    res = results[split_name]
    print(f"\n  [{split_name.upper()}]  n={len(train_preds if split_name=='train' else val_preds if split_name=='validation' else test_preds)}")
    print(f"    Target:     mean={res['mean_actual']}, std={res['std_actual']}")
    print(f"    Prediction: mean={res['mean_pred']}, std={res['std_pred']}")
    print(f"    MAE={res['MAE']}, RMSE={res['RMSE']}, R2={res['R2']}, Pearson={res['Pearson']}")
    print(f"    Baseline:   MAE={res['baseline_MAE']}, RMSE={res['baseline_RMSE']}, R2={res['baseline_R2']}")

# Victim-level aggregation diagnostics
print("\n--- Victim-Level Diagnostics ---")
victim_results = {}
for split_name, sub_df, preds in [
    ("train", train_df, train_preds),
    ("validation", val_df, val_preds),
    ("test", test_df, test_preds)
]:
    sub_df = sub_df.copy()
    sub_df["pred"] = preds
    v_agg = sub_df.groupby("Victim_ID").agg({"DDS": "mean", "pred": "mean"}).reset_index()
    v_res = evaluate_predictions(v_agg["DDS"].values, v_agg["pred"].values, split_name)
    victim_results[split_name] = v_res
    print(f"  [{split_name.upper()}] victims={len(v_agg)}: MAE={v_res['MAE']}, RMSE={v_res['RMSE']}, R2={v_res['R2']}, Pearson={v_res['Pearson']}")

# ===========================================================================
# 8.  FEATURE IMPORTANCE (STRUCTURED SPECIALIST ONLY)
# ===========================================================================
print("\n--- Feature Importance (Top 20 by Gain) ---")
# Feature names in column order: NUMERIC_COLS + CATEGORICAL_COLS
feature_names = NUMERIC_COLS + CATEGORICAL_COLS
importances = model.feature_importances_

imp_df = pd.DataFrame({
    "feature": feature_names,
    "importance": importances,
}).sort_values("importance", ascending=False).reset_index(drop=True)

for i, row in imp_df.head(20).iterrows():
    print(f"  {i+1:2d}. {row['feature']:<36s} {row['importance']:.4f}")

# Verify no text or voice in importance
imp_features = set(imp_df["feature"])
assert len(imp_features & set(V2_TEXT_DDS_FEATURES)) == 0, "Text features found in importance!"
assert len(imp_features & set(V2_VOICE_DDS_FEATURES)) == 0, "Voice features found in importance!"
print("  PASS: Zero Text/Voice features in importance ranking")

# ===========================================================================
# 9.  SAVE ARTIFACTS
# ===========================================================================
print("\n--- Saving Artifacts ---")
os.makedirs(MODEL_DIR, exist_ok=True)

# Save XGBoost model
model_path = os.path.join(MODEL_DIR, "v2_structured_dds_xgb.json")
model.save_model(model_path)
print(f"  Model:          {model_path}")

# Save preprocessor
preproc_path = os.path.join(MODEL_DIR, "v2_structured_dds_preprocessor.pkl")
with open(preproc_path, "wb") as f:
    pickle.dump(preprocessor, f)
print(f"  Preprocessor:   {preproc_path}")

# Save feature list metadata
feat_path = os.path.join(MODEL_DIR, "v2_structured_dds_features.json")
with open(feat_path, "w") as f:
    json.dump({
        "specialist": "structured_dds",
        "feature_count": len(FEATURES),
        "features": FEATURES,
        "numeric_features": NUMERIC_COLS,
        "categorical_features": CATEGORICAL_COLS,
        "excluded_text_features": V2_TEXT_DDS_FEATURES,
        "excluded_voice_features": V2_VOICE_DDS_FEATURES,
    }, f, indent=2)
print(f"  Feature list:   {feat_path}")

# Save metrics
metrics_path = os.path.join(MODEL_DIR, "v2_structured_dds_metrics.json")
with open(metrics_path, "w") as f:
    json.dump({
        "specialist": "structured_dds",
        "feature_universe": "42 approved structured/case/context/behaviour features",
        "row_level": results,
        "victim_level": victim_results,
        "train_mean_dds": train_mean,
        "model_config": {
            "objective": "reg:squarederror",
            "n_estimators": 300,
            "learning_rate": 0.05,
            "max_depth": 5,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": SEED,
        },
        "preprocessing": {
            "numeric_imputer": "median (train-fitted)",
            "categorical_imputer": "constant='MISSING'",
            "categorical_encoder": "OrdinalEncoder (unknown=-1)",
        },
        "split_reference": "engine/data/processed/v2_victim_split.csv",
        "feature_policy": "engine/v2/v2_feature_policy.py",
        "created_at": datetime.now().isoformat(),
    }, f, indent=2)
print(f"  Metrics:        {metrics_path}")

# Save importance
imp_path = os.path.join(MODEL_DIR, "v2_structured_dds_importance.csv")
imp_df.to_csv(imp_path, index=False)
print(f"  Importance:     {imp_path}")

print("\n" + "=" * 60)
print("STEP 5 COMPLETE -- Clean Structured DDS Regressor Trained (42 Features)")
print("=" * 60)
