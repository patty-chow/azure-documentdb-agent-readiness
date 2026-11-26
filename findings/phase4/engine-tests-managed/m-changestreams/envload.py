"""Shared helpers for m-changestreams: env loading, scrubbing, JSON conversion, command capture.
Never prints or stores the password or a URI containing it."""
import json
import os
import re
import urllib.parse
import warnings

from bson import json_util
from bson.json_util import JSONOptions, JSONMode
from pymongo import monitoring
from pymongo.errors import OperationFailure, PyMongoError

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(os.path.dirname(HERE), "managed.env")

warnings.filterwarnings("ignore", message=".*CosmosDB.*")
warnings.filterwarnings("ignore", message=".*cosmos.*")


def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            env[k.strip()] = v
    return env


ENV = load_env()
_SECRETS = set()
_pw = ENV.get("MANAGED_PASS")
if _pw:
    _SECRETS.add(_pw)
    _SECRETS.add(urllib.parse.quote(_pw, safe=""))
    _SECRETS.add(urllib.parse.quote_plus(_pw))
for key in ("MANAGED_URI", "MANAGED_GLOBAL_URI"):
    u = ENV.get(key, "")
    m = re.match(r"mongodb(?:\+srv)?://[^:/@]+:([^@]+)@", u)
    if m:
        _SECRETS.add(m.group(1))
        _SECRETS.add(urllib.parse.unquote(m.group(1)))
_SECRETS = {s for s in _SECRETS if s and len(s) >= 4}

GUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URI_CRED_RE = re.compile(r"(mongodb(?:\+srv)?://[^:/@\s]+:)[^@\s]+@")


def scrub(text):
    if not isinstance(text, str):
        return text
    for s in sorted(_SECRETS, key=len, reverse=True):
        text = text.replace(s, "<redacted>")
    text = URI_CRED_RE.sub(r"\1<redacted>@", text)
    text = EMAIL_RE.sub("<email-masked>", text)
    # GUID masking would also hide lsid UUIDs, which are random session ids; mask them anyway to be safe
    text = GUID_RE.sub("<guid-masked>", text)
    return text


RELAXED = JSONOptions(json_mode=JSONMode.RELAXED, tz_aware=True)


def j(obj):
    """bson -> JSON-able python (relaxed extended JSON)."""
    return json.loads(json_util.dumps(obj, json_options=RELAXED))


def err_info(e):
    info = {"exception": type(e).__name__, "message": scrub(str(e))}
    if isinstance(e, OperationFailure):
        d = e.details or {}
        info["code"] = e.code
        info["codeName"] = d.get("codeName")
        info["errmsg"] = scrub(d.get("errmsg")) if d.get("errmsg") else d.get("errmsg")
        info["errorLabels_server"] = d.get("errorLabels")
        info["errorLabels_driver"] = sorted(getattr(e, "_error_labels", set()) or [])
        info["details"] = j(d)
    return info


def clean_cmd(doc):
    """Drop noise and the $clusterTime signature hash from a captured command or reply."""
    d = j(doc)
    if isinstance(d, dict):
        ct = d.get("$clusterTime")
        if isinstance(ct, dict) and isinstance(ct.get("signature"), dict):
            ct["signature"] = {"hash": "<omitted>", "keyId": ct["signature"].get("keyId")}
    return d


CAPTURE_NAMES = {"aggregate", "getMore", "killCursors", "insert", "update", "delete", "drop",
                 "dropDatabase", "create", "collMod", "createIndexes", "findAndModify", "find"}


class Capture(monitoring.CommandListener):
    """Captures started/succeeded/failed events for data commands (never auth commands)."""

    def __init__(self):
        self.events = []
        self.enabled = True

    def _ok(self, name):
        return self.enabled and name in CAPTURE_NAMES

    def started(self, event):
        if self._ok(event.command_name):
            self.events.append({"kind": "started", "request_id": event.request_id,
                                "command_name": event.command_name, "db": event.database_name,
                                "command": clean_cmd(event.command)})

    def succeeded(self, event):
        if self._ok(event.command_name):
            self.events.append({"kind": "succeeded", "request_id": event.request_id,
                                "command_name": event.command_name,
                                "duration_ms": round(event.duration_micros / 1000.0, 1),
                                "reply": clean_cmd(event.reply)})

    def failed(self, event):
        if self._ok(event.command_name):
            self.events.append({"kind": "failed", "request_id": event.request_id,
                                "command_name": event.command_name,
                                "duration_ms": round(event.duration_micros / 1000.0, 1),
                                "failure": clean_cmd(event.failure)})

    def mark(self):
        return len(self.events)

    def since(self, mark):
        return self.events[mark:]
