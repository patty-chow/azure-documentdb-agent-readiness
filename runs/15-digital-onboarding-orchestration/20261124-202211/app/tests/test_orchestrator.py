import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from sample_orchestrator import orchestrator


@pytest.mark.asyncio
async def test_orchestrate_flow(monkeypatch):
    # Prepare a fake document returned from DB
    fake_doc = {"applicant_id": "test-1", "applicant_name": "Test User", "state": "INIT", "history": []}

    # Monkeypatch get_client to provide a fake client with required methods
    class FakeColl:
        def __init__(self):
            self.doc = fake_doc

        async def find_one(self, q):
            return self.doc

        async def find_one_and_update(self, *args, **kwargs):
            # args: filter, update, ...
            update = args[1]
            # apply $set
            s = update.get("$set")
            if s and "state" in s:
                self.doc["state"] = s["state"]
            # apply $push
            push = update.get("$push")
            if push:
                # push is a dict of arrays to push; for test we append the dict itself
                for k, v in push.items():
                    self.doc.setdefault(k, []).append(v)
            return self.doc

    class FakeClient:
        def __init__(self):
            self._coll = FakeColl()

        def __getitem__(self, item):
            return {"onboarding_applications": self._coll}

        async def start_session(self):
            class S:
                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    return False

                def start_transaction(self):
                    class T:
                        async def __aenter__(self):
                            return self

                        async def __aexit__(self, *args):
                            return False

                    return T()

            return S()

    fake_client = FakeClient()

    monkeypatch.setattr("sample_orchestrator.orchestrator.get_client", lambda: fake_client)

    # Run orchestrator
    res = await orchestrator.orchestrate("test-1")
    assert res["state"] in {"ACCOUNT_OPENED", "FAILED", "RISK_ASSESSED", "ID_VERIFIED"}
    assert "history" in res
