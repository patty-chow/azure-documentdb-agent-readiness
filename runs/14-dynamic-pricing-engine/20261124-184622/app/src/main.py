import argparse
from src.agent import PricingAgent


def main():
    parser = argparse.ArgumentParser(description="Run Pricing Agent for a SKU")
    parser.add_argument("--sku", required=True, help="SKU to price")
    args = parser.parse_args()

    agent = PricingAgent()
    out = agent.recommend_price_and_apply(args.sku)
    print("Result:")
    import json
    print(json.dumps(out, default=str, indent=2))


if __name__ == "__main__":
    main()
