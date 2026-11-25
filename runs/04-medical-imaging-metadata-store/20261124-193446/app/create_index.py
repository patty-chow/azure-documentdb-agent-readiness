from app.db import get_collection
import os
from dotenv import load_dotenv

load_dotenv()
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "medical_images")
collection = get_collection(COLLECTION_NAME)

# Try to create the vector-ivf index using pymongo create_index with cosmosSearchOptions
try:
    opts = {
        'name': 'medical_images_embedding_ivf',
        'cosmosSearchOptions': {
            'kind': 'vector-ivf',
            'dimensions': int(os.environ.get('EMBEDDING_DIM', '1536')),
            'similarity': 'COS',
            'numLists': 100,
            'lBuild': 50
        }
    }
    print('Creating index...')
    res = collection.create_index([('embedding', 'cosmosSearch')], **opts)
    print('Create index result:', res)
except Exception as e:
    print('Index creation failed:', e)
    raise
