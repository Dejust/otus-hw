import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize('table_name', (
        'users',
        'friends'
))
async def test_table_exists(table_name, db_cursor):
    await db_cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    row = await db_cursor.fetchone()
    assert row is not None
