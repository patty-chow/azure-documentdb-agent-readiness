import os
import json
import sys
from dotenv import load_dotenv
from db import get_collection
import openai

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not set. Set it in the environment to compute embeddings.")
    sys.exit(1)
openai.api_key = OPENAI_API_KEY

EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = int(os.environ.get("EMBED_DIMENSIONS", "1536"))

# Synthetic sample formulary entries
SAMPLE = [
    {"name": "Lisinopril", "indications": "Hypertension, heart failure, post-MI", "contraindications": "Pregnancy, history of angioedema", "dosing": "10mg once daily, titrate"},
    {"name": "Amlodipine", "indications": "Hypertension, angina", "contraindications": "Severe aortic stenosis", "dosing": "5-10mg once daily"},
    {"name": "Metformin", "indications": "Type 2 diabetes", "contraindications": "Severe renal impairment", "dosing": "500mg twice daily, titrate"},
    {"name": "Warfarin", "indications": "VTE, atrial fibrillation", "contraindications": "Active bleeding, pregnancy (relative)", "dosing": "Variable - monitor INR"},
    {"name": "Atorvastatin", "indications": "Hyperlipidemia, ASCVD risk reduction", "contraindications": "Active liver disease", "dosing": "10-80mg once daily"},
    {"name": "Albuterol", "indications": "Asthma exacerbation, COPD relief", "contraindications": "Hypersensitivity", "dosing": "Inhaled 90 mcg as needed"},
    {"name": "Prednisone", "indications": "Inflammatory conditions, asthma exacerbation", "contraindications": "Systemic fungal infections", "dosing": "5-60mg depending on condition"},
    {"name": "Amoxicillin", "indications": "Bacterial infections (respiratory, otitis)", "contraindications": "Penicillin allergy", "dosing": "500mg three times daily"},
    {"name": "Sertraline", "indications": "Depression, anxiety disorders", "contraindications": "MAOI use", "dosing": "50-200mg once daily"},
    {"name": "Omeprazole", "indications": "GERD, peptic ulcer disease", "contraindications": "Hypersensitivity", "dosing": "20-40mg once daily"}
]


def generate_embedding(text):
    resp = openai.Embedding.create(model=EMBED_MODEL, input=text)
    return resp['data'][0]['embedding']


def upsert_sample():
    coll = get_collection()
    for item in SAMPLE:
        # create a short doc text to embed
        doc_text = f"{item['name']}\nIndications: {item['indications']}\nContraindications: {item['contraindications']}\nDosing: {item['dosing']}"
        emb = generate_embedding(doc_text)
        if len(emb) != EMBED_DIM:
            print(f"Embedding dimension mismatch: got {len(emb)} expected {EMBED_DIM}")
            sys.exit(1)
        # upsert by name
        coll.update_one({"name": item['name']}, {"$set": {"name": item['name'], "indications": item['indications'], "contraindications": item['contraindications'], "dosing": item['dosing'], "embedding": emb}}, upsert=True)
    print("Seed data upsert complete.")

if __name__ == '__main__':
    upsert_sample()
