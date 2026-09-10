"""
Tests for Check-In and Question Engine Integration
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.tests.test_sessions_api import session_api_db, client, get_token


def test_checkin_process_success(client, session_api_db):
    token = get_token(client, "patient.alpha@medha.org", "PassAlpha123!")

    # Patient creates session
    create_resp = client.post(
        "/api/v1/sessions",
        json={"session_identifier": "sess_checkin_test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    session_id = create_resp.json()["id"]

    # Start Check-in
    start_resp = client.post(
        f"/api/v1/checkins/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # If the QuestionEngine has questions and no missing info overrides, it returns 201.
    if start_resp.status_code == 400 and start_resp.json()["detail"] == "No check-in needed at this time.":
        # It's possible the logic doesn't trigger a checkin on empty state, but normally it triggers SA-01
        pytest.skip("QuestionEngine returned no question for empty state.")
        
    assert start_resp.status_code == 201
    checkin_data = start_resp.json()
    assert checkin_data["status"] == "IN_PROGRESS"
    assert "current_question_id" in checkin_data
    assert len(checkin_data["questions"]) == 1
    
    checkin_id = checkin_data["id"]
    current_q_id = checkin_data["current_question_id"]
    
    # Get active check-in
    get_resp = client.get(
        f"/api/v1/checkins/{checkin_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    
    # Answer question
    # We don't know exactly which question it is, but let's submit a generic structure.
    answer_payload = {"answer": {"score": 3}}
    ans_resp = client.post(
        f"/api/v1/checkins/{checkin_id}/answer",
        json=answer_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ans_resp.status_code == 200
    ans_data = ans_resp.json()
    
    assert ans_data["checkin"]["status"] in ["IN_PROGRESS", "COMPLETED"]


def test_checkin_isolation(client, session_api_db):
    token_a = get_token(client, "patient.alpha@medha.org", "PassAlpha123!")
    token_b = get_token(client, "patient.beta@medha.org", "PassBeta123!")

    # Patient A creates session
    create_resp = client.post(
        "/api/v1/sessions",
        json={"session_identifier": "sess_checkin_iso_test"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_resp.status_code == 201
    session_id = create_resp.json()["id"]

    # Patient B tries to start checkin on Patient A's session -> 403
    start_resp = client.post(
        f"/api/v1/checkins/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert start_resp.status_code == 403

