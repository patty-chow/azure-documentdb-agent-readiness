from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.db import get_db
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Branch Performance Analytics")

class AskRequest(BaseModel):
    query: str

# endpoints
@app.get("/metrics/branches/{branch_id}")
def get_branch_metrics(branch_id: str):
    db = get_db()
    doc = db.branch_summaries.find_one({"branchId": branch_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Branch summary not found")
    # remove _id for JSON friendliness
    doc["id"] = str(doc.pop("_id"))
    return doc

@app.post("/summaries/refresh")
def refresh_summaries():
    # Trigger recompute — delegate to same logic as scripts/refresh_summaries.py
    from scripts.refresh_summaries import compute_and_store_summaries
    count = compute_and_store_summaries()
    return {"refreshed_branches": count}

@app.post("/ask")
def ask(request: AskRequest):
    # Simple lexical retrieval of summaries and forwarding to OpenAI chat
    query = request.query
    db = get_db()
    # naive retrieval: regex match on summaryText or branch name
    cursor = db.branch_summaries.find({"summaryText": {"$regex": query, "$options": "i"}}).limit(5)
    hits = list(cursor)
    if not hits:
        # fallback: return top N by totalVolume
        hits = list(db.branch_summaries.find().sort("totalVolume", -1).limit(3))
    # Compose context
    contexts = []
    branches = []
    for h in hits:
        branches.append(h.get("branchId"))
        contexts.append(f"Branch {h.get('branchId')}: totalVolume={h.get('totalVolume')}, avgTicket={h.get('avgTicket')}, productMix={h.get('productMix')}")
    context_text = "\n".join(contexts)

    # call OpenAI if available
    import openai
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        return {"answer": "OpenAI API key not configured. Install OPENAI_API_KEY to enable LLM answers.", "matched_branches": branches}
    openai.api_key = openai_key
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    prompt = f"You are an analyst. Use the branch performance context below to answer the question.\nContext:\n{context_text}\nQuestion: {query}\nAnswer concisely and list which branch(es) you used."
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role":"user", "content": prompt}],
            max_tokens=256,
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        answer = f"LLM call failed: {e}"
    return {"answer": answer, "matched_branches": branches}
