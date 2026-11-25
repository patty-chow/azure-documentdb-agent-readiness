#!/usr/bin/env python
"""Regenerate the readings of the two successful createIndexes steps in report.json.

The first run of run_ttl_test.py read numIndexesBefore/After from the top level of
the createIndexes reply, but the gateway nests them as {raw: {defaultShard: {...}}, ok: 1},
so those two readings said "None". run_ttl_test.py is fixed (ci_counts); this script
rewrites only the reading text of those steps from the recorded raw responses.
Touches no database. Idempotent.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "report.json")  # e.g. report.run1.json


def ci_counts(r):
    if not isinstance(r, dict):
        return {}
    if "numIndexesBefore" in r:
        return r
    for v in ((r or {}).get("raw") or {}).values():
        return v
    return {}


def main():
    rep = json.load(open(PATH))
    n_docs = None
    for s in rep["steps"]:
        if s["step"] == "insert the test documents" and s["ok"]:
            n_docs = s["response"].get("n")
    changed = []
    for s in rep["steps"]:
        if not s.get("ok"):
            continue
        if s["step"] != "create TTL index on exp" and not s["step"].startswith("create second TTL index on exp2"):
            continue
        r = s.get("response") or {}
        c = ci_counts(r)
        shards = ",".join((r.get("raw") or {}).keys()) or "-"
        if s["step"] == "create TTL index on exp":
            s["reading"] = (f"Single-field TTL index exp_ttl created in {s['elapsedMs']:.0f} ms (numIndexesBefore "
                            f"{c.get('numIndexesBefore')} -> numIndexesAfter {c.get('numIndexesAfter')}, "
                            f"createdCollectionAutomatically {c.get('createdCollectionAutomatically')}, reply wrapped "
                            f"in raw.{shards} as a sharded router would wrap it).")
            s["readingAmendedBy"] = "amend_readings.py (counts unwrapped from raw.defaultShard)"
            changed.append(s["n"])
        elif s["step"].startswith("create second TTL index on exp2"):
            s["reading"] = (f"A second single-field TTL index (exp2_ttl) is accepted next to exp_ttl (numIndexesBefore "
                            f"{c.get('numIndexesBefore')} -> numIndexesAfter {c.get('numIndexesAfter')}, reply in "
                            f"raw.{shards}) and took {s['elapsedMs']:.0f} ms on the {n_docs}-document collection.")
            s["readingAmendedBy"] = "amend_readings.py (counts unwrapped from raw.defaultShard)"
            changed.append(s["n"])
    with open(PATH, "w") as f:
        f.write(json.dumps(rep, indent=2, default=str) + "\n")
    print("amended steps:", changed)


if __name__ == "__main__":
    main()
