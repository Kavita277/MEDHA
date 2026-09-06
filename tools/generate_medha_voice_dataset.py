import os
import sys
import argparse
import json
import time
import subprocess
import wave
import pandas as pd
import numpy as np

# Set deterministic seed
SEED = 42
np.random.seed(SEED)

DATASET_DIR = os.path.join("datasets", "MEDHA_Longitudinal_Synthetic_1000x30")
TEXT_CSV = os.path.join(DATASET_DIR, "text_engine_raw_input_500x30.csv")
VOICE_MANIFEST_CSV = os.path.join(DATASET_DIR, "voice_engine_raw_manifest_500x30.csv")
AUDIO_DIR = os.path.join(DATASET_DIR, "audio")

MANIFEST_OUT = "voice_audio_manifest.csv"
FAILURES_OUT = "voice_generation_failures.csv"
METADATA_OUT = "tts_generation_metadata.json"

PIPER_MODEL = "en_US-lessac-medium.onnx"

def validate_wav(filepath):
    if not os.path.exists(filepath):
        return False, "File does not exist"
    try:
        with wave.open(filepath, 'rb') as w:
            frames = w.getnframes()
            rate = w.getframerate()
            channels = w.getnchannels()
            if frames == 0:
                return False, "Zero samples"
            if rate == 0:
                return False, "Zero sample rate"
            duration = frames / float(rate)
            if duration <= 0:
                return False, "Zero duration"
            return True, {
                "sample_rate": rate,
                "channels": channels,
                "duration_seconds": duration,
                "frames": frames
            }
    except Exception as e:
        return False, f"Invalid WAV file: {str(e)}"

def generate_audio_piper(text, out_path):
    # Write to a temporary file to avoid shell pipe issues on Windows
    temp_txt = out_path + ".txt"
    try:
        with open(temp_txt, "w", encoding="utf-8") as f:
            f.write(text)
        cmd = f'piper --model {PIPER_MODEL} --input_file "{temp_txt}" --output_file "{out_path}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Piper failed: {result.stderr.strip()}"
        return True, "Success"
    finally:
        if os.path.exists(temp_txt):
            os.remove(temp_txt)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Regenerate existing files")
    parser.add_argument("--limit", type=int, help="Limit number of samples to generate")
    parser.add_argument("--patient-id", type=int, help="Debug one patient")
    args = parser.parse_args()

    os.makedirs(AUDIO_DIR, exist_ok=True)

    print("Checking for Piper...")
    try:
        subprocess.run(["piper", "-h"], capture_output=True, check=True)
    except Exception:
        print("Piper not found. Please pip install piper-tts and download the model.")
        sys.exit(1)

    print(f"Loading datasets from {DATASET_DIR}...")
    df_text = pd.read_csv(TEXT_CSV)
    df_voice = pd.read_csv(VOICE_MANIFEST_CSV)

    # Merge to ensure we have the authoritative text
    df = pd.merge(df_voice, df_text[['patient_id', 'day_index', 'raw_text']], on=['patient_id', 'day_index'], suffixes=('', '_text'))
    
    # Assertions
    assert df['patient_id'].notnull().all(), "patient_id cannot be null"
    assert df['day_index'].notnull().all(), "day_index cannot be null"
    assert df['raw_text_text'].notnull().all(), "text cannot be null"
    assert len(df.drop_duplicates(subset=['patient_id', 'day_index'])) == len(df), "patient_day pairs must be unique"

    if 'voice_available' not in df.columns:
        print("voice_available column not found!")
        sys.exit(1)

    df = df[df['voice_available'] == 1].copy()

    if args.patient_id is not None:
        df = df[df['patient_id'] == args.patient_id].copy()

    if args.limit is not None:
        # Mandatory smoke test first if limit is 5
        df = df.head(args.limit).copy()

    # New Requirement: Only process the selected 150 patients
    selected_patients_df = pd.read_csv(os.path.join(DATASET_DIR, "selected_150_voice_patients.csv"))
    selected_patient_ids = set(selected_patients_df["patient_id"])
    df = df[df["patient_id"].isin(selected_patient_ids)]
    
    total_samples = len(df)
    print(f"Total samples to process for the 150-patient cohort: {total_samples}")

    manifest_records = []
    failure_records = []
    
    success_count = 0
    fail_count = 0

    for idx, row in df.iterrows():
        pid = row['patient_id']
        did = row['day_index']
        vid = row['voice_sample_id']
        text = row['raw_text_text']

        # E.g. patient_0001_day_01.wav
        filename = f"patient_{int(pid):04d}_day_{int(did):02d}.wav"
        out_path = os.path.join(AUDIO_DIR, filename)

        needs_generation = True
        if os.path.exists(out_path) and not args.force:
            valid, meta = validate_wav(out_path)
            if valid:
                needs_generation = False
            else:
                needs_generation = True

        status = "SUCCESS"
        fail_reason = ""
        meta_audio = {}

        if needs_generation:
            # Escape quotes in text for the shell command
            safe_text = text.replace('"', '\\"').replace('\n', ' ')
            ok, msg = generate_audio_piper(safe_text, out_path)
            if not ok:
                status = "FAILED"
                fail_reason = msg
            else:
                valid, meta = validate_wav(out_path)
                if not valid:
                    status = "FAILED"
                    fail_reason = meta
                else:
                    meta_audio = meta
        else:
            valid, meta = validate_wav(out_path)
            meta_audio = meta

        if status == "SUCCESS":
            success_count += 1
            manifest_records.append({
                "patient_id": pid,
                "day_index": did,
                "voice_sample_id": vid,
                "text_sample_id": f"TEXT_P{int(pid):03d}_D{int(did):02d}",  # synthetic text ID
                "text": text,
                "audio_path": os.path.abspath(out_path),
                "tts_model": PIPER_MODEL,
                "tts_model_version": "unknown",
                "sample_rate": meta_audio.get("sample_rate", ""),
                "channels": meta_audio.get("channels", ""),
                "duration_seconds": meta_audio.get("duration_seconds", ""),
                "generation_status": status,
                "failure_reason": ""
            })
        else:
            fail_count += 1
            failure_records.append({
                "patient_id": pid,
                "day_index": did,
                "voice_sample_id": vid,
                "failure_reason": fail_reason,
                "exception_type": "GenerationError"
            })

    print(f"Requested: {len(df)}")
    print(f"Generated: {success_count}")
    print(f"Failed: {fail_count}")
    
    pd.DataFrame(manifest_records).to_csv(MANIFEST_OUT, index=False)
    pd.DataFrame(failure_records).to_csv(FAILURES_OUT, index=False)

    metadata = {
        "generator_version": "1.0",
        "python_version": sys.version,
        "piper_version": "unknown", # Could be parsed from piper -h if needed
        "voice_name": PIPER_MODEL,
        "model_checksum": "unknown",
        "seed": SEED,
        "generation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_dataset_filename": VOICE_MANIFEST_CSV,
        "number_requested": len(df),
        "number_successfully_generated": success_count,
        "number_failed": fail_count
    }

    with open(METADATA_OUT, "w") as f:
        json.dump(metadata, f, indent=4)
        
    print("Generation complete!")

    if len(df) > 0:
        success_rate = success_count / len(df)
        print(f"Success rate: {success_rate:.2f}")
        if (1.0 - success_rate) > 0.01:
            print("Failure rate exceeds 1%. Exiting with error.")
            sys.exit(1)

if __name__ == "__main__":
    main()
