"""
MEDHA V2 — Step 3: Create Authoritative Victim-Level Data Split

This script:
1. Loads the regenerated dataset
2. Shuffles Victim_IDs with seed=42
3. Assigns 700/150/150 train/val/test
4. Saves v2_victim_split.csv (1000 rows)
5. Saves v2_longitudinal_split.csv (30000 rows)
6. Saves v2_split_config.json
7. Runs all verification checks
"""

import pandas as pd
import numpy as np
import os
import json
import sys
from datetime import datetime

# ==============================================================
# CONFIGURATION
# ==============================================================
SEED = 42
TRAIN_PCT = 0.70
VAL_PCT = 0.15
TEST_PCT = 0.15

ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(ENGINE_DIR, 'data', 'raw', 'MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx')
if not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.join(ENGINE_DIR, 'MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx')
SHEET_NAME = 'Longitudinal_Data'
OUTPUT_DIR = os.path.join(ENGINE_DIR, 'data', 'processed')
VICTIM_SPLIT_PATH = os.path.join(OUTPUT_DIR, 'v2_victim_split.csv')
LONGITUDINAL_SPLIT_PATH = os.path.join(OUTPUT_DIR, 'v2_longitudinal_split.csv')
CONFIG_PATH = os.path.join(OUTPUT_DIR, 'v2_split_config.json')

# ==============================================================
# LOAD DATA
# ==============================================================
print("Loading dataset...")
df = pd.read_excel(DATA_PATH, sheet_name=SHEET_NAME)
df = df.sort_values(['Victim_ID', 'Timepoint']).reset_index(drop=True)
print(f"  Loaded {len(df)} rows, {df['Victim_ID'].nunique()} unique victims")

# ==============================================================
# GET UNIQUE VICTIMS AND SHUFFLE
# ==============================================================
unique_victims = sorted(df['Victim_ID'].unique())
n_victims = len(unique_victims)
print(f"  Total unique victims: {n_victims}")

assert n_victims == 1000, f"Expected 1000 victims, got {n_victims}"

rng = np.random.RandomState(SEED)
shuffled_victims = unique_victims.copy()
rng.shuffle(shuffled_victims)

# ==============================================================
# ASSIGN SPLITS
# ==============================================================
n_train = int(n_victims * TRAIN_PCT)   # 700
n_val = int(n_victims * VAL_PCT)       # 150
n_test = n_victims - n_train - n_val   # 150

train_victims = shuffled_victims[:n_train]
val_victims = shuffled_victims[n_train:n_train + n_val]
test_victims = shuffled_victims[n_train + n_val:]

print(f"  Train victims: {len(train_victims)}")
print(f"  Validation victims: {len(val_victims)}")
print(f"  Test victims: {len(test_victims)}")

assert len(train_victims) == 700, f"Expected 700 train, got {len(train_victims)}"
assert len(val_victims) == 150, f"Expected 150 val, got {len(val_victims)}"
assert len(test_victims) == 150, f"Expected 150 test, got {len(test_victims)}"

# ==============================================================
# CREATE VICTIM SPLIT CSV
# ==============================================================
victim_split_df = pd.DataFrame({
    'Victim_ID': list(train_victims) + list(val_victims) + list(test_victims),
    'Split': ['train'] * len(train_victims) + ['validation'] * len(val_victims) + ['test'] * len(test_victims)
})
victim_split_df = victim_split_df.sort_values('Victim_ID').reset_index(drop=True)

os.makedirs(OUTPUT_DIR, exist_ok=True)
victim_split_df.to_csv(VICTIM_SPLIT_PATH, index=False)
print(f"\nSaved victim split: {VICTIM_SPLIT_PATH}")
print(f"  Rows: {len(victim_split_df)}")

# ==============================================================
# CREATE LONGITUDINAL SPLIT CSV
# ==============================================================
victim_to_split = dict(zip(victim_split_df['Victim_ID'], victim_split_df['Split']))
df['Split'] = df['Victim_ID'].map(victim_to_split)

assert df['Split'].isna().sum() == 0, "Some rows have no split assignment!"

df.to_csv(LONGITUDINAL_SPLIT_PATH, index=False)
print(f"\nSaved longitudinal split: {LONGITUDINAL_SPLIT_PATH}")
print(f"  Total rows: {len(df)}")
print(f"  Train rows: {(df['Split'] == 'train').sum()}")
print(f"  Validation rows: {(df['Split'] == 'validation').sum()}")
print(f"  Test rows: {(df['Split'] == 'test').sum()}")

# ==============================================================
# VERIFICATION 1: NO VICTIM OVERLAP
# ==============================================================
print("\n=== VERIFICATION: Victim Overlap ===")
train_set = set(train_victims)
val_set = set(val_victims)
test_set = set(test_victims)

overlap_tv = train_set & val_set
overlap_tt = train_set & test_set
overlap_vt = val_set & test_set

print(f"  Train ^ Validation: {len(overlap_tv)} (must be 0)")
print(f"  Train ^ Test: {len(overlap_tt)} (must be 0)")
print(f"  Validation ^ Test: {len(overlap_vt)} (must be 0)")
print(f"  Union covers all victims: {len(train_set | val_set | test_set)} (must be 1000)")

assert len(overlap_tv) == 0, "LEAKAGE: Train and Validation share victims!"
assert len(overlap_tt) == 0, "LEAKAGE: Train and Test share victims!"
assert len(overlap_vt) == 0, "LEAKAGE: Validation and Test share victims!"
assert len(train_set | val_set | test_set) == 1000, "Not all victims assigned!"

print("  PASS: No victim overlap")

# ==============================================================
# VERIFICATION 2: TEMPORAL INTEGRITY
# ==============================================================
print("\n=== VERIFICATION: Temporal Integrity ===")
fail_count = 0
for vid in unique_victims:
    vrows = df[df['Victim_ID'] == vid]
    if len(vrows) != 30:
        print(f"  FAIL: {vid} has {len(vrows)} rows (expected 30)")
        fail_count += 1
    tps = set(vrows['Timepoint'].values)
    if tps != set(range(1, 31)):
        print(f"  FAIL: {vid} timepoints are {tps}")
        fail_count += 1
    splits = vrows['Split'].unique()
    if len(splits) != 1:
        print(f"  FAIL: {vid} appears in multiple splits: {splits}")
        fail_count += 1

if fail_count == 0:
    print("  PASS: All 1000 victims have 30 rows, timepoints 1-30, single split")
else:
    print(f"  FAIL: {fail_count} issues found")
    sys.exit(1)

# ==============================================================
# VERIFICATION 3: ROW COUNTS
# ==============================================================
print("\n=== VERIFICATION: Row Counts ===")
train_rows = (df['Split'] == 'train').sum()
val_rows = (df['Split'] == 'validation').sum()
test_rows = (df['Split'] == 'test').sum()

print(f"  Train: {train_rows} (expected 21000)")
print(f"  Validation: {val_rows} (expected 4500)")
print(f"  Test: {test_rows} (expected 4500)")

assert train_rows == 21000, f"Train rows: {train_rows}"
assert val_rows == 4500, f"Val rows: {val_rows}"
assert test_rows == 4500, f"Test rows: {test_rows}"
print("  PASS")

# ==============================================================
# VERIFICATION 4: DDS DISTRIBUTION
# ==============================================================
print("\n=== DDS Distribution by Split ===")
for split in ['train', 'validation', 'test']:
    s = df[df['Split'] == split]['DDS']
    print(f"  {split:>10s}: mean={s.mean():.2f}, std={s.std():.2f}, "
          f"min={s.min():.2f}, max={s.max():.2f}, median={s.median():.2f}")

# ==============================================================
# VERIFICATION 5: FUTURE ESCALATION DISTRIBUTION
# ==============================================================
print("\n=== Future_Escalation_Label Distribution by Split ===")
for split in ['train', 'validation', 'test']:
    sub = df[df['Split'] == split]
    fel = sub['Future_Escalation_Label']
    valid = fel.dropna()
    pos = (valid == 1).sum()
    neg = (valid == 0).sum()
    total = len(valid)
    pct = pos / total * 100 if total > 0 else 0
    print(f"  {split:>10s}: pos={pos}, neg={neg}, total={total}, NaN={fel.isna().sum()}, pos_pct={pct:.2f}%")

# ==============================================================
# VERIFICATION 6: TRAJECTORY DISTRIBUTION (from Victim_Profiles)
# ==============================================================
print("\n=== Trajectory Distribution by Split ===")
try:
    vp = pd.read_excel(DATA_PATH, sheet_name='Victim_Profiles')
    vp_merged = vp.merge(victim_split_df, on='Victim_ID', how='inner')
    for split in ['train', 'validation', 'test']:
        sub = vp_merged[vp_merged['Split'] == split]
        dist = sub['Trajectory_Type'].value_counts().to_dict()
        print(f"  {split}: {dist}")
except Exception as e:
    print(f"  Could not load Victim_Profiles: {e}")

# ==============================================================
# SAVE CONFIG
# ==============================================================
config = {
    "dataset_path": "engine/data/raw/MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx",
    "sheet_name": SHEET_NAME,
    "random_seed": SEED,
    "train_percent": TRAIN_PCT,
    "validation_percent": VAL_PCT,
    "test_percent": TEST_PCT,
    "num_victims": n_victims,
    "num_rows": len(df),
    "train_victims": n_train,
    "validation_victims": n_val,
    "test_victims": n_test,
    "train_rows": int(train_rows),
    "validation_rows": int(val_rows),
    "test_rows": int(test_rows),
    "split_file_path": "engine/data/processed/v2_victim_split.csv",
    "longitudinal_split_path": "engine/data/processed/v2_longitudinal_split.csv",
    "created_at": datetime.now().isoformat()
}
with open(CONFIG_PATH, 'w') as f:
    json.dump(config, f, indent=2)
print(f"\nSaved config: {CONFIG_PATH}")

print("\n" + "=" * 50)
print("ALL CHECKS PASSED")
print("=" * 50)
