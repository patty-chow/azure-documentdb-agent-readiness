import argparse
import asyncio
from .db import init_db
from .orchestrator import orchestrate


async def main(app_id: str):
    await init_db()
    result = await orchestrate(app_id)
    print("Final document:", result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-id", required=True, dest="app_id")
    args = parser.parse_args()
    asyncio.run(main(args.app_id))
