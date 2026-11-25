"""One-shot script that queries the substitute function for a given SKU and prints results.

This script connects to the database, ensures Beanie is initialized, and calls the same
logic used by the FastAPI route to find substitutes. It is useful for automated verification
without starting the FastAPI server.
"""

import asyncio
import sys

from app.config import settings
from app.models import Product
from app.routes import find_substitutes
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie


async def run(product_id: str):
    client = AsyncIOMotorClient(settings.DOCUMENTDB_URI)
    await init_beanie(database=client[settings.DB_NAME], document_models=[Product])
    results = await find_substitutes(product_id, k=5)
    for r in results:
        print(f"{r.product_id}\t{r.name}\t{r.score}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/query_substitutes.py SKU-000000")
        sys.exit(1)
    asyncio.run(run(sys.argv[1]))
