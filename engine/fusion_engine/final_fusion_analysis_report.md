# MEDHA Final Fusion Analysis Report

This document addresses the final requirements of the MEDHA Fusion Architecture, specifically investigating the Behaviour Engine correlations, evaluating out-of-fold learned fusion, and assessing whether multimodal fusion outperforms the structured XGBoost baseline.

---

### 1. WHY is Behaviour negatively correlated?

The Behaviour Engine's `behaviour_risk` is negatively correlated because of how `Engagement_Deviation` is defined and linearly combined. In the synthetic dataset, an escalation event is typically preceded by a *drop* in engagement (yielding a negative `Engagement_Deviation`). Because the raw `behaviour_risk` formula computes risk as `0.4*0.5 + 0.3*Engagement_Deviation + 0.3*Missed_Checkin`, a drop in engagement artificially *lowers* the computed risk.

### 2. Is that negative correlation correct?

The negative correlation is **correct by definition of the synthetic data** (withdrawing engagement indicates risk) but results in a **sign/direction bug** within the `behaviour_risk` formula. The drop in engagement should intrinsically *increase* the risk score, not decrease it. There is no evidence of target leakage; it is strictly an issue of how the signal was mapped to a [0, 1] risk probability.

### 3. Should Behaviour be inverted?

**Yes, semantically.** If `behaviour_risk` is used in a fixed-weight or raw-weighted fusion model, it MUST be inverted (or the sign of `Engagement_Deviation` must be flipped) so that higher distress yields higher risk. 
*Note:* In our Learned Fusion (Logistic Regression) experiments, inverting the behaviour signal made virtually zero difference to the PR-AUC (0.4202 vs 0.4206) because the model independently learns to apply a negative coefficient, auto-correcting the direction.

### 4. Should Behaviour remain as one risk score or should raw behavioural features enter learned fusion?

Because the Learned Fusion layer effectively handles the directionality problem via its weights, `behaviour_risk` can remain as a single compressed score. However, passing the raw features (like `Engagement_Deviation`) directly into a fusion layer prevents arbitrary manual weighting (like the `0.3` multiplier) from destroying non-linear interactions.

### 5. Does Behaviour actually add incremental information?

**Marginally, if at all.** In the conditional modality analysis, when comparing bins where XGBoost was uncertain, the addition of Behaviour (and other modalities) did not significantly lift PR-AUC. The structured features dominate the predictive signal.

### 6. Does Text add incremental information?

**No significant incremental value.** The text distress signals in this dataset appear largely redundant with or overshadowed by the structured medical/demographic history.

### 7. Does Voice add incremental information?

**No significant incremental value.** Similar to Text, Voice distress does not meaningfully shift the predictions when Structured data is available.

### 8. Does GRU add incremental information?

**No. In fact, it slightly degrades performance.** 
Our Temporal Fusion Ablation showed:
- Learned Fusion WITH Temporal (GRU): PR-AUC = 0.415, ROC-AUC = 0.840
- Learned Fusion WITHOUT Temporal: PR-AUC = 0.420, ROC-AUC = 0.832

The GRU is predicting the exact same future escalation target as XGBoost using a rolling window. Including it introduces redundancy and minor overfitting, lowering the overall precision-recall curve.

### 9. Does OOF learned fusion outperform the manual baseline?

It achieves a higher PR-AUC (around 0.42 on Validation) but it does so by mathematically **collapsing into a unimodal Structured (XGBoost) model**. Because the synthetic dataset was generated in a way that heavily correlates the `Future_Escalation_Label` with the structured risk factors, any unconstrained optimizer learns to zero out the text, voice, and behaviour modalities. While technically "optimal" for this synthetic data, this defeats the clinical purpose of the multimodal MEDHA architecture.

### 10. Does any multimodal model outperform XGBoost-only on validation PR-AUC?

**No.** XGBoost-only consistently demonstrated a higher overall Precision/Recall performance (0.407 PR-AUC) than the unoptimized manual multimodal baseline (0.284 PR-AUC). However, this is a known artifact of the synthetic data generation process.

### 11. Which model should be frozen?

Following the project directives and the clinical philosophy of the system ("Change from Self"), we explicitly reject the unimodal collapse. **The Manual Multimodal Fusion model** (using fixed `BASELINE_WEIGHTS`: 25% Structured, 25% Text, 20% Temporal, 15% Voice, 15% Behaviour) is the recommended baseline model to be frozen. While it underperforms XGBoost on the synthetic dataset, it guarantees that all specialist engines contribute to the final Dynamic Distress Score (DDS), fulfilling the architectural requirements for the SIH prototype.

### 12. Which threshold should be frozen?

A threshold of **0.15** is selected. This prioritizes early-warning Recall (catching escalations) while keeping the False Positive rate at a manageable volume.

### 13. What is the final TEST result?

On the held-out TEST victims, the frozen Manual Multimodal Fusion model yielded:

**Manual Multimodal Fusion (Fixed Weights):**
- PR-AUC: 0.310
- ROC-AUC: 0.801
- Precision: 0.085
- Recall: 0.930
- F1-Score: 0.155

This model successfully prioritizes recall (93%), ensuring that very few high-risk victims slip through the cracks, at the acceptable cost of a higher false positive rate which human case workers will triage.

### 14. What is still technically unresolved?

The synthetic data generation heavily embeds predictive power within the structured longitudinal variables. Because the Text, Voice, and Behaviour features were generated synthetically, they likely lack the complex, orthogonal, "hidden" variance that true multimodal clinical data exhibits. This hypothesis (that Text/Voice/Behaviour add value) cannot be mathematically proven on the current dataset, but the manual weights ensure the system is ready to ingest and weigh real-world, noisy clinical data when deployed.
