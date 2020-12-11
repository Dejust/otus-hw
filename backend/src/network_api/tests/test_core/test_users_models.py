import pydantic
import pytest
from pydantic import SecretStr

from network_api.core.users.models import User, Credentials, HashedCredentials, Profile

from network_api.tests.utils import faker, build_user


def test_create_user():
    _ = build_user()


@pytest.mark.parametrize('attributes', (
    {'first_name': ''},
    {'first_name': 'a' * (255 + 1)},

    {'last_name': ''},
    {'last_name': 'a' * (255 + 1)},

    {'city': 'a' * (255 + 1)},
    {'city': ''},

    {'interests': 'a' * (512 + 1)},

    {'gender': 'a'},
    {'gender': 'aa'},
    {'gender': ''},

    {'age': 100},
    {'age': 0},
    {'age': -1},

    {'age': '50'}
))
def test_profile(attributes):
    with pytest.raises(pydantic.ValidationError):
        _ = Profile(**attributes)


def test_add_user_credentials():
    user = build_user()
    credentials = Credentials(email=faker.email(), password=faker.password())

    hashed_credentials = user.add_credentials(credentials)

    assert isinstance(user.credentials, HashedCredentials)
    assert user.credentials == hashed_credentials

    assert user.credentials.check_password_valid(credentials.password) is True
    assert user.credentials.check_password_valid(SecretStr('invalid-password')) is False
