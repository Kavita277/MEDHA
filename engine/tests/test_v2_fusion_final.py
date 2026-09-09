"""
MEDHA V2 Step 10C -- Unit Tests for Final Locked Fusion Evaluation
==================================================================

Validates the integrity, reproducibility, and holdout cleanliness of the
Step 10C final evaluation.
"""

import os
import sys
import json
import pytest
import numpy as np
import pandas as pd
import xgboost as xgb

ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V2_DIR = os.path.join(ENGINE_DIR, 'v2')
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
FINAL_OUT_DIR = os.path.join(ENGINE_DIR, "outputs", "dds_v2", "fusion_final")
FINAL_MOD_DIR = os.path.join(ENGINE_DIR, "models", "v2", "fusion_final")
OOF_MOD_DIR = os.path.join(ENGINE_DIR, "models", "v2", "fusion_oof")


def test_final_artifacts_exist():
    required_files = [
        os.path.join(FINAL_OUT_DIR, "fusion_final_test_predictions.csv"),
        os.path.join(FINAL_OUT_DIR, "fusion_final_test_metrics.csv"),
        os.path.join(FINAL_OUT_DIR, "fusion_final_availability_metrics.csv"),
        os.path.join(FINAL_OUT_DIR, "fusion_final_error_analysis.csv"),
        os.path.join(FINAL_OUT_DIR, "fusion_final_victim_level_metrics.csv"),
        os.path.join(FINAL_OUT_DIR, "fusion_final_reproducibility.json"),
        os.path.join(FINAL_OUT_DIR, "fusion_final_audit.json"),
        os.path.join(FINAL_MOD_DIR, "fusion_model.json"),
        os.path.join(FINAL_MOD_DIR, "fusion_feature_config.json"),
    ]
    for rf in required_files:
        assert os.path.exists(rf), f"Missing required Step 10C artifact: {rf}"


def test_test_dataset_holdout_integrity():
    split_df = pd.read_csv(SPLIT_CSV)
    train_vids = set(split_df[split_df["Split"].str.lower() == "train"]["Victim_ID"])
    val_vids   = set(split_df[split_df["Split"].str.lower() == "validation"]["Victim_ID"])
    test_vids  = set(split_df[split_df["Split"].str.lower() == "test"]["Victim_ID"])

    assert len(test_vids) == 150
    assert len(train_vids & test_vids) == 0
    assert len(val_vids & test_vids) == 0

    pred_csv = os.path.join(FINAL_OUT_DIR, "fusion_final_test_predictions.csv")
    df = pd.read_csv(pred_csv)

    assert len(df) == 4500, f"Expected 4,500 rows, got {len(df)}"
    assert df["Victim_ID"].nunique() == 150
    assert set(df["Victim_ID"].unique()) == test_vids

    v_counts = df.groupby("Victim_ID").size()
    assert (v_counts == 30).all(), "Every test victim must have exactly 30 timepoints!"
    assert not df.duplicated(subset=["Victim_ID", "Timepoint"]).any()


def test_fusion_input_contract_and_forbidden_features():
    cfg_path = os.path.join(FINAL_MOD_DIR, "fusion_feature_config.json")
    with open(cfg_path) as f:
        cfg = json.load(f)

    feature_order = cfg["feature_order"]
    validate_fusion_features(feature_order)

    assert len(feature_order) == 8
    expected = [
        "Struct_Pred", "Text_Pred", "Voice_Pred", "Behav_Pred",
        "Struct_Available", "Text_Available", "Voice_Available", "Behav_Available"
    ]
    assert feature_order == expected

    for forbidden in V2_FUSION_FORBIDDEN_FEATURES:
        assert forbidden not in feature_order


def test_deterministic_inference():
    model_path = os.path.join(FINAL_MOD_DIR, "fusion_model.json")
    model = xgb.XGBRegressor()
    model.load_model(model_path)

    sample = np.array([
        [60.0, 50.0, 45.0, 55.0, 1.0, 1.0, 1.0, 1.0],
        [70.0, 0.0, 0.0, 65.0, 1.0, 0.0, 0.0, 1.0],
    ])
    p1 = model.predict(sample)
    p2 = model.predict(sample)
    np.testing.assert_allclose(p1, p2)


def test_availability_stratification_sum():
    strata_csv = os.path.join(FINAL_OUT_DIR, "fusion_final_availability_metrics.csv")
    df = pd.read_csv(strata_csv)

    assert len(df) == 4
    assert df["N"].sum() == 4500
    assert set(df["Stratum"].str[0]) == {"A", "B", "C", "D"}


def test_audit_json_validation_mae_reference():
    audit_path = os.path.join(FINAL_OUT_DIR, "fusion_final_audit.json")
    with open(audit_path) as f:
        audit = json.load(f)

    assert audit["selection_basis"]["validation_mae"] == 5.8851
    assert audit["selection_basis"]["test_set_used_for_selection"] is False
    assert audit["final_unbiased_test_performance"]["MAE"] == pytest.approx(5.9537, abs=1e-3)
    assert audit["final_unbiased_test_performance"]["N"] == 4500
