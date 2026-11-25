from fastapi.testclient import TestClient
from src.app import app
from unittest.mock import patch

class DummyColl:
    def __init__(self):
        self.store = {}
    def update_one(self, q, u, upsert=False):
        pid = q.get('patient_id') or u.get('$set',{}).get('patient_id')
        self.store[pid] = u.get('$set')
    def aggregate(self, pipeline):
        return iter([
            {'patient_id':'p1','features':{'age':70},'risk_label':'high','recommended_interventions':['i1'], 'score': 0.9},
        ])

with patch('src.db.get_collection') as mock_get_coll, patch('src.embeddings.get_embedding_for_features') as mock_emb, patch('src.agent.generate_narrative') as mock_gen:
    mock_get_coll.return_value = DummyColl()
    mock_emb.return_value = [0.1,0.2,0.3]
    mock_gen.return_value = 'Test narrative.'
    client = TestClient(app)
    resp = client.post('/predict', json={"patient_id":"test1","features":{"age":67},"top_k":1})
    print('status', resp.status_code)
    try:
        print('json', resp.json())
    except Exception as e:
        print('content', resp.content)

