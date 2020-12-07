import pytest

from network_api.core.friends.models import Friend
from network_api.core.friends.repository import FriendsRepository
from network_api.core.users.models import User

pytestmark = pytest.mark.asyncio


@pytest.fixture
def friends_repository(db_cursor):
    return FriendsRepository(db_cursor)


async def test_add_friend(user_repository, friends_repository, db_cursor):
    user_a = await user_repository.register(User())
    user_b = await user_repository.register(User())

    friend = Friend(source_user=user_a, target_user=user_b)
    actual_friend = await friends_repository.add(friend)

    assert friend == actual_friend

    actual_friends = await friends_repository.get_all(user_a.id)

    assert actual_friends == [friend]


async def test_get_friends(user_repository, friends_repository):
    user_a = await user_repository.register(User())
    user_b = await user_repository.register(User())
    user_c = await user_repository.register(User())
    friend_1 = await friends_repository.add(Friend(source_user=user_a, target_user=user_b))
    friend_2 = await friends_repository.add(Friend(source_user=user_a, target_user=user_c))
    friends = await friends_repository.get_all(user_a.id)
    assert friends == [friend_1, friend_2]
