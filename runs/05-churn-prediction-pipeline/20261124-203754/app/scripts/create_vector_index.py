"""
Create a vector index on the customers.rfm_embedding path using a createIndexes command.
This script attempts to run a createIndexes command with cosmosSearchOptions for a vector index.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from src.db import get_db


def create_vector_index(kind: str, dimensions: int, similarity: str = "COS"):
    db = get_db()
    coll_name = "customers"
    print(f"Creating vector index on {coll_name}.rfm_embedding kind={kind} dims={dimensions} similarity={similarity}")
    cmd = {
        "createIndexes": coll_name,
        "indexes": [
            {
                "key": {"rfm_embedding": 1},
                "name": "idx_rfm_embedding_vector",
                "cosmosSearchOptions": {
                    "kind": kind,
                    "dimensions": dimensions,
                    "similarity": similarity
                }
            }
        ]
    }
    try:
        res = db.command(cmd)
        print("createIndexes result:", res)
    except Exception as e:
        print("Error creating vector index:", e)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dimensions", type=int, required=True)
    p.add_argument("--index-kind", type=str, default="vector-hnsw")
    args = p.parse_args()
    create_vector_index(args.index_kind, args.dimensions)
