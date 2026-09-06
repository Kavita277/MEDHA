import os
import sys
import pandas as pd
from tqdm import tqdm

# Add engine directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine', 'text engine')))

try:
    from medha_text_engine import medha_text_engine
except ImportError as e:
    print(f"Failed to import medha_text_engine: {e}")
    sys.exit(1)

DATASET_DIR = os.path.join("datasets", "MEDHA_Longitudinal_Synthetic_1000x30")
TEXT_CSV = os.path.join(DATASET_DIR, "text_engine_raw_input_500x30.csv")
OUT_CSV = os.path.join(DATASET_DIR, "text_engine_outputs_500x30.csv")

def main():
    print("Loading text dataset...")
    df = pd.read_csv(TEXT_CSV)
    
    print(f"Extracting features for {len(df)} samples...")
    results = []
    
    # We use iterrows. If performance is too slow, we can batch it if the engine supports it.
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        text = row['raw_text']
        
        request = {
            "text": text,
            "victim_id": row['patient_id'],
            "session_id": f"D{row['day_index']}",
            "timestamp": "2026-01-01T00:00:00Z",
            "source": "diary"
        }
        
        # frozen TextEngine extracts features
        response = medha_text_engine(request)
        vec = response['text_vector']
            
        results.append({
            "patient_id": row['patient_id'],
            "day_index": row['day_index'],
            "text_distress": vec["text_distress"],
            "fear_signal": vec["fear_signal"],
            "threat_context": vec["threat_context"],
            "negative_affect": vec["negative_affect"],
            "urgency": vec["urgency"],
            "text_available": row.get('text_available', 1)
        })
        
    out_df = pd.DataFrame(results)
    out_df.to_csv(OUT_CSV, index=False)
    print(f"Successfully extracted text features and saved to {OUT_CSV}")

if __name__ == "__main__":
    main()
