from db import get_db
from aggregations import get_cached_summary

db = get_db()
cache = db.aggregations_cache
doc = get_cached_summary(cache, 'default_cohort', {})
print('Found cached summary id:', doc.get('_id') if doc else 'None')
