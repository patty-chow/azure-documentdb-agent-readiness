import json, os, sys, time, datetime, warnings
warnings.simplefilter('ignore')
from pymongo import MongoClient
env = {}
for line in open(sys.argv[1]):
    line = line.strip()
    if line and '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1); env[k] = v.strip().strip('"').strip("'")
out = open(sys.argv[2], 'a')
stop = sys.argv[3]
deadline = time.time() + float(sys.argv[4])
c = MongoClient(env['MANAGED_URI'], serverSelectionTimeoutMS=3000, connectTimeoutMS=3000, socketTimeoutMS=3000)
coll = c['mt_upgrade']['probe']
i = 0
while time.time() < deadline and not os.path.exists(stop):
    t0 = time.time(); rec = {'i': i, 'ts': datetime.datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'}
    try:
        h = c.admin.command('hello')
        rec['wire'] = h.get('maxWireVersion'); rec['versions'] = h.get('internal', {}).get('documentdb_versions')
        coll.insert_one({'i': i, 't': t0})
        rec['find'] = coll.count_documents({})
        rec['ok'] = True
    except Exception as e:
        rec['ok'] = False; rec['err'] = type(e).__name__; rec['msg'] = str(e)[:300]
        rec['code'] = getattr(e, 'code', None)
    rec['ms'] = round((time.time() - t0) * 1000)
    out.write(json.dumps(rec) + '\n'); out.flush()
    i += 1
    time.sleep(max(0, 1 - (time.time() - t0)))
try:
    c.drop_database('mt_upgrade')
    out.write(json.dumps({'cleanup': 'dropped mt_upgrade'}) + '\n')
except Exception as e:
    out.write(json.dumps({'cleanup_error': type(e).__name__}) + '\n')
