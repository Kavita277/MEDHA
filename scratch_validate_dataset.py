import pandas as pd
import sys

def validate_text():
    print("Validating text_engine_raw_input_500x30.csv...")
    try:
        df = pd.read_csv(r"c:\Users\abbsw\.gemini\antigravity\scratch\MEDHA\datasets\MEDHA_Longitudinal_Synthetic_1000x30\text_engine_raw_input_500x30.csv")
        assert len(df) == 15000, f"Expected 15000 rows, got {len(df)}"
        assert df["raw_text"].nunique() == 15000, "raw_text must be unique"
        assert not df["raw_text"].str.contains(r"[\u0900-\u097F]", regex=True).any(), "Found Devanagari text!"
        print("Text validation PASSED")
    except Exception as e:
        print(f"Text validation FAILED: {e}")

def validate_voice():
    print("Validating voice_engine_raw_manifest_500x30.csv...")
    try:
        df = pd.read_csv(r"c:\Users\abbsw\.gemini\antigravity\scratch\MEDHA\datasets\MEDHA_Longitudinal_Synthetic_1000x30\voice_engine_raw_manifest_500x30.csv")
        assert len(df) == 15000, f"Expected 15000 rows, got {len(df)}"
        assert df["voice_sample_id"].nunique() == 15000, "voice_sample_id must be unique"
        assert not df.astype(str).apply(lambda col: col.str.contains(r"[\u0900-\u097F]", regex=True).any()).any(), "Found Devanagari text in voice manifest!"
        print("Voice validation PASSED")
    except Exception as e:
        print(f"Voice validation FAILED: {e}")

if __name__ == "__main__":
    validate_text()
    validate_voice()
