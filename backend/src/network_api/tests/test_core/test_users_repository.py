import pytest

from network_api.core.users.models import User
from network_api.core.users.repository import UserRepository
from network_api.tests.test_core.utils import build_profile, build_credentials

pytestmark = pytest.mark.asyncio


async def test_register_empty_user(user_repository):
    user = await user_repository.register(User())

    assert user.profile is None
    assert user.credentials is None
    assert user.id is not None


async def test_register_user_with_credentials_only(user_repository):
    credentials = build_credentials()

    new_user = User()
    new_user.add_credentials(credentials)

    user = await user_repository.register(new_user)

    assert user.profile is None
    assert user.credentials is not None
    assert user.credentials.email == credentials.email
    assert user.credentials.check_password_valid(credentials.password)
    assert user.id is not None


async def test_register_user_with_profile_only(user_repository):
    profile = build_profile()
    new_user = User(profile=profile)

    user = await user_repository.register(new_user)

    assert user.profile == profile
    assert user.credentials is None
    assert user.id is not None


async def test_register_complete_user(user_repository):
    credentials = build_credentials()
    profile = build_profile()

    new_user = User(profile=profile)
    new_user.add_credentials(credentials)

    user = await user_repository.register(new_user)

    assert user.profile == profile
    assert user.credentials is not None
    assert user.credentials.email == credentials.email
    assert user.credentials.check_password_valid(credentials.password)
    assert user.id is not None


async def test_get_not_existing_user(user_repository):
    with pytest.raises(UserRepository.NotFound):
        await user_repository.get(1)


async def test_get_user(user_repository):
    registered_user = await user_repository.register(User())

    user = await user_repository.get(registered_user.id)
    assert registered_user == user
