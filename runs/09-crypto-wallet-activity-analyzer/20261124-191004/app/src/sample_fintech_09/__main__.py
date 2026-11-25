import argparse
from .seed import seed_data
from .analyze import analyze_wallet


def main():
    parser = argparse.ArgumentParser(prog="sample_fintech_09")
    sub = parser.add_subparsers(dest="cmd")

    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--wallet", required=True)
    p_seed.add_argument("--days", type=int, default=30)
    p_seed.add_argument("--tx-per-day", type=int, default=5)

    p_an = sub.add_parser("analyze")
    p_an.add_argument("wallet", help="wallet address to analyze")

    args = parser.parse_args()
    if args.cmd == "seed":
        seed_data(args.wallet, days=args.days, tx_per_day=args.tx_per_day)
    elif args.cmd == "analyze":
        print(analyze_wallet(args.wallet))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
