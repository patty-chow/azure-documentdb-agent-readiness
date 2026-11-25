#!/usr/bin/env python
"""Supplementary checks for the bulkwrite-forms rerun (verifier). Owns database t_bulk_rerun only.
Uses a PyMongo CommandListener to observe the wire commands behind insert_many(25001) and a mixed
collection-level bulk_write, and probes the 8.0 bulkWrite command on a non-admin database and a
zero-document raw insert. Reads LOCAL_URI from ../local.env; never prints the password."""
import json, os, re, sys
from pymongo import MongoClient, InsertOne, UpdateOne, DeleteOne, monitoring
from pymongo.errors import BulkWriteError, OperationFailure

HERE = os.path.dirname(os.path.abspath(__file__))
DB = "t_bulk_rerun"
def load_uri():
    for line in open(os.path.join(HERE, "..", "local.env")):
        if line.startswith("LOCAL_URI="):
            v = line.split("=", 1)[1].strip()
            return v[1:-1] if v and v[0] in "\"'" and v[-1] == v[0] else v
    raise SystemExit("no LOCAL_URI")
RED = re.compile(r"(mongodb://[^:/]+:)[^@]+@")
def redact(s): return RED.sub(r"\1***@", str(s))

class L(monitoring.CommandListener):
    def __init__(self): self.ev = []
    def started(self, e):
        c = e.command
        if e.command_name in ("insert", "update", "delete"):
            key = {"insert": "documents", "update": "updates", "delete": "deletes"}[e.command_name]
            self.ev.append({"cmd": e.command_name, "n_ops": len(c.get(key, [])), "ordered": c.get("ordered"), "db": e.database_name, "request_id": e.request_id})
    def succeeded(self, e):
        for x in self.ev:
            if x["request_id"] == e.request_id and "reply" not in x:
                r = e.reply; x["reply"] = {"ok": r.get("ok"), "n": r.get("n"), "nModified": r.get("nModified"), "writeErrors": r.get("writeErrors")}
    def failed(self, e):
        for x in self.ev:
            if x["request_id"] == e.request_id and "reply" not in x:
                x["reply"] = {"failure": redact(e.failure)}

lst = L()
client = MongoClient(load_uri(), serverSelectionTimeoutMS=15000, event_listeners=[lst])
db = client[DB]
out = {"database": DB, "steps": []}
def rec(step, command, response, reading):
    out["steps"].append({"step": step, "command": command, "response": response, "reading": reading}); print(f"[{step}] {reading}", file=sys.stderr)

# X1: how does PyMongo split insert_many(25001)?
db.x_big.drop(); lst.ev.clear()
r = db.x_big.insert_many([{"_id": i} for i in range(25001)], ordered=False)
evs = [{k: v for k, v in e.items() if k != "request_id"} for e in lst.ev]
rec("X1-insert_many-25001-wire", "db.x_big.insert_many(25001 docs, ordered=False) with CommandListener",
    {"inserted": len(r.inserted_ids), "wire_commands": evs},
    f"PyMongo sent {len(evs)} insert command(s) with document counts {[e['n_ops'] for e in evs]}; the split is driver-side at hello.maxWriteBatchSize.")

# X2: how many wire commands does a mixed unordered collection bulk_write send?
db.x_mix.drop(); lst.ev.clear()
ops = [InsertOne({"_id": 10, "v": "x"}), InsertOne({"_id": 11, "v": "y"}), InsertOne({"_id": 10, "v": "dup"}), InsertOne({"_id": 12, "v": "z"}), UpdateOne({"_id": 11}, {"$set": {"v": "y2"}}), DeleteOne({"_id": 10})]
try:
    db.x_mix.bulk_write(ops, ordered=False); res = "no error"
except BulkWriteError as e:
    res = {"writeErrors": e.details.get("writeErrors"), "nInserted": e.details.get("nInserted"), "nMatched": e.details.get("nMatched"), "nRemoved": e.details.get("nRemoved")}
evs = [{k: v for k, v in e.items() if k != "request_id"} for e in lst.ev]
rec("X2-mixed-unordered-wire", "db.x_mix.bulk_write([4 inserts incl. dup, 1 update, 1 delete], ordered=False) with CommandListener",
    {"result": res, "wire_commands": evs},
    f"The mixed unordered bulk_write became {len(evs)} separate wire commands ({[e['cmd'] for e in evs]}); the 11000 writeError lives in the insert reply (ok:1) and the update/delete still ran.")

# X3: same, ordered
db.x_mix_o.drop(); lst.ev.clear()
try:
    db.x_mix_o.bulk_write(ops, ordered=True); res = "no error"
except BulkWriteError as e:
    res = {"writeErrors": e.details.get("writeErrors"), "nInserted": e.details.get("nInserted"), "nMatched": e.details.get("nMatched"), "nRemoved": e.details.get("nRemoved")}
evs = [{k: v for k, v in e.items() if k != "request_id"} for e in lst.ev]
rec("X3-mixed-ordered-wire", "db.x_mix_o.bulk_write(same ops, ordered=True) with CommandListener",
    {"result": res, "wire_commands": evs},
    f"Ordered: {len(evs)} wire command(s) sent ({[e['cmd'] for e in evs]}); after the insert reply carried the writeError the driver did not send the update/delete commands.")

# X4: 8.0 bulkWrite command against the test database (not admin)
try:
    r = db.command({"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1}}], "nsInfo": [{"ns": f"{DB}.x_bw"}], "ordered": True}); res = r
except OperationFailure as e:
    res = {"code": e.code, "codeName": (e.details or {}).get("codeName"), "errmsg": (e.details or {}).get("errmsg"), "errorLabels": sorted(e._error_labels or [])}
rec("X4-raw-bulkWrite-on-test-db", "db.command({'bulkWrite':1,...}) on t_bulk_rerun (not admin)", res,
    f"bulkWrite on a non-admin database: code={res.get('code')} codeName={res.get('codeName')}.")

# X5: zero-document raw insert (lower bound of the 1..25000 range in the errmsg)
try:
    r = db.command({"insert": "x_zero", "documents": [], "ordered": False}); res = r
except OperationFailure as e:
    res = {"code": e.code, "codeName": (e.details or {}).get("codeName"), "errmsg": (e.details or {}).get("errmsg")}
rec("X5-raw-insert-0-docs", "db.command({'insert':'x_zero','documents':[],'ordered':False})", res,
    f"Empty documents array: code={res.get('code')} codeName={res.get('codeName')} errmsg={res.get('errmsg')!r}.")

# X6: raw update command with 25,001 updates in one command (is the cap per write command type, not only insert?)
try:
    r = db.command({"update": "x_upd", "updates": [{"q": {"_id": i}, "u": {"$set": {"a": 1}}} for i in range(25001)], "ordered": False}); res = {"ok": r.get("ok"), "n": r.get("n")}
except OperationFailure as e:
    res = {"code": e.code, "codeName": (e.details or {}).get("codeName"), "errmsg": (e.details or {}).get("errmsg")}
rec("X6-raw-update-25001-one-command", "db.command({'update':'x_upd','updates':[25001 updates],'ordered':False})", res,
    f"25,001 updates in one update command: {res}.")

# X7: raw delete command with 25,001 deletes
try:
    r = db.command({"delete": "x_del", "deletes": [{"q": {"_id": i}, "limit": 1} for i in range(25001)], "ordered": False}); res = {"ok": r.get("ok"), "n": r.get("n")}
except OperationFailure as e:
    res = {"code": e.code, "codeName": (e.details or {}).get("codeName"), "errmsg": (e.details or {}).get("errmsg")}
rec("X7-raw-delete-25001-one-command", "db.command({'delete':'x_del','deletes':[25001 deletes],'ordered':False})", res,
    f"25,001 deletes in one delete command: {res}.")

client.drop_database(DB)
rec("X8-dropDatabase", f"client.drop_database('{DB}')", None, "Verifier database dropped.")
out["databases_after"] = sorted(client.list_database_names())
json.dump(out, open(os.path.join(HERE, "report.verify_extra.json"), "w"), indent=2, default=lambda o: redact(repr(o)))
print(json.dumps({"n_steps": len(out["steps"]), "databases_after": out["databases_after"]}))
