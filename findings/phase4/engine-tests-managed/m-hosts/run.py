#!/usr/bin/env python3
"""m-hosts: host forms and identity on the managed Azure DocumentDB service.

Run through run.sh, which sources ../managed.env into the environment.
Writes raw.json next to this file; every password, GUID and e-mail address is scrubbed
before anything is written. build_report.py turns raw.json into report.json.

Database written: mt_hosts only (dropped at the end). Read-only admin commands
(ping, hello, buildInfo, isMaster, getCmdLineOpts, getParameter, connectionStatus,
listDatabases filtered to mt_hosts) run against the admin database.
No cluster configuration is changed: the az calls are list/show/GET or the
non-mutating listConnectionStrings action.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import platform
import re
import shlex
import socket
import ssl
import subprocess
import sys
import time
import traceback
import urllib.parse
import warnings
from pathlib import Path

import dns.resolver
import dns.version
import pymongo
from bson import json_util
from pymongo import MongoClient
from pymongo.errors import OperationFailure

try:
    from pymongo.uri_parser import parse_uri
except Exception:  # pragma: no cover
    from pymongo.synchronous.uri_parser import parse_uri  # type: ignore

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw.json"
DB = "mt_hosts"
COLL = "docs"
PORT_DEFAULT = 10260

REQ = ["MANAGED_URI", "MANAGED_GLOBAL_URI", "MANAGED_HOST", "MANAGED_GLOBAL_HOST",
       "MANAGED_RG", "MANAGED_CLUSTER", "MANAGED_PASS"]
_missing = [k for k in REQ if not os.environ.get(k)]
if _missing:
    sys.exit(f"missing environment variables: {_missing} (run through run.sh)")

URI = {"plain": os.environ["MANAGED_URI"], "global": os.environ["MANAGED_GLOBAL_URI"]}
HOST = {"plain": os.environ["MANAGED_HOST"], "global": os.environ["MANAGED_GLOBAL_HOST"]}
RG = os.environ["MANAGED_RG"]
CLUSTER = os.environ["MANAGED_CLUSTER"]
PASS = os.environ["MANAGED_PASS"]
_m = re.match(r"^[A-Za-z0-9+.-]+://([^:@/]+):([^@]*)@", URI["plain"])
USER = urllib.parse.unquote(_m.group(1)) if _m else None

# ------------------------------------------------------------------------------ scrubbing
_secret_set = {PASS, urllib.parse.quote_plus(PASS), urllib.parse.quote(PASS, safe="")}
for _u in URI.values():
    _mm = re.match(r"^[A-Za-z0-9+.-]+://[^:@/]*:([^@]*)@", _u)
    if _mm:
        _secret_set.add(_mm.group(1))
        _secret_set.add(urllib.parse.unquote_plus(_mm.group(1)))
SECRETS = sorted({s for s in _secret_set if s}, key=len, reverse=True)
GUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}")
USERINFO_RE = re.compile(r"(://[^:/@\s\"'<>]+:)([^@\s\"'<][^@\s\"']*)@")
_guid_map: dict[str, str] = {}
# The local scratchpad directory name carries a Claude session GUID; it is not an Azure
# subscription, tenant or object id, so it is left readable in file paths.
PATH_GUIDS = {g.lower() for g in GUID_RE.findall(str(HERE))}


def scrub_str(s: str) -> str:
    for sec in SECRETS:
        if sec in s:
            s = s.replace(sec, "<password-masked>")
    s = USERINFO_RE.sub(lambda m: m.group(1) + "<password-masked>@", s)

    def _g(m: re.Match) -> str:
        g = m.group(0).lower()
        if g in PATH_GUIDS:
            return m.group(0)
        if g not in _guid_map:
            _guid_map[g] = f"<guid-{len(_guid_map) + 1}-masked>"
        return _guid_map[g]

    s = GUID_RE.sub(_g, s)

    def _e(m: re.Match) -> str:
        txt = m.group(0)
        if txt.lower().endswith(".cosmos.azure.com"):  # user@host inside a URI, not an e-mail
            return txt
        return "<email-masked>"

    return EMAIL_RE.sub(_e, s)


def scrub(o):
    if isinstance(o, str):
        return scrub_str(o)
    if isinstance(o, dict):
        return {scrub_str(str(k)): scrub(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [scrub(v) for v in o]
    return o


def jsonable(o):
    return json.loads(json_util.dumps(o, json_options=json_util.RELAXED_JSON_OPTIONS))


def ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 1)


# ------------------------------------------------------------------------------ recording
STEPS: list[dict] = []
T0 = time.time()


def record(step: str, section: str, command: str, **kw) -> dict:
    rec = {"step": step, "section": section, "command": command}
    rec.update(kw)
    rec = scrub(rec)
    STEPS.append(rec)
    status = "ERROR" if rec.get("error") else "ok"
    print(f"[{time.time() - T0:7.1f}s] {step}: {status}", flush=True)
    return rec


def err_dict(e: BaseException) -> dict:
    d = {"type": type(e).__name__, "message": str(e)}
    if isinstance(e, OperationFailure):
        det = e.details or {}
        d.update({
            "code": e.code,
            "codeName": det.get("codeName"),
            "errmsg": det.get("errmsg"),
            "errorLabels": det.get("errorLabels"),
            "details": jsonable(det),
        })
    labels = getattr(e, "_error_labels", None)
    if labels:
        d["driver_error_labels"] = sorted(labels)
    return d


def sh(cmd: list[str], timeout: int = 180) -> dict:
    t = time.perf_counter()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except subprocess.TimeoutExpired as e:
        def _d(x):
            return x.decode(errors="replace") if isinstance(x, bytes) else x
        out = {"returncode": None, "timeout_s": timeout, "stdout": _d(e.stdout), "stderr": _d(e.stderr)}
    out["elapsed_ms"] = ms(t)
    return out


def cmd_step(step: str, section: str, label: str, client: MongoClient, dbname: str, cmd: dict, **kw):
    command = f"client_{label}[{dbname!r}].command({json_util.dumps(cmd)})"
    t = time.perf_counter()
    try:
        res = client[dbname].command(cmd)
        record(step, section, command, response=jsonable(res), elapsed_ms=ms(t), **kw)
        return res
    except Exception as e:  # record the exact error, never skip
        record(step, section, command, error=err_dict(e), elapsed_ms=ms(t), **kw)
        return None


def topo(c: MongoClient) -> dict:
    td = c.topology_description
    out = {
        "topology_type": td.topology_type_name,
        "common_wire_version": td.common_wire_version,
        "servers": [],
    }
    for addr, sd in sorted(td.server_descriptions().items()):
        out["servers"].append({
            "address": f"{addr[0]}:{addr[1]}",
            "server_type": sd.server_type_name,
            "round_trip_time_ms": None if sd.round_trip_time is None else round(sd.round_trip_time * 1000, 1),
            "min_wire_version": sd.min_wire_version,
            "max_wire_version": sd.max_wire_version,
        })
    try:
        a = c.address
        out["client.address"] = None if a is None else f"{a[0]}:{a[1]}"
    except Exception as e:
        out["client.address"] = f"{type(e).__name__}: {e}"
    return out


def wlist_to_json(wl) -> list[dict]:
    return [{"category": w.category.__name__, "message": str(w.message),
             "filename": w.filename, "lineno": w.lineno} for w in wl]


def dict_diff(a: dict | None, b: dict | None, ignore=("localTime", "connectionId", "operationTime", "$clusterTime")) -> dict:
    if a is None or b is None:
        return {"comparable": False}
    a = jsonable(a)
    b = jsonable(b)
    keys = sorted(set(a) | set(b))
    out = {"comparable": True, "ignored_keys": list(ignore), "only_in_first": [], "only_in_second": [], "different_values": {}}
    for k in keys:
        if k in ignore:
            continue
        if k not in b:
            out["only_in_first"].append(k)
        elif k not in a:
            out["only_in_second"].append(k)
        elif a[k] != b[k]:
            out["different_values"][k] = [a[k], b[k]]
    out["identical_apart_from_ignored"] = not (out["only_in_first"] or out["only_in_second"] or out["different_values"])
    return out


# ------------------------------------------------------------------------------ (a) DNS
def section_a() -> dict:
    targets: dict[str, list[tuple[str, int]]] = {}
    for label in ("plain", "global"):
        h = HOST[label]
        srv_name = f"_mongodb._tcp.{h}"
        record(f"a-{label}-dig-srv-short", "a-dns", shlex.join(["dig", "+short", "SRV", srv_name]),
               response=sh(["dig", "+short", "SRV", srv_name], 30))
        record(f"a-{label}-dig-srv-answer", "a-dns", shlex.join(["dig", "+noall", "+answer", "SRV", srv_name]),
               response=sh(["dig", "+noall", "+answer", "SRV", srv_name], 30))
        # dnspython: the resolver PyMongo itself uses for SRV/TXT
        t = time.perf_counter()
        try:
            ans = dns.resolver.resolve(srv_name, "SRV", lifetime=10)
            recs = [{"priority": r.priority, "weight": r.weight, "port": r.port,
                     "target": r.target.to_text(omit_final_dot=True)} for r in ans]
            targets[label] = [(r["target"].lower(), r["port"]) for r in recs]
            record(f"a-{label}-dnspython-srv", "a-dns", f"dns.resolver.resolve({srv_name!r}, 'SRV', lifetime=10)",
                   response={"canonical_name": ans.canonical_name.to_text(), "ttl": ans.rrset.ttl, "records": recs},
                   elapsed_ms=ms(t))
        except Exception as e:
            targets[label] = []
            record(f"a-{label}-dnspython-srv", "a-dns", f"dns.resolver.resolve({srv_name!r}, 'SRV', lifetime=10)",
                   error=err_dict(e), elapsed_ms=ms(t))
        record(f"a-{label}-dig-txt", "a-dns", shlex.join(["dig", "+short", "TXT", h]),
               response=sh(["dig", "+short", "TXT", h], 30))
        t = time.perf_counter()
        try:
            ans = dns.resolver.resolve(h, "TXT", lifetime=10)
            record(f"a-{label}-dnspython-txt", "a-dns", f"dns.resolver.resolve({h!r}, 'TXT', lifetime=10)",
                   response={"records": [b"".join(r.strings).decode() for r in ans], "ttl": ans.rrset.ttl},
                   elapsed_ms=ms(t))
        except Exception as e:
            record(f"a-{label}-dnspython-txt", "a-dns", f"dns.resolver.resolve({h!r}, 'TXT', lifetime=10)",
                   error=err_dict(e), elapsed_ms=ms(t))
        # the bare cluster host itself (what a non-SRV mongodb:// URI would need)
        record(f"a-{label}-dig-host-A", "a-dns", shlex.join(["dig", "+noall", "+comments", "+answer", "+authority", "A", h]),
               response=sh(["dig", "+noall", "+comments", "+answer", "+authority", "A", h], 30))
        t = time.perf_counter()
        try:
            gai = socket.getaddrinfo(h, PORT_DEFAULT, proto=socket.IPPROTO_TCP)
            record(f"a-{label}-getaddrinfo-host", "a-dns", f"socket.getaddrinfo({h!r}, {PORT_DEFAULT}, proto=IPPROTO_TCP)",
                   response=sorted({g[4][0] for g in gai}), elapsed_ms=ms(t))
        except Exception as e:
            record(f"a-{label}-getaddrinfo-host", "a-dns", f"socket.getaddrinfo({h!r}, {PORT_DEFAULT}, proto=IPPROTO_TCP)",
                   error=err_dict(e), elapsed_ms=ms(t))
        # what PyMongo's URI parser makes of the SRV form (no credentials in this URI)
        t = time.perf_counter()
        try:
            res = parse_uri(f"mongodb+srv://{h}/", connect_timeout=10)
            opts = res["options"]
            record(f"a-{label}-pymongo-parse_uri", "a-dns", f"pymongo.uri_parser.parse_uri('mongodb+srv://{h}/', connect_timeout=10)",
                   response={"nodelist": [f"{n[0]}:{n[1]}" for n in res["nodelist"]],
                             "options": {k: opts[k] for k in opts}, "fqdn": res.get("fqdn")},
                   elapsed_ms=ms(t))
        except Exception as e:
            record(f"a-{label}-pymongo-parse_uri", "a-dns", f"pymongo.uri_parser.parse_uri('mongodb+srv://{h}/', connect_timeout=10)",
                   error=err_dict(e), elapsed_ms=ms(t))
    # A / CNAME / AAAA of every SRV target, plus what the OS resolver returns for it
    for label, tl in targets.items():
        for (tgt, port) in tl:
            record(f"a-{label}-target-dig-cname", "a-dns", shlex.join(["dig", "+short", "CNAME", tgt]),
                   response=sh(["dig", "+short", "CNAME", tgt], 30), target=tgt)
            record(f"a-{label}-target-dig-a", "a-dns", shlex.join(["dig", "+short", "A", tgt]),
                   response=sh(["dig", "+short", "A", tgt], 30), target=tgt)
            record(f"a-{label}-target-dig-a-chain", "a-dns", shlex.join(["dig", "+noall", "+answer", "A", tgt]),
                   response=sh(["dig", "+noall", "+answer", "A", tgt], 30), target=tgt)
            record(f"a-{label}-target-dig-aaaa-chain", "a-dns", shlex.join(["dig", "+noall", "+answer", "AAAA", tgt]),
                   response=sh(["dig", "+noall", "+answer", "AAAA", tgt], 30), target=tgt)
            t = time.perf_counter()
            try:
                gai = socket.getaddrinfo(tgt, port, proto=socket.IPPROTO_TCP)
                record(f"a-{label}-target-getaddrinfo", "a-dns", f"socket.getaddrinfo({tgt!r}, {port}, proto=IPPROTO_TCP)",
                       response=sorted({g[4][0] for g in gai}), elapsed_ms=ms(t), target=tgt)
            except Exception as e:
                record(f"a-{label}-target-getaddrinfo", "a-dns", f"socket.getaddrinfo({tgt!r}, {port}, proto=IPPROTO_TCP)",
                       error=err_dict(e), elapsed_ms=ms(t), target=tgt)
    return targets


def section_tls(targets: dict) -> list[str]:
    san_names: list[str] = []
    for label, tl in targets.items():
        for (tgt, port) in tl:
            command = (f"ssl.create_default_context().wrap_socket(socket.create_connection(({tgt!r}, {port}), timeout=15), "
                       f"server_hostname={tgt!r}).getpeercert()")
            t = time.perf_counter()
            try:
                ctx = ssl.create_default_context()
                with socket.create_connection((tgt, port), timeout=15) as sock:
                    with ctx.wrap_socket(sock, server_hostname=tgt) as ss:
                        cert = ss.getpeercert() or {}
                        resp = {
                            "peer_ip": ss.getpeername()[0],
                            "tls_version": ss.version(),
                            "cipher": list(ss.cipher() or []),
                            "subject": cert.get("subject"),
                            "issuer": cert.get("issuer"),
                            "subjectAltName": cert.get("subjectAltName"),
                            "notBefore": cert.get("notBefore"),
                            "notAfter": cert.get("notAfter"),
                            "serialNumber": cert.get("serialNumber"),
                        }
                        for typ, val in cert.get("subjectAltName") or []:
                            if typ == "DNS" and val.lower() not in san_names:
                                san_names.append(val.lower())
                record(f"a-{label}-target-tls-cert", "a-dns", command, response=resp, elapsed_ms=ms(t), target=tgt)
            except Exception as e:
                record(f"a-{label}-target-tls-cert", "a-dns", command, error=err_dict(e), elapsed_ms=ms(t), target=tgt)
    return san_names


def section_san_dns(san_names: list[str], targets: dict) -> list[tuple[str, int]]:
    """DNS for every certificate SAN that is not an SRV target, plus the SRV name a
    '.ro.global.' cluster form would use. Returns node hosts with an A record to probe."""
    srv_targets = {t for tl in targets.values() for (t, _p) in tl}
    probe: list[tuple[str, int]] = []
    for i, name in enumerate(san_names, 1):
        if name in srv_targets:
            continue
        record(f"a-san{i}-dig-a-chain", "a-dns", shlex.join(["dig", "+noall", "+answer", "A", name]),
               response=sh(["dig", "+noall", "+answer", "A", name], 30), target=name,
               note="name taken from the TLS certificate subjectAltName list")
        t = time.perf_counter()
        try:
            gai = socket.getaddrinfo(name, PORT_DEFAULT, proto=socket.IPPROTO_TCP)
            ips = sorted({g[4][0] for g in gai})
            record(f"a-san{i}-getaddrinfo", "a-dns", f"socket.getaddrinfo({name!r}, {PORT_DEFAULT}, proto=IPPROTO_TCP)",
                   response=ips, elapsed_ms=ms(t), target=name)
            if ".ro.global." in name:
                probe.append((name, PORT_DEFAULT))
        except Exception as e:
            record(f"a-san{i}-getaddrinfo", "a-dns", f"socket.getaddrinfo({name!r}, {PORT_DEFAULT}, proto=IPPROTO_TCP)",
                   error=err_dict(e), elapsed_ms=ms(t), target=name)
    base = HOST["plain"].split(".", 1)
    for j, guess in enumerate((f"{base[0]}.ro.global.{base[1]}", f"{base[0]}.data.{base[1]}",
                               f"{base[0]}.data.global.{base[1]}"), 1):
        srv_name = f"_mongodb._tcp.{guess}"
        record(f"a-guess{j}-dig-srv", "a-dns", shlex.join(["dig", "+noall", "+comments", "+answer", "SRV", srv_name]),
               response=sh(["dig", "+noall", "+comments", "+answer", "SRV", srv_name], 30), target=srv_name,
               note="cluster-level SRV name inferred from the certificate SAN pattern; not a documented host form")
    return probe


# ------------------------------------------------------------------------------ (b) connect
CLIENTS: dict[str, MongoClient] = {}
KW = dict(serverSelectionTimeoutMS=20000, connectTimeoutMS=20000, socketTimeoutMS=60000, appname="mt-hosts")


def connect_form(label: str) -> MongoClient | None:
    uri = URI[label]
    command = (f"client_{label} = MongoClient({scrub_str(uri)!r}, serverSelectionTimeoutMS=20000, "
               f"connectTimeoutMS=20000, socketTimeoutMS=60000, appname='mt-hosts')")
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        t = time.perf_counter()
        try:
            c = MongoClient(uri, **KW)
            err = None
        except Exception as e:
            c, err = None, e
        el = ms(t)
    w = wlist_to_json(wl)
    if c is None:
        record(f"b-{label}-construct", "b-connect", command, error=err_dict(err),
               warnings_during_call=w, elapsed_ms=el)
        return None
    record(f"b-{label}-construct", "b-connect", command, response={"constructed": True},
           warnings_during_call=w, elapsed_ms=el)
    CLIENTS[label] = c
    with warnings.catch_warnings(record=True) as wl2:
        warnings.simplefilter("always")
        cmd_step(f"b-{label}-ping", "b-connect", label, c, "admin", {"ping": 1})
    STEPS[-1]["warnings_during_call"] = scrub(wlist_to_json(wl2))
    record(f"b-{label}-topology", "b-connect", f"client_{label}.topology_description / client_{label}.address",
           response=topo(c))
    cmd_step(f"b-{label}-connectionStatus", "b-connect", label, c, "admin", {"connectionStatus": 1})
    return c


def crud(label: str, c: MongoClient) -> None:
    doc = {"_id": f"via-{label}", "form": label, "uri_host": HOST[label],
           "written_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0)}
    command = f"client_{label}[{DB!r}][{COLL!r}].insert_one({json_util.dumps(doc)})"
    t = time.perf_counter()
    try:
        r = c[DB][COLL].insert_one(doc)
        record(f"b-{label}-insert", "b-connect", command,
               response={"acknowledged": r.acknowledged, "inserted_id": r.inserted_id}, elapsed_ms=ms(t))
    except Exception as e:
        record(f"b-{label}-insert", "b-connect", command, error=err_dict(e), elapsed_ms=ms(t))
    command = f"list(client_{label}[{DB!r}][{COLL!r}].find({{'_id': 'via-{label}'}}))"
    t = time.perf_counter()
    try:
        docs = list(c[DB][COLL].find({"_id": f"via-{label}"}))
        record(f"b-{label}-find", "b-connect", command, response=jsonable(docs), elapsed_ms=ms(t))
    except Exception as e:
        record(f"b-{label}-find", "b-connect", command, error=err_dict(e), elapsed_ms=ms(t))


def connect_nonsrv(step_prefix: str, host: str, port: int, do_find: bool = True, do_hello: bool = False) -> None:
    command = (f"MongoClient(host={host!r}, port={port}, username={USER!r}, password='<password-masked>', tls=True, "
               f"authMechanism='SCRAM-SHA-256', retryWrites=False, serverSelectionTimeoutMS=10000, connectTimeoutMS=10000)"
               f"  # = mongodb://{USER}:<password-masked>@{host}:{port}/?tls=true&authMechanism=SCRAM-SHA-256&retryWrites=false")
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        t = time.perf_counter()
        try:
            c = MongoClient(host=host, port=port, username=USER, password=PASS, tls=True,
                            authMechanism="SCRAM-SHA-256", retryWrites=False,
                            serverSelectionTimeoutMS=10000, connectTimeoutMS=10000, appname="mt-hosts")
            err = None
        except Exception as e:
            c, err = None, e
        el = ms(t)
    if c is None:
        record(f"{step_prefix}-construct", "b-connect", command, error=err_dict(err),
               warnings_during_call=wlist_to_json(wl), elapsed_ms=el)
        return
    record(f"{step_prefix}-construct", "b-connect", command, response={"constructed": True},
           warnings_during_call=wlist_to_json(wl), elapsed_ms=el)
    try:
        cmd_step(f"{step_prefix}-ping", "b-connect", "nonsrv", c, "admin", {"ping": 1})
        if STEPS[-1].get("error") is None:
            record(f"{step_prefix}-topology", "b-connect", "client_nonsrv.topology_description / client_nonsrv.address",
                   response=topo(c))
            if do_hello:
                cmd_step(f"{step_prefix}-hello", "b-connect", "nonsrv", c, "admin", {"hello": 1})
            if do_find:
                command2 = f"list(client_nonsrv[{DB!r}][{COLL!r}].find({{}}, {{'_id': 1}}).sort('_id', 1))"
                t = time.perf_counter()
                try:
                    docs = list(c[DB][COLL].find({}, {"_id": 1}).sort("_id", 1))
                    record(f"{step_prefix}-find", "b-connect", command2, response=jsonable(docs), elapsed_ms=ms(t))
                except Exception as e:
                    record(f"{step_prefix}-find", "b-connect", command2, error=err_dict(e), elapsed_ms=ms(t))
    finally:
        c.close()


# ------------------------------------------------------------------------------ (c) CLI
def section_c() -> None:
    record("c-help", "c-cli", "az documentdb mongocluster list-connection-strings --help",
           response=sh(["az", "documentdb", "mongocluster", "list-connection-strings", "--help"], 120))
    out = sh(["az", "documentdb", "mongocluster", "list-connection-strings", "-g", RG,
              "--cluster-name", CLUSTER, "-o", "json"], 180)
    analysis = analyse_conn_strings(out)
    record("c-list-connection-strings", "c-cli",
           shlex.join(["az", "documentdb", "mongocluster", "list-connection-strings", "-g", RG,
                       "--cluster-name", CLUSTER, "-o", "json"]),
           response=out, analysis=analysis,
           note="CLI documentdb extension 1.0.0 sends api-version 2026-06-01 (aaz _list_connection_strings.py line 128)")
    out = sh(["az", "documentdb", "mongocluster", "show", "-g", RG, "--cluster-name", CLUSTER,
              "--query", "properties.connectionString", "-o", "json"], 180)
    record("c-show-default-connectionString", "c-cli",
           shlex.join(["az", "documentdb", "mongocluster", "show", "-g", RG, "--cluster-name", CLUSTER,
                       "--query", "properties.connectionString", "-o", "json"]),
           response=out)
    q = ("{location:location, serverVersion:properties.serverVersion, provisioningState:properties.provisioningState, "
         "clusterStatus:properties.clusterStatus, publicNetworkAccess:properties.publicNetworkAccess, "
         "replica:properties.replica, highAvailability:properties.highAvailability, sharding:properties.sharding, "
         "compute:properties.compute, storage:properties.storage, authConfig:properties.authConfig, "
         "previewFeatures:properties.previewFeatures, infrastructureVersion:properties.infrastructureVersion}")
    out = sh(["az", "documentdb", "mongocluster", "show", "-g", RG, "--cluster-name", CLUSTER,
              "--query", q, "-o", "json"], 180)
    record("c-show-topology-context", "c-cli",
           shlex.join(["az", "documentdb", "mongocluster", "show", "-g", RG, "--cluster-name", CLUSTER,
                       "--query", q, "-o", "json"]),
           response=out)
    out = sh(["az", "documentdb", "mongocluster", "replica", "list", "-g", RG, "--source-cluster", CLUSTER, "-o", "json"], 180)
    record("c-replica-list", "c-cli",
           shlex.join(["az", "documentdb", "mongocluster", "replica", "list", "-g", RG,
                       "--source-cluster", CLUSTER, "-o", "json"]),
           response=out)
    for ver in ("2026-09-01", "2026-10-15-preview"):
        url = (f"https://management.azure.com/subscriptions/{{subscriptionId}}/resourceGroups/{RG}"
               f"/providers/Microsoft.DocumentDB/mongoClusters/{CLUSTER}/listConnectionStrings?api-version={ver}")
        out = sh(["az", "rest", "--method", "post", "--url", url, "-o", "json"], 180)
        record(f"c-rest-listConnectionStrings-{ver}", "c-cli",
               shlex.join(["az", "rest", "--method", "post", "--url", url, "-o", "json"]),
               response=out, analysis=analyse_conn_strings(out))


def analyse_conn_strings(out: dict) -> dict:
    if out.get("returncode") != 0:
        return {"parsed": False}
    try:
        parsed = json.loads(out["stdout"])
    except Exception as e:
        return {"parsed": False, "json_error": str(e)}
    entries = parsed.get("connectionStrings") if isinstance(parsed, dict) else None
    res = {"parsed": True, "top_level_type": type(parsed).__name__,
           "top_level_keys": sorted(parsed) if isinstance(parsed, dict) else None,
           "entry_count": None if entries is None else len(entries), "entries": []}
    for e in entries or []:
        cs = e.get("connectionString", "")
        sp = urllib.parse.urlsplit(cs)
        userinfo = sp.netloc.rsplit("@", 1)[0] if "@" in sp.netloc else None
        res["entries"].append({
            "keys": sorted(e),
            "name": e.get("name"),
            "description": e.get("description"),
            "scheme": sp.scheme,
            "host": sp.hostname,
            "userinfo_literal": userinfo,
            "query": dict(urllib.parse.parse_qsl(sp.query)),
            "is_global_host": bool(sp.hostname and ".global." in sp.hostname),
        })
    res["any_global_host"] = any(x["is_global_host"] for x in res["entries"])
    return res


# ------------------------------------------------------------------------------ (d) identity
def section_d() -> None:
    cp, cg = CLIENTS.get("plain"), CLIENTS.get("global")
    hp = cmd_step("d-hello-plain", "d-identity", "plain", cp, "admin", {"hello": 1}) if cp else None
    hg = cmd_step("d-hello-global", "d-identity", "global", cg, "admin", {"hello": 1}) if cg else None
    record("d-hello-diff", "d-identity", "dict_diff(hello via plain host, hello via .global. host)",
           response=dict_diff(hp, hg))
    bp = cmd_step("d-buildInfo-plain", "d-identity", "plain", cp, "admin", {"buildInfo": 1}) if cp else None
    bg = cmd_step("d-buildInfo-global", "d-identity", "global", cg, "admin", {"buildInfo": 1}) if cg else None
    record("d-buildInfo-diff", "d-identity", "dict_diff(buildInfo via plain host, buildInfo via .global. host)",
           response=dict_diff(bp, bg))
    if cp:
        im = cmd_step("d-isMaster-plain", "d-identity", "plain", cp, "admin", {"isMaster": 1})
        record("d-isMaster-vs-hello-diff", "d-identity", "dict_diff(hello via plain host, isMaster via plain host)",
               response=dict_diff(hp, im))
        cmd_step("d-getCmdLineOpts", "d-identity", "plain", cp, "admin", {"getCmdLineOpts": 1})
        cmd_step("d-getParameter-star", "d-identity", "plain", cp, "admin", {"getParameter": "*"})
        cmd_step("d-getParameter-fcv", "d-identity", "plain", cp, "admin",
                 {"getParameter": 1, "featureCompatibilityVersion": 1})
        cmd_step("d-getParameter-transactionLifetimeLimitSeconds", "d-identity", "plain", cp, "admin",
                 {"getParameter": 1, "transactionLifetimeLimitSeconds": 1})
        cmd_step("d-connectionStatus-showPrivileges", "d-identity", "plain", cp, "admin",
                 {"connectionStatus": 1, "showPrivileges": True})


def section_warnings(targets: dict) -> None:
    probe = HERE / "warn_probe.py"
    pw = os.environ.get("PYTHONWARNINGS")
    for which in ("plain", "global"):
        out = sh([sys.executable, str(probe), which], 120)
        record(f"d-warning-default-filters-{which}", "d-identity",
               f"{sys.executable} {probe} {which}   # MongoClient(MANAGED_{'URI' if which == 'plain' else 'GLOBAL_URI'}) + ping, "
               f"default warning filters, PYTHONWARNINGS={pw!r}",
               response=out)
    tl = targets.get("plain") or []
    if tl:
        tgt, port = tl[0]
        out = sh([sys.executable, str(probe), "target", tgt, str(port)], 120)
        record("d-warning-default-filters-nonsrv-target", "d-identity",
               f"{sys.executable} {probe} target {tgt} {port}   # non-SRV MongoClient(host=SRV target) + ping, "
               f"default warning filters, PYTHONWARNINGS={pw!r}",
               response=out)


# ------------------------------------------------------------------------------ main
def main() -> int:
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    env_info = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pymongo": pymongo.version,
        "dnspython": dns.version.version,
        "openssl": ssl.OPENSSL_VERSION,
        "dig": sh(["dig", "-v"], 10).get("stderr", "").strip(),
        "az_version": sh(["az", "version", "-o", "json"], 120).get("stdout"),
        "PYTHONWARNINGS": os.environ.get("PYTHONWARNINGS"),
    }
    targets: dict = {}
    ro_probe: list = []
    try:
        targets = section_a()
        san_names = section_tls(targets)
        ro_probe = section_san_dns(san_names, targets)

        cp = connect_form("plain")
        if cp:
            cmd_step("b-preclean-dropDatabase", "b-connect", "plain", cp, DB, {"dropDatabase": 1},
                     note="pre-clean of this test's own database before the first insert")
            crud("plain", cp)
        cg = connect_form("global")
        if cg:
            crud("global", cg)
        for label, c in CLIENTS.items():
            command = f"list(client_{label}[{DB!r}][{COLL!r}].find({{}}, {{'_id': 1, 'form': 1}}).sort('_id', 1))"
            t = time.perf_counter()
            try:
                docs = list(c[DB][COLL].find({}, {"_id": 1, "form": 1}).sort("_id", 1))
                record(f"b-{label}-cross-visibility", "b-connect", command, response=jsonable(docs), elapsed_ms=ms(t))
            except Exception as e:
                record(f"b-{label}-cross-visibility", "b-connect", command, error=err_dict(e), elapsed_ms=ms(t))
        # non-SRV host forms
        connect_nonsrv("b-extra-nonsrv-plain-cluster-host", HOST["plain"], PORT_DEFAULT, do_find=False)
        connect_nonsrv("b-extra-nonsrv-global-cluster-host", HOST["global"], PORT_DEFAULT, do_find=False)
        for label in ("plain", "global"):
            for (tgt, port) in targets.get(label, [])[:1]:
                connect_nonsrv(f"b-extra-nonsrv-{label}-srv-target", tgt, port, do_find=True)
        # node host names that appear only in the certificate (read-only probe: ping, hello, find)
        for (h, port) in ro_probe[:1]:
            connect_nonsrv("b-extra-nonsrv-ro-global-san-host", h, port, do_find=True, do_hello=True)

        section_c()
        section_d()
        section_warnings(targets)
    except Exception as e:  # keep going to cleanup; record the crash
        record("zz-script-exception", "internal", "run.py main()", error={"type": type(e).__name__, "message": str(e),
                                                                           "traceback": traceback.format_exc()})
    finally:
        cp = CLIENTS.get("plain")
        if cp is None:
            try:
                cp = MongoClient(URI["plain"], **KW)
                CLIENTS["plain"] = cp
            except Exception as e:
                record("z-cleanup-connect", "z-cleanup", "MongoClient(MANAGED_URI)", error=err_dict(e))
        if cp is not None:
            cmd_step("z-dropDatabase", "z-cleanup", "plain", cp, DB, {"dropDatabase": 1})
            r = cmd_step("z-verify-listDatabases-filter", "z-cleanup", "plain", cp, "admin",
                         {"listDatabases": 1, "nameOnly": True, "filter": {"name": DB}})
            if r is None:
                command = f"{DB!r} in client_plain.list_database_names()"
                t = time.perf_counter()
                try:
                    present = DB in cp.list_database_names()
                    record("z-verify-list_database_names", "z-cleanup", command,
                           response={"mt_hosts_present": present}, elapsed_ms=ms(t),
                           note="only the boolean is recorded, not other databases' names")
                except Exception as e:
                    record("z-verify-list_database_names", "z-cleanup", command, error=err_dict(e), elapsed_ms=ms(t))
        for c in CLIENTS.values():
            try:
                c.close()
            except Exception:
                pass
        raw = {
            "test": "m-hosts",
            "database": DB,
            "started_utc": started,
            "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "cluster": {"resource_group": RG, "cluster": CLUSTER, "plain_host": HOST["plain"], "global_host": HOST["global"]},
            "uris_as_used": {k: scrub_str(v) for k, v in URI.items()},
            "environment": env_info,
            "steps": STEPS,
            "masking": {"guids_masked": len(_guid_map),
                        "rule": "password (raw and URL-encoded) -> <password-masked>; any GUID -> <guid-N-masked>; e-mail -> <email-masked>"},
        }
        text = json.dumps(scrub(raw), indent=2, default=str)
        for sec in SECRETS:
            if sec in text:  # belt and braces; should never happen after scrub()
                text = text.replace(sec, "<password-masked>")
        RAW.write_text(text)
        print(f"wrote {RAW} ({len(text)} bytes, {len(STEPS)} steps)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
