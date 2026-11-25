import re
from datetime import datetime
from typing import Optional
from .models import ParsedSwift

TAG_RE = re.compile(r"(:\d{2}[A-Z]?:)([^:\n]+)")


def parse_swift(raw: str) -> Optional[ParsedSwift]:
    message_type = ""
    payload = raw
    if raw.startswith("MT"):
        parts = raw.split("|", 1)
        if len(parts) == 2:
            message_type, payload = parts[0], parts[1]
        else:
            message_type = parts[0]
            payload = raw
    tags = {}
    for m in TAG_RE.finditer(payload):
        tag = m.group(1).strip(":")
        val = m.group(2).strip()
        tags[tag] = val
    message_id = tags.get("20") or tags.get("20:") or f"raw-{abs(hash(raw))}"
    amt = None
    cur = None
    value_date = None
    if "32A" in tags:
        v = tags["32A"].strip()
        try:
            date_s = v[0:6]
            value_date = datetime.strptime(date_s, "%y%m%d").date()
            cur = v[6:9]
            amt_s = v[9:]
            amt = float(amt_s)
        except Exception:
            pass
    sender = tags.get("50K")
    receiver = tags.get("59")
    parsed = {"tags": tags}
    if not message_type:
        if "23B" in tags or "32A" in tags:
            message_type = "MT103"
        else:
            message_type = "MT202"
    try:
        parsed_obj = ParsedSwift(
            message_id=message_id,
            message_type=message_type,
            sender=sender,
            receiver=receiver,
            amount=amt,
            currency=cur,
            value_date=value_date,
            parsed=parsed,
        )
        return parsed_obj
    except Exception:
        return None
