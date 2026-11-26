"""Standalone cluster monitor: Learn check GET + az documentdb mongocluster show every 30 s on the
schedule anchored on the PATCH return time, until about 12 minutes after the PATCH (max 9 min run)."""
import json
import os
import time

from common import HERE, ClusterMonitor, Recorder

st = json.load(open(os.path.join(HERE, 'state_c.json')))
t0 = st['t0']
start = time.time()
until = min(t0 + 12 * 60 + 5, start + 9 * 60)
rec = Recorder('steps_monitor.json')
mon = ClusterMonitor(rec, 'b5.mon', anchor=t0, interval=30, offset=0, until_epoch=until,
                     start_n=st.get('mon_n', 0))
mon.start()
mon.join(timeout=until - start + 60)
print('monitor done; samples', len(mon.samples), flush=True)
