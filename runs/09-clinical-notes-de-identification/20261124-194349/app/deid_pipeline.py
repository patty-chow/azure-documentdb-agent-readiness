"""De-identification pipeline CLI

Commands:
  dry-run  - process notes locally without calling OpenAI (safe for CI)
  run      - process notes using OpenAI (requires OPENAI_API_KEY)
"""
import os
import asyncio
import argparse
import re
from datetime import datetime
from typing import List

from src.db import init_db
from src.models import RawNote, DeidNote

# simple regex-based deid used for dry-run/testing
NAME_PATTERNS = [r"John Doe", r"Jane Smith", r"Mary Johnson", r"Alan S\\."]
DATE_PATTERN = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\w+ \d{1,2}, \d{4}\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{4}\b"
ID_PATTERN = r"\b(MRN|PID|INS|SSN)[:\- ]?\w+\b|\b\d{3}-\d{2}-\d{4}\b"
LOCATION_PATTERNS = [r"Seattle( General Hospital)?", r"Bellevue Clinic", r"Portland"]


def simple_deid(text: str) -> str:
    out = text
    for p in NAME_PATTERNS:
        out = re.sub(p, '[NAME]', out)
    out = re.sub(DATE_PATTERN, '[DATE]', out)
    out = re.sub(ID_PATTERN, '[ID]', out)
    for p in LOCATION_PATTERNS:
        out = re.sub(p, '[LOCATION]', out)
    return out


async def process_all(dry_run: bool = True, openai_client=None):
    client = await init_db()
    notes = await RawNote.find_all().to_list()
    print(f"Found {len(notes)} raw notes to process")
    created = 0
    for n in notes:
        if dry_run:
            deid_text = simple_deid(n.text)
            meta = {"method": "regex-dry-run"}
        else:
            # call OpenAI — keep experimentation minimal; caller must set OPENAI_API_KEY
            import openai
            prompt = (
                "You are a de-identification assistant. Replace all PHI (names, dates, locations, IDs) with placeholders: "
                "[NAME], [DATE], [LOCATION], [ID]. Return only the de-identified text.\n\nNote:\n" + n.text
            )
            resp = openai.ChatCompletion.create(
                model=os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[{"role":"user","content":prompt}],
                temperature=0.0,
                max_tokens=1024,
            )
            deid_text = resp['choices'][0]['message']['content'].strip()
            meta = {"method": "openai", "model": os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')}

        dn = DeidNote(text=deid_text, sourceId=str(n.id), deid_metadata=meta, tool_version="v0.1")
        # upsert behavior: ensure exactly one DeidNote per RawNote
        existing = await DeidNote.find(DeidNote.sourceId == str(n.id)).to_list()
        if existing:
            print(f"Deid note already exists for RawNote {n.id}; skipping insert.")
        else:
            await dn.insert()
            created += 1
    print(f"Created {created} de-identified notes")
    client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', choices=['dry-run', 'run'])
    args = parser.parse_args()
    dry = args.cmd == 'dry-run'
    if not dry and not os.environ.get('OPENAI_API_KEY'):
        print('OPENAI_API_KEY is required for run mode. Use dry-run for testing.')
        return
    asyncio.run(process_all(dry_run=dry))

if __name__ == '__main__':
    main()
