import sys
import json
from app.db import get_db
import os
from dotenv import load_dotenv

load_dotenv()
# optional OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    openai = None
    OPENAI_AVAILABLE = False

OPENAI_KEY = os.getenv('OPENAI_API_KEY')
MODEL = os.getenv('OPENAI_MODEL','text-embedding-3-small')
if OPENAI_AVAILABLE and OPENAI_KEY:
    openai.api_key = OPENAI_KEY

query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else "Spanish-speaking cardiologist accepting Medicare"
k = int(sys.argv[2]) if len(sys.argv) > 2 else 5

DIMS = 1536

def make_embedding(text: str):
    if OPENAI_AVAILABLE and OPENAI_KEY:
        resp = openai.Embedding.create(input=text, model=MODEL)
        return resp['data'][0]['embedding']
    else:
        import hashlib
        h = hashlib.sha256(text.encode('utf-8')).digest()
        floats = []
        for i in range(DIMS):
            b = h[i % len(h)]
            floats.append((b / 255.0) * 2.0 - 1.0)
        return floats

vec = make_embedding(query)

db = get_db('sample_healthcare_20')
coll = db['providers']

pipeline = [
    {"$search": {"cosmosSearch": {"vector": vec, "path": "embedding", "k": k}, "returnStoredSource": True}},
    {"$project": {"score": {"$meta":"searchScore"}, "doc": "$$ROOT"}},
    {"$limit": k}
]

res = list(coll.aggregate(pipeline))
print(json.dumps(res, indent=2, default=str))
