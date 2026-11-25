import sys, json
import numpy as np
from dotenv import load_dotenv
import os
load_dotenv()
EMBEDDING_DIM = int(os.environ.get('EMBEDDING_DIM','1536'))
text = ' '.join(sys.argv[1:]) if len(sys.argv)>1 else 'pulmonary nodule'
seed = abs(hash(text)) % (2**32)
rng = np.random.RandomState(seed)
arr = rng.normal(size=(EMBEDDING_DIM,)).astype(np.float32)
arr = arr / np.linalg.norm(arr)
print(json.dumps(arr.tolist()))
