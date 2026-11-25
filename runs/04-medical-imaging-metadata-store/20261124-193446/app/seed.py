"""Seed the sample database with synthetic medical imaging metadata.

Creates documents in database 'sample_healthcare_04', collection 'medical_images'.
If OPENAI_API_KEY is set, compute real embeddings; otherwise use pseudo-random deterministic embeddings.
"""
import os
from dotenv import load_dotenv
from app.db import get_collection
import openai
import numpy as np

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", "1536"))
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "medical_images")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

collection = get_collection(COLLECTION_NAME)

# small synthetic dataset
modalities = ["XR", "CT", "MRI", "US"]
body_parts = ["chest", "abdomen", "head", "pelvis", "extremity", "spine"]
findings_templates = [
    "No acute cardiopulmonary disease.",
    "Lung nodule in the right upper lobe measuring 6 mm.",
    "Complex ovarian cyst on the left with septations.",
    "Acute intracranial hemorrhage with midline shift.",
    "Compression fracture of the T12 vertebral body.",
    "Multiple small hypodense lesions in the liver suspicious for metastases.",
    "Moderate bilateral knee osteoarthritis.",
    "Small subsegmental pulmonary embolism in the left lower lobe." 
]


def embed_text(text: str):
    if OPENAI_API_KEY:
        resp = openai.Embeddings.create(input=text, model=OPENAI_MODEL)
        vec = resp["data"][0]["embedding"]
        arr = np.array(vec, dtype=np.float32)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = (arr / norm).astype(float)
        return arr.tolist()
    else:
        rng = np.random.RandomState(abs(hash(text)) % (2**32))
        arr = rng.normal(size=(EMBEDDING_DIM,)).astype(np.float32)
        arr = arr / np.linalg.norm(arr)
        return arr.tolist()


def make_doc(i: int):
    import random
    mod = random.choice(modalities)
    bp = random.choice(body_parts)
    findings = random.choice(findings_templates)
    emb = embed_text(findings + f" (doc {i})")
    return {"modality": mod, "body_part": bp, "findings": findings, "embedding": emb}


def main(n=50):
    print(f"Inserting {n} documents into collection '{COLLECTION_NAME}'...")
    docs = [make_doc(i) for i in range(n)]
    res = collection.insert_many(docs)
    print(f"Inserted {len(res.inserted_ids)} documents")


if __name__ == "__main__":
    main()
