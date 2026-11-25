"""Create the compound index {underlying:1, expiry:1, strike:1} on sample_fintech_19.options"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.db import get_db

if __name__ == "__main__":
    db = get_db()
    coll = db["options"]
    print("Creating compound index on {underlying:1, expiry:1, strike:1}...")
    index_name = coll.create_index([("underlying", 1), ("expiry", 1), ("strike", 1)], name="idx_underlying_expiry_strike")
    print("Created index:", index_name)
