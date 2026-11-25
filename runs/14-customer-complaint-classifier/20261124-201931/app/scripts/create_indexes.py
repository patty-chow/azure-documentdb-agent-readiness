"""Create indexes for the complaints collection.
This script attempts to create a standard single-field index and a cosmosSearch vector index.
Run with DOCUMENTDB_URI set in environment. Do not commit secrets.
"""
import os
from pymongo import MongoClient

DB_NAME = os.environ.get('DOCUMENTDB_DB_NAME', 'sample_banking_14')
URI = os.environ.get('DOCUMENTDB_URI')
if not URI:
    raise RuntimeError('DOCUMENTDB_URI required')

client = MongoClient(URI)
db = client[DB_NAME]
coll = db['complaints']
# Create a regular index on product_category
print('Creating single-field index on product_category...')
coll.create_index([('product_category', 1)], name='idx_product_category')

# Create a cosmosSearch vector index. This uses server-side createSearchIndexes command which may be specific to DocumentDB.
# The exact command shape depends on cluster version. Example payload (may need adjustment):
search_index = {
    'name': 'idx_embedding_hnsw',
    'definition': {
        'kind': 'cosmosSearch',
        'cosmosSearchOptions': {
            'indexType': 'vector-hnsw',
            'dimensions': 1536,
            'similarity': 'COS',
            'path': 'embedding'
        }
    }
}
try:
    print('Attempting createSearchIndexes command for vector index (may be DocumentDB-specific)...')
    res = db.command({'createSearchIndexes': 'complaints', 'indexes': [search_index]})
    print('createSearchIndexes result:', res)
except Exception as e:
    print('Failed to create cosmosSearch vector index via db.command():', e)
    print('Please use the DocumentDB portal or MCP tools to create a cosmosSearch index with dimensions=1536 and indexType=vector-hnsw')
