# STEP 9C: ORIGINAL V2 GENERATOR RECOVERY

## 1. Executive Summary
This investigation attempted to recover the authoritative generation logic and mathematical formulas for the critical frozen V2 behaviour features (`Engagement_Score`, `Baseline_Engagement`, `Engagement_Deviation`, `Behaviour_Trend`). The investigation comprehensively searched current files, the entire Git history, internal datasets, and notebooks. 

**Conclusion:** The original data generator **does not exist** in this repository. The `MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx` dataset was generated ex-situ (externally) and committed directly as a binary artifact. `Engagement_Score` was purely stochastic (`SIMULATED`) and not deterministically derived. Because the original simulation code is permanently absent, the runtime pipeline cannot safely reconstruct these features without inventing new semantics. Step 10 is therefore fundamentally BLOCKED.

## 2. Search Scope
- **Current Files**: All `.py`, `.ipynb`, `.md`, and `.xlsx` files across `engine/`, `backend/`, and `chatbot/`.
- **Git History**: Full repository commit history, deleted files, and diffs (searched via `git log -p`).
- **Dataset Metadata**: Sheets inside `MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx` and `MEDHA_Synthetic_1000x30-1.xlsx`.

## 3. Git History Investigation
Searched the full repository git log for:
- `Engagement_Score`
- `Baseline_Engagement`
- `Behaviour_Trend`
- `MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx`

**Findings**: The terms only appear in configuration lists, schemas, model documentation, downstream model tests, and the `medha_state.py` wrapper. There is absolutely no commit history containing Python formulas, pandas transformations, or simulation logic (e.g., `np.random.normal()`) for these features. The Excel dataset was committed as a binary object without an accompanying generation script.

## 4. Local File Investigation
Searched `engine/data_generation`, `engine/behaviour_engine`, and `engine/fusion_engine` for Python scripts. The only scripts present are for parsing the already-generated dataset (e.g., `create_v2_split.py`), training models (`train_v2_behaviour_dds.py`), and generating out-of-fold predictions. No dataset simulator exists.

## 5. Notebook Investigation
Searched `engine/Structured_risk_enigne/longitudinal_data.ipynb` and all other notebooks.
**Findings**: The notebook simply reads `MEDHA_Synthetic_1000x30-1.xlsx` via `pd.read_excel()` and runs `df.info()`. It does not contain the code that produced the Excel file. 

## 6. Dataset Metadata Investigation
Analyzed `MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx`.
- **Data_Dictionary Sheet**: Explicitly categorizes `Engagement_Score` as `SIMULATED` (a stochastic base variable), and `Baseline_Engagement`, `Engagement_Deviation`, and `Behaviour_Trend` as `DERIVED`.
- **Generation_Methodology Sheet**: Contains high-level conceptual text (e.g., "Noisy structured, behavioural, text, voice, diary and professional signals") but contains zero mathematical formulas.
- **Formulas**: The Excel cells contain raw literal numbers (`float64`), not Excel formulas (e.g., `=A2-B2`).

## 7. Candidate Generator Sources
None found.

## 8. Provenance Assessment
**D — Unrelated/obsolete generation logic.** 
We found no generator at all. The generation was performed externally by the data science team.

## 9. Engagement_Score Recovery
- **Exact Generation Rule**: Unavailable.
- **Mathematical Formula**: Unavailable.
- **Input Variables**: None (Stochastic).
- **Random Process**: Yes (Simulated base variable).

## 10. Baseline_Engagement Recovery
- **Exact Generation Rule**: Unavailable. Likely a rolling average of `Engagement_Score`, but specific windows and missing-value rules are unknown.

## 11. Engagement_Deviation Recovery
- **Exact Generation Rule**: Unavailable. Likely `Engagement_Score - Baseline_Engagement`, but cannot be reconstructed because the base variables are missing.

## 12. Behaviour_Trend Recovery
- **Exact Generation Rule**: Unavailable. Unknown if slope, delta, or categorical.

## 13. Other Frozen Behaviour Features
Features like `Missed_Checkin` and `Session_Duration_Minutes` are also listed as `SIMULATED`, but their real-world semantics are obvious (count of missed checkins, length of session) and are already perfectly captured by Step 9A. 

## 14. Dataset Reproduction Validation
Impossible to reproduce without the generator.

## 15. Leakage Assessment
N/A. Generator not found.

## 16. Runtime Reconstructability
**Impossible**. We cannot reconstruct abstract engineered traits (`Engagement_Score`, `Behaviour_Trend`) from raw events without an authoritative formula. Doing so would break the core assumption of the frozen model.

## 17. Final Recommendation
Do not attempt to guess the formulas. The frozen `Behaviour Specialist` (Ridge model) expects a specific distribution of `Engagement_Score` that we cannot replicate. 

**Recommendation**: The ML/Data Science team must either:
1. Provide the original data generation script so we can port the `Engagement_Score` formulas into the `BehaviourSpecialistAdapter`.
2. Or, retrain a new V3 `Behaviour Specialist` using the deterministic event metrics currently produced by Step 9A (e.g., `App_Interaction_Duration`, `Journal_Entry_Count`).

## 18. Step 10 Readiness
**STEP 10 BLOCKED — GENERATOR NOT RECOVERED**.

- **Unresolved Features**: `Engagement_Score`, `Baseline_Engagement`, `Engagement_Deviation`, `Behaviour_Trend`.
- **Sources Searched**: Full repository git log, local `.py` and `.ipynb` files, Excel Data Dictionaries.
- **Evidence Insufficient**: The Excel metadata proves the features were generated synthetically, but the code to generate them was never committed to this repository.
- **Artifact Required**: The original data generation python script (`generate_dataset.py` or equivalent) or an authoritative mathematical specification from the ML team.
