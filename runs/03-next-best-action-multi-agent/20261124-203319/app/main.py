import argparse
from fastapi import FastAPI, HTTPException
import uvicorn
from src.orchestrator import orchestrate

app = FastAPI()

@app.get('/nba')
def get_nba(customer_id: str):
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required")
    rec = orchestrate(customer_id)
    return rec


def demo_run():
    # run a demo for a seeded customer
    demo_customer = "cust_001"
    print("Running demo for", demo_customer)
    rec = orchestrate(demo_customer)
    print("Recommendation:")
    print(rec)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--customer-id')
    args = parser.parse_args()
    if args.demo:
        demo_run()
    elif args.customer_id:
        rec = orchestrate(args.customer_id)
        print(rec)
    else:
        print("Run with --demo or --customer-id <id>")
