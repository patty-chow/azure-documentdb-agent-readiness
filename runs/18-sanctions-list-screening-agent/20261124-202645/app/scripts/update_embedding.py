import os
import math
from pymongo import MongoClient

uri = os.environ.get('DOCUMENTDB_URI')
if not uri:
    raise SystemExit('DOCUMENTDB_URI not set')
client = MongoClient(uri)
db = client['sample_banking_18']
coll = db['sanctions']

vec = [0.0]*1536
vec[0] = 1.0
res = coll.update_one({'_id': 'sanction_1'}, {'$set': {'embedding': vec}})
print('matched:', res.matched_count, 'modified:', res.modified_count)
