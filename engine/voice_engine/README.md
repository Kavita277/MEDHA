# MEDHA Voice Engine

The Voice Engine processes acoustic and prosodic features from audio recordings (e.g., recorded statements, phone calls) to detect signs of emotional distress, anxiety, or trauma.

## Codebase File Directory
- **`voice_engine.py`**: The core logic containing the audio feature extraction and inference classes.
- **`main.py`**: The primary entry point or testing script to execute the voice engine on sample audio.
- **`models/`**: Stored machine learning models used for acoustic classification.
- **`services/`**: Helper services for handling audio files (e.g., resampling, format conversion).
- **`training/`**: Scripts used to train the original acoustic models.
- **`requirements.txt`**: Python dependencies specific to audio processing (e.g., librosa).

## Integration Guide (For Backend Developers)

To integrate the Voice Engine into the backend API, the system must accept audio streams/files, extract features, and return a distress probability.

**Current Status:** The core `voice_engine.py` exists, but a standardized API-ready inference wrapper is **yet to be explicitly exposed/built** for seamless routing.

Once built, integration will follow this pattern:
```python
# [PROPOSED INTEGRATION - Method Yet To Be Built / Finalized]
from voice_engine.voice_engine import analyze_audio

audio_file_path = "/path/to/recording.wav"
voice_risk_score = analyze_audio(audio_file_path)
# Output should be passed to the adapters.py in the Fusion Engine
```
