from src.utils import cosine_similarity, combine_scores


def test_cosine_similarity_basic():
    a = [1, 0]
    b = [0, 1]
    assert abs(cosine_similarity(a, b) - 0.0) < 1e-6
    c = [1, 0]
    assert abs(cosine_similarity(a, c) - 1.0) < 1e-6


def test_combine_scores():
    v = 0.8
    r = 1.0
    combined = combine_scores(v, r, v_weight=0.7, r_weight=0.3)
    assert combined == 0.7 * v + 0.3 * r
