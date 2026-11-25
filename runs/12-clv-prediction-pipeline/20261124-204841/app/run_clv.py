import argparse
from src.seed import seed
from src.agent import compute_and_classify

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed", action="store_true", help="Seed sample data")
    p.add_argument("--customer-id", type=str, default="sample_cust_1")
    args = p.parse_args()
    if args.seed:
        seed()
    res = compute_and_classify(args.customer_id)
    print("Result:")
    print(res)
