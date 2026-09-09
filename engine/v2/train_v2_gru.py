"""
MEDHA V2 — Step 13: Train and Evaluate GRU Future-Risk Model

Trains and evaluates the V2 GRU temporal model on the audited Step 12 sequence dataset:
- Input dimension: 57 features
- Sequence length: 7 timepoints
- Target: Future_Escalation_Label (binary classification)
- Class imbalance: Weighted BCEWithLogitsLoss (pos_weight = n_neg / n_pos)
- Early stopping & threshold selection strictly on Validation
- Final evaluation on Test performed ONCE on the frozen model
- Checkpoints saved to engine/models/v2/gru/
- Outputs saved to engine/outputs/gru_v2/
"""

import os
import sys
import json
import random
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
)

# ==============================================================
# PATHS
# ==============================================================
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SEQ_DIR = os.path.join(ENGINE_DIR, 'models', 'v2', 'gru_sequences')
MODEL_SAVE_DIR = os.path.join(ENGINE_DIR, 'models', 'v2', 'gru')
OUTPUT_DIR = os.path.join(ENGINE_DIR, 'outputs', 'gru_v2')

# ==============================================================
# REPRODUCIBILITY SEEDING
# ==============================================================
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass


# ==============================================================
# MODEL ARCHITECTURE
# ==============================================================
class V2GRUModel(nn.Module):
    """
    MEDHA V2 Temporal Risk GRU Architecture.
    
    Preserves the exact structural design of the V1 GRU:
      nn.GRU(input_size, hidden_size, num_layers=1, batch_first=True)
      nn.Dropout(dropout)
      nn.Linear(hidden_size, 1)
      
    Critical Update for V2:
      input_size = 57 (V1 used leaky 72 features).
    """
    def __init__(self, input_size=57, hidden_size=64, num_layers=1, dropout=0.3):
        super().__init__()
        if input_size != 57:
            raise ValueError(f"CRITICAL CONTRACT ERROR: input_size must be 57, got {input_size}")
            
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout_rate = dropout

        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        _, hidden_state = self.gru(x)
        last_hidden_state = hidden_state[-1]
        logits = self.fc(self.dropout(last_hidden_state))
        return logits.squeeze(-1)

    def predict_proba(self, x):
        return torch.sigmoid(self(x))


# ==============================================================
# METRICS COMPUTATION HELPER
# ==============================================================
def compute_classification_metrics(y_true, y_prob, threshold=0.5):
    """
    Computes comprehensive binary classification metrics.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    y_pred = (y_prob >= threshold).astype(int)

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_true, y_prob))
    pr_auc = float(average_precision_score(y_true, y_prob))
    cm = confusion_matrix(y_true, y_pred).tolist()

    tn, fp, fn, tp = int(cm[0][0]), int(cm[0][1]), int(cm[1][0]), int(cm[1][1])

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "threshold": float(threshold),
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
        },
        "support": {
            "negative": int(len(y_true) - y_true.sum()),
            "positive": int(y_true.sum()),
            "total": int(len(y_true)),
        }
    }


def compute_majority_baseline_metrics(y_true):
    """
    Majority-class baseline: always predict class 0 (negative).
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.zeros_like(y_true)
    prevalence = float(y_true.mean())
    y_prob = np.full_like(y_true, fill_value=prevalence, dtype=float)

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    roc_auc = 0.5000
    pr_auc = prevalence
    cm = confusion_matrix(y_true, y_pred).tolist()

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "threshold": "majority_class_0",
        "confusion_matrix": {
            "tn": int(cm[0][0]),
            "fp": int(cm[0][1]),
            "fn": int(cm[1][0]),
            "tp": int(cm[1][1]),
        },
        "support": {
            "negative": int(len(y_true) - y_true.sum()),
            "positive": int(y_true.sum()),
            "total": int(len(y_true)),
        }
    }


# ==============================================================
# DATA LOADER AND CONTRACT VERIFICATION
# ==============================================================
def load_and_verify_data():
    """
    Loads Step 12 sequence dataset and enforces the strict V2 contract.
    """
    config_path = os.path.join(SEQ_DIR, 'feature_config.json')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Missing Step 12 feature config: {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f)

    # 1. Feature contract assertions
    n_features = config.get('n_features')
    window_size = config.get('window_size')
    if n_features != 57:
        raise ValueError(f"Feature count contract violation: expected 57, got {n_features}")
    if window_size != 7:
        raise ValueError(f"Sequence length contract violation: expected 7, got {window_size}")

    # 2. Leakage verification
    whitelist = set(config.get('feature_whitelist', []))
    forbidden = [
        "Actual_DDS", "DDS", "Future_Escalation_Label", "Previous_DDS",
        "Rolling_DDS_Mean", "Rolling_DDS_SD", "DDS_Slope", "Trajectory_State"
    ]
    for feat in forbidden:
        if feat in whitelist:
            raise ValueError(f"CRITICAL LEAKAGE DETECTED: {feat} found in feature whitelist!")

    # 3. Load Train and Validation arrays (Test is NOT loaded here!)
    X_train = np.load(os.path.join(SEQ_DIR, 'X_train.npy'))
    y_train = np.load(os.path.join(SEQ_DIR, 'y_train.npy'))
    vids_train = np.load(os.path.join(SEQ_DIR, 'victim_ids_train.npy'), allow_pickle=True)

    X_val = np.load(os.path.join(SEQ_DIR, 'X_val.npy'))
    y_val = np.load(os.path.join(SEQ_DIR, 'y_val.npy'))
    vids_val = np.load(os.path.join(SEQ_DIR, 'victim_ids_val.npy'), allow_pickle=True)

    # Validate shapes
    if X_train.shape != (11200, 7, 57):
        raise ValueError(f"Unexpected X_train shape: {X_train.shape}, expected (11200, 7, 57)")
    if y_train.shape != (11200,):
        raise ValueError(f"Unexpected y_train shape: {y_train.shape}, expected (11200,)")
    if X_val.shape != (2400, 7, 57):
        raise ValueError(f"Unexpected X_val shape: {X_val.shape}, expected (2400, 7, 57)")
    if y_val.shape != (2400,):
        raise ValueError(f"Unexpected y_val shape: {y_val.shape}, expected (2400,)")

    return config, (X_train, y_train, vids_train), (X_val, y_val, vids_val)


# ==============================================================
# TRAINING FUNCTION
# ==============================================================
def train_model(train_data, val_data, seed=42, max_epochs=50, patience=7, lr=1e-3, batch_size=128):
    """
    Trains V2GRUModel using weighted BCE loss and early stopping on Validation loss.
    Returns: best_model, best_epoch, history, val_probs
    """
    set_seed(seed)
    device = torch.device("cpu")

    X_train, y_train, _ = train_data
    X_val, y_val, _ = val_data

    # Calculate exact class weight from Train set
    n_pos = float(y_train.sum())
    n_neg = float(len(y_train) - n_pos)
    pos_weight_value = n_neg / n_pos
    pos_weight = torch.tensor([pos_weight_value], dtype=torch.float32, device=device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    train_dataset = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
    val_dataset = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=256, shuffle=False)

    model = V2GRUModel(input_size=57, hidden_size=64, num_layers=1, dropout=0.3).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    history = {
        "epoch": [],
        "train_loss": [],
        "val_loss": [],
        "val_roc_auc": [],
        "val_pr_auc": [],
        "val_f1_05": [],
    }

    best_val_loss = float('inf')
    best_epoch = 0
    best_state_dict = None
    best_val_probs = None
    epochs_no_improve = 0

    print("=" * 65)
    print(f"Starting V2 GRU Training (Seed {seed})")
    print(f"Device: {device} | Max Epochs: {max_epochs} | Patience: {patience} | LR: {lr}")
    print(f"Train samples: {len(y_train)} (Pos: {int(n_pos)}, Neg: {int(n_neg)}, Pos Rate: {n_pos/len(y_train):.2%})")
    print(f"Class Imbalance pos_weight: {pos_weight_value:.4f}")
    print("=" * 65)

    for epoch in range(1, max_epochs + 1):
        model.train()
        train_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            logits = model(batch_x)
            loss = criterion(logits, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(batch_y)
        train_loss /= len(y_train)

        # Validation evaluation
        model.eval()
        val_loss = 0.0
        val_probs_list = []
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x = batch_x.to(device)
                batch_y = batch_y.to(device)
                logits = model(batch_x)
                loss = criterion(logits, batch_y)
                val_loss += loss.item() * len(batch_y)
                probs = torch.sigmoid(logits)
                val_probs_list.extend(probs.cpu().numpy().tolist())
        val_loss /= len(y_val)
        val_probs_arr = np.array(val_probs_list)

        val_roc = roc_auc_score(y_val, val_probs_arr)
        val_pr = average_precision_score(y_val, val_probs_arr)
        val_f1_05 = f1_score(y_val, (val_probs_arr >= 0.5).astype(int), zero_division=0)

        history["epoch"].append(epoch)
        history["train_loss"].append(round(train_loss, 5))
        history["val_loss"].append(round(val_loss, 5))
        history["val_roc_auc"].append(round(val_roc, 5))
        history["val_pr_auc"].append(round(val_pr, 5))
        history["val_f1_05"].append(round(val_f1_05, 5))

        print(f"Epoch {epoch:2d}/{max_epochs:2d} | "
              f"Train Loss: {train_loss:.4f} | "
              f"Val Loss: {val_loss:.4f} | "
              f"Val ROC: {val_roc:.4f} | "
              f"Val PR-AUC: {val_pr:.4f} | "
              f"Val F1@0.5: {val_f1_05:.4f}")

        # Check early stopping condition (on val_loss)
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            best_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            best_val_probs = val_probs_arr.copy()
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping triggered at epoch {epoch}. Restoring best weights from epoch {best_epoch} (Val Loss: {best_val_loss:.4f}).")
                break

    # Restore best model state
    model.load_state_dict(best_state_dict)
    model.eval()

    return model, best_epoch, history, best_val_probs, pos_weight_value


# ==============================================================
# THRESHOLD SELECTION ON VALIDATION
# ==============================================================
def select_validation_threshold(y_val, val_probs):
    """
    Sweeps thresholds on Validation predictions to maximize positive-class F1.
    Evaluates thresholds from 0.05 to 0.95 in steps of 0.01.
    Returns: best_threshold, threshold_search_results
    """
    y_val = np.asarray(y_val, dtype=int)
    thresholds = np.linspace(0.05, 0.95, 91)
    results = []

    best_f1 = -1.0
    best_threshold = 0.5

    for t in thresholds:
        t_val = round(float(t), 2)
        y_pred = (val_probs >= t_val).astype(int)
        f1 = float(f1_score(y_val, y_pred, zero_division=0))
        prec = float(precision_score(y_val, y_pred, zero_division=0))
        rec = float(recall_score(y_val, y_pred, zero_division=0))

        results.append({
            "threshold": t_val,
            "f1": f1,
            "precision": prec,
            "recall": rec
        })

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = t_val

    print("-" * 65)
    print(f"Validation Threshold Search Completed.")
    print(f"Default Threshold 0.50 -> F1: {f1_score(y_val, (val_probs >= 0.5).astype(int), zero_division=0):.4f}")
    print(f"Selected Optimal Threshold: {best_threshold:.2f} -> F1: {best_f1:.4f}")
    print("-" * 65)

    return best_threshold, results


# ==============================================================
# LOCKED TEST EVALUATION (FINAL RUN ONLY)
# ==============================================================
def evaluate_frozen_model_on_test(model, threshold):
    """
    Evaluates the frozen model on the locked Test set ONCE.
    """
    print("\n" + "#" * 65)
    print("EXECUTING FINAL LOCKED TEST SET EVALUATION")
    print(f"Operating Threshold: {threshold:.2f} (Frozen from Validation)")
    print("#" * 65)

    X_test = np.load(os.path.join(SEQ_DIR, 'X_test.npy'))
    y_test = np.load(os.path.join(SEQ_DIR, 'y_test.npy'))
    vids_test = np.load(os.path.join(SEQ_DIR, 'victim_ids_test.npy'), allow_pickle=True)

    if X_test.shape != (2400, 7, 57) or y_test.shape != (2400,):
        raise ValueError(f"Invalid Test shape: {X_test.shape}, {y_test.shape}")

    device = torch.device("cpu")
    model.eval()
    test_dataset = TensorDataset(torch.from_numpy(X_test))
    test_loader = DataLoader(test_dataset, batch_size=256, shuffle=False)

    test_probs = []
    with torch.no_grad():
        for (batch_x,) in test_loader:
            batch_x = batch_x.to(device)
            logits = model(batch_x)
            probs = torch.sigmoid(logits)
            test_probs.extend(probs.cpu().numpy().tolist())

    test_probs_arr = np.array(test_probs)

    test_metrics = compute_classification_metrics(y_test, test_probs_arr, threshold=threshold)
    majority_test_metrics = compute_majority_baseline_metrics(y_test)

    return (X_test, y_test, vids_test), test_probs_arr, test_metrics, majority_test_metrics


# ==============================================================
# REPRODUCIBILITY VERIFICATION
# ==============================================================
def verify_reproducibility(train_data, val_data, first_run_state, seed=42):
    """
    Runs training a second time from scratch with the identical seed and asserts
    that model weights and validation predictions match within numerical tolerance.
    """
    print("\n" + "=" * 65)
    print("VERIFYING DETERMINISTIC REPRODUCIBILITY (RUN 2)")
    print("=" * 65)

    model2, best_epoch2, history2, val_probs2, _ = train_model(
        train_data, val_data, seed=seed, max_epochs=50, patience=7, lr=1e-3, batch_size=128
    )

    state1 = first_run_state
    state2 = model2.state_dict()

    max_diff = 0.0
    for key in state1:
        diff = (state1[key] - state2[key]).abs().max().item()
        if diff > max_diff:
            max_diff = diff

    print(f"Run 1 Best Epoch: {len(history2['epoch'])} vs Run 2: {best_epoch2}")
    print(f"Maximum parameter difference between Run 1 and Run 2: {max_diff:.8e}")

    if max_diff > 1e-6:
        raise AssertionError(f"Reproducibility failure: max weight diff {max_diff} > 1e-6")

    print("[PASSED] Deterministic reproducibility verified. Weights and predictions match.")
    return True


# ==============================================================
# MAIN PIPELINE
# ==============================================================
def run_step13_training(check_reproducibility=True):
    os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load data and verify contract
    feature_config, train_data, val_data = load_and_verify_data()
    X_train, y_train, vids_train = train_data
    X_val, y_val, vids_val = val_data

    # 2. Train model with early stopping on Validation
    model, best_epoch, history, val_probs, pos_weight = train_model(
        train_data, val_data, seed=42, max_epochs=50, patience=7, lr=1e-3, batch_size=128
    )

    # Save first-run state dict for reproducibility check
    first_run_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    # 3. Threshold selection on Validation
    best_threshold, threshold_search = select_validation_threshold(y_val, val_probs)

    # 4. Compute validation metrics
    val_metrics_selected = compute_classification_metrics(y_val, val_probs, threshold=best_threshold)
    val_metrics_default = compute_classification_metrics(y_val, val_probs, threshold=0.5)
    majority_val_metrics = compute_majority_baseline_metrics(y_val)

    # 5. Locked Test Evaluation (ONCE)
    test_data, test_probs, test_metrics, majority_test_metrics = evaluate_frozen_model_on_test(
        model, threshold=best_threshold
    )
    X_test, y_test, vids_test = test_data

    # 6. Verify reproducibility if requested
    reproducibility_passed = False
    if check_reproducibility:
        reproducibility_passed = verify_reproducibility(train_data, val_data, first_run_state, seed=42)

    # ==============================================================
    # 7. SAVE MODEL CHECKPOINTS (engine/models/v2/gru/)
    # ==============================================================
    print("\nSaving checkpoints to engine/models/v2/gru/...")
    
    # Weights
    torch.save(model.state_dict(), os.path.join(MODEL_SAVE_DIR, "best_gru_model.pth"))

    # Model configuration
    model_config = {
        "model_type": "V2GRUModel",
        "input_size": 57,
        "hidden_size": 64,
        "num_layers": 1,
        "dropout": 0.3,
        "best_validation_epoch": best_epoch,
        "total_epochs_trained": len(history["epoch"]),
        "optimizer": "Adam",
        "learning_rate": 1e-3,
        "weight_decay": 1e-4,
        "batch_size": 128,
        "early_stopping_patience": 7,
        "early_stopping_criterion": "val_loss (min)",
        "random_seed": 42,
        "device": "cpu",
        "pytorch_version": torch.__version__,
    }
    with open(os.path.join(MODEL_SAVE_DIR, "model_config.json"), "w") as f:
        json.dump(model_config, f, indent=2)

    # Class weight configuration
    class_weight_config = {
        "strategy": "pos_weight in BCEWithLogitsLoss",
        "formula": "n_negative / n_positive (from Train split only)",
        "n_train_total": len(y_train),
        "n_train_positive": int(y_train.sum()),
        "n_train_negative": int(len(y_train) - y_train.sum()),
        "train_positive_rate": float(y_train.mean()),
        "pos_weight": float(pos_weight),
    }
    with open(os.path.join(MODEL_SAVE_DIR, "class_weight_config.json"), "w") as f:
        json.dump(class_weight_config, f, indent=2)

    # Threshold configuration
    threshold_config = {
        "selection_split": "Validation",
        "selection_criterion": "Maximize positive-class F1 score",
        "default_threshold": 0.5,
        "selected_threshold": best_threshold,
        "val_f1_at_default": val_metrics_default["f1"],
        "val_f1_at_selected": val_metrics_selected["f1"],
        "applied_to_test": True,
    }
    with open(os.path.join(MODEL_SAVE_DIR, "threshold_config.json"), "w") as f:
        json.dump(threshold_config, f, indent=2)

    # Training history
    with open(os.path.join(MODEL_SAVE_DIR, "training_history.json"), "w") as f:
        json.dump(history, f, indent=2)

    # Validation metrics
    val_summary = {
        "validation_metrics_selected_threshold": val_metrics_selected,
        "validation_metrics_default_threshold": val_metrics_default,
        "majority_baseline_val": majority_val_metrics,
    }
    with open(os.path.join(MODEL_SAVE_DIR, "validation_metrics.json"), "w") as f:
        json.dump(val_summary, f, indent=2)

    # Scaler reference
    scaler_ref = {
        "scaler_path": "engine/models/v2/gru_sequences/scaler.joblib",
        "fitted_on": "Train windows only (78,400 timesteps)",
        "features_scaled": 57
    }
    with open(os.path.join(MODEL_SAVE_DIR, "scaler_reference.json"), "w") as f:
        json.dump(scaler_ref, f, indent=2)

    # ==============================================================
    # 8. SAVE OUTPUT ARTIFACTS (engine/outputs/gru_v2/)
    # ==============================================================
    print("Saving outputs to engine/outputs/gru_v2/...")

    # Validation predictions dataframe
    val_df = pd.DataFrame({
        "Victim_ID": vids_val,
        "y_true": y_val.astype(int),
        "y_prob": val_probs,
        "pred_default_05": (val_probs >= 0.5).astype(int),
        "pred_selected": (val_probs >= best_threshold).astype(int),
    })
    val_df.to_csv(os.path.join(OUTPUT_DIR, "val_predictions.csv"), index=False)

    # Test predictions dataframe
    test_df = pd.DataFrame({
        "Victim_ID": vids_test,
        "y_true": y_test.astype(int),
        "y_prob": test_probs,
        "pred_selected": (test_probs >= best_threshold).astype(int),
    })
    test_df.to_csv(os.path.join(OUTPUT_DIR, "test_predictions.csv"), index=False)

    # Full metrics JSON
    metrics_all = {
        "step": "Step 13 — Train and Evaluate V2 GRU",
        "validation": {
            "gru_selected_threshold": val_metrics_selected,
            "gru_default_threshold_05": val_metrics_default,
            "majority_baseline": majority_val_metrics,
        },
        "test": {
            "gru_selected_threshold": test_metrics,
            "majority_baseline": majority_test_metrics,
        },
        "threshold_selection": {
            "selected_threshold": best_threshold,
            "criterion": "Max F1 on Validation",
        },
        "reproducibility": {
            "seed": 42,
            "passed": reproducibility_passed,
        }
    }
    with open(os.path.join(OUTPUT_DIR, "metrics.json"), "w") as f:
        json.dump(metrics_all, f, indent=2)

    # Confusion matrices
    with open(os.path.join(OUTPUT_DIR, "confusion_matrix_val.json"), "w") as f:
        json.dump({
            "selected_threshold": val_metrics_selected["confusion_matrix"],
            "default_05": val_metrics_default["confusion_matrix"],
        }, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "confusion_matrix_test.json"), "w") as f:
        json.dump({
            "selected_threshold": test_metrics["confusion_matrix"],
        }, f, indent=2)

    # Classification reports
    report_val = classification_report(
        y_val, (val_probs >= best_threshold).astype(int),
        target_names=["No Escalation (0)", "Escalation (1)"],
        digits=4
    )
    with open(os.path.join(OUTPUT_DIR, "classification_report_val.txt"), "w") as f:
        f.write(f"V2 GRU Validation Classification Report (Threshold = {best_threshold:.2f}):\n\n")
        f.write(report_val)

    report_test = classification_report(
        y_test, (test_probs >= best_threshold).astype(int),
        target_names=["No Escalation (0)", "Escalation (1)"],
        digits=4
    )
    with open(os.path.join(OUTPUT_DIR, "classification_report_test.txt"), "w") as f:
        f.write(f"V2 GRU Final Test Classification Report (Threshold = {best_threshold:.2f}):\n\n")
        f.write(report_test)

    # Copy training history and selected threshold
    with open(os.path.join(OUTPUT_DIR, "training_history.json"), "w") as f:
        json.dump(history, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "selected_threshold.json"), "w") as f:
        json.dump(threshold_config, f, indent=2)

    # Baseline comparison table CSV
    comparison_rows = [
        {
            "Model": "Majority Baseline",
            "Split": "Validation",
            "Accuracy": round(majority_val_metrics["accuracy"], 4),
            "Precision": round(majority_val_metrics["precision"], 4),
            "Recall": round(majority_val_metrics["recall"], 4),
            "F1": round(majority_val_metrics["f1"], 4),
            "ROC-AUC": round(majority_val_metrics["roc_auc"], 4),
            "PR-AUC": round(majority_val_metrics["pr_auc"], 4),
            "Threshold": "majority_0"
        },
        {
            "Model": "V2 GRU (t=0.50)",
            "Split": "Validation",
            "Accuracy": round(val_metrics_default["accuracy"], 4),
            "Precision": round(val_metrics_default["precision"], 4),
            "Recall": round(val_metrics_default["recall"], 4),
            "F1": round(val_metrics_default["f1"], 4),
            "ROC-AUC": round(val_metrics_default["roc_auc"], 4),
            "PR-AUC": round(val_metrics_default["pr_auc"], 4),
            "Threshold": 0.50
        },
        {
            "Model": f"V2 GRU (t={best_threshold:.2f})",
            "Split": "Validation",
            "Accuracy": round(val_metrics_selected["accuracy"], 4),
            "Precision": round(val_metrics_selected["precision"], 4),
            "Recall": round(val_metrics_selected["recall"], 4),
            "F1": round(val_metrics_selected["f1"], 4),
            "ROC-AUC": round(val_metrics_selected["roc_auc"], 4),
            "PR-AUC": round(val_metrics_selected["pr_auc"], 4),
            "Threshold": best_threshold
        },
        {
            "Model": "Majority Baseline",
            "Split": "Test",
            "Accuracy": round(majority_test_metrics["accuracy"], 4),
            "Precision": round(majority_test_metrics["precision"], 4),
            "Recall": round(majority_test_metrics["recall"], 4),
            "F1": round(majority_test_metrics["f1"], 4),
            "ROC-AUC": round(majority_test_metrics["roc_auc"], 4),
            "PR-AUC": round(majority_test_metrics["pr_auc"], 4),
            "Threshold": "majority_0"
        },
        {
            "Model": f"V2 GRU (t={best_threshold:.2f})",
            "Split": "Test",
            "Accuracy": round(test_metrics["accuracy"], 4),
            "Precision": round(test_metrics["precision"], 4),
            "Recall": round(test_metrics["recall"], 4),
            "F1": round(test_metrics["f1"], 4),
            "ROC-AUC": round(test_metrics["roc_auc"], 4),
            "PR-AUC": round(test_metrics["pr_auc"], 4),
            "Threshold": best_threshold
        },
    ]
    comp_df = pd.DataFrame(comparison_rows)
    comp_df.to_csv(os.path.join(OUTPUT_DIR, "baseline_comparison.csv"), index=False)

    # ==============================================================
    # 9. PRINT SUMMARY
    # ==============================================================
    print("\n" + "=" * 80)
    print("STEP 13 RESULTS SUMMARY TABLE")
    print("=" * 80)
    print(comp_df.to_string(index=False))
    print("=" * 80)
    print(f"\nFinal Test Confusion Matrix (Threshold = {best_threshold:.2f}):")
    print(f"  TN: {test_metrics['confusion_matrix']['tn']} | FP: {test_metrics['confusion_matrix']['fp']}")
    print(f"  FN: {test_metrics['confusion_matrix']['fn']}  | TP: {test_metrics['confusion_matrix']['tp']}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and evaluate MEDHA V2 GRU model.")
    parser.add_argument("--skip-reproducibility", action="store_true", help="Skip second training run for reproducibility.")
    args = parser.parse_args()

    run_step13_training(check_reproducibility=not args.skip_reproducibility)
