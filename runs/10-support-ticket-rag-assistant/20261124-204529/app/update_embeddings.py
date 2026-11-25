from src.db import get_client, pseudo_embedding, DB_NAME, COLLECTION

client = get_client()
db = client[DB_NAME]
col = db[COLLECTION]

count = 0
for doc in col.find({}):
    if 'embedding' not in doc:
        text = (doc.get('title','') + '\n' + doc.get('content',''))
        emb = pseudo_embedding(text)
        col.update_one({'_id': doc['_id']}, {'$set': {'embedding': emb}})
        count += 1

print(f"Updated {count} documents with pseudo-embeddings")
client.close()
