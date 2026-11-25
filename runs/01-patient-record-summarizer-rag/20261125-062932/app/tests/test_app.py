import sys
from pathlib import Path
# ensure project root is on sys.path so 'app' package can be imported
project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from fastapi.testclient import TestClient
from app.main import app

class DummyStore:
    def __init__(self):
        self.called = False
    def ensure_indexes(self):
        pass
    def query_by_patient_and_rerank(self, patient_id, query_embedding, top_k=5):
        # return deterministic fake results
        return [{"doc_id":"doc1","chunk_id":"c1","score":0.9,"excerpt":"important clinical finding"}]

@pytest.fixture(autouse=True)
def patch_store(monkeypatch):
    from app import main
    ds = DummyStore()
    monkeypatch.setattr(main, "store", ds)
    return ds

client = TestClient(app)

def test_search_returns_answer_and_sources():
    resp = client.post("/search", json={"patientId":"patient_1","question":"What is the cardiology history?","top_k":3})
    assert resp.status_code == 200
    j = resp.json()
    assert "answer" in j
    assert isinstance(j["sources"], list)
    assert j["debug"]["retrieved_count"] == 1

def test_search_bad_request():
    resp = client.post("/search", json={"patientId":"","question":""})
    assert resp.status_code == 400
