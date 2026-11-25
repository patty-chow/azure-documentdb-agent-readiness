"""Ad-hoc search helpers (vector KNN via local similarity or $search if desired)."""
from sample.db import get_db
from sample.utils import cosine_similarity


def knn_local(query_embedding, k=5):
    db = get_db()
    vectors = db["employee_vectors"]
    docs = list(vectors.find({}))
    scored = []
    for d in docs:
        emb = d.get("embedding")
        if not emb:
            continue
        scored.append((d, cosine_similarity(query_embedding, emb)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
