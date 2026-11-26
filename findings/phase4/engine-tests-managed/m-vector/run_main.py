"""m-vector parts (a)-(f), (h), (i) against the managed cluster, database mt_vector only.

Part (g), the build-delay poll, is in run_g_timing.py. Cleanup (dropDatabase) is in run_z_cleanup.py.
Every collection used here is dropped first, so a rerun is safe. Never prints credentials.
"""
import struct

from bson import Binary
from bson.binary import BinaryVectorDtype

from common import (DB_NAME, DOCS, Recorder, ci, diskann, get_client, hnsw, ids_of, ivf, search)

rec = Recorder('steps_main.json')
client = get_client()
db = client[DB_NAME]

COLLS = ['docs', 'alias_key', 'diskann', 'bin', 'bin_diskann', 'ivf']
for c in COLLS:
    db[c].drop()

# ---------------------------------------------------------------- (a) (b) (c) (d)
rec.run(db, 'a0', 'a', 'setup: insert five 3-dimensional number[] documents into docs',
        {'insert': 'docs', 'documents': DOCS, 'ordered': True}, oss_step='setup')
rec.run(db, 'a1', 'a', 'create vector-hnsw v_hnsw on path v', ci('docs', [hnsw('v_hnsw')]), oss_step='a1')
rec.run(db, 'a2', 'a', 'second vector-hnsw on the same path, different name (v_hnsw_two), identical options',
        ci('docs', [hnsw('v_hnsw_two')]), oss_step='a2')
rec.run(db, 'a3', 'a', 'second vector index on the same path, different name, different kind (vector-ivf numLists 1)',
        ci('docs', [ivf('v_ivf_second', numLists=1)]), oss_step='a3')
rec.run(db, 'a4', 'a', 'second vector-hnsw on the same path, different name, different options (m 32)',
        ci('docs', [hnsw('v_hnsw_m32', m=32)]), oss_step='a4')
rec.run(db, 'a5', 'a', 'second vector index on the same path, different name, kind vector-diskann',
        ci('docs', [diskann('v_diskann_second')]), extra=True)

rec.run(db, 'b1', 'b', 'repeat the identical createIndexes for v_hnsw', ci('docs', [hnsw('v_hnsw')]), oss_step='b1')

rec.run(db, 'c1', 'c', 'same name v_hnsw, different options (m 32)', ci('docs', [hnsw('v_hnsw', m=32)]), oss_step='c1')
rec.run(db, 'c2', 'c', 'same name v_hnsw, different similarity (L2)', ci('docs', [hnsw('v_hnsw', similarity='L2')]),
        oss_step='c2')
rec.run(db, 'c3', 'c', 'same name v_hnsw, different kind (vector-ivf)', ci('docs', [ivf('v_hnsw', numLists=1)]),
        oss_step='c3')
rec.run(db, 'c4', 'c', 'same name v_hnsw, different kind (vector-diskann)', ci('docs', [diskann('v_hnsw')]),
        extra=True)

r = rec.run(db, 'd1', 'd', 'listIndexes on docs: are the vector options under cosmosSearch, cosmosSearchOptions or both?',
            {'listIndexes': 'docs'}, oss_step='d1')
if r['outcome'] == 'ok':
    for ix in r['response']['cursor']['firstBatch']:
        if ix.get('name') == 'v_hnsw':
            print('[d1] RAW v_hnsw index document:', ix)
            print('[d1] top-level keys:', sorted(ix.keys()))

# extra: does createIndexes accept the options under a 'cosmosSearch' key (the key Learn's getIndexes sample shows)?
rec.run(db, 'd2a', 'd', 'setup: create empty collection alias_key', {'create': 'alias_key'}, extra=True, quiet=True)
rec.run(db, 'd2', 'd', "createIndexes with the options under 'cosmosSearch' (Learn's listIndexes key) instead of 'cosmosSearchOptions'",
        ci('alias_key', [{'name': 'v_alias', 'key': {'v': 'cosmosSearch'},
                          'cosmosSearch': {'kind': 'vector-hnsw', 'dimensions': 3, 'similarity': 'COS',
                                           'm': 16, 'efConstruction': 64}}]), extra=True)
rec.run(db, 'd3', 'd', 'listIndexes on alias_key after the cosmosSearch-key attempt', {'listIndexes': 'alias_key'},
        extra=True)

# ---------------------------------------------------------------- (e) DiskANN, 3 dimensions
rec.run(db, 'e0', 'e', 'setup: insert the same five documents into diskann',
        {'insert': 'diskann', 'documents': DOCS, 'ordered': True})
rec.run(db, 'e1', 'e', 'create vector-diskann v_diskann (dimensions 3, COS, maxDegree 32, lBuild 50)',
        ci('diskann', [diskann('v_diskann')]), oss_step='local-gateway-parity/06-vector-diskann')
r = rec.run(db, 'e2', 'e', 'listIndexes on diskann: raw vector-diskann index document', {'listIndexes': 'diskann'})
if r['outcome'] == 'ok':
    for ix in r['response']['cursor']['firstBatch']:
        if ix.get('name') == 'v_diskann':
            print('[e2] RAW v_diskann index document:', ix)
rec.run(db, 'e3', 'e', '$search cosmosSearch [1,0,0] k 3 on the DiskANN index (expect _ids 1, 4, 5)',
        search('diskann', [1.0, 0.0, 0.0], k=3), extra=True)

# ---------------------------------------------------------------- (f) dimension caps, one empty collection per case
cases = [
    ('f1', 'hnsw', 2001, None, 'g1'), ('f2', 'hnsw', 2000, None, 'g2'),
    ('f3', 'hnsw', 4001, 'half', 'g3'), ('f4', 'hnsw', 4000, 'half', 'g4'),
    ('f5', 'ivf', 2001, None, 'g5'), ('f6', 'ivf', 2000, None, 'g6'),
    ('f7', 'ivf', 4001, 'half', 'g7'), ('f8', 'ivf', 4000, 'half', 'g8'),
    ('f9', 'diskann', 2001, None, None), ('f10', 'diskann', 2000, None, None),
    ('f11', 'diskann', 16001, 'pq', None), ('f12', 'diskann', 16000, 'pq', None),
    # extras
    ('f13', 'hnsw', 2001, 'half', 'g9'), ('f14', 'diskann', 4000, 'half', None),
    ('f15', 'diskann', 2001, 'pq', None),
]
EXTRA_F = {'f10', 'f13', 'f14', 'f15'}
for sid, kind, dims, comp, oss in cases:
    coll = f'dims_{kind}_{dims}_{comp or "none"}'
    db[coll].drop()
    rec.run(db, f'{sid}.create', 'f', f'setup: create empty collection {coll}', {'create': coll},
            extra=sid in EXTRA_F, quiet=True)
    opts = {} if comp is None else {'compression': comp}
    builder = {'hnsw': hnsw, 'ivf': ivf, 'diskann': diskann}[kind]
    spec = builder(f'ix_{kind}_{dims}_{comp or "none"}', dims=dims, **opts)
    rec.run(db, sid, 'f', f'vector-{kind} dimensions {dims} compression {comp or "none"} on empty {coll}',
            ci(coll, [spec]), extra=sid in EXTRA_F, oss_step=oss)

# ---------------------------------------------------------------- (h) BSON Binary vectors
bin9 = Binary.from_vector([1.0, 0.0, 0.0], BinaryVectorDtype.FLOAT32)      # subtype 9, float32 BSON vector
bin0 = Binary(struct.pack('<3f', 1.0, 0.0, 0.0), 0)                         # subtype 0, packed little-endian float32
bin9_after = Binary.from_vector([0.0, 1.0, 0.0], BinaryVectorDtype.FLOAT32)
BIN_DOCS = [{'_id': 10, 'tag': 'bin9', 'v': bin9}, {'_id': 11, 'tag': 'bin0', 'v': bin0}]

for coll, builder, prefix, extra in (('bin', hnsw, 'h', False), ('bin_diskann', diskann, 'hd', True)):
    oss = (lambda s: s) if not extra else (lambda s: None)
    rec.run(db, f'{prefix}1a', 'h', f'insert three number[] documents (_id 1-3) into {coll}',
            {'insert': coll, 'documents': DOCS[:3], 'ordered': True}, extra=extra, oss_step=oss('setup'))
    rec.run(db, f'{prefix}1b', 'h', f'insert two documents whose v is BSON Binary (subtype 9 float32 [1,0,0]; subtype 0 packed float32 [1,0,0]) into {coll}',
            {'insert': coll, 'documents': BIN_DOCS, 'ordered': True}, extra=extra, oss_step=oss('h1'))
    rec.run(db, f'{prefix}2', 'h', f'create {builder.__name__} index v_{builder.__name__} on {coll} (collection holds number[] and Binary v)',
            ci(coll, [builder(f'v_{builder.__name__}')]), extra=extra, oss_step=oss('h2'))
    rec.run(db, f'{prefix}3', 'h', f'insert a Binary subtype 9 v ([0,1,0], _id 12) after the index exists on {coll}',
            {'insert': coll, 'documents': [{'_id': 12, 'tag': 'bin9_after', 'v': bin9_after}], 'ordered': True},
            extra=extra, oss_step=oss('h3'))
    rec.run(db, f'{prefix}4', 'h', f'$search with a number[] query vector [1,0,0], k 10, over {coll} (3 number[] + 3 Binary docs)',
            search(coll, [1.0, 0.0, 0.0], k=10), extra=extra, oss_step=oss('h4'))
    rec.run(db, f'{prefix}5', 'h', f'$search with a Binary subtype 9 query vector on {coll}',
            search(coll, bin9, k=10), extra=extra, oss_step=oss('h5'))
    rec.run(db, f'{prefix}6', 'h', f'$search with a Binary subtype 0 query vector on {coll}',
            search(coll, bin0, k=10), extra=extra, oss_step=oss('h6'))
    rec.run(db, f'{prefix}7', 'h', f'plain find of the Binary-typed documents (_id 10, 11, 12) in {coll}',
            {'find': coll, 'filter': {'_id': {'$in': [10, 11, 12]}}}, extra=extra, oss_step=oss('h7'))

# ---------------------------------------------------------------- (i) IVF numLists
rec.run(db, 'i0a', 'i', 'setup: insert the five documents into ivf', {'insert': 'ivf', 'documents': DOCS, 'ordered': True})
rec.run(db, 'i0', 'i', 'control: vector-ivf numLists 1 on 5 documents', ci('ivf', [ivf('v_ivf1', numLists=1)]),
        oss_step='f0')
rec.run(db, 'i0b', 'i', 'drop the control index v_ivf1', {'dropIndexes': 'ivf', 'index': 'v_ivf1'})
rec.run(db, 'i1', 'i', 'vector-ivf numLists 0', ci('ivf', [ivf('v_ivf0', numLists=0)]), oss_step='f1')
rec.run(db, 'i2', 'i', 'vector-ivf numLists 100 on 5 documents (numLists above the document count)',
        ci('ivf', [ivf('v_ivf100', numLists=100)]), oss_step='f2')
rec.run(db, 'i3', 'i', '$search [1,0,0] k 3 on the numLists 100 index, default nProbes',
        search('ivf', [1.0, 0.0, 0.0], k=3), oss_step='f3')
rec.run(db, 'i4', 'i', '$search [1,0,0] k 3 on the numLists 100 index, nProbes 100',
        search('ivf', [1.0, 0.0, 0.0], k=3, extra={'nProbes': 100}), oss_step='f4')

# ---------------------------------------------------------------- final index state
names = db.list_collection_names()
for c in sorted(names):
    rec.run(db, f'final.listIndexes.{c}', 'final', f'record final index state of {c}', {'listIndexes': c}, quiet=True)
print('collections:', sorted(names))
print('wrote', rec.path, len(rec.steps), 'steps')
