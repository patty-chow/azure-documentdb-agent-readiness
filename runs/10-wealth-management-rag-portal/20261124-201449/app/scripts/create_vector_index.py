"""Attempt to create a cosmosSearch vector index on research_documents.

This script will try to use the driver's database.command('createIndexes', ...) to create an index
with cosmosSearchOptions. If that fails, run the corresponding MCP server tool (documentdb_create_index)
that is bundled with the sample environment.
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
DOCUMENTDB_URI = os.environ.get('DOCUMENTDB_URI')
DB_NAME = os.environ.get('DB_NAME','sample_banking_10')
DIM = int(os.environ.get('EMBEDDING_DIM','1536'))

if not DOCUMENTDB_URI:
    print('DOCUMENTDB_URI not set. Aborting.')
    raise SystemExit(1)

client = MongoClient(DOCUMENTDB_URI, retryWrites=False)
db = client[DB_NAME]

index_spec = {
    'name': 'vector_search_embedding',
    'key': {'embedding': 'cosmosVector'},
    'cosmosSearchOptions': {
        'kind': 'vector-hnsw',
        'dimensions': DIM,
        'similarity': 'COS',
        # hnsw params (tuning for small sample)
        'm': 16,
        'efConstruction': 200,
        'efSearch': 64
    }
}

try:
    res = db.command('createIndexes', 'research_documents', indexes=[index_spec])
    print('createIndexes result:', res)
except Exception as e:
    print('Driver createIndexes failed:', e)
    print('\nIf this fails because the driver blocks vendor extensions, use the MCP tool to create the index:')
    print('documentdb_create_index --db sample_banking_10 --collection research_documents --keys "{\"embedding\":\"cosmosVector\"}" --options "{\"cosmosSearchOptions\":{...}}"')
