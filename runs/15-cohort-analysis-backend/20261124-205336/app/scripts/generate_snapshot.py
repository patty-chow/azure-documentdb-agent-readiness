"""Run cohort aggregation and write a snapshot document

Usage: python scripts/generate_snapshot.py
"""
from app.db import get_db
from app.cohort import generate_cohort_snapshot

if __name__ == '__main__':
    db = get_db()
    snap = generate_cohort_snapshot(db)
    print('Generated snapshot:', snap.get('snapshot_month'), 'buckets:', len(snap.get('buckets', [])))
