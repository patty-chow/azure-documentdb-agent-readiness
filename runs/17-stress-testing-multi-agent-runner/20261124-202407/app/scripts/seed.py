"""Idempotent seed script: creates collections, indexes and inserts sample data."""
import json
from pymongo import ASCENDING, DESCENDING
from src.db import get_db
import os

DB = get_db()

def ensure_collections():
    # Create collections if they don't exist
    if 'positions' not in DB.list_collection_names():
        DB.create_collection('positions')
    if 'stress_runs' not in DB.list_collection_names():
        DB.create_collection('stress_runs')

def create_indexes():
    pos = DB['positions']
    pos.create_index([('account_id', ASCENDING)], name='idx_account')
    pos.create_index([('instrument', ASCENDING)], name='idx_instrument')
    pos.create_index([('timestamp', DESCENDING)], name='idx_timestamp')
    # Partial index on rate sensitivity when present
    pos.create_index([('risk_factors.rateSensitivity', ASCENDING)], name='idx_rate_sens')

def load_seed_data():
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'positions_seed.json')
    with open(data_path) as f:
        docs = json.load(f)
    pos = DB['positions']
    for d in docs:
        pos.replace_one({'_id': d['_id']}, d, upsert=True)

if __name__ == '__main__':
    ensure_collections()
    create_indexes()
    load_seed_data()
    print('Seed complete')
