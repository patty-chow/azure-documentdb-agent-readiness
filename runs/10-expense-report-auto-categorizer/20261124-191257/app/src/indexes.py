import asyncio
from .db import init_db, get_client

async def create_indexes():
    await init_db()
    client = get_client()
    db_name = 'sample_fintech_10'
    db = client[db_name]
    collection = db['expense_reports']
    # Create an index on status and on submitter+created_at
    await collection.create_index([('status', 1)], name='idx_status')
    await collection.create_index([('submitter', 1), ('created_at', -1)], name='idx_submitter_date')
    print('Indexes created')

if __name__ == '__main__':
    asyncio.run(create_indexes())
