#!/usr/bin/env python
"""m-ttl analysis: builds report.json from raw.json (written by run_m_ttl.py). No server calls; re-runnable.

Compares every overlapping step with the open-source engine report
findings/phase4/engine-tests/ttl-semantics/report.json (documentdb-local 0.117, gateway 7.0.0).
"""
import json, os, re, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(HERE, "raw.json")
REPORT_PATH = os.path.join(HERE, "report.json")
OSS_REPORT = "/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/ttl-semantics/report.json"
TTL = 5
BIN = 0.1

_NODE_RE = re.compile(r"[A-Za-z0-9.-]+\.mongocluster\.cosmos\.azure\.com")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_GUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")


def mask(s):
    s = _NODE_RE.sub("<node-host>", s)
    s = _EMAIL_RE.sub("<email>", s)
    return _GUID_RE.sub("<guid>", s)


def P(s):
    return dt.datetime.fromisoformat(s) if s else None


def iso(d):
    return d.astimezone(dt.timezone.utc).isoformat(timespec="milliseconds") if d else None


def sec(a, b):
    return round((a - b).total_seconds(), 1)


def hms(d):
    return d.astimezone(dt.timezone.utc).strftime("%H:%M:%S.%f")[:-3]


def S(x):
    return dt.timedelta(seconds=x)


def som(d):
    """second of minute, 0.1 s resolution"""
    return round(d.second + d.microsecond / 1e6, 1)


def minute_boundaries(lo, hi):
    b = lo.replace(second=0, microsecond=0)
    if b < lo:
        b += dt.timedelta(minutes=1)
    out = []
    while b <= hi:
        out.append(b)
        b += dt.timedelta(minutes=1)
    return out


def untag(v):
    if isinstance(v, dict) and len(v) == 1:
        k = next(iter(v))
        if k == "$numberLong":
            return int(v[k])
        if k == "$date":
            return v[k]
    if isinstance(v, dict):
        return {k: untag(x) for k, x in v.items()}
    if isinstance(v, list):
        return [untag(x) for x in v]
    return v


def fmt_phase(ranges):
    if not ranges:
        return "no single second of the minute is consistent with every window"
    out = []
    for a, b in ranges:
        out.append(f"second {a:04.1f} to {b:04.1f}" + (" (across the minute boundary)" if b < a else ""))
    return "; ".join(out)


def wrapped_ranges(bins):
    n = len(bins)
    if all(bins):
        return [[0.0, 60.0]]
    if not any(bins):
        return []
    start = next(i for i in range(n) if not bins[i])  # begin scanning at a False bin so wrap is handled
    runs, cur = [], None
    for j in range(1, n + 1):
        i = (start + j) % n
        if bins[i] and cur is None:
            cur = [i, i]
        elif bins[i]:
            cur[1] = i
        elif cur is not None:
            runs.append(cur)
            cur = None
    if cur is not None:
        runs.append(cur)
    return [[round(a * BIN, 1), round(((b + 1) * BIN) % 60, 1)] for a, b in runs]


# ------------------------------------------------------------------ open-source reference
def load_oss():
    try:
        r = json.load(open(OSS_REPORT))
    except Exception as e:
        return {"error": repr(e), "by": {}}
    return {"report": r, "by": {s["step"]: s for s in r.get("steps", [])}}


OSS_STEP_FOR = {
    "buildInfo": "buildInfo",
    "create TTL index on exp (expireAfterSeconds 5)": "create TTL index on exp",
    "create second TTL index on exp2 (expireAfterSeconds 5)": "create second TTL index on another field",
    "create compound TTL index {a: 1, b: 1}": "create compound TTL index (two fields)",
    "create TTL index with non-numeric expireAfterSeconds (open-source parity)": "create TTL index with non-numeric expireAfterSeconds",
    "listIndexes after createIndexes attempts": "listIndexes after all createIndex attempts",
    "insert test documents": "insertMany test documents",
}
# documented open-source fates (report.json purgeTiming/purgeCadence)
OSS_FATE = {
    "past_date_60s": ("purged", "purged by the first top-of-minute pg_cron run after insert (20:08:00.005 run; gone 47.0-62.1 s after insert)"),
    "future_date_90s": ("purged", "purged by the first top-of-minute run after eligibility (20:09:00.004 run; gone 12.1-27.1 s after eligibility)"),
    "string_value": ("survived", "never purged within 4 min (242 s)"),
    "number_value": ("survived", "never purged within 4 min (242 s)"),
    "missing_field": ("survived", "never purged within 4 min (242 s)"),
    "null_value": ("survived", "never purged within 4 min (242 s)"),
    "array_of_dates": ("purged", "purged together with past_date_60s by the first run after insert (any expired element expires the document)"),
}
OSS_PROBE = ("purged", "open-source probes probe2/probe3 (already expired on insert) were purged by the first top-of-minute run after insert, 45-60 s after insert")


def cmp_step(name, m, oss):
    o = oss["by"].get(OSS_STEP_FOR.get(name, "\0"))
    if name in ("hello",):
        return "n/a (version context): open source was gateway wire version 21 advertising MongoDB 7.0.0 (documentdb-local 0.117); see buildInfo"
    if o is None:
        return "not tested on the open-source engine"
    if name == "buildInfo":
        mv, ov = (m.get("response") or {}).get("version"), (o.get("response") or {}).get("version")
        return f"different version: managed buildInfo.version {mv!r}, open source {ov!r}" if mv != ov else f"same version {mv!r}"
    if m["ok"] != o["ok"]:
        return f"different: managed {'accepted' if m['ok'] else 'rejected'} it, open source {'accepted' if o['ok'] else 'rejected'} it"
    if name == "listIndexes after createIndexes attempts" and m["ok"]:
        mi = {i["name"]: untag(i) for i in m["response"]["cursor"]["firstBatch"]}
        oi = {i["name"]: i for i in o["response"]}
        diffs = []
        for nm in sorted(set(mi) | set(oi)):
            a, b = mi.get(nm), oi.get(nm)
            if a is None or b is None:
                diffs.append(f"{nm} present only on {'open source' if a is None else 'managed'}")
                continue
            kd = [f"{k}: managed {a.get(k)!r} vs open source {b.get(k)!r}" for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
            if kd:
                diffs.append(f"{nm}: " + "; ".join(kd))
        return ("same: identical index documents for " + ", ".join(sorted(mi))) if not diffs else ("different: " + " | ".join(diffs))
    if not m["ok"]:
        mr, orr = m["response"], o["response"]
        same_code = mr.get("code") == orr.get("code") and mr.get("codeName") == orr.get("codeName")
        if same_code and mr.get("errmsg") == orr.get("errmsg"):
            return f"same: code {mr.get('code')} {mr.get('codeName')} with an identical errmsg; errorLabels managed {mr.get('errorLabels')} vs open source {orr.get('errorLabels')}"
        if same_code:
            return f"same code {mr.get('code')} {mr.get('codeName')}, different errmsg (open source: {orr.get('errmsg')!r})"
        return f"different: managed code {mr.get('code')} {mr.get('codeName')}, open source code {orr.get('code')} {orr.get('codeName')} ({orr.get('errmsg')!r})"
    if name.startswith("create ") and m["ok"]:
        return ("same: accepted on both; reply shape not comparable (managed reply is mongos-style {raw: {defaultShard: {numIndexesBefore, "
                "numIndexesAfter, createdCollectionAutomatically, ok}}, ok: 1}; the open-source run recorded only the create_index helper's return value "
                f"{o.get('response')!r})")
    return "same: accepted on both"


# ------------------------------------------------------------------ analysis
def analyze(raw):
    oss = load_oss()
    polls_all = raw.get("polls", [])
    polls = [p for p in polls_all if p.get("ok")]
    pidx = {p["poll"]: p for p in polls_all}
    offs = [c["offsetSecondsServerMinusClient"] for c in raw.get("clock", []) if c.get("offsetSecondsServerMinusClient") is not None]
    off = sum(offs) / len(offs) if offs else 0.0
    O = S(off)
    ins = raw["insert"]
    t_ins = P(ins["sentAt"])

    tracked = [dict(d, insertSentAt=ins["sentAt"], insertRepliedAt=ins["repliedAt"], origin="initial insert") for d in ins["documents"]]
    for p in polls_all:
        pe = p.get("probeInserted")
        if pe and pe.get("ok"):
            tracked.append({"_id": pe["_id"], "kind": pe["kind"], "ttlField": "exp", "valueType": "date", "value": {"$date": pe["exp"]},
                            "eligibleAt": pe["eligibleAt"], "expectedToExpire": True, "insertSentAt": pe["sentAt"],
                            "insertRepliedAt": pe["repliedAt"], "origin": f"probe inserted right after poll {p['poll']}"})

    docs = []
    for d in tracked:
        ins_s, ins_r = P(d["insertSentAt"]), P(d["insertRepliedAt"])
        r = {k: d[k] for k in ("_id", "kind", "ttlField", "valueType", "value", "expectedToExpire", "origin")}
        r.update({"insertSentAt": d["insertSentAt"], "insertRepliedAt": d["insertRepliedAt"], "eligibleAt": d["eligibleAt"]})
        elig_from = None
        if d["eligibleAt"]:
            elig_from = max(ins_s, P(d["eligibleAt"]) - O)  # server clock decides eligibility
            r["eligibleFromClient"] = iso(elig_from)
        after = [p for p in polls if P(p["sentAt"]) >= ins_r]
        first_gone = next((p for p in after if d["_id"] not in p["present"]), None)
        if first_gone is not None:
            seen = [p for p in after if P(p["sentAt"]) < P(first_gone["sentAt"])]
            last_present = seen[-1] if seen else None
            lo = P(last_present["sentAt"]) if last_present else ins_s
            hi = P(first_gone["repliedAt"])
            later = [p for p in after if P(p["sentAt"]) > P(first_gone["sentAt"])]
            r.update({"status": "purged",
                      "lastSeenPresent": ({"poll": last_present["poll"], "at": last_present["sentAt"]} if last_present
                                          else {"poll": None, "at": d["insertSentAt"], "note": "not polled while present; bracket starts at its insert"}),
                      "firstSeenGone": {"poll": first_gone["poll"], "at": first_gone["sentAt"], "repliedAt": first_gone["repliedAt"]},
                      "deletedBetweenClient": [iso(lo), iso(hi)],
                      "deletedBetweenServerClock": [iso(lo + O), iso(hi + O)],
                      "secondsAfterInsert": [sec(lo, ins_s), sec(hi, ins_s)],
                      "reappearedLater": any(d["_id"] in p["present"] for p in later)})
            if elig_from:
                # a document cannot be deleted before it is eligible, so a poll that saw it before eligibility gives a lower bound of 0
                r["secondsAfterEligible"] = [max(0.0, sec(lo, elig_from)), sec(hi, elig_from)]
                nb = minute_boundaries(elig_from + O, elig_from + O + S(61))[0]
                r["firstServerMinuteBoundaryAfterEligible"] = iso(nb)
                r["deletedAtFirstBoundaryAfterEligible"] = (lo + O) <= nb <= (hi + O)
                r["lagIfPurgedExactlyAtBoundary"] = sec(nb, elig_from + O)
        else:
            last = after[-1] if after else None
            r.update({"status": "survived", "lastSeenPresent": {"poll": last["poll"], "at": last["sentAt"]} if last else None,
                      "survivedSecondsAfterInsert": sec(P(last["sentAt"]), ins_s) if last else None})
            if elig_from and last:
                r["secondsEligibleButStillPresent"] = sec(P(last["sentAt"]), elig_from)
        # reading
        if r["status"] == "purged":
            lp, fg = r["lastSeenPresent"], r["firstSeenGone"]
            s = (f"{r['_id']} ({r['kind']}) was last seen " +
                 (f"at poll {lp['poll']} ({hms(P(lp['at']))} UTC)" if lp.get("poll") is not None else f"at its insert ({hms(P(lp['at']))} UTC)") +
                 f" and was gone at poll {fg['poll']} ({hms(P(fg['at']))} UTC), so it was deleted {r['secondsAfterInsert'][0]}-{r['secondsAfterInsert'][1]} s after insert")
            if "secondsAfterEligible" in r:
                s += f" and {r['secondsAfterEligible'][0]}-{r['secondsAfterEligible'][1]} s after it became eligible"
                s += (f"; the window contains the first server-clock minute boundary after eligibility ({hms(P(r['firstServerMinuteBoundaryAfterEligible']))})"
                      if r["deletedAtFirstBoundaryAfterEligible"] else "; the window does NOT contain the first minute boundary after eligibility")
            if not r["expectedToExpire"]:
                s += " (UNEXPECTED: the value is not a BSON Date)"
            if r.get("reappearedLater"):
                s += " (it reappeared in a later poll)"
            r["reading"] = s + "."
        else:
            s = f"{r['_id']} ({r['kind']}) was still present at the last poll"
            if r.get("survivedSecondsAfterInsert") is not None:
                s += f", {r['survivedSecondsAfterInsert']} s after insert"
            s += ", never purged" + (f" although it had been eligible for {r.get('secondsEligibleButStillPresent')} s (UNEXPECTED)" if r["expectedToExpire"] else "")
            r["reading"] = s + "."
        # open-source comparison
        if r["_id"] in OSS_FATE:
            fate, desc = OSS_FATE[r["_id"]]
        elif r["_id"].startswith("probe_"):
            fate, desc = OSS_PROBE
        else:
            fate, desc = None, None
        if fate is None:
            r["vs_open_source"] = "not tested on the open-source engine (the open-source run created exp2_ttl but inserted no document with exp2)"
        elif fate != r["status"]:
            r["vs_open_source"] = f"different: managed {r['status']}, open source {fate} ({desc})"
        elif fate == "purged" and r.get("deletedAtFirstBoundaryAfterEligible") is False:
            r["vs_open_source"] = f"same fate (purged) but different timing: not deleted at the first minute boundary after eligibility; open source {desc}"
        else:
            r["vs_open_source"] = f"same: {r['status']} on both" + (" and deleted at the first minute boundary after eligibility" if fate == "purged" else "") + f" (open source: {desc})"
        docs.append(r)

    # purge events grouped by the poll that first saw the documents gone
    events, by_poll = [], {}
    for r in docs:
        if r["status"] == "purged":
            by_poll.setdefault(r["firstSeenGone"]["poll"], []).append(r)
    for pn in sorted(by_poll):
        g, gone = by_poll[pn], pidx[pn]
        prev = [p for p in polls if p["poll"] < pn]
        prev = prev[-1] if prev else None
        tlo = max(P(x["deletedBetweenClient"][0]) for x in g)
        hi = P(gone["repliedAt"])
        bnds = minute_boundaries(tlo + O, hi + O)
        events.append({"firstSeenGonePoll": pn, "previousPoll": prev["poll"] if prev else None,
                       "pollWindowClient": [prev["sentAt"] if prev else None, gone["repliedAt"]],
                       "commonWindowServerClock": [iso(tlo + O), iso(hi + O)],
                       "commonWindowSecondOfMinute": [som(tlo + O), som(hi + O)],
                       "minuteBoundariesInside": [iso(b) for b in bnds], "documents": [x["_id"] for x in g]})
    intervals = []
    for a, b in zip(events, events[1:]):
        alo, ahi = P(a["commonWindowServerClock"][0]), P(a["commonWindowServerClock"][1])
        blo, bhi = P(b["commonWindowServerClock"][0]), P(b["commonWindowServerClock"][1])
        intervals.append({"from": a["firstSeenGonePoll"], "to": b["firstSeenGonePoll"], "secondsBetween": [max(0.0, sec(blo, ahi)), sec(bhi, alo)]})

    # every server-clock minute boundary inside a consecutive-poll window: were eligible docs purged by it?
    ticks = []
    for a, b in zip(polls, polls[1:]):
        lo, hi = P(a["sentAt"]), P(b["repliedAt"])
        for B in minute_boundaries(lo + O, hi + O):
            Bc = B - O
            cands = []
            for r in docs:
                if not r["expectedToExpire"] or not r.get("eligibleFromClient"):
                    continue
                existed = (r["_id"] in a["present"]) or (P(a["sentAt"]) <= P(r["insertSentAt"]) and P(r["insertRepliedAt"]) <= Bc - S(1))
                if existed and P(r["eligibleFromClient"]) <= Bc - S(1):
                    cands.append(r["_id"])
            gone = [x for x in cands if x not in b["present"]]
            still = [x for x in cands if x in b["present"]]
            ticks.append({"serverMinuteBoundary": iso(B), "betweenPolls": [a["poll"], b["poll"]],
                          "eligibleDocumentsBeforeBoundary": cands, "goneAtNextPoll": gone, "stillPresentAtNextPoll": still,
                          "verdict": ("no eligible documents" if not cands else "all eligible documents purged" if not still
                                      else "none purged" if not gone else "some purged")})

    # windows between consecutive polls that contain NO minute boundary: was anything deleted, and were eligible docs waiting?
    nob = []
    for a, b in zip(polls, polls[1:]):
        lo, hi = P(a["sentAt"]), P(b["repliedAt"])
        if minute_boundaries(lo + O, hi + O):
            continue
        waiting = []
        for r in docs:
            if not r["expectedToExpire"] or not r.get("eligibleFromClient"):
                continue
            existed = (r["_id"] in a["present"]) or (P(a["sentAt"]) <= P(r["insertSentAt"]) and P(r["insertRepliedAt"]) <= P(b["sentAt"]))
            if existed and P(r["eligibleFromClient"]) <= P(b["sentAt"]) - S(1) and r["_id"] in b["present"]:
                waiting.append(r["_id"])
        deleted = [x for x in a["present"] if x not in b["present"]]
        nob.append({"betweenPolls": [a["poll"], b["poll"]], "deletedInWindow": deleted, "eligibleButStillPresentAtNextPoll": waiting})

    # phase-of-minute intersection of all purge windows (assumes one fixed run time per minute)
    nbins = int(round(60 / BIN))
    acc = [True] * nbins
    for ev in events:
        lo_s, hi_s = P(ev["commonWindowServerClock"][0]), P(ev["commonWindowServerClock"][1])
        length = (hi_s - lo_s).total_seconds()
        if length >= 60:
            continue
        cover = [False] * nbins
        i0 = int((lo_s.second + lo_s.microsecond / 1e6) / BIN)
        for j in range(int(length / BIN) + 2):
            cover[(i0 + j) % nbins] = True
        acc = [x and y for x, y in zip(acc, cover)]

    # fine-grained probe
    fine, fine_res = raw.get("fine"), None
    if fine:
        smp = [s for s in fine.get("samples", []) if "present" in s]
        lastp, firstg = None, None
        for s_ in smp:
            if s_["present"]:
                lastp = s_
            else:
                firstg = s_
                break
        fins = P(fine["insertSentAt"])
        if firstg:
            lo = P(lastp["sentAt"]) if lastp else fins
            hi = P(firstg["repliedAt"])
            fine_res = {"status": "purged", "insertSentAt": fine["insertSentAt"], "samples": len(fine.get("samples", [])),
                        "lastSeenPresentSampleSentAt": lastp["sentAt"] if lastp else None, "firstSeenGoneSampleRepliedAt": firstg["repliedAt"],
                        "deletedBetweenServerClock": [iso(lo + O), iso(hi + O)], "windowSeconds": sec(hi, lo),
                        "secondOfMinuteServer": [som(lo + O), som(hi + O)],
                        "minuteBoundariesInside": [iso(b) for b in minute_boundaries(lo + O, hi + O)],
                        "secondsAfterInsert": [sec(lo, fins), sec(hi, fins)]}
            fine_res["reading"] = (f"fine_probe (already eligible on insert at {hms(fins)} UTC) was last seen at {hms(lo + O)} and gone by {hms(hi + O)} "
                                   f"server clock, a {fine_res['windowSeconds']} s window " +
                                   (f"that contains the minute boundary {hms(minute_boundaries(lo + O, hi + O)[0])}" if fine_res["minuteBoundariesInside"]
                                    else f"at second {fine_res['secondOfMinuteServer'][0]}-{fine_res['secondOfMinuteServer'][1]} of the minute (no minute boundary inside)") +
                                   f"; it was deleted {fine_res['secondsAfterInsert'][0]}-{fine_res['secondsAfterInsert'][1]} s after insert.")
            # tighten the phase intersection with the fine window too
            length = (hi - lo).total_seconds()
            if length < 60:
                cover = [False] * nbins
                i0 = int(((lo + O).second + (lo + O).microsecond / 1e6) / BIN)
                for j in range(int(length / BIN) + 2):
                    cover[(i0 + j) % nbins] = True
                acc = [x and y for x, y in zip(acc, cover)]
        else:
            fine_res = {"status": "not purged", "insertSentAt": fine["insertSentAt"], "samples": len(fine.get("samples", [])),
                        "reading": f"fine_probe was still present after {len(fine.get('samples', []))} one-second samples."}
    phase = wrapped_ranges(acc)

    purged_exp = [r for r in docs if r["expectedToExpire"] and r["status"] == "purged"]
    survived_exp = [r for r in docs if r["expectedToExpire"] and r["status"] == "survived"]
    purged_nondate = [r for r in docs if not r["expectedToExpire"] and r["status"] == "purged"]
    at_boundary = [r for r in purged_exp if r.get("deletedAtFirstBoundaryAfterEligible")]
    ev_with_b = [e for e in events if e["minuteBoundariesInside"]]
    tk = [t for t in ticks if t["eligibleDocumentsBeforeBoundary"]]
    tk_all = [t for t in tk if t["verdict"] == "all eligible documents purged"]
    lag = {}
    if purged_exp:
        lag = {"documents": len(purged_exp),
               "observedSecondsAfterEligible_minLowerBound": min(r["secondsAfterEligible"][0] for r in purged_exp),
               "observedSecondsAfterEligible_maxUpperBound": max(r["secondsAfterEligible"][1] for r in purged_exp),
               "perDocument": {r["_id"]: r["secondsAfterEligible"] for r in purged_exp},
               "lagByEligibilitySecondOfMinute": sorted({(round(som(P(r["eligibleFromClient"]) + O)), r["lagIfPurgedExactlyAtBoundary"]) for r in purged_exp}),
               "lagIfPurgedExactlyAtBoundary_min": min(r["lagIfPurgedExactlyAtBoundary"] for r in purged_exp),
               "lagIfPurgedExactlyAtBoundary_max": max(r["lagIfPurgedExactlyAtBoundary"] for r in purged_exp)}
    cadence = {"purgeEvents": len(events), "purgeEventsWhoseWindowContainsAMinuteBoundary": len(ev_with_b),
               "minuteBoundariesWithEligibleDocuments": len(tk), "ofWhichAllEligibleDocumentsPurged": len(tk_all),
               "expectedDocumentsPurged": len(purged_exp), "expectedDocumentsPurgedAtFirstBoundaryAfterEligible": len(at_boundary),
               "expectedDocumentsNeverPurged": [r["_id"] for r in survived_exp], "nonDateDocumentsPurged": [r["_id"] for r in purged_nondate],
               "intervalsBetweenConsecutivePurgeEvents": intervals,
               "phaseOfMinuteConsistentWithAllWindows_serverClock": phase,
               "windowsWithoutMinuteBoundary": len(nob),
               "windowsWithoutMinuteBoundaryWithAnyDeletion": len([w for w in nob if w["deletedInWindow"]]),
               "windowsWithoutMinuteBoundaryWhereEligibleDocumentsWaited": len([w for w in nob if w["eligibleButStillPresentAtNextPoll"]]),
               "noBoundaryWindows": nob,
               "serverMinusClientOffsetSecondsUsed": round(off, 3)}
    once_a_minute = (events and len(ev_with_b) == len(events) and tk and len(tk_all) == len(tk) and len(at_boundary) == len(purged_exp))
    if once_a_minute:
        cadence["reading"] = (f"Every one of the {len(events)} purge events fell in a poll window containing a server-clock minute boundary, every one of the "
                              f"{len(tk)} minute boundaries that had eligible documents purged all of them, and all {len(purged_exp)} purged Date documents "
                              f"were deleted at the first minute boundary after they became eligible; the combined windows put the run at "
                              f"{fmt_phase(phase)} of the server-clock minute, i.e. once a minute at the top of the minute.")
    else:
        cadence["reading"] = (f"{len(ev_with_b)} of {len(events)} purge events fell in a window containing a minute boundary; {len(tk_all)} of {len(tk)} boundaries with "
                              f"eligible documents purged all of them; {len(at_boundary)} of {len(purged_exp)} purged Date documents were deleted at the first "
                              f"boundary after eligibility; phase of the minute consistent with all windows: {fmt_phase(phase)}.")
    if lag:
        lag["reading"] = (f"Every purged Date document was gone within [{lag['observedSecondsAfterEligible_minLowerBound']}, {lag['observedSecondsAfterEligible_maxUpperBound']}] s "
                          f"of becoming eligible (union of the 15 s poll brackets, lower bounds clamped at 0)")
        if once_a_minute:
            lag["reading"] += (f"; since each was deleted at the first minute boundary after eligibility, its actual lag was the time left to that boundary, "
                               f"{lag['lagIfPurgedExactlyAtBoundary_min']}-{lag['lagIfPurgedExactlyAtBoundary_max']} s across the phases tested (0 to 60 s in general)")
        lag["reading"] += "."
    return docs, events, ticks, cadence, lag, fine_res, off, oss


def build_conclusions(raw, steps, docs, events, ticks, cadence, lag, fine_res):
    st = {x["step"]: x for x in steps}
    D = {d["_id"]: d for d in docs}
    li = st.get("listIndexes after createIndexes attempts", {})
    idx = {i["name"]: i for i in (li.get("response") or {}).get("cursor", {}).get("firstBatch", [])} if li.get("ok") else {}
    c1, c2 = st.get("create TTL index on exp (expireAfterSeconds 5)", {}), st.get("create second TTL index on exp2 (expireAfterSeconds 5)", {})
    cc, cb = st.get("create compound TTL index {a: 1, b: 1}", {}), st.get("create TTL index with non-numeric expireAfterSeconds (open-source parity)", {})
    survivors = [d["_id"] for d in docs if d["status"] == "survived"]
    out = []
    out.append({"question": "Is a single-field TTL index {exp: 1} with expireAfterSeconds 5 accepted, and how does listIndexes report it?",
                "answer": f"Accepted; createIndexes replied {json.dumps(c1.get('response'))}. listIndexes reports {json.dumps(idx.get('exp_ttl'))}, identical to the open-source index document (expireAfterSeconds is an int32 5, storageEngine.enableOrderedIndex true).",
                "vs_open_source": "same", "confidence": "observed"})
    out.append({"question": "Is a second single-field TTL index on another field (exp2) of the same collection accepted?",
                "answer": f"Accepted; createIndexes replied {json.dumps(c2.get('response'))} and listIndexes shows {json.dumps(idx.get('exp2_ttl'))}.",
                "vs_open_source": "same", "confidence": "observed"})
    e2 = D.get("exp2_past_date_60s", {})
    out.append({"question": "Does the second TTL index expire documents through its own field?",
                "answer": f"Yes: exp2_past_date_60s (exp2 = Date 60 s in the past, no exp field) was deleted between {e2.get('deletedBetweenServerClock')} (server clock), i.e. at the {e2.get('firstServerMinuteBoundaryAfterEligible')} boundary, in the same 15 s window as past_date_60s and array_of_dates from the exp_ttl index, so both TTL indexes on the collection are purged on the same per-minute schedule.",
                "vs_open_source": "not_tested_locally", "confidence": "observed"})
    r = cc.get("response") or {}
    out.append({"question": "Is a compound TTL index accepted?",
                "answer": f"No: code {r.get('code')} {r.get('codeName')}, errmsg {r.get('errmsg')!r}, no errorLabels field in the reply; byte-for-byte the same errmsg as the open-source engine.",
                "vs_open_source": "same", "confidence": "observed"})
    r = cb.get("response") or {}
    out.append({"question": "Is a non-numeric expireAfterSeconds accepted (open-source parity check)?",
                "answer": f"No: code {r.get('code')} {r.get('codeName')}, errmsg {r.get('errmsg')!r}, no errorLabels; identical to the open-source engine.",
                "vs_open_source": "same", "confidence": "observed"})
    out.append({"question": "Which exp values expire?",
                "answer": ("Only BSON Date values: past_date_60s, array_of_dates ([past Date, Date +1 day]; one expired element is enough) and future_date_90s (after it passed exp + 5 s) were purged; "
                           f"{', '.join(survivors)} (ISO string, int64 epoch milliseconds, missing field, null) were never purged in 300 s although a Date with the same instant would have been eligible for about 295 s."),
                "vs_open_source": "same", "confidence": "observed"})
    out.append({"question": "What is the TTL purge cadence on the managed service?",
                "answer": (f"Once a minute at the top of the server-clock minute. In 300 s of 15 s polling there were {cadence['purgeEvents']} purge events, each inside the poll window that straddles a minute boundary "
                           f"({', '.join(e['minuteBoundariesInside'][0][11:19] for e in events if e['minuteBoundariesInside'])} UTC, windows at second 52.2 to 07.2); every one of the {cadence['minuteBoundariesWithEligibleDocuments']} boundaries that had eligible documents deleted all of them; "
                           f"nothing was deleted in any of the {cadence['windowsWithoutMinuteBoundary']} poll windows that contain no minute boundary ({cadence['windowsWithoutMinuteBoundaryWithAnyDeletion']} with a deletion), although eligible documents were waiting in {cadence['windowsWithoutMinuteBoundaryWhereEligibleDocumentsWaited']} of them; "
                           f"consecutive events were {cadence['intervalsBetweenConsecutivePurgeEvents'][0]['secondsBetween'][0] if cadence['intervalsBetweenConsecutivePurgeEvents'] else '?'}-{cadence['intervalsBetweenConsecutivePurgeEvents'][0]['secondsBetween'][1] if cadence['intervalsBetweenConsecutivePurgeEvents'] else '?'} s apart (one per minute). "
                           f"The 1 s fine probe put the 21:11:00 run between {fine_res.get('deletedBetweenServerClock', ['?', '?'])[0][11:23]} and {fine_res.get('deletedBetweenServerClock', ['?', '?'])[1][11:23]} server clock. "
                           "No mid-minute deletion occurred: future_date_90s became eligible at about 21:06:42, was still present at the 21:06:52 poll and was gone only after the 21:07:00 boundary, so the release-note 'continuous for up to 60 seconds' behaviour did not delete newly eligible rows mid-minute on this idle collection (in the engine source that loop only continues while a run is still deleting rows)."),
                "vs_open_source": "same", "confidence": "observed"})
    out.append({"question": "What is the lag between eligibility (exp + expireAfterSeconds) and deletion?",
                "answer": (f"The time left until the next minute boundary, so 0 to just under 60 s on an idle cluster. Observed brackets after eligibility: {lag.get('observedSecondsAfterEligible_minLowerBound')} to {lag.get('observedSecondsAfterEligible_maxUpperBound')} s; "
                           f"all {lag.get('documents')} purged Date documents were deleted at the first boundary after eligibility, which means lags of {lag.get('lagIfPurgedExactlyAtBoundary_min')}-{lag.get('lagIfPurgedExactlyAtBoundary_max')} s for the phases tested "
                           "(" + ", ".join(f"eligible at second {sm:02d}: " + (f"{min(v)}-{max(v)}" if min(v) != max(v) else f"{v[0]}") + " s"
                                           for sm, v in sorted({sm: [l for s2, l in lag.get("lagByEligibilitySecondOfMinute", []) if s2 == sm]
                                                                for sm, _ in lag.get("lagByEligibilitySecondOfMinute", [])}.items()))
                           + f"); the fine probe, eligible on insert at second 07, was gone {fine_res.get('secondsAfterInsert')} s after insert. "
                           "DECISIONS topic 10 open item 5 can be closed for this tier: 'expiry happens at the first minute boundary after expireAfterSeconds has elapsed; allow up to about 60 s'. Behaviour with many expired rows was not tested."),
                "vs_open_source": "same", "confidence": "observed"})
    hs = st.get("hello", {}).get("response") or {}
    out.append({"question": "Side observation: what clock information does the managed gateway expose for timing TTL tests?",
                "answer": (f"hello.localTime is returned as BSON int64 epoch milliseconds ({json.dumps(hs.get('localTime'))}), not as a BSON Date as MongoDB documents it; server minus client offset was "
                           f"{[c.get('offsetSecondsServerMinusClient') for c in raw.get('clock', [])]} s by hello.localTime and "
                           f"{(st.get('$$NOW clock check', {}).get('response') or {}).get('offsetSecondsServerMinusClient')} s by $$NOW, so the Mac and server clocks agreed to about 10 ms."),
                "vs_open_source": "not_tested_locally", "confidence": "observed"})
    out.append({"question": "Side observation: what shape is the createIndexes reply on the managed service?",
                "answer": "mongos style: {\"raw\": {\"defaultShard\": {\"numIndexesBefore\": 1, \"numIndexesAfter\": 2, \"createdCollectionAutomatically\": true, \"ok\": 1}}, \"ok\": 1}; code that reads numIndexesAfter at the top level gets nothing. The open-source run recorded only the helper's return value, so the shapes were not compared.",
                "vs_open_source": "not_tested_locally", "confidence": "observed"})
    return out


def main():
    raw = json.load(open(RAW_PATH))
    docs, events, ticks, cadence, lag, fine_res, off, oss = analyze(raw)
    steps = []
    for s in raw["steps"]:
        s = dict(s)
        if s["step"].startswith("poll every 15 s"):
            s["response"] = {"polls": [{"poll": p["poll"], "sentAt": p["sentAt"], "repliedAt": p.get("repliedAt"),
                                        "secondsAfterInsert": p["secondsAfterInsert"], "ok": p.get("ok"), "count": p.get("count"),
                                        "present": p.get("present"), "error": p.get("error"),
                                        "probeInserted": ({"_id": p["probeInserted"]["_id"], "exp": p["probeInserted"]["exp"], "ok": p["probeInserted"]["ok"],
                                                           "reply": p["probeInserted"].get("reply"), "error": p["probeInserted"].get("error")}
                                                          if p.get("probeInserted") else None)} for p in raw["polls"]]}
            gone = [f"{r['_id']} {r['secondsAfterInsert'][0]}-{r['secondsAfterInsert'][1]} s after insert" for r in docs if r["status"] == "purged" and r["origin"] == "initial insert"]
            kept = [r["_id"] for r in docs if r["status"] == "survived"]
            bnd = [e["minuteBoundariesInside"][0][11:19] for e in events if e["minuteBoundariesInside"]]
            npurged = len([r for r in docs if r["status"] == "purged"])
            if cadence["reading"].startswith("Every one"):
                s["reading"] = (f"{len(raw['polls'])} polls 15 s apart over {raw['polls'][-1]['secondsAfterInsert']} s saw all {npurged} Date documents (initial and probes) vanish only in the "
                                f"{len(events)} poll windows straddling {', '.join(bnd)} UTC, each at the first minute boundary after it became eligible, and never in the "
                                f"{cadence['windowsWithoutMinuteBoundary']} windows without a boundary, while {', '.join(kept)} stayed for the whole run.")
            else:
                s["reading"] = (f"{len(raw['polls'])} polls 15 s apart over {raw['polls'][-1]['secondsAfterInsert']} s; gone: " + ("; ".join(gone) or "none")
                                + f"; kept: {kept}; " + cadence["reading"])
            s["vs_open_source"] = ("same mechanism: open source purged Date documents only, once a minute at the top of the minute (pg_cron '* * * * *'), "
                                   "lag 0 to ~60 s" if cadence["reading"].startswith("Every one") else
                                   "see cadence reading; open source purged Date documents once a minute at the top of the minute (pg_cron '* * * * *'), lag 0 to ~60 s")
        elif s["step"].startswith("supplement: fine-grained"):
            s["response"] = {"fine": raw.get("fine")}
            s["reading"] = (fine_res or {}).get("reading", "fine probe did not run")
            s["vs_open_source"] = (("same: the run happens at the top of the minute" if (fine_res or {}).get("minuteBoundariesInside") else "different: the run was not at the top of the minute")
                                   + "; the open-source 1 s probe could not run (container disk full), but its PostgreSQL log showed the pg_cron TTL job "
                                   "starting at hh:mm:00.003-00.016 every minute")
        elif s["step"] == "final listing of remaining documents":
            s["vs_open_source"] = ("same survivors as open source (string, number, missing, null)"
                                   if s["ok"] and {d["_id"] for d in s["response"]["cursor"]["firstBatch"]} >= {"string_value", "number_value", "missing_field", "null_value"}
                                   and not ({d["_id"] for d in s["response"]["cursor"]["firstBatch"]} & {"past_date_60s", "future_date_90s", "array_of_dates"})
                                   else "different from open source survivors (string, number, missing, null): see response")
        else:
            s["vs_open_source"] = cmp_step(s["step"], s, oss)
        steps.append(s)

    hello = next((s for s in raw["steps"] if s["step"] == "hello"), {}).get("response") or {}
    bi = next((s for s in raw["steps"] if s["step"] == "buildInfo"), {}).get("response") or {}
    report = {
        "test": "m-ttl",
        "target": ("Azure DocumentDB Microsoft.DocumentDB/mongoClusters 'ddb-samples-shared' (resource group documentdb-samples-rg, eastus, M30, one shard, "
                   "server version 8.0, Premium SSD v2, HA disabled, public access); connected with MANAGED_URI (plain host, mongodb+srv)"),
        "database": raw["database"], "collection": raw["collection"], "observedOn": "2026-11-25",
        "engine": {"helloMaxWireVersion": hello.get("maxWireVersion"), "helloInternal": hello.get("internal"), "helloMsg": hello.get("msg"),
                   "buildInfoVersion": bi.get("version"), "buildInfoVersionArray": bi.get("versionArray")},
        "client": {"python": raw["meta"].get("python"), "pymongo": raw["meta"].get("pymongo")},
        "method": ("TTL index exp_ttl {exp: 1} and exp2_ttl {exp2: 1}, both expireAfterSeconds 5, on mt_ttl.docs; compound and non-numeric attempts; "
                   "8 documents inserted at second :07 of a minute (client clock, server offset measured); one find of all _ids every 15 s on a fixed schedule "
                   "for 300 s with time.sleep; one already-expired probe inserted right after each of polls 1-15 so that every minute boundary had fresh eligible "
                   "documents at four phases of the minute; then a 1 s fine-grained probe; dropDatabase at the end. A deletion time is bracketed by the last poll "
                   "that saw the document (or its insert) and the reply of the first poll that did not."),
        "meta": raw["meta"],
        "clock": {"helloSamples": raw.get("clock"), "serverMinusClientOffsetSecondsUsed": round(off, 3),
                  "nowCheck": next((s.get("response") for s in raw["steps"] if s["step"] == "$$NOW clock check"), None)},
        "steps": steps,
        "documents": docs,
        "purgeEvents": events,
        "minuteBoundaryAccounting": ticks,
        "purgeCadence": cadence,
        "lag": lag,
        "finePurgeTiming": fine_res,
        "conclusions": build_conclusions(raw, steps, docs, events, ticks, cadence, lag, fine_res or {}),
        "configChanges": [],
        "abort": raw.get("abort"),
        "amendments": raw.get("amendments", []),
        "scripts": {"run": os.path.join(HERE, "run_m_ttl.py"), "analysis": os.path.join(HERE, "analyze.py"),
                    "amendment": os.path.join(HERE, "amend_raw.py"), "preflight": os.path.join(HERE, "preflight.py"),
                    "analysisSelfTest": os.path.join(HERE, "selftest_analyze.py")},
        "caveats": [
            "Observed on one M30 single-shard cluster with HA disabled and an almost empty collection on 2026-11-25 at engine versions "
            + str(hello.get("internal", {}).get("documentdb_versions")) + "; cadence under load (many expired rows, the 60 s continuous-batch budget) was not tested.",
            "15 s polling brackets each deletion to a 15 s window; the 1 s fine probe is a supplement to pin the run time.",
            "Client timestamps were converted to the server clock with the measured hello.localTime offset; hello.localTime is returned as int64 epoch milliseconds.",
        ],
        "rawFile": RAW_PATH,
        "polls": raw["polls"],
    }
    out = mask(json.dumps(report, indent=2, default=str))
    with open(REPORT_PATH, "w") as f:
        f.write(out)
    print(json.dumps({"purgeCadence": cadence, "lag": lag, "fine": fine_res,
                      "documents": {r["_id"]: [r["status"], r.get("secondsAfterInsert"), r.get("secondsAfterEligible"), r.get("deletedAtFirstBoundaryAfterEligible")] for r in docs},
                      "events": [[e["firstSeenGonePoll"], e["commonWindowServerClock"], e["documents"]] for e in events]}, indent=1, default=str))


if __name__ == "__main__":
    main()
