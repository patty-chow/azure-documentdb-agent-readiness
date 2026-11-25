"""Seed script: load seeds/sample_chain.json into the options collection using the app's db helper.

Usage: python scripts/seed.py
"""
import json
from pathlib import Path
import sys
# ensure the project root is on sys.path so 'app' package can be imported when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_collection
from datetime import datetime

SEED_PATH = Path(__file__).parent.parent / "seeds" / "sample_chain.json"


def load_seed():
    coll = get_collection("options")
    data = json.loads(SEED_PATH.read_text())
    # Expect data to be {"underlying":..., "expiry":"YYYY-MM-DD", "options":[...]} or an array of such snapshots
    if isinstance(data, list):
        snapshots = data
    else:
        snapshots = [data]

    from pymongo import UpdateOne
    ops = []
    for snapshot in snapshots:
        underlying = snapshot["underlying"]
        expiry = datetime.fromisoformat(snapshot["expiry"]).date()
        for opt in snapshot["options"]:
            doc = {
                "underlying": underlying,
                "expiry": datetime.combine(expiry, datetime.min.time()),
                "strike": opt["strike"],
                "optionType": opt.get("optionType"),
                "bid": opt.get("bid"),
                "ask": opt.get("ask"),
                "lastPrice": opt.get("lastPrice"),
                "timestamp": datetime.fromisoformat(opt.get("timestamp")) if opt.get("timestamp") else datetime.utcnow(),
            }
            filter_doc = {"underlying": doc["underlying"], "expiry": doc["expiry"], "strike": doc["strike"], "optionType": doc["optionType"]}
            ops.append(UpdateOne(filter_doc, {"$set": doc}, upsert=True))

    if ops:
        # batch
        BATCH = 1000
        for i in range(0, len(ops), BATCH):
            coll.bulk_write(ops[i:i+BATCH], ordered=False)
    print("Seed completed: wrote", len(ops), "operations")


if __name__ == "__main__":
    load_seed()
