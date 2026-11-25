#!/usr/bin/env python
"""Add engine-version context and per-question conclusions to report.json (run after run.py)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, 'report_rerun.json')
r = json.load(open(p))
r['engine'] = {
    'buildInfo_version': r['buildInfo'].get('version'),
    'note': 'buildInfo on documentdb-local reports only the MongoDB wire-compatibility version (7.0.0). Engine version taken from the container.',
    'image': 'ghcr.io/documentdb/documentdb/documentdb-local:latest',
    'image_label_version': '0.117.0',
    'image_revision': '28cc012070ce798361ed265251ec159180b7889f',
    'image_created': '2026-09-25T12:42:08Z',
    'pg_extensions': {'documentdb': '0.117-0', 'documentdb_core': '0.117-0', 'documentdb_extended_rum': '0.117-0'},
    'postgres_major': 17,
    'how_obtained': 'docker image inspect labels; docker exec psql -p 9712 "select extname, extversion from pg_extension"',
}
S = {s['step']: s for s in r['steps']}
def err(sid):
    e = S[sid]['error']; return f"code {e['code']} {e['codeName']}: {e['errmsg']}"
r['conclusions'] = [
    {'question': '(a) second vector index on the same path with a different name',
     'answer': 'Rejected. Identical options: ' + err('a2') + ' | Different kind (ivf): code 85 IndexOptionsConflict "An equivalent index already exists with a different name and options. Requested index: {...} existing index: {...}" | Different options (m=32): same code 85 IndexOptionsConflict message. The engine treats any cosmosSearch index on the same path as equivalent regardless of kind or options: one vector index per path is enforced.',
     'confidence': 'observed'},
    {'question': '(b) identical createIndexes repeated',
     'answer': 'No-op, ok:1. Response: {"raw":{"defaultShard":{"numIndexesBefore":2,"numIndexesAfter":2,"createdCollectionAutomatically":false,"note":"all indexes already exist","ok":1}},"ok":1}',
     'confidence': 'observed'},
    {'question': '(c) same name, different options',
     'answer': 'code 86 IndexKeySpecsConflict: "An existing index has the same name as the requested index. When index names are not specified, they are auto generated and can cause conflicts. Please refer to our documentation. Requested index: {...}, existing index: {...}". Same for different m, different similarity, and different kind under the same name.',
     'confidence': 'observed'},
    {'question': '(d) listIndexes key carrying the vector options',
     'answer': 'cosmosSearchOptions. The listIndexes entry is {"v":2,"key":{"v":"cosmosSearch"},"name":"v_hnsw","cosmosSearchOptions":{"kind":"vector-hnsw","dimensions":3,"similarity":"COS","m":16,"efConstruction":64}}; there is no cosmosSearch key. This contradicts the Learn page wording recorded in DECISIONS.md ("reports the options under cosmosSearch"), at least for the open-source gateway 0.117.',
     'confidence': 'observed'},
    {'question': '(e) vector-hnsw on an empty collection, then insert and search',
     'answer': 'Index created on the empty collection (numIndexesBefore 1 -> After 2); five inserts succeeded; a $search for [1,0,0] with k=3 immediately returned _ids [1, 4, 5] with scores 1.0, 0.9939, 0.1104. No build delay was observed locally.',
     'confidence': 'observed'},
    {'question': '(f) vector-ivf numLists 0 and numLists > document count',
     'answer': 'numLists=0: rejected, code 67 CannotCreateIndex, errmsg ends ":numLists must be greater than or equal to 0, but was 1" (the message has its values swapped: it reports 0 as the lower bound and 1 as the given value; the real check is numLists >= 1). numLists=100 on 5 documents: accepted (ok:1), and searches with default nProbes and nProbes=100 both returned the correct nearest neighbours [1, 4, 5]. The engine does not validate numLists against document count.',
     'confidence': 'observed'},
    {'question': '(g) dimension caps',
     'answer': 'vector-hnsw: 2001 uncompressed rejected (code 67 CannotCreateIndex "...:field cannot have more than 2000 dimensions for vector index"); 2000 uncompressed created; 4001 with compression half rejected (code 67 "...field cannot have more than 4000 dimensions for vector index"); 4000 with half created; 2001 with half created (half lifts the cap to 4000). vector-ivf: identical outcomes and identical messages for 2001/2000 uncompressed and 4001/4000 half. The 2,000/4,000 limits are enforced by the engine for both HNSW and IVF.',
     'confidence': 'observed'},
    {'question': '(h) BSON Binary vectors: insert, number[] query, Binary query',
     'answer': 'Documents with v as Binary subtype 9 (float32 BSON vector) and subtype 0 insert without error, both before and after the HNSW index exists, and plain find returns them intact. A $search with a number[] query vector and k=10 over 6 documents returned only the 3 number[] documents (_ids 1, 3, 2); the Binary-typed documents are silently absent. A Binary query vector (subtype 9 or subtype 0) fails with code 2 BadValue "Invalid type: expected an array type field, but received binData instead".',
     'confidence': 'observed'},
]
json.dump(r, open(p, 'w'), indent=2, default=str)
print('finalized', p, len(r['steps']), 'steps')
