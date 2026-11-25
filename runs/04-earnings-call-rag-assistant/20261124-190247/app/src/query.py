import argparse
import os
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from db import get_db

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION = "earnings_chunks"

try:
    import openai
    openai.api_key = OPENAI_KEY
except Exception:
    openai = None


def embed_text(text: str, model_name=EMBED_MODEL):
    model = SentenceTransformer(model_name)
    emb = model.encode(text, normalize_embeddings=True).astype(float)
    return emb


def retrieve_local(query: str, k=3):
    emb = embed_text(query)
    db = get_db()
    coll = db[COLLECTION]
    docs = list(coll.find({"embedding_model": EMBED_MODEL}, {"text":1,"source":1,"start_time":1,"embedding":1}))
    if not docs:
        print("No documents found in collection. Run ingest first.")
        return []
    scores = []
    for d in docs:
        vec = np.array(d.get("embedding"), dtype=float)
        # cosine similarity because embeddings are normalized
        score = float(np.dot(emb, vec) / (np.linalg.norm(emb) * np.linalg.norm(vec) + 1e-12))
        scores.append((score, d))
    scores.sort(key=lambda x: x[0], reverse=True)
    return scores[:k]


def synthesize_answer_naive(passages: List[dict], query: str):
    # If OpenAI is configured, call it to synthesize an answer; otherwise concatenate
    if OPENAI_KEY and openai is not None:
        context = "\n\n".join([f"Source: {p['source']}[{p.get('start_time',0)}]\\n{p['text']}" for p in passages])
        prompt = f"You are an analyst assistant. Use the context below to answer the question concisely and cite sources.\n\nCONTEXT:\n{context}\n\nQUESTION: {query}\n\nAnswer:" 
        resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=300, temperature=0)
        return resp.choices[0].text.strip()
    else:
        # fallback: join passages and echo
        out = "Answer (fallback):\n"
        out += "\n\n".join([f"[{i+1}] {p['source']} (t={p.get('start_time',0)}): {p['text']}" for i,p in enumerate(passages)])
        return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help="Analyst question")
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()

    results = retrieve_local(args.query, k=args.k)
    passages = []
    for score, d in results:
        passages.append({"score": score, "text": d['text'], "source": d.get('source'), "start_time": d.get('start_time')})
    if not passages:
        print("No passages retrieved.")
    else:
        answer = synthesize_answer_naive(passages, args.query)
        print("\n=== Retrieved passages ===\n")
        for p in passages:
            print(f"score={p['score']:.4f} source={p['source']} t={p['start_time']}\n{p['text']}\n---")
        print("\n=== Answer ===\n")
        print(answer)
