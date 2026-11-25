"""Create required indexes for the sample."""
from src.db import get_customers_collection

if __name__ == '__main__':
    coll = get_customers_collection()
    # create multikey index on purchases.date
    idx_name = coll.create_index([("purchases.date", 1)], name="purchases_date_idx")
    print("Created index:", idx_name)
