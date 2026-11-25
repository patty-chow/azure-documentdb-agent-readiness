import re
import hashlib
from typing import List


def normalize_name(name: str) -> str:
    if not name:
        return ""
    n = name.strip().lower()
    n = re.sub(r"[^a-z0-9\s]", "", n)
    n = re.sub(r"\s+", " ", n)
    return n


def name_similarity(a: str, b: str) -> float:
    a_n = normalize_name(a)
    b_n = normalize_name(b)
    if not a_n or not b_n:
        return 0.0
    # simple token-overlap similarity
    a_tokens = set(a_n.split())
    b_tokens = set(b_n.split())
    inter = a_tokens.intersection(b_tokens)
    union = a_tokens.union(b_tokens)
    if not union:
        return 0.0
    return len(inter)/len(union)


def deterministic_embedding(text: str, dims: int = 8) -> List[float]:
    # Deterministic pseudo-embedding for offline/demo runs: use SHA256 chunks
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    vals = []
    for i in range(dims):
        chunk = h[i*4:(i+1)*4]
        vals.append(int(chunk, 16) / float(0xFFFF))
    return vals
