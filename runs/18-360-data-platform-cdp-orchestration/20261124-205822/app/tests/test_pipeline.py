import pytest
from unittest.mock import MagicMock
import src.db as db_module

from run_pipeline import Pipeline


class DummyCollection(dict):
    def __init__(self):
        super().__init__()
        self._data = {}
        self._next_id = 1

    def find(self, *args, **kwargs):
        return list(self._data.values())

    def update_one(self, q, u, upsert=False):
        # simple upsert by email
        email = q.get("email") or (u.get("$set", {}).get("email"))
        if email in self._data:
            self._data[email].update(u.get("$set", {}))
        else:
            self._data[email] = {**u.get("$set", {}), **{"_id": self._next_id}}
            self._next_id += 1

    def insert_one(self, doc):
        self._data[doc.get("run_id")] = doc

    def aggregate(self, pipeline):
        # emulate grouping by normalized_name
        groups = {}
        for v in self._data.values():
            key = v.get("normalized_name")
            groups.setdefault(key, []).append(v.get("_id"))
        res = []
        for k, ids in groups.items():
            if len(ids) > 1:
                res.append({"_id": k, "ids": ids, "count": len(ids)})
        return res

    def replace_one(self, q, doc, upsert=False):
        _id = doc.get("_id")
        for k, v in list(self._data.items()):
            if v.get("_id") == _id:
                self._data[k] = doc

    def delete_one(self, q):
        _id = q.get("_id")
        for k, v in list(self._data.items()):
            if v.get("_id") == _id:
                del self._data[k]


class DummyDB:
    def __init__(self):
        self.collections = {
            "incoming": DummyCollection(),
            "customers": DummyCollection(),
            "workflows": DummyCollection(),
        }

    def __getitem__(self, item):
        return self.collections[item]


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    dummy = DummyDB()
    monkeypatch.setattr(db_module, "get_db", lambda: dummy)
    return dummy


def test_pipeline_run_patch(monkeypatch, patch_db):
    # seed some incoming
    incoming = patch_db["incoming"]
    incoming.update_one({"email": "x@e.com"}, {"$set": {"email": "x@e.com", "name": "X"}}, upsert=True)
    incoming.update_one({"email": "x2@e.com"}, {"$set": {"email": "x2@e.com", "name": "X"}}, upsert=True)

    # patch LLM usage to avoid network
    monkeypatch.setenv("OPENAI_API_KEY", "")

    p = Pipeline()
    run_id = p.run()
    assert run_id is not None
    workflows = patch_db["workflows"]._data
    assert run_id in workflows
