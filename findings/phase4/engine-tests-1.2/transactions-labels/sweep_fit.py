"""transactions-labels analysis: why the 1.2.0 idle/lifetime outcomes vary between runs.

Run after run.py (read-only; it reads the container log and the reports, and adds an "analysis" section and step 8
to report.json):
  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I \
    /private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests-1.2/transactions-labels/sweep_fit.py

Model tested: (1) PostgreSQL terminates a backend that has been idle in a transaction for 30 s
(idle_in_transaction_session_timeout); (2) the gateway's session manager periodically drops transactions older than
30 s ("Failed to abort expired transaction N" is logged when that abort fails). For each candidate sweep period P
whose grid contains every logged sweep, the model predicts for every statement whether the transaction is still in
the gateway's table (ok, or InternalError if the backend is already dead) or gone (251 "Cannot continue transaction").
"""
import datetime as dt
import json
import math
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = ["report.run1.json", "report.run2.json", "report.run3.json", "report.run4.json", "report.json"]
LIFETIME = 30.0
CANDIDATES = [3, 5, 6, 7.5, 10, 12, 15, 20, 25, 30, 37.5, 50, 60, 75, 100, 150]


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def utc(x):
    return dt.datetime.fromtimestamp(x, dt.timezone.utc).strftime("%H:%M:%S.%f")[:-3]


def log_events():
    out = subprocess.run(["docker", "logs", "--timestamps", "ddb-engine-test"], capture_output=True, text=True, timeout=60)
    sweeps, kills = [], []
    for ln in (out.stdout + out.stderr).splitlines():
        if "GATEWAY-FILE" in ln:
            continue
        m = re.match(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?)Z?\s", ln)
        if not m:
            continue
        if "expired transaction" in ln:
            sweeps.append(ts(m.group(1)[:26] + "+00:00"))
        elif "idle-in-transaction timeout" in ln:
            # use PostgreSQL's own timestamp ("[POSTGRES] 2026-11-25 21:00:43.631 UTC")
            p = re.search(r"\[POSTGRES\] (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+) UTC", ln)
            kills.append(ts(p.group(1).replace(" ", "T") + "+00:00") if p else ts(m.group(1)[:26] + "+00:00"))
    return sweeps, kills


def transactions(report, run):
    t0 = ts(report["started_utc"])
    evs = {}
    for st in report["steps"]:
        if st["step"][:2] not in ("4a", "4b", "4c", "4d", "4e", "4f", "4g"):
            continue
        for e in st.get("wire") or []:
            evs[e["seq"]] = (st["step"][:2], e)
        r = st.get("response") or {}
        w = r.get("wire") if isinstance(r, dict) else None
        for e in (w.values() if isinstance(w, dict) else [w] if isinstance(w, list) else []):
            for x in e:
                evs[x["seq"]] = (st["step"][:2], x)
    pending, out = {}, {}
    for seq in sorted(evs):
        sid, ev = evs[seq]
        if ev["event"] == "started":
            c = ev["command"]
            if "txnNumber" not in c:
                continue
            key = (json.dumps(c.get("lsid"), sort_keys=True), c["txnNumber"])
            pending[ev["request_id"]] = (key, sid, ev["command_name"], t0 + ev["t_s"])
        elif ev["request_id"] in pending:
            key, sid, name, t = pending.pop(ev["request_id"])
            rep = ev.get("reply") or ev.get("failure") or {}
            ok = rep.get("ok") in (1, 1.0) and "code" not in rep
            d = out.setdefault(key, {"run": run, "step": sid, "start": t, "stmts": []})
            d["stmts"].append({"t": t, "cmd": name, "ok": ok, "code": rep.get("code"),
                               "msg": re.sub(r"\[ActivityId=[^\]]*\]\s*", "", rep.get("errmsg", "") or "")})
    return list(out.values())


def first_sweep_after(x, anchor, P):
    return anchor + (math.floor((x - anchor) / P) + 1) * P


def classify(s):
    if s["ok"]:
        return "ok"
    if s["code"] == 251 and "Cannot continue" in s["msg"]:
        return "gone(251 Cannot continue)"
    if s["code"] == 251 and "backend session ended" in s["msg"]:
        return "aborted(251 backend session ended)"
    if s["code"] == 1:
        return "dead-backend(1 InternalError)"
    return f"other({s['code']})"


def check(P, anchor, txs, whole_seconds=False):
    """whole_seconds=True models a gateway that stores the transaction start time at one-second resolution."""
    mism = []
    for tx in txs:
        start = math.floor(tx["start"]) if whole_seconds else tx["start"]
        sweep = first_sweep_after(start + LIFETIME, anchor, P)
        for s in tx["stmts"][1:]:
            if s["cmd"] not in ("update", "commitTransaction"):
                continue
            c = classify(s)
            pred_gone = s["t"] > sweep
            obs_gone = c.startswith("gone")
            if c in ("ok", "dead-backend(1 InternalError)") or obs_gone:
                if pred_gone != obs_gone:
                    mism.append({"run": tx["run"], "step": tx["step"], "age_s": round(s["t"] - tx["start"], 2),
                                 "cmd": s["cmd"], "observed": c, "predicted": "gone" if pred_gone else "present"})
            if not s["ok"]:
                break
    return mism


def main():
    sweeps, kills = log_events()
    txs = []
    for i, name in enumerate(RUNS, 1):
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            with open(p) as f:
                txs += transactions(json.load(f), f"run{i}")
    anchor = sweeps[-1]
    fits = {}
    for P in CANDIDATES:
        on_grid = all(abs((x - anchor) / P - round((x - anchor) / P)) * P < 0.05 for x in sweeps)
        fits[str(P)] = {"logged_sweeps_on_grid": on_grid,
                        "mismatches": check(P, anchor, txs) if on_grid else "not on grid",
                        "mismatches_whole_second_start": check(P, anchor, txs, True) if on_grid else "not on grid"}
    fitting = [P for P in CANDIDATES if fits[str(P)]["logged_sweeps_on_grid"] and fits[str(P)]["mismatches"] == []]
    fitting_ws = [P for P in CANDIDATES if fits[str(P)]["logged_sweeps_on_grid"]
                  and fits[str(P)]["mismatches_whole_second_start"] == []]
    # PostgreSQL idle kills matched to the last statement before a >30 s gap
    kill_deltas = []
    for tx in txs:
        st = tx["stmts"]
        for a, b in zip(st, st[1:]):
            if b["t"] - a["t"] > LIFETIME:
                near = sorted((k for k in kills if abs(k - (a["t"] + LIFETIME)) < 2.0),
                              key=lambda k: abs(k - (a["t"] + LIFETIME)))
                kill_deltas.append({"run": tx["run"], "step": tx["step"],
                                    "kill_minus_last_statement_s": round(near[0] - a["t"], 3) if near else None})
    # idle outcomes across runs (first statement after the idle gap, then the commit)
    idle = {}
    busy = []
    for tx in txs:
        st = tx["stmts"]
        gaps = [b["t"] - a["t"] for a, b in zip(st, st[1:])]
        if gaps and max(gaps) > LIFETIME:
            i = gaps.index(max(gaps)) + 1
            after = classify(st[i])
            commit = next((classify(x) for x in st[i + 1:] if x["cmd"] == "commitTransaction"), "not sent")
            k = f"write: {after}; commit: {commit}"
            idle.setdefault(k, []).append(f"{tx['run']}:{tx['step']}")
        elif tx["step"] in ("4e", "4g"):
            oks = [round(x["t"] - tx["start"], 2) for x in st if x["ok"] and x["cmd"] == "update"]
            bad = next((x for x in st if not x["ok"]), None)
            com = next((x for x in st if x["cmd"] == "commitTransaction"), None)
            busy.append({"run": tx["run"], "step": tx["step"], "last_ok_write_age_s": max(oks) if oks else None,
                         "first_failure": ({"age_s": round(bad["t"] - tx["start"], 2), "result": classify(bad)}
                                           if bad else None),
                         "commit": ({"age_s": round(com["t"] - tx["start"], 2), "result": classify(com)} if com else None)})
    res = {
        "inputs": RUNS,
        "model": "PostgreSQL kills a backend idle in a transaction for 30 s; the gateway drops transactions older than "
                 "30 s at a periodic sweep of period P",
        "logged_sweeps_utc": [utc(x) for x in sweeps],
        "transactions_checked": len(txs),
        "candidate_periods": fits,
        "periods_with_zero_mismatches": fitting,
        "periods_with_zero_mismatches_whole_second_start": fitting_ws,
        "postgres_idle_kill_minus_last_statement_s": kill_deltas,
        "idle_outcomes_across_runs": {k: {"count": len(v), "samples": v} for k, v in idle.items()},
        "busy_transaction_outcomes_across_runs": busy,
        "baseline_0_117_idle_samples": "2 of 2 (driver and raw): write InternalError (code 1), commit InternalError "
                                       "(code 1), abort 251; the 0.117 log filter did not match the session_manager "
                                       "line, so whether 0.117 had the same sweep is unknown",
    }
    return res


if __name__ == "__main__":
    res = main()
    with open(os.path.join(HERE, "sweep_fit.json"), "w") as f:
        json.dump(res, f, indent=1)
    kd = [d["kill_minus_last_statement_s"] for d in res["postgres_idle_kill_minus_last_statement_s"]]
    ia = res["idle_outcomes_across_runs"]
    busy = res["busy_transaction_outcomes_across_runs"]
    cp = res["candidate_periods"]
    on_grid = [p for p, v in cp.items() if v["logged_sweeps_on_grid"]]
    m15 = cp["15"]["mismatches"]
    m15w = cp["15"]["mismatches_whole_second_start"]
    kd_ok = [x for x in kd if x is not None]
    n_idle = sum(v["count"] for v in ia.values())
    reading = (f"Inferred, not observed directly: all {len(res['logged_sweeps_utc'])} logged 'Failed to abort expired "
               f"transaction' lines lie on a 15 s grid (other on-grid periods {[p for p in on_grid if p != '15']} s "
               f"mispredict {[len(cp[p]['mismatches']) for p in on_grid if p != '15']} outcomes), and a model in which that "
               f"15 s sweep drops transactions about 30 s old while PostgreSQL kills a backend "
               f"{min(kd_ok) if kd_ok else None}-{max(kd_ok) if kd_ok else None} s after an idle transaction's last statement "
               f"predicts {res['transactions_checked'] - len(m15)} of {res['transactions_checked']} transactions with "
               f"exact start times and {res['transactions_checked'] - len(m15w)} of {res['transactions_checked']} with "
               f"whole-second start times, which explains why busy transactions ended 30-45 s after they began and why "
               f"the first statement after 36 s idle returned 251 in "
               f"{sum(v['count'] for k, v in ia.items() if k.startswith('write: gone'))} of {n_idle} samples and "
               f"InternalError in the rest.")
    path = os.path.join(HERE, "report.json")
    with open(path) as f:
        rep = json.load(f)
    rep["steps"] = [s for s in rep["steps"] if not s["step"].startswith("8 ")]
    rep["steps"].append({
        "step": "8 analysis: fit of the gateway's expired-transaction sweep to all idle and busy transactions (runs 1-5)",
        "command": "/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I " + os.path.abspath(__file__)
                   + "   (reads report.run1-4.json, report.json and docker logs --timestamps ddb-engine-test)",
        "response": {"periods_with_zero_mismatches": res["periods_with_zero_mismatches"],
                     "periods_with_zero_mismatches_whole_second_start": res["periods_with_zero_mismatches_whole_second_start"],
                     "candidate_periods_mismatch_counts": {p: (len(v["mismatches"]) if isinstance(v["mismatches"], list)
                                                               else v["mismatches"])
                                                           for p, v in res["candidate_periods"].items()},
                     "p15_mismatches_exact_start": res["candidate_periods"]["15"]["mismatches"],
                     "p15_mismatches_whole_second_start": res["candidate_periods"]["15"]["mismatches_whole_second_start"],
                     "logged_sweeps_utc": res["logged_sweeps_utc"],
                     "postgres_idle_kill_minus_last_statement_s": kd,
                     "idle_outcomes_across_runs": {k: v["count"] for k, v in ia.items()},
                     "busy_transaction_outcomes_across_runs": busy,
                     "full_output": os.path.join(HERE, "sweep_fit.json")},
        "reading": reading})
    rep["analysis"] = res
    rep.setdefault("summary", {})["idle_and_lifetime_mechanism_inferred"] = [reading]
    rep["rerun"] = (f"/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I {os.path.join(HERE, 'run.py')}"
                    f" ; then /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I {os.path.abspath(__file__)}")
    with open(path, "w") as f:
        json.dump(rep, f, indent=2)
        f.write("\n")
    print(json.dumps(rep["steps"][-1], indent=1)[:4000])
