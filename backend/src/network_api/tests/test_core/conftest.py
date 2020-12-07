import pytest

from network_api.core.users.repository import UserRepository


@pytest.fixture
def user_repository(db_cursor):
    return UserRepository(db_cursor)
