from .agents import propensity_agent, channel_agent, timing_agent, ACTIONS
from .db import get_db
from datetime import datetime
from typing import Dict, Any


def orchestrate(customer_id: str) -> Dict[str, Any]:
    """Run the three agents, combine results, and write NBA recommendation to DB.
    Returns the inserted recommendation document.
    """
    prop = propensity_agent(customer_id)
    chan = channel_agent(customer_id)
    time = timing_agent(customer_id)

    # choose best action by highest propensity score
    best_action = max(prop.items(), key=lambda kv: kv[1])[0]
    score = prop[best_action]

    recommendation = {
        "customer_id": customer_id,
        "action": best_action,
        "channel": chan["channel"],
        "send_time": time["send_time"],
        "score": float(score),
        "component_scores": {
            "propensity": prop,
            "channel": chan,
            "timing": time,
        },
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    db = get_db()
    coll = db.nba_recommendations
    res = coll.insert_one(recommendation)
    recommendation["_id"] = res.inserted_id
    return recommendation
