import argparse
from dotenv import load_dotenv
load_dotenv()

from src.agent import run_agent_assign_segment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--customer_id", required=True, help="customer id to segment")
    parser.add_argument("--use_llm", action="store_true", help="Try to use LLM (OpenAI) if configured")
    args = parser.parse_args()

    res = run_agent_assign_segment(args.customer_id, use_llm=args.use_llm)
    print("Assigned segment:", res["assigned_segment"])
    print("Profile document:")
    print(res["profile"])
    print("Metrics:")
    print(res["metrics"])


if __name__ == "__main__":
    main()
