"""Seed script to populate sample_banking_04 with accounts, transactions, and positions.
Idempotent: uses upsert on generated unique keys.
"""
import os
import random
import argparse
import sys
from pathlib import Path
# ensure repo root is on path so src is importable when invoked as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timedelta
from faker import Faker
from src.db import get_db

fake = Faker()

def seed(db, count=100):
    accounts = db.accounts
    transactions = db.transactions
    positions = db.positions

    # Create a small set of accounts
    acc_docs = []
    for i in range(10):
        acc_id = f"ACC-{1000+i}"
        acc = {"_id": acc_id, "name": fake.company(), "region": random.choice(['US','EU','APAC'])}
        acc_docs.append(acc)
        accounts.update_one({'_id': acc_id}, {'$set': acc}, upsert=True)

    # Create transactions across reporting periods
    periods = ['2023-Q4', '2024-Q1']
    start_date = datetime(2023,10,1)
    for i in range(count):
        tx_id = f"TX-{i+1}"
        acc = random.choice(acc_docs)
        date = start_date + timedelta(days=random.randint(0,180))
        amount = round(random.uniform(-10000,10000),2)
        tx = {
            '_id': tx_id,
            'account_id': acc['_id'],
            'date': date.isoformat(),
            'amount': amount,
            'currency': 'USD',
            'reporting_period': random.choice(periods)
        }
        transactions.update_one({'_id': tx_id}, {'$set': tx}, upsert=True)

    # Create simple positions
    for i, acc in enumerate(acc_docs):
        pos_id = f"POS-{i+1}"
        pos = {'_id': pos_id, 'account_id': acc['_id'], 'as_of': '2023-12-31', 'value': round(random.uniform(10000,1000000),2)}
        positions.update_one({'_id': pos_id}, {'$set': pos}, upsert=True)

    print(f"Seeded {len(acc_docs)} accounts, {count} transactions, {len(acc_docs)} positions")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=100, help='Number of transactions to create')
    args = parser.parse_args()
    db = get_db()
    seed(db, count=args.count)
