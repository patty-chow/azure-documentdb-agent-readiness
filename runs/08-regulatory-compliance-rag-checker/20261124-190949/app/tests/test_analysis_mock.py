import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import mongomock
from src import analysis

# Use mongomock to test analysis without a live DocumentDB

def test_analyze_keyword_fallback(monkeypatch):
    # create a fake db with sample regulation
    client = mongomock.MongoClient()
    db = client["sample_fintech_08"]
    db.regulations.insert_one({"_id": "r1", "text": "must encrypt data at rest"})

    # monkeypatch analysis.get_db to return our mock db
    monkeypatch.setattr(analysis, "get_db", lambda: db)

    rpt = analysis.analyze_text("Encrypt customer data at rest")
    assert rpt["verdict"] in ("compliant", "partial", "non-compliant")
    assert "matches" in rpt
