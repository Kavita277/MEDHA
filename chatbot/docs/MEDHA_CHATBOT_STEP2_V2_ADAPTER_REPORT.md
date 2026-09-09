# MEDHA CHATBOT — STEP 2: V2 ADAPTER REPORT

## 1. Objective

The objective of Step 2 is to create a thin, rigorously validated adapter between the chatbot's internal `MedhaState` and the **existing, frozen MEDHA V2 predictive pipeline** (`MedhaV2Pipeline.predict_v2()`). 

The adapter enables the chatbot layer to take accumulated validated session data, format it into the exact DataFrame required by the frozen V2 system, invoke `predict_v2()`, and return the authoritative V2 predictions wrapped in a clean, immutable result container without modifying, replacing, retraining, or redesigning any existing V2 component.

---

## 2. Existing V2 Contract Audited

A thorough line-by-line inspection of [`engine/v2/medha_v2_pipeline.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/v2/medha_v2_pipeline.py), [`docs/MEDHA_V2_DATA_CONTRACT.md`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/docs/MEDHA_V2_DATA_CONTRACT.md), and [`docs/MEDHA_V2_API_HANDOFF.md`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/docs/MEDHA_V2_API_HANDOFF.md) established the following authoritative requirements:

| Dimension | Authoritative V2 Implementation Rule |
| :--- | :--- |
| **Input Type** | Strictly a `pandas.DataFrame`. |
| **Identity & Order** | `Victim_ID` (string/object) and `Timepoint` (integer sequence). |
| **Availability Flags** | `Text_Available` and `Voice_Available` must be explicitly passed as `1.0` or `0.0`. `Struct_Available` and `Behav_Available` are internally treated as `1.0`. |
| **Structured Features** | 42 columns matching [`v2_structured_dds_features.json`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/models/v2/v2_structured_dds_features.json): 3 categorical (`Case_Type`, `Case_Stage`, `Episode_Severity`) and 39 numeric columns. |
| **Text Features** | 5 numeric MuRIL-derived columns: `Text_Distress`, `Fear`, `Threat_Context`, `Negative_Affect`, `Urgency`. |
| **Voice Features** | 5 numeric acoustic columns: `Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator`. |
| **Behaviour Features** | 10 numeric interaction columns matching [`v2_behaviour_dds_features.json`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/models/behaviour_dds_v2/v2_behaviour_dds_features.json). |
| **GRU Whitelist** | 57 numerical features matching `engine/models/v2/gru_sequences/feature_config.json`. Includes 6 additional baseline/trend features: `Baseline_Text_Distress`, `Baseline_Voice_Distress`, `Text_Distress_Deviation`, `Voice_Distress_Deviation`, `Text_Distress_Trend`, `Voice_Distress_Trend`. |
| **Missingness Semantics** | Unobserved features must be represented as `np.nan` (never `0.0`). The preprocessor handles them via fitted median imputation (numeric) and constant `"MISSING"` + ordinal encoding (categorical). |
| **Missing Modality Semantics** | When voice is unavailable, `Voice_Available = 0.0` and all 5 voice columns are `np.nan`. The specialist assigns `Voice_Pred = np.nan`, and Fusion zeroes it before passing into XGBoost with `Voice_Available = 0.0`. It is **never** interpreted as low distress. |
| **Longitudinal History** | GRU requires 7 preceding historical timesteps for a victim (`[i-7 : i]`). If history < 7, `Temporal_Risk_Score = np.nan` and `Temporal_Available = 0`. |
| **Output Contract** | `predict_v2()` appends: `Struct_Pred`, `Struct_Available`, `Text_Pred`, `Text_Available`, `Voice_Pred`, `Voice_Available`, `Behav_Pred`, `Behav_Available`, `Fusion_DDS_Prediction` (0-100), `Temporal_Risk_Score` (0-1), `Temporal_Available` (1 or 0), `Future_Escalation_Flag` (1, 0, or NaN). |

---

## 3. Files Created

1. [`chatbot/v2_adapter/__init__.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/v2_adapter/__init__.py): Exported `MedhaV2Adapter` and `V2PredictionResult`.
2. [`chatbot/v2_adapter/medha_v2_adapter.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/v2_adapter/medha_v2_adapter.py): Core adapter implementing state conversion, missingness preservation, candidate observation isolation, pipeline invocation, and output packaging.
3. [`chatbot/tests/test_v2_adapter.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/tests/test_v2_adapter.py): Comprehensive test suite covering tests 1 through 10.
4. [`MEDHA_CHATBOT_STEP2_V2_ADAPTER_REPORT.md`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/MEDHA_CHATBOT_STEP2_V2_ADAPTER_REPORT.md): This dedicated step report.

---

## 4. Files Modified

- **`engine/` Files Modified**: **NONE**. Zero files in `engine/` or its subdirectories were modified, retrained, or altered.
- **Model Checkpoints**: **NONE**. All SHA-256 hashes remain identical.

---

## 5. Adapter Architecture

The adapter strictly enforces an outward-to-inward flow:

```text
                  MedhaState
                      │
                      ▼
               MedhaV2Adapter
        ┌─────────────┴─────────────┐
        ▼                           ▼
   state_to_row()        build_input_dataframe()
 (Preserves NaN;        (Merges history states;
  Enforces flags;        Orders by Timepoint;
  Isolates candidates)   Validates canonical schema)
                      │
                      ▼
               Longitudinal DF
                      │
                      ▼
        MedhaV2Pipeline.predict_v2()
          [FROZEN PREDICTIVE SYSTEM]
                      │
                      ▼
           Downstream TriageEngine
         (Engineering Demonstration)
                      │
                      ▼
              V2PredictionResult
         (Immutable result container)
```

### Key Interface Methods
- `adapter.state_to_row(state: MedhaState) -> Dict[str, Any]`
- `adapter.build_input_dataframe(state, history_states=None, history_df=None) -> pd.DataFrame`
- `adapter.predict(state, history_states=None, history_df=None) -> V2PredictionResult`

---

## 6. Missingness Handling

The adapter implements strict compliance with the V2 Data Contract:
1. **Generic Missing Values**:
   - Any unobserved feature in `structured_features`, `text_features`, `voice_features`, or `behaviour_features` is mapped directly to `np.nan`.
   - Under no circumstances does the adapter set missing values to `0.0`.
2. **Unavailable Voice**:
   - If `state.voice_available == 0.0` (or `None`), the adapter sets `df["Voice_Available"] = 0.0` and explicitly fills all 5 voice columns (`Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator`) with `np.nan`.
   - `predict_v2()` sets `Voice_Pred = np.nan` and handles the meta-learner vector safely without attributing false low distress.
3. **Unavailable Text**:
   - If `state.text_available == 0.0` (or `None`), `df["Text_Available"] = 0.0` and all 5 text columns are set to `np.nan`.

---

## 7. Candidate Observation Boundary

In accordance with architectural rules:
- `MedhaState.candidate_observations` contains qualitative conversational extractions (e.g. `sleep = poor`, `stress = high`).
- `MedhaV2Adapter.state_to_row()` **explicitly ignores** `candidate_observations`.
- It only reads from `state.structured_features`, `state.text_features`, `state.voice_features`, and `state.behaviour_features`.
- If a qualitative observation has not passed through an authoritative feature mapper into `structured_features`, the corresponding V2 column remains `np.nan`.
- Verified by **Test 4**, which confirmed that adding candidate observations like `sleep = poor` leaves `df["Sleep"]` as `np.nan`.

---

## 8. Tests Executed

1. **Adapter Test Suite**:
   ```bash
   python -m pytest chatbot/tests/test_v2_adapter.py -v
   ```
2. **Full Chatbot Test Suite (State + Adapter)**:
   ```bash
   python -m pytest chatbot/tests/ -v
   ```
3. **Frozen MEDHA V2 Regression Suite**:
   ```bash
   python -m pytest engine/tests/
   ```

---

## 9. Test Results

### Chatbot Tests (`chatbot/tests/`)
```text
chatbot/tests/test_medha_state.py::test_empty_state PASSED
chatbot/tests/test_medha_state.py::test_partial_state PASSED
chatbot/tests/test_medha_state.py::test_complete_state PASSED
chatbot/tests/test_medha_state.py::test_missing_optional_modalities PASSED
chatbot/tests/test_medha_state.py::test_nan_structured_values PASSED
chatbot/tests/test_medha_state.py::test_conversation_history PASSED
chatbot/tests/test_medha_state.py::test_question_history PASSED
chatbot/tests/test_medha_state.py::test_candidate_observations_separation PASSED
chatbot/tests/test_medha_state.py::test_serialization_and_deserialization PASSED
chatbot/tests/test_medha_state.py::test_invalid_feature_names PASSED
chatbot/tests/test_medha_state.py::test_invalid_data_types PASSED
chatbot/tests/test_medha_state.py::test_invalid_state_creation PASSED
chatbot/tests/test_medha_state.py::test_modality_availability_validation PASSED
chatbot/tests/test_v2_adapter.py::test_1_minimal_valid_state PASSED
chatbot/tests/test_v2_adapter.py::test_2_partial_state PASSED
chatbot/tests/test_v2_adapter.py::test_3_voice_unavailable PASSED
chatbot/tests/test_v2_adapter.py::test_4_candidate_observation_isolation PASSED
chatbot/tests/test_v2_adapter.py::test_5_feature_whitelist PASSED
chatbot/tests/test_v2_adapter.py::test_6_input_schema PASSED
chatbot/tests/test_v2_adapter.py::test_7_existing_pipeline_invocation PASSED
chatbot/tests/test_v2_adapter.py::test_8_output_preservation PASSED
chatbot/tests/test_v2_adapter.py::test_9_failure_handling PASSED
chatbot/tests/test_v2_adapter.py::test_10_longitudinal_gru_history PASSED

Result: 23 passed, 0 failed in 4.53s
```

---

## 10. Frozen V2 Regression Result

```text
engine/tests/test_v2_ablation.py ....                                    [  1%]
engine/tests/test_v2_backend_smoke.py ......                             [  4%]
engine/tests/test_v2_behaviour_dds.py .......                            [  7%]
engine/tests/test_v2_feature_policy.py ...........                       [ 12%]
engine/tests/test_v2_fusion.py ......................................... [ 30%]
......                                                                   [ 33%]
engine/tests/test_v2_fusion_final.py ......                              [ 36%]
engine/tests/test_v2_fusion_oof.py .........                             [ 40%]
engine/tests/test_v2_gru_sequences.py .................................. [ 55%]
...................................                                      [ 70%]
engine/tests/test_v2_gru_training.py ................................... [ 86%]
..                                                                       [ 87%]
engine/tests/test_v2_inference_io.py .                                   [ 87%]
engine/tests/test_v2_pipeline_integration.py ..                          [ 88%]
engine/tests/test_v2_priority_triage.py ......                           [ 91%]
engine/tests/test_v2_structured_dds.py ......                            [ 94%]
engine/tests/test_v2_text_dds.py ......                                  [ 96%]
engine/tests/test_v2_voice_dds.py .......                                [100%]

Result: 224 passed, 20 warnings in 10.53s
Failures: 0
Total Repository Tests: 247 passed, 0 failed
```

---

## 11. Assumptions

1. **Pipeline Instantiation**: `MedhaV2Pipeline` is instantiated lazily or accepted via dependency injection, allowing fast unit testing and mock verification without reloading model weights for every test.
2. **Historical State Precedence**: Historical states passed to `build_input_dataframe()` or `predict()` must have the same `Victim_ID` and strictly smaller `Timepoint` numbers than the active state.

---

## 12. Known Limitations

1. **Text/Voice Upstream Extraction**: The adapter expects numeric text and voice features to already be populated in `MedhaState` (or left missing). Connecting raw audio and raw conversational text to the Text/Voice engines is intentionally deferred to Step 3 (Text Engine Adapter) and Step 11 (Voice Integration).
2. **Feature Mapping**: Semantic translation of conversational text into validated V2 values is intentionally deferred to Step 6 (Feature Mapper + Validator).

---

## 13. Architecture Compliance Certification

- [x] **No model retraining**: No models trained.
- [x] **No model replacement**: Frozen checkpoints preserved verbatim.
- [x] **No fusion redesign**: Meta-learner called via `predict_v2()`.
- [x] **No GRU redesign**: 7-timestep sequence logic preserved via `predict_v2()`.
- [x] **No new risk model**: Standard V2 risk outputs used exclusively.
- [x] **No modification of frozen V2 inference**: `MedhaV2Pipeline` unchanged.
- [x] **No fabricated features**: Missing information strictly preserved as `np.nan`.
- [x] **Candidate observations isolated**: Qualitative observations do not leak into V2 features.

---

## 14. Step 2 Status

`STEP 2 STATUS: PASS`
