"""
Step 30 — Demo Seed Verification Test Suite
===========================================

Verifies that the Demo Seed System creates authentic, longitudinal multi-case
data across the clinical risk spectrum and that the real MEDHA V2 inference
pipeline generates stored predictions without fabrication.
"""

from __future__ import annotations

import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.dependencies import get_db
from backend.main import app
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.persistence.models.user import User, UserRole
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.services.seed_service import (
    seed_demo_data,
    DEMO_THERAPIST_EMAIL,
    DEMO_THERAPIST_PASSWORD,
    DEMO_CASES_CONFIG,
)


@pytest.fixture(scope="function")
def seed_test_db():
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)

    def _get_db() -> Generator:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    yield engine
    app.dependency_overrides.clear()


def test_demo_seed_creation_and_counts(seed_test_db):
    """
    Verifies that running seed_demo_data creates the therapist, all 4 cases,
    3 timepoints per case, and persists authentic predictions.
    """
    with Session(seed_test_db) as db:
        result = seed_demo_data(db)

        # Therapist
        therapist = db.query(User).filter(User.email == DEMO_THERAPIST_EMAIL).first()
        assert therapist is not None
        assert therapist.role == UserRole.THERAPIST
        t_profile = db.query(Therapist).filter(Therapist.user_id == therapist.id).first()
        assert t_profile is not None

        # Cases
        cases = db.query(Case).filter(Case.therapist_id == t_profile.id).all()
        assert len(cases) == 4
        victim_ids = {c.victim_id for c in cases}
        assert victim_ids == {
            "V-DEMO-LOW-001",
            "V-DEMO-MOD-001",
            "V-DEMO-HIGH-001",
            "V-DEMO-CRIT-001",
        }

        # Sessions & Predictions (3 timepoints per case = 12 sessions and 12 predictions)
        sessions = db.query(SessionModel).all()
        assert len(sessions) == 12

        predictions = db.query(PredictionResultModel).all()
        assert len(predictions) == 12

        # Check prediction properties
        for pred in predictions:
            assert pred.fusion_dds_prediction is not None
            assert 0.0 <= pred.fusion_dds_prediction <= 100.0
            assert pred.triage_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            assert pred.struct_pred is not None
            assert pred.text_pred is not None
            assert pred.voice_pred is not None


def test_demo_seed_idempotency(seed_test_db):
    """
    Verifies that running the seed multiple times is completely idempotent
    and does not duplicate users, cases, sessions, or predictions.
    """
    with Session(seed_test_db) as db:
        res1 = seed_demo_data(db)
        assert res1["cases_created"] == 4
        assert res1["predictions_generated"] == 12

        # Run second time without force
        res2 = seed_demo_data(db, force_refresh=False)
        assert res2["cases_created"] == 0
        assert res2["cases_reused"] == 4
        assert res2["predictions_generated"] == 0

        # Verify DB counts remain identical
        assert db.query(User).count() == 5  # 1 therapist + 4 patients
        assert db.query(Therapist).count() == 1
        assert db.query(Case).count() == 4
        assert db.query(SessionModel).count() == 12
        assert db.query(PredictionResultModel).count() == 12


def test_predictions_authentic_and_progressive_risk_spectrum(seed_test_db):
    """
    Verifies that real V2 inference naturally produces a distinct risk gradient
    from LOW to CRITICAL across the 4 demo profiles.
    """
    with Session(seed_test_db) as db:
        seed_demo_data(db)

        low_case = db.query(Case).filter(Case.victim_id == "V-DEMO-LOW-001").first()
        mod_case = db.query(Case).filter(Case.victim_id == "V-DEMO-MOD-001").first()
        high_case = db.query(Case).filter(Case.victim_id == "V-DEMO-HIGH-001").first()
        crit_case = db.query(Case).filter(Case.victim_id == "V-DEMO-CRIT-001").first()

        # Get T3 (latest) predictions
        low_t3 = db.query(PredictionResultModel).filter(
            PredictionResultModel.case_id == low_case.id,
            PredictionResultModel.timepoint == 3,
        ).first()

        mod_t3 = db.query(PredictionResultModel).filter(
            PredictionResultModel.case_id == mod_case.id,
            PredictionResultModel.timepoint == 3,
        ).first()

        high_t3 = db.query(PredictionResultModel).filter(
            PredictionResultModel.case_id == high_case.id,
            PredictionResultModel.timepoint == 3,
        ).first()

        crit_t3 = db.query(PredictionResultModel).filter(
            PredictionResultModel.case_id == crit_case.id,
            PredictionResultModel.timepoint == 3,
        ).first()

        # Verify ascending risk gradient produced by authentic pipeline
        assert low_t3.fusion_dds_prediction < mod_t3.fusion_dds_prediction
        assert mod_t3.fusion_dds_prediction < high_t3.fusion_dds_prediction
        assert high_t3.fusion_dds_prediction < crit_t3.fusion_dds_prediction

        assert low_t3.triage_level in ["LOW", "MEDIUM"]
        assert crit_t3.triage_level in ["MEDIUM", "HIGH", "CRITICAL"]


def test_therapist_apis_with_seeded_demo_data(seed_test_db):
    """
    Verifies that all Step 22-29 therapist APIs seamlessly consume the seeded demo data.
    """
    with Session(seed_test_db) as db:
        seed_demo_data(db)

    client = TestClient(app)

    # 1. Therapist Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_THERAPIST_EMAIL, "password": DEMO_THERAPIST_PASSWORD},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. List Cases
    cases_resp = client.get("/api/v1/therapist/cases", headers=headers)
    assert cases_resp.status_code == 200
    cases_data = cases_resp.json()
    assert len(cases_data) == 4

    # 3. Verify APIs for each case
    for case_item in cases_data:
        case_id = case_item["case_id"]

        # Results
        res_resp = client.get(f"/api/v1/therapist/cases/{case_id}/results", headers=headers)
        assert res_resp.status_code == 200
        res_json = res_resp.json()
        assert res_json["results_available"] is True
        assert res_json["specialists"]["behav_blocked"] is True

        # Sessions
        sess_resp = client.get(f"/api/v1/therapist/cases/{case_id}/sessions", headers=headers)
        assert sess_resp.status_code == 200
        assert len(sess_resp.json()) == 3

        # Alerts
        alert_resp = client.get(f"/api/v1/therapist/cases/{case_id}/alerts", headers=headers)
        assert alert_resp.status_code == 200

        # Insights
        ins_resp = client.get(f"/api/v1/therapist/cases/{case_id}/insights", headers=headers)
        assert ins_resp.status_code == 200
        assert "factors" in ins_resp.json()
        assert "disclaimer" in ins_resp.json()

        # Recommendations
        rec_resp = client.get(f"/api/v1/therapist/cases/{case_id}/recommendations", headers=headers)
        assert rec_resp.status_code == 200
        assert "recommendations" in rec_resp.json()

        # Safety Protocol
        safety_resp = client.get(f"/api/v1/therapist/cases/{case_id}/safety-protocol", headers=headers)
        assert safety_resp.status_code == 200
        safety_data = safety_resp.json()
        assert "alert_id" in safety_data
        assert "alert_triggered" in safety_data
        assert "recommended_action" in safety_data
