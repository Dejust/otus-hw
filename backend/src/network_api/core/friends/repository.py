from aiomysql import DictCursor
from pymysql import IntegrityError

from network_api.core.friends.models import Friend
from network_api.core.users.repository import map_user


class FriendsRepository:
    class NotFound(Exception):
        pass

    class FriendAlreadyExists(Exception):
        pass

    def __init__(self, db_cursor: DictCursor):
        self._db_cursor = db_cursor

    async def add(self, friend: Friend) -> Friend:
        try:
            await self._db_cursor.execute(
                'INSERT INTO friends (source_user_id, target_user_id) '
                'VALUES (%(source_id)s, %(target_id)s), (%(target_id)s, %(source_id)s);',
                {'source_id': friend.source_user.id, 'target_id': friend.target_user.id}
            )
        except IntegrityError:
            raise self.FriendAlreadyExists()

        return friend

    async def delete(self, friend: Friend):
        await self._db_cursor.execute(
            'DELETE FROM friends WHERE source_user_id = %(source_id)s AND target_user_id = %(target_id)s'
            ' OR source_user_id = %(target_id)s AND target_user_id = %(source_id)s;',
            {'source_id': friend.source_user.id, 'target_id': friend.target_user.id}
        )

    async def get(self, source_user_id, target_user_id) -> Friend:
        await self._db_cursor.execute("""
            SELECT 
                *
            FROM friends 
            INNER JOIN users as source_user ON source_user.id = friends.source_user_id
            INNER JOIN users as target_user ON target_user.id = friends.target_user_id
            WHERE friends.source_user_id = %s AND friends.target_user_id = %s
        """, [source_user_id, target_user_id])

        row = await self._db_cursor.fetchone()

        if row is None:
            raise self.NotFound()

        return map_friend(row)

    async def get_all(self, source_user_id):
        await self._db_cursor.execute("""
            SELECT 
                source_user.*,
                target_user.*
            FROM friends 
            INNER JOIN users as source_user ON source_user.id = friends.source_user_id
            INNER JOIN users as target_user ON target_user.id = friends.target_user_id
            WHERE friends.source_user_id = %s
        """, [source_user_id])

        rows = await self._db_cursor.fetchall()

        return [map_friend(row) for row in rows]


def map_friend(row: dict) -> Friend:
    source_user = {
        key.split('.')[-1]: value
        for key, value in row.items() if not key.startswith('target_user.')
    }

    target_user = {
        key.split('.')[-1]: value
        for key, value in row.items() if key.startswith('target_user.')
    }

    return Friend(source_user=map_user(source_user), target_user=map_user(target_user))
