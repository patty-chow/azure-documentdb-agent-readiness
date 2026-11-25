import asyncio
from .db import init_db, get_client
from .agents import match_agent, merge_agent, audit_agent, write_golden
from beanie import PydanticObjectId

async def resolve_one(profile_id):
    # find candidates
    candidates = await match_agent(profile_id, k=5)
    if not candidates:
        print("No candidates")
        return None
    # fetch full docs for auditing
    client = await get_client()
    db_name = "sample_customer_360_20"
    coll = client[db_name]["profiles"]
    source_docs = []
    ids = []
    for c in candidates:
        doc = await coll.find_one({"_id": c['_id']})
        source_docs.append(doc)
        ids.append(c['_id'])
    merged, confidence, method = await merge_agent(source_docs)
    gr = await write_golden(merged, provenance=[str(i) for i in ids])
    audit_entry = await audit_agent(merged, ids, confidence, source_docs, note=f"merged by {method}")
    # handle beanie Document or raw dict
    def get_id(obj):
        if hasattr(obj, 'id'):
            return getattr(obj, 'id')
        if isinstance(obj, dict):
            return obj.get('_id')
        return None
    print("Wrote golden record", get_id(gr), "audit", get_id(audit_entry))
    return gr

async def run(limit=10):
    await init_db()
    client = await get_client()
    db_name = "sample_customer_360_20"
    coll = client[db_name]["profiles"]
    cur = coll.find({}).limit(limit)
    async for doc in cur:
        await resolve_one(doc['_id'])

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--sample-size', type=int, default=10)
    args = p.parse_args()
    asyncio.run(run(args.sample_size))