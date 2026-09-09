# Walkthrough — MEDHA V2 Step 10C

## Locked Final Fusion Evaluation and Audit

This walkthrough summarizes the execution, results, and verification of **MEDHA V2 Step 10C: Locked Final Fusion Evaluation and Audit**.

---

## 1. Context & Protocol

- **Frozen Model**: Candidate C (XGBoost Stacking Regressor), trained strictly on 5-fold Out-Of-Fold (OOF) predictions and selected on the Validation set (Validation MAE = **5.8851**).
- **Test Set Isolation**: The 150-victim Test set (4,500 longitudinal rows) was evaluated **exactly once** with the frozen model. No retraining, re-tuning, or model adjustments were permitted.
- **Artifact Protection**: Historical preliminary artifacts (`engine/models/v2/fusion/`, `walkthrough_step10c.md`) and OOF training artifacts (`engine/models/v2/fusion_oof/`) were preserved untouched. Corrected final evaluation results are stored in `engine/outputs/dds_v2/fusion_final/`.

---

## 2. Benchmark Results

### Primary Test Comparison (4,500 Test Rows, 150 Victims)

| Model | Evaluated Subset | N | Test MAE | Test RMSE | Test R² | Test Pearson |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train-Mean Baseline** | Full Test Set | 4,500 | 12.9648 | 16.1965 | -0.5187 | — |
| **Behaviour Specialist** (Ridge Ext-10) | Full Test Set | 4,500 | 7.3530 | 9.1945 | 0.5106 | 0.7147 |
| **Text Specialist** (Ridge Core-5) | Available Text Only | 3,362 | 6.4352 | 8.0783 | 0.6365 | 0.7978 |
| **Voice Specialist** (Ridge Core-5) | Available Voice Only| 1,692 | 6.3070 | 7.9104 | 0.6529 | 0.8082 |
| **Structured Specialist** (XGBoost) | Full Test Set | 4,500 | 6.1611 | 7.7353 | 0.6536 | 0.8086 |
| **MEDHA V2 Frozen Fusion (Candidate C)** | **Full Test Set** | **4,500** | **5.9537** | **7.4925** | **0.6750** | **0.8217** |

### Relative Improvements:
- **Fusion vs Structured Specialist**: **+3.37% improvement** (6.1611 $\rightarrow$ 5.9537 MAE) across all 4,500 rows.
- **Fusion vs Best Specialist**: **+3.37% improvement** over Structured (the best individual specialist).
- **Fusion vs Train-Mean Baseline**: **+54.08% improvement** (12.9648 $\rightarrow$ 5.9537 MAE).

---

## 3. Availability Stratification (Mutually Exclusive & Exhaustive)

| Stratum | Definition | N | % | Fusion MAE | Struct MAE | MAE Advantage vs Struct |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A. All Available** | Text=1, Voice=1 | 1,269 | 28.2% | **5.8929** | 6.3121 | **+0.4192 (+6.64%)** |
| **B. Voice Missing** | Text=1, Voice=0 | 2,093 | 46.5% | **5.9411** | 6.1231 | **+0.1820 (+2.97%)** |
| **C. Text Missing** | Text=0, Voice=1 | 423 | 9.4% | **6.0344** | 6.0690 | **+0.0346 (+0.57%)** |
| **D. Both Missing** | Text=0, Voice=0 | 715 | 15.9% | **6.0504** | 6.0584 | **+0.0080 (+0.13%)** |
| **Total** | — | **4,500** | **100%** | **5.9537** | **6.1611** | **+0.2074 (+3.37%)** |

*Key finding*: The fusion model delivers a monotonic advantage scaling with available modalities, achieving a **+0.4192 MAE reduction (+6.64% gain)** when all modalities are present, while gracefully stabilizing to Structured performance when modalities are missing.

---

## 4. Error & Longitudinal Diagnostics

- **Residual Mean (Bias)**: **+0.1195**
- **Median Absolute Error**: **4.9761**
- **Error Exceedances**: $|e| > 10\text{ DDS}$: 18.18% | $|e| > 15\text{ DDS}$: 4.80% | $|e| > 20\text{ DDS}$: 0.87%
- **Victim-Level Secondary Diagnostic (150 Victims)**:
  - Victim-Mean Fusion MAE: **1.4167** | RMSE: **1.7681** | R²: **0.9642** | Pearson: **0.9839**
  - Victim-Mean Structured MAE: 1.7280 | RMSE: 2.1944 | R²: 0.9449 | Pearson: 0.9781
- **Deterministic Inference**: Consecutive test evaluations produced identical predictions (max difference = **0.0000000000**).

---

## 5. Artifact Index (`engine/outputs/dds_v2/fusion_final/`)

- `fusion_final_test_predictions.csv` (4,500 rows)
- `fusion_final_test_metrics.csv`
- `fusion_final_availability_metrics.csv`
- `fusion_final_error_analysis.csv`
- `fusion_final_victim_level_metrics.csv`
- `fusion_final_reproducibility.json`
- `fusion_final_audit.json`
- Model copy: `engine/models/v2/fusion_final/fusion_model.json`

---

## 6. Test Suite Results

Full regression test suite passing:
```powershell
python -m pytest engine/tests/ -v
```
**Result**: **99/99 passed** (100% pass rate).
- `test_v2_fusion_final.py`: 6 passed
- `test_v2_fusion_oof.py`: 9 passed
- `test_v2_fusion.py`: 47 passed
- `test_v2_feature_policy.py`: 11 passed
- `test_v2_structured_dds.py`: 6 passed
- `test_v2_text_dds.py`: 6 passed
- `test_v2_voice_dds.py`: 7 passed
- `test_v2_behaviour_dds.py`: 7 passed
