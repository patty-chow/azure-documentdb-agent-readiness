"""m-vector extras for (b) and (d), run after run_main.py while its collections still exist.

b2  identical repeat of the vector-diskann createIndexes (managed-only kind)
b3  same name and same option values as v_hnsw, option keys in a different order
b4  same name as v_hnsw, defaults (m 16, efConstruction 64) omitted
d4  listIndexes on docs through the .global. host (MANAGED_GLOBAL_URI) as well as the plain host
"""
import pymongo

from common import DB_NAME, ENV, Recorder, ci, diskann, get_client

rec = Recorder('steps_extra.json')
client = get_client()
db = client[DB_NAME]

rec.run(db, 'b2', 'b', 'repeat the identical createIndexes for v_diskann (vector-diskann) on diskann',
        ci('diskann', [diskann('v_diskann')]), extra=True)
rec.run(db, 'b3', 'b', 'v_hnsw on docs with identical option values but option keys in a different order',
        ci('docs', [{'name': 'v_hnsw', 'key': {'v': 'cosmosSearch'},
                     'cosmosSearchOptions': {'similarity': 'COS', 'dimensions': 3, 'efConstruction': 64,
                                             'm': 16, 'kind': 'vector-hnsw'}}]), extra=True)
rec.run(db, 'b4', 'b', 'v_hnsw on docs with the documented defaults m 16 and efConstruction 64 omitted',
        ci('docs', [{'name': 'v_hnsw', 'key': {'v': 'cosmosSearch'},
                     'cosmosSearchOptions': {'kind': 'vector-hnsw', 'dimensions': 3, 'similarity': 'COS'}}]),
        extra=True)

gclient = pymongo.MongoClient(ENV['MANAGED_GLOBAL_URI'], serverSelectionTimeoutMS=30000, connectTimeoutMS=20000,
                              socketTimeoutMS=300000, appname='mt-vector-test')
r = rec.run(gclient.admin, 'd4.hello', 'd', 'hello through the .global. host (which gateway answers?)', {'hello': 1},
            extra=True)
rec.run(gclient[DB_NAME], 'd4', 'd', 'listIndexes on docs through the .global. host', {'listIndexes': 'docs'},
        extra=True)
print('wrote', rec.path)
