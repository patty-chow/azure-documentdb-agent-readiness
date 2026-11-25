import uuid
import time
from datetime import datetime
from app.embeddings import get_embedding
from app.store import DocumentStore

# Create synthetic patients and chunks; idempotent by using deterministic ids

def make_chunks_for_patient(patient_id: str, n_chunks: int = 10):
    chunks = []
    for i in range(n_chunks):
        text = f"Patient {patient_id} clinical note chunk {i}. Synthetic demo data describing condition, meds, and observations."
        source_doc_id = f"{patient_id}_note"
        chunk_id = f"{patient_id}_chunk_{i}"
        _id = f"{patient_id}_{i}"
        emb = get_embedding(text)
        chunks.append({
            "_id": _id,
            "patientId": patient_id,
            "source_doc_id": source_doc_id,
            "chunk_id": chunk_id,
            "text": text,
            "embedding": emb,
            "metadata": {"created_at": datetime.utcnow().isoformat()},
        })
    return chunks

if __name__ == "__main__":
    patients = ["patient_1", "patient_2", "patient_3"]
    store = DocumentStore()
    store.ensure_indexes()
    all_chunks = []
    for p in patients:
        ch = make_chunks_for_patient(p, n_chunks=12)
        all_chunks.extend(ch)
    store.upsert_chunks(all_chunks)
    print(f"Seeded {len(all_chunks)} chunks across {len(patients)} patients into sample_healthcare_01.{store.collection.name}")
