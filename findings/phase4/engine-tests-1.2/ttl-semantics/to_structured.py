#!/usr/bin/env python
"""Print report.json's steps as compact {step, command, response, reading} rows (stdout only).

The response is rendered as an exact but compact string: shell steps keep returncode,
stdout and stderr verbatim; driver steps keep the server reply as JSON; the poll step
is rendered one line per poll (time, seconds after insert, count, ids gone, probe).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
rep = json.load(open(os.path.join(HERE, "report.json")))


def compact(o):
    return json.dumps(o, separators=(",", ":"), default=str)


rows = []
for s in rep["steps"]:
    r = s.get("response")
    cmd = s["command"]
    if s["step"] == "insert the test documents":
        cmd = cmd.replace("<the 10 documents in insertedDocuments>", compact(s.get("insertedDocuments")))
    if isinstance(r, dict) and "returncode" in r:
        resp = f"returncode {r.get('returncode')}; stdout: {json.dumps(r.get('stdout'))}; stderr: {json.dumps(r.get('stderr'))}"
    elif s["step"].startswith("poll every"):
        lines = []
        for p in r["polls"]:
            extra = ""
            if p.get("probeInserted"):
                extra = f" then inserted {p['probeInserted']['_id']} at {p['probeInserted']['insertedAt'][11:23]}"
            if p.get("error"):
                extra += f" ERROR {compact(p['error'])}"
            lines.append(f"poll {p['poll']} {p['at'][11:23]}Z +{p['secondsAfterInsert']}s count={p.get('count')} "
                         f"gone={p.get('goneSinceLastPoll')}{extra}")
        resp = " | ".join(lines) + f" | final ids: {r.get('finalPresentIds')}"
    else:
        resp = compact(r)
    rows.append({"step": f"{s['n']:02d} {s['step']}", "command": cmd, "response": resp, "reading": s["reading"]})
print(json.dumps(rows, indent=1))
