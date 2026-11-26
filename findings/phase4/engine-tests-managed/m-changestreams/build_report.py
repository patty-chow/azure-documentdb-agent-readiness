#!/usr/bin/env python
"""Assemble report.json for m-changestreams from steps_<section>.json files, with reviewed one-sentence readings."""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from envload import HERE, scrub  # noqa: E402
import pymongo  # noqa: E402

OVR = {
 "a1-collection-watch-open": "collection.watch() opened with no cluster feature enabled: the aggregate with $changeStream returned a live cursor (ns mt_cs.cs_a) with an empty firstBatch, a postBatchResumeToken and an operationTime, whereas documentdb-local 0.117 fails this call with code 115.",
 "a2-insert-update-delete-read": "The insert, $set update and delete, written right after watch() returned and before any getMore, arrived together in the first getMore, 0.34 s after the first write was sent, with keys _id, operationType, wallTime, fullDocument (insert and update only), documentKey and ns, no clusterTime, no updateDescription, and a post-update fullDocument on the update event without updateLookup.",
 "a3-close": "stream.close() sent killCursors and the server listed the cursor under cursorsKilled.",
 "a4-raw-aggregate-changeStream": "The raw aggregate [{$changeStream: {}}] returned a non-zero cursor id, an empty firstBatch, a postBatchResumeToken and an operationTime but no $clusterTime, and the next getMore returned no events with an advanced postBatchResumeToken.",
 "b1-updateLookup-insert-update-update": "With full_document='updateLookup', two updates written before the first read came back as update events whose fullDocument is the document as of each update (qty 2, then qty 3), so the value is a write-time post-image rather than a lookup at read time, and neither event has updateDescription.",
 "b2-updateLookup-update-then-delete": "An update followed by a delete, both written before the read, produced an update event whose fullDocument is still the post-update document (qty 4) although the document no longer existed, and a delete event without fullDocument.",
 "c1-db-watch": "Database-level db.watch() opened (aggregate: 1 on mt_cs, cursor ns mt_cs.$cmd.aggregate) but delivered no event for inserts into mt_cs.cs_c1 and mt_cs.cs_c2 in 33.6 s, with no error and a postBatchResumeToken that kept advancing.",
 "c2-client-watch": "Cluster-level client.watch() (aggregate: 1 on admin with allChangesForCluster: true) opened and delivered the mt_cs.cs_c1 insert 0.16 s after the write, with no events from other databases in that window.",
 "c3-client-watch-match-ns": "client.watch([{$match: {'ns.db': 'mt_cs'}}]) delivered the mt_cs.cs_c2 insert 0.16 s after the write, so a server-side $match on ns works on the cluster-level stream.",
 "c4-db-vs-collection-same-write": "For the same insert into mt_cs.cs_c1, a collection-level stream delivered the event in 0.15 s while a database-level stream opened beside it delivered nothing in 45.5 s and raised no error.",
 "c5-db-watch-new-collection": "A database-level stream saw nothing for an insert, update and delete on a newly created collection (mt_cs.cs_c3) in 45.2 s, with no error.",
 "c6-raw-db-level-aggregate": "A raw database-level $changeStream cursor (ns mt_cs.$cmd.aggregate) returned three empty getMores of about 3.08 s each (maxTimeMS 3000) after an insert into mt_cs.cs_c1.",
 "c7-db-watch-resume-after-collection-token": "A database-level stream resumed from the d1 token, which predates ten later writes in mt_cs, delivered nothing in 30 s, so the database-level stream drops events rather than starting late.",
 "d1-capture-token": "After two inserts the last event's _id and stream.resume_token were the same token {_data: 'MzowOjE4Njg0MDgzMjowOjE4Njg0MDgzMjoxOjA='}, which base64-decodes to the ASCII string '3:0:186840832:0:186840832:1:0'.",
 "d2-missed-writes": "Three writes (insert d-3, update d-3, delete d-1) were made while no stream was open.",
 "d3-resume-after": "resume_after with the captured token replayed exactly the three missed events in order (insert d-3, update d-3, delete d-1) in the aggregate's firstBatch, with no replay of d-2 and nothing extra.",
 "d4-start-after": "start_after with the same token returned the same three events, so start_after and resume_after behave alike for an ordinary event token.",
 "d5-idle-token": "An idle stream (two empty getMores) exposed its postBatchResumeToken '3:0:186841688:0:0:1:0' as stream.resume_token, and resuming from it delivered exactly the two inserts made afterwards, so an idle consumer can checkpoint.",
 "e0-real-token": "A real event token captured on cs_e decodes to '3:0:205315048:0:205315048:1:0'.",
 "e1-fabricated-real-plus-AAAA-suffix": "A real token with 'AAAA' appended after its '=' padding is accepted at aggregate and the first getMore returned no events and no error, so trailing characters are ignored.",
 "e1-fabricated-structured-future-position (x100 third field)": "A well-formed token whose position field is 100 times the real one is accepted at aggregate and the first getMore returned no events and no error.",
 "e1-fabricated-structured-position-minus-1": "A well-formed token one position below the real e-1 token is accepted, but the first getMore returned no events (e-1 was not replayed) and no error.",
 "e1-driver-structured-future-position (x100 third field)": "Through the driver, watch(resume_after=<future-position token>) opens and returns nothing for 8 s with no error.",
 "e2-token-from-other-collection": "A valid event token captured on mt_cs.cs_d was accepted on mt_cs.cs_e and replayed the later e-1 insert, whose _id there ('3:0:205081984:0:205315048:1:0') differs from the _id the same event carried in e0 ('3:0:205315048:0:205315048:1:0'), so tokens are collection-independent positions and an event's _id is not a stable identity.",
 "e3a-token-before-drop": "A token taken on cs_e2 before the drop was captured ('3:0:221397744:0:221397744:1:0').",
 "e3b-drop-with-stream-open": "Dropping the watched collection produced no drop or invalidate event; the server instead failed the next getMore with code 43 CursorNotFound 'Cursor not found in server' (no errorLabels), PyMongo resumed automatically with resumeAfter, and the stream stayed alive with nothing to deliver for 21 s.",
 "e3d-resume-after-T_before": "resume_after with the pre-drop token opened on the recreated cs_e2 without error and delivered the recreated collection's inserts (after-recreate-1, after-recreate-probe-0), with no drop or invalidate event.",
 "e3e-start-after-T_before": "start_after with the pre-drop token behaved the same, delivering after-recreate-1, after-recreate-probe-0 and after-recreate-probe-1 without error.",
 "e3i-raw-resume-after-T_before": "The raw resumeAfter with the pre-drop token on the recreated collection returned all three post-recreate inserts in firstBatch and no error, which is the server reply behind e3d.",
 "e4-one-stream-across-drop-and-recreate": "A single stream kept open across drop and recreate delivered the pre-drop insert and then the post-recreate insert with no drop or invalidate event in between, because the server's CursorNotFound (code 43) on the getMore after the drop was absorbed by one automatic driver resume.",
 "e5-future-position-token-then-write": "A fabricated token pointing 100 times ahead is accepted and then silently skips a new insert for 15 s, so a corrupted future token yields an idle stream with no error.",
 "e6-older-position-10000000": "A fabricated token with position 10,000,000 fails at aggregate with code 72 InvalidOptions 'Expired resume token or cursor, reinitialize the change stream cursor' and no errorLabels, the same as position 1.",
 "e6-older-position-100000000": "A fabricated token with position 100,000,000 is accepted, but one 2-s getMore returned no events and the postBatchResumeToken stayed at that position.",
 "e6-older-position-170000000": "A fabricated token with position 170,000,000 (before this test's first write) is accepted and replays the cs_e inserts e-1 and e-future-probe in the firstBatch.",
 "f0-markers": "The marker insert, update and delete on cs_f were written at 21:09:50.33Z; their write replies carry no operationTime, so session.operation_time stayed None, while hello just before returned operationTime Timestamp(1795640990, 291).",
 "f1-start-at-wallclock-minus-30s": "start_at_operation_time Timestamp(1795640960, 0), 30 s before the markers and 3.5 minutes before the call, replayed the three marker events (insert, update, delete of f-1) in the aggregate's firstBatch with no error.",
 "f2-start-at-hello-operationTime-before-markers": "start_at_operation_time set to the operationTime hello returned just before the markers also replayed the three marker events.",
 "f3-start-at-1h-ago-before-cluster-creation": "start_at_operation_time one hour ago, 23 minutes before the cluster's createdAt, was accepted with no error and replayed the three marker events.",
 "f4-start-at-40-days-ago": "start_at_operation_time 40 days ago, beyond the documented 35-day window and before the cluster existed, was accepted with no error and replayed the three marker events.",
 "f5-start-at-2-minutes-in-future": "start_at_operation_time two minutes in the future was accepted, and an insert made immediately was not delivered within 10 s.",
 "f6-cs_a-start-at-40-days-ago": "On cs_a, start_at_operation_time 40 days ago replayed the three a2 events written about 13 minutes earlier, so a start time before the oldest retained change is clamped to it rather than rejected.",
 "f7-cs_a-start-at-210s-ago-control": "On cs_a, start_at_operation_time 210 s ago returned nothing, which confirms the timestamp is honoured and not ignored.",
 "f8-cs_a-start-at-1h-ago": "On cs_a, start_at_operation_time one hour ago (before the cluster existed) replayed the same three a2 events.",
 "x0-watch-nonexistent-collection": "watch() on a collection that did not exist yet opened, and the insert that created the collection was delivered 0.09 s later.",
 "x1a-collMod-enableUpdateDescription": "The Learn-documented form collMod {enableUpdateDescription: {enabled: true}} is rejected with code 14 TypeMismatch 'The BSON field 'collMod.enableUpdateDescription' has an incorrect type 'object'; it should be one of the following valid types: [bool, long, int, decimal, double]'.",
 "x1b-updateDescription-after-collMod": "With that collMod rejected, a $set+$unset, an $inc, a $push, a pipeline-style update and a replace_one all produced update events without updateDescription, and the replace_one was reported as operationType 'update', not 'replace'.",
 "x1c-collMod-enableUpdateDescription-bool": "collMod {enableUpdateDescription: true} (boolean) is accepted with {ok: 1} and listCollections then shows options {statsEnabled: true, enableUpdateDescription: true}.",
 "x1d-updateDescription-after-bool-collMod": "Even after the accepted boolean collMod, the same five updates produced update events without updateDescription, with replace_one again reported as 'update'.",
 "x1e-updateDescription-recheck": "About a minute later, with a new client and stream, a $set+$unset update still produced no updateDescription, so on this cluster with no feature enabled updateDescription is not emitted.",
 "x2a-collMod-changeStreamPreAndPostImages": "collMod {changeStreamPreAndPostImages: {enabled: true}} is accepted with {ok: 1}.",
 "x2b-preimages-whenAvailable": "With pre-images enabled and full_document_before_change='whenAvailable', the update event carried fullDocumentBeforeChange {v: 1} and fullDocument {v: 2}, and the delete event carried fullDocumentBeforeChange {v: 2}.",
 "x2c-preimage-required-not-enabled": "On a collection without pre-images, full_document_before_change='required' opens, but the getMore after an update fails with code 10065 Location10065 'Change stream was configured to require a pre-image for all update, delete and replace events, but the pre-image was not found for event' and no errorLabels.",
 "x3-showExpandedEvents": "show_expanded_events=True fails at open with code 115 CommandNotSupported 'BSON field 'showExpandedEvents' is not supported'.",
 "x4-watch-via-global-host": "Through the .global. host a collection stream delivered an insert 0.1 s after the write.",
 "x5-pipeline-match-project": "A server-side pipeline [{$match: {operationType: {$in: ['insert', 'delete']}}}, {$project: {fullDocument: 0}}] delivered only the insert (without fullDocument) and the delete, dropping the update.",
 "z1-dropDatabase-with-streams-open": "With a database-level and a cs_a stream open, dropDatabase produced no dropDatabase, drop or invalidate event on either stream; the server killed both cursors (getMore code 43 CursorNotFound), PyMongo resumed each once, both streams were then closed with killCursors, and mt_cs no longer exists.",
}


def fix_generic(step, reading):
    if step in OVR:
        return OVR[step]
    reading = reading.replace("; labels None.", ", with no errorLabels.")
    reading = reading.replace("; driver labels [].", ", with no errorLabels from the server and none added by the driver.")
    return reading


def main():
    files = glob.glob(os.path.join(HERE, "steps_*.json"))
    secs = [json.load(open(f)) for f in files]
    secs.sort(key=lambda s: s["started_utc"])
    steps = []
    for s in secs:
        for st in s["steps"]:
            st["section"] = s["section"]
            st["reading"] = fix_generic(st["step"], st["reading"])
            steps.append(st)
    conclusions = json.load(open(os.path.join(HERE, "conclusions.json")))
    report = {
        "test": "m-changestreams",
        "database": "mt_cs",
        "goal": "Change streams on a single-shard managed cluster with no feature enabled: collection, database and cluster streams, updateLookup, resume tokens, malformed and stale tokens, startAtOperationTime.",
        "observed": "Observations of the managed service on 2026-11-25 between " + secs[0]["started_utc"] + " and " + secs[-1]["finished_utc"] + " (UTC).",
        "cluster": {
            "resource": "Microsoft.DocumentDB/mongoClusters ddb-samples-shared, resource group documentdb-samples-rg, eastus (subscription id masked)",
            "tier": "M30", "shards": 1, "serverVersion": "8.0", "storage": "PremiumSSDv2 128 GB", "highAvailability": "Disabled",
            "publicNetworkAccess": "Enabled (firewall rule for this Mac)", "createdAt": "2026-11-25T20:35:33Z", "previewFeatures": "none set (no cluster feature enabled)",
            "hello": {"maxWireVersion": 25, "msg": "isdbgrid", "internal": {"documentdb_versions": ["2.2-1", "2.3.0", "12.1-1"], "kind": "azuredocumentdb"},
                      "operationTime": "present", "$clusterTime": "absent"},
            "connection": "MANAGED_URI (plain host, mongodb+srv, TLS, SCRAM-SHA-256, retrywrites=false); MANAGED_GLOBAL_URI only in x4",
        },
        "client": {"python": sys.version.split()[0], "pymongo": pymongo.version,
                   "interpreter": "/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python"},
        "scripts": {
            "main": os.path.join(HERE, "cs_test.py"),
            "helpers": os.path.join(HERE, "envload.py"),
            "preflight": os.path.join(HERE, "probe.py"),
            "assembler": os.path.join(HERE, "build_report.py"),
            "run_order": "probe.py; cs_test.py a; b; c; d; cr; e; er; setup_f; x; x1c; x1e; f; fr; cleanup; build_report.py",
            "raw_step_files": sorted(os.path.basename(f) for f in files),
        },
        "method": [
            "Every driver call ran through a pymongo CommandListener; each step's 'wire' holds the exact aggregate/getMore/killCursors/insert/update/delete/drop/collMod commands and raw replies (lsid removed, $clusterTime signature hash omitted; empty getMores are summarised as a count with durations plus one full sample).",
            "Events were read with stream.try_next() in a loop (max_await_time_ms=1000, 0.2 s pause after an empty batch) until the wanted count or the timeout (30 s unless the step says otherwise), plus a short extra wait to catch unexpected events.",
            "Raw probes used db.command(aggregate/getMore/killCursors) inside one explicit session so the server's reply or error is recorded without driver retries.",
            "Events seen on the cluster-level stream from databases other than mt_cs were only counted by namespace and operationType (none were seen).",
            "Steps prefixed x, cr, er and fr go beyond the spec's (a)-(f) to explain or confirm what (a)-(f) showed; they touched only collections inside mt_cs.",
        ],
        "open_source_reference": "findings/phase4/ENGINE-TESTS.md and engine-tests/local-gateway-parity (documentdb-local 0.117, wire 21): collection.watch() and aggregate [{$changeStream: {}}] fail with code 115 CommandNotSupported 'Stage $changeStream is not supported yet in native pipeline'. Only the open step is comparable; every later behaviour is not_tested_locally.",
        "steps": steps,
        "conclusions": conclusions,
        "config_changes": [],
        "collection_level_changes_inside_mt_cs": [
            "collMod {enableUpdateDescription: {enabled: true}} on mt_cs.cs_x1 (rejected, code 14)",
            "collMod {enableUpdateDescription: true} on mt_cs.cs_x1b (accepted)",
            "collMod {changeStreamPreAndPostImages: {enabled: true}} on mt_cs.cs_x2 (accepted)",
            "All removed with dropDatabase mt_cs in z1.",
        ],
        "cleanup": "All change streams were closed (killCursors replies list every cursor as killed) and database mt_cs was dropped; list_database_names() no longer contains mt_cs.",
    }
    text = scrub(json.dumps(report, indent=1, default=str))
    out = os.path.join(HERE, "report.json")
    with open(out, "w") as f:
        f.write(text)
    print("wrote", out, len(text), "bytes,", len(steps), "steps,", len(conclusions), "conclusions")


if __name__ == "__main__":
    main()
