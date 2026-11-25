#!/usr/bin/env python3
"""transactions-labels-rerun: verification of the tester's report against this rerun (read-only).

Reads the tester's five reports (report.run1-4.json and report.json in ../transactions-labels), this folder's
report.json (run.py rerun on t_txn_rerun) and extra_probes.json, re-runs the tester's static binary checks plus a
few more (read-only docker exec grep), tests the tester's sweep model out of sample on this rerun with its
parameters fixed (period 15 s, 30 s age threshold, anchor = last logged sweep), and appends steps 8-11 to this
folder's report.json. Touches no database.

Rerun (after run.py and extra_probes.py):
  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I \
    /private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests-1.2/transactions-labels-rerun/verify.py
"""
import datetime as dt
import json
import math
import os
import re
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTER = os.path.join(os.path.dirname(HERE), "transactions-labels")
sys.path.insert(0, HERE)
import sweep_fit as SF  # noqa: E402  (unmodified copy of the tester's analysis module; only its functions are used)

CONTAINER = "ddb-engine-test"
GW = "/home/documentdb/gateway/pg_documentdb_gw/target/release-with-symbols/documentdb_gateway"
RUN_FILES = [("tester run1", os.path.join(TESTER, "report.run1.json")),
             ("tester run2", os.path.join(TESTER, "report.run2.json")),
             ("tester run3", os.path.join(TESTER, "report.run3.json")),
             ("tester run4", os.path.join(TESTER, "report.run4.json")),
             ("tester run5", os.path.join(TESTER, "report.json")),
             ("rerun", os.path.join(HERE, "report.json"))]


def load(p):
    with open(p) as f:
        return json.load(f)


RUNS = [(n, load(p)) for n, p in RUN_FILES]
MINE = RUNS[-1][1]
T5 = RUNS[-2][1]


def step(rep, sid):
    for s in rep.get("steps", []):
        if s["step"].split(" ", 1)[0] == sid:
            return s
    return None


def resp(rep, sid):
    s = step(rep, sid)
    return s.get("response") if s else None


def norm(msg):
    if not isinstance(msg, str):
        return msg
    msg = re.sub(r"\[ActivityId=[0-9a-fA-F-]+\]\s*", "[ActivityId=<id>] ", msg)
    return re.sub(r"([Tt]ransaction) \d+", r"\1 <n>", msg)


def sig(x):
    """ok/code/codeName/normalised errmsg/errorLabels of a server reply, an err() dict or a client-side error."""
    if x is None or not isinstance(x, dict):
        return x
    if isinstance(x.get("server_reply"), dict):
        x = x["server_reply"]
    elif "exception" in x:
        return {"client_side": x["exception"], "message": x.get("message")}
    out = {"ok": float(x["ok"]) if isinstance(x.get("ok"), (int, float)) else x.get("ok")}
    for k in ("code", "codeName"):
        if k in x:
            out[k] = x[k]
    if "errmsg" in x:
        out["errmsg"] = norm(x["errmsg"])
    out["errorLabels"] = x.get("errorLabels", "absent")
    return out


def g(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


# ----------------------------------------------------------------------------- per-step signatures
def signature(rep, sid):
    r = resp(rep, sid)
    if r is None:
        return None
    if sid == "0a":
        return {k: r.get(k) for k in ("version", "versionArray", "maxBsonObjectSize", "ok")}
    if sid == "0b":
        return {k: r.get(k) for k in ("msg", "maxWireVersion", "minWireVersion", "logicalSessionTimeoutMinutes",
                                      "maxWriteBatchSize", "saslSupportedMechs", "internal")}
    if sid == "0c":
        return r
    if sid == "0d":
        return {k: r.get(k) for k in ("image_ref", "image_id", "started_at", "restart_count", "status", "oci_version",
                                      "oci_revision")}
    if sid == "0e":
        return r.get("decoded")
    if sid == "0f":
        return {"dynamic_configuration": r.get("dynamic_configuration"),
                "occurrences_in_gateway_binary": r.get("occurrences_in_gateway_binary")}
    if sid in ("0g", "1a", "1f", "5"):
        return r
    if sid == "1c":
        return r.get("result")
    if sid == "1b":
        return {"still_running_after_3s": r.get("still_running_after_3s"),
                "error": sig(g(r, "outcome_before_A_commits", "error"))}
    if sid == "1d":
        return {"error": sig(r.get("error")), "labels_seen_by_driver": g(r, "error", "labels_seen_by_driver")}
    if sid == "1e":
        return sig(r)
    if sid == "1g":
        return {"reply": sig(r.get("reply")), "returned_before_A_commit": r.get("returned_before_A_commit"),
                "A_commit": r.get("A_commit")}
    if sid == "1h":
        return {"abort": sig(r.get("abortTransaction")), "commit": sig(r.get("commitTransaction_after_abort"))}
    if sid == "1i":
        return {"callback_invocations": r.get("callback_invocations"),
                "raised": sig(g(r, "with_transaction_outcome", "raised")),
                "A_commit": g(r, "A_commit_by_timer", "result"), "document_after": r.get("document_after")}
    if sid == "1j":
        errs = sorted({json.dumps(sig(a.get("error"))) for a in r.get("attempts", []) if a.get("error")})
        last = (r.get("attempts") or [{}])[-1]
        return {"outcome": sorted((r.get("with_transaction_outcome") or {}).keys()),
                "attempt_error_kinds": [json.loads(e) for e in errs], "last_attempt_result": last.get("result"),
                "document_after": r.get("document_after")}
    if sid == "1k":
        return {k: (sig(v) if isinstance(v, dict) and ("server_reply" in v or "exception" in v) else v)
                for k, v in r.items()}
    if sid in ("2a", "2b", "2c"):
        if "error" in r:
            return {"rejected": sig(r["error"])}
        return {"accepted": True, "find": r.get("find"), "commit": r.get("commit")}
    if sid == "3a":
        return {"commit_1": r.get("commit_1"), "commit_2": r.get("commit_2"),
                "abort_after_commit": sig(r.get("abort_after_commit")),
                "commitTransaction_commands_sent": r.get("commitTransaction_commands_sent"),
                "second_commit_writeConcern_on_wire": r.get("second_commit_writeConcern_on_wire"),
                "document_after": r.get("document_after")}
    if sid in ("3b", "3c"):
        return {k: (sig(v) if k != "document_after" else v) for k, v in r.items()}
    if sid == "4a":
        return {"first_write": r.get("first_write"), "write_after_idle": sig(r.get("write_after_idle"))}
    if sid in ("4b", "4c"):
        return sig(r)
    if sid == "4d":
        return {k: sig(r.get(k)) for k in ("first_update", "update_after_idle", "commit", "abort")}
    if sid == "4e":
        ws = r.get("writes", [])
        bad = next((w for w in ws if "error" in w), None)
        return {"failed_write": (bad or {}).get("write"), "failed_at_s": (bad or {}).get("t_since_first_write_s"),
                "failure": sig((bad or {}).get("error")), "commit": sig(r.get("commit"))}
    if sid == "4f":
        return [{"write_after_idle": sig(o.get("write_after_idle")), "commit": sig(o.get("commit"))}
                for o in r.get("runs", [])]
    if sid == "4g":
        ws = r.get("writes", [])
        oks = [w["age_s"] for w in ws if w.get("ok")]
        bad = next((w for w in ws if "error" in w), None)
        return {"last_ok_age_s": max(oks) if oks else None, "failure_age_s": (bad or {}).get("age_s"),
                "failure": sig((bad or {}).get("error")), "commit": sig(r.get("commit"))}
    if sid == "6":
        return r.get("pattern_counts")
    if sid == "7":
        return r
    return r


TIMING = {"4a", "4b", "4d", "4e", "4f", "4g", "6"}   # outcomes the tester reports as timing-dependent
IDS = ["0a", "0b", "0c", "0d", "0e", "0f", "0g", "1a", "1b", "1c", "1d", "1e", "1f", "1g", "1h", "1i", "1j", "1k",
       "2a", "2b", "2c", "3a", "3b", "3c", "4a", "4b", "4c", "4d", "4e", "4f", "4g", "5", "6", "7"]


def compare_steps():
    rows = []
    for sid in IDS:
        a, b = signature(T5, sid), signature(MINE, sid)
        same = a == b
        seen_any = any(signature(rep, sid) == b for _, rep in RUNS[:-1])
        if same:
            verdict = "same as tester run5"
        elif seen_any:
            verdict = "differs from run5 but equals an earlier tester run"
        elif sid in TIMING:
            verdict = "differs (timing-dependent step)"
        else:
            verdict = "DIFFERS"
        rows.append({"step": sid, "tester_run5": a, "rerun": b, "verdict": verdict})
    return rows


# ----------------------------------------------------------------------------- cross-run aggregates
def all_wire(rep):
    """Wire events of the run.py steps only (steps appended by this script, e.g. 8a-8e, are excluded)."""
    evs = {}
    for s in rep.get("steps", []):
        if s["step"].split(" ", 1)[0] not in IDS:
            continue
        for e in s.get("wire") or []:
            evs[e["seq"]] = e
        w = (s.get("response") or {}).get("wire") if isinstance(s.get("response"), dict) else None
        if isinstance(w, dict):
            for lst in w.values():
                for e in lst:
                    evs[e["seq"]] = e
        elif isinstance(w, list):
            for e in w:
                evs[e["seq"]] = e
    return [evs[k] for k in sorted(evs)]


def wire_errors(rep):
    out = []
    for e in all_wire(rep):
        doc = e.get("failure") if e["event"] == "failed" else e.get("reply") if e["event"] == "succeeded" else None
        if isinstance(doc, dict) and doc.get("ok") in (0, 0.0) and "code" in doc:
            out.append({"code": doc.get("code"), "codeName": doc.get("codeName"), "labels": "errorLabels" in doc,
                        "command": e["command_name"], "duration_ms": e.get("duration_ms"), "event": e["event"]})
    return out


def any_labels(rep):
    n = 0
    for e in all_wire(rep):
        doc = e.get("failure") or e.get("reply")
        if isinstance(doc, dict) and "errorLabels" in doc:
            n += 1
    return n


def aggregates():
    agg = {"per_run": {}, "wire_error_replies": {}}
    tot5, tot6 = {}, {}
    lock_ms = []
    for name, rep in RUNS:
        r1b, r1g, r1i, r1j, r1k = (resp(rep, x) for x in ("1b", "1g", "1i", "1j", "1k"))
        errs = wire_errors(rep)
        counts = {}
        for e in errs:
            counts[e["code"]] = counts.get(e["code"], 0) + 1
            tot6[e["code"]] = tot6.get(e["code"], 0) + 1
            if name != "rerun":
                tot5[e["code"]] = tot5.get(e["code"], 0) + 1
            if e["code"] == 112 and e["command"] in ("update", "insert") and e["duration_ms"] is not None:
                lock_ms.append(e["duration_ms"])
        agg["per_run"][name] = {
            "1b_elapsed_s": g(r1b, "outcome_before_A_commits", "elapsed_s"),
            "1g_elapsed_s": g(r1g, "elapsed_s"),
            "1i": {"invocations": g(r1i, "callback_invocations"), "elapsed_s": g(r1i, "with_transaction_elapsed_s")},
            "1j": {"invocations": g(r1j, "callback_invocations"), "elapsed_s": g(r1j, "with_transaction_elapsed_s"),
                   "outcome": sorted((g(r1j, "with_transaction_outcome") or {}).keys())},
            "1k": ({"B_second_read_v": g(r1k, "B_second_read_after_A_commit", "v"), "final_v": g(r1k, "document_after", "v"),
                    "B_commit": g(r1k, "B_commit")} if r1k else "step absent"),
            "wire_error_replies_by_code": counts,
            "wire_error_replies_total": len(errs),
            "wire_error_replies_with_errorLabels": sum(e["labels"] for e in errs),
            "any_wire_document_with_errorLabels": any_labels(rep),
        }
    agg["wire_error_replies"] = {
        "tester_runs_1_5": {"total": sum(tot5.values()), "by_code": tot5},
        "all_six_runs": {"total": sum(tot6.values()), "by_code": tot6},
    }
    agg["lock_wait_ms_of_112_updates_all_runs"] = {
        "n": len(lock_ms), "min": min(lock_ms), "median": statistics.median(lock_ms), "max": max(lock_ms)}
    return agg


# ----------------------------------------------------------------------------- sweep model, out of sample
def sweep_out_of_sample():
    sweeps, kills = SF.log_events()
    anchor = sweeps[-1]
    offsets = [round(((x - anchor) % 15.0 + 7.5) % 15.0 - 7.5, 3) for x in sweeps]
    mine = SF.transactions(MINE, "rerun")
    t0 = SF.ts(MINE["started_utc"])
    res = {"logged_sweeps_utc": [SF.utc(x) for x in sweeps],
           "sweep_offset_from_15s_grid_of_last_sweep_s": offsets,
           "anchor_utc": SF.utc(anchor), "rerun_started_utc": MINE["started_utc"],
           "transactions_checked": len(mine), "periods": {}}
    for P in SF.CANDIDATES:
        on_grid = all(abs((x - anchor) / P - round((x - anchor) / P)) * P < 0.05 for x in sweeps)
        if not on_grid:
            continue
        res["periods"][str(P)] = {"mismatches_exact_start": SF.check(P, anchor, mine),
                                  "mismatches_whole_second_start": SF.check(P, anchor, mine, True)}
    # per-transaction view for P = 15 (prediction vs observation)
    view = []
    for tx in mine:
        for ws in (False, True):
            start = math.floor(tx["start"]) if ws else tx["start"]
            sweep = SF.first_sweep_after(start + SF.LIFETIME, anchor, 15)
            if not ws:
                rec = {"step": tx["step"], "start_utc": SF.utc(tx["start"]),
                       "predicted_drop_utc_exact": SF.utc(sweep),
                       "predicted_drop_age_s_exact": round(sweep - tx["start"], 2)}
            else:
                rec["predicted_drop_utc_whole_second"] = SF.utc(sweep)
                rec["predicted_drop_age_s_whole_second"] = round(sweep - tx["start"], 2)
        rec["statements"] = [{"cmd": s["cmd"], "age_s": round(s["t"] - tx["start"], 2), "observed": SF.classify(s)}
                             for s in tx["stmts"]]
        view.append(rec)
    res["p15_per_transaction"] = view
    kd = []
    for tx in mine:
        st = tx["stmts"]
        for a, b in zip(st, st[1:]):
            if b["t"] - a["t"] > SF.LIFETIME:
                near = sorted((k for k in kills if abs(k - (a["t"] + SF.LIFETIME)) < 2.0),
                              key=lambda k: abs(k - (a["t"] + SF.LIFETIME)))
                kd.append({"step": tx["step"], "kill_minus_last_statement_s": round(near[0] - a["t"], 3) if near else None})
    res["postgres_idle_kill_minus_last_statement_s"] = kd
    res["rerun_window_sweep_lines"] = [SF.utc(x) for x in sweeps if x >= t0 - 1]
    return res


def outcomes_idle_busy():
    idle, busy = {}, []
    for name, rep in RUNS:
        for tx in SF.transactions(rep, name):
            st = tx["stmts"]
            gaps = [b["t"] - a["t"] for a, b in zip(st, st[1:])]
            if gaps and max(gaps) > SF.LIFETIME:
                i = gaps.index(max(gaps)) + 1
                commit = next((SF.classify(x) for x in st[i + 1:] if x["cmd"] == "commitTransaction"), "not sent")
                k = f"write: {SF.classify(st[i])}; commit: {commit}"
                idle.setdefault(k, []).append(f"{name}:{tx['step']}")
            elif tx["step"] in ("4e", "4g"):
                oks = [round(x["t"] - tx["start"], 2) for x in st if x["ok"] and x["cmd"] == "update"]
                bad = next((x for x in st if not x["ok"]), None)
                com = next((x for x in st if x["cmd"] == "commitTransaction"), None)
                busy.append({"run": name, "step": tx["step"], "last_ok_write_age_s": max(oks) if oks else None,
                             "first_failure_age_s": round(bad["t"] - tx["start"], 2) if bad else None,
                             "first_failure": SF.classify(bad) if bad else None,
                             "commit": SF.classify(com) if com else None})
    return {"idle": {k: {"count": len(v), "samples": v} for k, v in idle.items()}, "busy": busy}


# ----------------------------------------------------------------------------- static, read-only container checks
def sh(cmd):
    p = subprocess.run(["docker", "exec", CONTAINER, "sh", "-c", cmd], capture_output=True, text=True, timeout=120)
    return p.stdout


def static_checks():
    cmds, out = [], {}
    libs = sh("ls /usr/lib/postgresql/*/lib/pg_documentdb*.so").split()
    strings = ["TransientTransactionError", "UnknownTransactionCommitResult", "RetryableWriteError", "errorLabels",
               "Could not acquire lock within transaction"]
    counts = {}
    for f in [GW] + libs:
        loop = "; ".join(f"printf '%s\\t' '{s}'; grep -a -o -F '{s}' '{f}' | wc -l" for s in strings)
        cmds.append(f"docker exec {CONTAINER} sh -c \"grep -a -o -F '<string>' {f} | wc -l\"  for each of {strings}")
        c = {}
        for ln in sh(loop).splitlines():
            if "\t" in ln:
                k, v = ln.split("\t", 1)
                c[k] = int(v.strip())
        counts[f] = c
    out["string_counts"] = counts
    pats = {"lock_timeout_sql": r"SET LOCAL lock_timeout=.[0-9a-z]+.",
            "isolation_sql": r"START TRANSACTION ISOLATION LEVEL (READ COMMITTED|REPEATABLE READ)?",
            "isolation_level_literals": r"READ COMMITTED|REPEATABLE READ|SERIALIZABLE",
            "timeout_connection_options": r"(statement_timeout|idle_in_transaction_session_timeout)=\{[a-z_]+\}",
            "sweep_message": r"Failed to abort expired transaction",
            "backend_ended_message": r"The transaction has been aborted because its backend session ended\."}
    found = {}
    for k, p in pats.items():
        cmd = f"grep -a -o -E '{p}' {GW} | tr -c '[:print:]\\n' '.' | sort -u | head -5"
        cmds.append(f"docker exec {CONTAINER} sh -c \"{cmd}\"")
        found[k] = [x for x in sh(cmd).splitlines() if x]
    out["gateway_strings"] = found
    return cmds, out


# ----------------------------------------------------------------------------- main
def main():
    rows = compare_steps()
    agg = aggregates()
    oib = outcomes_idle_busy()
    sw = sweep_out_of_sample()
    scmds, stat = static_checks()
    probes = load(os.path.join(HERE, "extra_probes.json"))
    full = {"step_comparison": rows, "aggregates": agg, "idle_and_busy_outcomes_all_runs": oib,
            "sweep_model_out_of_sample": sw, "static_checks": stat, "static_commands": scmds}
    with open(os.path.join(HERE, "verify.json"), "w") as f:
        json.dump(full, f, indent=1, default=str)

    rep = MINE
    rep["steps"] = [s for s in rep["steps"] if s["step"].split(" ", 1)[0] not in ("8a", "8b", "8c", "8d", "8e", "8f", "9",
                                                                                   "10", "11", "12")]
    py = "/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I"
    # 8: added probes
    for sid, (name, p) in zip(("8a", "8b", "8c", "8d", "8e", "8f"), probes["probes"].items()):
        rep["steps"].append({"step": f"{sid} added probe (rerun agent): {name}",
                             "command": {"script": f"{py} {os.path.join(HERE, 'extra_probes.py')}",
                                         "calls": p["command"]},
                             "response": p["response"], "reading": p["reading"], "wire": p["wire"]})
    # 9: static checks
    gw = stat["string_counts"][GW]
    libs_zero = all(all(v == 0 for v in c.values()) for f, c in stat["string_counts"].items() if f != GW)
    rep["steps"].append({
        "step": "9 static, read-only: label and conflict strings in the gateway and engine libraries, transaction SQL in the gateway",
        "command": scmds, "response": stat,
        "reading": (f"The field name 'errorLabels', the three label strings and the #339 message 'Could not acquire lock "
                    f"within transaction' occur {sum(gw.values())} times in the gateway binary and "
                    f"{'0 times in every' if libs_zero else 'in some'} pg_documentdb*.so library, and the gateway binary "
                    f"holds the literals {stat['gateway_strings'].get('lock_timeout_sql')}, "
                    f"{stat['gateway_strings'].get('isolation_sql')} and "
                    f"{stat['gateway_strings'].get('timeout_connection_options')}, which fits the observed 21-34 ms "
                    f"conflict errors, the read-committed visibility in 1k and the PostgreSQL idle kill at 30 s "
                    f"(string-level evidence, not source-confirmed).")})
    # 10: step comparison
    diff = [r for r in rows if r["verdict"] != "same as tester run5"]
    rep["steps"].append({
        "step": "10 comparison of this rerun with the tester's run 5 (and runs 1-4), step by step",
        "command": f"{py} {os.path.abspath(__file__)}   (signatures: ok, code, codeName, errmsg with ActivityId and "
                   f"transaction numbers normalised, errorLabels; documents; counts)",
        "response": {"rows": rows, "aggregates": agg, "idle_and_busy_outcomes_all_runs": oib},
        "reading": (f"{len(rows) - len(diff)} of {len(rows)} steps give the same signature as the tester's run 5; "
                    f"{', '.join(r['step'] for r in diff if r['verdict'].startswith('differs from run5')) or 'none'} "
                    f"differ from run 5 but equal one of the tester's runs 1-4 (timing-dependent idle and lifetime "
                    f"outcomes), "
                    f"{', '.join(r['step'] for r in diff if r['verdict'].startswith('differs (timing')) or 'none'} "
                    f"differ only in timing-dependent values or log-line counts, and "
                    f"{', '.join(r['step'] for r in diff if r['verdict'] == 'DIFFERS') or 'none'} differ otherwise.")})
    # 11: sweep model out of sample
    p15 = sw["periods"].get("15", {})
    me, mw = p15.get("mismatches_exact_start"), p15.get("mismatches_whole_second_start")
    rep["steps"].append({
        "step": "11 out-of-sample test of the tester's sweep model on this rerun (period 15 s, 30 s age, anchor = last logged sweep)",
        "command": f"{py} {os.path.abspath(__file__)}   (uses check()/transactions()/log_events() from the unmodified "
                   f"copy of sweep_fit.py; reads docker logs --timestamps {CONTAINER})",
        "response": sw,
        "reading": (f"With its parameters fixed, the model mispredicts {len(me) if isinstance(me, list) else me} of the "
                    f"rerun's {sw['transactions_checked']} transactions with exact start times and "
                    f"{len(mw) if isinstance(mw, list) else mw} with whole-second start times, and the rerun logged "
                    f"{len(sw['rerun_window_sweep_lines'])} sweep lines, as the model expects when every idle transaction "
                    f"hits the dead backend before a sweep removes it.")})
    with open(os.path.join(HERE, "report.json"), "w") as f:
        json.dump(rep, f, indent=2, default=str)
        f.write("\n")
    for s in rep["steps"][-8:]:
        print("\n##", s["step"], "\n  ", s["reading"])


if __name__ == "__main__":
    main()
