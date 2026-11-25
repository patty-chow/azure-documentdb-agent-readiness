import pytest
from fastapi.testclient import TestClient
from src.app import app
from unittest.mock import patch
import src.db as dbmod

client = TestClient(app)

class DummyColl:
    def __init__(self):
        self.store = {}
    def update_one(self, q, u, upsert=False):
        pid = q.get('patient_id') or u.get('$set',{}).get('patient_id')
        self.store[pid] = u.get('$set')
    def aggregate(self, pipeline):
        # Return some fake retrieved profiles
        return iter([
            {'patient_id':'p1','features':{'age':70},'risk_label':'high','recommended_interventions':['i1'], 'score': 0.9},
            {'patient_id':'p2','features':{'age':68},'risk_label':'high','recommended_interventions':['i2'], 'score': 0.85}
        ])

@patch('src.agent.generate_narrative')
@patch('src.app.get_embedding_for_features')
@patch('src.app.get_collection')
def test_predict(mock_get_coll, mock_get_emb, mock_generate):
    mock_get_emb.return_value = [0.1,0.2,0.3]
    mock_get_coll.return_value = DummyColl()
    mock_generate.return_value = 'Test narrative.'
    resp = client.post('/predict', json={"patient_id":"test1","features":{"age":67},"top_k":2})
    assert resp.status_code == 200
    j = resp.json()
    assert 'narrative' in j
    assert 'retrieved' in j
    assert len(j['retrieved']) == 2
