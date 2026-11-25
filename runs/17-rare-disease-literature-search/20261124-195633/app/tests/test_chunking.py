import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.ingest import chunk_texts


def test_chunk_texts_small():
    docs = [{'pmid': '123', 'title': 'Test', 'abstract': 'This is a short abstract.' , 'year':'2020'}]
    chunks = chunk_texts(docs, chunk_size=10, chunk_overlap=2)
    assert len(chunks) >= 1
    assert chunks[0]['pmid'] == '123'
    assert 'text' in chunks[0]
