import os
import sys
import pandas as pd
import numpy as np
from tqdm import tqdm

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine', 'voice_engine')))

try:
    from voice_engine import VoiceEngine
except ImportError as e:
    print(f"Failed to import VoiceEngine: {e}")
    sys.exit(1)

DATASET_DIR = os.path.join("datasets", "MEDHA_Longitudinal_Synthetic_1000x30")
VOICE_CSV = os.path.join(DATASET_DIR, "voice_engine_raw_manifest_500x30.csv")
PATIENTS_CSV = os.path.join(DATASET_DIR, "selected_150_voice_patients.csv")
OUT_NPZ = os.path.join(DATASET_DIR, "voice_engine_outputs_150x30.npz")
AUDIO_DIR = os.path.join(DATASET_DIR, "audio")

def main():
    print("Loading artifacts...")
    engine = VoiceEngine()
    
    print("Loading voice dataset...")
    df = pd.read_csv(VOICE_CSV)
    selected_patients = pd.read_csv(PATIENTS_CSV)['patient_id'].tolist()
    # Ensure sorted order for consistency
    selected_patients = sorted(selected_patients)
    
    num_patients = len(selected_patients)
    num_days = 30
    hidden_dim = 768  # Wav2Vec2 base
    
    # Initialize tensors
    X_voice = np.zeros((num_patients, num_days, hidden_dim), dtype=np.float32)
    voice_mask = np.zeros((num_patients, num_days), dtype=np.int32)
    patient_ids = np.array(selected_patients, dtype=np.int32)
    
    # Create mapping from patient_id to array index
    pid_to_idx = {pid: idx for idx, pid in enumerate(selected_patients)}
    
    # Filter original df to only selected patients
    df = df[df['patient_id'].isin(selected_patients)]
    
    print(f"Extracting Wav2Vec2 features for {len(df)} samples sequentially...")
    
    for _, row in tqdm(df.iterrows(), total=len(df)):
        pid = int(row['patient_id'])
        did = int(row['day_index'])
        p_idx = pid_to_idx[pid]
        d_idx = did - 1  # 0-indexed day
        
        filename = f"patient_{pid:04d}_day_{did:02d}.wav"
        audio_path = os.path.join(AUDIO_DIR, filename)
        
        if os.path.exists(audio_path):
            try:
                res = engine.analyze(audio_path)
                embedding = res["wav2vec2_embedding"]
                X_voice[p_idx, d_idx, :] = embedding
                voice_mask[p_idx, d_idx] = 1
            except Exception as e:
                print(f"Error analyzing {filename}: {e}")
        else:
            print(f"Audio not found: {filename}")
            
    print(f"Saving features to {OUT_NPZ}...")
    np.savez_compressed(
        OUT_NPZ, 
        X_voice=X_voice, 
        voice_mask=voice_mask, 
        patient_ids=patient_ids
    )
    print("Successfully extracted Wav2Vec2 features!")

if __name__ == "__main__":
    main()
