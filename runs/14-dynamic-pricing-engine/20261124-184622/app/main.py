"""Run the pricing agent for a SKU.
This script exposes the same high-level behavior as a LangChain agent with tools:
- It exposes tool functions in agent.py that query DocumentDB.
- If OPENAI_API_KEY is present, it prompts the model to reason and return a recommended price.
- If no OPENAI_API_KEY is set, it runs deterministic logic to compute a recommended price.
In both cases it writes the updated price atomically using the update_price tool.
"""
import os
import sys
import json
from dotenv import load_dotenv
from datetime import datetime

import openai
import db
import agent

load_dotenv()

MODEL = os.getenv("MODEL", "gpt-4")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_NAME = "sample_retail_14"

if not os.getenv("DOCUMENTDB_URI"):
    print("DOCUMENTDB_URI not set in environment. Exiting.")
    sys.exit(1)

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


def get_product(sku: str):
    database = db.get_db(DB_NAME)
    return database.get_collection("products").find_one({"sku": sku})


def deterministic_pricing(sku: str) -> dict:
    # Simple heuristic: use competitor avg and margin rules to compute price
    prod = get_product(sku)
    if not prod:
        return {"error": "product not found", "sku": sku}
    cost = prod.get("cost", 0)
    # Call tools directly
    comp_raw = agent.get_competitor_prices_tool(f"sku:{sku};hours:72")
    comp = json.loads(comp_raw)
    demand_raw = agent.get_demand_metrics_tool(f"sku:{sku};hours:72")
    demand = json.loads(demand_raw)
    rules_raw = agent.get_margin_rules_tool(f"sku:{sku}")
    rules = json.loads(rules_raw)

    comp_avg = comp.get("avg") if comp.get("count", 0) > 0 else None
    min_margin = None
    for r in rules.get("rules", []):
        if r.get("sku_or_category") == sku:
            min_margin = r.get("min_margin")
            break
    if min_margin is None:
        # fallback to first rule or default
        if rules.get("rules"):
            min_margin = rules["rules"][0].get("min_margin")
        else:
            min_margin = 0.15

    # Minimum price to satisfy margin
    min_price_by_margin = cost / (1 - min_margin) if min_margin < 1 else cost * 1.5

    # Start with competitor average if present, else current price
    if comp_avg:
        target = comp_avg * 0.995  # slight undercut
    else:
        target = prod.get("price", cost * (1 + min_margin))

    # Ensure margin satisfied
    recommended = max(target, min_price_by_margin)
    # Round to 2 decimals
    recommended = round(recommended, 2)

    rationale = f"Computed from competitor_avg={comp_avg}, cost={cost}, min_margin={min_margin}, min_price_by_margin={min_price_by_margin}"
    return {"recommended_price": recommended, "rationale": rationale}


def call_model_for_price(sku: str) -> dict:
    # Gather tool outputs to include in the prompt
    comp_raw = agent.get_competitor_prices_tool(f"sku:{sku};hours:72")
    demand_raw = agent.get_demand_metrics_tool(f"sku:{sku};hours:72")
    rules_raw = agent.get_margin_rules_tool(f"sku:{sku}")

    prompt = (
        f"You are a pricing assistant.\nProduct SKU: {sku}\n\n"
        f"Competitor prices (recent): {comp_raw}\n\n"
        f"Demand metrics (recent): {demand_raw}\n\n"
        f"Margin rules: {rules_raw}\n\n"
        "Based on the above, reason step-by-step, then return a JSON object with fields:\n"
        "{\"recommended_price\": <number>, \"rationale\": <string>}"
    )

    resp = openai.ChatCompletion.create(model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0)
    content = resp["choices"][0]["message"]["content"]
    # Try to parse JSON from response
    try:
        parsed = json.loads(content)
        return parsed
    except Exception:
        # If the model returned extra text, try to extract JSON block
        import re
        m = re.search(r"\{[\s\S]*\}", content)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        # As a fallback, return full content as rationale and no price
        return {"recommended_price": None, "rationale": content}


def run(sku: str):
    if OPENAI_API_KEY:
        print("OPENAI_API_KEY detected — calling model")
        res = call_model_for_price(sku)
    else:
        print("No OPENAI_API_KEY set — using deterministic fallback logic")
        res = deterministic_pricing(sku)

    print("Recommendation:", res)

    if res.get("recommended_price") is not None:
        # Write back atomically
        update_input = f"sku:{sku};price:{res['recommended_price']}"
        out = agent.update_price_tool(update_input)
        print("Update result:", out)
    else:
        print("No numeric recommended_price produced; skipping update.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <SKU>")
        sys.exit(2)
    run(sys.argv[1])
