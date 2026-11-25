import sys
sys.path.insert(0, "src")
from agent import cosine_similarity


def test_cosine_similarity():
    a = [1, 0, 0]
    b = [1, 0, 0]
    c = [0, 1, 0]
    assert abs(cosine_similarity(a, b) - 1.0) < 1e-6
    assert abs(cosine_similarity(a, c) - 0.0) < 1e-6
