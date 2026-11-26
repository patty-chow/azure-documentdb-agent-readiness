"""Shared helpers for the m-concerns test. Never prints the password or a URI."""
import json
import os
import re
import subprocess
import urllib.parse
import warnings

from bson import json_util

warnings.filterwarnings("ignore", message=".*CosmosDB.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pymongo")

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, "..", "managed.env")


def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            if k.startswith("export "):
                k = k[len("export "):].strip()
            v = v.strip()
            if v and v[0] in "\"'" and v[-1] == v[0]:
                v = v[1:-1]
            env[k] = v
    return env


ENV = load_env()
_SECRETS = set()
pw = ENV.get("MANAGED_PASS", "")
if pw:
    _SECRETS.update({pw, urllib.parse.quote(pw, safe=""), urllib.parse.quote_plus(pw)})
for k in ("MANAGED_URI", "MANAGED_GLOBAL_URI"):
    if ENV.get(k):
        _SECRETS.add(ENV[k])

_MASKS = {}  # exact string -> mask label (subscription / tenant ids), filled lazily


def load_az_masks():
    try:
        r = subprocess.run(["az", "account", "show", "--query", "{s:id,t:tenantId}", "-o", "json"],
                           capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout)
        if d.get("s"):
            _MASKS[d["s"]] = "<subscription-id>"
        if d.get("t"):
            _MASKS[d["t"]] = "<tenant-id>"
    except Exception:
        pass


URI_RE = re.compile(r"(mongodb(?:\+srv)?://)[^@/\s]*@")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def redact(s):
    s = str(s)
    for sec in sorted(_SECRETS, key=len, reverse=True):
        if sec:
            s = s.replace(sec, "<redacted>")
    s = URI_RE.sub(r"\1<userinfo-redacted>@", s)
    s = EMAIL_RE.sub("<email-masked>", s)
    for raw, label in _MASKS.items():
        s = s.replace(raw, label)
        s = s.replace(raw.upper(), label)
    return s


def to_jsonable(doc):
    """Exact BSON -> relaxed Extended JSON -> Python structure, redacted."""
    try:
        text = json_util.dumps(doc, json_options=json_util.RELAXED_JSON_OPTIONS)
        return json.loads(redact(text))
    except Exception:
        return redact(repr(doc))
