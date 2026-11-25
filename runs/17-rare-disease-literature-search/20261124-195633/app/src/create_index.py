from src.db import get_db
import os

def create_vector_index(dimensions=1536):
    db = get_db()
    coll_name = 'pubmed_chunks'
    index_spec = {
        'createIndexes': coll_name,
        'indexes': [
            {
                'key': {'embedding': 'cosmosSearch'},
                'name': 'idx_embedding_vector_diskann',
                'cosmosSearchOptions': {
                    'kind': 'vector-diskann',
                    'dimensions': dimensions,
                    'similarity': 'COS',
                    'maxDegree': 64,
                    'lBuild': 50
                }
            }
        ]
    }
    try:
        res = db.command(index_spec)
        print('createIndexes result:', res)
    except Exception as e:
        print('createIndexes failed:', e)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dims', type=int, default=int(os.getenv('OPENAI_EMBEDDING_DIMS', '1536')))
    args = parser.parse_args()
    create_vector_index(args.dims)
