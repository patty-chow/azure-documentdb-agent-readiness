#!/usr/bin/env python
"""m-ttl: TTL behaviour on the managed Azure DocumentDB cluster (database mt_ttl only).

Collects raw evidence into raw.json and then runs analyze.py to build report.json (both next to this
script). Reads ../managed.env; never prints or writes the password, a URI or a host name.
Data-plane only: no cluster configuration is read or changed beyond hello/buildInfo.

Timeline: hello, buildInfo, clock offset -> createIndexes (exp TTL 5 s, exp2 TTL 5 s, compound TTL
attempt, non-numeric expireAfterSeconds attempt) -> listIndexes -> wait (time.sleep) for second :07 of a
minute -> insert the test documents -> poll every 15 s for 300 s on a fixed schedule (time.sleep),
inserting one already-expired probe document after each poll during the first 230 s -> supplementary
1 s fine-grained probe (<= 75 s) -> final listing, $$NOW, clock offset -> dropDatabase mt_ttl.
"""
import json, os, re, sys, time, warnings, platform, urllib.parse, datetime as dt
warnings.filterwarnings("ignore", message=".*CosmosDB.*")  # PyMongo's CosmosDB host warning (expected)
import bson, pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError, OperationFailure

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, "..", "managed.env")
RAW_PATH = os.path.join(HERE, "raw.json")

DB, COLL = "mt_ttl", "docs"
TTL = 5
POLL_EVERY, POLL_MAX, PROBE_UNTIL = 15, 300, 230
INSERT_AT_SECOND = 7
FINE_EVERY, FINE_MAX = 1.0, 75
HARD_DEADLINE_S = 540
_T0 = time.monotonic()


def remaining():
    return HARD_DEADLINE_S - (time.monotonic() - _T0)


# ---------------------------------------------------------------- env + sanitising
def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            s = line.rstrip("\n").strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            k = k.strip()
            if k.startswith("export "):
                k = k[len("export "):].strip()
            env[k] = v.strip().strip('"').strip("'")
    return env


ENV = load_env(ENV_PATH)
_SECRETS = set()
for _k in ("MANAGED_URI", "MANAGED_GLOBAL_URI", "MANAGED_PASS"):
    _v = ENV.get(_k)
    if _v:
        _SECRETS.update({_v, urllib.parse.quote_plus(_v), urllib.parse.quote(_v, safe="")})
_SECRETS = sorted((s for s in _SECRETS if s), key=len, reverse=True)
_HOSTS = [(ENV.get("MANAGED_GLOBAL_HOST"), "<cluster-global-host>"), (ENV.get("MANAGED_HOST"), "<cluster-host>")]
_NODE_RE = re.compile(r"[A-Za-z0-9.-]+\.mongocluster\.cosmos\.azure\.com")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_GUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")


def san(s):
    s = str(s)
    for sec in _SECRETS:
        s = s.replace(sec, "<redacted>")
    for h, ph in _HOSTS:
        if h:
            s = s.replace(h, ph)
    s = _NODE_RE.sub("<node-host>", s)
    s = _EMAIL_RE.sub("<email>", s)
    s = _GUID_RE.sub("<guid>", s)
    return s


# ---------------------------------------------------------------- helpers
def now():
    return dt.datetime.now(dt.timezone.utc)


def iso(d):
    if d is None:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc).isoformat(timespec="milliseconds")


def P(s):
    return dt.datetime.fromisoformat(s) if s else None


def trunc_ms(d):
    return d.replace(microsecond=(d.microsecond // 1000) * 1000)


def tag(o):
    """JSON-safe copy that keeps BSON type information visible (Extended-JSON-like markers)."""
    if o is None or isinstance(o, bool):
        return o
    if isinstance(o, bson.int64.Int64):
        return {"$numberLong": str(int(o))}
    if isinstance(o, (int, float, str)):
        return o
    if isinstance(o, dt.datetime):
        return {"$date": iso(o)}
    if isinstance(o, bson.timestamp.Timestamp):
        return {"$timestamp": {"t": o.time, "i": o.inc}}
    if isinstance(o, bson.objectid.ObjectId):
        return {"$oid": str(o)}
    if isinstance(o, bson.decimal128.Decimal128):
        return {"$numberDecimal": str(o)}
    if isinstance(o, (bytes, bson.binary.Binary)):
        return {"$binaryHex": bytes(o).hex()}
    if isinstance(o, dict):
        return {str(k): tag(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [tag(v) for v in o]
    return repr(o)


def err_dict(e):
    d = {"exception": type(e).__name__}
    if isinstance(e, OperationFailure):
        det = dict(e.details or {})
        d["code"] = det.get("code", e.code)
        d["codeName"] = det.get("codeName")
        d["errmsg"] = det.get("errmsg", str(e))
        d["errorLabels"] = det.get("errorLabels", [])
        d["errorLabelsFieldInReply"] = "errorLabels" in det
        d["rawReply"] = det
    else:
        d["errmsg"] = str(e)
        labels = getattr(e, "_error_labels", None)
        d["errorLabels"] = sorted(labels) if labels else []
    return d


raw = {"test": "m-ttl", "database": DB, "collection": COLL, "meta": {}, "steps": [], "clock": [],
       "insert": None, "polls": [], "fine": None}


def log(m):
    print(san(m)[:900], file=sys.stderr, flush=True)


def save_raw():
    s = san(json.dumps(raw, indent=1, default=str))
    with open(RAW_PATH, "w") as f:
        f.write(s)


def default_err_reading(r):
    return f"Rejected with code {r.get('code')} {r.get('codeName')}: {r.get('errmsg')}"


def run_step(name, command, fn, reading_ok, reading_err=None, **extra):
    t0 = now()
    ok = True
    try:
        resp = fn()
    except PyMongoError as e:
        ok, resp = False, err_dict(e)
    t1 = now()
    try:
        if ok:
            reading = reading_ok(resp) if callable(reading_ok) else reading_ok
        else:
            reading = (reading_err or default_err_reading)(resp) if (reading_err is None or callable(reading_err)) else reading_err
    except Exception as ex:  # never let a reading crash the run
        reading = f"(reading could not be generated: {ex!r})"
    entry = {"step": name, "command": command, "startedAt": iso(t0), "endedAt": iso(t1), "ok": ok,
             "response": tag(resp), "reading": reading}
    entry.update(extra)
    raw["steps"].append(entry)
    log(f"[{name}] ok={ok} {json.dumps(entry['response'], default=str)[:500]}")
    return entry, (resp if ok else None)


def clock_probe(client):
    t0 = time.time()
    h = client.admin.command("hello")
    t1 = time.time()
    lt = h.get("localTime")
    out = {"clientSentAt": iso(dt.datetime.fromtimestamp(t0, dt.timezone.utc)),
           "clientRepliedAt": iso(dt.datetime.fromtimestamp(t1, dt.timezone.utc)),
           "helloLocalTimeRaw": tag(lt), "helloLocalTimeBsonType": type(lt).__name__,
           "operationTime": tag(h.get("operationTime"))}
    if isinstance(lt, dt.datetime):
        lt_s = (lt if lt.tzinfo else lt.replace(tzinfo=dt.timezone.utc)).timestamp()
    elif isinstance(lt, int):
        lt_s = int(lt) / 1000.0
    else:
        lt_s = None
    if lt_s is not None:
        out["helloLocalTimeAsUtc"] = iso(dt.datetime.fromtimestamp(lt_s, dt.timezone.utc))
        out["offsetSecondsServerMinusClient"] = round(lt_s - (t0 + t1) / 2, 3)
        out["uncertaintySeconds"] = round((t1 - t0) / 2, 3)
    return out


def build_docs(t):
    past = trunc_ms(t - dt.timedelta(seconds=60))
    fut = trunc_ms(t + dt.timedelta(seconds=90))
    day = trunc_ms(t + dt.timedelta(days=1))
    rows = [
        ({"_id": "past_date_60s", "kind": "exp = BSON Date 60 s before insert", "exp": past}, "exp", "date", past),
        ({"_id": "future_date_90s", "kind": "exp = BSON Date 90 s after insert", "exp": fut}, "exp", "date", fut),
        ({"_id": "string_value", "kind": "exp = ISO-8601 string of a time 60 s before insert", "exp": iso(past)}, "exp", "string", None),
        ({"_id": "number_value", "kind": "exp = int64 epoch milliseconds of a time 60 s before insert",
          "exp": bson.int64.Int64(int(past.timestamp() * 1000))}, "exp", "long", None),
        ({"_id": "missing_field", "kind": "no exp field (and no exp2 field)"}, "exp", "missing", None),
        ({"_id": "exp2_past_date_60s", "kind": "exp2 = BSON Date 60 s before insert, no exp field (covered only by the second TTL index exp2_ttl)",
          "exp2": past}, "exp2", "date", past),
        ({"_id": "array_of_dates", "kind": "extra for open-source parity: exp = [Date 60 s before insert, Date 1 day after insert]",
          "exp": [past, day]}, "exp", "array<date>", past),
        ({"_id": "null_value", "kind": "extra for open-source parity: exp = null", "exp": None}, "exp", "null", None),
    ]
    meta = []
    for doc, field, vtype, earliest in rows:
        meta.append({"_id": doc["_id"], "kind": doc["kind"], "ttlField": field, "valueType": vtype,
                     "value": tag(doc[field]) if field in doc else "<absent>",
                     "eligibleAt": iso(earliest + dt.timedelta(seconds=TTL)) if earliest else None,
                     "expectedToExpire": earliest is not None})
    return [r[0] for r in rows], meta


def ci_cmd(spec):
    return 'db.command({"createIndexes": "docs", "indexes": [%s]})' % json.dumps(spec)


def ci_ok_reading(label):
    # the managed gateway answers createIndexes in mongos form: {"raw": {"defaultShard": {...}}, "ok": 1}
    def f(r):
        shards = r.get("raw") or {"(top level)": r}
        parts = [f"{sh}: numIndexesBefore={d.get('numIndexesBefore')}, numIndexesAfter={d.get('numIndexesAfter')}, "
                 f"createdCollectionAutomatically={d.get('createdCollectionAutomatically')}" + (f", note={d.get('note')!r}" if d.get("note") else "")
                 for sh, d in shards.items()]
        return f"{label} accepted (ok={r.get('ok')}); reply is per shard under raw: " + "; ".join(parts) + "."
    return f


def main():
    raw["meta"] = {"python": platform.python_version(), "pymongo": pymongo.version,
                   "uriVariable": "MANAGED_URI (plain host, mongodb+srv)", "scriptStartedAt": iso(now()),
                   "ttlSeconds": TTL, "pollEverySeconds": POLL_EVERY, "pollMaxSeconds": POLL_MAX,
                   "probeUntilSeconds": PROBE_UNTIL, "insertAtSecondOfMinute": INSERT_AT_SECOND,
                   "fineEverySeconds": FINE_EVERY, "fineMaxSeconds": FINE_MAX}
    client = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=15000, connectTimeoutMS=15000,
                         socketTimeoutMS=30000, tz_aware=True, appname="m-ttl")
    admin, db = client.admin, client[DB]
    try:
        run_step("hello", 'client.admin.command("hello")', lambda: admin.command("hello"),
                 lambda r: (f"Gateway answered hello with maxWireVersion {r.get('maxWireVersion')}, msg {r.get('msg')!r}, "
                            f"internal {r.get('internal')} and localTime as BSON {type(r.get('localTime')).__name__} "
                            f"(MongoDB documents hello.localTime as a Date)."))
        run_step("buildInfo", 'client.admin.command("buildInfo")', lambda: admin.command("buildInfo"),
                 lambda r: f"Server reports version {r.get('version')} (versionArray {r.get('versionArray')}).")
        e, r = run_step("clock offset before insert", 'time.time(); client.admin.command("hello"); time.time()  # hello.localTime vs client midpoint',
                        lambda: clock_probe(client),
                        lambda r: (f"Server clock minus client clock = {r.get('offsetSecondsServerMinusClient')} s "
                                   f"(+/- {r.get('uncertaintySeconds')} s half round trip), so client timestamps below match the server clock to well under a second."))
        if r:
            raw["clock"].append(dict(r, label="before insert"))
        run_step("mt_ttl exists before test", 'DB in client.list_database_names()  # only membership of mt_ttl is recorded',
                 lambda: {"mt_ttl_exists": DB in client.list_database_names()},
                 lambda r: "mt_ttl " + ("already existed and is dropped next." if r["mt_ttl_exists"] else "did not exist, so the test starts from an empty database."))
        if raw["steps"][-1]["response"].get("mt_ttl_exists"):
            run_step("clean start: dropDatabase mt_ttl", 'client["mt_ttl"].command("dropDatabase")',
                     lambda: db.command("dropDatabase"), lambda r: f"Leftover mt_ttl dropped (ok={r.get('ok')}).")

        spec_exp = {"expireAfterSeconds": TTL, "name": "exp_ttl", "key": {"exp": 1}}
        spec_exp2 = {"expireAfterSeconds": TTL, "name": "exp2_ttl", "key": {"exp2": 1}}
        spec_cmp = {"expireAfterSeconds": TTL, "name": "ab_ttl", "key": {"a": 1, "b": 1}}
        spec_bad = {"expireAfterSeconds": "abc", "name": "exp3_bad", "key": {"exp3": 1}}
        run_step("create TTL index on exp (expireAfterSeconds 5)", ci_cmd(spec_exp) + "  # mongosh: db.docs.createIndex({exp: 1}, {expireAfterSeconds: 5, name: 'exp_ttl'})",
                 lambda: db.command({"createIndexes": COLL, "indexes": [spec_exp]}), ci_ok_reading("Single-field TTL index exp_ttl"))
        run_step("create second TTL index on exp2 (expireAfterSeconds 5)", ci_cmd(spec_exp2) + "  # mongosh: db.docs.createIndex({exp2: 1}, {expireAfterSeconds: 5, name: 'exp2_ttl'})",
                 lambda: db.command({"createIndexes": COLL, "indexes": [spec_exp2]}), ci_ok_reading("Second single-field TTL index exp2_ttl on the same collection"))
        run_step("create compound TTL index {a: 1, b: 1}", ci_cmd(spec_cmp) + "  # mongosh: db.docs.createIndex({a: 1, b: 1}, {expireAfterSeconds: 5, name: 'ab_ttl'})",
                 lambda: db.command({"createIndexes": COLL, "indexes": [spec_cmp]}),
                 lambda r: f"UNEXPECTED: compound TTL index accepted: {r}.",
                 lambda r: f"Compound TTL index rejected with code {r.get('code')} {r.get('codeName')}: {r.get('errmsg')}")
        run_step("create TTL index with non-numeric expireAfterSeconds (open-source parity)", ci_cmd(spec_bad) + "  # mongosh: db.docs.createIndex({exp3: 1}, {expireAfterSeconds: 'abc', name: 'exp3_bad'})",
                 lambda: db.command({"createIndexes": COLL, "indexes": [spec_bad]}),
                 lambda r: f"UNEXPECTED: non-numeric expireAfterSeconds accepted: {r}.",
                 lambda r: f"Non-numeric expireAfterSeconds rejected with code {r.get('code')} {r.get('codeName')}: {r.get('errmsg')}")
        run_step("listIndexes after createIndexes attempts", 'db.command({"listIndexes": "docs"})',
                 lambda: db.command({"listIndexes": COLL}),
                 lambda r: "Indexes present: " + "; ".join(
                     f"{i.get('name')} key={dict(i.get('key', {}))} expireAfterSeconds={i.get('expireAfterSeconds')!r} ({type(i.get('expireAfterSeconds')).__name__})"
                     for i in r["cursor"]["firstBatch"]) + ".")

        # ---- align the insert to second :07 of a minute so that every 15 s poll window has a fixed phase
        t = now()
        target = t.replace(second=INSERT_AT_SECOND, microsecond=0)
        if target <= t + dt.timedelta(seconds=1):
            target += dt.timedelta(minutes=1)
        wait = (target - now()).total_seconds()
        raw["meta"]["alignmentWaitSeconds"] = round(wait, 3)
        log(f"waiting {wait:.1f} s for second :{INSERT_AT_SECOND:02d}")
        time.sleep(max(0.0, wait))

        docs, meta = build_docs(now())
        e, r = run_step("insert test documents",
                        'db.command({"insert": "docs", "documents": [<the 8 documents in insert.documents>], "ordered": True})',
                        lambda: db.command({"insert": COLL, "documents": docs, "ordered": True}),
                        lambda r: f"Insert acknowledged with n={r.get('n')} (ok={r.get('ok')}); writeErrors={r.get('writeErrors')}.",
                        documents=tag(docs))
        raw["insert"] = {"sentAt": e["startedAt"], "repliedAt": e["endedAt"], "ok": e["ok"], "documents": meta}
        save_raw()
        if not e["ok"]:
            raise RuntimeError("insert failed; polling skipped")

        # ---- poll every 15 s on a fixed schedule for up to 300 s
        t_ins, t_base = P(raw["insert"]["sentAt"]), P(raw["insert"]["repliedAt"])
        k = 0
        while True:
            target = t_base + dt.timedelta(seconds=POLL_EVERY * k)
            d = (target - now()).total_seconds()
            if d > 0:
                time.sleep(d)
            tb = now()
            entry = {"poll": k, "targetAt": iso(target), "sentAt": iso(tb),
                     "secondsAfterInsert": round((tb - t_ins).total_seconds(), 1)}
            try:
                rr = db.command({"find": COLL, "filter": {}, "projection": {"_id": 1}, "batchSize": 1000})
                ta = now()
                ids = sorted(x["_id"] for x in rr["cursor"]["firstBatch"])
                entry.update({"repliedAt": iso(ta), "ok": True, "replyOk": rr.get("ok"),
                              "cursorId": tag(rr["cursor"].get("id")), "count": len(ids), "present": ids})
            except PyMongoError as ex:
                entry.update({"repliedAt": iso(now()), "ok": False, "error": tag(err_dict(ex))})
            if k >= 1 and (tb - t_ins).total_seconds() <= PROBE_UNTIL:
                pid = f"probe_{k:02d}"
                tp = now()
                expv = trunc_ms(tp - dt.timedelta(seconds=60))
                pdoc = {"_id": pid, "kind": "probe: exp = BSON Date 60 s before its insert (eligible on insert)", "exp": expv}
                pe = {"_id": pid, "kind": pdoc["kind"], "exp": iso(expv),
                      "eligibleAt": iso(expv + dt.timedelta(seconds=TTL)), "sentAt": iso(tp),
                      "command": 'db.command({"insert": "docs", "documents": [{"_id": "%s", "kind": "...", "exp": ISODate("%s")}]})' % (pid, iso(expv))}
                try:
                    pr = db.command({"insert": COLL, "documents": [pdoc]})
                    pe.update({"repliedAt": iso(now()), "ok": True, "reply": tag(pr)})
                except PyMongoError as ex:
                    pe.update({"repliedAt": iso(now()), "ok": False, "error": tag(err_dict(ex))})
                entry["probeInserted"] = pe
            raw["polls"].append(entry)
            log(f"poll {k} +{entry['secondsAfterInsert']}s ok={entry.get('ok')} n={entry.get('count')} present={entry.get('present')}"
                + (f" probe={entry['probeInserted']['_id']}" if 'probeInserted' in entry else ""))
            k += 1
            if POLL_EVERY * k > POLL_MAX or remaining() < 40:
                break
        save_raw()
        raw["steps"].append({"step": "poll every 15 s for 300 s (with one already-expired probe inserted after each of polls 1-15)",
                             "command": ('every 15 s on a fixed schedule from the insert reply (time.sleep): db.command({"find": "docs", "filter": {}, '
                                         '"projection": {"_id": 1}, "batchSize": 1000}); after polls 1-15 also db.command({"insert": "docs", '
                                         '"documents": [{"_id": "probe_NN", "exp": <client now - 60 s>}]})'),
                             "startedAt": raw["polls"][0]["sentAt"] if raw["polls"] else None,
                             "endedAt": raw["polls"][-1]["repliedAt"] if raw["polls"] else None,
                             "ok": all(p.get("ok") for p in raw["polls"]), "response": {"polls": "see polls[] (every poll's ids, sent/replied times and probe inserts)"},
                             "reading": "(filled by analyze.py)"})

        # ---- supplementary fine-grained probe: 1 s polling for up to 75 s
        if remaining() > FINE_MAX + 25:
            tp = now()
            expv = trunc_ms(tp - dt.timedelta(seconds=60))
            fdoc = {"_id": "fine_probe", "kind": "fine-grained probe: exp = BSON Date 60 s before its insert", "exp": expv}
            fine = {"_id": "fine_probe", "exp": iso(expv), "eligibleAt": iso(expv + dt.timedelta(seconds=TTL)), "insertSentAt": iso(tp)}
            try:
                fr = db.command({"insert": COLL, "documents": [fdoc]})
                fine.update({"insertRepliedAt": iso(now()), "insertOk": True, "insertReply": tag(fr)})
            except PyMongoError as ex:
                fine.update({"insertRepliedAt": iso(now()), "insertOk": False, "insertError": tag(err_dict(ex))})
            samples = []
            if fine["insertOk"]:
                t_end = time.monotonic() + FINE_MAX
                while time.monotonic() < t_end:
                    sb = now()
                    try:
                        fr = db.command({"find": COLL, "filter": {"_id": "fine_probe"}, "projection": {"_id": 1}, "limit": 1})
                        present = len(fr["cursor"]["firstBatch"]) == 1
                        samples.append({"sentAt": iso(sb), "repliedAt": iso(now()), "present": present})
                        if not present:
                            break
                    except PyMongoError as ex:
                        samples.append({"sentAt": iso(sb), "repliedAt": iso(now()), "error": tag(err_dict(ex))})
                    time.sleep(max(0.0, FINE_EVERY - (now() - sb).total_seconds()))
            fine["samples"] = samples
            raw["fine"] = fine
            raw["steps"].append({"step": "supplement: fine-grained purge timing (1 s polling, up to 75 s)",
                                 "command": ('db.command({"insert": "docs", "documents": [{"_id": "fine_probe", "exp": ISODate("%s")}]}); then every 1 s: '
                                             'db.command({"find": "docs", "filter": {"_id": "fine_probe"}, "projection": {"_id": 1}, "limit": 1}) until it is gone') % iso(expv),
                                 "startedAt": fine["insertSentAt"], "endedAt": samples[-1]["repliedAt"] if samples else fine.get("insertRepliedAt"),
                                 "ok": bool(fine["insertOk"]), "response": {"fine": "see fine{} (insert reply and every 1 s sample)"},
                                 "reading": "(filled by analyze.py)"})
            log(f"fine probe: {len(samples)} samples, last={samples[-1] if samples else None}")
            save_raw()

        run_step("final listing of remaining documents", 'db.command({"find": "docs", "filter": {}, "sort": {"_id": 1}})',
                 lambda: db.command({"find": COLL, "filter": {}, "sort": {"_id": 1}}),
                 lambda r: "Remaining at the end: " + ", ".join(
                     f"{x['_id']} (exp={json.dumps(tag(x['exp'])) if 'exp' in x else '<absent>'})" for x in r["cursor"]["firstBatch"]) + ".")

        def now_probe():
            t0 = time.time()
            rr = db.command({"aggregate": COLL, "pipeline": [{"$limit": 1}, {"$project": {"_id": 0, "now": "$$NOW"}}], "cursor": {}})
            t1 = time.time()
            out = {"reply": rr, "clientSentAt": iso(dt.datetime.fromtimestamp(t0, dt.timezone.utc)),
                   "clientRepliedAt": iso(dt.datetime.fromtimestamp(t1, dt.timezone.utc))}
            fb = rr["cursor"]["firstBatch"]
            if fb and isinstance(fb[0].get("now"), dt.datetime):
                nv = fb[0]["now"]  # db.command() decodes with DEFAULT_CODEC_OPTIONS: naive datetime in UTC
                nv = nv if nv.tzinfo else nv.replace(tzinfo=dt.timezone.utc)
                out["offsetSecondsServerMinusClient"] = round(nv.timestamp() - (t0 + t1) / 2, 3)
                out["uncertaintySeconds"] = round((t1 - t0) / 2, 3)
            return out
        run_step("$$NOW clock check", 'db.command({"aggregate": "docs", "pipeline": [{"$limit": 1}, {"$project": {"_id": 0, "now": "$$NOW"}}], "cursor": {}})',
                 now_probe, lambda r: f"$$NOW minus client clock = {r.get('offsetSecondsServerMinusClient')} s (+/- {r.get('uncertaintySeconds')} s).")
        e, r = run_step("clock offset after polling", 'time.time(); client.admin.command("hello"); time.time()  # hello.localTime vs client midpoint',
                        lambda: clock_probe(client),
                        lambda r: f"Server clock minus client clock = {r.get('offsetSecondsServerMinusClient')} s (+/- {r.get('uncertaintySeconds')} s).")
        if r:
            raw["clock"].append(dict(r, label="after polling"))
    except Exception as ex:
        raw["abort"] = f"{type(ex).__name__}: {ex}"
        log(f"ABORT: {raw['abort']}")
    finally:
        run_step("dropDatabase mt_ttl (cleanup)", 'client["mt_ttl"].command("dropDatabase")', lambda: db.command("dropDatabase"),
                 lambda r: f"mt_ttl dropped: {r}.")
        run_step("verify mt_ttl is gone", 'DB in client.list_database_names()  # only membership of mt_ttl is recorded',
                 lambda: {"mt_ttl_exists": DB in client.list_database_names()},
                 lambda r: "mt_ttl " + ("STILL EXISTS after dropDatabase." if r["mt_ttl_exists"] else "no longer exists."))
        raw["meta"]["scriptEndedAt"] = iso(now())
        save_raw()
        client.close()
    sys.path.insert(0, HERE)
    import analyze
    analyze.main()


if __name__ == "__main__":
    main()
