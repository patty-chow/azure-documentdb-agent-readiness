"""Aggregation pipelines using pymongo"""
from datetime import datetime, timedelta
from src.app.db import get_db

COLLECTION_NAME = 'feedbacks'

def sentiment_by_channel():
    db = get_db()
    coll = db[COLLECTION_NAME]
    pipeline = [
        {"$group": {"_id": "$channel", "avgSentiment": {"$avg": "$sentiment_score"}, "count": {"$sum": 1}}},
        {"$sort": {"avgSentiment": -1}}
    ]
    res = list(coll.aggregate(pipeline))
    print("Sentiment by channel:")
    for r in res:
        print(r)


def sentiment_by_topic():
    db = get_db()
    coll = db[COLLECTION_NAME]
    pipeline = [
        {"$unwind": {"path": "$topics", "preserveNullAndEmptyArrays": False}},
        {"$group": {"_id": "$topics", "avgSentiment": {"$avg": "$sentiment_score"}, "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    res = list(coll.aggregate(pipeline))
    print("Sentiment by topic:")
    for r in res:
        print(r)


def sentiment_by_time(window_days=7):
    db = get_db()
    coll = db[COLLECTION_NAME]
    since = datetime.utcnow() - timedelta(days=window_days)
    pipeline = [
        {"$match": {"timestamp": {"$gte": since}}},
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, "avgSentiment": {"$avg": "$sentiment_score"}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    res = list(coll.aggregate(pipeline))
    print(f"Sentiment by day (last {window_days} days):")
    for r in res:
        print(r)


def run_all():
    sentiment_by_channel()
    sentiment_by_topic()
    sentiment_by_time()

if __name__ == '__main__':
    run_all()
