"""
MEDHA V2 — validate_v2_split.py

Independent validation of the V2 victim-level data split.

Loads the source dataset and the saved split files, then verifies:
1. Victim uniqueness in split file
2. Split counts (700/150/150)
3. Row counts (21000/4500/4500)
4. No victim overlap between splits
5. 30 timepoints per victim
6. All timepoints of each victim have the same split
7. Row-level split dataset matches the victim split
8. Prints PASS/FAIL

Exits with non-zero status on any failure.
"""

import pandas as pd
import os
import sys
import json

ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(ENGINE_DIR, 'data', 'raw', 'MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx')
if not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.join(ENGINE_DIR, 'MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx')
SPLIT_PATH = os.path.join(ENGINE_DIR, 'data', 'processed', 'v2_victim_split.csv')
LONGITUDINAL_PATH = os.path.join(ENGINE_DIR, 'data', 'processed', 'v2_longitudinal_split.csv')
CONFIG_PATH = os.path.join(ENGINE_DIR, 'data', 'processed', 'v2_split_config.json')

errors = []
warnings = []

def check(name, condition, msg):
    """Record a check result."""
    if condition:
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name}: {msg}")
        errors.append(f"{name}: {msg}")

# ==============================================================
# 1. LOAD FILES
# ==============================================================
print("=== Loading Files ===")

if not os.path.exists(DATA_PATH):
    print(f"FATAL: Source dataset not found: {DATA_PATH}")
    sys.exit(1)

if not os.path.exists(SPLIT_PATH):
    print(f"FATAL: Victim split file not found: {SPLIT_PATH}")
    sys.exit(1)

if not os.path.exists(LONGITUDINAL_PATH):
    print(f"FATAL: Longitudinal split file not found: {LONGITUDINAL_PATH}")
    sys.exit(1)

source_df = pd.read_excel(DATA_PATH, sheet_name='Longitudinal_Data')
source_df = source_df.sort_values(['Victim_ID', 'Timepoint']).reset_index(drop=True)
print(f"  Source dataset: {len(source_df)} rows, {source_df['Victim_ID'].nunique()} victims")

split_df = pd.read_csv(SPLIT_PATH)
print(f"  Victim split: {len(split_df)} rows")

long_df = pd.read_csv(LONGITUDINAL_PATH)
print(f"  Longitudinal split: {len(long_df)} rows")

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    print(f"  Config: seed={config.get('random_seed')}, created={config.get('created_at')}")

# ==============================================================
# 2. VICTIM SPLIT FILE CHECKS
# ==============================================================
print("\n=== Victim Split File Validation ===")

check("Split file has 1000 rows", len(split_df) == 1000,
      f"Got {len(split_df)}")

check("All Victim_IDs unique", split_df['Victim_ID'].nunique() == len(split_df),
      f"Unique: {split_df['Victim_ID'].nunique()}, Total: {len(split_df)}")

check("Only valid split values", set(split_df['Split'].unique()) == {'train', 'validation', 'test'},
      f"Got: {split_df['Split'].unique()}")

train_count = (split_df['Split'] == 'train').sum()
val_count = (split_df['Split'] == 'validation').sum()
test_count = (split_df['Split'] == 'test').sum()

check("700 train victims", train_count == 700, f"Got {train_count}")
check("150 validation victims", val_count == 150, f"Got {val_count}")
check("150 test victims", test_count == 150, f"Got {test_count}")

# ==============================================================
# 3. NO VICTIM OVERLAP
# ==============================================================
print("\n=== Victim Overlap Check ===")

train_vids = set(split_df[split_df['Split'] == 'train']['Victim_ID'])
val_vids = set(split_df[split_df['Split'] == 'validation']['Victim_ID'])
test_vids = set(split_df[split_df['Split'] == 'test']['Victim_ID'])

check("Train ^ Validation = empty", len(train_vids & val_vids) == 0,
      f"Overlap: {train_vids & val_vids}")

check("Train ^ Test = empty", len(train_vids & test_vids) == 0,
      f"Overlap: {train_vids & test_vids}")

check("Validation ^ Test = empty", len(val_vids & test_vids) == 0,
      f"Overlap: {val_vids & test_vids}")

check("Union = all 1000 victims", len(train_vids | val_vids | test_vids) == 1000,
      f"Union has {len(train_vids | val_vids | test_vids)}")

# ==============================================================
# 4. ALL SOURCE VICTIMS COVERED
# ==============================================================
print("\n=== Source Coverage Check ===")

source_vids = set(source_df['Victim_ID'].unique())
split_vids = set(split_df['Victim_ID'].unique())

check("All source victims in split file", source_vids == split_vids,
      f"Missing: {source_vids - split_vids}, Extra: {split_vids - source_vids}")

# ==============================================================
# 5. LONGITUDINAL FILE CHECKS
# ==============================================================
print("\n=== Longitudinal Split File Validation ===")

check("Longitudinal file has 30000 rows", len(long_df) == 30000,
      f"Got {len(long_df)}")

long_train = (long_df['Split'] == 'train').sum()
long_val = (long_df['Split'] == 'validation').sum()
long_test = (long_df['Split'] == 'test').sum()

check("21000 train rows", long_train == 21000, f"Got {long_train}")
check("4500 validation rows", long_val == 4500, f"Got {long_val}")
check("4500 test rows", long_test == 4500, f"Got {long_test}")

# ==============================================================
# 6. TEMPORAL INTEGRITY
# ==============================================================
print("\n=== Temporal Integrity ===")

all_30 = True
all_single_split = True
all_timepoints = True

for vid in source_vids:
    vrows = long_df[long_df['Victim_ID'] == vid]
    if len(vrows) != 30:
        all_30 = False
    if len(vrows['Split'].unique()) != 1:
        all_single_split = False
    if set(vrows['Timepoint'].values) != set(range(1, 31)):
        all_timepoints = False

check("All victims have 30 rows", all_30, "Some victims have != 30 rows")
check("All victims in single split", all_single_split, "Some victims span multiple splits")
check("All victims have timepoints 1-30", all_timepoints, "Some victims have missing timepoints")

# ==============================================================
# 7. SPLIT CONSISTENCY: victim file vs longitudinal file
# ==============================================================
print("\n=== Split Consistency ===")

victim_to_split = dict(zip(split_df['Victim_ID'], split_df['Split']))
long_df['expected_split'] = long_df['Victim_ID'].map(victim_to_split)

consistent = (long_df['Split'] == long_df['expected_split']).all()
check("Longitudinal splits match victim splits", consistent,
      f"Mismatches: {(long_df['Split'] != long_df['expected_split']).sum()}")

# ==============================================================
# 8. DDS DISTRIBUTION COMPARISON
# ==============================================================
print("\n=== DDS Distribution ===")
for split in ['train', 'validation', 'test']:
    s = long_df[long_df['Split'] == split]['DDS']
    print(f"  {split:>10s}: mean={s.mean():.2f}, std={s.std():.2f}, "
          f"min={s.min():.2f}, max={s.max():.2f}, median={s.median():.2f}")

# ==============================================================
# 9. FUTURE ESCALATION DISTRIBUTION
# ==============================================================
print("\n=== Future_Escalation_Label ===")
for split in ['train', 'validation', 'test']:
    sub = long_df[long_df['Split'] == split]
    fel = sub['Future_Escalation_Label']
    valid = fel.dropna()
    pos = (valid == 1).sum()
    neg = (valid == 0).sum()
    total = len(valid)
    pct = pos / total * 100 if total > 0 else 0
    print(f"  {split:>10s}: pos={pos}, neg={neg}, NaN={fel.isna().sum()}, pct_pos={pct:.2f}%")

# ==============================================================
# FINAL RESULT
# ==============================================================
print("\n" + "=" * 50)
if len(errors) == 0:
    print("VALIDATION RESULT: ALL CHECKS PASSED")
    print("=" * 50)
    sys.exit(0)
else:
    print(f"VALIDATION RESULT: {len(errors)} CHECKS FAILED")
    for e in errors:
        print(f"  - {e}")
    print("=" * 50)
    sys.exit(1)
