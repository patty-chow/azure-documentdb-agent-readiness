import math
from typing import List


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def combine_scores(vector_score: float, regex_score: float, v_weight: float = 0.7, r_weight: float = 0.3) -> float:
    # vector_score expected in [0,1], regex_score in [0,1]
    return max(0.0, min(1.0, v_weight * vector_score + r_weight * regex_score))
