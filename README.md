# MEDHA — Multimodal AI Clinical Decision Support & Patient Companion

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React Native / Expo](https://img.shields.io/badge/Expo-51.0%2B-000020.svg)](https://expo.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-336791.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

MEDHA is a multi-modal clinical intelligence and longitudinal distress-monitoring platform. It empowers clinicians with AI-assisted distress scoring, safety escalation warnings, and explainable recommendations while providing patients with a non-stigmatizing daily companion for structured check-ins, journal reflections, and voice check-ins.

---

## 1. Key Capabilities

* **Unified Multimodal Prediction Engine**:
  * **Structured Specialist**: Analyzes 10–15 randomized daily clinical questionnaire responses.
  * **Text Specialist (NLP)**: Ingests journal reflections to score distress indicators.
  * **Voice Specialist**: Extracts acoustic prosody (pitch, jitter, shimmer, HNR) from voice check-ins.
  * **Behaviour Telemetry**: Ingests app interaction patterns and consistency.
  * **XGBoost Multimodal Fusion Engine**: Synthesizes available signals into a holistic Dynamic Distress Score (0–100) and clinical **Triage Level** (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  * **Temporal GRU Model**: Evaluates trailing 7-day sequences to forecast Day-8 safety escalation risk (`temporal_risk`).
* **Strict Patient Safety Safeguards**:
  * Patients only see warm, non-clinical supportive feedback (breathing, grounding, mindfulness).
  * Raw risk probabilities, triage classifications, and diagnostic labels are strictly isolated to authenticated clinicians.
* **Clinician / Therapist Workspace**:
  * Case overview with longitudinal trajectories.
  * Real-time audit of patient check-in responses, question by question.
  * Actionable clinical recommendations and explainability summaries.

---

## 2. Project Architecture

```
MEDHA/
├── backend/                  # FastAPI REST API & Clinical Services
│   ├── api/v1/               # Endpoints (Auth, Checkins, Sessions, Therapist, Voice)
│   ├── persistence/          # SQLAlchemy 2.0 ORM Models & Repositories
│   └── services/             # Prediction orchestration, journal, checkin services
├── app-frontend/             # Cross-platform Patient & Therapist App (React Native / Expo)
│   └── medha-app/            # Modern Expo Router UI (home, check-in, therapist, profile)
├── chatbot/                  # Conversational and Question Generation Engines
│   └── engines/              # Randomized 10-15 Question Engine across 4 domains
├── engine/                   # Frozen Machine Learning Models & Pipeline
│   ├── v2/                   # MedhaV2Pipeline execution logic
│   └── models/               # Frozen model weights (XGBoost, MuRIL, GRU, preprocessors)
├── database/                 # Database Schema & DDL Scripts
│   └── schema.sql            # Full PostgreSQL DDL creation script
├── docs/                     # Technical specifications & architecture docs
│   └── DATABASE_STRUCTURE.md # Detailed schema & ER diagrams
└── scripts/                  # Seeding, verification, and CLI inspection utilities
```

---

## 3. Prerequisites

* **Python**: `3.10` or `3.11`
* **Node.js**: `18.x` or `20.x` (with `npm` or `yarn`)
* **PostgreSQL**: `14+` running locally or accessible via network
* **Git**: Installed and configured

---

## 4. Quickstart Setup Guide

### Step 1: Clone Repository & Switch to `medha-v2` Branch
```bash
git clone https://github.com/Kavita277/MEDHA.git
cd MEDHA
git checkout medha-v2
```

### Step 2: Set Up Python Backend Environment
```bash
# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to configure your PostgreSQL credentials and optional Gemini API Key:
```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/medha
GEMINI_API_KEY=your_gemini_api_key_here
```

### Step 4: Initialize the PostgreSQL Database
Ensure your PostgreSQL database (e.g. `medha`) is created:
```sql
CREATE DATABASE medha;
```
Run the seed scripts to automatically build all tables and populate default accounts:
```bash
# 1. Base Administrator & Patient Seeder
python seed_db.py

# 2. Multi-Case Longitudinal Clinical Demo Seeder
python scripts/seed_demo_data.py
```
*(Alternatively, you can manually apply the DDL from `database/schema.sql`)*.

### Step 5: Set Up Frontend (Expo Mobile & Web App)
```bash
cd app-frontend/medha-app
npm install
cd ../..
```

---

## 5. Running the Application

### 1. Start the Backend API Server
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
* **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Start the Frontend Application
In a separate terminal:
```bash
cd app-frontend/medha-app
npx expo start --web
```
* **Patient App**: [http://localhost:8081/home](http://localhost:8081/home)
* **Clinician Workspace**: [http://localhost:8081/therapist-login](http://localhost:8081/therapist-login)

---

## 6. Pre-Configured Demo Credentials

| Role | Name | Email | Password | Assigned Case |
|---|---|---|---|---|
| **Clinician / Therapist** | Dr. Radhika Sharma | `demo.therapist@medha.org` | `TherapistDemo123!` | Manages 4 Active Cases |
| **Clinician / Therapist** | Dr. Jane Clinician | `therapist@medha.org` | `TherapistPass123!` | Base Clinician Account |
| **Patient (Low Risk)** | Ananya Sharma | `ananya.sharma@medha.org` | `PatientPass123!` | `V-LOW-001` |
| **Patient (Moderate Risk)** | Rahul Verma | `rahul.verma@medha.org` | `PatientPass123!` | `V-MED-002` |
| **Patient (High Risk)** | Priya Patel | `priya.patel@medha.org` | `PatientPass123!` | `V-HIGH-003` |
| **Patient (Critical / GRU)** | Kavita Rao | `kavita.rao@medha.org` | `PatientPass123!` | `V-CRIT-004` |

---

## 7. Useful CLI Tools

* **Inspect Latest Check-In Answers**:
  ```bash
  python scripts/view_quiz_answers.py
  ```
* **Sync PostgreSQL Data to Local SQLite Replica**:
  ```bash
  python scripts/sync_pg_to_sqlite.py
  ```
* **Run Backend Unit & Integration Tests**:
  ```bash
  pytest backend/tests/
  ```

---

## 8. Database Structure Documentation

For full details regarding table relationships, foreign keys, and ML prediction schemas, refer to:
* **[docs/DATABASE_STRUCTURE.md](docs/DATABASE_STRUCTURE.md)**
* **[database/schema.sql](database/schema.sql)**

---

## 9. License

This repository is proprietary and confidential. Developed for the MEDHA clinical monitoring initiative.