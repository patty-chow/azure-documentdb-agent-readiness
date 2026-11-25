import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)) or '.')
from utils import chunk_text


def test_chunk_text_basic():
    text = 'Sentence one. Sentence two is a bit longer. Sentence three.'
    chunks = chunk_text(text, max_chars=20)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) <= 20 or c.endswith('.')
