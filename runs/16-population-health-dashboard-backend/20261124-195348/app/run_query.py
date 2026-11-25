from db import get_db
from aggregations import compute_facets

if __name__ == '__main__':
    db = get_db()
    patients = db.patients
    summary = compute_facets(patients, {})
    print('Diagnoses buckets:', len(summary.get('diagnoses', [])))
    print('Age bands:', summary.get('age_bands'))
    print('Gender buckets:', summary.get('gender'))
    print('Region buckets:', summary.get('region'))
