#!/usr/bin/env python
"""write-read-concerns (engine-tests-1.2): writeConcern (w / j / wtimeout) on insert and update,
readConcern levels on reads outside a transaction, readPreference modes on find (driver options
and raw $readPreference), and getDefaultRWConcern / setDefaultRWConcern, against the
documentdb-local container ddb-engine-test (open-source DocumentDB engine + gateway).

Rerun:
    /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I run.py

Reads LOCAL_URI from ../../engine-tests/local.env; the URI and password are never printed or
written. Owns database t_concern only: it is created here and dropped at the end.
getDefaultRWConcern / setDefaultRWConcern are admin-database commands by definition;
setDefaultRWConcern is sent only with the values getDefaultRWConcern already reports, so an
unexpected acceptance could not change the defaults that concurrent tests see.

Every step records the exact driver call, the command document pymongo put on the wire and the
server's reply or failure (captured with a CommandListener, rendered as MongoDB Extended JSON,
relaxed), the outcome, a verdict, a comparison with the DECISIONS.md topic 9 claims (which come
from the main-branch gateway source), and a one-sentence reading. Writes report.json.
"""
import datetime
import json
import os
import re
import shlex
import subprocess
import sys
import time
import traceback

import bson
import pymongo
from bson import Int64, Timestamp, json_util
from bson.son import SON
from pymongo import MongoClient, monitoring
from pymongo.errors import OperationFailure, PyMongoError
from pymongo.read_concern import ReadConcern
from pymongo.read_preferences import Nearest, Primary, PrimaryPreferred, Secondary, SecondaryPreferred
from pymongo.uri_parser import parse_uri
from pymongo.write_concern import WriteConcern

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.normpath(os.path.join(HERE, "..", "..", "engine-tests", "local.env"))
REPORT = os.path.join(HERE, "report.json")
DB = "t_concern"
COLL = "c"
CONTAINER = "ddb-engine-test"


# --------------------------------------------------------------------------- secrets / encoding
def load_uri():
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if line.startswith("LOCAL_URI="):
                v = line.split("=", 1)[1].strip()
                if v and v[0] in "\"'" and v[-1] == v[0]:
                    v = v[1:-1]
                return v
    raise SystemExit("LOCAL_URI not found in local.env")


URI = load_uri()
_PW = parse_uri(URI).get("password") or ""


def scrub(s):
    s = re.sub(r"(mongodb(?:\+srv)?://[^:/@]+:)[^@]+@", r"\1***@", str(s))
    if _PW and len(_PW) >= 4:
        s = s.replace(_PW, "***")
        s = s.replace(json.dumps(_PW)[1:-1], "***")
    return s


def ej(o):
    """Value as MongoDB Extended JSON (relaxed), scrubbed of credentials."""
    try:
        return json.loads(scrub(json_util.dumps(o, json_options=json_util.RELAXED_JSON_OPTIONS)))
    except Exception:  # noqa: BLE001
        return scrub(repr(o))


# --------------------------------------------------------------------------- monitoring
IGNORED = {"hello", "ismaster", "isMaster", "saslStart", "saslContinue", "authenticate", "getnonce",
           "endSessions"}


class Capture(monitoring.CommandListener):
    """Records every command event while armed (the step's own commands only)."""

    def __init__(self):
        self.armed = False
        self.events = []

    def start(self):
        self.events = []
        self.armed = True

    def stop(self):
        self.armed = False
        ev, self.events = self.events, []
        return ev

    def _want(self, name):
        return self.armed and name not in IGNORED

    def started(self, e):
        if self._want(e.command_name):
            self.events.append({"event": "CommandStarted", "command_name": e.command_name,
                                "database": e.database_name, "request_id": e.request_id,
                                "server_connection_id": e.server_connection_id,
                                "command": ej(dict(e.command))})

    def succeeded(self, e):
        if self._want(e.command_name):
            self.events.append({"event": "CommandSucceeded", "command_name": e.command_name,
                                "request_id": e.request_id, "server_connection_id": e.server_connection_id,
                                "duration_micros": e.duration_micros, "reply": ej(dict(e.reply))})

    def failed(self, e):
        if self._want(e.command_name):
            self.events.append({"event": "CommandFailed", "command_name": e.command_name,
                                "request_id": e.request_id, "server_connection_id": e.server_connection_id,
                                "duration_micros": e.duration_micros, "failure": ej(dict(e.failure))})


class PoolEvents(monitoring.ConnectionPoolListener):
    """Counts connection churn, used to show whether a w:0 write broke its connection."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.created = 0
        self.closed = 0
        self.closed_reasons = []
        self.checkout_failed = 0

    def snapshot(self):
        return {"connections_created": self.created, "connections_closed": self.closed,
                "closed_reasons": list(self.closed_reasons), "checkout_failed": self.checkout_failed}

    def pool_created(self, e): pass
    def pool_ready(self, e): pass
    def pool_cleared(self, e): pass
    def pool_closed(self, e): pass
    def connection_created(self, e): self.created += 1
    def connection_ready(self, e): pass

    def connection_closed(self, e):
        self.closed += 1
        self.closed_reasons.append(str(e.reason))

    def connection_check_out_started(self, e): pass
    def connection_check_out_failed(self, e): self.checkout_failed += 1
    def connection_checked_out(self, e): pass
    def connection_checked_in(self, e): pass


CAP = Capture()
POOL = PoolEvents()
STEPS = []

CODES = {"BadValue": 2, "FailedToParse": 9, "Unauthorized": 13, "IllegalOperation": 20, "InvalidOptions": 72,
         "CommandNotSupported": 115, "FailedToSatisfyReadPreference": 133, "CommandNotFound": 59,
         "UnknownBsonField": 40415}


def err_info(e):
    d = {"type": type(e).__name__, "message": scrub(str(e))}
    if isinstance(e, OperationFailure):
        det = e.details or {}
        d["code"] = e.code
        d["codeName"] = det.get("codeName")
        d["errmsg"] = det.get("errmsg")
        d["errorLabels"] = det.get("errorLabels")  # as the server sent it; None means the field was absent
        d["errorLabels_seen_by_driver"] = sorted(getattr(e, "_error_labels", None) or [])
        d["details"] = ej(det)
    return d


def wire_commands(rec):
    return [ev for ev in rec.get("wire", []) if ev["event"] == "CommandStarted"]


def wire_reply(rec, name=None, index=0):
    """index-th reply/failure document for command `name` (or any)."""
    out = [ev for ev in rec.get("wire", []) if ev["event"] in ("CommandSucceeded", "CommandFailed")
           and (name is None or ev["command_name"] == name)]
    if len(out) <= index:
        return None
    ev = out[index]
    return ev.get("reply") if ev["event"] == "CommandSucceeded" else ev.get("failure")


def compare(rec, exp):
    if not exp or exp.get("outcome") is None:
        return "no claim in DECISIONS.md"
    if rec["outcome"] == "exception":
        return "not comparable (driver-side exception)"
    if rec["outcome"] == "error" and rec["error"].get("code") is None and not wire_commands(rec):
        return "not comparable (driver refused before sending)"
    if exp["outcome"] == "accepted":
        return "match" if rec["outcome"] == "ok" else "differs (rejected; DECISIONS expects acceptance)"
    if rec["outcome"] != "error":
        return "differs (accepted; DECISIONS expects rejection)"
    e = rec["error"]
    probs = []
    if exp.get("codeName"):
        want = exp["codeName"]
        got_name, got_code = e.get("codeName"), e.get("code")
        if got_name != want and got_code != CODES.get(want):
            probs.append(f"got code {got_code} {got_name}, expected {want}")
    if exp.get("errmsg_contains"):
        msg = e.get("errmsg") or e.get("message") or ""
        if exp["errmsg_contains"] not in msg:
            probs.append(f"errmsg lacks {exp['errmsg_contains']!r}")
    return "match" if not probs else "differs: " + "; ".join(probs)


def run_step(sid, *, group, spec_item, question, decisions_item, driver_call, fn, read, post=None, expect=None,
             notes=None):
    CAP.start()
    t0 = time.perf_counter()
    rec = {"id": sid, "group": group, "spec_item": spec_item, "question": question,
           "decisions_item": decisions_item, "driver_call": driver_call}
    result = None
    try:
        result = fn()
        rec["outcome"] = "ok"
        rec["response"] = ej(result)
    except PyMongoError as e:
        rec["outcome"] = "error"
        rec["error"] = err_info(e)
    except Exception as e:  # noqa: BLE001
        rec["outcome"] = "exception"
        rec["error"] = {"type": type(e).__name__, "message": scrub(str(e)),
                        "trace": scrub(traceback.format_exc())}
    rec["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    rec["wire"] = CAP.stop()
    if post is not None:
        try:
            rec["observed_after"] = ej(post(rec, result))
        except Exception as e:  # noqa: BLE001
            rec["observed_after"] = {"post_check_exception": f"{type(e).__name__}: {scrub(str(e))}"}
    if expect is not None:
        rec["decisions_expectation"] = expect
        rec["matches_decisions"] = compare(rec, expect)
    if notes:
        rec["notes"] = notes
    try:
        rec["verdict"], rec["reading"] = read(rec)
    except Exception as e:  # noqa: BLE001
        rec["verdict"], rec["reading"] = "unclassified", f"Reading generator failed: {type(e).__name__}: {e}."
    if rec["outcome"] in ("error", "exception") and not wire_commands(rec):
        rec["verdict"] = "driver_refused"
        rec["reading"] = (f"pymongo raised {rec['error']['type']} before sending any command, so the gateway never saw "
                          f"it: {rec['error']['message']}.")
    elif str(rec.get("matches_decisions", "")).startswith("differs"):
        rec["reading"] = (rec["reading"].rstrip(".") +
                          f", which differs from DECISIONS.md topic 9 ({exp_text(expect)} per the main-branch gateway source).")
    STEPS.append(rec)
    print(f"[{rec['outcome']:>9}] {sid}: {rec['verdict']} | {rec['reading']}", flush=True)
    return rec


def exp_text(exp):
    if not exp or exp.get("outcome") is None:
        return "no claim"
    if exp["outcome"] == "accepted":
        return "it expects acceptance"
    t = f"it expects rejection with {exp.get('codeName') or 'an error'}"
    if exp.get("errmsg_contains"):
        t += f" \"...{exp['errmsg_contains']}...\""
    return t


def run_shell_step(sid, *, group, question, decisions_item, cmd, read, parse=None):
    """Read-only container inspection (not the wire protocol); recorded like any other step."""
    t0 = time.perf_counter()
    rec = {"id": sid, "group": group, "spec_item": "supplementary: container inspection", "question": question,
           "decisions_item": decisions_item, "driver_call": " ".join(shlex.quote(c) for c in cmd), "wire": []}
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        rec["outcome"] = "ok" if r.returncode == 0 else "error"
        rec["response"] = {"exit": r.returncode, "output": scrub(out)[:20000]}
        if parse is not None:
            rec["parsed"] = parse(out)
    except Exception as e:  # noqa: BLE001
        rec["outcome"] = "exception"
        rec["error"] = {"type": type(e).__name__, "message": scrub(str(e))}
    rec["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    try:
        rec["verdict"], rec["reading"] = read(rec)
    except Exception as e:  # noqa: BLE001
        rec["verdict"], rec["reading"] = "unclassified", f"Reading generator failed: {type(e).__name__}: {e}."
    STEPS.append(rec)
    print(f"[{rec['outcome']:>9}] {sid}: {rec['verdict']} | {rec['reading']}", flush=True)
    return rec


def fmt_err(rec):
    e = rec["error"]
    if e.get("code") is None:
        return f"{e['type']}: {e['message']}"
    labels = e.get("errorLabels")
    lab = "no errorLabels field" if labels is None else f"errorLabels {json.dumps(labels)}"
    return f"code {e['code']} {e.get('codeName')} \"{e.get('errmsg') or e['message']}\" ({lab})"


def jd(o):
    return json.dumps(ej(o), separators=(", ", ": "))


# --------------------------------------------------------------------------- readings
def reading_write(kind, wc_text, label, framing):
    """kind: insert|update; framing: raw|driver|client."""
    def f(rec):
        obs = rec.get("observed_after") or {}
        landed = obs.get("document_present") if kind == "insert" else obs.get("update_applied")
        what = "the document" if kind == "insert" else "the update"
        if rec["outcome"] != "ok":
            reply = wire_reply(rec)
            level = ("a command-level failure (ok:0)" if isinstance(reply, dict) and reply.get("ok") in (0, 0.0)
                     else "an error")
            if landed is False:
                effect = f"{what} was NOT applied, so writeConcern {wc_text} is validated before the {kind} executes"
            elif landed:
                effect = f"{what} WAS applied anyway, so the error for writeConcern {wc_text} is reported after the write"
            else:
                effect = f"whether {what} landed could not be checked"
            return "rejected", f"Rejected as {level} with {fmt_err(rec)}, and {effect}."
        reply = wire_reply(rec) or {}
        n = reply.get("n")
        wce = reply.get("writeConcernError")
        wce_txt = "no writeConcernError" if not wce else f"writeConcernError {jd(wce)}"
        state = (f"{what} is visible afterwards" if landed else f"{what} is NOT visible afterwards")
        if not landed:
            return "accepted_not_applied", (f"Accepted: {kind} with writeConcern {wc_text} returned ok:1, n:{n}, "
                                            f"{wce_txt}, but {state}.")
        if label in ("w1", "control"):
            return "accepted_honored", (f"Accepted: {kind} with {wc_text} returned ok:1, n:{n}, {wce_txt}, and "
                                        f"{state}, which is the w:1 acknowledgement contract.")
        if label == "w0" and framing == "raw":
            return "accepted_silently", (f"Accepted silently: {kind} with writeConcern {wc_text} sent as an ordinary "
                                         f"request (no moreToCome flag) still got a full reply ok:1, n:{n}, and "
                                         f"{state}, so w:0 inside the command body changes nothing.")
        return "accepted_silently", (f"Accepted silently: {kind} with writeConcern {wc_text} returned ok:1, n:{n}, "
                                     f"{wce_txt}, and {state}, with no observable difference from w:1 on this "
                                     f"single-node engine.")
    return f


def reading_w0_driver(kind):
    def f(rec):
        obs = rec.get("observed_after") or {}
        resp = rec.get("response") or {}
        if rec["outcome"] != "ok":
            if rec["error"].get("code") is not None:
                return "rejected", f"The unacknowledged {kind} sequence failed with {fmt_err(rec)}."
            return "accepted_not_honored", (f"The same-connection follow-up after the unacknowledged {kind} raised "
                                            f"{rec['error']['type']} ({rec['error']['message']}), so the gateway did not "
                                            f"treat the OP_MSG moreToCome message as reply-less.")
        pool = resp.get("pool_during_step") or {}
        conn_ids = sorted({ev.get("server_connection_id") for ev in rec["wire"] if ev["event"] == "CommandStarted"
                           and ev.get("server_connection_id") is not None})
        landed = obs.get("visible_to_separate_client")
        follow = resp.get("same_connection_follow_up_find")
        same_conn = len(conn_ids) == 1
        clean = same_conn and pool.get("connections_created") == 0 and pool.get("connections_closed") == 0
        ok = landed and follow and clean and resp.get("acknowledged") is False
        verdict = "accepted_honored" if ok else "accepted_not_honored"
        return verdict, (f"Driver-level w:0 {kind} (OP_MSG moreToCome) returned acknowledged=False, the follow-up "
                         f"find on the same server connection {conn_ids} "
                         f"{'succeeded' if follow else 'did not return the document'} with "
                         f"{pool.get('connections_created')} connection(s) created and "
                         f"{pool.get('connections_closed')} closed, and the {'document' if kind == 'insert' else 'update'} "
                         f"{'is' if landed else 'is NOT'} visible to a separate client, so the gateway "
                         f"{'sent no reply and applied the write' if ok else 'did not behave as an unacknowledged write should'}.")
    return f


def reading_read_concern(level_text, framing):
    def f(rec):
        if rec["outcome"] != "ok":
            return "rejected", f"Rejected with {fmt_err(rec)}, so readConcern {level_text} is refused on this path."
        reply = wire_reply(rec) or {}
        cur = reply.get("cursor") or {}
        n = len(cur.get("firstBatch") or [])
        atct = cur.get("atClusterTime")
        sent = [ev["command"].get("readConcern") for ev in wire_commands(rec)]
        sent_txt = f"readConcern {jd(sent[0])} was on the wire" if sent and sent[0] is not None else \
            "the command carried no readConcern"
        if "snapshot" in level_text and "atClusterTime" not in level_text:
            if atct is None:
                resp = rec.get("response")
                extra = ""
                if isinstance(resp, dict) and "session_snapshot_time" in resp:
                    extra = (f" and pymongo's snapshot session recorded snapshot time "
                             f"{jd(resp.get('session_snapshot_time'))}")
                return "accepted_not_honored", (f"Accepted: {sent_txt} and the reply returned {n} document(s) but no "
                                                f"cursor.atClusterTime{extra}, so the level is accepted without exposing the "
                                                f"snapshot point a driver snapshot session uses to pin later reads.")
            return "accepted_honored", (f"Accepted: {sent_txt} and the reply carried cursor.atClusterTime "
                                        f"{jd(atct)} with {n} document(s).")
        return "accepted_silently", (f"Accepted silently: {sent_txt}, the reply returned {n} document(s), and nothing "
                                     f"distinguishes the result from a read without readConcern on this single-node engine.")
    return f


def reading_read_pref(mode_text, framing):
    def f(rec):
        cmds = wire_commands(rec)
        rp = cmds[0]["command"].get("$readPreference") if cmds else None
        rp_txt = (f"$readPreference {jd(rp)} was on the wire" if rp is not None
                  else "the driver sent no $readPreference (pymongo omits it for primary)")
        if rec["outcome"] != "ok":
            return "rejected", f"Rejected with {fmt_err(rec)}; {rp_txt}."
        reply = wire_reply(rec) or {}
        n = len(((reply.get("cursor") or {}).get("firstBatch")) or []) if reply else None
        if n is None and isinstance(rec.get("response"), list):
            n = len(rec["response"])
        return "accepted_silently", (f"Accepted silently: {rp_txt} and the find returned {n} document(s); a "
                                     f"single-node gateway has no other member to route {mode_text} to.")
    return f


# --------------------------------------------------------------------------- helpers
def driver_result(r):
    """Plain dict of a pymongo write result."""
    if r is None:
        return None
    d = {"type": type(r).__name__, "acknowledged": r.acknowledged}
    if hasattr(r, "inserted_id"):
        d["inserted_id"] = r.inserted_id
    if r.acknowledged and hasattr(r, "matched_count"):
        d["matched_count"] = r.matched_count
        d["modified_count"] = r.modified_count
        d["raw_result"] = r.raw_result
    return d


def docker_provenance():
    out = {}
    for key, cmd in {
        "docker_inspect": ["docker", "inspect", CONTAINER, "--format",
                           "{{.Config.Image}} {{.Image}} created={{.Created}}"],
        "docker_ps": ["docker", "ps", "--filter", f"name={CONTAINER}", "--format",
                      "{{.Names}} | {{.Status}} | {{.Image}}"],
    }.items():
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            out[key] = {"command": " ".join(cmd), "exit": r.returncode, "output": (r.stdout + r.stderr).strip()}
        except Exception as e:  # noqa: BLE001
            out[key] = {"command": " ".join(cmd), "error": repr(e)}
    return out


# --------------------------------------------------------------------------- DECISIONS references
DEC_W = ("DECISIONS.md topic 9 settled: 'Which writeConcern w values are honored, with and without HA?' "
         "(engine_source, main-branch write_concern.rs); open item 8 (Azure gateway parity)")
DEC_J = "DECISIONS.md topic 9 settled: 'Is writeConcern j (journal) honored?' (engine_source)"
DEC_WT = "DECISIONS.md topic 9 settled: 'Is wtimeoutMS / wtimeout honored?' (engine_source)"
DEC_RC = ("DECISIONS.md topic 9 settled: 'Which readConcern levels are honored?' (engine_source, validation.rs / "
          "read_concern.rs); open item 3 (snapshot)")
DEC_RP = ("DECISIONS.md topic 9 settled: 'Which readPreference values are honored, with and without HA, and what is "
          "the default?' (engine_source, read_preference.rs); kit statement skills/connection/SKILL.md:207 (nearest)")
DEC_GD = ("DECISIONS.md topic 9 settled: 'What does getDefaultRWConcern return?' (engine_source, constant.rs) and the "
          "compatibility-page rows getDefaultRWConcern Yes / setDefaultRWConcern No")
SRC = "DECISIONS.md topic 9, from the main-branch gateway source"

ACCEPT = {"outcome": "accepted", "source": SRC}


def REJECT(code_name, contains=None):
    d = {"outcome": "rejected", "codeName": code_name, "source": SRC}
    if contains:
        d["errmsg_contains"] = contains
    return d


# --------------------------------------------------------------------------- main
def main():
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    client = MongoClient(URI, serverSelectionTimeoutMS=15000, socketTimeoutMS=60000, connectTimeoutMS=15000,
                         event_listeners=[CAP])
    admin = client.admin
    db = client[DB]
    coll = db[COLL]

    bi = admin.command("buildInfo")
    hello = admin.command("hello")
    td = client.topology_description
    engine = {
        "buildInfo.version": bi.get("version"),
        "buildInfo.versionArray": ej(bi.get("versionArray")),
        "hello.internal.documentdb_versions": ej((hello.get("internal") or {}).get("documentdb_versions")),
        "hello.msg": hello.get("msg"),
        "hello.maxWireVersion": hello.get("maxWireVersion"),
        "hello.isWritablePrimary": hello.get("isWritablePrimary"),
        "hello.setName": hello.get("setName"),
        "hello.hosts": ej(hello.get("hosts")),
        "hello.logicalSessionTimeoutMinutes": hello.get("logicalSessionTimeoutMinutes"),
        "driver_topology_type": td.topology_type_name,
        "driver_server_types": [s.server_type_name for s in td.server_descriptions().values()],
        "buildInfo_full": ej(bi),
        "hello_full": ej(hello),
    }
    print("engine:", json.dumps({k: v for k, v in engine.items() if not k.endswith("_full")}), flush=True)

    # ---------------------------------------------------------------- setup (own database only)
    G0 = "S setup"
    pre_exists = DB in client.list_database_names()
    if pre_exists:
        run_step("S.drop_leftover_database", group=G0, spec_item="setup", question="Remove a t_concern left by an earlier run.",
                 decisions_item=None, driver_call=f"client.drop_database('{DB}')",
                 fn=lambda: client.drop_database(DB),
                 read=lambda r: ("setup", "Dropped a t_concern database left over from an earlier run of this script."))
    seed = [{"_id": "raw_upd_target", "n": 0, "last": None}, {"_id": "drv_upd_target", "n": 0, "last": None},
            {"_id": "read_target", "v": 1}]
    run_step("S.seed", group=G0, spec_item="setup", question="Create t_concern.c with the update and read targets.",
             decisions_item=None, driver_call=f"client['{DB}']['{COLL}'].insert_many({seed!r})",
             fn=lambda: {"inserted_ids": coll.insert_many([dict(d) for d in seed]).inserted_ids},
             read=lambda r: ("setup", f"Seeded {len(seed)} documents with the default write concern (outcome {r['outcome']})."))

    def present(doc_id):
        return coll.count_documents({"_id": doc_id}) == 1

    # ---------------------------------------------------------------- A. raw insert/update commands
    GA = "A writeConcern in raw insert/update command bodies (db.command, ordinary acknowledged OP_MSG)"
    raw_variants = [
        # label, spec item, writeConcern document (None = omit), decisions ref, expectation
        ("control", "no writeConcern (control)", None, DEC_W, ACCEPT),
        ("w1", "w:1", {"w": 1}, DEC_W, ACCEPT),
        ("w_majority", "w:majority", {"w": "majority"}, DEC_W, ACCEPT),
        ("w0", "w:0", {"w": 0}, DEC_W, ACCEPT),
        ("w2", "w:2", {"w": 2}, DEC_W, REJECT("BadValue", "exceeds the number of data-bearing voting members")),
        ("w3", "w:3", {"w": 3}, DEC_W, REJECT("BadValue", "exceeds the number of data-bearing voting members")),
        ("j_true", "j:true", {"j": True}, DEC_J, ACCEPT),
        ("j_false", "j:false", {"j": False}, DEC_J, ACCEPT),
        ("w_majority_wtimeout1", "wtimeoutMS:1", {"w": "majority", "wtimeout": 1}, DEC_WT, ACCEPT),
        # extras (clearly labelled)
        ("extra_w_tag", "extra: w:<custom tag>", {"w": "myTag"}, DEC_W, REJECT("BadValue")),
        ("extra_w0_j_true", "extra: w:0 with j:true", {"w": 0, "j": True}, DEC_J, {"outcome": None}),
        ("extra_wtimeoutMS_field", "extra: wtimeoutMS spelled inside writeConcern",
         {"w": "majority", "wtimeoutMS": 1}, DEC_WT, REJECT("UnknownBsonField")),
        ("extra_wtimeout_over_int32", "extra: wtimeout above int32 max",
         {"w": 1, "wtimeout": Int64(2147483648)}, DEC_WT,
         REJECT("FailedToParse", "must not exceed the maximum 32-bit integer")),
    ]
    for label, item, wc, dref, exp in raw_variants:
        wc_text = "omitted" if wc is None else jd(wc)
        doc_id = f"raw_ins_{label}"

        def ins(wc=wc, doc_id=doc_id, label=label):
            cmd = SON([("insert", COLL), ("documents", [{"_id": doc_id, "wc": label}])])
            if wc is not None:
                cmd["writeConcern"] = wc
            return db.command(cmd)

        call = (f"client['{DB}'].command(SON([('insert', '{COLL}'), ('documents', [{{'_id': '{doc_id}', 'wc': '{label}'}}])"
                + (f", ('writeConcern', {wc!r})" if wc is not None else "") + "]))")
        run_step(f"A.raw.insert.{label}", group=GA, spec_item=item,
                 question=f"Does an insert command whose body carries writeConcern {wc_text} succeed, and does the write land?",
                 decisions_item=dref, driver_call=call, fn=ins, expect=exp,
                 post=lambda rec, res, doc_id=doc_id: {"document_present": present(doc_id)},
                 read=reading_write("insert", wc_text if wc is not None else "no writeConcern", label, "raw"))

        def upd(wc=wc, label=label):
            cmd = SON([("update", COLL),
                       ("updates", [SON([("q", {"_id": "raw_upd_target"}),
                                         ("u", {"$set": {"last": label}, "$inc": {"n": 1}})])])])
            if wc is not None:
                cmd["writeConcern"] = wc
            return db.command(cmd)

        def upd_post(rec, res, label=label):
            d = coll.find_one({"_id": "raw_upd_target"})
            return {"update_applied": bool(d and d.get("last") == label), "target_after": d}

        call = (f"client['{DB}'].command(SON([('update', '{COLL}'), ('updates', [SON([('q', {{'_id': 'raw_upd_target'}}), "
                f"('u', {{'$set': {{'last': '{label}'}}, '$inc': {{'n': 1}}}})])])"
                + (f", ('writeConcern', {wc!r})" if wc is not None else "") + "]))")
        run_step(f"A.raw.update.{label}", group=GA, spec_item=item,
                 question=f"Does an update command whose body carries writeConcern {wc_text} succeed, and is the update applied?",
                 decisions_item=dref, driver_call=call, fn=upd, expect=exp, post=upd_post,
                 read=reading_write("update", wc_text if wc is not None else "no writeConcern", label, "raw"))

    # ---------------------------------------------------------------- B. driver-level WriteConcern objects
    GB = "B writeConcern through pymongo WriteConcern options (collection.with_options / MongoClient kwargs)"
    drv_variants = [
        ("w1", "w:1", WriteConcern(w=1), "WriteConcern(w=1)", DEC_W, ACCEPT),
        ("w_majority", "w:majority", WriteConcern(w="majority"), "WriteConcern(w='majority')", DEC_W, ACCEPT),
        ("w2", "w:2", WriteConcern(w=2), "WriteConcern(w=2)", DEC_W,
         REJECT("BadValue", "exceeds the number of data-bearing voting members")),
        ("w3", "w:3", WriteConcern(w=3), "WriteConcern(w=3)", DEC_W,
         REJECT("BadValue", "exceeds the number of data-bearing voting members")),
        ("j_true", "j:true", WriteConcern(j=True), "WriteConcern(j=True)", DEC_J, ACCEPT),
        ("j_false", "j:false", WriteConcern(j=False), "WriteConcern(j=False)", DEC_J, ACCEPT),
        ("w_majority_wtimeout1", "wtimeoutMS:1", WriteConcern(w="majority", wtimeout=1),
         "WriteConcern(w='majority', wtimeout=1)", DEC_WT, ACCEPT),
    ]
    for label, item, wco, wtext, dref, exp in drv_variants:
        c2 = coll.with_options(write_concern=wco)
        doc_id = f"drv_ins_{label}"
        run_step(f"B.driver.insert_one.{label}", group=GB, spec_item=item,
                 question=f"Does insert_one through {wtext} succeed, and what writeConcern does the driver put on the wire?",
                 decisions_item=dref,
                 driver_call=f"client['{DB}']['{COLL}'].with_options(write_concern={wtext}).insert_one({{'_id': '{doc_id}', 'wc': '{label}'}})",
                 fn=lambda c2=c2, doc_id=doc_id, label=label: driver_result(c2.insert_one({"_id": doc_id, "wc": label})),
                 expect=exp, post=lambda rec, res, doc_id=doc_id: {"document_present": present(doc_id)},
                 read=reading_write("insert", jd(wco.document), label, "driver"))

        def dupd_post(rec, res, label=label):
            d = coll.find_one({"_id": "drv_upd_target"})
            return {"update_applied": bool(d and d.get("last") == label), "target_after": d}

        run_step(f"B.driver.update_one.{label}", group=GB, spec_item=item,
                 question=f"Does update_one through {wtext} succeed, and is the update applied?",
                 decisions_item=dref,
                 driver_call=(f"client['{DB}']['{COLL}'].with_options(write_concern={wtext}).update_one("
                              f"{{'_id': 'drv_upd_target'}}, {{'$set': {{'last': '{label}'}}, '$inc': {{'n': 1}}}})"),
                 fn=lambda c2=c2, label=label: driver_result(
                     c2.update_one({"_id": "drv_upd_target"}, {"$set": {"last": label}, "$inc": {"n": 1}})),
                 expect=exp, post=dupd_post,
                 read=reading_write("update", jd(wco.document), label, "driver"))

    # w:0 through the driver: OP_MSG moreToCome. One pooled connection, so a stray reply from the
    # gateway would surface as a ProtocolError on the follow-up command, and connection churn is counted.
    c_w0 = MongoClient(URI, maxPoolSize=1, minPoolSize=0, retryReads=False, serverSelectionTimeoutMS=15000,
                       socketTimeoutMS=60000, event_listeners=[CAP, POOL])
    c_w0[DB][COLL].find_one({"_id": "read_target"})  # warm and authenticate the single connection
    w0coll = c_w0[DB][COLL].with_options(write_concern=WriteConcern(w=0))

    def drv_w0_insert():
        POOL.reset()
        r = w0coll.insert_one({"_id": "drv_ins_w0", "wc": "w0"})
        follow = c_w0[DB][COLL].find_one({"_id": "drv_ins_w0"})
        d = driver_result(r)
        d["same_connection_follow_up_find"] = follow
        d["pool_during_step"] = POOL.snapshot()
        return d

    def w0_ins_post(rec, res):
        t_end = time.time() + 5
        seen = present("drv_ins_w0")
        while not seen and time.time() < t_end:
            time.sleep(0.25)
            seen = present("drv_ins_w0")
        return {"visible_to_separate_client": seen, "document_present": seen}

    run_step("B.driver.insert_one.w0", group=GB, spec_item="w:0",
             question="Is a driver-level unacknowledged w:0 insert (OP_MSG with moreToCome) accepted without a reply and applied?",
             decisions_item=DEC_W,
             driver_call=("c_w0 = MongoClient(LOCAL_URI, maxPoolSize=1, retryReads=False); "
                          f"c_w0['{DB}']['{COLL}'].with_options(write_concern=WriteConcern(w=0)).insert_one({{'_id': 'drv_ins_w0', 'wc': 'w0'}}); "
                          f"then c_w0['{DB}']['{COLL}'].find_one({{'_id': 'drv_ins_w0'}}) on the same single pooled connection"),
             fn=drv_w0_insert, post=w0_ins_post, expect=ACCEPT,
             notes=("pymongo sends unacknowledged writes as OP_MSG with flagBits moreToCome (pymongo/synchronous/pool.py "
                    "computes unacknowledged from the write concern; command_runner.py sets _OpMsg.MORE_TO_COME) and "
                    "publishes a synthetic {ok: 1} CommandSucceeded event because no reply is read."),
             read=reading_w0_driver("insert"))

    def drv_w0_update():
        POOL.reset()
        r = w0coll.update_one({"_id": "drv_upd_target"}, {"$set": {"last": "w0"}, "$inc": {"n": 1}})
        follow = c_w0[DB][COLL].find_one({"_id": "drv_upd_target"})
        d = driver_result(r)
        d["same_connection_follow_up_find"] = follow
        d["pool_during_step"] = POOL.snapshot()
        return d

    def w0_upd_post(rec, res):
        t_end = time.time() + 5
        d = coll.find_one({"_id": "drv_upd_target"})
        while not (d and d.get("last") == "w0") and time.time() < t_end:
            time.sleep(0.25)
            d = coll.find_one({"_id": "drv_upd_target"})
        ok = bool(d and d.get("last") == "w0")
        return {"visible_to_separate_client": ok, "update_applied": ok, "target_after": d}

    run_step("B.driver.update_one.w0", group=GB, spec_item="w:0",
             question="Is a driver-level unacknowledged w:0 update (OP_MSG with moreToCome) accepted without a reply and applied?",
             decisions_item=DEC_W,
             driver_call=(f"c_w0['{DB}']['{COLL}'].with_options(write_concern=WriteConcern(w=0)).update_one("
                          "{'_id': 'drv_upd_target'}, {'$set': {'last': 'w0'}, '$inc': {'n': 1}}); then "
                          f"c_w0['{DB}']['{COLL}'].find_one({{'_id': 'drv_upd_target'}}) on the same single pooled connection"),
             fn=drv_w0_update, post=w0_upd_post, expect=ACCEPT,
             notes="Same single-connection client as B.driver.insert_one.w0.",
             read=reading_w0_driver("update"))
    c_w0.close()

    # Client-level options: the URI/kwarg spelling wTimeoutMS.
    c_wt = MongoClient(URI, w="majority", wTimeoutMS=1, serverSelectionTimeoutMS=15000, socketTimeoutMS=60000,
                       event_listeners=[CAP])
    ccoll = c_wt[DB][COLL]
    run_step("B.client.insert_one.w_majority_wTimeoutMS1", group=GB, spec_item="wtimeoutMS:1",
             question="With the client option wTimeoutMS=1 (and w='majority'), what reaches the wire and is the insert accepted?",
             decisions_item=DEC_WT,
             driver_call=(f"MongoClient(LOCAL_URI, w='majority', wTimeoutMS=1)['{DB}']['{COLL}']"
                          ".insert_one({'_id': 'cli_ins_wtimeoutMS1', 'wc': 'client_wTimeoutMS1'})"),
             fn=lambda: driver_result(ccoll.insert_one({"_id": "cli_ins_wtimeoutMS1", "wc": "client_wTimeoutMS1"})),
             expect=ACCEPT, post=lambda rec, res: {"document_present": present("cli_ins_wtimeoutMS1")},
             read=reading_write("insert", "{w: 'majority', wtimeout: 1} from the client options", "w_majority_wtimeout1",
                                "client"))

    def cupd_post(rec, res):
        d = coll.find_one({"_id": "drv_upd_target"})
        return {"update_applied": bool(d and d.get("last") == "client_wTimeoutMS1"), "target_after": d}

    run_step("B.client.update_one.w_majority_wTimeoutMS1", group=GB, spec_item="wtimeoutMS:1",
             question="With the client option wTimeoutMS=1 (and w='majority'), is update_one accepted and applied?",
             decisions_item=DEC_WT,
             driver_call=(f"MongoClient(LOCAL_URI, w='majority', wTimeoutMS=1)['{DB}']['{COLL}'].update_one("
                          "{'_id': 'drv_upd_target'}, {'$set': {'last': 'client_wTimeoutMS1'}, '$inc': {'n': 1}})"),
             fn=lambda: driver_result(ccoll.update_one({"_id": "drv_upd_target"},
                                                       {"$set": {"last": "client_wTimeoutMS1"}, "$inc": {"n": 1}})),
             expect=ACCEPT, post=cupd_post,
             read=reading_write("update", "{w: 'majority', wtimeout: 1} from the client options", "w_majority_wtimeout1",
                                "client"))
    c_wt.close()

    # ---------------------------------------------------------------- C. readConcern outside a transaction
    GC = "C readConcern on reads outside a transaction"
    rc_expect = {
        "local": ACCEPT,
        "majority": ACCEPT,
        "available": REJECT("CommandNotSupported", "'Available' read concern is not supported"),
        "linearizable": REJECT("CommandNotSupported", "'Linearizable' read concern is not supported"),
        "snapshot": REJECT("CommandNotSupported", "'Snapshot' read concern is not supported"),
    }
    for level in ("local", "majority", "available", "linearizable", "snapshot"):
        exp = rc_expect[level]
        run_step(f"C.raw.find.{level}", group=GC, spec_item=f"readConcern {level}",
                 question=f"Is a find command with readConcern {{level: '{level}'}} accepted outside a transaction?",
                 decisions_item=DEC_RC,
                 driver_call=(f"client['{DB}'].command(SON([('find', '{COLL}'), ('filter', {{'_id': 'read_target'}}), "
                              f"('readConcern', {{'level': '{level}'}})]))"),
                 fn=lambda level=level: db.command(SON([("find", COLL), ("filter", {"_id": "read_target"}),
                                                        ("readConcern", {"level": level})])),
                 expect=exp, read=reading_read_concern(f"{{level: '{level}'}}", "raw"))
        rcoll = coll.with_options(read_concern=ReadConcern(level))
        run_step(f"C.driver.find.{level}", group=GC, spec_item=f"readConcern {level}",
                 question=f"Does pymongo's ReadConcern('{level}') reach the gateway and get the same verdict?",
                 decisions_item=DEC_RC,
                 driver_call=f"list(client['{DB}']['{COLL}'].with_options(read_concern=ReadConcern('{level}')).find({{'_id': 'read_target'}}))",
                 fn=lambda rcoll=rcoll: list(rcoll.find({"_id": "read_target"})),
                 expect=exp, read=reading_read_concern(f"{{level: '{level}'}}", "driver"))
        run_step(f"C.raw.aggregate.{level}", group=GC, spec_item=f"readConcern {level}",
                 question=f"Does aggregate validate readConcern {{level: '{level}'}} the same way as find?",
                 decisions_item=DEC_RC,
                 driver_call=(f"client['{DB}'].command(SON([('aggregate', '{COLL}'), ('pipeline', [{{'$match': {{'_id': 'read_target'}}}}]), "
                              f"('cursor', {{}}), ('readConcern', {{'level': '{level}'}})]))"),
                 fn=lambda level=level: db.command(SON([("aggregate", COLL), ("pipeline", [{"$match": {"_id": "read_target"}}]),
                                                        ("cursor", {}), ("readConcern", {"level": level})])),
                 expect=exp, read=reading_read_concern(f"{{level: '{level}'}}", "raw"))

    # extras
    rc_extras = [
        ("extra_no_readConcern", "extra: no readConcern (control)", None, ACCEPT),
        ("extra_empty_readConcern", "extra: readConcern {}", {}, {"outcome": None}),
        ("extra_level_Majority_case", "extra: level 'Majority' (case)", {"level": "Majority"},
         REJECT("BadValue", "Invalid readConcern level")),
        ("extra_level_bogus", "extra: unknown level", {"level": "bogus"}, REJECT("BadValue", "Invalid readConcern level")),
        ("extra_afterClusterTime", "extra: majority + afterClusterTime", {"level": "majority", "afterClusterTime": Timestamp(1, 1)},
         dict(REJECT("IllegalOperation"), note="main-branch read_concern.rs doc; issue #770 reports release/1.0-RC2 silently accepts it")),
        ("extra_atClusterTime_majority", "extra: majority + atClusterTime", {"level": "majority", "atClusterTime": Timestamp(1, 1)},
         dict(REJECT("InvalidOptions"), note="main-branch read_concern.rs doc; issue #770 reports release/1.0-RC2 silently accepts it")),
        ("extra_atClusterTime_snapshot", "extra: snapshot + atClusterTime", {"level": "snapshot", "atClusterTime": Timestamp(1, 1)},
         {"outcome": None}),
    ]
    for label, item, rc, exp in rc_extras:
        def fx(rc=rc):
            cmd = SON([("find", COLL), ("filter", {"_id": "read_target"})])
            if rc is not None:
                cmd["readConcern"] = rc
            return db.command(cmd)
        call = (f"client['{DB}'].command(SON([('find', '{COLL}'), ('filter', {{'_id': 'read_target'}})"
                + (f", ('readConcern', {rc!r})" if rc is not None else "") + "]))")
        run_step(f"C.raw.find.{label}", group=GC, spec_item=item,
                 question=f"How does the gateway treat readConcern {jd(rc) if rc is not None else '(absent)'} on find?",
                 decisions_item=DEC_RC, driver_call=call, fn=fx, expect=exp,
                 read=reading_read_concern(jd(rc) if rc is not None else "(absent)", "raw"))

    # snapshot session (the MongoDB 5.0+ way to do snapshot reads outside a transaction)
    def snap_session():
        with client.start_session(snapshot=True) as s:
            docs = list(coll.find({"_id": "read_target"}, session=s))
            return {"docs": docs, "session_snapshot_time": getattr(s, "_snapshot_time", None)}

    run_step("C.driver.snapshot_session.find", group=GC, spec_item="readConcern snapshot",
             question="Does a pymongo snapshot session (start_session(snapshot=True)) read work outside a transaction?",
             decisions_item=DEC_RC,
             driver_call=(f"with client.start_session(snapshot=True) as s: list(client['{DB}']['{COLL}'].find("
                          "{'_id': 'read_target'}, session=s))"),
             fn=snap_session, expect=REJECT("CommandNotSupported", "'Snapshot' read concern is not supported"),
             read=reading_read_concern("{level: 'snapshot'} via a snapshot session", "driver"))

    # causal-consistency session: does the gateway return operationTime so that the driver sends afterClusterTime?
    def causal():
        with client.start_session(causal_consistency=True) as s:
            coll.insert_one({"_id": "causal_doc", "wc": "causal"}, session=s)
            op_time = s.operation_time
            cl_time = s.cluster_time
            docs = list(coll.with_options(read_concern=ReadConcern("majority")).find({"_id": "causal_doc"}, session=s))
            return {"session_operation_time_after_write": op_time, "session_cluster_time_after_write": cl_time,
                    "docs": docs}

    def causal_read(rec):
        if rec["outcome"] != "ok":
            return "rejected", f"The causal session failed with {fmt_err(rec)}."
        finds = [ev for ev in wire_commands(rec) if ev["command_name"] == "find"]
        rc = finds[0]["command"].get("readConcern") if finds else None
        ins_reply = wire_reply(rec, "insert") or {}
        op_time = (rec.get("response") or {}).get("session_operation_time_after_write")
        has_act = isinstance(rc, dict) and "afterClusterTime" in rc
        return ("accepted_honored" if has_act else "accepted_silently"), (
            f"In a causally consistent session the insert reply {'carried' if 'operationTime' in ins_reply else 'carried no'} "
            f"operationTime (session.operation_time={jd(op_time)}), so the following majority find was sent with readConcern "
            f"{jd(rc)} and {'was accepted with afterClusterTime' if has_act else 'had no afterClusterTime to send'}, returning "
            f"{len((rec.get('response') or {}).get('docs') or [])} document(s).")

    run_step("C.driver.causal_session.majority_find", group=GC, spec_item="extra: causal session (majority + afterClusterTime)",
             question="Does a causally consistent session make the driver send afterClusterTime, and does the gateway accept it?",
             decisions_item=DEC_RC,
             driver_call=(f"with client.start_session(causal_consistency=True) as s: client['{DB}']['{COLL}'].insert_one("
                          "{'_id': 'causal_doc', 'wc': 'causal'}, session=s); list(client['" + DB + "']['" + COLL +
                          "'].with_options(read_concern=ReadConcern('majority')).find({'_id': 'causal_doc'}, session=s))"),
             fn=causal, expect={"outcome": None}, read=causal_read)

    # ---------------------------------------------------------------- C2. diagnostic, beyond the spec
    # The spec asks for readConcern outside a transaction. These four steps repeat the levels as a
    # transaction's readConcern only to explain why outside-transaction results differ from the
    # DECISIONS.md claims (main-branch validation.rs), which name no transaction scope.
    GC2 = "C2 diagnostic beyond the spec: the same readConcern levels as a transaction readConcern"
    txn_expect = {
        "majority": ACCEPT,
        "snapshot": REJECT("CommandNotSupported", "'Snapshot' read concern is not supported"),
        "available": REJECT("CommandNotSupported", "'Available' read concern is not supported"),
        "linearizable": REJECT("CommandNotSupported", "'Linearizable' read concern is not supported"),
    }
    for level in ("majority", "snapshot", "available", "linearizable"):
        def txn(level=level):
            with client.start_session() as s:
                s.start_transaction(read_concern=ReadConcern(level))
                try:
                    docs = list(coll.find({"_id": "read_target"}, session=s))
                    s.commit_transaction()
                    return {"docs": docs, "committed": True}
                except Exception:
                    if s.in_transaction:
                        s.abort_transaction()
                    raise

        run_step(f"C2.diag.transaction.{level}", group=GC2, spec_item=f"diagnostic: readConcern {level} in a transaction",
                 question=(f"Is readConcern {{level: '{level}'}} refused when it is the transaction's readConcern, which "
                           f"would explain why the outside-transaction result differs from DECISIONS.md?"),
                 decisions_item=DEC_RC,
                 driver_call=(f"with client.start_session() as s: s.start_transaction(read_concern=ReadConcern('{level}')); "
                              f"list(client['{DB}']['{COLL}'].find({{'_id': 'read_target'}}, session=s)); "
                              "s.commit_transaction()  # abort_transaction() if the find fails"),
                 fn=txn, expect=txn_expect[level],
                 read=reading_read_concern(f"{{level: '{level}'}} as the transaction readConcern", "transaction"))

    # ---------------------------------------------------------------- D. readPreference on find
    GD = "D readPreference on find"
    rp_expect = {
        "primary": ACCEPT,
        "secondary": REJECT("FailedToSatisfyReadPreference", "no server available for query with ReadPreference secondary"),
        "secondaryPreferred": ACCEPT,
        "nearest": ACCEPT,
        "primaryPreferred": ACCEPT,
    }
    rp_objs = {"primary": (Primary(), "Primary()"), "secondary": (Secondary(), "Secondary()"),
               "secondaryPreferred": (SecondaryPreferred(), "SecondaryPreferred()"),
               "nearest": (Nearest(), "Nearest()"), "primaryPreferred": (PrimaryPreferred(), "PrimaryPreferred()")}
    for mode in ("primary", "secondary", "secondaryPreferred", "nearest", "primaryPreferred"):
        obj, otext = rp_objs[mode]
        item = f"readPreference {mode}" if mode != "primaryPreferred" else "extra: readPreference primaryPreferred"
        pcoll = coll.with_options(read_preference=obj)
        run_step(f"D.driver.with_options.{mode}", group=GD, spec_item=item,
                 question=f"Does a find through collection.with_options(read_preference={otext}) succeed, and what goes on the wire?",
                 decisions_item=DEC_RP,
                 driver_call=f"list(client['{DB}']['{COLL}'].with_options(read_preference={otext}).find({{'_id': 'read_target'}}))",
                 fn=lambda pcoll=pcoll: list(pcoll.find({"_id": "read_target"})),
                 expect=rp_expect[mode], read=reading_read_pref(mode, "driver"))
    for mode in ("primary", "secondary", "secondaryPreferred", "nearest"):
        c_rp = MongoClient(URI, readPreference=mode, serverSelectionTimeoutMS=15000, socketTimeoutMS=60000,
                           event_listeners=[CAP])
        run_step(f"D.client_option.{mode}", group=GD, spec_item=f"readPreference {mode}",
                 question=f"Does a find on a client created with readPreference='{mode}' (URI/client option) behave the same?",
                 decisions_item=DEC_RP,
                 driver_call=f"list(MongoClient(LOCAL_URI, readPreference='{mode}')['{DB}']['{COLL}'].find({{'_id': 'read_target'}}))",
                 fn=lambda c_rp=c_rp: list(c_rp[DB][COLL].find({"_id": "read_target"})),
                 expect=rp_expect[mode], read=reading_read_pref(mode, "client"))
        c_rp.close()
    raw_rp = [
        ("primary", "readPreference primary", {"mode": "primary"}, rp_expect["primary"]),
        ("secondary", "readPreference secondary", {"mode": "secondary"}, rp_expect["secondary"]),
        ("secondaryPreferred", "readPreference secondaryPreferred", {"mode": "secondaryPreferred"}, ACCEPT),
        ("nearest", "readPreference nearest", {"mode": "nearest"}, ACCEPT),
        ("primaryPreferred", "extra: readPreference primaryPreferred", {"mode": "primaryPreferred"}, ACCEPT),
        ("extra_tags_secondaryPreferred", "extra: tag set", {"mode": "secondaryPreferred", "tags": [{"dc": "east"}]},
         REJECT("FailedToSatisfyReadPreference", "no server available for query with specified tag set list")),
        ("extra_hedge_nearest", "extra: hedge enabled", {"mode": "nearest", "hedge": {"enabled": True}},
         REJECT("BadValue", "hedged reads are not supported")),
        ("extra_maxStaleness90_secondaryPreferred", "extra: maxStalenessSeconds 90",
         {"mode": "secondaryPreferred", "maxStalenessSeconds": 90}, ACCEPT),
        ("extra_maxStaleness90_primary", "extra: primary with maxStalenessSeconds", {"mode": "primary", "maxStalenessSeconds": 90},
         REJECT("FailedToParse")),
        ("extra_unknown_mode", "extra: unknown mode", {"mode": "bogus"}, REJECT("FailedToParse", "Unsupported read preference mode")),
        ("extra_case_Nearest", "extra: mode case 'Nearest'", {"mode": "Nearest"}, ACCEPT),
        ("extra_case_SECONDARY", "extra: mode case 'SECONDARY'", {"mode": "SECONDARY"},
         REJECT("FailedToSatisfyReadPreference")),
    ]
    for label, item, rp, exp in raw_rp:
        run_step(f"D.raw.find.{label}", group=GD, spec_item=item,
                 question=f"Is a raw find command carrying $readPreference {jd(rp)} accepted?",
                 decisions_item=DEC_RP,
                 driver_call=(f"client['{DB}'].command(SON([('find', '{COLL}'), ('filter', {{'_id': 'read_target'}}), "
                              f"('$readPreference', {rp!r})]))"),
                 fn=lambda rp=rp: db.command(SON([("find", COLL), ("filter", {"_id": "read_target"}), ("$readPreference", rp)])),
                 expect=exp, read=reading_read_pref(f"a {rp['mode']} read", "raw"))
    drv_rp_extras = [
        ("extra_tag_sets", "extra: tag set", SecondaryPreferred(tag_sets=[{"dc": "east"}]),
         "SecondaryPreferred(tag_sets=[{'dc': 'east'}])",
         REJECT("FailedToSatisfyReadPreference", "no server available for query with specified tag set list")),
        ("extra_max_staleness90", "extra: maxStalenessSeconds 90", SecondaryPreferred(max_staleness=90),
         "SecondaryPreferred(max_staleness=90)", ACCEPT),
    ]
    for label, item, obj, otext, exp in drv_rp_extras:
        pcoll = coll.with_options(read_preference=obj)
        run_step(f"D.driver.with_options.{label}", group=GD, spec_item=item,
                 question=f"Does a find through with_options(read_preference={otext}) behave like the raw form?",
                 decisions_item=DEC_RP,
                 driver_call=f"list(client['{DB}']['{COLL}'].with_options(read_preference={otext}).find({{'_id': 'read_target'}}))",
                 fn=lambda pcoll=pcoll: list(pcoll.find({"_id": "read_target"})),
                 expect=exp, read=reading_read_pref("a secondaryPreferred read", "driver"))

    # ---------------------------------------------------------------- E. get/setDefaultRWConcern
    GE = "E getDefaultRWConcern / setDefaultRWConcern"
    gd_expect = {"outcome": "accepted", "source": SRC,
                 "response": {"defaultReadConcern": {"level": "majority"},
                              "defaultWriteConcern": {"w": "majority", "wtimeout": 0},
                              "defaultReadConcernSource": "implicit", "defaultWriteConcernSource": "implicit", "ok": 1}}

    def gd_read(rec):
        if rec["outcome"] != "ok":
            return "rejected", f"Rejected with {fmt_err(rec)}."
        r = dict(rec.get("response") or {})
        keys = ("defaultReadConcern", "defaultWriteConcern", "defaultReadConcernSource", "defaultWriteConcernSource")
        core = {k: r.get(k) for k in keys}
        same = all(r.get(k) == gd_expect["response"][k] for k in keys)
        extra = sorted(set(r) - set(keys) - {"ok"})
        return "accepted", (f"Returned {json.dumps(core)} (other fields: {extra or 'none'}), "
                                     f"{'identical to' if same else 'different from'} the constant document DECISIONS.md "
                                     f"reads from the main-branch constant.rs.")

    e1 = run_step("E.admin.getDefaultRWConcern", group=GE, spec_item="getDefaultRWConcern",
                  question="What does getDefaultRWConcern return on the admin database?", decisions_item=DEC_GD,
                  driver_call="client.admin.command('getDefaultRWConcern')",
                  fn=lambda: admin.command("getDefaultRWConcern"), expect=gd_expect, read=gd_read)
    run_step("E.admin.getDefaultRWConcern.inMemory", group=GE, spec_item="getDefaultRWConcern",
             question="Is the inMemory:true option accepted, and does it change the answer?", decisions_item=DEC_GD,
             driver_call="client.admin.command(SON([('getDefaultRWConcern', 1), ('inMemory', True)]))",
             fn=lambda: admin.command(SON([("getDefaultRWConcern", 1), ("inMemory", True)])), expect=gd_expect, read=gd_read)
    run_step("E.admin.getDefaultRWConcern.unknown_field", group=GE, spec_item="extra: getDefaultRWConcern unknown field",
             question="Is an unknown top-level field rejected?", decisions_item=DEC_GD,
             driver_call="client.admin.command(SON([('getDefaultRWConcern', 1), ('bogusField', 1)]))",
             fn=lambda: admin.command(SON([("getDefaultRWConcern", 1), ("bogusField", 1)])),
             expect=REJECT("UnknownBsonField", "Not a valid value for getDefaultRWConcern: bogusField"), read=gd_read)
    run_step("E.t_concern.getDefaultRWConcern", group=GE, spec_item="getDefaultRWConcern",
             question="Is getDefaultRWConcern refused on a non-admin database?", decisions_item=DEC_GD,
             driver_call=f"client['{DB}'].command('getDefaultRWConcern')",
             fn=lambda: db.command("getDefaultRWConcern"),
             expect=REJECT("Unauthorized", "Only the admin database can process getDefaultRWConcern."), read=gd_read)

    base = e1.get("response") if e1["outcome"] == "ok" else None
    dwc = dict((base or {}).get("defaultWriteConcern") or {"w": "majority", "wtimeout": 0})
    drc = dict((base or {}).get("defaultReadConcern") or {"level": "majority"})

    def sd_read(rec):
        if rec["outcome"] != "ok":
            return "rejected", f"Rejected with {fmt_err(rec)}, so setDefaultRWConcern is not available on this path."
        return "accepted_silently", (f"Accepted with reply {jd(rec.get('response'))}; whether the stored defaults "
                                     f"changed is checked in E.admin.getDefaultRWConcern.after_set.")

    sd_exp = {"outcome": "rejected", "source": "DECISIONS.md topic 9 (compatibility page: setDefaultRWConcern No); "
                                                 "the gateway's exact error is not recorded there"}
    run_step("E.admin.setDefaultRWConcern.defaultWriteConcern", group=GE, spec_item="setDefaultRWConcern",
             question="Is setDefaultRWConcern with defaultWriteConcern accepted (value = what getDefaultRWConcern reports)?",
             decisions_item=DEC_GD,
             driver_call=f"client.admin.command(SON([('setDefaultRWConcern', 1), ('defaultWriteConcern', {dwc!r})]))",
             fn=lambda: admin.command(SON([("setDefaultRWConcern", 1), ("defaultWriteConcern", dwc)])),
             expect=sd_exp, read=sd_read,
             notes="Value copied from the getDefaultRWConcern reply so an unexpected acceptance would not change any default.")
    run_step("E.admin.setDefaultRWConcern.defaultReadConcern", group=GE, spec_item="setDefaultRWConcern",
             question="Is setDefaultRWConcern with defaultReadConcern accepted (value = what getDefaultRWConcern reports)?",
             decisions_item=DEC_GD,
             driver_call=f"client.admin.command(SON([('setDefaultRWConcern', 1), ('defaultReadConcern', {drc!r})]))",
             fn=lambda: admin.command(SON([("setDefaultRWConcern", 1), ("defaultReadConcern", drc)])),
             expect=sd_exp, read=sd_read,
             notes="Value copied from the getDefaultRWConcern reply so an unexpected acceptance would not change any default.")
    run_step("E.admin.setDefaultRWConcern.no_fields", group=GE, spec_item="setDefaultRWConcern",
             question="Does the gateway parse setDefaultRWConcern at all (no defaults given), or refuse the command name?",
             decisions_item=DEC_GD, driver_call="client.admin.command('setDefaultRWConcern')",
             fn=lambda: admin.command("setDefaultRWConcern"), expect=sd_exp, read=sd_read)
    run_step("E.t_concern.setDefaultRWConcern", group=GE, spec_item="setDefaultRWConcern",
             question="What does setDefaultRWConcern return on a non-admin database?", decisions_item=DEC_GD,
             driver_call=f"client['{DB}'].command(SON([('setDefaultRWConcern', 1), ('defaultWriteConcern', {dwc!r})]))",
             fn=lambda: db.command(SON([("setDefaultRWConcern", 1), ("defaultWriteConcern", dwc)])),
             expect=sd_exp, read=sd_read)

    def after_read(rec):
        if rec["outcome"] != "ok":
            return "rejected", f"Rejected with {fmt_err(rec)}."
        r = rec.get("response") or {}
        keys = ("defaultReadConcern", "defaultWriteConcern", "defaultReadConcernSource", "defaultWriteConcernSource")
        same = base is not None and all(r.get(k) == base.get(k) for k in keys)
        return "accepted", (f"After the setDefaultRWConcern attempts getDefaultRWConcern returned "
                                     f"{json.dumps({k: r.get(k) for k in keys})}, "
                                     f"{'unchanged from' if same else 'DIFFERENT from'} the first call.")

    run_step("E.admin.getDefaultRWConcern.after_set", group=GE, spec_item="getDefaultRWConcern",
             question="Did any setDefaultRWConcern attempt change what getDefaultRWConcern reports?", decisions_item=DEC_GD,
             driver_call="client.admin.command('getDefaultRWConcern')",
             fn=lambda: admin.command("getDefaultRWConcern"), expect=gd_expect, read=after_read)

    # ---------------------------------------------------------------- Z. cleanup
    final_docs = list(coll.find({}).sort("_id", 1))
    GZ = "Z cleanup"

    def drop_read(rec):
        gone = (rec.get("observed_after") or {}).get("t_concern_listed_after_drop") is False
        if rec["outcome"] != "ok":
            return "cleanup_failed", f"dropDatabase failed with {fmt_err(rec)}."
        return ("cleanup_ok" if gone else "cleanup_incomplete"), (
            f"dropDatabase on {DB} returned {jd(wire_reply(rec))} and {DB} is "
            f"{'no longer' if gone else 'STILL'} listed by listDatabases.")

    run_step("Z.drop_database", group=GZ, spec_item="cleanup", question="Drop the test database t_concern.",
             decisions_item=None, driver_call=f"client.drop_database('{DB}')", fn=lambda: client.drop_database(DB),
             post=lambda rec, res: {"t_concern_listed_after_drop": DB in client.list_database_names()},
             read=drop_read)
    client.close()

    container_inspection()
    write_report(started_at, engine, final_docs, pre_exists)


# --------------------------------------------------------------------------- X. container inspection
GW_BIN = "/home/documentdb/gateway/pg_documentdb_gw/target/release-with-symbols/documentdb_gateway"
SECRET_KEY_RE = re.compile(r"pass|secret|key|cert|token|pwd|credential", re.I)
BINARY_STRINGS = [
    ("exceeds the number of data-bearing voting members", "write", "main-branch write_concern.rs BadValue text for w 2..50"),
    ("data-bearing", "write", "fragment of the same message"),
    ("w value", "write", "leading fragment of the same message"),
    ("writeConcern wtimeout must not exceed the maximum 32-bit integer", "write", "main-branch write_concern.rs FailedToParse text"),
    ("enable_write_concern_validation", "write", "main-branch dynamic.rs switch name"),
    ("writeConcern", "write", "any writeConcern literal at all"),
    ("' read concern is not supported", "read", "fragment of the main-branch validation.rs CommandNotSupported format string"),
    ("Invalid readConcern level", "read", "read_concern.rs BadValue text (observed on the wire)"),
    ("AllowTransactionSnapshot", "read", "snapshot switch name, PascalCase"),
    ("allow_transaction_snapshot", "read", "snapshot switch name, snake_case"),
    ("Read concern cannot be defined after transaction has started", "read", "validation.rs InvalidOptions text"),
    ("no server available for query with ReadPreference", "pref", "read_preference.rs text (observed on the wire)"),
    ("hedged reads are not supported", "pref", "read_preference.rs text (observed on the wire)"),
    ("Only the admin database can process getDefaultRWConcern", "pref", "constant.rs text (observed on the wire)"),
]


def redact_keys(o):
    if isinstance(o, dict):
        return {k: ("***" if SECRET_KEY_RE.search(k) else redact_keys(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [redact_keys(v) for v in o]
    return o


def container_inspection():
    GX = "X supplementary read-only container inspection (not the wire protocol)"
    run_shell_step("X.version_txt", group=GX, question="Which DocumentDB build does the container say it runs?",
                   decisions_item=None, cmd=["docker", "exec", CONTAINER, "cat", "/version.txt"],
                   read=lambda r: ("inspected", f"/version.txt reads {((r.get('response') or {}).get('output'))!r}."))
    run_shell_step("X.gateway_process", group=GX, question="Which gateway binary and setup file are serving port 10260?",
                   decisions_item=None,
                   cmd=["docker", "exec", CONTAINER, "sh", "-c", "ps -eo pid,args | grep '[d]ocumentdb_gateway '"],
                   read=lambda r: ("inspected", f"The serving gateway process is {((r.get('response') or {}).get('output'))!r}."))

    def dyn_parse(out):
        try:
            return redact_keys(json.loads(out))
        except ValueError:
            return {"unparsed_output_withheld": True}

    rec = run_shell_step("X.gateway_dynamic_configuration", group=GX,
                         question="Does the gateway's dynamic configuration file set any writeConcern or readConcern switch?",
                         decisions_item=DEC_W + "; " + DEC_RC,
                         cmd=["docker", "exec", CONTAINER, "sh", "-c", "cat /tmp/documentdb_host_config_*.json"],
                         parse=dyn_parse,
                         read=lambda r: ("inspected", f"The dynamic configuration file holds {json.dumps(r.get('parsed'))}, so "
                                                      f"no writeConcern, readConcern or snapshot switch is set there and the "
                                                      f"gateway runs on its compiled defaults for them."))
    if isinstance(rec.get("response"), dict):  # keep only the key-redacted form
        rec["response"]["output"] = json.dumps(rec.get("parsed"))

    t0 = time.perf_counter()
    rows = []
    for s, area, why in BINARY_STRINGS:
        row = {"string": s, "area": area, "why": why}
        for key, cmd in (("gateway_binary_count",
                          ["docker", "exec", CONTAINER, "sh", "-c", 'grep -a -o -F -e "$1" "$2" | wc -l', "sh", s, GW_BIN]),
                         ("extension_so_count",
                          ["docker", "exec", CONTAINER, "sh", "-c",
                           'cat /usr/lib/postgresql/17/lib/pg_documentdb*.so | grep -a -o -F -e "$1" | wc -l', "sh", s])):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                row[key] = int((r.stdout or "").strip()) if (r.stdout or "").strip().isdigit() else (r.stdout + r.stderr).strip()
            except Exception as e:  # noqa: BLE001
                row[key] = f"error: {e!r}"
        rows.append(row)
    write_rows = [r for r in rows if r["area"] == "write"]
    absent_w = [r["string"] for r in write_rows if r["gateway_binary_count"] == 0]
    rp_rows = [r for r in rows if r["area"] in ("read", "pref")]
    present_r = [r["string"] for r in rp_rows if isinstance(r["gateway_binary_count"], int) and r["gateway_binary_count"] > 0]
    w_word = "none" if len(absent_w) == len(write_rows) else f"only {len(write_rows) - len(absent_w)} of {len(write_rows)}"
    rec = {"id": "X.binary_strings", "group": GX, "spec_item": "supplementary: container inspection",
           "question": ("Does the 1.2.0 gateway binary contain the main-branch writeConcern and readConcern validation "
                        "messages that DECISIONS.md cites, i.e. is the difference a build difference?"),
           "decisions_item": DEC_W + "; " + DEC_RC,
           "driver_call": ("for each string S: docker exec ddb-engine-test sh -c 'grep -a -o -F -e \"$1\" \"$2\" | wc -l' sh S "
                           + GW_BIN + "; docker exec ddb-engine-test sh -c 'cat /usr/lib/postgresql/17/lib/pg_documentdb*.so "
                           "| grep -a -o -F -e \"$1\" | wc -l' sh S"),
           "wire": [], "outcome": "ok", "response": {"rows": rows},
           "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1), "verdict": "inspected"}
    rec["reading"] = (f"The serving gateway binary contains {w_word} of the {len(write_rows)} main-branch writeConcern "
                      f"validation literals checked (count 0: {'; '.join(absent_w) if absent_w else 'none'}) but contains "
                      f"{len(present_r)} of the {len(rp_rows)} readConcern, readPreference and getDefaultRWConcern literals"
                      + (", including the AllowTransactionSnapshot switch" if "AllowTransactionSnapshot" in present_r else "")
                      + (", so the missing w/wtimeout/unknown-field rejections look like a build difference while the "
                         "readConcern level check is compiled in but did not fire outside a transaction"
                         if w_word == "none" and "' read concern is not supported" in present_r else "")
                      + " (absence of a literal is strong, not conclusive, evidence because Rust format strings split "
                        "messages at placeholders).")
    STEPS.append(rec)
    print(f"[{rec['outcome']:>9}] {rec['id']}: {rec['verdict']} | {rec['reading']}", flush=True)


# --------------------------------------------------------------------------- report
def build_summary():
    by_item = {}
    for s in STEPS:
        item = s["spec_item"]
        if item in ("setup", "cleanup"):
            continue
        e = s.get("error") or {}
        by_item.setdefault(item, []).append({
            "step": s["id"], "verdict": s["verdict"], "code": e.get("code"), "codeName": e.get("codeName"),
            "errmsg": e.get("errmsg") if e else None, "matches_decisions": s.get("matches_decisions")})
    return by_item


CORE_ITEMS = ["w:1", "w:majority", "w:0", "w:2", "w:3", "j:true", "j:false", "wtimeoutMS:1",
              "readConcern local", "readConcern majority", "readConcern available", "readConcern linearizable",
              "readConcern snapshot", "readPreference primary", "readPreference secondary",
              "readPreference secondaryPreferred", "readPreference nearest", "getDefaultRWConcern", "setDefaultRWConcern"]


def build_headlines():
    """One generated line per spec item: verdicts across every path that exercised it."""
    out = []
    for item in CORE_ITEMS:
        steps = [s for s in STEPS if s["spec_item"] == item]
        if not steps:
            out.append(f"{item}: not exercised")
            continue
        verdicts = {}
        for s in steps:
            verdicts[s["verdict"]] = verdicts.get(s["verdict"], 0) + 1
        errs = sorted({f"{s['error'].get('code')} {s['error'].get('codeName')} \"{s['error'].get('errmsg')}\""
                       for s in steps if s.get("error") and s["error"].get("code") is not None})
        diff = sum(1 for s in steps if str(s.get("matches_decisions", "")).startswith("differs"))
        line = (f"{item}: " + ", ".join(f"{v} x{n}" for v, n in sorted(verdicts.items()))
                + (f"; errors {'; '.join(errs)}" if errs else "")
                + f"; steps {', '.join(s['id'] for s in steps)}"
                + (f"; {diff} of {len(steps)} differ from DECISIONS.md" if diff else "; consistent with DECISIONS.md"))
        out.append(line)
    return out


def write_report(started_at, engine, final_docs, pre_exists):
    mism = []
    for s in STEPS:
        if not str(s.get("matches_decisions", "")).startswith(("differs", "not comparable")):
            continue
        e = s.get("error") or {}
        mism.append({"step": s["id"], "matches_decisions": s["matches_decisions"],
                     "expected": s.get("decisions_expectation"),
                     "observed": {"outcome": s["outcome"], "verdict": s["verdict"], "code": e.get("code"),
                                  "codeName": e.get("codeName"), "errmsg": e.get("errmsg")}})
    tally = {}
    for s in STEPS:
        m = s.get("matches_decisions")
        if m is None:
            continue
        k = "differs" if str(m).startswith("differs") else m
        tally[k] = tally.get(k, 0) + 1
    report = {
        "test": "write-read-concerns",
        "database": DB,
        "status": "completed",
        "run_started_at": started_at,
        "run_finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "script": os.path.join(HERE, "run.py"),
        "rerun_command": f"/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I {os.path.join(HERE, 'run.py')}",
        "target": "documentdb-local container ddb-engine-test, mongodb wire protocol on localhost:10260, TLS with a self-signed certificate, SCRAM-SHA-256",
        "container": docker_provenance(),
        "engine": engine,
        "driver": {"pymongo": pymongo.version, "bson_c_extension": bson.has_c(), "python": sys.version.split()[0]},
        "evidence_scope": (
            "Every fact in this report was observed on documentdb-local, i.e. the open-source DocumentDB engine and gateway "
            "at the version this container reports (hello.internal.documentdb_versions " +
            json.dumps(engine.get("hello.internal.documentdb_versions")) + "; buildInfo.version " +
            json.dumps(engine.get("buildInfo.version")) + ", which is the MongoDB compatibility version the gateway "
            "advertises, not the engine version), running as a single node that the driver sees as a mongos. It is "
            "evidence about the open-source engine and gateway at that version only; it does not prove what the managed "
            "Azure DocumentDB service does (DECISIONS.md topic 9 open item 8), and single-node results cannot show "
            "replication, failover or HA durability effects."),
        "decisions_topic": ("findings/phase4/DECISIONS.md, 'Transactions, write semantics and bulk operations (SME topic 9)': "
                            "settled items on writeConcern w, j and wtimeout, readConcern levels, readPreference, "
                            "getDefaultRWConcern; open items 3 (snapshot readConcern) and 8 (Azure gateway parity). Those "
                            "settled items were read from the main-branch gateway source; this run checks them against "
                            "engine 1.2.0 behaviour."),
        "encoding_note": ("wire[].command is the command document pymongo published in CommandStartedEvent after adding "
                          "$db, lsid, $clusterTime and $readPreference (the same dict it encoded into OP_MSG); "
                          "wire[].reply / wire[].failure are the server documents from CommandSucceeded/CommandFailed. "
                          "For unacknowledged (w:0) writes pymongo publishes a synthetic {ok: 1} because no reply is read. "
                          "Values are MongoDB Extended JSON (relaxed)."),
        "t_concern_existed_before_run": pre_exists,
        "headlines_by_spec_item": build_headlines(),
        "summary_by_spec_item": build_summary(),
        "cross_references": [
            ("engine-tests-1.2/transactions-labels/report.run3.json step '2a readConcern snapshot inside a transaction' "
             "(same container) recorded code 115 CommandNotSupported \"'Snapshot' read concern is not supported\" for a "
             "transaction readConcern snapshot, consistent with C2.diag.transaction.snapshot here."),
            ("engine-tests/write-read-concerns and engine-tests/write-read-concerns-rerun (engine 0.117 attempts) never "
             "executed a step: authentication failed because the container's disk was full; this is the first executed run."),
        ],
        "decisions_comparison_tally": tally,
        "decisions_mismatches": mism,
        "final_documents_in_t_concern.c_before_drop": ej(final_docs),
        "steps": STEPS,
    }
    text = scrub(json.dumps(report, indent=2, default=lambda o: ej(o)))
    if _PW and len(_PW) >= 4:
        assert _PW not in text
    with open(REPORT, "w") as f:
        f.write(text)
    print(f"report written: {REPORT} ({len(STEPS)} steps, {len(mism)} DECISIONS mismatches)", flush=True)


if __name__ == "__main__":
    main()
