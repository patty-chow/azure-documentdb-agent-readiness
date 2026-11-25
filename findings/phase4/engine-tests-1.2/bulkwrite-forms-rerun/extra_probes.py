#!/usr/bin/env python
"""bulkwrite-forms REPRODUCTION, extra probes (not part of the tester's script).

Small probes that test gaps in the tester's conclusions, run against the same container and the
same database the reproduction owns (t_bulk_rerun), which is dropped at the start and at the end:
  X1  unknown-command control: is 'bulkWrite' answered exactly like a command name that does not exist?
  X2  legacy isMaster: does the handshake form drivers use first advertise the same limits as hello?
  X3  interleaved op types, ordered vs unordered: how does PyMongo group them into commands?
      (the tester's batches were already in type order, so regrouping was not shown)
  X4  25,001 UpdateOne and 25,001 DeleteOne through collection-level bulk_write: does the driver
      split update and delete batches at 25,000 too? (the tester showed this for inserts only)
  X5  duplicate on a secondary unique index, through insert_many and through a raw insert command:
      code, errmsg wording, and which fields a write error carries
  X9  drop t_bulk_rerun and confirm it is gone
Reuses the helpers of the copied run.py (WireLog, run, record, err_info, redaction) so every step is
recorded the same way. Never prints or stores the password. Writes extra.json next to this file.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run as R  # noqa: E402  (the copied tester script; only its helpers are used, main() is not called)

from pymongo import DeleteOne, InsertOne, MongoClient, UpdateOne  # noqa: E402
from pymongo.errors import BulkWriteError  # noqa: E402

DB = R.DB
assert DB == "t_bulk_rerun", DB


def main():
    wire = R.WireLog()
    client = MongoClient(
        R.URI,
        serverSelectionTimeoutMS=15000,
        connectTimeoutMS=15000,
        socketTimeoutMS=R.SOCKET_TIMEOUT_MS,
        event_listeners=[wire],
        appname="engine-tests-1.2-bulkwrite-forms-rerun-extra",
    )
    db = client[DB]
    run = R.run

    run("X0-pre-clean-dropDatabase", f"client.drop_database('{DB}')", lambda: client.drop_database(DB),
        f"Dropped {DB} (the only database the reproduction owns) before the extra probes.")

    # X1 unknown-command control
    run(
        "X1a-unknown-command-control",
        "db.command({'noSuchCommandXyz': 1})  # a command name that exists nowhere",
        lambda: db.command({"noSuchCommandXyz": 1}),
        lambda r: f"An invented command name was accepted: {r}.",
        R.of_reading("An invented command name"),
    )
    run(
        "X1b-bulkWrite-same-db-again",
        "db.command({'bulkWrite': 1, 'ops': [{'insert': 0, 'document': {'_id': 1}}], 'nsInfo': [{'ns': 't_bulk_rerun.x1'}]})",
        lambda: db.command({"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1}}], "nsInfo": [{"ns": f"{DB}.x1"}]}),
        lambda r: f"bulkWrite was accepted: {r}.",
        R.of_reading("bulkWrite (control pair for X1a)"),
    )

    # X2 legacy isMaster
    run(
        "X2-legacy-isMaster",
        "client.admin.command('isMaster')",
        lambda: client.admin.command("isMaster"),
        lambda r: (
            f"Legacy isMaster advertises maxWriteBatchSize={r.get('maxWriteBatchSize')}, maxWireVersion={r.get('maxWireVersion')}, "
            f"msg={r.get('msg')!r}, ismaster={r.get('ismaster')}, maxMessageSizeBytes={r.get('maxMessageSizeBytes')}."
        ),
    )

    # X3 interleaved op types
    def interleaved():
        return [
            InsertOne({"_id": 1}),
            UpdateOne({"_id": 1}, {"$set": {"a": 1}}),
            InsertOne({"_id": 2}),
            DeleteOne({"_id": 2}),
            InsertOne({"_id": 3}),
            UpdateOne({"_id": 3}, {"$set": {"a": 3}}),
        ]

    for sid, coll, ordered in (("X3a-interleaved-ordered", "inter_o", True), ("X3b-interleaved-unordered", "inter_u", False)):
        run(
            sid,
            f"db.{coll}.bulk_write([InsertOne({{'_id':1}}), UpdateOne({{'_id':1}},{{'$set':{{'a':1}}}}), InsertOne({{'_id':2}}), DeleteOne({{'_id':2}}), InsertOne({{'_id':3}}), UpdateOne({{'_id':3}},{{'$set':{{'a':3}}}})], ordered={ordered})",
            lambda coll=coll, ordered=ordered: R.bwr(db[coll].bulk_write(interleaved(), ordered=ordered)),
            lambda r: (
                f"Interleaved batch (insert, update, insert, delete, insert, update) with ordered={ordered} succeeded "
                f"(inserted={r['inserted_count']} matched={r['matched_count']} modified={r['modified_count']} deleted={r['deleted_count']}) "
                f"and went over the wire as {R.wire_summary(wire.events)}."
            ),
            lambda e: R.bwe_reading(e, f"wire: {R.wire_summary(wire.events)}."),
            wire=wire,
        )
        run(
            sid + "-state",
            f"list(db.{coll}.find().sort('_id'))",
            lambda coll=coll: list(db[coll].find().sort("_id")),
            lambda r, coll=coll: f"{coll} holds {r}.",
        )

    # X4 driver splitting for update and delete batches
    run(
        "X4a-seed-25001",
        "db.big_ud.insert_many([{'_id': i} for i in range(25001)], ordered=False)",
        lambda: (lambda r: {"inserted_ids_count": len(r.inserted_ids)})(db.big_ud.insert_many([{"_id": i} for i in range(25001)], ordered=False)),
        lambda r: f"Seeded big_ud with {r['inserted_ids_count']} documents (wire {R.wire_summary(wire.events)}).",
        wire=wire,
    )
    run(
        "X4b-bulk_write-25001-UpdateOne",
        "db.big_ud.bulk_write([UpdateOne({'_id': i}, {'$set': {'u': 1}}) for i in range(25001)], ordered=False)",
        lambda: R.bwr(db.big_ud.bulk_write([UpdateOne({"_id": i}, {"$set": {"u": 1}}) for i in range(25001)], ordered=False)),
        lambda r: (
            f"Collection-level bulk_write of 25,001 UpdateOne ops succeeded (matched={r['matched_count']} modified={r['modified_count']}) "
            f"as {R.wire_summary(wire.events)}."
        ),
        lambda e: R.bwe_reading(e, f"wire: {R.wire_summary(wire.events)}.") if isinstance(e, BulkWriteError) else R.of_reading("bulk_write(25001 UpdateOne)")(e),
        wire=wire,
    )
    run("X4c-count-updated", "db.big_ud.count_documents({'u': 1})", lambda: db.big_ud.count_documents({"u": 1}),
        lambda r: f"{r} documents in big_ud carry u=1 after the 25,001-op update bulk_write.")
    run(
        "X4d-bulk_write-25001-DeleteOne",
        "db.big_ud.bulk_write([DeleteOne({'_id': i}) for i in range(25001)], ordered=False)",
        lambda: R.bwr(db.big_ud.bulk_write([DeleteOne({"_id": i}) for i in range(25001)], ordered=False)),
        lambda r: f"Collection-level bulk_write of 25,001 DeleteOne ops succeeded (deleted={r['deleted_count']}) as {R.wire_summary(wire.events)}.",
        lambda e: R.bwe_reading(e, f"wire: {R.wire_summary(wire.events)}.") if isinstance(e, BulkWriteError) else R.of_reading("bulk_write(25001 DeleteOne)")(e),
        wire=wire,
    )
    run("X4e-count-after-delete", "db.big_ud.count_documents({})", lambda: db.big_ud.count_documents({}),
        lambda r: f"big_ud holds {r} documents after the 25,001-op delete bulk_write.")

    # X5 secondary unique index duplicate
    run("X5a-create-unique-index", "db.uniq.create_index('email', unique=True)", lambda: db.uniq.create_index("email", unique=True),
        lambda r: f"Created unique index {r!r} on uniq.email.")
    run(
        "X5b-insert_many-dup-secondary-unique",
        "db.uniq.insert_many([{'_id':1,'email':'a'},{'_id':2,'email':'a'},{'_id':3,'email':'b'}], ordered=False)",
        lambda: {"unexpected_success": len(db.uniq.insert_many([{"_id": 1, "email": "a"}, {"_id": 2, "email": "a"}, {"_id": 3, "email": "b"}], ordered=False).inserted_ids)},
        "Unexpectedly succeeded despite the duplicate email.",
        lambda e: R.bwe_reading(e, f"errmsg {[w.get('errmsg') for w in e.details.get('writeErrors', [])] if isinstance(e, BulkWriteError) else None}; wire: {R.wire_summary(wire.events)}."),
        wire=wire,
    )
    run(
        "X5c-raw-insert-dup-secondary-unique",
        "db.command({'insert':'uniq','documents':[{'_id':4,'email':'b'},{'_id':5,'email':'c'}],'ordered':False})",
        lambda: db.command({"insert": "uniq", "documents": [{"_id": 4, "email": "b"}, {"_id": 5, "email": "c"}], "ordered": False}),
        lambda r: (
            f"Raw insert with a duplicate on the secondary unique index returns ok={r.get('ok')} n={r.get('n')} writeErrors={r.get('writeErrors')} "
            f"(write error keys {sorted((r.get('writeErrors') or [{}])[0].keys())}; reply keys {sorted(r.keys())})."
        ),
        R.of_reading("Raw insert with a duplicate on the secondary unique index"),
    )
    run("X5d-uniq-state", "list(db.uniq.find().sort('_id'))", lambda: list(db.uniq.find().sort("_id")),
        lambda r: f"uniq holds {r}.")

    # X9 cleanup
    run("X9a-dropDatabase", f"client.drop_database('{DB}')", lambda: client.drop_database(DB),
        f"Dropped {DB} at the end of the extra probes; no other database was touched.")

    def gone():
        r = client.admin.command({"listDatabases": 1, "nameOnly": True, "filter": {"name": DB}})
        names = [d.get("name") for d in r.get("databases", [])]
        return {"t_bulk_rerun_present": DB in names, "databases_returned": names}

    run("X9b-verify-dropped", f"client.admin.command({{'listDatabases':1,'nameOnly':True,'filter':{{'name':'{DB}'}}}})", gone,
        lambda r: f"After the final drop, {DB} present = {r['t_bulk_rerun_present']}.")

    out = {"note": "extra probes added by the reproduction; not part of the tester's script", "database": DB, "steps": R.steps}
    with open(os.path.join(HERE, "extra.json"), "w") as f:
        json.dump(out, f, indent=2, default=lambda o: R.redact(repr(o)))
    print(json.dumps({"n_extra_steps": len(R.steps)}))
    client.close()


if __name__ == "__main__":
    main()
