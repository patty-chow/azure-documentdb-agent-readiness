import os
from dotenv import load_dotenv
from src.db import get_top_k_for_text

load_dotenv()

if __name__ == '__main__':
    q = "Users cannot login with SSO after password rotation"
    print("Query:\n", q)
    results = get_top_k_for_text(q, embedder=None, k=5)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.get('title')} (score={r.get('score')})")
        print(r.get('content'))
        print('---')
