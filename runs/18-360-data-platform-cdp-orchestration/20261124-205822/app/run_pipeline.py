"""Run the ingest -> dedup -> enrich pipeline once.
"""
import os
import time
import uuid
from datetime import datetime
from pymongo import ReturnDocument
from dotenv import load_dotenv

import src.db as db_module
from src.models import CustomerRecord

load_dotenv()

# optional OpenAI/LangChain imports
USE_LLM = bool(os.environ.get("OPENAI_API_KEY"))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "1536"))

if USE_LLM:
    try:
        from langchain.chat_models import ChatOpenAI
        from langchain.embeddings import OpenAIEmbeddings
    except Exception as e:
        print("LangChain not available or failed to import:", e)
        USE_LLM = False


class Pipeline:
    def __init__(self):
        self.db = db_module.get_db()
        self.customers = self.db["customers"]
        self.incoming = self.db["incoming"]
        self.workflows = self.db["workflows"]
        if USE_LLM:
            self.chat = ChatOpenAI(temperature=float(os.environ.get("LLM_TEMPERATURE", "0.0")))
            self.embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    def log_workflow(self, run_id, stage, info=None):
        self.workflows.update_one({"run_id": run_id}, {"$set": {"run_id": run_id, "last_stage": stage, "updated_at": datetime.utcnow()}, "$push": {"stages": {"stage": stage, "timestamp": datetime.utcnow(), "info": info or {}}}}, upsert=True)

    def ingest(self):
        # Read incoming and normalize + upsert into customers collection
        inserted = 0
        for doc in self.incoming.find():
            email = doc.get("email")
            name = doc.get("name", "")
            normalized = name.strip().lower()
            now = datetime.utcnow()
            update = {"$set": {"email": email, "name": name, "normalized_name": normalized, "updated_at": now}, "$setOnInsert": {"created_at": now, "schemaVersion": 1}}
            self.customers.update_one({"email": email}, update, upsert=True)
            inserted += 1
        return {"ingested": inserted}

    def dedup(self):
        # Very small demo: look for customers with identical normalized_name and run LLM matching
        counts = 0
        names = self.customers.aggregate([
            {"$group": {"_id": "$normalized_name", "ids": {"$push": "$_id"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ])
        for group in names:
            ids = group["ids"]
            if len(ids) < 2:
                continue
            # fetch docs
            docs = list(self.customers.find({"_id": {"$in": ids}}))
            # pairwise compare using LLM if available, otherwise simple heuristic
            keep = docs[0]
            merged = keep.copy()
            for other in docs[1:]:
                is_dup = False
                if USE_LLM:
                    # ask LLM if they are the same person
                    prompt = f"Are these two customer profiles duplicates? Answer yes or no. ProfileA: {keep}. ProfileB: {other}"
                    resp = self.chat.predict(prompt)
                    if "yes" in resp.lower():
                        is_dup = True
                else:
                    # heuristic: same email local-part or same city
                    if keep.get("email") and other.get("email") and keep.get("email").split("@")[0] == other.get("email").split("@")[0]:
                        is_dup = True
                if is_dup:
                    # merge addresses and firmographics
                    merged_addresses = merged.get("addresses", []) + other.get("addresses", [])
                    merged["addresses"] = merged_addresses
                    merged["firmographics"] = {**merged.get("firmographics", {}), **other.get("firmographics", {})}
                    # remove the other doc
                    self.customers.delete_one({"_id": other["_id"]})
                    counts += 1
            # update the kept doc
            self.customers.replace_one({"_id": merged["_id"]}, merged, upsert=True)
        return {"merged": counts}

    def enrich(self):
        # For records without firmographics, call the embedder (to store embedding) and use LLM to generate sample firmographics
        updated = 0
        for doc in self.customers.find({}):
            if not doc.get("firmographics"):
                firm = {"industry": "Unknown", "company_size": "Unknown"}
                if USE_LLM:
                    prompt = f"Given this customer profile, suggest a plausible firmographic object (json) with fields industry and company_size: {doc}"
                    resp = self.chat.predict(prompt)
                    # naive parse: try to find JSON in response
                    try:
                        import json as _json
                        parsed = _json.loads(resp)
                        firm = parsed
                    except Exception:
                        # fallback heuristic
                        firm = {"industry": "Technology", "company_size": "1-50"}
                # compute embedding if possible
                embedding = []
                if USE_LLM:
                    text = (doc.get("name","") + " " + doc.get("email",""))
                    embedding = self.embedder.embed_query(text)
                self.customers.update_one({"_id": doc["_id"]}, {"$set": {"firmographics": firm, "embedding": embedding, "updated_at": datetime.utcnow()}})
                updated += 1
        return {"enriched": updated}

    def run(self):
        run_id = str(uuid.uuid4())
        start = datetime.utcnow()
        self.workflows.insert_one({"run_id": run_id, "start": start, "stages": [], "status": "running"})
        try:
            self.log_workflow(run_id, "ingest", self.ingest())
            self.log_workflow(run_id, "dedup", self.dedup())
            self.log_workflow(run_id, "enrich", self.enrich())
            self.workflows.update_one({"run_id": run_id}, {"$set": {"status": "succeeded", "end": datetime.utcnow()}})
        except Exception as e:
            self.workflows.update_one({"run_id": run_id}, {"$set": {"status": "failed", "error": str(e), "end": datetime.utcnow()}})
            raise
        return run_id


if __name__ == "__main__":
    p = Pipeline()
    rid = p.run()
    print("Workflow run recorded with id:", rid)
