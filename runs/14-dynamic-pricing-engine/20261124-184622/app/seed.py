"""Idempotent seed script for the Dynamic Pricing sample.
Creates collections, indexes (via db.init_indexes), and inserts sample documents.
"""
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import ReturnDocument
import db

DB_NAME = "sample_retail_14"

SAMPLE_PRODUCTS = [
    {"sku": "SKU-001", "price": 19.99, "cost": 10.00, "updated_at": datetime.utcnow()},
    {"sku": "SKU-002", "price": 29.99, "cost": 15.00, "updated_at": datetime.utcnow()},
]

SAMPLE_COMPETITOR_PRICES = [
    {"sku": "SKU-001", "price": 18.50, "source": "compA", "timestamp": datetime.utcnow() - timedelta(hours=3)},
    {"sku": "SKU-001", "price": 20.00, "source": "compB", "timestamp": datetime.utcnow() - timedelta(hours=6)},
    {"sku": "SKU-002", "price": 27.99, "source": "compA", "timestamp": datetime.utcnow() - timedelta(days=1)},
]

SAMPLE_DEMAND_METRICS = [
    {"sku": "SKU-001", "views": 120, "units_sold": 8, "timestamp": datetime.utcnow() - timedelta(hours=2)},
    {"sku": "SKU-001", "views": 60, "units_sold": 5, "timestamp": datetime.utcnow() - timedelta(hours=26)},
    {"sku": "SKU-002", "views": 20, "units_sold": 1, "timestamp": datetime.utcnow() - timedelta(hours=4)},
]

SAMPLE_MARGIN_RULES = [
    {"sku_or_category": "SKU-001", "min_margin": 0.2, "max_margin": 0.6},
    {"sku_or_category": "SKU-002", "min_margin": 0.25, "max_margin": 0.5},
    {"sku_or_category": "DEFAULT", "min_margin": 0.15, "max_margin": 0.6},
]


def upsert_sample_data(db_name=DB_NAME):
    database = db.get_db(db_name)
    products = database.get_collection("products")
    competitor_prices = database.get_collection("competitor_prices")
    demand_metrics = database.get_collection("demand_metrics")
    margin_rules = database.get_collection("margin_rules")

    # Upsert products
    for p in SAMPLE_PRODUCTS:
        products.update_one({"sku": p["sku"]}, {"$set": p}, upsert=True)

    # Insert competitor prices (append; allow duplicates across runs)
    for cp in SAMPLE_COMPETITOR_PRICES:
        # Avoid inserting duplicates by checking exact match
        existing = competitor_prices.find_one({"sku": cp["sku"], "price": cp["price"], "source": cp["source"], "timestamp": cp["timestamp"]})
        if not existing:
            competitor_prices.insert_one(cp)

    # Insert demand metrics similarly
    for dm in SAMPLE_DEMAND_METRICS:
        existing = demand_metrics.find_one({"sku": dm["sku"], "views": dm["views"], "units_sold": dm["units_sold"], "timestamp": dm["timestamp"]})
        if not existing:
            demand_metrics.insert_one(dm)

    # Upsert margin rules by sku_or_category
    for mr in SAMPLE_MARGIN_RULES:
        margin_rules.update_one({"sku_or_category": mr["sku_or_category"]}, {"$set": mr}, upsert=True)


if __name__ == "__main__":
    print("Initializing indexes and seeding sample data...")
    db.init_indexes(DB_NAME)
    upsert_sample_data()
    print("Seeding complete.")
