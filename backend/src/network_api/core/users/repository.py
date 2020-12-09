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

    async def get_all(self, *, criteria: SearchCriteria = default_search_criteria, page: Page = default_page):
        query = 'SELECT * FROM users'

        criteria = self._search_criteria_to_query(criteria)
        if criteria:
            search_query, params = criteria
            query += f' WHERE {search_query}'
        else:
            params = {}

        query += ' LIMIT %(limit)s OFFSET %(offset)s'
        params.update(page.dict())

        await self._db_cursor.execute(query, params)
        rows = await self._db_cursor.fetchall()
        return [map_user(row) for row in rows]

    def _search_criteria_to_query(self, criteria: SearchCriteria = None):
        criteria_query = []
        params = {}
        if criteria.first_name_prefix:
            criteria_query.append('first_name LIKE %(first_name_prefix)s')
            params['first_name_prefix'] = criteria.first_name_prefix + '%'
        if criteria.last_name_prefix:
            criteria_query.append('last_name LIKE %(last_name_prefix)s')
            params['last_name_prefix'] = criteria.last_name_prefix + '%'

        if criteria_query:
            return ' AND '.join(criteria_query), params
        else:
            return None


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
