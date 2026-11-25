import os
import sys
import pytest
from dotenv import load_dotenv

# ensure project root is on path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

load_dotenv()
from aml_agent.db import get_db


def test_seed_created():
    # Seed must be run before tests by CI or local user. This test verifies expected collections exist.
    db = get_db()
    assert "transactions" in db.list_collection_names()
    assert "accounts" in db.list_collection_names()
    tx_count = db.transactions.count_documents({})
    assert tx_count >= 1


def test_analysis_runs():
    from aml_agent.analysis import analyze
    results = analyze()
    # Results should be a list (possibly empty depending on seed)
    assert isinstance(results, list)
