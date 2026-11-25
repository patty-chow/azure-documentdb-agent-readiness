import os
import json
from pymongo import MongoClient
from utils import bsonbinary_to_floats
import numpy as np

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    print("DOCUMENTDB_URI required in env to run verification")
    exit(1)

client = MongoClient(DOCUMENTDB_URI)
col = client["sample_retail_01"]["products"]

with open("data/sample_embeddings.json","r",encoding="utf-8") as f:
    pre = json.load(f)

# Use embedding for product 1 as a surrogate query
q_emb = pre["1"]

def cosine(a,b):
    a = np.asarray(a,dtype=np.float32)
    b = np.asarray(b,dtype=np.float32)
    return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))

docs = list(col.find({}, {"title":1, "description":1, "embedding":1}))
res = []
for d in docs:
    emb = d.get("embedding")
    if not emb: continue
    vec = bsonbinary_to_floats(emb)
    score = cosine(q_emb, vec)
    res.append((d.get("_id"), d.get("title"), score))
res.sort(key=lambda x: x[2], reverse=True)
print("Top results for synthetic query (embedding of product 1):")
for r in res[:10]:
    print(r)
