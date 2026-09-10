# STEP 9B: FROZEN V2 BEHAVIOUR FEATURE LINEAGE RECOVERY

## 1. Executive Summary
This report investigates the authoritative lineage of the 10 behaviour features expected by the frozen V2 pipeline. The investigation concludes that **Step 10 is permanently BLOCKED without a domain decision**. The most critical feature, `Engagement_Score`, is explicitly flagged as a `SIMULATED` base variable in the canonical dataset's Data Dictionary, not a derived construct. Its original Python generation code does not exist in this repository. Consequently, these features cannot be deterministically reconstructed from raw backend events without either inventing an arbitrary formula (violating the frozen model contract) or receiving an authoritative definition from the data science team.

## 2. Frozen Behaviour Contract
The exact 10 features expected by the frozen V2 `Behaviour Specialist` (Ridge Regression model), verified via `engine/models/behaviour_dds_v2/v2_behaviour_dds_features.json`:
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

## 3. Repository Search Results
- No python file in the repository (e.g. `generate_dataset.py`) contains the generation logic for the dataset.
- `longitudinal_data.ipynb` simply loads the already-generated dataset to train the Structured Risk Engine.
- The `Generation_Methodology` sheet in the Excel file provides only high-level conceptual descriptions (e.g., "Noisy structured, behavioural, text, voice, diary and professional signals"), not mathematical formulas.

## 4. Dataset Generation Lineage
The authoritative dataset is `engine/data/raw/MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx`. 
Investigation of the `Data_Dictionary` sheet in this workbook yields the exact origin types of the features:
- `Response_Delay_Hours`: SIMULATED
- `Missed_Checkin`: SIMULATED
- `Interaction_Frequency_7d`: SIMULATED
- `Session_Duration_Minutes`: SIMULATED
- `Engagement_Score`: SIMULATED
- `Engagement_Deviation`: DERIVED
- `Response_Delay_Deviation`: DERIVED
- `Baseline_Engagement`: DERIVED
- `Behaviour_Trend`: DERIVED

## 5. Feature-by-Feature Lineage Table

| Feature | Source Type | Generation Logic | Can Reconstruct From Runtime Events? | Evidence | Confidence |
|---|---|---|---|---|---|
| `Engagement_Score` | SIMULATED | None / Sampled | No | `Data_Dictionary` Sheet | High |
| `Engagement_Deviation` | DERIVED | Likely `Engagement_Score - Baseline_Engagement` | No (requires Engagement_Score) | `Data_Dictionary` Sheet | High |
| `Response_Delay_Hours` | SIMULATED | None / Sampled | Yes (from `checkin_completed` delta) | `Data_Dictionary` Sheet | High |
| `Response_Delay_Deviation` | DERIVED | Likely `Response_Delay - Baseline` | Yes (if baseline is defined) | `Data_Dictionary` Sheet | High |
| `Missed_Checkin` | SIMULATED | None / Sampled | Yes (from checkin expiration logic) | `Data_Dictionary` Sheet | High |
| `Interaction_Frequency_7d`| SIMULATED | None / Sampled | Yes (rolling count of events) | `Data_Dictionary` Sheet | High |
| `Session_Duration_Minutes`| SIMULATED | None / Sampled | Yes (duration of session logs) | `Data_Dictionary` Sheet | High |
| `Baseline_Response_Delay`| DERIVED | Unknown (likely rolling mean) | Yes (can be calculated historically) | `Data_Dictionary` Sheet | High |
| `Baseline_Engagement` | DERIVED | Unknown (likely rolling mean) | No (requires Engagement_Score) | `Data_Dictionary` Sheet | High |
| `Behaviour_Trend` | DERIVED | Unknown (likely slope or delta) | No (requires Engagement_Score) | `Data_Dictionary` Sheet | High |

## 6. Exact Recovered Formulas
No exact mathematical formulas exist in the repository for `Engagement_Score` or `Behaviour_Trend`. They were generated ex-situ. 

## 7. Engagement_Score Analysis
- **Exact Mathematical Definition**: UNKNOWN.
- **Input Variables**: UNKNOWN. 
- **Whether it was synthetically sampled rather than derived**: YES. The `Data_Dictionary` sheet explicitly labels it as `SIMULATED`, meaning it is a base stochastic variable injected into the dataset to represent abstract engagement, rather than a deterministic aggregate of smaller raw events.
- **Is it reconstructable without leakage?**: NO. Any attempt to build an `Engagement_Score` from raw events (like chat duration + journal entries) would be a pure guess, silently violating the original distribution the frozen Ridge Regression model was trained on.

## 8. Baseline_Engagement Analysis
- **Exact Mathematical Definition**: UNKNOWN (likely rolling mean/median of `Engagement_Score` up to $T-1$).
- **Is it reconstructable?**: NO. It is mathematically dependent on the missing `Engagement_Score` logic.

## 9. Behaviour_Trend Analysis
- **Exact Mathematical Definition**: UNKNOWN.
- **Is it reconstructable?**: NO.

## 10. Runtime Reconstructability
**CASE C — Synthetic/training-only feature whose original runtime semantics cannot be recovered.**
We are missing the mathematical definitions to transition these synthetic training variables into operationalized runtime pipelines.

## 11. Missing-Value Semantics
- In training, missing values were median-imputed via `v2_behaviour_dds_preprocessor.pkl`. 
- Runtime must provide `np.nan` for missing fields.

## 12. Leakage Analysis
The deviation formulas (Current - Baseline) and historical baselines are inherently safe from temporal leakage *if* computed causally ($T < T_n$), as established in Step 9A. However, without the formulas, we cannot guarantee safe reconstruction.

## 13. Step 9A Compatibility
Step 9A is a perfectly valid *intermediate observable layer*. It accurately calculates `Session_Duration_Minutes` (from `App_Interaction_Duration`) and `Response_Delay_Hours` (from `Checkin_Response_Delay`). It should be **RETAINED**. 

## 14. Recommended Architecture
```
Raw Events
    ↓
Step 9A intermediate observables (RETAINED)
    ↓
Canonical V2 Behaviour Feature Transformation (BLOCKED)
    ↓
Frozen 10-feature contract
    ↓
Frozen Behaviour Ridge
    ↓
Behav_Pred
```

## 15. Remaining Blockers
We need an authoritative mathematical formula from the ML team defining how to construct `Engagement_Score` and `Behaviour_Trend` from raw application events. 

## 16. Final Decision
**STEP 10 BLOCKED**.

We lack the mathematical definition to construct `Engagement_Score`, `Baseline_Engagement`, and `Behaviour_Trend`. The original data generation scripts are not in the repository, and the Excel dictionary confirms they were synthetic simulations, not derived aggregates. Step 10 cannot proceed safely.
