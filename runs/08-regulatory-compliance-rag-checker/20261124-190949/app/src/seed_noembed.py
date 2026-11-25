"""
Seed sample documents without computing embeddings. Use when OPENAI_API_KEY is not available.
"""
import os
from dotenv import load_dotenv
from src.db import get_db
load_dotenv()

REG_DOCS = [
    {
        "_id": "reg-1",
        "title": "PCI Requirement: MFA for Remote Admin",
        "source": "PCI-DSS",
        "section": "8.3",
        "content": "All remote administrative access to cardholder data environments must be protected with multi-factor authentication.",
    },
    {
        "_id": "reg-2",
        "title": "GDPR Personal Data Access",
        "source": "GDPR",
        "section": "15",
        "content": "Data subjects must be able to request access to their personal data and the controller must provide a copy of the data upon request within one month.",
    },
    {
        "_id": "reg-3",
        "title": "SOX Financial Controls",
        "source": "SOX",
        "section": "302",
        "content": "Company officers must certify the accuracy of financial reports and maintain internal controls to ensure completeness and accuracy.",
    },
]

POLICY_DOCS = [
    {
        "_id": "pol-1",
        "title": "Admin Access Policy",
        "owner": "IT Security",
        "content": "Administrators must use strong passwords and rotate them every 90 days. Remote administrative access is allowed without additional factors.",
    },
    {
        "_id": "pol-2",
        "title": "Data Subject Requests",
        "owner": "Privacy Office",
        "content": "Employees must escalate data access requests to the Privacy Office. The Privacy Office aims to respond within 45 days.",
    },
]

if __name__ == "__main__":
    db = get_db()
    reg_coll = db["regulatory"]
    pol_coll = db["internal_policies"]
    for d in REG_DOCS:
        d["embedding"] = None
        d["embedding_model"] = os.environ.get("OPENAI_EMBEDDING_MODEL")
        d["embedding_dims"] = 0
        reg_coll.update_one({"_id": d["_id"]}, {"$set": d}, upsert=True)
    for d in POLICY_DOCS:
        d["embedding"] = None
        d["embedding_model"] = os.environ.get("OPENAI_EMBEDDING_MODEL")
        d["embedding_dims"] = 0
        pol_coll.update_one({"_id": d["_id"]}, {"$set": d}, upsert=True)
    # text index
    reg_coll.create_index([("content", "text")], name="content_text_idx")
    pol_coll.create_index([("content", "text")], name="content_text_idx")
    print("Seeded documents without embeddings")
