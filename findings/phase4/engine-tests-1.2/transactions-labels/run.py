#!/usr/bin/env python3
"""transactions-labels -- ENGINE 1.2.0 RERUN against documentdb-local (container ddb-engine-test).

Owns database t_txn only; drops it at the start (fresh state) and again at the end.

Rerun:
  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I \
    /private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests-1.2/transactions-labels/run.py

Takes about 2.5 minutes (deliberate waits of 36 s, 36 s and 40 s; pass --skip-idle to leave out section 4 while
debugging). Reads LOCAL_URI from scratchpad/engine-tests/local.env and never prints or writes credentials: every
line printed or written passes through redact(). Writes report.json and run.out next to this file and compares
the results with the engine 0.117 baseline report. Every docker call is read-only (inspect, logs, exec cat/grep);
the container is never stopped, restarted or removed.
"""
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import threading
import time
import traceback
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from urllib.parse import parse_qsl, unquote, urlsplit

import bson
import pymongo
from bson import Int64, json_util
from bson.binary import Binary, UUID_SUBTYPE
from pymongo import MongoClient, monitoring
from pymongo.errors import OperationFailure, PyMongoError
from pymongo.read_concern import ReadConcern

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad"
ENV_FILE = os.path.join(SCRATCH, "engine-tests", "local.env")
BASELINE = ("/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/"
            "engine-tests/transactions-labels/report.json")
CONTAINER = "ddb-engine-test"
DB, COLL = "t_txn", "docs"
IDLE_S = 36
LIFETIME_GAP_S = 8
LIFETIME_WRITES = 6
COMMIT_A_DELAY_S = 0.5
WATCHDOG_S = 285
SKIP_IDLE = "--skip-idle" in sys.argv


# ----------------------------------------------------------------------------- credentials and redaction
def load_env(path):
    vals = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            if k.startswith("export "):
                k = k[len("export "):].strip()
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            vals[k] = v
    return vals


ENV = load_env(ENV_FILE)
URI = ENV["LOCAL_URI"]
_secrets = {v for k, v in ENV.items() if "PASS" in k.upper() and v}
_m = re.match(r"^mongodb(?:\+srv)?://[^:@/]+:([^@/]+)@", URI)
if _m:
    _secrets.update({_m.group(1), unquote(_m.group(1))})
SECRETS = sorted((s for s in _secrets if len(s) >= 4), key=len, reverse=True)


def redact(s):
    s = str(s)
    for sec in SECRETS:
        s = s.replace(sec, "***")
    return re.sub(r"(mongodb(?:\+srv)?://)[^@/\s]*@", r"\1***@", s)


OUT_LINES = []


def log(msg=""):
    msg = redact(msg)
    OUT_LINES.append(msg)
    print(msg, flush=True)


# ----------------------------------------------------------------------------- JSON helpers
def jsonable(o):
    if isinstance(o, Mapping):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set, frozenset)):
        return [jsonable(v) for v in o]
    if o is None or isinstance(o, (str, bool, int, float)):
        return o
    try:
        return json.loads(json_util.dumps(o, json_options=json_util.RELAXED_JSON_OPTIONS))
    except Exception:
        return repr(o)


# ----------------------------------------------------------------------------- wire capture (CommandListener)
T0 = time.monotonic()
EVENTS = []
_EV_LOCK = threading.Lock()
_SEQ = [0]
WIRE_CMDS = {"insert", "update", "delete", "find", "findAndModify", "aggregate", "getMore", "commitTransaction",
             "abortTransaction", "create", "drop", "dropDatabase", "endSessions"}


def now_s():
    return round(time.monotonic() - T0, 3)


def _push(ev):
    with _EV_LOCK:
        _SEQ[0] += 1
        ev = {"seq": _SEQ[0], **ev}
        EVENTS.append(ev)


class Wire(monitoring.CommandListener):
    """Records the exact command document each client sends and the exact reply or failure document."""

    def __init__(self, tag):
        self.tag = tag

    def started(self, e):
        if e.command_name in WIRE_CMDS:
            _push({"t_s": now_s(), "client": self.tag, "event": "started", "request_id": e.request_id,
                   "db": e.database_name, "command_name": e.command_name, "command": jsonable(e.command)})

    def succeeded(self, e):
        if e.command_name in WIRE_CMDS:
            _push({"t_s": now_s(), "client": self.tag, "event": "succeeded", "request_id": e.request_id,
                   "command_name": e.command_name, "duration_ms": round(e.duration_micros / 1000, 1),
                   "reply": jsonable(e.reply)})

    def failed(self, e):
        if e.command_name in WIRE_CMDS:
            _push({"t_s": now_s(), "client": self.tag, "event": "failed", "request_id": e.request_id,
                   "command_name": e.command_name, "duration_ms": round(e.duration_micros / 1000, 1),
                   "failure": jsonable(e.failure)})


def mark():
    with _EV_LOCK:
        return _SEQ[0]


def wire_since(m):
    with _EV_LOCK:
        return [ev for ev in EVENTS if ev["seq"] > m]


def wire_for(m, lsid):
    """Events since mark m whose command carries this lsid, plus their replies (matched by request_id)."""
    key = json.dumps(jsonable(lsid), sort_keys=True)
    with _EV_LOCK:
        evs = [ev for ev in EVENTS if ev["seq"] > m]
    ids = {ev["request_id"] for ev in evs if ev["event"] == "started"
           and json.dumps((ev.get("command") or {}).get("lsid"), sort_keys=True) == key}
    return [ev for ev in evs if ev["request_id"] in ids]


# ----------------------------------------------------------------------------- errors and phrasing
def err(exc):
    """code, codeName, errmsg and errorLabels exactly as the server sent them, plus the labels the driver holds."""
    d = {"exception": type(exc).__name__, "message": redact(str(exc))}
    if isinstance(exc, OperationFailure):
        det = dict(exc.details or {})
        d["code"] = det.get("code", exc.code)
        d["codeName"] = det.get("codeName")
        d["errmsg"] = det.get("errmsg")
        d["errorLabels_present"] = "errorLabels" in det
        if "errorLabels" in det:
            d["errorLabels"] = det.get("errorLabels")
        d["server_reply"] = jsonable(det)
    if isinstance(exc, PyMongoError):
        d["labels_seen_by_driver"] = sorted(getattr(exc, "_error_labels", None) or [])
    return d


def _reply_of(x):
    if isinstance(x, dict) and isinstance(x.get("server_reply"), dict):
        return x["server_reply"]
    return x


def lbl(x):
    x = _reply_of(x)
    if not isinstance(x, dict):
        return "no reply"
    if "errorLabels" in x:
        return f"errorLabels {x['errorLabels']}"
    return "no errorLabels field"


def desc(x):
    """One-line description of an err() dict, a raw reply or a success placeholder."""
    if not isinstance(x, dict):
        return str(x)
    if x.get("exception") and "server_reply" not in x:
        return f"client-side {x['exception']} \"{x.get('message')}\" (nothing sent to the server)"
    x = _reply_of(x)
    if x.get("ok") in (1, 1.0) and "code" not in x:
        return f"ok: {x.get('ok')}"
    return f"code {x.get('code')} {x.get('codeName')} \"{x.get('errmsg')}\" with {lbl(x)}"


def norm_desc(x):
    """Copy of an err() dict or reply with the per-request ActivityId removed from errmsg, for grouping."""
    if not isinstance(x, dict):
        return x
    y = dict(x)
    if isinstance(y.get("server_reply"), dict):
        y["server_reply"] = dict(y["server_reply"])
        tgt = y["server_reply"]
    else:
        tgt = y
    if isinstance(tgt.get("errmsg"), str):
        tgt["errmsg"] = re.sub(r"\[ActivityId=[0-9a-fA-F-]+\]\s*", "", tgt["errmsg"])
    return y


def is_ok(x):
    x = _reply_of(x)
    return isinstance(x, dict) and x.get("ok") in (1, 1.0) and "code" not in x and not x.get("exception")


# ----------------------------------------------------------------------------- raw wire helpers
def raw(client, dbname, doc):
    """Send one command document verbatim (PyMongo adds only $db; no implicit session) and return the reply."""
    with client._conn_for_writes(None, "raw") as conn:
        return conn.command(dbname, dict(doc), check=False)


class RawTxn:
    """A transaction driven entirely by hand-built commands on a fresh logical session id."""

    def __init__(self, client):
        self.client = client
        self.lsid = {"id": Binary(uuid.uuid4().bytes, UUID_SUBTYPE)}
        self.txn = Int64(1)
        self.started = False

    def _ids(self):
        return {"lsid": self.lsid, "txnNumber": self.txn, "autocommit": False}

    def update(self, q, u):
        doc = {"update": COLL, "updates": [{"q": q, "u": u}], **self._ids()}
        if not self.started:
            doc["startTransaction"] = True
            self.started = True
        return doc, raw(self.client, DB, doc)

    def commit(self, wc=None):
        doc = {"commitTransaction": 1, **self._ids()}
        if wc:
            doc["writeConcern"] = wc
        return doc, raw(self.client, "admin", doc)

    def abort(self):
        doc = {"abortTransaction": 1, **self._ids()}
        return doc, raw(self.client, "admin", doc)

    def end(self):
        try:
            return raw(self.client, "admin", {"endSessions": [self.lsid]})
        except Exception as e:  # noqa: BLE001
            return err(e)


# ----------------------------------------------------------------------------- docker (read-only)
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def run_cmd(args, timeout=60):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def container_facts():
    out = {}
    fmt = ('{"image_ref":{{json .Config.Image}},"image_id":{{json .Image}},"container_created":{{json .Created}},'
           '"started_at":{{json .State.StartedAt}},"restart_count":{{json .RestartCount}},'
           '"status":{{json .State.Status}},'
           '"health":{{if .State.Health}}{{json .State.Health.Status}}{{else}}null{{end}}}')
    rc, so, se = run_cmd(["docker", "inspect", "--format", fmt, CONTAINER])
    try:
        out.update(json.loads(so))
    except Exception:  # noqa: BLE001
        out["inspect_error"] = redact((so + se)[:500])
    if out.get("image_id"):
        fmt2 = '{"labels":{{json .Config.Labels}},"repo_digests":{{json .RepoDigests}},"image_created":{{json .Created}}}'
        rc, so, se = run_cmd(["docker", "image", "inspect", "--format", fmt2, out["image_id"]])
        try:
            img = json.loads(so)
            labels = img.get("labels") or {}
            out["oci_version"] = labels.get("org.opencontainers.image.version")
            out["oci_revision"] = labels.get("org.opencontainers.image.revision")
            out["oci_created"] = labels.get("org.opencontainers.image.created")
            out["repo_digests"] = img.get("repo_digests")
            out["image_created"] = img.get("image_created")
        except Exception:  # noqa: BLE001
            out["image_inspect_error"] = redact((so + se)[:500])
    return out


def topology_versions():
    rc, so, se = run_cmd(["docker", "logs", "--since", "30m", CONTAINER])
    lines = [ANSI.sub("", ln) for ln in (so + "\n" + se).splitlines() if "Topology acquired" in ln]
    if not lines:
        return {"found": False}
    last = lines[-1]
    out = {"found": True, "log_line": redact(last[:260])}
    m = re.search(r'data: "([0-9a-fA-F]+)"', last)
    if m:
        try:
            out["decoded"] = jsonable(bson.decode(bytes.fromhex(m.group(1))))
        except Exception as e:  # noqa: BLE001
            out["decode_error"] = repr(e)
    return out


LABEL_STRINGS = ["TransientTransactionError", "UnknownTransactionCommitResult", "RetryableWriteError",
                 "NoSuchTransaction", "WriteConflict", "Could not acquire lock", "lock_timeout",
                 "idle_in_transaction_session_timeout", "transaction_timeout", "allow_transaction_snapshot"]


def gateway_static_facts():
    cmds, res = [], {}
    cmds.append("docker exec ddb-engine-test sh -c 'cat /tmp/SetupConfiguration_*.json'  "
                "(parsed in Python; only the DynamicConfigurationFile value is kept)")
    rc, so, se = run_cmd(["docker", "exec", CONTAINER, "sh", "-c", "cat /tmp/SetupConfiguration_*.json"], 30)
    dyn = None
    try:
        dyn = json.loads(so).get("DynamicConfigurationFile")
    except Exception:  # noqa: BLE001
        res["setup_configuration_error"] = redact(se[:300])
    res["DynamicConfigurationFile"] = dyn
    if dyn:
        cmds.append(f"docker exec ddb-engine-test cat {dyn}")
        rc, so, se = run_cmd(["docker", "exec", CONTAINER, "cat", dyn], 30)
        try:
            res["dynamic_configuration"] = json.loads(so)
        except Exception:  # noqa: BLE001
            res["dynamic_configuration_raw"] = redact(so[:300])
    rc, so, se = run_cmd(["docker", "exec", CONTAINER, "sh", "-c",
                          "find /home/documentdb/gateway -type f -name documentdb_gateway 2>/dev/null | head -1"], 30)
    binpath = so.strip()
    res["gateway_binary"] = binpath
    if binpath:
        loop = "; ".join(f"printf '%s\\t' {shlex.quote(s)}; grep -a -o -F {shlex.quote(s)} {shlex.quote(binpath)} | wc -l"
                         for s in LABEL_STRINGS)
        cmds.append(f"docker exec ddb-engine-test sh -c \"grep -a -o -F '<string>' {binpath} | wc -l\"  for each of "
                    + ", ".join(LABEL_STRINGS))
        rc, so, se = run_cmd(["docker", "exec", CONTAINER, "sh", "-c", loop], 120)
        counts = {}
        for ln in so.splitlines():
            if "\t" in ln:
                k, v = ln.split("\t", 1)
                try:
                    counts[k] = int(v.strip())
                except ValueError:
                    counts[k] = v.strip()
        res["occurrences_in_gateway_binary"] = counts
    return cmds, res


KEEP = re.compile(r"Lock not available|lock timeout|idle-in-transaction|transaction timeout|terminating connection|"
                  r"expired transaction|"
                  r"drop a transaction|abandon|Connection error|connection closed|NoSuchTransaction|WriteConflict|"
                  r"InternalError|could not serialize|deadlock|read concern|statement timeout", re.I)
DROP = re.compile(r"password|secret|GATEWAY-FILE|cron job|Topology acquired|accept a TCP|stream_driver", re.I)
TIDY = [re.compile(p) for p in (r'network\.connection\.id=\S+ ', r'request\.id=\d+ ', r'span\.kind="[a-z]+" ',
                                r'db\.system\.name="[a-z]+" ', r'network\.protocol\.name=TCP ', r'tls\.established=true ')]


def container_logs(since_iso):
    rc, so, se = run_cmd(["docker", "logs", "--since", since_iso, "--timestamps", CONTAINER], 60)
    keep = []
    for ln in (so + "\n" + se).splitlines():
        ln = ANSI.sub("", ln)
        if not ln.strip() or DROP.search(ln) or not KEEP.search(ln):
            continue
        for rx in TIDY:
            ln = rx.sub("", ln)
        keep.append(redact(ln)[:420])
    return keep


# ----------------------------------------------------------------------------- step recording
STEPS = []
R = {}
CLIENTS = []


def record(sid, title, command, response, reading, m=None):
    entry = {"step": f"{sid} {title}", "command": jsonable(command), "response": jsonable(response),
             "reading": reading}
    if m is not None:
        entry["wire"] = wire_since(m)
    STEPS.append(entry)
    R[sid] = entry
    log(f"\n### {entry['step']}\n  cmd:  {json.dumps(entry['command'], default=str)[:700]}\n"
        f"  resp: {json.dumps(entry['response'], default=str)[:1800]}\n  read: {reading}")
    return entry


def txn_number(session):
    """txnNumber PyMongo assigned (the server session is created lazily, on the first operation)."""
    try:
        return session._server_session.transaction_id
    except Exception:  # noqa: BLE001
        return None


def doc1(client):
    return client[DB][COLL].find_one({"_id": 1})


def reset(client):
    client[DB][COLL].replace_one({"_id": 1}, {"_id": 1, "v": 0, "by": None})


def _timeout(signum, frame):
    raise TimeoutError(f"watchdog: run exceeded {WATCHDOG_S} s")


# ============================================================================= the test
def main():
    c1 = MongoClient(URI, serverSelectionTimeoutMS=10000, socketTimeoutMS=90000, appname="t_txn-rerun-c1",
                     event_listeners=[Wire("c1")])
    c2 = MongoClient(URI, serverSelectionTimeoutMS=10000, socketTimeoutMS=90000, appname="t_txn-rerun-c2",
                     event_listeners=[Wire("c2")])
    CLIENTS.extend([c1, c2])
    coll1, coll2 = c1[DB][COLL], c2[DB][COLL]

    # ------------------------------------------------------------------ 0. preamble
    bi = c1.admin.command("buildInfo")
    R["buildInfo"] = bi
    record("0a", "buildInfo", "c1.admin.command('buildInfo')", bi,
           f"The gateway reports buildInfo version {bi.get('version')} (its advertised MongoDB compatibility level; "
           f"gitVersion {bi.get('gitVersion') or 'absent'}), so everything below is evidence about the open-source "
           f"engine and gateway in this documentdb-local container, not proof of managed-service behaviour.")

    hello = c1.admin.command("hello")
    R["hello"] = hello
    record("0b", "hello", "c1.admin.command('hello')", hello,
           f"The gateway advertises maxWireVersion {hello.get('maxWireVersion')}, logicalSessionTimeoutMinutes "
           f"{hello.get('logicalSessionTimeoutMinutes')}, msg {hello.get('msg')!r} and internal.documentdb_versions "
           f"{(hello.get('internal') or {}).get('documentdb_versions')}, so PyMongo allows sessions and transactions, "
           f"treats the endpoint as a mongos, and the engine under test is 1.2.0.")

    q = dict(parse_qsl(urlsplit(URI).query))
    drv = {"pymongo": pymongo.__version__, "python": sys.version.split()[0], "uri_options": q,
           "with_transaction_time_limit_s": 120}
    R["driver"] = drv
    record("0c", "driver and connection options",
           "pymongo.__version__; sys.version; query options of LOCAL_URI (credentials omitted)", drv,
           f"Every step uses PyMongo {pymongo.__version__} on Python {sys.version.split()[0]} with URI options {q}; "
           f"retryWrites=false does not affect with_transaction, whose retry loop keys only on error labels.")

    cont = container_facts()
    R["container"] = cont
    record("0d", "container and image under test",
           "docker inspect --format '<Config.Image, Image, Created, State.StartedAt, RestartCount, State.Status, "
           "State.Health.Status>' ddb-engine-test; docker image inspect --format '<Config.Labels, RepoDigests, "
           "Created>' <image id>   (read-only, selected fields only)", cont,
           f"The container runs {cont.get('image_ref')} (OCI version label {cont.get('oci_version')}, revision "
           f"{cont.get('oci_revision')}), started {cont.get('started_at')} with {cont.get('restart_count')} restarts, "
           f"so these results describe engine {cont.get('oci_version')}.")

    topo = topology_versions()
    R["topology"] = topo
    record("0e", "engine version strings from the gateway's topology query",
           "docker logs --since 30m ddb-engine-test | grep 'Topology acquired' | tail -1   (hex BSON decoded)", topo,
           (f"The gateway's periodic topology read returns {topo.get('decoded')}, matching the 1.2.0 image label."
            if topo.get("decoded") else "No topology line was found in the last 30 minutes of the container log."))

    gcmds, gres = gateway_static_facts()
    R["gateway_static"] = gres
    cnt = gres.get("occurrences_in_gateway_binary", {})
    dyn_keys = sorted((gres.get("dynamic_configuration") or {}).keys())
    record("0f", "gateway configuration and transaction-label strings in the gateway binary (static, read-only)",
           gcmds, gres,
           f"The gateway's dynamic configuration sets only {dyn_keys} (no allow_transaction_snapshot or timeout "
           f"override), and the gateway binary contains 'TransientTransactionError' {cnt.get('TransientTransactionError')} "
           f"times, 'UnknownTransactionCommitResult' {cnt.get('UnknownTransactionCommitResult')} times and "
           f"'RetryableWriteError' {cnt.get('RetryableWriteError')} times.")

    m = mark()
    c1.drop_database(DB)
    c1[DB].create_collection(COLL)
    coll1.insert_one({"_id": 1, "v": 0, "by": None})
    record("0g", "fresh test database",
           "c1.drop_database('t_txn'); c1.t_txn.create_collection('docs'); "
           "c1.t_txn.docs.insert_one({'_id': 1, 'v': 0, 'by': None})", {"document": doc1(c1)},
           "Database t_txn was dropped and recreated with the single document {_id: 1, v: 0} that every conflict "
           "step updates.", m)

    # ------------------------------------------------------------------ 1. write conflict, two sessions
    sA, sB = c1.start_session(), c2.start_session()
    m = mark()
    sA.start_transaction()
    rA = coll1.update_one({"_id": 1}, {"$set": {"v": 1, "by": "A"}}, session=sA)
    record("1a", "session A updates _id 1 inside a transaction",
           "sA = c1.start_session(); sA.start_transaction(); "
           "c1.t_txn.docs.update_one({'_id': 1}, {'$set': {'v': 1, 'by': 'A'}}, session=sA)",
           {"matched": rA.matched_count, "modified": rA.modified_count,
            "txnNumber": txn_number(sA)},
           "Transaction A's update succeeded, so A holds the row lock on _id 1 until it commits.", m)

    m = mark()
    sB.start_transaction()
    out_b = {}

    def b_update():
        t = time.monotonic()
        try:
            r = coll2.update_one({"_id": 1}, {"$set": {"v": 2, "by": "B"}}, session=sB)
            out_b["result"] = {"matched": r.matched_count, "modified": r.modified_count}
        except Exception as e:  # noqa: BLE001
            out_b["error"] = err(e)
        out_b["elapsed_s"] = round(time.monotonic() - t, 3)
        out_b["finished_at_s"] = now_s()

    th = threading.Thread(target=b_update, daemon=True)
    th.start()
    th.join(3.0)
    blocked = th.is_alive()
    snap = dict(out_b)
    if blocked:
        rd = "B's update was still waiting on A's lock after 3 s, so the conflict does not fail fast."
    elif "error" in snap:
        rd = (f"B's update failed {snap['elapsed_s']} s after it was sent, before A committed, with "
              f"{desc(snap['error'])}.")
    else:
        rd = f"B's update returned {snap.get('result')} before A committed, so the gateway did not detect a conflict."
    record("1b", "session B updates the same document inside its own transaction (A not yet committed)",
           "sB = c2.start_session(); sB.start_transaction(); "
           "c2.t_txn.docs.update_one({'_id': 1}, {'$set': {'v': 2, 'by': 'B'}}, session=sB)   # waited up to 3 s",
           {"still_running_after_3s": blocked, "outcome_before_A_commits": snap or None}, rd, m)

    m = mark()
    t_commit_a = now_s()
    try:
        sA.commit_transaction()
        ca = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        ca = err(e)
    record("1c", "commit transaction A", "sA.commit_transaction()", {"result": ca, "sent_at_s": t_commit_a},
           f"Transaction A's commit returned {desc(ca)}.", m)

    th.join(60)
    r1d = {"thread_finished": not th.is_alive(), **out_b, "A_commit_sent_at_s": t_commit_a}
    if "error" in out_b:
        e = out_b["error"]
        rd = (f"The second transaction's write on the same document failed with code {e.get('code')} "
              f"{e.get('codeName')}, errmsg \"{e.get('errmsg')}\", and "
              + (f"errorLabels {e.get('errorLabels')}" if e.get("errorLabels_present")
                 else "no errorLabels field, so no TransientTransactionError label")
              + f" (driver-held labels: {e.get('labels_seen_by_driver')}).")
    else:
        rd = f"The second transaction's write did not fail: {out_b.get('result')}."
    record("1d", "session B: outcome of the conflicting update (THE KEY OBSERVATION)",
           "(outcome of the update_one call started in 1b)", r1d, rd)

    m = mark()
    try:
        sB.commit_transaction()
        cb = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        cb = err(e)
    retry_rule = isinstance(cb, dict) and any(
        x in (cb.get("labels_seen_by_driver") or []) for x in ("TransientTransactionError", "UnknownTransactionCommitResult"))
    record("1e", "commit transaction B after its failed update", "sB.commit_transaction()", cb,
           (f"Committing B after the conflict returned {desc(cb)}, so "
            + ("a with_transaction retry rule would apply." if retry_rule
               else "neither with_transaction retry rule (TransientTransactionError, UnknownTransactionCommitResult) applies.")),
           m)
    sA.end_session()
    sB.end_session()
    d = doc1(c1)
    record("1f", "document after the conflict", "c1.t_txn.docs.find_one({'_id': 1})", d,
           f"The surviving document is {d}, i.e. "
           + ("transaction A's write; B's write was not applied." if d and d.get("by") == "A"
              else "not A's write alone, see response."))

    # 1g/1h: the same conflict, B driven by hand-built commands so the wire replies are untouched
    reset(c1)
    sA = c1.start_session()
    sA.start_transaction()
    coll1.update_one({"_id": 1}, {"$set": {"v": 11, "by": "A-raw"}}, session=sA)
    rb = RawTxn(c2)
    out_r = {}

    def b_raw():
        t = time.monotonic()
        try:
            doc, rep = rb.update({"_id": 1}, {"$set": {"v": 12, "by": "B-raw"}})
            out_r["command"], out_r["reply"] = doc, rep
        except Exception as e:  # noqa: BLE001
            out_r["error"] = err(e)
        out_r["elapsed_s"] = round(time.monotonic() - t, 3)

    m = mark()
    th = threading.Thread(target=b_raw, daemon=True)
    th.start()
    th.join(3.0)
    blocked = th.is_alive()
    try:
        sA.commit_transaction()
        ca = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        ca = err(e)
    th.join(60)
    sA.end_session()
    rep = out_r.get("reply")
    record("1g", "raw wire: the conflicting update sent by hand as the first statement of transaction B",
           [out_r.get("command") or "(not sent)"],
           {"reply": rep, "error": out_r.get("error"), "elapsed_s": out_r.get("elapsed_s"),
            "returned_before_A_commit": not blocked, "A_commit": ca},
           f"The untouched wire reply to the conflicting update is {desc(rep) if rep else out_r.get('error')}.", m)

    m = mark()
    adoc, arep = rb.abort()
    cdoc, crep = rb.commit()
    rb.end()
    record("1h", "raw wire: abortTransaction (as in the 0.117 run), then commitTransaction, for the failed transaction B",
           [adoc, cdoc], {"abortTransaction": arep, "commitTransaction_after_abort": crep},
           f"After the conflict the server answers abortTransaction with {desc(arep)} and a following "
           f"commitTransaction with {desc(crep)}.", m)

    # 1i: with_transaction on the same conflict, no changes to the driver
    def wt_run(sid, title, relabel):
        reset(c1)
        sa = c1.start_session()
        sa.start_transaction()
        coll1.update_one({"_id": 1}, {"$set": {"v": 21 if not relabel else 31, "by": "A-wt"}}, session=sa)
        timer_out = {}

        def commit_a_later():
            try:
                sa.commit_transaction()
                timer_out["result"] = {"ok": 1}
            except Exception as e:  # noqa: BLE001
                timer_out["result"] = err(e)
            timer_out["at_s"] = now_s()

        attempts = []
        bval = 22 if not relabel else 32

        def cb(s):
            rec = {"attempt": len(attempts) + 1, "start_s": now_s()}
            attempts.append(rec)
            try:
                r = coll2.update_one({"_id": 1}, {"$set": {"v": bval, "by": "B-wt"}}, session=s)
                rec["result"] = {"matched": r.matched_count, "modified": r.modified_count}
                rec["txnNumber"] = txn_number(s)
            except OperationFailure as e:
                rec["txnNumber"] = txn_number(s)
                rec["error"] = err(e)
                if relabel and e.code == 112 and not e.has_error_label("TransientTransactionError"):
                    e._add_error_label("TransientTransactionError")
                    rec["TransientTransactionError_added_client_side"] = True
                raise

        sb = c2.start_session()
        m = mark()
        t_start = now_s()
        tm = threading.Timer(COMMIT_A_DELAY_S, commit_a_later)
        tm.start()
        try:
            ret = sb.with_transaction(cb)
            outcome = {"returned": ret}
        except Exception as e:  # noqa: BLE001
            outcome = {"raised": err(e)}
        elapsed = round(now_s() - t_start, 3)
        tm.join(30)
        sa.end_session()
        sb.end_session()
        final = doc1(c1)
        resp = {"callback_invocations": len(attempts), "attempts": attempts, "with_transaction_outcome": outcome,
                "with_transaction_elapsed_s": elapsed, "with_transaction_started_at_s": t_start,
                "A_commit_by_timer": timer_out, "document_after": final}
        n = len(attempts)
        if not relabel:
            if n == 1 and "raised" in outcome:
                rd = (f"with_transaction invoked the callback once and re-raised {desc(outcome['raised'])} after "
                      f"{elapsed} s without retrying, although A released the lock {COMMIT_A_DELAY_S} s after the "
                      f"start, because the error carried no TransientTransactionError label.")
            elif "returned" in outcome:
                rd = f"with_transaction committed after {n} callback invocation(s) in {elapsed} s (it retried)."
            else:
                rd = f"with_transaction invoked the callback {n} times and then raised {desc(outcome['raised'])}."
            cmd = ("sb = c2.start_session(); sb.with_transaction(cb) where cb(s) = c2.t_txn.docs.update_one("
                   "{'_id': 1}, {'$set': {'v': 22, 'by': 'B-wt'}}, session=s); transaction A (already holding the "
                   f"lock on _id 1) is committed by a threading.Timer {COMMIT_A_DELAY_S} s after with_transaction starts")
        else:
            if "returned" in outcome and n > 1:
                rd = (f"Control: with the TransientTransactionError label added client-side to the same server error, "
                      f"with_transaction retried with backoff and committed on attempt {n} after {elapsed} s, once A "
                      f"had released the lock, so the missing server label is what stops the retry in 1i.")
            else:
                rd = f"Control: with the label added client-side, with_transaction made {n} attempt(s): {outcome}."
            cmd = ("same as 1i, but cb catches the server's OperationFailure and, if code == 112 and the "
                   "TransientTransactionError label is missing, calls exc._add_error_label('TransientTransactionError') "
                   "before re-raising (client-side simulation of the label MongoDB sends); v is 32 instead of 22")
        record(sid, title, cmd, resp, rd, m)

    wt_run("1i", "with_transaction on the same conflict (driver helper, unmodified)", relabel=False)
    wt_run("1j", "control: with_transaction when the conflict error carries TransientTransactionError", relabel=True)

    # 1k: added probe -- B reads first, A updates and commits, then B writes (MongoDB's snapshot-conflict ordering)
    reset(c1)
    sA, sB = c1.start_session(), c2.start_session()
    m = mark()
    sB.start_transaction()
    b_first = coll2.find_one({"_id": 1}, session=sB)
    sA.start_transaction()
    coll1.update_one({"_id": 1}, {"$inc": {"v": 1}, "$set": {"by": "A-iso"}}, session=sA)
    try:
        sA.commit_transaction()
        a_commit = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        a_commit = err(e)
    b_second = coll2.find_one({"_id": 1}, session=sB)
    new_v = (b_first or {}).get("v", 0) + 10
    try:
        r = coll2.update_one({"_id": 1}, {"$set": {"v": new_v, "by": "B-iso"}}, session=sB)
        b_upd = {"matched": r.matched_count, "modified": r.modified_count}
    except Exception as e:  # noqa: BLE001
        b_upd = err(e)
    try:
        sB.commit_transaction()
        b_commit = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        b_commit = err(e)
    sA.end_session()
    sB.end_session()
    final = doc1(c1)
    resp = {"B_first_read": b_first, "A_commit": a_commit, "B_second_read_after_A_commit": b_second,
            "B_update": b_upd, "B_commit": b_commit, "document_after": final}
    saw_a = isinstance(b_second, dict) and b_second.get("v") == 1
    if is_ok(b_upd) or "matched" in b_upd:
        if is_ok(b_commit) and final and final.get("v") == new_v:
            rd = (f"Added probe: B {'saw' if saw_a else 'did not see'} A's committed write mid-transaction and its "
                  f"read-modify-write update made after A's commit succeeded and committed, so A's increment was lost "
                  f"(final v {final.get('v')}, not {new_v + 1}) with no error or label returned to either transaction.")
        else:
            rd = (f"Added probe: B {'saw' if saw_a else 'did not see'} A's committed write, its update succeeded and its "
                  f"commit returned {desc(b_commit)}; final document {final}.")
    else:
        rd = (f"Added probe: B {'saw' if saw_a else 'did not see'} A's committed write mid-transaction and its update "
              f"made after A's commit failed with {desc(b_upd)}.")
    record("1k", "added probe: B reads, A updates and commits, then B writes the same document",
           "sB.start_transaction(); c2.t_txn.docs.find_one({'_id': 1}, session=sB); sA.start_transaction(); "
           "c1.t_txn.docs.update_one({'_id': 1}, {'$inc': {'v': 1}, '$set': {'by': 'A-iso'}}, session=sA); "
           "sA.commit_transaction(); c2.t_txn.docs.find_one({'_id': 1}, session=sB); "
           "c2.t_txn.docs.update_one({'_id': 1}, {'$set': {'v': <B's first read of v> + 10, 'by': 'B-iso'}}, "
           "session=sB); sB.commit_transaction()", resp, rd, m)

    # ------------------------------------------------------------------ 2. readConcern inside a transaction
    for letter, level in (("2a", "snapshot"), ("2b", "majority"), ("2c", "local")):
        s = c1.start_session()
        m = mark()
        res = {}
        try:
            s.start_transaction(read_concern=ReadConcern(level))
            res["find"] = list(coll1.find({"_id": 1}, session=s))
            try:
                s.commit_transaction()
                res["commit"] = {"ok": 1}
            except Exception as e:  # noqa: BLE001
                res["commit"] = err(e)
        except Exception as e:  # noqa: BLE001
            res["error"] = err(e)
            try:
                s.abort_transaction()
            except Exception as e2:  # noqa: BLE001
                res["abort_error"] = err(e2)
        s.end_session()
        if "error" in res:
            rd = (f"readConcern '{level}' inside a transaction is rejected on the transaction's first command with "
                  f"{desc(res['error'])}.")
        elif is_ok(res.get("commit")):
            rd = (f"readConcern '{level}' inside a transaction is accepted: the first find, sent with readConcern "
                  f"{{level: '{level}'}} and startTransaction, returned the document and the commit succeeded.")
        else:
            rd = f"readConcern '{level}': the find succeeded but the commit returned {desc(res.get('commit'))}."
        record(letter, f"readConcern '{level}' inside a transaction",
               f"s = c1.start_session(); s.start_transaction(read_concern=ReadConcern('{level}')); "
               f"list(c1.t_txn.docs.find({{'_id': 1}}, session=s)); s.commit_transaction()", res, rd, m)

    # ------------------------------------------------------------------ 3. commit twice / abort after commit
    reset(c1)
    s = c1.start_session()
    m = mark()
    s.start_transaction()
    coll1.update_one({"_id": 1}, {"$inc": {"v": 100}}, session=s)
    o3 = {}
    for key, fn in (("commit_1", s.commit_transaction), ("commit_2", s.commit_transaction),
                    ("abort_after_commit", s.abort_transaction)):
        try:
            fn()
            o3[key] = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            o3[key] = err(e)
    s.end_session()
    o3["document_after"] = doc1(c1)
    w = wire_since(m)
    commits = [ev for ev in w if ev["event"] == "started" and ev["command_name"] == "commitTransaction"]
    second_wc = commits[1]["command"].get("writeConcern") if len(commits) > 1 else None
    o3["commitTransaction_commands_sent"] = len(commits)
    o3["second_commit_writeConcern_on_wire"] = second_wc
    record("3a", "driver: commit_transaction twice, then abort_transaction",
           "s.start_transaction(); c1.t_txn.docs.update_one({'_id': 1}, {'$inc': {'v': 100}}, session=s); "
           "s.commit_transaction(); s.commit_transaction(); s.abort_transaction()", o3,
           f"Driver path: the first commit returned {desc(o3['commit_1'])}, the second commit_transaction was re-sent "
           f"with writeConcern {second_wc} and returned {desc(o3['commit_2'])}, and abort_transaction after commit gave "
           f"{desc(o3['abort_after_commit'])}.", m)

    rt = RawTxn(c1)
    m = mark()
    u = rt.update({"_id": 1}, {"$inc": {"v": 1000}})
    c1r = rt.commit()
    c2r = rt.commit()
    c3r = rt.commit({"w": "majority", "wtimeout": 10000})
    ar = rt.abort()
    rt.end()
    o3b = {"update": u[1], "commit_1": c1r[1], "commit_2": c2r[1], "commit_3_majority_wc": c3r[1],
           "abort_after_commit": ar[1], "document_after": doc1(c1)}
    record("3b", "raw wire: commitTransaction twice (and once more in the driver's retry form), then abortTransaction",
           [u[0], c1r[0], c2r[0], c3r[0], ar[0]], o3b,
           f"Repeated commitTransaction returned {desc(c1r[1])}, {desc(c2r[1])} and {desc(c3r[1])} (v is now "
           f"{(o3b['document_after'] or {}).get('v')}, so the increment applied once), and abortTransaction after "
           f"commit returned {desc(ar[1])}.", m)

    rt = RawTxn(c1)
    m = mark()
    u = rt.update({"_id": 1}, {"$inc": {"v": 1}})
    a1 = rt.abort()
    a2 = rt.abort()
    cr = rt.commit()
    rt.end()
    o3c = {"update": u[1], "abort_1": a1[1], "abort_2": a2[1], "commit_after_abort": cr[1], "document_after": doc1(c1)}
    record("3c", "raw wire: abortTransaction twice, then commitTransaction after abort",
           [u[0], a1[0], a2[0], cr[0]], o3c,
           f"abortTransaction returned {desc(a1[1])} then {desc(a2[1])}, and commitTransaction after abort returned "
           f"{desc(cr[1])} (v stays {(o3c['document_after'] or {}).get('v')}, so the aborted increment was not applied).",
           m)

    if SKIP_IDLE:
        record("4", "idle-transaction steps skipped", "--skip-idle", None, "Section 4 was skipped on request.")
        return

    # ------------------------------------------------------------------ 4. idle transaction (36 s)
    reset(c1)
    s = c1.start_session()
    m = mark()
    s.start_transaction()
    r0 = coll1.update_one({"_id": 1}, {"$set": {"idle": "start"}}, session=s)
    t_last = time.monotonic()
    time.sleep(IDLE_S)
    slept = round(time.monotonic() - t_last, 1)
    try:
        r = coll1.update_one({"_id": 1}, {"$set": {"idle": "after"}}, session=s)
        w4 = {"matched": r.matched_count, "modified": r.modified_count}
    except Exception as e:  # noqa: BLE001
        w4 = err(e)
    record("4a", f"driver: write after {slept} s idle inside a transaction",
           "s.start_transaction(); c1.t_txn.docs.update_one({'_id': 1}, {'$set': {'idle': 'start'}}, session=s); "
           f"time.sleep({IDLE_S}); c1.t_txn.docs.update_one({{'_id': 1}}, {{'$set': {{'idle': 'after'}}}}, session=s)",
           {"first_write": {"matched": r0.matched_count, "modified": r0.modified_count}, "idle_s": slept,
            "write_after_idle": w4},
           f"After {slept} s idle the next write in the transaction returned {desc(w4)} (driver-held labels: "
           f"{w4.get('labels_seen_by_driver') if isinstance(w4, dict) else None}).", m)
    m = mark()
    try:
        s.commit_transaction()
        c4 = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        c4 = err(e)
    record("4b", "driver: commit after the idle period", "s.commit_transaction()", c4,
           f"Committing the idle-expired transaction returned {desc(c4)} (driver-held labels: "
           f"{c4.get('labels_seen_by_driver') if isinstance(c4, dict) else None}).", m)
    m = mark()
    try:
        s.abort_transaction()
        a4 = {"ok": 1, "note": "PyMongo ignores server errors from abortTransaction; the wire events show the reply"}
    except Exception as e:  # noqa: BLE001
        a4 = err(e)
    s.end_session()
    record("4c", "driver: abort_transaction after the failed commit", "s.abort_transaction()", a4,
           f"abort_transaction after the failed commit gave {desc(a4)}.", m)

    rt = RawTxn(c1)
    m = mark()
    u0 = rt.update({"_id": 1}, {"$set": {"idle2": "start"}})
    t_last = time.monotonic()
    time.sleep(IDLE_S)
    slept = round(time.monotonic() - t_last, 1)
    u1 = rt.update({"_id": 1}, {"$set": {"idle2": "after"}})
    cr = rt.commit()
    ar = rt.abort()
    rt.end()
    record("4d", f"raw wire: write, commitTransaction and abortTransaction after {slept} s idle",
           [u0[0], f"(sleep {IDLE_S} s)", u1[0], cr[0], ar[0]],
           {"first_update": u0[1], "idle_s": slept, "update_after_idle": u1[1], "commit": cr[1], "abort": ar[1]},
           f"On the wire, the write after {slept} s idle returned {desc(u1[1])}, commitTransaction returned "
           f"{desc(cr[1])} and abortTransaction returned {desc(ar[1])}.", m)

    # 4e: added probe -- an active transaction (a write every 8 s) that lives longer than 30 s
    s = c1.start_session()
    m = mark()
    s.start_transaction()
    ops = []
    t_txn = time.monotonic()
    for i in range(LIFETIME_WRITES):
        if i:
            time.sleep(LIFETIME_GAP_S)
        t = round(time.monotonic() - t_txn, 1)
        try:
            r = coll1.update_one({"_id": 1}, {"$set": {"life": i}}, session=s)
            ops.append({"write": i, "t_since_first_write_s": t, "result": {"matched": r.matched_count,
                                                                           "modified": r.modified_count}})
        except Exception as e:  # noqa: BLE001
            ops.append({"write": i, "t_since_first_write_s": t, "error": err(e)})
            break
    t = round(time.monotonic() - t_txn, 1)
    try:
        s.commit_transaction()
        c4e = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        c4e = err(e)
    s.end_session()
    final = doc1(c1)
    failed_op = next((o for o in ops if "error" in o), None)
    if failed_op is None and is_ok(c4e):
        rd = (f"Added probe: a transaction kept active with a write every {LIFETIME_GAP_S} s ran {t} s from first "
              f"write to commit and committed (life={final.get('life') if final else None}), so a busy transaction "
              f"can outlive 30 s on this build; whether it does depends on timing (compare 4g and the earlier runs).")
    elif failed_op is not None:
        rd = (f"Added probe: in a transaction kept active with a write every {LIFETIME_GAP_S} s, write "
              f"{failed_op['write']} at {failed_op['t_since_first_write_s']} s failed with {desc(failed_op['error'])} "
              f"although no gap between statements exceeded {LIFETIME_GAP_S} s, so the limit applies to transaction "
              f"lifetime and not only to idle time.")
    else:
        rd = f"Added probe: all writes succeeded but the commit at {t} s returned {desc(c4e)}."
    record("4e", f"added probe: active transaction, one write every {LIFETIME_GAP_S} s, commit attempted {t} s after the first write",
           f"s.start_transaction(); for i in range({LIFETIME_WRITES}): (time.sleep({LIFETIME_GAP_S}) if i else None); "
           f"c1.t_txn.docs.update_one({{'_id': 1}}, {{'$set': {{'life': i}}}}, session=s); s.commit_transaction()",
           {"writes": ops, "commit": c4e, "commit_at_s_since_first_write": t, "document_after": final}, rd, m)

    # 4f (added): three more idle transactions on separate documents, and 4g (added): a transaction written
    # every 2 s until it fails, all running concurrently so they share the gateway's expiry sweep schedule
    for i in (101, 102, 103, 201):
        coll1.replace_one({"_id": i}, {"_id": i, "v": 0}, upsert=True)
    res_f, res_g, lsids = {}, {}, {}
    m = mark()

    def idle_one(k, delay):
        time.sleep(delay)
        s = c1.start_session()
        did = 100 + k
        out = {"doc_id": did}
        try:
            s.start_transaction()
            coll1.update_one({"_id": did}, {"$set": {"idle": "start"}}, session=s)
            lsids[f"f{k}"] = s.session_id
            out["first_write_at_s"] = now_s()
            t = time.monotonic()
            time.sleep(IDLE_S)
            out["idle_s"] = round(time.monotonic() - t, 1)
            try:
                coll1.update_one({"_id": did}, {"$set": {"idle": "after"}}, session=s)
                out["write_after_idle"] = {"ok": 1}
            except Exception as e:  # noqa: BLE001
                out["write_after_idle"] = err(e)
            out["write_after_idle_at_s"] = now_s()
            try:
                s.commit_transaction()
                out["commit"] = {"ok": 1}
            except Exception as e:  # noqa: BLE001
                out["commit"] = err(e)
        except Exception as e:  # noqa: BLE001
            out["unexpected"] = err(e)
        finally:
            s.end_session()
        res_f[k] = out

    def lifetime_fine():
        s = c1.start_session()
        writes = []
        try:
            s.start_transaction()
            t_first = time.monotonic()
            i = 0
            while True:
                age = round(time.monotonic() - t_first, 2)
                try:
                    coll1.update_one({"_id": 201}, {"$set": {"life": i}}, session=s)
                    if i == 0:
                        lsids["g"] = s.session_id
                    writes.append({"write": i, "age_s": age, "at_s": now_s(), "ok": 1})
                except Exception as e:  # noqa: BLE001
                    writes.append({"write": i, "age_s": age, "at_s": now_s(), "error": err(e)})
                    break
                if age > 50:
                    break
                i += 1
                time.sleep(2)
            age = round(time.monotonic() - t_first, 2)
            try:
                s.commit_transaction()
                c = {"ok": 1}
            except Exception as e:  # noqa: BLE001
                c = err(e)
            res_g.update({"writes": writes, "commit": c, "commit_age_s": age})
        except Exception as e:  # noqa: BLE001
            res_g["unexpected"] = err(e)
        finally:
            s.end_session()

    threads = [threading.Thread(target=idle_one, args=(k, d), daemon=True) for k, d in ((1, 0.0), (2, 1.5), (3, 3.0))]
    threads.append(threading.Thread(target=lifetime_fine, daemon=True))
    for t_ in threads:
        t_.start()
    for t_ in threads:
        t_.join(120)
    outs = [res_f.get(k, {}) for k in (1, 2, 3)]
    groups = {}
    for o in outs:
        k = (f"the write after {IDLE_S} s idle returned {desc(norm_desc(o.get('write_after_idle')))} and the commit "
             f"returned {desc(norm_desc(o.get('commit')))}")
        groups[k] = groups.get(k, 0) + 1
    descs = [f"{n} of {len(outs)}: {k}" for k, n in groups.items()]
    record("4f", f"added: three more transactions idle {IDLE_S} s (separate documents, started 1.5 s apart, concurrent with 4g)",
           f"for k in (1, 2, 3), in its own thread and session: s.start_transaction(); "
           f"c1.t_txn.docs.update_one({{'_id': 100 + k}}, {{'$set': {{'idle': 'start'}}}}, session=s); "
           f"time.sleep({IDLE_S}); c1.t_txn.docs.update_one({{'_id': 100 + k}}, {{'$set': {{'idle': 'after'}}}}, "
           f"session=s); s.commit_transaction()",
           {"runs": outs, "wire": {f"f{k}": wire_for(m, lsids[f"f{k}"]) for k in (1, 2, 3) if f"f{k}" in lsids}},
           "Three more idle transactions gave: " + "; ".join(descs) + " (ActivityId values omitted here).")
    ws = res_g.get("writes", [])
    ok_ages = [w["age_s"] for w in ws if w.get("ok")]
    fail = next((w for w in ws if "error" in w), None)
    if fail:
        rd = (f"Added probe: with a write every 2 s (never more than about 2 s idle), writes succeeded up to "
              f"{max(ok_ages) if ok_ages else None} s after the first write and the write at {fail['age_s']} s failed "
              f"with {desc(fail['error'])}, so a busy transaction is ended once its lifetime passes 30 s, here between "
              f"{max(ok_ages) if ok_ages else None} s and {fail['age_s']} s after its first write.")
    else:
        rd = (f"Added probe: writes every 2 s all succeeded up to {max(ok_ages) if ok_ages else None} s and the commit "
              f"returned {desc(res_g.get('commit'))}, so no lifetime limit was enforced in this window.")
    record("4g", "added probe: one transaction written every 2 s until a write fails (concurrent with 4f)",
           "s.start_transaction(); loop: c1.t_txn.docs.update_one({'_id': 201}, {'$set': {'life': i}}, session=s); "
           "time.sleep(2); stop at the first error or after 50 s; s.commit_transaction()",
           {**res_g, "wire": wire_for(m, lsids["g"]) if "g" in lsids else []}, rd)

    final = doc1(c1)
    record("5", "final document", "c1.t_txn.docs.find_one({'_id': 1})", final,
           f"Final document {final}: the idle-expired transactions' writes (idle, idle2) "
           + ("were not applied" if final and "idle" not in final and "idle2" not in final else "are present, see response")
           + ".")


def cleanup_and_logs(started_iso):
    # 6. container log lines for this run (read-only)
    try:
        lines = container_logs(started_iso)
        keys = {
            "Lock not available": sum("Lock not available" in ln for ln in lines),
            "lock timeout": sum("lock timeout" in ln.lower() for ln in lines),
            "idle-in-transaction timeout": sum("idle-in-transaction" in ln for ln in lines),
            "transaction timeout (PG17 transaction_timeout)": sum("due to transaction timeout" in ln for ln in lines),
            "Failed to drop a transaction": sum("drop a transaction" in ln for ln in lines),
            "session_manager: Failed to abort expired transaction": sum("expired transaction" in ln for ln in lines),
        }
        record("6", "gateway and PostgreSQL log lines during this run (read-only docker logs)",
               f"docker logs --since {started_iso} --timestamps ddb-engine-test, ANSI stripped, [GATEWAY-FILE] "
               f"duplicates and cron lines dropped, filtered to lock/transaction/connection patterns",
               {"pattern_counts": keys, "lines": lines[:150], "lines_total": len(lines),
                "caveat": "the container is shared with other tests; lines are filtered by time window and pattern"},
               f"The container log for this run shows {keys['Lock not available']} 'Lock not available' gateway lines, "
               f"{keys['idle-in-transaction timeout']} PostgreSQL 'idle-in-transaction timeout' terminations, "
               f"{keys['session_manager: Failed to abort expired transaction']} gateway 'Failed to abort expired "
               f"transaction' sweep line(s) and {keys['transaction timeout (PG17 transaction_timeout)']} PostgreSQL "
               f"'transaction timeout' terminations.")
    except Exception as e:  # noqa: BLE001
        record("6", "container log capture failed", "docker logs ...", {"error": redact(repr(e))},
               "The container log could not be read, so the mechanism behind the errors is not confirmed here.")

    # 7. drop the test database
    try:
        c1 = CLIENTS[0] if CLIENTS else MongoClient(URI, serverSelectionTimeoutMS=10000)
        m = mark()
        c1.drop_database(DB)
        listed = DB in c1.list_database_names()
        record("7", "drop the test database", "c1.drop_database('t_txn'); 't_txn' in c1.list_database_names()",
               {"t_txn_still_listed": listed},
               "The test database t_txn was dropped." if not listed else "t_txn is still listed after the drop.", m)
    except Exception as e:  # noqa: BLE001
        record("7", "drop the test database (failed)", "c1.drop_database('t_txn')", err(e),
               f"Dropping t_txn failed with {desc(err(e))}.")
    for c in CLIENTS:
        try:
            c.close()
        except Exception:  # noqa: BLE001
            pass


# ============================================================================= comparison with 0.117
def norm_msg(msg):
    if not isinstance(msg, str):
        return msg
    msg = re.sub(r"\[ActivityId=[0-9a-fA-F-]+\]\s*", "[ActivityId=<id>] ", msg)
    return re.sub(r"([Tt]ransaction) \d+", r"\1 <n>", msg)


def sig(x):
    """Comparable signature: ok, code, codeName, normalised errmsg, errorLabels (or 'absent')."""
    if x is None:
        return None
    if not isinstance(x, dict):
        return x
    if isinstance(x.get("server_reply"), dict):
        x = x["server_reply"]
    elif isinstance(x.get("raw"), dict):
        x = x["raw"]
    elif "exception" in x:
        return {"client_side": x["exception"], "message": x.get("message")}
    out = {"ok": float(x["ok"]) if isinstance(x.get("ok"), (int, float)) else x.get("ok")}
    for k in ("code", "codeName"):
        if k in x:
            out[k] = x[k]
    if "errmsg" in x:
        out["errmsg"] = norm_msg(x["errmsg"])
    out["errorLabels"] = x.get("errorLabels", "absent")
    return out


def bstep(base, prefix):
    for s in (base or {}).get("steps", []):
        if s.get("step", "").startswith(prefix):
            return s.get("response")
    return None


def cstep(sid):
    e = R.get(sid)
    return e.get("response") if e else None


def compare():
    try:
        with open(BASELINE) as f:
            base = json.load(f)
    except Exception as e:  # noqa: BLE001
        return {"baseline": BASELINE, "error": repr(e)}, []

    def rc_base(resp):
        if not isinstance(resp, dict):
            return None
        if "find_result" in resp:
            return {"accepted": True, "commit": sig(resp.get("commit"))}
        return {"rejected": sig(resp)}

    def rc_cur(resp):
        if not isinstance(resp, dict):
            return None
        if "error" in resp:
            return {"rejected": sig(resp["error"])}
        return {"accepted": True, "commit": sig(resp.get("commit"))}

    def g(d, *keys):
        for k in keys:
            if not isinstance(d, dict):
                return None
            d = d.get(k)
        return d

    items = [
        ("write conflict: second transaction's update (driver, 1d)",
         lambda: sig(g(bstep(base, "1d"), "error")), lambda: sig(g(cstep("1d"), "error"))),
        ("write conflict: untouched wire reply (1g)",
         lambda: sig(g(bstep(base, "1g"), "reply")), lambda: sig(g(cstep("1g"), "reply"))),
        ("abortTransaction for the failed transaction B (1h)",
         lambda: sig(bstep(base, "1h")), lambda: sig(g(cstep("1h"), "abortTransaction"))),
        ("readConcern snapshot inside a transaction (2a)",
         lambda: rc_base(bstep(base, "2 readConcern snapshot")), lambda: rc_cur(cstep("2a"))),
        ("readConcern majority inside a transaction (2b)",
         lambda: rc_base(bstep(base, "2 readConcern majority")), lambda: rc_cur(cstep("2b"))),
        ("readConcern local inside a transaction (2c)",
         lambda: rc_base(bstep(base, "2 readConcern local")), lambda: rc_cur(cstep("2c"))),
        ("driver: second commit_transaction (3a)",
         lambda: sig(g(bstep(base, "3a"), "commit2")), lambda: sig(g(cstep("3a"), "commit_2"))),
        ("driver: abort_transaction after commit (3a)",
         lambda: sig(g(bstep(base, "3a"), "abort_after_commit")), lambda: sig(g(cstep("3a"), "abort_after_commit"))),
        ("raw: commitTransaction repeated (3b)",
         lambda: [sig(g(bstep(base, "3b"), k)) for k in ("commit1", "commit2", "commit2_majority_wc")],
         lambda: [sig(g(cstep("3b"), k)) for k in ("commit_1", "commit_2", "commit_3_majority_wc")]),
        ("raw: abortTransaction after commit (3b)",
         lambda: sig(g(bstep(base, "3b"), "abort_after_commit")), lambda: sig(g(cstep("3b"), "abort_after_commit"))),
        ("raw: abortTransaction twice, commitTransaction after abort (3c)",
         lambda: [sig(g(bstep(base, "3c"), k)) for k in ("abort1", "abort2", "commit_after_abort")],
         lambda: [sig(g(cstep("3c"), k)) for k in ("abort_1", "abort_2", "commit_after_abort")]),
        ("driver: write after 36 s idle (4a)",
         lambda: sig(g(bstep(base, "4a"), "write_result")), lambda: sig(g(cstep("4a"), "write_after_idle"))),
        ("driver: commit after 36 s idle (4b)",
         lambda: sig(bstep(base, "4b")), lambda: sig(cstep("4b"))),
        ("raw: write / commit / abort after 36 s idle (4d)",
         lambda: [sig(g(bstep(base, "4d"), k)) for k in ("update", "commit", "abort")],
         lambda: [sig(g(cstep("4d"), k)) for k in ("update_after_idle", "commit", "abort")]),
    ]
    rows = []
    for name, fb, fc in items:
        try:
            b = fb()
        except Exception as e:  # noqa: BLE001
            b = {"extract_error": repr(e)}
        try:
            c = fc()
        except Exception as e:  # noqa: BLE001
            c = {"extract_error": repr(e)}
        def missing(v):
            return v is None or (isinstance(v, list) and all(x is None for x in v))
        row = {"item": name, "engine_0_117": b, "engine_1_2_0": c,
               "same": None if (missing(b) or missing(c)) else (b == c)}
        if "idle" in name:
            row["note"] = ("timing-dependent on 1.2.0 (race between PostgreSQL's 30 s idle-in-transaction kill and the "
                           "gateway's expired-transaction sweep); one run is one sample, see analysis.idle_outcomes")
        rows.append(row)
    for name, sid in (("with_transaction on the conflict (1i)", "1i"), ("with_transaction control (1j)", "1j"),
                      ("isolation / lost-update probe (1k)", "1k"), ("commit B after its conflict (1e)", "1e"),
                      ("active transaction lifetime > 30 s (4e)", "4e"),
                      ("three more idle transactions (4f)", "4f"),
                      ("transaction written every 2 s until it fails (4g)", "4g")):
        rows.append({"item": name, "engine_0_117": "not tested in the 0.117 run",
                     "engine_1_2_0": R.get(sid, {}).get("reading"), "same": None})
    meta = {"baseline": BASELINE, "baseline_started_utc": base.get("started_utc"),
            "baseline_target": base.get("target"),
            "normalisation": "errmsg ActivityId values and transaction numbers are normalised before comparing"}
    return meta, rows


# ============================================================================= entry point
if __name__ == "__main__":
    started = datetime.now(timezone.utc)
    started_iso = started.strftime("%Y-%m-%dT%H:%M:%SZ")
    signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(WATCHDOG_S)
    fatal = None
    try:
        main()
    except BaseException as e:  # noqa: BLE001
        fatal = {"exception": type(e).__name__, "message": redact(str(e)), "traceback": redact(traceback.format_exc())}
        log(f"FATAL {fatal}")
    finally:
        signal.alarm(0)
        try:
            cleanup_and_logs(started_iso)
        except BaseException as e:  # noqa: BLE001
            log(f"cleanup error {redact(repr(e))}")
    cmp_meta, cmp_rows = compare()
    bi = R.get("buildInfo") or {}
    cont = R.get("container") or {}
    topo = (R.get("topology") or {}).get("decoded")
    changed = [r["item"] for r in cmp_rows if r["same"] is False]
    unchanged = [r["item"] for r in cmp_rows if r["same"] is True]

    def rd(*sids):
        return [R[x]["reading"] for x in sids if x in R]

    summary = {
        "write_conflict_second_transaction": rd("1b", "1d", "1e", "1g", "1h"),
        "with_transaction_retry": rd("1i", "1j"),
        "isolation_probe_added": rd("1k"),
        "readConcern_in_transaction": rd("2a", "2b", "2c"),
        "commit_twice_and_abort_after_commit": rd("3a", "3b", "3c"),
        "idle_36_s_then_write_and_commit": rd("4a", "4b", "4c", "4d"),
        "idle_repeats_added": rd("4f"),
        "active_transaction_longer_than_30_s_added": rd("4e", "4g"),
        "mechanism_from_logs_and_binary": rd("0f", "6"),
        "unchanged_vs_0_117": unchanged,
        "changed_vs_0_117": changed,
    }
    earlier = []
    for name, note in (("report.run1.json", "full run 1, earlier revision of this script (no 4f/4g)"),
                       ("report.run2.json", "full run 2, earlier revision of this script (4f/4g present; 4e/4f/4g "
                                            "reading templates later corrected, raw responses unaffected)"),
                       ("report.run3.json", "full run 3, same steps as this revision (only the 4e title and the "
                                            "step 6 wording changed afterwards)"),
                       ("report.run4.json", "full run 4, same steps as this revision (the 1j/4e/4g reading templates "
                                            "were corrected afterwards: its 4e reading wrongly said the limit is "
                                            "idle-only; raw responses unaffected)")):
        p_run = os.path.join(HERE, name)
        if not os.path.exists(p_run):
            continue
        try:
            with open(p_run) as f:
                r1 = json.load(f)
            earlier.append({"file": p_run, "started_utc": r1.get("started_utc"), "note": note,
                            "outcomes": {x["step"]: x["reading"] for x in r1.get("steps", [])
                                         if x["step"][:2] in ("1d", "1e", "1i", "1j", "1k", "2a", "2b", "3b", "3c",
                                                              "4a", "4b", "4d", "4e", "4f", "4g")}})
        except Exception as e:  # noqa: BLE001
            earlier.append({"file": p_run, "error": repr(e)})
    report = {
        "test": "transactions-labels",
        "stage": "ENGINE 1.2.0 RERUN; compared with the engine 0.117 results in findings/phase4/ENGINE-TESTS.md",
        "database": DB,
        "started_utc": started.isoformat(),
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "target": (f"documentdb-local container {CONTAINER} ({cont.get('image_ref')}, OCI version "
                   f"{cont.get('oci_version')}, revision {cont.get('oci_revision')}), localhost:10260, TLS with a "
                   f"self-signed certificate, SCRAM-SHA-256"),
        "engine_version": (f"buildInfo.version {bi.get('version')} (gateway-advertised MongoDB level); "
                           f"hello.internal.documentdb_versions "
                           f"{((R.get('hello') or {}).get('internal') or {}).get('documentdb_versions')}; image "
                           f"{cont.get('image_ref')} OCI version {cont.get('oci_version')} revision "
                           f"{cont.get('oci_revision')}; gateway topology query {topo}"),
        "buildInfo": jsonable(bi),
        "driver": R.get("driver"),
        "evidence_scope": ("Observed on the open-source DocumentDB engine and gateway in documentdb-local at buildInfo "
                           f"version {bi.get('version')} (image {cont.get('image_ref')}, engine 1.2.0). This is "
                           "evidence about the open-source engine and gateway only; it does not prove managed Azure "
                           "DocumentDB behaviour."),
        "script": os.path.abspath(__file__),
        "rerun": f"/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I {os.path.abspath(__file__)}",
        "skipped_idle_section": SKIP_IDLE,
        "steps": STEPS,
        "summary": summary,
        "earlier_full_runs": earlier,
        "comparison_with_0_117": {"meta": cmp_meta, "rows": cmp_rows, "items_changed": changed},
        "fatal": fatal,
    }
    text = redact(json.dumps(report, indent=2, default=str))
    for sec in SECRETS:
        assert sec not in text
    with open(os.path.join(HERE, "report.json"), "w") as f:
        f.write(text + "\n")
    log(f"\nitems changed vs 0.117: {changed}")
    log("report written: " + os.path.join(HERE, "report.json"))
    with open(os.path.join(HERE, "run.out"), "w") as f:
        f.write("\n".join(OUT_LINES) + "\n")
