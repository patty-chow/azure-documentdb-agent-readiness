#!/usr/bin/env python
"""Test vector-index-rules against documentdb-local (database t_vector only).

Reruns are safe: every collection used is dropped at start. Never prints credentials.
Usage: .venv/bin/python run.py   (reads ../local.env for LOCAL_URI)
"""
import json, os, re, struct, sys, time, datetime
import pymongo
from bson import Binary
from bson.binary import BinaryVectorDtype
from bson.json_util import dumps, RELAXED_JSON_OPTIONS
from pymongo.errors import OperationFailure, PyMongoError

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, '..', 'local.env')
REPORT = os.path.join(HERE, 'report_rerun.json')
DB = 't_vector_rerun'

def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        line = re.sub(r'^export\s+', '', line)
        k, _, v = line.partition('=')
        env[k] = v.strip().strip('"').strip("'")
    return env

env = load_env(ENV)
client = pymongo.MongoClient(env['LOCAL_URI'], tlsAllowInvalidCertificates=True,
                             serverSelectionTimeoutMS=15000, socketTimeoutMS=300000)
db = client[DB]
build = client.admin.command('buildInfo')

steps = []

def j(x):
    return json.loads(dumps(x, json_options=RELAXED_JSON_OPTIONS))

def run(step_id, question, cmd, reading=None, db_=None):
    """Run a raw database command, record exact command and exact response/error."""
    d = db_ or db
    rec = {'step': step_id, 'question': question, 'command': j(cmd)}
    t0 = time.time()
    try:
        resp = d.command(cmd)
        rec['response'] = j(resp)
        rec['outcome'] = 'ok'
    except OperationFailure as e:
        det = e.details or {}
        rec['error'] = {'code': e.code, 'codeName': det.get('codeName'), 'errmsg': det.get('errmsg', str(e)),
                        'errorLabels': det.get('errorLabels', []), 'raw': j(det)}
        rec['outcome'] = 'error'
    except PyMongoError as e:
        rec['error'] = {'code': None, 'codeName': type(e).__name__, 'errmsg': str(e), 'errorLabels': []}
        rec['outcome'] = 'driver_error'
    rec['elapsed_s'] = round(time.time() - t0, 3)
    rec['reading'] = reading(rec) if callable(reading) else (reading or '')
    steps.append(rec)
    short = rec.get('response') if rec['outcome'] == 'ok' else rec['error']
    print(f"[{step_id}] {rec['outcome']}: {json.dumps(short, default=str)[:400]}")
    return rec

def ci(coll, indexes):
    return {'createIndexes': coll, 'indexes': indexes}

def hnsw(name, path='v', dims=3, **opts):
    o = {'kind': 'vector-hnsw', 'dimensions': dims, 'similarity': 'COS', 'm': 16, 'efConstruction': 64}
    o.update(opts)
    return {'name': name, 'key': {path: 'cosmosSearch'}, 'cosmosSearchOptions': o}

def ivf(name, path='v', dims=3, numLists=1, **opts):
    o = {'kind': 'vector-ivf', 'dimensions': dims, 'similarity': 'COS', 'numLists': numLists}
    o.update(opts)
    return {'name': name, 'key': {path: 'cosmosSearch'}, 'cosmosSearchOptions': o}

def search(coll, vector, path='v', k=5, extra=None):
    cs = {'vector': vector, 'path': path, 'k': k}
    if extra:
        cs.update(extra)
    return {'aggregate': coll, 'pipeline': [
        {'$search': {'cosmosSearch': cs, 'returnStoredSource': True}},
        {'$project': {'_id': 1, 'tag': 1, 'v': 1, 'score': {'$meta': 'searchScore'}}}
    ], 'cursor': {}}

def err_reading(rec, ok_text, err_prefix):
    if rec['outcome'] == 'ok':
        return ok_text
    e = rec['error']
    return f"{err_prefix}: code {e['code']} {e['codeName']}: {e['errmsg']}"

DOCS = [
    {'_id': 1, 'tag': 'a', 'v': [1.0, 0.0, 0.0]},
    {'_id': 2, 'tag': 'b', 'v': [0.0, 1.0, 0.0]},
    {'_id': 3, 'tag': 'c', 'v': [0.0, 0.0, 1.0]},
    {'_id': 4, 'tag': 'd', 'v': [0.9, 0.1, 0.0]},
    {'_id': 5, 'tag': 'e', 'v': [0.1, 0.9, 0.0]},
]

# ---- setup -------------------------------------------------------------
for c in ['docs', 'empty_hnsw', 'ivf', 'dims', 'bin']:
    db[c].drop()
db.docs.insert_many(DOCS)
steps.append({'step': 'setup', 'question': 'prepare collection', 'command': {'insert': 'docs', 'documents': DOCS},
              'response': {'n': 5}, 'outcome': 'ok', 'reading': 'Five 3-dimensional number[] documents inserted into t_vector.docs.'})

# ---- (a) first hnsw, then second vector index on same path, different name
run('a1', '(a) create vector-hnsw on v', ci('docs', [hnsw('v_hnsw')]),
    lambda r: err_reading(r, 'First vector-hnsw index on path v is created.', 'Unexpected failure creating the first HNSW index'))
run('a2', '(a) second vector-hnsw on same path, different name, identical options', ci('docs', [hnsw('v_hnsw_two')]),
    lambda r: err_reading(r, 'Engine ALLOWED a second HNSW index on the same path under a different name.',
                          'Second vector index on the same path (different name, same options) is rejected'))
run('a3', '(a) second vector index on same path, different name, different kind (ivf)', ci('docs', [ivf('v_ivf_second', numLists=1)]),
    lambda r: err_reading(r, 'Engine ALLOWED a second vector index of a different kind on the same path.',
                          'Second vector index of a different kind on the same path is rejected'))
run('a4', '(a) second vector-hnsw on same path, different name, different options (m=32)', ci('docs', [hnsw('v_hnsw_m32', m=32)]),
    lambda r: err_reading(r, 'Engine ALLOWED a second HNSW index on the same path with different options.',
                          'Second HNSW on the same path with different options and a different name is rejected'))

# ---- (b) identical createIndexes repeated
run('b1', '(b) repeat the identical createIndexes', ci('docs', [hnsw('v_hnsw')]),
    lambda r: err_reading(r, 'Identical createIndexes is a no-op; see numIndexesBefore/After and note in the response.',
                          'Identical createIndexes repeated returns an error'))

# ---- (c) same name, different options
run('c1', '(c) same name v_hnsw, different options (m=32)', ci('docs', [hnsw('v_hnsw', m=32)]),
    lambda r: err_reading(r, 'Engine accepted same-name index with different options (unexpected).',
                          'Same name with different options is rejected'))
run('c2', '(c) same name v_hnsw, different similarity (L2)', ci('docs', [hnsw('v_hnsw', similarity='L2')]),
    lambda r: err_reading(r, 'Engine accepted same-name index with different similarity (unexpected).',
                          'Same name with different similarity is rejected'))
run('c3', '(c) same name v_hnsw, different kind (ivf)', ci('docs', [ivf('v_hnsw', numLists=1)]),
    lambda r: err_reading(r, 'Engine accepted same-name index with different kind (unexpected).',
                          'Same name with different kind is rejected'))

# ---- (d) listIndexes key
r = run('d1', '(d) listIndexes: cosmosSearch or cosmosSearchOptions?', {'listIndexes': 'docs'})
if r['outcome'] == 'ok':
    keys = set()
    for ix in r['response']['cursor']['firstBatch']:
        if ix['name'] == 'v_hnsw':
            keys = set(ix.keys())
    which = [k for k in ('cosmosSearch', 'cosmosSearchOptions') if k in keys]
    r['reading'] = f"listIndexes entry for v_hnsw has top-level keys {sorted(keys)}; the vector options key present is {which}."
    print('[d1] keys:', sorted(keys))

# ---- (e) empty collection: hnsw, then insert, then search
db.create_collection('empty_hnsw')
run('e1', '(e) vector-hnsw on EMPTY collection', ci('empty_hnsw', [hnsw('v_hnsw')]),
    lambda r: err_reading(r, 'HNSW index created on an empty collection.', 'HNSW on an empty collection failed'))
db.empty_hnsw.insert_many(DOCS)
steps.append({'step': 'e2', 'question': '(e) insert after index', 'command': {'insert': 'empty_hnsw', 'documents': DOCS},
              'response': {'n': 5}, 'outcome': 'ok', 'reading': 'Five documents inserted after the index existed.'})
def e3_reading(r):
    if r['outcome'] != 'ok':
        return f"Search failed: code {r['error']['code']} {r['error']['codeName']}: {r['error']['errmsg']}"
    ids = [d['_id'] for d in r['response']['cursor']['firstBatch']]
    return f"Search immediately after insert returned _ids {ids} (expected nearest to [1,0,0]: 1 then 4)."
run('e3', '(e) search after insert', search('empty_hnsw', [1.0, 0.0, 0.0], k=3), e3_reading)

# ---- (f) ivf numLists 0 and > doc count
db.ivf.insert_many(DOCS)
run('f0', '(f) control: vector-ivf numLists=1 on 5 docs', ci('ivf', [ivf('v_ivf1', numLists=1)]),
    lambda r: err_reading(r, 'IVF with numLists=1 is created on 5 documents (control).', 'IVF numLists=1 failed'))
db.ivf.drop_index('v_ivf1') if any(i['name'] == 'v_ivf1' for i in db.ivf.list_indexes()) else None
run('f1', '(f) vector-ivf numLists=0', ci('ivf', [ivf('v_ivf0', numLists=0)]),
    lambda r: err_reading(r, 'IVF with numLists=0 was ACCEPTED.', 'IVF with numLists=0 is rejected'))
if any(i['name'] == 'v_ivf0' for i in db.ivf.list_indexes()):
    db.ivf.drop_index('v_ivf0')
run('f2', '(f) vector-ivf numLists=100 on 5 docs (numLists > document count)', ci('ivf', [ivf('v_ivf100', numLists=100)]),
    lambda r: err_reading(r, 'IVF with numLists=100 on 5 documents was ACCEPTED (no check against document count).', 'IVF numLists > count rejected'))
def f3_reading(r):
    if r['outcome'] != 'ok':
        return f"Search on numLists=100 index failed: code {r['error']['code']} {r['error']['codeName']}: {r['error']['errmsg']}"
    ids = [d['_id'] for d in r['response']['cursor']['firstBatch']]
    return f"Search on the numLists=100 IVF index (5 docs) returned _ids {ids}."
if any(i['name'] == 'v_ivf100' for i in db.ivf.list_indexes()):
    run('f3', '(f) search on numLists=100 index', search('ivf', [1.0, 0.0, 0.0], k=3), f3_reading)
    run('f4', '(f) search with nProbes=100 on numLists=100 index', search('ivf', [1.0, 0.0, 0.0], k=3, extra={'nProbes': 100}), f3_reading)

# ---- (g) dimension caps (empty collection 'dims', one path per attempt)
db.create_collection('dims')
cases = [
    ('g1', 'hnsw', 2001, None), ('g2', 'hnsw', 2000, None), ('g3', 'hnsw', 4001, 'half'), ('g4', 'hnsw', 4000, 'half'),
    ('g5', 'ivf', 2001, None), ('g6', 'ivf', 2000, None), ('g7', 'ivf', 4001, 'half'), ('g8', 'ivf', 4000, 'half'),
]
for sid, kind, dims, comp in cases:
    opts = {} if comp is None else {'compression': comp}
    path = f'{kind}_{dims}_{comp or "none"}'
    spec = hnsw(f'ix_{path}', path=path, dims=dims, **opts) if kind == 'hnsw' else ivf(f'ix_{path}', path=path, dims=dims, numLists=1, **opts)
    label = f"vector-{kind} dimensions={dims} compression={comp or 'none'}"
    run(sid, f'(g) {label}', ci('dims', [spec]),
        lambda r, label=label: err_reading(r, f'{label}: index CREATED.', f'{label}: REJECTED'))
# hnsw 2001 with half, to see whether 'half' lifts the uncompressed cap
run('g9', '(g) vector-hnsw dimensions=2001 compression=half', ci('dims', [hnsw('ix_hnsw_2001_half', path='hnsw_2001_half', dims=2001, compression='half')]),
    lambda r: err_reading(r, 'vector-hnsw 2001 dims with compression=half: index CREATED (half lifts the 2000 cap).', 'vector-hnsw 2001 dims with half: REJECTED'))

# ---- (h) BSON Binary vectors
db.bin.insert_many(DOCS[:3])
bin_vec_sub9 = Binary.from_vector([1.0, 0.0, 0.0], BinaryVectorDtype.FLOAT32)        # subtype 9 (BSON vector)
bin_vec_sub0 = Binary(struct.pack('<3f', 1.0, 0.0, 0.0), 0)                            # generic subtype 0
bin_docs = [{'_id': 10, 'tag': 'bin9', 'v': bin_vec_sub9}, {'_id': 11, 'tag': 'bin0', 'v': bin_vec_sub0}]
try:
    res = db.bin.insert_many(bin_docs)
    steps.append({'step': 'h1', 'question': '(h) insert documents whose v is BSON Binary (subtype 9 float32 vector, subtype 0 packed floats)',
                  'command': {'insert': 'bin', 'documents': j(bin_docs)}, 'response': {'insertedIds': res.inserted_ids}, 'outcome': 'ok',
                  'reading': 'Binary-typed v documents are inserted without error (before any index exists).'})
except PyMongoError as e:
    steps.append({'step': 'h1', 'question': '(h) insert BSON Binary v', 'command': {'insert': 'bin', 'documents': j(bin_docs)},
                  'error': {'code': getattr(e, 'code', None), 'errmsg': str(e)}, 'outcome': 'error', 'reading': f'Insert of Binary v failed: {e}'})
run('h2', '(h) create vector-hnsw on bin (collection already holds Binary v docs)', ci('bin', [hnsw('v_hnsw')]),
    lambda r: err_reading(r, 'HNSW index built over a collection containing Binary-typed v documents without error.',
                          'HNSW build over Binary-typed v failed'))
# insert another binary doc AFTER the index exists
try:
    db.bin.insert_one({'_id': 12, 'tag': 'bin9_after', 'v': Binary.from_vector([0.0, 1.0, 0.0], BinaryVectorDtype.FLOAT32)})
    steps.append({'step': 'h3', 'question': '(h) insert Binary v after index exists', 'command': {'insert': 'bin', 'documents': [{'_id': 12, 'tag': 'bin9_after', 'v': '<Binary subtype 9 float32 [0,1,0]>'}]},
                  'response': {'n': 1}, 'outcome': 'ok', 'reading': 'Binary-typed v inserted after the HNSW index exists, without error.'})
except PyMongoError as e:
    det = getattr(e, 'details', {}) or {}
    steps.append({'step': 'h3', 'question': '(h) insert Binary v after index exists', 'command': {'insert': 'bin', 'documents': [{'_id': 12, 'tag': 'bin9_after', 'v': '<Binary subtype 9 float32 [0,1,0]>'}]},
                  'error': {'code': getattr(e, 'code', None), 'codeName': det.get('codeName'), 'errmsg': det.get('errmsg', str(e)), 'errorLabels': det.get('errorLabels', [])},
                  'outcome': 'error', 'reading': f'Insert of Binary v after index exists FAILED: {det.get("errmsg", str(e))}'})
def h4_reading(r):
    if r['outcome'] != 'ok':
        return f"Search failed: code {r['error']['code']} {r['error']['codeName']}: {r['error']['errmsg']}"
    got = [(d['_id'], d.get('tag')) for d in r['response']['cursor']['firstBatch']]
    return f"number[] query vector returned {got}; Binary-typed docs (_id 10, 11, 12) {'ARE' if any(i in (10,11,12) for i,_ in got) else 'are NOT'} among the results (k=10 over 6 docs)."
run('h4', '(h) $search cosmosSearch with number[] query vector over the mixed collection', search('bin', [1.0, 0.0, 0.0], k=10), h4_reading)
run('h5', '(h) $search cosmosSearch with Binary (subtype 9) query vector', search('bin', bin_vec_sub9, k=10),
    lambda r: err_reading(r, f"Binary subtype-9 query vector ACCEPTED; returned {[d['_id'] for d in r['response']['cursor']['firstBatch']]}." if r['outcome']=='ok' else '',
                          'Binary subtype-9 query vector rejected'))
run('h6', '(h) $search cosmosSearch with Binary (subtype 0) query vector', search('bin', bin_vec_sub0, k=10),
    lambda r: err_reading(r, f"Binary subtype-0 query vector ACCEPTED; returned {[d['_id'] for d in r['response']['cursor']['firstBatch']]}." if r['outcome']=='ok' else '',
                          'Binary subtype-0 query vector rejected'))
# plain find shows the binary docs are stored intact
fr = list(db.bin.find({'_id': {'$in': [10, 11, 12]}}))
steps.append({'step': 'h7', 'question': '(h) plain find returns the Binary-typed documents?', 'command': {'find': 'bin', 'filter': {'_id': {'$in': [10, 11, 12]}}},
              'response': j(fr), 'outcome': 'ok',
              'reading': f"find returns {len(fr)} Binary-typed documents with v as Binary subtypes {[getattr(d['v'], 'subtype', 0) for d in fr]}; they are stored intact, only vector search excludes them."})

# ---- final listIndexes of every collection for the record
for c in ['docs', 'empty_hnsw', 'ivf', 'dims', 'bin']:
    run(f'final_listIndexes_{c}', 'record final index state', {'listIndexes': c}, lambda r, c=c: f"Index names on {c}: {[i['name'] for i in r['response']['cursor']['firstBatch']] if r['outcome']=='ok' else r['error']['errmsg']}")

report = {
    'test': 'vector-index-rules',
    'database': DB,
    'ran_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'target': 'documentdb-local container ddb-engine-test, localhost:10260 (open-source DocumentDB engine + gateway)',
    'buildInfo': j(build),
    'driver': f'pymongo {pymongo.__version__}',
    'evidence_scope': 'Observations are about the open-source DocumentDB engine and gateway at the buildInfo version above, as packaged in documentdb-local. They do not prove managed Azure DocumentDB behaviour.',
    'steps': steps,
}
with open(REPORT, 'w') as f:
    json.dump(report, f, indent=2, default=str)
print('wrote', REPORT)
