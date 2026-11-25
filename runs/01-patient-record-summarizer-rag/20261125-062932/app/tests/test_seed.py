import sys
from pathlib import Path
project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from app import embeddings
from app.store import DocumentStore

class InMemoryStore(DocumentStore):
    def __init__(self):
        self._docs = []
    def ensure_indexes(self):
        pass
    def upsert_chunks(self, chunks):
        self._docs.extend(chunks)
    def query_by_patient_and_rerank(self, patient_id, query_embedding, top_k=5):
        # simple echo
        return [{"doc_id":"d","chunk_id":"c","score":0.5,"excerpt":"x"}]

def test_embedding_fallback_is_length():
    v = embeddings.get_embedding("some text")
    assert len(v) == embeddings.EMBEDDING_DIM

@pytest.mark.skipif(True, reason="seed writes to a real DB; manual run only")
def test_seed_idempotent():
    # placeholder for integration test against live DB
    pass
