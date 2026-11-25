"""Idempotent index creation for the sample collection."""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB_NAME = "sample_banking_02"

async def create_indexes():
    if not DOCUMENTDB_URI:
        raise RuntimeError("DOCUMENTDB_URI not set in environment")
    client = AsyncIOMotorClient(DOCUMENTDB_URI)
    coll = client[DB_NAME]["swift_messages"]
    # unique index on message_id
    try:
        await coll.create_index([("message_id", 1)], unique=True, name="ux_message_id")
    except OperationFailure as e:
        print("ux_message_id index create skipped:", e)
    # compound index for aggregations
    try:
        await coll.create_index([("message_type", 1), ("value_date", 1)], name="ix_type_value_date")
    except OperationFailure as e:
        print("ix_type_value_date create skipped:", e)
    # index on amount for range queries
    try:
        await coll.create_index([("amount", -1)], name="ix_amount_desc")
    except OperationFailure as e:
        print("ix_amount_desc create skipped:", e)
    print("Indexes ensured")
    client.close()

if __name__ == "__main__":
    asyncio.run(create_indexes())
