# MEDHA V2 STEP 3 — SPLIT REPORT

## 1. Split Methodology

- **Grouping key**: `Victim_ID` (victim-level split — no victim appears in multiple splits)
- **Method**: Deterministic shuffle of unique Victim_IDs followed by sequential assignment
- **Proportions**: 70% Train / 15% Validation / 15% Test
- **Random seed**: 42
- **Library**: `numpy.random.RandomState(42).shuffle()`

## 2. Victim Counts

| Split | Victims | Expected |
|---|---|---|
| Train | 700 | 700 |
| Validation | 150 | 150 |
| Test | 150 | 150 |
| **Total** | **1000** | **1000** |

## 3. Row Counts

| Split | Rows | Expected |
|---|---|---|
| Train | 21,000 | 21,000 (700 x 30) |
| Validation | 4,500 | 4,500 (150 x 30) |
| Test | 4,500 | 4,500 (150 x 30) |
| **Total** | **30,000** | **30,000** |

## 4. DDS Distribution by Split

| Split | Mean | Std | Min | Max | Median |
|---|---|---|---|---|---|
| Train | 39.70 | 13.07 | 0.00 | 81.67 | 39.81 |
| Validation | 40.73 | 12.77 | 1.66 | 76.91 | 41.00 |
| Test | 40.53 | 13.14 | 0.00 | 84.66 | 40.98 |

DDS distributions are well-balanced across all three splits. Mean differences < 1.1 points.

## 5. Future Escalation Distribution by Split

| Split | Positive | Negative | NaN | Total Valid | Positive % |
|---|---|---|---|---|---|
| Train | 1,070 | 15,030 | 4,900 | 16,100 | 6.65% |
| Validation | 262 | 3,188 | 1,050 | 3,450 | 7.59% |
| Test | 279 | 3,171 | 1,050 | 3,450 | 8.09% |

NaN values are at timepoints 24-30 (by design: 7-step lookahead unavailable at end). Positive rates are reasonably balanced (6.65%-8.09%).

## 6. Trajectory Distribution by Split

| Trajectory Type | Train | Validation | Test | Total |
|---|---|---|---|---|
| stable | 139 | 33 | 26 | 198 |
| gradual_deterioration | 117 | 31 | 30 | 178 |
| gradual_recovery | 101 | 21 | 26 | 148 |
| fluctuating | 84 | 28 | 16 | 128 |
| event_triggered_deterioration | 83 | 12 | 15 | 110 |
| resilient | 71 | 6 | 8 | 85 |
| event_triggered_recovery | 52 | 10 | 15 | 77 |
| rapid_deterioration | 53 | 9 | 14 | 76 |

No manual rebalancing was applied. The distribution is a natural result of the random shuffle.

## 7. Leakage Verification

All checks PASSED:

- Train victim set has **zero intersection** with Validation victim set
- Train victim set has **zero intersection** with Test victim set
- Validation victim set has **zero intersection** with Test victim set
- Union of all three sets = 1000 (all victims covered)

## 8. Temporal Integrity Verification

All checks PASSED:

- All 1000 victims have exactly 30 rows
- All 1000 victims have timepoints 1 through 30
- All 1000 victims have a single consistent Split value across all their rows
- Longitudinal split file assignments match victim split file exactly

## 9. Files Created

| File | Purpose |
|---|---|
| `engine/data/processed/v2_victim_split.csv` | 1000-row authoritative victim-level split (Victim_ID, Split) |
| `engine/data/processed/v2_longitudinal_split.csv` | 30,000-row dataset with Split column appended |
| `engine/data/processed/v2_split_config.json` | Metadata: seed, counts, paths, timestamp |
| `engine/create_v2_split.py` | Split generation script with built-in verification |
| `engine/validate_v2_split.py` | Independent validation script (18 checks) |
| `docs/MEDHA_V2_STEP3_SPLIT_REPORT.md` | This report |

## 10. V1 Files Deliberately Left Untouched

| File | Status |
|---|---|
| `engine/data/processed/victim_split.csv` | **NOT modified** — belongs to V1 workflow |
| `engine/evaluate_medha_pipeline.py` | **NOT modified** — V1 orchestrator |
| `engine/Structured_risk_enigne/` | **NOT modified** — V1 models and artifacts |
| `engine/fusion_engine/` | **NOT modified** — V1 fusion logic |
| `engine/gru-temporal-risk/` | **NOT modified** — V1 GRU models |
| `engine/MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx` | **NOT modified** — source dataset |

## 11. Scripts and Commands Used

```bash
# Generate split
python engine/create_v2_split.py

# Independent validation
python engine/validate_v2_split.py
```

Both scripts exited with code 0 (success).

## 12. Final Status

| Check | Result |
|---|---|
| Victim uniqueness | PASS |
| Split counts (700/150/150) | PASS |
| Row counts (21000/4500/4500) | PASS |
| No victim overlap | PASS |
| 30 timepoints per victim | PASS |
| Single split per victim | PASS |
| Longitudinal matches victim split | PASS |
| DDS distribution balanced | PASS |
| Source dataset unmodified | PASS |
| V1 files untouched | PASS |

**OVERALL: ALL CHECKS PASSED**

## 13. V2 Split Authority

For all future V2 work:

- **Authoritative split file**: `engine/data/processed/v2_victim_split.csv`
- **Row-level dataset**: `engine/data/processed/v2_longitudinal_split.csv`
- **Config**: `engine/data/processed/v2_split_config.json`

The old V1 split file (`engine/data/processed/victim_split.csv`) must NOT be used for V2 experiments.
