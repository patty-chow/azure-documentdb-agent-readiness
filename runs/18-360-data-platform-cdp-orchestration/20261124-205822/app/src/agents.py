import os
import uuid
from typing import Dict, Any, List
from langchain import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from .db import get_db

EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small')
LLM_MODEL = os.environ.get('LLM_MODEL', 'gpt-4o-mini')

# Simple normalizer
def normalize_name(name: str) -> str:
    return ' '.join(name.strip().lower().split())

class IngestAgent:
    def __init__(self):
        self.db = get_db()

    def ingest(self, records: List[Dict[str, Any]]):
        customers = self.db['customers']
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        for r in records:
            r = dict(r)
            r['normalized_name'] = normalize_name(r.get('name',''))
            # upsert by email if available, otherwise create synthetic id
            if 'email' in r and r['email']:
                filter_q = {'email': r['email']}
            else:
                filter_q = {'_id': r.get('_id', str(uuid.uuid4()))}
            # compute embedding for the concatenated profile text
            text = f"{r.get('name','')} {r.get('email','')}"
            emb = embeddings.embed_documents([text])[0]
            # normalize embedding for cosine similarity
            import math
            norm = math.sqrt(sum(x*x for x in emb)) or 1.0
            emb = [x / norm for x in emb]
            r['embedding'] = emb
            r['embedding_model'] = EMBEDDING_MODEL
            r['embedding_dims'] = len(emb)
            r['schemaVersion'] = 1
            customers.update_one(filter_q, {'$set': r}, upsert=True)

class DedupAgent:
    """LLM-assisted dedup: given a list of candidate pairs, ask LLM to decide if they are duplicates
    and produce a merged document."""
    def __init__(self):
        self.db = get_db()
        self.llm = OpenAI(model_name=LLM_MODEL)

    def is_duplicate(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        # Build a small prompt and ask LLM to answer duplicate or not
        prompt = f"Decide if the following two customer profiles are the same person.\nA: {a}\nB: {b}\nAnswer 'YES' or 'NO' and a short reason." 
        resp = self.llm.predict(prompt)
        return resp.strip().upper().startswith('YES')

    def merge(self, a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        # simple merge: prefer non-empty fields, union arrays
        merged = dict(a)
        for k, v in b.items():
            if k in merged and merged[k]:
                continue
            merged[k] = v
        # merge addresses
        a_addr = a.get('addresses', []) or []
        b_addr = b.get('addresses', []) or []
        merged['addresses'] = a_addr + [x for x in b_addr if x not in a_addr]
        return merged

    def run_merging_pass(self):
        customers = list(self.db['customers'].find({}))
        merged_ids = set()
        for i in range(len(customers)):
            if customers[i]['_id'] in merged_ids:
                continue
            for j in range(i+1, len(customers)):
                if customers[j]['_id'] in merged_ids:
                    continue
                if self.is_duplicate(customers[i], customers[j]):
                    m = self.merge(customers[i], customers[j])
                    # upsert merged doc by keeping _id of i
                    self.db['customers'].update_one({'_id': customers[i]['_id']}, {'$set': m})
                    # delete j
                    self.db['customers'].delete_one({'_id': customers[j]['_id']})
                    merged_ids.add(customers[j]['_id'])

class EnrichAgent:
    def __init__(self):
        self.db = get_db()

    def enrich_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        # Append a tiny synthetic firmographics object for demo purposes
        firm = {
            'company_size_bucket': 'small' if profile.get('email','').endswith('@example.com') else 'unknown',
            'industry': 'software' if 'example' in profile.get('email','') else 'other'
        }
        profile['firmographics'] = firm
        self.db['customers'].update_one({'_id': profile['_id']}, {'$set': {'firmographics': firm}})
        return profile

    def run_enrichment_pass(self):
        for p in self.db['customers'].find({}):
            self.enrich_profile(p)
