def test_get_root(api_client):
    response = api_client.get('/')
    assert response.status_code == 404
