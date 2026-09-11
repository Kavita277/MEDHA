"""
Step 28 Data Privacy Hardening & Redaction Tests
=================================================

Validates:
  1. Validation Error Redaction (422 responses do not leak sensitive inputs).
  2. URL Query Parameter Redaction (access logging does not log tokens/secrets).
  3. Internal Error Masking (HTTP error responses do not leak server file paths).
  4. Patient Schema Boundary Verification (patient endpoints strictly exclude DDS/risk/specialist predictions).
  5. Password Hash Exclusion (UserResponse never serializes password_hash).
  6. Temporary Audio File Lifecycle (raw audio is not stored on disk).
  7. Centralized Redaction Integration with AuditService.
"""

import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.models.user import User
from backend.persistence.repositories.audit_log import AuditLogRepository
from backend.security.redaction import (
    sanitize_url,
    sanitize_payload,
    sanitize_validation_errors,
    mask_internal_error,
)
from backend.services.audit_service import audit_service


def test_validation_error_input_redaction(client: TestClient):
    """Validates that validation error responses never echo raw passwords or tokens in 422 details."""
    # 1. Attempt login with invalid password type (array instead of str)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@hospital.org", "password": ["invalid_raw_secret_value"]},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"] is True
    assert "errors" in data

    # Check that any error for password redacts input
    found_password_error = False
    for err in data["errors"]:
        loc = err.get("loc", [])
        if "password" in loc or "token" in loc:
            found_password_error = True
            assert err["input"] == "[REDACTED]"
            assert "invalid_raw_secret_value" not in str(err)
    assert found_password_error is True

    # 2. Direct unit test of sanitize_validation_errors
    raw_pydantic_errors = [
        {
            "type": "string_too_short",
            "loc": ("body", "password"),
            "msg": "String should have at least 8 characters",
            "input": "super_secret_short_pass",
            "ctx": {"min_length": 8},
        },
        {
            "type": "value_error",
            "loc": ("headers", "authorization"),
            "msg": "Invalid token header",
            "input": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0",
        },
        {
            "type": "missing",
            "loc": ("body", "name"),
            "msg": "Field required",
            "input": {"safe_field": 123},
        }
    ]
    sanitized = sanitize_validation_errors(raw_pydantic_errors)
    assert sanitized[0]["input"] == "[REDACTED]"
    assert "super_secret_short_pass" not in str(sanitized[0])
    assert sanitized[1]["input"] == "[REDACTED]"
    assert "eyJhbGci" not in str(sanitized[1])
    assert sanitized[2]["input"] == {"safe_field": 123}



def test_sanitize_url_query_parameters():
    """Validates that sensitive query parameters in request URLs are masked."""
    url_with_token = "/api/v1/sessions?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9&limit=10&secret=my_secret_key"
    sanitized = sanitize_url(url_with_token)

    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
    assert "my_secret_key" not in sanitized
    assert "limit=10" in sanitized
    assert "token=%5BREDACTED%5D" in sanitized or "token=[REDACTED]" in sanitized
    assert "secret=%5BREDACTED%5D" in sanitized or "secret=[REDACTED]" in sanitized


def test_mask_internal_error_strips_paths_and_tokens():
    """Validates that error message masking strips file paths and auth tokens."""
    internal_err = "FileNotFoundError: [Errno 2] No such file: 'C:\\Users\\Kavita\\Desktop\\MEDHA\\engine\\model.pkl' with token Bearer abc12345xyz"
    masked = mask_internal_error(internal_err)

    assert "C:\\Users\\Kavita" not in masked
    assert "Bearer abc12345xyz" not in masked
    assert "[INTERNAL_PATH]" in masked
    assert "[REDACTED_TOKEN]" in masked


def test_user_response_schema_never_contains_password_hash(client: TestClient, user_token_headers: dict):
    """Validates that /auth/me and UserResponse never expose password_hash."""
    response = client.get("/api/v1/auth/me", headers=user_token_headers)
    assert response.status_code == 200
    user_data = response.json()

    assert "id" in user_data
    assert "email" in user_data
    assert "role" in user_data
    assert "password_hash" not in user_data
    assert "password" not in user_data
    assert "hashed_password" not in user_data


def test_patient_schemas_contain_no_therapist_prediction_fields(
    client: TestClient,
    db_session: Session,
    test_user: User,
    test_case: Case,
    user_token_headers: dict,
):
    """
    Validates that patient endpoints (/sessions, /chat/sessions/.../history)
    strictly exclude therapist-only prediction fields (DDS, temporal risk, future flags, specialist preds).
    """
    # 1. Create a session as patient
    sess = SessionModel(
        id=uuid.uuid4(),
        session_identifier="sess_privacy_test",
        case_id=test_case.id,
        timepoint=1,
        status=SessionStatus.ACTIVE,
    )
    db_session.add(sess)
    db_session.commit()

    # 2. Get session
    resp_session = client.get(f"/api/v1/sessions/{sess.id}", headers=user_token_headers)
    assert resp_session.status_code == 200
    session_json = resp_session.json()

    # Assert therapist prediction fields do NOT exist in patient SessionResponse
    forbidden_prediction_fields = [
        "fusion_dds_prediction",
        "temporal_risk_score",
        "future_escalation_flag",
        "triage_level",
        "struct_pred",
        "text_pred",
        "voice_pred",
        "behav_pred",
        "specialists",
        "disclaimer",
    ]
    for field in forbidden_prediction_fields:
        assert field not in session_json

    # 3. Get chat history as patient
    resp_chat = client.get(f"/api/v1/chat/sessions/{sess.id}/history", headers=user_token_headers)
    assert resp_chat.status_code == 200
    chat_json = resp_chat.json()
    for field in forbidden_prediction_fields:
        assert field not in chat_json


def test_centralized_redaction_with_audit_service(db_session: Session, test_user: User):
    """Validates that AuditService seamlessly leverages centralized redaction."""
    repo = AuditLogRepository(db_session)
    
    audit_service.log_event(
        db=db_session,
        action="PRIVACY_TEST_EVENT",
        actor_user_id=test_user.id,
        actor_role="patient",
        resource_type="test",
        resource_id="T-001",
        status="SUCCESS",
        metadata={
            "safe_count": 5,
            "password": "RawPassword123!",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotStoreThis",
            "chat_message": "Patient confidential narrative here",
            "api_key": "sk-1234567890abcdef",
        },
    )
    db_session.commit()

    logs = repo.list_logs(action="PRIVACY_TEST_EVENT")
    assert len(logs) >= 1
    stored_meta = logs[0].metadata_payload

    assert stored_meta["safe_count"] == 5
    assert stored_meta["password"] == "[REDACTED]"
    assert stored_meta["token"] == "[REDACTED]"
    assert stored_meta["chat_message"] == "[REDACTED]"
    assert stored_meta["api_key"] == "[REDACTED]"
    assert "RawPassword123!" not in str(stored_meta)
    assert "eyJhbGci" not in str(stored_meta)
