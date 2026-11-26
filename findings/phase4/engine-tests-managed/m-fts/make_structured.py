"""Compact step list for the workflow's structured output (full raw replies stay in report.json)."""
import copy
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(HERE, 'report.json')))
S = {s['step']: s for s in r['steps']}
J = lambda v: json.dumps(v, separators=(',', ':'), default=str)
DEF_ABBR = '<latestDefinition identical to the submitted idx_products_filters mappings>'


def abbr_defs(v):
    v = copy.deepcopy(v)
    fb = ((v or {}).get('cursor') or {}).get('firstBatch') if isinstance(v, dict) else None
    if fb:
        for d in fb:
            if isinstance(d, dict) and 'latestDefinition' in d:
                d['latestDefinition'] = DEF_ABBR
    return v


def cmd(s):
    c = s.get('command')
    if isinstance(c, str):
        v = s.get('command_variables') or {}
        if 'URL' not in v:
            return c + '   [bash -c; ' + ', '.join(f'{k}={x}' for k, x in v.items()) + ']'
        return c + '   [bash -c; $URL = ' + v['URL'] + (
            '; $BODY = ' + J(json.loads(v['BODY'])) if 'BODY' in v else '') + ']'
    return s['driver_call'] + ' with command ' + J(c)


def resp(s, abbreviate=True, limit=1500):
    if s['outcome'] == 'ok':
        v = s.get('response')
        if abbreviate:
            v = abbr_defs(v)
        t = J(v)
    else:
        e = s.get('error') or {}
        t = J({'code': e.get('code'), 'codeName': e.get('codeName'), 'errmsg': e.get('errmsg'), 'errorLabels': e.get('errorLabels'), 'raw': e.get('raw')})
    return t if len(t) <= limit else t[:limit] + f'...[truncated here; full raw reply in report.json step {s["step"]}]'


def hello_sel(s):
    v = s['response']
    return J({k: v.get(k) for k in ('msg', 'maxWireVersion', 'internal', 'saslSupportedMechs', 'maxWriteBatchSize', 'connectionId', 'ok')}) + \
        '  [selected fields; full reply in report.json]'


def ro(s):
    return s['reading'] + (f" Open source: {s['vs_open_source']} ({s.get('vs_open_source_detail', '')})" if s.get('vs_open_source') not in (None, 'n/a') else '')


out = []


def add(step_label, command, response, reading):
    out.append({'step': step_label, 'command': command, 'response': response, 'reading': reading})


def one(name, response=None, label=None):
    s = S[name]
    sp = f" (+{s['since_patch_s']} s after the PATCH)" if s.get('since_patch_s') is not None else ''
    add(label or f"{name} @ {s['at_utc']}{sp}", cmd(s), response if response is not None else resp(s), ro(s))


one('a0.hello', hello_sel(S['a0.hello']))
for n in ['a0.buildInfo', 'a0.az.get_state']:
    one(n)
s = S['a0.az.show']
one('a0.az.show', J(s['response_fields']) + '  [fields extracted from the full show output, which is in report.json; no previewFeatures key was present]')
for n in ['a1.db_absent', 'a2.create', 'a3.insert', 'a4.createSearchIndexes.pre', 'a5x.listSearchIndexes.pre', 'a6x.search_text.pre',
          'a7x.rankFusion.pre', 'a8x.searchMeta.pre', 'a9x.createSearchIndexes.dynamic.pre', 'a10x.listIndexes.pre']:
    one(n)
one('c.persistent.hello.start', J({'connectionId': S['c.persistent.hello.start']['response']['connectionId'], 'ok': 1.0}) + '  [selected fields]')
for n in ['b1.get_state', 'b2.get_body']:
    one(n)
one('b3.patch', resp(S['b3.patch'], limit=2500))


def mon_pair(n, prefix):
    g, sh = S[f'{prefix}.mon.{n:02d}.get'], S[f'{prefix}.mon.{n:02d}.show']
    return g, sh


def mon_entry(ns, prefix):
    rows = []
    for n in ns:
        g, sh = mon_pair(n, prefix)
        f = sh['response_fields']
        rows.append(f"#{n:02d} GET {g['at_utc'][11:19]}Z +{g['since_patch_s']}s {J(g['response'])}; show +{sh['since_patch_s']}s "
                    f"provisioningState={f['provisioningState']} clusterStatus={f['clusterStatus']} previewFeatures={J(f['previewFeatures'])}")
    g0 = mon_pair(ns[0], prefix)[0]
    label = f"{prefix}.mon.{ns[0]:02d}" + (f"-{ns[-1]:02d}" if len(ns) > 1 else '') + f" @ {g0['at_utc']} (+{g0['since_patch_s']} s)"
    command = ('Learn check GET: ' + S[f'{prefix}.mon.{ns[0]:02d}.get']['command'] + '  AND  ' + S[f'{prefix}.mon.{ns[0]:02d}.show']['command'] +
               '  [bash -c; $URL as in b1; MANAGED_RG=documentdb-samples-rg, MANAGED_CLUSTER=ddb-samples-shared; one sample every 30 s on the PATCH-anchored schedule]')
    states = sorted({(mon_pair(n, prefix)[0]['response'] or {}).get('state') for n in ns})
    reading = (f"{len(ns)} sample(s): Learn GET state {states}, previewFeatures [\"FullTextSearch\"] in every sample; show provisioningState/clusterStatus as listed. "
               "No open-source counterpart (cluster configuration).")
    add(label, command, ' | '.join(rows), reading)


mon_entry([0], 'b4')
mon_entry([1, 2, 3, 4, 5], 'b4')
mon_entry([6], 'b4')
mon_entry([7], 'b4')

for k in range(0, 8):
    parts, readings = [], []
    for which in ('persistent', 'fresh', 'listx'):
        s = S.get(f'c.{k:02d}.{which}')
        if not s:
            continue
        if s['outcome'] == 'ok':
            body = J(s['response'])
        else:
            e = s['error']
            body = J({'code': e['code'], 'codeName': e['codeName'], 'errmsg': e['errmsg'], 'errorLabels': e['errorLabels']})
        parts.append(f"{which} @ {s['at_utc'][11:23]}Z (+{s['since_patch_s']} s): {body}")
        readings.append(s['reading'])
    sp = S[f'c.{k:02d}.persistent']
    if k == 0:
        command = (f"createSearchIndexes attempt {k} (scheduled +{k * 30} s): pymongo Database(\"mt_fts\").command({J(sp['command'])}) on the persistent client "
                   "(connection opened before the PATCH); if it failed, the same command on a fresh client; then extra probe "
                   "Database(\"mt_fts\").command({\"aggregate\":\"products\",\"pipeline\":[{\"$listSearchIndexes\":{}}],\"cursor\":{}}) on the persistent client")
    else:
        command = f"createSearchIndexes attempt {k} (scheduled +{k * 30} s): same commands and clients as c.00"
    ctx = sp.get('state_around_attempt') or {}
    b4_, af_ = ctx.get('before') or {}, ctx.get('after') or {}
    pers, fresh, lx = S[f'c.{k:02d}.persistent'], S.get(f'c.{k:02d}.fresh'), S.get(f'c.{k:02d}.listx')
    def o(x):
        if x is None: return None
        return 'ok' if x['outcome'] == 'ok' else f"{x['error']['code']} {x['error']['codeName']} \"{x['error']['errmsg']}\""
    if pers['outcome'] == 'ok':
        rd = (f"Slot {k}: the persistent client's createSearchIndexes succeeded at +{pers['since_patch_s']} s, so activation finished between +180.1 s and +210.0 s.")
        ossd = "Open source: different (the open-source gateway always returns 115 \"Command 'createSearchIndexes' not supported.\")."
    else:
        rd = (f"Slot {k}: persistent and fresh clients both got {o(pers)} with no errorLabels; the $listSearchIndexes probe got "
              + ('ok with an empty list' if lx and lx['outcome'] == 'ok' else o(lx)) + '.')
        ossd = ("Open source: different (open source returns 115 with errmsg \"Command 'createSearchIndexes' not supported.\"" +
                ('; same code here, different errmsg' if pers['error']['code'] == 115 else '; here 67 CannotCreateIndex') + ').')
    rd += f" provisioningState: {b4_.get('provisioningState')} sent at +{b4_.get('sampled_since_patch_s')} s before, {af_.get('provisioningState')} sent at +{af_.get('sampled_since_patch_s')} s after. " + ossd
    add(f"c.{k:02d} @ {sp['at_utc']} (+{sp['since_patch_s']} s after the PATCH)", command, ' | '.join(parts), rd)

one('d1.00.listSearchIndexes', resp(S['d1.00.listSearchIndexes'], abbreviate=False, limit=2500))
for n in ['d0x.search_right_after_create']:
    one(n)
one('c.persistent.hello.end.seg1', J({'connectionId': S['c.persistent.hello.end.seg1']['response']['connectionId'], 'ok': 1.0}) + '  [selected fields]')
for n in ['d1.r.listSearchIndexes', 'd2.search_text', 'd2x.search_text_any', 'd2y.search_text_all', 'd3.compound', 'd3x.compound_mustNot_effective',
          'd4.compound_minimumShouldMatch', 'd5.searchMeta', 'd5x.searchMeta_count', 'd6a.rankFusion', 'd7a.create_vector_ivf', 'd7b.listIndexes',
          'd7c.keyword_query', 'd7d.vector_query', 'd7e.client_side_rrf', 'd7f.hybrid_unionWith_rrf', 'd6b.rankFusion_hybrid',
          'd8x.listSearchIndexes_all', 'x1.createSearchIndexes.dynamic', 'x2.updateSearchIndex', 'x3.dropIndexes_search_index',
          'x3b.listSearchIndexes', 'x4.createSearchIndexes.again', 'x4b.listSearchIndexes', 'x4c.search_text', 'x5.dropSearchIndex',
          'x5b.listSearchIndexes']:
    one(n)
one('x6.search_text_no_index', resp(S['x6.search_text_no_index'], limit=700))
mon_entry(list(range(8, 21)), 'b5')
one('z0.hello_after', hello_sel(S['z0.hello_after']))
for n in ['z0.buildInfo_after', 'z1.dropDatabase', 'z2.db_absent', 'z3.final_state']:
    one(n)

# d7e is a local computation, not a server command
for o in out:
    if o['step'].startswith('d7e'):
        o['command'] = 'local Python port of the Learn hybrid page rrf(lists, k=60) over the firstBatch lists of d7c and d7d (no server call)'

json.dump(out, open(os.path.join(HERE, 'structured_steps_compact.json'), 'w'), indent=1)
print(len(out), 'entries', len(json.dumps(out)), 'chars')
