import os
import json
import random
import numpy as np
from dotenv import load_dotenv

load_dotenv()

from app.db import get_db

EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", "1536"))
COLLECTION = os.environ.get("COLLECTION_NAME", "trials")

# sample synthetic trials
SAMPLE_TRIALS = [
    {
        "trial_id": "T-001",
        "title": "Study of Drug A for Hypertension",
        "summary": "A phase 2 trial evaluating Drug A for patients with hypertension.",
        "criteria": {"min_age": 18, "max_age": 75, "conditions": ["hypertension"], "labs": {"creatinine": 0.5}},
    },
    {
        "trial_id": "T-002",
        "title": "Study of Drug B in Diabetes",
        "summary": "A study of Drug B for patients with type 2 diabetes.",
        "criteria": {"min_age": 21, "max_age": 80, "conditions": ["diabetes"], "labs": {"hba1c": 6.5}},
    },
    {
        "trial_id": "T-003",
        "title": "Study of Device C for Heart Failure",
        "summary": "A device trial for certain classes of heart failure patients.",
        "criteria": {"min_age": 40, "max_age": 85, "conditions": ["heart failure"], "labs": {}},
    },
]


def generate_random_vector(dim):
    v = np.random.RandomState(42).randn(dim)
    v = v / np.linalg.norm(v)
    return v.tolist()


def maybe_embed(text):
    key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    if key:
        try:
            import openai
            resp = openai.Embedding.create(input=text, model=model)
            return resp['data'][0]['embedding']
        except Exception as e:
            print("OpenAI embedding failed, falling back to random: ", e)
            return generate_random_vector(EMBEDDING_DIM)
    else:
        return generate_random_vector(EMBEDDING_DIM)


def seed():
    db = get_db()
    coll = db.get_collection(COLLECTION)
    print("Creating scalar indexes...")
    coll.create_index([("criteria.conditions", 1)])
    coll.create_index([("criteria.min_age", 1), ("criteria.max_age", 1)])

    print("Inserting sample trials...")
    docs = []
    for t in SAMPLE_TRIALS:
        doc = t.copy()
        # embed the summary+title as the vector field
        text = (doc.get('title','') + '\n' + doc.get('summary',''))
        doc['embedding'] = maybe_embed(text)
        docs.append(doc)

    # upsert to avoid duplicates in repeated runs
    for d in docs:
        coll.update_one({"trial_id": d['trial_id']}, {"$set": d}, upsert=True)

    print("Seed complete. Inserted/updated {} trials.".format(len(docs)))


if __name__ == '__main__':
    seed()
