def test_root_returns_health_message(api_client):
    client, _ = api_client

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
