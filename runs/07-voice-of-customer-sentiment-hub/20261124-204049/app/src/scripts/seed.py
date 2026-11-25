"""Seed sample data and create search indexes where possible (best-effort). Uses pymongo sync client."""
from src.app.db import get_db, get_client
from src.app.processor import analyze_and_prepare
from src.app.models import make_feedback_doc
import os

SAMPLE = [
    {"channel": "email", "text": "I love the new product! It has excellent performance and I am very satisfied."},
    {"channel": "chat", "text": "The app crashed twice today. Very disappointed and frustrated."},
    {"channel": "survey", "text": "Service was okay but the response time was a bit slow."},
    {"channel": "email", "text": "Amazing experience, the team was helpful and resolved my issue quickly."},
    {"channel": "chat", "text": "I keep seeing an error when I try to upload a file. Please fix this bug."},
]

COLLECTION_NAME = 'feedbacks'

def create_search_indexes(client):
    db = client[os.getenv('DATABASE_NAME', 'sample_customer_360_07')]
    try:
        index_def = {
            "createSearchIndexes": COLLECTION_NAME,
            "indexes": [
                {
                    "name": "feedback_vector_hnsw",
                    "type": "vector-hnsw",
                    "vectorOptions": {
                        "vectorSize": int(os.getenv('EMBEDDING_DIM', '1536')),
                        "distanceMetric": "cosine",
                        "vectorPath": "embedding"
                    }
                },
                {
                    "name": "feedback_text_index",
                    "type": "text",
                    "textOptions": {
                        "path": "text",
                        "analyzer": "english"
                    }
                }
            ]
        }
        print('Attempting createSearchIndexes...')
        res = db.command(index_def)
        print('createSearchIndexes result:', res)
        return True
    except Exception as e:
        print('createSearchIndexes failed:', e)
        return False


def seed():
    client = get_client()
    db = get_db()
    coll = db[COLLECTION_NAME]
    created_idx = create_search_indexes(client)
    for item in SAMPLE:
        prepared = analyze_and_prepare(item)
        # dedupe by text and channel
        existing = coll.find_one({'text': prepared['text'], 'channel': prepared['channel']})
        if existing:
            print('Skipping existing:', prepared['text'][:60])
            continue
        res = coll.insert_one(prepared)
        print('Inserted id:', res.inserted_id)
    print('Seed done. Index creation verified:', created_idx)

if __name__ == '__main__':
    seed()
