import os
import sys
import pandas as pd
from tqdm import tqdm

# Set artifacts path before importing the API
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine', 'behaviour_engine'))
os.environ["MEDHA_ARTIFACTS_PATH"] = os.path.join(ENGINE_DIR, "medha_scoring_artifacts.joblib")

sys.path.insert(0, ENGINE_DIR)

try:
    from medha_scoring_api import load_artifacts, score_one_day, DailyFeaturesIn
except ImportError as e:
    print(f"Failed to import medha_scoring_api: {e}")
    sys.exit(1)

DATASET_DIR = os.path.join("datasets", "MEDHA_Longitudinal_Synthetic_1000x30")
BEHAVIOUR_CSV = os.path.join(DATASET_DIR, "behaviour_engine_raw_input_500x30.csv")
OUT_CSV = os.path.join(DATASET_DIR, "behaviour_engine_outputs_500x30.csv")

def main():
    print("Loading artifacts...")
    load_artifacts()
    
    print("Loading behaviour dataset...")
    df = pd.read_csv(BEHAVIOUR_CSV)
    
    # Sort by patient and day to ensure sequential processing
    df = df.sort_values(by=['patient_id', 'day_index']).reset_index(drop=True)
    
    print(f"Extracting features for {len(df)} samples sequentially...")
    results = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        pid = str(row['patient_id'])
        
        # Build DailyFeaturesIn object
        def nan_to_none(val):
            return None if pd.isna(val) else float(val)
            
        feat_in = DailyFeaturesIn(
            day_index=int(row['day_index']),
            completion_baseline_z=nan_to_none(row.get('completion_baseline_z')),
            latency_baseline_z=nan_to_none(row.get('latency_baseline_z')),
            question_skip_rate=nan_to_none(row.get('question_skip_rate')),
            session_duration_baseline_z=nan_to_none(row.get('session_duration_baseline_z')),
            response_length_baseline_z=nan_to_none(row.get('response_length_baseline_z')),
            missed_checkins=int(row.get('missed_checkins', 0))
        )
        
        score_out = score_one_day(pid, feat_in)
        
        results.append({
            "patient_id": row['patient_id'],
            "day_index": row['day_index'],
            "anomaly_score": score_out.anomaly_score if score_out.anomaly_score is not None else 0.0,
            "engagement_deviation": score_out.engagement_deviation if score_out.engagement_deviation is not None else 0.0,
            "inactivity_score": score_out.inactivity_score if score_out.inactivity_score is not None else 0.0,
            "behaviour_available": row.get('behaviour_available', 1)
        })
        
    out_df = pd.DataFrame(results)
    out_df.to_csv(OUT_CSV, index=False)
    print(f"Successfully extracted behaviour features and saved to {OUT_CSV}")

if __name__ == "__main__":
    main()
