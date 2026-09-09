# MEDHA V2 Step 10C — Fusion Validation & Independent Evaluation

## 1. Overview
This report details the independent validation of the MEDHA V2 Fusion Engine (Step 10C). The objective of this step is purely diagnostic: to audit the implementation, verify reproducibility and splits, rule out data leakage, and quantify the true performance benefit of the fusion layer across different data availability regimes.

No models were modified or retrained during this step.

---

## 2. Audit Results

### 2.1 Reproducibility Audit
*   **Status:** **PASS**
*   **Result:** The saved XGBoost fusion model (`v2_fusion_xgb.json`) and its feature configuration (`v2_fusion_feature_config.json`) were independently re-loaded. When applied to the saved test feature inputs, the re-generated predictions perfectly matched the saved `test_fusion_dds_predictions.csv` (Max difference: `0.000003`).

### 2.2 Leakage Audit
*   **Status:** **PASS**
*   **Result:** The saved feature order explicitly excludes all identified leaky features (`Actual_DDS`, `Future_Escalation_Label`, `Previous_DDS`, `Trajectory_State`, etc.). The model exclusively operates on:
    *   `Struct_Pred`, `Text_Pred`, `Voice_Pred`, `Behav_Pred`
    *   `Struct_Available`, `Text_Available`, `Voice_Available`, `Behav_Available`

### 2.3 Split & Alignment Audit
*   **Status:** **PASS**
*   **Result:** 
    *   Authoritative splits were strictly preserved: Train (700 victims), Validation (150 victims), Test (150 victims).
    *   Zero victim overlap exists between the splits.
    *   Every row in the test predictions perfectly aligns with the authoritative 150 test victims (N=4,500).
    *   No duplicate `(Victim_ID, Timepoint)` keys were found in the output.

---

## 3. Final Performance Metrics (Full Test Set)

The following metrics were independently calculated from the saved test predictions on the 150 held-out test victims (N=4,500):

| Model | MAE | RMSE | R² | Pearson |
| :--- | :--- | :--- | :--- | :--- |
| **Fusion (XGBoost)** | **6.0626** | **7.6266** | **0.6633** | **0.8146** |
| Structured Specialist | 6.1611 | 7.7353 | 0.6536 | 0.8086 |
| Voice Specialist | 6.3070 | 7.9104 | 0.6529 | 0.8082 |
| Text Specialist | 6.4352 | 8.0783 | 0.6365 | 0.7978 |
| Behaviour Specialist | 7.3530 | 9.1945 | 0.5106 | 0.7147 |
| Baseline (Train-Mean) | 10.8196 | 13.1688 | -0.0039 | NaN |

**Conclusion:** The Fusion Engine successfully outperforms the best individual specialist (Structured) with a +1.6% MAE improvement, validating the efficacy of the ensemble.

---

## 4. Availability Stratification & Benefit Analysis

The test set (N=4,500) was stratified by the availability of unstructured modalities (Voice and Text). Structured and Behaviour modalities are always available (100% coverage).

### 4.1 All Modalities Available (S+T+V+B)
*   **Count:** N=1,269
*   **Fusion MAE:** 6.0730
*   **Structured MAE:** 6.3121
*   **Voice (Best Spec) MAE:** 6.2707
*   **Benefit:** 
    *   vs. Structured: +0.2392 MAE improvement (+3.8%)
    *   vs. Best Available (Voice): +0.1978 MAE improvement (+3.2%)
*   **Verdict:** Fusion provides the most significant benefit when all signals are present.

### 4.2 Voice Missing (S+T+B)
*   **Count:** N=2,093
*   **Fusion MAE:** 6.0415
*   **Structured (Best Spec) MAE:** 6.1231
*   **Benefit:** 
    *   vs. Structured: +0.0816 MAE improvement (+1.3%)
*   **Verdict:** Fusion provides a modest but consistent improvement over Structured.

### 4.3 Text Missing (S+V+B)
*   **Count:** N=423
*   **Fusion MAE:** 6.1500
*   **Structured (Best Spec) MAE:** 6.0690
*   **Benefit:** 
    *   vs. Structured: -0.0810 MAE degradation (-1.3%)
*   **Verdict:** In this specific small subgroup, the Fusion Engine slightly underperforms the Structured Specialist. The XGBoost model struggles to balance the missing Text signal correctly in this regime.

### 4.4 Text & Voice Missing (S+B)
*   **Count:** N=715
*   **Fusion MAE:** 6.0543
*   **Structured (Best Spec) MAE:** 6.0584
*   **Benefit:** 
    *   vs. Structured: +0.0041 MAE improvement (+0.1%)
*   **Verdict:** With minimal complementary signals (only Behaviour), Fusion essentially mirrors the Structured specialist's performance, successfully falling back without catastrophic degradation.

---

## 5. Error Analysis (Diagnostic)

An analysis of the absolute errors (AbsError) and residuals (Actual - Predicted) reveals the following:

### 5.1 Bias & Range Analysis
*   **Overall Bias:** The model exhibits a very slight overall bias (Mean Residual = -0.1035), indicating minimal systematic drift on average.
*   **DDS 0-25:** Overpredicts slightly (MAE 7.97, Bias -7.18).
*   **DDS 25-50:** Highly accurate, minimal bias (MAE 5.48, Bias -0.75).
*   **DDS 50-75:** Underpredicts slightly (MAE 6.42, Bias +4.98).
*   **DDS 75-100:** Significant underprediction (MAE 18.33, Bias +18.33). 
    *   *Note: This is a classic regression to the mean effect for high-severity outliers.*

### 5.2 High-Error Cases
*   Predictions with >20 points of error occurred in only 48 rows (1.1% of the test set). The fusion engine is highly stable.

---

## 6. Testing
*   A comprehensive unit test suite (`engine/tests/`) was executed.
*   **Results:** 84 / 84 tests PASSED.

---

## 7. Limitations & Go/No-Go Decision

**Limitations:**
1.  While Fusion beats the Structured specialist overall, the improvement is relatively modest (+1.6% MAE).
2.  The Fusion Engine slightly underperforms the Structured specialist when Text is missing but Voice is present (a smaller subgroup of N=423).
3.  The fusion model struggles to accurately capture extreme high-severity events (DDS > 75).

**Recommendation for Step 11:**
The V2 Fusion Engine has been successfully validated. It demonstrates robust reproducibility, strict adherence to leakage and split constraints, and provides a measurable improvement over any single specialist (MAE 6.0626). 

The evidence is sufficient to proceed to **Step 11 (Fusion Ablation & Temporal Extension)** to investigate whether the V1 GRU or other temporal mechanisms can further reduce the error.
