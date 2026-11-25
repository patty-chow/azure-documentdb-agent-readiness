import os
import json
import asyncio
from typing import Dict, Any
import openai

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

PROMPT_TEMPLATE = '''
You are an extraction assistant. Given the raw text of a KYC document, extract the following fields as JSON exactly with keys: name, dob, address, government_id. Also include a "raw" key that can contain any extra fields.
Return only valid JSON. If a field cannot be found, set it to null.

Document:
"""
{document}
"""

Respond with JSON only.
'''

async def extract_entities(document_text: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set in environment; cannot call OpenAI")
    # Use the OpenAI Chat completion API asynchronously
    prompt = PROMPT_TEMPLATE.format(document=document_text)
    # The openai package currently doesn't offer an official async chat completion in older versions.
    # We'll call the sync API in a thread to avoid blocking the event loop for this sample.
    loop = asyncio.get_event_loop()
    def call_sync():
        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return resp
    resp = await loop.run_in_executor(None, call_sync)
    # Parse the text response --- it should be JSON
    text = resp['choices'][0]['message']['content']
    try:
        parsed = json.loads(text)
    except Exception:
        # not valid JSON
        return {"name": None, "dob": None, "address": None, "government_id": None, "raw": {"text": text}}
    # Ensure keys exist
    for k in ("name","dob","address","government_id","raw"):
        if k not in parsed:
            parsed[k] = None if k != 'raw' else {}
    return parsed
