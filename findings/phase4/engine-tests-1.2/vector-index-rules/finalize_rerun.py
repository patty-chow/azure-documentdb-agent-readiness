#!/usr/bin/env python
"""Add conclusions, the curated 0.117 comparison and notes to report.json (run after run.py).

Run:  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I finalize.py

Every conclusion is built from the recorded steps. Each one carries checks of the recorded outcomes;
if a check fails (for example a rerun on another build behaves differently), the conclusion is
written as inconclusive with the failed checks instead of reusing stale text.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, 'report_rerun.json')
PREV_REPORT = '/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/vector-index-rules/report.json'
PREV_PARITY = '/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/local-gateway-parity/report.json'

r = json.load(open(P))
S = {s['step']: s for s in r['steps']}
CMP = {c['step']: c for c in r['comparison_with_0_117_auto'] if 'step' in c}


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


def ok(sid):
    return S[sid]['outcome'] == 'ok'


def code(sid):
    return (S[sid].get('error') or {}).get('code')


def cname(sid):
    return (S[sid].get('error') or {}).get('codeName')


def msg(sid):
    return (S[sid].get('error') or {}).get('errmsg') or ''


def tail(sid):
    return msg(sid).rsplit('}:', 1)[-1]


def labels(sid):
    return (S[sid].get('error') or {}).get('errorLabels')


def shard(sid):
    resp = S[sid]['response']
    return (resp.get('raw') or {}).get('defaultShard') or resp


def batch(sid):
    return S[sid]['response']['cursor']['firstBatch']


def ids(sid):
    return [d['_id'] for d in batch(sid)]


def scores(sid):
    return [round(d['score'], 4) for d in batch(sid)]


def params(sid):
    return find_key(S[sid]['response'], 'cosmosSearchCustomParams')


def same(*sids):
    return all(CMP.get(s, {}).get('status') == 'identical' for s in sids)


conclusions = []


def conclude(question, checks, answer, confidence='observed'):
    failed = []
    for desc, fn in checks:
        try:
            if not fn():
                failed.append(desc)
        except Exception as e:
            failed.append(f'{desc} ({type(e).__name__}: {e})')
    if failed:
        conclusions.append({'question': question, 'confidence': 'inconclusive',
                            'answer': 'The recorded results do not match the pattern this conclusion states; review the steps. Failed checks: ' + '; '.join(failed)})
        return
    conclusions.append({'question': question, 'answer': answer(), 'confidence': confidence})


eng = r['engine']
labels_json = json.loads(eng['container_image_and_labels'].split(' ', 2)[2])
conclude('Which engine build was tested?',
         [('hello reports 1.2-0', lambda: eng['hello_internal_documentdb_versions'] == ['1.2-0', '1.2.0']),
          ('image label 1.2.0', lambda: labels_json['org.opencontainers.image.version'] == '1.2.0')],
         lambda: (f"documentdb-local image {eng['container_image_and_labels'].split()[0]} (OCI version {labels_json['org.opencontainers.image.version']}, "
                  f"revision {labels_json['org.opencontainers.image.revision'][:8]}, created {labels_json['org.opencontainers.image.created']}); "
                  f"hello.internal.documentdb_versions {eng['hello_internal_documentdb_versions']}; gateway startup line \"{eng['release_log_line']}\"; "
                  f"extensions documentdb 1.2-0 and vector (pgvector) 0.8.7; {eng['binary_and_postgres_version'].split(' on ')[0].replace('|', ', ')}. "
                  f"buildInfo reports only the MongoDB compatibility version {eng['buildInfo_version']}, so the engine version comes from hello and the container. "
                  "Everything below is evidence about this open-source engine and gateway build, not about the managed service."))

conclude('(a) A second vector index on the same path with a different name: what error?',
         [('a1 created', lambda: ok('a1')), ('a2 is 85', lambda: code('a2') == 85 and cname('a2') == 'IndexOptionsConflict'),
          ('a3 is 85', lambda: code('a3') == 85), ('a4 is 85', lambda: code('a4') == 85),
          ('no labels', lambda: not any(labels(s) for s in ('a2', 'a3', 'a4'))), ('same as 0.117', lambda: same('a1', 'a2', 'a3', 'a4'))],
         lambda: (f"Rejected with code 85 IndexOptionsConflict and no errorLabels in all three variants: identical options under a new name "
                  f"(\"{msg('a2')}\"), and a different kind (vector-ivf) or a different m (32) under a new name (\"{msg('a3').split(' Requested index:')[0]} "
                  "Requested index: {...}, existing index: {...}\"). The engine enforces one vector index per path whatever the kind or options. Identical to 0.117."))

conclude('(b) Repeating the identical createIndexes: a no-op? What response?',
         [('b1 ok', lambda: ok('b1')), ('note', lambda: shard('b1').get('note') == 'all indexes already exist'),
          ('count unchanged', lambda: shard('b1')['numIndexesBefore'] == shard('b1')['numIndexesAfter']),
          ('same as 0.117', lambda: same('b1')), ('b2 is 86', lambda: code('b2') == 86), ('b3 is 86', lambda: code('b3') == 86)],
         lambda: (f"Yes, a no-op with ok 1. The reply is {json.dumps(S['b1']['response'], separators=(',', ':'))}, identical to 0.117. "
                  "New on 1.2.0 (extra steps with no 0.117 counterpart): the no-op holds only for an options document that matches field for field and in "
                  "the same order. The same options sent in a different field order (b2), and the same index with the default m 16 and efConstruction 64 "
                  "left out (b3), both fail with code 86 IndexKeySpecsConflict, the error a changed option gets. An ensure-index helper must resend exactly "
                  "the options it created the index with, or treat code 86 as 'exists with a different spec'."))

conclude('(c) Same name, different options: error code and message?',
         [('c1..c3 are 86', lambda: all(code(s) == 86 and cname(s) == 'IndexKeySpecsConflict' for s in ('c1', 'c2', 'c3'))),
          ('no labels', lambda: not any(labels(s) for s in ('c1', 'c2', 'c3'))), ('same as 0.117', lambda: same('c1', 'c2', 'c3'))],
         lambda: (f"Code 86 IndexKeySpecsConflict with no errorLabels and errmsg \"{msg('c1').split(' Requested index:')[0]} Requested index: {{...}}, "
                  "existing index: {...}\" (both specs printed in full), for a different m (c1), a different similarity (c2) and a different kind (c3). "
                  "Identical to 0.117."))

ok_keys = r['vector_index_option_keys']
kinds = sorted({f"{v['kind']} {v['compression'] or 'uncompressed'}" for v in ok_keys.values()})
conclude('(d) listIndexes: which key carries the vector options, cosmosSearch or cosmosSearchOptions?',
         [('d1 ok', lambda: ok('d1')), ('all have cosmosSearchOptions', lambda: all(v['has_cosmosSearchOptions'] for v in ok_keys.values())),
          ('none has cosmosSearch', lambda: not any(v['has_cosmosSearch'] for v in ok_keys.values())), ('same as 0.117', lambda: same('d1'))],
         lambda: (f"cosmosSearchOptions. The v_hnsw entry is {json.dumps(next(i for i in batch('d1') if i['name'] == 'v_hnsw'), separators=(',', ':'))}. "
                  f"All {len(ok_keys)} vector indexes listed at the end ({', '.join(kinds)}; on populated and empty collections) carry cosmosSearchOptions, "
                  "and none has a cosmosSearch key. Identical to 0.117, so engine 1.2.0 still disagrees with the Learn sample that shows cosmosSearch. "
                  "The managed service is still unchecked, so helpers should keep reading both keys."))

conclude('(e) vector-hnsw on an EMPTY collection, then insert and search',
         [('e1 ok', lambda: ok('e1') and shard('e1')['numIndexesBefore'] == 1 and shard('e1')['numIndexesAfter'] == 2),
          ('e2 n=5', lambda: S['e2']['response']['n'] == 5), ('e3 ids', lambda: ids('e3') == [1, 4, 5]),
          ('e4 uses v_hnsw', lambda: find_key(S['e4']['response'], 'indexName') == 'v_hnsw'), ('same as 0.117', lambda: same('e1', 'e2', 'e3'))],
         lambda: (f"Works. The index is created on the empty collection (numIndexesBefore 1, numIndexesAfter 2), five inserts follow, and a $search sent "
                  f"straight after the inserts returns _ids {ids('e3')} with scores {scores('e3')}. Explain shows FETCH over an IXSCAN of v_hnsw. No build "
                  "delay was visible locally. Identical to 0.117; the explain is new."))

conclude('(f) vector-ivf with numLists 0 and with numLists above the document count; is the swapped-numbers message fixed?',
         [('f1 67', lambda: code('f1') == 67 and cname('f1') == 'CannotCreateIndex'),
          ('f1 text', lambda: tail('f1') == 'numLists must be greater than or equal to 0, but was 1'),
          ('f1b text', lambda: tail('f1b') == 'numLists must be greater than or equal to -1, but was 1'),
          ('f2 ok', lambda: ok('f2')), ('f3 ids', lambda: ids('f3') == [1, 4, 5]), ('f4 ids', lambda: ids('f4') == [1, 4, 5]),
          ('same as 0.117', lambda: same('f0', 'f1', 'f2', 'f3', 'f4'))],
         lambda: (f"Not fixed. numLists 0 fails with code 67 CannotCreateIndex \"Error in specification {{...}}:{tail('f1')}\", identical to 0.117. "
                  f"numLists -1 (extra) returns \"...:{tail('f1b')}\", which shows that the message prints the requested value as the bound and the real "
                  "minimum, 1, as the received value. numLists 100 on 5 documents is accepted, with no check against the document count, and searches "
                  "with the default nProbes and with nProbes 100 both return _ids [1, 4, 5]. Identical to 0.117."))

conclude('(g) Dimension caps for vector-hnsw, vector-ivf and vector-diskann (with compression half and pq)',
         [('g1/g5 2000', lambda: all(code(s) == 67 and tail(s) == 'field cannot have more than 2000 dimensions for vector index' for s in ('g1', 'g5'))),
          ('g3/g7 4000', lambda: all(code(s) == 67 and tail(s) == 'field cannot have more than 4000 dimensions for vector index' for s in ('g3', 'g7'))),
          ('g2/g4/g6/g8/g9 ok', lambda: all(ok(s) for s in ('g2', 'g4', 'g6', 'g8', 'g9'))),
          ('hnsw/ivf same as 0.117', lambda: same('g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'g7', 'g8', 'g9')),
          ('diskann kind error everywhere', lambda: all(code(s) == 67 and tail(s) == 'Invalid search index kind vector-diskann' for s in ('g10', 'g11', 'g12', 'g13', 'g14'))),
          ('diskann same as 0.117 parity', lambda: same('g10')),
          ('no diskann am', lambda: 'diskann' not in eng['index_access_methods']),
          ('pq refused per kind', lambda: tail('g15') == "Compression type 'pq' is not supported for hnsw index" and tail('g15c') == "Compression type 'pq' is not supported for ivf index"),
          ('bogus control', lambda: tail('g15b') == 'Invalid compression type of vector index: bogus')],
         lambda: (f"HNSW and IVF are unchanged from 0.117 and behave alike: 2001 dimensions uncompressed fail with code 67 CannotCreateIndex "
                  f"\"...:{tail('g1')}\" and 2000 are created; with compression half, 4001 fail with \"...:{tail('g3')}\" and 4000 are created; HNSW at "
                  "2001 with half is created. vector-diskann still does not exist in 1.2.0: dimensions 3, 2000, 2001, 16000 and 16001, with and without "
                  f"compression pq, all fail with code 67 \"...:{tail('g10')}\", the message 0.117's parity test got. The kind check runs before any "
                  "dimension check, so the 16,000 PQ cap cannot be tested on this image, and there is no diskann PostgreSQL access method (only hnsw "
                  "and ivfflat). The engine does know pq: documentdb.enableVectorCompressionPQ is on, and pq is refused per kind "
                  f"(\"{tail('g15')}\", \"{tail('g15c')}\"), while an unknown value gets \"{tail('g15b')}\"."))

conclude('(h) BSON Binary vectors (subtype 9 and 0): what does $search return for a number[] query, and what error for a Binary query vector?',
         [('h1 n=2', lambda: S['h1']['response']['n'] == 2), ('h2 ok', lambda: ok('h2')), ('h3 n=1', lambda: S['h3']['response']['n'] == 1),
          ('h4 ids', lambda: ids('h4') == [1, 3, 2]), ('h5/h6 BadValue', lambda: all(code(s) == 2 and cname(s) == 'BadValue' for s in ('h5', 'h6'))),
          ('h7 3 docs', lambda: len(batch('h7')) == 3), ('same as 0.117', lambda: same('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7'))],
         lambda: (f"Unchanged from 0.117. Documents whose v is Binary subtype 9 (float32 vector) or subtype 0 insert without error before the HNSW "
                  "index exists, the index builds over them, and a further subtype 9 document inserts after the index exists (subtype 0 was not "
                  "inserted after the index). A number[] query with k 10 over 6 documents returns only the three number[] "
                  f"documents (_ids {ids('h4')}, scores {scores('h4')}), and the Binary documents are left out without any error. A Binary query vector, "
                  f"subtype 9 or 0, fails with code 2 BadValue \"{msg('h5')}\" and no errorLabels. find returns the three Binary documents intact "
                  "(subtypes 09, 00, 09)."))

conclude('Incidental (extra steps): which efSearch and nProbes does the engine apply when the query names none?',
         [('e4 64', lambda: params('e4') == {'efSearch': 64}), ('e5 40', lambda: params('e5') == {'efSearch': 40}),
          ('e6 100', lambda: params('e6') == {'efSearch': 100}), ('e7 64', lambda: params('e7') == {'efSearch': 64}),
          ('f5 100', lambda: params('f5') == {'nProbes': 100}), ('f6 7', lambda: params('f6') == {'nProbes': 7})],
         lambda: ("Explain's cosmosSearchCustomParams shows efSearch 64 for an efConstruction 64 index at k 3 and at k 100, efSearch 100 for an "
                  "efConstruction 100 index, and nProbes 100 for a numLists 100 index. Explicit efSearch 40 and nProbes 7 pass through unchanged. "
                  "documentdb.enableVectorCalculateDefaultSearchParam is on in this image. DECISIONS cites efSearch 40 and nProbes 1 from Learn as the "
                  "defaults; this engine applies different ones."))
conclude('Incidental (extra steps): what rule produces those defaults?',
         [('pattern holds', lambda: params('e4') == {'efSearch': 64} and params('e6') == {'efSearch': 100} and params('f5') == {'nProbes': 100})],
         lambda: ("Probably efSearch = the index's efConstruction (independent of k) and nProbes = numLists, which makes a default IVF query probe "
                  "every list. This is inferred from the points above plus 0.117's query-behaviour explain (nProbes 2 on a numLists 2 index with no "
                  "nProbes in the query); efSearch was not observed on 0.117, and the managed service may differ."),
         confidence='inferred')

ndiff = [c for c in r['comparison_with_0_117_auto'] if c.get('status') == 'different']
nident = [c['step'] for c in r['comparison_with_0_117_auto'] if c.get('status') == 'identical']
newsteps = [c['step'] for c in r['comparison_with_0_117_auto'] if c.get('status') == 'new_on_1_2_0']
conclude('What differs from the 0.117 results?',
         [('no behavioural differences', lambda: not ndiff)],
         lambda: (f"Nothing in behaviour. All {len(nident)} steps with a 0.117 counterpart ({len(nident) - 1} vector-index-rules steps plus the parity "
                  "test's DiskANN step, compared with g10) match on outcome, code, codeName, errmsg and errorLabels (none anywhere); createIndexes "
                  "replies, listIndexes entries and search results with scores match as well. What changed is the stack: documentdb 0.117-0 to 1.2-0, "
                  "PostgreSQL 17.11 to 17.12, pgvector 0.8.6 to 0.8.7, image revision 28cc0120 to 965b6e7a; buildInfo says 7.0.0 on both. "
                  f"The {len(newsteps)} steps new on 1.2.0 have no 0.117 counterpart. Elapsed times were not compared."))

prev = json.load(open(PREV_REPORT))
pe = prev.get('engine', {})
par_hello = None
try:
    par_hello = find_key(json.load(open(PREV_PARITY)), 'documentdb_versions')
except Exception:
    pass
r['differences_from_0_117'] = [
    {'item': 'documentdb extensions', 'was_0_117': pe.get('pg_extensions'),
     'now_1_2_0': {k: v for k, v in (l.split('|', 1) for l in eng['pg_extensions'].splitlines()) if k.startswith('documentdb')},
     'source_0_117': '0.117 vector-index-rules report, engine.pg_extensions'},
    {'item': 'other PostgreSQL extensions on 1.2.0', 'was_0_117': 'not recorded by the 0.117 run (pgvector 0.8.6 per ENGINE-TESTS.md)',
     'now_1_2_0': {k: v for k, v in (l.split('|', 1) for l in eng['pg_extensions'].splitlines()) if not k.startswith('documentdb')},
     'source_0_117': 'ENGINE-TESTS.md header'},
    {'item': 'hello.internal.documentdb_versions', 'was_0_117': par_hello, 'now_1_2_0': eng['hello_internal_documentdb_versions'],
     'source_0_117': '0.117 local-gateway-parity report'},
    {'item': 'container image', 'was_0_117': f"{pe.get('image')} (OCI {pe.get('image_label_version')}, revision {pe.get('image_revision')}, created {pe.get('image_created')})",
     'now_1_2_0': f"{eng['container_image_and_labels'].split()[0]} (OCI {labels_json['org.opencontainers.image.version']}, revision "
                  f"{labels_json['org.opencontainers.image.revision']}, created {labels_json['org.opencontainers.image.created']})",
     'source_0_117': '0.117 vector-index-rules report, engine'},
    {'item': 'PostgreSQL', 'was_0_117': '17.11', 'now_1_2_0': eng['binary_and_postgres_version'].split('|')[1].split(' on ')[0],
     'source_0_117': 'ENGINE-TESTS.md header'},
    {'item': 'pgvector', 'was_0_117': '0.8.6', 'now_1_2_0': '0.8.7', 'source_0_117': 'ENGINE-TESTS.md header'},
    {'item': 'buildInfo.version', 'was_0_117': prev['buildInfo'].get('version'), 'now_1_2_0': eng['buildInfo_version'],
     'source_0_117': '0.117 vector-index-rules report, buildInfo', 'note': 'unchanged; it is the MongoDB compatibility version, not the engine version'},
    {'item': 'behaviour of the steps with a 0.117 counterpart', 'was_0_117': 'see 0.117 report', 'now_1_2_0':
     f"identical in all {len(nident)} ({', '.join(nident)})" if not ndiff else f"{len(ndiff)} differ: {[c['step'] for c in ndiff]}",
     'source_0_117': PREV_REPORT + ' and, for g10, ' + PREV_PARITY + ' step 06-vector-diskann'},
]
r['conclusions'] = conclusions
r['decisions_topic6_mapping'] = [
    {'steps': 'a1-a4', 'decisions_item': 'One index per path (settled from Learn)', 'result_on_1_2_0': 'enforced by the engine: code 85 IndexOptionsConflict'},
    {'steps': 'b1-b3, c1-c3', 'decisions_item': 'Not an SME item: same-name/different-options error and identical-createIndexes no-op',
     'result_on_1_2_0': 'no-op = ok with note "all indexes already exist"; same name with any difference (including option order or omitted defaults) = code 86 IndexKeySpecsConflict'},
    {'steps': 'd1, final_listIndexes_*', 'decisions_item': 'listIndexes key (Learn shows cosmosSearch, 0.117 returned cosmosSearchOptions)',
     'result_on_1_2_0': 'cosmosSearchOptions only, as on 0.117; managed service unchecked'},
    {'steps': 'e0-e4', 'decisions_item': 'Build order: HNSW on an empty collection', 'result_on_1_2_0': 'works; search right after insert returns correct neighbours'},
    {'steps': 'f0-f4, f1b', 'decisions_item': 'IVF numLists guidance and the swapped-numbers engine message',
     'result_on_1_2_0': 'numLists > document count accepted; numLists < 1 rejected with the bound and value still swapped'},
    {'steps': 'g1-g15c', 'decisions_item': 'Dimension limits 2,000 / 4,000 half / 16,000 PQ on DiskANN (and the product-owner answer on 4,001 half)',
     'result_on_1_2_0': 'HNSW/IVF caps enforced as documented; DiskANN kind absent, so the PQ 16,000 cap is untestable locally'},
    {'steps': 'h1-h7', 'decisions_item': 'BSON binary vectors', 'result_on_1_2_0': 'silently excluded from results; Binary query vector rejected with code 2 BadValue'},
    {'steps': 'e4-e7, f5, f6 (extras)', 'decisions_item': 'Parameter defaults listed as settled (efSearch 40, nProbes 1)',
     'result_on_1_2_0': 'engine applies efSearch = efConstruction and nProbes = numLists when the query names none; check the managed service before quoting Learn defaults'},
]
r['notes'] = [
    'Evidence scope: open-source DocumentDB engine 1.2-0 (binary 1.2.0, commit 965b6e7a) with its gateway in documentdb-local; none of this proves managed-service behaviour.',
    'Steps b2, b3, e4, e5, e6_setup, e6_index, e6, e7, f1b, f5, f6, g14, g15, g15b and g15c go beyond the task spec and say "extra" in their question text. g10 is a DiskANN control with the same spec as the 0.117 parity test and is compared with it; g11-g13 are the DiskANN cases the spec asked for and have no 0.117 counterpart.',
    'For DECISIONS topic 6: one-index-per-path (85), the identical no-op (ok with note) and same-name conflicts (86) are engine behaviour on 1.2.0. The no-op is sensitive to option field order and to omitted defaults, which matters for the kit ensure-index helper.',
    'For DECISIONS topic 6: listIndexes still returns cosmosSearchOptions on 1.2.0. The Learn sample (cosmosSearch) and the managed service still need checking, and helpers should keep reading both keys.',
    'For DECISIONS topic 6: the efSearch and nProbes defaults this engine applies (efConstruction and numLists) differ from the Learn defaults DECISIONS lists as settled (40 and 1). Check them on the managed service before a filing quotes either.',
    'The numLists bound message is still swapped on 1.2.0 (engine issue still worth filing). DiskANN and PQ cannot be exercised on this image.',
    'Container identity commands (docker inspect, docker logs filtered to the Release Version line, psql catalog SELECTs) were read-only. Only database t_vector_rerun was written, and it was dropped at the start and at the end (cleanup_verify shows no collections left).',
]
json.dump(r, open(P, 'w'), indent=2, default=str)
print('finalized', P, len(r['steps']), 'steps;', len(conclusions), 'conclusions;',
      sum(1 for c in conclusions if c['confidence'] == 'inconclusive'), 'inconclusive')
for c in conclusions:
    print('-', c['confidence'], '|', c['question'])
