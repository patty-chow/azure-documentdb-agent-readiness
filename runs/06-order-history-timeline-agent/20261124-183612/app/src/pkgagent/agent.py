import os
import json
from datetime import datetime, timedelta
from typing import Optional

from . import db

class SimpleContext:
    def __init__(self):
        self.last_customer: Optional[str] = None
        self.last_time_range: Optional[tuple[Optional[datetime], Optional[datetime]]] = None

    def set_customer(self, customer_id: str):
        self.last_customer = customer_id

    def set_time_range(self, start: Optional[datetime], end: Optional[datetime]):
        self.last_time_range = (start, end)

    def resolve_customer(self, maybe_customer: Optional[str]):
        return maybe_customer or self.last_customer

    def resolve_time_range(self, start: Optional[datetime], end: Optional[datetime]):
        if start or end:
            self.set_time_range(start, end)
            return (start, end)
        return self.last_time_range


ctx = SimpleContext()


def parse_args_kv(text: str) -> dict:
    out = {}
    for part in text.replace(",", " ").split():
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def tool_fetch_order_history(raw: str) -> str:
    args = parse_args_kv(raw)
    customer = args.get("customer_id")
    if not customer:
        if ctx.last_customer:
            customer = ctx.last_customer
        else:
            return "Error: no customer_id provided and no previous customer in memory."
    ctx.set_customer(customer)
    limit = int(args.get("limit", 10))
    orders = db.find_orders_by_customer(customer, limit=limit)
    lines = [f"Found {len(orders)} orders for {customer} (limit {limit}):"]
    for o in orders:
        lines.append(f"- {o['order_id']} | {o['order_date'].strftime('%Y-%m-%d')} | ${o['total_amount']} | {o['status']}")
    return "\n".join(lines)


def tool_spend_summary(raw: str) -> str:
    args = parse_args_kv(raw)
    customer = args.get("customer_id") or ctx.last_customer
    if raw.strip().lower() == "last_month":
        end = datetime.utcnow()
        start = (end.replace(day=1) - timedelta(days=1)).replace(day=1)
        ctx.set_time_range(start, end)
    else:
        start = None
        end = None
        if "start" in args:
            start = datetime.fromisoformat(args["start"])  # may raise
        if "end" in args:
            end = datetime.fromisoformat(args["end"])  # may raise
        if start or end:
            ctx.set_time_range(start, end)

    start, end = ctx.last_time_range if ctx.last_time_range else (None, None)
    res = db.aggregate_spend_summary(customer_id=customer, start_date=start, end_date=end)
    return json.dumps({"customer_id": customer, "start": start.isoformat() if start else None, "end": end.isoformat() if end else None, **res}, default=str)


def tool_order_lookup(raw: str) -> str:
    args = parse_args_kv(raw)
    order_id = args.get("order_id")
    if not order_id:
        return "Error: provide order_id=ORDER_xxx"
    doc = db.get_order_status(order_id)
    if not doc:
        return f"Order {order_id} not found"
    return json.dumps(doc, default=str)


def build_langchain_agent():
    # Import langchain pieces only when building the agent so importing this module doesn't require langchain community extras
    from langchain.llms import OpenAI
    from langchain.tools import Tool
    from langchain.agents import initialize_agent, AgentType
    from langchain.memory import ConversationBufferMemory

    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        raise EnvironmentError("OPENAI_API_KEY not set; cannot build LLM agent")
    llm = OpenAI(openai_api_key=openai_key, temperature=0)
    tools = [
        Tool(name="fetch_order_history", func=tool_fetch_order_history, description="Fetch order history for a customer. Input: customer_id=<id> limit=<n>"),
        Tool(name="spend_summary", func=tool_spend_summary, description="Return spend summary; accepts customer_id=<id> start=YYYY-MM-DD end=YYYY-MM-DD or 'last_month'"),
        Tool(name="order_lookup", func=tool_order_lookup, description="Lookup an order status. Input: order_id=<id>"),
    ]
    memory = ConversationBufferMemory(memory_key="chat_history")
    agent = initialize_agent(tools, llm, agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, memory=memory, verbose=False)
    return agent
