# MEDHA Text Engine

The Text Engine is responsible for analyzing unstructured textual inputs (e.g., chat logs, transcribed interviews, check-ins) to detect psychological distress and trauma indicators in victims.

## Codebase File Directory
- **`medha_text_engine.py`**: The core operational script containing the text analysis models and NLP pipelines.
- **`test_integration.py`**: Testing suite for validating the engine's outputs and pipeline integrity.
- **`Models/`**: Directory containing serialized NLP models or vectorizers used by the engine.
- **`notebooks/`**: Exploratory Jupyter notebooks used during the training and validation phase.
- **`data/` & `results/`**: Directories for input datasets and output prediction logs.

## Integration Guide (For Backend Developers)

To integrate the Text Engine into the main backend API, you need to pass raw text to the engine and receive a distress score [0, 1].

**Current Status:** The core engine is built, but a unified `inference(text: str) -> float` wrapper method specifically designed for the backend is **yet to be built**. 

Once built, integration will look like this:
```python
# [PROPOSED INTEGRATION - Method Yet To Be Built]
from text_engine.medha_text_engine import calculate_text_risk

raw_text = "I am feeling very overwhelmed today..."
text_risk_score = calculate_text_risk(raw_text)
# Output should be passed to the adapters.py in the Fusion Engine
```
