"""Seed script: insert sample products and chunk documents into DocumentDB.

Usage:
  python seed.py [--skip-embeddings]

If OPENAI_API_KEY is set and --skip-embeddings not provided, this script will
compute embeddings using the model configured in EMBEDDING_MODEL env var and
store them on the chunk documents under the `embedding` field.
"""
import json
import os
import argparse
from db import get_db
from utils import chunk_text
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'openai/text-embedding-3-small')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
EMBEDDING_DIMS = int(os.environ.get('EMBEDDING_DIMS', '1536'))

try:
    import openai
except Exception:
    openai = None


def compute_embedding(text):
    if not OPENAI_API_KEY or openai is None:
        raise RuntimeError('OpenAI not configured')
    openai.api_key = OPENAI_API_KEY
    # Use OpenAI python client to create embedding
    resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=text)
    vec = resp['data'][0]['embedding']
    return vec


def main(skip_embeddings: bool):
    db = get_db()
    products_col = db[os.environ.get('PRODUCTS_COLLECTION', 'products')]
    chunks_col = db[os.environ.get('CHUNKS_COLLECTION', 'product_chunks')]

    with open('data/sample_products.json','r',encoding='utf-8') as f:
        products = json.load(f)

    print(f'Inserting {len(products)} products into {products_col.full_name}...')
    for p in products:
        products_col.update_one({'product_id': p['product_id']}, {'$set': p}, upsert=True)

    # create chunks
    total_chunks = 0
    for p in products:
        text = f"{p.get('title','')}\n\n{p.get('description','')}\n\nSpecs:\n{json.dumps(p.get('specs',{}))}\n\nReviews:\n{json.dumps(p.get('reviews',[]))}"
        chunks = chunk_text(text, max_chars=800)
        for i, c in enumerate(chunks):
            doc = {
                'chunk_id': f"{p['product_id']}_c{i}",
                'product_id': p['product_id'],
                'chunk_text': c,
                'metadata': {'title': p.get('title')}
            }
            if (not skip_embeddings) and OPENAI_API_KEY:
                try:
                    emb = compute_embedding(c)
                    if len(emb) != EMBEDDING_DIMS:
                        print('Warning: embedding size mismatch, expected', EMBEDDING_DIMS, 'got', len(emb))
                    doc['embedding'] = emb
                except Exception as e:
                    print('Failed to compute embedding for chunk', e)
            chunks_col.update_one({'chunk_id': doc['chunk_id']}, {'$set': doc}, upsert=True)
            total_chunks += 1

    print(f'Inserted/updated {total_chunks} chunks in {chunks_col.full_name}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-embeddings', action='store_true', help='Do not compute embeddings (default: compute if OPENAI_API_KEY is set)')
    args = parser.parse_args()
    main(args.skip_embeddings)
