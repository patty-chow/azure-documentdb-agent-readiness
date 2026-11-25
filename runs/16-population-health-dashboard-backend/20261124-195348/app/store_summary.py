from db import get_db
from aggregations import compute_facets, upsert_summary

db = get_db()
patients = db.patients
cache = db.aggregations_cache
summary = compute_facets(patients, {})
upsert_summary(cache, 'default_cohort', {}, summary)
print('Upserted default_cohort')
