# STEP 9A vs V2 BEHAVIOUR CONTRACT RECONCILIATION

## 1. Problem Statement
The Step 9A Behaviour Aggregator was implemented with the assumption that the behaviour features required by the frozen V2 pipeline were ten specific event-driven metrics (e.g., `App_Interaction_Duration`, `Journal_Entry_Count`, `Chat_Message_Count`, `Late_Night_Usage_Ratio`, etc.). However, attempting to integrate these metrics in Step 10 revealed a severe contract mismatch. The frozen Behaviour Specialist expects an entirely different set of 10 features, centered around pre-engineered constructs like `Engagement_Score`, `Baseline_Engagement`, and `Behaviour_Trend`, which are fundamentally different from the raw aggregates produced by Step 9A.

## 2. Existing Step 9A Contract
Step 9A currently produces the following 10 features:
1. `App_Interaction_Duration`
2. `App_Interaction_Duration_Deviation`
3. `Checkin_Response_Delay`
4. `Checkin_Response_Delay_Deviation`
5. `Checkin_Completion_Rate`
6. `Missed_Checkin_Count`
7. `Journal_Entry_Count`
8. `Chat_Message_Count`
9. `Late_Night_Usage_Ratio`
10. `Support_Resource_Access_Count`

## 3. Actual Frozen Model Contract
The frozen V2 Behaviour Specialist contract actually expects:
1. `Engagement_Score`
2. `Engagement_Deviation`
3. `Response_Delay_Hours`
4. `Response_Delay_Deviation`
5. `Missed_Checkin`
6. `Interaction_Frequency_7d`
7. `Session_Duration_Minutes`
8. `Baseline_Response_Delay`
9. `Baseline_Engagement`
10. `Behaviour_Trend`

## 4. Evidence from Model Artifacts
Inspection of the following definitive model artifacts confirms the actual contract:
- **`engine/models/behaviour_dds_v2/v2_behaviour_dds_features.json`**: This configuration explicitly maps the `all_10_features` attribute to the list defined in Section 3.
- **`chatbot/state/medha_state.py`**: The `BEHAVIOUR_FEATURES` registry identically defines these 10 exact features.
- **`engine/v2/train_v2_behaviour_dds.py`**: The original training script rigorously enforces this boundary.

## 5. Exact Frozen Feature Order
Derived directly from the frozen JSON configuration and state definitions:
1. Engagement_Score
2. Engagement_Deviation
3. Response_Delay_Hours
4. Response_Delay_Deviation
5. Missed_Checkin
6. Interaction_Frequency_7d
7. Session_Duration_Minutes
8. Baseline_Response_Delay
9. Baseline_Engagement
10. Behaviour_Trend

*(The 10th feature is indeed `Behaviour_Trend`, NOT `Baseline_Checkin_Distress` as suggested by legacy documentation, resolving the conflict).*

## 6. Feature-by-Feature Mapping Analysis

| Step 9A Feature | Frozen Feature | Mapping | Formula / Rationale | Confidence |
|---|---|---|---|---|
| `App_Interaction_Duration` | `Session_Duration_Minutes` | Direct | Unit conversion (seconds to minutes) | High |
| `Checkin_Response_Delay` | `Response_Delay_Hours` | Direct | Unit conversion (seconds to hours) | High |
| `Checkin_Response_Delay_Deviation` | `Response_Delay_Deviation` | Direct | Deviation calculation (Current - Baseline) | High |
| `Missed_Checkin_Count` | `Missed_Checkin` | Direct | Same semantics | High |
| `App_Interaction_Duration_Deviation` | N/A | None | Dropped from frozen V2 | High |
| `Checkin_Completion_Rate` | N/A | None | Dropped from frozen V2 | High |
| `Journal_Entry_Count` | N/A | None | Dropped from frozen V2 | High |
| `Chat_Message_Count` | N/A | None | Dropped from frozen V2 | High |
| `Late_Night_Usage_Ratio` | N/A | None | Dropped from frozen V2 | High |
| `Support_Resource_Access_Count` | N/A | None | Dropped from frozen V2 | High |

## 7. Features Directly Available
Only basic interaction metrics are directly available:
- `Response_Delay_Hours`
- `Response_Delay_Deviation`
- `Session_Duration_Minutes`
- `Missed_Checkin`

## 8. Features Derivable
- `Interaction_Frequency_7d`: Can be derived using rolling 7-day windows over raw events.

## 9. Features Currently Unavailable
- `Engagement_Score`
- `Engagement_Deviation`
- `Baseline_Response_Delay`
- `Baseline_Engagement`
- `Behaviour_Trend`

These features are high-level engineered constructs that cannot be naively mapped from existing metrics. 

## 10. Original Feature-Generation Source Locations
- `Engagement_Score` and its derivatives were originally constructed in the legacy synthetic data generation pipeline (`engine/data/raw/MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx`) and the initial `engine/behaviour_engine/MEDHA_Behaviour_Engine_Complete_Summary.md` pipeline. 
- There is currently no verified pure python formula inside the `backend/` or `engine/` execution code to recreate `Engagement_Score` or `Behaviour_Trend` cleanly from raw events. 

## 11. Missing-Data Semantics
- Frozen Model: Uses `SimpleImputer(strategy="median")` for missing data.
- State Wrapper: Values are initialized as `None` and translated to `np.nan` for missing information. They must NEVER be coerced to `0.0`.

## 12. Baseline Semantics
- The frozen model (`v2_behaviour_dds_features.json`) mathematically defines deviations as Absolute Deviations `|z|` for `Engagement_Deviation` and `Response_Delay_Deviation`.

## 13. Recommended Architecture
**CASE C**: The required frozen features cannot be reconstructed from the current backend/event architecture without introducing new assumptions or changing the model/training contract.

The `Engagement_Score` and `Behaviour_Trend` metrics are highly complex and undefined in the current pipeline. Reconstructing them correctly requires locating or standardizing their formulas. 

## 14. What Must Change
- An architectural decision is required on how to generate the missing core metrics (`Engagement_Score`, `Behaviour_Trend`, `Baseline_Engagement`).
- Step 9A must eventually be extended, wrapped, or rewritten to produce the canonical 10 features expected by V2, not the 10 ad-hoc metrics it currently produces.

## 15. What Must NOT Change
- The frozen V2 Model weights, architectures, preprocessing, missing data strategies, and scalers MUST NOT change. 
- Step 10 MUST NOT proceed until the feature generation logic is fully reconciled.

## 16. Should Step 9A be rewritten, extended, or wrapped?
Step 9A should be **wrapped or extended**. The existing metrics (like interaction duration, response delays) are still highly useful intermediates. We should treat Step 9A as the "Intermediate Observable Layer", and build a "Canonical Feature Transformation Layer" that consumes these metrics (and others) to produce the exact 10 canonical features. However, we cannot build this wrapper until we have the exact formulas for the unavailable features.

## 17. Can Step 10 Proceed?
**BLOCKED**.

## 18. Explicit Decision
**CASE C**. We are blocked because we cannot reconstruct `Engagement_Score`, `Baseline_Engagement`, and `Behaviour_Trend` accurately without risking silent divergence from the frozen V2 model's original training semantics. We must either find the original generation scripts for these features or receive an authoritative formula before building the `BehaviourSpecialistAdapter`.
