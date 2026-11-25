from sample.utils import cosine_similarity, centroid


def test_cosine_and_centroid():
    a = [1,0,0]
    b = [0,1,0]
    c = [1,1,0]
    assert abs(cosine_similarity(a,b) - 0.0) < 1e-6
    cent = centroid([a,b,c])
    assert len(cent) == 3
