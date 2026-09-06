# MEDHA — FINAL ANTIGRAVITY IMPLEMENTATION & TRAINING INSTRUCTIONS

## 0. Mission

You are implementing the finalized MEDHA longitudinal multimodal distress pipeline inside the existing MEDHA repository.

Repository:
`https://github.com/Kavita277/MEDHA.git`

This repository is the authoritative codebase for the existing engines. It contains the existing Text Engine, Voice Engine, Behaviour Engine, the older Structured-risk workflow, and the legacy Temporal GRU workflow.

The old Structured dataset and legacy Temporal GRU implementation are NOT authoritative for the new architecture. Do not accidentally train the new system from them.

The corrected synthetic datasets supplied with this prompt are the authoritative raw-data source for the new training workflow.

---

# 1. NON-NEGOTIABLE ARCHITECTURE

MEDHA has EXACTLY THREE risk modalities:

1. Text
2. Voice
3. Behaviour

Final architecture:

Text
  -> EXISTING Text Engine
  -> Text GRU
  -> Text Logit

Voice
  -> EXISTING Voice Engine
  -> Voice GRU
  -> Voice Logit

Behaviour
  -> EXISTING Behaviour Engine
  -> Behaviour GRU
  -> Behaviour Logit

Text Logit
Voice Logit
Behaviour Logit
       +
Structured Context as conditioning information
       |
       v
Gated Late Fusion
       |
       v
Final Distress Probability
       |
       v
Distress Trajectory

Structured Context is NOT a fourth modality.

Structured Context:
- has NO GRU
- produces NO fusion risk logit
- must never become `structured_logit`
- must never become `structured_risk`
- must never be added as a fourth weighted risk pathway

It may condition the fusion gate.

Question Engine is adaptive data collection, NOT a risk modality.

Safety pathway is separate from ordinary distress estimation.

---

# 2. FIRST ACTION — INSPECT BEFORE MODIFYING

Before writing or modifying code:

1. Inspect the entire repository.
2. Identify the actual current files and artifact locations.
3. Read:
   - `engine/text engine/medha_text_engine.py`
   - `engine/voice_engine/voice_engine.py`
   - `engine/behaviour_engine/medha_scoring_api.py`
   - `engine/Structured_risk_enigne/inference.py`
   - `engine/gru-temporal-risk/src/model.py`
   - relevant preprocessing/sequence-building files
4. Identify all model checkpoints/joblib/pkl/npy artifacts.
5. Identify existing dependencies.
6. Do NOT assume the repository is identical to documentation.
7. Do NOT overwrite files merely because they look obsolete.
8. Prefer NEW files for the new pipeline.
9. Clearly report:
   - EXISTING FILE — READ ONLY
   - EXISTING FILE — EXPLICITLY MODIFIED
   - NEW FILE

STOP if repository inspection reveals a conflict with this specification. Do not silently improvise.

---

# 3. FROZEN EXISTING ENGINES

The following are frozen and must not be changed unless this prompt explicitly says otherwise:

## Existing Text Engine

Path:
`engine/text engine/medha_text_engine.py`

It currently:
- loads tokenizer/model from `Models/medha_final_model`
- constructs the MuRIL sequence classifier
- loads `medha_model.pt`
- exposes `get_medha_text_features(text)`
- returns five values:
  - `text_distress`
  - `fear_signal`
  - `threat_context`
  - `negative_affect`
  - `urgency`

Canonical Text vector:

```text
[
    text_distress,
    fear_signal,
    threat_context,
    negative_affect,
    urgency
]
```

Size = 5.

IMPORTANT:
The supplied repository snapshot did NOT contain `medha_model.pt`.

If the checkpoint is still missing:
- DO NOT fabricate Text Engine outputs.
- DO NOT substitute random weights.
- DO NOT silently replace the engine with another classifier.
- Mark Text inference/training as BLOCKED until the real checkpoint is available.

---

## Existing Voice Engine

Path:
`engine/voice_engine/voice_engine.py`

Use its real:
`VoiceEngine.analyze(audio_path)`

It uses the existing voice models and feature definitions.

Canonical Voice vector:

```text
[
    voice_distress,
    confidence,
    angry,
    sad,
    neutral,
    happy,
    duration_seconds,
    rms_energy,
    pitch_mean,
    pitch_std,
    zero_crossing_rate,
    speaking_rate,
    acoustic_indicator
]
```

Size = 13.

DO NOT fabricate Voice Engine outputs.

The voice CSV is a manifest/control dataset. It is not a collection of fabricated model predictions.

If actual audio cannot be produced and supplied to `VoiceEngine.analyze()`:
- mark Voice processing BLOCKED
- do not replace it with synthetic probabilities
- do not claim Voice GRU training is complete.

---

## Existing Behaviour Engine

Path:
`engine/behaviour_engine/medha_scoring_api.py`

Use its actual API.

Raw input fields are exactly:

```text
day_index
completion_baseline_z
latency_baseline_z
question_skip_rate
session_duration_baseline_z
response_length_baseline_z
missed_checkins
```

Its output contains:

```text
anomaly_score
engagement_deviation
inactivity_score
behavioral_risk_score
triage_status
insufficient_history
gru_sequence
gru_sequence_mask
```

For the new Behaviour GRU, use ONLY:

```text
[
    anomaly_score,
    engagement_deviation,
    inactivity_score
]
```

Size = 3.

Do NOT put the raw Behaviour API fields inside the Behaviour GRU vector.

Do NOT change the frozen Behaviour Engine.

---

# 4. AUTHORITATIVE DATASET

Use the supplied corrected dataset bundle:

`MEDHA_Longitudinal_Synthetic_1000x30_LATIN_ONLY.zip`

After extracting it, the authoritative files are:

```text
MEDHA_Longitudinal_Synthetic_1000x30/
    master_raw_longitudinal_1000x30.csv
    patient_profiles.csv
    text_engine_raw_input_500x30.csv
    voice_engine_raw_manifest_500x30.csv
    behaviour_engine_raw_input_500x30.csv
    structured_context_1000x30.csv
    targets_1000x30.csv
    scenario_distribution.csv
    data_dictionary.csv
    scientific_reference_mapping.csv
    README.md
```

The corrected Text and Voice files are the important replacements.

DO NOT use the old:

`engine/Structured_risk_enigne/data/MEDHA_Synthetic_1000x30-1.xlsx`

as the training source for the new pipeline.

It is retained only for historical/reference purposes.

DO NOT use the old:

`engine/gru-temporal-risk/`

model as the new Text/Voice/Behaviour GRU.

It is legacy/reference only.

---

# 5. TEXT DATA REQUIREMENTS

File:

`text_engine_raw_input_500x30.csv`

Expected:
- 500 patients
- 30 days each
- 15,000 rows
- 15,000 unique raw text samples
- Latin/Roman script only
- NO Devanagari/Hindi Unicode script

Validate these assertions before training:

```python
assert len(df) == 15000
assert df["raw_text"].nunique() == 15000
assert not df["raw_text"].str.contains(r"[\u0900-\u097F]", regex=True).any()
```

Every raw text sample must be treated as an independent patient-day input.

Do not deduplicate, copy, or reuse text across days.

Run the ACTUAL frozen Text Engine over every valid text row.

Create:

`text_engine_outputs_500x30.csv`

Required fields should include identifiers:

```text
patient_id
day_index
```

plus the five actual Text Engine outputs.

Never generate these five values manually.

---

# 6. VOICE DATA REQUIREMENTS

File:

`voice_engine_raw_manifest_500x30.csv`

Expected:
- 500 patients
- 30 days
- 15,000 rows
- 15,000 unique voice sample IDs
- Latin script only in textual metadata

Validate:

```python
assert len(df) == 15000
assert df["voice_sample_id"].nunique() == 15000
assert not df.astype(str).apply(
    lambda col: col.str.contains(r"[\u0900-\u097F]", regex=True).any()
).any()
```

The manifest describes unique patient-day recordings/control specifications.

IMPORTANT:
A manifest is not audio.

You must create or obtain actual audio files that can be passed to:

`VoiceEngine.analyze(audio_path)`

If a deterministic, valid TTS/audio generation mechanism is available in the environment:
- generate actual audio files from the manifest/text
- preserve patient/day/sample IDs
- make the process reproducible with seed 42 where applicable
- document the generator

If valid audio cannot be generated:
STOP Voice processing and clearly report BLOCKED.

Never turn the control columns directly into fake `voice_distress` outputs.

Create:

`voice_engine_outputs_500x30.csv`

only after running the actual frozen Voice Engine.

---

# 7. BEHAVIOUR DATA REQUIREMENTS

File:

`behaviour_engine_raw_input_500x30.csv`

Run the actual frozen Behaviour Engine sequentially for each patient.

Do not shuffle days before scoring.

Do not calculate Behaviour outputs manually if the frozen engine can be invoked.

Create:

`behaviour_engine_outputs_500x30.csv`

with at minimum:

```text
patient_id
day_index
anomaly_score
engagement_deviation
inactivity_score
```

The canonical Behaviour GRU input is exactly the three output fields above.

---

# 8. STRUCTURED CONTEXT

File:

`structured_context_1000x30.csv`

Structured Context is a SUPPORT/CONDITIONING layer.

It can contain:
- case event/context information
- self-report/context
- protective factors
- episode/professional context
- longitudinal context features

But:

DO NOT convert Structured Context into:
- structured risk probability
- structured risk logit
- fourth modality
- fourth GRU

The gate may receive an encoded Structured Context representation.

The gate must still produce exactly three modality weights:

```text
w_text
w_voice
w_behaviour
```

with:

```text
w_text + w_voice + w_behaviour = 1
```

---

# 9. CURRENT VS FUTURE TARGETS

Use:

`targets_1000x30.csv`

The primary task is CURRENT DISTRESS.

Current target:

```text
current_distress_target
```

and/or:

```text
current_distress_label
```

Current distress must never be replaced by a future escalation label.

`future_escalation_label` is a separate optional prediction task.

Do not leak future information into current distress training.

If future escalation is evaluated:
- make it a separate experiment
- clearly label it
- do not feed future values into current distress inputs.

---

# 10. DAILY VECTORS

The final daily modality vectors are FROZEN:

## Text

```text
[
    text_distress,
    fear_signal,
    threat_context,
    negative_affect,
    urgency
]
```

Shape:

```text
[N, 30, 5]
```

## Voice

```text
[
    voice_distress,
    confidence,
    angry,
    sad,
    neutral,
    happy,
    duration_seconds,
    rms_energy,
    pitch_mean,
    pitch_std,
    zero_crossing_rate,
    speaking_rate,
    acoustic_indicator
]
```

Shape:

```text
[N, 30, 13]
```

## Behaviour

```text
[
    anomaly_score,
    engagement_deviation,
    inactivity_score
]
```

Shape:

```text
[N, 30, 3]
```

DO NOT add:
- availability fields
- counts
- time-since fields
- raw Behaviour fields
- trends
- deviations
- extra engineered fields

inside these modality vectors.

Availability masks belong OUTSIDE the modality vectors.

---

# 11. MISSING MODALITY POLICY

Missing does NOT mean:
- zero
- neutral
- average
- imputed fake observation

Use explicit availability masks.

For example:

```text
text_mask
voice_mask
behaviour_mask
```

The exact implementation may be chosen after inspecting the repository, but it must preserve the distinction between:

1. actual observed value
2. missing value

The gate must be able to handle missing modalities.

Do not silently zero-fill missing voice/text/behaviour before scaling.

---

# 12. 30-DAY SEQUENCES

Use exactly 30 days.

For each patient:

```text
Day 1 ... Day 30
```

Construct:

```text
X_text       = [N, 30, 5]
X_voice      = [N, 30, 13]
X_behaviour  = [N, 30, 3]
```

No 7-day replacement.

No overlapping windows that mix patients.

Prefer one complete 30-day sequence per patient.

---

# 13. PATIENT-LEVEL SPLIT

Use patient-level splitting.

Required approximate split:

```text
70% train
15% validation
15% test
```

For 500 primary engine patients, approximately:

```text
350 train
75 validation
75 test
```

The exact assignment must be reproducible with:

```text
seed = 42
```

A patient must appear in exactly one split.

Assert no overlap:

```python
assert set(train_ids).isdisjoint(val_ids)
assert set(train_ids).isdisjoint(test_ids)
assert set(val_ids).isdisjoint(test_ids)
```

Do not split rows randomly.

Do not split individual days across train/validation/test.

---

# 14. SCALING AND PREPROCESSING

Fit scalers ONLY on training patients.

Never fit a scaler on validation or test data.

Never fit on the complete dataset before splitting.

Persist the scalers.

Missing observations must remain distinguishable from true values.

Do not use test data to select:
- thresholds
- hyperparameters
- preprocessing choices
- architecture
- calibration.

---

# 15. NEW TEXT GRU

Build a NEW Text GRU.

Do not modify the old generic Temporal GRU to pretend it is the Text GRU.

Input size:

```text
5
```

Sequence length:

```text
30
```

Output:

```text
one Text logit
```

The Text GRU is trained independently before fusion.

Save:
- model checkpoint
- preprocessing/scaler artifact if used
- configuration
- training history
- validation metrics
- test metrics

Do not fabricate metrics.

---

# 16. NEW VOICE GRU

Build a NEW Voice GRU.

Input size:

```text
13
```

Sequence length:

```text
30
```

Output:

```text
one Voice logit
```

Train and evaluate independently before fusion.

Save:
- checkpoint
- preprocessing artifacts
- configuration
- history
- metrics

If Voice Engine inference is blocked because audio is unavailable, do not claim completion.

---

# 17. NEW BEHAVIOUR GRU

Build a NEW Behaviour GRU.

Input size:

```text
3
```

Sequence length:

```text
30
```

Output:

```text
one Behaviour logit
```

Train and evaluate independently before fusion.

Do not feed raw Behaviour API fields into this GRU.

---

# 18. GRU OUTPUT SEMANTICS

Each GRU produces a logit:

```text
z_text
z_voice
z_behaviour
```

Convert to probability only when needed:

```text
p = sigmoid(z)
```

Do not average probabilities if the specified fusion operates on logits.

---

# 19. GATED LATE FUSION

The fusion stage receives:

```text
z_text
z_voice
z_behaviour
```

plus allowed modality masks and a representation of Structured Context.

It outputs:

```text
w_text
w_voice
w_behaviour
```

Use a softmax or equivalent normalized gating mechanism.

Required:

```text
w_text + w_voice + w_behaviour = 1
```

Final logit:

```text
z_final =
    w_text * z_text +
    w_voice * z_voice +
    w_behaviour * z_behaviour
```

Final distress:

```text
p_final = sigmoid(z_final)
```

ABSOLUTELY FORBIDDEN:

```text
z_structured
structured_risk
structured_probability
structured_logit
```

as a fourth fusion input.

---

# 20. STRUCTURED CONTEXT ABLATION

Evaluate:

### Model A
Three modality logits + modality masks.

### Model B
Three modality logits + modality masks + Structured Context conditioning.

Never compare against a fourth structured risk logit.

---

# 21. COURT-HEARING EDGE CASE

The dataset intentionally contains a critical case:

Patient is stable for approximately 26 days.

On Day 27:
- a real-life court hearing/case event occurs
- the patient reports it
- Structured Context records it
- Text/Voice/Behaviour do NOT show meaningful deterioration

Expected result:

Day 27 final distress should remain near the patient's baseline.

The event alone must NOT cause a sudden high distress score.

Later:

If observable Text/Voice/Behaviour deterioration occurs:
- distress may rise
- recent Structured Context may condition how the gate interprets the signals

The event must not substitute for observable multimodal evidence.

---

# 22. REQUIRED TRAJECTORY LOGIC

Daily final fusion gives:

```text
p_t = sigmoid(z_final,t)
```

Trajectory is derived only from:

```text
p_1 ... p_t
```

No future information.

Track:

- current distress level
- recent change
- causal 7-day rolling mean
- causal trend/slope
- persistence
- volatility

Do NOT introduce another GRU for trajectory.

Do not use future days when calculating a day-t trajectory feature.

---

# 23. REQUIRED STRESS TESTS

Implement explicit tests for:

### A — Event without deterioration
Court/case event but stable modalities.

Expected:
near-baseline distress.

### B — Event followed by delayed deterioration
Event occurs first; multimodal deterioration appears later.

Expected:
distress rises after observable deterioration.

### C — Event followed by recovery
Event and temporary deterioration followed by recovery.

Expected:
temporary elevation then decline.

### D — Deterioration without event
Text/Voice/Behaviour deteriorate without recent structured event.

Expected:
fusion can detect deterioration.

### E — Structured Context unavailable
Only Text/Voice/Behaviour available.

Expected:
system continues.

### F — Modality discordance
One modality strongly disagrees with the others.

Expected:
gate handles disagreement rather than blindly averaging.

### G — Missing modality
One or more modalities absent.

Expected:
explicit mask handling; no fake zero/neutral observation.

---

# 24. REQUIRED ABLATION EXPERIMENTS

Evaluate:

1. Text only
2. Voice only
3. Behaviour only
4. Text + Voice
5. Text + Behaviour
6. Voice + Behaviour
7. All three

Also evaluate:

8. Simple average of the three modality logits
9. Fusion without Structured Context
10. Final gated fusion with Structured Context

The final model must not use a structured risk score.

---

# 25. REQUIRED METRICS

For every independently evaluated model and final fusion:

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- PR-AUC
- Confusion matrix
- test count
- positive count
- negative count
- test loss where applicable
- Brier Score where applicable

Final fusion must also receive a calibration assessment.

Report class imbalance.

Do not report fabricated numbers.

---

# 26. THRESHOLD SELECTION

Do NOT blindly use 0.5.

Choose the final classification threshold using validation data only.

Do not inherit the old Structured XGBoost threshold of 0.16.

Do not tune the threshold on the test set.

Once the threshold is selected:
- freeze it
- evaluate exactly once on the held-out test set.

---

# 27. CALIBRATION

Evaluate calibration of the final distress probability.

Suitable outputs may include:
- Brier score
- reliability/calibration curve
- calibration error if implemented

Any calibrator must be fitted on training/validation data only.

Do not fit calibration using the test set.

---

# 28. REPRODUCIBILITY

Use:

```text
seed = 42
```

Set deterministic seeds where practical for:
- Python
- NumPy
- PyTorch
- data splitting

Document:
- Python version
- PyTorch version
- CPU/GPU
- random seed
- dataset version/hash
- engine artifact hashes
- model configuration

---

# 29. FROZEN ENGINE INTEGRITY CHECK

Before running the pipeline, calculate hashes of frozen engine files/artifacts.

After implementation, calculate them again.

Confirm that the frozen files did not change.

At minimum inspect/hash:

```text
engine/text engine/medha_text_engine.py
engine/voice_engine/voice_engine.py
engine/behaviour_engine/medha_scoring_api.py
```

and the actual model artifacts used by them.

If a frozen file changes unexpectedly:
STOP and report it.

---

# 30. ARTIFACT ORGANIZATION

Create a NEW directory for the new workflow, for example:

```text
engine/multimodal_distress/
```

Suggested structure:

```text
engine/multimodal_distress/
    README.md
    config.py

    data/
        validation/
        processed/

    engines/
        run_text_engine.py
        run_voice_engine.py
        run_behaviour_engine.py

    models/
        text_gru.py
        voice_gru.py
        behaviour_gru.py
        gated_fusion.py

    training/
        train_text_gru.py
        train_voice_gru.py
        train_behaviour_gru.py
        train_fusion.py

    evaluation/
        evaluate_grus.py
        evaluate_fusion.py
        ablations.py
        stress_tests.py
        trajectory_eval.py

    artifacts/
        checkpoints/
        preprocessors/
        metrics/
        reports/
```

You may choose a different organization if repository inspection shows a better fit, but preserve the architecture.

---

# 31. REQUIRED DATA PRODUCTS

After successful engine execution, produce:

```text
text_engine_outputs_500x30.csv
voice_engine_outputs_500x30.csv
behaviour_engine_outputs_500x30.csv
```

Then produce sequence tensors/datasets:

```text
X_text
X_voice
X_behaviour
y_current
modality_masks
structured_context
patient_ids
```

Use a machine-readable format appropriate to the repository.

Persist split assignments so they cannot accidentally change between experiments.

---

# 32. REQUIRED REPORTS

Produce a consolidated report containing:

1. Dataset validation
2. Engine-output validation
3. Patient-level split
4. Text GRU results
5. Voice GRU results
6. Behaviour GRU results
7. Fusion results
8. Ablation results
9. Structured Context ablation
10. Missing-modality tests
11. Discordance tests
12. Court-event tests
13. Delayed deterioration test
14. Recovery test
15. Deterioration-without-event test
16. Trajectory behavior
17. Calibration
18. Class balance
19. Limitations

Clearly separate:

**Synthetic engineering validation**

from:

**Clinical validity**

The synthetic dataset does NOT establish clinical validity.

---

# 33. DATASET LIMITATION

The supplied dataset is synthetic.

It is designed for:
- pipeline development
- architecture validation
- reproducibility
- stress testing
- engineering experimentation

It must NOT be described as:
- clinically validated
- representative of real patients
- a substitute for clinical trial data
- proof of medical performance

---

# 34. NO FABRICATION POLICY

Never fabricate:

- model checkpoints
- Text Engine outputs
- Voice Engine outputs
- Behaviour Engine outputs
- evaluation metrics
- ROC-AUC
- F1
- Brier score
- calibration
- stress-test results
- clinical conclusions

If a dependency is missing, say:

`BLOCKED — <reason>`

and explain exactly what is required.

---

# 35. EXECUTION ORDER

Follow this exact order:

## Phase 1 — Repository audit
Inspect repository and dependencies.

## Phase 2 — Frozen-engine audit
Verify actual Text/Voice/Behaviour APIs and artifacts.

## Phase 3 — Dataset audit
Validate the supplied Latin-only datasets.

## Phase 4 — Engine inference
Run:
1. Text Engine
2. Voice Engine
3. Behaviour Engine

Do not continue a modality if its frozen engine is blocked.

## Phase 5 — Sequence construction
Construct 30-day patient-level sequences.

## Phase 6 — Patient split
Create fixed 70/15/15 patient split.

## Phase 7 — Preprocessing
Fit preprocessing only on training patients.

## Phase 8 — Text GRU
Train and independently evaluate.

## Phase 9 — Voice GRU
Train and independently evaluate.

## Phase 10 — Behaviour GRU
Train and independently evaluate.

## Phase 11 — Fusion
Train gated late fusion.

## Phase 12 — Validation threshold
Choose threshold only on validation data.

## Phase 13 — Final test
Run once on held-out test data.

## Phase 14 — Ablations
Run all required modality and context ablations.

## Phase 15 — Stress tests
Run event/missingness/discordance tests.

## Phase 16 — Trajectory
Evaluate causal trajectory behavior.

## Phase 17 — Calibration
Evaluate final probability calibration.

## Phase 18 — Architecture verification
Confirm there are exactly three risk modalities.

## Phase 19 — Final report
Generate complete reproducible report.

---

# 36. FINAL ARCHITECTURE ASSERTION

Before declaring success, verify programmatically:

```text
Risk modalities = {
    Text,
    Voice,
    Behaviour
}
```

Verify:

```text
Text GRU input = 5
Voice GRU input = 13
Behaviour GRU input = 3
Sequence length = 30
Fusion risk logits = exactly 3
```

Verify:

```text
Structured Context = conditioning only
Structured GRU = absent
Structured risk logit = absent
```

Verify:

```text
Future escalation = separate optional task
Current distress = primary task
```

Verify:

```text
Missing != zero
```

Verify:

```text
patient-level split
```

Verify:

```text
seed = 42
```

Only after every assertion passes may the implementation be declared complete.

---

# 37. WHAT NOT TO DO

DO NOT:

- modify the frozen Text Engine
- modify the frozen Voice Engine
- modify the frozen Behaviour Engine
- use the old Structured Excel as the new training source
- use the old Temporal GRU as a substitute
- create a Structured GRU
- create a fourth fusion modality
- create a structured risk logit
- fabricate missing engine outputs
- zero-fill missing modalities
- use future information
- use future escalation as current distress
- randomly split rows
- tune thresholds on test data
- tune hyperparameters on test data
- report fabricated metrics
- claim clinical validity from synthetic data

---

# 38. IMPORTANT BLOCKING CONDITIONS

STOP and report instead of improvising if:

1. Text checkpoint is missing.
2. Voice audio cannot be created/accessed.
3. Frozen Behaviour Engine cannot be executed.
4. Required dataset columns do not match.
5. Repository APIs conflict with this specification.
6. Patient-level split cannot be enforced.
7. A frozen engine file was modified unexpectedly.
8. A fourth modality appears in the fusion implementation.
9. Future leakage is detected.
10. Missing values are silently converted to valid observations.

---

# 39. FINAL DELIVERABLE

At completion, provide:

1. Exact files created.
2. Exact existing files modified.
3. Exact frozen files verified unchanged.
4. Dataset validation results.
5. Engine inference status.
6. Model checkpoints.
7. Preprocessing artifacts.
8. Split file.
9. Evaluation reports.
10. Ablation results.
11. Stress-test results.
12. Calibration results.
13. Architecture verification results.
14. Any BLOCKED items.

Do not simply say "done."

Provide evidence.

