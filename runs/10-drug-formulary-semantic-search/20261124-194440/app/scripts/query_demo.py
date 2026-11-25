import os
import argparse
from dotenv import load_dotenv
from db import get_collection
import openai

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = int(os.environ.get("EMBED_DIMENSIONS", "1536"))

parser = argparse.ArgumentParser()
parser.add_argument("--query", required=True)
args = parser.parse_args()

query = args.query
resp = openai.Embedding.create(model=EMBED_MODEL, input=query)
qvec = resp['data'][0]['embedding']

coll = get_collection()
pipeline = [
    {"$search": {"cosmosSearch": {"path": "embedding", "vector": qvec, "k": 10, "lSearch": 100}}},
    {"$project": {"name": 1, "indications": 1, "dosing":1, "score": {"$meta": "searchScore"}}},
    {"$limit": 10}
]

print("Running vector search against DocumentDB...")
hits = list(coll.aggregate(pipeline))
for i, h in enumerate(hits, start=1):
    print(i, h.get('name'), f"score={h.get('score')}")
