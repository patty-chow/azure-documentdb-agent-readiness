import os
from db import get_client
from sample_data import GUIDELINES
from utils import get_embedding

DB_NAME = "sample_healthcare_06"
COLLECTION = "guidelines"

INDEX_NAME = "guidelines_embedding_diskann"


def ensure_index(coll):
    # Create a vector-diskann index on the 'embedding' field with dimensions matching our embedding model
    try:
        print("Creating or ensuring vector index (this is idempotent)...")
        coll.create_index(
            [("embedding", "cosmosSearch")],
            name=INDEX_NAME,
            cosmosSearchOptions={
                "kind": "vector-diskann",
                "dimensions": int(os.environ.get("EMBEDDING_DIMS", "1536")),
                "similarity": "COS",
                "maxDegree": 32,
                "lBuild": 50,
            },
        )
        print("Index ensured.")
    except Exception as e:
        print("Warning: could not create index (server may not accept the command):", e)


def seed():
    client = get_client()
    db = client[DB_NAME]
    coll = db[COLLECTION]

    ensure_index(coll)

    for doc in GUIDELINES:
        text = doc["text"]
        emb = get_embedding(text)
        # Upsert document
        record = {
            "section_id": doc["section_id"],
            "title": doc["title"],
            "text": doc["text"],
            "embedding": emb,
            "embeddingModel": os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"),
            "embeddingDims": int(os.environ.get("EMBEDDING_DIMS", "1536")),
            "documented_urgency": doc.get("documented_urgency", "low"),
        }
        coll.update_one({"section_id": doc["section_id"]}, {"$set": record}, upsert=True)
    print(f"Seeded {len(GUIDELINES)} documents into {DB_NAME}.{COLLECTION}")


if __name__ == "__main__":
    seed()
