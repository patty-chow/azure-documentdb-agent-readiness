"""Simple CLI REPL that retrieves top-5 chunks and returns a grounded answer.

Behavior:
- If OPENAI_API_KEY is set and chunk embeddings exist in DB, computes query embedding and performs a cosmosSearch vector query (if available).
- Otherwise falls back to simple text-match scoring over chunk_text.
"""
import os
import sys
import math
from dotenv import load_dotenv
from db import get_db

load_dotenv()

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'openai/text-embedding-3-small')
EMBEDDING_DIMS = int(os.environ.get('EMBEDDING_DIMS', '1536'))
LLM_MODEL = os.environ.get('LLM_MODEL', 'gpt-4o-mini')

try:
    import openai
except Exception:
    openai = None


def compute_embedding(text: str):
    if not OPENAI_API_KEY or openai is None:
        raise RuntimeError('OpenAI not configured')
    openai.api_key = OPENAI_API_KEY
    resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=text)
    return resp['data'][0]['embedding']


def cosine(a, b):
    # pure-python cosine similarity
    if not a or not b:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += float(x) * float(y)
        na += float(x) * float(x)
        nb += float(y) * float(y)
    if na == 0 or nb == 0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


def fallback_text_search(db, query, top_k=5):
    # naive substring scoring: longer overlap => higher score
    chunks = list(db[os.environ.get('CHUNKS_COLLECTION','product_chunks')].find({}, {'chunk_id':1,'chunk_text':1}))
    scored = []
    q = query.lower()
    for c in chunks:
        text = (c.get('chunk_text') or '').lower()
        score = 0
        if q in text:
            score += 10
        # count common words
        qwords = set(q.split())
        twords = set(text.split())
        score += len(qwords & twords)
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [(c, s) for s,c in scored[:top_k]]
    return top


def retrieve_top_k(db, query, top_k=5):
    chunks_col = db[os.environ.get('CHUNKS_COLLECTION','product_chunks')]
    # If embeddings exist and OpenAI configured, compute query embedding and attempt vector search via $search (cosmosSearch)
    sample = chunks_col.find_one({'embedding': {'$exists': True}})
    if sample and OPENAI_API_KEY and openai is not None:
        try:
            q_emb = compute_embedding(query)
            # Prefer server-side vector search if available: use aggregation $search with cosmosSearch
            pipeline = [{
                '$search': {
                    'knnBeta': {
                        'vector': q_emb,
                        'path': 'embedding',
                        'k': top_k
                    }
                }
            }, {'$project': {'chunk_id':1,'chunk_text':1,'embedding':1}}]
            agg = list(chunks_col.aggregate(pipeline))
            results = []
            for r in agg:
                emb = r.get('embedding')
                sim = cosine(q_emb, emb) if emb else None
                results.append((r, sim))
            return results
        except Exception as e:
            print('Vector search via $search failed or not supported on this cluster:', e)
            # fallthrough to fallback
    return fallback_text_search(db, query, top_k=top_k)


def format_retrieval(retrieved):
    lines = []
    for item, score in retrieved:
        cid = item.get('chunk_id')
        text = item.get('chunk_text')
        lines.append(f"- {cid} (score={score}): {text[:200].replace('\n',' ')}")
    return '\n'.join(lines)


def generate_answer(context_chunks, question):
    # For sample simplicity: use OpenAI completion if available; otherwise, craft a simple template answer.
    if OPENAI_API_KEY and openai is not None:
        context_text = '\n\n'.join([c.get('chunk_text','') for c, _ in context_chunks])
        prompt = f"""You are a product QA assistant. Use the following context to answer the question. If the answer is not in the context, say "I don't know."\n\nContext:\n{context_text}\n\nQuestion: {question}"""
        try:
            openai.api_key = OPENAI_API_KEY
            resp = openai.ChatCompletion.create(model=LLM_MODEL, messages=[{'role':'user','content':prompt}], max_tokens=512)
            return resp['choices'][0]['message']['content']
        except Exception as e:
            print('LLM call failed:', e)
    # fallback: stitch top chunk excerpts
    excerpts = '\n---\n'.join([c.get('chunk_text','') for c,_ in context_chunks[:3]])
    return f"Grounded answer (fallback):\nContext excerpts:\n{excerpts}\n\nQuestion: {question}\nAnswer: Based on the provided context, here's a short answer: ..."


def main():
    db = get_db()
    print('Simple Product Q&A REPL. Type "exit" to quit.')
    while True:
        q = input('\nAsk a product question> ').strip()
        if not q or q.lower() in ('exit','quit'):
            print('Goodbye')
            break
        retrieved = retrieve_top_k(db, q, top_k=5)
        print('\nRetrieved chunks:')
        print(format_retrieval(retrieved))
        ans = generate_answer(retrieved, q)
        print('\nAnswer:\n')
        print(ans)

if __name__ == '__main__':
    main()
