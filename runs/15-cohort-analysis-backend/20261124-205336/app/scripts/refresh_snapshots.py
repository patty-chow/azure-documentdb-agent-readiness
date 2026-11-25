"""
One-shot script to compute cohort snapshots and persist them to the
`cohort_snapshots` collection. Useful for CI and manual verification.
"""
from app.db import get_db
from app.cohort import compute_cohort_snapshots


def main():
    db = get_db()
    snaps = compute_cohort_snapshots(db)
    coll = db.cohort_snapshots
    for s in snaps:
        coll.update_one({"cohort_month": s["cohort_month"]}, {"$set": s}, upsert=True)
    print(f"Wrote {len(snaps)} snapshots")


if __name__ == "__main__":
    main()
