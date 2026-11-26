"""Condense report.json steps into the {step, command, response, reading} list returned to the workflow.

report.json keeps every step with the exact command and the exact raw reply. This condensed list keeps every
test step, renders errors as 'code, codeName, errmsg (verbatim), errorLabels', abbreviates the repeated
five-document payload as DOCS and the repeated $project stage as PROJECT (both defined in the notes), and
groups repetitive setup, poll and DiskANN-repeat steps.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(HERE, 'report.json')))
steps = r['steps']
S = {s['step']: s for s in steps}

DOCS = [{'_id': 1, 'tag': 'a', 'v': [1.0, 0.0, 0.0]}, {'_id': 2, 'tag': 'b', 'v': [0.0, 1.0, 0.0]},
        {'_id': 3, 'tag': 'c', 'v': [0.0, 0.0, 1.0]}, {'_id': 4, 'tag': 'd', 'v': [0.9, 0.1, 0.0]},
        {'_id': 5, 'tag': 'e', 'v': [0.1, 0.9, 0.0]}]
PROJECT = {'$project': {'_id': 1, 'tag': 1, 'v': 1, 'score': {'$meta': 'searchScore'}}}


def cj(x):
    return json.dumps(x, separators=(',', ':'), ensure_ascii=False)


BASE = {'vector-hnsw': {'similarity': 'COS', 'm': 16, 'efConstruction': 64},
        'vector-ivf': {'similarity': 'COS'},
        'vector-diskann': {'similarity': 'COS', 'maxDegree': 32, 'lBuild': 50}}
MACRO = {'vector-hnsw': 'HNSW', 'vector-ivf': 'IVF', 'vector-diskann': 'DISKANN'}


def spec_macro(ix):
    """Render an index spec built by common.hnsw/ivf/diskann as a macro call; fall back to raw JSON."""
    o = ix.get('cosmosSearchOptions')
    if not o or ix.get('key') != {'v': 'cosmosSearch'} or set(ix) != {'name', 'key', 'cosmosSearchOptions'}:
        return cj(ix)
    kind = o.get('kind')
    base = BASE.get(kind)
    if base is None:
        return cj(ix)
    order = ['kind', 'dimensions', 'similarity'] + (['numLists'] if kind == 'vector-ivf' else []) + \
        [k for k in base if k != 'similarity']
    if list(o)[:len(order)] != order or any(o[k] != v for k, v in base.items()):
        return cj(ix)
    args = [cj(ix['name'])]
    if o['dimensions'] != 3:
        args.append(f"dims={o['dimensions']}")
    if kind == 'vector-ivf':
        args.append(f"numLists={o['numLists']}")
    for k in list(o)[len(order):]:
        args.append(f"{k}={cj(o[k])}")
    return f"{MACRO[kind]}({', '.join(args)})"


def cmd_str(s):
    c = json.loads(json.dumps(s['command']))
    db = 'admin' if s['step'] in ('0.hello', '0.buildInfo', '0.listDatabases', 'd4.hello', 'z3') else 'mt_vector'
    host = ' via MANAGED_GLOBAL_URI' if s['step'] in ('d4', 'd4.hello') else ''
    if 'createIndexes' in c:
        text = '{"createIndexes":' + cj(c['createIndexes']) + ',"indexes":[' + ','.join(spec_macro(ix) for ix in c['indexes']) + ']}'
    elif 'aggregate' in c and len(c['pipeline']) == 2 and c['pipeline'][1] == PROJECT and set(c) == {'aggregate', 'pipeline', 'cursor'}:
        st = c['pipeline'][0]['$search']
        cs = dict(st['cosmosSearch'])
        vec = cs.pop('vector'); path = cs.pop('path'); k = cs.pop('k')
        assert path == 'v' and st.get('returnStoredSource') is True
        extra = ''.join(f', {kk}={cj(vv)}' for kk, vv in cs.items())
        text = f"SEARCH({cj(c['aggregate'])}, vector={cj(vec)}, k={k}{extra})"
        return f"Database('{db}').command({text}){host}"
    else:
        if 'documents' in c:
            if c['documents'] == DOCS:
                c['documents'] = '__DOCS__'
            elif c['documents'] == DOCS[:3]:
                c['documents'] = '__DOCS[0:3]__'
        text = cj(c).replace('"__DOCS__"', 'DOCS').replace('"__DOCS[0:3]__"', 'DOCS[0:3]')
    return f"Database('{db}').command({text}){host}"


def resp_str(s):
    if s['outcome'] == 'ok':
        return cj(s['response'])
    e = s['error']
    labels = (e.get('raw') or {}).get('errorLabels')
    return (f"error: ok 0, code {e['code']}, codeName {e['codeName']}, errmsg: {e['errmsg']} | errorLabels: "
            f"{'absent' if labels is None else labels}")


def vs(s):
    v = s['vs_open_source']
    if v == 'n/a':
        return ''
    if v == 'not_tested_locally':
        if 'vector-diskann altogether' in s['vs_open_source_detail']:
            return ' Open source: not tested (no vector-diskann locally).'
        return ' Open source: not tested.'
    if v == 'different':
        return ' Open source: different (documentdb-local 0.117 rejects vector-diskann, code 67 "Invalid search index kind vector-diskann").'
    ref = s['oss']['step'] if s.get('oss') else 'e1-e3'
    return f' Open source ({ref}): same.'


def one(sid, label=None):
    s = S[sid]
    return {'step': label or sid, 'command': cmd_str(s), 'response': resp_str(s), 'reading': s['reading'] + vs(s)}


out = []
# identity and start state
out.append(one('0.hello'))
out.append({'step': '0.buildInfo, 0.listDatabases', 'command': cmd_str(S['0.buildInfo']) + ' ; ' + cmd_str(S['0.listDatabases']),
            'response': resp_str(S['0.buildInfo']) + ' ; ' + resp_str(S['0.listDatabases']),
            'reading': S['0.buildInfo']['reading'] + ' ' + S['0.listDatabases']['reading']})
for sid in ['a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'b1', 'c1', 'c2', 'c3', 'c4', 'd1']:
    out.append(one(sid))
out.append({'step': 'd2a, d2', 'command': cmd_str(S['d2a']) + ' ; ' + cmd_str(S['d2']),
            'response': resp_str(S['d2a']) + ' ; ' + resp_str(S['d2']), 'reading': S['d2']['reading'] + vs(S['d2'])})
for sid in ['d3', 'e0', 'e1', 'e2', 'e3']:
    out.append(one(sid))
fcreates = [s for s in steps if s['step'].startswith('f') and s['step'].endswith('.create')]
assert all(s['response'] == {'ok': 1.0} for s in fcreates)
out.append({'step': 'f*.create (15 setup steps)',
            'command': "Database('mt_vector').command({\"create\":<coll>}) for " + ', '.join(s['command']['create'] for s in fcreates),
            'response': 'every reply {"ok":1.0}',
            'reading': 'Each dimension-cap case got its own empty collection so one-index-per-path could not interfere.'})
for i in range(1, 16):
    out.append(one(f'f{i}'))
for sid in ['h1a', 'h1b', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7']:
    out.append(one(sid))
# DiskANN repeat of (h), grouped
hd = ['hd1a', 'hd1b', 'hd2', 'hd3', 'hd4', 'hd5', 'hd6', 'hd7']
assert S['hd7']['response']['cursor']['firstBatch'] == S['h7']['response']['cursor']['firstBatch']
assert S['hd4']['response']['cursor']['firstBatch'] == S['h4']['response']['cursor']['firstBatch']
out.append({'step': 'hd1a-hd7 (extra: part h repeated on collection bin_diskann with vector-diskann v_diskann)',
            'command': 'the h1a-h7 commands with collection bin_diskann; hd2 is ' + cmd_str(S['hd2']),
            'response': ' ; '.join(f"{sid}: " + (resp_str(S[sid]) if sid not in ('hd4', 'hd7') else
                                                    f"firstBatch identical to {sid.replace('hd', 'h')} (ns mt_vector.bin_diskann)")
                                   for sid in hd),
            'reading': ('With a vector-diskann index the Binary behaviour is identical to HNSW: Binary inserts succeed before and after the '
                        'index, a number[] query returns only _ids [1, 3, 2], Binary query vectors fail with code 2 BadValue, find returns '
                        'the Binary documents intact. Open source: not tested (no vector-diskann locally).')})
for sid in ['i0a', 'i0', 'i0b', 'i1', 'i2', 'i3', 'i4']:
    out.append(one(sid))
# final index state, grouped
fl = [s for s in steps if s['step'].startswith('final.listIndexes.')]
state = {}
for s in fl:
    vec = [ix for ix in s['response']['cursor']['firstBatch'] if ix['name'] != '_id_']
    assert all(ix['v'] == 2 and ix['key'] == {'v': 'cosmosSearch'} and set(ix) == {'v', 'key', 'name', 'cosmosSearchOptions'} for ix in vec)
    state[s['command']['listIndexes']] = {ix['name']: ix['cosmosSearchOptions'] for ix in vec}
out.append({'step': 'final.listIndexes (21 collections)',
            'command': "Database('mt_vector').command({\"listIndexes\":<coll>}) for each collection",
            'response': ('every non-_id_ index document is {"v":2,"key":{"v":"cosmosSearch"},"name":<name>,"cosmosSearchOptions":<opts>}; '
                         'per collection {name: opts} (empty = only _id_): ' + cj(state)),
            'reading': ('Every vector index in the run (HNSW, IVF, DiskANN; uncompressed, half, pq) has exactly the top-level keys v, key, '
                        'name, cosmosSearchOptions, with the options echoed as sent; collections whose attempt was rejected hold only _id_.')})
# (g) timing
for v in ('hnsw_empty', 'diskann_empty', 'ivf_empty'):
    p = f'g.{v}'
    for sid in (f'{p}.1', f'{p}.2', f'{p}.3'):
        out.append(one(sid))
    polls = [s for s in steps if s['step'].startswith(f'{p}.poll')]
    first = polls[0]
    same = all(x['response']['cursor']['firstBatch'] == first['response']['cursor']['firstBatch'] for x in polls)
    summ = S[f'{p}.summary']
    out.append({'step': f'{p}.poll00-poll{len(polls) - 1:02d} ({len(polls)} polls)',
                'command': cmd_str(first) + ' every 10 s, starting the moment the insert returned',
                'response': (f"offsets_s {[x['offset_s_after_insert'] for x in polls]}; " + ('every reply ' if same else 'first reply ')
                             + resp_str(first)),
                'reading': summ['reading'] + vs(summ if v == 'hnsw_empty' else first)})
out.append({'step': 'g.noindex.1, g.noindex.2 (extra)', 'command': cmd_str(S['g.noindex.1']) + ' ; ' + cmd_str(S['g.noindex.2']),
            'response': resp_str(S['g.noindex.1']) + ' ; ' + resp_str(S['g.noindex.2']),
            'reading': S['g.noindex.2']['reading'] + vs(S['g.noindex.2'])})
for sid in ['b2', 'b3', 'b4', 'd4.hello', 'd4']:
    out.append(one(sid))
out.append({'step': 'z1-z3 (cleanup)', 'command': ' ; '.join(cmd_str(S[x]) for x in ('z1', 'z2', 'z3')),
            'response': ('z1: ' + str(len(S['z1']['response']['cursor']['firstBatch'])) + ' collections ' +
                         cj(sorted(c['name'] for c in S['z1']['response']['cursor']['firstBatch'])) +
                         ' ; z2: ' + resp_str(S['z2']) + ' ; z3: ' + resp_str(S['z3'])),
            'reading': S['z2']['reading'] + ' ' + S['z3']['reading']})

json.dump(out, open(os.path.join(HERE, 'structured_steps.json'), 'w'), indent=1, ensure_ascii=False)
print(len(out), 'entries; tool-call JSON size', len(json.dumps(out, ensure_ascii=False)), 'bytes')
