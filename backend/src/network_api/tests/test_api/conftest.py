import pytest
from starlette.requests import Request
from starlette.testclient import TestClient

from network_api.api.app import get_application
from network_api.api.deps import get_db_pool


@pytest.fixture
def api_client(db_connection_pool) -> TestClient:
    app = get_application()

    def _get_db_pool(request: Request):
        return db_connection_pool

    app.dependency_overrides[get_db_pool] = _get_db_pool
    return TestClient(app)
