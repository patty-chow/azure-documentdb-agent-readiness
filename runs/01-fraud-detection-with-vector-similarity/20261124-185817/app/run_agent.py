"""
Demo script: encode a sample transaction, run a vector search against
sample_fintech_01.fraud_patterns, compute a simple fraud risk score, and
print a natural-language explanation.

Usage:
  python run_agent.py "transaction text or features"

If OPENAI_API_KEY is set, the script may call OpenAI to produce a nicer
explanation. Otherwise a deterministic template-based explanation is used.
"""
import os
import sys
from docdb_client import get_db
from embeddings import embed_text


def vector_search(query_vector, k=5):
    db = get_db()
    coll = db["fraud_patterns"]
    pipeline = [
        {"$search": {"cosmosSearch": {"vector": query_vector, "path": "vector", "k": k}, "returnStoredSource": True}},
        {"$project": {"similarityScore": {"$meta": "searchScore"}, "document": "$$ROOT"}},
    ]
    cursor = coll.aggregate(pipeline)
    results = list(cursor)
    return results


def compute_risk(results):
    # results contain similarityScore in descending order
    if not results:
        return 0.0
    scores = [r.get("similarityScore", 0.0) for r in results]
    # simple weighted score: top score * 100, clipped
    top = max(scores)
    score = max(0.0, min(100.0, float(top) * 100.0))
    return round(score, 2)


def explain(results, transaction_text):
    if not results:
        return "No similar known fraud patterns were found."
    lines = [f"Transaction: {transaction_text}\nFraud risk matches:\n"]
    for r in results:
        doc = r.get("document", {})
        pattern = doc.get("pattern_name")
        desc = doc.get("description")
        sim = r.get("similarityScore")
        lines.append(f"- Pattern: {pattern} (sim={sim:.4f})\n  Description: {desc}\n")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_agent.py \"transaction text\"")
        sys.exit(1)
    transaction_text = sys.argv[1]
    vec = embed_text(transaction_text)

    results = vector_search(vec, k=5)
    risk = compute_risk(results)
    explanation = explain(results, transaction_text)

    print("Fraud risk score:", risk)
    print("Explanation:\n", explanation)


if __name__ == "__main__":
    main()
