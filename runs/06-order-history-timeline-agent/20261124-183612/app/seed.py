"""Idempotent seed script for sample_retail_06.orders

Usage: python seed.py
Reads DOCUMENTDB_URI from environment.
"""
from src.pkgagent import db

if __name__ == "__main__":
    print("Seeding sample_retail_06.orders ...")
    db.seed_sample(size=300)
    print("Done.")
