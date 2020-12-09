from functools import partial
from typing import List

from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from pydantic import BaseModel

from network_api import jwt
from network_api.api.deps import setup_db, close_db, get_users_repository, get_friends_repository
from network_api.core.friends.models import Friend
from network_api.core.friends.repository import FriendsRepository
from network_api.core.users.models import Credentials, Profile, User, SearchCriteria
from network_api.core.users.repository import UserRepository

auth = APIRouter()
users = APIRouter()


class RegisterRequest(BaseModel):
    credentials: Credentials
    profile: Profile


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_logged_user(
    token: str = Depends(oauth2_scheme),
    users_repository: UserRepository = Depends(get_users_repository)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token)
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception

        try:
            user = await users_repository.get(user_id)
        except users_repository.NotFound:
            raise credentials_exception

        return user

    except PyJWTError:
        raise credentials_exception


@auth.post('/register')
async def auth_register(register_request: RegisterRequest,
                        users_repository: UserRepository = Depends(get_users_repository)):
    user = User(profile=register_request.profile)
    user.add_credentials(register_request.credentials)
    try:
        user = await users_repository.register(user)
    except users_repository.UserWithThisEmailAlreadyExists:
        raise HTTPException(status_code=409, detail='User with this email already exists.')
    return {'token': jwt.create(user.id)}


@auth.post('/login')
async def auth_login(credentials: Credentials, users_repository: UserRepository = Depends(get_users_repository)):
    try:
        user = await users_repository.get_by_email(credentials.email)
    except users_repository.NotFound:
        raise HTTPException(status_code=401)

    if not user.credentials.check_password_valid(credentials.password):
        raise HTTPException(status_code=401)

    return {'token': jwt.create(user.id)}


@users.get('/')
async def get_users(
    first_name_prefix: str = None, last_name_prefix: str = None,
    users_repository: UserRepository = Depends(get_users_repository)
) -> List[User]:
    criteria = SearchCriteria(first_name_prefix=first_name_prefix, last_name_prefix=last_name_prefix)
    user_list = await users_repository.get_all(criteria=criteria)
    return user_list


@users.get('/{user_id}')
async def get_user(user_id: int, users_repository: UserRepository = Depends(get_users_repository)) -> User:
    try:
        user = await users_repository.get(user_id)
    except users_repository.NotFound:
        raise HTTPException(status_code=404)

    return user


class FriendRequest(BaseModel):
    target_user_id: int


@users.post('/{user_id}/friends')
async def add_friend(
    user_id: int,
    friend_request: FriendRequest,
    logged_user: User = Depends(get_logged_user),
    users_repository: UserRepository = Depends(get_users_repository),
    friends_repository: FriendsRepository = Depends(get_friends_repository)
):
    if logged_user.id != user_id:
        raise HTTPException(status_code=403)

    source_user = await users_repository.get(user_id)
    target_user = await users_repository.get(friend_request.target_user_id)

    friend = Friend(source_user=source_user, target_user=target_user)
    try:
        return await friends_repository.add(friend)
    except friends_repository.FriendAlreadyExists:
        raise HTTPException(status_code=409)


@users.delete('/{source_user_id}/friends/{target_user_id}')
async def delete_friend(
    source_user_id: int,
    target_user_id: int,
    logged_user: User = Depends(get_logged_user),
    friends_repository: FriendsRepository = Depends(get_friends_repository)
):
    if logged_user.id != source_user_id:
        raise HTTPException(status_code=403)

    try:
        friend = await friends_repository.get(source_user_id, target_user_id)
    except friends_repository.NotFound:
        raise HTTPException(status_code=204)

    await friends_repository.delete(friend)

    raise HTTPException(status_code=204)


@users.get('/{source_user_id}/friends')
async def get_friends(
    source_user_id: int,
    friends_repository: FriendsRepository = Depends(get_friends_repository)
):
    return await friends_repository.get_all(source_user_id)


def get_application() -> FastAPI:
    app = FastAPI()

    app.add_event_handler('startup', partial(setup_db, app))
    app.add_event_handler('shutdown', partial(close_db, app))

    app.include_router(auth, prefix='/auth')
    app.include_router(users, prefix='/users')

    return app
