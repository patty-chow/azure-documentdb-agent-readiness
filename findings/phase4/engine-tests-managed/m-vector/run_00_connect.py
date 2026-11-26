"""m-vector step 0: connect, record hello/buildInfo, confirm mt_vector starts absent."""
from common import Recorder, get_client, DB_NAME

rec = Recorder('steps_00_connect.json')
client = get_client()
admin = client.admin
db = client[DB_NAME]

rec.run(admin, '0.hello', 'setup', 'hello on the plain host (engine identity)', {'hello': 1})
rec.run(admin, '0.buildInfo', 'setup', 'buildInfo (engine identity)', {'buildInfo': 1})
r = rec.run(admin, '0.listDatabases', 'setup', 'does mt_vector already exist? (filtered to mt_vector only)',
            {'listDatabases': 1, 'nameOnly': True, 'filter': {'name': DB_NAME}})
if r['outcome'] == 'ok' and r['response'].get('databases'):
    rec.run(db, '0.dropDatabase_pre', 'setup', 'mt_vector existed from an earlier run: drop it before starting',
            {'dropDatabase': 1})
print('wrote', rec.path)
