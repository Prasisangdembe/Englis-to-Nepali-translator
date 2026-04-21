def test_submit_feedback_success(client):
    response = client.post(
        "/api/feedback",
        json={
            "english": "hello",
            "suggested_limbu": "sewaro",
            "comment": "Looks accurate",
        },
    )
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["success"] is True
    assert payload["feedback"]["id"] == 1
    assert payload["feedback"]["status"] == "received"


def test_submit_feedback_validation_error(client):
    response = client.post(
        "/api/feedback",
        json={"english": "hello"},
    )
    assert response.status_code == 400

    payload = response.get_json()
    assert payload["success"] is False
    assert "required" in payload["error"].lower()


def test_get_feedback_returns_submissions(client):
    client.post(
        "/api/feedback",
        json={"english": "sun", "suggested_limbu": "nam", "comment": "Good"},
    )
    client.post(
        "/api/feedback",
        json={"english": "moon", "suggested_limbu": "la", "comment": "Correct"},
    )

    response = client.get("/api/feedback")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["success"] is True
    assert payload["count"] == 2
    assert len(payload["feedback"]) == 2
