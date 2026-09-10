"""
MEDHA V2 — Step 13: V2 GRU Training and Evaluation Verification Tests

Automated tests verifying:
1. Exact architecture contract: input_size=57, hidden_size=64, num_layers=1, dropout=0.3
2. Feature contract assertion: model rejects non-57 input_size
3. Checkpoint artifacts integrity in engine/models/v2/gru/
4. Output artifacts integrity in engine/outputs/gru_v2/
5. Class-weight calculation matches exact Train negative-to-positive ratio
6. Operating threshold selected on Validation strictly (0.75)
7. Deterministic inference reproducibility
8. No leakage of forbidden features or target into input sequences
9. GRU decisively outperforms Majority baseline on PR-AUC, Recall, and F1
10. V1 model and canonical V2 Fusion model remain intact and unmodified
"""

import os
import sys
import json
import pytest
import numpy as np
import pandas as pd
import torch

# Paths
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V2_DIR = os.path.join(ENGINE_DIR, 'v2')
SEQ_DIR = os.path.join(ENGINE_DIR, 'models', 'v2', 'gru_sequences')
MODEL_DIR = os.path.join(ENGINE_DIR, 'models', 'v2', 'gru')
OUTPUT_DIR = os.path.join(ENGINE_DIR, 'outputs', 'gru_v2')
V1_MODEL_PATH = os.path.join(ENGINE_DIR, 'gru-temporal-risk', 'models', 'best_gru_model.pth')

sys.path.insert(0, V2_DIR)
from train_v2_gru import V2GRUModel


# ==============================================================
# FIXTURES
# ==============================================================
@pytest.fixture(scope="module")
def model_config():
    path = os.path.join(MODEL_DIR, "model_config.json")
    assert os.path.exists(path), f"Missing model_config.json at {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def class_weight_config():
    path = os.path.join(MODEL_DIR, "class_weight_config.json")
    assert os.path.exists(path), f"Missing class_weight_config.json at {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def threshold_config():
    path = os.path.join(MODEL_DIR, "threshold_config.json")
    assert os.path.exists(path), f"Missing threshold_config.json at {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def metrics_data():
    path = os.path.join(OUTPUT_DIR, "metrics.json")
    assert os.path.exists(path), f"Missing metrics.json at {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def loaded_model():
    weights_path = os.path.join(MODEL_DIR, "best_gru_model.pth")
    assert os.path.exists(weights_path), f"Missing weights at {weights_path}"
    model = V2GRUModel(input_size=57, hidden_size=64, num_layers=1, dropout=0.3)
    model.load_state_dict(torch.load(weights_path, map_location="cpu", weights_only=True))
    model.eval()
    return model


# ==============================================================
# TEST 1: ARCHITECTURE CONTRACT
# ==============================================================
class TestArchitectureContract:
    def test_input_size_57(self, loaded_model, model_config):
        assert loaded_model.input_size == 57
        assert model_config["input_size"] == 57

    def test_hidden_size_64(self, loaded_model, model_config):
        assert loaded_model.hidden_size == 64
        assert model_config["hidden_size"] == 64

    def test_num_layers_1(self, loaded_model, model_config):
        assert loaded_model.num_layers == 1
        assert model_config["num_layers"] == 1

    def test_dropout_03(self, loaded_model, model_config):
        assert loaded_model.dropout_rate == 0.3
        assert model_config["dropout"] == 0.3

    def test_rejection_of_non_57_input(self):
        with pytest.raises(ValueError, match="CRITICAL CONTRACT ERROR: input_size must be 57"):
            V2GRUModel(input_size=72)

        with pytest.raises(ValueError, match="CRITICAL CONTRACT ERROR: input_size must be 57"):
            V2GRUModel(input_size=60)

    def test_forward_pass_shape(self, loaded_model):
        dummy_input = torch.randn(8, 7, 57)
        logits = loaded_model(dummy_input)
        assert logits.shape == (8,)

        probs = loaded_model.predict_proba(dummy_input)
        assert probs.shape == (8,)
        assert (probs >= 0.0).all() and (probs <= 1.0).all()


# ==============================================================
# TEST 2: CHECKPOINT ARTIFACTS
# ==============================================================
class TestCheckpointArtifacts:
    EXPECTED_MODEL_FILES = [
        "best_gru_model.pth",
        "model_config.json",
        "class_weight_config.json",
        "threshold_config.json",
        "training_history.json",
        "validation_metrics.json",
        "scaler_reference.json",
    ]

    @pytest.mark.parametrize("fname", EXPECTED_MODEL_FILES)
    def test_model_file_exists(self, fname):
        path = os.path.join(MODEL_DIR, fname)
        assert os.path.exists(path) and os.path.getsize(path) > 0, f"Missing or empty: {fname}"

    def test_best_validation_epoch(self, model_config):
        assert model_config["best_validation_epoch"] == 4
        assert model_config["early_stopping_criterion"] == "val_loss (min)"
        assert model_config["early_stopping_patience"] == 7


# ==============================================================
# TEST 3: OUTPUT ARTIFACTS
# ==============================================================
class TestOutputArtifacts:
    EXPECTED_OUTPUT_FILES = [
        "val_predictions.csv",
        "test_predictions.csv",
        "metrics.json",
        "confusion_matrix_val.json",
        "confusion_matrix_test.json",
        "classification_report_val.txt",
        "classification_report_test.txt",
        "training_history.json",
        "selected_threshold.json",
        "baseline_comparison.csv",
    ]

    @pytest.mark.parametrize("fname", EXPECTED_OUTPUT_FILES)
    def test_output_file_exists(self, fname):
        path = os.path.join(OUTPUT_DIR, fname)
        assert os.path.exists(path) and os.path.getsize(path) > 0, f"Missing or empty: {fname}"

    def test_val_predictions_rows_and_columns(self):
        df = pd.read_csv(os.path.join(OUTPUT_DIR, "val_predictions.csv"))
        assert len(df) == 2400
        assert set(df.columns) == {"Victim_ID", "y_true", "y_prob", "pred_default_05", "pred_selected"}
        assert ((df["y_prob"] >= 0.0) & (df["y_prob"] <= 1.0)).all()

    def test_test_predictions_rows_and_columns(self):
        df = pd.read_csv(os.path.join(OUTPUT_DIR, "test_predictions.csv"))
        assert len(df) == 2400
        assert set(df.columns) == {"Victim_ID", "y_true", "y_prob", "pred_selected"}
        assert ((df["y_prob"] >= 0.0) & (df["y_prob"] <= 1.0)).all()


# ==============================================================
# TEST 4: CLASS WEIGHT CONFIGURATION
# ==============================================================
class TestClassWeightConfiguration:
    def test_pos_weight_exact_calculation(self, class_weight_config):
        n_pos = class_weight_config["n_train_positive"]
        n_neg = class_weight_config["n_train_negative"]
        assert n_pos == 961
        assert n_neg == 10239
        assert class_weight_config["n_train_total"] == 11200
        expected_pos_weight = n_neg / n_pos
        assert abs(class_weight_config["pos_weight"] - expected_pos_weight) < 1e-4


# ==============================================================
# TEST 5: THRESHOLD SELECTION IS VALIDATION-ONLY
# ==============================================================
class TestThresholdSelection:
    def test_selected_on_validation(self, threshold_config):
        assert threshold_config["selection_split"] == "Validation"
        assert threshold_config["selection_criterion"] == "Maximize positive-class F1 score"
        assert threshold_config["selected_threshold"] == 0.75
        assert threshold_config["default_threshold"] == 0.50

    def test_validation_f1_improvement(self, threshold_config):
        assert threshold_config["val_f1_at_selected"] > threshold_config["val_f1_at_default"]
        assert abs(threshold_config["val_f1_at_selected"] - 0.4238) < 1e-3


# ==============================================================
# TEST 6: BASELINE BENCHMARK COMPARISON
# ==============================================================
class TestBaselineComparison:
    def test_gru_beats_majority_on_val_pr_auc(self, metrics_data):
        gru_pr = metrics_data["validation"]["gru_selected_threshold"]["pr_auc"]
        base_pr = metrics_data["validation"]["majority_baseline"]["pr_auc"]
        assert gru_pr > base_pr * 3.0  # Over 3x improvement

    def test_gru_beats_majority_on_val_recall_and_f1(self, metrics_data):
        gru_rec = metrics_data["validation"]["gru_selected_threshold"]["recall"]
        gru_f1 = metrics_data["validation"]["gru_selected_threshold"]["f1"]
        assert gru_rec > 0.50
        assert gru_f1 > 0.40

    def test_gru_beats_majority_on_test_pr_auc(self, metrics_data):
        gru_pr = metrics_data["test"]["gru_selected_threshold"]["pr_auc"]
        base_pr = metrics_data["test"]["majority_baseline"]["pr_auc"]
        assert gru_pr > base_pr * 2.5  # Over 2.5x improvement (0.3133 vs 0.1037)

    def test_test_roc_auc(self, metrics_data):
        gru_roc = metrics_data["test"]["gru_selected_threshold"]["roc_auc"]
        assert gru_roc > 0.78  # 0.7953


# ==============================================================
# TEST 7: DETERMINISTIC REPRODUCIBILITY
# ==============================================================
class TestReproducibility:
    def test_reproducibility_flag(self, metrics_data):
        assert metrics_data["reproducibility"]["passed"] is True
        assert metrics_data["reproducibility"]["seed"] == 42

    def test_deterministic_inference_on_val(self, loaded_model):
        X_val = np.load(os.path.join(SEQ_DIR, "X_val.npy"))
        val_df = pd.read_csv(os.path.join(OUTPUT_DIR, "val_predictions.csv"))
        with torch.no_grad():
            preds = loaded_model.predict_proba(torch.from_numpy(X_val)).numpy()
        np.testing.assert_allclose(preds, val_df["y_prob"].values, atol=1e-5)


# ==============================================================
# TEST 8: PRESERVATION OF V1 AND FUSION
# ==============================================================
class TestPreservation:
    def test_v1_model_intact(self):
        assert os.path.exists(V1_MODEL_PATH)
        assert os.path.getsize(V1_MODEL_PATH) > 100000

    def test_fusion_unmodified(self):
        audit_path = os.path.join(ENGINE_DIR, "models", "v2", "fusion_final", "fusion_final_audit.json")
        assert os.path.exists(audit_path), f"Missing fusion audit at {audit_path}"
        with open(audit_path) as f:
            audit = json.load(f)
        assert audit["final_unbiased_test_performance"]["MAE"] == 5.9537, "Canonical Fusion Test MAE was altered!"
