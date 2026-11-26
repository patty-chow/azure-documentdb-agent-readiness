"""Merge the step files into report.json, add a one-sentence reading and the open-source comparison
to every step, and write structured_steps.json / structured_conclusions.json for the final output."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ['steps_a_pre.json', 'steps_bc_seg1.json', 'steps_d.json', 'steps_extra.json',
         'steps_monitor.json', 'steps_z.json', 'steps_final.json']
OSS_REPORT_117 = '/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/local-gateway-parity/report.json'
OSS_REPORT_120 = '/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests-1.2/local-gateway-parity/report.json'
state = json.load(open(os.path.join(HERE, 'state_c.json')))
T0 = state['t0']

steps = []
for fn in FILES:
    p = os.path.join(HERE, fn)
    if not os.path.exists(p):
        continue
    for i, s in enumerate(json.load(open(p))):
        s['source_file'] = fn
        steps.append(s)
steps.sort(key=lambda s: (s.get('at_utc') or '', s.get('step')))
for i, s in enumerate(steps, 1):
    s['seq'] = i


def err(s):
    e = s.get('error') or {}
    return e.get('code'), e.get('codeName'), e.get('errmsg')


def first_batch(s):
    if s.get('outcome') != 'ok' or not isinstance(s.get('response'), dict):
        return None
    return (s['response'].get('cursor') or {}).get('firstBatch')


def short_err(s):
    c, n, m = err(s)
    return f'code {c} {n} "{m}"'


# nearest monitor state at or before a time
mon_states = []
for s in steps:
    if s['step'].endswith('.show') and s.get('response_fields') and s.get('since_patch_s') is not None:
        mon_states.append((s.get('at_epoch') or 0, s['response_fields'].get('provisioningState') + ' (show)', s.get('since_patch_s')))
    if re.match(r'(b4|b5)\.mon\.\d\d\.get$', s['step']) and isinstance(s.get('response'), dict):
        mon_states.append((s.get('at_epoch') or 0, str(s['response'].get('state')) + ' (Learn GET)', s.get('since_patch_s')))
    if s['step'] == 'b3.patch' and isinstance(s.get('response'), dict):
        mon_states.append((s.get('ended_epoch') or T0, (s['response'].get('properties') or {}).get('provisioningState') + ' (PATCH response)', 0.0))
mon_states.sort()


def state_before(epoch):
    best = None
    for e, ps, sp in mon_states:
        if e <= epoch:
            best = (ps, sp)
    return best


def state_after(epoch):
    for e, ps, sp in mon_states:
        if e > epoch:
            return (ps, sp)
    return None


OSS_115 = ("open-source gateway (0.117 and 1.2.0) returns code 115 CommandNotSupported "
           "\"Command 'createSearchIndexes' not supported.\" for every createSearchIndexes")

FIXED = {
    'a0.hello': ('The plain host answers as the managed service before enabling: maxWireVersion 25, internal.documentdb_versions ["2.2-1","2.3.0","12.1-1"], kind azuredocumentdb.',
                 'n/a', 'Identity, not behaviour; the open-source gateway reports wire version 21 and documentdb_versions 1.2-0/1.2.0 on 1.2.0.'),
    'a0.buildInfo': ('buildInfo reports version 8.0.0 before enabling.', 'n/a', 'Identity only; the open-source gateway reports 7.0.0.'),
    'a0.az.get_state': ('Before the PATCH the Learn check GET reported state "Succeeded" and features null: no preview feature was enabled.', 'n/a', 'Cluster configuration; no open-source counterpart.'),
    'a0.az.show': ('Before the PATCH, az documentdb mongocluster show reported provisioningState Succeeded and clusterStatus Ready and had no previewFeatures key at all.', 'n/a', 'Cluster configuration; no open-source counterpart.'),
    'a1.db_absent': ('mt_fts did not exist before the test, so every later step ran in a fresh database.', 'n/a', 'Setup.'),
    'a2.create': ('Collection mt_fts.products was created.', 'n/a', 'Setup.'),
    'a3.insert': ('The three Learn structured-search sample documents (with a 3-dimensional embedding field added) were inserted.', 'n/a', 'Setup.'),
    'a4.createSearchIndexes.pre': ('Before enabling, createSearchIndexes fails with code 115 CommandNotSupported "Search index creation is not supported yet" and no errorLabels, the same reply runs/07 recorded.',
                                   'different', 'Same code 115 and codeName CommandNotSupported, different errmsg: the open-source gateway (0.117 and 1.2.0, step 02b) says "Command \'createSearchIndexes\' not supported.".'),
    'a5x.listSearchIndexes.pre': ('Before enabling, $listSearchIndexes fails with code 115 CommandNotSupported "$listSearchIndexes stage is not enabled".',
                                  'same', 'Identical code, codeName and errmsg to the open-source step 04 (0.117) / 04a (1.2.0).'),
    'a6x.search_text.pre': ('Before enabling, $search with a text operator fails with code 40324 UnrecognizedCommand "Unrecognized $search option: text".',
                            'same', 'Identical to the open-source step 03 (0.117) / 03a (1.2.0).'),
    'a7x.rankFusion.pre': ('Before enabling, $rankFusion fails with code 40324 UnrecognizedCommand "Pipeline stage name not recognized: $rankFusion".',
                           'same', 'Identical to the open-source step 07 on 0.117 and 1.2.0.'),
    'a8x.searchMeta.pre': ('Before enabling, $searchMeta fails with code 115 CommandNotSupported "Stage $searchMeta is not supported yet in native pipeline".',
                           'not_tested_locally', 'The open-source parity tests did not call $searchMeta.'),
    'a9x.createSearchIndexes.dynamic.pre': ('Before enabling, a dynamic-mapping definition gets the same 115 "Search index creation is not supported yet", so the feature gate runs before definition validation.',
                                            'different', 'Open-source step 02 (dynamic true) returns 115 with errmsg "Command \'createSearchIndexes\' not supported."; same code, different message.'),
    'a10x.listIndexes.pre': ('Before any index was created, listIndexes shows only _id_.', 'n/a', 'Baseline.'),
    'c.persistent.hello.start': ('The persistent client was connected before the PATCH (gateway connectionId 174955255).', 'n/a', 'Connection bookkeeping.'),
    'b1.get_state': ('Learn command 1 (review): state "Succeeded", features null immediately before the PATCH.', 'n/a', 'Cluster configuration.'),
    'b2.get_body': ('Learn command 2 built BODY {"properties":{"previewFeatures":["FullTextSearch"]}}: there were no other preview features to preserve.', 'n/a', 'Cluster configuration.'),
    'b3.patch': ('Learn command 3 (PATCH) returned rc 0 after 0.88 s at 2026-11-25T21:50:26.818Z with the full resource showing provisioningState "Updating", clusterStatus "Updating" and previewFeatures ["FullTextSearch"].', 'n/a', 'Cluster configuration.'),
    'd1.00.listSearchIndexes': ('Sent as soon as createSearchIndexes returned (that call took 1.08 s; this one went out 1.1 s after it was sent), $listSearchIndexes already reported the index with status "READY" and queryable true (id "225", latestDefinition echoing the definition).',
                                'different', 'The open-source gateway rejects $listSearchIndexes with 115 "$listSearchIndexes stage is not enabled".'),
    'd0x.search_right_after_create': ('A $search text query sent 1.2 s after createSearchIndexes was sent (0.1 s after it returned) already returned all three titles with BM25 scores, so no wait was needed on a 3-document collection.',
                                      'different', 'The open-source gateway rejects $search text with 40324.'),
    'c.persistent.hello.end.seg1': ('The persistent client still used gateway connectionId 174955255 after activation, so the connection opened before the PATCH survived and saw the feature without reconnecting.', 'n/a', 'Connection bookkeeping.'),
    'd1.r.listSearchIndexes': ('At the start of step d the index was still READY and queryable.', 'different', 'The open-source gateway rejects $listSearchIndexes with 115.'),
    'd2.search_text': ('$search text "bracket" on title returns the three documents with identical BM25 scores 0.1335 (one matching term each).',
                       'different', 'The open-source gateway rejects $search text with 40324 "Unrecognized $search option: text" (step 03/03a).'),
    'd2x.search_text_any': ('$search text "industrial controller" on description ranks document 2 (both terms, 1.043) above 3 (0.143) and 1 (0.134): default matching is any term, with length normalisation.',
                            'not_tested_locally', 'Text search cannot run on the open-source gateway.'),
    'd2y.search_text_all': ('With matchCriteria "all" across title and description only document 2 matches.', 'not_tested_locally', 'Text search cannot run on the open-source gateway.'),
    'd3.compound': ('The Learn compound query (must, should, filter, mustNot) runs and returns only "Bracket controller" (score 4.97), exactly the result Learn documents.',
                    'not_tested_locally', 'The open-source gateway was never asked for compound; its $search accepts only cosmosSearch/knnBeta, so it would be rejected.'),
    'd3x.compound_mustNot_effective': ('A mustNot that excludes region "west" removes documents 1 and 3 and returns only document 2, so mustNot is enforced.', 'not_tested_locally', 'Text search cannot run on the open-source gateway.'),
    'd4.compound_minimumShouldMatch': ('compound.minimumShouldMatch is rejected with code 115 CommandNotSupported "\'compound.minimumShouldMatch\' is not supported yet." as Learn lists.',
                                       'not_tested_locally', 'Not tested on the open-source gateway.'),
    'd5.searchMeta': ('$searchMeta is rejected after enabling with the same 115 "Stage $searchMeta is not supported yet in native pipeline" as before, as Learn lists.', 'not_tested_locally', 'Not tested on the open-source gateway.'),
    'd5x.searchMeta_count': ('$searchMeta with count is rejected the same way (115).', 'not_tested_locally', 'Not tested on the open-source gateway.'),
    'd6a.rankFusion': ('After enabling, $rankFusion is still unrecognised: 40324 UnrecognizedCommand "Pipeline stage name not recognized: $rankFusion".',
                       'same', 'Identical to the open-source step 07 (0.117 and 1.2.0).'),
    'd7a.create_vector_ivf': ('A vector-ivf index (3 dimensions, COS, numLists 1) is created next to the search index; numIndexesBefore 2 shows the search index is counted as an index.',
                              'same', 'IVF creation succeeds on the open-source gateway too (step 06c) with the same raw.defaultShard reply shape on 1.2.0; the count including a search index cannot occur there.'),
    'd7b.listIndexes': ('listIndexes lists _id_ and desc_ivf (options under cosmosSearchOptions) but not the search index, as Learn says.',
                        'same', 'cosmosSearchOptions with no cosmosSearch key, as on the open-source gateway; the search-index part has no open-source counterpart.'),
    'd7c.keyword_query': ('The hybrid page keyword query for "industrial" returns only document 2 (searchScore 0.918).', 'different', 'Rejected with 40324 on the open-source gateway.'),
    'd7d.vector_query': ('The hybrid page vector query on the IVF index, without returnStoredSource, returns documents 1, 3, 2 with cosine scores 0.994, 0.685, 0.110.',
                         'same', 'cosmosSearch over IVF works on the open-source gateway too (step 06d used returnStoredSource true).'),
    'd7e.client_side_rrf': ('The page rrf() helper (k 60) over d7c and d7d gives 2 (0.032266), 1 (0.016393), 3 (0.016129).', 'n/a', 'Computed locally from d7c and d7d.'),
    'd7f.hybrid_unionWith_rrf': ('The Learn $unionWith RRF pipeline runs in one round trip ($search allowed inside $unionWith) and returns 2, 1, 3 with scores identical to the client-side RRF, with titles carried through from the vector branch.',
                                 'not_tested_locally', 'Not run on the open-source gateway; its keyword branch ($search text) is rejected there with 40324, so the pipeline cannot run.'),
    'd6b.rankFusion_hybrid': ('$rankFusion over the vector and keyword pipelines is rejected with 40324 "Pipeline stage name not recognized: $rankFusion".',
                              'not_tested_locally', 'The open-source test used a $sort-only form (same 40324); this vector/keyword form was not run there.'),
    'd8x.listSearchIndexes_all': ('$listSearchIndexes {} lists exactly one search index, idx_products_filters, READY.', 'different', 'Rejected with 115 on the open-source gateway.'),
    'x1.createSearchIndexes.dynamic': ('After enabling, mappings.dynamic true fails with code 67 CannotCreateIndex "Error in specification {...}:mappings.dynamic is not supported in search indexes yet", wrapped and without the trailing period Learn shows.',
                                       'different', 'The open-source gateway returns 115 "Command \'createSearchIndexes\' not supported." for the same definition (step 02/02a).'),
    'x2.updateSearchIndex': ('updateSearchIndex is not a command on the service: 59 CommandNotFound "Command \'updateSearchIndex\' not found.".', 'not_tested_locally', 'Not tested on the open-source gateway.'),
    'x3.dropIndexes_search_index': ('dropIndexes with the search index name drops it (ok 1, nIndexesWas 3, so the search index was counted).', 'not_tested_locally', 'Not tested on the open-source gateway.'),
    'x3b.listSearchIndexes': ('After dropIndexes, $listSearchIndexes returns an empty list.', 'not_tested_locally', 'Not tested on the open-source gateway.'),
    'x4.createSearchIndexes.again': ('Re-creating the index with the same name succeeds immediately once the feature is active.', 'different', 'The open-source gateway returns 115.'),
    'x4b.listSearchIndexes': ('The re-created index (new id "227") is READY and queryable on the first check.', 'different', 'The open-source gateway returns 115.'),
    'x4c.search_text': ('The re-created index answers $search with the same scores as before.', 'different', 'The open-source gateway returns 40324.'),
    'x5.dropSearchIndex': ('dropSearchIndex, the command driver drop_search_index helpers send, is not a command on the service: 59 CommandNotFound "Command \'dropSearchIndex\' not found.".', 'not_tested_locally', 'Not tested on the open-source gateway.'),
    'x5b.listSearchIndexes': ('After the failed dropSearchIndex the index is still listed, READY.', 'not_tested_locally', 'Not tested on the open-source gateway.'),
    'x6.search_text_no_index': ('Because dropSearchIndex failed the index still existed; this $search without $project returns whole documents carrying an internal __cosmos_meta__: {score} field.',
                                'not_tested_locally', 'Text search cannot run on the open-source gateway.'),
    'z0.hello_after': None,  # filled from data
    'z0.buildInfo_after': None,
    'z1.dropDatabase': ('mt_fts was dropped.', 'n/a', 'Cleanup.'),
    'z2.db_absent': ('mt_fts no longer exists.', 'n/a', 'Cleanup.'),
    'z3.final_state': None,
}

for s in steps:
    st = s['step']
    if st in FIXED and FIXED[st] is not None:
        s['reading'], s['vs_open_source'], s['vs_open_source_detail'] = FIXED[st]
        continue
    m = re.match(r'c\.(\d\d)\.(persistent|fresh)$', st)
    if m:
        k, which = int(m.group(1)), m.group(2)
        ps = state_before(s.get('at_epoch') or 0)
        nx = state_after(s.get('at_epoch') or 0)
        pstxt = (f' (provisioningState: {ps[0]} sent at +{ps[1]} s before it' + (f'; {nx[0]} sent at +{nx[1]} s after it)' if nx else ')')) if ps else ''
        if s['outcome'] == 'ok':
            s['reading'] = (f'Attempt {k} at +{s["since_patch_s"]} s on the {which} client succeeded '
                            f'(ok 1, numIndexesBefore 1, numIndexesAfter 2){pstxt}: activation finished between +180.1 s and +210.0 s.')
            s['vs_open_source'] = 'different'
            s['vs_open_source_detail'] = OSS_115 + '; the managed service accepts it once activation finishes.'
        else:
            s['reading'] = f'Attempt {k} at +{s["since_patch_s"]} s on the {which} client failed with {short_err(s)}, no errorLabels{pstxt}.'
            c = err(s)[0]
            s['vs_open_source'] = 'different'
            s['vs_open_source_detail'] = (OSS_115 + '; here the code is the same (115) but the errmsg differs.') if c == 115 else \
                (OSS_115 + '; here the code is 67 CannotCreateIndex with the activation-pending message.')
        s['state_around_attempt'] = {'before': {'provisioningState': ps[0], 'sampled_since_patch_s': ps[1]} if ps else None,
                                     'after': {'provisioningState': nx[0], 'sampled_since_patch_s': nx[1]} if nx else None}
        continue
    m = re.match(r'c\.(\d\d)\.listx$', st)
    if m:
        k = int(m.group(1))
        if s['outcome'] == 'ok':
            s['reading'] = f'Extra probe in slot {k} (+{s["since_patch_s"]} s): $listSearchIndexes is enabled and returns an empty list.'
            s['vs_open_source'] = 'different'
            s['vs_open_source_detail'] = 'The open-source gateway always returns 115 "$listSearchIndexes stage is not enabled".'
        else:
            s['reading'] = f'Extra probe in slot {k} (+{s["since_patch_s"]} s): $listSearchIndexes still fails with {short_err(s)}.'
            s['vs_open_source'] = 'same'
            s['vs_open_source_detail'] = 'Identical to the open-source 115 "$listSearchIndexes stage is not enabled".'
        continue
    m = re.match(r'(b4|b5)\.mon\.(\d\d)\.get$', st)
    if m:
        r = s.get('response') or {}
        s['reading'] = (f'Learn check GET at +{s.get("since_patch_s")} s: state "{r.get("state")}", features {json.dumps(r.get("features"))}.')
        s['vs_open_source'] = 'n/a'
        s['vs_open_source_detail'] = 'Cluster configuration; no open-source counterpart.'
        continue
    m = re.match(r'(b4|b5)\.mon\.(\d\d)\.show$', st)
    if m:
        f = s.get('response_fields') or {}
        s['reading'] = (f'az documentdb mongocluster show at +{s.get("since_patch_s")} s: provisioningState {f.get("provisioningState")}, '
                        f'clusterStatus {f.get("clusterStatus")}, previewFeatures {json.dumps(f.get("previewFeatures"))}.')
        s['vs_open_source'] = 'n/a'
        s['vs_open_source_detail'] = 'Cluster configuration; no open-source counterpart.'
        continue
    if st == 'z0.hello_after':
        r = s.get('response') or {}
        dv = (r.get('internal') or {}).get('documentdb_versions')
        s['reading'] = f'After enabling, hello still reports maxWireVersion {r.get("maxWireVersion")} and documentdb_versions {json.dumps(dv)}: enabling the preview did not change the reported engine versions.'
        s['vs_open_source'] = 'n/a'
        s['vs_open_source_detail'] = 'Identity only.'
        continue
    if st == 'z0.buildInfo_after':
        r = s.get('response') or {}
        s['reading'] = f'After enabling, buildInfo still reports version {r.get("version")}.'
        s['vs_open_source'] = 'n/a'
        s['vs_open_source_detail'] = 'Identity only.'
        continue
    if st == 'z3.final_state':
        r = s.get('response') or {}
        s['reading'] = f'Final Learn check GET at +{s.get("since_patch_s")} s: state "{r.get("state")}", features {json.dumps(r.get("features"))}; the feature is left enabled.'
        s['vs_open_source'] = 'n/a'
        s['vs_open_source_detail'] = 'Cluster configuration.'
        continue
    s.setdefault('reading', '(no reading)')
    s.setdefault('vs_open_source', 'n/a')

missing = [s['step'] for s in steps if s.get('reading') in (None, '(no reading)')]

# activation timeline (one row per 30-s slot)
slots = {}
for s in steps:
    m = re.match(r'c\.(\d\d)\.(persistent|fresh|listx)$', s['step'])
    if m:
        k = int(m.group(1))
        row = slots.setdefault(k, {'attempt': k, 'scheduled_since_patch_s': k * 30})
        if s['outcome'] == 'ok':
            v = 'ok' if m.group(2) != 'listx' else f'ok, {len(first_batch(s) or [])} indexes'
        else:
            c, n, msg = err(s)
            v = f'{c} {n}: {msg}'
        row[m.group(2)] = v
        row[m.group(2) + '_at_utc'] = s['at_utc']
        row[m.group(2) + '_since_patch_s'] = s.get('since_patch_s')
        if m.group(2) == 'persistent':
            ps = state_before(s.get('at_epoch') or 0)
            nx = state_after(s.get('at_epoch') or 0)
            row['provisioningState_before'] = f'{ps[0]} sent at +{ps[1]} s' if ps else None
            row['provisioningState_after'] = f'{nx[0]} sent at +{nx[1]} s' if nx else None
timeline = [slots[k] for k in sorted(slots)]

monitor_series = []
for s in steps:
    if re.match(r'(b4|b5)\.mon\.\d\d\.show$', s['step']):
        g = next((x for x in steps if x['step'] == s['step'][:-5] + '.get'), None)
        monitor_series.append({'sample': s['step'][:-5], 'at_utc': s['at_utc'], 'since_patch_s': s.get('since_patch_s'),
                               'learn_get': g.get('response') if g else None, 'show': s.get('response_fields')})

report = {
    'test': 'm-fts',
    'database': 'mt_fts',
    'goal': ('Full-text search activation on the managed service: the error before enabling, enabling the FullTextSearch '
             'preview exactly as the Learn overview shows for the Azure CLI, the error codes and timing during activation, '
             'and, after activation, $listSearchIndexes READY/queryable, $search text, compound (must/should/filter/mustNot), '
             'compound.minimumShouldMatch, $searchMeta, $rankFusion and the hybrid $unionWith RRF pipeline with a vector-ivf index.'),
    'target': ('Azure DocumentDB Microsoft.DocumentDB/mongoClusters "ddb-samples-shared", resource group documentdb-samples-rg, eastus, '
               'tier M30, one shard, server version 8.0, Premium SSD v2, high availability disabled, public access. Data plane through '
               'MANAGED_URI (plain host, mongodb+srv, TLS, SCRAM-SHA-256, retrywrites=false). Control plane through Azure CLI 2.89.1 '
               '(az rest, api-version 2024-07-01) and the documentdb extension 1.0.0 (az documentdb mongocluster show).'),
    'engine': {'hello.maxWireVersion': 25, 'hello.internal': {'documentdb_versions': ['2.2-1', '2.3.0', '12.1-1'], 'kind': 'azuredocumentdb'},
               'hello.msg': 'isdbgrid', 'buildInfo.version': '8.0.0',
               'after_enabling': 'see step z0.hello_after (unchanged)'},
    'driver': ('PyMongo 4.20.1 on Python 3.13 (/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python); '
               "PyMongo's CosmosDB UserWarning was filtered. All database calls are raw Database.command() documents."),
    'observed_on': '2026-11-25 (UTC timestamps on every step; PATCH returned at 2026-11-25T21:50:26.818Z = +0 s)',
    'evidence_scope': ('One activation on one M30 single-shard cluster with high availability disabled, sampled every 30 s, and a '
                       '3-document collection. Timings are single observations bounded by the 30-s cadence, not service guarantees; '
                       'index build time on large collections was not measured.'),
    'learn_pages_read_2026_11_25': {
        'full-text-search-overview': 'ms.date 2026-11-04, updated_at 2026-11-17, git 16c9484b (Azure CLI enable block, 10-minute wait, current limitations)',
        'full-text-search-hybrid': 'ms.date 2026-05-07, updated_at 2026-11-17 (Server-side RRF with $unionWith pipeline)',
        'full-text-search-structured': 'ms.date 2026-10-23, updated_at 2026-11-17 (sample data, index definition, compound query, minimumShouldMatch note)',
        'full-text-search-keyword': 'ms.date 2026-10-23, updated_at 2026-11-17 ($listSearchIndexes READY/queryable, $search text form)',
        'limitations': 'ms.date 2026-11-04, updated_at 2026-11-17 (Full-text search limitations (preview))',
    },
    'open_source_reference': {
        'report_0_117': OSS_REPORT_117, 'report_1_2_0': OSS_REPORT_120,
        'summary': ('findings/phase4/ENGINE-TESTS.md "Local gateway parity": createSearchIndexes 115 "Command \'createSearchIndexes\' not supported.", '
                    '$search text 40324 "Unrecognized $search option: text", $listSearchIndexes 115 "$listSearchIndexes stage is not enabled", '
                    '$rankFusion 40324 "Pipeline stage name not recognized: $rankFusion"; reproduced unchanged on 1.2.0. '
                    'compound, minimumShouldMatch, $searchMeta, search-index lifecycle commands and the hybrid pipeline were not tested locally.'),
    },
    'scripts': {f: os.path.join(HERE, f) for f in ['common.py', 'run_a_pre.py', 'run_bc.py', 'run_monitor.py', 'run_d.py',
                                                    'run_extra.py', 'run_z.py', 'run_final.py', 'conclusions.py', 'finalize.py']},
    'run_order': ['run_a_pre.py', 'run_bc.py (one segment; succeeded at +210 s, so --continue was not needed)',
                  'run_monitor.py (background, +361 s to about +12 min)', 'run_d.py', 'run_extra.py', 'run_z.py', 'run_final.py (after the monitor ended)', 'finalize.py'],
    'learn_cli_fidelity': ('Steps b1, b2, b3 and every monitor GET ran the exact command text from the Learn overview through bash -c with '
                           'URL="https://management.azure.com${RESOURCE_ID}?api-version=2024-07-01" and RESOURCE_ID built from the current '
                           'subscription, the resource group and the cluster name. BODY was captured from b2 with trailing newlines stripped, as '
                           'bash $(...) does, and passed to the PATCH unchanged. "set -euo pipefail" was honoured by stopping on any non-zero rc; '
                           '"az login" was not re-run because the CLI was already signed in. Learn\'s fourth command (check the updated '
                           'configuration) is monitor sample b4.mon.00 at +1.2 s.'),
    'masking': ('Every recorded string passed through a scrubber that removes the password, both URIs and the subscription id and masks '
                'e-mail addresses and GUIDs. Masked in this report: the subscription id in resource ids and URLs (<subscription-id>) and the '
                'createdBy/lastModifiedBy e-mail addresses in systemData (<email-masked>). The connectionString in ARM output already '
                'carries <user>:<password> placeholders.'),
    'monitor_gap': ('Cluster samples ran every 30 s from +1.2 s to +210.6 s (in run_bc.py) and from +360.9 s to about +12 min '
                    '(run_monitor.py). There are no samples between +210.6 s and +360.9 s; both sides read Succeeded/Ready with the same '
                    'systemData.lastModifiedAt.'),
    'config_changes': ['Enabled the FullTextSearch preview feature on Microsoft.DocumentDB/mongoClusters "ddb-samples-shared" (resource group '
                       'documentdb-samples-rg) with az rest --method patch, api-version 2024-07-01, body {"properties":{"previewFeatures":'
                       '["FullTextSearch"]}}, sent 2026-11-25T21:50:25.938Z and returned 2026-11-25T21:50:26.818Z: properties.previewFeatures '
                       'changed from null to ["FullTextSearch"] (no other preview features existed to preserve). Left enabled.'],
    'activation': {
        'patch_started_utc': state['patch_started_utc'], 'patch_returned_utc': state['t0_utc'],
        'first_success_utc': state['success_utc'], 'first_success_since_patch_s': state['success_since_patch_s'],
        'first_success_step': state['success_step'],
        'index_ready_first_seen_utc': next(s['at_utc'] for s in steps if s['step'] == 'd1.00.listSearchIndexes'),
        'timeline': timeline,
        'cluster_samples': monitor_series,
    },
    'readings_missing': missing,
    'conclusions': None,
    'notes': None,
    'steps': steps,
}
import conclusions as _c
_last = max((x for x in monitor_series if x.get('since_patch_s') is not None), key=lambda x: x['since_patch_s'], default=None)
_fin = next((x for x in steps if x['step'] == 'z3.final_state'), None)
_fin_txt = (f'Learn GET at +{_fin.get("since_patch_s")} s returned {json.dumps(_fin.get("response"))}' if _fin else 'not yet taken')
report['conclusions'] = _c.build(_last['since_patch_s'] if _last else None, _fin_txt)
report['notes'] = _c.NOTES
json.dump(report['conclusions'], open(os.path.join(HERE, 'structured_conclusions.json'), 'w'), indent=2)
json.dump(report, open(os.path.join(HERE, 'report.json'), 'w'), indent=2)


def compact(v, limit):
    t = json.dumps(v, separators=(',', ':'))
    return t if len(t) <= limit else t[:limit] + f'... [truncated; full raw reply in report.json, {len(t)} chars]'


def cmd_text(s):
    c = s.get('command')
    dc = s.get('driver_call', '')
    if isinstance(c, str):
        vars_ = s.get('command_variables') or {}
        return f'{c}   [via {dc}; variables {json.dumps(vars_, separators=(",", ":"))}]'
    if c is None:
        return dc
    return f'{dc}  with command = {json.dumps(c, separators=(",", ":"), default=str)}'


structured = []
for s in steps:
    if s['outcome'] == 'ok':
        body = s.get('response') if s.get('response') is not None else s.get('response_fields')
        if s['step'].endswith('.show') and s.get('response') is None:
            body = {'extracted_fields': s.get('response_fields'), 'full_output_recorded': 'only when fields change; unchanged here'}
        resp = compact(body, 1800 if s['step'] in ('b3.patch', 'a0.az.show') else 1200)
        if s.get('stderr'):
            resp += f' | stderr: {s["stderr"][:200]}'
    else:
        e = s.get('error') or {}
        resp = compact({k: e.get(k) for k in ('code', 'codeName', 'errmsg', 'errorLabels')} | {'raw': e.get('raw')}, 1200) \
            if e else compact({'returncode': s.get('returncode'), 'stdout': s.get('response'), 'stderr': s.get('stderr')}, 1200)
    structured.append({'step': f"{s['step']} @ {s['at_utc']}" + (f" (+{s['since_patch_s']} s after PATCH)" if s.get('since_patch_s') is not None else ''),
                       'command': cmd_text(s), 'response': resp,
                       'reading': s['reading'] + (f" [vs open source: {s['vs_open_source']}; {s.get('vs_open_source_detail','')}]"
                                                  if s.get('vs_open_source') not in (None, 'n/a') else '')})
json.dump(structured, open(os.path.join(HERE, 'structured_steps.json'), 'w'), indent=2)
print('steps', len(steps), 'structured', len(structured), 'missing readings', missing)
print(json.dumps(timeline, indent=1))
