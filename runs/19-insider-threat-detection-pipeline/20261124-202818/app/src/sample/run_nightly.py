"""Run nightly anomaly detection process: compare recent vector to historical centroid and anomaly profiles."""
from sample.db import get_db
from sample.utils import centroid, cosine_similarity
from datetime import datetime
from sample.config import ANOMALY_COSINE_THRESHOLD


def run_nightly_once():
    db = get_db()
    vectors = db["employee_vectors"]
    profiles = db["anomaly_profiles"]
    alerts = db["alerts"]

    # load anomaly profile embeddings
    profile_docs = list(profiles.find({}))
    profile_embeddings = [(p.get("profile_id"), p.get("embedding")) for p in profile_docs]

    # for each employee, get latest vector and historical vectors (exclude latest)
    for emp_doc in vectors.find({}):
        emp = emp_doc["employee_id"]
        recent = emp_doc.get("embedding")
        if not recent:
            continue
        # historical: other documents for this employee
        hist_cursor = vectors.find({"employee_id": emp, "_id": {"$ne": emp_doc.get("_id")}})
        hist_vecs = [d.get("embedding") for d in hist_cursor if d.get("embedding")]
        if hist_vecs:
            cent = centroid(hist_vecs)
            sim = cosine_similarity(recent, cent)
        else:
            # no history: treat as not anomalous
            sim = 1.0
        # compare to anomaly profiles (local cosine); if any profile is highly similar, that can influence
        profile_sims = []
        for pid, p_emb in profile_embeddings:
            if p_emb:
                profile_sims.append((pid, cosine_similarity(recent, p_emb)))
        # decide
        is_anomaly = sim < ANOMALY_COSINE_THRESHOLD
        reason = {
            "employee_id": emp,
            "timestamp": datetime.utcnow(),
            "similarity_to_centroid": sim,
            "profile_sims": profile_sims,
            "threshold": ANOMALY_COSINE_THRESHOLD
        }
        if is_anomaly:
            alerts.insert_one({"employee_id": emp, "detected_at": datetime.utcnow(), "reason": reason})
            print(f"ALERT: {emp} similarity {sim:.3f} < {ANOMALY_COSINE_THRESHOLD}")


if __name__ == "__main__":
    run_nightly_once()
