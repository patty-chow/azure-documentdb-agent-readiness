import os
from typing import List, Dict

try:
    import openai
    _OPENAI_AVAILABLE = True
except Exception:
    _OPENAI_AVAILABLE = False

# We use a simple prompt template for clinical summarization. LlamaIndex is referenced in README as an integration point for prompt engineering

PROMPT_TEMPLATE = """
You are a clinical summarization assistant. Use the provided context sections (with source and chunk ids) to write a concise, referenced clinical summary answering the question.
Question: {question}

Context sections:
{context}

Return a brief summary and list references (doc_id, chunk_id) that support each statement.
"""


def summarize(question: str, retrieved: List[Dict], max_tokens: int = 512) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    context_blocks = []
    for r in retrieved:
        context_blocks.append(f"[doc={r['doc_id']}|chunk={r['chunk_id']}|score={r['score']:.4f}] {r['excerpt']}")
    context = "\n\n".join(context_blocks)
    prompt = PROMPT_TEMPLATE.format(question=question, context=context)
    if key and _OPENAI_AVAILABLE:
        openai.api_key = key
        resp = openai.ChatCompletion.create(
            model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            messages=[{"role":"user","content":prompt}],
            max_tokens=max_tokens,
            temperature=0.0,
        )
        return resp["choices"][0]["message"]["content"].strip()
    # fallback: return a simple concatenation
    lines = ["SUMMARY (fallback, no OpenAI key):"]
    lines.append("Question: " + question)
    lines.append("")
    for i, r in enumerate(retrieved, start=1):
        lines.append(f"{i}. (doc={r['doc_id']},chunk={r['chunk_id']},score={r['score']:.3f}) {r['excerpt'][:200]}")
    return "\n".join(lines)
