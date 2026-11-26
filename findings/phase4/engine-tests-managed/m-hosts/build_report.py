#!/usr/bin/env python3
"""Builds report.json for test m-hosts from raw.json (run 2, canonical), raw_run1.json
(run 1, consistency check) and dns_extra.json, adding a one-sentence reading and an
open-source comparison to every step. Reads only already-scrubbed files; needs no secrets.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OSS_REPORT = Path("/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/local-gateway-parity/report.json")

raw = json.loads((HERE / "raw.json").read_text())
run1 = json.loads((HERE / "raw_run1.json").read_text())
extra = json.loads((HERE / "dns_extra.json").read_text())
oss = json.loads(OSS_REPORT.read_text())
oss_steps = {s["step"]: s for s in oss["steps"]}
OSS_HELLO = oss_steps["00-hello"]["response"]
OSS_BUILDINFO = oss_steps["00-buildInfo"]["response"]
OSS_CONNSTATUS = oss_steps["10-connectionStatus-showPrivileges"]["response"]
OSS_REF = {
    "hello": f"{OSS_REPORT} step 00-hello",
    "buildInfo": f"{OSS_REPORT} step 00-buildInfo",
    "connectionStatus": f"{OSS_REPORT} step 10-connectionStatus-showPrivileges",
}

S = {s["step"]: s for s in raw["steps"]}
X = {s["step"]: s for s in extra["steps"]}

PLAIN = raw["cluster"]["plain_host"]
GLOBAL = raw["cluster"]["global_host"]
NODE = "fc-a472369cc681-000"
SUF = "mongocluster.cosmos.azure.com"


def out(step: str) -> str:
    return (S[step]["response"]["stdout"] or "").strip()


def dig_ttl(step: str) -> str:
    m = re.search(r"\s(\d+)\s+IN\s+SRV", out(step))
    return m.group(1) if m else "?"


def dig_status(text: str) -> str:
    m = re.search(r"status: (\w+)", text)
    return m.group(1) if m else "?"


def diff_keys(managed: dict, oss_doc: dict, volatile=("localTime", "connectionId", "operationTime")) -> dict:
    res = {"only_in_managed": [], "only_in_oss": [], "different_values": {}, "same_values": []}
    for k in sorted(set(managed) | set(oss_doc)):
        if k in volatile:
            if k not in oss_doc:
                res["only_in_managed"].append(k)
            elif k not in managed:
                res["only_in_oss"].append(k)
            continue
        if k not in oss_doc:
            res["only_in_managed"].append(k)
        elif k not in managed:
            res["only_in_oss"].append(k)
        elif managed[k] != oss_doc[k]:
            res["different_values"][k] = {"managed": managed[k], "oss_0.117": oss_doc[k]}
        else:
            res["same_values"].append(k)
    return res


hello_p = S["d-hello-plain"]["response"]
bi_p = S["d-buildInfo-plain"]["response"]
cs_p = S["d-connectionStatus-showPrivileges"]["response"]
hello_vs_oss = diff_keys(hello_p, OSS_HELLO)
bi_vs_oss = diff_keys(bi_p, OSS_BUILDINFO)
m_priv = cs_p["authInfo"]["authenticatedUserPrivileges"]
o_priv = OSS_CONNSTATUS["authInfo"]["authenticatedUserPrivileges"]
priv_cmp = {
    "managed_roles": cs_p["authInfo"]["authenticatedUserRoles"],
    "oss_roles": OSS_CONNSTATUS["authInfo"]["authenticatedUserRoles"],
    "managed_entry_count": len(m_priv),
    "oss_entry_count": len(o_priv),
    "any_db_actions_identical": m_priv[0]["actions"] == o_priv[0]["actions"] and m_priv[0]["resource"] == o_priv[0]["resource"],
    "cluster_actions_identical": m_priv[1]["actions"] == o_priv[1]["actions"] and m_priv[1]["resource"] == o_priv[1]["resource"],
    "managed_only_entries": m_priv[2:],
}
lcs = S["c-list-connection-strings"]["analysis"]

# ------------------------------------------------------------------ readings and OSS comparison
R: dict[str, tuple[str, str]] = {}  # step -> (reading, vs_open_source)
NA_DNS = "n/a"  # the local container is reached at localhost:10260; no SRV/DNS host forms exist there

R["a-plain-dig-srv-short"] = (f"The plain host's SRV record returns exactly one target, {NODE}.{SUF} on port 10260 (priority 0, weight 0).", NA_DNS)
R["a-plain-dig-srv-answer"] = (f"The same single SRV record, served with a TTL of {dig_ttl('a-plain-dig-srv-answer')} s from the resolver cache (authoritative TTL 30 s per dnspython).", NA_DNS)
R["a-plain-dnspython-srv"] = ("dnspython, the resolver PyMongo uses, gets the same single SRV record (TTL 30 s) and the SRV name is not itself a CNAME.", NA_DNS)
R["a-plain-dig-txt"] = ("No TXT record exists for the plain host, so SRV resolution injects no URI options (authSource, replicaSet or loadBalanced).", NA_DNS)
R["a-plain-dnspython-txt"] = ("dnspython raises NoAnswer for TXT, which PyMongo treats as 'no TXT options'.", NA_DNS)
R["a-plain-dig-host-A"] = (f"The plain cluster host has no A record (status NOERROR, ANSWER 0, SOA of zone {SUF}), so it exists only as an SRV name.", NA_DNS)
R["a-plain-getaddrinfo-host"] = ("The OS resolver cannot resolve the bare plain cluster host ([Errno 8]), which is why a non-SRV mongodb:// URI naming it fails.", NA_DNS)
R["a-plain-pymongo-parse_uri"] = (f"PyMongo's URI parser expands mongodb+srv://{PLAIN}/ to nodelist [{NODE}.{SUF}:10260] with only tls=true implied, and its SRV parent-domain check passes.", NA_DNS)
R["a-global-dig-srv-short"] = (f"The .global. host's SRV record returns exactly one target, {NODE}.global.{SUF} on port 10260: the node name keeps the .global. label.", NA_DNS)
R["a-global-dig-srv-answer"] = (f"The same single SRV record for the .global. host, TTL {dig_ttl('a-global-dig-srv-answer')} s.", NA_DNS)
R["a-global-dnspython-srv"] = ("dnspython gets the same single .global. SRV record (TTL 30 s); the SRV name is not a CNAME.", NA_DNS)
R["a-global-dig-txt"] = ("No TXT record exists for the .global. host either.", NA_DNS)
R["a-global-dnspython-txt"] = ("dnspython raises NoAnswer for the .global. host's TXT, so no URI options come from DNS.", NA_DNS)
R["a-global-dig-host-A"] = (f"The .global. cluster host has no A record (NOERROR, ANSWER 0, SOA {SUF}); it is in the same zone as the plain host and exists only as an SRV name.", NA_DNS)
R["a-global-getaddrinfo-host"] = ("The OS resolver cannot resolve the bare .global. cluster host ([Errno 8]).", NA_DNS)
R["a-global-pymongo-parse_uri"] = (f"PyMongo expands mongodb+srv://{GLOBAL}/ to nodelist [{NODE}.global.{SUF}:10260]; the target ends in global.{SUF}, so the SRV spec's shared-parent-domain check that PyMongo enforces passes.", NA_DNS)
R["a-plain-target-dig-cname"] = (f"The plain SRV target is a CNAME to {NODE}.privatelink.{SUF}.", NA_DNS)
R["a-plain-target-dig-a"] = ("Following the CNAME, the plain SRV target resolves to A 20.42.93.93.", NA_DNS)
R["a-plain-target-dig-a-chain"] = (f"Full chain: {NODE}.{SUF} CNAME {NODE}.privatelink.{SUF} A 20.42.93.93, both with TTL 30 s, although the cluster uses public access and has no private endpoint.", NA_DNS)
R["a-plain-target-dig-aaaa-chain"] = ("An AAAA query returns only the CNAME, so the node has no IPv6 address.", NA_DNS)
R["a-plain-target-getaddrinfo"] = ("The OS resolver returns 20.42.93.93 for the plain SRV target.", NA_DNS)
R["a-global-target-dig-cname"] = (f"The .global. SRV target is a CNAME to {NODE}.global.privatelink.{SUF}, a separate name in the privatelink namespace.", NA_DNS)
R["a-global-target-dig-a"] = ("Following the CNAME, the .global. SRV target resolves to the same A 20.42.93.93 as the plain target.", NA_DNS)
R["a-global-target-dig-a-chain"] = (f"Full chain: {NODE}.global.{SUF} CNAME {NODE}.global.privatelink.{SUF} A 20.42.93.93 (TTL 30 s).", NA_DNS)
R["a-global-target-dig-aaaa-chain"] = ("An AAAA query for the .global. target returns only the CNAME; no IPv6 address.", NA_DNS)
R["a-global-target-getaddrinfo"] = ("The OS resolver returns 20.42.93.93 for the .global. SRV target, the same IP as the plain target.", NA_DNS)
R["a-plain-target-tls-cert"] = (f"The node presents a TLSv1.3 certificate (CN ed484574ee80.{SUF}, issuer Microsoft TLS G2 RSA CA OCSP 04, valid Nov 25 2026 to Mar 5 2027) that verifies for the plain target and lists seven SANs: both node names, the plain cluster host, both Data API hosts, a .ro.global. node name and the CN.", "n/a")
R["a-global-target-tls-cert"] = (f"The same certificate (same serial) is served for the .global. target and verifies for that name; {GLOBAL} itself is not a SAN, which does not matter because clients connect only to SRV targets.", "n/a")
R["a-san2-dig-a-chain"] = ("The plain cluster host, although a certificate SAN, has no A or CNAME record.", NA_DNS)
R["a-san2-getaddrinfo"] = ("The OS resolver cannot resolve it ([Errno 8]).", NA_DNS)
R["a-san3-dig-a-chain"] = (f"The Data API host ddb-samples-shared.data.{SUF} is a CNAME to the plain node name and resolves to 20.42.93.93.", NA_DNS)
R["a-san3-getaddrinfo"] = ("The OS resolver returns 20.42.93.93 for the Data API host.", NA_DNS)
R["a-san4-dig-a-chain"] = (f"The Data API global host ddb-samples-shared.data.global.{SUF} is a CNAME to the self Data API host and then to the plain node, so on this single cluster both Data API host forms reach the same node.", NA_DNS)
R["a-san4-getaddrinfo"] = ("The OS resolver returns 20.42.93.93 for the Data API global host.", NA_DNS)
R["a-san6-dig-a-chain"] = (f"The node name {NODE}.ro.global.{SUF}, which appears only in the certificate, is a CNAME to {NODE}.ro.global.privatelink.{SUF} and resolves to 20.42.93.93.", NA_DNS)
R["a-san6-getaddrinfo"] = ("The OS resolver returns 20.42.93.93 for the .ro.global. node name.", NA_DNS)
R["a-san7-dig-a-chain"] = (f"The certificate CN ed484574ee80.{SUF} has no DNS record.", NA_DNS)
R["a-san7-getaddrinfo"] = ("The OS resolver cannot resolve the CN name ([Errno 8]).", NA_DNS)
R["a-guess1-dig-srv"] = (f"_mongodb._tcp.ddb-samples-shared.ro.global.{SUF} answers NOERROR with no SRV record, while an invented control name gives NXDOMAIN (dns_extra x2), so the name exists but publishes no SRV target on this cluster.", NA_DNS)
R["a-guess2-dig-srv"] = ("There is no SRV record under the Data API host name (NXDOMAIN); it is not a MongoDB SRV name.", NA_DNS)
R["a-guess3-dig-srv"] = ("There is no SRV record under the Data API global host name (NXDOMAIN).", NA_DNS)

NT = "not_tested_locally"
R["b-plain-construct"] = ("MongoClient(MANAGED_URI) constructs, resolving SRV in the constructor, and under simplefilter('always') records two CosmosDB UserWarnings: one at the caller's line and one at pymongo/synchronous/mongo_client.py:1916 (_resolve_srv).", NT)
R["b-plain-ping"] = ("ping through the plain host returns {ok: 1.0}.", NT)
R["b-plain-topology"] = (f"PyMongo classifies the deployment as a Sharded topology with one Mongos at {NODE}.{SUF}:10260 (wire versions 0 to 25), as msg 'isdbgrid' implies; the OSS gateway also answers 'isdbgrid'.", "same")
R["b-plain-connectionStatus"] = ("The connection is authenticated as factoryadmin@admin with role root; the reply has the same shape as on OSS 0.117, where the test user held readWriteAnyDatabase and clusterAdmin instead.", "different")
R["b-preclean-dropDatabase"] = ("dropDatabase on mt_hosts returns {ok: 1.0, dropped: 'mt_hosts'} even though run 1 had already dropped the database, so 'dropped' does not prove the database existed.", NT)
R["b-plain-insert"] = ("insert_one through the plain host is acknowledged with inserted_id 'via-plain'.", "same")
R["b-plain-find"] = ("find through the plain host returns the inserted document unchanged.", "same")
R["b-global-construct"] = ("MongoClient(MANAGED_GLOBAL_URI) constructs and records the same two CosmosDB UserWarnings as the plain form.", NT)
R["b-global-ping"] = ("ping through the .global. host returns {ok: 1.0}: the global form resolves and connects on a single-region cluster with no replica.", NT)
R["b-global-topology"] = (f"The driver is connected to the .global. node name {NODE}.global.{SUF}:10260 (Sharded, one Mongos, wire 0 to 25), not to the plain node name.", NT)
R["b-global-connectionStatus"] = ("SCRAM-SHA-256 authentication succeeds through the .global. host: factoryadmin@admin with role root.", NT)
R["b-global-insert"] = ("insert_one through the .global. host is acknowledged with inserted_id 'via-global'.", NT)
R["b-global-find"] = ("find through the .global. host returns the document written through it.", NT)
R["b-plain-cross-visibility"] = ("Through the plain host both documents are visible, including the one written through the .global. host.", NT)
R["b-global-cross-visibility"] = ("Through the .global. host both documents are visible, so the two forms reach the same cluster and data.", NT)
R["b-extra-nonsrv-plain-cluster-host-construct"] = ("A non-SRV client naming the bare plain cluster host constructs (no DNS lookup at construction) and records one CosmosDB UserWarning.", NT)
R["b-extra-nonsrv-plain-cluster-host-ping"] = ("ping fails after 10 s with ServerSelectionTimeoutError '[Errno 8] nodename nor servname provided, or not known': mongodb://<cluster>.mongocluster.cosmos.azure.com:10260 cannot work because the host has no A record.", NT)
R["b-extra-nonsrv-global-cluster-host-construct"] = ("A non-SRV client naming the bare .global. cluster host constructs and records one CosmosDB UserWarning.", NT)
R["b-extra-nonsrv-global-cluster-host-ping"] = ("ping fails the same way (ServerSelectionTimeoutError, [Errno 8]) for mongodb://<cluster>.global.mongocluster.cosmos.azure.com:10260.", NT)
R["b-extra-nonsrv-plain-srv-target-construct"] = ("A non-SRV client naming the plain SRV target node constructs and records one CosmosDB UserWarning.", NT)
R["b-extra-nonsrv-plain-srv-target-ping"] = (f"ping succeeds through mongodb://{NODE}.{SUF}:10260 with SCRAM-SHA-256 and TLS.", NT)
R["b-extra-nonsrv-plain-srv-target-topology"] = ("The non-SRV client also sees a Sharded topology with one Mongos at the node name.", NT)
R["b-extra-nonsrv-plain-srv-target-find"] = ("find through the plain node name sees both documents.", NT)
R["b-extra-nonsrv-global-srv-target-construct"] = ("A non-SRV client naming the .global. SRV target node constructs and records one CosmosDB UserWarning.", NT)
R["b-extra-nonsrv-global-srv-target-ping"] = (f"ping succeeds through mongodb://{NODE}.global.{SUF}:10260.", NT)
R["b-extra-nonsrv-global-srv-target-topology"] = ("Sharded topology with one Mongos at the .global. node name.", NT)
R["b-extra-nonsrv-global-srv-target-find"] = ("find through the .global. node name sees both documents.", NT)
R["b-extra-nonsrv-ro-global-san-host-construct"] = ("A non-SRV client naming the .ro.global. node name taken from the certificate constructs and records one CosmosDB UserWarning.", NT)
R["b-extra-nonsrv-ro-global-san-host-ping"] = (f"ping succeeds through mongodb://{NODE}.ro.global.{SUF}:10260, a host form that no service-issued connection string names and that DECISIONS topic 3 does not mention.", NT)
R["b-extra-nonsrv-ro-global-san-host-topology"] = ("Sharded topology with one Mongos at the .ro.global. node name.", NT)
R["b-extra-nonsrv-ro-global-san-host-hello"] = (f"hello through the .ro.global. name reports endpointName {NODE}.ro.global.{SUF}, isWritablePrimary true and readOnly false on this single cluster, so the name does not make the connection read-only here.", NT)
R["b-extra-nonsrv-ro-global-san-host-find"] = ("find through the .ro.global. node name sees both documents (no write was attempted through it).", NT)

R["c-help"] = ("--help confirms the parameter names --cluster-name and --resource-group/-g (or --ids, plus optional --subscription); the command is a 'list' with no body.", "n/a")
R["c-list-connection-strings"] = (
    "Returns {connectionStrings: [...]} with two entries in this order: name 'GlobalReadWrite' (description 'Global read-write cluster connection string', host "
    f"{GLOBAL}) and name 'Self' (description 'Cluster connection string', host {PLAIN}); both are mongodb+srv with the literal placeholder '<user>:<password>' "
    "and ?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000, so nothing needed masking.", "n/a")
R["c-show-default-connectionString"] = ("GET properties.connectionString returns the Self string on the plain host, identical to the 'Self' entry, not the GlobalReadWrite one.", "n/a")
R["c-show-topology-context"] = ("The cluster is a single Primary (replica.role 'Primary'), HA Disabled, shardCount 1, M30, PremiumSSDv2 128 GB, serverVersion 8.0, NativeAuth only, public network access Enabled, infrastructureVersion 2.0.", "n/a")
R["c-replica-list"] = ("replica list returns [], confirming there is no replica cluster.", "n/a")
R["c-rest-listConnectionStrings-2026-09-01"] = ("The REST listConnectionStrings action at api-version 2026-09-01 returns the identical two named entries (the CLI uses 2026-06-01).", "n/a")
R["c-rest-listConnectionStrings-2026-10-15-preview"] = ("The REST action at api-version 2026-10-15-preview returns the identical two named entries.", "n/a")

R["d-hello-plain"] = ("hello reports maxWireVersion 25, msg 'isdbgrid', isWritablePrimary true, readOnly false, saslSupportedMechs ['SCRAM-SHA-256'], internal.documentdb_versions ['2.2-1','2.3.0','12.1-1'], internal.kind 'azuredocumentdb', endpointName "
                      f"'{NODE}.{SUF}' and an operationTime timestamp; against OSS 0.117 the wire version, versions and kind differ and endpointName and operationTime are new, while every size limit and the SASL list are the same.", "different")
R["d-hello-global"] = (f"Through the .global. host hello is the same document except endpointName '{NODE}.global.{SUF}'.", "different")
R["d-hello-diff"] = ("The only non-volatile difference between the two host forms is endpointName, so hello tells a client which host form it connected through.", "n/a")
R["d-buildInfo-plain"] = ("buildInfo returns only version '8.0.0', versionArray [8,0,0,0], bits 64, maxBsonObjectSize 16777216 and ok: no gitVersion, modules, openssl or internal.documentdb_versions (those are in hello only); the key set equals OSS 0.117's, whose version is '7.0.0'.", "different")
R["d-buildInfo-global"] = ("buildInfo through the .global. host is identical.", "different")
R["d-buildInfo-diff"] = ("buildInfo has no difference between the two host forms.", "n/a")
R["d-isMaster-plain"] = ("Legacy isMaster returns the hello document with 'ismaster' in place of 'isWritablePrimary', including internal.documentdb_versions and endpointName.", NT)
R["d-isMaster-vs-hello-diff"] = ("Only the ismaster / isWritablePrimary key differs between isMaster and hello.", NT)
R["d-getCmdLineOpts"] = ("getCmdLineOpts is accepted and returns {argv: [], ok: 1.0} with no 'parsed' section, so it reveals no server options.", NT)
R["d-getParameter-star"] = ("getParameter '*' is allowed and returns exactly eight parameters: failpoint.disablePipelineOptimization false, featureFlagCollModIndexUnique false, featureFlagTimeseriesMetricIndexes false, internalDocumentSourceDensifyMaxMemoryBytes 104857600, internalQueryEnableSlotBasedExecutionEngine true, internalQueryForceClassicEngine true, internalQueryMaxAllowedDensifyDocs 500000, transactionLifetimeLimitSeconds 30.", NT)
R["d-getParameter-fcv"] = ("Reading featureCompatibilityVersion fails with {ok: 0.0, errmsg: 'No option found for get'} and no code, codeName or errorLabels, so PyMongo raises OperationFailure with code None.", NT)
R["d-getParameter-transactionLifetimeLimitSeconds"] = ("A parameter from the '*' list can be read on its own: transactionLifetimeLimitSeconds 30.", NT)
R["d-connectionStatus-showPrivileges"] = ("factoryadmin holds role root@admin and three privilege entries: the any-database and cluster action lists, identical to OSS 0.117's (the cluster list includes getCmdLineOpts and getParameter), plus an admin-database entry with user and role management actions (createUser, createRole, grantRole, viewUser and others).", "different")
R["d-warning-default-filters-plain"] = ("With Python's default warning filters PyMongo prints the CosmosDB UserWarning twice to stderr for the plain SRV URI, at warn_probe.py:15 (the MongoClient call) and at pymongo/synchronous/mongo_client.py:1916 (self._resolve_srv()), and the ping still succeeds.", NT)
R["d-warning-default-filters-global"] = ("For the .global. SRV URI the warning is printed twice as well (warn_probe.py:17 and mongo_client.py:1916).", NT)
R["d-warning-default-filters-nonsrv-target"] = ("For a non-SRV client naming the node host the warning is printed once (warn_probe.py:21).", NT)
R["z-dropDatabase"] = ("dropDatabase removes mt_hosts: {ok: 1.0, dropped: 'mt_hosts'}.", NT)
R["z-verify-listDatabases-filter"] = ("listDatabases with nameOnly and filter {name: 'mt_hosts'} returns databases [], so the test database is gone and the filter option is honoured.", NT)

RX = {
    "x1-ro-global-srv": (f"SRV for _mongodb._tcp.ddb-samples-shared.ro.global.{SUF}: NOERROR with ANSWER 0 (the name exists, no SRV record).", NA_DNS),
    "x2-control-ro-global-srv-nonexistent": ("The invented control name under .ro.global. returns NXDOMAIN, so x1's NOERROR means the cluster's .ro.global. SRV name really exists.", NA_DNS),
    "x3-ro-global-cluster-host-A": (f"ddb-samples-shared.ro.global.{SUF} A: NOERROR with ANSWER 0, the same shape as the plain and .global. cluster hosts.", NA_DNS),
    "x4-control-plain-srv-nonexistent": ("An invented plain-zone SRV name returns NXDOMAIN (control).", NA_DNS),
    "x5-control-global-srv-nonexistent": ("An invented .global. SRV name returns NXDOMAIN (control).", NA_DNS),
    "x6-privatelink-zone-SOA": (f"SOA for privatelink.{SUF} returns NOERROR with the parent {SUF} SOA in AUTHORITY, so the privatelink names are published inside the public {SUF} zone rather than a separately delegated zone.", NA_DNS),
    "x7-global-privatelink-name-A": (f"{NODE}.global.privatelink.{SUF} has its own A record (20.42.93.93).", NA_DNS),
    "x8-plain-privatelink-name-A": (f"{NODE}.privatelink.{SUF} has its own A record (20.42.93.93).", NA_DNS),
    "x9-global-cluster-host-in-privatelink-A": (f"ddb-samples-shared.global.privatelink.{SUF} is NXDOMAIN: only node names, not cluster names, have privatelink records.", NA_DNS),
    "x10-ro-global-srvname-TXT": ("The .ro.global. SRV name also has no TXT record (NOERROR, ANSWER 0).", NA_DNS),
    "x11-ro-global-srvname-CNAME": ("The .ro.global. SRV name has no CNAME (NOERROR, ANSWER 0).", NA_DNS),
    "x12-ro-global-srvname-A": ("The .ro.global. SRV name has no A record (NOERROR, ANSWER 0); with SRV, TXT, CNAME and A all empty it behaves like an empty record set (inference).", NA_DNS),
    "x13-ro-global-cluster-host-TXT": ("The .ro.global. cluster host has no TXT record (NOERROR, ANSWER 0).", NA_DNS),
    "x14-plain-srvname-TXT": ("The plain SRV name carries no TXT record either (NOERROR, ANSWER 0).", NA_DNS),
}

missing = [k for k in S if k not in R] + [k for k in X if k not in RX]
if missing:
    raise SystemExit(f"steps without a reading: {missing}")

steps = []
for s in raw["steps"]:
    rec = dict(s)
    rec["reading"], rec["vs_open_source"] = R[s["step"]]
    rec["run"] = "raw.json (run 2)"
    if s["step"] == "d-hello-plain":
        rec["oss_reference"] = OSS_REF["hello"]
        rec["oss_comparison"] = hello_vs_oss
    elif s["step"] == "d-hello-global":
        rec["oss_reference"] = OSS_REF["hello"]
    elif s["step"] in ("d-buildInfo-plain", "d-buildInfo-global"):
        rec["oss_reference"] = OSS_REF["buildInfo"]
        if s["step"] == "d-buildInfo-plain":
            rec["oss_comparison"] = bi_vs_oss
    elif s["step"] == "d-connectionStatus-showPrivileges":
        rec["oss_reference"] = OSS_REF["connectionStatus"]
        rec["oss_comparison"] = priv_cmp
    elif s["step"] in ("b-plain-connectionStatus", "b-global-connectionStatus"):
        rec["oss_reference"] = OSS_REF["connectionStatus"] + " (OSS user testadmin: roles readWriteAnyDatabase and clusterAdmin)"
    elif s["step"] == "b-plain-topology":
        rec["oss_reference"] = OSS_REF["hello"] + " (msg 'isdbgrid')"
    elif s["step"] in ("b-plain-insert", "b-plain-find"):
        rec["oss_reference"] = "every OSS engine test inserts and finds over mongodb://localhost:10260 (ENGINE-TESTS.md); the host forms themselves cannot be tested locally"
    steps.append(rec)
for s in extra["steps"]:
    rec = dict(s)
    rec["reading"], rec["vs_open_source"] = RX[s["step"]]
    rec["run"] = f"dns_extra.json ({extra['run_utc']})"
    steps.append(rec)

# run-1 consistency
r1 = {s["step"]: s for s in run1["steps"]}
consistency = {
    "run1": {"file": str(HERE / "raw_run1.json"), "started_utc": run1["started_utc"], "finished_utc": run1["finished_utc"], "steps": len(run1["steps"])},
    "run2": {"file": str(HERE / "raw.json"), "started_utc": raw["started_utc"], "finished_utc": raw["finished_utc"], "steps": len(raw["steps"])},
    "dns_extra": {"file": str(HERE / "dns_extra.json"), "run_utc": extra["run_utc"], "steps": len(extra["steps"])},
    "comparison": "Every step present in both runs gave the same result apart from volatile values (DNS TTLs and query ids, RTTs, connectionId, localTime, operationTime, document timestamps, topology ids in error text). Run 1 masked the scratchpad session GUID in file paths; run 2 leaves it readable because it is not an Azure identifier. Run 2 added the certificate-SAN DNS probes, the .ro.global. connection and getParameter transactionLifetimeLimitSeconds.",
}

conclusions = [
    {
        "question": "(a) What do the SRV records of the plain and .global. hosts return, and what do their targets point to?",
        "answer": (f"Each host has exactly one SRV record, port 10260, priority 0, weight 0, TTL 30 s: _mongodb._tcp.{PLAIN} -> {NODE}.{SUF}; _mongodb._tcp.{GLOBAL} -> {NODE}.global.{SUF} (the target keeps the .global. label). "
                   f"Targets: {NODE}.{SUF} CNAME {NODE}.privatelink.{SUF} A 20.42.93.93; {NODE}.global.{SUF} CNAME {NODE}.global.privatelink.{SUF} A 20.42.93.93; no AAAA. "
                   "Neither host has a TXT record (no options come from DNS) and neither cluster host has an A record (NOERROR/NODATA), so both exist only as SRV names. One SRV target matches one shard / one node."),
        "vs_open_source": "n/a",
        "confidence": "observed",
    },
    {
        "question": "(b) Does the .global. form resolve and authenticate on a single-region cluster with no replica?",
        "answer": ("Yes. With MANAGED_GLOBAL_URI PyMongo 4.20.1 resolved SRV to the .global. node name (its shared-parent-domain check passes), ping returned ok 1.0, connectionStatus showed factoryadmin@admin with role root (SCRAM-SHA-256), insert_one and find worked, and documents written through either form were visible through both. "
                   "The cluster was a single Primary: replica.role 'Primary', `replica list` [], HA Disabled, shardCount 1. hello through the two forms differs only in endpointName. This is the first observation of the .global. form in this project; DECISIONS topic 3 had it as documented-only."),
        "vs_open_source": "not_tested_locally",
        "confidence": "observed",
    },
    {
        "question": "(b, extra) Which non-SRV mongodb:// host forms work?",
        "answer": (f"mongodb://{PLAIN}:10260 and mongodb://{GLOBAL}:10260 fail after serverSelectionTimeoutMS with ServerSelectionTimeoutError '[Errno 8] nodename nor servname provided, or not known' because the cluster hosts have no A record. "
                   f"mongodb://{NODE}.{SUF}:10260, mongodb://{NODE}.global.{SUF}:10260 and mongodb://{NODE}.ro.global.{SUF}:10260 (a name found only in the TLS certificate) all authenticate and read. "
                   "So the cluster host must be used with mongodb+srv; a non-SRV string needs the SRV target, a node name (fc-<id>-000...) that appears in no service-issued connection string (Learn's Private Link page shows such names only as SRV targets)."),
        "vs_open_source": "not_tested_locally",
        "confidence": "observed",
    },
    {
        "question": "(c) What does az documentdb mongocluster list-connection-strings return, and does it include a global string?",
        "answer": ("Parameters (from --help): -g/--resource-group and --cluster-name (or --ids). Output: {\"connectionStrings\": [{\"connectionString\": \"mongodb+srv://<user>:<password>@ddb-samples-shared.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000\", \"description\": \"Global read-write cluster connection string\", \"name\": \"GlobalReadWrite\"}, "
                   "{\"connectionString\": \"mongodb+srv://<user>:<password>@ddb-samples-shared.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000\", \"description\": \"Cluster connection string\", \"name\": \"Self\"}]}. "
                   "Yes, it returns the global string, listed first, on a single cluster with no replica. The strings carry literal '<user>:<password>' placeholders, so there was nothing to mask. The REST action returns the same two entries at api-versions 2026-09-01 and 2026-10-15-preview (the CLI sends 2026-06-01). GET properties.connectionString is the Self (plain) string. "
                   "This settles DECISIONS topic 3 open item 1 for a single cluster with NativeAuth only: names are 'GlobalReadWrite' and 'Self'. The REST reference samples (one unnamed entry described 'default connection string') do not match the live response. Whether an Entra ID entry appears when MicrosoftEntraID auth is enabled, and what a replica's list holds, were not tested because both need configuration changes."),
        "vs_open_source": "n/a",
        "confidence": "observed",
    },
    {
        "question": "(c, implication) Is connectionStrings[0] the plain host?",
        "answer": ("No. Array position 0 is GlobalReadWrite (.global. host), while GET properties.connectionString gives the Self (plain) string. Code and agents should select an entry by name ('Self' or 'GlobalReadWrite'), not by index, and should not assume the 'default' string is in the list at position 0."),
        "vs_open_source": "n/a",
        "confidence": "observed",
    },
    {
        "question": "(d) What do hello and buildInfo report, and how does that compare with the open-source engine?",
        "answer": ("hello: isWritablePrimary true, msg 'isdbgrid', maxBsonObjectSize 16777216, maxMessageSizeBytes 48000000, maxWriteBatchSize 25000, logicalSessionTimeoutMinutes 30, minWireVersion 0, maxWireVersion 25, endpointName '<SRV target the client used>', readOnly false, saslSupportedMechs ['SCRAM-SHA-256'], internal {documentdb_versions ['2.2-1','2.3.0','12.1-1'], kind 'azuredocumentdb'}, ok 1.0, operationTime <Timestamp>. "
                   "buildInfo: {version '8.0.0', versionArray [8,0,0,0], bits 64, maxBsonObjectSize 16777216, ok 1.0}. buildInfo does NOT carry internal.documentdb_versions; only hello (and isMaster) do. "
                   "Against documentdb-local 0.117: hello differs in maxWireVersion (25 vs 21), documentdb_versions (3 entries vs ['0.117-0','0.117.0']), kind ('azuredocumentdb' vs ''), and adds endpointName and operationTime; all limits and the SASL list are the same. buildInfo has the same keys with version 8.0.0 vs 7.0.0. Both answer identically through the plain and .global. forms apart from endpointName."),
        "vs_open_source": "different",
        "confidence": "observed",
    },
    {
        "question": "(d) Are getCmdLineOpts and getParameter '*' allowed?",
        "answer": ("Both are allowed for the root admin user. getCmdLineOpts returns {argv: [], ok: 1.0} with no 'parsed' section. getParameter '*' returns eight parameters: failpoint.disablePipelineOptimization false, featureFlagCollModIndexUnique false, featureFlagTimeseriesMetricIndexes false, internalDocumentSourceDensifyMaxMemoryBytes 104857600, internalQueryEnableSlotBasedExecutionEngine true, internalQueryForceClassicEngine true, internalQueryMaxAllowedDensifyDocs 500000, transactionLifetimeLimitSeconds 30. "
                   "Single parameters from that list can be read (transactionLifetimeLimitSeconds -> 30), but {getParameter: 1, featureCompatibilityVersion: 1} fails with {ok: 0.0, errmsg: 'No option found for get'} with no code or codeName, so tools that read the FCV get an uncoded OperationFailure. "
                   "The OSS run only listed getCmdLineOpts and getParameter as cluster privileges; it never executed them."),
        "vs_open_source": "not_tested_locally",
        "confidence": "observed",
    },
    {
        "question": "(d) Does PyMongo print a CosmosDB warning, and when?",
        "answer": ("Yes. PyMongo 4.20.1 emits UserWarning 'You appear to be connected to a CosmosDB cluster. For more information regarding feature compatibility and support please visit https://www.mongodb.com/supportability/cosmosdb' for every host ending in '.cosmos.azure.com' (pymongo/mongo_client_shared.py _detect_external_db). "
                   "With default filters it is printed twice for each mongodb+srv URI, plain or .global.: once at the caller's MongoClient(...) line and once at pymongo/synchronous/mongo_client.py:1916 (self._resolve_srv()), because the SRV-resolved node names match too. A non-SRV client prints it once. Connections still work. "
                   "From the code (not exercised here), it is logged at INFO instead of warned when the 'pymongo.client' logger is enabled for INFO. It cannot fire against documentdb-local at localhost."),
        "vs_open_source": "not_tested_locally",
        "confidence": "observed",
    },
    {
        "question": "What names does the service's TLS certificate cover?",
        "answer": (f"One TLSv1.3 certificate (CN ed484574ee80.{SUF}, issuer Microsoft TLS G2 RSA CA OCSP 04, notBefore Nov 25 20:27:37 2026 GMT, notAfter Mar 5 19:27:37 2027 GMT) is served for both SRV targets, and it verifies against the default CA store. Its SANs are {NODE}.{SUF}, {PLAIN}, ddb-samples-shared.data.{SUF}, ddb-samples-shared.data.global.{SUF}, {NODE}.global.{SUF}, {NODE}.ro.global.{SUF} and ed484574ee80.{SUF}. "
                   f"{GLOBAL} is not a SAN, which is harmless because it has no A record and clients connect to the SRV target. The local container uses a self-signed certificate with tlsAllowInvalidCertificates, so there is nothing to compare."),
        "vs_open_source": "n/a",
        "confidence": "observed",
    },
    {
        "question": "Are there host forms beyond plain and .global.?",
        "answer": (f"Yes, by observation, but none appears in the service-issued connection strings or in the sources DECISIONS topic 3 cites. {NODE}.ro.global.{SUF} (a certificate SAN) CNAMEs to {NODE}.ro.global.privatelink.{SUF}, resolves to the same IP and accepts SCRAM connections; hello through it reports isWritablePrimary true and readOnly false on this single cluster. _mongodb._tcp.ddb-samples-shared.ro.global.{SUF} exists (NOERROR, while an invented name gives NXDOMAIN) but holds no SRV, TXT, CNAME or A record. "
                   f"The Data API hosts ddb-samples-shared.data.{SUF} and ddb-samples-shared.data.global.{SUF} both resolve (the global one is a CNAME to the self one, then to the node), so both forms on the Data API Learn page are real names; they have no MongoDB SRV record. "
                   "Inferred, not verified: '.ro.global.' is a read-only global endpoint that would point at a replica once one exists; behaviour with a replica needs a later test."),
        "vs_open_source": "n/a",
        "confidence": "observed",
    },
    {
        "question": "Does the public DNS chain support the private-endpoint best guess in DECISIONS topic 3 open item 2?",
        "answer": (f"It supports it but does not settle it. In public DNS the .global. node name has its own CNAME into the privatelink namespace ({NODE}.global.privatelink.{SUF}), separate from the plain node's {NODE}.privatelink.{SUF}, and the .ro.global. node has a third ({NODE}.ro.global.privatelink.{SUF}); cluster names have no privatelink record (NXDOMAIN). "
                   "So a private DNS zone named privatelink.mongocluster.cosmos.azure.com would need records '<node>', '<node>.global' (and '<node>.ro.global') for the .global. form to resolve privately, which matches the Microsoft Q&A nslookup. Resolution through a real private endpoint was not tested (none exists, and Phase 1 forbids configuration changes)."),
        "vs_open_source": "n/a",
        "confidence": "inferred",
    },
    {
        "question": "Do the service-issued connection strings agree with the retryWrites decision and the ALLOWED_HOSTS guidance?",
        "answer": ("Yes. Both service-issued strings (CLI, REST at three api-versions, GET) contain retrywrites=false and maxIdleTimeMS=120000, consistent with the 'retrywrites=false is required' decision. The SRV-resolved hosts are node names (fc-<id>-000[.global|.ro.global].mongocluster.cosmos.azure.com), not the cluster name in the URI. "
                   "This is the case the Mongoose tutorial describes for ALLOWED_HOSTS: '*.mongocluster.cosmos.azure.com' covers every observed node name, since the auth spec allows nested subdomains. OIDC itself was not exercised (NativeAuth only), so the ALLOWED_HOSTS part is inferred."),
        "vs_open_source": "n/a",
        "confidence": "inferred",
    },
]

report = {
    "test": "m-hosts",
    "goal": "Host forms and identity on the managed service",
    "database": "mt_hosts (created by the test, dropped at the end; listDatabases filter confirms it is gone)",
    "observed_on": "2026-11-25",
    "cluster": {
        "resource": "Microsoft.DocumentDB/mongoClusters ddb-samples-shared, resource group documentdb-samples-rg, eastus",
        "shape": "M30, shardCount 1, serverVersion 8.0, PremiumSSDv2 128 GB, HA Disabled, replica.role Primary with no replicas, NativeAuth only, public network access",
        "engine_identity": {"hello.maxWireVersion": 25, "hello.internal.documentdb_versions": ["2.2-1", "2.3.0", "12.1-1"],
                            "hello.internal.kind": "azuredocumentdb", "buildInfo.version": "8.0.0"},
    },
    "client": raw["environment"],
    "uris_as_used": raw["uris_as_used"],
    "scripts": {
        "runner": str(HERE / "run.sh"),
        "main": str(HERE / "run.py"),
        "warning_probe": str(HERE / "warn_probe.py"),
        "dns_supplement": str(HERE / "dns_extra.py"),
        "report_builder": str(HERE / "build_report.py"),
        "raw_outputs": [str(HERE / "raw.json"), str(HERE / "raw_run1.json"), str(HERE / "dns_extra.json")],
    },
    "runs": consistency,
    "open_source_reference": {
        "file": str(OSS_REPORT),
        "engine": "documentdb-local 0.117 (gateway buildInfo 7.0.0, hello.maxWireVersion 21), see findings/phase4/ENGINE-TESTS.md",
        "comparable_steps": ["d-hello-plain/global (OSS 00-hello)", "d-buildInfo-plain/global (OSS 00-buildInfo)",
                             "d-connectionStatus-showPrivileges (OSS 10-connectionStatus-showPrivileges)",
                             "b-plain-topology (OSS hello msg isdbgrid)", "basic insert/find"],
        "not_comparable": "DNS, SRV, TLS certificate, host forms, CLI/REST connection strings and the PyMongo CosmosDB warning have no local counterpart (localhost:10260, self-signed certificate).",
    },
    "masking": {"rule": raw["masking"]["rule"], "guids_masked_in_run2": raw["masking"]["guids_masked"],
                "notes": "No password, subscription id, tenant id, object id or e-mail address appears in any response; the service-issued connection strings contain the literal placeholder '<user>:<password>'. IP addresses shown are the service's public node IP."},
    "config_changes": [],
    "steps": steps,
    "conclusions": conclusions,
    "decisions_topic": "DECISIONS.md, 'Host forms' (SME topic 3): settled items confirmed by observation; open item 1 answered for a single cluster; open item 2 supported (inferred); open item 3 not in scope (needs a replica and a promotion).",
}
(HERE / "report.json").write_text(json.dumps(report, indent=2))
print(f"wrote {HERE / 'report.json'}: {len(steps)} steps, {len(conclusions)} conclusions")
