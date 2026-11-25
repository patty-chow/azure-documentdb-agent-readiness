"""Wrapper to run the sample orchestrator with src on sys.path."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--application-id", required=True)
    args = parser.parse_args()

    from sample_orchestrator.run import main as run_main

    import asyncio
    asyncio.run(run_main(args.application_id))
