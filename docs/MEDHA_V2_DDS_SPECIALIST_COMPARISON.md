# MEDHA V2 STEP 9 — DDS SPECIALIST COMPARISON & AUDIT REPORT

## 1. Executive Summary

This report delivers a rigorous comparative evaluation of all four independent **DDS Specialists** developed in Steps 5 through 8 for MEDHA V2:

1. **Structured DDS Specialist** (Step 5 — 42 structured, context, and case features)
2. **Text DDS Specialist** (Step 6 — 5 core MuRIL transformer features)
3. **Voice DDS Specialist** (Step 7 — 5 core acoustic & prosodic features)
4. **Behaviour DDS Specialist** (Step 8 — 10 longitudinal interaction & engagement features)

All four specialists were trained strictly on the 700 training victims ($21,000$ longitudinal observations) and independently evaluated against the exact same 150 held-out test victims ($4,500$ longitudinal observations) from the authoritative Step 3 split (`engine/data/processed/v2_victim_split.csv`).

---

## 2. Definitive Specialist Performance Ranking

### Summary Comparison Table (Held-Out Test Set)

| Rank | Model / Specialist | Modality | Evaluated Test Rows | Test MAE | Test RMSE | Test $R^2$ | Pearson $r$ | Spearman $\rho$ | Baseline MAE | MAE Improvement |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| — | **Simple Baseline (Train Mean)** | None (Dummy) | 4,500 (100%) | 10.8196 | 13.1688 | -0.0039 | 0.0000 | 0.0000 | 10.8196 | +0.00% |
| **1** | **Structured Specialist (Canonical XGBoost)** | Structured / Case | 4,500 (100%) | **6.1611** | **7.7353** | **0.6536** | **0.8086** | **0.8146** | 10.8196 | **+43.06%** |
| **2** | **Voice Specialist (Canonical Ridge)** | Acoustic / Audio | 1,692 (37.6%) | **6.3070** | **7.9104** | **0.6529** | **0.8082** | **0.8179** | 11.1102 | **+43.23%** |
| **3** | **Text Specialist (Canonical Ridge)** | NLP / MuRIL | 3,362 (74.7%) | **6.4352** | **8.0783** | **0.6365** | **0.7978** | **0.8067** | 11.0051 | **+41.53%** |
| **4** | **Behaviour Specialist (Canonical Ridge)** | App Interaction | 4,500 (100%) | **7.3530** | **9.1945** | **0.5106** | **0.7147** | **0.7332** | 10.8196 | **+32.04%** |

*Note: Baseline MAE and RMSE reflect the train-mean dummy predictor evaluated on the exact subset of rows available for that specialist.*

---

## 3. In-Depth Comparative Performance Analysis

### A. Which Specialist Performs Best?
**The Structured Specialist ranks #1 overall.**
- **Test MAE**: **6.1611** (Lowest absolute error across the full population)
- **Test RMSE**: **7.7353**
- **Test $R^2$**: **0.6536**
- **Test Pearson $r$**: **0.8086**
- **Why it performs best**:
  The Structured Specialist draws on explicit, multi-dimensional psychometric inputs directly tied to internal state: self-reported mood, acute stress, sleep disruption, functional impairment, and safety status. Furthermore, it incorporates situational amplifiers (threat events, legal proceedings, protective support factors, clinical episodes) that directly drive acute psychological distress. Because these indicators are both highly predictive and available on 100% of check-in timepoints, the Structured Specialist provides the strongest and most reliable standalone foundation for DDS estimation.

### B. The Strongest Expressive Biomarker: Voice Specialist
**The Voice Specialist ranks #2 overall and is virtually tied with Structured in signal density.**
- **Test MAE**: **6.3070**
- **Test RMSE**: **7.9104**
- **Test $R^2$**: **0.6529**
- **Test Pearson $r$**: **0.8082**
- **Test Spearman $\rho$**: **0.8179** (Highest rank correlation of all specialists)
- **Clinical Insight**:
  Acoustic and prosodic indicators (pause ratios, vocal distress, speech rate deviations, RMS energy fluctuations) provide an objective, involuntary biometric channel. Vocal distress does not depend on subjective user honesty, making it an exceptionally pure distress signal. However, its primary operational limitation is modality availability: voice recordings were only submitted on $37.6\%$ of test timepoints.

### C. The Text Specialist
**The Text Specialist ranks #3 overall.**
- **Test MAE**: **6.4352**
- **Test RMSE**: **8.0783**
- **Test $R^2$**: **0.6365**
- **Test Pearson $r$**: **0.7978**
- **Clinical Insight**:
  The fine-tuned MuRIL transformer extracts nuanced semantic distress cues (fear, threat context, negative affect, urgency). It provides strong predictive accuracy on $74.7\%$ of test check-ins, slightly trailing the acoustic precision of voice and the comprehensive domain coverage of structured questions.

### D. Which Specialist Performs Worst?
**The Behaviour Specialist ranks #4 (Worst).**
- **Test MAE**: **7.3530** ($+1.19$ points higher error than Structured)
- **Test RMSE**: **9.1945** ($+1.46$ points higher error than Structured)
- **Test $R^2$**: **0.5106** ($0.14$ points lower variance explained than Structured/Voice)
- **Test Pearson $r$**: **0.7147**
- **Objective Evaluation**:
  We do not claim that a modality is clinically strong simply because its model produces a non-zero $R^2$. Evaluated comparatively, **behavioural interaction metadata is the weakest predictor of psychological distress**.
  
  **Why Behaviour performs worst**:
  1. **Passive Indirect Signal**: Check-in response delay, session duration, and app click counts are passive behavioral artifacts, not direct measurements of emotional trauma or psychological distress.
  2. **High Real-World Confounding**: A delay in opening an app or a shorter session duration can be caused by normal external factors (work schedule, dead phone battery, lack of Wi-Fi, routine distraction) entirely unrelated to acute crisis.
  3. **Low Fine-Grained Resolution**: While sudden behavioral withdrawal produces an identifiable signal ($|\text{Engagement\_Deviation}|$ correlates $+0.52$ with DDS), it cannot resolve whether a victim's distress score is 45 vs 75 with the precision that structured clinical questionnaires or vocal prosody can.
  4. **Value Proposition**: The sole clinical value of the Behaviour specialist is **universal availability** ($100\%$ temporal coverage), serving as a passive safety net when victims are unwilling or unable to speak or write.

---

## 4. Strictly Paired Evaluation on Common Subset ($N = 1,269$)

To eliminate sampling differences between modalities that have different missing rates (e.g. Voice $37.6\%$ vs Text $74.7\%$), we evaluated all four specialists on the **exact same 1,269 test timepoints** where all four modalities were observed simultaneously:

### Common Subset Comparison ($N = 1,269$ Paired Test Rows)

| Specialist Model | Modality | Common MAE | Common RMSE | Common $R^2$ | Common Pearson $r$ | Common Spearman $\rho$ | Common MAE Improvement |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Simple Baseline (Common Mean)** | None (Dummy) | 11.3326 | 13.7188 | -0.0004 | 0.0000 | 0.0000 | +0.00% |
| **Voice Specialist (Canonical Ridge)** | Acoustic / Audio | **6.2707** | **7.8890** | **0.6692** | **0.8181** | **0.8278** | **+44.67%** |
| **Structured Specialist (Canonical XGBoost)** | Structured / Case | **6.3121** | **7.8811** | **0.6699** | **0.8209** | **0.8275** | **+44.30%** |
| **Text Specialist (Canonical Ridge)** | NLP / MuRIL | **6.3260** | **7.9821** | **0.6613** | **0.8140** | **0.8236** | **+44.18%** |
| **Behaviour Specialist (Canonical Ridge)** | App Interaction | **7.6249** | **9.4778** | **0.5225** | **0.7251** | **0.7364** | **+32.72%** |

### Critical Takeaways from the Common Subset:
1. **Convergence of Top Three Modalities**: When audio recordings and text statements are present, Voice ($R^2 = 0.6692$), Structured ($R^2 = 0.6699$), and Text ($R^2 = 0.6613$) exhibit remarkably close predictive power (all MAEs between $6.27$ and $6.33$).
2. **Voice Outperforms All on Available Audio**: On observations where audio is submitted, Voice achieves the lowest MAE ($6.2707$) and highest rank correlation ($\rho = 0.8278$).
3. **Behaviour Remains Substantially Inferior**: Even when isolated to the active-check-in common subset, Behaviour lags by over $1.3$ MAE points and $0.14$ $R^2$ points, proving its comparative limitation is intrinsic to the modality, not a sampling artifact.

---

## 5. Verification of the 6 Mandated Audits

Every requirement outlined in the Step 9 specification was programmatically verified and passed:

### Audit 1: Same Victim Split
- **Verification**: `engine/data/processed/v2_victim_split.csv` was verified across all four training and evaluation pipelines.
- **Victim Count**: Exactly 700 training victims, 150 validation victims, and 150 test victims.
- **Isolation**: Strictly zero victim overlap ($(\text{Train} \cap \text{Val}) = \emptyset$, $(\text{Train} \cap \text{Test}) = \emptyset$, $(\text{Val} \cap \text{Test}) = \emptyset$).

### Audit 2: Same Target DDS Predicted
- **Verification**: Ground truth target arrays were extracted from each specialist's output dataset and compared element-by-element across all 4,500 test rows.
- **Result**: Exactly identical target values across all files ($\max |\text{Actual\_DDS}_i - \text{Actual\_DDS}_j| = 0.0$). Target mean = $40.5276$, std = $13.1430$, range = $[0.00, 84.66]$.

### Audit 3: Evaluated on Same Test Victims
- **Verification**: Evaluated test victim rosters match the exact 150 test victims from Step 3:
  - Structured: 150 victims, 4,500 rows ($100\%$)
  - Behaviour: 150 victims, 4,500 rows ($100\%$)
  - Text: 150 victims, 3,362 observed rows ($74.7\%$)
  - Voice: 150 victims, 1,692 observed rows ($37.6\%$)

### Audit 4: Forbidden DDS Lag Features Strictly Excluded
- **Verification**: Inspected `v2_structured_dds_features.json`, `v2_text_dds_features.json`, `v2_voice_dds_features.json`, and `v2_behaviour_dds_features.json`.
- **Result**: Zero forbidden lag features (`Previous_DDS`, `Rolling_DDS_Mean`, `Rolling_DDS_SD`, `DDS_Slope`, `Recent_Change_Rate`, `Recent_Max_DDS`, `Recent_Min_DDS`, `Delta_DDS`, `DDS_Deviation_From_Baseline`, `Baseline_DDS`) were used by any specialist model.

### Audit 5: No Test Predictions Used During Training
- **Verification**: Training scripts confirmed that all scalers, median imputers, ordinal encoders, and model estimators were fit solely on observations belonging to `Split == 'train'`. No validation or test rows were seen during training.

### Audit 6: Metrics Calculated Consistently
- **Verification**: All specialists compute metrics via identical standard definitions:
  - $\text{MAE} = \frac{1}{n} \sum |y - \hat{y}|$
  - $\text{RMSE} = \sqrt{\frac{1}{n} \sum (y - \hat{y})^2}$
  - $R^2 = 1 - \frac{\sum (y - \hat{y})^2}{\sum (y - \bar{y})^2}$
  - Pearson $r$ via `scipy.stats.pearsonr`
  - Spearman $\rho$ via `scipy.stats.spearmanr`
  - Baseline MAE computed using the authoritative train-split target mean ($39.7031$).

---

## 6. Modality Trade-Off Matrix (Predictive Power vs Availability)

| Modality | Specialist Engine | Predictive Precision ($R^2$ / MAE) | Temporal Coverage (% of timepoints) | Primary Clinical Strengths | Primary Operational Limitations |
|---|---|:---:|:---:|---|---|
| **Structured** | XGBoost (42 feats) | **High** ($0.654$ / $6.16$) | **100.0%** ($4,500$ rows) | Multi-item psychometrics + acute threat / protection events | Requires active victim completion of survey prompts |
| **Voice** | Ridge (5 feats) | **High** ($0.653$ / $6.31$) | **37.6%** ($1,692$ rows) | Involuntary acoustic prosody; highest rank correlation | High missing rate ($62.4\%$ absent) |
| **Text** | Ridge (5 feats) | **Moderate-High** ($0.637$ / $6.44$) | **74.7%** ($3,362$ rows) | Captures nuanced semantic fear, threats, and urgency | Subject to brief responses or text omissions ($25.3\%$ absent) |
| **Behaviour** | Ridge (10 feats) | **Low-Moderate** ($0.511$ / $7.35$) | **100.0%** ($4,500$ rows) | Passive interaction tracking; zero victim burden | Highly noisy indirect proxy; weakest distress resolution |

---

## 7. Implications for Downstream Multimodal Fusion

1. **Avoid Naive Fixed-Weight Averaging**:
   Because Voice is missing in $62.4\%$ of rows and Text in $25.3\%$, any fixed-weight fusion formula (e.g. $0.25 \text{Text} + 0.25 \text{Voice} + 0.25 \text{Struct} + 0.25 \text{Behav}$) will either collapse on missing rows or severely distort predictions if unobserved modalities are filled with constant priors.
2. **Gated / Modality-Aware Fusion Architecture**:
   The Fusion Engine must dynamically route or re-normalize weights depending on modality availability flags (`Text_Available`, `Voice_Available`).
3. **Weight Allocation Hierarchy**:
   When Voice and Text are present, they should be weighted heavily alongside Structured features. When Voice or Text are absent, Structured inputs should carry the primary weight, with Behaviour providing a modest secondary regularization signal.
4. **Behaviour Down-Weighting**:
   Because Behaviour has significantly higher error ($7.35$ MAE vs $6.16$ MAE), giving Behaviour equal weight to Structured or Voice degrades overall precision. Behaviour should serve primarily as a baseline stability monitor.

---

## 8. Artifact Summary

- **Primary Output CSV**: [outputs/dds_v2/specialist_comparison.csv](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/outputs/dds_v2/specialist_comparison.csv)
- **Mirrored Output CSV**: [engine/outputs/dds_v2/specialist_comparison.csv](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/outputs/dds_v2/specialist_comparison.csv)
- **Test Predictions**:
  - Structured: [outputs/dds_v2/structured/test_structured_dds_predictions.csv](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/outputs/dds_v2/structured/test_structured_dds_predictions.csv)
  - Voice: [outputs/dds_v2/voice/test_voice_dds_predictions.csv](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/outputs/dds_v2/voice/test_voice_dds_predictions.csv)
  - Text: [outputs/dds_v2/text/test_text_dds_predictions.csv](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/outputs/dds_v2/text/test_text_dds_predictions.csv)
  - Behaviour: [outputs/dds_v2/behaviour/test_behaviour_dds_predictions.csv](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/outputs/dds_v2/behaviour/test_behaviour_dds_predictions.csv)

Step 9 is complete. All four specialists have been comparatively audited, verified, and ranked.
