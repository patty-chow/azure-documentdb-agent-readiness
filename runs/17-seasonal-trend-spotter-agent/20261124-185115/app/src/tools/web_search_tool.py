"""
Simple pluggable web search tool.
If BING_API_KEY is present (and BING_ENDPOINT), it will call Bing Web Search API.
If not present, it returns mock/sample trend signals so the sample can run without keys.
"""
import os
import requests
from datetime import datetime


def bing_search(query, top_k=5):
    key = os.environ.get("BING_API_KEY")
    endpoint = os.environ.get("BING_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search")
    if not key:
        raise RuntimeError("BING_API_KEY not set")
    headers = {"Ocp-Apim-Subscription-Key": key}
    params = {"q": query, "count": top_k}
    resp = requests.get(endpoint, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("webPages", {}).get("value", [])[:top_k]:
        results.append({"title": item.get("name"), "url": item.get("url"), "snippet": item.get("snippet")})
    return results


def mock_trend_signals(categories):
    # deterministic mock signals for demo
    now = datetime.utcnow().isoformat()
    signals = []
    for i, c in enumerate(categories):
        signals.append({
            "category": c,
            "signal": 1.0 - (i * 0.1),
            "source": "mock",
            "timestamp": now,
            "evidence": [f"Mock article saying {c} is trending"],
        })
    return signals


def fetch_trend_signals(categories):
    """
    For each category, fetch web search signals. Returns list of {category, signal, source, evidence}
    """
    key = os.environ.get("BING_API_KEY")
    signals = []
    if not key:
        # fallback to mock
        return mock_trend_signals(categories)

    for c in categories:
        try:
            hits = bing_search(f"{c} trending", top_k=3)
            score = min(1.0, 0.2 * len(hits))
            signals.append({"category": c, "signal": score, "source": "bing", "timestamp": datetime.utcnow().isoformat(), "evidence": hits})
        except Exception as e:
            signals.append({"category": c, "signal": 0.0, "source": "bing-error", "error": str(e)})
    return signals

if __name__ == '__main__':
    print(fetch_trend_signals(["electronics","home","garden"]))
