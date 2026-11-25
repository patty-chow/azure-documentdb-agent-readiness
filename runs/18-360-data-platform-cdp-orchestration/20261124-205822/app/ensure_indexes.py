#!/usr/bin/env python3
"""Create demo indexes: hashed email and text normalized_name."""
from src.db import get_db
import pymongo

def ensure():
    db = get_db()
    customers = db['customers']
    print('Creating hashed index on email...')
    customers.create_index([('email', pymongo.HASHED)], background=True)
    print('Creating text index on normalized_name...')
    customers.create_index([('normalized_name', 'text')], background=True)
    print('Indexes ensured')

if __name__ == '__main__':
    ensure()
