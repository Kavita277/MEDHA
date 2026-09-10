"""
MEDHA V2 Step 10B Correction -- Unit Tests for Leakage-Safe Fusion Pipeline
===========================================================================

Validates the corrected Step 10B Out-Of-Fold (OOF) fusion methodology:
1. Authoritative split integrity (700 Train / 150 Val / 150 Test, zero overlap).
2. Victim-level fold partitioning (5 folds, 140 victims each, zero fold overlap).
3. Exact OOF prediction coverage (21,000 rows, 0 duplicate keys, 0 missing OOF rows).
4. No in-sample stacking leakage.
5. Strict feature policy & zero forbidden features.
6. Validation-only candidate selection (Test set completely untouched).
7. Candidate A weights derived strictly from OOF training MAE.
8. Missing modality handling & availability flags.
9. Deterministic inference & model loading.
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
LONG_CSV  = os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv")
OOF_OUT_DIR = os.path.join(ENGINE_DIR, "outputs", "dds_v2", "fusion_oof")
OOF_MOD_DIR = os.path.join(ENGINE_DIR, "models", "v2", "fusion_oof")


# ===========================================================================
# 1. Authoritative Split Integrity
# ===========================================================================
def test_authoritative_split_integrity():
    split_df = pd.read_csv(SPLIT_CSV)
    train_vids = set(split_df[split_df["Split"].str.lower() == "train"]["Victim_ID"])
    val_vids   = set(split_df[split_df["Split"].str.lower() == "validation"]["Victim_ID"])
    test_vids  = set(split_df[split_df["Split"].str.lower() == "test"]["Victim_ID"])

    assert len(train_vids) == 700, f"Expected 700 train victims, got {len(train_vids)}"
    assert len(val_vids) == 150, f"Expected 150 val victims, got {len(val_vids)}"
    assert len(test_vids) == 150, f"Expected 150 test victims, got {len(test_vids)}"

    # Zero victim overlap
    assert len(train_vids & val_vids) == 0, "Train and Val victims overlap!"
    assert len(train_vids & test_vids) == 0, "Train and Test victims overlap!"
    assert len(val_vids & test_vids) == 0, "Val and Test victims overlap!"
    assert len(train_vids | val_vids | test_vids) == 1000, "Split does not cover all 1,000 victims!"


# ===========================================================================
# 2. Fold Partitioning Integrity
# ===========================================================================
def test_fold_assignments_integrity():
    fold_csv = os.path.join(OOF_OUT_DIR, "fusion_oof_fold_assignments.csv")
    assert os.path.exists(fold_csv), f"Missing fold assignments CSV: {fold_csv}"
    
    df = pd.read_csv(fold_csv)
    assert len(df) == 700, f"Expected 700 victim fold assignments, got {len(df)}"
    assert df["Victim_ID"].nunique() == 700, "Duplicate victims in fold assignments!"
    
    fold_counts = df["fold_id"].value_counts().to_dict()
    assert len(fold_counts) == 5, f"Expected 5 folds, got {len(fold_counts)}"
    for f in range(1, 6):
        assert fold_counts.get(f, 0) == 140, f"Fold {f} does not have exactly 140 victims! Got {fold_counts.get(f, 0)}"

    # Check that folds are mutually disjoint
    for f1 in range(1, 6):
        v1 = set(df[df["fold_id"] == f1]["Victim_ID"])
        for f2 in range(f1 + 1, 6):
            v2 = set(df[df["fold_id"] == f2]["Victim_ID"])
            assert len(v1 & v2) == 0, f"Folds {f1} and {f2} have overlapping victims!"


# ===========================================================================
# 3. OOF Train Predictions Integrity
# ===========================================================================
def test_oof_train_predictions_integrity():
    oof_csv = os.path.join(OOF_OUT_DIR, "fusion_oof_train_predictions.csv")
    assert os.path.exists(oof_csv), f"Missing OOF predictions CSV: {oof_csv}"

    df = pd.read_csv(oof_csv)
    assert len(df) == 21000, f"Expected 21,000 OOF rows, got {len(df)}"
    assert df["Victim_ID"].nunique() == 700, f"Expected 700 unique victims, got {df['Victim_ID'].nunique()}"

    # Verify each victim has exactly 30 timepoints
    v_counts = df.groupby("Victim_ID").size()
    assert (v_counts == 30).all(), "Every victim must have exactly 30 timepoints in OOF dataset!"

    # Verify zero duplicate (Victim_ID, Timepoint) keys
    assert not df.duplicated(subset=["Victim_ID", "Timepoint"]).any(), "Duplicate keys found in OOF dataset!"

    # Verify metadata columns
    assert (df["prediction_type"] == "OOF").all(), "All rows must have prediction_type == 'OOF'!"
    assert (df["fusion_training_split"] == "TRAIN").all(), "All rows must have fusion_training_split == 'TRAIN'!"
    assert df["fold_id"].isin([1, 2, 3, 4, 5]).all(), "Invalid fold_id values found!"


# ===========================================================================
# 4. Absence of In-Sample Predictions & Coverage
# ===========================================================================
def test_no_missing_and_no_in_sample_specialist_predictions():
    oof_csv = os.path.join(OOF_OUT_DIR, "fusion_oof_train_predictions.csv")
    df = pd.read_csv(oof_csv)

    # 1. Structured & Behaviour must have 100% valid predictions
    assert df["Struct_Pred"].notna().all(), "Missing Struct_Pred in OOF dataset!"
    assert df["Behav_Pred"].notna().all(), "Missing Behav_Pred in OOF dataset!"
    assert (df["Struct_Available"] == 1).all()
    assert (df["Behav_Available"] == 1).all()

    # 2. Text predictions: present if Text_Available==1, NaN if Text_Available==0
    avail_text = df[df["Text_Available"] == 1]
    unavail_text = df[df[ "Text_Available"] == 0]
    assert avail_text["Text_Pred"].notna().all(), "Available text has NaN predictions!"
    assert unavail_text["Text_Pred"].isna().all(), "Unavailable text must be masked (NaN)!"

    # 3. Voice predictions: present if Voice_Available==1, NaN if Voice_Available==0
    avail_voice = df[df["Voice_Available"] == 1]
    unavail_voice = df[df["Voice_Available"] == 0]
    assert avail_voice["Voice_Pred"].notna().all(), "Available voice has NaN predictions!"
    assert unavail_voice["Voice_Pred"].isna().all(), "Unavailable voice must be masked (NaN)!"


# ===========================================================================
# 5. Strict Feature Policy & Forbidden Features Enforcement
# ===========================================================================
def test_forbidden_features_and_leakage_policy():
    cfg_path = os.path.join(OOF_MOD_DIR, "fusion_feature_config.json")
    assert os.path.exists(cfg_path), f"Missing feature config: {cfg_path}"

    with open(cfg_path) as f:
        cfg = json.load(f)

    feature_order = cfg["feature_order"]
    validate_fusion_features(feature_order)

    # Assert no forbidden feature enters the model
    for forbidden in V2_FUSION_FORBIDDEN_FEATURES:
        assert forbidden not in feature_order, f"Forbidden feature '{forbidden}' found in feature_order!"

    assert "Future_Escalation_Label" not in feature_order
    assert "Actual_DDS" not in feature_order
    assert "DDS" not in feature_order
    assert "Previous_DDS" not in feature_order
    assert "Rolling_DDS_Mean" not in feature_order
    assert "DDS_Slope" not in feature_order
    assert "Trajectory_State" not in feature_order

    expected_features = [
        "Struct_Pred", "Text_Pred", "Voice_Pred", "Behav_Pred",
        "Struct_Available", "Text_Available", "Voice_Available", "Behav_Available"
    ]
    assert feature_order == expected_features, f"Feature order mismatch! Got {feature_order}"


# ===========================================================================
# 6. Candidate Selection Strictly on Validation
# ===========================================================================
def test_candidate_selection_strictly_on_validation():
    selected_path = os.path.join(OOF_MOD_DIR, "fusion_selected_model.json")
    metrics_path = os.path.join(OOF_OUT_DIR, "fusion_candidate_metrics.csv")
    meta_path = os.path.join(OOF_MOD_DIR, "fusion_oof_metadata.json")

    assert os.path.exists(selected_path)
    assert os.path.exists(metrics_path)
    assert os.path.exists(meta_path)

    with open(selected_path) as f:
        sel = json.load(f)

    with open(meta_path) as f:
        meta = json.load(f)

    metrics_df = pd.read_csv(metrics_path)

    # Verify candidate selection was by Validation MAE
    assert sel["selection_metric"] == "Validation MAE"
    assert "UNTOUCHED" in sel["test_split_status"]
    assert "TEST SET UNTOUCHED" in meta["test_status"]

    # Candidate with minimum Val_MAE must match selected_candidate
    best_candidate_expected = metrics_df.loc[metrics_df["Val_MAE"].idxmin(), "Candidate"]
    assert sel["selected_candidate"] == best_candidate_expected, (
        f"Selected {sel['selected_candidate']}, but minimum Val_MAE candidate was {best_candidate_expected}"
    )


# ===========================================================================
# 7. Candidate A Weights Derived from OOF Training MAE
# ===========================================================================
def test_candidate_a_weights_derived_from_oof():
    weights_path = os.path.join(OOF_MOD_DIR, "v2_fusion_oof_weights.json")
    meta_path = os.path.join(OOF_MOD_DIR, "fusion_oof_metadata.json")

    with open(weights_path) as f:
        w_data = json.load(f)
    with open(meta_path) as f:
        meta = json.load(f)

    assert w_data["derived_from"] == "OOF Training MAE"
    weights = w_data["weights"]
    
    # Check weights sum to 1.0
    assert sum(weights.values()) == pytest.approx(1.0, abs=1e-5)

    # Check inverse-MAE calculation: w_i = (1 / MAE_i) / sum(1 / MAE_j)
    oof_maes = {
        "structured": meta["specialist_oof_metrics"]["Struct_Pred"]["MAE"],
        "text": meta["specialist_oof_metrics"]["Text_Pred"]["MAE"],
        "voice": meta["specialist_oof_metrics"]["Voice_Pred"]["MAE"],
        "behaviour": meta["specialist_oof_metrics"]["Behav_Pred"]["MAE"],
    }
    inv_maes = {k: 1.0 / v for k, v in oof_maes.items()}
    sum_inv = sum(inv_maes.values())
    expected_weights = {k: inv_maes[k] / sum_inv for k in inv_maes}

    for k in weights:
        assert weights[k] == pytest.approx(expected_weights[k], abs=1e-4)


# ===========================================================================
# 8. Missing Modality Handling & Availability Flags
# ===========================================================================
def test_missing_modality_handling():
    val_csv = os.path.join(OOF_OUT_DIR, "fusion_validation_predictions.csv")
    df = pd.read_csv(val_csv)

    assert len(df) == 4500
    assert df["Victim_ID"].nunique() == 150

    # Availability flags exist and are binary
    for flag in ["Struct_Available", "Text_Available", "Voice_Available", "Behav_Available"]:
        assert flag in df.columns
        assert set(df[flag].unique()).issubset({0, 1})

    # When modality unavailable, its raw prediction is NaN/masked
    text_unavail = df[df["Text_Available"] == 0]
    voice_unavail = df[df["Voice_Available"] == 0]

    assert text_unavail["Text_Pred"].isna().all()
    assert voice_unavail["Voice_Pred"].isna().all()

    # Fusion prediction is non-null for all 4,500 validation rows
    assert df["Fusion_DDS_Prediction"].notna().all()
    assert (df["Fusion_DDS_Prediction"] >= 0.0).all()
    assert (df["Fusion_DDS_Prediction"] <= 100.0).all()


# ===========================================================================
# 9. Model Loading & Deterministic Inference
# ===========================================================================
def test_model_loading_and_deterministic_inference():
    model_json = os.path.join(OOF_MOD_DIR, "fusion_model.json")
    feat_json = os.path.join(OOF_MOD_DIR, "fusion_feature_config.json")

    assert os.path.exists(model_json)
    assert os.path.exists(feat_json)

    with open(feat_json) as f:
        feat_config = json.load(f)
    feature_order = feat_config["feature_order"]

    model = xgb.XGBRegressor()
    model.load_model(model_json)

    # Dummy inputs
    sample_input_1 = np.array([[60.0, 55.0, 50.0, 65.0, 1.0, 1.0, 1.0, 1.0]])
    sample_input_2 = np.array([[60.0, 0.0, 0.0, 65.0, 1.0, 0.0, 0.0, 1.0]])

    pred1_a = model.predict(sample_input_1)
    pred1_b = model.predict(sample_input_1)
    np.testing.assert_allclose(pred1_a, pred1_b)

    pred2_a = model.predict(sample_input_2)
    pred2_b = model.predict(sample_input_2)
    np.testing.assert_allclose(pred2_a, pred2_b)

    assert 0.0 <= pred1_a[0] <= 100.0
    assert 0.0 <= pred2_a[0] <= 100.0
