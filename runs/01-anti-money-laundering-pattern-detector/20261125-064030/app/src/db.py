import os
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB_NAME = os.getenv("DB_NAME", "sample_banking_01")


def get_client() -> MongoClient:
    if not DOCUMENTDB_URI:
        raise EnvironmentError(
            "DOCUMENTDB_URI is not set. Set it in the environment or copy .env.example to .env and fill it."
        )
    client = MongoClient(DOCUMENTDB_URI)
    return client


def get_db():
    client = get_client()
    return client[DB_NAME]


def supports_graph_lookup(db) -> bool:
    """Try running a tiny aggregation that uses $graphLookup and see if server accepts it.

    Returns True if the server accepts $graphLookup, False otherwise.
    """
    try:
        # Use an aggregation on a non-existing collection with $graphLookup that does nothing
        # The aggregation itself will be validated by the server for operator support.
        db.command({"ping": 1})
        pipeline = [
            {"$match": {}},
            {"$graphLookup": {
                "from": "transactions",
                "startWith": "$from_account",
                "connectFromField": "to_account",
                "connectToField": "from_account",
                "as": "chain",
                "maxDepth": 0
            }}
        ]
        # Use explain to avoid scanning or requiring data
        db.command({"aggregate": "transactions", "pipeline": pipeline, "explain": True})
        return True
    except OperationFailure:
        return False
    except Exception:
        # If any other error occurs, return False to trigger client-side fallback
        return False
