import aiomysql
import pytest

from network_api import database
from network_api.database import create_tables


@pytest.fixture
async def db_connection_pool():
    pool = await database.create_pool()

    async with pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await create_tables(cursor, reset=True)

    yield pool

    pool.close()
    await pool.wait_closed()


@pytest.fixture
async def db_connection(db_connection_pool):
    async with db_connection_pool.acquire() as connection:
        yield connection


@pytest.fixture
async def db_cursor(db_connection) -> aiomysql.DictCursor:
    async with db_connection.cursor(aiomysql.DictCursor) as cursor:
        yield cursor
