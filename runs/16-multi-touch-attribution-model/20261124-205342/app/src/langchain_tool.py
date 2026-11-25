import os
from langchain import OpenAI


def answer_question_for_customer(db, customer_id: str, question: str) -> str:
    """Fetch the latest attribution results for the given customer and ask the LLM to answer the question.

    This is a small wrapper used by the FastAPI endpoint. It uses OpenAI via LangChain.
    """
    results_coll = db["attribution_results"]
    # fetch the latest version per model by sorting model asc, version desc and grabbing first per model
    latest = {}
    cursor = results_coll.find({"customer_id": customer_id}).sort([("model", 1), ("version", -1)])
    for doc in cursor:
        model = doc.get("model")
        if model and model not in latest:
            latest[model] = doc

    # Build a short context
    context_lines = []
    for model, doc in latest.items():
        context_lines.append(f"Model: {model}\nTotal revenue: {doc.get('total_revenue')}\nAttribution:\n")
        for a in doc.get("attribution", []):
            context_lines.append(f" - {a.get('channel')}: {a.get('amount')}\n")

    context = "\n".join(context_lines) or "No attribution results found."

    # Configure LangChain/OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    # LangChain OpenAI wrapper will read OPENAI_API_KEY from env
    llm = OpenAI(temperature=0)

    prompt = (
        f"You are an analytics assistant. Answer the marketer's question using ONLY the provided attribution results context.\n\n"
        f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:" 
    )
    resp = llm(prompt)
    return resp
