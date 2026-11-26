"""Final Learn check GET after the monitor ended (the FullTextSearch feature is left enabled)."""
import json
import os
import time

from common import HERE, LEARN_GET_STATE, Recorder, now_utc

st = json.load(open(os.path.join(HERE, 'state_c.json')))
rec = Recorder('steps_final.json')
rec.az('z3.final_state', 'b', 'final Learn check GET (feature left enabled)', LEARN_GET_STATE,
       more={'since_patch_s': round(time.time() - st['t0'], 1)})
print('done', now_utc())
