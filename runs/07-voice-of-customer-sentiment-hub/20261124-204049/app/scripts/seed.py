import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from src.db import init_db, get_client
from src.models import Feedback
from src.ingest import enrich_and_store, create_search_indexes

SAMPLE = [
    {"channel": "email", "source_id": "E-001", "text": "I love the new product. It saved me time and the support was helpful."},
    {"channel": "chat", "source_id": "C-102", "text": "The app crashes sometimes on launch. Very frustrating."},
    {"channel": "survey", "source_id": "S-201", "text": "Overall satisfied, but the billing section is confusing."},
    {"channel": "email", "source_id": "E-002", "text": "Great features, but performance is slow when uploading large files."},
    {"channel": "chat", "source_id": "C-103", "text": "Agent resolved my issue quickly, very happy."}
]

async def main():
    db = await get_client()
    # Initialize Beanie
    await init_db([Feedback])
    # Create search indexes (best-effort)
    created = await create_search_indexes(db[os.getenv('DB_NAME','sample_customer_360_07')])
    print('create_search_indexes result:', created)

    # Insert sample docs if not present
    for item in SAMPLE:
        exists = await Feedback.find_one((Feedback.source_id == item['source_id']))
        if not exists:
            print('Ingesting', item['source_id'])
            try:
                await enrich_and_store(item)
            except Exception as e:
                print('Enrich/store failed:', e)

if __name__ == '__main__':
    asyncio.run(main())
