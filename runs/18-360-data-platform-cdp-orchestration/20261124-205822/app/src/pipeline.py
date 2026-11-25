import os
import time
import uuid
from typing import List, Dict, Any, Optional
from pymongo import ASCENDING, IndexModel
from dotenv import load_dotenv

from .db import get_database
from .utils import normalize_name, deterministic_embedding, name_similarity

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
EMBED_DIM = 1536  # default embedding dims for text-embedding-3-small


class IngestAgent:
    def __init__(self, db):
        self.db = db
        self.customers = db.get_collection("customers")
        # ensure unique email index
        self.customers.create_index([("email", ASCENDING)], unique=False)

    def normalize_and_upsert(self, records: List[Dict[str, Any]]):
        ops = []
        for r in records:
            r = r.copy()
            r["normalized_name"] = normalize_name(r.get("name"))
            r.setdefault("schemaVersion", 1)
            # compute a placeholder embedding if not provided (real embedding happens later)
            if "embedding" not in r:
                r["embedding"] = None
            # use email for id if exists
            if r.get("email"):
                filter_q = {"email": r["email"]}
            else:
                if "_id" in r:
                    filter_q = {"_id": r["_id"]}
                else:
                    r["_id"] = str(uuid.uuid4())
                    filter_q = {"_id": r["_id"]}
            self.customers.update_one(filter_q, {"$set": r}, upsert=True)


class DedupAgent:
    def __init__(self, db, embeddings_fn=None, llm_fn=None):
        self.db = db
        self.customers = db.get_collection("customers")
        self.embeddings_fn = embeddings_fn
        self.llm_fn = llm_fn

    def find_potential_duplicates(self, threshold: float = 0.6) -> List[List[Dict[str, Any]]]:
        # naive approach: group by similar normalized_name using a windowed scan
        docs = list(self.customers.find({}))
        groups = []
        seen = set()
        for i, doc in enumerate(docs):
            if doc.get("_id") in seen:
                continue
            group = [doc]
            for j in range(i+1, len(docs)):
                other = docs[j]
                if other.get("_id") in seen:
                    continue
                # quick email exact match
                if doc.get("email") and other.get("email") and doc.get("email") == other.get("email"):
                    group.append(other)
                    seen.add(other.get("_id"))
                    continue
                sim = name_similarity(doc.get("normalized_name"), other.get("normalized_name"))
                if sim >= threshold:
                    group.append(other)
                    seen.add(other.get("_id"))
            if len(group) > 1:
                groups.append(group)
        return groups

    def llm_decide_and_merge(self, groups: List[List[Dict[str, Any]]]):
        merged_count = 0
        for group in groups:
            # Ask LLM whether to merge and how. If not available, merge by simple rules.
            if self.llm_fn:
                try:
                    decision = self.llm_fn(group)
                except Exception:
                    decision = None
            else:
                decision = None

            if decision is None:
                # fallback merge: pick the doc with most filled fields as canonical
                canonical = max(group, key=lambda d: len([k for k,v in d.items() if v]))
                for d in group:
                    if d["_id"] == canonical["_id"]:
                        continue
                    # merge non-null fields into canonical
                    for k, v in d.items():
                        if k not in canonical or not canonical.get(k):
                            canonical[k] = v
                    self.customers.delete_one({"_id": d["_id"]})
                # upsert canonical
                self.customers.update_one({"_id": canonical["_id"]}, {"$set": canonical}, upsert=True)
                merged_count += len(group)-1
            else:
                # If LLM returned a canonical doc, apply it
                canonical = decision.get("canonical")
                to_remove = decision.get("remove_ids", [])
                self.customers.update_one({"_id": canonical["_id"]}, {"$set": canonical}, upsert=True)
                for rid in to_remove:
                    self.customers.delete_one({"_id": rid})
                merged_count += len(to_remove)
        return merged_count


class EnrichAgent:
    def __init__(self, db, enrichment_provider=None):
        self.db = db
        self.customers = db.get_collection("customers")
        self.enrichment_provider = enrichment_provider

    def enrich(self, batch_size: int = 100) -> int:
        updated = 0
        cursor = self.customers.find({})
        for doc in cursor:
            # Skip if already enriched with firmographics
            if doc.get("firmographics"):
                continue
            if self.enrichment_provider:
                signals = self.enrichment_provider(doc)
            else:
                # synthetic enrichment: domain-based firmographic cues from email
                signals = {
                    "company_size": "small",
                    "industry": "unknown"
                }
                email = doc.get("email") or ""
                if "@" in email:
                    domain = email.split("@")[-1]
                    if domain.endswith("example.com"):
                        signals["company_size"] = "enterprise"
                        signals["industry"] = "technology"
            self.customers.update_one({"_id": doc["_id"]}, {"$set": {"firmographics": signals}})
            updated += 1
        return updated


class Orchestrator:
    def __init__(self, db, embeddings_fn=None, llm_fn=None, enrichment_provider=None):
        self.db = db
        self.customers = db.get_collection("customers")
        self.workflows = db.get_collection("workflows")
        self.ingest = IngestAgent(db)
        self.dedup = DedupAgent(db, embeddings_fn=embeddings_fn, llm_fn=llm_fn)
        self.enrich = EnrichAgent(db, enrichment_provider=enrichment_provider)

    def run_batch(self, records: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        started_at = time.time()
        stages = {}
        # Stage: ingest
        if records:
            self.ingest.normalize_and_upsert(records)
        stages["ingest"] = {"status": "done"}

        # Stage: dedupe
        groups = self.dedup.find_potential_duplicates()
        merged = self.dedup.llm_decide_and_merge(groups)
        stages["dedupe"] = {"status": "done", "merged": merged}

        # Stage: enrich
        enriched = self.enrich.enrich()
        stages["enrich"] = {"status": "done", "updated": enriched}

        finished_at = time.time()
        doc = {
            "_id": run_id,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": finished_at - started_at,
            "stages": stages,
        }
        self.workflows.insert_one(doc)
        return doc
