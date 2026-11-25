import asyncio
from .orchestrator import run

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--sample-size', type=int, default=10)
    args = p.parse_args()
    asyncio.run(run(args.sample_size))
