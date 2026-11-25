import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import seed

@patch('seed.get_db')
def test_ensure_index_creates_collection(mock_get_db):
    mock_db = MagicMock()
    mock_db.list_collection_names.return_value = []
    mock_get_db.return_value = mock_db
    # should not raise
    seed.ensure_index(mock_db)
    mock_db.create_collection.assert_called()

@patch('seed.openai')
def test_make_embedding_fallback(mock_openai):
    # when no OPENAI_KEY present, make_embedding should return a list of length DIMS
    with patch.dict('os.environ', {}, clear=True):
        emb = seed.make_embedding('test')
        assert isinstance(emb, list)
        assert len(emb) == seed.DIMS
