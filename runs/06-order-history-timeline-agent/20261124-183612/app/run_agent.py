"""Run a scripted demonstration of the agent.

- If OPENAI_API_KEY is set, build a LangChain agent and run two turns.
- Otherwise, run the local deterministic flow without an LLM.
"""
import os
from datetime import datetime, timedelta

from src.pkgagent import agent
from src.pkgagent import db


def scripted_demo_with_llm():
    ag = agent.build_langchain_agent()
    # 1) ask for a customer's history
    q1 = "Fetch order history for customer_id=cust_001 limit=5"
    print("USER:", q1)
    out1 = ag.run(q1)
    print("AGENT:\n", out1)

    # 2) follow-up
    q2 = "What about last month?"
    print("USER:", q2)
    out2 = ag.run(q2)
    print("AGENT:\n", out2)


def deterministic_demo():
    print("Running deterministic demo (no OPENAI_API_KEY set). Using tool functions directly.")
    coll = db.get_orders_collection()
    doc = coll.find_one({}, {"customer_id": 1})
    if not doc:
        print("No data found. Run: python seed.py")
        return
    customer = doc["customer_id"]
    print(f"Demo customer: {customer}")
    print("-> Fetching orders for the customer (limit 5)")
    print(agent.tool_fetch_order_history(f"customer_id={customer} limit=5"))
    print("-> Follow-up: last_month")
    print(agent.tool_spend_summary("last_month"))


if __name__ == "__main__":
    if os.environ.get("OPENAI_API_KEY"):
        scripted_demo_with_llm()
    else:
        deterministic_demo()
