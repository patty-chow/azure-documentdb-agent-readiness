import pytest
from fastapi.testclient import TestClient
from app.main import app
import app.db as dbmod
from datetime import datetime


class FakeCollection:
    def __init__(self):
        self.docs = []
    def create_index(self, *args, **kwargs):
        return "idx"
    def bulk_write(self, ops, ordered=False):
        # emulate performing upserts by replacing or appending
        for up in ops:
            filt = up._filter
            doc = up._doc['$set']
            found = None
            for i, d in enumerate(self.docs):
                if all(d.get(k)==v for k,v in filt.items()):
                    self.docs[i] = doc
                    found = True
                    break
            if not found:
                self.docs.append(doc)
        class Res:
            def __init__(self, n):
                self.n = n
        return Res(len(ops))
    def find(self, q):
        # simple filter
        return [d for d in self.docs if all(d.get(k)==v for k,v in q.items())]


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    fake = FakeCollection()
    monkeypatch.setattr(dbmod, 'get_collection', lambda name: fake)
    return fake


def test_ingest_and_get_chain(patch_db):
    client = TestClient(app)
    payload = {
        "underlying": "TEST",
        "expiry": "2026-12-17",
        "options": [
            {"strike": 10, "optionType": "call", "bid": 1.0, "ask": 1.1},
            {"strike": 5, "optionType": "put", "bid": 0.5, "ask": 0.6}
        ]
    }
    r = client.post("/ingest", json=payload)
    assert r.status_code == 200
    res = client.get('/chains?underlying=TEST&expiry=2026-12-17')
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['strike'] == 5
