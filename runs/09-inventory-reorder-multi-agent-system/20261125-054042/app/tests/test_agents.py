import pytest
from sample_retail_09.agents import ForecastAgent, SupplierAgent, Orchestrator

class DummyColl:
    def __init__(self, docs):
        self.docs = docs
    def find(self, q):
        return [d for d in self.docs if d.get('item_id')==q.get('item_id')]
    def find_one(self, q, sort=None):
        for d in self.docs:
            if d.get('item_id')==q.get('item_id'):
                return d
        return None

class DummyDB:
    def __init__(self):
        self._data = {}
    def __getitem__(self, name):
        return DummyColl(self._data.get(name, []))

@pytest.fixture
def forecast():
    return ForecastAgent()

def test_forecast_no_history(forecast):
    qty = forecast.predict_reorder_qty('UNKNOWN_SKU')
    assert qty >= 1

# Simple sanity tests only; DB integration is covered by seed + run scripts in CI where DOCUMENTDB_URI is present
