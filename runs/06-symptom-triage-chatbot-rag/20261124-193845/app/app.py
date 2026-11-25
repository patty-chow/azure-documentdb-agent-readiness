import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any
from db import get_client
from utils import get_embedding, generate_response_with_fallback

try:
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage
    _LANGCHAIN_AVAILABLE = True
except Exception:
    _LANGCHAIN_AVAILABLE = False

app = FastAPI(title="Symptom Triage Chatbot (RAG)")

DB_NAME = "sample_healthcare_06"
COLLECTION = "guidelines"

class TriageRequest(BaseModel):
    symptoms: str

class SourceItem(BaseModel):
    section_id: str
    title: str
    snippet: str
    score: float

class TriageResponse(BaseModel):
    urgency: str
    advice: str
    sources: List[SourceItem]


def llm_generate(symptoms: str, contexts: List[dict]):
    """Generate triage advice using LangChain/OpenAI when available, otherwise fallback to deterministic generator.
    The returned value is a dict with keys urgency, advice, sources.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key and _LANGCHAIN_AVAILABLE:
        # Build a careful prompt enforcing guardrails
        system_prompt = (
            "You are a clinical triage assistant used for educational scenarios. Do NOT provide medical diagnoses. "
            "Always recommend the user consult a qualified healthcare professional for medical advice. If symptoms are life-threatening, advise seeking emergency care. "
            "Return a JSON object with fields: urgency (one of low, urgent, emergency), advice (brief text), and sources (array of {section_id,title,snippet,score})."
        )
        context_text = "\n\n".join([f"[{c['section_id']}] {c['title']}: {c['text']}" for c in contexts])
        user_prompt = (
            f"Context docs:\n{context_text}\n\nUser symptoms: {symptoms}\n\nProvide the JSON response as specified."
        )
        chat = ChatOpenAI(model_name=os.environ.get("LLM_MODEL", "gpt-3.5-turbo"), openai_api_key=api_key, temperature=0.0)
        resp = chat([HumanMessage(content=system_prompt + "\n\n" + user_prompt)])
        # Attempt to parse JSON from the model output
        import json
        try:
            parsed = json.loads(resp.content)
            return parsed
        except Exception:
            # Fallback to deterministic generator on parse error
            return generate_response_with_fallback(symptoms, contexts)
    else:
        return generate_response_with_fallback(symptoms, contexts)


@app.post("/triage", response_model=TriageResponse)
def triage(req: TriageRequest):
    symptoms = req.symptoms
    if not symptoms or not symptoms.strip():
        raise HTTPException(status_code=400, detail="symptoms text is required")

    client = get_client()
    coll = client[DB_NAME][COLLECTION]

    qv = get_embedding(symptoms)

    pipeline = [
        {
            "$search": {
                "cosmosSearch": {
                    "path": "embedding",
                    "vector": qv,
                    "k": 5,
                    "lSearch": 100
                }
            }
        },
        {
            "$project": {
                "section_id": 1,
                "title": 1,
                "text": 1,
                "documented_urgency": 1,
                "score": {"$meta": "searchScore"}
            }
        }
    ]

    try:
        hits = list(coll.aggregate(pipeline))
    except Exception as e:
        # If the server does not support $search/cosmosSearch, return an error
        raise HTTPException(status_code=500, detail=f"Vector search failed: {e}")

    contexts = []
    for h in hits:
        contexts.append({
            "section_id": h.get("section_id"),
            "title": h.get("title"),
            "text": h.get("text"),
            "documented_urgency": h.get("documented_urgency"),
            "score": h.get("score", 0.0)
        })

    result = llm_generate(symptoms, contexts)

    # Coerce into response model shape
    sources = [SourceItem(**s) for s in result.get("sources", [])]
    return TriageResponse(urgency=result.get("urgency", "low"), advice=result.get("advice", ""), sources=sources)
