import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch

from src import db


def test_normalize_vector():
    v = [3.0, 4.0]
    nv = db.normalize_vector(v)
    assert abs(nv[0] - 0.6) < 1e-6
    assert abs(nv[1] - 0.8) < 1e-6


@patch("src.db.get_db")
def test_upsert_research_documents(mock_get_db):
    mock_coll = MagicMock()
    mock_db = {"research_documents": mock_coll}
    mock_get_db.return_value = mock_db

    docs = [{"_id": "x", "embedding": db.generate_synthetic_embedding("x"), "content": "c"}]
    db.upsert_research_documents(docs)
    mock_coll.replace_one.assert_called_once()
