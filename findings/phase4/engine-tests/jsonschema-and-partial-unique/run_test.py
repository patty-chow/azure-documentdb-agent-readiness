"""Test jsonschema-and-partial-unique against documentdb-local (database t_schema).

Reads LOCAL_URI from ../local.env; never prints or stores the password.
Writes report.json next to this script.
"""
import json, os, re, sys, time
from collections import OrderedDict
from pymongo import MongoClient, errors
from bson import json_util

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", "local.env")
DB = "t_schema"

def load_uri():
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if line.startswith("LOCAL_URI="):
                v = line.split("=", 1)[1].strip()
                return v.strip('"').strip("'")
    raise SystemExit("LOCAL_URI not found")

def redact(s):
    return re.sub(r"(mongodb://[^:/]+:)[^@]+@", r"\1***@", str(s))

def jsonable(x):
    return json.loads(json_util.dumps(x))

def err_info(e):
    info = OrderedDict()
    info["exception"] = type(e).__name__
    details = getattr(e, "details", None)
    code = getattr(e, "code", None)
    if details is None and isinstance(e, errors.BulkWriteError):
        details = e.details
    if isinstance(details, dict):
        we = details.get("writeErrors")
        if we:
            d0 = we[0]
            info["code"] = d0.get("code")
            info["codeName"] = d0.get("codeName")
            info["errmsg"] = d0.get("errmsg")
            if "errInfo" in d0:
                info["errInfo"] = jsonable(d0["errInfo"])
        else:
            info["code"] = details.get("code", code)
            info["codeName"] = details.get("codeName")
            info["errmsg"] = details.get("errmsg")
            if "errInfo" in details:
                info["errInfo"] = jsonable(details["errInfo"])
        info["errorLabels"] = details.get("errorLabels", [])
        info["raw"] = redact(json_util.dumps(details))
    else:
        info["code"] = code
        info["errmsg"] = redact(str(e))
    return info

steps = []
def record(step, command, response, reading):
    steps.append(OrderedDict(step=step, command=command, response=response, reading=reading))
    print(f"[{len(steps):02d}] {step}\n     -> {json.dumps(response)[:400]}\n     {reading}")

def run(step, command_desc, fn, reading_ok, reading_err=None):
    t0 = time.time()
    try:
        r = fn()
        resp = jsonable(r) if r is not None else {"ok": 1}
        record(step, command_desc, {"result": resp, "ms": int((time.time()-t0)*1000)}, reading_ok(resp) if callable(reading_ok) else reading_ok)
        return True, resp
    except Exception as e:
        info = err_info(e)
        info["ms"] = int((time.time()-t0)*1000)
        rd = reading_err(info) if callable(reading_err) else (reading_err or f"Rejected with code {info.get('code')} {info.get('codeName')}: {info.get('errmsg')}")
        record(step, command_desc, {"error": info}, rd)
        return False, info

uri = load_uri()
client = MongoClient(uri, serverSelectionTimeoutMS=15000, socketTimeoutMS=120000)
db = client[DB]

# --- buildInfo ---
bi = client.admin.command("buildInfo")
engine_version = {k: jsonable(bi.get(k)) for k in ("version", "gitVersion", "modules", "versionArray", "maxBsonObjectSize") if k in bi}
record("buildInfo", "db.adminCommand({buildInfo: 1})", engine_version,
       "Version string the gateway reports; all facts below are about the open-source engine/gateway at this version, not the managed service.")
try:
    hello = client.admin.command("hello")
    record("hello", "db.adminCommand({hello: 1})", {k: jsonable(hello.get(k)) for k in ("maxWireVersion","minWireVersion","maxWriteBatchSize","maxBsonObjectSize") if k in hello},
           "Wire-version advertised by the gateway.")
except Exception as e:
    record("hello", "db.adminCommand({hello: 1})", {"error": err_info(e)}, "hello failed.")

# --- clean test db (owned by this test) ---
run("drop t_schema (setup)", f"db.getSiblingDB('{DB}').dropDatabase()", lambda: client.drop_database(DB), "Test database dropped so the run is repeatable.")

# ---------- Part A: $jsonSchema validators ----------
# Baseline validator with only widely-supported keywords, to detect the EnableSchemaValidation gate.
BASELINE = {"$jsonSchema": {"bsonType": "object", "required": ["name"], "properties": {"name": {"bsonType": "string"}}}}

KEYWORDS = OrderedDict([
    ("enum", {"$jsonSchema": {"bsonType": "object", "properties": {"status": {"enum": ["new", "done"]}}}}),
    ("additionalProperties", {"$jsonSchema": {"bsonType": "object", "properties": {"a": {"bsonType": "int"}}, "additionalProperties": False}}),
    ("allOf", {"$jsonSchema": {"allOf": [{"required": ["a"]}, {"required": ["b"]}]}}),
    ("anyOf", {"$jsonSchema": {"anyOf": [{"required": ["a"]}, {"required": ["b"]}]}}),
    ("oneOf", {"$jsonSchema": {"oneOf": [{"required": ["a"]}, {"required": ["b"]}]}}),
    ("not", {"$jsonSchema": {"not": {"required": ["forbidden"]}}}),
    ("patternProperties", {"$jsonSchema": {"patternProperties": {"^x_": {"bsonType": "int"}}}}),
    ("dependencies", {"$jsonSchema": {"dependencies": {"a": ["b"]}}}),
    ("minProperties", {"$jsonSchema": {"minProperties": 2}}),
    ("maxProperties", {"$jsonSchema": {"maxProperties": 2}}),
])
# documents: (valid, violating)
DOCS = {
    "enum": ({"status": "new"}, {"status": "bogus"}),
    "additionalProperties": ({"a": 1}, {"a": 1, "extra": 1}),
    "allOf": ({"a": 1, "b": 1}, {"a": 1}),
    "anyOf": ({"a": 1}, {"c": 1}),
    "oneOf": ({"a": 1}, {"a": 1, "b": 1}),
    "not": ({"ok": 1}, {"forbidden": 1}),
    "patternProperties": ({"x_1": 1}, {"x_1": "str"}),
    "dependencies": ({"a": 1, "b": 1}, {"a": 1}),
    "minProperties": ({"a": 1, "b": 1}, {"a": 1}),
    "maxProperties": ({"a": 1}, {"a": 1, "b": 1, "c": 1}),
}

def create_with_validator(name, validator):
    return db.command("create", name, validator=validator)

def collmod_validator(name, validator):
    return db.command("collMod", name, validator=validator)

def insert(name, doc, bypass=False):
    kwargs = {"bypass_document_validation": True} if bypass else {}
    r = db[name].insert_one(dict(doc), **kwargs)
    return {"acknowledged": r.acknowledged, "inserted_id": r.inserted_id}

def list_validator(name):
    cols = list(db.list_collections(filter={"name": name}))
    return cols[0].get("options", {}) if cols else None

# Baseline: does this build accept any validator at all?
ok_base, resp_base = run("A0 create collection with baseline validator (bsonType/required/properties)",
    f"db.createCollection('v_baseline', {{validator: {json.dumps(BASELINE)}}})",
    lambda: create_with_validator("v_baseline", BASELINE),
    "Collection validators are enabled on this build: create accepted a baseline $jsonSchema.",
    lambda i: f"Collection validators are gated on this build: create returned {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}' even for a baseline $jsonSchema.")
if ok_base:
    run("A0b listCollections options for v_baseline", "db.getCollectionInfos({name:'v_baseline'})[0].options",
        lambda: list_validator("v_baseline"), lambda r: f"Stored options: {json.dumps(r)[:300]}")
    run("A0c insert violating doc into v_baseline (missing required name)", "db.v_baseline.insertOne({x:1})",
        lambda: insert("v_baseline", {"x": 1}),
        "Violating insert was ACCEPTED: validator stored but not enforced.",
        lambda i: f"Violating insert rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
    run("A0d insert violating doc with bypassDocumentValidation", "db.v_baseline.insertOne({x:1}, {bypassDocumentValidation:true})",
        lambda: insert("v_baseline", {"x": 1}, bypass=True),
        "bypassDocumentValidation lets the violating document through.",
        lambda i: f"bypassDocumentValidation did not help: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
else:
    # plain collection then collMod, to see if the gate also covers collMod
    run("A0e create plain collection cm_baseline", "db.createCollection('cm_baseline')", lambda: db.command("create", "cm_baseline"), "Plain collection created.")
    run("A0f collMod baseline validator onto cm_baseline",
        f"db.runCommand({{collMod:'cm_baseline', validator: {json.dumps(BASELINE)}}})",
        lambda: collmod_validator("cm_baseline", BASELINE),
        "collMod accepted a baseline validator even though create rejected one.",
        lambda i: f"collMod also gated: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
    run("A0g validationAction/validationLevel on create", "db.createCollection('v_opts', {validationAction:'warn', validationLevel:'moderate'})",
        lambda: db.command("create", "v_opts", validationAction="warn", validationLevel="moderate"),
        "validationAction/validationLevel accepted without validator.",
        lambda i: f"validationAction/validationLevel rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")

for kw, validator in KEYWORDS.items():
    cname = f"v_{kw}"
    ok, resp = run(f"A1.{kw} create collection with $jsonSchema using {kw}",
        f"db.createCollection('{cname}', {{validator: {json.dumps(validator)}}})",
        lambda: create_with_validator(cname, validator),
        f"create accepted a validator using '{kw}'.",
        lambda i, kw=kw: f"create rejected '{kw}': {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
    valid, bad = DOCS[kw]
    if ok:
        run(f"A2.{kw} insert valid doc", f"db.{cname}.insertOne({json.dumps(valid)})",
            lambda: insert(cname, valid), "Valid document accepted.",
            lambda i, kw=kw: f"Valid document unexpectedly rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
        run(f"A3.{kw} insert violating doc", f"db.{cname}.insertOne({json.dumps(bad)})",
            lambda: insert(cname, bad),
            f"Violating document ACCEPTED: '{kw}' is parsed but not enforced (or validator not applied).",
            lambda i, kw=kw: f"Violating document rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}' -> '{kw}' is enforced.")
    # collMod path, independent of create result
    cm = f"cm_{kw}"
    db.command("create", cm)
    ok2, resp2 = run(f"A4.{kw} collMod validator using {kw} onto plain collection",
        f"db.runCommand({{collMod:'{cm}', validator: {json.dumps(validator)}}})",
        lambda: collmod_validator(cm, validator),
        f"collMod accepted a validator using '{kw}'.",
        lambda i, kw=kw: f"collMod rejected '{kw}': {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
    if ok2 and not ok:
        run(f"A5.{kw} insert violating doc after collMod", f"db.{cm}.insertOne({json.dumps(bad)})",
            lambda: insert(cm, bad), "Violating document ACCEPTED after collMod.",
            lambda i: f"Violating document rejected after collMod: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")

# ---------- Part B: unique partial indexes ----------
def create_index(cname, keys, **opts):
    return db.command("createIndexes", cname, indexes=[dict(key=keys, name=opts.pop("name"), **opts)])

def shard(r):
    return (r.get('raw') or {}).get('defaultShard', r)

def list_indexes(cname):
    return list(db[cname].list_indexes())

# B1: { key: { $exists: true } }
c1 = "pu_exists"
db.command("create", c1)
okB1, _ = run("B1 createIndexes unique + partialFilterExpression {key:{$exists:true}}",
    f"db.{c1}.createIndex({{key:1}}, {{unique:true, partialFilterExpression:{{key:{{$exists:true}}}}, name:'uq_key_exists'}})",
    lambda: create_index(c1, {"key": 1}, name="uq_key_exists", unique=True, partialFilterExpression={"key": {"$exists": True}}),
    lambda r: f"Accepted: numIndexesBefore={shard(r).get('numIndexesBefore')} numIndexesAfter={shard(r).get('numIndexesAfter')} (gateway nests the result under raw.defaultShard).",
    lambda i: f"Rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
if okB1:
    run("B1a listIndexes", f"db.{c1}.getIndexes()", lambda: list_indexes(c1), lambda r: f"Index spec as stored: {json.dumps(r)[:400]}")
    run("B1b insert {key:1}", f"db.{c1}.insertOne({{key:1}})", lambda: insert(c1, {"key": 1}), "First keyed document accepted.")
    run("B1c insert duplicate {key:1}", f"db.{c1}.insertOne({{key:1}})", lambda: insert(c1, {"key": 1}),
        "DUPLICATE ACCEPTED: uniqueness not enforced for indexed docs.",
        lambda i: f"Duplicate rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
    run("B1d insert doc without key {other:1}", f"db.{c1}.insertOne({{other:1}})", lambda: insert(c1, {"other": 1}), "Doc without key accepted (outside partial filter).")
    run("B1e insert second doc without key {other:2}", f"db.{c1}.insertOne({{other:2}})", lambda: insert(c1, {"other": 2}),
        "Second keyless doc accepted: missing-key docs are not treated as duplicate nulls.",
        lambda i: f"Second keyless doc rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}' -> missing key treated as duplicate null despite filter.")
    run("B1f insert {key:null}", f"db.{c1}.insertOne({{key:null}})", lambda: insert(c1, {"key": None}), "First explicit null accepted.")
    run("B1g insert second {key:null}", f"db.{c1}.insertOne({{key:null}})", lambda: insert(c1, {"key": None}),
        "Second explicit null ACCEPTED: $exists:true filter does not index null (differs from MongoDB, where $exists:true matches null).",
        lambda i: f"Second explicit null rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}' -> null is inside the $exists:true filter (matches MongoDB semantics).")
    run("B1h count docs", f"db.{c1}.countDocuments({{}})", lambda: {"count": db[c1].count_documents({})}, lambda r: f"{r['count']} documents stored.")

# B2: { key: { $gt: 0 } }
c2 = "pu_gt"
db.command("create", c2)
okB2, _ = run("B2 createIndexes unique + partialFilterExpression {key:{$gt:0}}",
    f"db.{c2}.createIndex({{key:1}}, {{unique:true, partialFilterExpression:{{key:{{$gt:0}}}}, name:'uq_key_gt0'}})",
    lambda: create_index(c2, {"key": 1}, name="uq_key_gt0", unique=True, partialFilterExpression={"key": {"$gt": 0}}),
    lambda r: f"Accepted: numIndexesBefore={shard(r).get('numIndexesBefore')} numIndexesAfter={shard(r).get('numIndexesAfter')} (gateway nests the result under raw.defaultShard).",
    lambda i: f"Rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
if okB2:
    run("B2a listIndexes", f"db.{c2}.getIndexes()", lambda: list_indexes(c2), lambda r: f"Index spec as stored: {json.dumps(r)[:400]}")
    run("B2b insert {key:5}", f"db.{c2}.insertOne({{key:5}})", lambda: insert(c2, {"key": 5}), "First positive key accepted.")
    run("B2c insert duplicate {key:5}", f"db.{c2}.insertOne({{key:5}})", lambda: insert(c2, {"key": 5}),
        "DUPLICATE ACCEPTED: uniqueness not enforced inside filter.",
        lambda i: f"Duplicate rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
    run("B2d insert {key:0}", f"db.{c2}.insertOne({{key:0}})", lambda: insert(c2, {"key": 0}), "key:0 accepted (outside filter).")
    run("B2e insert duplicate {key:0}", f"db.{c2}.insertOne({{key:0}})", lambda: insert(c2, {"key": 0}),
        "Duplicate key:0 accepted: docs outside $gt:0 are not uniqueness-checked.",
        lambda i: f"Duplicate key:0 rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}' -> filter not honoured.")
    run("B2f insert {key:-1} twice", f"db.{c2}.insertMany([{{key:-1}},{{key:-1}}])",
        lambda: {"inserted": len(db[c2].insert_many([{"key": -1}, {"key": -1}]).inserted_ids)},
        "Two key:-1 docs accepted: negatives outside filter.",
        lambda i: f"Negative duplicates rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
    run("B2g insert two docs without key", f"db.{c2}.insertMany([{{other:1}},{{other:2}}])",
        lambda: {"inserted": len(db[c2].insert_many([{"other": 1}, {"other": 2}]).inserted_ids)},
        "Two keyless docs accepted: missing key outside filter.",
        lambda i: f"Keyless duplicates rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
    run("B2h insert {key:'str'} twice", f"db.{c2}.insertMany([{{key:'s'}},{{key:'s'}}])",
        lambda: {"inserted": len(db[c2].insert_many([{"key": "s"}, {"key": "s"}]).inserted_ids)},
        "Two string keys accepted: strings do not satisfy numeric $gt:0 (type-bracketed comparison).",
        lambda i: f"String duplicates rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}' -> strings are inside the $gt:0 filter on this engine.")
    run("B2i update {key:0} -> {key:5} (move into filter, collides)", f"db.{c2}.updateOne({{key:0}}, {{$set:{{key:5}}}})",
        lambda: jsonable(db[c2].update_one({"key": 0}, {"$set": {"key": 5}}).raw_result),
        "UPDATE ACCEPTED: moving a doc into the filter with a colliding value was not blocked.",
        lambda i: f"Update rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}' -> uniqueness enforced on update into the filter.")
    run("B2j count docs", f"db.{c2}.countDocuments({{}})", lambda: {"count": db[c2].count_documents({})}, lambda r: f"{r['count']} documents stored.")

# B3 extras: $exists:false and sparse+pfe mix (engine_source claims)
c3 = "pu_extra"
db.command("create", c3)
run("B3 createIndexes unique + partialFilterExpression {key:{$exists:false}}",
    f"db.{c3}.createIndex({{key:1}}, {{unique:true, partialFilterExpression:{{key:{{$exists:false}}}}, name:'uq_key_notexists'}})",
    lambda: create_index(c3, {"key": 1}, name="uq_key_notexists", unique=True, partialFilterExpression={"key": {"$exists": False}}),
    lambda r: "Accepted $exists:false (contradicts engine-source reading).",
    lambda i: f"Rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")
run("B4 createIndexes unique + sparse + partialFilterExpression",
    f"db.{c3}.createIndex({{key2:1}}, {{unique:true, sparse:true, partialFilterExpression:{{key2:{{$gt:0}}}}, name:'uq_sparse_pfe'}})",
    lambda: create_index(c3, {"key2": 1}, name="uq_sparse_pfe", unique=True, sparse=True, partialFilterExpression={"key2": {"$gt": 0}}),
    lambda r: "Accepted sparse+partialFilterExpression mix.",
    lambda i: f"Rejected: {i.get('code')} {i.get('codeName')} '{i.get('errmsg')}'.")

# ---------- summarize ----------
report = OrderedDict()
report["test"] = "jsonschema-and-partial-unique"
report["database"] = DB
report["target"] = "documentdb-local container ddb-engine-test, localhost:10260 (TLS, self-signed), MongoDB wire protocol"
report["engine_version"] = engine_version
report["evidence_scope"] = ("Observed on documentdb-local; evidence about the open-source engine and gateway at the buildInfo version above. "
                            "Does not prove managed Azure DocumentDB behaviour.")
report["run_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
report["steps"] = steps
out = os.path.join(HERE, "report.json")
with open(out, "w") as f:
    json.dump(report, f, indent=2, default=str)
print("REPORT:", out)
