from typing import Dict, Any, List
from datetime import datetime, timedelta
from .db import get_db
import os

# Agents are implemented as simple functions. If OPENAI_API_KEY is present,
# these could be extended to call LangChain/LLM; for this sample we provide
# deterministic heuristics so the sample runs without LLM credentials.

ACTIONS = ["promo_email", "discount_offer", "cross_sell", "survey"]


def propensity_agent(customer_id: str) -> Dict[str, float]:
    """Score likelihood to respond for each action type based on past interactions.
    Returns a dict action -> score (0..1)
    """
    db = get_db()
    coll = db.interactions
    scores = {a: 0.1 for a in ACTIONS}
    # Compute success rate per action type
    for a in ACTIONS:
        total = coll.count_documents({"customer_id": customer_id, "action_type": a})
        successes = coll.count_documents({"customer_id": customer_id, "action_type": a, "outcome": "success"})
        if total > 0:
            scores[a] = successes / total
    # normalize to 0..1 and add small smoothing
    maxv = max(scores.values()) if scores else 1
    if maxv > 0:
        for k in scores:
            scores[k] = min(1.0, scores[k] or 0) * 0.99 + 0.01
    return scores


def channel_agent(customer_id: str) -> Dict[str, Any]:
    """Pick the best channel from preferences collection.
    Returns {'channel': 'email'|'sms'|'push', 'score': float}
    """
    db = get_db()
    pref = db.preferences.find_one({"customer_id": customer_id})
    if not pref:
        return {"channel": "email", "score": 0.5}
    rankings = pref.get("channel_rankings", ["email", "sms", "push"])[:]
    # channel_rankings is an ordered list of channels
    best = rankings[0] if rankings else "email"
    return {"channel": best, "score": 1.0}


def timing_agent(customer_id: str) -> Dict[str, Any]:
    """Determine a send time. Use preference or infer from recent interaction timestamps.
    Returns {'send_time': ISO8601 string, 'score': float}
    """
    db = get_db()
    pref = db.preferences.find_one({"customer_id": customer_id})
    if pref and pref.get("contact_times"):
        # choose the first preferred time
        t = pref["contact_times"][0]
        # t might be a string like '09:00' — convert to next occurrence
        try:
            hh, mm = map(int, t.split(":"))
            now = datetime.utcnow()
            send_dt = datetime(now.year, now.month, now.day, hh, mm)
            if send_dt < now:
                send_dt = send_dt + timedelta(days=1)
            return {"send_time": send_dt.isoformat() + "Z", "score": 1.0}
        except Exception:
            pass
    # fallback: pick next hour
    now = datetime.utcnow()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return {"send_time": next_hour.isoformat() + "Z", "score": 0.5}
