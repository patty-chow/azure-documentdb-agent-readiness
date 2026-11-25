import re
from datetime import datetime
from typing import Dict, Any, Optional

# Very small SWIFT parser for MT103/MT202 sample messages. Extracts a few tags.
TAG_RE = re.compile(r":(\d{2,3}[A-Z]?):(.*?) (?=:\d{2,3}[A-Z]?:|$)", re.S)
# Simpler fallback patterns
TAG_SIMPLE_RE = re.compile(r":(\d{2,3}[A-Z]?):(.*?)(?=\n:|\n-|\Z)", re.S)


def parse_swift(raw: str) -> Dict[str, Any]:
    """Parse raw SWIFT message into a dict. This is a heuristic parser for demo only."""
    parsed = {}
    # find tags like :20:, :23B:, :32A:, :50K:, :59:
    for m in TAG_SIMPLE_RE.finditer(raw):
        tag = m.group(1)
        val = m.group(2).strip().replace('\n', ' ')
        parsed[tag] = val
    # message_type can be inferred from block 4 first 3 chars in examples like {1:F01...}
    # fallback: look for MT in first line
    mt = None
    m = re.search(r"MT(\d{3})", raw)
    if m:
        mt_num = m.group(1)
        if mt_num == '103':
            mt = 'MT103'
        elif mt_num == '202':
            mt = 'MT202'
    # extract :20: as message id
    message_id = parsed.get('20')
    # parse :32A: => YYMMDDCURAMT e.g., 231231USD1234,56
    value_date = None
    amount = None
    currency = None
    if '32A' in parsed:
        v = parsed['32A']
        # date first 6 chars
        try:
            datepart = v[:6]
            value_date = datetime.strptime(datepart, "%y%m%d").date()
            currency = v[6:9]
            amt = v[9:].replace(',', '.')
            # remove any non-numeric characters (like spaces)
            amt = re.sub(r"[^0-9\.\-]", "", amt)
            amount = float(amt) if amt else None
        except Exception:
            pass
    # try to glean sender/receiver from 50/59 or 50K
    sender = parsed.get('50K') or parsed.get('50')
    receiver = parsed.get('59') or parsed.get('57A')

    return {
        'message_type': mt or ('MT103' if '103' in raw else ('MT202' if '202' in raw else 'MT103')),
        'message_id': message_id,
        'sender': sender,
        'receiver': receiver,
        'value_date': value_date,
        'amount': amount,
        'currency': currency,
        'parsed': parsed,
        'raw_text': raw,
    }
