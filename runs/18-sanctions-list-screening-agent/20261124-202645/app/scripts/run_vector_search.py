import os
from pymongo import MongoClient

uri = os.environ.get('DOCUMENTDB_URI')
if not uri:
    raise SystemExit('DOCUMENTDB_URI not set')
client = MongoClient(uri)
db = client['sample_banking_18']
coll = db['sanctions']

qvec = [0.0]*1536
qvec[0] = 1.0
pipeline = [
    {"$search": {"cosmosSearch": {"vector": qvec, "path": "embedding", "k": 5}, "returnStoredSource": True}},
    {"$project": {"score": {"$meta": "searchScore"}, "document": "$$ROOT"}},
]

res = list(coll.aggregate(pipeline))
print('results count:', len(res))
for r in res:
    print(r.get('score'), r.get('document', {}).get('_id'))
