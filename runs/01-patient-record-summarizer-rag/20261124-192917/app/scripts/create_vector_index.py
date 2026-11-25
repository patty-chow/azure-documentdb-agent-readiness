"""Create a cosmosSearch vector-hnsw index on the patient_chunks collection using runCommand (createIndexes).
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.db import get_db

DB = get_db()
coll_name = 'patient_chunks'

cmd = {
    'createIndexes': coll_name,
    'indexes': [
        {
            'name': 'idx_embedding_hnsw',
            'key': {'embedding': 'cosmosSearch'},
            'cosmosSearchOptions': {
                'kind': 'vector-hnsw',
                'dimensions': int(__import__('os').environ.get('EMBEDDING_DIMS', '1536')),
                'similarity': 'COS',
                'm': 16,
                'efConstruction': 200
            }
        }
    ]
}

print('Running createIndexes command...')
res = DB.command(cmd)
print('createIndexes result:', res)

# also ensure a standard index on patientId for efficient filtering
print('Ensuring scalar index on patientId...')
idx_res = DB[coll_name].create_index([('patientId', 1)], name='idx_patientId')
print('patientId index:', idx_res)
