#!/usr/bin/env python
"""Build report.json for the write-read-concerns reproduce stage from preflight.json, raw_run.json (the tester's
run.py rerun against t_concern_rerun), compare.json (step-by-step comparison with the tester's report) and
extra.json (extra_probes.py). Also checks that the test password appears in no file in this folder.
Rerun order: preflight.py, run.py, compare.py, extra_probes.py, finalize.py (see run_all.sh)."""
import datetime, hashlib, json, os, re, subprocess
from pymongo.uri_parser import parse_uri

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.dirname(HERE)
P = lambda *a: os.path.join(HERE, *a)
SCRATCH = os.path.dirname(B)
MAIN_SRC = os.path.join(SCRATCH, "phase4", "sme", "engine-src")
SRC_965 = os.path.join(B, "bulkwrite-forms-rerun", "src_965b6e7a")


def load(p):
    return json.load(open(p))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


pre, raw, cmp_, extra = load(P("preflight.json")), load(P("raw_run.json")), load(P("compare.json")), load(P("extra.json"))
tester = load(P("tester_snapshot", "report.json"))
cmp_rows = {r["step"]: r for r in cmp_["rows"]}


def slim_wire(w):
    out = []
    for ev in w:
        d = {"event": ev["event"], "command_name": ev["command_name"]}
        for k in ("server_connection_id", "command", "reply", "failure"):
            if k in ev:
                d[k] = ev[k]
        out.append(d)
    return out


def step_rec(s, source, identical=None):
    d = {"id": s["id"], "source": source, "question": s.get("question"), "driver_call": s.get("driver_call"),
         "wire": slim_wire(s.get("wire") or []), "outcome": s.get("outcome")}
    if s.get("outcome") == "ok":
        d["response"] = s.get("response")
    if s.get("error"):
        e = s["error"]
        d["error"] = {k: e.get(k) for k in ("type", "code", "codeName", "errmsg", "errorLabels") if k in e}
        if e.get("code") is None:
            d["error"]["message"] = e.get("message")
    if "observed_after" in s:
        d["observed_after"] = s["observed_after"]
    for k in ("verdict", "matches_decisions", "vs_main_branch_source", "main_branch_expectation", "parsed"):
        if k in s:
            d[k] = s[k]
    d["reading"] = s.get("reading")
    if identical is not None:
        d["identical_to_tester_after_normalisation"] = identical
    return d


steps = []
for s in raw["steps"]:
    row = cmp_rows.get(s["id"], {})
    steps.append(step_rec(s, "rerun of the tester's run.py (database t_concern_rerun)",
                          bool(row.get("key_fields_identical")) and not row.get("normalised_differences")))
for s in extra["steps"]:
    steps.append(step_rec(s, "extra_probes.py (beyond the tester's script; database t_concern_rerun)"))
ci = extra["container_inspection"]
steps.append({"id": "XC.binary_strings_more", "source": "extra_probes.py read-only container inspection",
              "driver_call": ci["binary_strings"]["command"], "wire": [], "outcome": "ok",
              "response": {"rows": ci["binary_strings"]["rows"]},
              "reading": ("The gateway binary contains none of errorLabels, TransientTransactionError, RetryableWriteError, "
                          "UnknownTransactionCommitResult, NoWritesPerformed, writeConcernError, $clusterTime, "
                          "enable_read_concern_validation, 'Unknown writeConcern w tag' or 'writeConcern must be a document', "
                          "but does contain mongoAllowTransactionSnapshot, afterClusterTime, atClusterTime, operationTime, "
                          "maxWriteBatchSize and the main-branch read_concern.rs and read_preference.rs messages probed.")})
steps.append({"id": "XC.pg_settings", "source": "extra_probes.py read-only container inspection",
              "driver_call": ci["pg_settings"]["command"], "wire": [], "outcome": "ok" if ci["pg_settings"]["exit"] == 0 else "error",
              "response": {"exit": ci["pg_settings"]["exit"], "rows": ci["pg_settings"]["output"].splitlines()},
              "reading": ("pg_settings has no setting whose name contains snapshot or concern and no documentdb.mongo* setting, "
                          "and documentdb.maxWriteBatchSize is 25000 at its boot value, which is what hello.maxWriteBatchSize "
                          "advertises.")})
steps.append({"id": "XC.pg_file_settings", "source": "extra_probes.py read-only container inspection",
              "driver_call": ci["pg_file_settings"]["command"], "wire": [], "outcome": "ok" if ci["pg_file_settings"]["exit"] == 0 else "error",
              "response": {"exit": ci["pg_file_settings"]["exit"], "rows": ci["pg_file_settings"]["output"].splitlines()},
              "reading": ("postgresql.conf sets five documentdb.* parameters (index handler, background worker, RUM load "
                          "option) and none about read or write concern or snapshot.")})
steps.append({"id": "XC.host_config_and_setup_keys", "source": "extra_probes.py read-only container inspection",
              "driver_call": ci["host_config_file"]["command"] + "; " + ci["setup_configuration_keys_only"]["command"],
              "wire": [], "outcome": "ok",
              "response": {"host_config_file": ci["host_config_file"]["output"],
                           "setup_configuration": ci["setup_configuration_keys_only"]["summary"]},
              "reading": ("The host-config file holds only SendShutdownResponses and the setup configuration has no read or "
                          "write concern key, so neither file is where a snapshot or write-concern switch would live on this "
                          "build.")})

src_facts = {
    "main_branch_local_copies": {"dir": MAIN_SRC, "note": "saved by the DECISIONS.md topic 9 research, fetched 2026-11-25; data only",
                                 "sha256": {f: sha(os.path.join(MAIN_SRC, f)) for f in
                                            ("validation.rs", "read_concern.rs", "write_concern.rs", "read_preference.rs", "dynamic.rs")}},
    "rev_965b6e7a_local_copies": {"dir": SRC_965, "note": ("saved by the bulkwrite-forms-rerun stage from raw.githubusercontent.com at the "
                                                          "image's org.opencontainers.image.revision; data only"),
                                  "sha256": {f: sha(os.path.join(SRC_965, f)) for f in
                                             ("pg_documentdb_gw_documentdb_gateway_core_src_configuration_dynamic.rs",
                                              "pg_documentdb_gw_documentdb_gateway_core_src_configuration_pg_configuration.rs",
                                              "pg_documentdb_gw_documentdb_gateway_src_main.rs",
                                              "pg_documentdb_gw_documentdb_gateway_core_src_requests_request_type.rs")}},
    "facts": [
        "main validation.rs validate_request(): 'let Some(request_transaction_info) = request.transaction_info() else { return Ok(()); }' and 'if request_transaction_info.auto_commit { ... return Ok(()); }' precede the Snapshot (allow_transaction_snapshot) and Available/Linearizable CommandNotSupported checks, so on main those checks run only for multi-document transaction requests.",
        "main dynamic.rs:129-130 defines enable_write_concern_validation (default true) and :137-138 enable_read_concern_validation (default true); dynamic.rs at 965b6e7a defines neither.",
        "965b6e7a pg_configuration.rs load_configurations(): the host-config JSON supplies only IsPrimary and SendShutdownResponses; every other key comes from pg_settings (and pg_file_settings when enabled) with the prefix 'documentdb.' stripped (main.rs passes vec![\"documentdb.\".to_owned()]).",
        "965b6e7a pg_configuration.rs:413-414: allow_transaction_snapshot() = get_bool(\"mongoAllowTransactionSnapshot\", false).",
        "965b6e7a dynamic.rs:145-146: max_write_batch_size() = get_i32(\"maxWriteBatchSize\", 100_000); ismaster.rs:70 advertises it as hello.maxWriteBatchSize.",
        "request_type.rs is byte-identical at main (local copy) and 965b6e7a; it has GetDefaultRWConcern but no SetDefaultRWConcern and maps unknown names to CommandNotFound \"Command '{cmd_name}' not found.\" (lines 713-714).",
        "pymongo 4.20.1 network_layer.py:755 raises ProtocolError('Got response id ... but expected ...') when a reply's responseTo does not match, and synchronous/command_runner.py:432 sets OP_MSG MORE_TO_COME for unacknowledged writes, so a stray reply to a w:0 write would have failed the next command on that connection.",
    ],
}

conclusions = [
    {"question": "Which writeConcern values does engine 1.2.0 accept on insert and update?",
     "verdict": "confirmed",
     "evidence": "Rerun steps A.raw.* and B.* are identical to the tester's: every insert {n:1, ok:1.0}, every update {ok:1.0, nModified:1, n:1}, no writeConcernError, writes applied.",
     "note": ("'All of them' means every value tested. The extras go further: XW.* (writeConcern 'notADocument' and 1, w -1, 50, 51, NaN, true, [1], "
              "null, {}, {dc:'east'}, j 'yes', fsync 'yes', provenance 'bogus' and 5, unknown sub-field foo), XW2.* (delete and findAndModify "
              "with w:2 and 'myTag') and XT.transaction.commit_writeConcern_w2 were all accepted and applied, so this gateway build does not "
              "inspect writeConcern at all. The behaviour belongs to the gateway; 'engine 1.2.0' is shorthand for gateway plus extension at 1.2.0.")},
    {"question": "Does engine 1.2.0 reject w:2 and w:3 with BadValue, as DECISIONS.md topic 9 states from the main-branch write_concern.rs?",
     "verdict": "confirmed",
     "evidence": "Rerun A/B w2 and w3 steps accepted and applied; X.binary_strings counts reproduced (0 for every main-branch write_concern.rs literal).",
     "note": ("'Build difference, not a configuration setting' is an inference, not an observation, but it is now better supported. dynamic.rs at "
              "the image's OCI revision 965b6e7a has no enable_write_concern_validation; main's dynamic.rs:129-130 has it, defaulting to true. "
              "The gateway binary also lacks main's 'Unknown writeConcern w tag' and 'writeConcern must be a document' literals. "
              "pg_settings and pg_file_settings hold no write-concern parameter.")},
    {"question": "Is w:0 honored?",
     "verdict": "confirmed",
     "evidence": "Rerun B.driver.insert_one.w0 and B.driver.update_one.w0 gave acknowledged=False, a follow-up on the same server connection, 0 connections created and 0 closed, and writes visible to a separate client.",
     "note": ("pymongo 4.20.1 raises ProtocolError on a responseTo mismatch, so a stray reply would have shown up. Extra steps "
              "XU.driver.insert_one.w0_duplicate_key and XU.driver.update_one.w0_invalid_operator show that failing unacknowledged writes "
              "also get no reply, not even an error. The connection stays usable, and the failed writes change nothing.")},
    {"question": "Are j and wtimeout honored?",
     "verdict": "confirmed",
     "evidence": "Rerun j_true, j_false and wtimeout-1 steps on raw, driver and client paths gave replies identical to w:1.",
     "note": ("The answer is correctly limited to 'accepted'. A single node cannot show durability or replication waits, and a real MongoDB "
              "single node would not time out at 1 ms either. The extras add that j:'yes', fsync:'yes', wtimeout 'abc' and wtimeout -5 are "
              "also accepted, so these fields are not even type-checked.")},
    {"question": "Which readConcern levels are accepted outside a transaction on 1.2.0?",
     "verdict": "confirmed",
     "evidence": "Rerun C.raw.find.*, C.driver.find.* and C.raw.aggregate.* match the tester's exactly. The 'Majority' and 'bogus' levels gave 2 BadValue, afterClusterTime Timestamp(1,1) gave 20 and atClusterTime gave 72.",
     "note": ("The extras confirm main's read_concern.rs rules on 1.2.0: count and distinct accept available, linearizable and "
              "snapshot, ping accepts linearizable, and ping rejects level 'bogus' with 2. Level 1 gives 14 TypeMismatch, level '' gives 2, and an unknown sub-field gives "
              "40415 \"BSON field 'readConcern.foo' is an unknown field\". Provenance 'bogus' gives 2. A non-timestamp afterClusterTime or a "
              "null atClusterTime gives 14, and a non-document readConcern gives 14. One nuance: afterClusterTime Timestamp(0,0) gives 72 "
              "InvalidOptions, not 20, so the tester's '20 IllegalOperation' holds only for non-zero timestamps.")},
    {"question": "Is snapshot readConcern honored outside a transaction?",
     "verdict": "confirmed (now observed directly)",
     "evidence": "XS.snapshot_session.two_reads_with_concurrent_update; XS.cursor.snapshot.getMore_after_concurrent_update; XS.cursor.none.getMore_after_concurrent_update",
     "note": ("The tester inferred this from the missing atClusterTime. It is now observed. In one pymongo snapshot session, the second "
              "find saw another client's update (v=2 after v=1), and the session never recorded a snapshot time. A single find cursor with "
              "readConcern snapshot and batchSize 2 returned the concurrently updated v=2 in its getMore batches, as the no-readConcern "
              "control did. MongoDB would return v=1 in both cases.")},
    {"question": "Why do available, linearizable and snapshot differ from the DECISIONS.md claim of CommandNotSupported?",
     "verdict": "confirmed on behaviour, corrected on cause",
     "evidence": "Rerun C2.diag.transaction.{snapshot,available,linearizable} gave 115 with the main-branch messages, and C2 majority committed; XT.transaction.readConcern_local was accepted; XT.transaction.readConcern_on_second_statement gave 72 InvalidOptions \"Read concern cannot be defined after transaction has started\".",
     "note": ("The difference is not specific to 1.2.0. In the main-branch validation.rs (local copy fetched 2026-11-25), validate_request "
              "returns Ok(()) when a request has no transaction info or autocommit is true. Main therefore also checks the level only inside "
              "multi-document transactions. DECISIONS.md dropped that scope when it paraphrased the source. See disputed.")},
    {"question": "Does causal consistency work at the protocol level?",
     "verdict": "confirmed",
     "evidence": "Rerun: 0 of 113 captured replies had operationTime or $clusterTime, and pymongo sent $clusterTime 0 times. C.driver.causal_session.majority_find had session.operation_time null and sent readConcern {level:'majority'} only. Extra hello had neither field.",
     "note": ("The gateway binary has no '$clusterTime' literal but does have one 'operationTime' literal. 'Returns no operationTime' is "
              "therefore an observation for the commands exercised, not a structural guarantee.")},
    {"question": "Which readPreference modes are accepted on find, via driver options and raw $readPreference?",
     "verdict": "confirmed",
     "evidence": "Rerun D.* identical to the tester's.",
     "note": ("The extras XP.* show main's remaining read_preference.rs rules on 1.2.0. These give 9 FailedToParse: {} ('mode' is "
              "required), mode 1, a non-document $readPreference, primary with hedge {enabled:false}, and maxStalenessSeconds -1 or 1.5. "
              "nearest with hedge {enabled:false} is accepted, and so is maxStalenessSeconds 5, although MongoDB requires at least 90. "
              "primary with tags [{}] gives 133.")},
    {"question": "What do getDefaultRWConcern and setDefaultRWConcern do?",
     "verdict": "confirmed",
     "evidence": "Rerun E.* identical to the tester's; XE.admin.getDefaultRWConcern.comment was accepted with the same constant document.",
     "note": ("Source agrees: request_type.rs, byte-identical at main and 965b6e7a, has GetDefaultRWConcern but no SetDefaultRWConcern. "
              "It maps unknown names to CommandNotFound \"Command '{cmd_name}' not found.\".")},
    {"question": "Did any error reply carry errorLabels?",
     "verdict": "confirmed, and broader than stated",
     "evidence": "The rerun had 26 CommandFailed events (the 23 step errors plus 3 abortTransaction replies with 251 NoSuchTransaction 'Cannot continue transaction N', N = 2, 3, 4), none with errorLabels; no extra-probe error had them either.",
     "note": ("The gateway binary and the extension .so contain no 'errorLabels', 'TransientTransactionError', 'RetryableWriteError', "
              "'UnknownTransactionCommitResult' or 'NoWritesPerformed' literal. This build appears unable to emit error labels at all. "
              "Literal absence is strong but not conclusive evidence.")},
    {"question": "Does this establish managed Azure DocumentDB behaviour?",
     "verdict": "confirmed",
     "evidence": "Scope statement only.",
     "note": "Correct. 'inconclusive' is an odd label for a 'No', but it rightly signals that Azure behaviour stays unknown (DECISIONS topic 9 open item 8)."},
]

disputed = [
    {"question": ("Step readings for the 10 readConcern mismatches (C.raw.find, C.driver.find and C.raw.aggregate with available, "
                  "linearizable and snapshot, plus C.driver.snapshot_session.find), which end 'which differs from DECISIONS.md topic 9 (it "
                  "expects rejection with CommandNotSupported ... per the main-branch gateway source)'. Also conclusion 7's 'On 1.2.0 the check "
                  "fires only ...' and the notes' reading that the 24 mismatches show main-branch source claims failing on 1.2.0."),
     "reason": ("Read in full, the main-branch source does not expect rejection outside a transaction. validation.rs validate_request "
                "(local copy saved by the DECISIONS research, fetched 2026-11-25) returns Ok(()) before the CommandNotSupported checks when "
                "the request has no transaction info or autocommit is true. 1.2.0 behaves as main reads, and the mismatch is DECISIONS.md "
                "dropping the transaction scope. Only the 14 writeConcern mismatches are build differences between 1.2.0 and main.")},
    {"question": ("X.gateway_dynamic_configuration reading: 'no writeConcern, readConcern or snapshot switch is set there and the gateway "
                  "runs on its compiled defaults for them'."),
     "reason": ("The conclusion does not follow from the file inspected. At 965b6e7a, pg_configuration.rs takes only IsPrimary and "
                "SendShutdownResponses from that JSON file. All other dynamic keys come from PostgreSQL pg_settings and pg_file_settings with "
                "the 'documentdb.' prefix stripped, including mongoAllowTransactionSnapshot (default false), and the tester did not read "
                "those. A read-only query here found no snapshot or concern parameter, so the default false does apply, consistent with 115 "
                "in C2. That rests on pg_settings, though, not on the file. The same mechanism supplies hello.maxWriteBatchSize 25000 from "
                "documentdb.maxWriteBatchSize.")},
]

extra_observations = [
    ("No writeConcern validation exists on the 1.2.0 gateway, not even a type check. A string or integer writeConcern; w -1, 50, 51, "
     "NaN, true, [1], null, {} or {dc:'east'}; j or fsync 'yes'; provenance 'bogus' or 5; and an unknown sub-field were all accepted with "
     "{n:1, ok:1.0} and the write applied (XW.*). Main's write_concern.rs rejects every one except {} and null. The gateway binary has no "
     "'writeConcern' literal at all."),
    ("writeConcern {w:2} and {w:'myTag'} are also accepted and applied on delete and findAndModify (XW2.*). commitTransaction with "
     "writeConcern {w:2} returns {ok:1.0} and commits (XT.transaction.commit_writeConcern_w2)."),
    ("Snapshot readConcern outside a transaction is directly observed not to pin reads. A snapshot session's second find saw a concurrent "
     "update. A readConcern-snapshot cursor's getMore batches saw concurrent updates, exactly like the no-readConcern control, so find "
     "cursors on this build are not snapshot-isolated across getMore."),
    ("readConcern sub-field validation on 1.2.0 matches main's read_concern.rs for every rule probed. It covers TypeMismatch for non-string "
     "level, non-timestamp afterClusterTime, null atClusterTime and non-document readConcern, and BadValue for '' and bad provenance. It "
     "also covers 40415 UnknownBsonField for unknown sub-fields and 72 for afterClusterTime Timestamp(0,0). The level check applies to "
     "any command (ping with level 'bogus' gives 2)."),
    ("Inside a transaction, a readConcern on a later statement gives 72 InvalidOptions \"Read concern cannot be defined after transaction "
     "has started\", matching DECISIONS (validation.rs:99-106); this was not tested by the tester. Transaction readConcern 'local' is "
     "accepted."),
    ("The main-branch validation.rs gates the CommandNotSupported readConcern checks on multi-document transactions. Several DECISIONS.md "
     "texts are therefore mis-scoped: the topic 9 settled readConcern item; the doc-gap recommendation at DECISIONS.md:404, which says "
     "'readConcern available/linearizable rejected with CommandNotSupported' and 'w>=2 rejected with BadValue', both wrong for 1.2.0; and "
     "the kit-gap line at DECISIONS.md:416 ('writeConcern/readConcern are validated and ignored'), wrong for writeConcern on 1.2.0."),
    ("The snapshot switch on this build is the PostgreSQL setting documentdb.mongoAllowTransactionSnapshot, which the gateway reads "
     "through pg_settings (pg_configuration.rs:413-414, default false). The container defines no such setting, so transaction snapshot "
     "is off by default and not through the host-config file. For DECISIONS open item 3 this shows only the mechanism in this "
     "build; what Azure sets cannot be observed here."),
    ("hello.maxWriteBatchSize 25000 comes from the extension parameter documentdb.maxWriteBatchSize (setting 25000, boot_val 25000, source "
     "default), which the gateway reads through pg_settings and which overrides its compiled default of 100,000. For DECISIONS open item "
     "4: in this build, where the extension parameter is at its default, the gateway advertises 25,000. The mechanism is observed "
     "locally; the Azure value cannot be observed here."),
    ("Failing unacknowledged writes (duplicate-key insert, $bogusOp update with w:0) get no reply and leave the single pooled connection "
     "usable with no churn (XU.*)."),
    ("The 3 abortTransaction replies in C2 (251 NoSuchTransaction 'Cannot continue transaction N', N = 2, 3, 4) carry no errorLabels. The binaries "
     "contain no TransientTransactionError, RetryableWriteError, UnknownTransactionCommitResult, NoWritesPerformed or errorLabels "
     "literal."),
    ("readPreference maxStalenessSeconds 5 is accepted with nearest, although MongoDB requires at least 90 s; DECISIONS states no "
     "minimum. The other main read_preference.rs parse rules hold on 1.2.0 (XP.*)."),
    ("The tester's raw report embeds a hard-coded cross_references sentence calling it 'the first executed run'. The rerun's raw_run.json "
     "repeats it verbatim, so it is stale there. Script-path and database fields are otherwise correct."),
]

pw = parse_uri([l.split("=", 1)[1].strip().strip("'\"") for l in open(os.path.join(SCRATCH, "engine-tests", "local.env"))
                if l.strip().startswith("LOCAL_URI=")][0]).get("password") or ""
leaks = {}
for root, _, files in os.walk(HERE):
    for f in files:
        p = os.path.join(root, f)
        try:
            t = open(p, "rb").read()
        except OSError:
            continue
        if pw and pw.encode() in t:
            leaks[os.path.relpath(p, HERE)] = t.count(pw.encode())

eng = raw["engine"]
report = {
    "test": "write-read-concerns",
    "stage": "reproduce",
    "database": "t_concern_rerun",
    "database_fresh_before_run": {"t_concern_rerun_exists_before_run": pre["t_concern_rerun_exists_before_run"], "checked_at": pre["at"],
                                  "command": pre["command"]},
    "ran_at": {"rerun": [raw["run_started_at"], raw["run_finished_at"]], "extra_probes": [extra["started_at"], extra["finished_at"]],
               "finalized_at": datetime.datetime.now(datetime.timezone.utc).isoformat()},
    "target": raw["target"],
    "engine_version": {"hello.internal.documentdb_versions": eng["hello.internal.documentdb_versions"],
                       "buildInfo.version": eng["buildInfo.version"],
                       "buildInfo.version_meaning": "MongoDB compatibility version the gateway advertises, not the engine version",
                       "version_txt": next(s for s in raw["steps"] if s["id"] == "X.version_txt")["response"]["output"],
                       "image": raw["container"]["docker_inspect"]["output"],
                       "oci_revision_label": "965b6e7ad1c49aefb983a412a3fea0ff637cd7f1",
                       "hello.msg": eng["hello.msg"], "hello.maxWireVersion": eng["hello.maxWireVersion"],
                       "driver_topology": [eng["driver_topology_type"], eng["driver_server_types"]],
                       "driver": raw["driver"]},
    "evidence_scope": ("Facts observed on documentdb-local are evidence about the open-source DocumentDB engine and gateway at the build this "
                       "container reports. buildInfo.version is 7.0.0, the advertised MongoDB compatibility version; "
                       "hello.internal.documentdb_versions is ['1.2-0','1.2.0']; /version.txt names commit 965b6e7a. The build runs as a "
                       "single node that pymongo sees as a mongos. Nothing here proves managed Azure DocumentDB behaviour (DECISIONS.md topic "
                       "9 open item 8), and a single node cannot show replication, failover or HA durability effects. Source excerpts come "
                       "from local copies saved by earlier stages, not from this run."),
    "how_the_script_was_copied": {"tester_script": os.path.join(B, "write-read-concerns", "run.py"),
                                  "tester_script_sha256": sha(P("tester_snapshot", "run.py")),
                                  "rerun_script": P("run.py"), "rerun_script_sha256": sha(P("run.py")),
                                  "diff": open(P("script.diff")).read(),
                                  "changes": ["DB = 't_concern' -> 't_concern_rerun'",
                                              "REPORT report.json -> raw_run.json (so this report.json is not overwritten)"],
                                  "test_logic_changed": False},
    "comparison_with_tester": {**cmp_["summary"],
                               "tester_report_original": os.path.join(B, "write-read-concerns", "report.json"),
                               "tester_report_sha256": sha(P("tester_snapshot", "report.json")),
                               "normalisation": ("database name t_concern_rerun mapped to t_concern; dropped durations, request and "
                                                 "connection ids, lsid, txnNumber, localTime; transaction numbers and connection ids in "
                                                 "readings masked"),
                               "wire_counts_both_runs": {"commands": 113, "commands_with_lsid": 111,
                                                         "commands_without_lsid": ["insert w:0", "update w:0"],
                                                         "$clusterTime_sent": 0, "replies_with_operationTime": 0,
                                                         "replies_with_$clusterTime": 0, "CommandFailed": 26,
                                                         "CommandFailed_with_errorLabels": 0}},
    "field_notes": ("steps[].error.errorLabels null means the server reply had no errorLabels field. steps[].wire holds the exact "
                    "command documents pymongo sent and the exact replies or failures (relaxed Extended JSON). For w:0 writes pymongo "
                    "publishes a synthetic {ok: 1} because no reply is read."),
    "conclusion_verdicts": conclusions,
    "source_checks_behind_verdicts": src_facts,
    "disputed": disputed,
    "extra_observations": extra_observations,
    "steps": steps,
    "files": {k: P(v) for k, v in {"report": "report.json", "rerun_script": "run.py", "rerun_raw_report": "raw_run.json",
                                    "rerun_log": "run.log", "script_diff": "script.diff", "preflight": "preflight.py",
                                    "preflight_output": "preflight.json", "compare": "compare.py", "compare_output": "compare.json",
                                    "extra_probes": "extra_probes.py", "extra_output": "extra.json", "extra_log": "extra.log",
                                    "finalize": "finalize.py", "run_all": "run_all.sh", "tester_snapshot": "tester_snapshot"}.items()},
    "safety": {"databases_written": ["t_concern_rerun (created by run.py and dropped; recreated by extra_probes.py and dropped; confirmed "
                                     "not listed afterwards)"],
               "admin_commands": "getDefaultRWConcern (read-only), setDefaultRWConcern (rejected 59; values mirrored the defaults), "
                                 "commitTransaction/abortTransaction (transaction control), listDatabases",
               "container": "read-only: docker inspect/ps, cat of /version.txt and config files, ps, grep over binaries, SELECT on "
                            "pg_settings/pg_file_settings with default_transaction_read_only=on; nothing modified",
               "password_occurrences_in_output_files": sum(leaks.values()), "files_with_password": sorted(leaks)},
}
open(P("report.json"), "w").write(json.dumps(report, indent=2))
print("report.json written:", len(steps), "steps;", "password occurrences:", sum(leaks.values()))
