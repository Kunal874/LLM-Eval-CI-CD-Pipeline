"""Test fixtures for the backend API.

Patches Supabase client to mock all DB calls — no real database connections
are made during testing.
"""

import os
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch

# Set environment variables BEFORE any app imports
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "test-service-key"
os.environ["LLMEVAL_API_KEY"] = "test-key-12345"

from httpx import AsyncClient, ASGITransport
from api.main import app


class MockSupabaseQuery:
    """Chainable mock for Supabase query builder pattern."""

    def __init__(self, data=None, count=None):
        self._data = data if data is not None else []
        self._count = count

    def select(self, *args, **kwargs):
        return self

    def insert(self, data):
        self._pending_insert = data
        return self

    def update(self, data):
        self._pending_update = data
        return self

    def delete(self):
        return self

    def eq(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def range(self, *args, **kwargs):
        return self

    def execute(self):
        result = MagicMock()
        result.data = self._data
        result.count = self._count
        return result


class MockSupabaseTable:
    """Mock for supabase.table() calls with configurable responses."""

    def __init__(self):
        self._responses = {}

    def configure(self, table_name, data=None, count=None):
        """Set up the response for a specific table."""
        self._responses[table_name] = {"data": data or [], "count": count}

    def __call__(self, table_name):
        resp = self._responses.get(table_name, {"data": [], "count": None})
        return MockSupabaseQuery(data=resp["data"], count=resp["count"])


@pytest.fixture
def mock_table():
    """Provide a configurable mock Supabase table."""
    return MockSupabaseTable()


@pytest.fixture
def api_key_headers():
    """Headers with a valid API key for authenticated requests."""
    return {"X-API-Key": "test-key-12345"}


@pytest_asyncio.fixture
async def client(mock_table):
    """Async HTTP test client with mocked Supabase."""
    with patch("api.routers.runs.supabase") as mock_runs_db, \
         patch("api.routers.results.supabase") as mock_results_db, \
         patch("api.routers.cases.supabase") as mock_cases_db:

        # Configure all mocked supabase instances to use the mock_table
        mock_runs_db.table = mock_table
        mock_results_db.table = mock_table
        mock_cases_db.table = mock_table

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as ac:
            yield ac
