from aiomysql import DictCursor

from network_api.core.users.models import SearchCriteria, default_search_criteria, Page, default_page


class UserView:
    def __init__(self, db_cursor: DictCursor):
        self._db_cursor = db_cursor

    async def get_all(self, *, criteria: SearchCriteria = default_search_criteria, page: Page = default_page):
        query = 'SELECT id, first_name, last_name FROM users'

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
        return rows

    @classmethod
    def _search_criteria_to_query(self, criteria: SearchCriteria):
        criteria_query = []
        params = {}

        if criteria.last_name_prefix and criteria.first_name_prefix:
            criteria_query.append('last_name LIKE %(last_name_prefix)s')
            params['last_name_prefix'] = criteria.last_name_prefix + '%'

        if criteria.first_name_prefix:
            criteria_query.append('first_name LIKE %(first_name_prefix)s')
            params['first_name_prefix'] = criteria.first_name_prefix + '%'

        if criteria_query:
            return ' AND '.join(criteria_query), params
        else:
            return None
