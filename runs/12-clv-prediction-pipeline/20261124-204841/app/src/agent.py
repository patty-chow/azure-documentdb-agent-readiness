import os
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent
from langchain.agents.agent_types import AgentType
from langchain.schema import HumanMessage
from src.clv_tool import compute_customer_metrics, update_customer_clv

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Prompt engineering: instruct LLM how to map metrics to tier and produce rationale
PROMPT_INSTR = """
You are given customer metrics and a numeric baseline CLV score computed by the system.
Your task:
- Return a concise numeric `clv_score` (0-1000), a categorical `clv_tier` in [low, medium, high, VIP],
  and a short `rationale` explaining the classification in 2-4 sentences.
- If the baseline score is sensible, you may keep or slightly adjust it.
- Prefer tiers by these heuristics (informational only):
  VIP: top 5% of scores or extremely high spend; high: top 20%; medium: middle 50%; low: bottom 25%.
Return JSON only with keys: clv_score, clv_tier, rationale.
"""


def call_llm_for_clv(metrics: dict, baseline_score: float) -> dict:
    # Use ChatOpenAI wrapper from LangChain
    model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.0)
    system = PROMPT_INSTR
    human = f"Customer metrics: {metrics}\nBaseline score: {baseline_score}\nRespond with JSON only."
    msgs = [HumanMessage(content=human)]
    resp = model.generate(messages=[msgs[0]]) if False else model([HumanMessage(content=human)])
    # LangChain Chat models return a ChatResult; access content
    content = resp.content if hasattr(resp, "content") else str(resp)
    # try to parse JSON from assistant
    import json
    try:
        # Attempt to find JSON object in content
        text = content.strip()
        # If the model returned extra text, try to extract the first JSON object
        if text.startswith("{"):
            j = json.loads(text)
        else:
            # fallback: find first '{' and last '}'
            start = text.find('{')
            end = text.rfind('}')
            j = json.loads(text[start:end+1])
        return j
    except Exception as e:
        # Fallback heuristic: map baseline to tiers
        score = float(baseline_score)
        if score > 800:
            tier = "VIP"
        elif score > 500:
            tier = "high"
        elif score > 200:
            tier = "medium"
        else:
            tier = "low"
        return {"clv_score": score, "clv_tier": tier, "rationale": "LLM parsing failed; used heuristic fallback."}


def compute_and_classify(customer_id: str):
    metrics = compute_customer_metrics(customer_id)
    if not metrics:
        raise ValueError("Customer not found or no purchases")
    # Baseline numeric score: frequency per year * avg_order_value * tenure_years
    purchase_count = metrics.get("purchase_count", 0)
    tenure_days = metrics.get("tenure_days") or 0
    tenure_years = max(tenure_days / 365.0, 0.001)
    # frequency per year
    freq_per_year = purchase_count / tenure_years if tenure_years > 0 else float(purchase_count)
    baseline = freq_per_year * metrics.get("avg_order_value", 0.0) * tenure_years
    # Normalize roughly into 0-1000
    norm = baseline / 10.0
    if norm > 1000:
        norm = 1000.0
    # Call LLM for tiering
    llm_res = call_llm_for_clv(metrics, round(norm, 2))
    clv_score = float(llm_res.get("clv_score", norm))
    clv_tier = llm_res.get("clv_tier", "medium")
    rationale = llm_res.get("rationale", "No rationale provided")
    # persist
    update_customer_clv(customer_id, clv_score, clv_tier, rationale)
    return {"customer_id": customer_id, "clv_score": clv_score, "clv_tier": clv_tier, "rationale": rationale, "metrics": metrics}
