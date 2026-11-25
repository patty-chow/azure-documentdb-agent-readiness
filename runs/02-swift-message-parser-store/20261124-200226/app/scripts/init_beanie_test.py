import asyncio
from src.db import init_db, close_db

async def run():
    await init_db()
    print('Beanie initialized')
    await close_db()

if __name__ == '__main__':
    asyncio.run(run())
