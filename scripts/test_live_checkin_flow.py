import requests

def test_checkin_flow():
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # 1. Login
    login_resp = requests.post(f"{base_url}/auth/login", json={
        "email": "ananya.sharma@medha.org",
        "password": "PatientPass123!"
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[1] Logged in successfully.")

    # 2. Create Session
    sess_resp = requests.post(f"{base_url}/sessions", headers=headers)
    assert sess_resp.status_code in (200, 201), f"Session creation failed: {sess_resp.text}"
    session_id = sess_resp.json()["id"]
    print(f"[2] Created session: {session_id}")

    # 3. Start Check-in (calls Question Engine)
    chk_resp = requests.post(f"{base_url}/checkins/sessions/{session_id}", headers=headers)
    assert chk_resp.status_code == 201, f"Check-in start failed: {chk_resp.text}"
    chk = chk_resp.json()
    q1 = chk["questions"][0]
    print(f"[3] Check-in started: ID {chk['id']}")
    print(f"    Question 1: [{q1['question_id']}] \"{q1['question_text']}\"")

    # 4. Answer Question 1
    ans_resp = requests.post(f"{base_url}/checkins/{chk['id']}/answer", headers=headers, json={
        "answer": {"value": 2}
    })
    assert ans_resp.status_code == 200, f"Answer submit failed: {ans_resp.text}"
    ans_data = ans_resp.json()
    next_q = ans_data.get("next_question")
    if next_q:
        print(f"[4] Answered Q1. Next question from Question Engine: [{next_q['question_id']}] \"{next_q['question_text']}\"")
        # Answer Question 2
        ans2_resp = requests.post(f"{base_url}/checkins/{chk['id']}/answer", headers=headers, json={
            "answer": {"value": 1}
        })
        assert ans2_resp.status_code == 200
        print("[4b] Answered Q2.")
    else:
        print("[4] Answered Q1. No further questions required by policy.")

    # 5. Complete Check-in
    comp_resp = requests.post(f"{base_url}/checkins/{chk['id']}/complete", headers=headers)
    assert comp_resp.status_code == 200, f"Check-in complete failed: {comp_resp.text}"
    print(f"[5] Check-in completed successfully! Status: {comp_resp.json()['status']}")
    print("=== LIVE CHECKIN AND QUESTION ENGINE VERIFIED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_checkin_flow()
