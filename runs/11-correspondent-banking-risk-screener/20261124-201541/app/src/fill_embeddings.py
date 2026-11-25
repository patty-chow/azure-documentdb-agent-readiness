import os
import random
import math
from src.db import get_db
from dotenv import load_dotenv

load_dotenv()
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", 1536))

def random_vector(dim):
    # deterministic random for reproducibility using a fixed seed
    rnd = random.Random(42)
    vec = [rnd.uniform(-1, 1) for _ in range(dim)]
    # normalize for cosine similarity
    norm = math.sqrt(sum(x*x for x in vec)) or 1.0
    return [x / norm for x in vec]


def fill():
    db = get_db()
    vec = random_vector(EMBEDDING_DIMS)
    for coll in ("correspondents", "sanctions", "adverse_media"):
        for doc in db[coll].find({}):
            if "embedding" not in doc:
                db[coll].update_one({"_id": doc["_id"]}, {"$set": {"embedding": vec}})
    print("Filled embeddings for documents where missing.")

if __name__ == "__main__":
    fill()
