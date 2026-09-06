import os
import json
import pandas as pd
import numpy as np

# Reproducibility
SEED = 42
np.random.seed(SEED)

DATASET_DIR = os.path.join("datasets", "MEDHA_Longitudinal_Synthetic_1000x30")
TEXT_CSV = os.path.join(DATASET_DIR, "text_engine_raw_input_500x30.csv")
SPLITS_OUT = os.path.join(DATASET_DIR, "patient_splits.json")

def main():
    print("Loading patient IDs from text dataset...")
    df = pd.read_csv(TEXT_CSV)
    
    unique_patients = df['patient_id'].unique()
    num_patients = len(unique_patients)
    print(f"Total unique patients: {num_patients}")
    
    # Shuffle patients
    shuffled_patients = np.random.permutation(unique_patients)
    
    # 70% train, 15% val, 15% test
    n_train = int(0.70 * num_patients)
    n_val = int(0.15 * num_patients)
    
    train_ids = shuffled_patients[:n_train].tolist()
    val_ids = shuffled_patients[n_train:n_train+n_val].tolist()
    test_ids = shuffled_patients[n_train+n_val:].tolist()
    
    print(f"Train: {len(train_ids)} patients")
    print(f"Val: {len(val_ids)} patients")
    print(f"Test: {len(test_ids)} patients")
    
    # Assertions
    assert set(train_ids).isdisjoint(val_ids), "Train and Val overlap!"
    assert set(train_ids).isdisjoint(test_ids), "Train and Test overlap!"
    assert set(val_ids).isdisjoint(test_ids), "Val and Test overlap!"
    
    splits = {
        "train": [int(x) for x in train_ids],
        "val": [int(x) for x in val_ids],
        "test": [int(x) for x in test_ids]
    }
    
    with open(SPLITS_OUT, "w") as f:
        json.dump(splits, f, indent=4)
        
    print(f"Splits successfully saved to {SPLITS_OUT}")

if __name__ == "__main__":
    main()
