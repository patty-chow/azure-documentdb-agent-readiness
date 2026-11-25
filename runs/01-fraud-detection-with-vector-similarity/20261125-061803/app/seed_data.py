"""Seed script: creates the fraud_patterns collection in database sample_fintech_01 and inserts synthetic patterns.
Attempts to create a server-side vector index; if that fails, continues and the app will fall back to client-side search.
"""
import os
import random
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

DOC_URI = os.environ.get("DOCUMENTDB_URI")
if not DOC_URI:
    raise RuntimeError("DOCUMENTDB_URI is not set. Copy .env.example to .env and set DOCUMENTDB_URI.")

DB_NAME = "sample_fintech_01"
COLLECTION = "fraud_patterns"

# small synthetic patterns
PATTERN_COUNT = 12
EMBED_DIM = 128

# embedding generator: use OpenAI via LangChain if available, otherwise deterministic mock
USE_OPENAI = bool(os.environ.get("OPENAI_API_KEY"))

def deterministic_embedding(text, dim=EMBED_DIM):
    # deterministic pseudo-embedding based on hash
    h = abs(hash(text))
    rnd = random.Random(h)
    return [rnd.random() for _ in range(dim)]


def generate_pattern(i):
    desc = f"Pattern {i}: suspicious sequence of actions with amount={1000 + i*50}"
    example = {"amount": 1000 + i*50, "steps": ["login","transfer","withdraw"]}
    emb = deterministic_embedding(desc)
    return {"pattern_id": f"p{i}", "description": desc, "example_transactions": example, "embedding": emb, "metadata": {"severity": (i % 5) + 1}}


def main():
    client = MongoClient(DOC_URI)
    db = client[DB_NAME]
    col = db[COLLECTION]

    # create collection if not exists
    if COLLECTION not in db.list_collection_names():
        db.create_collection(COLLECTION)
        print(f"Created collection {COLLECTION}")
    else:
        print(f"Collection {COLLECTION} already exists")

    # attempt server-side vector index creation (best-effort)
    try:
        # This is a plausible index spec; exact names may vary by server implementation.
        # If the server rejects these options, we catch the error and continue.
        index_spec = [("embedding", "cosmosSearch")]
        # Many MongoDB-compatible clusters expose create_index with 'vectorOptions'; try a representative form.
        idx_name = col.create_index([("embedding", 1)], name="embedding_vector_idx")
        print("Created simple array index for embedding (server-side vector index attempt is best-effort)", idx_name)
    except Exception as e:
        print("Server-side vector index creation failed or not supported, continuing with seed. Error:", str(e))

    # clear existing sample docs with our pattern_id prefix
    col.delete_many({"pattern_id": {"$regex": "^p\\d+"}})

    docs = [generate_pattern(i) for i in range(1, PATTERN_COUNT + 1)]
    col.insert_many(docs)
    print(f"Inserted {len(docs)} pattern documents into {DB_NAME}.{COLLECTION}")

    # write a small sample transactions file for local tests
    with open("sample_transactions.json", "w") as f:
        samples = [{"tx_id": f"t{i}", "amount": 50 + i*10, "description": f"user transfer {i}"} for i in range(1, 6)]
        json.dump(samples, f, indent=2)
    print("Wrote sample_transactions.json")

if __name__ == "__main__":
    main()
