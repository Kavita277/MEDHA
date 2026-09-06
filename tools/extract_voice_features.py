import os
import sys
import pandas as pd
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
OUT_CSV = os.path.join(DATASET_DIR, "voice_engine_outputs_150x30.csv")
AUDIO_DIR = os.path.join(DATASET_DIR, "audio")

def main():
    print("Loading artifacts...")
    engine = VoiceEngine()
    
    print("Loading voice dataset...")
    df = pd.read_csv(VOICE_CSV)
    selected_patients = pd.read_csv(PATIENTS_CSV)['patient_id'].tolist()
    df = df[df['patient_id'].isin(selected_patients)]
    
    print(f"Extracting features for {len(df)} samples sequentially...")
    results = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        pid = row['patient_id']
        did = row['day_index']
        
        filename = f"patient_{int(pid):04d}_day_{int(did):02d}.wav"
        audio_path = os.path.join(AUDIO_DIR, filename)
        
        if os.path.exists(audio_path):
            try:
                res = engine.analyze(audio_path)
                results.append({
                    "patient_id": pid,
                    "day_index": did,
                    "voice_distress": res["voice_distress"],
                    "confidence": res["confidence"],
                    "angry": res["emotion_probabilities"]["angry"],
                    "sad": res["emotion_probabilities"]["sad"],
                    "neutral": res["emotion_probabilities"]["neutral"],
                    "happy": res["emotion_probabilities"]["happy"],
                    "duration_seconds": res["acoustic_features"]["duration_seconds"],
                    "rms_energy": res["acoustic_features"]["rms_energy"],
                    "pitch_mean": res["acoustic_features"]["pitch_mean"],
                    "pitch_std": res["acoustic_features"]["pitch_std"],
                    "zero_crossing_rate": res["acoustic_features"]["zero_crossing_rate"],
                    "speaking_rate": res["acoustic_features"]["speaking_rate"],
                    "acoustic_indicator": res["acoustic_indicator"],
                    "voice_available": 1
                })
            except Exception as e:
                print(f"Error analyzing {filename}: {e}")
                results.append({"patient_id": pid, "day_index": did, "voice_available": 0})
        else:
            # Missing audio (generation failed)
            results.append({"patient_id": pid, "day_index": did, "voice_available": 0})
            
    # For missing days, fill with 0
    out_df = pd.DataFrame(results)
    features = [
        "voice_distress", "confidence", "angry", "sad", "neutral", "happy",
        "duration_seconds", "rms_energy", "pitch_mean", "pitch_std",
        "zero_crossing_rate", "speaking_rate", "acoustic_indicator"
    ]
    for feat in features:
        if feat not in out_df.columns:
            out_df[feat] = 0.0
        out_df[feat] = out_df[feat].fillna(0.0)
        
    out_df.to_csv(OUT_CSV, index=False)
    print(f"Successfully extracted voice features and saved to {OUT_CSV}")

if __name__ == "__main__":
    main()
