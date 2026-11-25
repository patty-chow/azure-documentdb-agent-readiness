import random
import time
from typing import Dict, Any, List
from pymongo.collection import Collection

class ScenarioAgent:
    """Generates macroeconomic shock parameters."""
    def __init__(self, seed: int | None = None):
        if seed is not None:
            random.seed(seed)

    def generate(self) -> Dict[str, Any]:
        # Simple scenario: rate shock (bps) and FX shocks (pct) for a few currencies
        rate_bps = random.choice([-200, -100, -50, 0, 50, 100, 200])
        fx_shocks = {
            "USD": 0.0,
            "EUR": round(random.uniform(-0.15, 0.15), 4),
            "JPY": round(random.uniform(-0.20, 0.20), 4),
        }
        scenario = {
            "id": f"scenario_{int(time.time())}",
            "rate_bps": rate_bps,
            "fx_shocks": fx_shocks,
            "created_at": int(time.time()),
            "description": f"Rate shock {rate_bps} bps; FX shocks {fx_shocks}",
        }
        return scenario

class ImpactAgent:
    """Runs aggregation pipelines against positions to compute P&L impacts.
    The agent writes no data; it returns computed summaries which the orchestrator
    can persist.
    """
    def __init__(self, positions_coll: Collection):
        self.positions = positions_coll

    def compute(self, scenario: Dict[str, Any], sample_filter: Dict[str, Any] | None = None) -> Dict[str, Any]:
        # Build aggregation pipeline to compute per-instrument and total impact.
        # For this sample, assume each position has fields: quantity, market_value, currency, risk_factors.rate
        rate_factor = 1 + (scenario.get("rate_bps", 0) / 10000.0)
        fx_shocks = scenario.get("fx_shocks", {})

        match_stage = {"$match": sample_filter} if sample_filter else {"$match": {}}

        # Project a computed 'pl' field: simple approximation
        project_stage = {
            "$project": {
                "account_id": 1,
                "instrument": 1,
                "currency": 1,
                "market_value": 1,
                "quantity": 1,
                "base_pl": {"$multiply": ["$market_value", {"$subtract": [rate_factor, 1]}]},
                "fx_shock": {"$literal": 0},
            }
        }

        # We cannot compute fx_shock per-document easily in aggregation without a lookup table; instead,
        # we'll use $set to map a few known currencies. For sample brevity do a conditional mapping.
        project_stage["$project"]["fx_shock"] = {
            "$switch": {
                "branches": [
                    {"case": {"$eq": ["$currency", "EUR"]}, "then": fx_shocks.get("EUR", 0)},
                    {"case": {"$eq": ["$currency", "JPY"]}, "then": fx_shocks.get("JPY", 0)},
                    {"case": {"$eq": ["$currency", "USD"]}, "then": fx_shocks.get("USD", 0)},
                ],
                "default": 0,
            }
        }

        # Add fx impact to base_pl: fx impact ~= market_value * fx_shock
        project_stage["$project"]["pl"] = {"$add": ["$base_pl", {"$multiply": ["$market_value", "$fx_shock"]}]}

        group_stage = {
            "$group": {
                "_id": {"instrument": "$instrument"},
                "instrument_pl": {"$sum": "$pl"},
                "notional": {"$sum": {"$multiply": ["$quantity", "$market_value"]}},
                "count": {"$sum": 1},
            }
        }

        sort_stage = {"$sort": {"instrument_pl": -1}}

        pipeline = [match_stage, project_stage, group_stage, sort_stage]

        cursor = self.positions.aggregate(pipeline)
        per_instrument = list(cursor)

        # Total impact
        total_pipeline = [match_stage,
                          {"$project": {"pl": project_stage["$project"]["pl"]}},
                          {"$group": {"_id": None, "total_pl": {"$sum": "$pl"}, "count": {"$sum": 1}}}]
        total_res = list(self.positions.aggregate(total_pipeline))
        total_pl = total_res[0]["total_pl"] if total_res else 0.0

        return {
            "scenario_id": scenario.get("id"),
            "per_instrument": per_instrument,
            "total_pl": total_pl,
            "count_instruments": len(per_instrument),
        }

class ReportingAgent:
    """Synthesis of impact results. Optionally queries an LLM to produce a narrative summary.
    """
    def __init__(self, llm_client=None):
        # llm_client is optional; if None, produce a deterministic summary
        self.llm = llm_client

    def synthesize(self, scenario: Dict[str, Any], impact: Dict[str, Any]) -> Dict[str, Any]:
        # Basic structured report
        per_instrument = impact.get("per_instrument") or impact.get("by_instrument") or []
        total_pl = impact.get("total_pl") or impact.get("total_impact") or 0.0

        report = {
            "scenario": scenario,
            "impact_summary": {
                "total_pl": total_pl,
                "top_instruments": per_instrument[:10],
            },
            "generated_at": int(time.time()),
        }

        # Optionally enrich with LLM narrative
        if self.llm:
            try:
                prompt = f"Summarize the stress test scenario {scenario['id']}: total P&L {total_pl}. Provide key observations."
                resp = self.llm.generate(prompt)
                report["narrative"] = resp
            except Exception as e:
                report["narrative_error"] = str(e)

        return report
