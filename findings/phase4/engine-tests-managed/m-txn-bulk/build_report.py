"""Assemble report.json for m-txn-bulk from the step files written by txn.py, txn_followup.py,
txn_errors.py, txn_errors2.py and bulk.py. Adds a final one-sentence reading and the comparison with the
open-source engine results (findings/phase4/engine-tests/transactions-labels and bulkwrite-forms, engine 0.117)
to every step. Reads no credentials.
Run: /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python build_report.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, redact  # noqa: E402

FILES = ["txn_steps.json", "txn_followup_steps.json", "txn_errors_steps.json", "txn_errors2_steps.json", "bulk_steps.json"]
SCRIPTS = {"txn_steps.json": "txn.py", "txn_followup_steps.json": "txn_followup.py", "txn_errors_steps.json": "txn_errors.py",
           "txn_errors2_steps.json": "txn_errors2.py", "bulk_steps.json": "bulk.py"}
OSS_T = "findings/phase4/engine-tests/transactions-labels/report.json"
OSS_B = "findings/phase4/engine-tests/bulkwrite-forms/report.json"

# step name -> (reading, vs_open_source, open-source reference or None)
M = {
    "0a hello": ("The gateway advertises maxWireVersion 25, maxWriteBatchSize 25000 and logicalSessionTimeoutMinutes 30, with internal.kind 'azuredocumentdb' and documentdb_versions ['2.2-1','2.3.0','12.1-1'].",
                 "different", f"{OSS_T} step 0b: maxWireVersion 21, maxWriteBatchSize 25000, logicalSessionTimeoutMinutes 30 (wire version differs; batch size and session timeout match)"),
    "0b buildInfo": ("buildInfo reports version 8.0.0.", "different", f"{OSS_T} step 0a: version 7.0.0"),
    "0c driver + topology": ("PyMongo 4.20.1 sees a Sharded topology with a single Mongos-type server, the one host the SRV record resolves to.", "not_tested_locally", None),
    "a0 setup": ("Fresh collection docs with one document {_id: 1, v: 0}.", "n/a", None),
    "a1 session A update in txn": ("Transaction A updated _id 1 and holds its row lock until it commits.", "same", f"{OSS_T} step 1a"),
    "a2 session B update same doc in txn while A is uncommitted": ("B's update of the same document did not wait for A: it failed in about 0.11 s on the wire (normal round trip about 0.07 s), before A committed, with 112 WriteConflict 'canceling statement due to lock timeout'.",
                 "same", f"{OSS_T} step 1b: 112 WriteConflict 'canceling statement due to lock timeout' after 0.026 s, before A committed"),
    "a3 commit A": ("A committed normally (ok:1) after B had already failed.", "same", f"{OSS_T} step 1c"),
    "a4 session B outcome (the second transaction's error)": ("The second transaction's error is {ok:0, code:112, codeName:'WriteConflict', errmsg:'canceling statement due to lock timeout'} with no errorLabels field, so TransientTransactionError is absent both on the wire and on the driver exception.",
                 "same", f"{OSS_T} step 1d: identical code, codeName, errmsg, no errorLabels"),
    "a5 abort B after its error": ("PyMongo's abort_transaction returned normally because it swallows abort errors, but the wire reply was 251 NoSuchTransaction 'Cannot continue transaction 1': the failed write had already ended B's transaction on the server.",
                 "same", f"{OSS_T} steps 1e (driver abort ok) and 1h (raw abort 251 NoSuchTransaction)"),
    "a6 final document": ("Only A's write survived ({v: 1, by: 'A'}).", "same", f"{OSS_T} step 1f"),
    "a7 write conflict, raw wire reply": ("The untouched wire reply for the conflicting write is {ok:0, code:112, codeName:'WriteConflict', errmsg:'canceling statement due to lock timeout'} with no errorLabels field, returned in 0.1 s while A still held the lock.",
                 "same", f"{OSS_T} step 1g: identical reply"),
    "a8 raw abortTransaction for B after the conflict": ("abortTransaction for the transaction that hit the conflict returns 251 NoSuchTransaction 'Cannot continue transaction 2' with no errorLabels.",
                 "same", f"{OSS_T} step 1h: 251 NoSuchTransaction 'Cannot continue transaction 2'"),
    "a9 with_transaction for B while A holds the row lock (A commits at ~3 s)": ("with_transaction ran the callback once, sent abortTransaction (reply 251, swallowed) and re-raised 112 WriteConflict without the TransientTransactionError label after 0.17 s, so it neither retried nor succeeded, although A committed 3 s later.",
                 "not_tested_locally", "Not run on the open-source engine; ENGINE-TESTS.md predicted from the missing label that withTransaction would not retry, which this confirms on the managed service"),
    "a10 final document after with_transaction": ("B's {$inc: {n: 1}} was never applied (n: 0); only A's write is present.", "not_tested_locally", None),
    "a11 (extra) B reads, an outside write commits, B reads again and updates the same document": ("With no readConcern, B's second read inside its transaction saw a write committed after its first read (v: 7), and B's update then succeeded and overwrote it (final v: 8): statements see the latest committed data instead of one snapshot per transaction.",
                 "not_tested_locally", None),
    "b readConcern snapshot in a transaction": ("readConcern snapshot is accepted inside a transaction: the find carrying readConcern {level: 'snapshot'} and startTransaction, the update and the commit all returned ok:1.",
                 "different", f"{OSS_T} step '2 readConcern snapshot': 115 CommandNotSupported \"'Snapshot' read concern is not supported\""),
    "b readConcern majority in a transaction": ("readConcern majority is accepted inside a transaction (find, update and commit ok:1).", "same", f"{OSS_T} step '2 readConcern majority': accepted"),
    "b readConcern local in a transaction": ("readConcern local is accepted inside a transaction (find, update and commit ok:1).", "same", f"{OSS_T} step '2 readConcern local': accepted"),
    "b final document": ("All three readConcern transactions committed their writes (rc_snapshot, rc_majority and rc_local are all true).", "n/a", None),
    "c1 driver: commit, commit again, abort after commit": ("Through PyMongo a second commit_transaction succeeds (resent with writeConcern {w:'majority', wtimeout:10000}, reply ok:1) and abort_transaction after commit is refused client-side with InvalidOperation 'Cannot call abortTransaction after calling commitTransaction'.",
                 "same", f"{OSS_T} step 3a"),
    "c2 raw: commitTransaction twice (+ the driver's w:majority retry form), then abortTransaction": ("commitTransaction is idempotent (ok:1 twice and in the w:majority retry form) and abortTransaction after commit returns 256 TransactionCommitted 'Transaction 8 already committed' with no errorLabels.",
                 "same", f"{OSS_T} step 3b: identical replies"),
    "c3 raw: abortTransaction twice, then commitTransaction after abort": ("The first abortTransaction returns ok:1; a second abortTransaction and a commitTransaction after abort both return 251 NoSuchTransaction 'Cannot continue transaction 9'.",
                 "same", f"{OSS_T} step 3c: identical replies"),
    "c4 document after part c": ("v rose by exactly 1100 (the two committed transactions) and not by the aborted +1.", "n/a", None),
    "d1 driver: write after 36 s idle in a transaction": ("In this trial the first write after 36 s idle failed with code 1 InternalError '[ActivityId=...] An unexpected internal error has occurred.' and no errorLabels; repeat trials (g-idle-*) show this is one of two possible first errors.",
                 "same", f"{OSS_T} step 4a: code 1 InternalError with the same generic message"),
    "d2 driver: commit after the idle timeout": ("commitTransaction then returned 251 NoSuchTransaction 'The transaction has been aborted because its backend session ended.' with no errorLabels.",
                 "different", f"{OSS_T} step 4b: code 1 InternalError on commit"),
    "d3 driver: abort after the idle timeout": ("PyMongo refuses abort_transaction after a commit attempt (InvalidOperation, client-side, nothing sent).", "same", f"{OSS_T} step 4c"),
    "d4 raw: write, commit, abort after 36 s idle": ("In this trial the first write after 36 s idle already got 251 NoSuchTransaction 'Cannot continue transaction 11', and commit and abort returned the same 251, none with errorLabels.",
                 "different", f"{OSS_T} step 4d: write code 1 InternalError, commit code 1 InternalError, abort 251"),
    "d5 document after the idle tests": ("Neither idle transaction applied any of its writes (idle and idle2 fields absent).", "same", f"{OSS_T} step 5"),
    "e1 busy transaction: a small write every 5 s for 40 s": ("Writing every 5 s, all nine writes up to 40.0 s succeeded and the commit at 40.08 s returned ok:1 with all nine documents kept, so this transaction outlived 30 s; the same pattern failed at 35 s and 40 s in g-busy-6 and g-busy-7.",
                 "not_tested_locally", None),
    "e2 (extra) busy transaction: a small write every 1 s for 36 s": ("Writing every 1 s, writes succeeded through 33.0 s; the write at 34.0 s, every later write and the commit returned 251 NoSuchTransaction 'Cannot continue transaction 13' with no errorLabels, and none of the 34 successful writes were kept.",
                 "not_tested_locally", None),
    "f-iso readConcern default: read, outside write commits, read again, update, commit": ("With no readConcern the second read saw the outside commit (v: 7) and the transaction's update and commit succeeded and overwrote it (final v: 8): read-committed visibility, no write conflict.",
                 "not_tested_locally", None),
    "f-iso readConcern snapshot: read, outside write commits, read again, update, commit": ("With readConcern snapshot the second read did not see the outside commit (v: 0), the update of that document failed with 117 ConflictingOperationInProgress 'Could not complete operation due to conflict with internal apply operation' and no errorLabels, and commitTransaction still returned ok:1 (the outside value v: 7 remained).",
                 "not_tested_locally", "The open-source 0.117 image rejects readConcern snapshot with 115, so this path could not be exercised there"),
    "f-iso readConcern majority: read, outside write commits, read again, update, commit": ("readConcern majority behaves like the default: the second read saw the outside commit and the update overwrote it without a conflict.",
                 "not_tested_locally", None),
    "g0 timing origin": ("Common time origin T0 for the concurrent busy and idle trials.", "n/a", None),
    "g-summary concurrent busy and idle trials": ("Busy transactions were ended in groups at the same instants (about 35.5, 50.5 and 65.5 s after T0, i.e. every ~15 s) once older than about 30 s, giving lifetimes of 31 to 41 s; idle transactions survived 25 s, and after 31 s or more the next statement returned code 1 InternalError when no sweep had yet run and 251 NoSuchTransaction otherwise, never with errorLabels.",
                 "not_tested_locally", "Only one 36 s idle trial per path was run on the open-source engine (code 1 on the write); busy transactions were not tested there"),
    "h0 setup": ("Collection serr with Y1, Y2 and Y4.", "n/a", None),
    "h1 snapshot txn: insert X1, read Y1, outside write to Y1 commits, update Y1 in txn (conflict), commit": ("After the 117 conflict, commitTransaction returned ok:1 but the transaction's earlier successful insert X1 was not kept (count 0): the commit reported success for a transaction that had been rolled back.",
                 "not_tested_locally", None),
    "h2 default txn: insert X2, update Y2 while another transaction holds its lock (112), commit": ("After a 112 lock timeout, commitTransaction returned 251 NoSuchTransaction 'Cannot continue transaction 2' and the earlier insert X2 was not kept: a 112 ends the whole transaction.",
                 "not_tested_locally", None),
    "h3 default txn: insert X3, insert X3 again (duplicate key), commit": ("A duplicate-key insert inside a transaction returns ok:1 with writeErrors [{index: 0, code: 11000}] (driver DuplicateKeyError), the transaction stays open, and the commit keeps the earlier insert X3 (n: 1).",
                 "not_tested_locally", None),
    "h4 default txn: insert X4, $inc on a string field (type error), commit": ("An $inc on a string field returns ok:1 with writeErrors code 14 (driver WriteError), the transaction stays open, and the commit keeps the earlier insert X4.",
                 "not_tested_locally", None),
    "h5 control: insert X5, commit": ("Control: a transaction with no failing statement commits its insert.", "n/a", None),
    "h1-repeat-1 snapshot txn: insert pre, read Y, outside write to Y, update Y in txn (117), commit": ("Reproduced: 117 on the conflicting update, commitTransaction ok:1, earlier insert not kept.", "not_tested_locally", None),
    "h1-repeat-2 snapshot txn: insert pre, read Y, outside write to Y, update Y in txn (117), insert post, commit": ("Reproduced, and an insert after the 117 returns 263 OperationNotSupportedInTransaction 'Operation was attempted in a transaction that was aborted', yet commitTransaction returns ok:1 and neither insert is kept.",
                 "not_tested_locally", None),
    "f1 hello": ("hello advertises maxWireVersion 25, maxWriteBatchSize 25000, maxMessageSizeBytes 48000000 and maxBsonObjectSize 16777216, plus endpointName and operationTime fields.",
                 "different", f"{OSS_B} step 0b: maxWireVersion 21; maxWriteBatchSize, maxMessageSizeBytes and maxBsonObjectSize identical; no endpointName or operationTime; internal.kind ''"),
    "f2 buildInfo": ("buildInfo reports version 8.0.0.", "different", f"{OSS_B} step 0a: 7.0.0"),
    "f3 driver view": ("PyMongo's pooled connection reports max_wire_version 25, so its client-level bulk_write gate (refuse below 25) is passed.", "different", f"{OSS_B} step 5a: wire version 21, PyMongo refused client-side"),
    "g0 setup": ("Collections for the bulk tests dropped (only in mt_txn).", "n/a", None),
    "g1 collection bulk_write ordered, no error": ("An ordered mixed bulk_write succeeds (inserted 2, matched 1, modified 1, upserted 1, deleted 1) and is sent as separate insert, update and delete commands.",
                 "same", f"{OSS_B} step 1a: identical counts"),
    "g2 state after g1": ("The collection holds {_id: 1, v: 'a2'} and {_id: 99, v: 'ups'}.", "same", f"{OSS_B} step 1b"),
    "g3 collection bulk_write ordered with a duplicate _id at index 2": ("The ordered run raises BulkWriteError with one writeError {index: 2, code: 11000, errmsg: \"Duplicate key violation on the requested collection: Index '_id_'\"}, nInserted 2, and stops at the duplicate.",
                 "same", f"{OSS_B} step 2a: identical writeError and counts"),
    "g4 state after g3": ("Documents 10 and 11 were inserted and the operations after the duplicate were not applied.", "same", f"{OSS_B} step 2b"),
    "g5 collection bulk_write unordered with a duplicate _id at index 2": ("The unordered run reports the same single writeError but continues past it (nInserted 3, nMatched 1, nModified 1, nRemoved 1).",
                 "same", f"{OSS_B} step 3a: identical"),
    "g6 state after g5": ("The collection holds {_id: 11, v: 'y2'} and {_id: 12, v: 'z'}.", "same", f"{OSS_B} step 3b"),
    "g7 raw insert command, unordered, one duplicate": ("A raw unordered insert with one duplicate returns ok:1, n:1 and writeErrors [{index: 0, code: 11000}] in the reply body, with no codeName or errorLabels.",
                 "same", f"{OSS_B} step 4: identical reply"),
    "h1 MongoClient.bulk_write ordered": ("PyMongo sends the bulkWrite command to admin (ops and nsInfo as two OP_MSG document sequences) and the gateway rejects it with {ok:0, code:2, codeName:'BadValue', errmsg:'Expected at most one command document and one extra section.'}, raised as ClientBulkWriteException with nothing written.",
                 "different", f"{OSS_B} step 5a: PyMongo refused client-side with InvalidOperation 'MongoClient.bulk_write requires MongoDB server version 8.0+.' (wire version 21)"),
    "h2 MongoClient.bulk_write unordered, verbose_results": ("The unordered verbose form fails the same way (code 2 BadValue, same errmsg, no errorLabels).", "different", f"{OSS_B} step 5b: InvalidOperation client-side"),
    "h3 raw bulkWrite command on admin": ("The bulkWrite command sent as a single body document returns {ok:0, code:59, codeName:'CommandNotFound', errmsg:\"Command 'bulkWrite' not found.\"}.",
                 "same", f"{OSS_B} step 5c: identical reply"),
    "h4 state of the client_bw namespaces": ("Neither client_bw_a nor client_bw_b received a document, and neither collection was created.", "n/a", None),
    "i1 insert_many of 25,001 small documents": ("insert_many of 25,001 documents succeeded because the driver split it into insert commands of 25,000 and 1 documents.",
                 "same", f"{OSS_B} step 6a: succeeded (split observed only indirectly there)"),
    "i2 count after i1": ("All 25,001 documents are present.", "same", f"{OSS_B} step 6b"),
    "i3 raw insert command with 25,001 documents (one command, no driver split)": ("A single insert command with 25,001 documents fails with {ok:0, code:16, codeName:'InvalidLength', errmsg:'Write batch size must fall within the range of 1 to 25000, but 25001 operations were provided.'} and no errorLabels.",
                 "same", f"{OSS_B} step 6d: identical reply"),
    "i4 count after i3": ("The failed command inserted nothing (0 documents).", "same", f"{OSS_B} step 6e"),
    "i5 raw insert command with exactly 25,000 documents": ("Exactly 25,000 documents in one insert command succeed (ok:1, n:25000).", "same", f"{OSS_B} step 6f"),
    "i6 count after i5": ("25,000 documents are present.", "same", None),
    "j1 drop the test database": ("Dropped database mt_txn.", "n/a", None),
    "j2 verify the database is gone": ("mt_txn is no longer listed.", "n/a", None),
}


def brief_err(e):
    if not isinstance(e, dict):
        return str(e)
    if "exception" in e:
        return f"{e.get('exception')} {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'"
    return f"{e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'"


def trial_reading(step, r):
    if r.get("kind") == "busy":
        ff = r.get("first_failure")
        if not ff:
            return (f"{r['trial']} ({r['interval_s']} s cadence) never failed up to age {r.get('last_ok_age_s')} s; commit {brief_err(r.get('commit'))}.")
        e = ff["error"]
        return (f"{r['trial']} ({r['interval_s']} s cadence, started at {r.get('txn_start_abs_s')} s) last succeeded at age {r.get('last_ok_age_s')} s and first failed at age "
                f"{ff['age_s']} s (T0+{ff['abs_s']} s) with {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}' and no errorLabels; the commit returned "
                f"{(r.get('commit') or {}).get('code')} and {r.get('docs_visible_after')} of {r.get('n_writes_ok')} successful writes were kept.")
    w = r.get("write")
    c = r.get("commit")
    wtxt = "ok" if isinstance(w, dict) and w.get("ok") == 1 and "code" not in w else brief_err(w)
    ctxt = "ok" if isinstance(c, dict) and c.get("ok") == 1 and "code" not in c else brief_err(c)
    return (f"{r['trial']} ({r.get('path')}, idle {r.get('idle_s')} s, started at T0+{r.get('txn_start_abs_s')} s, write at T0+{r.get('write_abs_s')} s): "
            f"write {wtxt}; commit {ctxt}; {r.get('docs_visible_after')} documents kept; no errorLabels.")


def main():
    parts = []
    all_steps = []
    for fn in FILES:
        d = json.load(open(os.path.join(HERE, fn)))
        parts.append({"file": fn, "script": SCRIPTS[fn], "part": d.get("part"), "started_utc": d.get("started_utc"), "finished_utc": d.get("finished_utc")})
        for st in d["steps"]:
            name = st["step"]
            st["script"] = SCRIPTS[fn]
            if name in M:
                reading, vs, ref = M[name]
            elif name.startswith("g-busy-") or name.startswith("g-idle-"):
                reading = trial_reading(name, st["response"])
                vs, ref = "not_tested_locally", None
            else:
                reading, vs, ref = st.get("reading") or "(no reading)", "n/a", None
                print("WARNING: no mapping for step", name)
            st["reading"] = reading
            st["vs_open_source"] = vs
            if ref:
                st["open_source_reference"] = ref
            all_steps.append(st)

    conclusions = json.load(open(os.path.join(HERE, "conclusions.json")))
    report = {
        "test": "m-txn-bulk",
        "goal": "Transactions and bulk writes on the managed service.",
        "database": "mt_txn (the only database created or touched; dropped at the end, step j1/j2)",
        "observed_on": "2026-11-25",
        "target": {"service": "Azure DocumentDB (Microsoft.DocumentDB/mongoClusters)", "cluster": "ddb-samples-shared", "resource_group": "documentdb-samples-rg",
                   "region": "eastus", "tier": "M30", "shards": 1, "server_version": "8.0", "storage": "Premium SSD v2", "high_availability": "disabled",
                   "endpoint_used": "MANAGED_URI (plain host <cluster>.mongocluster.cosmos.azure.com via mongodb+srv; tls=true, authMechanism=SCRAM-SHA-256, retrywrites=false, maxIdleTimeMS=120000)",
                   "hello": {"maxWireVersion": 25, "maxWriteBatchSize": 25000, "internal.documentdb_versions": ["2.2-1", "2.3.0", "12.1-1"], "internal.kind": "azuredocumentdb"},
                   "buildInfo.version": "8.0.0"},
        "driver": "PyMongo 4.20.1 (/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python)",
        "evidence_scope": "Observations of the managed service on 2026-11-25 at the engine versions above, single-shard M30 without HA. Comparisons are with the open-source documentdb-local image (engine 0.117, wire version 21) results in findings/phase4/ENGINE-TESTS.md.",
        "open_source_references": [OSS_T, OSS_B],
        "phase": "Phase 1, data plane only",
        "config_changes": [],
        "scripts": {"helpers": "common.py", "probe": "probe.py", "a-e transactions": "txn.py", "isolation and 30 s limit follow-up": "txn_followup.py",
                    "commit after a failed statement": "txn_errors.py", "repeat of the 117 silent rollback": "txn_errors2.py", "f-i bulk writes and cleanup": "bulk.py",
                    "report builder": "build_report.py"},
        "runs": parts,
        "steps": all_steps,
        "conclusions": conclusions,
        "notes": [
            "Every step records the exact driver call or raw command, the raw server reply or error (code, codeName, errmsg, whether the errorLabels field exists in the server reply, and the labels on the driver exception) and the driver's wire-level commands captured with a pymongo CommandListener.",
            "No errorLabels field appeared in any server reply in this test (112, 117, 251, 256, 263, 1, 16, 2, 59 and 11000 all came without labels), and PyMongo added no label client-side in any step.",
            "The ~15 s sweep is inferred from black-box timing: in txn_followup.py, transactions started at different times were ended at the same instants, and the same 15 s phase also explains every result in txn.py (d1 vs d4, e1 vs e2).",
            "PyMongo's CosmosDB UserWarning on connect was filtered in common.py, as the task allows. ActivityId values in errmsg are per-request ids and were kept. No password, URI, e-mail address, subscription id, tenant id or object id is recorded.",
            "Steps marked (extra) go beyond the stated plan but stay inside mt_txn: a11, f-iso, g-*, h* and e2 were added to explain behaviour the planned steps exposed.",
        ],
    }
    out = os.path.join(HERE, "report.json")
    with open(out, "w") as f:
        f.write(redact(json.dumps(report, indent=2, default=str)))
    print("written:", out, "steps:", len(all_steps))


if __name__ == "__main__":
    main()
