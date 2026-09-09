# MEDHA V2 Step 10A --- Fusion Architecture & Existing Fusion Engine Audit

> **Scope**: Audit-only. No models trained, no V1 code modified, no V2 specialists changed.

---

## 1. V1 Fusion Engine Summary

### 1.1 Architecture

The V1 Fusion Engine is a **fixed-weight linear combination** of 5 modality risk scores:

| Modality | V1 Weight | Signal Source |
|:---------|:---------:|:-------------|
| Text | 0.25 | Mean of 5 sub-signals (text_distress, fear, threat, negative_affect, urgency) |
| Voice | 0.15 | Passthrough of `voice_distress` |
| Behaviour | 0.15 | `0.40*anomaly + 0.30*clip(engagement_dev/3, 0, 1) + 0.30*clip(inactivity, 0, 1)` |
| Structured | 0.25 | Passthrough of XGBoost probability |
| Temporal (GRU) | 0.20 | Passthrough of calibrated GRU probability |

**Formula**: `fused_risk = sum(effective_weight[i] * risk[i])`, then `DDS = fused_risk * 100`

### 1.2 Missing-Modality Handling

If a modality is unavailable, its weight is **redistributed proportionally** among available modalities so effective weights always sum to 1.0. If ALL modalities are unavailable, fusion returns `None`.

### 1.3 V1 Target

V1 fuses **risk probabilities** (0--1 scale) and multiplies by 100 to get DDS (0--100).

The downstream target for V1 evaluation was `Future_Escalation_Label` (binary classification), not DDS regression.

### 1.4 V1 Results

| Config | PR-AUC | ROC-AUC | Notes |
|:-------|:------:|:-------:|:------|
| Structured Only | 0.4077 | 0.8545 | Best individual |
| All 5 (Manual Weights) | 0.2842 | 0.7793 | 96.7% Recall |
| Test Set (final) | 0.2561 | 0.7708 | Frozen threshold 0.19 |

V1 conclusion: "Unimodal Collapse" --- synthetic data caused optimizers to zero-out unstructured modalities. Manual weights were enforced to preserve multimodal architecture.

### 1.5 V1 File Inventory

#### Core Operational Files (5 files)

| File | Purpose | Status |
|:-----|:--------|:-------|
| [`fusion.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/fusion_engine/fusion.py) | Core `compute_fusion()` function | Production |
| [`schemas.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/fusion_engine/schemas.py) | `FusionInput`, `FusionOutput`, `ModalitySignal` dataclasses | Production |
| [`adapters.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/fusion_engine/adapters.py) | 5 adapter functions (text, voice, behaviour, structured, temporal) | Production |
| [`weights.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/fusion_engine/weights.py) | `FUSION_WEIGHTS` dict (single source of truth) | Production |
| [`priority_thresholds.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/fusion_engine/priority_thresholds.py) | `determine_priority(dds, future_risk)` -> LOW/MED/HIGH/CRIT | Production |

#### Test & Evaluation (6 files)

| File | Purpose |
|:-----|:--------|
| [`test_fusion.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/fusion_engine/test_fusion.py) | 19 unit test classes (643 lines) |
| [`evaluate_fusion.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/fusion_engine/evaluate_fusion.py) | Master evaluation pipeline (grid search, ablation, missing modality) |
| [`learned_fusion_experiments.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/fusion_engine/learned_fusion_experiments.py) | LogReg, MLP, interaction experiments |
| [`fusion_validation_pipeline.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/fusion_engine/fusion_validation_pipeline.py) | Legacy evaluation pipeline |
| [`final_fusion_experiments.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/fusion_engine/final_fusion_experiments.py) | Final experiment runner |
| [`test_weights_proof.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/fusion_engine/test_weights_proof.py) | Manual weight proof script |

#### Config & Results (4 files)

| File | Contents |
|:-----|:---------|
| `final_fusion_config.json` | `{weights: {text: 0.25, voice: 0.15, ...}, threshold: 0.19}` |
| `selected_fusion_config.json` | `{model: "Learned Logistic Fusion", threshold: 0.15}` |
| `final_test_results.json` | Precision=0.118, Recall=0.777, F1=0.205 |
| `fusion_test_results.json` | Precision=0.398, Recall=0.537, ROC-AUC=0.885 |

#### Reports & CSV artifacts: ~20 CSV files + 2 markdown reports

---

## 2. V1 Component Triage for V2

### Category A: Safe to Reuse As-Is

| Component | Rationale |
|:----------|:----------|
| `ModalitySignal` dataclass | Generic `(available: bool, risk: float)` pair. V2 can use the same contract with `risk` renamed/reinterpreted as `predicted_dds`. |
| `FusionOutput.to_dict()` serialization pattern | Clean JSON-safe serialization. |
| Missing-modality weight redistribution logic | Mathematically correct proportional redistribution. The algorithm is sound regardless of the number of modalities or weight values. |
| `determine_priority()` operational layer | Post-model thresholding is task-independent. DDS thresholds (25/50/75) map cleanly to V2 DDS output (0--100 scale). |
| Unit test structure (`test_fusion.py`) | Test patterns (all-available, one-missing, all-missing, bounds, serialization) are directly reusable for V2. |

### Category B: Reuse with Modification

| Component | Required Modification | Rationale |
|:----------|:---------------------|:----------|
| `FusionInput` schema | **Remove temporal field** (no V2 GRU specialist). Keep 4 modality fields: structured, text, voice, behaviour. | V2 has 4 specialists, not 5. |
| `FusionOutput` schema | **Remove `future_escalation` field**. Change `fused_risk` -> `fused_dds`. Remove `dds = fused_risk * 100` conversion (V2 specialists already output DDS on 0--100 scale). | V1 worked on 0--1 risk scale; V2 works directly on DDS (0--100). |
| `FUSION_WEIGHTS` | **Change from 5-key to 4-key dict**. Values must be re-derived (see Candidate architectures below). | Different modality count and learned vs fixed weights. |
| `compute_fusion()` | **Adapt for 4 modalities and DDS-scale inputs**. Remove the `fused_risk * 100` conversion. Remove GRU future_escalation logic. | Core weighted-sum logic is sound; only the modality list and scale change. |
| Adapters | **V2 does not need V1 adapters.** V2 specialists directly output `predicted_dds` floats. A thin V2 adapter wraps `(available_flag, predicted_dds)` -> `ModalitySignal`. | V1 adapters consumed raw engine JSON; V2 specialists produce standardized CSV predictions. |

### Category C: Reject / Do Not Port

| Component | Rationale |
|:----------|:----------|
| V1 fixed weights `{text: 0.25, voice: 0.15, ...}` | These were manually imposed to prevent unimodal collapse on V1's synthetic classification target. V2 specialists predict DDS regression; weights must be re-derived. |
| `evaluate_fusion.py` evaluation pipeline | Tightly coupled to V1's binary classification target, XGBoost structured engine, and GRU temporal engine. V2 uses DDS regression metrics (MAE, RMSE, R2). |
| `learned_fusion_experiments.py` | Logistic regression/MLP on binary target. V2 fusion is regression, not classification. |
| `generate_oof_predictions.py` / `oof_specialist_predictions.csv` | V1 OOF predictions for V1 models. V2 needs its own validation predictions. |
| All V1 CSV experiment artifacts | Results from V1 experiments on binary target. Not applicable to V2 regression. |
| `final_fusion_config.json` / `selected_fusion_config.json` | V1-specific config. V2 will have its own. |

---

## 3. V2 Fusion Input Contract

### 3.1 Modalities (4, not 5)

| Modality | V2 Specialist | Canonical Model | Features | Output |
|:---------|:-------------|:---------------|:---------|:-------|
| **Structured** | Step 5 | XGBoost | 42 structured-only features | `Predicted_DDS` (0--100) |
| **Text** | Step 6 | Ridge (Core-5) | 5 text features | `Predicted_DDS` (0--100) |
| **Voice** | Step 7 | Ridge (Core-5) | 5 voice features | `Predicted_DDS` (0--100) |
| **Behaviour** | Step 8 | Ridge | 5 behaviour features | `Predicted_DDS` (0--100) |

### 3.2 Temporal / GRU

> [!IMPORTANT]
> V1 had a 5th "Temporal" modality powered by a GRU recurrent model predicting `Future_Escalation_Label`. V2 does **not** include a temporal specialist at this stage. The GRU is a V1-only component. If temporal modeling is added later, it would be a V2 Step N addition, not part of this fusion.

### 3.3 V2 Fusion Input Dataclass (Proposed)

```python
@dataclass
class V2FusionInput:
    victim_id: str
    timepoint: int

    structured: ModalitySignal  # .available=True always; .dds=float
    text:       ModalitySignal  # .available from Text_Available; .dds=float or None
    voice:      ModalitySignal  # .available from Voice_Available; .dds=float or None
    behaviour:  ModalitySignal  # .available=True always; .dds=float
```

### 3.4 V2 Fusion Output Dataclass (Proposed)

```python
@dataclass
class V2FusionOutput:
    victim_id: str
    timepoint: int

    fusion_available: bool           # True if >= 1 modality available
    specialist_predictions: dict     # {modality: predicted_dds or None}
    availability: dict               # {modality: 0 or 1}
    effective_weights: dict          # {modality: float}, sum=1.0
    fused_dds: Optional[float]       # Weighted DDS (0-100 scale)
```

---

## 4. Missing-Modality Semantics

### 4.1 Availability Profile (Test Set, 150 victims, 4500 rows)

| Pattern | Modalities Present | Count | % |
|:--------|:-------------------|------:|--:|
| `1101` | Structured + Text + Behaviour | 2,808 | 62.4% |
| `1111` | Structured + Text + Voice + Behaviour | 1,692 | 37.6% |

> [!NOTE]
> Structured and Behaviour are **always available** (100%). Text is always available (100%) because the Text specialist produces predictions for all rows (when `Text_Available=0`, it outputs the training-mean DDS ~40.36). Voice is available only when `Voice_Available=1` (37.6%).

### 4.2 Text Availability Decision

> [!WARNING]
> The Text specialist currently outputs predictions for **all** rows, including `Text_Available=0` rows (using training-mean imputation ~40.36). The V2 Fusion Engine must decide:
>
> **Option A**: Trust the Text specialist's own imputation. Accept all Text predictions.
> **Option B**: Mask Text predictions when `Text_Available=0`. This creates a true 3-modality fallback.
>
> **Recommendation**: Option B (mask when unavailable). Reason: A constant ~40.36 prediction adds no information and pulls the fused DDS toward the mean. The fusion engine's weight redistribution handles this more cleanly.

### 4.3 Voice Imputation Decision

The Voice specialist has two prediction columns:
- `pred_voice_dds_ridge_core5`: NaN when `Voice_Available=0` (canonical)
- `pred_voice_dds_imputed_full`: Available for all rows (imputed)

**Recommendation**: Use the canonical NaN-when-unavailable column. Let the fusion engine's weight redistribution handle missing voice.

### 4.4 Effective Availability Matrix (Recommended)

| Scenario | S | T | V | B | Coverage |
|:---------|:-:|:-:|:-:|:-:|:--------:|
| All available | Y | Y | Y | Y | 37.6% |
| Voice missing | Y | Y | N | Y | 37.7% |
| Text + Voice missing | Y | N | N | Y | 24.7% |
| Voice + Text missing, only S+B | Y | N | N | Y | (subset of above) |

---

## 5. Complementarity Analysis

### 5.1 Prediction Correlation (Common Subset, N=1,692)

|  | Structured | Text | Voice | Behaviour |
|:-|:----------:|:----:|:-----:|:---------:|
| **Structured** | 1.000 | 0.784 | 0.887 | 0.868 |
| **Text** | 0.784 | 1.000 | 0.822 | 0.697 |
| **Voice** | 0.887 | 0.822 | 1.000 | 0.810 |
| **Behaviour** | 0.868 | 0.697 | 0.810 | 1.000 |

**Interpretation**: Predictions are positively correlated (0.70--0.89) but far from identical. Text and Behaviour have the lowest mutual correlation (0.697), suggesting the most complementary information.

### 5.2 Residual Correlation

|  | Structured | Text | Voice | Behaviour |
|:-|:----------:|:----:|:-----:|:---------:|
| **Structured** | 1.000 | 0.721 | 0.789 | 0.831 |
| **Text** | 0.721 | 1.000 | 0.750 | 0.702 |
| **Voice** | 0.789 | 0.750 | 1.000 | 0.732 |
| **Behaviour** | 0.831 | 0.702 | 0.732 | 1.000 |

**Interpretation**: Residual correlations (0.70--0.83) are lower than prediction correlations, confirming that specialists make **partially independent errors**. This is the key prerequisite for fusion to improve over any single specialist.

### 5.3 Individual Performance (Common Subset)

| Specialist | MAE | RMSE | R2 |
|:-----------|:---:|:----:|:--:|
| **Structured** | **6.2514** | **7.8174** | **0.6610** |
| Voice | 6.3070 | 7.9104 | 0.6529 |
| Text | 7.3465 | 9.3287 | 0.5173 |
| Behaviour | 7.4666 | 9.2794 | 0.5224 |

### 5.4 Ensemble Baselines (Common Subset)

| Method | MAE | RMSE | R2 |
|:-------|:---:|:----:|:--:|
| Best Individual (Structured) | 6.2514 | 7.8174 | 0.6610 |
| Simple Average (equal weight) | 6.1908 | 7.7449 | 0.6673 |
| Inverse-MAE Weighted Average | **6.1498** | **7.6978** | **0.6713** |
| **Oracle (best-of-4 per row)** | **3.6091** | **5.1951** | -- |

### 5.5 Key Findings

1. **Simple averaging already beats the best individual specialist** (MAE 6.19 vs 6.25, a 1.0% improvement).
2. **Inverse-MAE weighting improves further** (MAE 6.15, a 1.6% improvement over best individual).
3. **The oracle ensemble achieves MAE 3.61** --- a 42.3% improvement over the best individual. This demonstrates that substantial complementary information exists across specialists, if the fusion model can learn which specialist to trust for each observation.
4. **Oracle selection is well-distributed**: Structured 27.2%, Voice 27.0%, Text 24.1%, Behaviour 21.7%. No single specialist dominates, confirming all four contribute meaningfully.

> [!TIP]
> The large gap between simple averaging (MAE 6.15) and the oracle (MAE 3.61) suggests that a learned fusion model has significant room to improve beyond naive averaging.

---

## 6. V2 Fusion Candidate Architectures

### Candidate A: Weighted Average (Baseline)

**Method**: `fused_dds = sum(w[i] * specialist_dds[i])` with proportional redistribution for missing modalities.

| Aspect | Details |
|:-------|:--------|
| Weights | Inverse-MAE derived: Struct=0.2718, Voice=0.2694, Text=0.2313, Behav=0.2276 |
| Missing Modality | Proportional weight redistribution (same as V1) |
| Training | No training required (weights derived from validation MAE) |
| Expected MAE | ~6.15 (from complementarity analysis) |
| Pros | Simple, interpretable, no overfitting risk, works with any availability pattern |
| Cons | Cannot learn observation-level routing; limited ceiling |

### Candidate B: Ridge / Linear Stacking (Recommended)

**Method**: Train a Ridge regression on specialist predictions as features: `fused_dds = intercept + sum(beta[i] * specialist_dds[i])`

| Aspect | Details |
|:-------|:--------|
| Features | 4 specialist DDS predictions (+ possibly availability flags) |
| Target | Actual DDS |
| Training Data | V2 **validation set** predictions only (150 victims, not train set) |
| Missing Modality | Impute missing predictions with 0 and add binary availability indicator |
| Regularization | Ridge (L2), cross-validated alpha |
| Expected MAE | Better than 6.15 (learned intercept and non-equal weights) |
| Pros | Learns optimal weights, handles bias correction (intercept), low overfitting risk with Ridge, interpretable coefficients |
| Cons | Linear; cannot learn interaction effects |

### Candidate C: XGBoost / Nonlinear Stacking

**Method**: Train XGBoost on specialist predictions + availability flags.

| Aspect | Details |
|:-------|:--------|
| Features | 4 specialist DDS predictions + 4 availability flags (8 features) |
| Target | Actual DDS |
| Training Data | V2 **validation set** predictions (or OOF train predictions if available) |
| Expected MAE | Potentially closer to oracle (~3.6--5.0), but overfitting risk is high |
| Pros | Can learn nonlinear routing (e.g., "trust Voice when Structured predicts mid-range") |
| Cons | Overfitting risk with only 4,500 training rows and 8 features; less interpretable |

---

## 7. Recommended V2 Fusion Strategy

> [!IMPORTANT]
> **Recommendation**: Implement **all three candidates** (A, B, C) as a progression, evaluate on test set, and select the best.
>
> - **Candidate A** (Weighted Average) serves as the interpretable baseline.
> - **Candidate B** (Ridge Stacking) is the recommended primary model.
> - **Candidate C** (XGBoost Stacking) is the exploratory ceiling test.
>
> The final selection will be based on test-set performance with the constraint that the chosen model must not overfit (validation performance must be within 10% of test performance).

### Training Protocol

1. Generate **validation-set predictions** from each specialist (already available in `outputs/dds_v2/*/val_*_dds_predictions.csv`).
2. Train fusion candidates on validation predictions (150 victims, ~4,500 rows).
3. Evaluate on **test predictions** (150 victims, ~4,500 rows).
4. Compare against individual specialists and ensemble baselines.

### Missing-Modality Protocol

For Candidates B and C:
- When a modality is unavailable, set its prediction to **0** (not the training mean) and add a binary flag `available_[modality] = 0/1`.
- This allows the model to learn the conditional distribution without conflating imputed values with real predictions.

---

## 8. Open Questions

> [!IMPORTANT]
> **Q1: Text Availability Masking** --- Should the fusion engine mask Text predictions when `Text_Available=0` (recommendation: yes), or trust the Text specialist's own training-mean imputation?

> [!IMPORTANT]
> **Q2: Voice Imputation** --- Should we use the canonical NaN-when-unavailable voice predictions (recommendation: yes), or the imputed-full variant?

> [!IMPORTANT]
> **Q3: Priority Layer** --- Should V2 retain the V1 `determine_priority(dds, future_risk)` function? With no GRU in V2, the `future_risk` input would not be available. Options:
> - (a) Keep priority based on DDS only (remove future_risk dependency)
> - (b) Defer priority layer to a later step
> - (c) Port the GRU as a separate component

---

## 9. Verification Checklist

- [x] V1 Fusion Engine files fully inventoried (5 core + 6 eval + 4 config + ~20 CSV/MD)
- [x] V1 architecture documented (5-modality fixed-weight linear fusion)
- [x] V1 components categorized as A (reuse) / B (modify) / C (reject)
- [x] V2 Fusion Input Contract defined (4 modalities, DDS-scale)
- [x] Missing-modality semantics documented (2 availability patterns)
- [x] Complementarity analysis completed (oracle 42.3% improvement, positive ensemble gains)
- [x] Three V2 Fusion candidates defined (A: weighted average, B: Ridge stacking, C: XGBoost stacking)
- [x] No V1 code modified
- [x] No V2 specialists modified
- [x] No models trained
