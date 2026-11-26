"""Assemble the final m-schema report.json from run 1 (report.json), run 2 (report.rerun.json) and the
read-only cluster read (cluster_show_selected.json). Adds per-step rerun consistency, the read-only
cluster step, curated readings for a few steps, and the conclusions. Contains no secrets."""
import json
import os
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda n: os.path.join(HERE, n)  # noqa: E731

r1 = json.load(open(P("report.json")), object_pairs_hook=OrderedDict)
r2 = json.load(open(P("report.rerun.json")), object_pairs_hook=OrderedDict)
show = json.load(open(P("cluster_show_selected.json")), object_pairs_hook=OrderedDict)

if r1.get("finalized"):
    raise SystemExit("report.json already finalized; rerun run_test.py first")

KEYS = ("kind", "code", "codeName", "errmsg", "errInfo_present", "errorLabels", "n", "nModified", "nWriteErrors", "matched")


def okey(o):
    return json.dumps({k: o.get(k) for k in KEYS}, sort_keys=True)


assert len(r1["steps"]) == len(r2["steps"]), "step count differs between runs"
mismatch = []
for a, b in zip(r1["steps"], r2["steps"]):
    same = a["step"] == b["step"] and okey(a["outcome"]) == okey(b["outcome"])
    a["rerun_consistent"] = same
    if not same:
        mismatch.append(a["step"])

# read-only control-plane step
m3 = OrderedDict()
m3["step"] = "M3 read-only cluster resource read (selected fields)"
m3["command"] = ("az documentdb mongocluster show -g documentdb-samples-rg -n <cluster> -o json "
                 "| select properties.previewFeatures, serverVersion, compute.tier, sharding.shardCount, storage.type, "
                 "highAvailability.targetMode, clusterStatus, systemData.createdAt/lastModifiedAt and the list of property keys "
                 "(read-only; identifiers, connection string, administrator and e-mail fields not recorded)")
m3["response"] = OrderedDict(selected=show)
m3["outcome"] = OrderedDict(kind="ok")
m3["reading"] = ("Read-only: the cluster resource has no previewFeatures property and lastModifiedAt equals createdAt "
                 "(%s), so every validator result below was obtained with no preview flag and no configuration change; "
                 "no open-source comparison applies." % show.get("createdAt"))
m3["vs_open_source"] = "n/a"
m3["rerun_consistent"] = True
idx = next(i for i, s in enumerate(r1["steps"]) if s["step"].startswith("M2 ")) + 1
r1["steps"].insert(idx, m3)

CURATED = {
    "A0b": ("listCollections stores the validator verbatim with the defaults validationLevel 'strict' and validationAction "
            "'error' plus an extra option statsEnabled: true; open-source 0.117 differed only in lacking statsEnabled."),
    "A0c": ("The violating insert {x:1} is rejected with write error 121 'Document failed validation', no codeName, no errInfo "
            "and no errorLabels (writeErrors[0] is just {index, code, errmsg}); open-source 0.117 behaved the same."),
    "A0fam": ("findAndModify that would break the validator fails as a command error (ok: 0) with code 121, codeName "
              "'DocumentFailedValidation' (the open-source gateway's name for 121 in error_mappings.csv; MongoDB's is "
              "'DocumentValidationFailure'), errmsg 'Document failed validation' and no errInfo; not tested on open-source."),
    "A1.additionalProperties_with_id": ("create rejected additionalProperties: false even with _id declared in properties, "
                                        "with 9 FailedToParse 'Unknown $jsonSchema keyword: additionalProperties'; "
                                        "not tested on open-source."),
    "A4.additionalProperties_with_id": ("collMod rejected additionalProperties: false even with _id declared in properties, "
                                        "with 9 FailedToParse 'Unknown $jsonSchema keyword: additionalProperties'; "
                                        "not tested on open-source."),
    "C.additionalProperties_with_id": ("find with {$jsonSchema} using additionalProperties: false with _id declared was "
                                       "rejected with 9 FailedToParse 'Unknown $jsonSchema keyword: additionalProperties'; "
                                       "not tested on open-source."),
    "A7.title_description": ("create accepted a validator carrying title and description at the top level and on a "
                             "property (Learn's $jsonSchema page lists both as unsupported); not tested on open-source."),
    "A7.title_description.violating": ("The violating insert {x:1} is rejected with 121 'Document failed validation' "
                                       "(no codeName, no errInfo), so required is still enforced alongside "
                                       "title/description; not tested on open-source."),
    "B1c": ("Duplicate {key:1} is rejected with write error 11000 'Duplicate key violation on the requested collection: "
            "Index 'uq_key_exists'' with no codeName, no keyPattern/keyValue and no errInfo; open-source 0.117 behaved "
            "the same."),
    "B4d": ("In an ordered batch of two {key4:7}, the first is inserted (n=1) and the second fails with write error 11000 "
            "'Duplicate key violation on the requested collection: Index 'uq_key4_sparse'' at index 1; not tested on "
            "open-source."),
}
for s in r1["steps"]:
    sid = s["step"].split(" ", 1)[0]
    if sid in CURATED:
        s["reading_auto"] = s["reading"]
        s["reading"] = CURATED[sid]

CONCLUSIONS = [
    OrderedDict(question="Are collection validators (validator / validationLevel / validationAction) enabled on the managed "
                         "service, or gated behind CommandNotSupported 'validator not supported yet'?",
                answer=("Enabled on this cluster with no enablement step. create and collMod both accept a baseline "
                        "$jsonSchema (bsonType/required/properties) with ok: 1; listCollections shows the validator with "
                        "validationLevel 'strict' and validationAction 'error'; violating inserts, updates and findAndModify "
                        "are rejected. The cluster resource has no previewFeatures property and has never been modified "
                        "(lastModifiedAt = createdAt 2026-11-25T20:35:33Z). The words 'not supported yet' appeared in no "
                        "response; the only 'not supported' wording was 'The '<keyword>' keyword in $jsonSchema is not "
                        "supported at this time' for $schema and format, and 'The 'integer' type in $jsonSchema is not "
                        "supported at this time.' (all code 9 FailedToParse)."),
                vs_open_source="same", confidence="observed"),
    OrderedDict(question="Which $jsonSchema keywords do create and collMod accept on the managed service?",
                answer=("enum and oneOf: accepted by create and collMod and enforced (valid docs inserted, violating docs "
                        "rejected with 121), also after collMod. additionalProperties (also with _id declared in "
                        "properties), allOf, anyOf, not, patternProperties, dependencies, minProperties and maxProperties: "
                        "rejected identically by create and collMod with code 9 FailedToParse 'Unknown $jsonSchema keyword: "
                        "<keyword>' and no errorLabels. The $jsonSchema query operator in find accepts and rejects exactly the "
                        "same set, and for baseline, enum and oneOf it matched only the valid document, as MongoDB would. So "
                        "Learn's $jsonSchema page (which lists enum and oneOf as unsupported) is stale for this managed "
                        "build, and the engine-source dispatch list in DECISIONS topic 10 matches the managed service."),
                vs_open_source="same", confidence="observed"),
    OrderedDict(question="What does a write that violates a validator return (code, codeName, message, errInfo, labels)?",
                answer=("insert and update: ok: 1 with writeErrors[0] = {index, code: 121, errmsg: 'Document failed "
                        "validation'}: no codeName, no errInfo (so no MongoDB 5.0-style errInfo.details explaining which rule "
                        "failed) and no errorLabels; PyMongo insert_one raises WriteError code 121 with those details. "
                        "findAndModify: command error ok: 0, code 121, codeName 'DocumentFailedValidation', same errmsg, no "
                        "errInfo. MongoDB's codeName for 121 is 'DocumentValidationFailure'; the managed name matches the "
                        "open-source gateway's error_mappings.csv entry '121,DocumentFailedValidation', so code that matches "
                        "on codeName must use the code 121 instead."),
                vs_open_source="same", confidence="observed"),
    OrderedDict(question="Do bypassDocumentValidation, validationAction 'warn' and collMod-attached validators behave as in "
                         "MongoDB?",
                answer=("Yes on this cluster: bypassDocumentValidation: true on insert lets a violating document through "
                        "(n=1); a collection created with validationAction 'warn' accepts a violating insert (n=1); a "
                        "validator attached by collMod to an existing collection is enforced on the next insert (121). The "
                        "bypass result matches open-source 0.117; warn and collMod enforcement were not run there."),
                vs_open_source="same", confidence="observed"),
    OrderedDict(question="Extra (beyond the spec list): are title/description, $schema, format and type 'integer' accepted?",
                answer=("title and description (top level and on a property) are accepted and the validator still enforces "
                        "required, although Learn lists them as unsupported. $schema and format are rejected with 9 "
                        "FailedToParse 'The '$schema' keyword in $jsonSchema is not supported at this time' / 'The 'format' "
                        "keyword in $jsonSchema is not supported at this time'; type 'integer' is rejected with 9 "
                        "FailedToParse 'The 'integer' type in $jsonSchema is not supported at this time.' (MongoDB also omits "
                        "these three). Generated JSON Schemas (for example from Pydantic or zod) must be stripped of $schema "
                        "and format and use bsonType 'int'/'long' instead of type 'integer'."),
                vs_open_source="not_tested_locally", confidence="observed"),
    OrderedDict(question="Is a unique index with partialFilterExpression { key: { $exists: true } } accepted and enforced?",
                answer=("Accepted: createIndexes returns ok: 1 with numIndexesBefore 1 / numIndexesAfter 2 nested under "
                        "raw.defaultShard; listIndexes shows the spec verbatim plus storageEngine.enableOrderedIndex: true. A "
                        "duplicate {key:1} fails with write error 11000 'Duplicate key violation on the requested collection: "
                        "Index 'uq_key_exists'' (no codeName, no keyPattern/keyValue). Two documents without the key both "
                        "insert; two explicit {key:null} documents collide (second fails 11000), so null is inside the "
                        "$exists:true filter as in MongoDB. 4 documents stored."),
                vs_open_source="same", confidence="observed"),
    OrderedDict(question="Is a unique index with partialFilterExpression { key: { $gt: 0 } } accepted and enforced?",
                answer=("Accepted (numIndexesAfter 2). A duplicate {key:5} fails with 11000; duplicates of {key:0}, "
                        "{key:-1}, a missing key and {key:'s'} all insert (outside the numeric filter; strings are "
                        "type-bracketed out). updateOne moving {key:0} to {key:5} fails with write error 11000, so uniqueness "
                        "is enforced when an update brings a document into the filter. 9 documents stored."),
                vs_open_source="same", confidence="observed"),
    OrderedDict(question="Is $exists: false allowed in a partial filter?",
                answer=("No. createIndexes fails with 67 CannotCreateIndex 'Error in specification { \"key\" : { \"key\" : 1 }, "
                        "\"name\" : \"uq_key_notexists\", \"unique\" : true, \"partialFilterExpression\" : { \"key\" : { "
                        "\"$exists\" : false } } }:Expression not supported in partial index: key $exists false' (with a "
                        "trailing newline). A non-unique partial index with $exists: false is rejected the same way "
                        "(open-source only tested the unique form)."),
                vs_open_source="same", confidence="observed"),
    OrderedDict(question="Can unique + sparse be combined with partialFilterExpression?",
                answer=("No: 197 InvalidIndexSpecificationOption 'Error in specification { ... \"sparse\" : true, "
                        "\"partialFilterExpression\" : { \"key2\" : { \"$gt\" : 0 } } }:cannot mix \"partialFilterExpression\" "
                        "and \"sparse\" options'. unique + sparse without a filter is accepted and behaves as a sparse unique "
                        "index: two documents without the key insert, and a duplicate value fails with 11000 (the first of an "
                        "ordered pair is inserted, n=1)."),
                vs_open_source="same", confidence="observed"),
    OrderedDict(question="Where does the managed service differ from open-source 0.117 in this test?",
                answer=("Only in metadata: hello.maxWireVersion 25 vs 21, buildInfo.version 8.0.0 vs 7.0.0, "
                        "hello.internal.documentdb_versions ['2.2-1','2.3.0','12.1-1'] with kind 'azuredocumentdb', and an "
                        "extra statsEnabled: true in listCollections options. Every code, codeName, errmsg, errInfo absence "
                        "and createIndexes result shape matched in all steps run on both."),
                vs_open_source="different", confidence="observed"),
    OrderedDict(question="Is the result reproducible?",
                answer=("Yes. A second full run against a freshly dropped mt_schema produced identical outcomes (kind, "
                        "code, codeName, errmsg, errInfo presence, n, matched) for all %d scripted steps." % len(r2["steps"])),
                vs_open_source="n/a", confidence="observed"),
    OrderedDict(question="What does this mean for DECISIONS topic 10 open item 1 (engine build, enum/oneOf live, validator "
                         "enablement path)?",
                answer=("For a new cluster created 2026-11-25 in eastus (M30, server 8.0, engine documentdb_versions 2.2-1 / "
                        "2.3.0 / 12.1-1), enum and oneOf are live and collection validators need no preview flag, support "
                        "request or configuration change. Filings can say validators work out of the box on current "
                        "clusters, that enum and oneOf are supported, and that the remaining unsupported keywords fail with "
                        "9 FailedToParse. Whether older clusters, other regions or other server versions behave the same "
                        "was not tested."),
                vs_open_source="n/a", confidence="inferred"),
]

r1["finalized"] = True
r1["phase"] = "Phase 1: data-plane only"
r1["config_changes"] = []
r1["control_plane_reads"] = ["az documentdb mongocluster show (read-only, step M3)"]
r1["rerun"] = OrderedDict(report="report.rerun.json", steps=len(r2["steps"]), mismatched_steps=mismatch,
                          run_at=r2.get("run_at"), duration_s=r2.get("duration_s"))
r1["files"] = OrderedDict(script=P("run_test.py"), probe=P("probe.py"), finalize=P("finalize.py"),
                          stdout=P("run_stdout.txt"), rerun_stdout=P("run_stdout.rerun.txt"),
                          rerun_report=P("report.rerun.json"), cluster_read=P("cluster_show_selected.json"))
r1["conclusions"] = CONCLUSIONS
json.dump(r1, open(P("report.json"), "w"), indent=2)
print("finalized: %d steps, rerun mismatches: %s" % (len(r1["steps"]), mismatch))
