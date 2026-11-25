import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_cross_sell_empty_basket():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post('/cross-sell', json={'basket': []})
        assert r.status_code == 400

# The integration style behavior (with DB) is covered by seed and manual run; unit tests that require DB are omitted here.
