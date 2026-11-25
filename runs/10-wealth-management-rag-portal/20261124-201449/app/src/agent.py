"""Simple RAG agent that combines portfolio context with retrieved research and calls an LLM.
It attempts to use LlamaIndex for the query/answer orchestration if available; otherwise it uses direct OpenAI chat calls.
Memory is implemented as a simple per-client conversation history stored on disk (./memory/{client_id}.txt).
"""
import os
import json
from typing import List, Dict
from dotenv import load_dotenv
from src import db

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

try:
    from openai import OpenAI
    _openai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    _openai = None

# Try to import LlamaIndex but be tolerant if it's not installed in the environment.
try:
    from llama_index import GPTSimpleVectorIndex  # type: ignore
    _have_llama_index = True
except Exception:
    _have_llama_index = False

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")
os.makedirs(MEMORY_DIR, exist_ok=True)


def _read_memory(client_id: str) -> str:
    path = os.path.join(MEMORY_DIR, f"{client_id}.txt")
    if not os.path.exists(path):
        return ""
    return open(path, "r").read()


def _append_memory(client_id: str, user_question: str, assistant_answer: str):
    path = os.path.join(MEMORY_DIR, f"{client_id}.txt")
    with open(path, "a") as f:
        f.write("USER: " + user_question + "\n")
        f.write("ASSISTANT: " + assistant_answer + "\n\n")


def answer_question(client_id: str, question: str, top_k: int = 5) -> Dict[str, object]:
    # Fetch portfolio context
    db_conn = db.get_db()
    portfolios = db_conn["portfolios"]
    pf = portfolios.find_one({"client_id": client_id})
    portfolio_text = json.dumps(pf, default=str) if pf else "(no portfolio found)"

    # Create embedding for the question using OpenAI if available; otherwise synthetic
    if _openai:
        emb = _openai.embeddings.create(model=EMBEDDING_MODEL, input=question).data[0].embedding
    else:
        emb = db.generate_synthetic_embedding(question)

    # Retrieve similar research docs
    hits = db.search_similar(emb, k=top_k)

    # Build a context for the LLM: portfolio + retrieved docs
    combined_context = "Portfolio:\n" + portfolio_text + "\n\nRetrieved documents:\n"
    for h in hits:
        combined_context += f"- {h.get('title')} (score={h.get('score')})\n"
        snippet = h.get("content", "")[:500]
        combined_context += snippet + "\n\n"

    # Include memory
    memory = _read_memory(client_id)

    system_prompt = (
        "You are a Relationship Manager assistant. Use the portfolio context and retrieved research to answer concisely."
    )

    user_prompt = (
        f"Conversation history:\n{memory}\nUser question:\n{question}\n\nContext:\n{combined_context}\nAnswer:" 
    )

    # Use LlamaIndex if available -- a very lightweight example that doesn't wire its vector store
    if _have_llama_index:
        # NOTE: For a full LlamaIndex integration we'd implement a custom Retriever that calls db.search_similar.
        # For brevity this sample uses a direct LLM prompt even when llama-index is present.
        pass

    # Call the LLM (OpenAI chat) directly
    if _openai:
        chat_resp = _openai.chat.completions.create(model=CHAT_MODEL, messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ], max_tokens=512)
        answer = chat_resp.choices[0].message.content
    else:
        # Without a real LLM, return a deterministic placeholder answer
        answer = "[Simulated LLM answer] The client appears positioned toward intermediate-duration bonds and selective equities. See retrieved docs for more detail."

    # Persist memory
    _append_memory(client_id, question, answer)

    return {"answer": answer, "retrieved": hits}
