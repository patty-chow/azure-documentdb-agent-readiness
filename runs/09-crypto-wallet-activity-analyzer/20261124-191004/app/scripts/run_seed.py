#!/usr/bin/env python3
import sys
import argparse
sys.path.insert(0, "src")
from sample_fintech_09.seed import seed_data

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--wallet", required=True)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--tx-per-day", type=int, default=5)
    args = parser.parse_args()
    seed_data(args.wallet, days=args.days, tx_per_day=args.tx_per_day)
