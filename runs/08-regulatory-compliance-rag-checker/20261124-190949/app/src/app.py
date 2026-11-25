"""
Simple CLI + small FastAPI app that performs analysis on a policy excerpt.
- Computes embedding for the input
- Finds top-k regulatory clauses by brute-force cosine similarity
- Calls OpenAI ChatCompletion to produce a compliance gap report using context engineering
"""
import os
import argparse
from dotenv import load_dotenv
from src.db import get_db
import openai
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
EMBED_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.environ.get("OPENAI_LLM_MODEL", "gpt-3.5-turbo")
DB_NAME = os.environ.get("DB_NAME", "sample_fintech_08")

app = FastAPI()

class AnalyzeRequest(BaseModel):
    excerpt: str
    top_k: int = 3


def embed_text(text: str):
    resp = openai.Embedding.create(model=EMBED_MODEL, input=text)
    vec = resp["data"][0]["embedding"]
    arr = np.array(vec, dtype=float)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr.tolist()


def cosine_similarity(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def retrieve_top_regulatory(excerpt_embedding, top_k=3):
    db = get_db()
    reg_coll = db["regulatory"]
    # small dataset: fetch all and compute similarity client-side
    docs = list(reg_coll.find({}, {"_id": 1, "title": 1, "source": 1, "section": 1, "content": 1, "embedding": 1}))
    scored = []
    for d in docs:
        emb = d.get("embedding")
        if emb:
            score = cosine_similarity(excerpt_embedding, emb)
            scored.append((score, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [ {"score": s, "doc": doc} for s, doc in scored[:top_k] ]


def build_prompt(excerpt, retrieved):
    # Context-engineered prompt: include the policy excerpt and the top regulatory clauses
    prompt = "You are a compliance analyst. Compare the following internal policy excerpt to the listed regulatory clauses and produce a compliance gap report. For each regulatory clause, state whether the policy meets it, partially meets it, or does not meet it. Provide a short remediation suggestion if there is a gap.\n\n"
    prompt += "Policy excerpt:\n" + excerpt + "\n\n"
    prompt += "Regulatory clauses (top matches):\n"
    for i, r in enumerate(retrieved, start=1):
        doc = r["doc"]
        prompt += f"{i}. {doc.get('source','') } {doc.get('section','') } - {doc.get('title','')}\n"
        prompt += doc.get("content","") + "\n---\n"
    prompt += "\nPlease output a JSON object with fields: verdict (Compliant|Partial|Non-compliant), details: array of {regulatory_id, title, verdict, confidence, remediations}"
    return prompt


def call_llm(prompt):
    # Simple ChatCompletion call
    messages = [
        {"role": "system", "content": "You are a helpful compliance analyst that outputs structured JSON when asked."},
        {"role": "user", "content": prompt},
    ]
    resp = openai.ChatCompletion.create(model=LLM_MODEL, messages=messages, temperature=0.0)
    return resp["choices"][0]["message"]["content"]


def analyze_excerpt(excerpt: str, top_k: int = 3):
    emb = embed_text(excerpt)
    retrieved = retrieve_top_regulatory(emb, top_k=top_k)
    prompt = build_prompt(excerpt, retrieved)
    llm_out = call_llm(prompt)
    return {
        "retrieved": retrieved,
        "report": llm_out,
    }

@app.post("/analyze")
def analyze_api(req: AnalyzeRequest):
    try:
        return analyze_excerpt(req.excerpt, top_k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyze", help="Policy excerpt to analyze", type=str)
    parser.add_argument("--top-k", help="Number of top regulatory clauses to retrieve", type=int, default=3)
    args = parser.parse_args()
    if args.analyze:
        out = analyze_excerpt(args.analyze, top_k=args.top_k)
        print("Retrieved:")
        for r in out["retrieved"]:
            print(f"- {r['doc']['_id']} (score={r['score']:.4f}): {r['doc']['title']}")
        print("\nLLM report:\n")
        print(out["report"])
    else:
        print("Run with --analyze \"Your policy excerpt\"")
