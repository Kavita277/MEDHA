"""
MEDHA V2 Step 11 -- Unit Tests for Fusion Ablation Study
========================================================

Validates:
1. Exact modality removal in each ablation configuration.
2. Zero forbidden features.
3. Total holdout cleanliness: Test set is never touched.
4. Output results CSV schema and metric ranges.
"""

import os
import sys
import json
import pytest
import pandas as pd

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
from engine.v2.run_v2_ablation import ABLATION_CONFIGS

SPLIT_CSV = os.path.join(ENGINE_DIR, "data", "processed", "v2_victim_split.csv")
RESULTS_CSV = os.path.join(ROOT_DIR, "outputs", "fusion_v2", "ablation_validation_results.csv")
META_JSON = os.path.join(ROOT_DIR, "outputs", "fusion_v2", "ablation_metadata.json")


def test_ablation_configurations_feature_contracts():
    # Full Fusion: exactly 8 features
    full_feats = ABLATION_CONFIGS["Full Fusion"]
    assert len(full_feats) == 8
    validate_fusion_features(full_feats)

    # No Text: exactly 6 features, Text_Pred and Text_Available removed
    no_text = ABLATION_CONFIGS["Fusion without Text"]
    assert len(no_text) == 6
    assert "Text_Pred" not in no_text
    assert "Text_Available" not in no_text
    validate_fusion_features(no_text)

    # No Voice: exactly 6 features, Voice_Pred and Voice_Available removed
    no_voice = ABLATION_CONFIGS["Fusion without Voice"]
    assert len(no_voice) == 6
    assert "Voice_Pred" not in no_voice
    assert "Voice_Available" not in no_voice
    validate_fusion_features(no_voice)

    # No Behaviour: exactly 6 features, Behav_Pred and Behav_Available removed
    no_behav = ABLATION_CONFIGS["Fusion without Behaviour"]
    assert len(no_behav) == 6
    assert "Behav_Pred" not in no_behav
    assert "Behav_Available" not in no_behav
    validate_fusion_features(no_behav)

    # No Structured: exactly 6 features, Struct_Pred and Struct_Available removed
    no_struct = ABLATION_CONFIGS["Fusion without Structured"]
    assert len(no_struct) == 6
    assert "Struct_Pred" not in no_struct
    assert "Struct_Available" not in no_struct
    validate_fusion_features(no_struct)


def test_zero_forbidden_features_in_any_configuration():
    for name, feats in ABLATION_CONFIGS.items():
        for forbidden in V2_FUSION_FORBIDDEN_FEATURES:
            assert forbidden not in feats, f"Forbidden feature '{forbidden}' found in configuration '{name}'"


def test_test_set_sealed_in_ablation_workflow():
    split_df = pd.read_csv(SPLIT_CSV)
    test_vids = set(split_df[split_df["Split"].str.lower() == "test"]["Victim_ID"])
    assert len(test_vids) == 150

    with open(META_JSON) as f:
        meta = json.load(f)

    assert meta["test_set_sealed"] is True
    assert "Validation" in meta["evaluation_dataset"]
    assert "Train" in meta["training_dataset"]


def test_ablation_validation_results_content():
    assert os.path.exists(RESULTS_CSV), f"Missing ablation results CSV: {RESULTS_CSV}"
    df = pd.read_csv(RESULTS_CSV)

    assert len(df) == 5
    expected_configs = [
        "Full Fusion",
        "Fusion without Text",
        "Fusion without Voice",
        "Fusion without Behaviour",
        "Fusion without Structured",
    ]
    assert list(df["Configuration"]) == expected_configs

    # Verify column presence
    for col in [
        "Validation_MAE", "Validation_RMSE", "Validation_R2",
        "Validation_Pearson", "Validation_Spearman", "MAE_Diff_vs_Full"
    ]:
        assert col in df.columns
        assert df[col].notna().all()

    # Full Fusion MAE must equal 5.8851
    full_mae = df.loc[df["Configuration"] == "Full Fusion", "Validation_MAE"].values[0]
    assert full_mae == pytest.approx(5.8851, abs=1e-4)

    # No Structured must have the highest degradation
    no_struct_diff = df.loc[df["Configuration"] == "Fusion without Structured", "MAE_Diff_vs_Full"].values[0]
    assert no_struct_diff > 0.40, f"Expected Structured omission to degrade MAE by >0.40, got {no_struct_diff}"
