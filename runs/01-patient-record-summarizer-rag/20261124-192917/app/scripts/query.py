"""Example retrieval: compute embedding for question, run a cosmosSearch vector KNN pre-filtered by patientId, and print results.
"""
import os
import sys
from pathlib import Path
# ensure src is importable
sys.path.append(str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from src.db import get_db

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "1536"))

try:
    import openai
    openai.api_key = OPENAI_API_KEY
except Exception:
    openai = None


def embed_text(text):
    if openai and OPENAI_API_KEY:
        resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=[text])
        return resp['data'][0]['embedding']
    # fallback deterministic embedding similar to seed
    import random
    rnd = random.Random(42 + abs(hash(text)) % 100000)
    v = [rnd.random() - 0.5 for _ in range(EMBEDDING_DIMS)]
    norm = sum(x*x for x in v) ** 0.5
    return [x / norm for x in v]


def search(patientId, question, k=5):
    db = get_db()
    coll = db['patient_chunks']
    qv = embed_text(question)
    pipeline = [
        {
            "$search": {
                "cosmosSearch": {
                    "path": "embedding",
                    "vector": qv,
                    "k": k,
                    "lSearch": max(50, k*10),
                    "filter": {"patientId": {"$eq": patientId}}
                }
            }
        },
        {"$project": {"patientId": 1, "chunkId": 1, "text": 1, "score": {"$meta": "searchScore"}}}
    ]
    res = list(coll.aggregate(pipeline))
    return res


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--patient', default='patient_001')
    p.add_argument('--question', default='summarize vitals')
    args = p.parse_args()
    hits = search(args.patient, args.question, k=5)
    print(f"Retrieved {len(hits)} hits for {args.patient}")
    for h in hits:
        print(h['chunkId'], h.get('score'))
        print(h['text'])
        print('---')
