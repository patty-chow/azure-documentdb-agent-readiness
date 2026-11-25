#!/usr/bin/env python
"""Reproducer's parameter sweep for the default efSearch / nProbes (engine 1.2.0), database t_vector_rerun only.

Run:  .venv/bin/python -I extra_probes_sweep.py 2000 8000 12000 20000 200000

For each size N: insert N random 3-dimensional documents, then for IVF numLists 10, 100 and 400 and for HNSW
efConstruction 64 and 200: create the index, explain a $search that names no nProbes / efSearch (k=10), and
for HNSW also count what a k=100 $search returns; drop the index. Drops t_vector_rerun at the start and end.
Writes extra_probes_sweep_report.json.

(Original probe-script docstring follows.)

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
SIZES = [int(a) for a in sys.argv[1:]] or [2000, 8000, 12000, 20000, 200000]
REPORT = os.path.join(HERE, f"extra_probes_sweep_report_{'_'.join(map(str, SIZES))}.json")
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


run('s_setup0', 'clean start: drop database t_vector_rerun', {'dropDatabase': 1}, lambda r: 'dropped (or absent) before the sweep')
summary = []
for N in SIZES:
    coll = f'sweep{N}'
    rng = random.Random(N)
    docs = [{'_id': i, 'v': [rng.uniform(-1, 1) for _ in range(3)]} for i in range(N)]
    t0 = time.time()
    ir = db[coll].insert_many(docs, ordered=True)
    steps.append({'step': f's_{N}_insert', 'question': f'insert {N} random 3-dimensional documents into {coll}',
                  'driver_call': f"pymongo {pymongo.__version__}: client['{DB}']['{coll}'].insert_many(docs, ordered=True)",
                  'command': f"rng = random.Random({N}); docs = [{{'_id': i, 'v': [rng.uniform(-1, 1) for _ in range(3)]}} for i in range({N})]",
                  'response': {'inserted': len(ir.inserted_ids)}, 'outcome': 'ok', 'elapsed_s': round(time.time() - t0, 3),
                  'reading': f'{len(ir.inserted_ids)} documents inserted'})
    print(f's_{N}_insert ok {len(ir.inserted_ids)}')
    for nl in (10, 100, 400):
        c = run(f's_{N}_ivf{nl}', f'vector-ivf numLists {nl} on {coll}', ci(coll, [ivf(f'v_ivf{nl}', numLists=nl)]), res)
        if c['outcome'] == 'ok':
            e = run(f's_{N}_ivf{nl}_explain', f'explain without nProbes, k=10, on {coll} numLists {nl}',
                    {'explain': search(coll, Q, k=10), 'verbosity': 'queryPlanner'}, plan)
            summary.append({'N': N, 'kind': 'ivf', 'numLists': nl,
                            'default': find_key(e.get('response'), 'cosmosSearchCustomParams'),
                            'row_estimate': find_key(e.get('response'), 'estimatedTotalIndexEntries')})
            run(f's_{N}_ivf{nl}_drop', 'drop it', {'dropIndexes': coll, 'index': f'v_ivf{nl}'}, lambda r: 'dropped' if r['outcome'] == 'ok' else res(r))
    for efc in (64, 200):
        c = run(f's_{N}_hnsw{efc}', f'vector-hnsw m 16 efConstruction {efc} on {coll}', ci(coll, [hnsw(f'v_hnsw{efc}', efConstruction=efc)]), res)
        if c['outcome'] == 'ok':
            e = run(f's_{N}_hnsw{efc}_explain', f'explain without efSearch, k=10, on {coll} efConstruction {efc}',
                    {'explain': search(coll, Q, k=10), 'verbosity': 'queryPlanner'}, plan)
            k100 = run(f's_{N}_hnsw{efc}_k100', f'$search without efSearch, k=100, on {coll} efConstruction {efc}', search(coll, Q, k=100), count_ids)
            summary.append({'N': N, 'kind': 'hnsw', 'efConstruction': efc,
                            'default': find_key(e.get('response'), 'cosmosSearchCustomParams'),
                            'row_estimate': find_key(e.get('response'), 'estimatedTotalIndexEntries'),
                            'k100_returned': len(k100['response']['cursor']['firstBatch']) if k100['outcome'] == 'ok' else None})
            run(f's_{N}_hnsw{efc}_drop', 'drop it', {'dropIndexes': coll, 'index': f'v_hnsw{efc}'}, lambda r: 'dropped' if r['outcome'] == 'ok' else res(r))
    run(f's_{N}_drop', f'drop collection {coll}', {'drop': coll}, lambda r: 'dropped' if r['outcome'] == 'ok' else res(r))

run('s_cleanup', 'drop database t_vector_rerun', {'dropDatabase': 1}, lambda r: f"dropped {r['response'].get('dropped')}")
run('s_cleanup_verify', 'confirm t_vector_rerun lists no collections', {'listCollections': 1, 'nameOnly': True},
    lambda r: f"{len(r['response']['cursor']['firstBatch'])} collections left")
report = {'test': 'vector-index-rules (reproducer default-parameter sweep)', 'database': DB,
          'ran_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'target': 'documentdb-local container ddb-engine-test, localhost:10260 (open-source engine 1.2-0, commit 965b6e7a)',
          'driver': f'pymongo {pymongo.__version__}', 'python': sys.version.split()[0],
          'evidence_scope': 'Open-source DocumentDB engine and gateway 1.2-0 in documentdb-local only; not evidence about the managed service.',
          'summary': summary, 'steps': steps}
with open(REPORT, 'w') as fh:
    fh.write(scrub(json.dumps(report, indent=2, default=str)))
print('SUMMARY')
for s in summary:
    print(json.dumps(s))
print('wrote', REPORT, len(steps), 'steps')
