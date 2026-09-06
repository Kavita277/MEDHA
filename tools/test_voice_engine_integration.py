import os
import sys

# Add engine directory to path so we can import VoiceEngine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine', 'voice_engine')))

try:
    from voice_engine import VoiceEngine
except ImportError as e:
    print(f"Failed to import VoiceEngine: {e}")
    sys.exit(1)

def test_integration(audio_dir, limit=5):
    print("Initializing VoiceEngine...")
    engine = VoiceEngine()
    
    # Find generated WAV files
    wav_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
    wav_files.sort()
    
    if not wav_files:
        print("No WAV files found for testing.")
        sys.exit(1)
        
    test_files = wav_files[:limit]
    print(f"Running VoiceEngine on {len(test_files)} generated files...")
    
    for f in test_files:
        path = os.path.join(audio_dir, f)
        print(f"Analyzing {f}...")
        try:
            result = engine.analyze(path)
            print("Result:")
            print(f"  voice_distress: {result.get('voice_distress')}")
            print(f"  confidence: {result.get('confidence')}")
            print(f"  acoustic_indicator: {result.get('acoustic_indicator')}")
            print(f"  Keys returned: {list(result.keys())}")
        except Exception as e:
            print(f"Error analyzing {f}: {e}")
            sys.exit(1)
            
    print("\nIntegration test PASSED.")

if __name__ == "__main__":
    audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasets', 'MEDHA_Longitudinal_Synthetic_1000x30', 'audio'))
    test_integration(audio_dir)
