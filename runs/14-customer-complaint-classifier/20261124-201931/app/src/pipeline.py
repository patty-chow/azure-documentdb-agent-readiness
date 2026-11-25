import os
import asyncio
from typing import List
from datetime import datetime
from beanie import PydanticObjectId
from .models import Complaint, ClassificationMetadata
from .db import init_db, get_client
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

# Simple prompt template for classification
PROMPT = """
You are a helpful assistant. Classify the following customer complaint into:
- product_category (one of: 'card', 'deposit', 'loan', 'online_banking', 'other')
- root_cause (brief phrase)
- urgency (one of: 'low', 'medium', 'high')

Complaint:
{complaint}

Return a JSON object with keys: product_category, root_cause, urgency.
"""

async def _init_llm_chain():
    # Lazy import to avoid heavy deps during unit tests
    from langchain.llms import OpenAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain

    prompt = PromptTemplate(input_variables=["complaint"], template=PROMPT)
    llm = OpenAI(openai_api_key=OPENAI_API_KEY, model_name=LLM_MODEL, temperature=0)
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain

async def _get_openai_client():
    from openai import OpenAI as OpenAIClient
    return OpenAIClient(api_key=OPENAI_API_KEY)

async def embed_text(text: str) -> List[float]:
    openai_client = await _get_openai_client()
    resp = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding

async def classify_and_store(limit: int = 50) -> int:
    await init_db()
    # find unclassified complaints
    docs = await Complaint.find(Complaint.product_category == None).limit(limit).to_list()
    updated = 0
    if not docs:
        return 0
    chain = await _init_llm_chain()
    for doc in docs:
        # call LLM
        out = chain.run(complaint=doc.complaint_text)
        try:
            import json
            parsed = json.loads(out)
            product_category = parsed.get("product_category")
            root_cause = parsed.get("root_cause")
            urgency = parsed.get("urgency")
        except Exception:
            # fallback: naive rules
            product_category = "other"
            root_cause = "classification_failed"
            urgency = "low"
        emb = await embed_text(doc.complaint_text)
        doc.product_category = product_category
        doc.root_cause = root_cause
        doc.urgency = urgency
        doc.embedding = emb
        doc.embedding_dimensions = len(emb) if emb else None
        doc.classification_metadata = ClassificationMetadata(model=LLM_MODEL, timestamp=datetime.utcnow())
        await doc.save()
        updated += 1
    return updated

# A synchronous wrapper for CLI
def run_classify(limit: int = 50):
    return asyncio.run(classify_and_store(limit))
