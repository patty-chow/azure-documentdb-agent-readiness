"""Seed script to upload sample KYC documents and demonstrate outcomes.
This script reads DOCUMENTDB_URI from env, and OPENAI_API_KEY must be set to call the extraction model.
"""
import asyncio
import os
from httpx import AsyncClient

SAMPLES = [
    ("complete.txt", "Name: Alice Example\nDOB: 1990-01-01\nAddress: 1 Azure Way, Cloud City\nID: AZ1234567"),
    ("partial.txt", "Name: Bob MissingID\nDOB: 1985-05-05\nAddress: 42 Example Lane\n"),
    ("garbled.txt", "This is not a standard form. Only a name: Charlie and some numbers 555-12.")
]

async def upload_sample(name, content):
    async with AsyncClient() as client:
        files = {'file': (name, content, 'text/plain')}
        resp = await client.post('http://127.0.0.1:8000/upload', files=files)
        print(name, resp.status_code, resp.text)

async def main():
    for name, content in SAMPLES:
        await upload_sample(name, content)

if __name__ == '__main__':
    # This script assumes the sample app is running on localhost:8000
    asyncio.run(main())
