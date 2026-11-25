import os
import json
import openai
from src import db

MODEL = os.environ.get("MODEL", "gpt-4")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


class PricingAgent:
    def __init__(self):
        if not OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY not set. LLM calls will fail.")

    # Tools: wrappers around db functions
    def get_demand_metrics(self, sku):
        return db.compute_demand_metric_for_sku(sku)

    def get_competitor_prices(self, sku, limit=10):
        return db.get_recent_competitor_prices(sku, limit=limit)

    def get_margin_rule(self, sku):
        return db.get_margin_rule_for_sku_or_category(sku)

    def write_price(self, sku, price):
        return db.write_price_atomic(sku, price)

    def _call_llm(self, prompt):
        # Simple call to OpenAI ChatCompletion.
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set; cannot call LLM")
        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=800,
        )
        return resp["choices"][0]["message"]["content"]

    def recommend_price_and_apply(self, sku):
        # Gather data using tools
        demand = self.get_demand_metrics(sku)
        competitors = self.get_competitor_prices(sku)
        margin = self.get_margin_rule(sku)
        product = db.get_db().products.find_one({"sku": sku})

        context = {
            "product": product,
            "demand": demand,
            "competitor_prices": competitors,
            "margin_rule": margin,
        }

        prompt = f"""
You are a pricing agent. Inspect the provided data and reason step-by-step (show your chain-of-thought briefly), then return ONLY a JSON object with the fields:\n
- recommended_price: numeric (round to 2 decimals)\n- rationale: short string explaining the key reasons\n- checks: array of checks applied (e.g., margin_ok, competitor_no_underprice)\n
Data (product, demand, competitor_prices, margin_rule):\n{json.dumps(context, default=str, indent=2)}\n
Constraints:\n- Enforce margin rules if present: resulting price must produce a margin between min_margin and max_margin relative to product.cost where provided. If margin rule conflict, choose the conservative bound (respect min_margin).\n- Prefer to be competitive with competitor prices but do not systematically undercut by more than 5% without margin justification.\n
Return only the JSON object. After you produce the price, this script will write it back atomically to the product document.\n"""

        resp = self._call_llm(prompt)
        # Attempt to parse JSON from model output
        try:
            parsed = json.loads(resp)
        except Exception:
            import re
            m = re.search(r"\{[\s\S]*\}$", resp)
            if m:
                parsed = json.loads(m.group(0))
            else:
                raise RuntimeError("LLM response was not valid JSON:\n" + resp)

        recommended_price = float(parsed["recommended_price"])
        # Apply margin enforcement in code to be safe
        if product and "cost" in product and margin:
            cost = float(product["cost"])
            min_m = float(margin.get("min_margin", 0))
            max_m = float(margin.get("max_margin", 10))
            min_price = round(cost * (1 + min_m) + 1e-9, 2)
            max_price = round(cost * (1 + max_m) + 1e-9, 2)
            # clamp
            if recommended_price < min_price:
                print(f"Recommended price {recommended_price} is below min margin price {min_price}, clamping up.")
                recommended_price = float(min_price)
            if recommended_price > max_price:
                print(f"Recommended price {recommended_price} is above max margin price {max_price}, clamping down.")
                recommended_price = float(max_price)

        # Write back atomically
        updated = self.write_price(sku, recommended_price)
        return {"updated_document": updated, "llm_parsed": parsed}
