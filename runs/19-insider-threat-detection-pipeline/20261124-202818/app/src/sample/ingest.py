"""Aggregate recent activity per employee, compute features, embed and store vectors."""
from datetime import datetime, timedelta
from sample.db import get_db
from sample.embedder import embed_features_as_text
from sample.config import EMBEDDING_DIMS

FEATURE_WINDOW_DAYS = 7


def compute_features(events):
    # events: list of activity docs
    total = len(events)
    by_type = {}
    days = set()
    for e in events:
        t = e.get("event_type")
        by_type[t] = by_type.get(t, 0) + 1
        ts = e.get("timestamp")
        if ts:
            days.add(ts.date())
    unique_days = len(days)
    # feature vector: total, unique_days, counts for the canonical types order
    canonical = ["login", "file_access", "email_sent", "external_transfer", "privileged_command"]
    counts = [by_type.get(k, 0) for k in canonical]
    # normalize counts by total if total>0
    norm_counts = [(c / total) if total>0 else 0.0 for c in counts]
    features = [float(total), float(unique_days)] + norm_counts
    return features


def ingest_once():
    db = get_db()
    logs = db["activity_logs"]
    vectors = db["employee_vectors"]
    now = datetime.utcnow()
    start = now - timedelta(days=FEATURE_WINDOW_DAYS)

    # find distinct employees in logs within window
    cursor = logs.find({"timestamp": {"$gte": start}})
    employees = set()
    events_by_emp = {}
    for doc in cursor:
        emp = doc["employee_id"]
        employees.add(emp)
        events_by_emp.setdefault(emp, []).append(doc)

    for emp in employees:
        events = events_by_emp.get(emp, [])
        features = compute_features(events)
        # get embedding
        try:
            emb = embed_features_as_text(features)
        except Exception as exc:
            print("Embedding failed:", exc)
            emb = []
        doc = {
            "employee_id": emp,
            "window_start": start,
            "window_end": now,
            "features": features,
            "embedding": emb,
            "model": "text-embedding-3-small",
            "dims": len(emb)
        }
        vectors.replace_one({"employee_id": emp, "window_start": start}, doc, upsert=True)
    print(f"Ingested {len(employees)} employee vectors")


if __name__ == "__main__":
    ingest_once()
