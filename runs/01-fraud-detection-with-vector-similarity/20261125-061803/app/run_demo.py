"""One-shot demo that loads sample_transactions.json and scores each transaction using the FraudAgent."""
import json
from src.agent import FraudAgent

agent = FraudAgent()

with open("sample_transactions.json") as f:
    txs = json.load(f)

for tx in txs:
    res = agent.score_transaction(tx)
    print(tx["tx_id"], "->", res)
