"""Steps (b) and (c): enable FullTextSearch exactly as the Learn overview shows for the Azure CLI,
then attempt createSearchIndexes every 30 s (anchored on the PATCH return time) until it succeeds
or 25 minutes pass. A monitor thread samples Learn's check GET and `az documentdb mongocluster show`
every 30 s.

  run_bc.py             segment 1: Learn GET (state), Learn GET (BODY), Learn PATCH, then poll
  run_bc.py --continue  later segments: resume the same 30-s schedule
Each invocation stops after SEG_LIMIT seconds so no command runs longer than 10 minutes.
Each attempt runs first on a persistent client, then (if that failed) on a fresh client.
"""
import argparse
import json
import os
import sys
import time

from common import (DB_NAME, HERE, LEARN_GET_BODY, LEARN_GET_STATE, LEARN_PATCH, ClusterMonitor,
                    Recorder, agg, create_search_index_cmd, get_client, index_ready, iso, j,
                    list_search_indexes_cmd, now_utc, IDX_NAME)

STATE_PATH = os.path.join(HERE, 'state_c.json')
SEG_LIMIT = 8 * 60 + 50
OVERALL = 25 * 60
INTERVAL = 30


def load_state():
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(st):
    tmp = STATE_PATH + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(st, f, indent=2)
    os.replace(tmp, STATE_PATH)


def client_opts(app):
    return dict(serverSelectionTimeoutMS=20000, connectTimeoutMS=15000, socketTimeoutMS=25000, appname=app)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--continue', dest='cont', action='store_true')
    args = ap.parse_args()
    seg_start = time.time()

    if not args.cont:
        if os.path.exists(STATE_PATH):
            print('state_c.json exists: the PATCH already ran; use --continue'); sys.exit(2)
        seg = 1
        rec = Recorder('steps_bc_seg1.json')
        persistent = get_client(**client_opts('mt-fts-persistent'))
        pdb = persistent[DB_NAME]
        rec.run(persistent['admin'], 'c.persistent.hello.start', 'c',
                'persistent client: hello before the PATCH (connection predates activation)', {'hello': 1})

        # ---- (b) exactly the Learn commands, in order ----
        rec.az('b1.get_state', 'b', 'Learn: review the current provisioning state and preview features',
               LEARN_GET_STATE)
        out, res = rec.az('b2.get_body', 'b',
                          'Learn: BODY=$(az rest ... --query <preserve others, add FullTextSearch once>)',
                          LEARN_GET_BODY)
        if res['returncode'] != 0:
            print('BODY GET failed; stopping'); sys.exit(4)
        body = res['stdout_text'].rstrip('\n')   # bash $(...) strips trailing newlines
        patch_out, pres = rec.az('b3.patch', 'b', 'Learn: az rest --method patch --url "$URL" --body "$BODY"',
                                 LEARN_PATCH, extra_env={'BODY': body}, record_env={'BODY': body})
        if pres['returncode'] != 0:
            save_state({'patch_failed': True, 'patch': j(patch_out)})
            print('PATCH failed; not polling'); sys.exit(4)
        t0 = pres['ended_epoch']
        st = {'t0': t0, 't0_utc': iso(t0), 'patch_started_utc': pres['started_utc'],
              'patch_ended_utc': pres['ended_utc'], 'next_k': 0, 'success': False, 'seg': 1,
              'mon_n': 0, 'persistent_opened_before_patch': True}
        save_state(st)
        print(f'PATCH returned at {iso(t0)}; polling starts now', flush=True)
        persistent_label = 'persistent client (connection opened before the PATCH)'
    else:
        st = load_state()
        if st.get('success'):
            print('already succeeded'); sys.exit(0)
        st['seg'] += 1
        seg = st['seg']
        t0 = st['t0']
        rec = Recorder(f'steps_c_seg{seg}.json')
        persistent = get_client(**client_opts('mt-fts-persistent'))
        pdb = persistent[DB_NAME]
        rec.run(persistent['admin'], f'c.persistent.hello.seg{seg}', 'c',
                f'persistent client for segment {seg}: hello at segment start', {'hello': 1})
        persistent_label = f'persistent client (opened at the start of segment {seg}, after the PATCH)'
        save_state(st)

    mon = ClusterMonitor(rec, f'b4.mon', anchor=t0, interval=30, offset=0,
                         until_epoch=seg_start + SEG_LIMIT - 5, start_n=st.get('mon_n', 0))
    mon.start()

    k = st['next_k']
    outcome = None
    success_rec = None
    while True:
        slot = t0 + k * INTERVAL
        if slot - t0 > OVERALL:
            outcome = 'overall_timeout'; break
        if slot > seg_start + SEG_LIMIT - 20:
            outcome = 'segment_end'; break
        delay = slot - time.time()
        if delay > 0:
            time.sleep(delay)
        since = round(time.time() - t0, 1)
        more = {'attempt': k, 'scheduled_since_patch_s': k * INTERVAL, 'since_patch_s': since}
        a = rec.run(pdb, f'c.{k:02d}.persistent', 'c',
                    '(c) createSearchIndexes attempt (persistent client)', create_search_index_cmd(),
                    client_label=persistent_label, more=more)
        if a['outcome'] == 'ok':
            success_rec = a
        else:
            fresh = get_client(**client_opts('mt-fts-fresh'))
            more2 = dict(more, since_patch_s=round(time.time() - t0, 1))
            b = rec.run(fresh[DB_NAME], f'c.{k:02d}.fresh', 'c',
                        '(c) createSearchIndexes attempt (fresh client created for this attempt)',
                        create_search_index_cmd(), client_label='fresh client created for this attempt',
                        more=more2)
            fresh.close()
            if b['outcome'] == 'ok':
                success_rec = b
            else:
                rec.run(pdb, f'c.{k:02d}.listx', 'c',
                        'extra: $listSearchIndexes probe in the same slot (persistent client)',
                        agg([{'$listSearchIndexes': {}}]), extra=True, client_label=persistent_label,
                        more=dict(more, since_patch_s=round(time.time() - t0, 1)), quiet=True)
        st['next_k'] = k + 1
        st['mon_n'] = mon.n
        save_state(st)
        if success_rec:
            outcome = 'success'; break
        k += 1

    if outcome == 'success':
        st.update({'success': True, 'success_step': success_rec['step'], 'success_utc': success_rec['at_utc'],
                   'success_since_patch_s': round(success_rec['at_epoch'] - t0, 1)})
        save_state(st)
        print(f"SUCCESS at {success_rec['at_utc']} ({st['success_since_patch_s']} s after the PATCH) via {success_rec['step']}", flush=True)
        # (d1) right after success: list once, one $search (extra), then poll until READY
        first = rec.run(pdb, 'd1.00.listSearchIndexes', 'd',
                        '$listSearchIndexes right after createSearchIndexes succeeded',
                        list_search_indexes_cmd(), more={'since_patch_s': round(time.time() - t0, 1)})
        rec.run(pdb, 'd0x.search_right_after_create', 'd',
                'extra: $search text immediately after createSearchIndexes returned (before waiting for READY)',
                agg([{'$search': {'index': IDX_NAME, 'text': {'query': 'bracket', 'path': 'title'}}},
                     {'$limit': 20}, {'$project': {'_id': 0, 'title': 1, 'score': {'$meta': 'searchScore'}}}]),
                extra=True, more={'since_patch_s': round(time.time() - t0, 1)})
        ready = index_ready(first)
        n = 1
        created_epoch = success_rec['at_epoch']
        last_sig = None
        while not ready and time.time() < seg_start + SEG_LIMIT - 10:
            time.sleep(3)
            r = rec.run(pdb, f'd1.{n:02d}.listSearchIndexes', 'd', '$listSearchIndexes poll until READY and queryable',
                        list_search_indexes_cmd(), quiet=True,
                        more={'since_create_s': round(time.time() - created_epoch, 1),
                              'since_patch_s': round(time.time() - t0, 1)})
            b = (r.get('response') or {}).get('cursor', {}).get('firstBatch') if r['outcome'] == 'ok' else r['error']
            sig = json.dumps([{k2: d.get(k2) for k2 in ('status', 'queryable')} for d in b] if isinstance(b, list) else b)
            if sig != last_sig:
                print(f"[d1.{n:02d}] {r['at_utc']} {sig}", flush=True)
                last_sig = sig
            ready = index_ready(r)
            n += 1
        st['ready'] = ready
        if ready:
            last = rec.steps[-1]
            st['ready_utc'] = last['at_utc']
            st['ready_since_create_s'] = round(last['at_epoch'] - created_epoch, 1)
            print(f"READY and queryable at {last['at_utc']} ({st['ready_since_create_s']} s after create)", flush=True)
        st['d1_next_n'] = n
        save_state(st)
    elif outcome == 'segment_end':
        print(f'segment {seg} ended without success; next attempt index {k}; rerun with --continue', flush=True)
    else:
        print('25 minutes passed without success', flush=True)
        st['overall_timeout'] = True
        save_state(st)

    mon.stop()
    mon.join(timeout=60)
    st['mon_n'] = mon.n
    save_state(st)
    rec.run(persistent['admin'], f'c.persistent.hello.end.seg{seg}', 'c',
            'persistent client: hello at segment end (same connectionId means the same connection was used)',
            {'hello': 1}, quiet=True)
    persistent.close()
    print('segment done', outcome, flush=True)
    sys.exit(0 if outcome == 'success' else 3)


if __name__ == '__main__':
    main()
