import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils import normalize_name, name_similarity


def test_normalize():
    assert normalize_name(" Alice O'Neill ") == "alice oneill"
    assert normalize_name("") == ""


def test_similarity():
    a = "Alice Smith"
    b = "Alicia Smith"
    sim = name_similarity(a, b)
    assert sim > 0
