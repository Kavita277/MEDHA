# MEDHA Structured Risk Engine — Complete Work Log

## 1. Purpose

This document records the work completed for the MEDHA Structured Risk Engine.

The engine takes structured/longitudinal MEDHA information and produces:
1. A probability of future escalation.
2. A binary structured-risk flag.
3. SHAP-based explainability.
4. A standardized output for the downstream fusion engine.

---

## 2. Architecture

```text
MEDHA Structured Data
        |
        v
Feature Selection
        |
        v
Preprocessing
        |
        v
XGBoost
        |
        v
Structured Risk Probability
        |
        +------------------+
        |                  |
        v                  v
Risk Threshold           SHAP
        |                  |
        v                  v
Structured Flag      Explanation
        |                  |
        +---------+--------+
                  |
                  v
        Structured API Output
                  |
                  v
             Gated Fusion
```

The Structured Engine is separate from the Text, Voice, Behaviour, and other modality engines.

---

# 3. Dataset

The primary dataset used was the MEDHA synthetic longitudinal dataset.

Important identifiers include:

- `Victim_ID`
- `Timepoint`

Target:

```text
Future_Escalation_Label
```

Full target distribution:

```text
Class 0: 21389
Class 1: 1611

Class 0 proportion: ~92.996%
Class 1 proportion: ~7.004%
```

Therefore, the task is an imbalanced binary classification problem.

---

# 4. Dataset Investigation

The dataset was inspected for:

- Column names
- Data types
- Missing values
- Target distribution
- Categorical variables
- Longitudinal structure
- Potential target leakage
- Feature availability

Two categorical variables were identified:

```text
Case_Type
Case_Stage
```

## Case_Type

```text
sexual_violence                4117
witness_intimidation           4071
murder_grievous_hurt           3956
caste_based_violence           3887
arson_displacement             3680
compensation_rehabilitation    3289
```

## Case_Stage

```text
Investigation          7124
Compensation           6492
Trial_Preparation      5982
Investigation_Delay    1138
Complaint              1000
Post_Hearing            634
Hearing                 630
```

Types:

```text
Case_Type     str
Case_Stage    str
```

---

# 5. Missing Values

Missing-value analysis showed:

```text
Episode_Severity               22846
Mood                            2374
Sleep                           2374
Functioning                     2374
Safety                          2374
Stress                          2374
Social_Support_Checkin          2374
Self_Reported_Wellbeing         2374
Delta_DDS                       1000
Previous_DDS                    1000
```

Variables with no missing values included:

```text
Session_Duration_Minutes
Response_Delay_Hours
Missed_Checkin
Interaction_Frequency_7d
Threat_Event
Upcoming_Hearing
Hearing_Completed
Investigation_Delay
Compensation_Delay
Engagement_Score
Engagement_Deviation
Response_Delay_Deviation
Protection_Event
Rehabilitation_Issue
Relocation_Stress
Family_Support
Social_Support
Therapist_Engagement
Access_To_Services
Stable_Housing
Other_Protective_Factors
Recent_Episode
Family_Reported_Episode
DDS
Baseline_Response_Delay
Baseline_DDS
Baseline_Engagement
DDS_Deviation_From_Baseline
```

---

# 6. Episode_Severity Investigation

Observed values:

```text
NaN         22846
Low            69
Moderate       63
High           22
```

The relationship with `Recent_Episode` was:

```text
Episode_Severity  False  True   All
Recent_Episode
0                     0  22846  22846
1                   154      0    154
All                 154  22846  23000
```

Therefore, missing `Episode_Severity` is structurally associated with `Recent_Episode = 0`.

The mapping used was:

```python
{
    "Low": 1,
    "Moderate": 2,
    "High": 3
}
```

---

# 7. Final Structured Feature List

The original structured feature list contains 38 features:

```python
structured_features = [
    "Mood",
    "Stress",
    "Sleep",
    "Functioning",
    "Safety",
    "Social_Support_Checkin",
    "Self_Reported_Wellbeing",
    "Response_Delay_Hours",
    "Missed_Checkin",
    "Interaction_Frequency_7d",
    "Session_Duration_Minutes",
    "Engagement_Score",
    "Engagement_Deviation",
    "Response_Delay_Deviation",
    "Threat_Event",
    "Upcoming_Hearing",
    "Hearing_Completed",
    "Investigation_Delay",
    "Compensation_Delay",
    "Relocation_Stress",
    "Rehabilitation_Issue",
    "Protection_Event",
    "Family_Support",
    "Social_Support",
    "Therapist_Engagement",
    "Access_To_Services",
    "Stable_Housing",
    "Other_Protective_Factors",
    "Recent_Episode",
    "Episode_Severity",
    "Family_Reported_Episode",
    "DDS",
    "Baseline_DDS",
    "Baseline_Response_Delay",
    "Baseline_Engagement",
    "Previous_DDS",
    "Delta_DDS",
    "DDS_Deviation_From_Baseline"
]
```

---

# 8. Categorical Encoding

The encoder used was:

```python
OneHotEncoder(
    handle_unknown="ignore",
    sparse_output=False
)
```

Categories were confirmed.

## Case_Type

```text
arson_displacement
caste_based_violence
compensation_rehabilitation
murder_grievous_hurt
sexual_violence
witness_intimidation
```

## Case_Stage

```text
Compensation
Complaint
Hearing
Investigation
Investigation_Delay
Post_Hearing
Trial_Preparation
```

Therefore:

```text
38 original features
+
6 Case_Type one-hot features
+
7 Case_Stage one-hot features
=
51 model features
```

---

# 9. Final 51 Feature Representation

The exact processed feature order was:

```text
Mood
Stress
Sleep
Functioning
Safety
Social_Support_Checkin
Self_Reported_Wellbeing
Response_Delay_Hours
Missed_Checkin
Interaction_Frequency_7d
Session_Duration_Minutes
Engagement_Score
Engagement_Deviation
Response_Delay_Deviation
Threat_Event
Upcoming_Hearing
Hearing_Completed
Investigation_Delay
Compensation_Delay
Relocation_Stress
Rehabilitation_Issue
Protection_Event
Family_Support
Social_Support
Therapist_Engagement
Access_To_Services
Stable_Housing
Other_Protective_Factors
Recent_Episode
Family_Reported_Episode
DDS
Baseline_DDS
Baseline_Response_Delay
Baseline_Engagement
Previous_DDS
Delta_DDS
DDS_Deviation_From_Baseline
Episode_Severity
Case_Type_arson_displacement
Case_Type_caste_based_violence
Case_Type_compensation_rehabilitation
Case_Type_murder_grievous_hurt
Case_Type_sexual_violence
Case_Type_witness_intimidation
Case_Stage_Compensation
Case_Stage_Complaint
Case_Stage_Hearing
Case_Stage_Investigation
Case_Stage_Investigation_Delay
Case_Stage_Post_Hearing
Case_Stage_Trial_Preparation
```

This order is saved in `model_columns.pkl`.

---

# 10. Target Leakage

Target leakage was treated as a critical issue because synthetic datasets can accidentally generate the target from the same features used by the model.

The target was:

```text
Future_Escalation_Label
```

The model uses structured features such as:

```text
DDS
Previous_DDS
Baseline_DDS
DDS_Deviation_From_Baseline
```

These became some of the strongest predictors.

Therefore, the synthetic target-generation methodology must be documented and reviewed before claiming real-world predictive validity.

The current model results should be presented as **synthetic prototype results**, not clinical validation.

---

# 11. Victim-Level Train / Validation / Test Split

Because the dataset is longitudinal, rows were not randomly split across sets.

The correct strategy was:

```text
Victim IDs
    |
    +-- Train victims
    +-- Validation victims
    +-- Test victims
```

This prevents the same victim from appearing in both training and test sets.

Processed shapes:

```text
Train:      (16100, 51)
Validation: (3450, 51)
Test:       (3450, 51)
```

Target distributions:

## Train

```text
0 = 14957
1 = 1143
Positive proportion = 7.0994%
```

## Validation

```text
0 = 3205
1 = 245
Positive proportion = 7.1014%
```

## Test

```text
0 = 3227
1 = 223
Positive proportion = 6.4638%
```

---

# 12. Baseline XGBoost

The baseline model produced:

```text
ROC-AUC = 0.829809
PR-AUC  = 0.271265
```

At threshold 0.50:

```text
Class 0:
precision = 0.9323
recall    = 0.9922
f1        = 0.9613

Class 1:
precision = 0.3590
recall    = 0.0571
f1        = 0.0986
```

Confusion matrix:

```text
[[3180   25]
 [ 231   14]]
```

This showed that threshold 0.50 was poor for minority-class detection.

---

# 13. Class Weighting Experiment

A weighted model was tested.

Results:

```text
Baseline:
ROC-AUC = 0.829809
PR-AUC  = 0.271265

Weighted:
ROC-AUC = 0.828439
PR-AUC  = 0.268734
```

Class weighting did not improve the main ranking metrics, so it was not retained.

Final:

```text
Class weighting = OFF
```

---

# 14. Threshold Tuning

Because the target is imbalanced, multiple thresholds were tested.

Examples:

```text
threshold    precision    recall      f1

0.05         0.178020     0.800000    0.291233
0.10         0.238671     0.644898    0.348401
0.15         0.281377     0.567347    0.376184
0.20         0.302632     0.469388    0.368000
0.30         0.334951     0.281633    0.305987
0.50         0.358974     0.057143    0.098592
```

The selected threshold was:

```text
0.16
```

Validation result around the selected threshold:

```text
Precision ≈ 0.2987
Recall    ≈ 0.5510
F1        ≈ 0.3874
```

Final decision threshold:

```text
0.16
```

The threshold was selected using validation data and then fixed for final test evaluation.

---

# 15. Hyperparameter Experiments

Compared models:

```text
Model             ROC-AUC    PR-AUC

more_trees        0.831609   0.279454
shallower         0.834156   0.277817
regularized       0.830368   0.274986
strong_sampling   0.831096   0.273698
baseline          0.829809   0.271265
deeper            0.830757   0.265111
```

The selected configuration was the practical final candidate from these experiments.

---

# 16. Final XGBoost Configuration

The frozen model configuration is:

```text
n_estimators       = 400
max_depth          = 4
learning_rate      = 0.03
min_child_weight   = 1
subsample          = 0.8
colsample_bytree   = 0.8
class weighting    = OFF
threshold          = 0.16
```

This model should now be treated as frozen for the current prototype.

---

# 17. Final Test Performance

Final test results:

```text
ROC-AUC = 0.851038
PR-AUC  = 0.329106
```

At threshold 0.16:

```text
Class 0:
precision = 0.9644
recall    = 0.9247
f1        = 0.9442

Class 1:
precision = 0.3174
recall    = 0.5067
f1        = 0.3903
```

Overall:

```text
accuracy    = 0.8977
macro F1    = 0.6672
weighted F1 = 0.9084
```

Confusion matrix:

```text
[[2984  243]
 [ 110  113]]
```

Positive class:

```text
True Positives  = 113
False Positives = 243
False Negatives = 110
True Negatives  = 2984
```

Key tradeoff:

```text
Recall    ≈ 50.7%
Precision ≈ 31.7%
```

These are results on the synthetic dataset.

---

# 18. Feature Importance

Important model features included:

```text
DDS                           0.126826
Previous_DDS                  0.078434
DDS_Deviation_From_Baseline   0.053017
Engagement_Score              0.040766
Baseline_DDS                  0.020879
Case_Stage_Investigation      0.020674
Mood                          0.018772
Hearing_Completed             0.018591
Threat_Event                  0.018087
Response_Delay_Deviation      0.018003
Self_Reported_Wellbeing       0.017806
```

DDS-related features are particularly influential.

---

# 19. SHAP Explainability

SHAP was added using:

```python
shap.TreeExplainer(model)
```

Example prediction:

```text
structured_risk = 0.0057228859
structured_flag = 0
threshold       = 0.16
```

Top contributors:

```text
DDS                    -0.9688
Previous_DDS           -0.9042
Baseline_DDS           -0.4221
Engagement_Deviation    0.2180
Engagement_Score       -0.1625
```

Interpretation:

- Negative SHAP values pushed the model toward lower escalation risk.
- Positive SHAP values pushed the model toward higher escalation risk.

SHAP values are not percentages.

For example:

```text
DDS contribution = -0.9688
```

does not mean DDS reduced risk by 96.88%.

The probability is the risk estimate; SHAP is used for explanation.

---

# 20. Human-Readable Feature Names

A `FEATURE_DISPLAY_NAMES` dictionary was added to `inference.py`.

Examples:

```python
FEATURE_DISPLAY_NAMES = {
    "DDS": "Current distress score",
    "Previous_DDS": "Previous distress score",
    "Baseline_DDS": "Baseline distress level",
    "DDS_Deviation_From_Baseline": "Change from baseline distress",
    "Engagement_Score": "Engagement level",
    "Engagement_Deviation": "Change in engagement",
    "Mood": "Mood",
    "Stress": "Stress level",
    "Sleep": "Sleep quality",
    "Functioning": "Daily functioning",
    "Safety": "Sense of safety",
    "Threat_Event": "Recent threat event",
    "Upcoming_Hearing": "Upcoming hearing"
}
```

Additional mappings were added for the one-hot `Case_Type` and `Case_Stage` features.

---

# 21. Saved Model Artifacts

The following files were created:

```text
structured_engine/
├── xgboost_model.pkl
├── case_encoder.pkl
├── episode_mapping.pkl
├── structured_features.pkl
├── model_columns.pkl
├── threshold.pkl
└── inference.py
```

Meaning:

### `xgboost_model.pkl`

Frozen trained XGBoost model.

### `case_encoder.pkl`

Fitted:

```python
OneHotEncoder(
    handle_unknown="ignore",
    sparse_output=False
)
```

### `episode_mapping.pkl`

```python
{
    "Low": 1,
    "Moderate": 2,
    "High": 3
}
```

### `structured_features.pkl`

The 38 original structured input features.

### `model_columns.pkl`

The exact 51 processed feature columns and order.

### `threshold.pkl`

```text
0.16
```

### `inference.py`

Deployment/inference implementation.

---

# 22. Inference Pipeline

The training notebook is used for:

```text
EDA
Experimentation
Training
Evaluation
Model selection
```

`inference.py` is used for:

```text
Load artifacts
      |
Preprocess new input
      |
Generate probability
      |
Apply threshold
      |
Generate SHAP explanation
      |
Return structured output
```

The inference code validates:

- Required feature presence
- Episode severity values
- Feature ordering
- Number of processed features

Expected input representation:

```text
38 original structured features
```

Expected XGBoost representation:

```text
51 processed features
```

---

# 23. Inference Verification

The saved inference pipeline was tested against the original notebook prediction.

Observed:

```text
Notebook probability:
0.027639676

Inference probability:
0.027639676

Difference:
0.0
```

This confirms that the saved preprocessing and model reproduce the notebook prediction exactly.

This is a critical deployment verification.

---

# 24. API Contract

The standardized output from the Structured Engine is:

```json
{
  "structured_available": true,
  "structured_risk": 0.0057,
  "structured_flag": 0,
  "threshold": 0.16,
  "explanation": {
    "top_contributors": [
      {
        "feature": "DDS",
        "display_name": "Current distress score",
        "contribution": -0.9688
      },
      {
        "feature": "Previous_DDS",
        "display_name": "Previous distress score",
        "contribution": -0.9042
      },
      {
        "feature": "Baseline_DDS",
        "display_name": "Baseline distress level",
        "contribution": -0.4221
      }
    ]
  }
}
```

For fusion, the primary fields are:

```text
structured_available
structured_risk
structured_flag
```

SHAP explanation is primarily for UI, auditability, and interpretability.

---

# 25. Integration With Fusion

The intended downstream architecture is:

```text
Text Engine -----------+
Voice Engine -----------+
Behaviour Engine -------+
Longitudinal Engine ----+----> Gated Fusion
Structured Engine ------+
                         |
                         v
                  Final Priority
```

Jay's Structured Engine supplies:

```text
structured_risk
```

The fusion engine should use that structured representation as one input rather than treating the Structured Engine's output as the final system decision.

---

# 26. What This Engine Does NOT Do

The Structured Risk Engine does not:

- Process raw text
- Run MuRIL
- Process raw audio
- Perform voice analysis
- Perform behavioural anomaly detection
- Train the longitudinal GRU
- Perform final multimodal fusion
- Make autonomous clinical decisions

Its responsibility is:

```text
Structured MEDHA data
        |
        v
Preprocessing
        |
        v
XGBoost
        |
        v
Structured escalation risk
+
SHAP explanation
```

---

# 27. Current Status

Completed:

- [x] Dataset inspection
- [x] Feature selection
- [x] Missing-value investigation
- [x] Episode severity investigation
- [x] Categorical feature identification
- [x] One-hot encoding
- [x] Target distribution analysis
- [x] Victim-level train/validation/test split
- [x] Target leakage investigation
- [x] Baseline XGBoost
- [x] Class-weighting experiment
- [x] Hyperparameter experiments
- [x] Threshold tuning
- [x] Final XGBoost selection
- [x] Final test evaluation
- [x] Feature importance
- [x] SHAP explainability
- [x] Human-readable feature names
- [x] Model artifact saving
- [x] Separate inference code
- [x] Inference-vs-notebook verification
- [x] Structured API contract

Not yet part of this engine:

- [ ] Final multimodal fusion
- [ ] Fusion API/server
- [ ] Therapist dashboard integration
- [ ] Production deployment
- [ ] Real-world validation

---

# 28. Important Limitations

The current model was evaluated on a synthetic dataset.

Therefore:

```text
ROC-AUC = 0.851
PR-AUC  = 0.329
```

should not be presented as real-world or clinical performance.

The synthetic target-generation methodology should be reviewed before making stronger claims.

The strong influence of:

```text
DDS
Previous_DDS
Baseline_DDS
DDS_Deviation_From_Baseline
```

also makes target-generation/leakage analysis particularly important.

The Structured Engine is a prototype prioritization/support component and should not be presented as an autonomous clinical decision-maker.

---

# 29. Freeze Point

For the current prototype, freeze the Structured Engine at:

```text
Model:
XGBoost

Input:
38 structured features

Processed representation:
51 features

Class weighting:
OFF

Threshold:
0.16

Test ROC-AUC:
0.851038

Test PR-AUC:
0.329106

Positive-class precision:
0.3174

Positive-class recall:
0.5067

Positive-class F1:
0.3903
```

Further tuning should only be done for a clear methodological reason or when a new dataset becomes available.

---

# 30. Final Summary

The MEDHA Structured Risk Engine is now a complete prototype ML component.

Final pipeline:

```text
MEDHA structured longitudinal data
              |
              v
       38 input features
              |
              v
       Data preprocessing
       - Episode severity mapping
       - Case_Type one-hot encoding
       - Case_Stage one-hot encoding
              |
              v
          51 features
              |
              v
        Frozen XGBoost
              |
              v
     Future escalation probability
              |
              v
        Threshold = 0.16
              |
              +----------------+
              |                |
              v                v
       Structured Flag       SHAP
              |                |
              +-------+--------+
                      |
                      v
             Structured API
                      |
                      v
                Gated Fusion
```

The model is saved, preprocessing is saved, deployment inference is separated from training, SHAP explanations are available, and inference has been verified against the original notebook with zero probability difference.

**STATUS: STRUCTURED RISK ENGINE COMPLETE AND FROZEN FOR PROTOTYPE INTEGRATION.**

The next engineering stage is integration with the downstream Gated Fusion Engine.
