"""Run aggregation pipeline to compute composite ESG score and rank companies.

Run as: python -m sample.aggregate
"""
from .db import get_db
from .config import COLLECTION_NAME


def aggregate_top(n=10):
    db = get_db()
    col = db[COLLECTION_NAME]
    pipeline = [
        {"$match": {"score_E": {"$exists": True}, "score_S": {"$exists": True}, "score_G": {"$exists": True}}},
        {"$addFields": {"composite": {"$avg": ["$score_E", "$score_S", "$score_G"]}}},
        {"$sort": {"composite": -1}},
        {"$limit": n},
        {"$project": {"name": 1, "score_E": 1, "score_S": 1, "score_G": 1, "composite": 1}}
    ]
    return list(col.aggregate(pipeline))


if __name__ == "__main__":
    top = aggregate_top(20)
    print("Top companies by composite ESG score:")
    for doc in top:
        print(f"{doc['name']}: E={doc['score_E']} S={doc['score_S']} G={doc['score_G']} composite={doc['composite']:.2f}")
