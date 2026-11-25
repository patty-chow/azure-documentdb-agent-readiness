import os
import uuid
import time
from datetime import datetime
from pymongo import UpdateOne
from langchain import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from .db import get_db

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_DIMS = 1536  # decision: text-embedding-3-small

# Simple normalizer

def normalize_name(name: str) -> str:
    if not name:
        return ""
    return " ".join(part.capitalize() for part in name.strip().replace('\n', ' ').split())


class Pipeline:
    def __init__(self):
        self.db = get_db()
        self.customers = self.db["customers"]
        self.staging = self.db["staging_customers"]
        self.workflows = self.db["workflows"]
        # configure embeddings if key provided
        if OPENAI_API_KEY:
            self.embedder = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            # langchain OpenAI wrapper used here only for embeddings; chat used in dedupe when available
        else:
            self.embedder = None

    def log_workflow_start(self):
        run_id = str(uuid.uuid4())
        now = datetime.utcnow()
        doc = {
            "run_id": run_id,
            "started_at": now,
            "stages": {},
        }
        self.workflows.insert_one(doc)
        return run_id

    def log_workflow_end(self, run_id, updates: dict):
        now = datetime.utcnow()
        self.workflows.update_one({"run_id": run_id}, {"$set": {"finished_at": now, "stages": updates}})

    def ingest(self):
        # Move from staging to customers with normalization and upsert
        ops = []
        for doc in self.staging.find():
            normalized = {
                "email": doc.get("email"),
                "name": doc.get("name"),
                "normalized_name": normalize_name(doc.get("name")),
                "addresses": doc.get("addresses", []),
                "schemaVersion": 1,
            }
            # compute embedding if embedder present
            if self.embedder and doc.get("name"):
                emb = self.embedder.embed_query(doc.get("name"))
                normalized["embedding"] = emb
            ops.append(UpdateOne({"email": normalized["email"]}, {"$set": normalized, "$setOnInsert": {"workflow_history": []}}, upsert=True))
        if ops:
            res = self.customers.bulk_write(ops)
            return {"ingested": res.upserted_count + res.modified_count}
        return {"ingested": 0}

    def dedupe(self):
        # Very small demo: group by email duplicates and also check normalized_name similarity via heuristic or LLM
        merged = 0
        # first, merge exact-email duplicates (should be handled by upsert but we demonstrate merging addresses and firmographics)
        pipeline = [
            {"$group": {"_id": "$email", "ids": {"$push": "$_id"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        groups = list(self.customers.aggregate(pipeline))
        for g in groups:
            ids = g["ids"]
            primary = ids[0]
            others = ids[1:]
            primary_doc = self.customers.find_one({"_id": primary})
            updates = {}
            for oid in others:
                other = self.customers.find_one({"_id": oid})
                # merge addresses
                upd_addresses = primary_doc.get("addresses", []) + [a for a in other.get("addresses", []) if a not in primary_doc.get("addresses", [])]
                primary_doc["addresses"] = upd_addresses
                # merge firmographics
                if not primary_doc.get("firmographics") and other.get("firmographics"):
                    primary_doc["firmographics"] = other.get("firmographics")
                # remove the duplicate
                self.customers.delete_one({"_id": oid})
                merged += 1
            # write merged primary
            self.customers.replace_one({"_id": primary}, primary_doc)
        # second, LLM-assisted fuzzy dedupe on similar normalized_name (fallback to heuristic if no OPENAI_API_KEY)
        if OPENAI_API_KEY:
            # TODO: call LLM to generate match decisions. For demo we keep this simple and skip detailed prompt construction.
            pass
        else:
            # heuristic: merge documents with identical normalized_name
            pipeline = [
                {"$group": {"_id": "$normalized_name", "ids": {"$push": "$_id"}, "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            groups = list(self.customers.aggregate(pipeline))
            for g in groups:
                name = g["_id"]
                ids = g["ids"]
                primary = ids[0]
                for oid in ids[1:]:
                    other = self.customers.find_one({"_id": oid})
                    primary_doc = self.customers.find_one({"_id": primary})
                    primary_doc["addresses"] = primary_doc.get("addresses", []) + [a for a in other.get("addresses", []) if a not in primary_doc.get("addresses", [])]
                    if not primary_doc.get("firmographics") and other.get("firmographics"):
                        primary_doc["firmographics"] = other.get("firmographics")
                    self.customers.delete_one({"_id": oid})
                    merged += 1
                self.customers.replace_one({"_id": primary}, primary_doc)
        return {"merged": merged}

    def enrich(self):
        # Append deterministic firmographic signals based on email domain when missing
        updated = 0
        for c in self.customers.find({"firmographics": {"$exists": False}}):
            email = c.get("email", "")
            domain = email.split("@")[-1] if "@" in email else "unknown"
            firm = {
                "company_size": "small" if domain.endswith(".com") else "micro",
                "industry": "technology" if "example" in domain else "other",
            }
            self.customers.update_one({"_id": c["_id"]}, {"$set": {"firmographics": firm}})
            updated += 1
        return {"enriched": updated}


if __name__ == "__main__":
    p = Pipeline()
    run_id = p.log_workflow_start()
    stages = {}
    stages["ingest"] = p.ingest()
    stages["dedupe"] = p.dedupe()
    stages["enrich"] = p.enrich()
    p.log_workflow_end(run_id, stages)
    print("Run complete", stages)
