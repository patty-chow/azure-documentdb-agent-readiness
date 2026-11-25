#!/usr/bin/env python3
"""jsonschema-and-partial-unique: ENGINE 1.2.0 RERUN against documentdb-local (database t_schema).

Rerun of findings/phase4/engine-tests/jsonschema-and-partial-unique/run_test.py (engine 0.117).
Every step the 0.117 run recorded is repeated with the same step label, validator and documents,
so report.json can carry a step-by-step comparison. Extra steps are added (raw server replies,
_id-counting probes, collMod enforcement, update/findAndModify validation, validationAction warn,
numeric-type duplicates, $exists:false / sparse combinations, sparse unique without a filter).

Reads LOCAL_URI from the shared local.env; never prints or stores the password.
Touches only database t_schema: dropped at the start (setup) and at the end (teardown).
Writes report.json next to this script.

Run: /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python run_test.py
"""
import json
import os
import re
import subprocess
import time
from collections import OrderedDict
from urllib.parse import quote_plus

import pymongo
from bson import Int64, ObjectId, json_util
from pymongo import MongoClient, errors

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/local.env"
PRIOR_REPORT = ("/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/"
                "jsonschema-and-partial-unique/report.json")
DB = "t_schema"
CONTAINER = "ddb-engine-test"
TEST_ID = "jsonschema-and-partial-unique"


# ----------------------------------------------------------------------------- credentials
def load_env():
    env = {}
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    if "LOCAL_URI" not in env:
        raise SystemExit("LOCAL_URI not found in local.env")
    return env


ENVV = load_env()
URI = ENVV["LOCAL_URI"]
_m = re.match(r"mongodb(?:\+srv)?://[^:/@]+:([^@]+)@", URI)
SECRETS = {s for s in (ENVV.get("LOCAL_PASS"), _m.group(1) if _m else None) if s and len(s) >= 4}
SECRETS |= {quote_plus(s) for s in list(SECRETS)}


def redact(s):
    s = re.sub(r"(mongodb(?:\+srv)?://[^:/@\s]+:)[^@\s]+@", r"\1***@", str(s))
    for sec in SECRETS:
        s = s.replace(sec, "***")
    return s


# ----------------------------------------------------------------------------- helpers
def jsonable(x):
    return json.loads(json_util.dumps(x))


def pj(x):
    return json.dumps(x)


def err_info(e):
    """Exact error fields as the driver surfaced them (write error doc or command reply)."""
    info = OrderedDict()
    info["exception"] = type(e).__name__
    details = getattr(e, "details", None)
    if isinstance(e, errors.BulkWriteError):
        we = (details or {}).get("writeErrors") or []
        d0 = we[0] if we else {}
        info["code"] = d0.get("code")
        info["codeName"] = d0.get("codeName")
        info["errmsg"] = d0.get("errmsg")
        info["errInfo_present"] = "errInfo" in d0
        if "errInfo" in d0:
            info["errInfo"] = jsonable(d0["errInfo"])
        info["writeError_fields"] = sorted(d0.keys())
        info["nInserted"] = (details or {}).get("nInserted")
    elif isinstance(e, errors.WriteError):  # includes DuplicateKeyError
        d0 = details or {}
        info["code"] = d0.get("code", getattr(e, "code", None))
        info["codeName"] = d0.get("codeName")
        info["errmsg"] = d0.get("errmsg")
        info["errInfo_present"] = "errInfo" in d0
        if "errInfo" in d0:
            info["errInfo"] = jsonable(d0["errInfo"])
        info["writeError_fields"] = sorted(d0.keys())
    elif isinstance(e, errors.OperationFailure):
        d = details or {}
        info["code"] = d.get("code", getattr(e, "code", None))
        info["codeName"] = d.get("codeName")
        info["errmsg"] = redact(d.get("errmsg", str(e)))
        info["errInfo_present"] = "errInfo" in d
        if "errInfo" in d:
            info["errInfo"] = jsonable(d["errInfo"])
        info["reply_fields"] = sorted(d.keys())
    else:
        info["code"] = getattr(e, "code", None)
        info["codeName"] = None
        info["errmsg"] = redact(str(e))
        info["errInfo_present"] = False
    labels = details.get("errorLabels") if isinstance(details, dict) else None
    if labels is None:
        labels = sorted(getattr(e, "_error_labels", None) or [])
    info["errorLabels"] = labels
    info["raw"] = jsonable(details) if isinstance(details, dict) else None
    return info


def fmt(i):
    cn = i.get("codeName")
    msg = (i.get("errmsg") or "").strip().replace("\n", " ")
    s = f"code {i.get('code')} {cn if cn else '(no codeName)'} \"{msg}\""
    s += ", errInfo present" if i.get("errInfo_present") else ", no errInfo"
    if i.get("errorLabels"):
        s += f", errorLabels {i['errorLabels']}"
    return s


steps = []
S = {}  # label -> step


def record(step, command, response, reading):
    entry = OrderedDict(step=step, command=command, response=response, reading=reading)
    steps.append(entry)
    S[step] = entry
    print(redact(f"[{len(steps):03d}] {step}\n      -> {json.dumps(response, default=str)[:360]}\n      {reading}"))
    return entry


def run(step, command, fn, reading_ok, reading_err=None, post=None, extra=None):
    """Run one driver call; record exact result or error, optional post-check, and a reading.
    reading_ok / reading_err are strings or callables receiving the full response dict."""
    t0 = time.time()
    resp = OrderedDict()
    try:
        r = fn()
        resp["result"] = jsonable(r) if r is not None else None
        ok = True
    except Exception as e:  # noqa: BLE001 - every error is recorded
        resp["error"] = err_info(e)
        ok = False
    resp["ms"] = int((time.time() - t0) * 1000)
    if extra:
        resp.update(extra)
    if post:
        try:
            resp["post_check"] = jsonable(post())
        except Exception as e:  # noqa: BLE001
            resp["post_check"] = {"error": err_info(e)}
    if ok:
        reading = reading_ok(resp) if callable(reading_ok) else reading_ok
    else:
        if callable(reading_err):
            reading = reading_err(resp)
        else:
            reading = reading_err or f"Rejected with {fmt(resp['error'])}."
    record(step, command, resp, reading)
    return ok, resp


def sh(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return OrderedDict(cmd=" ".join(cmd), rc=p.returncode, stdout=redact(p.stdout.strip()),
                           stderr=redact(p.stderr.strip()[:400]))
    except Exception as e:  # noqa: BLE001
        return OrderedDict(cmd=" ".join(cmd), error=repr(e))


def raw_reading(resp, expect=None):
    r = resp["result"] or {}
    we = r.get("writeErrors") or []
    if we:
        w = we[0]
        s = (f"Server reply ok={r.get('ok')} n={r.get('n')} with writeErrors[0] fields {sorted(w.keys())}: "
             f"code {w.get('code')}, codeName {'absent' if 'codeName' not in w else repr(w.get('codeName'))}, "
             f"errmsg \"{w.get('errmsg')}\", errInfo {'PRESENT' if 'errInfo' in w else 'absent'}")
        for k in ("keyPattern", "keyValue"):
            if k in w:
                s += f", {k} {json.dumps(w[k])}"
        return s + "."
    return f"Server reply ok={r.get('ok')} n={r.get('n')} nModified={r.get('nModified')} with no writeErrors: the write was applied."


def expect_reading(accepted, expect, why, resp, kw, doc=None):
    why_s = f" ({why})" if why else ""
    d = f"Document {pj(doc)}" if doc is not None else "Document"
    if accepted:
        if expect == "accept":
            return f"{d} accepted, as MongoDB semantics predict{why_s}."
        return f"{d} ACCEPTED although MongoDB semantics reject it{why_s}, so '{kw}' is not enforced for it."
    e = resp["error"]
    if expect == "reject":
        return f"{d} rejected with {fmt(e)}, as MongoDB semantics predict{why_s}."
    return f"{d} REJECTED although MongoDB semantics accept it{why_s}: {fmt(e)}."


# ----------------------------------------------------------------------------- connect
client = MongoClient(URI, serverSelectionTimeoutMS=15000, connectTimeoutMS=15000, socketTimeoutMS=280000)
db = client[DB]


def coll_state(name):
    cols = list(db.list_collections(filter={"name": name}))
    return OrderedDict(exists=bool(cols), options=(cols[0].get("options") if cols else None))


def options(name):
    cols = list(db.list_collections(filter={"name": name}))
    return cols[0].get("options", {}) if cols else None


def ins(cname, doc, bypass=False):
    kwargs = {"bypass_document_validation": True} if bypass else {}
    r = db[cname].insert_one(dict(doc), **kwargs)
    return {"acknowledged": r.acknowledged, "inserted_id": r.inserted_id}


def ins_many(cname, docs):
    return {"inserted": len(db[cname].insert_many([dict(d) for d in docs]).inserted_ids)}


def raw_insert(cname, doc):
    return db.command("insert", cname, documents=[OrderedDict([("_id", ObjectId())] + list(doc.items()))])


def cidx(cname, spec):
    return db.command("createIndexes", cname, indexes=[spec])


def list_indexes(cname):
    return list(db[cname].list_indexes())


def count(cname):
    return {"count": db[cname].count_documents({})}


def shard(resp):
    r = resp.get("result") or {}
    return (r.get("raw") or {}).get("defaultShard", r)


# ----------------------------------------------------------------------------- engine identity
bi = client.admin.command("buildInfo")
BI_KEYS = ("version", "gitVersion", "modules", "versionArray", "maxBsonObjectSize")
bi_subset = OrderedDict((k, jsonable(bi.get(k))) for k in BI_KEYS if k in bi)
record("buildInfo", "pymongo: client.admin.command('buildInfo')  [mongosh: db.adminCommand({buildInfo: 1})]",
       bi_subset,
       f"buildInfo reports version {bi.get('version')}, the MongoDB compatibility version the gateway advertises, "
       f"not the engine release; facts below are about the open-source engine and gateway in this container, not the managed service.")
record("buildInfo (full reply)", "pymongo: client.admin.command('buildInfo')", jsonable(bi),
       f"Full buildInfo reply has keys {sorted(bi.keys())}; none of them names the DocumentDB engine release, so the image label and extension control file identify it.")
hello = client.admin.command("hello")
HELLO_KEYS = ("maxWireVersion", "minWireVersion", "maxWriteBatchSize", "maxBsonObjectSize")
record("hello", "pymongo: client.admin.command('hello')  [mongosh: db.adminCommand({hello: 1})]",
       OrderedDict((k, jsonable(hello.get(k))) for k in HELLO_KEYS if k in hello),
       f"Gateway advertises wire versions {hello.get('minWireVersion')}..{hello.get('maxWireVersion')} and maxWriteBatchSize {hello.get('maxWriteBatchSize')}.")

img = sh(["docker", "inspect", CONTAINER, "--format", "{{.Config.Image}}|{{.Image}}"])
lab = sh(["docker", "inspect", CONTAINER, "--format", "{{json .Config.Labels}}"])
pgv = sh(["docker", "exec", CONTAINER, "/usr/lib/postgresql/17/bin/postgres", "--version"])
ctl = sh(["docker", "exec", CONTAINER, "sh", "-c",
          "grep -H default_version /usr/share/postgresql/17/extension/documentdb.control "
          "/usr/share/postgresql/17/extension/documentdb_core.control"])
try:
    labels = json.loads(lab.get("stdout") or "{}")
except Exception:  # noqa: BLE001
    labels = {}
image_ref, _, image_id = (img.get("stdout") or "|").partition("|")
ext_versions = dict(re.findall(r"extension/(\w+)\.control:default_version = '([^']+)'", ctl.get("stdout") or ""))
container_facts = OrderedDict(
    container=CONTAINER, image=image_ref, image_id=image_id,
    image_version_label=labels.get("org.opencontainers.image.version"),
    image_revision=labels.get("org.opencontainers.image.revision"),
    image_created=labels.get("org.opencontainers.image.created"),
    postgres=(pgv.get("stdout") or "").strip(), extension_default_versions=ext_versions,
    commands=[img, lab, pgv, ctl])
record("container image and engine build (docker inspect / docker exec, read-only)",
       "docker inspect ddb-engine-test --format '{{.Config.Image}}|{{.Image}}'; docker inspect ddb-engine-test --format "
       "'{{json .Config.Labels}}'; docker exec ddb-engine-test /usr/lib/postgresql/17/bin/postgres --version; docker exec "
       "ddb-engine-test grep -H default_version .../extension/documentdb.control .../documentdb_core.control",
       container_facts,
       f"Container runs {image_ref} (OCI version {container_facts['image_version_label']}, revision "
       f"{(container_facts['image_revision'] or '')[:8]}, built {container_facts['image_created']}) with "
       f"{container_facts['postgres']} and documentdb extension {ext_versions.get('documentdb')}.")

engine_version = OrderedDict(
    buildInfo=bi_subset,
    buildInfo_note=(f"buildInfo.version {bi.get('version')} is the MongoDB compatibility version the gateway advertises "
                    f"(hello.maxWireVersion {hello.get('maxWireVersion')}), not the engine release."),
    container_image=image_ref, image_version_label=container_facts["image_version_label"],
    image_revision=container_facts["image_revision"], image_created=container_facts["image_created"],
    postgres=container_facts["postgres"], documentdb_extension_default_version=ext_versions.get("documentdb"),
    pymongo=pymongo.version)

# ----------------------------------------------------------------------------- setup
run("drop t_schema (setup)",
    "pymongo: client['t_schema'].command('dropDatabase')  [mongosh: db.getSiblingDB('t_schema').dropDatabase()]",
    lambda: db.command("dropDatabase"),
    lambda r: f"dropDatabase returned {json.dumps(r['result'])}, so the run starts from an empty t_schema.")

# ============================================================================= Part A: $jsonSchema validators
BASELINE = {"$jsonSchema": {"bsonType": "object", "required": ["name"], "properties": {"name": {"bsonType": "string"}}}}

ok_base, resp_base = run(
    "A0 create collection with baseline validator (bsonType/required/properties)",
    f"pymongo: db.command('create', 'v_baseline', validator={pj(BASELINE)})  [mongosh: db.createCollection('v_baseline', {{validator: {pj(BASELINE)}}})]",
    lambda: db.command("create", "v_baseline", validator=BASELINE),
    "Collection validators are enabled on this build: create accepted a baseline $jsonSchema.",
    lambda r: f"Collection validators are gated on this build: create returned {fmt(r['error'])} even for a baseline $jsonSchema.")

if ok_base:
    run("A0b listCollections options for v_baseline",
        "pymongo: list(db.list_collections(filter={'name': 'v_baseline'}))[0]['options']  [mongosh: db.getCollectionInfos({name:'v_baseline'})[0].options]",
        lambda: options("v_baseline"),
        lambda r: (f"Stored options are validator plus validationLevel '{(r['result'] or {}).get('validationLevel')}' and "
                   f"validationAction '{(r['result'] or {}).get('validationAction')}'."))
    run("A0c insert violating doc into v_baseline (missing required name)",
        "pymongo: db['v_baseline'].insert_one({'x': 1})  [mongosh: db.v_baseline.insertOne({x:1})]",
        lambda: ins("v_baseline", {"x": 1}),
        "Violating insert was ACCEPTED: the validator is stored but not enforced.",
        lambda r: f"Violating insert rejected by the driver as {r['error']['exception']} with {fmt(r['error'])}.")
    run("A0c-r raw insert command reply for violating doc (missing required name)",
        "pymongo: db.command('insert', 'v_baseline', documents=[{'_id': ObjectId(), 'x': 1}])  [mongosh: db.runCommand({insert:'v_baseline', documents:[{x:1}]})]",
        lambda: raw_insert("v_baseline", {"x": 1}),
        lambda r: raw_reading(r),
        lambda r: f"Insert command itself failed: {fmt(r['error'])}.")
    run("A0d insert violating doc with bypassDocumentValidation",
        "pymongo: db['v_baseline'].insert_one({'x': 1}, bypass_document_validation=True)  [mongosh: db.v_baseline.insertOne({x:1}, {bypassDocumentValidation:true})]",
        lambda: ins("v_baseline", {"x": 1}, bypass=True),
        "bypassDocumentValidation:true lets the violating document through.",
        lambda r: f"bypassDocumentValidation did not help: {fmt(r['error'])}.")
    run("A0e insert valid doc {name:'n1'} into v_baseline",
        "pymongo: db['v_baseline'].insert_one({'name': 'n1'})  [mongosh: db.v_baseline.insertOne({name:'n1'})]",
        lambda: ins("v_baseline", {"name": "n1"}),
        "Valid document accepted, giving the update tests a target.",
        lambda r: f"Valid document unexpectedly rejected: {fmt(r['error'])}.")
    run("A0f updateOne $set name to a number (violates)",
        "pymongo: db['v_baseline'].update_one({'name': 'n1'}, {'$set': {'name': 5}})  [mongosh: db.v_baseline.updateOne({name:'n1'}, {$set:{name:5}})]",
        lambda: db["v_baseline"].update_one({"name": "n1"}, {"$set": {"name": 5}}).raw_result,
        lambda r: f"Violating update was APPLIED ({json.dumps(r['result'])}): updates are not validated.",
        lambda r: f"Violating update rejected by the driver as {r['error']['exception']} with {fmt(r['error'])}.")
    run("A0f-r raw update command reply for violating update",
        "pymongo: db.command('update', 'v_baseline', updates=[{'q': {'name': 'n1'}, 'u': {'$set': {'name': 5}}}])  [mongosh: db.runCommand({update:'v_baseline', updates:[{q:{name:'n1'}, u:{$set:{name:5}}}]})]",
        lambda: db.command("update", "v_baseline", updates=[{"q": {"name": "n1"}, "u": {"$set": {"name": 5}}}]),
        lambda r: raw_reading(r),
        lambda r: f"Update command itself failed: {fmt(r['error'])}.")
    run("A0g findOneAndUpdate $set name to a number (violates)",
        "pymongo: db['v_baseline'].find_one_and_update({'name': 'n1'}, {'$set': {'name': 6}})  [mongosh: db.v_baseline.findOneAndUpdate({name:'n1'}, {$set:{name:6}})]",
        lambda: db["v_baseline"].find_one_and_update({"name": "n1"}, {"$set": {"name": 6}}),
        lambda r: f"Violating findAndModify was APPLIED (returned {json.dumps(r['result'])}): findAndModify is not validated.",
        lambda r: f"Violating findAndModify rejected as {r['error']['exception']} with {fmt(r['error'])}.")
    run("A0h create collection with baseline validator and validationAction 'warn'",
        f"pymongo: db.command('create', 'v_warn', validator={pj(BASELINE)}, validationAction='warn')  [mongosh: db.createCollection('v_warn', {{validator: {pj(BASELINE)}, validationAction:'warn'}})]",
        lambda: db.command("create", "v_warn", validator=BASELINE, validationAction="warn"),
        "create accepted validationAction 'warn'.",
        lambda r: f"validationAction 'warn' rejected: {fmt(r['error'])}.",
        post=lambda: coll_state("v_warn"))
    run("A0i insert violating doc into validationAction 'warn' collection",
        "pymongo: db['v_warn'].insert_one({'x': 1})  [mongosh: db.v_warn.insertOne({x:1})]",
        lambda: ins("v_warn", {"x": 1}),
        "Violating insert accepted under validationAction 'warn', as MongoDB semantics predict.",
        lambda r: f"Violating insert rejected even with validationAction 'warn': {fmt(r['error'])}.")
else:
    run("A0e create plain collection cm_baseline", "pymongo: db.command('create', 'cm_baseline')",
        lambda: db.command("create", "cm_baseline"), "Plain collection created.")
    run("A0f collMod baseline validator onto cm_baseline",
        f"pymongo: db.command('collMod', 'cm_baseline', validator={pj(BASELINE)})",
        lambda: db.command("collMod", "cm_baseline", validator=BASELINE),
        "collMod accepted a baseline validator even though create rejected one.",
        lambda r: f"collMod also gated: {fmt(r['error'])}.")

# Keyword cases. Validators and valid/violating documents are the 0.117 ones except where noted.
# Each document carries the outcome MongoDB semantics predict (the driver adds a client-side _id,
# which $jsonSchema sees as a top-level field).
CASES = [
    dict(kw="enum", safe="enum",
         validator={"$jsonSchema": {"bsonType": "object", "properties": {"status": {"enum": ["new", "done"]}}}},
         valid=({"status": "new"}, "accept", ""), violating=({"status": "bogus"}, "reject", "")),
    dict(kw="additionalProperties", safe="additionalProperties",
         validator={"$jsonSchema": {"bsonType": "object", "properties": {"a": {"bsonType": "int"}}, "additionalProperties": False}},
         valid=({"a": 1}, "reject", "the client-generated _id is not listed in properties, so it counts as an additional property"),
         valid_label="A2.additionalProperties insert valid doc ({a:1}; _id is not listed in properties)",
         violating=({"a": 1, "extra": 1}, "reject", "")),
    dict(kw="additionalProperties+_id", safe="additionalProperties_with_id",
         validator={"$jsonSchema": {"bsonType": "object", "properties": {"_id": {"bsonType": "objectId"}, "a": {"bsonType": "int"}},
                                    "additionalProperties": False}},
         valid=({"a": 1}, "accept", ""), violating=({"a": 1, "extra": 1}, "reject", "")),
    dict(kw="allOf", safe="allOf",
         validator={"$jsonSchema": {"allOf": [{"required": ["a"]}, {"required": ["b"]}]}},
         valid=({"a": 1, "b": 1}, "accept", ""), violating=({"a": 1}, "reject", "")),
    dict(kw="anyOf", safe="anyOf",
         validator={"$jsonSchema": {"anyOf": [{"required": ["a"]}, {"required": ["b"]}]}},
         valid=({"a": 1}, "accept", ""), violating=({"c": 1}, "reject", "")),
    dict(kw="oneOf", safe="oneOf",
         validator={"$jsonSchema": {"oneOf": [{"required": ["a"]}, {"required": ["b"]}]}},
         valid=({"a": 1}, "accept", ""), violating=({"a": 1, "b": 1}, "reject", "both branches match")),
    dict(kw="not", safe="not",
         validator={"$jsonSchema": {"not": {"required": ["forbidden"]}}},
         valid=({"ok": 1}, "accept", ""), violating=({"forbidden": 1}, "reject", "")),
    dict(kw="patternProperties", safe="patternProperties",
         validator={"$jsonSchema": {"patternProperties": {"^x_": {"bsonType": "int"}}}},
         valid=({"x_1": 1}, "accept", ""), violating=({"x_1": "str"}, "reject", "")),
    dict(kw="dependencies", safe="dependencies",
         validator={"$jsonSchema": {"dependencies": {"a": ["b"]}}},
         valid=({"a": 1, "b": 1}, "accept", ""), violating=({"a": 1}, "reject", "")),
    dict(kw="dependencies(schema)", safe="dependencies_schema",
         validator={"$jsonSchema": {"dependencies": {"a": {"required": ["c"]}}}},
         valid=({"a": 1, "c": 1}, "accept", ""), violating=({"a": 1}, "reject", "schema dependency requires c when a is present")),
    dict(kw="minProperties", safe="minProperties",
         validator={"$jsonSchema": {"minProperties": 2}},
         valid=({"a": 1, "b": 1}, "accept", ""),
         violating=({}, "reject", "only the client-generated _id is present; the 0.117 script used {a:1}, which has 2 fields once _id is counted"),
         probes=[({"a": 1}, "accept", "2 top-level fields once the client-generated _id is counted; a rejection would mean the engine does not count _id")]),
    dict(kw="maxProperties", safe="maxProperties",
         validator={"$jsonSchema": {"maxProperties": 2}},
         valid=({"a": 1}, "accept", ""), violating=({"a": 1, "b": 1, "c": 1}, "reject", ""),
         probes=[({"a": 1, "b": 1}, "reject", "3 top-level fields once the client-generated _id is counted; acceptance would mean the engine does not count _id")]),
]

KW = OrderedDict()  # keyword -> matrix row


def outcome(resp):
    if "error" in resp:
        e = resp["error"]
        return f"rejected ({e.get('code')} {e.get('codeName') or '(no codeName)'}: {(e.get('errmsg') or '').strip()})"
    return "accepted"


for c in CASES:
    kw, v, s = c["kw"], c["validator"], c["safe"]
    cname, cm = f"v_{s}", f"cm_{s}"
    row = OrderedDict(validator=v)
    ok1, r1 = run(
        f"A1.{kw} create collection with $jsonSchema using {kw}",
        f"pymongo: db.command('create', '{cname}', validator={pj(v)})  [mongosh: db.createCollection('{cname}', {{validator: {pj(v)}}})]",
        lambda v=v, cname=cname: db.command("create", cname, validator=v),
        lambda r, kw=kw: (f"create accepted a validator using '{kw}'; listCollections shows it stored with validationLevel "
                          f"'{((r.get('post_check') or {}).get('options') or {}).get('validationLevel')}' and validationAction "
                          f"'{((r.get('post_check') or {}).get('options') or {}).get('validationAction')}'."),
        lambda r, kw=kw: (f"create rejected '{kw}' with {fmt(r['error'])}, and "
                          f"{'no collection was left behind' if not (r.get('post_check') or {}).get('exists') else 'a collection WAS left behind'}."),
        post=lambda cname=cname: coll_state(cname))
    row["create"] = outcome(r1)
    if not ok1:
        row["violating_insert_after_create"] = ("not applicable: create rejected the keyword and left no collection, "
                                                "so there is no validator to enforce")
        if c.get("probes"):
            row["id_counting_probes"] = "not run: they need a collection whose validator uses this keyword"
    if ok1:
        vdoc, vexp, vwhy = c["valid"]
        okv, rv = run(c.get("valid_label") or f"A2.{kw} insert valid doc",
                      f"pymongo: db['{cname}'].insert_one({pj(vdoc)})  [mongosh: db.{cname}.insertOne({pj(vdoc)})]",
                      lambda d=vdoc, cname=cname: ins(cname, d),
                      lambda r, a=vexp, w=vwhy, kw=kw, d=vdoc: expect_reading(True, a, w, r, kw, d),
                      lambda r, a=vexp, w=vwhy, kw=kw, d=vdoc: expect_reading(False, a, w, r, kw, d))
        row["valid_insert_after_create"] = outcome(rv)
        bdoc, bexp, bwhy = c["violating"]
        okb, rb = run(f"A3.{kw} insert violating doc",
                      f"pymongo: db['{cname}'].insert_one({pj(bdoc)})  [mongosh: db.{cname}.insertOne({pj(bdoc)})]",
                      lambda d=bdoc, cname=cname: ins(cname, d),
                      lambda r, a=bexp, w=bwhy, kw=kw, d=bdoc: expect_reading(True, a, w, r, kw, d),
                      lambda r, a=bexp, w=bwhy, kw=kw, d=bdoc: expect_reading(False, a, w, r, kw, d))
        row["violating_insert_after_create"] = outcome(rb) + (
            "" if okb else (", errInfo present" if rb["error"].get("errInfo_present") else ", no errInfo"))
        run(f"A3r.{kw} raw insert command reply for violating doc",
            f"pymongo: db.command('insert', '{cname}', documents=[{{'_id': ObjectId(), **{pj(bdoc)}}}])  [mongosh: db.runCommand({{insert:'{cname}', documents:[{pj(bdoc)}]}})]",
            lambda d=bdoc, cname=cname: raw_insert(cname, d),
            lambda r: raw_reading(r),
            lambda r: f"Insert command itself failed: {fmt(r['error'])}.")
        for j, (pdoc, pexp, pwhy) in enumerate(c.get("probes", []), 1):
            okp, rp = run(f"A3p{j}.{kw} probe insert {pj(pdoc)} (does validation count _id?)",
                          f"pymongo: db['{cname}'].insert_one({pj(pdoc)})  [mongosh: db.{cname}.insertOne({pj(pdoc)})]",
                          lambda d=pdoc, cname=cname: ins(cname, d),
                          lambda r, a=pexp, w=pwhy, kw=kw, d=pdoc: expect_reading(True, a, w, r, kw, d),
                          lambda r, a=pexp, w=pwhy, kw=kw, d=pdoc: expect_reading(False, a, w, r, kw, d))
            row[f"probe_{j}_{pj(pdoc)}"] = outcome(rp)
    # collMod path, independent of the create result (same as 0.117)
    try:
        setup = jsonable(db.command("create", cm))
    except Exception as e:  # noqa: BLE001
        setup = {"error": err_info(e)}
    ok2, r2 = run(
        f"A4.{kw} collMod validator using {kw} onto plain collection",
        f"pymongo: db.command('create', '{cm}'); db.command('collMod', '{cm}', validator={pj(v)})  [mongosh: db.createCollection('{cm}'); db.runCommand({{collMod:'{cm}', validator: {pj(v)}}})]",
        lambda v=v, cm=cm: db.command("collMod", cm, validator=v),
        lambda r, kw=kw: (f"collMod accepted a validator using '{kw}'; listCollections then shows "
                          f"{'the validator stored' if ((r.get('post_check') or {}).get('options') or {}).get('validator') else 'NO validator'}."),
        lambda r, kw=kw: (f"collMod rejected '{kw}' with {fmt(r['error'])}, and the collection kept "
                          f"{'no validator' if not ((r.get('post_check') or {}).get('options') or {}).get('validator') else 'a validator'}."),
        extra={"setup_create_plain_reply": setup},
        post=lambda cm=cm: coll_state(cm))
    row["collMod"] = outcome(r2)
    if not ok2:
        row["violating_insert_after_collMod"] = ("not applicable: collMod rejected the keyword and the collection kept no "
                                                 "validator (see the A4 post_check)")
    if ok2:
        bdoc, bexp, bwhy = c["violating"]
        ok5, r5 = run(f"A5.{kw} insert violating doc after collMod",
                      f"pymongo: db['{cm}'].insert_one({pj(bdoc)})  [mongosh: db.{cm}.insertOne({pj(bdoc)})]",
                      lambda d=bdoc, cm=cm: ins(cm, d),
                      lambda r, a=bexp, w=bwhy, kw=kw, d=bdoc: expect_reading(True, a, w, r, kw, d),
                      lambda r, a=bexp, w=bwhy, kw=kw, d=bdoc: expect_reading(False, a, w, r, kw, d))
        row["violating_insert_after_collMod"] = outcome(r5) + (
            "" if ok5 else (", errInfo present" if r5["error"].get("errInfo_present") else ", no errInfo"))
        vdoc, vexp, vwhy = c["valid"]
        ok6, r6 = run(f"A6.{kw} insert valid doc after collMod",
                      f"pymongo: db['{cm}'].insert_one({pj(vdoc)})  [mongosh: db.{cm}.insertOne({pj(vdoc)})]",
                      lambda d=vdoc, cm=cm: ins(cm, d),
                      lambda r, a=vexp, w=vwhy, kw=kw, d=vdoc: expect_reading(True, a, w, r, kw, d),
                      lambda r, a=vexp, w=vwhy, kw=kw, d=vdoc: expect_reading(False, a, w, r, kw, d))
        row["valid_insert_after_collMod"] = outcome(r6)
    KW[kw] = row

# ============================================================================= Part B: unique partial indexes
# B1: { key: { $exists: true } }
c1 = "pu_exists"
db.command("create", c1)
okB1, rB1 = run(
    "B1 createIndexes unique + partialFilterExpression {key:{$exists:true}}",
    "pymongo: db.command('create', 'pu_exists'); db.command('createIndexes', 'pu_exists', indexes=[{'key': {'key': 1}, 'name': 'uq_key_exists', "
    "'unique': True, 'partialFilterExpression': {'key': {'$exists': True}}}])  [mongosh: db.pu_exists.createIndex({key:1}, {unique:true, "
    "partialFilterExpression:{key:{$exists:true}}, name:'uq_key_exists'})]",
    lambda: cidx(c1, {"key": {"key": 1}, "name": "uq_key_exists", "unique": True, "partialFilterExpression": {"key": {"$exists": True}}}),
    lambda r: (f"Accepted: numIndexesBefore={shard(r).get('numIndexesBefore')} numIndexesAfter={shard(r).get('numIndexesAfter')} "
               f"ok={r['result'].get('ok')} (the gateway nests the per-shard result under raw.defaultShard)."),
    lambda r: f"Rejected: {fmt(r['error'])}.")
if okB1:
    run("B1a listIndexes", "pymongo: list(db['pu_exists'].list_indexes())  [mongosh: db.pu_exists.getIndexes()]",
        lambda: list_indexes(c1),
        lambda r: f"Index stored as {json.dumps([i for i in r['result'] if i.get('name') == 'uq_key_exists'])}.")
    run("B1b insert {key:1}", "pymongo: db['pu_exists'].insert_one({'key': 1})  [mongosh: db.pu_exists.insertOne({key:1})]",
        lambda: ins(c1, {"key": 1}), "First keyed document accepted.",
        lambda r: f"First keyed document rejected: {fmt(r['error'])}.")
    run("B1c insert duplicate {key:1}", "pymongo: db['pu_exists'].insert_one({'key': 1})  [mongosh: db.pu_exists.insertOne({key:1})]",
        lambda: ins(c1, {"key": 1}), "DUPLICATE ACCEPTED: uniqueness is not enforced for documents inside the filter.",
        lambda r: f"Duplicate rejected by the driver as {r['error']['exception']} with {fmt(r['error'])}.")
    run("B1c-r raw insert command reply for duplicate {key:1}",
        "pymongo: db.command('insert', 'pu_exists', documents=[{'_id': ObjectId(), 'key': 1}])  [mongosh: db.runCommand({insert:'pu_exists', documents:[{key:1}]})]",
        lambda: raw_insert(c1, {"key": 1}), lambda r: raw_reading(r),
        lambda r: f"Insert command itself failed: {fmt(r['error'])}.")
    run("B1d insert doc without key {other:1}", "pymongo: db['pu_exists'].insert_one({'other': 1})  [mongosh: db.pu_exists.insertOne({other:1})]",
        lambda: ins(c1, {"other": 1}), "Document without the key accepted (outside the partial filter).",
        lambda r: f"Document without the key rejected: {fmt(r['error'])}.")
    run("B1e insert second doc without key {other:2}", "pymongo: db['pu_exists'].insert_one({'other': 2})  [mongosh: db.pu_exists.insertOne({other:2})]",
        lambda: ins(c1, {"other": 2}),
        "Second keyless document accepted: documents missing the key are not indexed, so they are not duplicate nulls.",
        lambda r: f"Second keyless document rejected with {fmt(r['error'])}: missing key treated as a duplicate null despite the filter.")
    run("B1f insert {key:null}", "pymongo: db['pu_exists'].insert_one({'key': None})  [mongosh: db.pu_exists.insertOne({key:null})]",
        lambda: ins(c1, {"key": None}), "First explicit null accepted.",
        lambda r: f"First explicit null rejected: {fmt(r['error'])}.")
    run("B1g insert second {key:null}", "pymongo: db['pu_exists'].insert_one({'key': None})  [mongosh: db.pu_exists.insertOne({key:null})]",
        lambda: ins(c1, {"key": None}),
        "Second explicit null ACCEPTED: the $exists:true filter does not index null (MongoDB's $exists:true matches null, so it would reject this).",
        lambda r: f"Second explicit null rejected with {fmt(r['error'])}: null is inside the $exists:true filter, as in MongoDB.")
    run("B1h count docs", "pymongo: db['pu_exists'].count_documents({})  [mongosh: db.pu_exists.countDocuments({})]",
        lambda: count(c1), lambda r: f"{r['result']['count']} documents stored.")
    run("B1i update {other:1} -> $set {key:1} (move into filter, collides)",
        "pymongo: db['pu_exists'].update_one({'other': 1}, {'$set': {'key': 1}})  [mongosh: db.pu_exists.updateOne({other:1}, {$set:{key:1}})]",
        lambda: db[c1].update_one({"other": 1}, {"$set": {"key": 1}}).raw_result,
        lambda r: f"UPDATE APPLIED ({json.dumps(r['result'])}): moving a document into the filter with a colliding value was not blocked.",
        lambda r: f"Update rejected by the driver as {r['error']['exception']} with {fmt(r['error'])}: uniqueness is enforced when an update brings a document into the filter.")

# B2: { key: { $gt: 0 } }
c2 = "pu_gt"
db.command("create", c2)
okB2, rB2 = run(
    "B2 createIndexes unique + partialFilterExpression {key:{$gt:0}}",
    "pymongo: db.command('create', 'pu_gt'); db.command('createIndexes', 'pu_gt', indexes=[{'key': {'key': 1}, 'name': 'uq_key_gt0', "
    "'unique': True, 'partialFilterExpression': {'key': {'$gt': 0}}}])  [mongosh: db.pu_gt.createIndex({key:1}, {unique:true, "
    "partialFilterExpression:{key:{$gt:0}}, name:'uq_key_gt0'})]",
    lambda: cidx(c2, {"key": {"key": 1}, "name": "uq_key_gt0", "unique": True, "partialFilterExpression": {"key": {"$gt": 0}}}),
    lambda r: (f"Accepted: numIndexesBefore={shard(r).get('numIndexesBefore')} numIndexesAfter={shard(r).get('numIndexesAfter')} "
               f"ok={r['result'].get('ok')} (the gateway nests the per-shard result under raw.defaultShard)."),
    lambda r: f"Rejected: {fmt(r['error'])}.")
if okB2:
    run("B2a listIndexes", "pymongo: list(db['pu_gt'].list_indexes())  [mongosh: db.pu_gt.getIndexes()]",
        lambda: list_indexes(c2),
        lambda r: f"Index stored as {json.dumps([i for i in r['result'] if i.get('name') == 'uq_key_gt0'])}.")
    run("B2b insert {key:5}", "pymongo: db['pu_gt'].insert_one({'key': 5})  [mongosh: db.pu_gt.insertOne({key:5})]",
        lambda: ins(c2, {"key": 5}), "First positive key accepted.",
        lambda r: f"First positive key rejected: {fmt(r['error'])}.")
    run("B2c insert duplicate {key:5}", "pymongo: db['pu_gt'].insert_one({'key': 5})  [mongosh: db.pu_gt.insertOne({key:5})]",
        lambda: ins(c2, {"key": 5}), "DUPLICATE ACCEPTED: uniqueness is not enforced inside the filter.",
        lambda r: f"Duplicate rejected by the driver as {r['error']['exception']} with {fmt(r['error'])}.")
    run("B2c-r raw insert command reply for duplicate {key:5}",
        "pymongo: db.command('insert', 'pu_gt', documents=[{'_id': ObjectId(), 'key': 5}])  [mongosh: db.runCommand({insert:'pu_gt', documents:[{key:5}]})]",
        lambda: raw_insert(c2, {"key": 5}), lambda r: raw_reading(r),
        lambda r: f"Insert command itself failed: {fmt(r['error'])}.")
    run("B2d insert {key:0}", "pymongo: db['pu_gt'].insert_one({'key': 0})  [mongosh: db.pu_gt.insertOne({key:0})]",
        lambda: ins(c2, {"key": 0}), "key:0 accepted (outside the filter).",
        lambda r: f"key:0 rejected: {fmt(r['error'])}.")
    run("B2e insert duplicate {key:0}", "pymongo: db['pu_gt'].insert_one({'key': 0})  [mongosh: db.pu_gt.insertOne({key:0})]",
        lambda: ins(c2, {"key": 0}), "Duplicate key:0 accepted: documents outside $gt:0 are not uniqueness-checked.",
        lambda r: f"Duplicate key:0 rejected with {fmt(r['error'])}: the filter is not honoured.")
    run("B2f insert {key:-1} twice", "pymongo: db['pu_gt'].insert_many([{'key': -1}, {'key': -1}])  [mongosh: db.pu_gt.insertMany([{key:-1},{key:-1}])]",
        lambda: ins_many(c2, [{"key": -1}, {"key": -1}]), "Two key:-1 documents accepted: negatives are outside the filter.",
        lambda r: f"Negative duplicates rejected: {fmt(r['error'])}.")
    run("B2g insert two docs without key", "pymongo: db['pu_gt'].insert_many([{'other': 1}, {'other': 2}])  [mongosh: db.pu_gt.insertMany([{other:1},{other:2}])]",
        lambda: ins_many(c2, [{"other": 1}, {"other": 2}]), "Two keyless documents accepted: a missing key is outside the filter.",
        lambda r: f"Keyless duplicates rejected: {fmt(r['error'])}.")
    run("B2h insert {key:'str'} twice", "pymongo: db['pu_gt'].insert_many([{'key': 's'}, {'key': 's'}])  [mongosh: db.pu_gt.insertMany([{key:'s'},{key:'s'}])]",
        lambda: ins_many(c2, [{"key": "s"}, {"key": "s"}]),
        "Two string keys accepted: strings do not satisfy the numeric $gt:0 (type-bracketed comparison).",
        lambda r: f"String duplicates rejected with {fmt(r['error'])}: strings are inside the $gt:0 filter on this engine.")
    run("B2i update {key:0} -> {key:5} (move into filter, collides)",
        "pymongo: db['pu_gt'].update_one({'key': 0}, {'$set': {'key': 5}})  [mongosh: db.pu_gt.updateOne({key:0}, {$set:{key:5}})]",
        lambda: db[c2].update_one({"key": 0}, {"$set": {"key": 5}}).raw_result,
        lambda r: f"UPDATE APPLIED ({json.dumps(r['result'])}): moving a document into the filter with a colliding value was not blocked.",
        lambda r: f"Update rejected by the driver as {r['error']['exception']} with {fmt(r['error'])}: uniqueness is enforced when an update brings a document into the filter.")
    run("B2i-r raw update command reply for the colliding update",
        "pymongo: db.command('update', 'pu_gt', updates=[{'q': {'key': 0}, 'u': {'$set': {'key': 5}}}])  [mongosh: db.runCommand({update:'pu_gt', updates:[{q:{key:0}, u:{$set:{key:5}}}]})]",
        lambda: db.command("update", c2, updates=[{"q": {"key": 0}, "u": {"$set": {"key": 5}}}]),
        lambda r: raw_reading(r), lambda r: f"Update command itself failed: {fmt(r['error'])}.")
    run("B2j count docs", "pymongo: db['pu_gt'].count_documents({})  [mongosh: db.pu_gt.countDocuments({})]",
        lambda: count(c2), lambda r: f"{r['result']['count']} documents stored.")
    run("B2k insert {key:5.0} (double equal to the stored int 5)",
        "pymongo: db['pu_gt'].insert_one({'key': 5.0})  [mongosh: db.pu_gt.insertOne({key:5.0})]",
        lambda: ins(c2, {"key": 5.0}),
        "DOUBLE 5.0 ACCEPTED next to int 5: the unique index treats numerically equal values of different BSON types as distinct, unlike MongoDB.",
        lambda r: f"Double 5.0 rejected with {fmt(r['error'])}: numerically equal int and double collide, as in MongoDB.")
    run("B2l insert {key:NumberLong(5)} (int64 equal to the stored int 5)",
        "pymongo: db['pu_gt'].insert_one({'key': Int64(5)})  [mongosh: db.pu_gt.insertOne({key:NumberLong(5)})]",
        lambda: ins(c2, {"key": Int64(5)}),
        "INT64 5 ACCEPTED next to int 5: the unique index treats numerically equal values of different BSON types as distinct, unlike MongoDB.",
        lambda r: f"Int64 5 rejected with {fmt(r['error'])}: numerically equal int32 and int64 collide, as in MongoDB.")
    run("B2m count docs after numeric-type probes", "pymongo: db['pu_gt'].count_documents({})",
        lambda: count(c2), lambda r: f"{r['result']['count']} documents stored after the numeric-type probes.")

# B3/B4 extras on pu_extra: $exists:false, sparse + partialFilterExpression
c3 = "pu_extra"
db.command("create", c3)
run("B3 createIndexes unique + partialFilterExpression {key:{$exists:false}}",
    "pymongo: db.command('create', 'pu_extra'); db.command('createIndexes', 'pu_extra', indexes=[{'key': {'key': 1}, 'name': 'uq_key_notexists', "
    "'unique': True, 'partialFilterExpression': {'key': {'$exists': False}}}])  [mongosh: db.pu_extra.createIndex({key:1}, {unique:true, "
    "partialFilterExpression:{key:{$exists:false}}, name:'uq_key_notexists'})]",
    lambda: cidx(c3, {"key": {"key": 1}, "name": "uq_key_notexists", "unique": True, "partialFilterExpression": {"key": {"$exists": False}}}),
    "Accepted $exists:false in a unique partial filter (contradicts the engine-source reading).",
    lambda r: f"Rejected: {fmt(r['error'])}.")
run("B3b createIndexes NON-unique + partialFilterExpression {key:{$exists:false}}",
    "pymongo: db.command('createIndexes', 'pu_extra', indexes=[{'key': {'key': 1}, 'name': 'ix_key_notexists', "
    "'partialFilterExpression': {'key': {'$exists': False}}}])  [mongosh: db.pu_extra.createIndex({key:1}, {partialFilterExpression:{key:{$exists:false}}, name:'ix_key_notexists'})]",
    lambda: cidx(c3, {"key": {"key": 1}, "name": "ix_key_notexists", "partialFilterExpression": {"key": {"$exists": False}}}),
    "Accepted $exists:false in a non-unique partial filter, so the restriction is specific to unique indexes.",
    lambda r: f"Rejected for a non-unique index too, so the restriction applies to every partial filter: {fmt(r['error'])}.")
run("B4 createIndexes unique + sparse + partialFilterExpression",
    "pymongo: db.command('createIndexes', 'pu_extra', indexes=[{'key': {'key2': 1}, 'name': 'uq_sparse_pfe', 'unique': True, 'sparse': True, "
    "'partialFilterExpression': {'key2': {'$gt': 0}}}])  [mongosh: db.pu_extra.createIndex({key2:1}, {unique:true, sparse:true, "
    "partialFilterExpression:{key2:{$gt:0}}, name:'uq_sparse_pfe'})]",
    lambda: cidx(c3, {"key": {"key2": 1}, "name": "uq_sparse_pfe", "unique": True, "sparse": True, "partialFilterExpression": {"key2": {"$gt": 0}}}),
    "Accepted the sparse + partialFilterExpression mix.",
    lambda r: f"Rejected: {fmt(r['error'])}.")
run("B4b createIndexes NON-unique + sparse + partialFilterExpression",
    "pymongo: db.command('createIndexes', 'pu_extra', indexes=[{'key': {'key2': 1}, 'name': 'ix_sparse_pfe', 'sparse': True, "
    "'partialFilterExpression': {'key2': {'$gt': 0}}}])  [mongosh: db.pu_extra.createIndex({key2:1}, {sparse:true, partialFilterExpression:{key2:{$gt:0}}, name:'ix_sparse_pfe'})]",
    lambda: cidx(c3, {"key": {"key2": 1}, "name": "ix_sparse_pfe", "sparse": True, "partialFilterExpression": {"key2": {"$gt": 0}}}),
    "Accepted the sparse + partialFilterExpression mix for a non-unique index.",
    lambda r: f"Rejected for a non-unique index too: {fmt(r['error'])}.")
run("B4c createIndexes unique + sparse:false + partialFilterExpression",
    "pymongo: db.command('createIndexes', 'pu_extra', indexes=[{'key': {'key3': 1}, 'name': 'uq_sparsefalse_pfe', 'unique': True, 'sparse': False, "
    "'partialFilterExpression': {'key3': {'$gt': 0}}}]); then list(db['pu_extra'].list_indexes())  [mongosh: db.pu_extra.createIndex({key3:1}, "
    "{unique:true, sparse:false, partialFilterExpression:{key3:{$gt:0}}, name:'uq_sparsefalse_pfe'})]",
    lambda: cidx(c3, {"key": {"key3": 1}, "name": "uq_sparsefalse_pfe", "unique": True, "sparse": False, "partialFilterExpression": {"key3": {"$gt": 0}}}),
    lambda r: (f"Accepted sparse:false next to partialFilterExpression, so only sparse:true conflicts; the stored spec is "
               f"{json.dumps([i for i in (r.get('post_check') or []) if i.get('name') == 'uq_sparsefalse_pfe'])}."),
    lambda r: f"Rejected even with sparse:false, so the mere presence of the sparse option conflicts: {fmt(r['error'])}.",
    post=lambda: list_indexes(c3))

# B5: sparse unique without a partial filter (how null and missing are treated, for contrast with B1)
c5 = "pu_sparse"
db.command("create", c5)
okB5, _ = run(
    "B5 createIndexes unique + sparse (no partialFilterExpression)",
    "pymongo: db.command('create', 'pu_sparse'); db.command('createIndexes', 'pu_sparse', indexes=[{'key': {'key': 1}, 'name': 'uq_key_sparse', "
    "'unique': True, 'sparse': True}])  [mongosh: db.pu_sparse.createIndex({key:1}, {unique:true, sparse:true, name:'uq_key_sparse'})]",
    lambda: cidx(c5, {"key": {"key": 1}, "name": "uq_key_sparse", "unique": True, "sparse": True}),
    lambda r: f"Accepted: numIndexesBefore={shard(r).get('numIndexesBefore')} numIndexesAfter={shard(r).get('numIndexesAfter')} ok={r['result'].get('ok')}.",
    lambda r: f"Rejected: {fmt(r['error'])}.")
if okB5:
    run("B5a listIndexes", "pymongo: list(db['pu_sparse'].list_indexes())  [mongosh: db.pu_sparse.getIndexes()]",
        lambda: list_indexes(c5),
        lambda r: f"Index stored as {json.dumps([i for i in r['result'] if i.get('name') == 'uq_key_sparse'])}.")
    run("B5b insert two docs without key", "pymongo: db['pu_sparse'].insert_many([{'other': 1}, {'other': 2}])  [mongosh: db.pu_sparse.insertMany([{other:1},{other:2}])]",
        lambda: ins_many(c5, [{"other": 1}, {"other": 2}]),
        "Two keyless documents accepted: the sparse index skips documents that lack the field.",
        lambda r: f"Keyless documents rejected under a sparse unique index: {fmt(r['error'])}.")
    run("B5c insert {key:null}", "pymongo: db['pu_sparse'].insert_one({'key': None})  [mongosh: db.pu_sparse.insertOne({key:null})]",
        lambda: ins(c5, {"key": None}), "First explicit null accepted.",
        lambda r: f"First explicit null rejected: {fmt(r['error'])}.")
    run("B5d insert second {key:null}", "pymongo: db['pu_sparse'].insert_one({'key': None})  [mongosh: db.pu_sparse.insertOne({key:null})]",
        lambda: ins(c5, {"key": None}),
        "Second explicit null ACCEPTED: this sparse index skips explicit nulls (MongoDB's sparse indexes index null, so it would reject this).",
        lambda r: f"Second explicit null rejected with {fmt(r['error'])}: the sparse index includes explicit null, as in MongoDB.")
    run("B5e insert {key:1}", "pymongo: db['pu_sparse'].insert_one({'key': 1})  [mongosh: db.pu_sparse.insertOne({key:1})]",
        lambda: ins(c5, {"key": 1}), "Keyed document accepted.",
        lambda r: f"Keyed document rejected: {fmt(r['error'])}.")
    run("B5f insert duplicate {key:1}", "pymongo: db['pu_sparse'].insert_one({'key': 1})  [mongosh: db.pu_sparse.insertOne({key:1})]",
        lambda: ins(c5, {"key": 1}), "DUPLICATE ACCEPTED under a sparse unique index.",
        lambda r: f"Duplicate rejected by the driver as {r['error']['exception']} with {fmt(r['error'])}.")
    run("B5g count docs", "pymongo: db['pu_sparse'].count_documents({})  [mongosh: db.pu_sparse.countDocuments({})]",
        lambda: count(c5), lambda r: f"{r['result']['count']} documents stored.")

# ----------------------------------------------------------------------------- teardown
run("Z1 drop t_schema (teardown)",
    "pymongo: client['t_schema'].command('dropDatabase')  [mongosh: db.getSiblingDB('t_schema').dropDatabase()]",
    lambda: db.command("dropDatabase"),
    lambda r: f"dropDatabase returned {json.dumps(r['result'])}.",
    lambda r: f"Teardown drop failed: {fmt(r['error'])}.")
run("Z2 verify t_schema is gone",
    "pymongo: 't_schema' in client.list_database_names()  [mongosh: db.adminCommand({listDatabases:1, nameOnly:true})]",
    lambda: {"t_schema_present": DB in client.list_database_names()},
    lambda r: ("t_schema no longer appears in listDatabases." if not r["result"]["t_schema_present"]
               else "t_schema STILL appears in listDatabases after the drop."))

# ============================================================================= comparison with 0.117
METHOD_NOTES = {
    "drop t_schema (setup)": ("Methodology, not engine: the 0.117 script recorded a placeholder {ok: 1} because PyMongo's "
                              "drop_database() returns None; this run records the raw dropDatabase reply."),
}


def strip_ids(x):
    if isinstance(x, dict):
        if set(x.keys()) == {"$oid"}:
            return "<ObjectId>"
        return {k: strip_ids(v) for k, v in x.items() if k not in ("inserted_id", "ms")}
    if isinstance(x, list):
        return [strip_ids(v) for v in x]
    return x


def norm(resp):
    if not isinstance(resp, dict):
        return {"outcome": "info", "value": resp}
    if "error" in resp:
        e = resp["error"]
        return OrderedDict(outcome="error", code=e.get("code"), codeName=e.get("codeName"),
                           errmsg=re.sub(r"\[ActivityId=[^\]]*\]\s*", "", (e.get("errmsg") or "")).strip(),
                           errorLabels=e.get("errorLabels") or [],
                           errInfo_present=bool(e.get("errInfo_present")) or ("errInfo" in e))
    if "result" in resp:
        return OrderedDict(outcome="ok", result=strip_ids(resp["result"]))
    return OrderedDict(outcome="info", value=strip_ids(resp))


comparison = OrderedDict()
try:
    prior = json.load(open(PRIOR_REPORT))
    prior_steps = OrderedDict((s["step"], s) for s in prior.get("steps", []))
    same, diff, missing = [], [], []
    for label, ps in prior_steps.items():
        ns = S.get(label)
        if ns is None:
            missing.append(label)
            continue
        a, b = norm(ps["response"]), norm(ns["response"])
        entry = OrderedDict(step=label, engine_0117=a, engine_120=b)
        if label in METHOD_NOTES:
            entry["note"] = METHOD_NOTES[label]
        (same if a == b else diff).append(entry)
    new_steps = [lbl for lbl in S if lbl not in prior_steps]
    comparison["prior_report"] = PRIOR_REPORT
    comparison["prior_engine"] = prior.get("engine_version")
    eng = [d for d in diff if "note" not in d]
    meth = [d for d in diff if "note" in d]
    comparison["method"] = ("Each 0.117 step is matched to the 1.2.0 step with the same label; responses are compared on outcome "
                            "(result or error), code, codeName, errmsg (ActivityId removed), errorLabels, errInfo presence and the "
                            "result body with ObjectIds, inserted_id and timings removed.")
    comparison["summary"] = (f"{len(prior_steps)} steps in the 0.117 report: {len(same)} reproduced identically on 1.2.0, "
                             f"{len(meth)} differ only because the recording method changed, {len(eng)} differ in engine "
                             f"behaviour, {len(missing)} not rerun; {len(new_steps)} steps are new in this rerun.")
    comparison["engine_differences"] = eng
    comparison["methodology_differences"] = meth
    comparison["identical_steps"] = [e["step"] for e in same]
    comparison["not_rerun"] = missing
    comparison["new_steps_in_rerun"] = new_steps
except Exception as e:  # noqa: BLE001
    comparison["error"] = f"could not load or compare the 0.117 report: {e!r}"


# ============================================================================= conclusions (data-driven)
def st(label):
    return S.get(label) or {}


def res(label):
    return st(label).get("response") or {}


def okd(label):
    return "result" in res(label)


def e_of(label):
    return res(label).get("error") or {}


def short(label):
    r = res(label)
    if not r:
        return "not run"
    if "error" in r:
        e = r["error"]
        msg = (e.get("errmsg") or "").strip().replace("\n", " ")
        cn = e.get("codeName") or "(no codeName)"
        tail = " with errInfo" if e.get("errInfo_present") else " without errInfo"
        return f"rejected {e.get('code')} {cn} \"{msg}\"{tail}"
    return "accepted"


def write_errors_of(step):
    r = (step.get("response") or {}).get("result")
    return (r.get("writeErrors") or []) if isinstance(r, dict) else []


def count_of(label):
    return (res(label).get("result") or {}).get("count")


L_A0 = "A0 create collection with baseline validator (bsonType/required/properties)"
L_A0B = "A0b listCollections options for v_baseline"
L_A0C = "A0c insert violating doc into v_baseline (missing required name)"
L_A0CR = "A0c-r raw insert command reply for violating doc (missing required name)"
L_A0D = "A0d insert violating doc with bypassDocumentValidation"
L_A0F = "A0f updateOne $set name to a number (violates)"
L_A0G = "A0g findOneAndUpdate $set name to a number (violates)"
L_A0H = "A0h create collection with baseline validator and validationAction 'warn'"
L_A0I = "A0i insert violating doc into validationAction 'warn' collection"
L_B1 = "B1 createIndexes unique + partialFilterExpression {key:{$exists:true}}"
L_B1C = "B1c insert duplicate {key:1}"
L_B1CR = "B1c-r raw insert command reply for duplicate {key:1}"
L_B1D = "B1d insert doc without key {other:1}"
L_B1E = "B1e insert second doc without key {other:2}"
L_B1F = "B1f insert {key:null}"
L_B1G = "B1g insert second {key:null}"
L_B1H = "B1h count docs"
L_B1I = "B1i update {other:1} -> $set {key:1} (move into filter, collides)"
L_B2 = "B2 createIndexes unique + partialFilterExpression {key:{$gt:0}}"
L_B2C = "B2c insert duplicate {key:5}"
L_B2E = "B2e insert duplicate {key:0}"
L_B2F = "B2f insert {key:-1} twice"
L_B2G = "B2g insert two docs without key"
L_B2H = "B2h insert {key:'str'} twice"
L_B2I = "B2i update {key:0} -> {key:5} (move into filter, collides)"
L_B2J = "B2j count docs"
L_B2K = "B2k insert {key:5.0} (double equal to the stored int 5)"
L_B2L = "B2l insert {key:NumberLong(5)} (int64 equal to the stored int 5)"
L_B3 = "B3 createIndexes unique + partialFilterExpression {key:{$exists:false}}"
L_B3B = "B3b createIndexes NON-unique + partialFilterExpression {key:{$exists:false}}"
L_B4 = "B4 createIndexes unique + sparse + partialFilterExpression"
L_B4B = "B4b createIndexes NON-unique + sparse + partialFilterExpression"
L_B4C = "B4c createIndexes unique + sparse:false + partialFilterExpression"
L_B5 = "B5 createIndexes unique + sparse (no partialFilterExpression)"
L_B5B = "B5b insert two docs without key"
L_B5D = "B5d insert second {key:null}"
L_B5F = "B5f insert duplicate {key:1}"

conclusions = []
bl_opts = res(L_A0B).get("result") or {}
conclusions.append(OrderedDict(
    question=("Are collection validators (validator/validationLevel/validationAction) enabled on documentdb-local 1.2.0, "
              "or gated behind 'validator not supported yet'?"),
    answer=(f"{'Enabled' if okd(L_A0) else 'Gated'} on this build. Baseline create: {short(L_A0)}; listCollections shows validationLevel "
            f"'{bl_opts.get('validationLevel')}' and validationAction '{bl_opts.get('validationAction')}'. Violating insert: {short(L_A0C)}. "
            f"bypassDocumentValidation:true: {short(L_A0D)}. Violating updateOne: {short(L_A0F)}. Violating findOneAndUpdate: {short(L_A0G)}. "
            f"validationAction 'warn': create {short(L_A0H)}, violating insert {short(L_A0I)}."),
    confidence="observed"))

acc_c = [k for k, r in KW.items() if r["create"] == "accepted"]
rej_c = [k for k, r in KW.items() if r["create"] != "accepted"]
acc_m = [k for k, r in KW.items() if r["collMod"] == "accepted"]
rej_m = [k for k, r in KW.items() if r["collMod"] != "accepted"]
enf_c = [k for k, r in KW.items() if str(r.get("violating_insert_after_create", "")).startswith("rejected")]
nenf_c = [k for k, r in KW.items() if r.get("violating_insert_after_create") == "accepted"]
enf_m = [k for k, r in KW.items() if str(r.get("violating_insert_after_collMod", "")).startswith("rejected")]
nenf_m = [k for k, r in KW.items() if r.get("violating_insert_after_collMod") == "accepted"]
rej_msgs = sorted({r["create"] for r in KW.values() if r["create"] != "accepted"})
kw_eng_diffs = [d["step"] for d in (comparison.get("engine_differences") or []) if d["step"].startswith(("A1.", "A2.", "A3.", "A4."))]
if "error" in comparison:
    kw_vs_0117 = f"Comparison with 0.117 unavailable: {comparison['error']}."
elif kw_eng_diffs:
    kw_vs_0117 = f"Keyword steps that changed since 0.117: {kw_eng_diffs}."
else:
    kw_vs_0117 = ("Every create, collMod and insert step shared with the 0.117 run returned the same outcome, code and message, so none "
                  "of the keywords 0.117 rejected became available in 1.2.0.")
if set(acc_c) == {"enum", "oneOf"} and set(acc_m) == {"enum", "oneOf"}:
    kw_vs_source = ("This matches the engine-source reading in DECISIONS.md topic 10: enum and oneOf parse, the other keywords fall "
                    "through to 'Unknown $jsonSchema keyword'.")
else:
    kw_vs_source = "This differs from the engine-source reading in DECISIONS.md topic 10, which expects exactly enum and oneOf to parse."
probe_note = (" The _id-counting probes for minProperties and maxProperties did not run because both keywords are rejected."
              if all(KW.get(k, {}).get("id_counting_probes") for k in ("minProperties", "maxProperties")) else "")
conclusions.append(OrderedDict(
    question="Which $jsonSchema keywords does engine 1.2.0 accept via create and via collMod, and are they enforced on insert?",
    answer=(f"create accepted: {acc_c or 'none'}; create rejected: {rej_c or 'none'}. collMod accepted: {acc_m or 'none'}; collMod rejected: "
            f"{rej_m or 'none'}. Violating insert rejected after create: {enf_c or 'none'}; accepted after create (parsed, not enforced): "
            f"{nenf_c or 'none'}. Violating insert rejected after collMod: {enf_m or 'none'}; accepted after collMod: {nenf_m or 'none'}. "
            f"For rejected keywords no validator can be installed, so the violating-insert check does not apply. Rejection replies: "
            f"{rej_msgs or 'none'}. {kw_vs_0117} {kw_vs_source}{probe_note} Per-keyword detail is in keyword_matrix."),
    confidence="observed"))

w121 = e_of(L_A0C)
raw121 = res(L_A0CR).get("result") or {}
we121 = (raw121.get("writeErrors") or [{}])[0]
steps_121 = [s["step"] for s in steps
             if ((s.get("response") or {}).get("error") or {}).get("code") == 121
             or any(w.get("code") == 121 for w in write_errors_of(s))]
steps_121_errinfo = [s["step"] for s in steps
                     if ((s.get("response") or {}).get("error") or {}).get("errInfo_present")
                     or any("errInfo" in w for w in write_errors_of(s))]
errinfo_txt = (" (" + ", ".join(steps_121_errinfo) + ")") if steps_121_errinfo else ""
upd = e_of(L_A0F)
fam = e_of(L_A0G)
upd_txt = (f" updateOne raises {upd.get('exception')} with the same write-error fields {upd.get('writeError_fields')}." if upd else "")
fam_txt = (f" findOneAndUpdate instead gets a command-level error (ok: {(fam.get('raw') or {}).get('ok')}) with code {fam.get('code')}, "
           f"codeName {fam.get('codeName') or 'absent'} and errmsg \"{fam.get('errmsg')}\", "
           f"{'with' if fam.get('errInfo_present') else 'also without'} errInfo." if fam else "")
conclusions.append(OrderedDict(
    question="What does a $jsonSchema validation failure look like on 1.2.0 (code, codeName, errmsg, errInfo, errorLabels)?",
    answer=(f"insert_one raises {w121.get('exception')} with code {w121.get('code')}, codeName {w121.get('codeName') or 'absent'}, "
            f"errmsg \"{w121.get('errmsg')}\" and write-error fields {w121.get('writeError_fields')}; the raw insert reply is "
            f"ok={raw121.get('ok')} n={raw121.get('n')} with writeErrors[0] fields {sorted(we121.keys())}.{upd_txt}{fam_txt} "
            f"{len(steps_121)} steps returned code 121 and {len(steps_121_errinfo)} of them carried errInfo{errinfo_txt}. "
            f"errorLabels: {w121.get('errorLabels') or 'none'}."),
    confidence="observed"))

raw11000 = res(L_B1CR).get("result") or {}
we11000 = (raw11000.get("writeErrors") or [{}])[0]
kp_txt = ("no keyPattern or keyValue" if not ({"keyPattern", "keyValue"} & set(we11000.keys()))
          else f"keyPattern {we11000.get('keyPattern')} and keyValue {we11000.get('keyValue')}")
conclusions.append(OrderedDict(
    question="Is a unique index with partialFilterExpression { key: { $exists: true } } accepted and enforced on 1.2.0?",
    answer=(f"createIndexes: {short(L_B1)}. Duplicate {{key:1}}: {short(L_B1C)}; raw reply writeErrors[0] fields {sorted(we11000.keys())} "
            f"({kp_txt}). "
            f"Two documents without the key: {short(L_B1D)} and {short(L_B1E)}. Two explicit nulls: first {short(L_B1F)}, second "
            f"{short(L_B1G)}. Update that moves a keyless document to key:1: {short(L_B1I)}. Documents stored: {count_of(L_B1H)}."),
    confidence="observed"))
conclusions.append(OrderedDict(
    question="Is a unique index with partialFilterExpression { key: { $gt: 0 } } accepted and enforced on 1.2.0?",
    answer=(f"createIndexes: {short(L_B2)}. Duplicate {{key:5}}: {short(L_B2C)}. Duplicates outside the filter: key:0 {short(L_B2E)}, "
            f"key:-1 x2 {short(L_B2F)}, keyless x2 {short(L_B2G)}, key:'s' x2 {short(L_B2H)}. Update moving key:0 to key:5: {short(L_B2I)}. "
            f"Documents stored: {count_of(L_B2J)}. Numerically equal duplicates of the stored int 5: double 5.0 {short(L_B2K)}, "
            f"NumberLong(5) {short(L_B2L)}."),
    confidence="observed"))
conclusions.append(OrderedDict(
    question="Are $exists:false partial filters and sparse + partialFilterExpression combinations accepted on 1.2.0?",
    answer=(f"Unique + $exists:false: {short(L_B3)}. Non-unique + $exists:false: {short(L_B3B)}. Unique + sparse:true + partial filter: "
            f"{short(L_B4)}. Non-unique + sparse:true + partial filter: {short(L_B4B)}. Unique + sparse:false + partial filter: {short(L_B4C)}."),
    confidence="observed"))
conclusions.append(OrderedDict(
    question="For contrast, how does a sparse unique index without a partial filter treat missing keys, explicit nulls and duplicates?",
    answer=(f"createIndexes: {short(L_B5)}. Two keyless documents: {short(L_B5B)}. Second explicit null: {short(L_B5D)}. "
            f"Duplicate key:1: {short(L_B5F)}."),
    confidence="observed"))


def nshort(n):
    if n.get("outcome") == "error":
        return f"error {n.get('code')} {n.get('codeName') or '(no codeName)'} \"{n.get('errmsg')}\""
    if n.get("outcome") == "ok":
        return "ok " + json.dumps(n.get("result"))[:200]
    return json.dumps(n.get("value"))[:200]


def dtxt(lst):
    return "; ".join(
        f"[{d['step']}] 0.117: {nshort(d['engine_0117'])} -> 1.2.0: {nshort(d['engine_120'])}" + (f" ({d['note']})" if d.get("note") else "")
        for d in lst)


eng_d = comparison.get("engine_differences") or []
meth_d = comparison.get("methodology_differences") or []
if "error" in comparison:
    holds = ""
elif eng_d:
    holds = " The 0.117 summary in ENGINE-TESTS.md (topic 10 section) needs the engine differences above applied before it describes 1.2.0."
else:
    holds = " The 0.117 summary in ENGINE-TESTS.md (topic 10 section) therefore still describes engine 1.2.0."
conclusions.append(OrderedDict(
    question="What changed between engine 0.117 and engine 1.2.0 for this test?",
    answer=(f"{comparison.get('summary', comparison.get('error'))} Engine differences: {dtxt(eng_d) or 'none'}. "
            f"Recording-method differences: {dtxt(meth_d) or 'none'}.{holds}"),
    confidence="observed"))
conclusions.append(OrderedDict(
    question="What did the steps added in this rerun (not in the 0.117 run) show?",
    answer=(f"collMod-installed validators are enforced: enum {KW.get('enum', {}).get('violating_insert_after_collMod')}; oneOf "
            f"{KW.get('oneOf', {}).get('violating_insert_after_collMod')}. Updates are validated: updateOne {short(L_A0F)}; findOneAndUpdate "
            f"{short(L_A0G)}. validationAction 'warn': violating insert {short(L_A0I)}. additionalProperties with _id listed in properties: "
            f"create {KW.get('additionalProperties+_id', {}).get('create')}; schema-form dependencies: create "
            f"{KW.get('dependencies(schema)', {}).get('create')}. Duplicate-key write errors carry only {sorted(we11000.keys())}. Against a "
            f"stored int 5 in a unique index, double 5.0 is {short(L_B2K)} and NumberLong(5) is {short(L_B2L)}. Non-unique partial index "
            f"with $exists:false: {short(L_B3B)}. Non-unique sparse + partial filter: {short(L_B4B)}. Unique sparse:false + partial filter: "
            f"{short(L_B4C)}. Sparse unique index without a filter: two keyless documents {short(L_B5B)}, second explicit null "
            f"{short(L_B5D)}."),
    confidence="observed"))
conclusions.append(OrderedDict(
    question="Does any of this prove managed Azure DocumentDB behaviour?",
    answer=(f"No. Every fact here comes from documentdb-local image {engine_version['container_image']} (OCI version "
            f"{engine_version['image_version_label']}, revision {(engine_version['image_revision'] or '')[:8]}, built "
            f"{engine_version['image_created']}, documentdb extension {engine_version['documentdb_extension_default_version']}, "
            f"{engine_version['postgres']}), whose gateway reports buildInfo.version {bi.get('version')} and maxWireVersion "
            f"{hello.get('maxWireVersion')}. Whether the managed service runs this engine build, has schema validation enabled, and "
            f"returns the same error shapes is not shown by this test (DECISIONS.md topic 10, open item 1)."),
    confidence="inferred"))

# ============================================================================= report
report = OrderedDict()
report["test"] = TEST_ID
report["stage"] = "ENGINE 1.2.0 RERUN (compare with the 0.117 results in findings/phase4/ENGINE-TESTS.md)"
report["database"] = DB
report["target"] = ("documentdb-local container ddb-engine-test, localhost:10260, TLS with a self-signed certificate, "
                    "MongoDB wire protocol, SCRAM-SHA-256 test credentials (not recorded)")
report["engine_version"] = engine_version
report["evidence_scope"] = ("Observed on documentdb-local; evidence about the open-source engine and gateway at the version above "
                            "(image pg17-1.2.0, documentdb extension 1.2-0). It does not prove managed Azure DocumentDB behaviour.")
report["decisions_topic"] = ("findings/phase4/DECISIONS.md, 'Schema validation, TTL, indexing and query behaviour (SME topic 10)': "
                             "settled item 1 ($jsonSchema keyword support), settled item 2 (unique index with partialFilterExpression "
                             "{ $exists: true }), open item 1 (which engine build the managed service runs and how validators are enabled).")
report["run_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
report["script"] = os.path.abspath(__file__)
report["keyword_matrix"] = KW
report["comparison_with_0117"] = comparison
report["conclusions"] = conclusions
report["steps"] = steps
text = redact(json.dumps(report, indent=2, default=str))
for sec in SECRETS:
    assert sec not in text, "secret leaked into report text"
out = os.path.join(HERE, "report.json")
with open(out, "w") as f:
    f.write(text + "\n")
print("REPORT:", out)
print(comparison.get("summary"))
