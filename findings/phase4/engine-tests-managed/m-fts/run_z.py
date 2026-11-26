"""Cleanup: hello after enabling, drop mt_fts, confirm it is gone, final Learn check GET.
The FullTextSearch preview feature is left enabled."""
import json
import os
import time

from common import DB_NAME, HERE, LEARN_GET_STATE, Recorder, get_client, now_utc

st = json.load(open(os.path.join(HERE, 'state_c.json')))
t0 = st['t0']
rec = Recorder('steps_z.json')
fresh = get_client(appname='mt-fts-hello')
rec.run(fresh['admin'], 'z0.hello_after', 'cleanup', 'hello after enabling (engine identity)', {'hello': 1})
rec.run(fresh['admin'], 'z0.buildInfo_after', 'cleanup', 'buildInfo after enabling', {'buildInfo': 1})
fresh.close()
client = get_client(appname='mt-fts-cleanup')
db = client[DB_NAME]
rec.run(db, 'z1.dropDatabase', 'cleanup', 'drop database mt_fts', {'dropDatabase': 1})
rec.run(client['admin'], 'z2.db_absent', 'cleanup', 'mt_fts is gone',
        {'listDatabases': 1, 'nameOnly': True, 'filter': {'name': DB_NAME}})
client.close()
print('done', now_utc())
