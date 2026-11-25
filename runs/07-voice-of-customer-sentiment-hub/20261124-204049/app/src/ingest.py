import os
import asyncio
from typing import Dict, Any, List
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from .models import Feedback
from .db import init_db, get_client

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# Simple prompt for extraction. In production tune prompt and handle errors/ratelimits.
EXTRACTION_PROMPT = (
    "Extract a JSON object with keys: sentiment (number -1..1), topics (array of short tags), "
    "quote (a short verbatim quote from the text). Only return the JSON. Text:\n\n" )

async def enrich_and_store(raw: Dict[str, Any]):
    """Given a raw feedback dict with keys 'channel', 'text', optional 'source_id', enrich and store."""
    client = await get_client()
    # Initialize embeddings and LLM
    llm = ChatOpenAI(model_name=LLM_MODEL, openai_api_key=OPENAI_API_KEY, temperature=0)
    embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL, client=None, openai_api_key=OPENAI_API_KEY)

    text = raw["text"]
    prompt = EXTRACTION_PROMPT + text
    try:
        resp = llm.generate([{"text": prompt}])
        # LangChain's ChatOpenAI generate API returns a complex object; fall back to simple call if needed
        # Attempt to extract content
        content = resp.generations[0][0].text if hasattr(resp, 'generations') else str(resp)
    except Exception as e:
        content = '{}'
    # naive JSON extraction
    import json
    try:
        j = json.loads(content)
    except Exception:
        j = {"sentiment": None, "topics": [], "quote": None}

    # embeddings
    try:
        emb = embedder.embed_documents([text])[0]
    except Exception:
        emb = None

    doc = Feedback(
        channel=raw.get("channel", "unknown"),
        source_id=raw.get("source_id"),
        text=text,
        sentiment=j.get("sentiment"),
        topics=j.get("topics"),
        quote=j.get("quote"),
        embedding=emb
    )
    await doc.insert()
    return doc

async def create_search_indexes(db):
    """Attempt to create search indexes (vector + text) using createSearchIndexes command.
    Falls back to a normal create_index for text if search command isn't supported."""
    coll = db.get_collection("feedback")
    try:
        # Vector index example for DocumentDB (best-effort). The exact format may vary by cluster.
        idx_body = {
            "createSearchIndexes": "feedback",
            "indexes": [
                {
                    "name": "embedding_vector_hnsw",
                    "type": "vector-hnsw",
                    "source": "feedback",
                    "fields": [
                        {"path": "embedding", "type": "vector", "dimensions": int(os.getenv('EMBEDDING_DIM', '1536')), "similarity": "COS"}
                    ]
                },
                {
                    "name": "text_search",
                    "type": "text",
                    "source": "feedback",
                    "fields": [
                        {"path": "text", "type": "text"},
                        {"path": "topics", "type": "text"}
                    ]
                }
            ]
        }
        await db.command(idx_body)
        return True
    except Exception as e:
        # Fallback: create a simple text index
        try:
            await coll.create_index([("text", "text")])
        except Exception:
            pass
        return False
