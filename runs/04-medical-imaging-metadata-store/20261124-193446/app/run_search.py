import sys
from app.db import get_collection
from compute_vector import load_dotenv
import json
import numpy as np
from compute_vector import load_dotenv

# We'll reuse the deterministic vector generation logic from compute_vector.py
import os
EMBEDDING_DIM = int(os.environ.get('EMBEDDING_DIM','1536'))

text = ' '.join(sys.argv[1:]) if len(sys.argv)>1 else 'pulmonary nodule'
seed = abs(hash(text)) % (2**32)
import numpy as np
rng = np.random.RandomState(seed)
arr = rng.normal(size=(EMBEDDING_DIM,)).astype(float)
arr = arr / (np.linalg.norm(arr) or 1.0)
qvec = arr.tolist()

collection = get_collection(os.environ.get('COLLECTION_NAME','medical_images'))

pipeline = [
    {
        "$search": {
            "cosmosSearch": {
                "path": "embedding",
                "vector": qvec,
                "k": 5,
                "lSearch": 200
            }
        }
    },
    {"$project": {"modality":1, "body_part":1, "findings":1, "score":{"$meta":"searchScore"}}}
]

print('Running search for:', text)
for doc in collection.aggregate(pipeline):
    print('---')
    print('id:', doc.get('_id'))
    print('modality:', doc.get('modality'))
    print('body_part:', doc.get('body_part'))
    print('findings:', doc.get('findings'))
    print('score:', doc.get('score'))
