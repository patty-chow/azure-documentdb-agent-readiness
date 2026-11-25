#!/usr/bin/env python
"""Compare the reproducer's rerun (report_rerun.json, database t_vector_rerun) with the tester's report.json
(database t_vector), step by step.

Run:  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I compare_rerun.py

The database name is normalised (t_vector_rerun -> t_vector) before comparing, in commands and replies.
Elapsed times are ignored. Everything else in each step (command, outcome, full reply or full error with
code, codeName, errmsg, errorLabels and raw) is compared exactly; differences are printed and written to
compare_rerun.json. It also checks, for every step the run.py auto-comparison calls identical to 0.117,
whether the 0.117 step sent the same command (an ok reply can match by coincidence when the spec differs).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = json.load(open(os.path.join(HERE, 'report.json')))
RERUN = json.load(open(os.path.join(HERE, 'report_rerun.json')))
PREV_REPORT = '/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/vector-index-rules/report.json'
PREV_PARITY = '/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/local-gateway-parity/report.json'


def norm(x):
    """Replace the rerun database name by the original one, recursively, in strings."""
    if isinstance(x, str):
        return x.replace('t_vector_rerun', 't_vector')
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, dict):
        return {norm(k): norm(v) for k, v in x.items()}
    return x


def strip(step):
    s = {k: v for k, v in step.items() if k not in ('elapsed_s',)}
    return norm(s)


def diff(a, b, path=''):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append((path + '/' + k, '<absent>', b[k]))
            elif k not in b:
                out.append((path + '/' + k, a[k], '<absent>'))
            else:
                out.extend(diff(a[k], b[k], path + '/' + k))
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(diff(x, y, f'{path}[{i}]'))
    elif a != b:
        out.append((path, a, b))
    return out


o_steps = {s['step']: s for s in ORIG['steps']}
r_steps = {s['step']: s for s in RERUN['steps']}
result = {'orig_ran_at': ORIG.get('ran_at'), 'rerun_ran_at': RERUN.get('ran_at'),
          'orig_steps': len(ORIG['steps']), 'rerun_steps': len(RERUN['steps']),
          'order_identical': [s['step'] for s in ORIG['steps']] == [s['step'] for s in RERUN['steps']],
          'only_in_orig': sorted(set(o_steps) - set(r_steps)), 'only_in_rerun': sorted(set(r_steps) - set(o_steps)),
          'identical_steps': [], 'different_steps': {}}
for sid, o in o_steps.items():
    r = r_steps.get(sid)
    if r is None:
        continue
    d = diff(strip(o), strip(r))
    if d:
        result['different_steps'][sid] = [{'path': p, 'orig': a, 'rerun': b} for p, a, b in d]
    else:
        result['identical_steps'].append(sid)

# Compare the top-level derived blocks too.
for key in ('engine', 'vector_index_option_keys', 'comparison_with_0_117_auto'):
    d = diff(norm(ORIG.get(key)), norm(RERUN.get(key)))
    result[f'{key}_differences'] = [{'path': p, 'orig': a, 'rerun': b} for p, a, b in d]

# Did the 0.117 counterpart of each "identical" step send the same command?
prev = {s['step']: s for s in json.load(open(PREV_REPORT))['steps']}
par = next((s for s in json.load(open(PREV_PARITY))['steps'] if s['step'] == '06-vector-diskann'), None)
cmd_check = {}
for c in RERUN['comparison_with_0_117_auto']:
    if c.get('status') != 'identical':
        continue
    sid = c['step']
    now = r_steps[sid].get('command')
    if sid == 'g10':
        then = par.get('command') if par else None
    else:
        then = prev.get(sid, {}).get('command')
    now_n, then_n = norm(now), then
    if isinstance(then_n, str):
        try:
            then_n = json.loads(then_n)
        except Exception:
            pass
    cmd_check[sid] = 'same command' if now_n == then_n else {'now': now_n, 'then_0_117': then_n}
result['identical_to_0_117_command_check'] = cmd_check

with open(os.path.join(HERE, 'compare_rerun.json'), 'w') as fh:
    json.dump(result, fh, indent=2, default=str)

print('orig', result['orig_ran_at'], result['orig_steps'], 'steps; rerun', result['rerun_ran_at'], result['rerun_steps'], 'steps')
print('order identical:', result['order_identical'], '| only in orig:', result['only_in_orig'], '| only in rerun:', result['only_in_rerun'])
print('identical steps:', len(result['identical_steps']))
print('different steps:', len(result['different_steps']))
for sid, ds in result['different_steps'].items():
    for d in ds:
        print(f"  {sid} {d['path']}: orig={json.dumps(d['orig'], default=str)[:300]} | rerun={json.dumps(d['rerun'], default=str)[:300]}")
for key in ('engine', 'vector_index_option_keys', 'comparison_with_0_117_auto'):
    print(f'{key} differences:', result[f'{key}_differences'])
print('0.117 command check for steps called identical to 0.117:')
for sid, v in cmd_check.items():
    if v != 'same command':
        print('  ', sid, json.dumps(v, default=str)[:600])
print('  same command:', [s for s, v in cmd_check.items() if v == 'same command'])
