import os
import time
import pytest
from fastapi.testclient import TestClient
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1].resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Load seed.py as a module by file path to avoid import path issues
spec = importlib.util.spec_from_file_location("seed_module", str(REPO_ROOT / "seed.py"))
seed_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed_mod)

from app import app

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def run_seed():
    # Run seeding once for the test session
    seed_mod.seed()
    # small wait to ensure server-side indexing tasks settle (if any)
    time.sleep(1)

def test_triage_endpoint_basic():
    payload = {"symptoms": "I have sudden chest pain and shortness of breath"}
    resp = client.post("/triage", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "urgency" in data
    assert "advice" in data
    assert isinstance(data.get("sources", []), list)
