from network_api import jwt
from network_api.tests.test_core.utils import build_profile, build_credentials


def build_register_request():
    profile = build_profile().dict()
    credentials = build_credentials().dict()
    credentials['password'] = credentials['password'].get_secret_value()
    return {
        'profile': profile,
        'credentials': credentials
    }


def register_user(api_client, request):
    return api_client.post('/auth/register', json=request)


def login_user(api_client, request):
    return api_client.post('/auth/login', json=request)


def assert_token_ok(data):
    """Asserts token and returns user id"""
    assert 'token' in data
    token = jwt.decode(data['token'])
    assert 'user_id' in token
    return token['user_id']


def test_register(api_client):
    register_request = build_register_request()
    response = register_user(api_client, register_request)

    assert response.status_code == 200

    assert_token_ok(response.json())


def test_register_twice(api_client):
    register_request = build_register_request()

    response_1 = register_user(api_client, register_request)
    response_2 = register_user(api_client, register_request)

    assert response_1.status_code == 200
    assert response_2.status_code == 409


def test_login(api_client):
    request = build_register_request()
    _ = register_user(api_client, request)

    credentials = request['credentials']
    response = login_user(api_client, credentials)

    assert response.status_code == 200
    assert_token_ok(response.json())


def test_login_with_invalid_email(api_client):
    request = build_register_request()
    response = login_user(api_client, request['credentials'])
    assert response.status_code == 401


def test_login_with_invalid_password(api_client):
    request = build_register_request()
    _ = register_user(api_client, request)

    credentials = request['credentials']
    credentials['password'] += '123456'

    response = login_user(api_client, credentials)
    assert response.status_code == 401


def test_get_users_lists(api_client):
    users = [
        build_register_request(),
        build_register_request(),
        build_register_request()
    ]

    for user in users:
        register_user(api_client, user)

    response = api_client.get('/users')
    assert response.status_code == 200

    actual_users = response.json()

    actual_profiles = [actual_user['profile'] for actual_user in actual_users]
    expected_profiles = [user['profile'] for user in users]

    assert actual_profiles == expected_profiles


def test_get_user_by_id(api_client):
    user = build_register_request()
    response = register_user(api_client, user)
    user_id = assert_token_ok(response.json())

    response = api_client.get(f'/users/{user_id}')
    assert response.status_code == 200
    assert response.json()['profile'] == user['profile']


def test_add_friend(api_client):
    user_a = build_register_request()
    user_b = build_register_request()

    response_a = register_user(api_client, user_a)
    response_b = register_user(api_client, user_b)

    user_a_id = assert_token_ok(response_a.json())
    user_b_id = assert_token_ok(response_b.json())

    user_a_token = response_a.json()['token']

    response = api_client.post(
        f'/users/{user_a_id}/friends',
        json={'target_user_id': user_b_id},
        headers={
            'Authorization': f"Bearer {user_a_token}"
        }
    )

    assert response.status_code == 200
    assert response.json()['source_user']['profile'] == user_a['profile']
    assert response.json()['target_user']['profile'] == user_b['profile']


def test_delete_friend(api_client):
    user_a = build_register_request()
    user_b = build_register_request()

    response_a = register_user(api_client, user_a)
    response_b = register_user(api_client, user_b)

    user_a_id = assert_token_ok(response_a.json())
    user_b_id = assert_token_ok(response_b.json())

    user_a_token = response_a.json()['token']

    response = api_client.post(
        f'/users/{user_a_id}/friends',
        json={'target_user_id': user_b_id},
        headers={
            'Authorization': f"Bearer {user_a_token}"
        }
    )

    assert response.status_code == 200
    assert response.json()['source_user']['profile'] == user_a['profile']
    assert response.json()['target_user']['profile'] == user_b['profile']

    response = api_client.delete(
        f"/users/{user_a_id}/friends/{user_b_id}",
        headers={
            'Authorization': f"Bearer {user_a_token}"
        }
    )

    assert response.status_code == 204


def test_get_friends(api_client):
    user_a = build_register_request()
    user_b = build_register_request()
    user_c = build_register_request()

    response_a = register_user(api_client, user_a)
    response_b = register_user(api_client, user_b)
    response_c = register_user(api_client, user_c)

    user_a_id = assert_token_ok(response_a.json())
    user_b_id = assert_token_ok(response_b.json())
    user_c_id = assert_token_ok(response_c.json())

    user_a_token = response_a.json()['token']

    response_b = api_client.post(
        f'/users/{user_a_id}/friends',
        json={'target_user_id': user_b_id},
        headers={
            'Authorization': f"Bearer {user_a_token}"
        }
    )

    assert response_b.status_code == 200

    response_c = api_client.post(
        f'/users/{user_a_id}/friends',
        json={'target_user_id': user_c_id},
        headers={
            'Authorization': f"Bearer {user_a_token}"
        }
    )

    assert response_c.status_code == 200

    response = api_client.get(f'/users/{user_a_id}/friends')
    assert response.status_code == 200
    assert [x['source_user']['profile'] for x in response.json()] == [user_a['profile']] * 2
    assert [x['target_user']['profile'] for x in response.json()] == [user_b['profile'], user_c['profile']]
