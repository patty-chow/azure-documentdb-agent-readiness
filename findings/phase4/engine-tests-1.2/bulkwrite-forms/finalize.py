#!/usr/bin/env python
"""Finalize report.json for bulkwrite-forms (engine 1.2.0 rerun).

Run after run.py and inspect_container.py. Idempotent: it rebuilds every derived section from the
raw steps run.py wrote and the checks inspect_container.py wrote.
  * merges the read-only container checks (steps 8a-8e) into report["steps"]
  * compares every step with the 0.117 report (behaviour signature, volatile fields ignored)
  * checks each claim of the "Bulk writes (topic 9)" section of ENGINE-TESTS.md against this run
  * writes conclusions and notes whose numbers are read from this run's steps, not typed in
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "report.json")
INSPECT = os.path.join(HERE, "inspect.json")
BASELINE = "/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/bulkwrite-forms/report.json"

r = json.load(open(REPORT))
r["steps"] = [s for s in r["steps"] if not s["step"].startswith("8")]  # idempotent re-merge
if os.path.exists(INSPECT):
    r["steps"].extend(json.load(open(INSPECT))["steps"])
base = json.load(open(BASELINE))

st = {s["step"]: s for s in r["steps"]}
bst = {s["step"]: s for s in base["steps"]}


def R(step):
    return st[step]["response"]


def wire(step):
    return [(w["command"], w.get("n_ops")) for w in st[step].get("wire_commands") or [] if w["command"] in ("insert", "update", "delete", "bulkWrite")]


# ---------------------------------------------------------------- comparison with 0.117
VOLATILE = {"_elapsed_s", "elapsed_s", "localTime", "connectionId", "wire_commands"}


def norm(o):
    if isinstance(o, dict):
        return {k: norm(v) for k, v in o.items() if k not in VOLATILE}
    if isinstance(o, list):
        return [norm(v) for v in o]
    return o


def sig(step_id, resp):
    x = norm(resp)
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


per_step = []
for s in r["steps"]:
    b = bst.get(s["step"])
    if b is None:
        per_step.append({"step": s["step"], "status": "new in 1.2.0 run (no 0.117 counterpart)"})
        continue
    a, c = sig(s["step"], b["response"]), sig(s["step"], s["response"])
    row = {"step": s["step"], "status": "same" if a == c else "DIFFERS"}
    if a != c:
        row["v0_117"], row["v1_2_0"] = a, c
    per_step.append(row)
for sid in bst:
    if sid not in st:
        per_step.append({"step": sid, "status": "0.117 only (not repeated)", "note": "per-collection pre-clean drops; replaced by 0d-pre-clean-dropDatabase" if sid.startswith("0d-drop-") else ""})

bh, h = base["hello"], r["hello"]
pg = next((l.split("|")[1] for l in R("8e-pg_settings-batch")["stdout"].splitlines() if l.startswith("server_version|")), None) if "8e-pg_settings-batch" in st else None
version_fields = {
    "buildInfo.version": [base["buildInfo"].get("version"), r["buildInfo"].get("version")],
    "hello.maxWireVersion": [bh.get("maxWireVersion"), h.get("maxWireVersion")],
    "hello.maxWriteBatchSize": [bh.get("maxWriteBatchSize"), h.get("maxWriteBatchSize")],
    "hello.maxMessageSizeBytes": [bh.get("maxMessageSizeBytes"), h.get("maxMessageSizeBytes")],
    "hello.maxBsonObjectSize": [bh.get("maxBsonObjectSize"), h.get("maxBsonObjectSize")],
    "hello.internal.documentdb_versions": [bh.get("internal", {}).get("documentdb_versions"), h.get("internal", {}).get("documentdb_versions")],
    "PostgreSQL server_version": ["17.11 (per ENGINE-TESTS.md; not in the 0.117 report)", pg],
    "pymongo": [base.get("pymongo_version"), r.get("pymongo_version")],
}
common = [p for p in per_step if p["status"] in ("same", "DIFFERS")]
diffs = [p for p in per_step if p["status"] == "DIFFERS"]

# ---------------------------------------------------------------- values used in the text
upd_err, ins_err, del_err, zero_err = R("6i-raw-update-25001-one-command"), R("6d-raw-insert-25001-one-command"), R("6j-raw-delete-25001-one-command"), R("6h-raw-insert-0-docs")
we2 = R("2a-coll-bulk-ordered-dup").get("details", {})
we3 = R("3a-coll-bulk-unordered-dup").get("details", {})
w_first = (we2.get("writeErrors") or [{}])[0]
raw4 = R("4-raw-insert-dup-unordered")
raw4b = R("4b-raw-insert-dup-ordered")
bw59 = R("5c-raw-bulkWrite-command")
bw59b = R("5c2-raw-bulkWrite-command-multi-namespace")
bw59c = R("5d-raw-bulkWrite-on-test-db")
cli = R("5a-client-bulk-ordered")
cli_sent = [w["command"] for w in st["5a-client-bulk-ordered"].get("wire_commands") or []] + [w["command"] for w in st["5b-client-bulk-unordered-verbose"].get("wire_commands") or []]
state5 = R("5e-client-bw-state")
strings = R("8b-error-string-locations")["stdout"] if "8b-error-string-locations" in st else ""
gw_sql = R("8c-gateway-settings-query")["stdout"] if "8c-gateway-settings-query" in st else ""
guc = next((l for l in R("8e-pg_settings-batch")["stdout"].splitlines() if l.startswith("documentdb.maxWriteBatchSize|")), "") if "8e-pg_settings-batch" in st else ""
subtx = next((l for l in R("8e-pg_settings-batch")["stdout"].splitlines() if l.startswith("documentdb.batchWriteSubTransactionCount|")), "") if "8e-pg_settings-batch" in st else ""
dyn = R("8d-gateway-config-file-keys")["stdout"] if "8d-gateway-config-file-keys" in st else ""
ver = h.get("internal", {}).get("documentdb_versions")


status = {p["step"]: p["status"] for p in per_step}


def same(*ids):
    return all(status.get(i) == "same" for i in ids)


def vs0117(*ids):
    bad = [i for i in ids if status.get(i) != "same"]
    return "Identical to 0.117 (steps " + ", ".join(ids) + " match)." if not bad else "DIFFERENT from 0.117 at steps " + ", ".join(bad) + "."


dyn = "; ".join(l.strip() for l in dyn.splitlines() if l.strip())
w_keys = sorted(w_first.keys())
missing_keys = [k for k in ("codeName", "keyPattern", "keyValue", "errInfo") if k not in w_first]
labels_2a3a = sorted(set((R("2a-coll-bulk-ordered-dup").get("errorLabels") or []) + (R("3a-coll-bulk-unordered-dup").get("errorLabels") or [])))


def em(x):
    return f"code {x.get('code')} {x.get('codeName')} \"{x.get('errmsg')}\"" if x.get("exception") else f"no error ({x})"


# ---------------------------------------------------------------- claims in ENGINE-TESTS.md (Bulk writes)
claims = [
    {
        "claim": "Collection-level bulkWrite works, ordered and unordered, with per-op writeErrors on a duplicate _id.",
        "result_on_1_2_0": "reproduced" if R("1a-coll-bulk-ordered-clean").get("acknowledged") and w_first.get("code") == 11000 and we3.get("nInserted") == 3 else "NOT reproduced",
        "evidence_steps": ["1a", "2a", "2b", "3a", "3b"],
    },
    {
        "claim": "It is sent as separate insert, update and delete commands grouped by type, as every driver does.",
        "result_on_1_2_0": f"now observed on the wire (CommandListener): ordered clean batch {wire('1a-coll-bulk-ordered-clean')}, ordered with duplicate {wire('2a-coll-bulk-ordered-dup')}, unordered with duplicate {wire('3a-coll-bulk-unordered-dup')}; the 0.117 report has no wire capture, so this was not directly evidenced at 0.117",
        "evidence_steps": ["1a", "2a", "3a"],
    },
    {
        "claim": "Client-level MongoClient.bulkWrite: PyMongo refuses it client-side because the wire version is 21, and the raw bulkWrite admin command returns code 59 CommandNotFound.",
        "result_on_1_2_0": ("reproduced" if cli.get("exception") == "InvalidOperation" and bw59.get("code") == 59 else "NOT reproduced") + f"; additionally observed that the driver sent no command at all ({cli_sent}) and that the multi-namespace and non-admin forms also return 59",
        "evidence_steps": ["5a", "5b", "5c", "5c2", "5d", "5e"],
    },
    {
        "claim": "hello.maxWriteBatchSize is 25,000, so drivers split larger batches automatically; insert_many of 25,001 documents succeeded as 25,000 plus 1.",
        "result_on_1_2_0": ("reproduced" if h.get("maxWriteBatchSize") == 25000 and R("6b-big-count") == 25001 else "NOT reproduced") + f"; the 25,000 + 1 split is now observed on the wire: {wire('6a-insert_many-25001')} (at 0.117 it was inferred from the success)",
        "evidence_steps": ["0b", "0c", "6a", "6b", "6k"],
    },
    {
        "claim": "A raw single command with 25,001 operations fails with code 16 InvalidLength: 'Write batch size must fall within the range of 1 to 25000, but N operations were provided.'",
        "result_on_1_2_0": ("reproduced for insert" if ins_err.get("code") == 16 else "NOT reproduced for insert") + f" and delete ({em(del_err)}); update returns the same code with different text ({em(upd_err)}), so the quoted message is insert/delete-specific",
        "evidence_steps": ["6d", "6e", "6f", "6h", "6i", "6j"],
    },
]

r["comparison_with_0117"] = {
    "baseline_report": BASELINE,
    "method": "behaviour signature per step id: exception, code, codeName, errmsg, message, details, errorLabels for errors; the full result otherwise; timings, localTime, connectionId and hello.internal.documentdb_versions excluded",
    "version_fields_0117_vs_120": version_fields,
    "steps_compared": len(common),
    "steps_differing": len(diffs),
    "differing_steps": [d["step"] for d in diffs],
    "per_step": per_step,
    "engine_tests_md_claims": claims,
}

# ---------------------------------------------------------------- conclusions
same_all = len(diffs) == 0
r["conclusions"] = [
    {
        "question": "On engine 1.2.0, does collection-level bulk_write work, ordered and unordered, and how is a duplicate _id reported?",
        "answer": (
            f"Yes, on documentdb-local {ver} (buildInfo {r['buildInfo'].get('version')}, wire {h.get('maxWireVersion')}). The clean ordered batch returned "
            f"inserted={R('1a-coll-bulk-ordered-clean')['inserted_count']} matched={R('1a-coll-bulk-ordered-clean')['matched_count']} modified={R('1a-coll-bulk-ordered-clean')['modified_count']} "
            f"upserted={R('1a-coll-bulk-ordered-clean')['upserted_count']} deleted={R('1a-coll-bulk-ordered-clean')['deleted_count']}. With a duplicate _id at index 2, both forms raise "
            f"BulkWriteError (driver code {R('2a-coll-bulk-ordered-dup')['code']}) carrying {len(we2.get('writeErrors') or [])} and {len(we3.get('writeErrors') or [])} writeError(s) respectively, {{index: {w_first.get('index')}, code: {w_first.get('code')}, errmsg: \"{w_first.get('errmsg')}\"}} "
            f"(keys as reported by PyMongo {w_keys}, where 'op' is added by the driver; server reply keys in step 4: {sorted((raw4.get('writeErrors') or [{}])[0].keys())}; absent: {missing_keys}; errorLabels {labels_2a3a}). Ordered stops at the duplicate (nInserted={we2.get('nInserted')}, later insert, update and delete not applied; "
            f"state {R('2b-coll-ordered-dup-state')}). Unordered continues (nInserted={we3.get('nInserted')} nMatched={we3.get('nMatched')} nModified={we3.get('nModified')} nRemoved={we3.get('nRemoved')}; "
            f"state {R('3b-coll-unordered-dup-state')}). The raw insert command reports partial failure in the reply body: unordered ok={raw4.get('ok')} n={raw4.get('n')} with writeErrors at index "
            f"{[w.get('index') for w in raw4.get('writeErrors', [])]}; ordered ok={raw4b.get('ok')} n={raw4b.get('n')} with writeErrors at index {[w.get('index') for w in raw4b.get('writeErrors', [])]} "
            f"and the document after the duplicate not inserted ({R('4c-raw-ordered-state')}). " + vs0117("1a-coll-bulk-ordered-clean", "1b-coll-ordered-state", "2a-coll-bulk-ordered-dup", "2b-coll-ordered-dup-state", "3a-coll-bulk-unordered-dup", "3b-coll-unordered-dup-state", "4-raw-insert-dup-unordered") + " Steps 4b-4c are new."
        ),
        "confidence": "observed",
    },
    {
        "question": "How does the driver send a collection-level bulk_write to this engine?",
        "answer": (
            f"As ordinary insert, update and delete commands, one per group of same-type operations, observed with a PyMongo CommandListener (these batches were already in type order, so they do not show whether an unordered batch is regrouped): the ordered clean batch "
            f"(insert, insert, update, update-upsert, delete) went out as {wire('1a-coll-bulk-ordered-clean')}; the ordered batch with the duplicate as {wire('2a-coll-bulk-ordered-dup')} only, because the "
            f"driver stops after the insert reply carries a writeError; the unordered batch as {wire('3a-coll-bulk-unordered-dup')}. No bulkWrite command is involved, which is why the collection-level "
            f"form works while the 8.0 command does not. The 0.117 report had no wire capture, so this is the first direct evidence for ENGINE-TESTS.md's 'grouped by type' sentence."
        ),
        "confidence": "observed",
    },
    {
        "question": "Does client-level MongoClient.bulk_write (the MongoDB 8.0 bulkWrite command) work on engine 1.2.0, and what does the raw bulkWrite command return?",
        "answer": (
            f"No{', unchanged from 0.117' if same('5a-client-bulk-ordered', '5b-client-bulk-unordered-verbose', '5c-raw-bulkWrite-command') else ' (CHANGED from 0.117 at one of 5a-5c)'}. PyMongo {r.get('pymongo_version')} raises {cli.get('exception')} '{cli.get('message')}' for ordered and unordered/verbose calls and sends no command "
            f"(commands captured during both calls: {cli_sent}), because hello.maxWireVersion is {h.get('maxWireVersion')} and the installed driver gates on {R('0c-pymongo').get('client_bulk_write_gate', {}).get('lines')}. The raw command on admin returns ok:0 "
            f"{em(bw59)} with errorLabels {bw59.get('errorLabels')}; a well-formed multi-namespace form (insert, insert, update, delete over two namespaces) returns {em(bw59b)}, and the same "
            f"command sent to t_bulk instead of admin returns {em(bw59c)}. Nothing was applied (client_bw_a={state5.get('client_bw_a')}, client_bw_b={state5.get('client_bw_b')}). "
            f"The engine extension in this image still contains the stub text 'bulkWrite is not yet implemented' (absent from the gateway binary), so on 1.2.0 the gateway still does not route the name to it. "
            f"Observed on the open-source gateway/engine only; consistent with the compatibility page's 'bulkWrite: No' row."
        ),
        "confidence": "observed",
    },
    {
        "question": "What does hello.maxWriteBatchSize advertise on the 1.2.0 gateway (DECISIONS topic 9, open item 4)?",
        "answer": (
            f"{h.get('maxWriteBatchSize')}, {'unchanged from' if version_fields['hello.maxWriteBatchSize'][0] == version_fields['hello.maxWriteBatchSize'][1] else 'CHANGED from'} 0.117's {version_fields['hello.maxWriteBatchSize'][0]} (maxMessageSizeBytes={h.get('maxMessageSizeBytes')}, maxBsonObjectSize={h.get('maxBsonObjectSize')}, maxWireVersion={h.get('maxWireVersion')}). "
            f"PyMongo stores it as the server's max_write_batch_size ({R('0c-pymongo')['driver_server_descriptions']}); its fallback if hello omitted the field would be "
            f"{R('0c-pymongo')['driver_default_MAX_WRITE_BATCH_SIZE_if_hello_omits_it']}. So on the open-source gateway at 1.2.0 the advertised split size matches the engine cap, not the 100,000 "
            f"default that DECISIONS topic 9 cites from the gateway source (ismaster.rs, dynamic.rs). This settles open item 4 for documentdb-local 1.2.0 only; the managed service's value is still unobserved."
        ),
        "confidence": "observed",
    },
    {
        "question": "Where does the advertised 25,000 come from on this build?",
        "answer": (
            f"Most likely from the engine setting, not from gateway configuration. The engine GUC reads '{guc}' (name|setting|boot_val|source) and '{subtx}'; the gateway binary embeds "
            f"\"{gw_sql}\"; and the gateway's two configuration files contain no batch key ({dyn}). Together these indicate the gateway takes maxWriteBatchSize from documentdb.maxWriteBatchSize "
            f"via pg_settings, so a deployment's advertised value would follow its engine setting. Inferred from binary strings and configuration, not from gateway source at this revision."
        ),
        "confidence": "inferred",
    },
    {
        "question": "What happens to insert_many of 25,001 documents (driver splitting)?",
        "answer": (
            f"It succeeds: {R('6a-insert_many-25001')['inserted_ids_count']} ids returned and count_documents={R('6b-big-count')}. The CommandListener shows PyMongo sent "
            f"{wire('6a-insert_many-25001')}, i.e. two insert commands of 25,000 and 1 documents. A collection-level bulk_write of 25,001 InsertOne ops splits the same way "
            f"({wire('6k-coll-bulk_write-25001-inserts')}, count {R('6k2-big3-count')}). " + ("Same outcome as 0.117" if same("6a-insert_many-25001", "6b-big-count") else "Outcome DIFFERS from 0.117") + ", where the split was inferred from the success rather than captured."
        ),
        "confidence": "observed",
    },
    {
        "question": "What does a single raw write command with more than 25,000 operations return, and which error should the Learn limitations page name?",
        "answer": (
            f"Code 16 InvalidLength, no errorLabels, and the whole command is rejected. insert with 25,001 documents: {em(ins_err)}, 0 documents written (count {R('6e-big2-count')}); exactly 25,000: "
            f"ok={R('6f-raw-insert-25000-one-command').get('ok')} n={R('6f-raw-insert-25000-one-command').get('n')}; an empty documents array: {em(zero_err)}. delete with 25,001 statements: "
            f"{em(del_err)}, nothing deleted (count {R('6j2-big-count-after-delete')}). update with 25,001 statements: {em(upd_err)}, nothing applied (count of updated docs {R('6i2-big-updated-count')}). "
            f"Both texts are in the engine extension pg_documentdb.so, not the gateway. The limitations page should name code 16 (InvalidLength) and not rely on one message, since update words it "
            f"differently. Observed on 1.2.0; the 0.117 run tested only insert" + (", with the same code and text." if same("6d-raw-insert-25001-one-command", "6e-big2-count", "6f-raw-insert-25000-one-command") else ", and its result DIFFERS from this one.")
        ),
        "confidence": "observed",
    },
    {
        "question": "Did anything in bulk-write behaviour change between engine 0.117 and 1.2.0?",
        "answer": (
            (f"No. All {len(common)} steps common to both runs have the same behaviour signature (exception, code, codeName, errmsg, errorLabels, counts, resulting documents). "
             if same_all else f"Yes: {len(diffs)} of {len(common)} common steps differ: {[d['step'] for d in diffs]}. ")
            + f"The version fields that moved are hello.internal.documentdb_versions {version_fields['hello.internal.documentdb_versions'][0]} -> {version_fields['hello.internal.documentdb_versions'][1]} "
            f"and PostgreSQL 17.11 -> {pg}; buildInfo.version ({r['buildInfo'].get('version')}), maxWireVersion ({h.get('maxWireVersion')}) and maxWriteBatchSize ({h.get('maxWriteBatchSize')}) did not move, "
            f"{'so drivers still gate MongoClient.bulk_write off' if (h.get('maxWireVersion') or 0) < 25 else 'but the wire version now allows MongoClient.bulk_write'}. "
            f"{sum(1 for c in claims if c['result_on_1_2_0'].startswith(('reproduced', 'now observed')))} of {len(claims)} ENGINE-TESTS.md bulk-write claims hold at 1.2.0, with one refinement: the quoted cap message is the insert and delete wording; "
            f"update returns '{upd_err.get('errmsg')}'."
        ),
        "confidence": "observed",
    },
    {
        "question": "Do these results show what the managed Azure DocumentDB service does?",
        "answer": (
            "No. They are evidence about the open-source engine and gateway in image documentdb-local:pg17-1.2.0 (extension " + str(ver) + "). Which gateway and engine build Azure runs, the "
            "maxWriteBatchSize its hello advertises, and whether its gateway routes bulkWrite are not observable from here; the earlier Azure run (02-real-time-event-stream-ingestion) only "
            "shows collection-level bulkWrite working there."
        ),
        "confidence": "inconclusive",
    },
]

wire_ms = [w.get("duration_ms") or 0 for s in r["steps"] for w in (s.get("wire_commands") or [])]
total_s = round(sum(s.get("elapsed_s") or 0 for s in r["steps"] if not s["step"].startswith("8")), 3)
longest_step = max((s for s in r["steps"] if not s["step"].startswith("8")), key=lambda s: s.get("elapsed_s") or 0)
timing = (f"The wire steps took {total_s} s in total; the longest step was {longest_step['step']} at {longest_step.get('elapsed_s')} s and the longest captured "
          f"server command took {max(wire_ms) if wire_ms else '?'} ms. ")

r["notes"] = (
    "Scripts: run.py (wire-protocol steps 0a-7b), inspect_container.py (read-only container checks 8a-8e), finalize.py (comparison, conclusions); rerun in that order with "
    "/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python. Step ids that match the 0.117 run.py are the same steps; 4b, 4c, 5c2, 5d, 5e, 6g-6k2, 7b and 8a-8e are new. "
    "The 0.117 per-collection pre-clean drops (0d-drop-*) were replaced by one drop of t_bulk (0d-pre-clean-dropDatabase). Only database t_bulk was created; it was dropped at the end and "
    "confirmed absent (7b). The pg_settings read in 8e is a catalog query over a local psql connection inside the container; it touched no MongoDB database and no table data. Other agents' "
    "tests used the same container concurrently. " + timing + "Every command had a 240 s socket timeout. "
    "The password is not in any script, log or report written here (see password_check, counted without printing it); every string in the report passed through a redactor. Facts observed on documentdb-local are evidence "
    "about the open-source engine and gateway at the version buildInfo and hello report, not proof of managed-service behaviour."
)
r["files"] = {
    "run": os.path.join(HERE, "run.py"),
    "inspect": os.path.join(HERE, "inspect_container.py"),
    "finalize": os.path.join(HERE, "finalize.py"),
    "run_all": os.path.join(HERE, "run_all.sh"),
    "inspect_stdout_log": os.path.join(HERE, "inspect.stdout.log"),
    "stderr_log": os.path.join(HERE, "run.stderr.log"),
    "inspect_raw": INSPECT,
    "report": REPORT,
}
def _password():
    from urllib.parse import unquote, urlsplit
    for line in open("/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/local.env"):
        if line.startswith("LOCAL_URI="):
            v = line.split("=", 1)[1].strip().strip("\"'")
            pw = urlsplit(v).password or ""
            return {x for x in (pw, unquote(pw)) if x}
    return set()


def _count(pwset, text):
    return sum(text.count(x) for x in pwset)


PW = _password()
out_text = json.dumps(r, indent=2)
r["password_check"] = {
    "method": "occurrences of the LOCAL_URI password (raw and URL-decoded) counted in each file in this folder and in the report text before writing; the value is never printed",
    "counts": {fn: _count(PW, open(os.path.join(HERE, fn), errors="replace").read()) for fn in sorted(os.listdir(HERE)) if os.path.isfile(os.path.join(HERE, fn)) and fn != "report.json"},
    "report_json_as_written": _count(PW, out_text),
}
assert r["password_check"]["report_json_as_written"] == 0 and not any(r["password_check"]["counts"].values()), "password found in output files"
json.dump(r, open(REPORT, "w"), indent=2)
assert _count(PW, open(REPORT).read()) == 0
print(json.dumps({"steps": len(r["steps"]), "compared": len(common), "differing": [d["step"] for d in diffs], "conclusions": len(r["conclusions"])}))
for c in claims:
    print("CLAIM:", c["result_on_1_2_0"][:220])
