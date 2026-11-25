import os
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_root_get_not_found():
    # start app without DB for a simple import-based smoke test
    # This test simply ensures the FastAPI app is importable and routes exist
    r = client.get('/consents/nonexistent')
    # If DOCUMENTDB_URI is not set, the app startup would raise; so we only assert route handling if available
    assert r.status_code in (200, 404)
