import sys
from pathlib import Path

# Ensure repo root in sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from fastapi.testclient import TestClient
from backend.main import create_application

def test_full_integration():
    print("=== Testing MEDHA Frontend Endpoints & ML Integration ===")
    app = create_application()
    client = TestClient(app)

    # 1. Test Therapist Auth & Results Retrieval
    print("\n--- 1. Testing Therapist Auth & Cases ---")
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "demo.therapist@medha.org", "password": "TherapistDemo123!"}
    )
    assert login_resp.status_code == 200, f"Therapist login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    user = login_resp.json()["user"]
    print(f"[OK] Therapist login succeeded. User: {user['name']}, Role: {user['role']}")
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch Cases
    cases_resp = client.get("/api/v1/therapist/cases", headers=headers)
    assert cases_resp.status_code == 200, f"Get cases failed: {cases_resp.text}"
    cases = cases_resp.json()
    print(f"[OK] Retrieved {len(cases)} cases for therapist:")
    for c in cases:
        print(f"   * {c['patient_name']} ({c['victim_id']}), Current Timepoint: T{c['current_timepoint']}")

    # Check Results for each Case
    print("\n--- 2. Testing Case Prediction Results ---")
    for c in cases:
        res_resp = client.get(f"/api/v1/therapist/cases/{c['case_id']}/results", headers=headers)
        assert res_resp.status_code == 200, f"Get results failed: {res_resp.text}"
        res = res_resp.json()
        print(f"[OK] {c['victim_id']} ({c['patient_name']}):")
        print(f"     Triage: {res['triage_level']}")
        print(f"     Fusion DDS: {res['fusion_dds_prediction']}")
        print(f"     Temporal Risk: {res['temporal_risk_score']}, Escalation: {res['future_escalation_flag']}")
        print(f"     Specialists -> Struct: {res['specialists']['struct_pred']}, Text: {res['specialists']['text_pred']}, Voice: {res['specialists']['voice_pred']}")

        # Test Step 25 Insights
        ins_resp = client.get(f"/api/v1/therapist/cases/{c['case_id']}/insights", headers=headers)
        assert ins_resp.status_code == 200, f"Get insights failed: {ins_resp.text}"
        ins = ins_resp.json()
        print(f"     [Insights] Available: {ins['results_available']}, Factors: {len(ins['factors'])}, Summary: {ins['summary'][:50]}...")

        # Test Step 26 Recommendations & Safety Protocol
        rec_resp = client.get(f"/api/v1/therapist/cases/{c['case_id']}/recommendations", headers=headers)
        assert rec_resp.status_code == 200, f"Get recommendations failed: {rec_resp.text}"
        rec = rec_resp.json()
        print(f"     [Recommendations] Count: {len(rec['recommendations'])}, Self-help: {len(rec['self_help_resources'])}")

        sp_resp = client.get(f"/api/v1/therapist/cases/{c['case_id']}/safety-protocol", headers=headers)
        assert sp_resp.status_code == 200, f"Get safety protocol failed: {sp_resp.text}"
        sp = sp_resp.json()
        print(f"     [Safety Protocol] Triggered: {sp['alert_triggered']}, Priority: {sp['priority']}, Action: {sp['recommended_action'][:40]}...")

    # 3. Test Patient Login, Chat, and MuRIL continuous inference
    print("\n--- 3. Testing Patient Auth & Chat Continuous Inference ---")
    pat_login = client.post(
        "/api/v1/auth/login",
        json={"email": "ananya.sharma@medha.org", "password": "PatientPass123!"}
    )
    assert pat_login.status_code == 200, f"Patient login failed: {pat_login.text}"
    pat_token = pat_login.json()["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}
    print("[OK] Patient login succeeded.")

    # Create Session
    sess_resp = client.post("/api/v1/sessions", headers=pat_headers)
    assert sess_resp.status_code in (200, 201), f"Session create failed: {sess_resp.text}"
    session_id = sess_resp.json()["id"]
    print(f"[OK] Created new patient session: {session_id}")

    # Send Chat Message (MEDHA companion response)
    chat_resp = client.post(
        f"/api/v1/chat/sessions/{session_id}/message",
        headers=pat_headers,
        json={"message": "I have been feeling really exhausted and stressed about work lately."}
    )
    assert chat_resp.status_code == 200, f"Chat failed: {chat_resp.text}"
    turn = chat_resp.json()
    print(f"[OK] Chat message processed successfully!")
    print(f"     User sent: \"{turn['user_message']}\"")
    print(f"     MEDHA Companion replied: \"{turn['assistant_response']}\"")
    assert turn["assistant_response"] and len(turn["assistant_response"]) > 0

    # 4. Test Check-in Workflow
    print("\n--- 4. Testing Check-in Flow ---")
    chk_start = client.post(f"/api/v1/checkins/sessions/{session_id}", headers=pat_headers)
    assert chk_start.status_code == 201, f"Check-in start failed: {chk_start.text}"
    chk = chk_start.json()
    print(f"[OK] Check-in started: ID {chk['id']}, initial question: {chk['questions'][0]['question_text']}")

    # Submit answer
    chk_ans = client.post(
        f"/api/v1/checkins/{chk['id']}/answer",
        headers=pat_headers,
        json={"answer": {"value": 2}}
    )
    assert chk_ans.status_code == 200, f"Check-in answer failed: {chk_ans.text}"
    print(f"[OK] Answer submitted successfully. Status: {chk_ans.json()['status']}")

    # Complete check-in
    chk_comp = client.post(f"/api/v1/checkins/{chk['id']}/complete", headers=pat_headers)
    assert chk_comp.status_code == 200, f"Check-in complete failed: {chk_comp.text}"
    print(f"[OK] Check-in completed. Background prediction queue triggered.")

    print("\n=== ALL INTEGRATION ENDPOINTS VERIFIED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_full_integration()
