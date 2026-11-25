"""Run aggregation queries against the survey_responses collection and print results."""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_customer_360_17")

if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI must be set in environment (.env)")

client = MongoClient(DOCUMENTDB_URI)
db = client[DATABASE_NAME]
col = db["survey_responses"]

# Top themes per question: unwind themes and count
pipeline_themes = [
    {"$unwind": {"path": "$themes", "preserveNullAndEmptyArrays": False}},
    {"$group": {"_id": {"question_id": "$question_id", "theme": "$themes"}, "count": {"$sum": 1}}},
    {"$sort": {"_id.question_id": 1, "count": -1}},
    {"$group": {"_id": "$_id.question_id", "top": {"$push": {"theme": "$_id.theme", "count": "$count"}}}},
    {"$project": {"question_id": "$_id", "top": {"$slice": ["$top", 5]}, "_id": 0}}
]

print("Top themes per question:")
for doc in col.aggregate(pipeline_themes):
    print(doc)

# Sentiment distribution per question
pipeline_sentiment = [
    {"$group": {"_id": {"question_id": "$question_id", "sentiment": "$sentiment.label"}, "count": {"$sum": 1}}},
    {"$group": {"_id": "$_id.question_id", "distribution": {"$push": {"sentiment": "$_id.sentiment", "count": "$count"}}}},
    {"$project": {"question_id": "$_id", "distribution": 1, "_id": 0}}
]

print("\nSentiment distribution per question:")
for doc in col.aggregate(pipeline_sentiment):
    print(doc)

client.close()
