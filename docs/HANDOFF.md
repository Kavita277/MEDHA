# MEDHA Backend & Dashboard Handoff

This directory (``) contains the complete FastAPI backend and single-file HTML frontend for the MEDHA project, successfully joined with the models from Aby's branch.

## What is Included

- **`app/`**: The FastAPI application including standardized routers (`/analyze/text`, `/analyze/voice`, `/analyze/behaviour`, `/analyze/structured`, `/analyze/temporal`).
- **`generate_html_pt1.py` & `generate_html_pt2.py`**: Generators for `index.html`. The dashboard now includes the 7 new Structured Risk parameters introduced by the Question Engine: Mood, Stress, Sleep, Functioning, Safety, Social Support, and Wellbeing.
- **`tests/`**: Contains `pytest` integration tests.
- **`medha.db`**: SQLite database configured for storing patient histories and logging longitudinal risk assessments.

## Architecture

The backend adapters natively interface with the existing ML engines located in `../engine`.
1. **Text Adapter**: Interfaces with `../engine/text engine`.
2. **Voice Adapter**: Interfaces with `../engine/voice_engine` (now leveraging Wav2Vec2).
3. **Behaviour Adapter**: Interfaces with `../engine/behaviour_engine` converting UI parameters to `DailyFeaturesIn`.
4. **Structured Adapter**: Interfaces with `../engine/Structured_risk_enigne` mapping the new 7 core Question Engine indicators perfectly.
5. **Temporal Adapter**: Interfaces with `../engine/gru-temporal-risk`.
6. **Fusion Service**: Calculates a holistic `DDS` score. Due to the absence of the Gated Late Fusion weights in the repository, it falls back to a deterministic weighting system combining all available signals.

## Running the System

To run the unified dashboard and API:

1. Setup the Python environment and install `requirements.txt`.
2. Generate the frontend:
   ```bash
   python generate_html_pt1.py
   python generate_html_pt2.py
   ```
3. Start the API Server:
   ```bash
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
4. Open the generated `templates/index.html` file in a browser, or navigate to `http://127.0.0.1:8000/test`.
