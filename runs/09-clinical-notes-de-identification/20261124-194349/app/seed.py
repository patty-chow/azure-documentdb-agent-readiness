"""Seed the sample database with synthetic clinical notes.
This script is idempotent: it creates notes only if no RawNote with
metadata['seed'] == True exists.
"""
import asyncio
import os
from datetime import datetime
from src.db import init_db
from src.models import RawNote

SYNTHETIC_NOTES = [
    {
        "text": "Patient John Doe presented on 03/14/2024 complaining of chest pain. MRN: MRN12345. Lives in Seattle.",
        "metadata": {"author": "system", "seed": True},
    },
    {
        "text": "Jane Smith had surgery on 2024-01-10 at Bellevue Clinic. SSN: 123-45-6789.",
        "metadata": {"author": "system", "seed": True},
    },
    {
        "text": "Follow up appointment for patient Mary Johnson scheduled for April 2, 2024. Contact: (555) 123-4567.",
        "metadata": {"author": "system", "seed": True},
    },
    {
        "text": "Patient with ID PID-98765 from Portland reports improved symptoms since 02/2024.",
        "metadata": {"author": "system", "seed": True},
    },
    {
        "text": "Emergency visit: Alan S. at 11/11/23, transported from Seattle General Hospital. Insurance ID: INS-4455.",
        "metadata": {"author": "system", "seed": True},
    },
]

async def run():
    client = await init_db()
    # check if seeded
    existing = await RawNote.find({"metadata.seed": True}).to_list()
    if existing:
        print(f"Already seeded ({len(existing)} notes).")
        return
    docs = []
    for n in SYNTHETIC_NOTES:
        docs.append(RawNote(text=n['text'], metadata=n['metadata']))
    await RawNote.insert_many(docs)
    print(f"Inserted {len(docs)} synthetic notes.")
    client.close()

if __name__ == '__main__':
    asyncio.run(run())
