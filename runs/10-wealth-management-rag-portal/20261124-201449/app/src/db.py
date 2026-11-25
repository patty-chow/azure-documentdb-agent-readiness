import os
import math
import random
from typing import List, Dict, Any
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_banking_10")

# Embedding dims must match the chosen model
EMBEDDING_DIMS = 1536

_client = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        if not DOCUMENTDB_URI:
            raise RuntimeError("DOCUMENTDB_URI environment variable is required to connect to DocumentDB.")
        # vendor guidance: prefer retryWrites=false for Azure DocumentDB
        uri = DOCUMENTDB_URI
        if "retryWrites" not in uri:
            if uri.strip().endswith("/"):
                uri = uri + "?retryWrites=false"
            else:
                uri = uri + ("&retryWrites=false" if "?" in uri else "?retryWrites=false")
        _client = MongoClient(uri)
    return _client


def get_db():
    return get_client()[DATABASE_NAME]


def ensure_collections_and_indexes():
    db = get_db()
    research: Collection = db["research_documents"]
    portfolios: Collection = db["portfolios"]

    # Create simple indexes for portfolio lookups
    portfolios.create_index([("client_id", ASCENDING)], unique=True, name="idx_portfolio_client")

    # Create the vector index on the embedding field using cosmosSearch vector-hnsw
    # The exact options follow DocumentDB's `createIndexes` with `cosmosSearchOptions`.
    try:
        # If index exists, creation will be ignored or raise; handle idempotently.
        research.create_index(
            [("embedding", "cosmosSearch")],
            name="research_embedding_hnsw",
            cosmosSearchOptions={
                "kind": "vector-hnsw",
                "dimensions": EMBEDDING_DIMS,
                "similarity": "COS",
                "maxDegree": 32,
                "lBuild": 50,
            },
        )
    except Exception as exc:
        # Some server versions may not accept the python driver hint; try a raw command
        try:
            db.command({
                "createIndexes": "research_documents",
                "indexes": [
                    {
                        "key": {"embedding": "cosmosSearch"},
                        "name": "research_embedding_hnsw",
                        "cosmosSearchOptions": {
                            "kind": "vector-hnsw",
                            "dimensions": EMBEDDING_DIMS,
                            "similarity": "COS",
                            "maxDegree": 32,
                            "lBuild": 50,
                        },
                    }
                ],
            })
        except Exception:
            # If creation fails, leave it to the user/MCP tools; raise for visibility
            raise


def normalize_vector(vec: List[float]) -> List[float]:
    # Normalize for cosine similarity
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def upsert_research_documents(docs: List[Dict[str, Any]]):
    db = get_db()
    research = db["research_documents"]
    for d in docs:
        # Ensure embedding length
        embedding = d.get("embedding")
        if embedding and len(embedding) != EMBEDDING_DIMS:
            raise ValueError(f"Embedding dimension mismatch: got {len(embedding)} expected {EMBEDDING_DIMS}")
        research.replace_one({"_id": d["_id"]}, d, upsert=True)


def upsert_portfolio(portfolio: Dict[str, Any]):
    db = get_db()
    portfolios = db["portfolios"]
    portfolios.replace_one({"client_id": portfolio["client_id"]}, portfolio, upsert=True)


def search_similar(embedding: List[float], k: int = 5, l_search: int = 100) -> List[Dict[str, Any]]:
    """Perform a vector KNN search using $search with cosmosSearch vector query.
    Returns top-k documents with their metadata and score.
    """
    db = get_db()
    research = db["research_documents"]
    vec = normalize_vector(embedding)
    pipeline = [
        {
            "$search": {
                "cosmosSearch": {
                    "path": "embedding",
                    "vector": vec,
                    "k": k,
                    "lSearch": max(l_search, k),
                    "similarity": "COS",
                }
            }
        },
        {"$limit": k},
        {"$project": {"title": 1, "content": 1, "metadata": 1, "score": {"$meta": "searchScore"}}},
    ]
    try:
        res = list(research.aggregate(pipeline))
    except Exception as exc:
        # Some clusters expose different $search behavior; bubble up error for debugging
        raise
    return res


def generate_synthetic_embedding(seed_text: str) -> List[float]:
    random.seed(hash(seed_text))
    return normalize_vector([random.uniform(-1, 1) for _ in range(EMBEDDING_DIMS)])
