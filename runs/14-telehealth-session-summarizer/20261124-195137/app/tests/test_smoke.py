import os
import sys
import pytest

# make src importable when running tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.db import get_collections


def test_db_connection():
    # This smoke test will only run if DOCUMENTDB_URI is set in env; otherwise skip.
    if not os.environ.get("DOCUMENTDB_URI"):
        pytest.skip("DOCUMENTDB_URI not set; skipping live DB tests")
    cols = get_collections()
    assert "clinical_summaries" in cols
