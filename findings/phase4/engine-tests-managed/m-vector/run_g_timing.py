"""m-vector part (g): how long after inserts into a brand-new vector index do $search results appear?

Usage: python run_g_timing.py <variant>
  hnsw_empty     (required) new empty collection -> vector-hnsw -> insert 5 docs -> poll every 10 s for 4 min
  diskann_empty  (extra)    same with vector-diskann; stops after 3 consecutive complete results
  ivf_empty      (extra)    same with vector-ivf numLists 1; stops after 3 consecutive complete results
  noindex        (extra)    $search on a collection holding the 5 docs and no vector index (what "not ready" could look like)
Poll query: $search cosmosSearch [1,0,0] k 3; complete result = _ids [1, 4, 5].
"""
import sys
import time

from common import DB_NAME, DOCS, Recorder, ci, diskann, get_client, hnsw, ids_of, ivf, search

variant = sys.argv[1]
EXPECTED = [1, 4, 5]
rec = Recorder(f'steps_g_{variant}.json')
client = get_client()
db = client[DB_NAME]

if variant == 'noindex':
    coll = 'timing_noindex'
    db[coll].drop()
    rec.run(db, 'g.noindex.1', 'g', f'setup: insert the five documents into {coll} (no vector index)',
            {'insert': coll, 'documents': DOCS, 'ordered': True}, extra=True)
    rec.run(db, 'g.noindex.2', 'g', f'$search cosmosSearch [1,0,0] k 3 on {coll}, which has no vector index',
            search(coll, [1.0, 0.0, 0.0], k=3), extra=True)
    print('wrote', rec.path)
    sys.exit(0)

builders = {'hnsw_empty': ('timing_hnsw', hnsw('v_hnsw'), False, 240),
            'diskann_empty': ('timing_diskann', diskann('v_diskann'), True, 240),
            'ivf_empty': ('timing_ivf', ivf('v_ivf', numLists=1), True, 240)}
coll, spec, extra, max_s = builders[variant]
full_run = variant == 'hnsw_empty'          # the required case polls the whole 4 minutes
p = f'g.{variant}'

db[coll].drop()
rec.run(db, f'{p}.1', 'g', f'create a NEW empty collection {coll}', {'create': coll}, extra=extra)
rec.run(db, f'{p}.2', 'g', f'create {spec["cosmosSearchOptions"]["kind"]} on the empty {coll}', ci(coll, [spec]),
        extra=extra, oss_step='e1' if variant == 'hnsw_empty' else None)
ins = rec.run(db, f'{p}.3', 'g', f'insert five 3-dimensional number[] documents into {coll}',
              {'insert': coll, 'documents': DOCS, 'ordered': True}, extra=extra,
              oss_step='e2' if variant == 'hnsw_empty' else None)
t0 = time.monotonic()
first_any = first_full = None
consecutive_full = 0
i = 0
while True:
    target = t0 + 10 * i
    delay = target - time.monotonic()
    if delay > 0:
        time.sleep(delay)
    offset = round(time.monotonic() - t0, 2)
    r = rec.run(db, f'{p}.poll{i:02d}', 'g',
                f'poll {i}: $search cosmosSearch [1,0,0] k 3 on {coll}, {offset} s after the insert returned',
                search(coll, [1.0, 0.0, 0.0], k=3), extra=extra, quiet=True,
                oss_step='e3' if (variant == 'hnsw_empty' and i == 0) else None)
    got = ids_of(r)
    rec.steps[-1]['offset_s_after_insert'] = offset
    rec.save()
    print(f'[{p}.poll{i:02d}] t+{offset:6.2f}s outcome={r["outcome"]} ids={got}', flush=True)
    if got and first_any is None:
        first_any = offset
    if got == EXPECTED:
        consecutive_full += 1
        if first_full is None:
            first_full = offset
    else:
        consecutive_full = 0
    i += 1
    if 10 * i > max_s:
        break
    if not full_run and consecutive_full >= 3:
        break

summary = {'variant': variant, 'collection': coll, 'polls': i, 'poll_interval_s': 10, 'max_window_s': max_s,
           'first_nonempty_offset_s': first_any, 'first_complete_offset_s': first_full,
           'expected_ids': EXPECTED, 'stopped_early': (not full_run and consecutive_full >= 3)}
rec.note(f'{p}.summary', 'g', 'summary of the poll loop', 'computed from the poll steps above', summary, extra=extra)
print('wrote', rec.path)
