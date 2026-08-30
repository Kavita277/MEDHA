# MEDHA Behaviour Engine — Complete Session Summary

**Scope:** everything designed, built, tested, and decided in this session, in
order. Supersedes the earlier interim status report — this is the complete
version, including the Questionnaire Engine integration work that came after it.
All numbers below were actually computed and verified in this session, not
projected.

---

## 1. What this session covered

1. Finished the synthetic Behaviour Engine dataset (trajectory labels, latent
   state, case-aware features) on top of an existing partial baseline.
2. Trained and evaluated an Isolation Forest anomaly model — twice, because
   the first pass had real bugs.
3. Defined and validated 3 output scores (anomaly, engagement deviation,
   inactivity).
4. Designed the real-time scoring pipeline architecture and built a tested
   FastAPI serving layer for it.
5. Designed (not built) the evaluation methodology for a future GRU + gated
   late fusion model.
6. Worked through the raw-event contract with the Questionnaire Engine team —
   confirmed field mappings, found one hard gap, resolved three ambiguities.

---

## 2. Synthetic dataset

**File:** `MEDHA_Behaviour_Engine_FINAL_1000_Candidates_30_Days.csv` — 30,000
rows (1,000 candidates × 30 days), 38 columns.

Started from an existing baseline (23 core Behaviour Engine features +
`future_deterioration_7d` target, already generated). Added on top of it,
without altering the original behavioural values except one fix:

- **Data-quality bug found and fixed:** 669 rows had `completion_baseline_z`
  at exactly ±1,000,000 — an epsilon-division artifact from the personal
  baseline formula blowing up when early-history variance is near zero.
  Winsorized 6 affected z-score/slope columns at their own data-driven
  0.5th/99.5th percentile.
- **`patient_trajectory_type`** (8-class simulation label) — reconstructed
  from the actual 30-day behavioural sequences (trend, volatility,
  level-shift, change-point per candidate) rather than assigned arbitrarily,
  so labels are internally consistent with the data they describe. All 8
  classes represented (60–320 candidates each). Simulation metadata only —
  never a model input.
- **`latent_behaviour_state`** (0/1/2, simulation-only) — derived per day
  from a disruption composite of existing z-scores + persistence. Distribution:
  69.4% stable, 24.9% mild, 5.8% sustained.
- **9 case-aware features** — `case_stage`, `case_event_today`, severity,
  recency, rolling counts, `case_change_score`, `protective_support_level`,
  `case_stability_index`. Event timing deliberately coupled to trajectory
  class (e.g. `event_triggered_deterioration` candidates get a primary case
  event placed 0–3 days before their detected behavioural change-point).

Full methodology, formulas, and a spec-mandated validation checklist:
`DATA_CARD.md` (delivered earlier, still valid).

---

## 3. Anomaly detection model

**Two distinct iterations exist across this session — do not conflate them.**

### 3a. Exploratory iteration (superseded)
23 features, `contamination='auto'`, fit on all training candidates' full
history. Used to validate the synthetic dataset itself and produce the first
version of the 3 scores. ROC-AUC 0.809 (strict) / 0.706 (loose). **Not the
currently deployed model.** Its output files (`MEDHA_Behaviour_Engine_Scores.csv`,
`MEDHA_Behaviour_Engine_FINAL_with_scores.csv`) are kept for audit trail only.

### 3b. Canonical iteration — currently frozen and deployed
- **Features (3):** `completion_baseline_z`, `latency_baseline_z`,
  `question_skip_rate` — reduced from 23 to the minimal spec-clean set fast
  enough for real-time single-row scoring.
- **Fit population:** each training candidate's own days 1–10, restricted to
  `missed_checkins == 0` — a baseline-stabilization window before scoring
  activates (matches Master Doc §18.2 directly).
- **Algorithm:** `IsolationForest(n_estimators=200, contamination=0.05,
  random_state=42)`, `StandardScaler` + `SimpleImputer(median)`, both fit on
  the training baseline window only.
- **Split:** candidate-level 70/30, disjoint `user_id`s.
- **Anomaly scaling fix:** raw decision-function output is percentile-ranked
  against a **frozen training reference distribution**, not batch min-max —
  this is what makes single-patient real-time scoring work at all (a lone row
  scored alone no longer collapses to 0.0 by construction, which is what the
  original batch min-max design did).
- **Persisted as:** `medha_scoring_artifacts.joblib` (imputer + scaler +
  forest + reference distribution, load-once).

---

## 4. Bugs found and fixed in the original draft pipeline

All six were real, verified bugs — not style preferences:

1. **Cross-candidate score leakage.** `.ffill()` with no `.groupby('user_id')`
   pulled a *different* candidate's last score forward into another patient's
   early days, because day-1 rows routinely fail the "all features present"
   mask. Fixed by per-row imputation instead of forward-fill, plus an explicit
   `insufficient_history` flag rather than silently defaulting to a number.
2. **Batch-dependent normalization.** `(v - min) / (max - min)` computed
   against whatever else was in the current scoring batch. For a single
   real-time patient, `min == max`, so every solo score became exactly 0.0
   regardless of actual anomalousness. Fixed via the frozen reference
   distribution in §3b.
3. **Redundant feature.** `missed_checkins` was in the feature set but held
   constant (always 0) by the active-day scoring filter — contributed
   nothing. Removed; `inactivity_score` is the dedicated feature for that
   signal instead.
4. **NaN dilution.** `engagement_deviation` filled missing z-columns with 0
   *before* averaging, artificially shrinking deviation exactly when data was
   most missing. Fixed to average only observed columns.
5. **Incomplete evaluation coverage.** The original evaluation silently
   excluded any row with `missed_checkins != 0` — 45% of the test set,
   including exactly the population a triage system most needs to catch.
   Fixed to evaluate 100% of test rows.
6. **Hardcoded stress tests.** `engagement_deviation` values in the stress
   tests were typed in by hand, not computed — a passing test proved little
   about the actual scoring function. Fixed by routing stress tests through
   the same `score_dataframe()` function as real data.

---

## 5. The 3 output scores — current (canonical) formulas

| Score | Formula | Range |
|---|---|---|
| `anomaly_score` | Percentile rank of `-IsolationForest.decision_function()` vs. frozen training reference | 0–1 |
| `engagement_deviation` | Mean of `\|z\|` over whichever of 4 baseline-z columns are observed that day | 0–∞ (typically 0–6) |
| `inactivity_score` | 3-day rolling mean of `missed_checkins`, per candidate | 0–1 |
| `behavioral_risk_score` | `0.4·anomaly_score + 0.3·clip(engagement_deviation/3, 0, 1) + 0.3·inactivity_score` | 0–1 |
| `triage_status` | GREEN <0.25 / YELLOW <0.50 / ORANGE <0.75 / RED ≥0.75 / **GRAY — Insufficient History** when no pure feature exists that day | categorical |

`GRAY` is a deliberate 5th state — a day with genuinely no data never
silently presents as "low risk."

**Validated against hidden ground truth** (`latent_behaviour_state`, never a
model input): mean `anomaly_score` rose monotonically 43.4 → 61.6 → 80.4
across states 0→1→2; `engagement_deviation` moved the expected direction
(+0.22 → −0.88 → −1.92). `inactivity_score` rose 0→1 but plateaued into
state 2 — stated honestly at the time: sustained disruption doesn't always
mean full non-participation, and the scores shouldn't be assumed redundant
with each other.

---

## 6. Evaluation metrics — canonical model, full test population

Candidate-level 70/30 split, **100% of test rows evaluated (9,000/9,000)** —
this is the corrected figure; an earlier draft only covered 4,945/9,000
because it excluded every missed check-in.

| Metric | Strict (state=2, sustained disruption) | Loose (state≥1, any disruption) |
|---|---|---|
| ROC-AUC | 0.903 | 0.880 |
| PR-AUC | 0.308 | 0.748 |
| Precision @ 0.50 threshold | 0.122 | 0.584 |
| Recall @ 0.50 threshold | 0.979 | 0.870 |
| F1 | 0.217 | 0.699 |
| Confusion matrix (TN, FP / FN, TP) | 4871, 3615 / 11, 503 | 4523, 1713 / 359, 2405 |

**Honest read:** recall is very high at the 0.50 (ORANGE+) threshold —
consistent with Master Doc §41's explicit priority that false negatives cost
far more than false positives — but precision of 0.122 means roughly 8 in 9
ORANGE+ flags will be false alarms at this threshold. That trade-off is real
and should be presented as-is, not smoothed over. Threshold has not yet been
tuned against an explicit alert-budget constraint (see Limitations).

**Stress tests** (computed through the real scoring function end-to-end):
chaotic synthetic input → risk 0.70, ORANGE, passed. Zero-deviation "perfect"
synthetic patient → risk 0.016, GREEN, passed.

---

## 7. Real-time serving layer

**Pipeline architecture (6 stages):** patient check-in (app event) → event &
feature store (per-patient rolling history) → feature engineering (23/3
features, causal only) → frozen model scoring → trend & threshold check →
therapist review (human-in-the-loop, never automated).

**Built and tested:** `medha_scoring_api.py`, a FastAPI service that loads
the frozen artifacts once at startup and exposes:
- `POST /v1/patients/{id}/score` — accepts today's raw features, returns all
  5 fields from §5 plus `gru_sequence` (last 30 days of `[anomaly,
  engagement, inactivity]`) and `gru_sequence_mask` (real observation vs.
  insufficient-history placeholder, per day).
- `GET /v1/patients/{id}/sequence`, `GET /health`.

**Verified with `TestClient`, not just written:**
- Day 1 (full features): `anomaly_score = 0.7936` — matches the standalone
  single-row demo from the training script exactly, confirming API and batch
  pipeline compute identically.
- Day 2 (no features sent): correctly returned `insufficient_history=True`,
  all scores `None`, `GRAY` — not a fabricated 0.0.
- Day 3 (deliberately chaotic input): `anomaly_score=1.0`, `risk=0.8`, `RED`.
- Sequence mask after 3 calls: `[True, False, True]` — exactly right.

**Known limitation:** per-patient history is an in-memory Python `dict`. Fine
for a single-process demo; does not survive a restart and breaks under
multiple worker processes (each gets its own separate dict). Needs Redis or
a `patient_id`-keyed DB table before any durable/multi-worker deployment — no
other scoring logic needs to change when that happens.

---

## 8. GRU + gated late fusion — methodology only, nothing built

An evaluation framework was designed for when this gets built, not the model
itself:

- **Metrics anchored to Master Doc §41's priority** (false negatives cost
  more than false positives): recall at a fixed alert budget or F2-score as
  primary, not accuracy or plain F1; calibration (Brier score, reliability
  diagram) since threshold-based alerting needs real probabilities, not just
  ranking.
- **Splitting:** the same candidate-level split must be used for the upstream
  unsupervised scorer *and* the downstream fusion model, or the unsupervised
  model's exposure to "test" candidates during its own fitting leaks into
  the fusion evaluation. Temporal split also recommended (train on an earlier
  cohort, test on a later one) to simulate real deployment drift.
- **Ablations required to justify the architecture:** behaviour-only vs. full
  fusion; static aggregate vs. GRU sequence; gated fusion vs. simple
  concatenation; and the full staged-baseline comparison from §40.1
  (rule-based → logistic regression → XGBoost → GRU+fusion) on the same
  split, since a more complex model needs to *earn* its complexity.
- **Diagnostics specific to gating:** gate-collapse check (is one modality's
  weight stuck near 0 or 1 for everyone?), shuffled-order sanity check (does
  performance drop when day-order is scrambled — proves the GRU is using
  real temporal structure, not just averaging), lead-time metric (days
  between threshold-crossing and the actual labeled deterioration onset —
  directly tied to the problem statement's "predict escalation before a
  crisis" framing).

**Architecture-spec tension, flagged and still unresolved:** Master Doc
§22.2 and §40.1 explicitly choose feature-level fusion over an end-to-end
deep model for the hackathon prototype, specifically for explainability and
because there isn't enough labelled in-domain data yet — and explicitly scope
something like a GRU + gated fusion as future/production work. Building it
anyway isn't wrong, but it's a deliberate deviation from the team's own spec
that should be defensible to judges (§46), not accidental.

---

## 9. Questionnaire Engine integration — raw event contract

Reviewed 16 proposed raw fields against the 6 real-time inputs the Behaviour
Engine needs. **12 usable directly.** One hard gap, three resolved
clarifications:

### Hard gap
**`response_text_length` (or raw answer text) is not in the proposed field
list, and nothing else in it can substitute.** Without it,
`response_length_baseline_z` cannot be computed at all — this needs to be
added, either as a computed length per answered question or as raw text
(in which case length is computed on the Behaviour Engine side and text is
never stored there).

### Resolved: `session_status` only has completed/abandoned, no scheduler exists
Conclusion: **completed/abandoned is sufficient for most features** — timing,
skip rate, response length, session duration, abandonment rate, edit rate,
and the gap-since-last-session all only ever look at sessions that were
actually opened. The real dependency traces to one shared quantity,
**"expected check-ins,"** not to a missing session status:
`missed_checkins`, `checkin_completion_rate`, `completion_baseline_z`, and
**`inactivity_score`** (already 30% of the deployed composite score) all need
to know how many check-ins were scheduled, independent of whether a session
was ever created.

Two ways to close this gap were offered, **neither requiring a notification
scheduler:**
- **Option A:** expose each patient's enrollment/start date. Under the
  project's assumed fixed 1-check-in/day cadence, "expected" for any day
  becomes a simple derived fact — no new session status, no new event type.
- **Option B:** redefine those features to be gap-based instead of
  count-based, using only `session_start_time`/`session_end_time` already
  being sent — "is the gap since this patient's last session unusually long
  relative to their own typical gap" instead of a hard completion count.
  Needs zero new fields from the Questionnaire Engine.

If neither is available: `missed_checkins`, `checkin_completion_rate`,
`completion_baseline_z`, and `inactivity_score` become genuinely unavailable
(not degraded), and the deployed composite formula needs deliberate
reweighting to drop `inactivity_score`'s 0.3 share — never let it silently
default to 0 (= "no risk").

### Resolved: `patient_id` as `user_id`
Confirmed usable, **conditional on the ID being stable for the life of the
patient's enrollment.** Every baseline z-score, slope, and persistence
feature depends on an unbroken per-ID history; a rotated/reissued ID makes
that patient look like a brand-new cold-start patient, silently discarding
their real history.

### Resolved: `session_start_time` as questionnaire opening time
Confirmed usable, **conditional on no intermediate screen** (landing page,
consent, intro card) between notification tap and `session_start_time`. If
such a screen exists, `session_start_time` measures a later moment than true
"opened," which would systematically undercount latency. Lower-stakes than
it first appears, though: the baseline-z math is self-referential (compares
a patient to their own prior history using whatever moment is measured), so
it tolerates *which* definition is used — what it does not tolerate is that
definition changing mid-study for an existing patient, which would look like
a real behavioural shift to the model when it's actually an instrumentation
change.

---

## 10. Limitations — consolidated

- **Everything is synthetic.** No real patient data has been used or
  validated against anywhere in this pipeline. All numbers describe how well
  the pipeline recovers a *designed* synthetic signal, not real-world
  clinical performance — this must be stated in any judge-facing material.
- **Two non-comparable model iterations exist** (§3a vs. §3b) — don't quote
  both ROC-AUC figures as if describing the same model.
- **`contamination=0.05` is a default assumption**, not yet tuned against an
  explicit alerts-per-patient-per-week budget.
- **No calibration analysis has been run** on the current Isolation Forest
  scores (Brier score / reliability diagram) — needed before any threshold is
  presented as operationally meaningful rather than just well-ranked.
- **In-memory state store** in the FastAPI service — not durable, not
  multi-worker safe.
- **No authentication/access control** on the API at all.
- **No model versioning scheme** — artifacts are saved but untagged; once
  retraining starts, there's no way yet to track which reference distribution
  a historical score was computed against.
- **The upstream feature-engineering service (raw events → the 6 real-time
  inputs) has not been built** — every layer in this session has assumed it
  as already-done input. This is the single largest remaining piece of work.
- **`response_length_baseline_z` is currently uncomputable** pending the
  Questionnaire Engine gap above.
- **"Expected check-ins" is currently uncomputable** pending confirmation of
  an enrollment-date source or adoption of the gap-based redefinition.

---

## 11. Gaps for next session, priority order

1. Close the two open Questionnaire Engine gaps (`response_text_length`;
   an "expected check-ins" source) once their team responds.
2. Build the upstream feature-engineering service — owns the raw per-patient
   event log, computes the 6 real-time inputs via the personal-baseline-z
   formula, calls the scoring API.
3. Replace the FastAPI service's in-memory store with Redis/DB.
4. Run calibration analysis on the current model; tune `contamination`
   against an explicit alert-budget.
5. Build NLP and voice modality services (Master Doc §20–21) — not started.
6. Build the GRU + gated fusion model itself, using the evaluation
   methodology in §8 — currently only designed, not implemented.
7. Build the fusion orchestrator service tying behaviour + NLP + voice → GRU.
8. Add model versioning and API authentication before any deployment beyond
   local demo.
9. Real-data validation once real MEDHA data exists — required before any
   number in this document is used as a clinical claim.

---

## 12. File inventory

**Canonical / currently deployed:**
`medha_scoring_pipeline_corrected.py`, `medha_scoring_artifacts.joblib`,
`medha_scoring_api.py`, `MEDHA_scored_test_set.csv`, `gru_behavioral_tensor.npy`

**Dataset & documentation:**
`MEDHA_Behaviour_Engine_FINAL_1000_Candidates_30_Days.csv`,
`MEDHA_Behaviour_Engine_Feature_Dictionary_FINAL.csv`, `DATA_CARD.md`

**Superseded (kept for audit trail only, not canonical):**
`MEDHA_Behaviour_Engine_Scores.csv`, `MEDHA_Behaviour_Engine_FINAL_with_scores.csv`
— used the exploratory 23-feature model and an earlier scoring formula, both
replaced by §3b–5 above.
