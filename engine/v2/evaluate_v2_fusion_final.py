"""
MEDHA V2 Step 10C -- Locked Final Fusion Evaluation and Audit
============================================================

Performs the final unbiased evaluation and audit of the frozen Step 10B
Candidate C (XGBoost Stacking Regressor) model on the untouched 4,500-row
Test set.

Strict Audit Constraints:
- NO retraining, hyperparameter tuning, model modification, or reselection.
- The model is loaded directly from the Step 10B frozen artifact:
  engine/models/v2/fusion_oof/fusion_model.json
- Canonical specialist predictions for the 150 test victims are merged.
- Deterministic inference is verified via repeated evaluation.
- All evaluation tables (Primary, Availability, Error, Victim-Level) are generated.

Usage:
    python engine/v2/evaluate_v2_fusion_final.py
"""

import os
import sys
import json
import shutil
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
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

from engine.v2.v2_fusion import (
    validate_fusion_features,
    V2_FUSION_APPROVED_FEATURES,
    V2_FUSION_AVAILABILITY_FLAGS,
    V2_FUSION_FORBIDDEN_FEATURES,
)

SPLIT_CSV = os.path.join(ENGINE_DIR, "data", "processed", "v2_victim_split.csv")
LONG_CSV  = os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv")
PRED_DIR  = os.path.join(ENGINE_DIR, "outputs", "dds_v2")

FROZEN_MODEL_DIR = os.path.join(ENGINE_DIR, "models", "v2", "fusion_oof")
FINAL_OUT_DIRS = [
    os.path.join(ENGINE_DIR, "outputs", "dds_v2", "fusion_final"),
    os.path.join(ROOT_DIR, "outputs", "dds_v2", "fusion_final"),
]
FINAL_MOD_DIRS = [
    os.path.join(ENGINE_DIR, "models", "v2", "fusion_final"),
    os.path.join(ROOT_DIR, "models", "v2", "fusion_final"),
]

for d in FINAL_OUT_DIRS + FINAL_MOD_DIRS:
    os.makedirs(d, exist_ok=True)

KEYS = ["Victim_ID", "Timepoint"]

TEST_SPECIALIST_CONFIGS = {
    "structured": {
        "test_csv": os.path.join(PRED_DIR, "structured", "test_structured_dds_predictions.csv"),
        "pred_col": "Predicted_DDS_Structured_XGB",
        "out_col": "Struct_Pred",
        "actual_col": "Actual_DDS",
        "avail_col": None,
    },
    "text": {
        "test_csv": os.path.join(PRED_DIR, "text", "test_text_dds_predictions.csv"),
        "pred_col": "pred_text_dds_ridge_core5",
        "out_col": "Text_Pred",
        "actual_col": "DDS_actual",
        "avail_col": "Text_Available",
    },
    "voice": {
        "test_csv": os.path.join(PRED_DIR, "voice", "test_voice_dds_predictions.csv"),
        "pred_col": "pred_voice_dds_ridge_core5",
        "out_col": "Voice_Pred",
        "actual_col": "DDS_actual",
        "avail_col": "Voice_Available",
    },
    "behaviour": {
        "test_csv": os.path.join(PRED_DIR, "behaviour", "test_behaviour_dds_predictions.csv"),
        "pred_col": "Predicted_DDS_Ridge",
        "out_col": "Behav_Pred",
        "actual_col": "Actual_DDS",
        "avail_col": None,
    },
}


# ===========================================================================
# Metrics Helper
# ===========================================================================
def evaluate_predictions(y_true, y_pred, model_name=""):
    """Compute standard regression metrics."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    pr, _ = pearsonr(y_true, y_pred)
    sr, _ = spearmanr(y_true, y_pred)
    return {
        "Model": model_name,
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "Pearson": round(pr, 4),
        "Spearman": round(sr, 4),
        "N": int(len(y_true)),
    }


# ===========================================================================
# Main Evaluation Pipeline
# ===========================================================================
def main():
    print("=" * 80)
    print("MEDHA V2 — STEP 10C: LOCKED FINAL FUSION EVALUATION & AUDIT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    # -----------------------------------------------------------------------
    # 1. Authoritative Data Split Verification
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("AUDIT 1: AUTHORITATIVE DATA SPLIT & TEST INTEGRITY")
    print("=" * 70)

    split_df = pd.read_csv(SPLIT_CSV)
    train_vids = set(split_df[split_df["Split"].str.lower() == "train"]["Victim_ID"])
    val_vids   = set(split_df[split_df["Split"].str.lower() == "validation"]["Victim_ID"])
    test_vids  = set(split_df[split_df["Split"].str.lower() == "test"]["Victim_ID"])

    assert len(train_vids) == 700, f"Train victims mismatch: {len(train_vids)}"
    assert len(val_vids) == 150, f"Val victims mismatch: {len(val_vids)}"
    assert len(test_vids) == 150, f"Test victims mismatch: {len(test_vids)}"
    assert len(train_vids & test_vids) == 0, "FATAL: Train/Test victim overlap!"
    assert len(val_vids & test_vids) == 0, "FATAL: Val/Test victim overlap!"
    assert len(train_vids & val_vids) == 0, "FATAL: Train/Val victim overlap!"
    assert len(train_vids | val_vids | test_vids) == 1000, "Split does not cover exactly 1,000 victims!"
    print("  PASS: Victim split verified (700 Train / 150 Val / 150 Test, zero overlap).")

    long_df = pd.read_csv(LONG_CSV)
    test_long_df = long_df[long_df["Victim_ID"].isin(test_vids)].copy().reset_index(drop=True)
    assert len(test_long_df) == 4500, f"Test rows mismatch: {len(test_long_df)}"
    v_counts = test_long_df.groupby("Victim_ID").size()
    assert (v_counts == 30).all(), "Some test victims do not have exactly 30 timepoints!"
    assert not test_long_df.duplicated(subset=KEYS).any(), "Duplicate keys in longitudinal test set!"
    print("  PASS: 4,500 Test rows, exactly 30 timepoints per test victim, zero duplicate keys.")

    # -----------------------------------------------------------------------
    # 2. Model Loading & Feature Order Audit
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("AUDIT 2: FROZEN FUSION MODEL & FEATURE CONFIG AUDIT")
    print("=" * 70)

    model_path = os.path.join(FROZEN_MODEL_DIR, "fusion_model.json")
    feat_config_path = os.path.join(FROZEN_MODEL_DIR, "fusion_feature_config.json")
    meta_path = os.path.join(FROZEN_MODEL_DIR, "fusion_oof_metadata.json")
    selected_path = os.path.join(FROZEN_MODEL_DIR, "fusion_selected_model.json")

    assert os.path.exists(model_path), f"Missing frozen model: {model_path}"
    assert os.path.exists(feat_config_path), f"Missing feature config: {feat_config_path}"
    assert os.path.exists(selected_path), f"Missing selection metadata: {selected_path}"

    with open(selected_path) as f:
        selected_info = json.load(f)
    print(f"  Selected model: {selected_info['selected_candidate']}")
    print(f"  Selection metric: {selected_info['selection_metric']}")
    print(f"  Validation MAE: {selected_info['validation_performance']['MAE']}")
    assert selected_info["selected_candidate"] == "C_XGBoost"
    assert selected_info["validation_performance"]["MAE"] == 5.8851
    print("  PASS: Confirmed frozen model is Candidate C (XGBoost) selected strictly on Validation MAE (5.8851).")

    with open(feat_config_path) as f:
        feat_config = json.load(f)
    feature_order = feat_config["feature_order"]
    validate_fusion_features(feature_order)
    print(f"  Feature order ({len(feature_order)} features): {feature_order}")
    assert feature_order == [
        "Struct_Pred", "Text_Pred", "Voice_Pred", "Behav_Pred",
        "Struct_Available", "Text_Available", "Voice_Available", "Behav_Available"
    ]
    print("  PASS: Feature order confirmed and zero forbidden features present.")

    # Load XGBoost Regressor
    fusion_model = xgb.XGBRegressor()
    fusion_model.load_model(model_path)
    print("  PASS: Frozen XGBoost model loaded successfully.")

    # -----------------------------------------------------------------------
    # 3. Assemble Canonical Test Specialist Predictions
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("AUDIT 3: ASSEMBLE TEST PREDICTIONS FROM CANONICAL SPECIALISTS")
    print("=" * 70)

    cfg_struct = TEST_SPECIALIST_CONFIGS["structured"]
    struct_test_df = pd.read_csv(cfg_struct["test_csv"])
    merged_test = struct_test_df[KEYS + [cfg_struct["actual_col"], cfg_struct["pred_col"]]].copy()
    merged_test.rename(columns={
        cfg_struct["actual_col"]: "Actual_DDS",
        cfg_struct["pred_col"]: "Struct_Pred"
    }, inplace=True)
    merged_test["Struct_Available"] = 1

    # Text
    cfg_text = TEST_SPECIALIST_CONFIGS["text"]
    text_test_df = pd.read_csv(cfg_text["test_csv"])
    merged_test = merged_test.merge(
        text_test_df[KEYS + [cfg_text["pred_col"], cfg_text["avail_col"]]].rename(
            columns={cfg_text["pred_col"]: "Text_Pred", cfg_text["avail_col"]: "Text_Available"}
        ),
        on=KEYS, how="left"
    )
    # Mask unavailable text to NaN
    merged_test.loc[merged_test["Text_Available"] == 0, "Text_Pred"] = np.nan

    # Voice
    cfg_voice = TEST_SPECIALIST_CONFIGS["voice"]
    voice_test_df = pd.read_csv(cfg_voice["test_csv"])
    merged_test = merged_test.merge(
        voice_test_df[KEYS + [cfg_voice["pred_col"], cfg_voice["avail_col"]]].rename(
            columns={cfg_voice["pred_col"]: "Voice_Pred", cfg_voice["avail_col"]: "Voice_Available"}
        ),
        on=KEYS, how="left"
    )
    # Mask unavailable voice to NaN
    merged_test.loc[merged_test["Voice_Available"] == 0, "Voice_Pred"] = np.nan

    # Behaviour
    cfg_behav = TEST_SPECIALIST_CONFIGS["behaviour"]
    behav_test_df = pd.read_csv(cfg_behav["test_csv"])
    merged_test = merged_test.merge(
        behav_test_df[KEYS + [cfg_behav["pred_col"]]].rename(
            columns={cfg_behav["pred_col"]: "Behav_Pred"}
        ),
        on=KEYS, how="left"
    )
    merged_test["Behav_Available"] = 1

    assert len(merged_test) == 4500
    assert merged_test["Victim_ID"].nunique() == 150
    assert not merged_test.duplicated(subset=KEYS).any()
    print("  PASS: All 4 canonical specialists successfully merged for 4,500 Test rows.")

    # -----------------------------------------------------------------------
    # 4. Input Matrix Construction & Reproducibility Verification
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("AUDIT 4: INPUT MATRIX & DETERMINISTIC INFERENCE")
    print("=" * 70)

    # Missing predictions are set to 0.0 with availability flag = 0
    X_test_df = merged_test[feature_order].copy()
    for col in V2_FUSION_APPROVED_FEATURES:
        X_test_df[col] = X_test_df[col].fillna(0.0)
    X_test = X_test_df.values
    y_test = merged_test["Actual_DDS"].values

    assert X_test.shape == (4500, 8), f"X_test shape mismatch: {X_test.shape}"

    # Inference Run 1
    preds_run1 = np.clip(fusion_model.predict(X_test), 0.0, 100.0)
    # Inference Run 2 (verify determinism)
    preds_run2 = np.clip(fusion_model.predict(X_test), 0.0, 100.0)

    diff = np.max(np.abs(preds_run1 - preds_run2))
    print(f"  Maximum prediction difference between repeated runs: {diff:.10f}")
    assert diff == 0.0, f"Inference is non-deterministic! Max diff: {diff}"
    print("  PASS: Deterministic inference verified (diff = 0.0).")

    merged_test["Fusion_DDS_Prediction"] = preds_run1

    # Reproducibility audit record
    reproducibility_record = {
        "status": "DETERMINISTIC",
        "max_run_difference": float(diff),
        "test_rows": len(merged_test),
        "test_victims": int(merged_test["Victim_ID"].nunique()),
        "model_file": model_path,
        "timestamp": datetime.now().isoformat(),
    }
    for d in FINAL_OUT_DIRS:
        with open(os.path.join(d, "fusion_final_reproducibility.json"), "w") as f:
            json.dump(reproducibility_record, f, indent=2)

    # -----------------------------------------------------------------------
    # 5. Final Test Evaluation: Specialists vs Fusion
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("AUDIT 5: FINAL TEST PERFORMANCE — SPECIALISTS vs FROZEN FUSION")
    print("=" * 70)

    # Baseline: Train-mean dummy
    with open(meta_path) as f:
        oof_meta = json.load(f)
    train_mean_dds = 49.9928  # from train split Actual_DDS
    baseline_preds = np.full_like(y_test, train_mean_dds)

    res_baseline = evaluate_predictions(y_test, baseline_preds, "Train-Mean Baseline")
    res_struct = evaluate_predictions(y_test, merged_test["Struct_Pred"].values, "Structured Specialist (XGBoost)")
    
    # Text on available
    text_mask = merged_test["Text_Available"] == 1
    res_text = evaluate_predictions(
        merged_test.loc[text_mask, "Actual_DDS"].values,
        merged_test.loc[text_mask, "Text_Pred"].values,
        "Text Specialist (Ridge Core-5)"
    )
    
    # Voice on available
    voice_mask = merged_test["Voice_Available"] == 1
    res_voice = evaluate_predictions(
        merged_test.loc[voice_mask, "Actual_DDS"].values,
        merged_test.loc[voice_mask, "Voice_Pred"].values,
        "Voice Specialist (Ridge Core-5)"
    )

    res_behav = evaluate_predictions(y_test, merged_test["Behav_Pred"].values, "Behaviour Specialist (Ridge Ext-10)")
    res_fusion = evaluate_predictions(y_test, preds_run1, "MEDHA V2 Frozen Fusion (Candidate C)")

    primary_comparison = [
        res_baseline,
        res_struct,
        res_text,
        res_voice,
        res_behav,
        res_fusion,
    ]
    comp_df = pd.DataFrame(primary_comparison)
    print(comp_df.to_string(index=False))

    # Calculate improvements
    fusion_mae = res_fusion["MAE"]
    struct_mae = res_struct["MAE"]
    baseline_mae = res_baseline["MAE"]
    best_spec_mae = min(struct_mae, res_text["MAE"], res_voice["MAE"], res_behav["MAE"])

    imp_over_struct = (struct_mae - fusion_mae) / struct_mae * 100.0
    imp_over_best = (best_spec_mae - fusion_mae) / best_spec_mae * 100.0
    imp_over_baseline = (baseline_mae - fusion_mae) / baseline_mae * 100.0

    print(f"\n  Fusion Improvement over Structured Specialist: {imp_over_struct:+.2f}% ({struct_mae:.4f} -> {fusion_mae:.4f})")
    print(f"  Fusion Improvement over Best Individual Specialist: {imp_over_best:+.2f}% ({best_spec_mae:.4f} -> {fusion_mae:.4f})")
    print(f"  Fusion Improvement over Train-Mean Baseline:        {imp_over_baseline:+.2f}% ({baseline_mae:.4f} -> {fusion_mae:.4f})")

    # Save metrics table
    for d in FINAL_OUT_DIRS:
        comp_df.to_csv(os.path.join(d, "fusion_final_test_metrics.csv"), index=False)

    # -----------------------------------------------------------------------
    # 6. Availability Stratification Evaluation
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("AUDIT 6: AVAILABILITY STRATIFICATION EVALUATION")
    print("=" * 70)

    # Mutually exclusive and exhaustive strata
    strata = {
        "A. All Modalities Available (Text=1, Voice=1)": (
            (merged_test["Text_Available"] == 1) & (merged_test["Voice_Available"] == 1)
        ),
        "B. Voice Missing, Text Available (Text=1, Voice=0)": (
            (merged_test["Text_Available"] == 1) & (merged_test["Voice_Available"] == 0)
        ),
        "C. Text Missing, Voice Available (Text=0, Voice=1)": (
            (merged_test["Text_Available"] == 0) & (merged_test["Voice_Available"] == 1)
        ),
        "D. Both Text & Voice Missing (Text=0, Voice=0)": (
            (merged_test["Text_Available"] == 0) & (merged_test["Voice_Available"] == 0)
        ),
    }

    total_strata_n = 0
    strata_rows = []

    for name, mask in strata.items():
        n = int(mask.sum())
        total_strata_n += n
        subset = merged_test[mask]
        
        f_res = evaluate_predictions(subset["Actual_DDS"].values, subset["Fusion_DDS_Prediction"].values, "Fusion")
        s_res = evaluate_predictions(subset["Actual_DDS"].values, subset["Struct_Pred"].values, "Structured")

        strata_rows.append({
            "Stratum": name,
            "N": n,
            "Pct_Test_Set": round(n / len(merged_test) * 100, 2),
            "Fusion_MAE": f_res["MAE"],
            "Fusion_RMSE": f_res["RMSE"],
            "Fusion_R2": f_res["R2"],
            "Fusion_Pearson": f_res["Pearson"],
            "Structured_MAE": s_res["MAE"],
            "Structured_RMSE": s_res["RMSE"],
            "MAE_Diff_vs_Struct": round(s_res["MAE"] - f_res["MAE"], 4),
        })

    assert total_strata_n == 4500, f"Strata sum mismatch: {total_strata_n} != 4500"
    strata_df = pd.DataFrame(strata_rows)
    print(strata_df.to_string(index=False))
    print("  PASS: All 4 strata sum exactly to 4,500 rows.")

    for d in FINAL_OUT_DIRS:
        strata_df.to_csv(os.path.join(d, "fusion_final_availability_metrics.csv"), index=False)

    # -----------------------------------------------------------------------
    # 7. Error Analysis
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("AUDIT 7: RESIDUAL & ERROR DISTRIBUTION ANALYSIS")
    print("=" * 70)

    residuals = merged_test["Fusion_DDS_Prediction"].values - y_test
    abs_errors = np.abs(residuals)

    mean_res = float(np.mean(residuals))
    median_abs_err = float(np.median(abs_errors))
    max_abs_err = float(np.max(abs_errors))

    pct_err_gt_5 = float(np.mean(abs_errors > 5.0) * 100)
    pct_err_gt_10 = float(np.mean(abs_errors > 10.0) * 100)
    pct_err_gt_15 = float(np.mean(abs_errors > 15.0) * 100)
    pct_err_gt_20 = float(np.mean(abs_errors > 20.0) * 100)

    print(f"  Mean Residual (Bias):      {mean_res:+.4f}")
    print(f"  MAE:                       {res_fusion['MAE']:.4f}")
    print(f"  RMSE:                      {res_fusion['RMSE']:.4f}")
    print(f"  Median Absolute Error:     {median_abs_err:.4f}")
    print(f"  Maximum Absolute Error:    {max_abs_err:.4f}")
    print(f"  Absolute Error > 5 DDS:    {pct_err_gt_5:.2f}%")
    print(f"  Absolute Error > 10 DDS:   {pct_err_gt_10:.2f}%")
    print(f"  Absolute Error > 15 DDS:   {pct_err_gt_15:.2f}%")
    print(f"  Absolute Error > 20 DDS:   {pct_err_gt_20:.2f}%")

    # Stratify by DDS Target Range
    range_bins = [
        ("0–25 (Low Distress)", (y_test >= 0) & (y_test < 25)),
        ("25–50 (Moderate Distress)", (y_test >= 25) & (y_test < 50)),
        ("50–75 (High Distress)", (y_test >= 50) & (y_test < 75)),
        ("75–100 (Severe Distress)", (y_test >= 75) & (y_test <= 100)),
    ]

    range_rows = []
    for r_name, r_mask in range_bins:
        n_r = int(r_mask.sum())
        if n_r > 0:
            r_res = float(np.mean(residuals[r_mask]))
            r_mae = float(np.mean(abs_errors[r_mask]))
            range_rows.append({
                "DDS_Range": r_name,
                "N": n_r,
                "Pct_Test_Set": round(n_r / len(y_test) * 100, 2),
                "MAE": round(r_mae, 4),
                "Mean_Residual": round(r_res, 4),
            })
    range_df = pd.DataFrame(range_rows)
    print("\nError Stratified by Target DDS Range:")
    print(range_df.to_string(index=False))

    error_summary = {
        "metric": [
            "Mean Residual (Bias)", "MAE", "RMSE", "Median Absolute Error", "Maximum Absolute Error",
            "Pct Error > 5", "Pct Error > 10", "Pct Error > 15", "Pct Error > 20"
        ],
        "value": [
            round(mean_res, 4), res_fusion["MAE"], res_fusion["RMSE"],
            round(median_abs_err, 4), round(max_abs_err, 4),
            round(pct_err_gt_5, 2), round(pct_err_gt_10, 2),
            round(pct_err_gt_15, 2), round(pct_err_gt_20, 2)
        ]
    }
    error_df = pd.DataFrame(error_summary)
    for d in FINAL_OUT_DIRS:
        error_df.to_csv(os.path.join(d, "fusion_final_error_analysis.csv"), index=False)

    # -----------------------------------------------------------------------
    # 8. Victim-Level Longitudinal Diagnostic
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("AUDIT 8: VICTIM-LEVEL SECONDARY LONGITUDINAL DIAGNOSTIC")
    print("=" * 70)

    victim_agg = merged_test.groupby("Victim_ID").agg({
        "Actual_DDS": "mean",
        "Fusion_DDS_Prediction": "mean",
        "Struct_Pred": "mean",
    }).reset_index()

    assert len(victim_agg) == 150

    v_fusion_res = evaluate_predictions(victim_agg["Actual_DDS"].values, victim_agg["Fusion_DDS_Prediction"].values, "Victim-Mean Fusion")
    v_struct_res = evaluate_predictions(victim_agg["Actual_DDS"].values, victim_agg["Struct_Pred"].values, "Victim-Mean Structured")

    victim_metrics_df = pd.DataFrame([v_fusion_res, v_struct_res])
    print(victim_metrics_df.to_string(index=False))

    for d in FINAL_OUT_DIRS:
        victim_metrics_df.to_csv(os.path.join(d, "fusion_final_victim_level_metrics.csv"), index=False)

    # -----------------------------------------------------------------------
    # 9. Save Predictions & Audit JSON
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SAVING FINAL ARTIFACTS IN FUSION_FINAL NAMESPACE")
    print("=" * 70)

    test_pred_cols = [
        "Victim_ID", "Timepoint", "Actual_DDS",
        "Struct_Pred", "Text_Pred", "Voice_Pred", "Behav_Pred",
        "Struct_Available", "Text_Available", "Voice_Available", "Behav_Available",
        "Fusion_DDS_Prediction"
    ]
    for d in FINAL_OUT_DIRS:
        merged_test[test_pred_cols].to_csv(os.path.join(d, "fusion_final_test_predictions.csv"), index=False)
    print("  Saved: fusion_final_test_predictions.csv (4,500 rows)")

    # Complete Audit JSON
    audit_payload = {
        "step": "10C_FINAL_EVALUATION",
        "timestamp": datetime.now().isoformat(),
        "model_architecture": "Candidate C: XGBoost Stacking Regressor",
        "training_protocol": "5-fold victim-level cross-fitting (OOF) on 700 train victims",
        "selection_basis": {
            "dataset": "Validation Set (150 victims, 4,500 rows)",
            "metric": "Validation MAE",
            "validation_mae": 5.8851,
            "test_set_used_for_selection": False,
        },
        "preliminary_benchmark_reference": {
            "preliminary_test_mae": 6.0626,
            "status": "PRELIMINARY / EXPLORATORY / TEST-SELECTED (NON-CANONICAL)",
        },
        "final_unbiased_test_performance": {
            "N": len(merged_test),
            "MAE": res_fusion["MAE"],
            "RMSE": res_fusion["RMSE"],
            "R2": res_fusion["R2"],
            "Pearson": res_fusion["Pearson"],
            "Spearman": res_fusion["Spearman"],
        },
        "specialist_test_performance": {
            "Structured": res_struct,
            "Text_Available_Only": res_text,
            "Voice_Available_Only": res_voice,
            "Behaviour": res_behav,
            "Train_Mean_Baseline": res_baseline,
        },
        "improvements": {
            "over_structured_specialist_pct": round(imp_over_struct, 4),
            "over_best_specialist_pct": round(imp_over_best, 4),
            "over_baseline_pct": round(imp_over_baseline, 4),
        },
        "availability_stratification": strata_rows,
        "error_analysis": {
            "mean_residual": round(mean_res, 4),
            "median_absolute_error": round(median_abs_err, 4),
            "max_absolute_error": round(max_abs_err, 4),
            "pct_gt_5": round(pct_err_gt_5, 2),
            "pct_gt_10": round(pct_err_gt_10, 2),
            "pct_gt_15": round(pct_err_gt_15, 2),
            "pct_gt_20": round(pct_err_gt_20, 2),
            "range_stratification": range_rows,
        },
        "victim_level_longitudinal_diagnostic": {
            "fusion": v_fusion_res,
            "structured": v_struct_res,
        },
        "reproducibility": reproducibility_record,
        "feature_order": feature_order,
        "clinical_disclaimer": "This is a DDS regression system, not a clinical diagnosis. Performance does not establish causal or clinical validity.",
    }

    for d in FINAL_OUT_DIRS + FINAL_MOD_DIRS:
        with open(os.path.join(d, "fusion_final_audit.json"), "w") as f:
            json.dump(audit_payload, f, indent=2)
    print("  Saved: fusion_final_audit.json")

    # Copy frozen model and feature config to fusion_final model directory for standalone completeness
    for d in FINAL_MOD_DIRS:
        shutil.copy(model_path, os.path.join(d, "fusion_model.json"))
        shutil.copy(feat_config_path, os.path.join(d, "fusion_feature_config.json"))
    print("  Copied frozen model and feature config into fusion_final model directory.")

    print("\n" + "=" * 80)
    print("MEDHA V2 STEP 10C COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
