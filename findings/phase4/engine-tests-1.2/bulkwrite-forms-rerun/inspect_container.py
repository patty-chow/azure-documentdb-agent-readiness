#!/usr/bin/env python
"""Supplementary, read-only inspection of the ddb-engine-test container for bulkwrite-forms.

Answers two side questions the wire tests raise, without writing anything anywhere:
  * which layer (gateway binary or engine extension pg_documentdb.so) contains the batch-limit and
    bulkWrite-stub error strings observed or expected in run.py;
  * where the advertised hello.maxWriteBatchSize=25000 most plausibly comes from (the engine GUC
    documentdb.maxWriteBatchSize, read by the gateway through pg_settings, versus the gateway's
    dynamic-configuration file).
Commands: docker inspect (labels only), grep -c / grep -o over two binaries, key names of the
gateway's JSON config files (no values), and one SELECT on pg_settings (catalog view, no table
data, no MongoDB database touched). Writes inspect.json next to this file.
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
C = "ddb-engine-test"
GW = "/home/documentdb/gateway/pg_documentdb_gw/target/release-with-symbols/documentdb_gateway"
SO = "/usr/lib/postgresql/17/lib/pg_documentdb.so"

STRINGS = [
    "Write batch size must fall within the range",
    "Batch sizes should always fall between",
    "bulkWrite is not yet implemented",
    "the bulkwrite procedure cannot be used in transactions",
]

checks = []


def sh(step, argv, reading_fn):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    resp = {"returncode": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    checks.append({"step": step, "command": " ".join(argv if argv[0] != "docker" else [a if " " not in a else repr(a) for a in argv]), "response": resp, "reading": reading_fn(resp)})
    print(f"[{step}] {checks[-1]['reading']}")


sh(
    "8a-container-image",
    ["docker", "inspect", C, "--format",
     '{{.Config.Image}}|{{.Image}}|{{index .Config.Labels "org.opencontainers.image.version"}}|{{index .Config.Labels "org.opencontainers.image.revision"}}|{{index .Config.Labels "org.opencontainers.image.created"}}'],
    lambda r: f"The container under test runs image {r['stdout'].split('|')[0]} (OCI version label {r['stdout'].split('|')[2]}, revision {r['stdout'].split('|')[3][:8]}, created {r['stdout'].split('|')[4]})." if r["returncode"] == 0 else f"docker inspect failed: {r['stderr']}",
)

grep_script = "; ".join(
    f'printf "%s|gateway=%s|pg_documentdb.so=%s\\n" "{s}" "$(grep -c -a -F "{s}" {GW})" "$(grep -c -a -F "{s}" {SO})"' for s in STRINGS
)
sh(
    "8b-error-string-locations",
    ["docker", "exec", C, "sh", "-c", grep_script],
    lambda r: "grep -c line counts per binary (0 = string absent) show where each error text lives: " + "; ".join(r["stdout"].splitlines()) + ".",
)

sh(
    "8c-gateway-settings-query",
    ["docker", "exec", C, "sh", "-c", f"grep -a -o \"SELECT name, setting FROM pg_settings WHERE name LIKE [^)]*)\" {GW} | head -1"],
    lambda r: f"The gateway binary embeds the SQL {r['stdout']!r}, so it is built to read documentdb.* engine settings from PostgreSQL (the string alone does not show which settings feed hello)." if r["stdout"] else "No pg_settings query string found in the gateway binary.",
)

sh(
    "8d-gateway-config-file-keys",
    ["docker", "exec", C, "sh", "-c",
     'for f in /tmp/SetupConfiguration_*.json; do d=$(grep -o "\\"DynamicConfigurationFile\\"[^,}]*" "$f" | sed -E "s/.*: *\\"([^\\"]*)\\".*/\\1/"); '
     'printf "setup_keys=%s\\n" "$(grep -o "\\"[A-Za-z]*\\":" "$f" | tr -d "\\":" | sort -u | tr "\\n" " ")"; '
     'printf "dynamic_file=%s\\n" "$d"; [ -f "$d" ] && printf "dynamic_keys=%s\\n" "$(grep -o "\\"[A-Za-z_]*\\":" "$d" | tr -d "\\":" | sort -u | tr "\\n" " ")"; '
     'printf "batch_mentions_in_setup=%s batch_mentions_in_dynamic=%s\\n" "$(grep -c -i batch "$f")" "$(grep -c -i batch "$d" 2>/dev/null)"; done'],
    lambda r: "Gateway configuration files (key names only): " + " ; ".join(r["stdout"].splitlines()) + ".",
)

sh(
    "8e-pg_settings-batch",
    ["docker", "exec", "-e", "PGCONNECT_TIMEOUT=5", C, "psql", "-w", "-X", "-p", "9712", "-d", "postgres", "-At", "-c",
     "select name, setting, boot_val, source from pg_settings where name ilike '%batch%' or name = 'server_version' order by name"],
    lambda r: "Engine settings (name|setting|boot_val|source): " + "; ".join(r["stdout"].splitlines()) + "." if r["returncode"] == 0 else f"pg_settings query failed: {r['stderr']}",
)

with open(os.path.join(HERE, "inspect.json"), "w") as f:
    json.dump({"note": "read-only container inspection; no MongoDB database touched", "steps": checks}, f, indent=2)
print(json.dumps({"n_checks": len(checks)}))
