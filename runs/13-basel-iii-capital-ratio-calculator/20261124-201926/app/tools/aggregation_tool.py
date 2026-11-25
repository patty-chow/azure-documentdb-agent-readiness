"""Aggregation tool that connects to Azure DocumentDB (MongoDB-wire) and computes sums across positions."""
import os
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI environment variable is required to connect to Azure DocumentDB")

# Singleton MongoClient per documentdb-driver guidance
_client: Optional[MongoClient] = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        # Use recommended defaults; keep pool sizing conservative for samples
        _client = MongoClient(DOCUMENTDB_URI, tls=True)
    return _client


def get_positions_collection() -> Collection:
    client = get_client()
    db = client.get_database("sample_banking_13")
    return db.get_collection("positions")


def aggregate_totals(match_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run an aggregation that sums risk-weighted-assets and capital elements.

    Returns a dict with summed fields and counts, e.g.
    {
      "count": 10,
      "rwa": 123456.0,
      "cet1": 9876.0,
      "total_capital": 15000.0
    }
    """
    coll = get_positions_collection()
    pipeline = []
    if match_filter:
        pipeline.append({"$match": match_filter})
    pipeline.extend([
        {
            "$group": {
                "_id": None,
                "count": {"$sum": 1},
                "rwa": {"$sum": {"$ifNull": ["$risk_weighted_assets", 0]}},
                "cet1": {"$sum": {"$ifNull": ["$capital.cet1", 0]}},
                "total_capital": {"$sum": {"$ifNull": ["$capital.total", 0]}},
            }
        }
    ])
    res = list(coll.aggregate(pipeline))
    if not res:
        return {"count": 0, "rwa": 0.0, "cet1": 0.0, "total_capital": 0.0}
    doc = res[0]
    return {"count": int(doc.get("count", 0)),
            "rwa": float(doc.get("rwa", 0.0)),
            "cet1": float(doc.get("cet1", 0.0)),
            "total_capital": float(doc.get("total_capital", 0.0))}
