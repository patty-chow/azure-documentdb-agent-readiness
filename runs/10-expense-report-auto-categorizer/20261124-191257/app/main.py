import argparse
import asyncio
import os
from src.db import init_db
from src.seed import seed
from src.processor import process_submitted_reports


async def _main(args):
    # Load .env if present
    from dotenv import load_dotenv
    load_dotenv()
    await init_db()
    if args.seed:
        await seed()
    use_ai = False if args.no_ai else True
    if use_ai and not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set — falling back to deterministic non-AI mode. Use --no-ai to suppress this message.")
        use_ai = False
    await process_submitted_reports(use_ai=use_ai)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="store_true", help="Run the seed data inserter before processing")
    parser.add_argument("--no-ai", action="store_true", help="Run deterministic fallback instead of calling LLM")
    args = parser.parse_args()
    asyncio.run(_main(args))
