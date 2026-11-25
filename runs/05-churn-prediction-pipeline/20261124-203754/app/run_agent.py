"""
Simple CLI to retrieve nearest churned customer profiles for a given customer_id and produce a narrative via an LLM (if configured).
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import argparse
import os
from src.db import get_db
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")


def find_neighbors(customer_id: str, k: int = 5):
    db = get_db()
    cust_coll = db["customers"]
    cust = cust_coll.find_one({"_id": customer_id})
    if not cust:
        print("Customer not found")
        return
    print("Customer RFM:", cust.get("rfm"))
    embedding = cust.get("rfm_embedding")
    if not embedding:
        print("No embedding present for customer. Compute embeddings first.")
        return
    # Use a $search knn if available
    pipeline = [
        {"$search": {"knn": {"vector": embedding, "path": "rfm_embedding", "k": k}}},
        {"$match": {"churn": True}},
        {"$limit": k},
        {"$project": {"_id": 1, "rfm": 1, "churn": 1}}
    ]
    try:
        res = list(cust_coll.aggregate(pipeline))
        print(f"Found {len(res)} neighbors (churned):")
        for r in res:
            print(r)
        return res
    except Exception as e:
        print("Error running vector search (maybe not supported in your cluster or index missing):", e)
        return []


def generate_narrative(customer, neighbors):
    # Minimal templating using an LLM if configured; otherwise echo a template
    if not OPENAI_API_KEY:
        print("No OPENAI_API_KEY found; skipping LLM narrative generation. Provide OPENAI_API_KEY for end-to-end demo.")
        return {
            "narrative": "LLM not configured. Provide OPENAI_API_KEY to enable narrative generation.",
            "action": "Offer a small discount and personalized outreach."
        }
    # Use a very small call via OpenAI directly to avoid heavy LangChain wiring in the sample
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        prompt = f"Given the customer RFM: {customer.get('rfm')} and {len(neighbors)} churned neighbor profiles, provide a short churn-risk narrative (2-3 sentences) and one recommended retention action. Output JSON with keys narrative and action." 
        resp = openai.ChatCompletion.create(model=LLM_MODEL, messages=[{"role":"user","content":prompt}], max_tokens=200)
        msg = resp["choices"][0]["message"]["content"]
        return {"narrative": msg, "action": "see narrative"}
    except Exception as e:
        print("LLM call failed:", e)
        return {"narrative": "LLM call failed", "action": "LLM error"}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--customer-id", required=True)
    p.add_argument("--k", type=int, default=5)
    args = p.parse_args()
    neighbors = find_neighbors(args.customer_id, args.k)
    if neighbors:
        db = get_db()
        cust = db["customers"].find_one({"_id": args.customer_id})
        out = generate_narrative(cust, neighbors)
        print("Narrative:", out)
