#!/usr/bin/env python
"""Build report.json for the bulkwrite-forms REPRODUCTION (engine 1.2.0, database t_bulk_rerun).

Inputs, all in this folder unless noted:
  raw_run.json       what the copied tester script run.py wrote (run_all.sh renames its report.json)
  inspect.json       what the unchanged copy of inspect_container.py wrote (read-only container checks)
  extra.json         what extra_probes.py wrote (probes for gaps in the tester's conclusions)
  preflight.json     whether t_bulk_rerun existed before the run
  src_965b6e7a/      open-source files at the image's OCI revision, fetched by fetch_source.sh
  tester report      .../engine-tests-1.2/bulkwrite-forms/report.json   (compared step by step)
  0.117 baseline     findings/phase4/engine-tests/bulkwrite-forms/report.json (tester's comparison redone)
Every number in the verdicts is read from these files; checks that do not hold turn a verdict into
NOT REPRODUCED. Never prints or stores the password (counted, not shown).
"""
import datetime
import hashlib
import json
import os
from urllib.parse import unquote, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
TESTER = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests-1.2/bulkwrite-forms/report.json"
BASELINE = "/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/bulkwrite-forms/report.json"
ENV = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/local.env"
SRC = os.path.join(HERE, "src_965b6e7a")
REV = "965b6e7ad1c49aefb983a412a3fea0ff637cd7f1"
DB, TDB = "t_bulk_rerun", "t_bulk"


def load(p):
    with open(p) as f:
        return json.load(f)


T = load(TESTER)
B = load(BASELINE)
M = load(os.path.join(HERE, "raw_run.json"))
I = load(os.path.join(HERE, "inspect.json"))
X = load(os.path.join(HERE, "extra.json"))
P = load(os.path.join(HERE, "preflight.json"))

mst = {s["step"]: s for s in M["steps"] + I["steps"]}
tst = {s["step"]: s for s in T["steps"]}
xst = {s["step"]: s for s in X["steps"]}


def R(step):
    return mst[step]["response"]


def XR(step):
    return xst[step]["response"]


def wire(s):
    return [(w["command"], w.get("n_ops")) for w in s.get("wire_commands") or [] if w["command"] in ("insert", "update", "delete", "bulkWrite")]


# ------------------------------------------------------------------ step-by-step comparison with the tester
VOL = {"elapsed_s", "duration_ms", "localTime", "connectionId"}


def norm(o):
    if isinstance(o, dict):
        return {k: norm(v) for k, v in o.items() if k not in VOL}
    if isinstance(o, list):
        return [norm(v) for v in o]
    if isinstance(o, str):
        return o.replace(DB, TDB)
    return o


per_step = []
for s in M["steps"] + I["steps"]:
    t = tst.get(s["step"])
    if t is None:
        per_step.append({"step": s["step"], "status": "MISSING in tester report"})
        continue
    diff = [f for f in ("command", "response", "reading") if norm(s.get(f)) != norm(t.get(f))]
    if norm(s.get("wire_commands")) != norm(t.get("wire_commands")):
        diff.append("wire_commands")
    row = {"step": s["step"], "status": "identical" if not diff else "DIFFERS", "fields_differing": diff}
    if diff:
        row["rerun"] = {f: norm(s.get(f)) for f in diff}
        row["tester"] = {f: norm(t.get(f)) for f in diff}
    per_step.append(row)
for sid in tst:
    if sid not in mst:
        per_step.append({"step": sid, "status": "in tester report only"})
identical = [p["step"] for p in per_step if p["status"] == "identical"]
differing = [p for p in per_step if p["status"] != "identical"]

# ------------------------------------------------------------------ the tester's 0.117 comparison, redone on this rerun
VOL0117 = {"_elapsed_s", "elapsed_s", "localTime", "connectionId", "wire_commands"}


def norm0(o):
    if isinstance(o, dict):
        return {k: norm0(v) for k, v in o.items() if k not in VOL0117}
    if isinstance(o, list):
        return [norm0(v) for v in o]
    if isinstance(o, str):
        return o.replace(DB, TDB)
    return o


def sig(step_id, resp):  # same signature as the tester's finalize.py
    x = norm0(resp)
    if isinstance(x, dict) and "exception" in x:
        keep = {k: x.get(k) for k in ("exception", "code", "codeName", "errmsg", "message", "details")}
        keep = {k: v for k, v in keep.items() if v not in (None, {}, [])}
        keep["errorLabels"] = sorted(x.get("errorLabels") or [])
        return keep
    if step_id == "0b-hello" and isinstance(x, dict):
        x = dict(x)
        x["internal"] = {k: v for k, v in (x.get("internal") or {}).items() if k != "documentdb_versions"}
    if step_id == "0c-pymongo" and isinstance(x, dict):
        x = {k: x.get(k) for k in ("pymongo", "client_bulk_write_available")}
    return x


bst = {s["step"]: s for s in B["steps"]}
vs0117 = []
for s in M["steps"]:
    b = bst.get(s["step"])
    if b is not None:
        vs0117.append({"step": s["step"], "same_as_0117": sig(s["step"], b["response"]) == sig(s["step"], s["response"])})
vs0117_same = [v["step"] for v in vs0117 if v["same_as_0117"]]
NON_ENGINE_COMMON = ["0c-pymongo", "6c-drop-big2", "7-dropDatabase"]

# ------------------------------------------------------------------ source checks at the image revision
def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def src_lines(fname, patterns, after=0):
    path = os.path.join(SRC, fname)
    with open(path, errors="replace") as f:
        lines = f.read().splitlines()
    hits = []
    for pat in patterns:
        for i, ln in enumerate(lines, 1):
            if pat in ln:
                for j in range(i, min(i + after, len(lines)) + 1):
                    hits.append(f"{j}: {lines[j - 1].strip()}")
    return path, sorted(set(hits), key=lambda h: int(h.split(":", 1)[0])), lines


def url(fname):
    return f"https://raw.githubusercontent.com/documentdb/documentdb/{REV}/" + fname.replace("pg_documentdb_gw_documentdb_gateway_core_src_", "pg_documentdb_gw/documentdb_gateway_core/src/").replace("pg_documentdb_gw_documentdb_gateway_src_", "pg_documentdb_gw/documentdb_gateway/src/").replace("pg_documentdb_src_", "pg_documentdb/src/").replace("configuration_", "configuration/").replace("processor_", "processor/").replace("requests_", "requests/").replace("commands_", "commands/").replace("configs_", "configs/")


SOURCE_SPECS = [
    ("S1-gateway-hello-field", "pg_documentdb_gw_documentdb_gateway_core_src_processor_ismaster.rs",
     ['"msg": "isdbgrid"', '"maxWriteBatchSize": dynamic_configuration.max_write_batch_size()'], 0,
     "The gateway's hello/isMaster reply takes maxWriteBatchSize from dynamic_configuration.max_write_batch_size() and always says msg isdbgrid."),
    ("S2-gateway-default-100000", "pg_documentdb_gw_documentdb_gateway_core_src_configuration_dynamic.rs",
     ["fn max_write_batch_size(&self) -> i32 {"], 1,
     "max_write_batch_size() looks up the key 'maxWriteBatchSize' and uses 100,000 only when the key is missing."),
    ("S3-gateway-config-map", "pg_documentdb_gw_documentdb_gateway_core_src_configuration_pg_configuration.rs",
     ['"IsPrimary".to_owned()', '"SendShutdownResponses".to_owned()', ".query(self.pool_manager.query_catalog().pg_settings(), &[], &[])",
      "for settings_prefix in &self.settings_prefixes {", "key = key[settings_prefix.len()..].to_string();", "configs.insert(key.clone(), value);",
      "fn get_i32(&self, key: &str, default: i32) -> i32 {", ".map_or(default, |v| v.parse::<i32>().unwrap_or(default))"], 0,
     "The configuration map holds IsPrimary and SendShutdownResponses from the host config file plus every pg_settings row with its settings prefix stripped, so the engine GUC documentdb.maxWriteBatchSize becomes the key maxWriteBatchSize; the file cannot set it."),
    ("S4-gateway-prefix", "pg_documentdb_gw_documentdb_gateway_src_main.rs",
     ["PgConfiguration::new(", 'vec!["documentdb.".to_owned()],'], 0,
     "The gateway is started with the single settings prefix 'documentdb.'."),
    ("S5-gateway-command-table", "pg_documentdb_gw_documentdb_gateway_core_src_requests_request_type.rs",
     ["fn from_str(cmd_name: &str) -> Result<Self> {", "_ => Err(DocumentDBError::documentdb_error(", "ErrorCode::CommandNotFound,", "format!(\"Command '{cmd_name}' not found.\"),"], 0,
     "Any command name not in RequestType::from_str gets CommandNotFound \"Command '<name>' not found.\"; the file contains no bulkWrite entry."),
    ("S6-engine-bulkWrite-stub", "pg_documentdb_src_commands_bulk_write.c",
     ["Phase 1", "the bulkwrite procedure cannot be used in transactions.", "ERRCODE_DOCUMENTDB_COMMANDNOTSUPPORTED", "bulkWrite is not yet implemented"], 0,
     "The engine has only a Phase 1 bulkWrite stub that would answer CommandNotSupported 'bulkWrite is not yet implemented'; the wire never reaches it."),
    ("S7-engine-GUC", "pg_documentdb_src_configs_system_configs.c",
     ["TODO: Raise this back to 100,000", "#define DEFAULT_MAX_WRITE_BATCH_SIZE 25000", "int MaxWriteBatchSize = DEFAULT_MAX_WRITE_BATCH_SIZE;",
      'psprintf("%s.maxWriteBatchSize", prefix),', "&MaxWriteBatchSize,", "DEFAULT_MAX_WRITE_BATCH_SIZE, 1, INT_MAX,", "#define DEFAULT_BATCH_WRITE_SUB_TRANSACTION_COUNT 512"], 1,
     "The engine registers <prefix>.maxWriteBatchSize backed by MaxWriteBatchSize, default 25,000 (PGC_USERSET), the same variable the write commands check."),
    ("S8a-engine-insert-cap", "pg_documentdb_src_commands_insert.c",
     ["insertionCount > MaxWriteBatchSize)", '"Write batch size must fall within the range of 1 to %d, but %d operations were provided.",'], 0,
     "insert rejects 0 (unless documents were skipped) or more than MaxWriteBatchSize documents with INVALIDLENGTH before writing."),
    ("S8b-engine-delete-cap", "pg_documentdb_src_commands_delete.c",
     ["if (deletionCount == 0 || deletionCount > MaxWriteBatchSize)", '"Write batch size must fall within the range of 1 to %d, but %d operations were provided.",'], 0,
     "delete rejects 0 or more than MaxWriteBatchSize statements with the same INVALIDLENGTH text as insert."),
    ("S8c-engine-update-cap", "pg_documentdb_src_commands_update.c",
     ["if (updateCount == 0 || updateCount > MaxWriteBatchSize)", 'errmsg("Batch sizes should always fall between 1 and %d. "'], 0,
     "update rejects 0 or more than MaxWriteBatchSize statements with INVALIDLENGTH and different wording, in two code paths."),
]
source_steps = []
for sid, fname, pats, after, reading in SOURCE_SPECS:
    path, hits, lines = src_lines(fname, pats, after)
    resp = {"file": path, "sha256": sha(path), "matched_lines": hits}
    if sid == "S5-gateway-command-table":
        resp["case_insensitive_occurrences_of_bulk"] = sum(ln.lower().count("bulk") for ln in lines)
    source_steps.append({
        "step": sid,
        "command": f"curl -sS -m 30 -o {path} '{url(fname)}'  (fetch_source.sh); then search for {pats!r} (finalize_rerun.py)",
        "response": resp,
        "reading": reading,
    })
sst = {s["step"]: s for s in source_steps}

# ------------------------------------------------------------------ facts used in the verdicts
h = M["hello"]
w2 = (R("2a-coll-bulk-ordered-dup").get("details") or {})
w3 = (R("3a-coll-bulk-unordered-dup").get("details") or {})
we2 = (w2.get("writeErrors") or [{}])[0]
raw4 = R("4-raw-insert-dup-unordered")
ins, upd, dele, zero = R("6d-raw-insert-25001-one-command"), R("6i-raw-update-25001-one-command"), R("6j-raw-delete-25001-one-command"), R("6h-raw-insert-0-docs")
cli_sent = [w["command"] for w in (mst["5a-client-bulk-ordered"].get("wire_commands") or []) + (mst["5b-client-bulk-unordered-verbose"].get("wire_commands") or [])]
guc = next((l for l in R("8e-pg_settings-batch")["stdout"].splitlines() if l.startswith("documentdb.maxWriteBatchSize|")), "")
x1a, x1b, x2 = XR("X1a-unknown-command-control"), XR("X1b-bulkWrite-same-db-again"), XR("X2-legacy-isMaster")
x3a, x3b = wire(xst["X3a-interleaved-ordered"]), wire(xst["X3b-interleaved-unordered"])
x4b, x4d = wire(xst["X4b-bulk_write-25001-UpdateOne"]), wire(xst["X4d-bulk_write-25001-DeleteOne"])
x5b = (XR("X5b-insert_many-dup-secondary-unique").get("details") or {}).get("writeErrors") or [{}]
x5c = XR("X5c-raw-insert-dup-secondary-unique")
dup_msgs = sorted({we2.get("errmsg"), (raw4.get("writeErrors") or [{}])[0].get("errmsg"), x5b[0].get("errmsg"), (x5c.get("writeErrors") or [{}])[0].get("errmsg")} - {None})
s5 = sst["S5-gateway-command-table"]["response"]
t_reject = next((w.get("duration_ms") for w in mst["6d-raw-insert-25001-one-command"].get("wire_commands") or [] if w["command"] == "insert"), None)
t_accept = next((w.get("duration_ms") for w in mst["6a-insert_many-25001"].get("wire_commands") or [] if w["command"] == "insert" and w.get("n_ops") == 25000), None)

checks = {
    "C1": w2.get("nInserted") == 2 and we2.get("index") == 2 and we2.get("code") == 11000 and w3.get("nInserted") == 3 and w3.get("nRemoved") == 1 and R("3b-coll-unordered-dup-state") == [{"_id": 11, "v": "y2"}, {"_id": 12, "v": "z"}] and R("4c-raw-ordered-state") == [{"_id": 1}],
    "C2": wire(mst["1a-coll-bulk-ordered-clean"]) == [("insert", 2), ("update", 2), ("delete", 1)] and wire(mst["2a-coll-bulk-ordered-dup"]) == [("insert", 4)] and wire(mst["3a-coll-bulk-unordered-dup"]) == [("insert", 4), ("update", 1), ("delete", 1)],
    "C3": R("5a-client-bulk-ordered").get("exception") == "InvalidOperation" and cli_sent == [] and all(R(s).get("code") == 59 for s in ("5c-raw-bulkWrite-command", "5c2-raw-bulkWrite-command-multi-namespace", "5d-raw-bulkWrite-on-test-db")) and R("5e-client-bw-state") == {"client_bw_a": [], "client_bw_b": []},
    "C4": h.get("maxWriteBatchSize") == 25000 and h.get("maxWireVersion") == 21,
    "C5": guc == "documentdb.maxWriteBatchSize|25000|25000|default" and "batch_mentions_in_setup=0 batch_mentions_in_dynamic=0" in R("8d-gateway-config-file-keys")["stdout"],
    "C6": R("6b-big-count") == 25001 and wire(mst["6a-insert_many-25001"]) == [("insert", 25000), ("insert", 1)] and wire(mst["6k-coll-bulk_write-25001-inserts"]) == [("insert", 25000), ("insert", 1)],
    "C7": all(x.get("code") == 16 and x.get("codeName") == "InvalidLength" and not x.get("errorLabels") for x in (ins, upd, dele, zero)) and R("6e-big2-count") == 0 and R("6i2-big-updated-count") == 0 and R("6j2-big-count-after-delete") == 25001 and R("6f-raw-insert-25000-one-command").get("n") == 25000,
    "C8": len(vs0117) == 20 and len(vs0117_same) == 20,
    "C9": True,
}


def V(cid, verdict):
    return verdict if checks[cid] else "NOT REPRODUCED"


tconc = {c["question"]: c for c in T["conclusions"]}
tq = [c["question"] for c in T["conclusions"]]
verdicts = [
    {"question": tq[0], "tester_confidence": tconc[tq[0]]["confidence"], "verdict": V("C1", "confirmed"),
     "basis": f"Rerun on {DB}: ordered dup nInserted={w2.get('nInserted')} with writeError index {we2.get('index')} code {we2.get('code')}; unordered nInserted={w3.get('nInserted')} nMatched={w3.get('nMatched')} nRemoved={w3.get('nRemoved')}; states identical to the tester's; raw insert replies ok=1 with writeErrors in the body; write-error keys {sorted(we2.keys())} (PyMongo) and {sorted((raw4.get('writeErrors') or [{}])[0].keys())} (server). 'Identical to 0.117' re-checked on this rerun: {len(vs0117_same)} of {len(vs0117)} common steps have the 0.117 signature."},
    {"question": tq[1], "tester_confidence": tconc[tq[1]]["confidence"], "verdict": V("C2", "confirmed; the hedge about regrouping is now resolved"),
     "basis": f"Wire capture reproduced exactly (1a {wire(mst['1a-coll-bulk-ordered-clean'])}, 2a {wire(mst['2a-coll-bulk-ordered-dup'])}, 3a {wire(mst['3a-coll-bulk-unordered-dup'])}). Extra probe X3 with interleaved types: ordered -> {x3a} (one command per consecutive run), unordered -> {x3b} (PyMongo 4.20.1 regroups all ops of a type into one command). This is driver behaviour; only PyMongo was exercised."},
    {"question": tq[2], "tester_confidence": tconc[tq[2]]["confidence"], "verdict": V("C3", "confirmed (the routing clause was an inference; it is now backed by source and a control)"),
     "basis": f"Rerun: InvalidOperation with no command sent ({cli_sent}); raw bulkWrite 59 CommandNotFound on admin, multi-namespace and {DB}. Control X1a: an invented name returns code {x1a.get('code')} {x1a.get('codeName')} \"{x1a.get('errmsg')}\", the same template as \"{x1b.get('errmsg')}\". Gateway source at {REV[:8]} (S5): from_str has no bulkWrite arm (case-insensitive 'bulk' occurrences: {s5.get('case_insensitive_occurrences_of_bulk')}) and its default arm returns CommandNotFound \"Command '{{cmd_name}}' not found.\"; the engine stub (S6) answers CommandNotSupported and is never reached."},
    {"question": tq[3], "tester_confidence": tconc[tq[3]]["confidence"], "verdict": V("C4", "value confirmed; the claim that this settles DECISIONS open item 4 is disputed"),
     "basis": f"hello maxWriteBatchSize={h.get('maxWriteBatchSize')} maxWireVersion={h.get('maxWireVersion')} reproduced; legacy isMaster (X2) also says {x2.get('maxWriteBatchSize')}. Open item 4 asks what the Azure gateway advertises, which a documentdb-local run cannot answer. See disputed."},
    {"question": tq[4], "tester_confidence": tconc[tq[4]]["confidence"], "verdict": V("C5", "confirmed and upgraded from inferred to source-confirmed at the image revision"),
     "basis": f"8a-8e reproduced byte for byte ({guc}). Gateway source at {REV[:8]}: hello uses max_write_batch_size() (S1), which reads key maxWriteBatchSize with fallback 100,000 (S2) from a map built from pg_settings with prefix 'documentdb.' stripped (S3, S4); the host config file contributes only IsPrimary and SendShutdownResponses (S3). The engine GUC is backed by the same MaxWriteBatchSize variable the insert, update and delete checks use (S7, S8)."},
    {"question": tq[5], "tester_confidence": tconc[tq[5]]["confidence"], "verdict": V("C6", "confirmed"),
     "basis": f"insert_many 25,001 -> {wire(mst['6a-insert_many-25001'])}, count {R('6b-big-count')}; bulk_write 25,001 InsertOne -> {wire(mst['6k-coll-bulk_write-25001-inserts'])}, count {R('6k2-big3-count')}. Extra probe X4: 25,001 UpdateOne -> {x4b}, 25,001 DeleteOne -> {x4d}, so update and delete batches split the same way."},
    {"question": tq[6], "tester_confidence": tconc[tq[6]]["confidence"], "verdict": V("C7", "confirmed for the open-source engine; the Learn recommendation rests on local evidence only"),
     "basis": f"insert 25,001: {ins.get('code')} {ins.get('codeName')} \"{ins.get('errmsg')}\", count {R('6e-big2-count')}; 25,000: n={R('6f-raw-insert-25000-one-command').get('n')}; 0 docs: {zero.get('code')} \"{zero.get('errmsg')}\"; update 25,001: {upd.get('code')} \"{upd.get('errmsg')}\", updated count {R('6i2-big-updated-count')}; delete 25,001: {dele.get('code')} \"{dele.get('errmsg')}\", count {R('6j2-big-count-after-delete')}. Source S8a-S8c shows the checks run on the operation count before any write, and update has its own wording in two code paths. What Azure returns for an oversize command was not observed."},
    {"question": tq[7], "tester_confidence": tconc[tq[7]]["confidence"], "verdict": V("C8", "core finding confirmed; two generalizations disputed"),
     "basis": f"Redoing the tester's 0.117 signature comparison on this rerun: {len(vs0117_same)} of {len(vs0117)} common steps match. Three of those ({NON_ENGINE_COMMON}) compare only the driver version or a drop() returning null, so 17 carry engine behaviour. See disputed for 'drivers still gate' and '5 of 5 claims hold'."},
    {"question": tq[8], "tester_confidence": tconc[tq[8]]["confidence"], "verdict": "confirmed",
     "basis": "Correctly scoped: nothing in this run or the rerun observes the managed service. The 02-real-time-event-stream-ingestion Azure log does show the same duplicate-key message template (see extra observations), which is consistent with, not proof of, the same engine lineage."},
]

disputed = [
    {"question": tq[3],
     "reason": ("The answer says the 25,000 observation 'settles open item 4 for documentdb-local 1.2.0 only'. Open item 4 in DECISIONS topic 9 asks only what the Azure gateway advertises, so a documentdb-local run settles none of it and the item must stay open. "
                "What the run does settle is the open-source half, and the gateway source at the image revision (S1-S4) shows why: 100,000 is only the fallback when the engine GUC documentdb.maxWriteBatchSize is absent, so the DECISIONS settled-item phrase 'the advertised driver split size defaults to 100,000' is wrong for this code. "
                "For Azure the question becomes what documentdb.maxWriteBatchSize is set to there, which is still unobserved.")},
    {"question": tq[7],
     "reason": ("Two generalizations go beyond the evidence, which comes from PyMongo 4.20.1 only. (1) 'so drivers still gate MongoClient.bulk_write off': PyMongo refuses it client-side (wire 21 < 25), but no other driver was run; a driver that does send the command gets 59 CommandNotFound instead. "
                "(2) '5 of 5 ENGINE-TESTS.md bulk-write claims hold' counts claim 2 ('as every driver does') and claim 4 ('drivers split larger batches automatically') as holding, although only PyMongo was observed. Those claims should say 'PyMongo'. "
                "Separately, 3 of the '20 common steps' (0c-pymongo, 6c-drop-big2, 7-dropDatabase) do not test the engine. The core finding, no bulk-write behaviour change from 0.117 to 1.2.0, stands.")},
]

extra_observations = [
    (f"Source-level confirmation at the image's OCI revision {REV[:8]} (S1-S4, S7): the gateway's hello and isMaster reply take maxWriteBatchSize from the engine GUC documentdb.maxWriteBatchSize, read through pg_settings with the 'documentdb.' prefix stripped. "
     "The advertised split size and the enforced cap are the same engine variable (MaxWriteBatchSize, default 25,000), so they cannot drift apart unless the GUC is missing (then the gateway falls back to 100,000) or is overridden for some sessions only (it is PGC_USERSET; no such override was observed). "
     "The host config file cannot set the value: this revision copies only IsPrimary and SendShutdownResponses from it."),
    (f"bulkWrite is answered exactly like a command name that does not exist. An invented name returns {x1a.get('code')} {x1a.get('codeName')} \"{x1a.get('errmsg')}\" (X1a), and the gateway's command table at {REV[:8]} has no bulkWrite entry (S5). "
     "The engine's CommandNotSupported stub ('bulkWrite is not yet implemented', S6) is never reached. 'Not recognised by the gateway (59 CommandNotFound)' is the accurate wording. "
     "The 'Engine tests' headline in DECISIONS.md says 'client-level bulkWrite is unsupported (code 59)', which reads as 115 CommandNotSupported; code 59 is CommandNotFound."),
    (f"PyMongo 4.20.1 regroups unordered batches. Interleaved insert/update/insert/delete/insert/update goes out as {x3b} when unordered and as {x3a} when ordered (X3). "
     "An unordered batch therefore runs in type order, not in the order given. This is driver behaviour, and the engine accepts both forms."),
    (f"Driver splitting at hello.maxWriteBatchSize also covers update and delete batches: 25,001 UpdateOne -> {x4b} (all {XR('X4c-count-updated')} updated), 25,001 DeleteOne -> {x4d} (count after: {XR('X4e-count-after-delete')}) (X4). The tester showed this for inserts only."),
    f"The legacy isMaster command that drivers use for the initial handshake advertises the same limits as hello: maxWriteBatchSize {x2.get('maxWriteBatchSize')}, maxWireVersion {x2.get('maxWireVersion')}, msg {x2.get('msg')!r} (X2).",
    (f"Duplicate-key write errors carry only index, code and errmsg, and the errmsg is a fixed template naming only the index: {dup_msgs} for _id and for a secondary unique index (steps 2a, 4, X5b, X5c). "
     "There is no keyPattern, no keyValue, no namespace, no duplicated value, and no 'E11000' prefix. Code that parses MongoDB's 'E11000 duplicate key error ...' text or reads keyValue to find the duplicated field gets nothing. Match on code 11000 and, if needed, on the index name. "
     "The Azure run 02-real-time-event-stream-ingestion/20261124-203233 logged the same template (\"Duplicate key violation on the requested collection: Index 'customer_event_unique'\"), which is consistent with, not proof of, the same engine lineage on the managed service."),
    (f"The batch cap is checked on the operation count before anything is written. In source the checks sit in the spec-building step (BuildBatchInsertionSpec, PostProcessDeleteBatchSpec, BuildUpdates) or at the start of the update batch worker (S8a-S8c). "
     f"On the wire, the rejected 25,001-document insert came back in {t_reject} ms; the accepted 25,000-document insert command in 6a took {t_accept} ms. "
     "update with 0 statements is also code 16 per source (S8c); only insert with 0 documents was exercised."),
    (f"Reproduction was exact. All {len(identical)} steps of run.py plus the read-only checks (35 wire steps and 8a-8e) have the same command, response, wire capture and reading as the tester's report after normalising the database name and dropping timings, localTime and connectionId. "
     f"Differences: {[d['step'] for d in differing] or 'none'}."),
]

# ------------------------------------------------------------------ report
ran = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
report = {
    "test": "bulkwrite-forms REPRODUCTION (database t_bulk_rerun) of the engine 1.2.0 run reported at " + TESTER,
    "stage": "reproduce bulkwrite-forms",
    "database": DB,
    "database_fresh_before_run": not P["response"]["t_bulk_rerun_present_before_run"],
    "ran_at": M.get("ran_at"),
    "finalized_at": ran,
    "target": M.get("target"),
    "engine_version": {
        "image": R("8a-container-image")["stdout"],
        "buildInfo.version": M["buildInfo"].get("version"),
        "hello.maxWireVersion": h.get("maxWireVersion"),
        "hello.internal.documentdb_versions": (h.get("internal") or {}).get("documentdb_versions"),
        "postgresql": next((l.split("|")[1] for l in R("8e-pg_settings-batch")["stdout"].splitlines() if l.startswith("server_version|")), None),
        "pymongo": M.get("pymongo_version"),
        "python": M.get("python"),
    },
    "evidence_scope": ("Everything here was observed on documentdb-local (image pg17-1.2.0, extension 1.2-0/1.2.0, buildInfo 7.0.0, wire 21) or read from the open-source repository at the image's OCI revision. "
                       "It is evidence about the open-source engine and gateway at that version and does not prove what the managed Azure DocumentDB service does."),
    "how_the_script_was_copied": {
        "original": "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests-1.2/bulkwrite-forms/run.py",
        "copy": os.path.join(HERE, "run.py"),
        "changes": "DB = 't_bulk' -> 't_bulk_rerun' and every standalone t_bulk in recorded command and reading strings (21 replacements by a word-bounded regex, so client_bulk and the result key t_bulk_present were left unchanged); appname gained '-rerun'. No test logic changed. inspect_container.py copied unchanged.",
    },
    "steps": M["steps"] + I["steps"] + X["steps"] + source_steps,
    "comparison_with_tester": {
        "tester_report": TESTER,
        "method": "for each step of run.py and inspect_container.py: command, response, reading and wire_commands compared after replacing t_bulk_rerun with t_bulk and dropping elapsed_s, duration_ms, localTime and connectionId",
        "steps_compared": len(per_step),
        "identical": len(identical),
        "differing": [d["step"] for d in differing],
        "per_step": per_step,
    },
    "tester_0117_comparison_redone": {
        "baseline": BASELINE,
        "method": "the tester's own behaviour signature (finalize.py sig), applied to this rerun",
        "common_steps": len(vs0117),
        "same": len(vs0117_same),
        "per_step": vs0117,
        "common_steps_that_do_not_test_the_engine": NON_ENGINE_COMMON,
    },
    "conclusion_verdicts": verdicts,
    "checks_behind_verdicts": checks,
    "disputed": disputed,
    "extra_observations": extra_observations,
    "files": {
        "run": os.path.join(HERE, "run.py"),
        "inspect": os.path.join(HERE, "inspect_container.py"),
        "extra_probes": os.path.join(HERE, "extra_probes.py"),
        "fetch_source": os.path.join(HERE, "fetch_source.sh"),
        "finalize": os.path.join(HERE, "finalize_rerun.py"),
        "run_all": os.path.join(HERE, "run_all.sh"),
        "raw_run": os.path.join(HERE, "raw_run.json"),
        "inspect_raw": os.path.join(HERE, "inspect.json"),
        "extra_raw": os.path.join(HERE, "extra.json"),
        "source_dir": SRC,
        "report": os.path.join(HERE, "report.json"),
    },
    "notes": ("Only database t_bulk_rerun was used. It did not exist before the run (preflight.json), was dropped at the start and end of run.py and of extra_probes.py, and was confirmed absent afterwards (7b, X9b). "
              "The container was neither stopped nor modified; 8a-8e are read-only (docker inspect, grep over two binaries, key names of the gateway config files, one SELECT on pg_settings). "
              "The source files came from public raw.githubusercontent.com URLs at the image revision; they were read as text and never executed. "
              "Rerun with run_all.sh."),
}


def passwords():
    out = set()
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if line.startswith("LOCAL_URI="):
                pw = urlsplit(line.split("=", 1)[1].strip().strip("\"'")).password or ""
                out |= {x for x in (pw, unquote(pw)) if x}
            elif line.startswith("LOCAL_PASS="):
                v = line.split("=", 1)[1].strip().strip("\"'")
                if v:
                    out.add(v)
    return out


PW = passwords()


def count(text):
    return sum(text.count(x) for x in PW)


files_checked = {}
for root, _, fns in os.walk(HERE):
    for fn in fns:
        p = os.path.join(root, fn)
        if p == os.path.join(HERE, "report.json") or "__pycache__" in p:
            continue
        with open(p, errors="replace") as f:
            files_checked[os.path.relpath(p, HERE)] = count(f.read())
text = json.dumps(report, indent=2)
report["password_check"] = {
    "method": "occurrences of the LOCAL_URI password (raw and URL-decoded) and of LOCAL_PASS, counted in every file in this folder and in the report text; the value is never printed",
    "counts": dict(sorted(files_checked.items())),
    "report_json_as_written": count(text),
}
assert report["password_check"]["report_json_as_written"] == 0 and not any(files_checked.values()), "password found in an output file"
with open(os.path.join(HERE, "report.json"), "w") as f:
    json.dump(report, f, indent=2)
with open(os.path.join(HERE, "report.json")) as f:
    assert count(f.read()) == 0
print(json.dumps({"steps": len(report["steps"]), "identical_to_tester": len(identical), "differing": [d["step"] for d in differing],
                  "same_as_0117": f"{len(vs0117_same)}/{len(vs0117)}", "checks": checks, "verdicts": [v["verdict"] for v in verdicts]}, indent=1))
