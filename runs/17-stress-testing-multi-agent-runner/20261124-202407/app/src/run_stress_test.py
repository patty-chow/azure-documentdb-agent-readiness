"""CLI to run a stress test scenario and persist the run to the stress_runs collection.
Usage: python -m src.run_stress_test --sample_size 100
"""
import argparse
import os
import json
from src.db import get_db
from src.agents import ScenarioAgent, ImpactAgent, ReportingAgent
from dotenv import load_dotenv

load_dotenv()

try:
    from langchain import OpenAI
except Exception:
    OpenAI = None


def build_llm_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    # Minimal wrapper for the ReportingAgent (not full LangChain usage to keep sample small)
    class LLMClient:
        def __init__(self, key):
            self.key = key
            self.client = OpenAI(openai_api_key=key)
        def generate(self, prompt: str):
            # Use simple completion
            resp = self.client(prompt)
            return str(resp)
    return LLMClient(api_key)


def persist_run(db, report):
    coll = db.stress_runs
    coll.insert_one(report)


def main(sample_size: int = 100):
    db = get_db()
    scenario_agent = ScenarioAgent()
    scenario = scenario_agent.generate()

    impact_agent = ImpactAgent(db.positions)
    impact = impact_agent.compute(scenario)

    llm = build_llm_client()
    reporting_agent = ReportingAgent(llm_client=llm)
    report = reporting_agent.synthesize(scenario, impact)

    # Add metadata and persist
    run_doc = {
        "_id": report["scenario"]["id"],
        "scenario": report["scenario"],
        "impact_summary": report["impact_summary"],
        "narrative": report.get("narrative"),
        "generated_at": report["generated_at"],
        "schemaVersion": 1,
    }
    persist_run(db, run_doc)

    print(json.dumps(run_doc, default=str, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample_size", type=int, default=100)
    args = parser.parse_args()
    main(args.sample_size)
