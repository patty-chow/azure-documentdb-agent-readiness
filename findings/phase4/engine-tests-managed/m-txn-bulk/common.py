"""Shared helpers for test m-txn-bulk (managed Azure DocumentDB).

Reads ../managed.env (MANAGED_URI etc.). Never prints or writes the password or a URI that
contains it: every string that goes to stdout or a report passes through redact().
Owns database mt_txn only.
"""
import json
import os
import re
import threading
import time
import urllib.parse
import warnings

warnings.filterwarnings("ignore", message=".*CosmosDB.*")  # PyMongo's CosmosDB host warning on connect

from pymongo import monitoring
from pymongo.errors import BulkWriteError, ClientBulkWriteException, OperationFailure, PyMongoError
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(HERE, "..", "managed.env")
DB = "mt_txn"


def load_env():
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
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
_SECRETS = set()
_p = ENV.get("MANAGED_PASS", "")
if _p:
    _SECRETS.update({_p, urllib.parse.quote(_p, safe=""), urllib.parse.quote_plus(_p), urllib.parse.quote(_p)})
_SECRETS.discard("")

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_GUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
_KEYED_GUID_RE = re.compile(r"(?i)((?:subscriptions/|tenant[_ ]?id['\"]?\s*[:=]\s*['\"]?|object[_ ]?id['\"]?\s*[:=]\s*['\"]?|principal[_ ]?id['\"]?\s*[:=]\s*['\"]?|oid['\"]?\s*[:=]\s*['\"]?))" + _GUID)


def redact(s):
    s = str(s)
    for sec in sorted(_SECRETS, key=len, reverse=True):
        s = s.replace(sec, "***")
    s = re.sub(r"(mongodb(?:\+srv)?://)[^@/\s]*@", r"\1***:***@", s)
    s = _EMAIL_RE.sub("<email-masked>", s)
    s = _KEYED_GUID_RE.sub(lambda m: m.group(1) + "<guid-masked>", s)
    return s


def jsonable(o):
    """Make a server/driver object JSON-serialisable without losing information."""
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set, frozenset)):
        return [jsonable(v) for v in o]
    if isinstance(o, str):
        return redact(o)
    if isinstance(o, (int, float, bool)) or o is None:
        return o
    return redact(repr(o))


def err_dict(exc):
    """Exact error: exception type, code, codeName, errmsg, server-sent errorLabels, driver-side labels."""
    d = {"exception": type(exc).__name__, "message": redact(str(exc))}
    if isinstance(exc, ClientBulkWriteException):
        d["nested_error"] = err_dict(exc.error) if isinstance(exc.error, BaseException) else jsonable(exc.error)
        d["write_errors"] = jsonable(exc.write_errors)
        d["write_concern_errors"] = jsonable(exc.write_concern_errors)
        pr = exc.partial_result
        if pr is not None:
            try:
                d["partial_result"] = {"acknowledged": pr.acknowledged, "inserted_count": pr.inserted_count,
                                       "matched_count": pr.matched_count, "modified_count": pr.modified_count,
                                       "deleted_count": pr.deleted_count, "upserted_count": pr.upserted_count}
            except Exception as e2:  # noqa
                d["partial_result"] = redact(repr(pr)) + " / " + redact(str(e2))
    elif isinstance(exc, BulkWriteError):
        det = exc.details or {}
        d["code"] = exc.code
        d["details"] = jsonable(det)
    elif isinstance(exc, OperationFailure):
        det = exc.details or {}
        d.update({
            "code": det.get("code", exc.code),
            "codeName": det.get("codeName"),
            "errmsg": det.get("errmsg"),
            "errorLabels_in_server_reply": jsonable(det.get("errorLabels")) if "errorLabels" in det else "<absent>",
            "raw_server_reply": jsonable(det),
        })
    if isinstance(exc, PyMongoError):
        labels = sorted(getattr(exc, "_error_labels", set()) or [])
        d["driver_exception_labels"] = labels
        d["has_TransientTransactionError"] = exc.has_error_label("TransientTransactionError")
        d["has_UnknownTransactionCommitResult"] = exc.has_error_label("UnknownTransactionCommitResult")
    return d


def reply_summary(reply):
    """Summarise a raw reply dict: keep the error fields verbatim and say whether errorLabels exists."""
    if not isinstance(reply, dict):
        return jsonable(reply)
    out = jsonable(reply)
    out["_errorLabels_field_present"] = "errorLabels" in reply
    return out


class Recorder:
    def __init__(self):
        self.steps = []
        self.lock = threading.Lock()

    def record(self, step, command, response, reading="", **extra):
        entry = {"step": step, "at_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                 "command": redact(command), "response": jsonable(response), "reading": reading}
        entry.update({k: jsonable(v) for k, v in extra.items()})
        with self.lock:
            self.steps.append(entry)
        print(f"\n### {step}\n  cmd: {entry['command']}\n  resp: {json.dumps(entry['response'], default=str)[:2500]}", flush=True)
        return entry


_WATCH = {"insert", "update", "delete", "find", "bulkWrite", "commitTransaction", "abortTransaction", "findAndModify", "aggregate"}


def _req_summary(name, cmd):
    s = {}
    for k in ("ordered", "autocommit", "startTransaction", "txnNumber", "readConcern", "writeConcern", "errorsOnly", "maxTimeMS"):
        if k in cmd:
            s[k] = jsonable(cmd[k])
    if name == "insert":
        s["n_documents"] = len(cmd.get("documents", []))
        s["collection"] = cmd.get("insert")
    elif name == "update":
        s["n_updates"] = len(cmd.get("updates", []))
        s["collection"] = cmd.get("update")
    elif name == "delete":
        s["n_deletes"] = len(cmd.get("deletes", []))
        s["collection"] = cmd.get("delete")
    elif name == "bulkWrite":
        s["n_ops"] = len(cmd.get("ops", []))
        s["nsInfo"] = jsonable(cmd.get("nsInfo"))
        s["ops_first3"] = jsonable(list(cmd.get("ops", []))[:3])
    elif name == "find":
        s["collection"] = cmd.get("find")
        s["filter"] = jsonable(cmd.get("filter"))
    return s


def _reply_brief(name, reply):
    if not isinstance(reply, dict):
        return jsonable(reply)
    b = {}
    for k in ("ok", "n", "nModified", "code", "codeName", "errmsg", "errorLabels", "nErrors", "nInserted", "nMatched", "nDeleted", "nUpserted", "writeConcernError"):
        if k in reply:
            b[k] = jsonable(reply[k])
    b["_errorLabels_field_present"] = "errorLabels" in reply
    if "writeErrors" in reply:
        we = reply["writeErrors"]
        b["writeErrors_count"] = len(we)
        b["writeErrors_first3"] = jsonable(we[:3])
    if name == "bulkWrite" and "cursor" in reply:
        b["cursor_firstBatch"] = jsonable(reply["cursor"].get("firstBatch", [])[:10])
    return b


class CmdLog(monitoring.CommandListener):
    """Records the driver's wire-level commands (whitelisted names only; never auth commands)."""

    def __init__(self, label):
        self.label = label
        self.events = []
        self._pending = {}
        self.lock = threading.Lock()
        self.t0 = time.monotonic()

    def mark(self):
        with self.lock:
            n = len(self.events)
        return n

    def since(self, n):
        with self.lock:
            return list(self.events[n:])

    def started(self, event):
        if event.command_name not in _WATCH:
            return
        with self.lock:
            self._pending[(event.request_id, event.connection_id)] = {
                "client": self.label,
                "cmd": event.command_name,
                "db": event.database_name,
                "t_s": round(time.monotonic() - self.t0, 3),
                "request": _req_summary(event.command_name, event.command),
            }

    def _finish(self, event, ok, reply):
        if event.command_name not in _WATCH:
            return
        with self.lock:
            e = self._pending.pop((event.request_id, event.connection_id), None)
            if e is None:
                return
            e["succeeded"] = ok
            e["duration_ms"] = round(event.duration_micros / 1000.0, 1)
            e["reply"] = _reply_brief(event.command_name, reply)
            self.events.append(e)

    def succeeded(self, event):
        self._finish(event, True, event.reply)

    def failed(self, event):
        self._finish(event, False, event.failure)


def raw_command(client, dbname, doc):
    """Send one command verbatim on a pooled connection (PyMongo adds only $db); return the raw reply."""
    with client._conn_for_writes(None, "raw_command") as conn:
        return conn.command(dbname, dict(doc), check=False)


def write_json(path, obj):
    with open(path, "w") as f:
        f.write(redact(json.dumps(obj, indent=2, default=lambda o: redact(repr(o)))))
