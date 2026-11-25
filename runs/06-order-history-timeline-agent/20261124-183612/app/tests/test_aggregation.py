from src.db import get_db
from datetime import datetime, timedelta


def test_spend_summary_all():
    db = get_db()
    pipeline = [
        {'$group': {'_id': '$customer_id', 'order_count': {'$sum': 1}, 'total_spent': {'$sum': '$total_amount'}}},
        {'$sort': {'total_spent': -1}},
        {'$limit': 1}
    ]
    res = list(db.orders.aggregate(pipeline))
    assert isinstance(res, list)


def test_spend_summary_last_month():
    db = get_db()
    now = datetime.utcnow()
    first_of_this_month = datetime(now.year, now.month, 1)
    from_date = (first_of_this_month - timedelta(days=1)).replace(day=1)
    pipeline = [
        {'$match': {'order_date': {'$gte': from_date, '$lt': first_of_this_month}}},
        {'$group': {'_id': '$customer_id', 'order_count': {'$sum': 1}, 'total_spent': {'$sum': '$total_amount'}}}
    ]
    res = list(db.orders.aggregate(pipeline))
    assert isinstance(res, list)
