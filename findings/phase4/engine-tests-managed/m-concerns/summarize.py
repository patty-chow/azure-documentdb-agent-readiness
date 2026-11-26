#!/usr/bin/env python
"""Adds conclusions and DECISIONS corrections to report.json (from the observed steps) and
prints a compact per-step list. Reads only report.json; never touches the cluster."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import ENV, redact  # noqa: E402

PATH = os.path.join(HERE, "report.json")
r = json.load(open(PATH))
S = {s["id"]: s for s in r["steps"]}


def err(sid):
    e = S[sid].get("error") or {}
    return e.get("code"), e.get("codeName"), e.get("errmsg")


# guard: conclusions below quote these exact observations; stop if a rerun changed them
checks = {
    "A.raw.insert.w2": (2, "BadValue", "w value 2 exceeds the number of data-bearing voting members"),
    "A.raw.insert.w3": (2, "BadValue", "w value 3 exceeds the number of data-bearing voting members"),
    "A.raw.insert.w_custom_tag": (2, "BadValue", "Unknown writeConcern w tag: 'myTag'"),
    "C.raw.find.readConcern.Majority_mixed_case": (2, "BadValue", "Invalid readConcern level: 'Majority'"),
    "C.raw.find.readConcern.majority_afterClusterTime": (20, "IllegalOperation", "readConcern.afterClusterTime is not supported on this deployment"),
    "C.raw.find.readConcern.snapshot_atClusterTime": (72, "InvalidOptions", "readConcern.atClusterTime is not supported"),
    "C.driver.causal_session.advance_operation_time": (20, "IllegalOperation", "readConcern.afterClusterTime is not supported on this deployment"),
    "D.raw.find.$readPreference.secondary": (133, "FailedToSatisfyReadPreference", "no server available for query with ReadPreference secondary"),
    "D.raw.find.$readPreference.secondaryPreferred_tags": (133, "FailedToSatisfyReadPreference", "no server available for query with specified tag set list"),
    "D.raw.find.$readPreference.nearest_hedge_enabled": (2, "BadValue", "hedged reads are not supported"),
    "D.raw.find.$readPreference.primary_maxStalenessSeconds_90": (9, "FailedToParse", "mode 'primary' does not allow for 'maxStalenessSeconds'"),
    "E.mt_concern.getDefaultRWConcern": (13, "Unauthorized", "Only the admin database can process getDefaultRWConcern."),
    "E.admin.getDefaultRWConcern.unknown_field": (40415, "UnknownBsonField", "Not a valid value for getDefaultRWConcern: foo"),
    "E.admin.setDefaultRWConcern.probe_no_fields": (59, "CommandNotFound", "Command 'setDefaultRWConcern' not found."),
    "X.txn.readConcern.available": (115, "CommandNotSupported", "'Available' read concern is not supported"),
    "X.txn.readConcern.linearizable": (115, "CommandNotSupported", "'Linearizable' read concern is not supported"),
}
for sid, exp in checks.items():
    assert err(sid) == exp, (sid, err(sid), exp)
for sid in ("C.raw.find.readConcern.available", "C.raw.find.readConcern.linearizable", "C.raw.find.readConcern.snapshot",
            "C.driver.find.readConcern.snapshot", "X.txn.readConcern.snapshot", "X.txn.readConcern.majority", "X.txn.readConcern.local",
            "B.driver.w0.same_connection_followup", "X.txn.snapshot_plus_w_majority_update"):
    assert S[sid]["outcome"] == "ok", sid
assert S["X.txn.readConcern.snapshot.isolation"]["verdict"] == "accepted_and_honoured"
assert S["X.txn.readConcern.majority.isolation"]["verdict"] == "accepted_read_committed"
assert S["X.txn.readConcern.local.isolation"]["verdict"] == "accepted_read_committed"
assert S["C.driver.snapshot_session.find"]["verdict"] == "accepted_not_honoured"
assert S["C.driver.find.readConcern.snapshot.getMore_consistency"]["verdict"] == "accepted_not_honoured"
assert S["C.driver.causal_session.after_hello_in_session"]["verdict"] == "rejected"
assert r["config_changes"] == []

CONCLUSIONS = [
    {"question": "Which writeConcern w values does the managed service accept on insert and update, and is a rejected write applied?",
     "answer": ("w:0, w:1 and w:'majority' are accepted on raw insert and update commands, on collection-level WriteConcern objects and "
                "through MongoClient(w='majority'), each returning ok:1 with no writeConcernError. w:2 and w:3 (raw, driver and "
                "MongoClient(w=2)) are rejected before execution with code 2 BadValue \"w value N exceeds the number of data-bearing "
                "voting members\", with no errorLabels, and the document or update is not applied. The tag w:'myTag' is rejected with "
                "code 2 BadValue \"Unknown writeConcern w tag: 'myTag'\". This matches the DECISIONS reading of the open-source gateway "
                "(validated, then ignored; numeric w of 2 or more refused on this HA-disabled cluster)."),
     "vs_open_source": "not_tested_locally", "confidence": "observed",
     "steps": ["A.raw.*", "B.driver.*", "B.client.*"]},
    {"question": "Are j:true and j:false accepted, and do they change anything?",
     "answer": ("Accepted silently. {w:1, j:true} and {w:1, j:false} as raw commands, WriteConcern(j=True) and WriteConcern(j=False) "
                "(sent as {j:true} and {j:false}) and MongoClient(journal=True) all return ok:1 with no error on insert and update. "
                "Nothing observable changes; any difference in journaling cannot be seen from the data plane."),
     "vs_open_source": "not_tested_locally", "confidence": "observed",
     "steps": ["A.raw.*.w1_j_true", "A.raw.*.w1_j_false", "B.driver.*.j_true", "B.driver.*.j_false",
               "B.client.w_majority_wTimeoutMS_1_journal_true"]},
    {"question": "Is wtimeout / wTimeoutMS 1 honoured?",
     "answer": ("Accepted silently. Raw {w:'majority', wtimeout:1}, WriteConcern(w='majority', wtimeout=1) and MongoClient(w='majority', "
                "wTimeoutMS=1, journal=True) succeed on insert and update with no writeConcernError and no WTimeoutError. On a "
                "single-node cluster there is no replication wait for the timeout to cut short, so it has no observable effect."),
     "vs_open_source": "not_tested_locally", "confidence": "observed",
     "steps": ["A.raw.*.w_majority_wtimeout_1", "B.driver.*.w_majority_wtimeout_1", "B.client.w_majority_wTimeoutMS_1_journal_true"]},
    {"question": "Is w:0 honoured?",
     "answer": ("Yes, at the protocol level. PyMongo sends w:0 writes as unacknowledged OP_MSG messages (moreToCome, no lsid). Two such "
                "inserts followed by an acknowledged find and count on the same server connection succeeded, so the gateway sends no "
                "reply to moreToCome messages. The writes were readable within 1 s, and a duplicate _id under w:0 raised nothing, "
                "whereas the default write concern raised DuplicateKeyError 11000 (no codeName) \"Duplicate key violation on the "
                "requested collection: Index '_id_'\". A raw db.command insert with writeConcern {w:0} is not sent with moreToCome, so "
                "the gateway replies in full ({n:1, ok:1}) and still reports writeErrors code 11000 for a duplicate."),
     "vs_open_source": "not_tested_locally", "confidence": "observed",
     "steps": ["B.driver.insert_one.w0", "B.driver.update_one.w0", "B.driver.w0.same_connection_followup",
               "B.driver.insert_one.w0_duplicate_key", "B.driver.insert_one.default_wc_duplicate_key", "A.raw.insert.w0",
               "A.raw.insert.w0_duplicate_key"]},
    {"question": "Which readConcern levels are accepted outside a transaction, and with what effect?",
     "answer": ("local, majority, available, linearizable and snapshot are all accepted on raw find, on driver find_one with "
                "ReadConcern objects and on raw aggregate (majority and snapshot), returning the document with ok:1. On this "
                "single-node cluster local, majority, available and linearizable have no observable effect. Level parsing is "
                "case-sensitive: 'Majority' fails with code 2 BadValue \"Invalid readConcern level: 'Majority'\". This differs from the "
                "DECISIONS settled item, which says (from the open-source gateway source) that available and linearizable are rejected "
                "with CommandNotSupported and that snapshot is rejected unless configured. On the managed service those rejections "
                "apply only inside transactions."),
     "vs_open_source": "not_tested_locally", "confidence": "observed",
     "steps": ["C.raw.find.readConcern.*", "C.driver.find.readConcern.*", "C.raw.aggregate.readConcern.*",
               "C.raw.find.readConcern.Majority_mixed_case"]},
    {"question": "Is readConcern snapshot honoured outside a transaction?",
     "answer": ("No. It is accepted, but replies carry no atClusterTime, so a PyMongo snapshot session (start_session(snapshot=True)) "
                "cannot pin a point in time: its second read returned a document inserted after the first read. A snapshot cursor "
                "with batchSize 2 returned, in a later getMore, a document inserted between batches, exactly as the local control "
                "did. An explicit readConcern {level:'snapshot', atClusterTime: ts} fails with code 72 InvalidOptions "
                "\"readConcern.atClusterTime is not supported\". Outside a transaction, snapshot gives at most a per-batch view."),
     "vs_open_source": "not_tested_locally", "confidence": "observed",
     "steps": ["C.raw.find.readConcern.snapshot", "C.driver.snapshot_session.find",
               "C.driver.find.readConcern.snapshot.getMore_consistency", "C.driver.find.readConcern.local.getMore_consistency",
               "C.raw.find.readConcern.snapshot_atClusterTime"]},
    {"question": "Which readConcern levels are accepted inside a transaction, compared with documentdb-local?",
     "answer": ("snapshot, majority and local are accepted (find, then commitTransaction ok:1), and the canonical "
                "startTransaction(readConcern snapshot, writeConcern w:'majority') with an update commits. available and linearizable "
                "fail on the first statement with code 115 CommandNotSupported \"'Available' read concern is not supported\" and "
                "\"'Linearizable' read concern is not supported\", with no errorLabels. Compared with the open-source transactions-labels "
                "test (documentdb-local 0.117), majority and local behave the same, while snapshot is different: the local engine "
                "rejected it with code 115 \"'Snapshot' read concern is not supported\". This settles DECISIONS open item 3 for this "
                "cluster: the managed service accepts snapshot in transactions."),
     "vs_open_source": "different", "confidence": "observed",
     "steps": ["X.txn.readConcern.snapshot", "X.txn.readConcern.majority", "X.txn.readConcern.local",
               "X.txn.readConcern.available", "X.txn.readConcern.linearizable", "X.txn.snapshot_plus_w_majority_update"]},
    {"question": "Does readConcern snapshot give a stable snapshot inside a transaction, and what do local and majority give?",
     "answer": ("Snapshot is honoured: in a snapshot transaction, a second read did not see a document inserted or an update committed "
                "by another client after the first read. In local and majority transactions, the second read saw both. That is "
                "read-committed behaviour: each statement sees data committed before it started. An application that needs "
                "repeatable reads inside a transaction must request readConcern snapshot explicitly. (One trial per level.)"),
     "vs_open_source": "not_tested_locally", "confidence": "observed",
     "steps": ["X.txn.readConcern.snapshot.isolation", "X.txn.readConcern.majority.isolation", "X.txn.readConcern.local.isolation"]},
    {"question": "Do causally consistent sessions work?",
     "answer": ("Only because the session never learns an operation time. Data-command replies (insert, update, find, getMore, "
                "aggregate, commitTransaction, getDefaultRWConcern and others) carry no operationTime and no $clusterTime; only hello "
                "carries operationTime. A PyMongo causal session therefore normally sends no afterClusterTime, and its operations "
                "succeed. Once the session has an operation time (hello run with session=s, or s.advance_operation_time(ts), which is "
                "MongoDB's way to chain causality across sessions), PyMongo 4.20 adds readConcern {afterClusterTime} to the next reads "
                "and writes. Each of them fails with code 20 IllegalOperation \"readConcern.afterClusterTime is not supported on this "
                "deployment\", and the insert is not applied. A raw readConcern {level:'majority', afterClusterTime} fails the same way. "
                "This matches the main-branch read_concern.rs reported in DECISIONS, not the release/1.0-RC2 behaviour (silently "
                "accepted) described in issue #770."),
     "vs_open_source": "not_tested_locally", "confidence": "observed",
     "steps": ["C.driver.causal_session.afterClusterTime", "C.driver.causal_session.after_hello_in_session",
               "C.driver.causal_session.advance_operation_time", "C.raw.find.readConcern.majority_afterClusterTime",
               "X.txn.causal_session_afterClusterTime_at_start"]},
    {"question": "Which readPreference modes are accepted on a find, and are they honoured?",
     "answer": ("PyMongo sees one Mongos (hello msg 'isdbgrid', no setName or hosts) and sends $readPreference for every non-primary "
                "mode. primary (omitted by the driver, explicit in the raw command), primaryPreferred, secondaryPreferred and nearest "
                "are accepted and served by the single endpoint. secondary is rejected, whether set as a collection option, a client "
                "option or in a raw command, with code 133 FailedToSatisfyReadPreference \"no server available for query with "
                "ReadPreference secondary\" and no errorLabels. Extras: any tags fail with 133 \"no server available for query with "
                "specified tag set list\"; hedge {enabled:true} fails with 2 BadValue \"hedged reads are not supported\"; "
                "secondaryPreferred with maxStalenessSeconds 90 is accepted; primary with maxStalenessSeconds fails with 9 FailedToParse "
                "\"mode 'primary' does not allow for 'maxStalenessSeconds'\". With HA disabled there is one endpoint, so no routing can "
                "be observed. All of this matches DECISIONS."),
     "vs_open_source": "not_tested_locally", "confidence": "observed",
     "steps": ["D.driver.find.readPreference.*", "D.raw.find.$readPreference.*", "D.client.readPreference.*"]},
    {"question": "What do getDefaultRWConcern and setDefaultRWConcern do?",
     "answer": ("getDefaultRWConcern on admin returns {defaultReadConcern:{level:'majority'}, defaultWriteConcern:{w:'majority', "
                "wtimeout:0}, defaultReadConcernSource:'implicit', defaultWriteConcernSource:'implicit', ok:1}, the constant DECISIONS "
                "predicted. It is the same with inMemory:true and unchanged after the set attempts. On mt_concern it fails with code 13 "
                "Unauthorized \"Only the admin database can process getDefaultRWConcern.\", and an unknown field fails with code 40415 "
                "UnknownBsonField \"Not a valid value for getDefaultRWConcern: foo\". setDefaultRWConcern does not exist: with no fields, "
                "with defaultWriteConcern {w:1} and with defaultReadConcern {level:'local'} it fails with code 59 CommandNotFound "
                "\"Command 'setDefaultRWConcern' not found.\". No default was changed. On this single-node cluster, the reported "
                "majority defaults have no observable effect."),
     "vs_open_source": "not_tested_locally", "confidence": "observed",
     "steps": ["E.*"]},
    {"question": "Does hello advertise maxWriteBatchSize 25,000 (DECISIONS open item 4), and what topology does the driver see?",
     "answer": ("Yes. hello reports maxWriteBatchSize 25000, maxWireVersion 25, minWireVersion 0, msg 'isdbgrid', isWritablePrimary "
                "true, logicalSessionTimeoutMinutes 30, internal {documentdb_versions ['2.2-1','2.3.0','12.1-1'], kind "
                "'azuredocumentdb'}, and an operationTime, with no $clusterTime, setName or hosts. buildInfo reports version 8.0.0. "
                "PyMongo classifies the deployment as Sharded with one Mongos. maxWriteBatchSize is the same as documentdb-local "
                "(bulkwrite-forms test), but the wire version differs (21 locally)."),
     "vs_open_source": "same", "confidence": "observed",
     "steps": ["S0.buildInfo", "S1.hello"]},
    {"question": "Does the managed gateway validate these options as the open-source gateway does (DECISIONS open item 8)?",
     "answer": ("Mostly, with one material exception. Every writeConcern, readPreference, getDefaultRWConcern, afterClusterTime and "
                "atClusterTime reply matched the codes and messages DECISIONS derived from the main-branch gateway source. The "
                "exception is readConcern level validation. DECISIONS says available, linearizable and (unless configured) snapshot "
                "are rejected for every command. On the managed service all five levels are accepted outside transactions; available "
                "and linearizable are rejected only inside transactions, with exactly the predicted messages; and snapshot is "
                "accepted inside transactions. None of the rejections in this test carried errorLabels."),
     "vs_open_source": "not_tested_locally", "confidence": "observed",
     "steps": ["C.*", "X.txn.readConcern.*"]},
]

CORRECTIONS = [
    "DECISIONS topic 9, settled item 'Which readConcern levels are honored?': on the managed service, available, linearizable and "
    "snapshot are accepted outside transactions (find, aggregate, driver ReadConcern). The CommandNotSupported rejections apply "
    "only inside transactions, and only to available and linearizable; snapshot is accepted in transactions.",
    "DECISIONS topic 9, open item 3: answered for this cluster. readConcern snapshot is accepted in transactions and gives a stable "
    "snapshot there. Outside a transaction it is accepted but not point-in-time (no atClusterTime, getMore sees later inserts), and "
    "atClusterTime is rejected (72 InvalidOptions).",
    "New fact for the kit: transactions with readConcern local or majority behave read-committed (a later statement sees rows that "
    "other clients committed after the transaction's first read).",
    "New fact for the kit: data-command replies carry no operationTime/$clusterTime, and afterClusterTime is rejected (20 "
    "IllegalOperation). Causal sessions work only while the session has no operation time; advance_operation_time, or a hello inside "
    "the session, breaks every later read and write in that session.",
    "DECISIONS topic 9, open item 4: hello.maxWriteBatchSize is 25000 on this cluster.",
    "Confirmed on the managed service as DECISIONS predicted: the w validation codes and messages, the readPreference "
    "rejections (secondary, tags, hedge, primary+maxStalenessSeconds), the getDefaultRWConcern constant and its errors, and "
    "setDefaultRWConcern absent (59 CommandNotFound). The afterClusterTime/atClusterTime handling matches main, not RC2.",
]

r["conclusions"] = CONCLUSIONS
r["decisions_corrections"] = CORRECTIONS
text = redact(json.dumps(r, indent=2, default=str))
assert ENV["MANAGED_PASS"] not in text
open(PATH, "w").write(text)


def resp(s):
    if s.get("outcome") == "ok":
        return json.dumps(s.get("result"), separators=(",", ":"))[:420]
    if s.get("outcome") == "not_run":
        return "not sent"
    e = s.get("error") or {}
    lab = e.get("errorLabels")
    return (f"{e.get('type')}: code {e.get('code')}, codeName {e.get('codeName')}, errmsg {json.dumps(e.get('errmsg'))}, "
            f"errorLabels {'absent' if lab is None else lab}")


if "--steps" in sys.argv:
    out = []
    for s in r["steps"]:
        vs = s.get("vs_open_source")
        src = s.get("vs_oss_gateway_source_prediction")
        suffix = f" [vs open source: {vs}" + (f"; vs DECISIONS source prediction: {src}" if src else "") + "]"
        out.append({"step": s["id"], "command": s.get("call", "")[:420], "response": resp(s),
                    "reading": (s.get("reading") or "") + suffix})
    print(json.dumps(out, indent=0))
else:
    print("report.json updated with", len(CONCLUSIONS), "conclusions and", len(CORRECTIONS), "corrections")

# ---------------------------------------------------------------- grouped view for the structured return
GROUPS = [
    (["S0.buildInfo", "S1.hello"],
     "Context: buildInfo 8.0.0; hello msg 'isdbgrid', maxWireVersion 25, maxWriteBatchSize 25000, operationTime present, no $clusterTime/setName/hosts; PyMongo sees Sharded with one Mongos. [vs open source: different wire version (21 locally); same maxWriteBatchSize 25000]"),
    (["A.raw.insert.w1", "A.raw.update.w1", "A.raw.insert.w_majority", "A.raw.update.w_majority",
      "B.driver.insert_one.w1", "B.driver.update_one.w1", "B.driver.insert_one.w_majority", "B.driver.update_one.w_majority", "B.client.w_majority"],
     "w:1 and w:'majority' are accepted silently on insert and update (raw, WriteConcern objects, MongoClient(w='majority')): ok:1, no writeConcernError, writes visible. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["A.raw.insert.w2", "A.raw.update.w2", "A.raw.insert.w3", "A.raw.update.w3",
      "B.driver.insert_one.w2", "B.driver.update_one.w2", "B.driver.insert_one.w3", "B.driver.update_one.w3", "B.client.w2"],
     "w:2 and w:3 are rejected before execution with code 2 BadValue and no errorLabels, and the verification read shows the insert or update was NOT applied. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["A.raw.insert.w1_j_true", "A.raw.update.w1_j_true", "A.raw.insert.w1_j_false", "A.raw.update.w1_j_false",
      "B.driver.insert_one.j_true", "B.driver.update_one.j_true", "B.driver.insert_one.j_false", "B.driver.update_one.j_false"],
     "j:true and j:false (with w:1 raw, alone via WriteConcern(j=...)) are accepted silently with no observable effect. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["A.raw.insert.w_majority_wtimeout_1", "A.raw.update.w_majority_wtimeout_1", "B.driver.insert_one.w_majority_wtimeout_1",
      "B.driver.update_one.w_majority_wtimeout_1", "B.client.w_majority_wTimeoutMS_1_journal_true"],
     "wtimeout 1 / wTimeoutMS=1 (with w:'majority', and with journal=True on the client) is accepted silently: no writeConcernError, no WTimeoutError. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["A.raw.insert.w_custom_tag", "A.raw.update.w_custom_tag"],
     "A custom w tag is rejected with code 2 BadValue and nothing is written. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["A.raw.insert.w0", "A.raw.update.w0", "A.raw.insert.w0_duplicate_key"],
     "A raw db.command with writeConcern {w:0} is not sent with moreToCome, so the gateway replies in full and still reports a duplicate-key writeError (11000). [vs open source: not tested locally; matches DECISIONS source prediction for acceptance]"),
    (["B.driver.insert_one.w0", "B.driver.update_one.w0", "B.driver.w0.same_connection_followup"],
     "Driver w:0 is honoured: unacknowledged OP_MSG (moreToCome, no lsid, {ok:1} synthesized by PyMongo), the gateway sends no reply (acknowledged find/count on the same server connection afterwards succeed), and the writes land within 1 s. [vs open source: not tested locally]"),
    (["B.driver.insert_one.w0_duplicate_key", "B.driver.insert_one.default_wc_duplicate_key"],
     "Under w:0 a duplicate _id is silently dropped; with the default write concern the same insert raises DuplicateKeyError 11000 without codeName or errorLabels. [vs open source: not tested locally]"),
    (["C.raw.find.readConcern.local", "C.raw.find.readConcern.majority", "C.driver.find.readConcern.local",
      "C.driver.find.readConcern.majority", "C.raw.aggregate.readConcern.majority"],
     "readConcern local and majority are accepted on find and aggregate; no observable effect on a single node. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["C.raw.find.readConcern.available", "C.raw.find.readConcern.linearizable", "C.driver.find.readConcern.available",
      "C.driver.find.readConcern.linearizable"],
     "readConcern available and linearizable are accepted outside a transaction (no observable effect). [vs open source: not tested locally; DIFFERS from DECISIONS, which predicted 115 CommandNotSupported]"),
    (["C.raw.find.readConcern.snapshot", "C.driver.find.readConcern.snapshot", "C.raw.aggregate.readConcern.snapshot"],
     "readConcern snapshot is accepted outside a transaction on find and aggregate, but the reply carries no atClusterTime. [vs open source: not tested locally; DIFFERS from DECISIONS, which predicted 115 CommandNotSupported]"),
    (["C.raw.find.readConcern.Majority_mixed_case"],
     "readConcern level parsing is case-sensitive: 'Majority' is rejected with code 2 BadValue. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["C.raw.find.readConcern.majority_afterClusterTime"],
     "readConcern with afterClusterTime is rejected with code 20 IllegalOperation (main-branch behaviour, not RC2's silent acceptance). [vs open source: not tested locally; matches DECISIONS source prediction for main]"),
    (["C.raw.find.readConcern.snapshot_atClusterTime"],
     "readConcern snapshot with atClusterTime is rejected with code 72 InvalidOptions. [vs open source: not tested locally; matches DECISIONS source prediction for main]"),
    (["C.driver.snapshot_session.find"],
     "A PyMongo snapshot session is accepted but not honoured: no atClusterTime comes back, so the second read sees a document inserted after the first. [vs open source: not tested locally; DECISIONS predicted rejection]"),
    (["C.driver.find.readConcern.snapshot.getMore_consistency", "C.driver.find.readConcern.local.getMore_consistency"],
     "A snapshot cursor is not pinned across getMore: a document inserted between batches appears in a later batch, exactly as with the local control. [vs open source: not tested locally]"),
    (["C.driver.causal_session.afterClusterTime"],
     "A causal session works in normal use only because data-command replies carry no operationTime, so PyMongo never sends afterClusterTime. [vs open source: not tested locally]"),
    (["C.driver.causal_session.after_hello_in_session", "C.driver.causal_session.advance_operation_time"],
     "Once a causal session has an operation time (hello inside the session, or advance_operation_time), every later find and insert carries afterClusterTime and fails with code 20 IllegalOperation; the insert is not applied. [vs open source: not tested locally; matches DECISIONS source prediction for main]"),
    (["D.driver.find.readPreference.primary", "D.driver.find.readPreference.secondaryPreferred", "D.driver.find.readPreference.nearest",
      "D.driver.find.readPreference.primaryPreferred", "D.raw.find.$readPreference.primary", "D.raw.find.$readPreference.secondaryPreferred",
      "D.raw.find.$readPreference.nearest", "D.raw.find.$readPreference.primaryPreferred", "D.client.readPreference.nearest"],
     "primary, primaryPreferred, secondaryPreferred and nearest are accepted (the driver sends $readPreference for non-primary modes) and served by the single endpoint; routing cannot be observed with HA off. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["D.driver.find.readPreference.secondary", "D.raw.find.$readPreference.secondary", "D.client.readPreference.secondary"],
     "readPreference secondary is rejected (collection option, client option, raw) with code 133 FailedToSatisfyReadPreference and no errorLabels. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["D.raw.find.$readPreference.secondaryPreferred_tags"],
     "Any tag set is rejected with code 133 FailedToSatisfyReadPreference. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["D.raw.find.$readPreference.nearest_hedge_enabled"],
     "Hedged reads are rejected with code 2 BadValue. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["D.raw.find.$readPreference.secondaryPreferred_maxStalenessSeconds_90"],
     "secondaryPreferred with maxStalenessSeconds 90 is accepted. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["D.raw.find.$readPreference.primary_maxStalenessSeconds_90"],
     "primary with maxStalenessSeconds is rejected with code 9 FailedToParse. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["E.admin.getDefaultRWConcern", "E.admin.getDefaultRWConcern.inMemory_true", "E.admin.getDefaultRWConcern.after_set_attempts"],
     "getDefaultRWConcern on admin returns the constant majority/majority 'implicit' document, identical with inMemory:true and after the set attempts. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["E.mt_concern.getDefaultRWConcern"],
     "getDefaultRWConcern on a non-admin database is rejected with code 13 Unauthorized. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["E.admin.getDefaultRWConcern.unknown_field"],
     "getDefaultRWConcern with an unknown field is rejected with code 40415 UnknownBsonField. [vs open source: not tested locally; matches DECISIONS source prediction]"),
    (["E.admin.setDefaultRWConcern.probe_no_fields", "E.admin.setDefaultRWConcern.defaultWriteConcern_w1", "E.admin.setDefaultRWConcern.defaultReadConcern_local"],
     "setDefaultRWConcern does not exist: every form fails with code 59 CommandNotFound. The value-bearing forms were sent only after the no-field probe proved the command absent, and nothing changed. [vs open source: not tested locally; matches the compatibility page (No)]"),
    (["X.txn.readConcern.snapshot", "X.txn.snapshot_plus_w_majority_update"],
     "readConcern snapshot is accepted inside a transaction: find and commit ok:1, and the canonical snapshot + w:majority update transaction commits. [vs open source: DIFFERENT, documentdb-local 0.117 returned 115 CommandNotSupported]"),
    (["X.txn.readConcern.majority", "X.txn.readConcern.local"],
     "readConcern majority and local are accepted inside a transaction. [vs open source: SAME as the documentdb-local transactions-labels test]"),
    (["X.txn.readConcern.available", "X.txn.readConcern.linearizable"],
     "readConcern available and linearizable are rejected inside a transaction with code 115 CommandNotSupported, the exact messages DECISIONS attributed to all reads. [vs open source: not tested locally; matches DECISIONS source prediction inside transactions]"),
    (["X.txn.readConcern.snapshot.isolation"],
     "A snapshot transaction holds one stable snapshot: a concurrently committed insert and update stay invisible to its second read. [vs open source: not tested locally]"),
    (["X.txn.readConcern.majority.isolation", "X.txn.readConcern.local.isolation"],
     "local and majority transactions behave read-committed: a concurrently committed insert and update are visible to the second read. [vs open source: not tested locally]"),
    (["X.txn.causal_session_afterClusterTime_at_start"],
     "A transaction started in a causal session after a read carries no afterClusterTime (no operationTime was learned) and commits. [vs open source: not tested locally]"),
    (["S2.setup", "Z.dropDatabase"],
     "mt_concern was created fresh and dropped at the end ({ok:1, dropped:'mt_concern'}); afterwards it has no collections and listDatabases no longer lists it. [vs open source: n/a]"),
]


def wire_resp(s):
    """Exact raw server replies/failures of the step's commands, deduplicated, lsid/cursor ids kept as recorded."""
    out = []
    for ev in s.get("wire", []):
        body = ev.get("reply") if "reply" in ev else ev.get("failure")
        txt = f"{ev['command_name']} -> {json.dumps(body, separators=(',', ':'))}"
        if txt not in out:
            out.append(txt)
    return out


if "--grouped" in sys.argv:
    seen = set()
    result = []
    for ids, reading in GROUPS:
        for i in ids:
            assert i in S, i
            seen.add(i)
        cmds, resps = [], []
        for i in ids:
            c = S[i].get("call", "")
            if c not in cmds:
                cmds.append(c)
            for w in wire_resp(S[i]):
                w2 = w if len(w) <= 300 else w[:297] + "..."
                if w2 not in resps:
                    resps.append(w2)
            if S[i].get("verification") and any(k in S[i]["verification"] for k in ("update_applied", "document", "inserted_doc_seen")):
                pass
        def cap(items, k, width):
            items = [x if len(x) <= width else x[:width - 3] + "..." for x in items]
            more = len(items) - k
            return " | ".join(items[:k]) + (f" | (+{more} more variant(s) in report.json)" if more > 0 else "")
        result.append({"step": ", ".join(ids), "command": cap(cmds, 2, 230),
                       "response": cap(resps, 4, 260), "reading": reading})
    missing = [i for i in S if i not in seen]
    assert not missing, missing
    print(json.dumps(result, indent=0))
