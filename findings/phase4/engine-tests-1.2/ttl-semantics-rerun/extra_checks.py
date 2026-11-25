#!/usr/bin/env python
"""ttl-semantics rerun: read-only checks of claims in the tester's conclusions that no tester step recorded
(roles, pg_cron owners, process user) and of the index-build pg_cron runs inside each successful
createIndexes window of the tester's runs, this rerun and supplementary_probe.py.

All commands are SELECTs or process listings inside the container; nothing is written and no database
is touched. Writes extra_checks.json next to this script. Rerun with the .venv python after
run_ttl_test.py (it reads both reports to find the createIndexes(exp2_ttl) windows).
"""
import datetime as dt
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
TESTER = os.path.join(os.path.dirname(HERE), "ttl-semantics")
CONTAINER = "ddb-engine-test"
STEPS = []


def iso(d):
    return d.astimezone(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def run(argv):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    return {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def rows(stdout):
    return [ln.split("|") for ln in (stdout or "").splitlines() if ln.strip() and ln.strip() != "SET"]


def psql_argv(sql):
    return ["docker", "exec", CONTAINER, "psql", "-U", "documentdb", "-p", "9712", "-d", "postgres", "-tAc", sql]


def step(name, argv, reading_fn, command_text=None):
    started = dt.datetime.now(dt.timezone.utc)
    resp = run(argv)
    rr = rows(resp["stdout"])
    resp["parsedRows"] = rr
    try:
        reading = reading_fn(rr, resp)
    except Exception as e:  # noqa: BLE001
        reading = f"Output could not be parsed ({type(e).__name__}: {e}); raw output kept."
    STEPS.append({"n": len(STEPS) + 1, "step": name, "command": command_text or " ".join(argv[:10]) + " " + json.dumps(argv[-1]),
                  "at": iso(started), "ok": resp["returncode"] == 0, "response": resp, "reading": reading})


def main():
    step("PostgreSQL superuser roles and whether a role named postgres exists",
         psql_argv("select rolname, rolsuper, (select count(*) from pg_roles where rolname = 'postgres') "
                   "from pg_roles where rolsuper order by rolname"),
         lambda r, resp: (f"Superuser role(s): {', '.join(x[0] for x in r)}; roles named postgres: "
                          f"{r[0][2] if r else '?'}."))
    step("owner (username) of each pg_cron job",
         psql_argv("select jobid, jobname, username, database, active from cron.job order by jobid"),
         lambda r, resp: "pg_cron jobs and owners: " + "; ".join(f"{x[1]} owned by {x[2]} in database {x[3]} (active {x[4]})" for x in r) + ".")
    step("OS user of the postmaster process",
         ["docker", "exec", CONTAINER, "sh", "-c", "ps -eo user:20,pid,args | grep -E '[p]ostgres -D'"],
         lambda r, resp: f"Postmaster process line: {resp['stdout'].strip()}.",
         command_text="docker exec ddb-engine-test sh -c \"ps -eo user:20,pid,args | grep -E '[p]ostgres -D'\"")
    step("default user of docker exec in the container",
         ["docker", "exec", CONTAINER, "id"],
         lambda r, resp: f"docker exec runs as: {resp['stdout'].strip()}.")

    windows = []
    for label, path in (("tester run 1", os.path.join(TESTER, "report.run1.json")),
                        ("tester run 2", os.path.join(TESTER, "report.json")),
                        ("this rerun", os.path.join(HERE, "report.json"))):
        try:
            rep = json.load(open(path))
        except Exception:  # noqa: BLE001
            continue
        for s in rep.get("steps", []):
            if s["step"].startswith("create second TTL index on exp2"):
                a = dt.datetime.fromisoformat(s["at"].replace("Z", "+00:00"))
                windows.append((label, a, a + dt.timedelta(milliseconds=s["elapsedMs"])))
    try:
        sup = json.load(open(os.path.join(HERE, "supplementary.json")))
        for s in sup.get("steps", []):
            if s["ok"] and 'db.command("createIndexes"' in s["command"]:
                a = dt.datetime.fromisoformat(s["at"].replace("Z", "+00:00"))
                windows.append((f"supplementary probe, {s['step']}", a, a + dt.timedelta(milliseconds=s["elapsedMs"])))
    except FileNotFoundError:
        pass
    for label, a, b in windows:
        sql = ("select j.jobname, d.runid, d.status, "
               "to_char(d.start_time at time zone 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"'), "
               "round(extract(epoch from (d.end_time - d.start_time)) * 1000, 1) "
               "from cron.job_run_details d join cron.job j on j.jobid = d.jobid "
               "where j.jobname like 'documentdb_index_build_task%' "
               f"and d.start_time >= '{iso(a - dt.timedelta(seconds=2.5))}'::timestamptz "
               f"and d.start_time <= '{iso(b + dt.timedelta(seconds=0.5))}'::timestamptz order by d.start_time")

        def rd(r, resp, label=label, a=a, b=b):
            inside = [x for x in r if iso(a) <= x[3][:23] + "Z" <= iso(b)]
            longest = max(inside, key=lambda x: float(x[4])) if inside else None
            return (f"{label}: createIndexes ran {iso(a)} -> {iso(b)} "
                    f"({(b - a).total_seconds() * 1000:.0f} ms); index-build job runs from 2.5 s before to 0.5 s after: "
                    + "; ".join(f"{x[0]} {x[3][11:23]} {x[4]} ms" for x in r)
                    + (f". Longest run inside the window: {longest[0]} at {longest[3][11:23]}, {longest[4]} ms." if longest else
                       ". No index-build run started inside the window."))
        step(f"index-build pg_cron runs around createIndexes, {label}", psql_argv(sql), rd)

    out = {"test": "ttl-semantics rerun: extra read-only checks", "steps": STEPS,
           "caveat": "Read-only observations of documentdb-local pg17-1.2.0; not evidence about the managed service."}
    with open(os.path.join(HERE, "extra_checks.json"), "w") as f:
        f.write(json.dumps(out, indent=2) + "\n")
    for s in STEPS:
        print(f"[E{s['n']:02d}] {s['step']}: {s['reading']}")


if __name__ == "__main__":
    main()
