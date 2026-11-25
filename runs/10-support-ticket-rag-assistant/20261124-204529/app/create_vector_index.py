from src.db import get_client, DB_NAME, COLLECTION

client = get_client()
db = client[DB_NAME]

cmd = {
    'createIndexes': COLLECTION,
    'indexes': [
        {
            'key': {'embedding': 'cosmosSearch'},
            'name': 'kb_embedding_hnsw_py',
            'cosmosSearchOptions': {
                'kind': 'vector-hnsw',
                'dimensions': 1536,
                'similarity': 'COS',
                'maxDegree': 64,
                'lBuild': 100
            }
        }
    ]
}

print('Creating index...')
res = db.command(cmd)
print(res)
