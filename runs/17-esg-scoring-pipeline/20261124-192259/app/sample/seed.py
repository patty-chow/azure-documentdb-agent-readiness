"""Seed sample ESG company documents and create standard indexes.

Run as: python -m sample.seed
"""
from pymongo import ASCENDING
from .db import get_db
from .config import COLLECTION_NAME

SAMPLE_DOCS = [
    {"name": "Green Widgets Inc", "raw_esg_text": "Green Widgets has reduced emissions and uses recycled materials.", "schemaVersion": 1},
    {"name": "FastBank", "raw_esg_text": "FastBank offers community loans but had a recent compliance fine.", "schemaVersion": 1},
    {"name": "UrbanHomes", "raw_esg_text": "UrbanHomes invests in affordable housing and local hiring.", "schemaVersion": 1},
    {"name": "Oil&Co", "raw_esg_text": "Oil&Co reports high emissions and ongoing litigation.", "schemaVersion": 1},
    {"name": "HealthyFoods", "raw_esg_text": "HealthyFoods sources organic produce and discloses supplier audits.", "schemaVersion": 1},
    {"name": "TechNova", "raw_esg_text": "TechNova has strong governance but mixed labor practices in some factories.", "schemaVersion": 1},
    {"name": "RetailChain", "raw_esg_text": "RetailChain has many stores; recent data breach raised concerns.", "schemaVersion": 1},
    {"name": "SolarWorks", "raw_esg_text": "SolarWorks builds large-scale solar farms and community projects.", "schemaVersion": 1},
]


def seed():
    db = get_db()
    col = db[COLLECTION_NAME]
    # create useful standard indexes (not vector index)
    print("Creating standard indexes: name (unique) and schemaVersion")
    col.create_index([("name", ASCENDING)], unique=True, name="idx_name_unique")
    col.create_index([("schemaVersion", ASCENDING)], name="idx_schemaVersion")

    for doc in SAMPLE_DOCS:
        filter_q = {"name": doc["name"]}
        update = {"$setOnInsert": doc}
        res = col.update_one(filter_q, update, upsert=True)
        print(f"Upserted {doc['name']}")


if __name__ == "__main__":
    seed()
