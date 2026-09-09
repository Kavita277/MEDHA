"""
MEDHA V2 Step 6 -- Test script for Text DDS Specialist

Validates:
1. Feature policy & text specialist boundary compliance (0 voice, 0 structured)
2. Split integrity & victim isolation
3. Preprocessing correctness & feature matrix purity
4. Model loading and prediction (Ridge & XGBoost)
5. Metric sanity & baseline superiority
6. Prediction output artifacts
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
    validate_text_specialist_features,
    get_all_approved_text_dds_features,
    V2_DDS_APPROVED_FEATURES,
    V2_TEXT_DDS_FEATURES,
    V2_CORE_TEXT_DDS_FEATURES,
    V2_VOICE_DDS_FEATURES,
    V2_STRUCTURED_DDS_FEATURES,
    V2_DDS_EXCLUDED_FEATURES,
    V2_DDS_QUARANTINED_FEATURES,
    V2_DDS_TARGET_FEATURES,
    V2_DDS_ID_METADATA_FEATURES,
    V2_DDS_POST_HOC_FEATURES,
)

def test_text_feature_policy_and_boundaries():
    core_features = get_all_approved_text_dds_features(core_only=True)
    all_features = get_all_approved_text_dds_features(core_only=False)

    assert len(core_features) == 5
    assert len(all_features) == 9

    # Both pass strict text validation
    assert validate_text_specialist_features(core_features, allow_extended=False) is True
    assert validate_text_specialist_features(all_features, allow_extended=True) is True

    # Subset of global approved
    assert set(all_features).issubset(set(V2_DDS_APPROVED_FEATURES))

    # Reject Voice features
    for vf in V2_VOICE_DDS_FEATURES:
        with pytest.raises(ValueError, match="VOICE"):
            validate_text_specialist_features(["Text_Distress", vf])

    # Reject Structured features
    for sf in V2_STRUCTURED_DDS_FEATURES:
        with pytest.raises(ValueError, match="STRUCTURED"):
            validate_text_specialist_features(["Text_Distress", sf])

    # Reject Target features
    for tgt in V2_DDS_TARGET_FEATURES:
        with pytest.raises(ValueError, match="TARGET"):
            validate_text_specialist_features(["Text_Distress", tgt])

    # Reject Excluded leaky features
    for ex in V2_DDS_EXCLUDED_FEATURES:
        with pytest.raises(ValueError, match="EXCLUDED"):
            validate_text_specialist_features(["Text_Distress", ex])

    # Reject duplicates
    with pytest.raises(ValueError, match="Duplicate"):
        validate_text_specialist_features(["Text_Distress", "Text_Distress"])

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

    train_rows = (long_df["Split"] == "train").sum()
    val_rows = (long_df["Split"] == "validation").sum()
    test_rows = (long_df["Split"] == "test").sum()

    assert train_rows == 21000
    assert val_rows == 4500
    assert test_rows == 4500

def test_model_artifacts_exist():
    model_dir = os.path.join(ENGINE_DIR, "models", "text_dds_v2")
    output_dir = os.path.join(ROOT_DIR, "outputs", "dds_v2", "text")

    assert os.path.exists(os.path.join(model_dir, "v2_text_dds_ridge_core5.pkl"))
    assert os.path.exists(os.path.join(model_dir, "v2_text_dds_xgb_core5.json"))
    assert os.path.exists(os.path.join(model_dir, "v2_text_dds_xgb_all9.json"))
    assert os.path.exists(os.path.join(model_dir, "v2_text_dds_preprocessor.pkl"))
    assert os.path.exists(os.path.join(model_dir, "v2_text_dds_features.json"))
    assert os.path.exists(os.path.join(model_dir, "v2_text_dds_metrics.json"))
    assert os.path.exists(os.path.join(model_dir, "v2_text_dds_importance.csv"))

    assert os.path.exists(os.path.join(output_dir, "test_text_dds_predictions.csv"))
    assert os.path.exists(os.path.join(output_dir, "val_text_dds_predictions.csv"))

def test_model_loading_and_inference():
    model_dir = os.path.join(ENGINE_DIR, "models", "text_dds_v2")
    long_df = pd.read_csv(os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv"))
    test_sub = long_df[long_df["Split"] == "test"]

    core_features = get_all_approved_text_dds_features(core_only=True)

    with open(os.path.join(model_dir, "v2_text_dds_preprocessor.pkl"), "rb") as f:
        preprocessor = pickle.load(f)

    with open(os.path.join(model_dir, "v2_text_dds_ridge_core5.pkl"), "rb") as f:
        ridge = pickle.load(f)

    xgb_model = xgb.XGBRegressor()
    xgb_model.load_model(os.path.join(model_dir, "v2_text_dds_xgb_core5.json"))

    X_test = preprocessor.transform(test_sub[core_features])
    preds_ridge = ridge.predict(X_test)
    preds_xgb = xgb_model.predict(X_test)

    assert len(preds_ridge) == len(test_sub) == 4500
    assert len(preds_xgb) == len(test_sub) == 4500

    # Inference on available subset
    avail_mask = (test_sub["Text_Available"] == 1).values
    assert avail_mask.sum() == 3362
    assert not np.isnan(preds_ridge[avail_mask]).any()
    assert not np.isnan(preds_xgb[avail_mask]).any()

def test_metrics_integrity():
    model_dir = os.path.join(ENGINE_DIR, "models", "text_dds_v2")
    with open(os.path.join(model_dir, "v2_text_dds_metrics.json"), "r") as f:
        metrics = json.load(f)

    assert "ridge_core5" in metrics["models_evaluated"]
    assert "xgb_core5" in metrics["models_evaluated"]
    assert "xgb_all9" in metrics["models_evaluated"]

    ridge_test = metrics["models_evaluated"]["ridge_core5"]["test"]
    assert ridge_test["R2"] > 0.50  # got 0.6365
    assert ridge_test["Pearson"] > 0.70  # got 0.7978
    assert ridge_test["Spearman"] > 0.70  # got 0.8067
    assert ridge_test["mae_reduction_pct"] > 35.0  # got 41.53%

    # Verify all Ridge weights are positive (distress indicators positively correlate with DDS)
    weights = metrics["ridge_coefficients"]["weights"]
    for feat, w in weights.items():
        assert w > 0, f"Expected positive weight for {feat}, got {w}"

def test_predictions_csv_integrity():
    output_dir = os.path.join(ROOT_DIR, "outputs", "dds_v2", "text")
    pred_df = pd.read_csv(os.path.join(output_dir, "test_text_dds_predictions.csv"))

    assert len(pred_df) == 4500
    assert set(["Victim_ID", "Timepoint", "Split", "Text_Available", "DDS_actual",
                "pred_text_dds_ridge_core5", "pred_text_dds_xgb_core5"]).issubset(set(pred_df.columns))
    assert (pred_df["Split"] == "test").all()

if __name__ == "__main__":
    print("=== Running Text DDS Specialist Tests ===\n")
    test_text_feature_policy_and_boundaries()
    print("[PASS] Text feature policy & specialist boundary compliance")
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
