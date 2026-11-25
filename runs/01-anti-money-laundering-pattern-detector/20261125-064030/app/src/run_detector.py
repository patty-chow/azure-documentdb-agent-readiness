import argparse
import json
from src.db import get_db
from src.detector import AggregationTool


def main(limit: int = 50):
    db = get_db()
    tool = AggregationTool(db)
    suspects = tool.detect_suspicious(limit_accounts=limit)
    out = [s.dict() for s in suspects]
    print(json.dumps(out, default=str, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50, help="Limit number of accounts to scan")
    args = parser.parse_args()
    main(limit=args.limit)
