import argparse
import hashlib
import os
import json
from datetime import datetime
from typing import List, Tuple

from sentence_transformers import SentenceTransformer
import numpy as np

from db import get_db

EMBED_MODEL = "all-MiniLM-L6-v2"
EMBED_DIMS = 384
COLLECTION = "earnings_chunks"

# Simple chunker: split on lines and group into chunks up to N characters
def chunk_text(text: str, max_chars=800) -> List[Tuple[str,int,int]]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    chunks = []
    cur = []
    cur_len = 0
    start_time = 0
    for ln in lines:
        if cur_len + len(ln) > max_chars and cur:
            chunk_text = "\n".join(cur)
            chunks.append((chunk_text, start_time, 0))
            cur = [ln]
            cur_len = len(ln)
        else:
            cur.append(ln)
            cur_len += len(ln)
    if cur:
        chunks.append(("\n".join(cur), start_time, 0))
    return chunks


def chunk_id_for(source: str, start: int, end: int):
    h = hashlib.sha256(f"{source}:{start}:{end}".encode()).hexdigest()
    return h


def ensure_indexes_local(db):
    coll = db[COLLECTION]
    # Unique index on chunk_id to dedupe
    coll.create_index([("chunk_id", 1)], name="uniq_chunk_id", unique=True)


def ingest_file_local(path: str):
    with open(path, "r", encoding="utf8") as f:
        text = f.read()
    chunks = chunk_text(text)

    model = SentenceTransformer(EMBED_MODEL)

    db = get_db()
    coll = db[COLLECTION]

    docs = []
    for i, (chunk_text, start, end) in enumerate(chunks):
        emb = model.encode(chunk_text, normalize_embeddings=True).astype(float).tolist()
        cid = chunk_id_for(os.path.basename(path), i, i)
        doc = {
            "chunk_id": cid,
            "source": os.path.basename(path),
            "start_time": start,
            "end_time": end,
            "text": chunk_text,
            "embedding": emb,
            "embedding_model": EMBED_MODEL,
            "embedding_dims": EMBED_DIMS,
            "inserted_at": datetime.utcnow()
        }
        docs.append(doc)

    if docs:
        try:
            res = coll.insert_many(docs, ordered=False)
            print(f"Inserted {len(res.inserted_ids)} chunks into {COLLECTION}")
        except Exception as e:
            print("Insert finished with exception (some duplicates may have been skipped):", e)
    else:
        print("No chunks to insert")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path to transcript (txt). PDF support is not implemented in this minimal sample")
    args = parser.parse_args()

    db = get_db()
    ensure_indexes_local(db)
    ingest_file_local(args.source)
