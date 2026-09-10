"""
MEDHA V2 — Step 12: GRU Sequence Leakage Audit Tests

Automated tests verifying:
1. No victim overlap between Train/Val/Test
2. No forbidden features in feature config
3. Feature count = 57
4. Correct window shapes
5. No NaN in targets or features
6. Scaler fitted on Train only
7. Label distribution sanity
8. Sequence count verification
9. Deterministic reproducibility
"""

import numpy as np
import json
import os
import sys
import pytest
import joblib

# ==============================================================
# PATHS
# ==============================================================
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SEQ_DIR = os.path.join(ENGINE_DIR, 'models', 'v2', 'gru_sequences')
V2_DIR = os.path.join(ENGINE_DIR, 'v2')

sys.path.insert(0, V2_DIR)
from v2_feature_policy import (
    V2_DDS_EXCLUDED_FEATURES,
    V2_DDS_TARGET_FEATURES,
    V2_DDS_QUARANTINED_FEATURES,
    V2_DDS_POST_HOC_FEATURES,
    V2_DDS_ID_METADATA_FEATURES,
    validate_dds_features,
)


# ==============================================================
# FIXTURES
# ==============================================================
@pytest.fixture(scope="module")
def feature_config():
    path = os.path.join(SEQ_DIR, 'feature_config.json')
    assert os.path.exists(path), f"feature_config.json not found at {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def train_data():
    X = np.load(os.path.join(SEQ_DIR, 'X_train.npy'))
    y = np.load(os.path.join(SEQ_DIR, 'y_train.npy'))
    vids = np.load(os.path.join(SEQ_DIR, 'victim_ids_train.npy'), allow_pickle=True)
    return X, y, vids


@pytest.fixture(scope="module")
def val_data():
    X = np.load(os.path.join(SEQ_DIR, 'X_val.npy'))
    y = np.load(os.path.join(SEQ_DIR, 'y_val.npy'))
    vids = np.load(os.path.join(SEQ_DIR, 'victim_ids_val.npy'), allow_pickle=True)
    return X, y, vids


@pytest.fixture(scope="module")
def test_data():
    X = np.load(os.path.join(SEQ_DIR, 'X_test.npy'))
    y = np.load(os.path.join(SEQ_DIR, 'y_test.npy'))
    vids = np.load(os.path.join(SEQ_DIR, 'victim_ids_test.npy'), allow_pickle=True)
    return X, y, vids


@pytest.fixture(scope="module")
def scaler():
    path = os.path.join(SEQ_DIR, 'scaler.joblib')
    assert os.path.exists(path), f"scaler.joblib not found at {path}"
    return joblib.load(path)


# ==============================================================
# TEST 1: NO VICTIM OVERLAP
# ==============================================================
class TestVictimIsolation:
    def test_train_val_no_overlap(self, train_data, val_data):
        """Train and Validation must not share any Victim_IDs."""
        train_vids = set(train_data[2])
        val_vids = set(val_data[2])
        overlap = train_vids & val_vids
        assert len(overlap) == 0, f"LEAKAGE: {len(overlap)} victims in both Train and Val: {overlap}"

    def test_train_test_no_overlap(self, train_data, test_data):
        """Train and Test must not share any Victim_IDs."""
        train_vids = set(train_data[2])
        test_vids = set(test_data[2])
        overlap = train_vids & test_vids
        assert len(overlap) == 0, f"LEAKAGE: {len(overlap)} victims in both Train and Test: {overlap}"

    def test_val_test_no_overlap(self, val_data, test_data):
        """Validation and Test must not share any Victim_IDs."""
        val_vids = set(val_data[2])
        test_vids = set(test_data[2])
        overlap = val_vids & test_vids
        assert len(overlap) == 0, f"LEAKAGE: {len(overlap)} victims in both Val and Test: {overlap}"

    def test_victim_counts(self, train_data, val_data, test_data):
        """Verify correct victim counts: 700/150/150."""
        assert len(set(train_data[2])) == 700, f"Expected 700 train victims, got {len(set(train_data[2]))}"
        assert len(set(val_data[2])) == 150, f"Expected 150 val victims, got {len(set(val_data[2]))}"
        assert len(set(test_data[2])) == 150, f"Expected 150 test victims, got {len(set(test_data[2]))}"


# ==============================================================
# TEST 2: NO FORBIDDEN FEATURES
# ==============================================================
class TestFeaturePolicy:
    def test_no_excluded_dds_features(self, feature_config):
        """No DDS-derived excluded features in whitelist."""
        whitelist = set(feature_config['feature_whitelist'])
        for f in V2_DDS_EXCLUDED_FEATURES:
            assert f not in whitelist, f"LEAKAGE: Excluded feature '{f}' in whitelist!"

    def test_no_target_features(self, feature_config):
        """No target features (DDS, Future_Escalation_Label) in whitelist."""
        whitelist = set(feature_config['feature_whitelist'])
        for f in V2_DDS_TARGET_FEATURES:
            assert f not in whitelist, f"LEAKAGE: Target feature '{f}' in whitelist!"

    def test_no_quarantined_features(self, feature_config):
        """No quarantined features in whitelist."""
        whitelist = set(feature_config['feature_whitelist'])
        for f in V2_DDS_QUARANTINED_FEATURES:
            assert f not in whitelist, f"QUARANTINE: Feature '{f}' in whitelist!"

    def test_no_post_hoc_features(self, feature_config):
        """No post-hoc outcome features in whitelist."""
        whitelist = set(feature_config['feature_whitelist'])
        for f in V2_DDS_POST_HOC_FEATURES:
            assert f not in whitelist, f"LEAKAGE: Post-hoc feature '{f}' in whitelist!"

    def test_no_id_metadata_features(self, feature_config):
        """No ID/metadata features in whitelist."""
        whitelist = set(feature_config['feature_whitelist'])
        for f in V2_DDS_ID_METADATA_FEATURES:
            assert f not in whitelist, f"ID/metadata feature '{f}' in whitelist!"

    def test_explicit_forbidden_absent(self, feature_config):
        """Specific high-risk features must be absent."""
        whitelist = set(feature_config['feature_whitelist'])
        forbidden = [
            "Previous_DDS", "Rolling_DDS_Mean", "Rolling_DDS_SD", "DDS_Slope",
            "Recent_Change_Rate", "Recent_Max_DDS", "Recent_Min_DDS", "Delta_DDS",
            "DDS_Deviation_From_Baseline", "Baseline_DDS",
            "DDS", "Future_Escalation_Label",
            "Trajectory_State", "Intervention", "Follow_Up",
        ]
        for f in forbidden:
            assert f not in whitelist, f"FORBIDDEN: '{f}' found in feature whitelist!"

    def test_all_features_pass_central_validation(self, feature_config):
        """Every feature in the whitelist must pass validate_dds_features()."""
        try:
            validate_dds_features(feature_config['feature_whitelist'])
        except ValueError as e:
            pytest.fail(f"Feature policy validation failed: {e}")


# ==============================================================
# TEST 3: FEATURE COUNT
# ==============================================================
class TestFeatureCount:
    def test_whitelist_has_57_features(self, feature_config):
        """Whitelist must have exactly 57 features."""
        assert feature_config['n_features'] == 57, (
            f"Expected 57 features, got {feature_config['n_features']}"
        )
        assert len(feature_config['feature_whitelist']) == 57, (
            f"Expected 57 features in list, got {len(feature_config['feature_whitelist'])}"
        )

    def test_no_duplicate_features(self, feature_config):
        """No duplicate features in whitelist."""
        whitelist = feature_config['feature_whitelist']
        assert len(whitelist) == len(set(whitelist)), "Duplicate features found!"

    def test_x_feature_dimension(self, train_data, val_data, test_data):
        """X arrays must have 57 features in the last dimension."""
        assert train_data[0].shape[2] == 57, f"X_train features: {train_data[0].shape[2]}"
        assert val_data[0].shape[2] == 57, f"X_val features: {val_data[0].shape[2]}"
        assert test_data[0].shape[2] == 57, f"X_test features: {test_data[0].shape[2]}"


# ==============================================================
# TEST 4: WINDOW SHAPES
# ==============================================================
class TestWindowShapes:
    def test_3d_train(self, train_data):
        """X_train must be 3D: (n_windows, 7, 57)."""
        X, y, vids = train_data
        assert X.ndim == 3, f"Expected 3D, got {X.ndim}D"
        assert X.shape[1] == 7, f"Window size: {X.shape[1]}"
        assert X.shape[2] == 57, f"Features: {X.shape[2]}"

    def test_3d_val(self, val_data):
        """X_val must be 3D: (n_windows, 7, 57)."""
        X, y, vids = val_data
        assert X.ndim == 3 and X.shape[1] == 7 and X.shape[2] == 57

    def test_3d_test(self, test_data):
        """X_test must be 3D: (n_windows, 7, 57)."""
        X, y, vids = test_data
        assert X.ndim == 3 and X.shape[1] == 7 and X.shape[2] == 57

    def test_y_matches_x_length(self, train_data, val_data, test_data):
        """y arrays must match X array lengths."""
        assert len(train_data[1]) == train_data[0].shape[0]
        assert len(val_data[1]) == val_data[0].shape[0]
        assert len(test_data[1]) == test_data[0].shape[0]

    def test_vids_matches_x_length(self, train_data, val_data, test_data):
        """victim_ids arrays must match X array lengths."""
        assert len(train_data[2]) == train_data[0].shape[0]
        assert len(val_data[2]) == val_data[0].shape[0]
        assert len(test_data[2]) == test_data[0].shape[0]


# ==============================================================
# TEST 5: NO NaN IN DATA
# ==============================================================
class TestNoNaN:
    def test_no_nan_in_x_train(self, train_data):
        assert not np.any(np.isnan(train_data[0])), "NaN found in X_train!"

    def test_no_nan_in_x_val(self, val_data):
        assert not np.any(np.isnan(val_data[0])), "NaN found in X_val!"

    def test_no_nan_in_x_test(self, test_data):
        assert not np.any(np.isnan(test_data[0])), "NaN found in X_test!"

    def test_no_nan_in_y_train(self, train_data):
        assert not np.any(np.isnan(train_data[1])), "NaN found in y_train!"

    def test_no_nan_in_y_val(self, val_data):
        assert not np.any(np.isnan(val_data[1])), "NaN found in y_val!"

    def test_no_nan_in_y_test(self, test_data):
        assert not np.any(np.isnan(test_data[1])), "NaN found in y_test!"

    def test_no_inf_in_x_train(self, train_data):
        assert not np.any(np.isinf(train_data[0])), "Inf found in X_train!"

    def test_no_inf_in_x_val(self, val_data):
        assert not np.any(np.isinf(val_data[0])), "Inf found in X_val!"

    def test_no_inf_in_x_test(self, test_data):
        assert not np.any(np.isinf(test_data[0])), "Inf found in X_test!"


# ==============================================================
# TEST 6: SCALER FITTED ON TRAIN ONLY
# ==============================================================
class TestScalerIntegrity:
    def test_scaler_n_samples(self, scaler, train_data, feature_config):
        """Scaler must be fitted on exactly n_train_windows * window_size rows."""
        n_train_windows = train_data[0].shape[0]
        window_size = feature_config['window_size']
        expected = n_train_windows * window_size
        actual = int(scaler.n_samples_seen_)
        assert actual == expected, (
            f"Scaler fitted on {actual} samples, expected {expected} "
            f"({n_train_windows} windows * {window_size} timesteps)"
        )

    def test_scaler_n_features(self, scaler):
        """Scaler must have 57 features."""
        assert len(scaler.mean_) == 57, f"Scaler has {len(scaler.mean_)} features, expected 57"
        assert len(scaler.scale_) == 57, f"Scaler has {len(scaler.scale_)} scale values"

    def test_scaler_config_matches(self, scaler, feature_config):
        """Scaler n_samples_seen_ must match feature_config."""
        assert int(scaler.n_samples_seen_) == feature_config['scaler_n_samples_seen']


# ==============================================================
# TEST 7: LABEL DISTRIBUTION
# ==============================================================
class TestLabelDistribution:
    def test_binary_labels_train(self, train_data):
        """All train labels must be 0 or 1."""
        y = train_data[1]
        unique = set(np.unique(y))
        assert unique.issubset({0.0, 1.0}), f"Non-binary labels: {unique}"

    def test_binary_labels_val(self, val_data):
        """All val labels must be 0 or 1."""
        y = val_data[1]
        unique = set(np.unique(y))
        assert unique.issubset({0.0, 1.0}), f"Non-binary labels: {unique}"

    def test_binary_labels_test(self, test_data):
        """All test labels must be 0 or 1."""
        y = test_data[1]
        unique = set(np.unique(y))
        assert unique.issubset({0.0, 1.0}), f"Non-binary labels: {unique}"

    def test_positive_rate_reasonable(self, train_data, val_data, test_data):
        """Positive rate should be between 3% and 15% for all splits."""
        for name, data in [("train", train_data), ("val", val_data), ("test", test_data)]:
            y = data[1]
            pos_rate = y.mean()
            assert 0.03 <= pos_rate <= 0.15, (
                f"{name} positive rate {pos_rate:.4f} outside expected range [0.03, 0.15]"
            )

    def test_label_counts_match_config(self, train_data, val_data, test_data, feature_config):
        """Label counts must match feature_config."""
        dist = feature_config['label_distribution']
        assert int((train_data[1] == 1).sum()) == dist['train']['pos']
        assert int((train_data[1] == 0).sum()) == dist['train']['neg']
        assert int((val_data[1] == 1).sum()) == dist['val']['pos']
        assert int((val_data[1] == 0).sum()) == dist['val']['neg']
        assert int((test_data[1] == 1).sum()) == dist['test']['pos']
        assert int((test_data[1] == 0).sum()) == dist['test']['neg']


# ==============================================================
# TEST 8: SEQUENCE COUNT VERIFICATION
# ==============================================================
class TestSequenceCounts:
    def test_shapes_match_config(self, train_data, val_data, test_data, feature_config):
        """Array shapes must match feature_config."""
        shapes = feature_config['shapes']
        assert list(train_data[0].shape) == shapes['X_train']
        assert list(train_data[1].shape) == shapes['y_train']
        assert list(val_data[0].shape) == shapes['X_val']
        assert list(val_data[1].shape) == shapes['y_val']
        assert list(test_data[0].shape) == shapes['X_test']
        assert list(test_data[1].shape) == shapes['y_test']

    def test_total_windows_plausible(self, train_data, val_data, test_data):
        """Total windows should be less than total rows (30000)."""
        total = train_data[0].shape[0] + val_data[0].shape[0] + test_data[0].shape[0]
        assert total < 30000, f"Too many windows: {total}"
        assert total > 10000, f"Too few windows: {total}"

    def test_train_has_most_windows(self, train_data, val_data, test_data):
        """Train should have ~70% of windows."""
        total = train_data[0].shape[0] + val_data[0].shape[0] + test_data[0].shape[0]
        train_pct = train_data[0].shape[0] / total
        assert 0.60 <= train_pct <= 0.80, f"Train percentage {train_pct:.2%} outside expected range"


# ==============================================================
# TEST 9: DATA TYPE VERIFICATION
# ==============================================================
class TestDataTypes:
    def test_x_float32(self, train_data, val_data, test_data):
        """X arrays should be float32."""
        assert train_data[0].dtype == np.float32
        assert val_data[0].dtype == np.float32
        assert test_data[0].dtype == np.float32

    def test_y_float32(self, train_data, val_data, test_data):
        """y arrays should be float32."""
        assert train_data[1].dtype == np.float32
        assert val_data[1].dtype == np.float32
        assert test_data[1].dtype == np.float32


# ==============================================================
# TEST 10: ARTIFACT COMPLETENESS
# ==============================================================
class TestArtifactCompleteness:
    EXPECTED_FILES = [
        'X_train.npy', 'y_train.npy', 'victim_ids_train.npy',
        'X_val.npy', 'y_val.npy', 'victim_ids_val.npy',
        'X_test.npy', 'y_test.npy', 'victim_ids_test.npy',
        'X_train_unscaled.npy', 'X_val_unscaled.npy', 'X_test_unscaled.npy',
        'scaler.joblib', 'feature_config.json',
    ]

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_file_exists(self, filename):
        path = os.path.join(SEQ_DIR, filename)
        assert os.path.exists(path), f"Missing artifact: {filename}"

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_file_not_empty(self, filename):
        path = os.path.join(SEQ_DIR, filename)
        assert os.path.getsize(path) > 0, f"Empty artifact: {filename}"
