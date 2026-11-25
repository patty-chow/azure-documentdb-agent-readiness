import pytest
from unittest.mock import patch
from src.embeddings import features_to_text, get_embedding_for_features


def test_features_to_text():
    f = {'b':2, 'a':1}
    s = features_to_text(f)
    assert s == 'a:1; b:2'


@patch('src.embeddings._call_openai_create_embedding')
def test_get_embedding_for_features(mock_create, monkeypatch):
    # Provide OPENAI_API_KEY in env for the function to proceed
    monkeypatch.setenv('OPENAI_API_KEY', 'test')
    mock_create.return_value = {'data': [{'embedding': [0.1, 0.2, 0.3]}]}
    emb = get_embedding_for_features({'a':1})
    assert isinstance(emb, list)
    assert len(emb) == 3
