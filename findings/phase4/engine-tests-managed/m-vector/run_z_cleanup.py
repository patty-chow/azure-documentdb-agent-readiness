"""m-vector cleanup: drop database mt_vector (and only it), then confirm it is gone."""
from common import DB_NAME, Recorder, get_client

rec = Recorder('steps_z_cleanup.json')
client = get_client()
rec.run(client[DB_NAME], 'z1', 'cleanup', f'list the collections left in {DB_NAME} before the drop',
        {'listCollections': 1, 'nameOnly': True}, quiet=True)
rec.run(client[DB_NAME], 'z2', 'cleanup', f'drop database {DB_NAME}', {'dropDatabase': 1})
rec.run(client.admin, 'z3', 'cleanup', f'confirm {DB_NAME} is gone (listDatabases filtered to {DB_NAME})',
        {'listDatabases': 1, 'nameOnly': True, 'filter': {'name': DB_NAME}})
print('wrote', rec.path)
