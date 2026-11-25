import sys
import argparse
sys.path.insert(0, "src")
from sample_orchestrator.run import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-id", required=True, dest="app_id")
    args = parser.parse_args()
    import asyncio
    asyncio.run(main(args.app_id))
