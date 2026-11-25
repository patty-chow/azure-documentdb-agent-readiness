#!/usr/bin/env python
"""Print a compact per-step listing of report.json (step, command, response, reading) for hand-off.

Errors keep code, codeName, the exact errmsg and errorLabels. Successful replies are given whole when
short; explain and hello replies are given as labelled excerpts and other long replies are cut at 450
characters. report.json always holds every full reply."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(HERE, 'report.json')))
c = lambda x: json.dumps(x, separators=(',', ':'))
out = []
for s in r['steps']:
    cmd = s['command'] if isinstance(s['command'], str) else c(s['command'])
    if s['outcome'] != 'ok':
        e = s.get('error') or {}
        resp = (f"ERROR code {e.get('code')}, codeName {e.get('codeName')}, errmsg {json.dumps(e.get('errmsg'))}, "
                f"errorLabels {'absent' if not e.get('errorLabels_present') else e.get('errorLabels')}")
    elif s['kind'] == 'container':
        resp = f"returncode {s['response']['returncode']}; stdout: {s['response']['stdout'][:450]}" + (' ... (cut)' if len(s['response']['stdout']) > 450 else '')
    elif isinstance(s['command'], dict) and 'explain' in s['command']:
        wp = s['response']['stages'][0]['$cursor']['queryPlanner']['winningPlan']
        resp = ('ok 1; excerpt stages[0].$cursor.queryPlanner.winningPlan: ' +
                c({'stage': wp.get('stage'), 'cosmosSearchCustomParams': wp.get('cosmosSearchCustomParams'),
                   'inputStage': {k: wp.get('inputStage', {}).get(k) for k in ('stage', 'indexName')}}) +
                f"; later stages {[list(x)[0] for x in s['response']['stages'][1:]]} (full reply in report.json)")
    elif isinstance(s['command'], dict) and 'hello' in s['command']:
        h = s['response']
        resp = 'ok 1; excerpt: ' + c({k: h.get(k) for k in ('maxWireVersion', 'maxWriteBatchSize', 'saslSupportedMechs', 'internal')}) + ' (full reply in report.json)'
    else:
        resp = c(s['response'])
        if len(resp) > 450:
            resp = resp[:450] + ' ... (cut; full reply in report.json)'
    out.append({'step': s['step'], 'command': cmd, 'response': resp, 'reading': s['reading']})
json.dump(out, sys.stdout, indent=0, ensure_ascii=False)
