import aiomysql
from aiomysql import DictCursor
from fastapi import Depends, FastAPI
from starlette.requests import Request

from network_api.core.friends.repository import FriendsRepository
from network_api.core.users.repository import UserRepository
from network_api.database import create_pool, create_tables


async def setup_db(app: FastAPI):
    pool = await create_pool()
    app.state.db_pool = pool

    async with pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await create_tables(cursor)


async def close_db(app: FastAPI):
    await app.state.db_pool.close()


def get_db_pool(request: Request):
    return request.app.state.db_pool


async def get_db_connection(db_pool=Depends(get_db_pool)):
    async with db_pool.acquire() as connection:
        yield connection


async def get_db_cursor(db_connection=Depends(get_db_connection)):
    async with db_connection.cursor(aiomysql.DictCursor) as cursor:
        yield cursor


async def get_users_repository(db_cursor: DictCursor = Depends(get_db_cursor)) -> UserRepository:
    yield UserRepository(db_cursor)


async def get_friends_repository(db_cursor: DictCursor = Depends(get_db_cursor)) -> FriendsRepository:
    yield FriendsRepository(db_cursor)
