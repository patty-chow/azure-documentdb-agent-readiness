import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import scripts.seed as seed


def test_get_embedding_fallback():
    # Ensure get_embedding returns a vector of the expected dims when OPENAI_API_KEY is not set
    emb = seed.get_embedding("hello world")
    assert hasattr(emb, "__len__")
    assert len(emb) == seed.db.EMBEDDING_DIMS
