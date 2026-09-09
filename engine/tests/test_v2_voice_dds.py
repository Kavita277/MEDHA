"""
MEDHA V2 Step 7 -- Test script for Voice DDS Specialist

Validates:
1. Feature policy & voice specialist boundary compliance (0 text, 0 structured)
2. Missing voice representation (represented as NaN, not zero distress)
3. Split integrity & victim isolation
4. Preprocessing correctness & feature matrix purity
5. Model loading and prediction (Ridge & XGBoost)
6. Metric sanity & positive coefficient checks
7. Prediction output artifacts
"""

import os
import sys
import json
import pickle
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

def test_voice_feature_policy_and_boundaries():
    core_features = get_all_approved_voice_dds_features(core_only=True)
    all_features = get_all_approved_voice_dds_features(core_only=False)

    assert len(core_features) == 5
    assert len(all_features) == 9

    # Both pass strict voice validation
    assert validate_voice_specialist_features(core_features, allow_extended=False) is True
    assert validate_voice_specialist_features(all_features, allow_extended=True) is True

    # Subset of global approved
    assert set(all_features).issubset(set(V2_DDS_APPROVED_FEATURES))

    # Reject Text features
    for tf in V2_TEXT_DDS_FEATURES:
        with pytest.raises(ValueError, match="TEXT"):
            validate_voice_specialist_features(["Voice_Distress", tf])

    # Reject Structured features
    for sf in V2_STRUCTURED_DDS_FEATURES:
        with pytest.raises(ValueError, match="STRUCTURED"):
            validate_voice_specialist_features(["Voice_Distress", sf])

    # Reject Target features
    for tgt in V2_DDS_TARGET_FEATURES:
        with pytest.raises(ValueError, match="TARGET"):
            validate_voice_specialist_features(["Voice_Distress", tgt])

    # Reject Excluded leaky features
    for ex in V2_DDS_EXCLUDED_FEATURES:
        with pytest.raises(ValueError, match="EXCLUDED"):
            validate_voice_specialist_features(["Voice_Distress", ex])

    # Reject duplicates
    with pytest.raises(ValueError, match="Duplicate"):
        validate_voice_specialist_features(["Voice_Distress", "Voice_Distress"])

def test_missing_voice_representation():
    long_df = pd.read_csv(os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv"))
    
    # Missing voice count
    missing_mask = (long_df["Voice_Available"] == 0)
    avail_mask = (long_df["Voice_Available"] == 1)

    assert missing_mask.sum() == 19005
    assert avail_mask.sum() == 10995

    # Confirm missing voice is NaN, not zero distress
    missing_df = long_df[missing_mask]
    for col in V2_CORE_VOICE_DDS_FEATURES:
        assert missing_df[col].isna().all(), f"Feature {col} contains non-NaN values when Voice_Available == 0!"

    # Available voice rows have valid numeric features
    avail_df = long_df[avail_mask]
    for col in V2_CORE_VOICE_DDS_FEATURES:
        assert avail_df[col].notna().all(), f"Feature {col} contains NaNs when Voice_Available == 1!"

def test_split_integrity():
    split_df = pd.read_csv(os.path.join(ENGINE_DIR, "data", "processed", "v2_victim_split.csv"))
    long_df = pd.read_csv(os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv"))

    train_vids = set(split_df[split_df["Split"] == "train"]["Victim_ID"])
    val_vids   = set(split_df[split_df["Split"] == "validation"]["Victim_ID"])
    test_vids  = set(split_df[split_df["Split"] == "test"]["Victim_ID"])

    assert len(train_vids & val_vids) == 0
    assert len(train_vids & test_vids) == 0
    assert len(val_vids & test_vids) == 0
    assert len(train_vids) == 700
    assert len(val_vids) == 150
    assert len(test_vids) == 150

    train_avail = ((long_df["Split"] == "train") & (long_df["Voice_Available"] == 1)).sum()
    val_avail = ((long_df["Split"] == "validation") & (long_df["Voice_Available"] == 1)).sum()
    test_avail = ((long_df["Split"] == "test") & (long_df["Voice_Available"] == 1)).sum()

    assert train_avail == 7634
    assert val_avail == 1669
    assert test_avail == 1692

def test_model_artifacts_exist():
    model_dir = os.path.join(ENGINE_DIR, "models", "voice_dds_v2")
    output_dir = os.path.join(ROOT_DIR, "outputs", "dds_v2", "voice")

    assert os.path.exists(os.path.join(model_dir, "v2_voice_dds_ridge_core5.pkl"))
    assert os.path.exists(os.path.join(model_dir, "v2_voice_dds_xgb_core5.json"))
    assert os.path.exists(os.path.join(model_dir, "v2_voice_dds_xgb_all9.json"))
    assert os.path.exists(os.path.join(model_dir, "v2_voice_dds_preprocessor.pkl"))
    assert os.path.exists(os.path.join(model_dir, "v2_voice_dds_features.json"))
    assert os.path.exists(os.path.join(model_dir, "v2_voice_dds_metrics.json"))
    assert os.path.exists(os.path.join(model_dir, "v2_voice_dds_importance.csv"))

    assert os.path.exists(os.path.join(output_dir, "test_voice_dds_predictions.csv"))
    assert os.path.exists(os.path.join(output_dir, "val_voice_dds_predictions.csv"))

def test_model_loading_and_inference():
    model_dir = os.path.join(ENGINE_DIR, "models", "voice_dds_v2")
    long_df = pd.read_csv(os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv"))
    test_sub = long_df[long_df["Split"] == "test"]

    core_features = get_all_approved_voice_dds_features(core_only=True)

    with open(os.path.join(model_dir, "v2_voice_dds_preprocessor.pkl"), "rb") as f:
        preprocessor = pickle.load(f)

    with open(os.path.join(model_dir, "v2_voice_dds_ridge_core5.pkl"), "rb") as f:
        ridge = pickle.load(f)

    xgb_model = xgb.XGBRegressor()
    xgb_model.load_model(os.path.join(model_dir, "v2_voice_dds_xgb_core5.json"))

    # Available test rows
    avail_mask = (test_sub["Voice_Available"] == 1).values
    assert avail_mask.sum() == 1692

    X_test_avail = preprocessor.transform(test_sub.loc[avail_mask, core_features])
    preds_ridge = ridge.predict(X_test_avail)
    preds_xgb = xgb_model.predict(X_test_avail)

    assert len(preds_ridge) == 1692
    assert len(preds_xgb) == 1692
    assert not np.isnan(preds_ridge).any()
    assert not np.isnan(preds_xgb).any()

def test_metrics_integrity():
    model_dir = os.path.join(ENGINE_DIR, "models", "voice_dds_v2")
    with open(os.path.join(model_dir, "v2_voice_dds_metrics.json"), "r") as f:
        metrics = json.load(f)

    assert "ridge_core5" in metrics["models_evaluated"]
    assert "xgb_core5" in metrics["models_evaluated"]
    assert "xgb_all9" in metrics["models_evaluated"]

    ridge_test = metrics["models_evaluated"]["ridge_core5"]["test"]
    assert ridge_test["R2"] > 0.50  # got 0.6529
    assert ridge_test["Pearson"] > 0.70  # got 0.8082
    assert ridge_test["Spearman"] > 0.70  # got 0.8179
    assert ridge_test["mae_improvement_pct"] > 35.0  # got +43.23%

    # Verify all Ridge weights are positive
    weights = metrics["ridge_coefficients"]["weights"]
    for feat, w in weights.items():
        assert w > 0, f"Expected positive weight for {feat}, got {w}"

def test_predictions_csv_integrity():
    output_dir = os.path.join(ROOT_DIR, "outputs", "dds_v2", "voice")
    pred_df = pd.read_csv(os.path.join(output_dir, "test_voice_dds_predictions.csv"))

    assert len(pred_df) == 4500
    assert set(["Victim_ID", "Timepoint", "Split", "Voice_Available", "DDS_actual",
                "pred_voice_dds_ridge_core5", "pred_voice_dds_xgb_core5"]).issubset(set(pred_df.columns))

    # Check that missing voice has NaN clean prediction (preserves missingness, not 0 distress)
    missing_rows = pred_df[pred_df["Voice_Available"] == 0]
    assert missing_rows["pred_voice_dds_ridge_core5"].isna().all()
    assert missing_rows["pred_voice_dds_xgb_core5"].isna().all()

    # Check that available voice has non-NaN clean predictions
    avail_rows = pred_df[pred_df["Voice_Available"] == 1]
    assert avail_rows["pred_voice_dds_ridge_core5"].notna().all()
    assert avail_rows["pred_voice_dds_xgb_core5"].notna().all()

if __name__ == "__main__":
    print("=== Running Voice DDS Specialist Tests ===\n")
    test_voice_feature_policy_and_boundaries()
    print("[PASS] Voice feature policy & specialist boundary compliance")
    test_missing_voice_representation()
    print("[PASS] Missing voice representation (NaN, not zero distress)")
    test_split_integrity()
    print("[PASS] Split integrity")
    test_model_artifacts_exist()
    print("[PASS] Model artifacts and directories exist")
    test_model_loading_and_inference()
    print("[PASS] Model loading and inference checks")
    test_metrics_integrity()
    print("[PASS] Metrics integrity and positive weight checks")
    test_predictions_csv_integrity()
    print("[PASS] Prediction CSVs integrity")
    print("\n==================================================")
    print("ALL TESTS PASSED")
    print("==================================================")
