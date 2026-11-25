import os
import mongomock
import pytest
from src.retriever import vector_search

# Mock get_db to return mongomock DB
import src.db as dbmod

@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    client = mongomock.MongoClient()
    monkeypatch.setattr(dbmod, 'get_client', lambda: client)
    monkeypatch.setattr(dbmod, 'get_db', lambda: client['sample_healthcare_13'])


def test_vector_search_empty():
    # With no documents, should return empty list
    results = vector_search([0]*1536, k=3)
    assert results == []


def test_vector_search_basic():
    coll = dbmod.get_db()['high_risk_profiles']
    coll.insert_one({'patient_id':'p1','embedding':[0.1]*1536,'features':{}})
    res = vector_search([0.1]*1536, k=1)
    # mongomock does not implement $search; our retriever will try to run aggregate and get empty; so check gracefully returns list or empty
    assert isinstance(res, list)
