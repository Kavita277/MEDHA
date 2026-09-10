# MEDHA V2 FINAL SYSTEM FREEZE

## Certification of Freeze

As of **MEDHA V2 Step 16**, the MEDHA V2 architecture is formally **FROZEN**.

The following components are locked and must not be altered:
- **Architectures**: The four Specialist DDS Modalities (Structured, Text, Voice, Behaviour), the XGBoost Fusion Engine, and the Temporal GRU Engine.
- **Model Parameters**: The exact weights, biases, and thresholds trained on the authoritative V2 Split (Train/Val/Test).
- **Feature Contracts**: 8 meta-features for the Fusion Engine (four specialist DDS predictions and four modality-availability flags) and 57 explicitly whitelisted features arranged into 7-timestep historical sequences for the GRU, rigidly preventing Target/Future Leakage.
- **Data Splits**: 700 Train victims, 150 Validation victims, and 150 Test victims. Zero intersection.
- **Triage Thresholds**: The engineering demonstration rules in `engine/v2/priority_triage.py`.

## Canonical Frozen Metrics

The following metrics are the **locked, final empirical results** for the MEDHA V2 System evaluated on the uncompromised Test Split. These supersede any preliminary results generated during the migration.

### 1. Fusion (Current DDS)
- **Empirical Baseline (Train Mean)**: MAE = `10.8196` *(Note: The 12.9648 value is the Scale Midpoint baseline, not the Train Mean)*
- **MEDHA V2 Final Fusion Test MAE**: `5.9537`

### 2. Temporal Risk (Future Escalation)
- **MEDHA V2 Final GRU Test ROC-AUC**: `0.7953`
- **MEDHA V2 Final GRU Test PR-AUC**: `0.3133`
- **Frozen Operating Threshold**: `0.75`

## Verification Summary

An automated Step 16 System Audit (`scratch/audit_step16.py`) confirmed:
1. **Split Consistency**: 700/150/150 victims with strict non-overlap.
2. **Determinism**: Identical inputs yield identical predictions down to `1e-6` floating point tolerance. Maximum absolute difference between runs is exactly `0.0`.
3. **V1 Isolation**: No legacy V1 artifacts or pipelines were modified, overwritten, or deleted during the V2 migration.
4. **Test Pass Rate**: The full V2 test suite executed with **217 passing unit and integration tests** and 0 failures.

## Next Steps
MEDHA V2 is ready for technical demonstration, engineering integration, and domain/clinical expert review. The Priority/Triage layer remains an engineering demonstration and requires clinical validation before real-world clinical deployment. Do not initiate any further model training or hyperparameter tuning.
