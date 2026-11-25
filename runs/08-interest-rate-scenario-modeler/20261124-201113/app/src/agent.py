import os
import json
from typing import List, Dict, Any

# Delay heavy LLM imports until runtime so unit tests can import prompt formatters without LLM deps

from src.aggregation_tool import summarize_positions


DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4")


def format_system_prompt() -> str:
    return (
        "You are a financial analyst assistant. Given grouped exposures by maturity bucket and rate type, reason through the Net Interest Income (NII) impact under three scenarios: \n"
        "1) Parallel shift (e.g., +100 bps across the curve),\n"
        "2) Steepening (short rates down, long rates up by given amounts), and\n"
        "3) Inversion (short rates up, long rates down).\n"
        "Return a structured JSON object with per-bucket and aggregate estimated change in NII, key assumptions, and a short plain-language summary. Use the following JSON schema: {\n"
        "  'scenarios': { 'parallel_shift': {...}, 'steepening': {...}, 'inversion': {...}},\n"
        "  'assumptions': {...}, 'summary': '...'\n"
        "}. Be explicit about the assumptions you made (e.g., repricing behavior for floating positions)."
    )


def format_user_prompt(aggregated: List[Dict[str, Any]]) -> str:
    return (
        "Here is the aggregated exposure by bucket and rate type (notional in USD):\n"
        + json.dumps(aggregated, default=str, indent=2)
        + "\n\nPlease analyze NII impact under the three scenarios and return the structured JSON report."
    )


class ScenarioAnalyzer:
    def __init__(self, model_name: str = DEFAULT_MODEL, temperature: float = 0.0):
        # Delay import
        try:
            from langchain.chat_models import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage
        except Exception as e:
            raise RuntimeError("LangChain or ChatOpenAI not available: " + str(e))

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set; set it to call the LLM")
        # LangChain ChatOpenAI wrapper
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature, openai_api_key=api_key)
        self.SystemMessage = SystemMessage
        self.HumanMessage = HumanMessage

    def analyze(self) -> Dict[str, Any]:
        aggregated = summarize_positions()
        system = self.SystemMessage(content=format_system_prompt())
        user = self.HumanMessage(content=format_user_prompt(aggregated))
        resp = self.llm([system, user])
        text = resp.content
        # Expecting JSON back — attempt to parse
        try:
            parsed = json.loads(text)
        except Exception:
            # If not JSON, return a wrapper
            parsed = {"error": "LLM did not return JSON", "raw": text}
        return parsed


if __name__ == "__main__":
    analyzer = ScenarioAnalyzer()
    out = analyzer.analyze()
    print(json.dumps(out, indent=2))
