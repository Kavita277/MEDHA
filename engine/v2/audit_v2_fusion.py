import os
import sys
import json
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
import xgboost as xgb
from pathlib import Path

# Paths
ENGINE_DIR = Path(r"c:\Users\jnark\Documents\MEDHA\MEDHA\engine")
V2_DIR = ENGINE_DIR / "v2"
MODELS_DIR = ENGINE_DIR / "models" / "v2" / "fusion"
OUTPUTS_DIR = ENGINE_DIR / "outputs" / "dds_v2" / "fusion"
DATA_DIR = ENGINE_DIR / "data" / "processed"

sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(V2_DIR))

# ===========================================================================
# 1. REPRODUCIBILITY AUDIT
# ===========================================================================
print("=== 1. REPRODUCIBILITY AUDIT ===")

# Load saved test predictions
test_preds_df = pd.read_csv(OUTPUTS_DIR / "test_fusion_dds_predictions.csv")

# Load model and config
with open(MODELS_DIR / "v2_fusion_feature_config.json") as f:
    feature_config = json.load(f)

with open(MODELS_DIR / "v2_fusion_metadata.json") as f:
    metadata = json.load(f)

selected_model_name = metadata["selected_model"]
print(f"Selected model from metadata: {selected_model_name}")

feature_order = feature_config["feature_order"]

# Load XGBoost model
xgb_model = xgb.XGBRegressor()
xgb_model.load_model(MODELS_DIR / "v2_fusion_xgb.json")

# Re-predict using the features from the CSV
X_test = test_preds_df[feature_order].fillna(0.0).values
re_preds = np.clip(xgb_model.predict(X_test), 0, 100)

# Compare with saved predictions
saved_preds = test_preds_df["Fusion_DDS_Prediction"].values
max_diff = np.max(np.abs(re_preds - saved_preds))
print(f"Max difference between re-prediction and saved prediction: {max_diff:.6f}")
assert max_diff < 1e-4, "Reproducibility failed: Re-predictions do not match saved predictions!"
print("Reproducibility Audit: PASS")


# ===========================================================================
# 2. LEAKAGE AUDIT
# ===========================================================================
print("\n=== 2. LEAKAGE AUDIT ===")

forbidden_features = [
    "Actual_DDS",
    "Future_Escalation_Label",
    "Previous_DDS",
    "Rolling_DDS_Mean",
    "Rolling_DDS_SD",
    "DDS_Slope",
    "Recent_Change_Rate",
    "Recent_Max_DDS",
    "Recent_Min_DDS",
    "Delta_DDS",
    "DDS_Deviation_From_Baseline",
    "Baseline_DDS",
    "Trajectory_State",
    "Intervention",
    "Follow_Up"
]

leakage_found = False
for f in feature_order:
    if f in forbidden_features:
        print(f"LEAKAGE DETECTED: Forbidden feature '{f}' found in feature_order!")
        leakage_found = True

assert not leakage_found, "Leakage Audit Failed: Forbidden features found!"
print("Leakage Audit: PASS")


# ===========================================================================
# 3. SPLIT AUDIT
# ===========================================================================
print("\n=== 3. SPLIT AUDIT ===")

val_preds_df = pd.read_csv(OUTPUTS_DIR / "val_fusion_dds_predictions.csv")
train_fusion_df = pd.read_csv(DATA_DIR / "v2_victim_split.csv") # Used for victim count validation

train_vids = set(train_fusion_df[train_fusion_df["Split"] == "train"]["Victim_ID"])
val_vids = set(train_fusion_df[train_fusion_df["Split"] == "validation"]["Victim_ID"])
test_vids = set(train_fusion_df[train_fusion_df["Split"] == "test"]["Victim_ID"])

print(f"Authoritative Splits - Train: {len(train_vids)}, Val: {len(val_vids)}, Test: {len(test_vids)}")

assert len(train_vids) == 700
assert len(val_vids) == 150
assert len(test_vids) == 150
assert len(train_vids & val_vids) == 0
assert len(train_vids & test_vids) == 0
assert len(val_vids & test_vids) == 0

# Check that predictions belong to correct split
test_pred_vids = set(test_preds_df["Victim_ID"])
val_pred_vids = set(val_preds_df["Victim_ID"])

assert test_pred_vids.issubset(test_vids), "Test predictions contain non-test victims!"
assert test_pred_vids == test_vids, "Test predictions missing some test victims!"

assert val_pred_vids.issubset(val_vids), "Val predictions contain non-val victims!"
assert val_pred_vids == val_vids, "Val predictions missing some val victims!"

print("Split Audit: PASS")

# ===========================================================================
# 4. ALIGNMENT AUDIT
# ===========================================================================
print("\n=== 4. ALIGNMENT AUDIT ===")

# Check for duplicates
duplicates = test_preds_df.duplicated(subset=["Victim_ID", "Timepoint"])
print(f"Duplicate (Victim_ID, Timepoint) rows in test predictions: {duplicates.sum()}")
assert duplicates.sum() == 0, "Duplicate rows found!"

# Count rows
print(f"Total test rows: {len(test_preds_df)}")
assert len(test_preds_df) == 4500, "Expected 4500 test rows!"
print("Alignment Audit: PASS")


# ===========================================================================
# 5. PERFORMANCE AUDIT & FUSION BENEFIT ANALYSIS
# ===========================================================================
print("\n=== 5. PERFORMANCE AUDIT & BENEFIT ANALYSIS ===")
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def eval_metrics(df, pred_col, actual_col="Actual_DDS"):
    valid = df[pred_col].notna()
    if valid.sum() == 0:
        return None
    y_t = df.loc[valid, actual_col].values
    y_p = df.loc[valid, pred_col].values
    mae = mean_absolute_error(y_t, y_p)
    rmse = np.sqrt(mean_squared_error(y_t, y_p))
    r2 = r2_score(y_t, y_p)
    pearson = pearsonr(y_t, y_p)[0] if len(y_t) > 1 else np.nan
    spearman = spearmanr(y_t, y_p)[0] if len(y_t) > 1 else np.nan
    return {"MAE": mae, "RMSE": rmse, "R2": r2, "Pearson": pearson, "Spearman": spearman, "N": len(y_t)}

baseline_pred = metadata["train_mean_dds"]
test_preds_df["Baseline_Pred"] = baseline_pred

models = {
    "Fusion": "Fusion_DDS_Prediction",
    "Structured": "Struct_Pred",
    "Text": "Text_Pred",
    "Voice": "Voice_Pred",
    "Behaviour": "Behav_Pred",
    "Baseline": "Baseline_Pred"
}

def analyze_group(df, group_name):
    print(f"\nGroup: {group_name} (N={len(df)})")
    if len(df) == 0:
        return
    results = {}
    for name, col in models.items():
        res = eval_metrics(df, col)
        if res:
            results[name] = res
            print(f"  {name:10s} MAE={res['MAE']:.4f} RMSE={res['RMSE']:.4f} R2={res['R2']:.4f}")
    
    if "Fusion" in results:
        fusion_mae = results["Fusion"]["MAE"]
        struct_mae = results["Structured"]["MAE"]
        
        # Best available specialist
        spec_maes = {k: v["MAE"] for k, v in results.items() if k not in ["Fusion", "Baseline"]}
        best_spec_name = min(spec_maes, key=spec_maes.get)
        best_spec_mae = spec_maes[best_spec_name]
        
        base_mae = results["Baseline"]["MAE"]
        
        print(f"  --> Fusion vs Struct:   {struct_mae - fusion_mae:+.4f} ({(struct_mae - fusion_mae)/struct_mae*100:+.1f}%)")
        print(f"  --> Fusion vs Best ({best_spec_name[:3]}): {best_spec_mae - fusion_mae:+.4f} ({(best_spec_mae - fusion_mae)/best_spec_mae*100:+.1f}%)")
        print(f"  --> Fusion vs Baseline: {base_mae - fusion_mae:+.4f} ({(base_mae - fusion_mae)/base_mae*100:+.1f}%)")
        
        fusion_r2 = results["Fusion"]["R2"]
        struct_r2 = results["Structured"]["R2"]
        print(f"  --> R2 diff vs Struct:  {fusion_r2 - struct_r2:+.4f}")

# Full Test
analyze_group(test_preds_df, "Full Test Population")

# All modalities
all_avail = test_preds_df[(test_preds_df["Text_Available"] == 1) & (test_preds_df["Voice_Available"] == 1)]
analyze_group(all_avail, "All Modalities Available (S+T+V+B)")

# No Voice
no_voice = test_preds_df[(test_preds_df["Text_Available"] == 1) & (test_preds_df["Voice_Available"] == 0)]
analyze_group(no_voice, "Voice Missing (S+T+B)")

# No Text
no_text = test_preds_df[(test_preds_df["Text_Available"] == 0) & (test_preds_df["Voice_Available"] == 1)]
analyze_group(no_text, "Text Missing (S+V+B)")

# Neither Text nor Voice
both_miss = test_preds_df[(test_preds_df["Text_Available"] == 0) & (test_preds_df["Voice_Available"] == 0)]
analyze_group(both_miss, "Text + Voice Missing (S+B)")

# ===========================================================================
# 8. ERROR ANALYSIS
# ===========================================================================
print("\n=== 8. ERROR ANALYSIS ===")
test_preds_df["Residual"] = test_preds_df["Actual_DDS"] - test_preds_df["Fusion_DDS_Prediction"]
test_preds_df["AbsError"] = test_preds_df["Residual"].abs()

print(f"Mean Error (Bias): {test_preds_df['Residual'].mean():.4f}")

# DDS Ranges
test_preds_df["DDS_Bin"] = pd.cut(test_preds_df["Actual_DDS"], bins=[0, 25, 50, 75, 100], labels=["0-25", "25-50", "50-75", "75-100"])
bin_errors = test_preds_df.groupby("DDS_Bin", observed=False)["AbsError"].mean()
bin_bias = test_preds_df.groupby("DDS_Bin", observed=False)["Residual"].mean()

print("\nErrors by DDS Range:")
for b in bin_errors.index:
    print(f"  {b}: MAE = {bin_errors[b]:.4f}, Mean Bias = {bin_bias[b]:.4f} (pos=underpredict)")

# High Error cases
high_error = test_preds_df[test_preds_df["AbsError"] > 20]
print(f"\nHighly inaccurate predictions (>20 points error): {len(high_error)} ({len(high_error)/len(test_preds_df)*100:.1f}%)")

print("\nAudit Script Complete.")
