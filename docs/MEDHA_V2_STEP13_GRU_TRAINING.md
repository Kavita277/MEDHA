# MEDHA V2 — Step 13: GRU Temporal Model Training and Evaluation Report

## Executive Summary

This report documents the first official model training and evaluation of the **MEDHA V2 Gated Recurrent Unit (GRU) Future-Risk Model**. The V2 GRU forecasts future clinical escalation (`Future_Escalation_Label`) 7 days in advance using 7-step longitudinal sequences across 57 approved, leakage-free features constructed in Step 12.

Training strictly followed the V2 methodological protocol:
- **Class imbalance**: Handled via weighted binary cross-entropy with logits ($\text{pos\_weight} \approx 10.6545$ derived strictly from Train).
- **Split isolation**: Model fitting on Train (11,200 sequences), early stopping and threshold calibration strictly on Validation (2,400 sequences), and final evaluation executed **once** on the frozen Test set (2,400 sequences).
- **V1 and Fusion preservation**: Legacy V1 engine and canonical V2 Fusion model (Test MAE = 5.9537) remain strictly untouched.

---

## 1. Existing V1 GRU Problem

The legacy V1 GRU temporal engine (`engine/gru-temporal-risk/`) suffered from severe methodological flaws:
1. **DDS Leakage**: `preprocessing.py` dynamically selected all numeric columns minus 4 identifiers. Consequently, `Previous_DDS`, `Rolling_DDS_Mean`, `Rolling_DDS_SD`, `DDS_Slope`, `Baseline_DDS`, and even `DDS` itself were fed directly into the model, leaking target distress information.
2. **Hardcoded Input Dimension**: The V1 inference API and training code were hardcoded to `input_size = 72`.
3. **Absence of Victim-Level Split Isolation**: V1 did not adhere to a victim-isolated partition, risking victim-level cross-contamination.
4. **Uncontrolled Test Tuning**: Operating thresholds and model iterations were inspected on the Test partition.

---

## 2. V2 Model Architecture

The V2 GRU preserves the lean recurrent architecture of MEDHA while updating the input contract to 57 features:

```python
class V2GRUModel(nn.Module):
    def __init__(self, input_size=57, hidden_size=64, num_layers=1, dropout=0.3):
        super().__init__()
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
```

- **Recurrent Layer**: 1-layer PyTorch GRU, `batch_first=True`
- **Hidden Dimension**: 64 units
- **Regularization**: `nn.Dropout(p=0.3)` applied to the final recurrent hidden state
- **Classifier Head**: `nn.Linear(64, 1)` emitting a scalar logit
- **Parameter Count**: 23,873 trainable parameters

---

## 3. Input Size

- **Features**: Exactly **57 numeric features** per timepoint.
- **Contract Enforcement**: Hard assertion prevents training or inference if `input_size != 57`. Non-57 inputs immediately raise `ValueError`.

---

## 4. Sequence Length

- **Window Size**: Exactly **7 timepoints** ($[t-7, t-1]$).
- **Temporal Alignment**: Windows strictly contain historical observations strictly preceding target timepoint $t$ ($\max(\text{input timestep}) < \text{target timestep}$).

---

## 5. Target Definition

- **Target Column**: `Future_Escalation_Label`
- **Task**: Binary classification (0 = No escalation within the next 7 days, 1 = Escalation event occurs within the next 7 days).
- **Constraint**: Target is strictly binary. Problem was NOT converted into regression.

---

## 6. Class Distribution

The sequence dataset exhibits significant positive-class sparsity:

| Split | Victims | Total Windows | Negative (0) | Positive (1) | Positive Rate |
|---|---|---|---|---|---|
| **Train** | 700 | 11,200 | 10,239 | 961 | 8.58% |
| **Validation** | 150 | 2,400 | 2,162 | 238 | 9.92% |
| **Test** | 150 | 2,400 | 2,151 | 249 | 10.38% |
| **Total** | 1,000 | 16,000 | 14,552 | 1,448 | 9.05% |

---

## 7. Class-Imbalance Strategy

To prevent the model from collapsing into trivial negative predictions without looking at Test data:
- **Strategy**: Positive-class loss weighting using PyTorch's `BCEWithLogitsLoss(pos_weight=...)`.
- **Calculation Formula**:
  $$\text{pos\_weight} = \frac{N_{\text{Train, Negative}}}{N_{\text{Train, Positive}}} = \frac{10,239}{961} \approx 10.6545265$$
- **Leakage Prevention**: The weight was calculated **strictly on the Train split**. Validation and Test distributions were not used.

---

## 8. Loss Function

- **Function**: `torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor([10.6545]))`
- Combines a Sigmoid activation and binary cross-entropy into a single numerically stable layer while upweighting minority positive misclassifications by 10.65x.

---

## 9. Optimizer

- **Optimizer**: `torch.optim.Adam`
- **Weight Decay**: `1e-4` ($L_2$ penalty)

---

## 10. Learning Rate

- **Initial Learning Rate**: `1e-3` (0.001)

---

## 11. Batch Size

- **Train Batch Size**: 128 (shuffled per epoch)
- **Validation / Test Batch Size**: 256 (deterministic sequential evaluation)

---

## 12. Number of Epochs

- **Maximum Epochs Configured**: 50
- **Actual Epochs Run**: 11 (terminated by early stopping)

---

## 13. Early Stopping Configuration

- **Monitored Metric**: Validation Loss (`val_loss`, minimization)
- **Patience**: 7 epochs
- **Best Weights Restoration**: Enabled. The checkpoint with the lowest validation loss was restored.

---

## 14. Random Seed

- **Seed**: `42`
- **Deterministic Settings**:
  - `random.seed(42)`
  - `np.random.seed(42)`
  - `torch.manual_seed(42)`
  - `torch.backends.cudnn.deterministic = True`
  - `torch.backends.cudnn.benchmark = False`
  - `torch.use_deterministic_algorithms(True)`
- **Device**: CPU

---

## 15. Best Validation Epoch

- **Best Validation Epoch**: **Epoch 4**
- **Validation Loss at Best Epoch**: **1.0218**
- **Epoch Training Progression**:

| Epoch | Train Loss | Val Loss | Val ROC-AUC | Val PR-AUC | Val F1 (0.50) | Status |
|---|---|---|---|---|---|---|
| 1 | 1.0426 | 1.0344 | 0.8112 | 0.3695 | 0.3358 | |
| 2 | 0.9936 | 1.0405 | 0.8099 | 0.3686 | 0.3391 | |
| 3 | 0.9731 | 1.0528 | 0.8110 | 0.3731 | 0.3484 | |
| **4** | **0.9636** | **1.0218** | **0.8147** | **0.3754** | **0.3404** | **Best Checkpoint** |
| 5 | 0.9473 | 1.0250 | 0.8129 | 0.3777 | 0.3289 | |
| 6 | 0.9350 | 1.0297 | 0.8119 | 0.3771 | 0.3371 | |
| 7 | 0.9211 | 1.0453 | 0.8107 | 0.3679 | 0.3458 | |
| 8 | 0.8987 | 1.0521 | 0.8080 | 0.3619 | 0.3495 | |
| 9 | 0.8634 | 1.0441 | 0.8082 | 0.3552 | 0.3429 | |
| 10 | 0.8433 | 1.0640 | 0.7948 | 0.3417 | 0.3188 | |
| 11 | 0.8023 | 1.1024 | 0.8014 | 0.3394 | 0.3343 | Early Stop Triggered |

Weights from **Epoch 4** were restored.

---

## 16. Validation Metrics

Metrics evaluated on the 2,400 validation sequences at the restored Epoch 4 model:

- **ROC-AUC**: **0.8147**
- **PR-AUC**: **0.3754** (3.79x higher than validation prevalence of 0.0992)
- At default threshold 0.50: Accuracy = 0.7029, Precision = 0.2183, Recall = 0.7731, F1 = 0.3404
- At optimal threshold 0.75: Accuracy = 0.8629, Precision = 0.3634, Recall = 0.5084, F1 = 0.4238

---

## 17. Selected Threshold

- **Search Protocol**: Evaluated thresholds $\tau \in [0.05, 0.95]$ (step 0.01) on the Validation set.
- **Selection Criterion**: Maximize positive-class F1 score on Validation.
- **Selected Operating Threshold**: $\mathbf{\tau^* = 0.75}$
- **Validation F1 Gain**: Increased F1 from 0.3404 (@ 0.50) to 0.4238 (@ 0.75), reducing false alarms while retaining strong recall.
- **Lock**: Threshold $\tau^* = 0.75$ was frozen and saved prior to any Test evaluation.

---

## 18. Test Metrics

The frozen model with frozen threshold $\tau^* = 0.75$ was evaluated **once** on the 2,400 held-out Test sequences:

- **Accuracy**: **0.8358** (83.58%)
- **Precision**: **0.2981** (29.81%)
- **Recall**: **0.4297** (42.97%)
- **F1 Score**: **0.3520**
- **ROC-AUC**: **0.7953**
- **PR-AUC**: **0.3133** (3.02x higher than Test baseline prevalence of 0.1038)

---

## 19. Confusion Matrix

### Validation Set Confusion Matrix ($\tau^* = 0.75$)
- **True Negatives (TN)**: 1,950
- **False Positives (FP)**: 212
- **False Negatives (FN)**: 117
- **True Positives (TP)**: 121
- *Total Support*: 2,162 Negatives, 238 Positives

### Test Set Confusion Matrix ($\tau^* = 0.75$, Frozen)
- **True Negatives (TN)**: 1,899
- **False Positives (FP)**: 252
- **False Negatives (FN)**: 142
- **True Positives (TP)**: 107
- *Total Support*: 2,151 Negatives, 249 Positives

---

## 20. Baseline Comparison

### Required Result Table

| Model | Split | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Majority Baseline** | Validation | 0.9008 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0992 |
| **V2 GRU ($\tau=0.50$)** | Validation | 0.7029 | 0.2183 | 0.7731 | 0.3404 | 0.8147 | 0.3754 |
| **V2 GRU ($\tau=0.75$)** | Validation | **0.8629** | **0.3634** | **0.5084** | **0.4238** | **0.8147** | **0.3754** |
| **Majority Baseline** | Test | 0.8962 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.1037 |
| **V2 GRU ($\tau=0.75$)** | Test | **0.8358** | **0.2981** | **0.4297** | **0.3520** | **0.7953** | **0.3133** |

*Note: Per protocol, both default threshold 0.50 and selected threshold 0.75 are reported on Validation, but ONLY the frozen threshold 0.75 is applied to Test.*

### Assessment Against Baselines
- **PR-AUC**: The V2 GRU achieves a PR-AUC of **0.3133** on Test, representing a **3.02x improvement** over the trivial majority-class PR-AUC of 0.1037.
- **ROC-AUC**: At **0.7953**, the model demonstrates strong discriminatory capability between escalation and non-escalation sequences across thresholds.
- **Recall**: The model detects **43.0%** of future escalations 7 days in advance while maintaining an 83.6% accuracy.

---

## 21. Reproducibility Result

- **Test**: Two consecutive full training runs from scratch using seed 42 and PyTorch deterministic settings.
- **Parameter Check**: Maximum parameter difference across all model weight tensors:
  $$\max |\theta_{\text{Run 1}} - \theta_{\text{Run 2}}| = 0.00000000\times 10^0$$
- **Outcome**: `[PASSED]`. The training process is 100% bit-exact reproducible on CPU.

---

## 22. Artifact Locations

### Checkpoints (`engine/models/v2/gru/`)
- `best_gru_model.pth`: PyTorch state dict for the best model (Epoch 4).
- `model_config.json`: Architecture, hyperparameters, optimizer, and best epoch metadata.
- `class_weight_config.json`: Train positive/negative counts and exact `pos_weight` calculation.
- `threshold_config.json`: Frozen operating threshold ($\tau^* = 0.75$) and validation metrics.
- `training_history.json`: Loss and metric logs across all 11 epochs.
- `validation_metrics.json`: Validation evaluation metrics at $\tau = 0.50$ and $\tau = 0.75$.
- `scaler_reference.json`: Traceability pointer to Step 12 sequence scaler.

### Outputs (`engine/outputs/gru_v2/`)
- `val_predictions.csv`: 2,400 rows with true labels, predicted probabilities, and predictions.
- `test_predictions.csv`: 2,400 rows with true labels, predicted probabilities, and predictions.
- `metrics.json`: Complete serialized metrics for all splits and models.
- `confusion_matrix_val.json`: Confusion matrix entries on Validation.
- `confusion_matrix_test.json`: Confusion matrix entries on Test.
- `classification_report_val.txt`: Full classification report on Validation.
- `classification_report_test.txt`: Full classification report on Test.
- `baseline_comparison.csv`: Tabular comparison with Majority Baseline.

---

## 23. Limitations

1. **Class Sparsity**: The positive escalation rate is only ~8.6–10.4%. While weighted BCE and threshold calibration significantly improve PR-AUC (0.3133 vs 0.1037 baseline), precision remains at ~29.8% on Test. In clinical deployments, this represents approximately 2.3 false alarms per true positive alert.
2. **Fixed Sequence Length**: The model strictly requires 7 historical timepoints. Victims with fewer than 7 recorded check-ins cannot be scored by this temporal engine without padding or imputation.
3. **Linear Classifier Head**: The recurrent feature representation feeds through a single linear output layer. A multi-layer MLP head or bidirectional GRU may offer additional expressive power in future tuning phases.
4. **Non-Sequential Features**: Non-numeric features (`Case_Type`, `Case_Stage`, `Episode_Severity`) were excluded from the sequence representation to avoid premature categorical embedding complexity.

---

## Final Verification Checklist

- [x] Input size = 57 (verified and asserted in model)
- [x] Sequence length = 7
- [x] Target = `Future_Escalation_Label`
- [x] No `Future_Escalation_Label` in input features $X$
- [x] No Test-based model selection (early stopping strictly on Validation loss)
- [x] No Test-based threshold selection ($\tau^* = 0.75$ selected on Validation F1)
- [x] Scaler remains Train-fitted only (verified 78,400 seen samples)
- [x] V1 model untouched (`engine/gru-temporal-risk/models/best_gru_model.pth` preserved)
- [x] Canonical V2 Fusion model untouched (Test MAE = 5.9537 preserved)
- [x] Step 12 sequence artifacts untouched (all 69 Step 12 tests passing)
- [x] V2 GRU artifacts stored in dedicated directories (`engine/models/v2/gru/`, `engine/outputs/gru_v2/`)
- [x] Test set loaded and evaluated exactly once
