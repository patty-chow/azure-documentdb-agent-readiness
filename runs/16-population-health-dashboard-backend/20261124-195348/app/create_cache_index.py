from db import get_db

db = get_db()
cache = db.aggregations_cache
cache.create_index([("expiresAt", 1)], expireAfterSeconds=0)
print('Created TTL index on aggregations_cache.expiresAt')
