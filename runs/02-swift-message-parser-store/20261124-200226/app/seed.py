"""Seed the database with example MT103 and MT202 raw messages. Idempotent: checks message_id before inserting."""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from src.parser import parse_swift
from datetime import datetime

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB_NAME = "sample_banking_02"

SAMPLES = [
    # some simple examples using the MT prefix and tag format
    "MT103|:20:ABC123|:32A:240101USD1234.56|:50K:/12345\nJOHN DOE|:59:/98765\nJANE DOE",
    "MT103|:20:ABC124|:32A:240101USD2500.00|:50K:/22222\nACME CORP|:59:/33333\nFOO BAR",
    "MT202|:20:DEF001|:32A:240102USD2000.00|:50K:/44444\nBANK A|:59:/55555\nBANK B",
    "MT202|:20:DEF002|:32A:240102USD1500.00|:50K:/66666\nBANK C|:59:/77777\nBANK D",
]

async def seed():
    if not DOCUMENTDB_URI:
        raise RuntimeError("DOCUMENTDB_URI not set in environment")
    client = AsyncIOMotorClient(DOCUMENTDB_URI)
    coll = client[DB_NAME]["swift_messages"]
    inserted = 0
    for raw in SAMPLES:
        parsed = parse_swift(raw)
        if not parsed:
            continue
        exists = await coll.find_one({"message_id": parsed.message_id})
        if exists:
            continue
        value_date = None
        if parsed.value_date:
            value_date = datetime.combine(parsed.value_date, datetime.min.time())
        doc = {
            "message_id": parsed.message_id,
            "message_type": parsed.message_type,
            "raw_text": raw,
            "sender": parsed.sender,
            "receiver": parsed.receiver,
            "amount": parsed.amount,
            "currency": parsed.currency,
            "value_date": value_date,
            "parsed": parsed.parsed,
        }
        await coll.insert_one(doc)
        inserted += 1
    print(f"Inserted {inserted} documents")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed())
