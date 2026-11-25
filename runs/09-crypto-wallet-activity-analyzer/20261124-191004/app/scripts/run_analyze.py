#!/usr/bin/env python3
import sys
import argparse
sys.path.insert(0, "src")
from sample_fintech_09.analyze import analyze_wallet

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("wallet")
    args = parser.parse_args()
    print(analyze_wallet(args.wallet))
