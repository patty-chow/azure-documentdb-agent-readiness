from fastapi import FastAPI, HTTPException
from app.db import get_db
from app.cohort import generate_cohort_snapshot, list_snapshots, get_snapshot
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = FastAPI(title="Cohort Analysis Sample")

# Start scheduler to refresh weekly (7 days)
scheduler = BackgroundScheduler()

def weekly_job():
    db = get_db()
    generate_cohort_snapshot(db)

# schedule weekly (every 7 days)
scheduler.add_job(weekly_job, 'interval', days=7, id='weekly_cohort')
scheduler.start()

# ensure scheduler stops on exit
atexit.register(lambda: scheduler.shutdown(wait=False))


@app.get('/cohorts')
def api_list_snapshots(limit: int = 20):
    db = get_db()
    return list_snapshots(db, limit=limit)


@app.get('/cohorts/{snapshot_month}')
def api_get_snapshot(snapshot_month: str):
    db = get_db()
    snap = get_snapshot(db, snapshot_month)
    if not snap:
        raise HTTPException(status_code=404, detail='Snapshot not found')
    return snap


@app.post('/admin/refresh')
def api_refresh():
    db = get_db()
    snap = generate_cohort_snapshot(db)
    return {"ok": True, "snapshot_id": str(snap.get('_id'))}
