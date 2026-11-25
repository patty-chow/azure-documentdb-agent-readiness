import hashlib
import math
import numpy as np


def deterministic_scores_from_text(text):
    # Produce deterministic pseudo-random 1-10 scores from text using SHA256
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # split into 3 2-byte chunks
    nums = [int.from_bytes(h[i:i+2], "big") for i in (0,2,4)]
    scores = [1 + (n % 10) for n in nums]
    rationales = [f"Heuristic rationale based on text hash fragment {i}" for i in range(3)]
    return scores, rationales


def deterministic_embedding(text, dims=1536):
    # Create a deterministic "embedding" vector from hash bytes and normalize
    h = hashlib.sha256(text.encode("utf-8")).digest()
    arr = np.frombuffer(h, dtype=np.uint8).astype(float)
    # expand or tile to dims
    if arr.size < dims:
        repeats = math.ceil(dims / arr.size)
        arr = np.tile(arr, repeats)[:dims]
    else:
        arr = arr[:dims]
    vec = arr / (np.linalg.norm(arr) + 1e-12)
    return vec.tolist()


def normalize_embedding(vec):
    a = np.array(vec, dtype=float)
    n = np.linalg.norm(a)
    if n == 0:
        return vec
    return (a / n).tolist()
