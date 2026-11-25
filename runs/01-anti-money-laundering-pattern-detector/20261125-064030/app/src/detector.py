import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pydantic import BaseModel
from src.db import get_db, supports_graph_lookup

try:
    import openai
except Exception:
    openai = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY and openai:
    openai.api_key = OPENAI_API_KEY


class SuspiciousChain(BaseModel):
    chain_id: str
    accounts: List[str]
    transactions: List[Dict[str, Any]]
    reasons: List[str]
    narrative: str = ""


class AggregationTool:
    def __init__(self, db):
        self.db = db
        self.tx = db.transactions
        self.graph_ok = supports_graph_lookup(db)

    def follow_chain(self, start_account: str, max_hops: int = 5) -> List[Dict[str, Any]]:
        if self.graph_ok:
            pipeline = [
                {"$match": {"from_account": start_account}},
                {"$graphLookup": {
                    "from": "transactions",
                    "startWith": "$to_account",
                    "connectFromField": "to_account",
                    "connectToField": "from_account",
                    "as": "chain",
                    "maxDepth": max_hops
                }},
                {"$project": {"chain": 1}}
            ]
            docs = list(self.tx.aggregate(pipeline))
            # aggregate may return multiple docs; flatten chains
            chain_txs = []
            for d in docs:
                for c in d.get("chain", []):
                    chain_txs.append(c)
            return chain_txs
        else:
            # Client-side BFS following to_account -> from_account edges
            visited = set()
            results = []
            queue = [start_account]
            hops = 0
            while queue and hops < max_hops:
                acct = queue.pop(0)
                cursor = self.tx.find({"from_account": acct})
                for t in cursor:
                    tid = t.get("_id")
                    if tid in visited:
                        continue
                    visited.add(tid)
                    results.append(t)
                    queue.append(t.get("to_account"))
                hops += 1
            return results

    def detect_suspicious(self, limit_accounts: int = 50) -> List[SuspiciousChain]:
        # Simple heuristic rules applied to chains starting from accounts that sent funds
        suspects: List[SuspiciousChain] = []
        accounts = self.db.accounts.find().limit(limit_accounts)
        for acc in accounts:
            acct_id = acc["account_id"]
            chain_txs = self.follow_chain(acct_id, max_hops=6)
            if not chain_txs:
                continue
            # Simple patterns
            reasons = []
            tx_count = len(chain_txs)
            total_amount = sum(t.get("amount", 0) for t in chain_txs)

            # Structuring: many similar-size incoming txs to same recipient in short window
            incoming_to_acct = list(self.tx.find({"to_account": acct_id}).sort("timestamp", 1))
            if len(incoming_to_acct) >= 5:
                # check if amounts are similar
                amounts = [t.get("amount", 0) for t in incoming_to_acct]
                avg = sum(amounts) / len(amounts)
                if all(abs(a - avg) / max(1.0, avg) < 0.1 for a in amounts):
                    reasons.append("structuring: multiple similar-sized deposits to account")

            # Rapid pass-through: receives and forwards quickly
            # Look for tx where an account receives then forwards within 15 minutes
            for t_in in incoming_to_acct:
                in_time = t_in.get("timestamp")
                if not in_time:
                    continue
                out = self.tx.find_one({"from_account": acct_id, "timestamp": {"$gte": in_time, "$lte": in_time + timedelta(minutes=15)}})
                if out:
                    reasons.append("rapid_pass_through: funds received and forwarded quickly")
                    break

            # Circular transfer: detect if chain returns to start account
            seen_accounts = {acct_id}
            cycle = False
            for t in chain_txs:
                to = t.get("to_account")
                if to in seen_accounts:
                    cycle = True
                    break
                seen_accounts.add(to)
            if cycle:
                reasons.append("circular_transfers: chain returns to an earlier account")

            if reasons:
                sc = SuspiciousChain(
                    chain_id=f"chain_{acct_id}",
                    accounts=list(seen_accounts),
                    transactions=[{"_id": t.get("_id"), "from": t.get("from_account"), "to": t.get("to_account"), "amount": t.get("amount"), "timestamp": t.get("timestamp")} for t in chain_txs],
                    reasons=reasons,
                )
                # generate narrative
                sc.narrative = self._generate_narrative(sc)
                suspects.append(sc)
        return suspects

    def _generate_narrative(self, sc: SuspiciousChain) -> str:
        # If OpenAI key present, attempt to generate a polished narrative; otherwise a simple template
        if OPENAI_API_KEY and openai:
            try:
                prompt = (
                    f"You are an AML analyst. Given the following flagged chain (accounts: {sc.accounts}, reasons: {sc.reasons}, "
                    f"transactions: {sc.transactions}), write a short structured suspicious activity narrative (2-4 sentences) describing what happened and why it is suspicious."
                )
                resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=200)
                text = resp.choices[0].text.strip()
                return text
            except Exception:
                # ignore and fall back
                pass
        # Fallback narrative
        return (
            f"Flagged chain {sc.chain_id}: accounts involved {', '.join(sc.accounts)}. Reasons: {', '.join(sc.reasons)}. "
            f"Sample transactions include {len(sc.transactions)} transfers totaling {sum(t.get('amount',0) for t in sc.transactions)}."
        )
