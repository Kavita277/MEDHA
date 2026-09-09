"""
MEDHA V2 Step 5 -- Test script for Clean Structured DDS Regressor

Validates:
1. Feature policy & specialist boundary compliance (42 features, 0 text, 0 voice)
2. Split integrity & victim isolation
3. Preprocessing correctness & feature matrix shapes
4. Model loading and prediction
5. Post-preprocessing leakage checks & feature purity
6. Feature importance purity (no text/voice)
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
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)
if V2_DIR not in sys.path:
    sys.path.insert(0, V2_DIR)

try:
    from engine.v2.v2_feature_policy import (
        validate_dds_features,
        validate_structured_specialist_features,
        get_all_approved_dds_features,
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
        get_all_approved_dds_features,
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

def test_structured_feature_policy_and_boundaries():
    features = get_all_approved_structured_dds_features()
    assert len(features) == 42
    assert validate_structured_specialist_features(features) is True

    # Subset of global approved
    assert set(features).issubset(set(V2_DDS_APPROVED_FEATURES))

    # Reject text features
    for tf in V2_TEXT_DDS_FEATURES:
        with pytest.raises(ValueError, match="TEXT"):
            validate_structured_specialist_features(["Mood", tf])

    # Reject voice features
    for vf in V2_VOICE_DDS_FEATURES:
        with pytest.raises(ValueError, match="VOICE"):
            validate_structured_specialist_features(["Mood", vf])

    # Reject target features
    for tgt in V2_DDS_TARGET_FEATURES:
        with pytest.raises(ValueError, match="TARGET"):
            validate_structured_specialist_features(["Mood", tgt])

    # Reject excluded/leaky features
    for ex in V2_DDS_EXCLUDED_FEATURES:
        with pytest.raises(ValueError, match="EXCLUDED"):
            validate_structured_specialist_features(["Mood", ex])

    # Reject duplicates
    with pytest.raises(ValueError, match="Duplicate"):
        validate_structured_specialist_features(["Mood", "Mood"])

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

def test_preprocessing_and_matrix_purity():
    MODEL_DIR = os.path.join(ENGINE_DIR, "models", "v2")
    preproc_path = os.path.join(MODEL_DIR, "v2_structured_dds_preprocessor.pkl")
    feat_path = os.path.join(MODEL_DIR, "v2_structured_dds_features.json")
    long_df = pd.read_csv(os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv"))
    features = get_all_approved_structured_dds_features()

    assert os.path.exists(preproc_path)
    assert os.path.exists(feat_path)

    with open(feat_path, "r") as f:
        feat_meta = json.load(f)
    assert feat_meta["feature_count"] == 42
    assert len(feat_meta["features"]) == 42

    with open(preproc_path, "rb") as f:
        preprocessor = pickle.load(f)

    train_sub = long_df[long_df["Split"] == "train"]
    X_train = preprocessor.transform(train_sub[features])
    assert X_train.shape == (21000, 42)

    val_sub = long_df[long_df["Split"] == "validation"]
    X_val = preprocessor.transform(val_sub[features])
    assert X_val.shape == (4500, 42)

    test_sub = long_df[long_df["Split"] == "test"]
    X_test = preprocessor.transform(test_sub[features])
    assert X_test.shape == (4500, 42)

    # Check zero text and zero voice
    assert len(set(features) & set(V2_TEXT_DDS_FEATURES)) == 0
    assert len(set(features) & set(V2_VOICE_DDS_FEATURES)) == 0

    # Check no banned columns
    banned_all = set(V2_DDS_EXCLUDED_FEATURES + V2_DDS_QUARANTINED_FEATURES +
                     V2_DDS_TARGET_FEATURES + V2_DDS_ID_METADATA_FEATURES +
                     V2_DDS_POST_HOC_FEATURES)
    overlap = banned_all & set(features)
    assert len(overlap) == 0

def test_model_loading_and_predictions():
    MODEL_DIR = os.path.join(ENGINE_DIR, "models", "v2")
    model_path = os.path.join(MODEL_DIR, "v2_structured_dds_xgb.json")
    preproc_path = os.path.join(MODEL_DIR, "v2_structured_dds_preprocessor.pkl")
    long_df = pd.read_csv(os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv"))
    features = get_all_approved_structured_dds_features()

    assert os.path.exists(model_path)
    with open(preproc_path, "rb") as f:
        preprocessor = pickle.load(f)

    model = xgb.XGBRegressor()
    model.load_model(model_path)

    val_sub = long_df[long_df["Split"] == "validation"]
    X_val = preprocessor.transform(val_sub[features])
    val_preds = model.predict(X_val)
    assert len(val_preds) == 4500

    test_sub = long_df[long_df["Split"] == "test"]
    X_test = preprocessor.transform(test_sub[features])
    test_preds = model.predict(X_test)
    assert len(test_preds) == 4500

def test_feature_importance_purity():
    MODEL_DIR = os.path.join(ENGINE_DIR, "models", "v2")
    imp_path = os.path.join(MODEL_DIR, "v2_structured_dds_importance.csv")
    assert os.path.exists(imp_path)

    imp_df = pd.read_csv(imp_path)
    assert len(imp_df) == 42
    imp_features = set(imp_df["feature"])

    # Strict check: absolutely no text or voice in feature importance
    assert len(imp_features & set(V2_TEXT_DDS_FEATURES)) == 0
    assert len(imp_features & set(V2_VOICE_DDS_FEATURES)) == 0

def test_metrics_integrity():
    MODEL_DIR = os.path.join(ENGINE_DIR, "models", "v2")
    metrics_path = os.path.join(MODEL_DIR, "v2_structured_dds_metrics.json")
    assert os.path.exists(metrics_path)

    with open(metrics_path, "r") as f:
        metrics = json.load(f)

    for split in ["train", "validation", "test"]:
        assert split in metrics["row_level"]
        for m in ["MAE", "RMSE", "R2", "Pearson"]:
            assert m in metrics["row_level"][split]
        assert split in metrics["victim_level"]

    val_r2 = metrics["row_level"]["validation"]["R2"]
    assert val_r2 > 0.5  # got 0.6462
    test_r2 = metrics["row_level"]["test"]["R2"]
    assert test_r2 > 0.5  # got 0.6536

if __name__ == "__main__":
    print("=== Running Clean Structured DDS Regressor Tests ===\n")
    test_structured_feature_policy_and_boundaries()
    print("[PASS] Feature policy & specialist boundary compliance")
    test_split_integrity()
    print("[PASS] Split integrity")
    test_preprocessing_and_matrix_purity()
    print("[PASS] Preprocessing & matrix purity checks")
    test_model_loading_and_predictions()
    print("[PASS] Model loading and inference checks")
    test_feature_importance_purity()
    print("[PASS] Feature importance purity (0 text, 0 voice)")
    test_metrics_integrity()
    print("[PASS] Metrics integrity")
    print("\n==================================================")
    print("ALL TESTS PASSED")
    print("==================================================")
