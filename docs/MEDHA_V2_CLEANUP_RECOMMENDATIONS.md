# MEDHA V2 Cleanup Recommendations

During the transition from V1 to V2, several intermediary, test, and prototype scripts were generated. 
To maintain a pristine repository while preserving reproducibility, we classify these files as follows.
**No files have been deleted during the audit.**

## 1. KEEP — Required (Production Integration)
These files are the final V2 pipeline and must remain completely untouched:
- `engine/v2/medha_v2_pipeline.py`
- `engine/v2/priority_triage.py`
- `engine/v2/v2_feature_policy.py`
- `engine/models/v2/` (and subdirectories containing the SHA-256 frozen artifacts)
- `engine/tests/` (All test files starting with `test_v2_`)

## 2. KEEP — Historical / Reference
These files represent the final experiments and evaluations that validated V2. They should be kept for methodology review:
- `engine/v2/train_v2_structured_dds.py`
- `engine/v2/train_v2_text_dds.py`
- `engine/v2/train_v2_voice_dds.py`
- `engine/v2/train_v2_behaviour_dds.py`
- `engine/v2/train_v2_fusion_oof.py`
- `engine/v2/evaluate_v2_fusion_final.py`
- `engine/v2/train_v2_gru.py`
- `engine/v2/run_v2_ablation.py`
- All markdown reports in `docs/` starting with `MEDHA_V2_STEP`

## 3. KEEP — Experiment / Sandbox
These files were used to extract baseline values, prototype pipelines, or check preliminary metrics. They are technically obsolete but contain useful context.
- `engine/fusion_engine/final_fusion_experiments.py`
- `engine/fusion_engine/priority_thresholds.py` (V1 prototype)
- `engine/v2/v2_fusion.py` (Preliminary Step 10A script)

## 4. ARCHIVE — Obsolete but Useful
- Legacy V1 Engine files in `engine/legacy_v1/`. They are untouched and safely segregated, but represent the old architecture. They should be archived when V2 goes live.

## 5. SAFE TO DELETE — Temporary/Debug Only
These files were created strictly for ad-hoc debugging and integration testing during the V2 development process.
- `scratch/compare_pipeline_specialists.py`
- `scratch/run_step15_e2e.py`
- `scratch/audit_step16.py`

**Action:** Review the `SAFE TO DELETE` and `ARCHIVE` categories with the engineering team before executing `rm`.
