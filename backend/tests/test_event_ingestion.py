"""
Tests for Behaviour Event Ingestion
"""

import uuid
from datetime import datetime, timezone
import pytest

from backend.tests.test_sessions_api import session_api_db, client, get_token

def test_event_ingestion_success_and_idempotency(client, session_api_db):
    token = get_token(client, "patient.alpha@medha.org", "PassAlpha123!")
    case_id = session_api_db["case_a_id"]
    
    event_id = str(uuid.uuid4())
    
    payload = {
        "events": [
            {
                "event_id": event_id,
                "case_id": case_id,
                "event_type": "screen_view",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "metadata_payload": {"screen": "dashboard"}
            }
        ]
    }
    
    # 1. Successful insert
    resp1 = client.post(
        "/api/v1/events/batch",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["status"] == "success"
    assert data1["received_count"] == 1
    assert data1["processed_count"] == 1
    assert data1["ignored_duplicate_count"] == 0
    
    # 2. Idempotent duplicate insert
    resp2 = client.post(
        "/api/v1/events/batch",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["received_count"] == 1
    assert data2["processed_count"] == 0
    assert data2["ignored_duplicate_count"] == 1


def test_event_ingestion_isolation(client, session_api_db):
    token_b = get_token(client, "patient.beta@medha.org", "PassBeta123!")
    case_a_id = session_api_db["case_a_id"]
    
    payload = {
        "events": [
            {
                "event_id": str(uuid.uuid4()),
                "case_id": case_a_id,
                "event_type": "screen_view",
                "occurred_at": datetime.now(timezone.utc).isoformat()
            }
        ]
    }
    
    # Patient B tries to submit event for Patient A's case
    resp = client.post(
        "/api/v1/events/batch",
        json=payload,
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert resp.status_code == 403

def test_event_ingestion_therapist_isolation(client, session_api_db):
    token_t_b = get_token(client, "dr.beta@medha.org", "DocBeta123!")
    case_a_id = session_api_db["case_a_id"]
    
    payload = {
        "events": [
            {
                "event_id": str(uuid.uuid4()),
                "case_id": case_a_id,
                "event_type": "screen_view",
                "occurred_at": datetime.now(timezone.utc).isoformat()
            }
        ]
    }
    
    # Therapist B tries to submit event for Therapist A's case (Patient A)
    resp = client.post(
        "/api/v1/events/batch",
        json=payload,
        headers={"Authorization": f"Bearer {token_t_b}"}
    )
    assert resp.status_code == 403
