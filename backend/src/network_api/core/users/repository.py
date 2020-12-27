from aiomysql import DictCursor
from pymysql import IntegrityError

from network_api.core.users.models import User, HashedCredentials, Profile, SearchCriteria, default_search_criteria, \
    Page, default_page


class UserRepository:
    class NotFound(Exception):
        pass

    class UserWithThisEmailAlreadyExists(Exception):
        pass

    def __init__(self, db_cursor: DictCursor):
        self._db_cursor = db_cursor

    async def register(self, user: User) -> User:
        query = 'INSERT INTO users (%s) VALUES (%s);'
        data = {}

        if user.credentials:
            data.update(user.credentials.dict())

        if user.profile:
            data.update(user.profile.dict())

        query = query % (
            ', '.join(data.keys()),
            ', '.join((f'%({key})s' for key in data.keys()))
        )

        if 'age' in data:
            data['age'] = int(data['age'])

        try:
            await self._db_cursor.execute(query, data)
        except IntegrityError:
            raise self.UserWithThisEmailAlreadyExists

        user.id = self._db_cursor.lastrowid
        return user

    async def get(self, pk) -> User:
        await self._db_cursor.execute('SELECT * FROM users WHERE id = %(pk)s', {'pk': int(pk)})
        row = await self._db_cursor.fetchone()

        if row is None:
            raise self.NotFound()

        return map_user(row)

    async def get_by_email(self, email):
        await self._db_cursor.execute('SELECT * FROM users WHERE email = %(email)s', {'email': email})
        row = await self._db_cursor.fetchone()
        if row is None:
            raise self.NotFound()
        return map_user(row)


def map_user(row: dict) -> User:
    return User(id=row['id'], credentials=_map_credentials(row), profile=_map_profile(row))


def _map_credentials(row):
    if row['email'] is None:
        return None

    return HashedCredentials(**row)


def _map_profile(row):
    if row['first_name'] is None:
        return None

    return Profile(**row)
