from sample.utils import deterministic_scores_from_text, deterministic_embedding


def test_deterministic_scores():
    s, r = deterministic_scores_from_text("Test company alpha")
    assert len(s) == 3
    assert all(1 <= x <= 10 for x in s)
    assert len(r) == 3


def test_deterministic_embedding():
    vec = deterministic_embedding("some text", dims=64)
    assert len(vec) == 64
    # norm ~=1
    import math
    norm = math.sqrt(sum(x*x for x in vec))
    assert abs(norm - 1.0) < 1e-6
