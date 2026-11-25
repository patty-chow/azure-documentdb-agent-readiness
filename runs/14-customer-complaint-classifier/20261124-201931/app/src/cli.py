import argparse
from .pipeline import run_classify

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["classify-run"], help="command to run")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    if args.command == "classify-run":
        updated = run_classify(limit=args.limit)
        print(f"Updated {updated} documents")
