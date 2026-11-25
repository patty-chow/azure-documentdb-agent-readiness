#!/usr/bin/env python
"""vector-index-rules, ENGINE 1.2.0 RERUN, against documentdb-local (database t_vector only).

Run:   /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I run.py
Then:  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I finalize.py

Reads LOCAL_URI from scratchpad/engine-tests/local.env and never prints or stores the password.
Touches only database t_vector: drops it at the start (leftovers) and at the end.
Container commands are read-only (docker inspect, docker logs, psql catalog SELECTs).
Writes report.json next to this file, including an automatic step-by-step comparison with the
0.117 report in findings/phase4/engine-tests/vector-index-rules/report.json.
"""
import datetime
import json
import os
import re
import shlex
import struct
import subprocess
import sys
import time
from urllib.parse import unquote, urlsplit

import pymongo
from bson import Binary
from bson.binary import BinaryVectorDtype
from bson.json_util import RELAXED_JSON_OPTIONS, dumps
from pymongo.errors import OperationFailure, PyMongoError

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.abspath(os.path.join(HERE, '..', '..'))
ENV_FILE = os.path.join(SCRATCH, 'engine-tests', 'local.env')
PREV_REPORT = '/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/vector-index-rules/report.json'
PREV_PARITY = '/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/local-gateway-parity/report.json'
REPORT = os.path.join(HERE, 'report.json')
DB = 't_vector'
CONTAINER = 'ddb-engine-test'
PSQL = ['docker', 'exec', CONTAINER, 'psql', '-X', '-U', 'documentdb', '-p', '9712', '-d', 'postgres', '-tAc']


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
                             connectTimeoutMS=15000, socketTimeoutMS=290000)
db = client[DB]
steps = []


def j(x):
    return json.loads(dumps(x, json_options=RELAXED_JSON_OPTIONS))


def collapse(s):
    """Shorten an errmsg for a reading: replace each top-level {...} block by {...}."""
    out, depth = [], 0
    for ch in s or '':
        if ch == '{':
            if depth == 0:
                out.append('{...}')
            depth += 1
        elif ch == '}':
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return ''.join(out)


def run(step_id, question, cmd, reading=None):
    """Send one raw command to database t_vector; record the exact command and the exact reply or error."""
    rec = {'step': step_id, 'question': question, 'kind': 'wire',
           'driver_call': f"pymongo {pymongo.__version__}: client['{DB}'].command(<command>)",
           'command': j(cmd)}
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
    except Exception as e:  # never lose a step because a reading failed to format
        rec['reading'] = f'(reading could not be computed: {type(e).__name__}: {e})'
    steps.append(rec)
    short = rec.get('response') if rec['outcome'] == 'ok' else rec['error'].get('errmsg')
    print(f"[{step_id}] {rec['outcome']} ({rec['elapsed_s']}s): {json.dumps(short, default=str)[:300]}")
    return rec


def sh(step_id, question, argv, reading, grep=None):
    """Run one read-only container command; record argv, return code, stdout and stderr."""
    rec = {'step': step_id, 'question': question, 'kind': 'container',
           'command': ' '.join(shlex.quote(a) for a in argv) + (f"   (output filtered in Python to lines containing {grep!r})" if grep else '')}
    t0 = time.time()
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=120)
        out, err = p.stdout, p.stderr
        if grep:
            out = '\n'.join(l for l in (out + '\n' + err).splitlines() if grep in l)
            err = ''
        rec['response'] = {'returncode': p.returncode, 'stdout': out.strip(), 'stderr': err.strip()[-2000:]}
        rec['outcome'] = 'ok' if p.returncode == 0 else 'error'
    except Exception as e:
        rec['error'] = {'exception': type(e).__name__, 'errmsg': str(e)}
        rec['outcome'] = 'driver_error'
    rec['elapsed_s'] = round(time.time() - t0, 3)
    try:
        rec['reading'] = reading(rec)
    except Exception as e:
        rec['reading'] = f'(reading could not be computed: {type(e).__name__}: {e})'
    steps.append(rec)
    print(f"[{step_id}] {rec['outcome']}: {json.dumps(rec.get('response') or rec.get('error'))[:300]}")
    return rec


# ---------------------------------------------------------------- command builders
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


def diskann(name, path='v', dims=3, **opts):
    o = {'kind': 'vector-diskann', 'dimensions': dims, 'similarity': 'COS', 'maxDegree': 32, 'lBuild': 50}
    o.update(opts)
    return {'name': name, 'key': {path: 'cosmosSearch'}, 'cosmosSearchOptions': o}


def search(coll, vector, path='v', k=5, extra=None):
    cs = {'vector': vector, 'path': path, 'k': k}
    if extra:
        cs.update(extra)
    return {'aggregate': coll, 'pipeline': [
        {'$search': {'cosmosSearch': cs, 'returnStoredSource': True}},
        {'$project': {'_id': 1, 'tag': 1, 'v': 1, 'score': {'$meta': 'searchScore'}}}], 'cursor': {}}


# ---------------------------------------------------------------- reading helpers
def etext(rec):
    """code, codeName and the errmsg for a one-sentence reading: spec blobs become {...} and only the
    first sentence of a multi-sentence errmsg is kept (the exact errmsg is always in the error field)."""
    e = rec['error']
    msg = collapse(e.get('errmsg'))
    first, sep, rest = msg.partition('. ')
    if sep and rest:
        msg = first + ' [...]'
    return f"code {e.get('code')} {e.get('codeName')} \"{msg}\"" + ('' if e.get('errorLabels') else ', no errorLabels')


def ci_summary(rec):
    r = rec['response']
    shard = (r.get('raw') or {}).get('defaultShard') or r
    s = f"numIndexesBefore {shard.get('numIndexesBefore')}, numIndexesAfter {shard.get('numIndexesAfter')}"
    if shard.get('note'):
        s += f", note \"{shard['note']}\""
    return s


def created(ok_text, err_text):
    def f(rec):
        if rec['outcome'] == 'ok':
            return f"{ok_text} ({ci_summary(rec)})."
        return f"{err_text}{' ' if err_text.endswith(' with') else ': '}{etext(rec)}."
    return f


def hits(rec):
    return [(d.get('_id'), round(d['score'], 4) if isinstance(d.get('score'), (int, float)) else d.get('score'))
            for d in rec['response']['cursor']['firstBatch']]


def searched(prefix, expect=None):
    def f(rec):
        if rec['outcome'] != 'ok':
            return f"{prefix} failed: {etext(rec)}."
        h = hits(rec)
        s = f"{prefix} returned (_id, score) {h}"
        if expect is not None:
            s += f"; expected _ids {expect}, " + ('matches' if [i for i, _ in h] == expect else 'DOES NOT match')
        return s + '.'
    return f


def inserted(what):
    def f(rec):
        if rec['outcome'] != 'ok':
            return f"Insert of {what} failed: {etext(rec)}."
        r = rec['response']
        we = r.get('writeErrors')
        return f"Insert of {what} returned n={r.get('n')}" + (f" with writeErrors {we}" if we else ' and no writeErrors') + '.'
    return f


def okread(text):
    return lambda rec: (text if rec['outcome'] == 'ok' else f"Failed: {etext(rec)}.")


DOCS = [
    {'_id': 1, 'tag': 'a', 'v': [1.0, 0.0, 0.0]},
    {'_id': 2, 'tag': 'b', 'v': [0.0, 1.0, 0.0]},
    {'_id': 3, 'tag': 'c', 'v': [0.0, 0.0, 1.0]},
    {'_id': 4, 'tag': 'd', 'v': [0.9, 0.1, 0.0]},
    {'_id': 5, 'tag': 'e', 'v': [0.1, 0.9, 0.0]},
]
Q = [1.0, 0.0, 0.0]

# ================================================================ engine identity (read-only)
b = run('env_buildInfo', 'engine identity: buildInfo (sent to t_vector; the command is not database-specific)', {'buildInfo': 1},
        lambda r: f"buildInfo reports only the MongoDB compatibility version {r['response'].get('version')} and no engine version field.")
h = run('env_hello', 'engine identity: hello (internal.documentdb_versions)', {'hello': 1},
        lambda r: f"hello reports maxWireVersion {r['response'].get('maxWireVersion')} and internal.documentdb_versions {((r['response'].get('internal') or {}).get('documentdb_versions'))}.")
sh('env_image', 'engine identity: container image and OCI labels',
   ['docker', 'inspect', CONTAINER, '--format', '{{.Config.Image}} {{.Image}} {{json .Config.Labels}}'],
   lambda r: f"Container runs {r['response']['stdout'].split()[0]} with OCI version label "
             f"{json.loads(r['response']['stdout'].split(' ', 2)[2]).get('org.opencontainers.image.version')} and revision "
             f"{json.loads(r['response']['stdout'].split(' ', 2)[2]).get('org.opencontainers.image.revision')}.")
sh('env_release_line', 'engine identity: the gateway startup line naming the release',
   ['docker', 'logs', CONTAINER], lambda r: f"Startup log line: {r['response']['stdout'].splitlines()[0] if r['response']['stdout'] else '(none found)'}.",
   grep='Release Version')
sh('env_extensions', 'engine identity: PostgreSQL extension versions', PSQL + ['select extname, extversion from pg_extension order by 1'],
   lambda r: f"Extensions: {r['response']['stdout'].replace(chr(10), ', ')}.")
sh('env_binary_version', 'engine identity: documentdb binary version and PostgreSQL version',
   PSQL + ['select documentdb_api.binary_extended_version(), version()'],
   lambda r: f"Binary and server version: {r['response']['stdout']}.")
sh('env_access_methods', 'which PostgreSQL index access methods exist (is there a diskann access method?)',
   PSQL + ["select amname from pg_am where amtype = 'i' order by 1"],
   lambda r: f"Index access methods: {r['response']['stdout'].replace(chr(10), ', ')}; "
             + ('a diskann access method IS present.' if 'diskann' in r['response']['stdout'] else 'there is no diskann access method (only hnsw and ivfflat for vectors).'))

sh('env_vector_settings', 'engine settings that govern vector indexes (read-only pg_settings rows)',
   PSQL + ["select name || '=' || setting from pg_settings where name ilike 'documentdb.%vector%' order by 1"],
   lambda r: f"Vector settings: {r['response']['stdout'].replace(chr(10), ', ')}.")


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


def params_reading(prefix):
    def f(r):
        if r['outcome'] != 'ok':
            return f"{prefix}: explain failed: {etext(r)}."
        return (f"{prefix}: the plan reports cosmosSearchCustomParams {find_key(r['response'], 'cosmosSearchCustomParams')} "
                f"on IXSCAN of index {find_key(r['response'], 'indexName')}.")
    return f


# ================================================================ setup
run('setup0', 'clean start: drop database t_vector (removes leftovers of an interrupted run)', {'dropDatabase': 1},
    okread('Database t_vector dropped (or did not exist) before the test.'))
run('setup', 'prepare collection docs with five 3-dimensional number[] documents', {'insert': 'docs', 'documents': DOCS},
    inserted('five number[] documents into t_vector.docs'))

# ================================================================ (a) one vector index per path
run('a1', '(a) create vector-hnsw on v', ci('docs', [hnsw('v_hnsw')]),
    created('The first vector-hnsw index on path v is created', 'Unexpected failure creating the first HNSW index'))
run('a2', '(a) second vector-hnsw on the same path, different name, identical options', ci('docs', [hnsw('v_hnsw_two')]),
    created('Engine ALLOWED a second HNSW index on the same path under a different name',
            'A second vector index on the same path with identical options and a new name is rejected with'))
run('a3', '(a) second vector index on the same path, different name, different kind (vector-ivf)', ci('docs', [ivf('v_ivf_second', numLists=1)]),
    created('Engine ALLOWED a second vector index of a different kind on the same path',
            'A second vector index of a different kind on the same path is rejected with'))
run('a4', '(a) second vector-hnsw on the same path, different name, different options (m=32)', ci('docs', [hnsw('v_hnsw_m32', m=32)]),
    created('Engine ALLOWED a second HNSW index on the same path with different options',
            'A second HNSW index on the same path with different options and a new name is rejected with'))

# ================================================================ (b) identical createIndexes
run('b1', '(b) repeat the identical createIndexes', ci('docs', [hnsw('v_hnsw')]),
    created('The identical createIndexes succeeds as a no-op', 'The identical createIndexes fails'))
run('b2', '(b, extra) same name and same options, option fields sent in a different order',
    ci('docs', [{'name': 'v_hnsw', 'key': {'v': 'cosmosSearch'},
                 'cosmosSearchOptions': {'efConstruction': 64, 'm': 16, 'similarity': 'COS', 'dimensions': 3, 'kind': 'vector-hnsw'}}]),
    created('Reordered option fields are treated as the same index, a no-op', 'Reordered option fields are treated as a conflict'))
run('b3', '(b, extra) same name, options without m and efConstruction (documented defaults 16 and 64)',
    ci('docs', [{'name': 'v_hnsw', 'key': {'v': 'cosmosSearch'},
                 'cosmosSearchOptions': {'kind': 'vector-hnsw', 'dimensions': 3, 'similarity': 'COS'}}]),
    created('Omitting options that equal the defaults is treated as the same index, a no-op',
            'Omitting options that equal the defaults is treated as a different index'))

# ================================================================ (c) same name, different options
run('c1', '(c) same name v_hnsw, different options (m=32)', ci('docs', [hnsw('v_hnsw', m=32)]),
    created('Engine accepted a same-name index with different m (unexpected)', 'Same name with different m is rejected with'))
run('c2', '(c) same name v_hnsw, different similarity (L2)', ci('docs', [hnsw('v_hnsw', similarity='L2')]),
    created('Engine accepted a same-name index with different similarity (unexpected)', 'Same name with different similarity is rejected with'))
run('c3', '(c) same name v_hnsw, different kind (vector-ivf)', ci('docs', [ivf('v_hnsw', numLists=1)]),
    created('Engine accepted a same-name index with a different kind (unexpected)', 'Same name with a different kind is rejected with'))


# ================================================================ (d) listIndexes key
def d1_reading(r):
    if r['outcome'] != 'ok':
        return f"listIndexes failed: {etext(r)}."
    ent = next((ix for ix in r['response']['cursor']['firstBatch'] if ix.get('name') == 'v_hnsw'), None)
    if ent is None:
        return 'listIndexes has no v_hnsw entry.'
    which = [k for k in ('cosmosSearch', 'cosmosSearchOptions') if k in ent]
    return f"The v_hnsw entry has top-level keys {sorted(ent)}; the vector options are under {which}" + \
           ('' if 'cosmosSearch' in ent else ' and there is no cosmosSearch key') + '.'


run('d1', '(d) listIndexes on docs: is the vector options key cosmosSearch or cosmosSearchOptions?', {'listIndexes': 'docs'}, d1_reading)

# ================================================================ (e) HNSW on an empty collection
run('e0', '(e) create the empty collection empty_hnsw', {'create': 'empty_hnsw'}, okread('Empty collection empty_hnsw created.'))
run('e1', '(e) vector-hnsw on the EMPTY collection', ci('empty_hnsw', [hnsw('v_hnsw')]),
    created('HNSW index created on an empty collection', 'HNSW on an empty collection fails'))
run('e2', '(e) insert five documents after the index exists', {'insert': 'empty_hnsw', 'documents': DOCS},
    inserted('five number[] documents into the indexed empty collection'))
run('e3', '(e) $search immediately after the insert, k=3', search('empty_hnsw', Q, k=3),
    searched('The $search issued immediately after the insert', expect=[1, 4, 5]))


def e4_reading(r):
    if r['outcome'] != 'ok':
        return f"explain failed: {etext(r)}."
    t = json.dumps(r['response'])
    return (f"The plan is {find_key(r['response'], 'stage')} over "
            f"{'an IXSCAN' if 'IXSCAN' in t else 'no IXSCAN'} of index {find_key(r['response'], 'indexName')}, "
            f"with cosmosSearchCustomParams {find_key(r['response'], 'cosmosSearchCustomParams')} although the query sets no efSearch.")


run('e4', '(e, extra) explain (queryPlanner) of the same $search, to confirm the vector index serves it',
    {'explain': search('empty_hnsw', Q, k=3), 'verbosity': 'queryPlanner'}, e4_reading)
# Incidental extras: e4 shows efSearch 64 with no efSearch in the query, while Learn documents a default of 40.
run('e5', '(e, extra) explain with an explicit efSearch=40, k=3 (index efConstruction 64)',
    {'explain': search('empty_hnsw', Q, k=3, extra={'efSearch': 40}), 'verbosity': 'queryPlanner'},
    params_reading('With efSearch=40 in the query'))
run('e6_setup', '(e, extra) insert five documents into ef_probe', {'insert': 'ef_probe', 'documents': DOCS}, inserted('five documents into t_vector.ef_probe'))
run('e6_index', '(e, extra) vector-hnsw with efConstruction=100 on ef_probe', ci('ef_probe', [hnsw('v_hnsw_ef100', efConstruction=100)]),
    created('HNSW index with efConstruction=100 created', 'HNSW with efConstruction=100 fails'))
run('e6', '(e, extra) explain without efSearch, k=3, on the efConstruction=100 index',
    {'explain': search('ef_probe', Q, k=3), 'verbosity': 'queryPlanner'},
    params_reading('No efSearch, k=3, efConstruction=100'))
run('e7', '(e, extra) explain without efSearch, k=100, on the efConstruction=64 index',
    {'explain': search('empty_hnsw', Q, k=100), 'verbosity': 'queryPlanner'},
    params_reading('No efSearch, k=100, efConstruction=64'))

# ================================================================ (f) IVF numLists
run('f_setup', '(f) insert five documents into ivf', {'insert': 'ivf', 'documents': DOCS}, inserted('five documents into t_vector.ivf'))
f0 = run('f0', '(f) control: vector-ivf numLists=1 on 5 documents', ci('ivf', [ivf('v_ivf1', numLists=1)]),
         created('IVF with numLists=1 is created on 5 documents (control)', 'IVF numLists=1 fails'))
if f0['outcome'] == 'ok':
    run('f0_drop', '(f) drop the control index so path v is free again', {'dropIndexes': 'ivf', 'index': 'v_ivf1'},
        okread('Control index v_ivf1 dropped.'))


def numlists_reading(requested):
    def f(r):
        if r['outcome'] == 'ok':
            return f"IVF with numLists={requested} was ACCEPTED ({ci_summary(r)})."
        m = re.search(r'numLists must be greater than or equal to (-?\d+), but was (-?\d+)', r['error']['errmsg'] or '')
        verdict = ''
        if m:
            bound, was = int(m.group(1)), int(m.group(2))
            if bound == requested and was != requested:
                verdict = f"; the values are still SWAPPED (it names the request {requested} as the bound and {was} as the value)"
            elif was == requested:
                verdict = f"; the message is CORRECT (bound {bound}, value {was})"
        return f"IVF with numLists={requested} is rejected with {etext(r)}{verdict}."
    return f


f1 = run('f1', '(f) vector-ivf numLists=0', ci('ivf', [ivf('v_ivf0', numLists=0)]), numlists_reading(0))
if f1['outcome'] == 'ok':
    run('f1_drop', '(f) drop v_ivf0', {'dropIndexes': 'ivf', 'index': 'v_ivf0'}, okread('v_ivf0 dropped.'))
f1b = run('f1b', '(f, extra) vector-ivf numLists=-1, to tell a swapped message from a correct one',
          ci('ivf', [ivf('v_ivfm1', numLists=-1)]), numlists_reading(-1))
if f1b['outcome'] == 'ok':
    run('f1b_drop', '(f) drop v_ivfm1', {'dropIndexes': 'ivf', 'index': 'v_ivfm1'}, okread('v_ivfm1 dropped.'))
f2 = run('f2', '(f) vector-ivf numLists=100 on 5 documents (numLists > document count)', ci('ivf', [ivf('v_ivf100', numLists=100)]),
         created('IVF with numLists=100 on 5 documents is ACCEPTED, with no check against the document count',
                 'IVF with numLists greater than the document count is rejected with'))
if f2['outcome'] == 'ok':
    run('f3', '(f) $search on the numLists=100 index, default nProbes', search('ivf', Q, k=3),
        searched('The $search on the numLists=100 IVF index with default nProbes', expect=[1, 4, 5]))
    run('f4', '(f) $search on the numLists=100 index, nProbes=100', search('ivf', Q, k=3, extra={'nProbes': 100}),
        searched('The $search on the numLists=100 IVF index with nProbes=100', expect=[1, 4, 5]))
    # Incidental extras: which nProbes does the engine apply when the query names none (Learn documents a default of 1)?
    run('f5', '(f, extra) explain without nProbes on the numLists=100 index, k=3',
        {'explain': search('ivf', Q, k=3), 'verbosity': 'queryPlanner'}, params_reading('No nProbes, numLists=100'))
    run('f6', '(f, extra) explain with an explicit nProbes=7 on the numLists=100 index, k=3',
        {'explain': search('ivf', Q, k=3, extra={'nProbes': 7}), 'verbosity': 'queryPlanner'}, params_reading('With nProbes=7, numLists=100'))

# ================================================================ (g) dimension caps
run('g0', '(g) create the empty collection dims (one path per attempt)', {'create': 'dims'}, okread('Empty collection dims created.'))
for sid, kind, dims, comp in [('g1', 'hnsw', 2001, None), ('g2', 'hnsw', 2000, None), ('g3', 'hnsw', 4001, 'half'), ('g4', 'hnsw', 4000, 'half'),
                              ('g5', 'ivf', 2001, None), ('g6', 'ivf', 2000, None), ('g7', 'ivf', 4001, 'half'), ('g8', 'ivf', 4000, 'half')]:
    opts = {} if comp is None else {'compression': comp}
    path = f'{kind}_{dims}_{comp or "none"}'
    spec = hnsw(f'ix_{path}', path=path, dims=dims, **opts) if kind == 'hnsw' else ivf(f'ix_{path}', path=path, dims=dims, numLists=1, **opts)
    label = f"vector-{kind} dimensions={dims} compression={comp or 'none'}"
    run(sid, f'(g) {label}', ci('dims', [spec]), created(f'{label}: index CREATED', f'{label}: REJECTED with'))
run('g9', '(g) vector-hnsw dimensions=2001 compression=half (does half lift the 2000 cap?)',
    ci('dims', [hnsw('ix_hnsw_2001_half', path='hnsw_2001_half', dims=2001, compression='half')]),
    created('vector-hnsw 2001 dimensions with compression half: index CREATED, so half lifts the 2000 cap',
            'vector-hnsw 2001 dimensions with compression half: REJECTED with'))

run('g10_setup', '(g) insert five documents into diskann', {'insert': 'diskann', 'documents': DOCS}, inserted('five documents into t_vector.diskann'))
g10 = run('g10', '(g) does vector-diskann exist? dimensions=3, no compression, on 5 documents (same spec as the 0.117 parity test)',
          ci('diskann', [diskann('v_diskann')]),
          created('vector-diskann EXISTS on this engine: a 3-dimensional DiskANN index is created', 'vector-diskann (3 dimensions) is REJECTED with'))
for sid, dims, comp, extra in [('g11', 16001, 'pq', False), ('g12', 16000, 'pq', False), ('g13', 2001, None, False), ('g14', 2000, None, True)]:
    opts = {} if comp is None else {'compression': comp}
    path = f'diskann_{dims}_{comp or "none"}'
    label = f"vector-diskann dimensions={dims} compression={comp or 'none'}"
    run(sid, f"(g{', extra' if extra else ''}) {label} on the empty collection dims", ci('dims', [diskann(f'ix_{path}', path=path, dims=dims, **opts)]),
        created(f'{label}: index CREATED', f'{label}: REJECTED with'))
run('g15', '(g, extra) vector-hnsw dimensions=3 compression=pq: is pq a known compression value on this engine at all?',
    ci('dims', [hnsw('ix_hnsw_3_pq', path='hnsw_3_pq', dims=3, compression='pq')]),
    created('vector-hnsw with compression pq: index CREATED', 'vector-hnsw with compression pq: REJECTED with'))
run('g15b', '(g, extra) control: vector-hnsw dimensions=3 compression=bogus (message for an unknown compression value)',
    ci('dims', [hnsw('ix_hnsw_3_bogus', path='hnsw_3_bogus', dims=3, compression='bogus')]),
    created('vector-hnsw with compression bogus: index CREATED (unexpected)', 'vector-hnsw with compression bogus: REJECTED with'))
g15c = run('g15c', '(g, extra) vector-ivf dimensions=3 compression=pq: does any kind available here accept pq?',
           ci('dims', [ivf('ix_ivf_3_pq', path='ivf_3_pq', dims=3, numLists=1, compression='pq')]),
           created('vector-ivf with compression pq: index CREATED', 'vector-ivf with compression pq: REJECTED with'))
if g15c['outcome'] == 'ok':
    for sid, dims in [('g15d', 16001), ('g15e', 16000)]:
        run(sid, f'(g, extra) vector-ivf dimensions={dims} compression=pq on the empty collection dims',
            ci('dims', [ivf(f'ix_ivf_{dims}_pq', path=f'ivf_{dims}_pq', dims=dims, numLists=1, compression='pq')]),
            created(f'vector-ivf {dims} pq: index CREATED', f'vector-ivf {dims} pq: REJECTED with'))
if g10['outcome'] == 'ok':
    # Only reached if the DiskANN kind exists: search it and retry PQ where the collection holds data of that width.
    run('g16', '(g) $search on the DiskANN index', search('diskann', Q, k=3), searched('The $search on the DiskANN index', expect=[1, 4, 5]))
    run('g17_setup', '(g) insert five 16000-wide and five 16001-wide documents into pqdata',
        {'insert': 'pqdata', 'documents': [{'_id': i, 'w': [float((i * 7 + d) % 11) for d in range(16000)]} for i in range(1, 6)]
         + [{'_id': 10 + i, 'w1': [float((i * 5 + d) % 13) for d in range(16001)]} for i in range(1, 6)]},
        inserted('ten wide documents into t_vector.pqdata'))
    run('g17', '(g) vector-diskann dimensions=16000 compression=pq on a collection holding 16000-wide vectors',
        ci('pqdata', [diskann('ix_pq_16000', path='w', dims=16000, compression='pq')]),
        created('vector-diskann 16000 pq on data: index CREATED', 'vector-diskann 16000 pq on data: REJECTED with'))
    run('g18', '(g) vector-diskann dimensions=16001 compression=pq on a collection holding 16001-wide vectors',
        ci('pqdata', [diskann('ix_pq_16001', path='w1', dims=16001, compression='pq')]),
        created('vector-diskann 16001 pq on data: index CREATED (no 16000 cap)', 'vector-diskann 16001 pq on data: REJECTED with'))

# ================================================================ (h) BSON Binary vectors
bin9 = Binary.from_vector([1.0, 0.0, 0.0], BinaryVectorDtype.FLOAT32)   # subtype 9, float32 BSON vector
bin0 = Binary(struct.pack('<3f', 1.0, 0.0, 0.0), 0)                     # subtype 0, packed little-endian float32
bin9_after = Binary.from_vector([0.0, 1.0, 0.0], BinaryVectorDtype.FLOAT32)
run('h_setup', '(h) insert three number[] documents into bin', {'insert': 'bin', 'documents': DOCS[:3]}, inserted('three number[] documents into t_vector.bin'))
run('h1', '(h) insert documents whose v is BSON Binary: subtype 9 (float32 vector) and subtype 0 (packed float32), before any index',
    {'insert': 'bin', 'documents': [{'_id': 10, 'tag': 'bin9', 'v': bin9}, {'_id': 11, 'tag': 'bin0', 'v': bin0}]},
    inserted('two Binary-typed v documents (subtypes 9 and 0)'))
run('h2', '(h) create vector-hnsw on bin while it holds Binary-typed v', ci('bin', [hnsw('v_hnsw')]),
    created('The HNSW index builds over a collection that holds Binary-typed v without error', 'The HNSW build over Binary-typed v fails'))
run('h3', '(h) insert a Binary subtype 9 v after the index exists',
    {'insert': 'bin', 'documents': [{'_id': 12, 'tag': 'bin9_after', 'v': bin9_after}]},
    inserted('a Binary subtype 9 v document after the HNSW index exists'))


def h4_reading(r):
    if r['outcome'] != 'ok':
        return f"The number[] query failed: {etext(r)}."
    ids = [i for i, _ in hits(r)]
    present = [i for i in ids if i in (10, 11, 12)]
    return (f"A number[] query vector with k=10 over 6 documents returned (_id, score) {hits(r)}; the Binary-typed documents "
            + (f"{present} ARE among the results." if present else "(_id 10, 11, 12) are NOT among the results."))


run('h4', '(h) $search with a number[] query vector, k=10 over 6 documents', search('bin', Q, k=10), h4_reading)
run('h5', '(h) $search with a Binary subtype 9 query vector', search('bin', bin9, k=10),
    lambda r: (f"A Binary subtype 9 query vector is ACCEPTED and returns (_id, score) {hits(r)}." if r['outcome'] == 'ok'
               else f"A Binary subtype 9 query vector is rejected with {etext(r)}."))
run('h6', '(h) $search with a Binary subtype 0 query vector', search('bin', bin0, k=10),
    lambda r: (f"A Binary subtype 0 query vector is ACCEPTED and returns (_id, score) {hits(r)}." if r['outcome'] == 'ok'
               else f"A Binary subtype 0 query vector is rejected with {etext(r)}."))


def h7_reading(r):
    if r['outcome'] != 'ok':
        return f"find failed: {etext(r)}."
    docs = r['response']['cursor']['firstBatch']
    subs = [((d.get('v') or {}).get('$binary') or {}).get('subType') for d in docs]
    return f"find returns {len(docs)} Binary-typed documents with v subtypes {subs}, so they are stored intact and only vector search leaves them out."


run('h7', '(h) plain find of the Binary-typed documents', {'find': 'bin', 'filter': {'_id': {'$in': [10, 11, 12]}}}, h7_reading)

# ================================================================ final index state, option keys across all vector indexes
option_keys = {}
for c in ['docs', 'empty_hnsw', 'ef_probe', 'ivf', 'dims', 'diskann', 'bin'] + (['pqdata'] if g10['outcome'] == 'ok' else []):
    r = run(f'final_listIndexes_{c}', 'record the final index state', {'listIndexes': c},
            lambda r, c=c: (f"Index names on {c}: {[i['name'] for i in r['response']['cursor']['firstBatch']]}." if r['outcome'] == 'ok'
                            else f"listIndexes on {c} failed: {etext(r)}."))
    if r['outcome'] == 'ok':
        for ix in r['response']['cursor']['firstBatch']:
            if 'cosmosSearch' in (ix.get('key') or {}).values():
                opts = ix.get('cosmosSearchOptions') or ix.get('cosmosSearch') or {}
                option_keys[f"{c}.{ix['name']}"] = {
                    'kind': opts.get('kind'), 'compression': opts.get('compression'),
                    'has_cosmosSearchOptions': 'cosmosSearchOptions' in ix, 'has_cosmosSearch': 'cosmosSearch' in ix,
                    'top_level_keys': sorted(ix)}

# ================================================================ cleanup
run('cleanup', 'drop the test database t_vector', {'dropDatabase': 1}, okread('Database t_vector dropped.'))
run('cleanup_verify', 'confirm t_vector holds no collections after the drop', {'listCollections': 1, 'nameOnly': True},
    lambda r: (f"t_vector lists {len(r['response']['cursor']['firstBatch'])} collections after the drop." if r['outcome'] == 'ok'
               else f"listCollections failed: {etext(r)}."))


# ================================================================ automatic comparison with 0.117
def round_scores(d):
    if isinstance(d, dict) and isinstance(d.get('score'), float):
        d = dict(d)
        d['score'] = round(d['score'], 6)
    return d


def sig(s):
    if s.get('outcome') != 'ok':
        e = s.get('error') or {}
        return {'outcome': s.get('outcome'), 'code': e.get('code'), 'codeName': e.get('codeName'),
                'errmsg': e.get('errmsg') or e.get('message'), 'errorLabels': e.get('errorLabels') or []}
    r, cmd = s.get('response'), s.get('command') if isinstance(s.get('command'), dict) else {}
    if isinstance(r, list):
        return {'outcome': 'ok', 'docs': r}
    if not isinstance(r, dict):
        return {'outcome': 'ok', 'response': r}
    if 'insert' in cmd:
        n = r.get('n') if 'n' in r else (len(r['insertedIds']) if 'insertedIds' in r else None)
        return {'outcome': 'ok', 'n': n, 'writeErrors': r.get('writeErrors')}
    if 'find' in cmd and 'cursor' in r:
        return {'outcome': 'ok', 'docs': r['cursor'].get('firstBatch')}
    if 'cursor' in r:
        return {'outcome': 'ok', 'docs': [round_scores(d) for d in r['cursor'].get('firstBatch', [])]}
    return {'outcome': 'ok', 'response': r}


comparison = []
try:
    prev = {s['step']: s for s in json.load(open(PREV_REPORT))['steps']}
    try:
        par = next(s for s in json.load(open(PREV_PARITY))['steps'] if s['step'] == '06-vector-diskann')
        par = dict(par, outcome='error', command=None)
        prev['g10'] = par
    except Exception:
        pass
    seen = set()
    for s in steps:
        p = prev.get(s['step'])
        if p is None:
            comparison.append({'step': s['step'], 'status': 'new_on_1_2_0'})
            continue
        seen.add(s['step'])
        a, bb = sig(p), sig(s)
        src = 'local-gateway-parity 06-vector-diskann (0.117)' if s['step'] == 'g10' else 'vector-index-rules (0.117)'
        if a == bb:
            comparison.append({'step': s['step'], 'status': 'identical', 'compared_with': src})
        else:
            comparison.append({'step': s['step'], 'status': 'different', 'compared_with': src, 'was_0_117': a, 'now_1_2_0': bb})
    for sid in prev:
        if sid not in seen and sid not in [s['step'] for s in steps]:
            comparison.append({'step': sid, 'status': 'missing_on_1_2_0'})
except Exception as e:
    comparison.append({'error': f'comparison with the 0.117 report failed: {type(e).__name__}: {e}'})

S = {s['step']: s for s in steps}
report = {
    'test': 'vector-index-rules',
    'stage': 'ENGINE 1.2.0 RERUN',
    'database': DB,
    'ran_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'target': f'documentdb-local container {CONTAINER}, localhost:10260, TLS with a self-signed certificate (open-source DocumentDB engine + gateway)',
    'engine': {
        'buildInfo_version': (S['env_buildInfo'].get('response') or {}).get('version'),
        'hello_internal_documentdb_versions': ((S['env_hello'].get('response') or {}).get('internal') or {}).get('documentdb_versions'),
        'container_image_and_labels': (S['env_image'].get('response') or {}).get('stdout'),
        'release_log_line': (S['env_release_line'].get('response') or {}).get('stdout'),
        'pg_extensions': (S['env_extensions'].get('response') or {}).get('stdout'),
        'binary_and_postgres_version': (S['env_binary_version'].get('response') or {}).get('stdout'),
        'index_access_methods': (S['env_access_methods'].get('response') or {}).get('stdout'),
    },
    'driver': f'pymongo {pymongo.__version__}',
    'python': sys.version.split()[0],
    'evidence_scope': ('Observations are about the open-source DocumentDB engine and gateway at the version above (documentdb 1.2-0, '
                       'binary 1.2.0, commit 965b6e7a), as packaged in documentdb-local. buildInfo reports only the MongoDB '
                       'compatibility version 7.0.0. None of this proves managed Azure DocumentDB behaviour.'),
    'baseline_0_117': PREV_REPORT,
    'vector_index_option_keys': option_keys,
    'comparison_with_0_117_auto': comparison,
    'steps': steps,
}
text = scrub(json.dumps(report, indent=2, default=str))
with open(REPORT, 'w') as fh:
    fh.write(text)
print('wrote', REPORT, len(steps), 'steps')
print('AUTO COMPARISON:')
for c in comparison:
    print('  ', c['step'] if 'step' in c else '', c.get('status') or c.get('error'))
