from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from src.db import get_db
import openai
from typing import List

load_dotenv()
OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
OPENAI_LLM_MODEL = os.getenv('OPENAI_LLM_MODEL', 'gpt-3.5-turbo')
openai.api_key = os.getenv('OPENAI_API_KEY')

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    k: int = 5

class Citation(BaseModel):
    pmid: str
    year: str | None
    chunk_id: str
    text: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]


@app.post('/query', response_model=QueryResponse)
async def query(req: QueryRequest):
    # 1) embed the query
    emb_resp = openai.Embedding.create(model=OPENAI_EMBEDDING_MODEL, input=[req.query])
    qvec = emb_resp['data'][0]['embedding']

    # 2) run a $search with cosmosSearch knn
    db = get_db()
    coll = db['pubmed_chunks']
    pipeline = [
        {
            '$search': {
                'cosmosSearch': {
                    'knn': {
                        'vector': qvec,
                        'path': 'embedding',
                        'k': req.k,
                        'space': 'COS'
                    }
                }
            }
        },
        {'$project': {'pmid': 1, 'year': 1, 'chunk_id': 1, 'text': 1, 'score': {'$meta': 'searchScore'}}}
    ]
    res = list(coll.aggregate(pipeline))
    citations = []
    for r in res:
        citations.append(Citation(pmid=r.get('pmid'), year=r.get('year'), chunk_id=r.get('chunk_id'), text=r.get('text'), score=float(r.get('score', 0))))

    # 3) compose a prompt and call the LLM to generate an answer
    context = '\n\n'.join([f"PMID: {c.pmid} ({c.year})\n{c.text}" for c in citations])
    system = "You are an assistant that answers researcher questions using provided PubMed abstract snippets. Cite the PubMed ID and year for assertions."
    prompt = f"System:\n{system}\n\nUser question:\n{req.query}\n\nContext:\n{context}\n\nAnswer concisely and include inline citations as [PMID]."

    chat = openai.ChatCompletion.create(model=OPENAI_LLM_MODEL, messages=[{"role":"system","content":system},{"role":"user","content":prompt}], max_tokens=512)
    answer = chat['choices'][0]['message']['content']

    return QueryResponse(answer=answer, citations=citations)
