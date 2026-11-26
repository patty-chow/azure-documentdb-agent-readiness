"""m-schema: $jsonSchema validators and partial unique indexes on the managed Azure DocumentDB service.

Owns database mt_schema only. Reads MANAGED_URI from ../managed.env and never prints or stores the
password, the user name or a URI. Data-plane only: no cluster configuration is changed.

Writes report.json next to this script. For every step it records the exact PyMongo call, the raw
server response or error (code, codeName, errmsg, errorLabels, errInfo when present), a one-sentence
reading, and a comparison with the open-source engine run of the same step
(findings/phase4/engine-tests/jsonschema-and-partial-unique/report.json, documentdb-local 0.117).

Raw write commands (insert/update) are sent with db.command() so the full server reply, including
writeErrors[].errInfo and any top-level errorLabels, is visible; each document gets a client-side
ObjectId _id first, exactly as a driver's insert_one/insert_many would add it.
"""
import json
import os
import re
import sys
import time
import warnings
from collections import OrderedDict

warnings.filterwarnings("ignore", message=".*CosmosDB.*")  # PyMongo's CosmosDB notice; not part of this test

import pymongo  # noqa: E402
from pymongo import MongoClient, errors  # noqa: E402
from bson import json_util, ObjectId  # noqa: E402
from bson.json_util import RELAXED_JSON_OPTIONS  # noqa: E402
from bson.son import SON  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", "managed.env")
OSS_REPORT = ("/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/"
              "jsonschema-and-partial-unique/report.json")
DB = "mt_schema"
TEST_ID = "m-schema"


# ----------------------------------------------------------------------------- secrets and masking
def load_env():
    env = {}
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            if k.startswith("export "):
                k = k[7:].strip()
            env[k] = v.strip().strip('"').strip("'")
    return env


ENVV = load_env()
URI = ENVV["MANAGED_URI"]
SECRETS = [s for s in (ENVV.get("MANAGED_PASS"), URI, ENVV.get("MANAGED_GLOBAL_URI")) if s]
_m = re.match(r"mongodb(?:\+srv)?://([^:@/]+):", URI)
USER = _m.group(1) if _m else None
HOSTS = [h for h in (ENVV.get("MANAGED_GLOBAL_HOST"), ENVV.get("MANAGED_HOST")) if h]
GUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URIRE = re.compile(r"mongodb(?:\+srv)?://\S+")


def redact_str(s):
    if not isinstance(s, str):
        return s
    for sec in SECRETS:
        s = s.replace(sec, "<redacted>")
    s = URIRE.sub("<redacted-uri>", s)
    for h in HOSTS:
        s = s.replace(h, "<cluster-host>")
    if USER and len(USER) >= 6:
        s = re.sub(r"\b%s\b" % re.escape(USER), "<user>", s)
    s = EMAIL.sub("<email>", s)
    s = GUID.sub("<guid>", s)
    return s


def redact(obj):
    if isinstance(obj, str):
        return redact_str(obj)
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    if isinstance(obj, dict):
        return OrderedDict((redact_str(k), redact(v)) for k, v in obj.items())
    return obj


def J(x):
    """Relaxed Extended JSON, used for the command text."""
    return redact_str(json_util.dumps(x, json_options=RELAXED_JSON_OPTIONS))


def jsonable(x):
    return redact(json.loads(json_util.dumps(x, json_options=RELAXED_JSON_OPTIONS), object_pairs_hook=OrderedDict))


GOSSIP = ("$clusterTime", "operationTime")
GOSSIP_SEEN = set()


def strip_gossip(d):
    if isinstance(d, dict):
        for k in GOSSIP:
            if k in d:
                GOSSIP_SEEN.add(k)
        return OrderedDict((k, v) for k, v in d.items() if k not in GOSSIP)
    return d


# ----------------------------------------------------------------------------- open-source baseline
OSS = OrderedDict()
OSS_META = None
try:
    with open(OSS_REPORT) as _f:
        _r = json.load(_f)
    OSS_META = _r.get("engine_version")
    for _s in _r["steps"]:
        OSS[_s["step"].split(" ", 1)[0]] = _s
except Exception as _e:  # pragma: no cover
    print("WARNING: could not load open-source report:", type(_e).__name__)


def oss_outcome(s):
    resp = s["response"]
    if isinstance(resp, dict) and "error" in resp:
        e = resp["error"]
        rawd = {}
        if e.get("raw"):
            try:
                rawd = json.loads(e["raw"])
            except Exception:
                rawd = {}
        return OrderedDict(kind="error", code=e.get("code"), codeName=e.get("codeName") or rawd.get("codeName"),
                           errmsg=e.get("errmsg"), errInfo_present=("errInfo" in e) or ("errInfo" in rawd))
    return OrderedDict(kind="ok", result=resp.get("result", resp) if isinstance(resp, dict) else resp)


def describe(o):
    if o["kind"] == "ok":
        return "succeeded"
    msg = (o.get("errmsg") or "").strip()
    return "failed with %s %s '%s'%s" % (o.get("code"), o.get("codeName") or "(no codeName)", msg,
                                         ", errInfo present" if o.get("errInfo_present") else ", no errInfo")


def compare(sid, mine, value_cmp=None):
    s = OSS.get(sid)
    if s is None:
        return "not tested locally", None
    o = oss_outcome(s)
    mk = "ok" if mine["kind"] == "ok" else "error"
    if mk != o["kind"]:
        return "different", "open-source %s; managed %s" % (describe(o), describe(mine))
    if mk == "error":
        diffs = []
        if mine.get("code") != o.get("code"):
            diffs.append("code %s on open-source vs %s managed" % (o.get("code"), mine.get("code")))
        if (mine.get("codeName") or None) != (o.get("codeName") or None):
            diffs.append("codeName %s on open-source vs %s managed" % (o.get("codeName"), mine.get("codeName")))
        if (mine.get("errmsg") or "").strip() != (o.get("errmsg") or "").strip():
            diffs.append("errmsg '%s' on open-source vs '%s' managed" % ((o.get("errmsg") or "").strip(),
                                                                       (mine.get("errmsg") or "").strip()))
        if bool(mine.get("errInfo_present")) != bool(o.get("errInfo_present")):
            diffs.append("errInfo %s on open-source vs %s managed" % (
                "present" if o.get("errInfo_present") else "absent",
                "present" if mine.get("errInfo_present") else "absent"))
        return ("different", "; ".join(diffs)) if diffs else ("same", None)
    if value_cmp is not None:
        return value_cmp(o.get("result"), mine)
    return "same", None


# ----------------------------------------------------------------------------- execution helpers
client = MongoClient(URI, serverSelectionTimeoutMS=30000, connectTimeoutMS=20000, socketTimeoutMS=180000,
                     appname="m-schema-test")
db = client[DB]
steps = []


def _labels(e):
    try:
        return sorted(getattr(e, "_error_labels", set()) or [])
    except Exception:
        return []


def run_command(cmd, target_db=None):
    """db.command(cmd) -> (response, outcome, python_result_or_None)."""
    tdb = db if target_db is None else target_db
    t0 = time.perf_counter()
    try:
        r = tdb.command(cmd)
        ms = round((time.perf_counter() - t0) * 1000)
        raw = strip_gossip(jsonable(r))
        wes = raw.get("writeErrors") or []
        if wes:
            we = wes[0]
            out = OrderedDict(kind="write_error", code=we.get("code"), codeName=we.get("codeName"),
                              errmsg=we.get("errmsg"), errInfo_present="errInfo" in we,
                              errorLabels=raw.get("errorLabels", []), n=raw.get("n"), nWriteErrors=len(wes))
        else:
            out = OrderedDict(kind="ok")
            for k in ("n", "nModified"):
                if k in raw:
                    out[k] = raw[k]
        if "writeConcernError" in raw:
            out["writeConcernError"] = raw["writeConcernError"]
        return OrderedDict(raw_response=raw, ms=ms), out, r
    except errors.OperationFailure as e:
        ms = round((time.perf_counter() - t0) * 1000)
        d = e.details or {}
        out = OrderedDict(kind="error", exception=type(e).__name__, code=e.code, codeName=d.get("codeName"),
                          errmsg=redact_str(d.get("errmsg") if d.get("errmsg") is not None else str(e)),
                          errInfo_present="errInfo" in d,
                          errorLabels=list(d.get("errorLabels") or _labels(e)))
        err = OrderedDict((k, out[k]) for k in ("exception", "code", "codeName", "errmsg", "errorLabels"))
        if "errInfo" in d:
            err["errInfo"] = jsonable(d["errInfo"])
        err["raw"] = strip_gossip(jsonable(d)) if d else None
        return OrderedDict(error=err, ms=ms), out, None
    except Exception as e:
        ms = round((time.perf_counter() - t0) * 1000)
        out = OrderedDict(kind="error", exception=type(e).__name__, code=getattr(e, "code", None), codeName=None,
                          errmsg=redact_str(str(e)), errInfo_present=False, errorLabels=_labels(e))
        return OrderedDict(error=OrderedDict((k, out[k]) for k in ("exception", "code", "errmsg", "errorLabels")),
                           ms=ms), out, None


def run_call(fn):
    """A high-level driver call -> (response, outcome, python_result_or_None)."""
    t0 = time.perf_counter()
    try:
        r = fn()
        ms = round((time.perf_counter() - t0) * 1000)
        return OrderedDict(result=jsonable(r), ms=ms), OrderedDict(kind="ok"), r
    except errors.PyMongoError as e:
        ms = round((time.perf_counter() - t0) * 1000)
        d = getattr(e, "details", None) or {}
        out = OrderedDict(kind="write_error" if isinstance(e, errors.WriteError) else "error",
                          exception=type(e).__name__, code=getattr(e, "code", None), codeName=d.get("codeName"),
                          errmsg=redact_str(d.get("errmsg") if d.get("errmsg") is not None else str(e)),
                          errInfo_present="errInfo" in d, errorLabels=_labels(e))
        err = OrderedDict((k, out[k]) for k in ("exception", "code", "codeName", "errmsg", "errorLabels"))
        err["details"] = jsonable(d) if d else None
        return OrderedDict(error=err, ms=ms), out, None


def with_ids(docs):
    """Give each document a client-side ObjectId _id first, as insert_one/insert_many do."""
    out = []
    for d in docs:
        s = SON([("_id", ObjectId())])
        for k, v in d.items():
            s[k] = v
        out.append(s)
    return out


def err_phrase(o):
    msg = (o.get("errmsg") or "").strip()
    s = "%s %s '%s'" % (o.get("code"), o.get("codeName") or "(no codeName)", msg)
    if o["kind"] == "write_error":
        s += ", errInfo %s" % ("present" if o.get("errInfo_present") else "absent")
    if o.get("errorLabels"):
        s += ", errorLabels %s" % o["errorLabels"]
    return s


def add(sid, title, command, response, outcome, reading, oss_id=None, value_cmp=None, vs=None, note=None):
    if vs is None:
        vs, note = compare(oss_id or sid, outcome, value_cmp)
    if vs == "same":
        clause = "open-source 0.117 behaved the same"
    elif vs == "different":
        clause = "open-source 0.117 differed (%s)" % note
    elif vs == "n/a":
        clause = "no open-source comparison applies"
    else:
        clause = "not tested on open-source"
    entry = OrderedDict()
    entry["step"] = "%s %s" % (sid, title)
    entry["command"] = command
    entry["response"] = response
    entry["outcome"] = outcome
    entry["reading"] = "%s; %s." % (reading.rstrip(". "), clause)
    entry["vs_open_source"] = vs
    if note:
        entry["vs_open_source_note"] = note
    if (oss_id or sid) in OSS and vs != "n/a":
        entry["open_source_step"] = OSS[oss_id or sid]["step"]
    steps.append(entry)
    print("[%03d] %s %s\n      -> %s\n      %s" % (len(steps), sid, title, json.dumps(outcome)[:300], entry["reading"][:400]))
    sys.stdout.flush()
    return entry


def cmd_text(cmd, target="db"):
    """The command document as passed to Database.command. PyMongo adds lsid and $db to a SON it sends,
    in place; those are driver-added and are left out so the text is the call as written."""
    if isinstance(cmd, dict):
        cmd = SON([(k, v) for k, v in cmd.items() if k not in ("lsid", "$db")])
    return "%s.command(%s)" % (target, J(cmd))


def do(sid, title, cmd, reading_fn, oss_id=None, value_cmp=None, vs=None, note=None, target_db=None, target="db"):
    resp, out, r = run_command(cmd, target_db)
    reading = reading_fn(out, resp)
    add(sid, title, cmd_text(cmd, target), resp, out, reading, oss_id=oss_id, value_cmp=value_cmp, vs=vs, note=note)
    return out, resp, r


def insert_cmd(coll, docs, **opts):
    c = SON([("insert", coll), ("documents", with_ids(docs)), ("ordered", True)])
    for k, v in opts.items():
        c[k] = v
    return c


def rd_insert_expect_ok(what):
    def f(o, resp):
        if o["kind"] == "ok":
            return "%s accepted (n=%s)" % (what, o.get("n"))
        return "%s rejected: %s" % (what, err_phrase(o))
    return f


def rd_insert_violating(what):
    def f(o, resp):
        if o["kind"] == "ok":
            return "%s was ACCEPTED (n=%s), so the rule is not enforced" % (what, o.get("n"))
        return "%s rejected with %s" % (what, err_phrase(o))
    return f


def ok_count_cmp(expected_n):
    def f(oss_result, mine):
        on = oss_result.get("inserted") if isinstance(oss_result, dict) else None
        mn = mine.get("n")
        if on == mn:
            return "same", None
        return "different", "open-source inserted %s vs managed n=%s (expected %s)" % (on, mn, expected_n)
    return f


# ============================================================================= metadata
t_start = time.time()
hello = client.admin.command("hello")
hello_sel = OrderedDict((k, jsonable(hello.get(k))) for k in
                        ("maxWireVersion", "minWireVersion", "maxWriteBatchSize", "maxBsonObjectSize", "msg", "internal")
                        if k in hello)
oss_hello = OSS.get("hello", {}).get("response", {})
add("M1", "hello (selected fields)", "client.admin.command('hello')", OrderedDict(raw_response_selected=hello_sel),
    OrderedDict(kind="ok"),
    "Managed gateway reports maxWireVersion %s, maxWriteBatchSize %s and internal %s" % (
        hello_sel.get("maxWireVersion"), hello_sel.get("maxWriteBatchSize"), json.dumps(hello_sel.get("internal"))),
    vs="different", note="open-source reported maxWireVersion %s" % oss_hello.get("maxWireVersion"))
bi = client.admin.command("buildInfo")
bi_sel = strip_gossip(jsonable(bi))
oss_bi = OSS.get("buildInfo", {}).get("response", {})
add("M2", "buildInfo", "client.admin.command('buildInfo')", OrderedDict(raw_response=bi_sel), OrderedDict(kind="ok"),
    "buildInfo.version is %s (MongoDB compatibility version, not the engine release)" % bi_sel.get("version"),
    vs="different", note="open-source buildInfo.version was %s" % oss_bi.get("version"))

# ============================================================================= setup
do("S0", "drop test database mt_schema (setup, repeatable run)", SON([("dropDatabase", 1)]),
   lambda o, r: "Test database dropped before the run" if o["kind"] == "ok" else "dropDatabase failed: %s" % err_phrase(o),
   vs="n/a", target="client['mt_schema']")

# ============================================================================= Part A: validators
BASELINE = {"$jsonSchema": {"bsonType": "object", "required": ["name"], "properties": {"name": {"bsonType": "string"}}}}

o_base, _, _ = do("A0", "create collection with baseline validator (bsonType/required/properties)",
                  SON([("create", "v_baseline"), ("validator", BASELINE)]),
                  lambda o, r: ("create accepted a baseline $jsonSchema validator, so collection validators are enabled on this cluster"
                                if o["kind"] == "ok" else
                                "create rejected even a baseline validator with %s, so collection validators are gated on this cluster" % err_phrase(o)))


def opts_cmp(mine_opts):
    def f(oss_result, mine):
        if json.dumps(oss_result, sort_keys=True) == json.dumps(mine_opts, sort_keys=True):
            return "same", None
        return "different", "open-source options %s vs managed %s" % (json.dumps(oss_result), json.dumps(mine_opts))
    return f


# listCollections options (run regardless; shows whether anything was stored)
_lc_cmd = SON([("listCollections", 1), ("filter", {"name": "v_baseline"})])
_resp, _out, _r = run_command(_lc_cmd)
_opts = None
if _r is not None:
    fb = _r.get("cursor", {}).get("firstBatch", [])
    _opts = jsonable(fb[0].get("options", {})) if fb else None
add("A0b", "listCollections options for v_baseline", cmd_text(_lc_cmd), _resp, _out,
    ("Stored options are %s" % json.dumps(_opts)) if _out["kind"] == "ok" and _opts is not None else
    ("v_baseline does not exist" if _out["kind"] == "ok" else "listCollections failed: %s" % err_phrase(_out)),
    value_cmp=opts_cmp(_opts))

if o_base["kind"] == "ok":  # inserts/updates only make sense when the validator exists
    do("A0c", "insert violating doc into v_baseline (missing required name), raw insert command",
       insert_cmd("v_baseline", [{"x": 1}]), rd_insert_violating("Insert of {x:1} missing required 'name'"))

    _resp, _out, _ = run_call(lambda: db["v_baseline"].insert_one({"x": 1}))
    add("A0c.driver", "insert_one violating doc (driver exception shape)", "db['v_baseline'].insert_one({'x': 1})", _resp, _out,
        ("insert_one of a violating doc was ACCEPTED" if _out["kind"] == "ok" else
         "PyMongo raised %s with code %s, codeName %s, errInfo %s" % (_out.get("exception"), _out.get("code"), _out.get("codeName"),
                                                                     "present" if _out.get("errInfo_present") else "absent")),
        oss_id="A0c")

    do("A0c.type", "insert violating doc into v_baseline (name has wrong type)",
       insert_cmd("v_baseline", [{"name": 5}]), rd_insert_violating("Insert of {name:5} (int, not string)"))
    do("A0c.valid", "insert two valid docs into v_baseline",
       insert_cmd("v_baseline", [{"name": "ok"}, {"name": "fam"}]), rd_insert_expect_ok("Two valid documents"))
    do("A0d", "insert violating doc with bypassDocumentValidation: true",
       insert_cmd("v_baseline", [{"x": 1}], bypassDocumentValidation=True),
       lambda o, r: ("bypassDocumentValidation let the violating document through (n=%s)" % o.get("n")) if o["kind"] == "ok"
       else "bypassDocumentValidation did not help: %s" % err_phrase(o))
    do("A0u", "update a valid doc so it violates the validator ($set name: 5)",
       SON([("update", "v_baseline"), ("updates", [SON([("q", {"name": "ok"}), ("u", {"$set": {"name": 5}}),
                                                         ("multi", False), ("upsert", False)])]), ("ordered", True)]),
       lambda o, r: ("Violating update was ACCEPTED (n=%s, nModified=%s)" % (o.get("n"), o.get("nModified")))
       if o["kind"] == "ok" else "Violating update rejected with %s" % err_phrase(o))
    do("A0fam", "findAndModify a valid doc so it violates the validator ($unset name)",
       SON([("findAndModify", "v_baseline"), ("query", {"name": "fam"}), ("update", {"$unset": {"name": ""}}), ("new", True)]),
       lambda o, r: "Violating findAndModify was ACCEPTED" if o["kind"] == "ok"
       else "Violating findAndModify rejected with %s" % err_phrase(o))
else:
    print("A0 failed: skipping v_baseline write checks (the collection has no validator)")

_pre = run_command(SON([("create", "cm_baseline")]))
_resp, _out, _ = run_command(SON([("collMod", "cm_baseline"), ("validator", BASELINE)]))
_resp["precondition"] = OrderedDict(command=cmd_text(SON([("create", "cm_baseline")])), response=_pre[0])
add("A0cm", "collMod baseline validator onto a plain collection cm_baseline",
    "%s; then %s" % (cmd_text(SON([("create", "cm_baseline")])), cmd_text(SON([("collMod", "cm_baseline"), ("validator", BASELINE)]))),
    _resp, _out,
    "collMod accepted a baseline validator" if _out["kind"] == "ok" else "collMod rejected a baseline validator with %s" % err_phrase(_out))
if _out["kind"] == "ok":
    do("A0cm.insert", "insert violating doc into cm_baseline after collMod",
       insert_cmd("cm_baseline", [{"x": 1}]), rd_insert_violating("Insert of {x:1} after collMod"))

do("A0warn", "create collection with baseline validator and validationAction 'warn'",
   SON([("create", "v_warn"), ("validator", BASELINE), ("validationAction", "warn")]),
   lambda o, r: "create accepted validationAction 'warn'" if o["kind"] == "ok"
   else "create rejected validationAction 'warn' with %s" % err_phrase(o))
if steps[-1]["outcome"]["kind"] == "ok":
    do("A0warn.insert", "insert violating doc into v_warn",
       insert_cmd("v_warn", [{"x": 1}]),
       lambda o, r: ("Violating insert accepted under validationAction 'warn' (n=%s), as in MongoDB" % o.get("n"))
       if o["kind"] == "ok" else "Violating insert rejected despite validationAction 'warn': %s" % err_phrase(o))

KEYWORDS = OrderedDict([
    ("enum", {"$jsonSchema": {"bsonType": "object", "properties": {"status": {"enum": ["new", "done"]}}}}),
    ("additionalProperties", {"$jsonSchema": {"bsonType": "object", "properties": {"a": {"bsonType": "int"}},
                                              "additionalProperties": False}}),
    ("additionalProperties_with_id", {"$jsonSchema": {"bsonType": "object",
                                                      "properties": {"_id": {"bsonType": "objectId"}, "a": {"bsonType": "int"}},
                                                      "additionalProperties": False}}),
    ("allOf", {"$jsonSchema": {"allOf": [{"required": ["a"]}, {"required": ["b"]}]}}),
    ("anyOf", {"$jsonSchema": {"anyOf": [{"required": ["a"]}, {"required": ["b"]}]}}),
    ("oneOf", {"$jsonSchema": {"oneOf": [{"required": ["a"]}, {"required": ["b"]}]}}),
    ("not", {"$jsonSchema": {"not": {"required": ["forbidden"]}}}),
    ("patternProperties", {"$jsonSchema": {"patternProperties": {"^x_": {"bsonType": "int"}}}}),
    ("dependencies", {"$jsonSchema": {"dependencies": {"a": ["b"]}}}),
    ("minProperties", {"$jsonSchema": {"minProperties": 2}}),
    ("maxProperties", {"$jsonSchema": {"maxProperties": 2}}),
])
# (valid, violating) under MongoDB semantics, counting the _id every inserted document carries.
DOCS = OrderedDict([
    ("enum", ({"status": "new"}, {"status": "bogus"})),
    ("additionalProperties", ({"a": 1}, {"a": 1, "extra": 1})),          # MongoDB: _id not declared, so even {a:1} fails
    ("additionalProperties_with_id", ({"a": 1}, {"a": 1, "extra": 1})),
    ("allOf", ({"a": 1, "b": 1}, {"a": 1})),
    ("anyOf", ({"a": 1}, {"c": 1})),
    ("oneOf", ({"a": 1}, {"a": 1, "b": 1})),
    ("not", ({"ok": 1}, {"forbidden": 1})),
    ("patternProperties", ({"x_1": 1}, {"x_1": "str"})),
    ("dependencies", ({"a": 1, "b": 1}, {"a": 1})),
    ("minProperties", ({"a": 1}, {})),                                  # 2 vs 1 properties with _id
    ("maxProperties", ({"a": 1}, {"a": 1, "b": 1})),                    # 2 vs 3 properties with _id
])
# Expected documents matched by {$jsonSchema: ...} under MongoDB semantics (index into (valid, violating)).
EXPECT_MATCH = {kw: [0] for kw in DOCS}
EXPECT_MATCH["additionalProperties"] = []  # _id is not in properties, so MongoDB matches neither document
BASE_DOCS = ({"name": "ok"}, {"x": 1})

def rd_create_kw(kw):
    return lambda o, r: (("create accepted a validator using '%s'" % kw) if o["kind"] == "ok"
                         else "create rejected '%s' with %s" % (kw, err_phrase(o)))


def rd_valid_doc(doc, note, after=""):
    return lambda o, r: (("Document %s accepted%s (n=%s)" % (J(doc), after, o.get("n"))) if o["kind"] == "ok"
                         else "Document %s rejected%s with %s%s" % (J(doc), after, err_phrase(o), note))


def rd_violating_doc(doc, kw, after=""):
    return lambda o, r: (("Violating document %s was ACCEPTED%s (n=%s), so '%s' is not enforced" % (J(doc), after, o.get("n"), kw))
                         if o["kind"] == "ok" else
                         "Violating document %s rejected%s with %s, so '%s' is enforced" % (J(doc), after, err_phrase(o), kw))


for kw, validator in KEYWORDS.items():
    valid, bad = DOCS[kw]
    vname = "v_%s" % kw
    valid_note = (" (MongoDB rejects it too, because _id is not declared in properties)"
                  if kw == "additionalProperties" else "")
    o1, _, _ = do("A1.%s" % kw, "create collection with $jsonSchema using %s" % kw,
                  SON([("create", vname), ("validator", validator)]), rd_create_kw(kw))
    if o1["kind"] == "ok":
        do("A2.%s" % kw, "insert valid doc into %s" % vname, insert_cmd(vname, [valid]), rd_valid_doc(valid, valid_note))
        do("A3.%s" % kw, "insert violating doc into %s" % vname, insert_cmd(vname, [bad]), rd_violating_doc(bad, kw))
    # collMod path, independent of the create result
    cm = "cm_%s" % kw
    pre_cmd = SON([("create", cm)])
    pre = run_command(pre_cmd)
    cm_cmd = SON([("collMod", cm), ("validator", validator)])
    resp, out, _ = run_command(cm_cmd)
    resp["precondition"] = OrderedDict(command=cmd_text(pre_cmd), response=pre[0])
    add("A4.%s" % kw, "collMod validator using %s onto plain collection %s" % (kw, cm),
        "%s; then %s" % (cmd_text(pre_cmd), cmd_text(cm_cmd)), resp, out,
        ("collMod accepted a validator using '%s'" % kw) if out["kind"] == "ok" else "collMod rejected '%s' with %s" % (kw, err_phrase(out)))
    if out["kind"] == "ok":
        do("A5.%s" % kw, "insert valid doc into %s after collMod" % cm, insert_cmd(cm, [valid]),
           rd_valid_doc(valid, valid_note, " after collMod"))
        do("A6.%s" % kw, "insert violating doc into %s after collMod" % cm, insert_cmd(cm, [bad]),
           rd_violating_doc(bad, kw, " after collMod"))

# ----------------------------------------------------------------------------- extra keywords (beyond the spec list)
# Learn lists title/description as unsupported; generated schemas often carry $schema, format and type 'integer'.
EXTRAS = OrderedDict([
    ("title_description", ("title + description", {"$jsonSchema": {"bsonType": "object", "title": "Person", "description": "a person",
                                                                   "required": ["name"],
                                                                   "properties": {"name": {"bsonType": "string",
                                                                                           "description": "the name"}}}},
                           ({"name": "ok"}, {"x": 1}))),
    ("dollar_schema", ("$schema", {"$jsonSchema": {"$schema": "http://json-schema.org/draft-04/schema#", "bsonType": "object"}}, None)),
    ("format", ("format", {"$jsonSchema": {"bsonType": "object", "properties": {"email": {"bsonType": "string", "format": "email"}}}}, None)),
    ("type_integer", ("type: 'integer'", {"$jsonSchema": {"bsonType": "object", "properties": {"n": {"type": "integer"}}}}, None)),
])
for key, (label, validator, docs) in EXTRAS.items():
    vname = "x_%s" % key
    o7, _, _ = do("A7.%s" % key, "extra: create collection with $jsonSchema using %s" % label,
                  SON([("create", vname), ("validator", validator)]), rd_create_kw(label))
    if o7["kind"] == "ok" and docs:
        do("A7.%s.valid" % key, "extra: insert valid doc into %s" % vname, insert_cmd(vname, [docs[0]]), rd_valid_doc(docs[0], ""))
        do("A7.%s.violating" % key, "extra: insert violating doc into %s" % vname, insert_cmd(vname, [docs[1]]),
           rd_violating_doc(docs[1], "required (with %s present)" % label))

# ============================================================================= Part C: $jsonSchema as a query operator
# Not a validator, so it shows which keywords the engine's $jsonSchema parser accepts even if validators were gated.
QUERY_CASES = OrderedDict([("baseline", (BASELINE, BASE_DOCS))] + [(kw, (KEYWORDS[kw], DOCS[kw])) for kw in KEYWORDS])
EXPECT_MATCH["baseline"] = [0]
for kw, (validator, (valid, bad)) in QUERY_CASES.items():
    qc = "q_%s" % kw
    ins = insert_cmd(qc, [valid, bad])
    ins_resp, ins_out, _ = run_command(ins)
    ids = [d["_id"] for d in ins["documents"]]
    fcmd = SON([("find", qc), ("filter", {"$jsonSchema": validator["$jsonSchema"]}), ("projection", {"_id": 1})])
    resp, out, r = run_command(fcmd)
    resp["precondition"] = OrderedDict(command=cmd_text(ins), response=ins_resp)
    if out["kind"] == "ok" and r is not None:
        got = [d["_id"] for d in r.get("cursor", {}).get("firstBatch", [])]
        matched = [i for i, _id in enumerate(ids) if _id in got]
        out["matched"] = ["valid" if i == 0 else "violating" for i in matched]
        exp = EXPECT_MATCH[kw]
        out["expected_mongodb"] = ["valid" if i == 0 else "violating" for i in exp]
        verdict = "as MongoDB would" if matched == exp else "NOT as MongoDB would (expected %s)" % out["expected_mongodb"]
        reading = "find with {$jsonSchema} using '%s' was accepted and matched %s of the documents %s / %s, %s" % (
            kw, out["matched"] or "none", J(valid), J(bad), verdict)
    else:
        reading = "find with {$jsonSchema} using '%s' was rejected with %s" % (kw, err_phrase(out))
    add("C.%s" % kw, "find with $jsonSchema query operator using %s (no validator)" % kw,
        "%s; then %s" % (cmd_text(ins), cmd_text(fcmd)), resp, out, reading)

# ============================================================================= Part B: partial unique indexes
def ci_cmd(coll, spec):
    return SON([("createIndexes", coll), ("indexes", [spec])])


def nidx(r):
    """numIndexesAfter wherever the gateway puts it (top level or raw.<shard>)."""
    if not isinstance(r, dict):
        return None
    if "numIndexesAfter" in r:
        return r["numIndexesAfter"]
    for v in (r.get("raw") or {}).values():
        if isinstance(v, dict) and "numIndexesAfter" in v:
            return v["numIndexesAfter"]
    return None


def ci_cmp(mine_resp):
    mine_n = nidx(mine_resp.get("raw_response", {}))
    mine_shape = "raw.<shard>" if "raw" in mine_resp.get("raw_response", {}) else "top level"

    def f(oss_result, mine):
        on = nidx(oss_result)
        if on == mine_n:
            note = None
            if mine_shape != "raw.<shard>":
                note = "same numIndexesAfter; result shape differs: open-source nested it under raw.defaultShard, managed at %s" % mine_shape
                return "same", note
            return "same", None
        return "different", "numIndexesAfter %s on open-source vs %s managed" % (on, mine_n)
    return f


def rd_ci(o, resp):
    if o["kind"] == "ok":
        rr = resp.get("raw_response", {})
        return "createIndexes accepted (numIndexesAfter=%s, result %s)" % (
            nidx(rr), "nested under raw" if "raw" in rr else "at top level")
    return "createIndexes rejected with %s" % err_phrase(o)


def list_indexes_step(sid, coll):
    cmd = SON([("listIndexes", coll)])
    resp, out, r = run_command(cmd)
    specs = jsonable(r.get("cursor", {}).get("firstBatch", [])) if r is not None else None

    def cmp(oss_result, mine):
        if json.dumps(oss_result, sort_keys=True) == json.dumps(specs, sort_keys=True):
            return "same", None
        return "different", "open-source specs %s vs managed %s" % (json.dumps(oss_result), json.dumps(specs))
    add(sid, "listIndexes on %s" % coll, cmd_text(cmd), resp, out,
        ("Index specs as stored: %s" % json.dumps(specs)) if out["kind"] == "ok" else "listIndexes failed: %s" % err_phrase(out),
        value_cmp=cmp)


def count_step(sid, coll):
    resp, out, r = run_call(lambda: db[coll].count_documents({}))

    def cmp(oss_result, mine):
        on = oss_result.get("count") if isinstance(oss_result, dict) else None
        return ("same", None) if on == r else ("different", "open-source count %s vs managed %s" % (on, r))
    add(sid, "count documents in %s" % coll, "db['%s'].count_documents({})" % coll, resp, out,
        ("%s documents stored" % r) if out["kind"] == "ok" else "count failed: %s" % err_phrase(out), value_cmp=cmp)


# B1: unique + partialFilterExpression { key: { $exists: true } }
c1 = "pu_exists"
pre_cmd = SON([("create", c1)])
pre = run_command(pre_cmd)
spec1 = SON([("key", {"key": 1}), ("name", "uq_key_exists"), ("unique", True),
             ("partialFilterExpression", {"key": {"$exists": True}})])
resp, out, _ = run_command(ci_cmd(c1, spec1))
resp["precondition"] = OrderedDict(command=cmd_text(pre_cmd), response=pre[0])
add("B1", "createIndexes unique + partialFilterExpression {key:{$exists:true}}",
    "%s; then %s" % (cmd_text(pre_cmd), cmd_text(ci_cmd(c1, spec1))), resp, out, rd_ci(out, resp), value_cmp=ci_cmp(resp))
if out["kind"] == "ok":
    list_indexes_step("B1a", c1)
    do("B1b", "insert {key:1}", insert_cmd(c1, [{"key": 1}]), rd_insert_expect_ok("First keyed document {key:1}"))
    do("B1c", "insert duplicate {key:1}", insert_cmd(c1, [{"key": 1}]),
       lambda o, r: "DUPLICATE ACCEPTED (n=%s): uniqueness not enforced" % o.get("n") if o["kind"] == "ok"
       else "Duplicate {key:1} rejected with %s" % err_phrase(o))
    do("B1d", "insert doc without key {other:1}", insert_cmd(c1, [{"other": 1}]),
       rd_insert_expect_ok("Document without the key {other:1}"))
    do("B1e", "insert second doc without key {other:2}", insert_cmd(c1, [{"other": 2}]),
       lambda o, r: ("Second keyless document accepted (n=%s): missing keys are outside the filter, not duplicate nulls" % o.get("n"))
       if o["kind"] == "ok" else "Second keyless document rejected with %s: missing key treated as a duplicate null" % err_phrase(o))
    do("B1f", "insert {key:null}", insert_cmd(c1, [{"key": None}]), rd_insert_expect_ok("First explicit {key:null}"))
    do("B1g", "insert second {key:null}", insert_cmd(c1, [{"key": None}]),
       lambda o, r: ("Second explicit null ACCEPTED (n=%s): null is outside the $exists:true filter here, unlike MongoDB" % o.get("n"))
       if o["kind"] == "ok" else "Second {key:null} rejected with %s, so null is inside the $exists:true filter as in MongoDB" % err_phrase(o))
    count_step("B1h", c1)

# B2: unique + partialFilterExpression { key: { $gt: 0 } }
c2 = "pu_gt"
pre_cmd = SON([("create", c2)])
pre = run_command(pre_cmd)
spec2 = SON([("key", {"key": 1}), ("name", "uq_key_gt0"), ("unique", True), ("partialFilterExpression", {"key": {"$gt": 0}})])
resp, out, _ = run_command(ci_cmd(c2, spec2))
resp["precondition"] = OrderedDict(command=cmd_text(pre_cmd), response=pre[0])
add("B2", "createIndexes unique + partialFilterExpression {key:{$gt:0}}",
    "%s; then %s" % (cmd_text(pre_cmd), cmd_text(ci_cmd(c2, spec2))), resp, out, rd_ci(out, resp), value_cmp=ci_cmp(resp))
if out["kind"] == "ok":
    list_indexes_step("B2a", c2)
    do("B2b", "insert {key:5}", insert_cmd(c2, [{"key": 5}]), rd_insert_expect_ok("First positive key {key:5}"))
    do("B2c", "insert duplicate {key:5}", insert_cmd(c2, [{"key": 5}]),
       lambda o, r: "DUPLICATE ACCEPTED (n=%s) inside the filter" % o.get("n") if o["kind"] == "ok"
       else "Duplicate {key:5} rejected with %s" % err_phrase(o))
    do("B2d", "insert {key:0}", insert_cmd(c2, [{"key": 0}]), rd_insert_expect_ok("{key:0} (outside the filter)"))
    do("B2e", "insert duplicate {key:0}", insert_cmd(c2, [{"key": 0}]),
       lambda o, r: ("Duplicate {key:0} accepted (n=%s): documents outside $gt:0 are not uniqueness-checked" % o.get("n"))
       if o["kind"] == "ok" else "Duplicate {key:0} rejected with %s, so the filter was not honoured" % err_phrase(o))
    do("B2f", "insert {key:-1} twice in one batch", insert_cmd(c2, [{"key": -1}, {"key": -1}]),
       lambda o, r: ("Two {key:-1} documents accepted (n=%s): negatives are outside the filter" % o.get("n"))
       if o["kind"] == "ok" else "Negative duplicates rejected with %s" % err_phrase(o), value_cmp=ok_count_cmp(2))
    do("B2g", "insert two docs without key in one batch", insert_cmd(c2, [{"other": 1}, {"other": 2}]),
       lambda o, r: ("Two keyless documents accepted (n=%s)" % o.get("n"))
       if o["kind"] == "ok" else "Keyless documents rejected with %s" % err_phrase(o), value_cmp=ok_count_cmp(2))
    do("B2h", "insert {key:'s'} twice in one batch", insert_cmd(c2, [{"key": "s"}, {"key": "s"}]),
       lambda o, r: ("Two string keys accepted (n=%s): strings do not satisfy the numeric $gt:0 filter" % o.get("n"))
       if o["kind"] == "ok" else "String duplicates rejected with %s, so strings fall inside $gt:0 here" % err_phrase(o),
       value_cmp=ok_count_cmp(2))
    do("B2i", "update {key:0} -> {key:5} (moves a doc into the filter, colliding)",
       SON([("update", c2), ("updates", [SON([("q", {"key": 0}), ("u", {"$set": {"key": 5}}), ("multi", False),
                                              ("upsert", False)])]), ("ordered", True)]),
       lambda o, r: ("Colliding update ACCEPTED (n=%s, nModified=%s)" % (o.get("n"), o.get("nModified")))
       if o["kind"] == "ok" else "Update into the filter rejected with %s, so uniqueness is enforced on update" % err_phrase(o))
    count_step("B2j", c2)

# B3 / B4: partial-filter limits
c3 = "pu_extra"
pre_cmd = SON([("create", c3)])
pre = run_command(pre_cmd)
spec3 = SON([("key", {"key": 1}), ("name", "uq_key_notexists"), ("unique", True),
             ("partialFilterExpression", {"key": {"$exists": False}})])
resp, out, _ = run_command(ci_cmd(c3, spec3))
resp["precondition"] = OrderedDict(command=cmd_text(pre_cmd), response=pre[0])
add("B3", "createIndexes unique + partialFilterExpression {key:{$exists:false}}",
    "%s; then %s" % (cmd_text(pre_cmd), cmd_text(ci_cmd(c3, spec3))), resp, out,
    ("createIndexes ACCEPTED $exists:false in a partial filter (numIndexesAfter=%s)" % nidx(resp.get("raw_response", {})))
    if out["kind"] == "ok" else "$exists:false in a unique partial filter rejected with %s" % err_phrase(out))
spec3b = SON([("key", {"key3": 1}), ("name", "ix_key3_notexists"), ("partialFilterExpression", {"key3": {"$exists": False}})])
do("B3b", "createIndexes NON-unique + partialFilterExpression {key3:{$exists:false}}", ci_cmd(c3, spec3b),
   lambda o, r: ("createIndexes ACCEPTED $exists:false in a non-unique partial filter")
   if o["kind"] == "ok" else "$exists:false in a non-unique partial filter rejected with %s" % err_phrase(o))
spec4 = SON([("key", {"key2": 1}), ("name", "uq_sparse_pfe"), ("unique", True), ("sparse", True),
             ("partialFilterExpression", {"key2": {"$gt": 0}})])
do("B4", "createIndexes unique + sparse + partialFilterExpression", ci_cmd(c3, spec4),
   lambda o, r: "createIndexes ACCEPTED the sparse + partialFilterExpression mix" if o["kind"] == "ok"
   else "unique + sparse + partialFilterExpression rejected with %s" % err_phrase(o))

c4 = "pu_sparse"
pre_cmd = SON([("create", c4)])
pre = run_command(pre_cmd)
spec4b = SON([("key", {"key4": 1}), ("name", "uq_key4_sparse"), ("unique", True), ("sparse", True)])
resp, out, _ = run_command(ci_cmd(c4, spec4b))
resp["precondition"] = OrderedDict(command=cmd_text(pre_cmd), response=pre[0])
add("B4b", "control: createIndexes unique + sparse without partialFilterExpression",
    "%s; then %s" % (cmd_text(pre_cmd), cmd_text(ci_cmd(c4, spec4b))), resp, out,
    ("unique + sparse alone accepted (numIndexesAfter=%s), so B4 fails because of the mix" % nidx(resp.get("raw_response", {})))
    if out["kind"] == "ok" else "unique + sparse alone rejected with %s" % err_phrase(out))
if out["kind"] == "ok":
    do("B4c", "insert two docs without key4 into the sparse unique index", insert_cmd(c4, [{"other": 1}, {"other": 2}]),
       lambda o, r: ("Two documents without key4 accepted (n=%s): sparse skips missing keys" % o.get("n"))
       if o["kind"] == "ok" else "Keyless documents rejected with %s" % err_phrase(o))
    do("B4d", "insert {key4:7} twice into the sparse unique index", insert_cmd(c4, [{"key4": 7}, {"key4": 7}]),
       lambda o, r: ("Duplicate {key4:7} ACCEPTED (n=%s)" % o.get("n"))
       if o["kind"] == "ok" else "Second {key4:7} rejected with %s (n=%s inserted before the error)" % (err_phrase(o), o.get("n")))

# ============================================================================= cleanup
do("Z1", "drop test database mt_schema", SON([("dropDatabase", 1)]),
   lambda o, r: "Test database dropped" if o["kind"] == "ok" else "dropDatabase failed: %s" % err_phrase(o),
   vs="n/a", target="client['mt_schema']")
ld = SON([("listDatabases", 1), ("nameOnly", True), ("filter", {"name": DB})])
resp, out, r = run_command(ld, client.admin)
left = [d.get("name") for d in (r or {}).get("databases", [])] if r is not None else None
add("Z2", "verify mt_schema is gone", cmd_text(ld, "client.admin"), resp, out,
    ("mt_schema no longer listed" if left == [] else "mt_schema still listed: %s" % left) if out["kind"] == "ok"
    else "listDatabases failed: %s" % err_phrase(out), vs="n/a")

report = OrderedDict()
report["test"] = TEST_ID
report["database"] = DB
report["target"] = ("managed Azure DocumentDB test cluster (Microsoft.DocumentDB/mongoClusters, eastus, M30, one shard, "
                    "server version 8.0, Premium SSD v2, HA disabled), plain (non-global) host, SCRAM, TLS, retrywrites=false")
report["engine_versions"] = OrderedDict(hello_internal=hello_sel.get("internal"), maxWireVersion=hello_sel.get("maxWireVersion"),
                                        buildInfo_version=bi_sel.get("version"))
report["driver"] = "PyMongo %s, Python %s" % (pymongo.version, sys.version.split()[0])
report["open_source_baseline"] = OrderedDict(report=OSS_REPORT, engine=OSS_META)
report["run_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
report["duration_s"] = round(time.time() - t_start, 1)
report["notes"] = [
    "Writes are sent as raw insert/update commands through Database.command so writeErrors[].errInfo and top-level "
    "errorLabels are visible; each document gets a client-side ObjectId _id first, as insert_one/insert_many do.",
    "Gossip fields removed from recorded raw responses: %s." % (sorted(GOSSIP_SEEN) or "none were returned"),
    "Password, user name, URIs and host names are masked; no e-mail addresses or GUIDs were present.",
    "Data-plane only: no cluster configuration was changed.",
]
report["steps"] = steps
out_path = os.path.join(HERE, os.environ.get("REPORT_NAME", "report.json"))
with open(out_path, "w") as f:
    json.dump(report, f, indent=2, default=str)
print("REPORT:", out_path, "steps:", len(steps), "duration_s:", report["duration_s"])
client.close()
