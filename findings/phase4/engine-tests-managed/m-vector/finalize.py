"""Assemble report.json for m-vector from the step files, add one-sentence readings and the
comparison with the open-source engine results (findings/phase4/engine-tests/vector-index-rules)."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OSS_DIR = '/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests'
OSS = {s['step']: s for s in json.load(open(f'{OSS_DIR}/vector-index-rules/report.json'))['steps']}
PARITY = {s['step']: s for s in json.load(open(f'{OSS_DIR}/local-gateway-parity/report.json'))['steps']}

FILES = ['steps_00_connect.json', 'steps_main.json', 'steps_g_hnsw_empty.json', 'steps_g_diskann_empty.json',
         'steps_g_ivf_empty.json', 'steps_g_noindex.json', 'steps_extra.json', 'steps_z_cleanup.json']
steps = []
for f in FILES:
    for s in json.load(open(os.path.join(HERE, f))):
        s['source_file'] = f
        steps.append(s)
steps.sort(key=lambda s: s['at_utc'])
S = {}
for i, s in enumerate(steps, 1):
    s['seq'] = i
    S[s['step']] = s

# h1a was tagged with the OSS 'setup' step by mistake: that OSS step is the docs insert, not the bin insert.
S['h1a'].pop('oss_step', None)


def e(sid):
    return S[sid]['error']


def ids(sid):
    s = S[sid]
    return [d['_id'] for d in s['response']['cursor']['firstBatch']] if s['outcome'] == 'ok' else None


def scores(sid):
    return [round(d['score'], 4) for d in S[sid]['response']['cursor']['firstBatch']]


def spec_suffix(msg):
    m = re.match(r'^Error in specification \{.*\}:(.*)$', msg, re.S)
    return m.group(1) if m else msg


def q(msg):
    return '"' + msg + '"'


# ---------------------------------------------------------------- sanity checks on the facts the readings state
assert S['a1']['outcome'] == 'ok' and S['b1']['response']['raw']['defaultShard']['note'] == 'all indexes already exist'
for sid in ('a2', 'a3', 'a4', 'a5'):
    assert e(sid)['code'] == 85 and e(sid)['codeName'] == 'IndexOptionsConflict', sid
for sid in ('c1', 'c2', 'c3', 'c4', 'b3', 'b4'):
    assert e(sid)['code'] == 86 and e(sid)['codeName'] == 'IndexKeySpecsConflict', sid
assert e('d2')['code'] == 197
vec_d1 = [ix for ix in S['d1']['response']['cursor']['firstBatch'] if ix['name'] == 'v_hnsw'][0]
assert 'cosmosSearchOptions' in vec_d1 and 'cosmosSearch' not in vec_d1 and 'ns' not in vec_d1
assert ids('e3') == [1, 4, 5] and ids('i3') == [1, 4, 5] and ids('i4') == [1, 4, 5]
assert ids('h4') == [1, 3, 2] and ids('hd4') == [1, 3, 2]
for sid in ('h5', 'h6', 'hd5', 'hd6'):
    assert e(sid)['code'] == 2 and 'expected an array type field' in e(sid)['errmsg']
polls = [s for s in steps if '.poll' in s['step']]
assert all(ids(s['step']) == [1, 4, 5] for s in polls)
for s in steps:
    if s['outcome'] == 'error':
        assert 'errorLabels' not in (s['error'].get('raw') or {}), s['step']

# ---------------------------------------------------------------- readings
R = {}
h = S['0.hello']['response']
R['0.hello'] = (f"The plain host answers as the managed service: maxWireVersion {h['maxWireVersion']}, "
                f"internal.documentdb_versions {h['internal']['documentdb_versions']}, kind {h['internal']['kind']}, msg {h['msg']}.")
R['0.buildInfo'] = f"buildInfo reports version {S['0.buildInfo']['response']['version']}, the MongoDB compatibility version rather than an engine build."
R['0.listDatabases'] = 'mt_vector did not exist before the test (listDatabases filtered to mt_vector returned no databases).'
R['a0'] = 'Five 3-dimensional number[] documents were inserted into mt_vector.docs (n 5).'
R['a1'] = 'The first vector-hnsw index v_hnsw on path v was created (raw.defaultShard numIndexesBefore 1, numIndexesAfter 2).'
R['a2'] = f"A second vector-hnsw on the same path under another name with identical options is rejected: code 85 IndexOptionsConflict {q(e('a2')['errmsg'])}."
for sid, what in (('a3', 'a different kind (vector-ivf)'), ('a4', 'different options (m 32)'), ('a5', 'kind vector-diskann')):
    R[sid] = (f"A second vector index on the same path under another name with {what} is rejected with code 85 IndexOptionsConflict "
              f"(an equivalent index exists with a different name and options; both specs are echoed).")
R['b1'] = 'Repeating the identical createIndexes is a no-op: ok 1, note "all indexes already exist", numIndexesBefore 2 = numIndexesAfter 2.'
for sid, what in (('c1', 'different options (m 32)'), ('c2', 'a different similarity (L2)'), ('c3', 'a different kind (vector-ivf)'),
                  ('c4', 'a different kind (vector-diskann)')):
    R[sid] = (f"Reusing the name v_hnsw with {what} is rejected with code 86 IndexKeySpecsConflict (an existing index has the same "
              f"name; both specs are echoed).")
R['d1'] = ('listIndexes returns the vector index as {v, key, name, cosmosSearchOptions}: the options are under cosmosSearchOptions only, '
           'with no cosmosSearch key and no ns field, unlike the Learn getIndexes sample.')
R['d2a'] = 'Created the empty collection alias_key.'
R['d2'] = (f"createIndexes with the options under a cosmosSearch key (the key in Learn's getIndexes sample) is rejected with code 197 "
           f"InvalidIndexSpecificationOption, whose message says {q(spec_suffix(e('d2')['errmsg']).split(' Provided specification')[0].rstrip('.'))}.")
R['d3'] = 'The cosmosSearch-key attempt created nothing: alias_key still has only _id_.'
R['e0'] = 'Inserted the same five documents into mt_vector.diskann (n 5).'
R['e1'] = 'vector-diskann with dimensions 3 is created on the M30 cluster (numIndexesBefore 1, numIndexesAfter 2).'
R['e2'] = ('The vector-diskann index document carries its options under cosmosSearchOptions {kind vector-diskann, dimensions 3, '
           'similarity COS, maxDegree 32, lBuild 50}, with no cosmosSearch key.')
R['e3'] = f"A $search on the new DiskANN index returns _ids {ids('e3')} with scores {scores('e3')}, the correct nearest neighbours."
R['g.noindex.1'] = 'Inserted five documents into timing_noindex, which has no vector index.'
R['g.noindex.2'] = (f"$search cosmosSearch on a collection without a vector index fails with code 2 BadValue {q(e('g.noindex.2')['errmsg'])} "
                    "rather than returning empty results.")
R['i0a'] = 'Inserted the five documents into mt_vector.ivf (n 5).'
R['i0'] = 'The control vector-ivf index with numLists 1 is created on 5 documents.'
R['i0b'] = 'The control index v_ivf1 was dropped (nIndexesWas 2).'
R['i1'] = (f"numLists 0 is rejected with code 67 CannotCreateIndex and a message whose numbers are swapped: "
           f"{q(spec_suffix(e('i1')['errmsg']))}.")
R['i2'] = 'numLists 100 on 5 documents is accepted, with no warning or note in the response (numIndexesBefore 1, numIndexesAfter 2).'
R['i3'] = f"A search on the numLists 100 index with the default nProbes returns the correct neighbours _ids {ids('i3')} (scores {scores('i3')})."
R['i4'] = f"With nProbes 100 the search returns the same _ids {ids('i4')} and scores."
R['b2'] = 'Repeating the identical vector-diskann createIndexes is also a no-op: ok 1, note "all indexes already exist".'
R['b3'] = ('The same name with the same option values in a different key order is not treated as identical: code 86 '
           'IndexKeySpecsConflict, so the no-op needs the options document in the stored key order.')
R['b4'] = ('Omitting the documented defaults (m 16, efConstruction 64) under the same name is also rejected with code 86 '
           'IndexKeySpecsConflict: defaults are not filled in before the comparison.')
gh = S['d4.hello']['response']
R['d4.hello'] = (f"The .global. host reaches the same cluster (step d4 sees mt_vector.docs and v_hnsw) and reports endpointName "
                 f"{gh['endpointName']}, documentdb_versions {gh['internal']['documentdb_versions']} and maxWireVersion {gh['maxWireVersion']}.")
R['d4'] = 'listIndexes through the .global. host returns the identical v_hnsw document, options under cosmosSearchOptions, no cosmosSearch key.'
R['z1'] = f"Listed the {len(S['z1']['response']['cursor']['firstBatch'])} collections left in mt_vector before the drop."
R['z2'] = 'dropDatabase returned ok 1 with dropped "mt_vector".'
R['z3'] = 'mt_vector no longer exists (listDatabases filtered to mt_vector returned no databases).'

KIND_NAME = {'hnsw': 'vector-hnsw', 'ivf': 'vector-ivf', 'diskann': 'vector-diskann'}
for s in steps:
    sid = s['step']
    if sid in R:
        continue
    cmd = s.get('command') or {}
    if 'create' in cmd and len(cmd) == 1:
        R[sid] = f"Created the empty collection {cmd['create']} (ok 1)."
    elif re.fullmatch(r'f\d+', sid):
        o = cmd['indexes'][0]['cosmosSearchOptions']
        label = f"{o['kind']} with {o['dimensions']} dimensions and compression {o.get('compression', 'none')}"
        if s['outcome'] == 'ok':
            extra = ''
            if sid == 'f12':
                extra = f", taking {s['elapsed_s']} s, the slowest create in the run"
            if sid == 'f13':
                extra = ': half lifts the 2000 uncompressed cap'
            if sid == 'f15':
                extra = ': pq lifts the 2000 uncompressed cap'
            R[sid] = f"{label} is created on an empty collection{extra}."
        else:
            R[sid] = f"{label} is rejected: code {s['error']['code']} {s['error']['codeName']} {q(spec_suffix(s['error']['errmsg']))}."
    elif re.fullmatch(r'hd?\d[ab]?', sid):
        coll = cmd.get('insert') or cmd.get('createIndexes') or cmd.get('aggregate') or cmd.get('find')
        kind = 'vector-diskann' if coll == 'bin_diskann' else 'vector-hnsw'
        n = sid.lstrip('hd')
        if n == '1a':
            R[sid] = f'Inserted three number[] documents (_id 1-3) into {coll} (n 3).'
        elif n == '1b':
            R[sid] = (f'Two documents whose v is BSON Binary (subtype 9 float32 vector, subtype 0 packed floats) insert into {coll} '
                      'without error (n 2) before any index exists.')
        elif n == '2':
            R[sid] = f'The {kind} index builds without error over {coll}, which already holds Binary-typed v values.'
        elif n == '3':
            R[sid] = f'A Binary subtype 9 v inserted into {coll} after the {kind} index exists is accepted (n 1).'
        elif n == '4':
            R[sid] = (f"A number[] query vector with k 10 over the six documents of {coll} returns only the three number[] documents "
                      f"(_ids {ids(sid)}); the three Binary-typed documents are silently absent.")
        elif n in ('5', '6'):
            st = '9' if n == '5' else '0'
            R[sid] = f"A Binary subtype {st} query vector on {coll} is rejected: code 2 BadValue {q(s['error']['errmsg'])}."
        elif n == '7':
            subs = [d['v']['$binary']['subType'] for d in s['response']['cursor']['firstBatch']]
            R[sid] = (f"find returns the three Binary-typed documents of {coll} intact (subtypes {subs}, bytes as inserted), "
                      'so only vector search leaves them out.')
    elif sid.startswith('final.listIndexes.'):
        fb = s['response']['cursor']['firstBatch']
        vec = [ix for ix in fb if ix['name'] != '_id_']
        if vec:
            keys = sorted({k for ix in vec for k in ix})
            R[sid] = (f"Final state of {cmd['listIndexes']}: {[ix['name'] for ix in vec]} besides _id_, each with top-level keys {keys} "
                      '(options under cosmosSearchOptions).')
        else:
            R[sid] = f"Final state of {cmd['listIndexes']}: only _id_ (the vector index attempt on it was rejected)."
    elif '.poll' in sid:
        R[sid] = (f"Poll at +{s['offset_s_after_insert']} s after the insert returned _ids {ids(sid)} with scores {scores(sid)}, "
                  'the complete expected result.')
    elif sid.endswith('.summary'):
        r = s['response']
        if r['variant'] == 'hnsw_empty':
            R[sid] = ('Results were present and complete from the first poll (+0 s) and in all 25 polls through +240 s: no empty-result '
                      'window was observed with 5 documents.')
        else:
            R[sid] = (f"For {r['variant']} results were complete from the first poll (+0 s); the loop stopped after "
                      f"{r['polls']} consecutive complete polls.")
    elif re.fullmatch(r'g\.\w+\.2', sid):
        R[sid] = (f"{cmd['indexes'][0]['cosmosSearchOptions']['kind']} was created on the empty {cmd['createIndexes']} "
                  f"in {s['elapsed_s']} s (numIndexesBefore 1, numIndexesAfter 2).")
    elif re.fullmatch(r'g\.\w+\.3', sid):
        R[sid] = f"Five documents were inserted into {cmd['insert']} after the index existed (n 5); the poll clock starts when this insert returned."
for s in steps:
    s['reading'] = R[s['step']]
    if s['outcome'] == 'error' and 'errorLabels' not in (s['error'].get('raw') or {}):
        s['error']['errorLabels'] = 'absent (the reply has no errorLabels key)'

# ---------------------------------------------------------------- comparison with the open-source engine
LOCAL_DISKANN = ('The open-source image (documentdb-local 0.117) rejects vector-diskann altogether (code 67 CannotCreateIndex '
                 '"Invalid search index kind vector-diskann"), so this was not testable locally.')


def oss_ref(ref):
    if ref.startswith('local-gateway-parity/'):
        p = PARITY[ref.split('/', 1)[1]]['error']
        return {'outcome': 'error', 'code': p['code'], 'codeName': p['codeName'], 'errmsg': p['errmsg']}
    o = OSS[ref]
    if o['outcome'] == 'ok':
        return {'outcome': 'ok', 'response': o['response']}
    oe = o['error']
    return {'outcome': 'error', 'code': oe['code'], 'codeName': oe['codeName'], 'errmsg': oe['errmsg']}


def compare(s, o):
    if s['outcome'] != o['outcome']:
        what = f"code {o.get('code')} {o.get('codeName')} {q(spec_suffix(o.get('errmsg', '')))}" if o['outcome'] == 'error' else 'ok'
        return 'different', f"open-source: {what}; managed: {s['outcome']}."
    if s['outcome'] == 'error':
        me = s['error']
        same_code = (me['code'], me['codeName']) == (o['code'], o['codeName'])
        if me['errmsg'] == o['errmsg']:
            rel = 'identical errmsg'
        elif spec_suffix(me['errmsg']) == spec_suffix(o['errmsg']):
            rel = 'identical message after the echoed index specification (the echoed spec differs only in index name and path)'
        else:
            rel = f"different errmsg (open-source: {q(o['errmsg'])})"
        return ('same' if same_code and not rel.startswith('different') else 'different'), \
            f"open-source: code {o['code']} {o['codeName']}, {rel}."
    cmd = s['command']
    mr, orr = s['response'], o['response']
    if 'createIndexes' in cmd:
        def d(r):
            ds = r['raw']['defaultShard']
            return ds['numIndexesAfter'] - ds['numIndexesBefore'], ds.get('note')
        same = d(mr) == d(orr) and sorted(mr) == sorted(orr)
        return ('same' if same else 'different'), \
            f"open-source: ok, index count +{d(orr)[0]}, note {d(orr)[1]!r}, same raw.defaultShard response shape." if same else \
            f"open-source: {json.dumps(orr)}."
    if 'aggregate' in cmd:
        ob = orr['cursor']['firstBatch']
        mb = mr['cursor']['firstBatch']
        same = [(x['_id'], round(x['score'], 6)) for x in ob] == [(x['_id'], round(x['score'], 6)) for x in mb]
        return ('same' if same else 'different'), \
            f"open-source returned _ids {[x['_id'] for x in ob]} with scores {[round(x['score'], 4) for x in ob]}."
    if 'listIndexes' in cmd:
        same = orr['cursor']['firstBatch'] == mr['cursor']['firstBatch']
        return ('same' if same else 'different'), \
            f"open-source listIndexes firstBatch {'is identical' if same else 'differs: ' + json.dumps(orr['cursor']['firstBatch'])}."
    if 'insert' in cmd:
        on = orr.get('n', len(orr.get('insertedIds', [])))
        return ('same' if on == mr['n'] else 'different'), f"open-source inserted {on} document(s) without error."
    if 'find' in cmd:
        same = orr == mr['cursor']['firstBatch']
        return ('same' if same else 'different'), f"open-source find returned {'the same three documents and bytes' if same else json.dumps(orr)}."
    return 'different', 'not compared'


SETUP_IDS = {'d2a', 'e0', 'h1a', 'hd1a', 'i0a', 'i0b', 'g.noindex.1'}


def uses_diskann(s):
    c = s.get('command')
    if not c:
        return 'diskann' in s['step']
    coll = str(next(iter(c.values())))
    return 'vector-diskann' in json.dumps(c) or 'diskann' in coll


def classify(s):
    sid = s['step']
    ref = s.get('oss_step')
    if ref:
        o = oss_ref(ref)
        s['oss'] = {'step': ref, **({'response': o['response']} if o['outcome'] == 'ok' else
                                    {'error': {k: o[k] for k in ('code', 'codeName', 'errmsg')}})}
        return compare(s, o)
    if sid.startswith('0.') or sid == 'd4.hello':
        return 'n/a', 'Identity, not behaviour: the open-source gateway reported maxWireVersion 21 and buildInfo 7.0.0.'
    if (sid in SETUP_IDS or sid.endswith('.create') or sid.startswith('final.') or sid.startswith('z')
            or re.fullmatch(r'g\.\w+\.1', sid)):
        return 'n/a', 'Setup, bookkeeping or cleanup step.'
    if sid == 'g.hnsw_empty.summary':
        return 'same', ('Open-source steps e1-e3: HNSW created on an empty collection, five inserts, and a search right after them '
                        'returned the complete result with no visible delay; the open-source test did not poll further.')
    if uses_diskann(s):
        return 'not_tested_locally', LOCAL_DISKANN
    if '.poll' in sid or sid.endswith('.summary'):
        return 'not_tested_locally', 'The open-source test queried once, right after the inserts (its step e3), and did not poll.'
    if s['extra']:
        return 'not_tested_locally', 'Extra managed-service check with no open-source counterpart.'
    return 'n/a', 'Setup, bookkeeping or cleanup step.'


for s in steps:
    s['vs_open_source'], s['vs_open_source_detail'] = classify(s)

# ---------------------------------------------------------------- conclusions
def cj(x):
    return json.dumps(x, separators=(', ', ': '))


vec_e2 = [ix for ix in S['e2']['response']['cursor']['firstBatch'] if ix['name'] == 'v_diskann'][0]
CONCLUSIONS = [
    {'question': '(a) A second vector index on the same path with a different name: error code and message',
     'answer': (f"Rejected with code 85 IndexOptionsConflict in every variant, with no errorLabels. Identical options under another name: "
                f"{q(e('a2')['errmsg'])}. Another kind (vector-ivf), other options (m 32) or kind vector-diskann under another name: "
                f"\"An equivalent index already exists with a different name and options. Requested index: {{ ... }}, existing index: {{ ... }}\" "
                f"with both specs echoed. One vector index per path is enforced whatever the kind or options."),
     'vs_open_source': 'same', 'confidence': 'observed',
     'detail': 'errmsg byte-identical to documentdb-local 0.117 for the three variants it ran (OSS a2-a4); the DiskANN variant (a5) is managed-only.'},
    {'question': '(b) Repeating the identical createIndexes: no-op response',
     'answer': (f"No-op: {cj(S['b1']['response'])}. An identical vector-diskann repeat is also a no-op (b2). The match is exact: the same "
                f"name and option values with the option keys in another order (b3), or with the defaults m 16 and efConstruction 64 "
                f"omitted (b4), fail with code 86 IndexKeySpecsConflict instead of a no-op."),
     'vs_open_source': 'same', 'confidence': 'observed',
     'detail': 'b1 identical to OSS b1; the key-order and omitted-default checks (b3, b4) were not run on the open-source engine.'},
    {'question': '(c) Same name, different options: error',
     'answer': ("Code 86 IndexKeySpecsConflict, no errorLabels: \"An existing index has the same name as the requested index. When index "
                "names are not specified, they are auto generated and can cause conflicts. Please refer to our documentation. Requested "
                "index: { ... }, existing index: { ... }\". The same for other m (c1), other similarity L2 (c2), kind vector-ivf (c3) and "
                "kind vector-diskann (c4)."),
     'vs_open_source': 'same', 'confidence': 'observed',
     'detail': 'errmsg byte-identical to OSS c1-c3; c4 (DiskANN) is managed-only.'},
    {'question': '(d) listIndexes: are the vector options under cosmosSearch, cosmosSearchOptions, or both? (key question)',
     'answer': (f"cosmosSearchOptions only. Raw index document: {cj(vec_d1)}. There is no cosmosSearch key and no ns field, for every "
                f"vector index in the run (HNSW, IVF, DiskANN, compression half and pq), and the same document comes back through the "
                f".global. host (d4). The options are echoed exactly as sent; no defaults (for example pqCompressedDims) are added. "
                f"createIndexes with the options under a cosmosSearch key is rejected: code 197 InvalidIndexSpecificationOption "
                f"{q(spec_suffix(e('d2')['errmsg']).split(' Provided specification')[0])} (d2). The Learn vector-search sample "
                f"(\"Get vector index definitions\", showing cosmosSearch: {{...}} and ns) does not match the managed service."),
     'vs_open_source': 'same', 'confidence': 'observed',
     'detail': 'The listIndexes firstBatch is identical to documentdb-local 0.117 (OSS d1).'},
    {'question': '(e) vector-diskann with dimensions 3 on M30, and its listIndexes document',
     'answer': (f"Created ({cj(S['e1']['response'])}, {S['e1']['elapsed_s']} s). listIndexes document: {cj(vec_e2)}. A $search for "
                f"[1,0,0] with k 3 returned _ids {ids('e3')} with scores {scores('e3')}."),
     'vs_open_source': 'different', 'confidence': 'observed',
     'detail': 'documentdb-local 0.117 rejects the same command: code 67 CannotCreateIndex "Invalid search index kind vector-diskann".'},
    {'question': '(f) Dimension caps for vector-hnsw and vector-ivf (2001/2000 uncompressed, 4001/4000 with compression half)',
     'answer': ("Both kinds: 2001 uncompressed rejected, code 67 CannotCreateIndex \"Error in specification {...}:field cannot have more "
                "than 2000 dimensions for vector index\"; 2000 created; 4001 with compression half rejected, code 67 \"...:field cannot have "
                "more than 4000 dimensions for vector index\"; 4000 with half created. Extra: vector-hnsw 2001 with half is created, so "
                "half lifts the cap to 4,000."),
     'vs_open_source': 'same', 'confidence': 'observed',
     'detail': 'Identical codes and messages to OSS g1-g9 (only the echoed index name and path differ).'},
    {'question': '(f) Dimension caps for vector-diskann (2001 uncompressed; 16001/16000 with compression pq)',
     'answer': (f"2001 uncompressed rejected with the same message as HNSW and IVF (code 67 \"...:field cannot have more than 2000 "
                f"dimensions for vector index\"); 2000 created (control). 16001 with compression pq rejected: code 67 CannotCreateIndex "
                f"{q(spec_suffix(e('f11')['errmsg']))}, worded differently from the 2,000 and 4,000 messages. 16000 with pq created on an "
                f"empty collection in {S['f12']['elapsed_s']} s; 2001 with pq created. Extra: compression half on DiskANN is rejected, code 67 "
                f"{q(spec_suffix(e('f14')['errmsg']))}. The documented 2,000 / 4,000 (half, HNSW and IVF) / 16,000 (pq, DiskANN) limits "
                f"are enforced."),
     'vs_open_source': 'not_tested_locally', 'confidence': 'observed',
     'detail': 'documentdb-local 0.117 has no vector-diskann kind.'},
    {'question': '(g) New empty collection, vector-hnsw, insert 5 documents, $search every 10 s for 4 minutes: when do results first appear?',
     'answer': ("Immediately. The first poll, sent as soon as the insert returned (+0.0 s), returned the complete result _ids [1, 4, 5] "
                "(scores 1.0, 0.9939, 0.1104), and so did all 25 polls through +240 s. Extras: vector-diskann and vector-ivf (numLists 1) on "
                "new empty collections also returned complete results at +0 s, and in parts (e), (h) and (i) a search sent within 0.2 s of "
                "creating an index over existing documents returned correct results. A $search on a collection with no vector index fails "
                "with code 2 BadValue \"Similarity index was not found for a vector similarity search query.\" rather than returning empty "
                "results. The 2 to 3 minutes of empty results in Learn's troubleshooting note did not occur at 5 documents; large "
                "collections were not tested."),
     'vs_open_source': 'same', 'confidence': 'observed',
     'detail': 'OSS e1-e3 also returned the complete result right after the inserts; the open-source test did not poll for 4 minutes.'},
    {'question': '(h) BSON Binary vectors (subtype 9 and 0) next to number[] documents: which documents does a number[] query return, and is a Binary query vector an error?',
     'answer': ("Binary subtype 9 (float32 BSON vector) and subtype 0 v values insert without error before and after the index exists, "
                "the index builds over them, and find returns them intact. A number[] query with k 10 over 3 number[] and 3 Binary "
                "documents returns only the number[] documents (_ids [1, 3, 2]); the Binary ones are silently absent. A Binary query vector, "
                "subtype 9 or 0, fails with code 2 BadValue \"Invalid type: expected an array type field, but received binData instead\". "
                "The same with a vector-diskann index (extra hd1b-hd7)."),
     'vs_open_source': 'same', 'confidence': 'observed',
     'detail': 'Identical to OSS h1-h7 (same _ids, scores, codes and messages, same stored bytes).'},
    {'question': '(i) IVF numLists 0 error text, and numLists 100 on 5 documents',
     'answer': (f"numLists 0: code 67 CannotCreateIndex {q(e('i1')['errmsg'])}, with the numbers swapped (the given value was 0 and the "
                f"minimum is 1). numLists 100 on 5 documents is accepted with no warning, and searches with the default nProbes and with "
                f"nProbes 100 both return the correct neighbours _ids [1, 4, 5]."),
     'vs_open_source': 'same', 'confidence': 'observed',
     'detail': 'errmsg byte-identical to OSS f1; OSS f2-f4 gave the same results.'},
    {'question': 'Error and reply shapes across the run',
     'answer': ('No error reply carried errorLabels (the key is absent from every raw error document). createIndexes replies are '
                'wrapped as {"raw": {"defaultShard": {...}}, "ok": 1}. Each successful vector createIndexes took about 1.07 to 1.09 s, '
                'even on an empty collection (16000-dimension pq: 4.08 s), while rejections returned in about 0.07 s.'),
     'vs_open_source': 'same', 'confidence': 'observed',
     'detail': 'Same reply shape and no labels on documentdb-local 0.117; the open-source timings were not compared.'},
]

NOTES = ('Phase 1, data-plane only: no cluster configuration was read or changed (no az CLI or ARM calls). Every step ran in database '
         'mt_vector, which did not exist at the start and was dropped at the end (z2) and confirmed absent (z3). Steps marked extra go '
         'beyond the stage spec but stay inside mt_vector: a5, c4 (DiskANN variants), b2-b4 (no-op exactness), d2-d4 (cosmosSearch '
         'key on create, .global. host), e3, f10 and f13-f15, hd1a-hd7 (Binary with DiskANN) and the g diskann, ivf and noindex variants. '
         'Learn pages read on 2026-11-25: vector-search (its getIndexes sample shows cosmosSearch and ns) and product-quantization (an '
         'empty collection trains PQ on random vectors, consistent with f12 succeeding on an empty collection). '
         "PyMongo's CosmosDB UserWarning was filtered and not recorded.")

# ---------------------------------------------------------------- report
report = {
    'test': 'm-vector',
    'database': 'mt_vector',
    'goal': 'Vector indexes on the managed service: one-index-per-path errors, no-op repeats, same-name conflicts, the listIndexes options key, '
            'DiskANN, dimension caps, new-index result delay, BSON Binary vectors, IVF numLists.',
    'target': ('Azure DocumentDB Microsoft.DocumentDB/mongoClusters "ddb-samples-shared", resource group documentdb-samples-rg, eastus, '
               'tier M30, one shard, server version 8.0, Premium SSD v2, high availability disabled, public access. Connected through '
               'MANAGED_URI (plain host, mongodb+srv, tls, SCRAM-SHA-256, retrywrites=false); step d4 also used MANAGED_GLOBAL_URI.'),
    'engine': {'hello.maxWireVersion': h['maxWireVersion'], 'hello.internal': h['internal'], 'hello.msg': h['msg'],
               'buildInfo.version': S['0.buildInfo']['response']['version']},
    'driver': 'PyMongo 4.20.1 on Python 3.13.13 (/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python); '
              "PyMongo's CosmosDB UserWarning was filtered.",
    'observed_on': '2026-11-25 (UTC timestamps on every step)',
    'evidence_scope': ('Observations of the managed service on 2026-11-25 at the engine versions above, with 3-dimensional vectors and at most '
                       '6 documents per collection. They say nothing about index build time on large collections.'),
    'open_source_reference': {
        'report': f'{OSS_DIR}/vector-index-rules/report.json',
        'engine': 'documentdb-local 0.117.0 (PostgreSQL 17.11, pgvector 0.8.6, wire version 21), see findings/phase4/ENGINE-TESTS.md',
        'diskann': f'{OSS_DIR}/local-gateway-parity/report.json step 06-vector-diskann',
        'mapping': 'managed a1-a4,b1,c1-c3,d1 = OSS a1-a4,b1,c1-c3,d1; managed f1-f8,f13 = OSS g1-g9; managed h1b-h7 = OSS h1-h7; '
                   'managed i0-i4 = OSS f0-f4; managed g.hnsw_empty.2/.3/.poll00 = OSS e1/e2/e3.',
    },
    'scripts': {n: os.path.join(HERE, n) for n in
                ('common.py', 'run_00_connect.py', 'run_main.py', 'run_g_timing.py', 'run_extra.py', 'run_z_cleanup.py', 'finalize.py')},
    'run_order': ['run_00_connect.py', 'run_main.py', 'run_g_timing.py hnsw_empty', 'run_g_timing.py diskann_empty',
                  'run_g_timing.py ivf_empty', 'run_g_timing.py noindex', 'run_extra.py', 'run_z_cleanup.py', 'finalize.py'],
    'masking': ('Every recorded string passed through a scrubber that removes the password and both URIs and masks e-mail addresses '
                'and GUIDs; nothing needed masking in the data-plane replies.'),
    'config_changes': [],
    'conclusions': CONCLUSIONS,
    'notes': NOTES,
    'steps': steps,
}
json.dump(report, open(os.path.join(HERE, 'report.json'), 'w'), indent=2)
print('report.json:', len(steps), 'steps')
for s in steps:
    print(f"{s['seq']:3d} {s['step']:<24} {s['outcome']:<6} {s['vs_open_source']:<19} {s['reading'][:150]}")
