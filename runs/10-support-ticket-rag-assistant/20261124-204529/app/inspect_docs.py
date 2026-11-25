from src.db import get_client, DB_NAME, COLLECTION

client = get_client()
db = client[DB_NAME]
col = db[COLLECTION]
for doc in col.find().limit(3):
    print('id', doc.get('_id'))
    e = doc.get('embedding')
    print('embedding_type', type(e))
    if isinstance(e, list):
        print('len', len(e))
    else:
        print('value', repr(e)[:200])
    print('---')
client.close()
