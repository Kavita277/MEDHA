"""
Tests for Chatbot Integration
=============================
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.tests.test_sessions_api import session_api_db, client, get_token


def test_chatbot_process_message_success(client, session_api_db):
    token = get_token(client, "patient.alpha@medha.org", "PassAlpha123!")

    # Patient creates session
    create_resp = client.post(
        "/api/v1/sessions",
        json={"session_identifier": "sess_chat_test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    session_id = create_resp.json()["id"]

    # Send a message
    msg_resp = client.post(
        f"/api/v1/chat/sessions/{session_id}/message",
        json={"message": "I am feeling a bit anxious today."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert msg_resp.status_code == 200
    msg_data = msg_resp.json()

    assert msg_data["user_message"] == "I am feeling a bit anxious today."
    assert "assistant_response" in msg_data
    assert msg_data["turn_index"] == 1
    
    # Check history
    hist_resp = client.get(
        f"/api/v1/chat/sessions/{session_id}/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert len(hist_data["messages"]) == 2
    assert hist_data["messages"][0]["role"] == "user"
    assert hist_data["messages"][0]["content"] == "I am feeling a bit anxious today."
    assert hist_data["messages"][1]["role"] == "assistant"
    assert hist_data["messages"][1]["content"] == msg_data["assistant_response"]


def test_chatbot_isolation(client, session_api_db):
    token_a = get_token(client, "patient.alpha@medha.org", "PassAlpha123!")
    token_b = get_token(client, "patient.beta@medha.org", "PassBeta123!")

    # Patient A creates session
    create_resp = client.post(
        "/api/v1/sessions",
        json={"session_identifier": "sess_chat_isolation"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    session_id = create_resp.json()["id"]

    # Patient B tries to send message to Patient A's session -> 403
    msg_resp = client.post(
        f"/api/v1/chat/sessions/{session_id}/message",
        json={"message": "Hello"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert msg_resp.status_code == 403

    # Patient B tries to get history -> 403
    hist_resp = client.get(
        f"/api/v1/chat/sessions/{session_id}/history",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert hist_resp.status_code == 403
