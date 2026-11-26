#!/usr/bin/env python3
"""m-hosts supplementary DNS checks (no credentials, DNS queries only).

Interprets the NOERROR/NODATA answer for the '.ro.global.' SRV guess with control names
that cannot exist, and shows the zone apex records for the privatelink zone the SRV
targets CNAME into. Writes dns_extra.json next to this file.
"""
import datetime as dt
import json
import shlex
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLUSTER = "ddb-samples-shared"
NODE = "fc-a472369cc681-000"
SUFFIX = "mongocluster.cosmos.azure.com"

QUERIES = [
    ("x1-ro-global-srv", ["+noall", "+comments", "+answer", "+authority", "SRV", f"_mongodb._tcp.{CLUSTER}.ro.global.{SUFFIX}"]),
    ("x2-control-ro-global-srv-nonexistent", ["+noall", "+comments", "+answer", "+authority", "SRV", f"_mongodb._tcp.zz-mt-hosts-nonexistent.ro.global.{SUFFIX}"]),
    ("x3-ro-global-cluster-host-A", ["+noall", "+comments", "+answer", "+authority", "A", f"{CLUSTER}.ro.global.{SUFFIX}"]),
    ("x4-control-plain-srv-nonexistent", ["+noall", "+comments", "+answer", "+authority", "SRV", f"_mongodb._tcp.zz-mt-hosts-nonexistent.{SUFFIX}"]),
    ("x5-control-global-srv-nonexistent", ["+noall", "+comments", "+answer", "+authority", "SRV", f"_mongodb._tcp.zz-mt-hosts-nonexistent.global.{SUFFIX}"]),
    ("x6-privatelink-zone-SOA", ["+noall", "+comments", "+answer", "+authority", "SOA", f"privatelink.{SUFFIX}"]),
    ("x7-global-privatelink-name-A", ["+noall", "+comments", "+answer", "+authority", "A", f"{NODE}.global.privatelink.{SUFFIX}"]),
    ("x8-plain-privatelink-name-A", ["+noall", "+comments", "+answer", "+authority", "A", f"{NODE}.privatelink.{SUFFIX}"]),
    ("x9-global-cluster-host-in-privatelink-A", ["+noall", "+comments", "+answer", "+authority", "A", f"{CLUSTER}.global.privatelink.{SUFFIX}"]),
    ("x10-ro-global-srvname-TXT", ["+noall", "+comments", "+answer", "+authority", "TXT", f"_mongodb._tcp.{CLUSTER}.ro.global.{SUFFIX}"]),
    ("x11-ro-global-srvname-CNAME", ["+noall", "+comments", "+answer", "+authority", "CNAME", f"_mongodb._tcp.{CLUSTER}.ro.global.{SUFFIX}"]),
    ("x12-ro-global-srvname-A", ["+noall", "+comments", "+answer", "+authority", "A", f"_mongodb._tcp.{CLUSTER}.ro.global.{SUFFIX}"]),
    ("x13-ro-global-cluster-host-TXT", ["+noall", "+comments", "+answer", "+authority", "TXT", f"{CLUSTER}.ro.global.{SUFFIX}"]),
    ("x14-plain-srvname-TXT", ["+noall", "+comments", "+answer", "+authority", "TXT", f"_mongodb._tcp.{CLUSTER}.{SUFFIX}"]),
]


def main() -> None:
    steps = []
    for step, args in QUERIES:
        cmd = ["dig"] + args
        t = time.perf_counter()
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        steps.append({
            "step": step,
            "section": "a-dns",
            "command": shlex.join(cmd),
            "response": {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
                         "elapsed_ms": round((time.perf_counter() - t) * 1000, 1)},
        })
        print(step, "rc", p.returncode, flush=True)
    out = {"test": "m-hosts", "part": "dns_extra", "run_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "steps": steps}
    (HERE / "dns_extra.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
