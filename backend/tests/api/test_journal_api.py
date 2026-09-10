import uuid

def test_create_and_list_journal_entry(client, user_token_headers, db_session, test_user, test_case):
    # 1. Create entry
    response = client.post(
        "/api/v1/journal",
        headers=user_token_headers,
        json={"content": "I feel much better today after the breathing exercise."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "I feel much better today after the breathing exercise."
    assert data["case_id"] == str(test_case.id)
    entry_id = data["id"]

    # 2. List entries
    response = client.get(
        "/api/v1/journal",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data_list = response.json()
    assert len(data_list["entries"]) >= 1
    assert any(e["id"] == entry_id for e in data_list["entries"])

def test_get_and_update_journal_entry(client, user_token_headers, db_session, test_user, test_case):
    # Setup: create entry
    create_resp = client.post(
        "/api/v1/journal",
        headers=user_token_headers,
        json={"content": "Initial thought."}
    )
    entry_id = create_resp.json()["id"]

    # Get entry
    get_resp = client.get(
        f"/api/v1/journal/{entry_id}",
        headers=user_token_headers
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["content"] == "Initial thought."

    # Update entry
    update_resp = client.patch(
        f"/api/v1/journal/{entry_id}",
        headers=user_token_headers,
        json={"content": "Updated thought."}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["content"] == "Updated thought."
