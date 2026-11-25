#!/usr/bin/env python
"""Reproducer's extra probes for vector-index-rules (engine 1.2.0), database t_vector_rerun only.

Run:  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I extra_probes.py all 20000
      /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I extra_probes.py x7 200000
      (mode 'all' runs X1-X9 plus X7 at the given sizes; mode 'x7' runs only X7 at the given sizes)

Purpose: test points the tester's conclusions rest on but did not vary.
  X1-X2   (a) one index per path: IVF first then HNSW; two specs on one path in a single createIndexes.
  X3-X5   (b) what counts as identical: top-level field order, m sent as a double, dimensions as Int64.
  X6      (b) HNSW created WITHOUT m/efConstruction: what listIndexes stores, explain's default efSearch,
          and re-sending the spec WITH m 16 / efConstruction 64.
  X7      (e/f incidental) are the default efSearch / nProbes the same on larger collections, and does a
          k above the default efSearch return k documents?
  X8      (h) wrong-dimension and non-numeric arrays inserted into an HNSW-indexed path.
  X9      (f) IVF created on an EMPTY collection, then data, then search with default and nProbes 1.
Reads LOCAL_URI from scratchpad/engine-tests/local.env and never prints or stores the password.
Drops t_vector_rerun at the start and at the end. Writes extra_probes_report.json next to this file.
"""
import datetime
import json
import os
import random
import re
import sys
import time
from urllib.parse import unquote, urlsplit

import pymongo
from bson import Int64
from bson.json_util import RELAXED_JSON_OPTIONS, dumps
from pymongo.errors import OperationFailure, PyMongoError

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.abspath(os.path.join(HERE, '..', '..'))
ENV_FILE = os.path.join(SCRATCH, 'engine-tests', 'local.env')
MODE = sys.argv[1] if len(sys.argv) > 1 else 'all'
SIZES = [int(a) for a in sys.argv[2:]] or [20000]
REPORT = os.path.join(HERE, 'extra_probes_report.json' if MODE == 'all' else f"extra_probes_report_x7_{'_'.join(map(str, SIZES))}.json")
DB = 't_vector_rerun'


def load_env(path):
    env = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            line = re.sub(r'^export\s+', '', line)
            k, _, v = line.partition('=')
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


env = load_env(ENV_FILE)
URI = env['LOCAL_URI']
_pw = urlsplit(URI).password or ''
SECRETS = sorted({s for s in (env.get('LOCAL_PASS', ''), _pw, unquote(_pw)) if s}, key=len, reverse=True)


def scrub(text):
    for s in SECRETS:
        text = text.replace(s, '<redacted>')
    return text


client = pymongo.MongoClient(URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=15000,
                             connectTimeoutMS=15000, socketTimeoutMS=590000)
db = client[DB]
steps = []


def j(x):
    return json.loads(dumps(x, json_options=RELAXED_JSON_OPTIONS))


def find_key(o, key):
    if isinstance(o, dict):
        if key in o:
            return o[key]
        for v in o.values():
            x = find_key(v, key)
            if x is not None:
                return x
    elif isinstance(o, list):
        for v in o:
            x = find_key(v, key)
            if x is not None:
                return x
    return None


def tail(e):
    return (e.get('errmsg') or '').rsplit('}:', 1)[-1]


def run(step_id, question, cmd, reading=None, record_cmd=None):
    rec = {'step': step_id, 'question': question,
           'driver_call': f"pymongo {pymongo.__version__}: client['{DB}'].command(<command>)",
           'command': record_cmd if record_cmd is not None else j(cmd)}
    t0 = time.time()
    try:
        resp = db.command(cmd)
        rec['response'] = j(resp)
        rec['outcome'] = 'ok'
    except OperationFailure as e:
        det = e.details or {}
        rec['error'] = {'code': e.code, 'codeName': det.get('codeName'), 'errmsg': det.get('errmsg', str(e)),
                        'errorLabels_present': 'errorLabels' in det, 'errorLabels': det.get('errorLabels'),
                        'raw': j(det)}
        rec['outcome'] = 'error'
    except PyMongoError as e:
        rec['error'] = {'code': None, 'codeName': None, 'exception': type(e).__name__, 'errmsg': str(e),
                        'errorLabels_present': False, 'errorLabels': None}
        rec['outcome'] = 'driver_error'
    rec['elapsed_s'] = round(time.time() - t0, 3)
    try:
        rec['reading'] = reading(rec) if callable(reading) else (reading or '')
    except Exception as e:
        rec['reading'] = f'(reading could not be computed: {type(e).__name__}: {e})'
    steps.append(rec)
    short = rec.get('response') if rec['outcome'] == 'ok' else {k: rec['error'].get(k) for k in ('code', 'codeName', 'errmsg', 'errorLabels')}
    print(f"[{step_id}] {rec['outcome']} ({rec['elapsed_s']}s): {json.dumps(short, default=str)[:400]}")
    print(f"      reading: {rec['reading']}")
    return rec


def hnsw(name, path='v', dims=3, **opts):
    o = {'kind': 'vector-hnsw', 'dimensions': dims, 'similarity': 'COS', 'm': 16, 'efConstruction': 64}
    o.update(opts)
    return {'name': name, 'key': {path: 'cosmosSearch'}, 'cosmosSearchOptions': o}


def ivf(name, path='v', dims=3, numLists=1, **opts):
    o = {'kind': 'vector-ivf', 'dimensions': dims, 'similarity': 'COS', 'numLists': numLists}
    o.update(opts)
    return {'name': name, 'key': {path: 'cosmosSearch'}, 'cosmosSearchOptions': o}


def ci(coll, indexes):
    return {'createIndexes': coll, 'indexes': indexes}


def search(coll, vector, path='v', k=5, extra=None):
    cs = {'vector': vector, 'path': path, 'k': k}
    if extra:
        cs.update(extra)
    return {'aggregate': coll, 'pipeline': [
        {'$search': {'cosmosSearch': cs, 'returnStoredSource': True}},
        {'$project': {'_id': 1, 'score': {'$meta': 'searchScore'}}}], 'cursor': {'batchSize': 1000}}


def res(r):
    if r['outcome'] != 'ok':
        return f"code {r['error'].get('code')} {r['error'].get('codeName')} \"{tail(r['error'])}\"" + ('' if r['error'].get('errorLabels') else ', no errorLabels')
    shard = (r['response'].get('raw') or {}).get('defaultShard') or r['response']
    s = f"ok, numIndexesBefore {shard.get('numIndexesBefore')}, numIndexesAfter {shard.get('numIndexesAfter')}"
    return s + (f", note \"{shard['note']}\"" if shard.get('note') else '')


def plan(r):
    if r['outcome'] != 'ok':
        return f"explain failed: {res(r)}"
    return (f"cosmosSearchCustomParams {find_key(r['response'], 'cosmosSearchCustomParams')}, IXSCAN of "
            f"{find_key(r['response'], 'indexName')}, planner row estimate (estimatedTotalIndexEntries of _id_) "
            f"{find_key(r['response'], 'estimatedTotalIndexEntries')}")


def count_ids(r):
    if r['outcome'] != 'ok':
        return f"search failed: {res(r)}"
    b = r['response']['cursor']['firstBatch']
    more = r['response']['cursor'].get('id')
    return f"returned {len(b)} documents in the first batch (cursor id {more}); first _ids {[d['_id'] for d in b[:5]]}"


DOCS = [
    {'_id': 1, 'tag': 'a', 'v': [1.0, 0.0, 0.0]},
    {'_id': 2, 'tag': 'b', 'v': [0.0, 1.0, 0.0]},
    {'_id': 3, 'tag': 'c', 'v': [0.0, 0.0, 1.0]},
    {'_id': 4, 'tag': 'd', 'v': [0.9, 0.1, 0.0]},
    {'_id': 5, 'tag': 'e', 'v': [0.1, 0.9, 0.0]},
]
Q = [1.0, 0.0, 0.0]

run('x_setup0', 'clean start: drop database t_vector_rerun', {'dropDatabase': 1}, lambda r: 'dropped (or absent) before the probes')

if MODE == 'all':
    # ---------------------------------------------------------------- X1, X2: one index per path
    run('x1_setup', 'insert five documents into x1', {'insert': 'x1', 'documents': DOCS}, lambda r: f"n={r['response'].get('n')}")
    run('x1_ivf', '(a, extra) vector-ivf FIRST on x1.v', ci('x1', [ivf('v_ivf', numLists=1)]), res)
    run('x1_hnsw', '(a, extra) then vector-hnsw on the same path under a new name (reverse of a3)', ci('x1', [hnsw('v_hnsw')]), res)
    run('x2_setup', 'insert five documents into x2', {'insert': 'x2', 'documents': DOCS}, lambda r: f"n={r['response'].get('n')}")
    run('x2_both', '(a, extra) one createIndexes call carrying an HNSW and an IVF spec on the same path',
        ci('x2', [hnsw('v_hnsw'), ivf('v_ivf', numLists=1)]), res)
    run('x2_list', '(a, extra) listIndexes on x2 after the two-spec call', {'listIndexes': 'x2'},
        lambda r: f"index names {[i['name'] for i in r['response']['cursor']['firstBatch']]}")

    # ---------------------------------------------------------------- X3-X5: what counts as identical (existing x1? no: fresh x3)
    run('x3_setup', 'insert five documents into x3', {'insert': 'x3', 'documents': DOCS}, lambda r: f"n={r['response'].get('n')}")
    run('x3_create', 'create v_hnsw on x3 (same spec as a1)', ci('x3', [hnsw('v_hnsw')]), res)
    run('x3_toplevel_order', '(b, extra) re-send the a1 spec with top-level fields ordered key, name, cosmosSearchOptions',
        ci('x3', [{'key': {'v': 'cosmosSearch'}, 'name': 'v_hnsw',
                   'cosmosSearchOptions': {'kind': 'vector-hnsw', 'dimensions': 3, 'similarity': 'COS', 'm': 16, 'efConstruction': 64}}]), res)
    run('x4_m_double', '(b, extra) re-send the a1 spec with m as the double 16.0 (same field order)',
        ci('x3', [hnsw('v_hnsw', m=16.0)]), res)
    run('x5_dims_int64', '(b, extra) re-send the a1 spec with dimensions as Int64(3) (same field order)',
        ci('x3', [hnsw('v_hnsw', dims=Int64(3))]), res,
        record_cmd={'createIndexes': 'x3', 'indexes': [{'name': 'v_hnsw', 'key': {'v': 'cosmosSearch'}, 'cosmosSearchOptions': {
            'kind': 'vector-hnsw', 'dimensions': {'$numberLong': '3'}, 'similarity': 'COS', 'm': 16, 'efConstruction': 64}}]})

    # ---------------------------------------------------------------- X6: HNSW without m / efConstruction
    run('x6_setup', 'insert five documents into x6', {'insert': 'x6', 'documents': DOCS}, lambda r: f"n={r['response'].get('n')}")
    run('x6_create', '(b, extra) create vector-hnsw WITHOUT m and efConstruction',
        ci('x6', [{'name': 'v_hnsw', 'key': {'v': 'cosmosSearch'}, 'cosmosSearchOptions': {'kind': 'vector-hnsw', 'dimensions': 3, 'similarity': 'COS'}}]), res)
    run('x6_list', '(b, extra) listIndexes on x6: are m/efConstruction filled in?', {'listIndexes': 'x6'},
        lambda r: f"v_hnsw entry {next((i for i in r['response']['cursor']['firstBatch'] if i['name'] == 'v_hnsw'), None)}")
    run('x6_explain', '(b, extra) explain $search without efSearch on the index created without efConstruction',
        {'explain': search('x6', Q, k=3), 'verbosity': 'queryPlanner'}, plan)
    run('x6_resend_full', '(b, extra) re-send the same name WITH m 16 and efConstruction 64 (reverse of b3)', ci('x6', [hnsw('v_hnsw')]), res)
    run('x6_resend_same', '(b, extra) re-send exactly the creating spec (no m/efConstruction)',
        ci('x6', [{'name': 'v_hnsw', 'key': {'v': 'cosmosSearch'}, 'cosmosSearchOptions': {'kind': 'vector-hnsw', 'dimensions': 3, 'similarity': 'COS'}}]), res)

    # ---------------------------------------------------------------- X8: wrong-dimension and non-numeric arrays on an indexed path
    run('x8_wrongdim', '(h, extra) insert a 4-dimensional number[] into x6 (3-dimensional HNSW on v)',
        {'insert': 'x6', 'documents': [{'_id': 20, 'tag': 'dim4', 'v': [1.0, 0.0, 0.0, 0.0]}]},
        lambda r: (f"insert returned n={r['response'].get('n')}" + (f", writeErrors {r['response'].get('writeErrors')}" if r['response'].get('writeErrors') else ', no writeErrors'))
        if r['outcome'] == 'ok' else f"insert failed: {res(r)}")
    run('x8_strings', '(h, extra) insert an array of 3 strings into x6.v',
        {'insert': 'x6', 'documents': [{'_id': 21, 'tag': 'strs', 'v': ['a', 'b', 'c']}]},
        lambda r: (f"insert returned n={r['response'].get('n')}" + (f", writeErrors {r['response'].get('writeErrors')}" if r['response'].get('writeErrors') else ', no writeErrors'))
        if r['outcome'] == 'ok' else f"insert failed: {res(r)}")
    run('x8_search', '(h, extra) $search k=10 on x6 after those inserts', search('x6', Q, k=10),
        lambda r: count_ids(r) + ('' if r['outcome'] != 'ok' else f"; all _ids {[d['_id'] for d in r['response']['cursor']['firstBatch']]}"))
    run('x8_find', '(h, extra) find _id 20 and 21 on x6', {'find': 'x6', 'filter': {'_id': {'$in': [20, 21]}}},
        lambda r: f"find returns _ids {[d['_id'] for d in r['response']['cursor']['firstBatch']]}")

    # ---------------------------------------------------------------- X9: IVF on an EMPTY collection
    run('x9_create_coll', '(f, extra) create the empty collection x9', {'create': 'x9'}, lambda r: 'created')
    run('x9_ivf', '(f, extra) vector-ivf numLists 4 on the EMPTY collection x9', ci('x9', [ivf('v_ivf4', numLists=4)]), res)
    run('x9_insert', '(f, extra) insert the five documents after the index exists', {'insert': 'x9', 'documents': DOCS},
        lambda r: f"n={r['response'].get('n')}")
    run('x9_explain', '(f, extra) explain $search without nProbes on x9', {'explain': search('x9', Q, k=3), 'verbosity': 'queryPlanner'}, plan)
    run('x9_search_default', '(f, extra) $search k=3 without nProbes on x9', search('x9', Q, k=3),
        lambda r: count_ids(r) + ('' if r['outcome'] != 'ok' else f"; (_id, score) {[(d['_id'], round(d['score'], 4)) for d in r['response']['cursor']['firstBatch']]}"))
    run('x9_search_np1', '(f, extra) $search k=3 with nProbes 1 on x9', search('x9', Q, k=3, extra={'nProbes': 1}),
        lambda r: count_ids(r) + ('' if r['outcome'] != 'ok' else f"; (_id, score) {[(d['_id'], round(d['score'], 4)) for d in r['response']['cursor']['firstBatch']]}"))

# ---------------------------------------------------------------- X7: defaults on larger collections, and k above efSearch
GEN = ("rng = random.Random(<seed N>); docs = [{'_id': i, 'v': [rng.uniform(-1, 1) for _ in range(3)]} for i in range(N)]; "
       "db[coll].insert_many(docs, ordered=True)")
for N in SIZES:
    coll = f'big{N}'
    rng = random.Random(N)
    docs = [{'_id': i, 'v': [rng.uniform(-1, 1) for _ in range(3)]} for i in range(N)]
    rec = {'step': f'x7_{N}_insert', 'question': f'(e/f, extra) insert {N} random 3-dimensional documents into {coll}',
           'driver_call': f"pymongo {pymongo.__version__}: client['{DB}']['{coll}'].insert_many(docs, ordered=True)",
           'command': GEN.replace('<seed N>', str(N)).replace('N)', f'{N})').replace('coll', repr(coll), 1)}
    t0 = time.time()
    try:
        ir = db[coll].insert_many(docs, ordered=True)
        rec['response'] = {'inserted': len(ir.inserted_ids), 'acknowledged': ir.acknowledged}
        rec['outcome'] = 'ok'
        rec['reading'] = f"{len(ir.inserted_ids)} documents inserted"
    except PyMongoError as e:
        rec['error'] = {'exception': type(e).__name__, 'errmsg': str(e)[:2000]}
        rec['outcome'] = 'error'
        rec['reading'] = f"insert failed: {type(e).__name__}"
    rec['elapsed_s'] = round(time.time() - t0, 3)
    steps.append(rec)
    print(f"[{rec['step']}] {rec['outcome']} ({rec['elapsed_s']}s)")
    if rec['outcome'] != 'ok':
        continue
    run(f'x7_{N}_ivf', f'(f, extra) vector-ivf numLists 100 on {coll} ({N} documents)', ci(coll, [ivf('v_ivf100', numLists=100)]), res)
    run(f'x7_{N}_ivf_explain', f'(f, extra) explain without nProbes, k=10, on {coll}', {'explain': search(coll, Q, k=10), 'verbosity': 'queryPlanner'}, plan)
    run(f'x7_{N}_ivf_search', f'(f, extra) $search without nProbes, k=10, on {coll}', search(coll, Q, k=10), count_ids)
    run(f'x7_{N}_ivf_drop', f'drop v_ivf100 on {coll}', {'dropIndexes': coll, 'index': 'v_ivf100'}, lambda r: 'dropped' if r['outcome'] == 'ok' else res(r))
    run(f'x7_{N}_hnsw', f'(e, extra) vector-hnsw m 16 efConstruction 64 on {coll} ({N} documents)', ci(coll, [hnsw('v_hnsw')]), res)
    run(f'x7_{N}_hnsw_explain_k10', f'(e, extra) explain without efSearch, k=10, on {coll}', {'explain': search(coll, Q, k=10), 'verbosity': 'queryPlanner'}, plan)
    run(f'x7_{N}_hnsw_explain_k100', f'(e, extra) explain without efSearch, k=100, on {coll}', {'explain': search(coll, Q, k=100), 'verbosity': 'queryPlanner'}, plan)
    run(f'x7_{N}_hnsw_search_k100', f'(e, extra) $search without efSearch, k=100, on {coll}: how many documents come back?', search(coll, Q, k=100), count_ids)
    run(f'x7_{N}_hnsw_search_k100_ef100', f'(e, extra) $search with efSearch 100, k=100, on {coll}', search(coll, Q, k=100, extra={'efSearch': 100}), count_ids)
    run(f'x7_{N}_hnsw_search_k200', f'(e, extra) $search without efSearch, k=200, on {coll}', search(coll, Q, k=200), count_ids)
    run(f'x7_{N}_drop', f'drop collection {coll} to free space', {'drop': coll}, lambda r: 'dropped' if r['outcome'] == 'ok' else res(r))

# ---------------------------------------------------------------- cleanup
run('x_cleanup', 'drop database t_vector_rerun', {'dropDatabase': 1}, lambda r: f"dropped {r['response'].get('dropped')}")
run('x_cleanup_verify', 'confirm t_vector_rerun lists no collections', {'listCollections': 1, 'nameOnly': True},
    lambda r: f"{len(r['response']['cursor']['firstBatch'])} collections left")

report = {'test': 'vector-index-rules (reproducer extra probes)', 'database': DB,
          'ran_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'target': 'documentdb-local container ddb-engine-test, localhost:10260 (open-source engine 1.2-0, commit 965b6e7a)',
          'driver': f'pymongo {pymongo.__version__}', 'python': sys.version.split()[0],
          'evidence_scope': 'Open-source DocumentDB engine and gateway 1.2-0 in documentdb-local only; not evidence about the managed service.',
          'steps': steps}
with open(REPORT, 'w') as fh:
    fh.write(scrub(json.dumps(report, indent=2, default=str)))
print('wrote', REPORT, len(steps), 'steps')
