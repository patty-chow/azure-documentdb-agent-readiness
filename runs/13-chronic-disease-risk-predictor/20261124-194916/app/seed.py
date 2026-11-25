import os
import uuid
from dotenv import load_dotenv
from src.db import get_db
from src.embeddings import embed_texts, embed_vector_from_features

load_dotenv()
SEED_COUNT = int(os.environ.get("SEED_COUNT", "200"))
COLLECTION = "high_risk_profiles"


def synthetic_profile(i):
    # deterministic synthetic features
    age = 40 + (i % 50)
    bmi = 18 + (i % 30)
    systolic = 110 + (i % 60)
    features = {"age": age, "bmi": bmi, "systolic": systolic}
    risk_label = "high" if (bmi > 30 or systolic > 140 or age > 60) else "moderate"
    interventions = []
    if bmi > 30:
        interventions.append("weight management")
    if systolic > 140:
        interventions.append("antihypertensive review")
    if age > 60:
        interventions.append("frailty screening")
    patient_id = f"seed-{i:04d}"
    return patient_id, features, risk_label, interventions


def main():
    db = get_db()
    coll = db[COLLECTION]
    print(f"Seeding {SEED_COUNT} synthetic profiles into {COLLECTION}...")
    # Create batches
    batch = []
    texts = []
    ids = []
    metas = []
    for i in range(SEED_COUNT):
        pid, features, risk_label, interventions = synthetic_profile(i)
        text = ", ".join(f"{k}:{v}" for k, v in sorted(features.items()))
        batch.append({
            "patient_id": pid,
            "features": features,
            "risk_label": risk_label,
            "recommended_interventions": interventions,
        })
        texts.append(text)
        ids.append(pid)
        metas.append((risk_label, interventions))

    embeddings = embed_texts(texts)
    # Upsert each document with embedding
    for doc, emb, pid, meta in zip(batch, embeddings, ids, metas):
        doc["embedding"] = emb
        coll.update_one({"patient_id": pid}, {"$set": doc}, upsert=True)

    print("Seeding complete.")


if __name__ == "__main__":
    main()
