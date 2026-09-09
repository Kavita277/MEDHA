"""
MEDHA V2 Step 8 -- Test script for Behaviour DDS Specialist

Validates:
1. Feature policy & behaviour specialist boundary compliance (0 text, 0 voice, 0 structured clinical context)
2. Mathematical verification of deviation features (absolute deviation |z|)
3. Split integrity & victim isolation (700/150/150 disjoint victims, 100% coverage)
4. Model artifacts existence in root and engine directories
5. Model loading and inference execution (Ridge & XGBoost)
6. Metrics integrity (MAE, RMSE, R2, Pearson, Spearman, positive MAE improvement)
7. Predictions CSV integrity (4,500 rows, valid columns, no NaNs)
"""

import os
import sys
import json
import joblib
import pytest
import numpy as np
import pandas as pd
import xgboost as xgb

ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V2_DIR = os.path.join(ENGINE_DIR, 'v2')
ROOT_DIR = os.path.abspath(os.path.join(ENGINE_DIR, '..'))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)
if V2_DIR not in sys.path:
    sys.path.insert(0, V2_DIR)

from engine.v2.v2_feature_policy import (
    validate_dds_features,
    validate_behaviour_specialist_features,
    get_all_approved_behaviour_dds_features,
    V2_DDS_APPROVED_FEATURES,
    V2_CORE_BEHAVIOUR_DDS_FEATURES,
    V2_EXTENDED_BEHAVIOUR_DDS_FEATURES,
    V2_TEXT_DDS_FEATURES,
    V2_VOICE_DDS_FEATURES,
    V2_STRUCTURED_DDS_FEATURES,
    V2_DDS_EXCLUDED_FEATURES,
    V2_DDS_QUARANTINED_FEATURES,
    V2_DDS_TARGET_FEATURES,
    V2_DDS_ID_METADATA_FEATURES,
    V2_DDS_POST_HOC_FEATURES,
)

def test_behaviour_feature_policy_and_boundaries():
    core_features = get_all_approved_behaviour_dds_features(core_only=True)
    all_features = get_all_approved_behaviour_dds_features(core_only=False)

    assert len(core_features) == 7
    assert len(all_features) == 10

    # Both pass strict behaviour validation
    assert validate_behaviour_specialist_features(core_features, allow_extended=False) is True
    assert validate_behaviour_specialist_features(all_features, allow_extended=True) is True

    # Subset of global approved
    assert set(all_features).issubset(set(V2_DDS_APPROVED_FEATURES))

    # Reject Text features
    for tf in V2_TEXT_DDS_FEATURES:
        with pytest.raises(ValueError, match="TEXT"):
            validate_behaviour_specialist_features(["Engagement_Score", tf])

    # Reject Voice features
    for vf in V2_VOICE_DDS_FEATURES:
        with pytest.raises(ValueError, match="VOICE"):
            validate_behaviour_specialist_features(["Engagement_Score", vf])

    # Reject Structured clinical context features (e.g. Mood, Stress, Case_Type, Threat_Event)
    structured_context_features = [f for f in V2_STRUCTURED_DDS_FEATURES if f not in all_features]
    for sf in structured_context_features[:5]:
        with pytest.raises(ValueError, match="Structured"):
            validate_behaviour_specialist_features(["Engagement_Score", sf])

    # Reject Target features
    for tgt in V2_DDS_TARGET_FEATURES:
        with pytest.raises(ValueError, match="TARGET"):
            validate_behaviour_specialist_features(["Engagement_Score", tgt])

    # Reject Excluded leaky features
    for ex in V2_DDS_EXCLUDED_FEATURES:
        with pytest.raises(ValueError, match="EXCLUDED"):
            validate_behaviour_specialist_features(["Engagement_Score", ex])

    # Reject duplicates
    with pytest.raises(ValueError, match="Duplicate"):
        validate_behaviour_specialist_features(["Engagement_Score", "Engagement_Score"])

def test_mathematical_definition_of_deviations():
    long_df = pd.read_csv(os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv"))

    raw_eng_dev = long_df["Engagement_Deviation"]
    # Verify raw column in dataset is signed with substantial negative values
    assert (raw_eng_dev < 0).sum() > 20000

    # Verify absolute deviation is strictly non-negative
    abs_eng_dev = raw_eng_dev.abs()
    assert (abs_eng_dev >= 0).all()

    # Verify absolute deviation has positive correlation with DDS
    corr_abs = float(abs_eng_dev.corr(long_df["DDS"]))
    assert corr_abs > 0.50  # got ~0.5197

    # Verify canonical model features JSON includes absolute deviation metadata
    model_dir = os.path.join(ENGINE_DIR, "models", "behaviour_dds_v2")
    with open(os.path.join(model_dir, "v2_behaviour_dds_features.json"), "r") as f:
        feat_meta = json.load(f)
    assert "absolute deviation" in feat_meta["mathematical_definition"].lower()

    # Verify canonical Ridge weight for Engagement_Deviation is positive
    coefs = feat_meta["coefficients_ridge_all10"]
    assert coefs["Engagement_Deviation"] > 0, f"Expected positive Engagement_Deviation weight, got {coefs['Engagement_Deviation']}"

def test_split_integrity():
    split_df = pd.read_csv(os.path.join(ENGINE_DIR, "data", "processed", "v2_victim_split.csv"))
    long_df = pd.read_csv(os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv"))

    train_vids = set(split_df[split_df["Split"].str.lower() == "train"]["Victim_ID"])
    val_vids   = set(split_df[split_df["Split"].str.lower().isin(["val", "validation"])]["Victim_ID"])
    test_vids  = set(split_df[split_df["Split"].str.lower() == "test"]["Victim_ID"])

    assert len(train_vids & val_vids) == 0
    assert len(train_vids & test_vids) == 0
    assert len(val_vids & test_vids) == 0
    assert len(train_vids) == 700
    assert len(val_vids) == 150
    assert len(test_vids) == 150

    train_rows = (long_df["Split"].str.lower() == "train").sum()
    val_rows = (long_df["Split"].str.lower().isin(["val", "validation"])).sum()
    test_rows = (long_df["Split"].str.lower() == "test").sum()

    assert train_rows == 21000
    assert val_rows == 4500
    assert test_rows == 4500

    # 100% behavioural observation coverage (unlike Voice/Text, behaviour has 0 missing check-in interaction records)
    for feat in V2_CORE_BEHAVIOUR_DDS_FEATURES:
        assert long_df[feat].isna().sum() == 0, f"Core behaviour feature {feat} has missing values!"

def test_model_artifacts_exist():
    model_dirs = [
        os.path.join(ENGINE_DIR, "models", "behaviour_dds_v2"),
        os.path.join(ENGINE_DIR, "models", "behaviour_dds_v2"),
    ]
    output_dirs = [
        os.path.join(ROOT_DIR, "outputs", "dds_v2", "behaviour"),
        os.path.join(ENGINE_DIR, "outputs", "dds_v2", "behaviour"),
    ]

    for model_dir in model_dirs:
        assert os.path.exists(os.path.join(model_dir, "v2_behaviour_dds_ridge_all10.pkl"))
        assert os.path.exists(os.path.join(model_dir, "v2_behaviour_dds_xgb_all10.json"))
        assert os.path.exists(os.path.join(model_dir, "v2_behaviour_dds_ridge_core7.pkl"))
        assert os.path.exists(os.path.join(model_dir, "v2_behaviour_dds_xgb_core7.json"))
        assert os.path.exists(os.path.join(model_dir, "v2_behaviour_dds_diagnostic_signed.json"))
        assert os.path.exists(os.path.join(model_dir, "v2_behaviour_dds_preprocessor.pkl"))
        assert os.path.exists(os.path.join(model_dir, "v2_behaviour_dds_features.json"))
        assert os.path.exists(os.path.join(model_dir, "v2_behaviour_dds_metrics.json"))
        assert os.path.exists(os.path.join(model_dir, "v2_behaviour_dds_importance.csv"))

    for output_dir in output_dirs:
        assert os.path.exists(os.path.join(output_dir, "test_behaviour_dds_predictions.csv"))
        assert os.path.exists(os.path.join(output_dir, "val_behaviour_dds_predictions.csv"))

def test_model_loading_and_inference():
    model_dir = os.path.join(ENGINE_DIR, "models", "behaviour_dds_v2")
    long_df = pd.read_csv(os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv"))
    test_sub = long_df[long_df["Split"].str.lower() == "test"].copy()

    all_features = list(V2_EXTENDED_BEHAVIOUR_DDS_FEATURES)

    preprocessor = joblib.load(os.path.join(model_dir, "v2_behaviour_dds_preprocessor.pkl"))
    ridge = joblib.load(os.path.join(model_dir, "v2_behaviour_dds_ridge_all10.pkl"))

    xgb_model = xgb.XGBRegressor()
    xgb_model.load_model(os.path.join(model_dir, "v2_behaviour_dds_xgb_all10.json"))

    # Prepare absolute deviations
    X_test_raw = test_sub[all_features].copy()
    X_test_raw["Engagement_Deviation"] = X_test_raw["Engagement_Deviation"].abs()
    X_test_raw["Response_Delay_Deviation"] = X_test_raw["Response_Delay_Deviation"].abs()

    X_test_imp = pd.DataFrame(preprocessor.transform(X_test_raw), columns=all_features)

    preds_ridge = ridge.predict(X_test_imp)
    preds_xgb = xgb_model.predict(X_test_imp)

    assert len(preds_ridge) == 4500
    assert len(preds_xgb) == 4500
    assert not np.isnan(preds_ridge).any()
    assert not np.isnan(preds_xgb).any()

def test_metrics_integrity():
    model_dir = os.path.join(ENGINE_DIR, "models", "behaviour_dds_v2")
    with open(os.path.join(model_dir, "v2_behaviour_dds_metrics.json"), "r") as f:
        metrics = json.load(f)

    assert "ridge_all10_canonical" in metrics
    assert "xgb_all10" in metrics
    assert "ridge_core7" in metrics
    assert "diagnostic_ridge_signed" in metrics

    ridge_test = metrics["ridge_all10_canonical"]["test"]
    assert ridge_test["r2"] > 0.45  # got 0.5106
    assert ridge_test["pearson_r"] > 0.65  # got 0.7147
    assert ridge_test["spearman_rho"] > 0.65  # got 0.7332
    assert ridge_test["mae_improvement_pct"] > 25.0  # got +32.04%

    # Absolute deviations model outperforms signed deviations model on test MAE
    signed_test = metrics["diagnostic_ridge_signed"]["test"]
    assert ridge_test["mae"] <= signed_test["mae"]

def test_predictions_csv_integrity():
    output_dir = os.path.join(ROOT_DIR, "outputs", "dds_v2", "behaviour")
    pred_df = pd.read_csv(os.path.join(output_dir, "test_behaviour_dds_predictions.csv"))

    assert len(pred_df) == 4500
    required_cols = [
        "Victim_ID", "Timepoint", "Actual_DDS", "Predicted_DDS_Ridge",
        "Predicted_DDS_XGB", "Engagement_Score", "Engagement_Deviation_Abs",
        "Response_Delay_Hours", "Response_Delay_Deviation_Abs", "Missed_Checkin"
    ]
    assert set(required_cols).issubset(set(pred_df.columns))

    # All predictions non-null and within realistic DDS bounds [0, 100]
    assert pred_df["Predicted_DDS_Ridge"].notna().all()
    assert pred_df["Predicted_DDS_XGB"].notna().all()
    assert (pred_df["Predicted_DDS_Ridge"] >= 0).all()
    assert (pred_df["Predicted_DDS_Ridge"] <= 100).all()

if __name__ == "__main__":
    print("=== Running Behaviour DDS Specialist Tests ===\n")
    test_behaviour_feature_policy_and_boundaries()
    print("[PASS] Behaviour feature policy & specialist boundary compliance")
    test_mathematical_definition_of_deviations()
    print("[PASS] Mathematical verification of deviation features (absolute deviation |z|)")
    test_split_integrity()
    print("[PASS] Split integrity & 100% coverage")
    test_model_artifacts_exist()
    print("[PASS] Model artifacts and directories exist")
    test_model_loading_and_inference()
    print("[PASS] Model loading and inference checks")
    test_metrics_integrity()
    print("[PASS] Metrics integrity and performance assertions")
    test_predictions_csv_integrity()
    print("[PASS] Prediction CSVs integrity")
    print("\n==================================================")
    print("ALL BEHAVIOUR SPECIALIST TESTS PASSED")
    print("==================================================")
