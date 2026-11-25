import os
import re
import json
from pymongo import MongoClient

uri = os.environ.get('DOCUMENTDB_URI')
if not uri:
    raise SystemExit('DOCUMENTDB_URI not set')
client = MongoClient(uri)
db = client['sample_banking_18']
coll = db['sanctions']

name = os.environ.get('DEMO_NAME', 'Person 1')

# Simple fallback embedding: put 1.0 in first dim if name contains digit '1', else zeros
qvec = [0.0]*1536
if '1' in name:
    qvec[0] = 1.0

# vector search
pipeline = [
    {"$search": {"cosmosSearch": {"vector": qvec, "path": "embedding", "k": 10}, "returnStoredSource": True}},
    {"$project": {"score": {"$meta": "searchScore"}, "document": "$$ROOT"}},
]
vec_results = list(coll.aggregate(pipeline))

candidates = {}
for r in vec_results:
    score = r.get('score', 0.0)
    doc = r.get('document', {})
    doc_id = doc.get('_id')
    candidates[doc_id] = {'id': doc_id, 'name': doc.get('name'), 'vector_score': float(score), 'regex_score': 0.0}

# regex
pattern = re.compile(re.escape(name), re.IGNORECASE)
regex_cursor = coll.find({"$or": [{"name": {"$regex": pattern.pattern, "$options": "i"}}, {"alt_names": {"$elemMatch": {"$regex": pattern.pattern, "$options": "i"}}}]}, projection={"name": 1})
for d in regex_cursor:
    doc_id = d.get('_id')
    if doc_id in candidates:
        candidates[doc_id]['regex_score'] = 1.0
    else:
        candidates[doc_id] = {'id': doc_id, 'name': d.get('name'), 'vector_score': 0.0, 'regex_score': 1.0}

# combine
v_weight = float(os.environ.get('VECTOR_WEIGHT', '0.7'))
r_weight = float(os.environ.get('REGEX_WEIGHT', '0.3'))
merged = []
for c in candidates.values():
    combined = v_weight * c['vector_score'] + r_weight * c['regex_score']
    if combined >= float(os.environ.get('HIGH_CONFIDENCE', '0.8')):
        action = 'Review immediately - high confidence match'
    elif combined >= float(os.environ.get('MEDIUM_CONFIDENCE', '0.5')):
        action = 'Manual review - possible match'
    else:
        action = 'No action needed'
    merged.append({'id': c['id'], 'name': c['name'], 'confidence': combined, 'action': action, 'scores': {'vector': c['vector_score'], 'regex': c['regex_score']}})

merged_sorted = sorted(merged, key=lambda x: x['confidence'], reverse=True)
print(json.dumps({'query': {'name': name}, 'candidates': merged_sorted}, indent=2))
