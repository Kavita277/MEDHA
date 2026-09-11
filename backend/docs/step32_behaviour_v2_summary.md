# Step 32 — Behaviour/V2 Integration Tests Summary

## 1. Objective

Step 32 implements end-to-end integration and boundary tests connecting behavior telemetry, feature aggregation, specialist model evaluation, and multi-modal V2 fusion as specified in `backend/docs/backend_plan.md §32`.

The testing suite validates:
1. The end-to-end telemetry pipeline from raw telemetry events through database persistence, feature aggregation, specialist inference, and V2 fusion.
2. Ingestion idempotency and stability under duplicate events.
3. Graceful fallback and contract adherence under missing modalities (text, voice, behavior).
4. Automated imputation of missing structured features via `SimpleImputer`.
5. Missing voice inference semantics and availability flags.
6. The frozen 7-timestep temporal history boundary condition for the PyTorch GRU model.
7. Valid 8-timestep longitudinal GRU execution.
8. Multiple timepoint isolation and strictly historical baseline calculation across $T_1 \rightarrow T_2 \rightarrow T_3$.
9. Regression verification of frozen V2 pipeline contract boundaries and limitations without modifying production or ML engine code.

---

## 2. Pipeline Under Test

The integration pipeline spans the following architectural layers:

```
[Raw Telemetry Events]
        │
        ▼ (EventRepository.batch_insert_idempotent)
[RawEventModel Table]
        │
        ▼ (BehaviourAggregatorService.aggregate_case_timepoint)
[BehaviourFeatureSnapshotModel Table] (10 Authoritative Metrics + Deviations)
        │
        ▼ (generate_predictions / map_behaviour_to_v2)
[MedhaV2Pipeline / Specialists]
   ├─ Structured Specialist (XGBoost Regressor)
   ├─ Text Specialist (Ridge Regressor Core 5)
   ├─ Voice Specialist (Ridge Regressor Core 5)
   └─ Behaviour Specialist (Ridge Regressor All 10)
        │
        ▼
[V2 Fusion Model] (XGBoost Regressor → DDS ∈ [0, 100])
        │
        ▼ (Longitudinal Dataframe, >= 8 Timepoints)
[V2 GRU Temporal Model] (PyTorch GRU → Temporal Risk Score ∈ [0, 1])
        │
        ▼
[PredictionResultModel Table] (Persisted Case Prediction Record)
```

---

## 3. Detailed Scenarios & Observed Behavior

### Scenario 1: RAW EVENTS → BEHAVIOUR → SPECIALIST → FUSION
- **Test**: `test_scenario_1_raw_events_to_behaviour_to_specialist_to_fusion`
- **Execution Flow**:
  - Ingested 8 legitimate telemetry events: `session_start`, `journal_saved`, `chat_message_sent`, `checkin_prompt_shown`, `checkin_started`, `checkin_completed`, `support_resource_accessed`, `session_end`.
  - Persisted events idempotently via `EventRepository.batch_insert_idempotent()`.
  - Executed `BehaviourAggregatorService.aggregate_case_timepoint()`, producing authoritative metrics (`app_interaction_duration = 900.0s`, `journal_entry_count = 1.0`, `chat_message_count = 1.0`, `checkin_completion_rate = 1.0`, `checkin_response_delay = 14.0s`, `support_resource_access_count = 1.0`).
  - Persisted `BehaviourFeatureSnapshotModel`.
  - Triggered `generate_predictions()`, executing the real frozen V2 pipeline.
- **Observed Behavior**:
  - Events successfully persisted and aggregated.
  - Real Behaviour Specialist (Ridge all-10) executed and generated valid predictions.
  - Real V2 Fusion Model (XGBoost) executed and produced `Fusion_DDS_Prediction` within the contract range $[0.0, 100.0]$.
  - `PredictionResultModel` was created and persisted with valid `triage_level`.

### Scenario 2: DUPLICATE EVENTS
- **Test**: `test_scenario_2_duplicate_events_idempotency_and_stability`
- **Execution Flow**:
  - Ingested an initial batch of 6 events with fixed UUID `event_id` values.
  - Re-ingested the exact same batch of 6 events with identical `event_id` values.
  - Evaluated aggregation metrics and prediction outputs between single and duplicate ingestion runs.
- **Observed Behavior**:
  - `EventRepository.batch_insert_idempotent()` safely caught the `IntegrityError` via nested transaction savepoints, returning `inserted_count = 0` for duplicates without failing the transaction.
  - Raw event count in the database remained strictly at 6.
  - Metric counts (`journal_entry_count`, `chat_message_count`, `app_interaction_duration`) were not inflated.
  - Resulting `behav_pred` and `fusion_dds_prediction` matched the single-event baseline with zero distortion.

### Scenario 3: MISSING MODALITY
- **Test**: `test_scenario_3_missing_modality_graceful_fallback`
- **Execution Flow**:
  - Tested missing text (`Text_Available = 0`), missing voice (`Voice_Available = 0`), missing behavior (`Behav_Available = 0`), and combinations thereof.
- **Observed Behavior**:
  - When a modality is marked unavailable, its corresponding specialist prediction is `None` in the returned dictionary and `NaN` in pipeline calculations.
  - Fusion input zero-fills missing specialist predictions and conditions on availability flags.
  - Fusion prediction executes without exception and yields valid DDS scores within $[0.0, 100.0]$.

### Scenario 4: MISSING STRUCTURED FEATURES
- **Test**: `test_scenario_4_missing_structured_features_imputation`
- **Execution Flow**:
  - Omitted relevant clinical and case features: `Missed_Checkin`, `Upcoming_Hearing`, and `Investigation_Delay`.
  - Processed incomplete feature dictionary through `run_v2_inference()`.
- **Observed Behavior**:
  - The frozen preprocessor (`struct_preproc` containing `SimpleImputer`) successfully imputed missing features from training distributions.
  - `Struct_Pred` was generated without error.
  - Fusion DDS was successfully calculated.

### Scenario 5: MISSING VOICE
- **Test**: `test_scenario_5_missing_voice_inference`
- **Execution Flow**:
  - Provided legitimate structured, text, and behavior features, but omitted voice features and set `Voice_Available = 0.0`.
- **Observed Behavior**:
  - `Voice_Available` accurately reflected unavailable voice.
  - `Voice_Pred` was `None`.
  - `Struct_Pred`, `Text_Pred`, and `Behav_Pred` evaluated cleanly.
  - Fusion DDS prediction succeeded within contract bounds.

### Scenario 6: INSUFFICIENT GRU HISTORY
- **Test**: `test_scenario_6_insufficient_gru_history_boundary`
- **Execution Flow**:
  - Constructed a longitudinal sequence of length 7 ($T_1$ through $T_7$) for a single `Victim_ID`.
- **Observed Behavior**:
  - In `MedhaV2Pipeline.predict_v2`, the loop requires a window of length 7 *prior* to index $i$ (`window = features[i - 7 : i]`).
  - For rows $i = 0 \dots 6$ (timesteps $T_1 \dots T_7$), fewer than 7 prior timesteps exist.
  - Verified across all 7 rows:
    - `Temporal_Available == 0`
    - `Temporal_Risk_Score` is `NaN` / `None`
    - `Future_Escalation_Flag` is `NaN` / `None`
  - Specifically confirmed that $T_7$ (index 6, with 6 prior rows) is NOT eligible for temporal inference.

### Scenario 7: VALID SEVEN-TIMESTEP HISTORY
- **Test**: `test_scenario_7_valid_seven_timestep_history_gru_inference`
- **Execution Flow**:
  - Constructed a longitudinal sequence of 10 timesteps ($T_1$ through $T_{10}$) for the same `Victim_ID`.
  - Executed inference using the real frozen PyTorch GRU model (`best_gru_model.pth`).
- **Observed Behavior**:
  - Rows 0 through 6 ($T_1 \dots T_7$) had `Temporal_Available == 0`.
  - Row 7 ($T_8$, having 7 prior timesteps $T_1 \dots T_7$) was the first eligible row.
  - At $T_8$:
    - `Temporal_Available == 1`
    - `Temporal_Risk_Score` was a valid probability ($0.0 \le \text{score} \le 1.0$)
    - `Future_Escalation_Flag` was a valid binary flag ($0$ or $1$)
  - Rows 8 and 9 ($T_9, T_{10}$) also completed temporal inference successfully.

### Scenario 8: MULTIPLE TIMEPOINTS
- **Test**: `test_scenario_8_multiple_timepoints_isolation_and_baselines`
- **Execution Flow**:
  - Simulated sequential timepoints $T_1 \rightarrow T_2 \rightarrow T_3$ with distinct event timestamps and durations:
    - $T_1$: `duration = 100s`, `delay = 5.0s`
    - $T_2$: `duration = 200s`, `delay = 15.0s`
    - $T_3$: `duration = 300s`, `delay = 2.0s`
- **Observed Behavior**:
  - $T_1$: Cold start, strictly prior history is empty $\rightarrow$ deviations are `None`.
  - $T_2$: Prior mean $[100.0 \text{ duration}, 5.0 \text{ delay}]$ $\rightarrow$ deviations: `duration_dev = +100.0`, `delay_dev = +10.0`.
  - $T_3$: Prior mean $[150.0 \text{ duration}, 10.0 \text{ delay}]$ $\rightarrow$ deviations: `duration_dev = +150.0`, `delay_dev = -8.0`.
  - Verified no future data leaked into earlier baselines.
  - Verified all snapshots and prediction records maintained strict timepoint association.

---

## 4. Frozen V2 Contract Discrepancy & Limitation Report

In accordance with §32 instructions (*"If an existing V2 contract fails, REPORT the failure. Do not change V2 to make the test pass."* and *"write a regression/contract test that exposes the discrepancy where appropriate"*), we document the following finding:

### Finding: Cold-Start `None` Deviation Incompatibility with `Series.abs()`
- **Mechanism**:
  1. At $T_1$ (cold start), `BehaviourAggregatorService` calculates deviations as `None` (SQL `NULL`), strictly reflecting that zero prior observations exist.
  2. `map_behaviour_to_v2()` maps these into `current_features` as `{"Engagement_Deviation": None, "Response_Delay_Deviation": None}`.
  3. `run_v2_inference()` instantiates a DataFrame: `df = pd.DataFrame([row_data])`. In pandas, a column initialized with `None` receives `dtype: object`.
  4. In `engine/v2/medha_v2_pipeline.py` (lines 160–162):
     ```python
     if "Engagement_Deviation" in behav_df.columns:
         behav_df["Engagement_Deviation"] = behav_df["Engagement_Deviation"].abs()
     if "Response_Delay_Deviation" in behav_df.columns:
         behav_df["Response_Delay_Deviation"] = behav_df["Response_Delay_Deviation"].abs()
     ```
  5. Calling `.abs()` on an `object` series containing Python `None` invokes `np.abs(None)`, which raises:
     ```
     TypeError: bad operand type for abs(): 'NoneType'
     ```
- **Context & Precedent**:
  - When deviation columns contain `np.nan` (float) or numeric values like `0.0`, `Series.abs()` succeeds without error.
  - In Step 30, demo seed data initialized cold-start baseline deviations as `0.0` (rather than `None`), which allowed $T_1$ inference to execute cleanly.
  - In `test_step32_behaviour_v2_integration.py`, we added a dedicated contract test (`test_frozen_v2_cold_start_none_deviation_limitation`) verifying this exact `TypeError` behavior when calling `generate_predictions` directly on a raw cold-start snapshot containing `None`.
- **Resolution**:
  - In strict compliance with §32 instructions, **NO application or ML engine code was modified**.
  - The behavior is exposed and verified via `test_frozen_v2_cold_start_none_deviation_limitation`.
  - For $T_1$ prediction generation in Scenario 8, the Step 30 convention of initializing cold-start baseline deviations to `0.0` is followed. At $T_2$ and $T_3$, deviations are computed dynamically by `BehaviourAggregatorService` as floats and pass directly into the pipeline.

---

## 5. Verification & Test Execution Results

### Focused Test Suite
```bash
python -m pytest backend/tests/test_step32_behaviour_v2_integration.py -v
```
**Results**:
- `test_scenario_1_raw_events_to_behaviour_to_specialist_to_fusion`: **PASSED**
- `test_scenario_2_duplicate_events_idempotency_and_stability`: **PASSED**
- `test_scenario_3_missing_modality_graceful_fallback`: **PASSED**
- `test_scenario_4_missing_structured_features_imputation`: **PASSED**
- `test_scenario_5_missing_voice_inference`: **PASSED**
- `test_scenario_6_insufficient_gru_history_boundary`: **PASSED**
- `test_scenario_7_valid_seven_timestep_history_gru_inference`: **PASSED**
- `test_scenario_8_multiple_timepoints_isolation_and_baselines`: **PASSED**
- `test_frozen_v2_cold_start_none_deviation_limitation`: **PASSED**
- **Total**: **9 passed, 0 failed** in 10.63s

### Complete Backend Test Suite
```bash
python -m pytest backend/tests -v
```
**Results**:
- **267 passed, 0 failed** (258 baseline tests + 9 Step 32 integration tests)

---

## 6. Architectural Integrity Invariants

- **Production / Application Code**: 0 modifications.
- **Existing Test Code**: 0 modifications.
- **ML Engines / Preprocessors / Weights / Configs**: 0 modifications.
- **Alembic Database Migrations**: 0 created.
- **Mocking**: 0 mocks in Step 32; all tests executed against real SQLite persistence, XGBoost specialists, Linear Ridge specialists, and the real PyTorch GRU model.
