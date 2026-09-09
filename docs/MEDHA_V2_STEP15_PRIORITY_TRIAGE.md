# MEDHA V2 STEP 15: PRIORITY / TRIAGE LAYER

## 1. Existing Priority/Triage Audit
An audit was performed across the repository to locate any pre-existing priority, triage, severity, or escalation logic. The audit found a single legacy prototype in `engine/fusion_engine/priority_thresholds.py`. This file explicitly stated:
> *WARNING: These are prototype rules for deriving an operational priority level from the model outputs (DDS and Future Escalation Risk). They are NOT clinically validated and should be tuned in coordination with mental health professionals.*

## 2. Specification Source
Since no formal, clinically validated specification exists (**Case 3**), we proceeded to implement an **Engineering Demonstration Prototype**. 
This layer is clearly marked as an engineering artifact requiring domain validation.

## 3. Rules Implemented
The exact rules from the V1 prototype were preserved and applied to the V2 `Current_DDS` (mapped from `Fusion_DDS_Prediction`) and `Future_Risk_Probability` (mapped from the GRU `Temporal_Risk_Score`).

### 4. Thresholds
- **CRITICAL**: `Current DDS >= 75.0` OR `Future Risk >= 0.85`
- **HIGH**: `Current DDS >= 50.0` OR `Future Risk >= 0.50`
- **MEDIUM**: `Current DDS >= 25.0` OR `Future Risk >= 0.25`
- **LOW**: `Current DDS < 25.0` AND `Future Risk < 0.25`

### 5. Meaning of Priority Levels (Demonstration Only)
- **CRITICAL**: Immediate attention suggested due to extreme current distress or exceptionally high probability of imminent clinical escalation.
- **HIGH**: Prioritized attention suggested due to severe current distress or significant escalation risk.
- **MEDIUM**: Standard monitoring suggested.
- **LOW**: Routine asynchronous care pathway.
- **UNKNOWN**: Unable to determine priority due to insufficient data.

## 6. Current DDS Role
`Current_DDS` is strictly the instantaneous distress score output by the V2 XGBoost Fusion model (which itself aggregates the 4 Specialist Modalities). It anchors the triage layer in the patient's immediate state.

## 7. Future Risk Role
`Future_Risk_Probability` is strictly the 7-day forward-looking escalation probability output by the V2 Temporal GRU model. It augments triage by elevating priority for patients whose distress may be masked or slowly rising towards an escalation event.

## 8. Missing Data Behavior
If an upstream component is missing (e.g., GRU History is insufficient for a prediction, causing `Future Risk = NaN`), the triage engine gracefully falls back to evaluating thresholds on the remaining active score (`Current DDS`). 
If *both* are missing, it outputs `UNKNOWN`.

## 9. Semantic Separation & Error Handling
The triage engine `engine/v2/priority_triage.py` creates a downstream abstraction layer. It **does not mutate** the raw machine learning columns (`Fusion_DDS_Prediction`, `Temporal_Risk_Score`), ensuring absolute semantic separation between predictive modeling and downstream operations. It throws `ValueError` if the correct ML pipeline contract is violated.

## 10. Tests Passed
Unit tests (`test_v2_priority_triage.py`) fully passed, validating:
- Boundary edge-cases (exactly at 75.0, 0.85, 50.0, etc.)
- Missing DDS, missing Future Risk, and completely missing data.
- Preservation of original ML feature vectors.

## 11. End-To-End Integration Cases
The pipeline was run on the entire held-out Test Split to extract representative cases (`run_step15_e2e.py`):
- **Case A (Low / Low)**: V0014 at T=8 (DDS=23.17, Risk=0.06) -> **LOW**
- **Case B (High / Low)**: V0201 at T=8 (DDS=50.87, Risk=0.19) -> **HIGH**
- **Case C (Low / High)**: *No cases present in test split.*
- **Case D (High / High)**: V0002 at T=11 (DDS=52.21, Risk=0.67) -> **HIGH**
- **Case E (Missing Modality)**: V0002 at T=8 (Voice missing, DDS=42.27, Risk=0.63) -> **HIGH**
- **Case F (Insufficient GRU History)**: V0002 at T=1 (DDS=43.94, Risk=NaN) -> **MEDIUM**

## 12. Clinical Validation Limitations
This triage layer is strictly for **engineering demonstration**. It is **not clinically validated, medically diagnostic, or clinically proven**. 

**Unresolved Clinical/Domain Decisions:**
1. Do clinical experts agree with the Boolean OR logic (`DDS >= X` OR `Risk >= Y`), or should a weighted clinical matrix be used?
2. Are the specific threshold values (75, 50, 25 and 0.85, 0.50, 0.25) appropriate for the specific clinical cohort MEDHA serves?
3. Should priority determination depend on modality availability (e.g., treating missing behaviour logs as an implicit risk factor)?
