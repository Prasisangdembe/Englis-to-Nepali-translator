def test_translate_endpoint_success(client):
    response = client.post("/api/translate", json={"text": "hello water"})
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["success"] is True
    assert payload["translation"]["translated_romanized"] == "sewaro wa"


def test_translate_endpoint_error_handling(client):
    response = client.post("/api/translate", json={})
    assert response.status_code == 400

    payload = response.get_json()
    assert payload["success"] is False
    assert "text" in payload["error"]


def test_translate_endpoint_rate_limiting(client):
    last_response = None
    for _ in range(11):
        last_response = client.post("/api/translate", json={"text": "hello"})

    assert last_response is not None
    assert last_response.status_code == 429
