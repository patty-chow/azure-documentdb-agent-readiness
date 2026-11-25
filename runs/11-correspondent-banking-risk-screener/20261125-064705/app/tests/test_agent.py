import pytest
from unittest.mock import patch

from src.agent import compute_risk_score, cosine_similarity


def test_cosine_similarity_identical():
    a = [1, 0, 0]
    b = [1, 0, 0]
    assert pytest.approx(1.0) == cosine_similarity(a, b)


def test_compute_risk_score_empty():
    assert compute_risk_score([]) == 0


def test_compute_risk_score_basic():
    matches = [{"score": 0.9}, {"score": 0.4}, {"score": 0.2}]
    score = compute_risk_score(matches)
    assert isinstance(score, int) and 0 <= score <= 100


@patch("src.agent.embed_text")
@patch("src.agent.get_collection")
def test_review_flow(mock_get_collection, mock_embed_text):
    # simple smoke test that uses mocked DB and embeddings
    mock_embed_text.return_value = [0.1, 0.2, 0.3]

    class FakeColl:
        def __init__(self, docs):
            self.docs = docs

        def find(self, *args, **kwargs):
            return self.docs

        def find_one(self, q):
            return {"_id": "c1", "profile_text": "test profile"}

    sanctions_docs = [{"_id": "s1", "entry_text": "bad actor", "embedding": [0.1, 0.2, 0.3], "source": "OFAC"}]
    adverse_docs = [{"_id": "a1", "snippet": "news snippet", "embedding": [0.0, 0.1, 0.0], "source": "News"}]
    corr_coll = FakeColl([])
    # get_collection will be called for sanctions/adverse_media/correspondents
    def side_effect(name):
        if name == "sanctions":
            return FakeColl(sanctions_docs)
        if name == "adverse_media":
            return FakeColl(adverse_docs)
        if name == "correspondents":
            return corr_coll
        return FakeColl([])

    mock_get_collection.side_effect = side_effect

    # import here to ensure patches apply
    from src.agent import review_correspondent

    res = review_correspondent(correspondent_id="c1")
    assert "risk_score" in res and "matches" in res and "risk_narrative" in res
