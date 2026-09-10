"""
Test script for MEDHA V2 Feature Policy.
Validates the hard-fail behaviors, specialist boundaries, and export logic.
"""

import sys
import os
import json
import pytest

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
        get_allowed_dds_features,
        get_all_approved_dds_features,
        get_all_approved_structured_dds_features,
        export_policy_to_json,
        V2_DDS_APPROVED_FEATURES,
        V2_STRUCTURED_DDS_FEATURES,
        V2_TEXT_DDS_FEATURES,
        V2_VOICE_DDS_FEATURES,
    )
except ImportError:
    from v2_feature_policy import (
        validate_dds_features,
        validate_structured_specialist_features,
        get_allowed_dds_features,
        get_all_approved_dds_features,
        get_all_approved_structured_dds_features,
        export_policy_to_json,
        V2_DDS_APPROVED_FEATURES,
        V2_STRUCTURED_DDS_FEATURES,
        V2_TEXT_DDS_FEATURES,
        V2_VOICE_DDS_FEATURES,
    )

def test_approved_features_pass():
    validate_dds_features(["Mood", "Stress", "Engagement_Score"])

def test_excluded_features_fail():
    excluded = [
        "Previous_DDS", "Rolling_DDS_Mean", "Rolling_DDS_SD", "DDS_Slope",
        "Recent_Change_Rate", "Recent_Max_DDS", "Recent_Min_DDS", "Delta_DDS",
        "DDS_Deviation_From_Baseline", "Baseline_DDS"
    ]
    for f in excluded:
        with pytest.raises(ValueError, match="EXCLUDED"):
            validate_dds_features([f])

def test_quarantined_features_fail():
    quarantined = ["Trajectory_State", "Discordance_Test_Feature", "Discordance_Example_Flag", "Diary_Distress_Feature"]
    for f in quarantined:
        with pytest.raises(ValueError, match="QUARANTINED"):
            validate_dds_features([f])

def test_targets_fail():
    targets = ["DDS", "Future_Escalation_Label"]
    for f in targets:
        with pytest.raises(ValueError, match="TARGET"):
            validate_dds_features([f])

def test_metadata_fail():
    ids = ["Victim_ID", "Case_ID", "Timepoint", "Date_Time"]
    for f in ids:
        with pytest.raises(ValueError, match="ID/METADATA"):
            validate_dds_features([f])

def test_post_hoc_fail():
    posthoc = ["Intervention", "Follow_Up"]
    for f in posthoc:
        with pytest.raises(ValueError, match="POST-HOC"):
            validate_dds_features([f])

def test_unknown_features_fail():
    with pytest.raises(ValueError, match="UNKNOWN"):
        validate_dds_features(["Some_New_Numeric_Feature"])

def test_duplicate_features_fail():
    with pytest.raises(ValueError, match="Duplicate"):
        validate_dds_features(["Mood", "Mood"])

def test_strict_get_allowed_dds_features():
    all_mixed_columns = [
        "Victim_ID", "Mood", "Previous_DDS", "Unknown_Col", "Text_Distress", "DDS"
    ]
    with pytest.raises(ValueError):
        get_allowed_dds_features(all_mixed_columns)

    valid_columns = ["Mood", "Text_Distress"]
    allowed = get_allowed_dds_features(valid_columns)
    assert allowed == valid_columns

def test_structured_specialist_boundary():
    structured = get_all_approved_structured_dds_features()
    assert len(structured) == 42
    assert validate_structured_specialist_features(structured) is True

    # Test features are rejected
    for text_f in V2_TEXT_DDS_FEATURES:
        with pytest.raises(ValueError, match="TEXT"):
            validate_structured_specialist_features(["Mood", text_f])

    # Voice features are rejected
    for voice_f in V2_VOICE_DDS_FEATURES:
        with pytest.raises(ValueError, match="VOICE"):
            validate_structured_specialist_features(["Mood", voice_f])

    # Set disjointness
    assert len(set(structured) & set(V2_TEXT_DDS_FEATURES)) == 0
    assert len(set(structured) & set(V2_VOICE_DDS_FEATURES)) == 0
    assert set(structured) | set(V2_TEXT_DDS_FEATURES) | set(V2_VOICE_DDS_FEATURES) == set(V2_DDS_APPROVED_FEATURES)

def test_export_policy_json():
    json_path = os.path.join(ENGINE_DIR, 'data', 'processed', 'v2_feature_policy.json')
    export_policy_to_json(json_path)
    assert os.path.exists(json_path)
    with open(json_path, 'r') as f:
        data = json.load(f)
        assert len(data["approved_features"]) == len(V2_DDS_APPROVED_FEATURES)
        assert len(data["structured_specialist_features"]) == 42
        assert len(data["text_specialist_features"]) == 9
        assert len(data["voice_specialist_features"]) == 9

if __name__ == "__main__":
    print("=== Testing Feature Policy Validator ===\n")
    test_approved_features_pass()
    print("[PASS] Approved features are accepted")
    test_excluded_features_fail()
    print("[PASS] Excluded features are rejected")
    test_quarantined_features_fail()
    print("[PASS] Quarantined features are rejected")
    test_targets_fail()
    print("[PASS] Targets are rejected")
    test_metadata_fail()
    print("[PASS] Metadata columns are rejected")
    test_post_hoc_fail()
    print("[PASS] Post-hoc columns are rejected")
    test_unknown_features_fail()
    print("[PASS] Unknown features are rejected")
    test_duplicate_features_fail()
    print("[PASS] Duplicate features are rejected")
    test_strict_get_allowed_dds_features()
    print("[PASS] get_allowed_dds_features strict checks passed")
    test_structured_specialist_boundary()
    print("[PASS] Structured specialist boundary validation passed")
    test_export_policy_json()
    print("[PASS] JSON policy exported successfully")
    print("\nALL TESTS PASSED SUCCESSFULLY.")
