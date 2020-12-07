from pydantic import BaseModel, validator

from network_api.core.users.models import User


class Friend(BaseModel):
    source_user: User
    target_user: User

    @validator('target_user')
    def user_cant_be_friend_with_itself(cls, value, values, **kwargs):
        if value == values['source_user']:
            raise ValueError("User can't be friend with itself.")
        return value
