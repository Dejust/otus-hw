import pydantic
import pytest

from network_api.core.friends.models import Friend
from network_api.tests.utils import build_user


def test_create_friend():
    user_a = build_user()
    user_b = build_user()

    friend = Friend(source_user=user_a, target_user=user_b)

    assert friend.source_user == user_a
    assert friend.target_user == user_b


def test_user_cant_be_friend_with_itself():
    user_a = build_user()

    with pytest.raises(pydantic.ValidationError):
        Friend(source_user=user_a, target_user=user_a)
