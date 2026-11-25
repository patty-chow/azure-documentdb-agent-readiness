import os
import json
from langchain import OpenAI
from langchain.agents import Tool, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

from src.tools.aggregation_tool import seasonal_velocity
from src.tools.web_search_tool import web_trend_signals


class TrendAgent:
    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        # LangChain OpenAI wrapper; will work without key for mocked flows
        if self.openai_api_key:
            self.llm = ChatOpenAI(openai_api_key=self.openai_api_key, model="gpt-3.5-turbo", temperature=0)
        else:
            self.llm = ChatOpenAI(temperature=0)

        self.tools = [
            Tool.from_function(func=self._aggregation_tool, name="aggregation_tool", description="Run seasonal sales aggregation that returns category-season metrics."),
            Tool.from_function(func=self._web_search_tool, name="web_search_tool", description="Fetch recent web trend signals for categories.")
        ]

        # initialize_agent will not be called until run
        self.agent = None

    def _aggregation_tool(self, top_n: int = 10):
        results = seasonal_velocity(top_n=top_n)
        # return JSON serializable
        return json.dumps(results, default=str)

    def _web_search_tool(self, query_terms: list = None):
        results = web_trend_signals(query_terms=query_terms)
        return json.dumps(results, default=str)

    def run(self):
        # Simple orchestration: call both tools directly and combine signals.
        agg = seasonal_velocity()
        web = web_trend_signals()

        # compute a simple combined score per category: normalize total_quantity and combine with web score
        # aggregate agg into category → sum quantities across seasons
        cat_totals = {}
        for r in agg:
            c = r["category"]
            cat_totals.setdefault(c, 0)
            cat_totals[c] += r.get("total_quantity", 0)

        max_qty = max(cat_totals.values()) if cat_totals else 1
        web_map = {w["category"]: w for w in web}

        combined = []
        for cat, qty in cat_totals.items():
            normalized = qty / max_qty
            web_score = web_map.get(cat, {}).get("score", 0)
            score = 0.6 * normalized + 0.4 * web_score
            combined.append({"category": cat, "qty": qty, "normalized_qty": normalized, "web_score": web_score, "combined_score": score})

        combined_sorted = sorted(combined, key=lambda x: x["combined_score"], reverse=True)
        return combined_sorted
