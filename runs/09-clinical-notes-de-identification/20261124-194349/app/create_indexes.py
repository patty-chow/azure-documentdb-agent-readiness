import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    uri = os.environ.get('DOCUMENTDB_URI')
    if not uri:
        raise SystemExit('DOCUMENTDB_URI required')
    client = AsyncIOMotorClient(uri, tls=True)
    try:
        db = client.get_default_database()
    except Exception:
        db = None
    if not db:
        db = client['sample_healthcare_09']
    coll = db['deid_notes']
    idx1 = await coll.create_index([('sourceId', 1)], name='idx_sourceId')
    idx2 = await coll.create_index([('created_at', 1)], name='idx_created_at')
    print('Created indexes:', idx1, idx2)
    client.close()

if __name__ == '__main__':
    asyncio.run(main())
