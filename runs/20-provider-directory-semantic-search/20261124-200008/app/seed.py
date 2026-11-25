import os
import json
from dotenv import load_dotenv
from app.db import get_db

load_dotenv()
DOCUMENTDB_DB = "sample_healthcare_20"
COLLECTION = "providers"

# optional OpenAI import
try:
    import openai
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_KEY:
        openai.api_key = OPENAI_KEY
    OPENAI_AVAILABLE = True
except Exception:
    openai = None
    OPENAI_KEY = None
    OPENAI_AVAILABLE = False

MODEL = os.getenv("OPENAI_MODEL", "text-embedding-3-small")

# Index parameters chosen: vector-hnsw with dims 1536
INDEX_NAME = "providers_vector_hnsw"
DIMS = 1536
HNSW_OPTIONS = {"m": 16, "efConstruction": 64, "similarity": "COS", "dimensions": DIMS}


def make_embedding(text: str):
    if OPENAI_AVAILABLE and OPENAI_KEY:
        resp = openai.Embedding.create(input=text, model=MODEL)
        return resp["data"][0]["embedding"]
    else:
        # deterministic fallback
        import hashlib
        h = hashlib.sha256(text.encode('utf-8')).digest()
        dims = DIMS
        floats = []
        for i in range(dims):
            b = h[i % len(h)]
            floats.append((b / 255.0) * 2.0 - 1.0)
        return floats


def ensure_index(db):
    coll_name = COLLECTION
    # create collection if not exists
    if coll_name not in db.list_collection_names():
        db.create_collection(coll_name)
    # create vector index via createIndexes command
    cmd = {
        "createIndexes": coll_name,
        "indexes": [
            {
                "name": INDEX_NAME,
                "key": {"embedding": "cosmosSearch"},
                "cosmosSearchOptions": {"kind": "vector-hnsw", **HNSW_OPTIONS}
            }
        ]
    }
    try:
        print("Creating vector index (may take a moment)...")
        res = db.command(cmd)
        print("createIndexes result:", res)
    except Exception as e:
        print("createIndexes failed or index exists:", e)


def seed():
    db = get_db(DOCUMENTDB_DB)
    coll = db[COLLECTION]
    ensure_index(db)
    # load sample data
    data = json.load(open('data/providers.json'))
    docs = []
    for p in data:
        emb = make_embedding(p['bio'] + ' ' + ' '.join(p.get('languages',[])) + ' ' + ' '.join(p.get('insurance',[])))
        doc = p.copy()
        doc['embedding'] = emb
        docs.append(doc)
    # upsert by name for idempotency
    for d in docs:
        coll.update_one({'name': d['name']}, {'$set': d}, upsert=True)
    print(f"Seeded {len(docs)} providers into {DOCUMENTDB_DB}.{COLLECTION}")

if __name__ == '__main__':
    seed()
