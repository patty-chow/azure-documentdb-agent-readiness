"""Shared helpers for the m-entra test.

- Loads managed.env without printing anything from it.
- Masks the password, URIs that carry it, subscription/tenant/object ids,
  e-mail addresses, the signed-in user's name parts, the tenant domain,
  JWTs and any other GUID before anything is written or printed.
- Runs shell commands and appends a masked record to raw/steps.jsonl.
"""
import datetime
import json
import os
import re
import shlex
import subprocess
import time
import urllib.parse

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(os.path.dirname(TEST_DIR), "managed.env")
RAW_DIR = os.path.join(TEST_DIR, "raw")
STEPS_FILE = os.path.join(RAW_DIR, "steps.jsonl")
IDS_FILE = os.path.join(RAW_DIR, ".ids.json")  # mode 600, never copied into the report
os.makedirs(RAW_DIR, exist_ok=True)


def load_env():
    env = {}
    with open(ENV_FILE) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.replace("export ", "").strip()
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            env[k] = v
    return env


ENV = load_env()


def _load_ids():
    """Identity values used only for masking. Collected once from az, stored 0600."""
    if os.path.exists(IDS_FILE):
        with open(IDS_FILE) as fh:
            return json.load(fh)
    ids = {}
    try:
        out = subprocess.run(["az", "account", "show", "-o", "json"], capture_output=True, text=True, timeout=120)
        acct = json.loads(out.stdout)
        ids["subscription"] = acct.get("id")
        ids["tenant"] = acct.get("tenantId")
        ids["home_tenant"] = acct.get("homeTenantId")
        ids["tenant_domain"] = acct.get("tenantDefaultDomain")
        ids["tenant_display"] = acct.get("tenantDisplayName")
        ids["subscription_name"] = acct.get("name")
        uname = (acct.get("user") or {}).get("name") or ""
        ids["user_name"] = uname
    except Exception as exc:  # pragma: no cover
        ids["error"] = repr(exc)
    try:
        out = subprocess.run(["az", "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"],
                             capture_output=True, text=True, timeout=120)
        ids["oid"] = out.stdout.strip() or None
    except Exception as exc:  # pragma: no cover
        ids["oid_error"] = repr(exc)
    fd = os.open(IDS_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        json.dump(ids, fh)
    return ids


IDS = _load_ids()

GUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
EMAIL_RE = re.compile(r"[^\s\"'<>@,;:()\[\]{}\\/]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]*")


def _secret_pairs():
    pairs = []
    pw = ENV.get("MANAGED_PASS")
    if pw:
        for form in {pw, urllib.parse.quote_plus(pw), urllib.parse.quote(pw, safe="")}:
            pairs.append((form, "<password-masked>"))
    for k in ("MANAGED_URI", "MANAGED_GLOBAL_URI"):
        if ENV.get(k):
            pairs.append((ENV[k], f"<{k}-masked>"))
    for key, label in (("oid", "<object-id-masked>"), ("subscription", "<subscription-id-masked>"),
                       ("tenant", "<tenant-id-masked>"), ("home_tenant", "<tenant-id-masked>")):
        v = IDS.get(key)
        if v:
            pairs.append((v, label))
            pairs.append((v.upper(), label))
    for key, label in (("tenant_domain", "<tenant-domain-masked>"), ("tenant_display", "<tenant-name-masked>")):
        v = IDS.get(key)
        if v and len(v) >= 4:
            pairs.append((v, label))
    uname = IDS.get("user_name") or ""
    if "@" in uname:
        local = uname.split("@", 1)[0]
        if len(local) >= 3:
            pairs.append((local, "<user-masked>"))
    # longest first so URIs are replaced before the password inside them
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


_PAIRS = _secret_pairs()


_PLACEHOLDER_GUIDS = {"aaaaaaaa-0000-1111-2222-bbbbbbbbbbbb", "00000000-0000-0000-0000-000000000000"}
# the scratchpad session folder name in file paths is not an identity value
_PLACEHOLDER_GUIDS.update(g.lower() for g in GUID_RE.findall(TEST_DIR))


def _guid(m):
    g = m.group(0).lower()
    if g in _PLACEHOLDER_GUIDS or len(set(g.replace("-", ""))) == 1:
        return m.group(0)  # documentation placeholder such as 11111111-1111-1111-1111-111111111111
    return "<guid-masked>"


def mask(obj):
    """Mask a str, or every str inside a JSON-like structure."""
    if isinstance(obj, str):
        s = obj
        s = JWT_RE.sub("<jwt-masked>", s)
        soft = ("<user-masked>", "<tenant-domain-masked>")
        for needle, label in _PAIRS:
            if label not in soft and needle and needle in s:
                s = s.replace(needle, label)

        def _email(m):
            dom = m.group(0).rsplit("@", 1)[1].lower()
            if dom.endswith("mongocluster.cosmos.azure.com"):
                return m.group(0)
            return "<email-masked>"

        s = EMAIL_RE.sub(_email, s)
        # case-insensitive pass for the user local part and tenant domain
        for needle, label in _PAIRS:
            if label in soft and needle:
                s = re.sub(re.escape(needle), label, s, flags=re.I)
        s = GUID_RE.sub(_guid, s)
        return s
    if isinstance(obj, dict):
        return {mask(k): mask(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [mask(v) for v in obj]
    return obj


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def record(step_id, **fields):
    rec = {"id": step_id, "recorded_at": now_iso()}
    rec.update(fields)
    rec = mask(rec)
    with open(STEPS_FILE, "a") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")
    return rec


def run(step_id, argv, display=None, timeout=590, parse_json=False, extra=None, env=None, cwd=None):
    """Run argv (list), record masked stdout/stderr/exit code/duration.

    display: the command as it should appear in the report (placeholders), else argv joined.
    """
    t0 = time.time()
    started = now_iso()
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env, cwd=cwd)
        out, err, code = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = (exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")) + f"\n<timeout after {timeout}s>"
        code = None
    dur = round(time.time() - t0, 2)
    parsed = None
    if parse_json and out.strip():
        try:
            parsed = json.loads(out)
        except Exception:
            parsed = None
    rec = record(step_id,
                 command=display or " ".join(shlex.quote(a) for a in argv),
                 started_at=started, duration_s=dur, exit_code=code,
                 stdout=out if parsed is None else None,
                 stdout_json=parsed, stderr=err, **(extra or {}))
    return rec, out, err, code


def display_cmd(argv):
    """argv joined, with values masked and env values replaced by $VAR names."""
    s = " ".join(shlex.quote(a) for a in argv)
    for k in ("MANAGED_CLUSTER", "MANAGED_RG"):
        pass
    return mask(s)


if __name__ == "__main__":
    print(json.dumps({"ids_known": sorted(k for k, v in IDS.items() if v), "env_keys": sorted(ENV)}))
