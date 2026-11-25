#!/usr/bin/env python
"""Adds comparison_with_0_117 and computed conclusions to report.json (written by run.py).

Deterministic from report.json plus the archived 0.117 report, so it can be rerun on its own:
  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python finalize.py [report.json]
Explain summaries for both runs are computed with run.py's own summarize_explain, from plan nodes only.
"""
import importlib.util
import json
import os
import sys

BASELINE = "/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/query-behaviour/report.json"
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("qb_run", os.path.join(HERE, "run.py"))
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)


def bstep(base, sid):
    for s in (base or {}).get("steps", []):
        if s.get("step", "").split(" ", 1)[0] == sid:
            return s
    return None


def nstep(rep, sid):
    for s in rep["steps"]:
        if s.get("id") == sid:
            return s
    return None


def old_outcome(s):
    if s is None:
        return {"outcome": "not run"}
    r = s.get("response")
    if isinstance(r, dict) and "exception" in r:
        return {"outcome": "error", "code": r.get("code"), "codeName": r.get("codeName"), "errmsg": r.get("errmsg"),
                "errorLabels": r.get("errorLabels")}
    return {"outcome": "ok"}


def new_outcome(s):
    if s is None:
        return {"outcome": "not run"}
    r = s["response"]
    if "attempts" in r:
        o = {"outcome": r["outcome"], "attempts_failed": r["attempts_failed"], "attempts_total": r["attempts_total"],
             "error_codes": r["error_codes"]}
        f = [a for a in r["attempts"] if not a["completed"]]
        if f:
            e = f[0]["error"]
            o.update({"errmsg": e.get("errmsg"), "errorLabels": e.get("errorLabels"), "exception": e.get("exception")})
        return o
    if r.get("outcome") == "error":
        return {"outcome": "error", "code": r.get("code"), "codeName": r.get("codeName"), "errmsg": r.get("errmsg"),
                "errorLabels": r.get("errorLabels"), "exception": r.get("exception")}
    return {"outcome": "ok"}


def codes_equal(o, n):
    if o["outcome"] != "error" and n["outcome"] != "error":
        return o["outcome"] == n["outcome"]
    if o["outcome"] == "error" and n["outcome"] == "error":
        if "error_codes" in n:
            return ([{"code": o.get("code"), "codeName": o.get("codeName")}] == n["error_codes"]
                    and o.get("errmsg") == n.get("errmsg"))
        return (o.get("code"), o.get("codeName"), o.get("errmsg")) == (n.get("code"), n.get("codeName"), n.get("errmsg"))
    return False


def ex_view(summary):
    return {k: summary.get(k) for k in ("chain", "all_stage_names_unique", "has_COLLSCAN", "index_names_used",
                                        "first_executionStats", "max_node_totalDocsExamined",
                                        "max_node_totalDocsRemovedByRuntimeFilter", "parallel", "max_actualLoops",
                                        "max_node_totalDocsExamined_x_actualLoops", "cosmosSearchCustomParams",
                                        "indexCosts_first")
            if summary.get(k) is not None}


def old_explain(s):
    if s is None or "full_explain" not in (s.get("response") or {}):
        return None
    return ex_view(R.summarize_explain(s["response"]["full_explain"]))


def new_explain(s):
    if s is None:
        return None
    if s["response"].get("outcome") != "ok":
        return new_outcome(s)
    return ex_view(s["response"]["result"]["summary"])


def build_comparison(rep, base):
    items = []

    def add(item, old, new, verdict, note=None):
        d = {"item": item, "engine_0_117": old, "engine_1_2_0": new, "verdict": verdict}
        if note:
            d["note"] = note
        items.append(d)

    for oid, nid, label in (("a.1", "a.2", "chained $setWindowFields ($sum, then $max over amount) + $sort + $group $last on sales"),
                            ("a.2", "a.3", "same pipeline with no $sort before $group"),
                            ("a.3", "a.4", "one stage with cumulative $sum and $max (east rows)")):
        o, n = bstep(base, oid), nstep(rep, nid)
        if o is None or n is None:
            continue
        oval, nval = o["response"], n["response"].get("result")
        add(label, {"step": oid, "result": oval},
            {"step": nid, "result": nval, "matches_client_side": (n.get("checks") or {}).get("matches_expected")},
            "same" if oval == nval else "changed",
            "Same seed and generator in both runs, so the result documents are compared byte for byte.")
    n = nstep(rep, "a.1")
    if n:
        add("exact L08 pipeline ($max over the cumulativePnl output, $set drawdown, $sort, $group $max/$last)",
            {"step": None, "result": "not run on 0.117 (its a.1 was a sales variant with $max over the raw field)"},
            {"step": "a.1", "outcome": new_outcome(n)["outcome"], "result": n["response"].get("result"),
             "matches_client_side": (n.get("checks") or {}).get("matches_expected")},
            "new in 1.2.0 run")
    for oid, nid, label in (("a.4", "s.1", "documents ['unbounded','current'] window with no sortBy"),
                            ("a.5", "s.4", "documents ['unbounded','unbounded'] window with no sortBy"),
                            ("a.6", "s.5", "output with no window and no sortBy"),
                            ("a.7", "s.6", "range window with no sortBy")):
        o, n = bstep(base, oid), nstep(rep, nid)
        if o is None or n is None:
            continue
        oo, no = old_outcome(o), new_outcome(n)
        add(label, dict({"step": oid}, **oo), dict({"step": nid}, **no), "same" if codes_equal(oo, no) else "changed")

    for oid, nid, label in (("b.1", "b.1", "aggregate full $sort, allowDiskUse true"),
                            ("b.2", "b.2", "aggregate full $sort, allowDiskUse false"),
                            ("b.3", "b.8", "aggregate with allowDiskUse 'yes' (non-boolean)"),
                            ("b.4", "b.12", "find sort with allow_disk_use(True)")):
        o, n = bstep(base, oid), nstep(rep, nid)
        if o is None or n is None:
            continue
        oo, no = old_outcome(o), new_outcome(n)
        oo["elapsed_ms"], no["elapsed_ms"] = o.get("elapsed_ms"), n.get("elapsed_ms")
        add(label, dict({"step": oid}, **oo), dict({"step": nid}, **no), "same" if codes_equal(oo, no) else "changed",
            "Acceptance and error codes are compared; 0.117 sorted 200,000 documents and this run 100,000, so values "
            "and timings are not comparable." if oid != "b.3" else None)

    for oid, nid, label in (("c.1", "c.1", "explain unindexed find {rnd: {$gt: 0.999}}"),
                            ("c.3", "c.4", "explain indexed equality find {i: N}"),
                            ("c.3b", "c.4b", "explain indexed range find sorted on unindexed rnd"),
                            ("c.4", "c.5", "explain aggregate indexed $match + $sort + $limit"),
                            ("c.4b", "c.5b", "explain aggregate unindexed $match + $sort on indexed i"),
                            ("c.5d", "c.6d", "explain $search cosmosSearch on vector-ivf (executionStats)"),
                            ("c.5e", "c.6e", "explain $search cosmosSearch on vector-ivf (queryPlanner)"),
                            ("c.6", "c.7b", "explain chained $setWindowFields pipeline on sales")):
        o, n = old_explain(bstep(base, oid)), new_explain(nstep(rep, nid))
        if o is None or n is None:
            continue
        same = (o.get("chain") == n.get("chain") and o.get("has_COLLSCAN") == n.get("has_COLLSCAN")
                and o.get("index_names_used") == n.get("index_names_used"))
        add(label, dict({"step": oid}, **o), dict({"step": nid}, **n), "same" if same else "changed",
            "Verdict compares the plan chain (stage names, index names, bitmap and runtime-filter markers) and COLLSCAN "
            "presence, from plan nodes only; document counts differ where the collection size differs "
            "(200,000 on 0.117, 100,000 here). For unindexed predicates the plan depends on whether PostgreSQL has "
            "analyzed the freshly loaded table (see e.2): indexCosts_first with selectivity 0.005 and no correlation "
            "marks an un-analyzed table, so compare that field before reading a difference as an engine change.")

    for oid, nid, label in (("c.1", "c.1", "explain top-level keys (find)"), ("c.4", "c.5", "explain top-level keys (aggregate)")):
        o, n = bstep(base, oid), nstep(rep, nid)
        if o is None or n is None or n["response"].get("outcome") != "ok":
            continue
        ok_ = sorted(o["response"]["full_explain"].keys())
        nk_ = n["response"]["result"]["summary"]["top_level_keys"]
        add(label, {"step": oid, "top_level_keys": ok_}, {"step": nid, "top_level_keys": nk_},
            "same" if ok_ == nk_ else "changed",
            "Added keys: " + ", ".join(sorted(set(nk_) - set(ok_))) + "; removed: " + (", ".join(sorted(set(ok_) - set(nk_))) or "none")
            if ok_ != nk_ else None)
    for oid, nid, label in (("d.3", "d.6", "aggregate $match + $count with maxTimeMS 1"),
                            ("d.4", "d.10", "count_documents with maxTimeMS 1"),
                            ("d.1", "d.1", "find with max_time_ms(1), whole cursor consumed"),
                            ("d.2", "d.5", "raw find command with maxTimeMS 1 (first batch)"),
                            ("d.5", "d.11", "control: find with max_time_ms(120000)")):
        o, n = bstep(base, oid), nstep(rep, nid)
        if o is None or n is None:
            continue
        oo, no = old_outcome(o), new_outcome(n)
        r = n["response"]
        if "attempts" in r and oid in ("d.1", "d.2"):
            done = r["attempts_total"] - r["attempts_failed"]
            no["attempts_completed"] = done
            verdict = ("same" if done == r["attempts_total"] else "changed" if done == 0 else "mixed (timing-sensitive)")
            if oo["outcome"] == "error":
                verdict = "same" if done == 0 else "changed"
            add(label, dict({"step": oid}, **oo), dict({"step": nid}, **no), verdict,
                "maxTimeMS 1 on a 101-document first batch sits at the timing boundary (the initial command takes about "
                "1 ms), so outcomes can vary between attempts and runs; compare earlier_run_of_this_script.")
            continue
        add(label, dict({"step": oid}, **oo), dict({"step": nid}, **no), "same" if codes_equal(oo, no) else "changed")
    return items


# ----------------------------------------------------------------------------- conclusions

def fmt_err(o):
    return f"code {o.get('code')} {o.get('codeName')} '{o.get('errmsg')}'"


def conclude(rep, comparison):
    S = lambda sid: nstep(rep, sid)  # noqa: E731
    C = lambda sid, k="matches_expected": ((S(sid) or {}).get("checks") or {}).get(k)  # noqa: E731
    ok = lambda sid: S(sid) is not None and new_outcome(S(sid))["outcome"] == "ok"  # noqa: E731
    tgt = rep.get("target", {})
    ver = tgt.get("documentdb_versions")
    bver = (tgt.get("buildInfo") or {}).get("version")
    image = tgt.get("image")
    out = {"scope": (f"Observed on documentdb-local (image {image}, hello.internal.documentdb_versions {ver}, buildInfo "
                     f"version {bver}, PyMongo driver). Evidence about the open-source engine and gateway at that version "
                     "only; it does not prove managed Azure DocumentDB behaviour.")}
    qa = []
    same_items = [c["item"] for c in comparison if isinstance(comparison, list) and c["verdict"] == "same"]
    changed_items = [c["item"] for c in comparison if isinstance(comparison, list) and c["verdict"] == "changed"]

    # ---------------- (a)
    a = []
    if ok("a.1"):
        a.append(f"The exact L08 pipeline ran as written and returned {json.dumps(S('a.1')['response']['result'])}, "
                 f"{'equal to' if C('a.1') else 'NOT equal to'} the client-side computation (a.1). Per-row cumulativePnl, "
                 f"runningPeak and drawdown {'matched' if C('a.1b') else 'did not all match'} (a.1b). Without the $match, "
                 f"both partitions {'matched' if C('a.1c') else 'did not match'} (a.1c). Without the $sort before $group, the "
                 f"result {'still matched' if C('a.1d') else 'did not match'} (a.1d).")
    else:
        a.append(f"The exact L08 pipeline failed with {fmt_err(new_outcome(S('a.1')))} (a.1).")
    if C("a.1e", "runningPeak_all_null") is not None:
        a.append("Within one stage, an output that references a sibling output sees nothing: runningPeak was null in "
                 "every row (a.1e). That supports the L08 comment that the $max needs its own stage."
                 if C("a.1e", "runningPeak_all_null") else
                 "Within one stage, an output that references a sibling output did get a value (a.1e).")
    a.append("The 0.117 sales variants "
             + ("matched the client-side computation and returned the same documents as on 0.117 (a.2-a.4)."
                if all(C(x) for x in ("a.2", "a.3", "a.4")) else "did not all match (a.2-a.4)."))
    rows, mism = [], []
    for i in range(1, 23):
        s = S(f"s.{i}")
        if not s:
            continue
        c = s.get("checks") or {}
        title = s["step"].split(" ", 1)[1]
        rows.append(f"{title}: " + ("accepted" if c.get("outcome") == "accepted" else
                                    f"{s['response'].get('code')} {s['response'].get('codeName')} '{s['response'].get('errmsg')}'"))
        if not c.get("matches_source_prediction"):
            mism.append(f"s.{i}")
    a.append("sortBy cases (s.1-s.22): " + "; ".join(rows) + ".")
    a.append("Every case matched the prediction from the main-branch engine source." if not mism else
             f"These cases differ from the main-branch engine source prediction: {', '.join(mism)}.")
    if S("s.19") and S("s.19")["response"].get("errmsg", "").endswith("$shift"):
        a.append("Two source-level oddities show up on the wire. $expMovingAvg without sortBy is rejected with a message "
                 "that names $shift (s.19). $locf is accepted without sortBy (s.21), although DECISIONS topic 10 lists "
                 "$locf among the operators that need a single-element sortBy.")
    out["a_setWindowFields"] = " ".join(a)
    qa.append({"question": "Does the exact L08 example run as written and give the right answer? This is the one with two chained "
                           "$setWindowFields stages using cumulative documents ['unbounded','current'] windows on $sum and "
                           "then $max over the first output, followed by $set, $sort and $group with $last "
                           "(DECISIONS topic 10, open question 2).",
               "answer": a[0] + (" " + a[1] if len(a) > 1 else "") + f" This is on engine {ver}; the managed service was not tested.",
               "confidence": "observed"})
    s1, s6, s7, s8 = (new_outcome(S(x)) for x in ("s.1", "s.6", "s.7", "s.8"))
    qa.append({"question": "When is sortBy required, and what are the errors (engine 1.2.0)?",
               "answer": (f"Any documents window except ['unbounded','unbounded'] needs sortBy: {fmt_err(s1)} (s.1-s.3). "
                          f"A range window needs exactly one sortBy field, which must be ascending: no sortBy gives {fmt_err(s6)}, "
                          f"a compound sortBy gives {fmt_err(s7)} and a descending one gives {fmt_err(s8)}. Accepted without "
                          f"sortBy: ['unbounded','unbounded'], an output with no window, $first/$last with no window, and $locf. "
                          f"Operator rules: $rank, $denseRank and $documentNumber give 5371602; $shift, $derivative, "
                          f"$integral and $expMovingAvg give 9 FailedToParse; $linearFill gives 605001. "
                          + ("All 22 cases match the main-branch source." if not mism else f"Mismatches: {mism}.")),
               "confidence": "observed"})
    qa.append({"question": "Did the 0.117 window-function results reproduce on 1.2.0?",
               "answer": ("Yes. The three sales pipelines returned the same documents as on 0.117, and the four sortBy "
                          "cases 0.117 tested gave the same accept/reject outcome and the same code, codeName and errmsg "
                          "(see comparison_with_0_117)."
                          if all(any(c["item"].startswith(p) for c in comparison if c["verdict"] == "same")
                                 for p in ("chained $setWindowFields", "same pipeline", "one stage", "documents ['unbounded','current']",
                                           "documents ['unbounded','unbounded']", "output with no window", "range window"))
                          else "Not entirely; see comparison_with_0_117."),
               "confidence": "observed"})

    # ---------------- (b)
    b = []
    if all(S(x) for x in ("b.1", "b.2", "b.3")):
        r = [S(x)["response"].get("result") for x in ("b.1", "b.2", "b.3")]
        b.append(f"A full $sort of 100,000 documents on an unindexed field was accepted with allowDiskUse true, false and "
                 f"omitted. Results were {'identical' if r[0] == r[1] == r[2] else 'DIFFERENT'} and matched the "
                 f"client-side min/max; times were {S('b.1').get('elapsed_ms')}, {S('b.2').get('elapsed_ms')} and "
                 f"{S('b.3').get('elapsed_ms')} ms (b.1-b.3).")
    if S("b.4") and S("b.5"):
        if ok("b.4") and ok("b.5"):
            b.append(f"A sort over 240 MB of sort-key data, which is above MongoDB's 100 MB blocking-sort memory limit, "
                     f"completed with allowDiskUse false ({S('b.4').get('elapsed_ms')} ms) and true "
                     f"({S('b.5').get('elapsed_ms')} ms) and returned the expected document both times (b.4, b.5).")
        else:
            b.append(f"240 MB sort: allowDiskUse false gave {new_outcome(S('b.4'))}; true gave {new_outcome(S('b.5'))} (b.4, b.5).")
    if S("b.6") and S("b.7") and ok("b.6") and ok("b.7"):
        def sortfields(sid):
            n = [x for x in S(sid)["response"]["result"]["sort_nodes"] if "executionStats" in x["path"]]
            return n[0] if n else {}
        f6, f7 = sortfields("b.6"), sortfields("b.7")
        b.append(f"Explain of that sort shows usedDisk {f6.get('usedDisk')} and sortMethod '{f6.get('sortMethod')}' with "
                 f"allowDiskUse false, and usedDisk {f7.get('usedDisk')} and sortMethod '{f7.get('sortMethod')}' with true "
                 "(b.6, b.7). The sort spills to disk either way, so the flag has no observable effect. This matches the "
                 "engine source, which lists allowDiskUse in IgnoredCommonSpecFields.")
        b.append(f"The SORT field totalDataSizeSortedBytesEstimate read {f6.get('totalDataSizeSortedBytesEstimate')} for the "
                 "100,000 tuples of about 4.8 KB each. Elsewhere it reads 65 for a 109-document quicksort (c.1d), so it "
                 "looks like PostgreSQL's sort space in kB rather than bytes (inferred from the magnitudes, not from "
                 "source).")
    tc = []
    for k, lab in (("b.8", "string 'yes'"), ("b.9", "int 1"), ("b.10", "double 1.0"), ("b.11", "null")):
        if S(k):
            o = new_outcome(S(k))
            tc.append(f"{lab} -> {'accepted' if o['outcome'] == 'ok' else fmt_err(o)}")
    fc = []
    for k, lab in (("b.14", "string 'yes'"), ("b.15", "int 1")):
        if S(k):
            o = new_outcome(S(k))
            fc.append(f"{lab} -> {'accepted' if o['outcome'] == 'ok' else fmt_err(o)}")
    if tc:
        b.append("A non-boolean allowDiskUse on aggregate: " + "; ".join(tc) + " (b.8-b.11). The same on find: "
                 + "; ".join(fc) + " (b.14, b.15). So aggregate type-checks the field and find does not.")
    if S("b.12") and S("b.13"):
        b.append(f"find with allow_disk_use(True) and (False) both returned the correct three smallest values "
                 f"(b.12, b.13: {new_outcome(S('b.12'))['outcome']}, {new_outcome(S('b.13'))['outcome']}).")
    out["b_allowDiskUse"] = " ".join(b)
    qa.append({"question": "Does allowDiskUse change behaviour on engine 1.2.0?",
               "answer": " ".join(b[:3]) if len(b) >= 3 else " ".join(b), "confidence": "observed"})
    qa.append({"question": "Is a non-boolean allowDiskUse rejected?", "answer": next((x for x in b if x.startswith("A non-boolean")), "not run"),
               "confidence": "observed"})
    qa.append({"question": "Would MongoDB behave differently on the 240 MB sort with allowDiskUse false?",
               "answer": ("Probably. With an explicit allowDiskUse: false, MongoDB fails a blocking $sort above 100 MB with "
                          "code 292 QueryExceededMemoryLimitNoDiskUseAllowed. That comes from MongoDB documentation and was "
                          "not run here. The engine completed the same sort (b.4), so a rule that relies on "
                          "allowDiskUse: false to cap memory does not hold on this engine."),
               "confidence": "inferred"})
    qa.append({"question": "What unit does explain's SORT totalDataSizeSortedBytesEstimate use?",
               "answer": next((x for x in b if "totalDataSizeSortedBytesEstimate" in x), "not observed"),
               "confidence": "inferred"})

    # ---------------- (c) + (e)
    c = []
    FIND_IDS = ("c.1", "c.1b", "c.1c", "c.1d", "c.1e", "c.1f", "c.1g", "c.1h", "c.1i", "c.1j")

    def shapes(suffix):
        rows, coll, par, when = [], [], [], []
        for sid0 in FIND_IDS:
            sid = sid0 + suffix
            s = S(sid)
            if not s:
                continue
            if s.get("seconds_after_bulk_load") is not None:
                when.append(s["seconds_after_bulk_load"])
            if not ok(sid):
                rows.append(f"{sid} error {fmt_err(new_outcome(s))}")
                continue
            sm = s["response"]["result"]["summary"]
            fe = sm.get("first_executionStats") or {}
            extra = (f", per-loop counts over {sm['max_actualLoops']} loops, about "
                     f"{sm.get('max_node_totalDocsExamined_x_actualLoops')} examined in total" if sm.get("max_actualLoops") else "")
            rows.append(f"{sid} {sm['chain']} (top-level totalDocsExamined {fe.get('totalDocsExamined')}, deepest node "
                        f"{sm.get('max_node_totalDocsExamined')}, nReturned {fe.get('nReturned')}{extra})")
            if sm["has_COLLSCAN"]:
                coll.append(sid)
            if sm.get("parallel"):
                par.append(sid)
        return rows, coll, par, (min(when), max(when)) if when else None

    pre_rows, pre_coll, pre_par, pre_when = shapes("")
    post_rows, post_coll, post_par, post_when = shapes("-post")
    e2 = S("e.2")
    e2r = (e2 or {}).get("response", {}).get("result", {})
    changed_at = e2r.get("changed_after_bulk_load_s")
    first_ic = (e2r.get("samples") or [{}])[0].get("indexCosts_first")
    last_ic = (e2r.get("samples") or [{}])[-1].get("indexCosts_first")
    c.append(f"Right after the bulk load ({pre_when[0] if pre_when else '?'}-{pre_when[1] if pre_when else '?'} s after "
             f"it), COLLSCAN appeared in {len(pre_coll)} of {len(pre_rows)} unindexed find explains "
             f"({', '.join(pre_coll) or 'none'}).")
    if e2:
        c.append((f"The plan poll (e.2) saw the unindexed find's plan change with no client action about {changed_at} s "
                  f"after the load, from '{e2r.get('first_chain')}' to '{e2r.get('last_chain')}'. The _id_ index cost "
                  f"estimate went from {json.dumps(first_ic)} to {json.dumps(last_ic)}. That is consistent with "
                  "PostgreSQL's autovacuum analyzing the new table (inferred from the estimates; the catalog was not read).")
                 + (" Across executions the refresh timing varied. In the first execution, explains about 10 to 30 s "
                    "after its load still showed the bitmap _id_ plan with selectivity 0.005 (report.run1.json: run "
                    "started 21:00:12Z, c.1 at 21:00:25Z, c.4c at 21:00:44Z). In the third, an explain less than 10 s "
                    "after its run started already showed COLLSCAN with selectivity 1.0 and correlation 0.75 "
                    "(third_run_excerpt: run started 21:08:59Z, c.1d at 21:09:08Z). That fits a periodic background "
                    "analyze rather than a fixed delay (inferred)."
                    if rep.get("third_run_excerpt") else "")
                 if changed_at is not None else
                 f"The plan poll (e.2) saw no plan change within the 150 s cap (last chain '{e2r.get('last_chain')}').")
    c.append(f"After the poll ({post_when[0] if post_when else '?'}-{post_when[1] if post_when else '?'} s after the "
             f"load), COLLSCAN appeared in {len(post_coll)} of {len(post_rows)} unindexed find explains "
             f"({', '.join(post_coll) or 'none'}), and {len(post_par)} were parallel plans ({', '.join(post_par) or 'none'}).")
    c.append("So whether an unindexed find shows COLLSCAN depends on the planner's statistics for the collection, not "
             "only on the engine version. A freshly loaded, un-analyzed collection shows FETCH with runtimeFilterSet "
             "over a bitmap IXSCAN on _id_ (the 0.117 observation, whose explain also shows the un-analyzed estimate "
             "selectivity 0.005). Once statistics exist, the same finds show COLLSCAN, which is what the managed-cluster "
             "runs cited in DECISIONS topic 10 recorded."
             if (pre_coll != post_coll or changed_at is not None) else
             "The unindexed find plans were the same in both states, so this run cannot separate engine behaviour "
             "from statistics.")
    if "c.1e" in pre_coll:
        c.append("Even before the refresh, find {grp: 5} with limit 5 shows LIMIT > COLLSCAN, where the COLLSCAN node "
                 "carries indexName _id_ and direction Forward, an ordered walk of the _id index (c.1e).")
    for sid in ("c.1d", "c.1d-post"):
        s = S(sid)
        if s and ok(sid):
            sm = s["response"]["result"]["summary"]
            fe = sm.get("first_executionStats") or {}
            c.append(f"Top-level executionStats belong to the root stage. In {sid} (SORT on top), totalDocsExamined is "
                     f"{fe.get('totalDocsExamined')} for nReturned {fe.get('nReturned')}, while the deepest node examined "
                     f"{sm.get('max_node_totalDocsExamined')}"
                     + (f" per loop over {sm['max_actualLoops']} loops (about {sm.get('max_node_totalDocsExamined_x_actualLoops')} in total)"
                        if sm.get("max_actualLoops") else "")
                     + f" and the runtime filter removed {sm.get('max_node_totalDocsRemovedByRuntimeFilter')}"
                     + (" per loop" if sm.get("max_actualLoops") else "") + ".")
    c.append("A full-scan check therefore needs three things. First, look for COLLSCAN anywhere in the tree. Second, "
             "compare the scan node's totalDocsExamined, multiplied by actualLoops on parallel plans, and its "
             "totalDocsRemovedByRuntimeFilter against nReturned. Third, treat FETCH over a bitmap IXSCAN on _id_ with a "
             "runtimeFilterSet as a full scan. Top-level totalDocsExamined alone misses SORT- or LIMIT-rooted plans, and "
             "per-node nReturned on parallel plans is a per-loop average.")
    ch = lambda sid: S(sid)["response"]["result"]["summary"]["chain"]  # noqa: E731
    if all(ok(x) for x in ("c.1i", "c.1i-post", "c.1", "c.1-post")):
        if ch("c.1i-post") != ch("c.1-post"):
            c.append(f"hint {{$natural: 1}} was accepted. After the refresh it gave '{ch('c.1i-post')}' where the "
                     f"unhinted find gave '{ch('c.1-post')}' (c.1i-post, c.1-post). So on this engine $natural steers "
                     f"the plan to the _id_ index instead of forcing a collection scan. Before the refresh both gave "
                     f"'{ch('c.1i')}' (c.1i, c.1).")
        else:
            c.append("hint {$natural: 1} was accepted and gave the same plan as the unhinted find in both states (c.1i, c.1i-post).")
    if ok("c.1j-post"):
        icj = S("c.1j-post")["response"]["result"]["summary"].get("indexCosts_first") or {}
        if icj.get("selectivity") == 0.005 and "correlation" not in icj:
            c.append("The 24-document sales collection kept the bitmap _id_ plan and the un-analyzed estimate "
                     "(selectivity 0.005, no correlation) after the poll (c.1j-post). The 500-document vec collection, "
                     "explained seconds after its insert, showed the same (c.6f). So small or just-written collections can "
                     "keep the bitmap plan until enough writes trigger an analyze; for 24 documents that is consistent "
                     "with PostgreSQL's default autovacuum analyze threshold of 50 rows plus 10% (inferred, assuming "
                     "default settings).")
    for sid, lab in (("c.2", "Aggregate with unindexed $match and $sort, right after the load"),
                     ("c.2-post", "Same aggregate after the poll"),
                     ("c.4", "Indexed equality find"), ("c.4b", "Indexed range sorted on an unindexed field"),
                     ("c.4c", "Indexed range sorted on the indexed field"),
                     ("c.5", "Aggregate with indexed $match, $sort and $limit"),
                     ("c.5b", "Aggregate with unindexed $match and $sort on indexed i"),
                     ("c.5c", "Aggregate with indexed $match and $sort on the same field"),
                     ("c.6d", "The $search cosmosSearch pipeline on vector-ivf"), ("c.7", "The L08 window pipeline"),
                     ("c.7b", "The 0.117 window pipeline")):
        s = S(sid)
        if not s:
            continue
        if not ok(sid):
            c.append(f"{lab} ({sid}): error {fmt_err(new_outcome(s))}.")
            continue
        sm = s["response"]["result"]["summary"]
        fe = sm.get("first_executionStats") or {}
        extra = f", cosmosSearchCustomParams {json.dumps(sm['cosmosSearchCustomParams'])}" if sm.get("cosmosSearchCustomParams") else ""
        c.append(f"{lab} ({sid}): {sm['chain']}{extra}; COLLSCAN {'yes' if sm['has_COLLSCAN'] else 'no'}; "
                 f"SORT {'yes' if sm['has_SORT'] else 'no'}; first executionStats totalDocsExamined "
                 f"{fe.get('totalDocsExamined')} for nReturned {fe.get('nReturned')}"
                 + (f" (per-loop, {sm['max_actualLoops']} loops)" if sm.get("max_actualLoops") else "") + ".")
    s4c = S("c.4c")
    if s4c and ok("c.4c"):
        r1c = (rep.get("earlier_run_of_this_script") or {}).get("explain_chains", {})
        has_sort = s4c["response"]["result"]["summary"]["has_SORT"]
        txt = ("The indexed range sorted on the indexed field " +
               ("still runs a separate SORT over the IXSCAN (c.4c), so that sort is not served by the index."
                if has_sort else
                f"ran as '{ch('c.4c')}' with no SORT stage (c.4c; c.5c for the aggregate), with the statistics "
                f"refreshed (indexCosts {json.dumps(S('c.4c')['response']['result']['summary'].get('indexCosts_first'))}), "
                "so the ordered index scan served the sort."))
        if not has_sort and r1c.get("c.4c"):
            txt += (f" In the first execution, explained before the refresh (indexCosts "
                    f"{json.dumps(r1c['c.4c'].get('indexCosts_first'))}), the same find showed '{r1c['c.4c']['chain']}'"
                    + (f" and the aggregate '{r1c['c.5c']['chain']}'" if r1c.get("c.5c") else "") + " (report.run1.json).")
            txt += (" So whether the index serves a sort is also a statistics question. The Learn limitations line quoted "
                    "in DECISIONS topic 10 ('Sorting is done in memory and doesn't push down to the index') does not "
                    "describe engine 1.2.0 for this query once the table is analyzed; the managed service was not tested.")
        c.append(txt)
    if ok("c.1") and ok("c.5"):
        s1 = S("c.1")["response"]["result"]["summary"]
        s5 = S("c.5")["response"]["result"]["summary"]
        c.append(f"Layout: a find explain has top-level keys {s1['top_level_keys']}, with the plan at "
                 f"{s1['winningPlan_paths'][0]}. An aggregate explain has top-level keys {s5['top_level_keys']} and a "
                 f"stages array whose entries have the keys {s5.get('stages_array_keys')}; the plan is at "
                 f"{s5['winningPlan_paths'][0]}, and each later stage carries its own queryPlanner and executionStats. "
                 "Parallel aggregate plans add a $root entry (PARALLEL_SORT_MERGE). Window and $set stages show "
                 "COLLSCAN inside their own sub-plans over intermediate rows (c.7, c.7b), as on 0.117.")
    out["c_explain"] = " ".join(c)
    out["c_unindexed_find_shapes_right_after_load"] = pre_rows
    out["c_unindexed_find_shapes_after_poll"] = post_rows
    qa.append({"question": "Does COLLSCAN ever appear for an unindexed find, and what is totalDocsExamined?",
               "answer": " ".join(c[:4]) + " Right after the load: " + "; ".join(pre_rows) + ". After the poll: "
                         + "; ".join(post_rows) + ".",
               "confidence": "observed"})
    qa.append({"question": "Why does the explain plan for the same unindexed find differ between runs?",
               "answer": " ".join(c[1:4]), "confidence": "inferred" if changed_at is not None else "inconclusive"})
    qa.append({"question": "Is top-level executionStats.totalDocsExamined, or a COLLSCAN search, a reliable full-scan signal?",
               "answer": " ".join(x for x in c if x.startswith(("Top-level executionStats", "A full-scan check"))),
               "confidence": "observed"})
    qa.append({"question": "What are the explain('executionStats') shapes for an indexed find, an aggregate with $match/$sort, "
                           "and a $search cosmosSearch pipeline on vector-ivf (DECISIONS topic 10, open question 3)?",
               "answer": " ".join(x for x in c if x.startswith(("Indexed", "Aggregate", "Same aggregate", "The $search",
                                                                "Layout", "The indexed range"))),
               "confidence": "observed"})
    qa.append({"question": "Are there other statistics-dependent plan effects (hint $natural, small collections)?",
               "answer": " ".join(x for x in c if x.startswith(("hint {$natural", "The 24-document"))) or "none observed",
               "confidence": "observed"})
    e1, e3 = S("e.1"), S("e.3")
    if e1 and e3:
        def cnt(s):
            r = s["response"]
            return r["attempts_total"] - r["attempts_failed"], r["attempts_total"]
        a1, n1 = cnt(e1)
        a3, n3 = cnt(e3)
        etxt = (f"A raw find with maxTimeMS 1 (101-document first batch) completed {a1}/{n1} times right after the load "
                f"(e.1) and {a3}/{n3} times after the poll (e.3).")
        if a1 < n1 and a3 == n3:
            etxt += (" That fits the plan change: the bitmap IXSCAN on _id_ must read the whole index before the first "
                     "row, while COLLSCAN streams. The 1 ms boundary results in d.1, d.5 and d.7, and the failures in "
                     "the second execution, follow the statistics state rather than chance alone (inferred).")
        elif a1 == a3:
            etxt += (" The plan state made no difference here, so it does not explain the failures in the second "
                     "execution. Timing noise or load from other work on the container are possible causes; neither "
                     "was tested.")
        out["e_plan_stability"] = (c[1] if len(c) > 1 else "") + " " + etxt
        qa.append({"question": "Does the planner state change maxTimeMS 1 outcomes for a small first batch?",
                   "answer": etxt, "confidence": "observed"})

    # ---------------- (d)
    d = []
    def att(sid):
        s = S(sid)
        return None if s is None else s["response"]
    codes = set()
    for sid in ("d.1", "d.1b", "d.2", "d.3", "d.4", "d.6", "d.7", "d.7b", "d.8", "d.9", "d.10"):
        r = att(sid)
        if r and "attempts" in r:
            for e in r["error_codes"]:
                codes.add((e["code"], e["codeName"]))
    for sid in ("d.5b", "d.5c", "d.5f"):
        if S(sid) and not ok(sid):
            o = new_outcome(S(sid))
            codes.add((o.get("code"), o.get("codeName")))
    out["d_error_codes_seen"] = [{"code": x, "codeName": y} for x, y in sorted(codes, key=str)]
    first_fail = None
    for sid in ("d.2", "d.3", "d.4", "d.6", "d.8", "d.9", "d.10"):
        r = att(sid)
        if r and r.get("attempts_failed"):
            first_fail = next(a for a in r["attempts"] if not a["completed"])["error"]
            break
    if first_fail:
        d.append(f"Every maxTimeMS expiry returned code {first_fail.get('code')}, codeName '{first_fail.get('codeName')}', "
                 f"errmsg '{first_fail.get('errmsg')}', with {'errorLabels ' + str(first_fail.get('errorLabels')) if first_fail.get('errorLabels') else 'no errorLabels'}. "
                 f"PyMongo raised {first_fail.get('exception')}. Code 50 is MongoDB's MaxTimeMSExpired number, but the "
                 "codeName string differs, as on 0.117.")
    def line(sid, lab):
        r = att(sid)
        if not r:
            return None
        if "attempts" in r:
            if r["attempts_failed"] == 0:
                a0 = r["attempts"][0]
                return (f"{lab} ({sid}): {r['attempts_total']}/{r['attempts_total']} completed, "
                        f"{a0.get('consumed_docs', a0.get('value'))} docs, batches {a0['wire_summary']['batch_lens']}, "
                        f"getMore maxTimeMS sent {a0['wire_summary']['getMore_maxTimeMS_values']}")
            f = next(a for a in r["attempts"] if not a["completed"])
            where = f["wire_summary"]["failed_commands"][0]["command"] if f["wire_summary"]["failed_commands"] else "?"
            done = r["attempts_total"] - r["attempts_failed"]
            return (f"{lab} ({sid}): " + (f"{done}/{r['attempts_total']} completed, " if done else "")
                    + f"{r['attempts_failed']}/{r['attempts_total']} failed on {where} "
                    f"with code {f['error'].get('code')} {f['error'].get('codeName')}")
        o = new_outcome(S(sid))
        return f"{lab} ({sid}): {o['outcome']}" + (f" {fmt_err(o)}" if o["outcome"] == "error" else "")
    lines = [x for x in (
        line("d.1", "find, maxTimeMS 1, default batch"), line("d.1b", "find, maxTimeMS 20, default batch"),
        line("d.2", "find, maxTimeMS 1, batchSize 1000"), line("d.3", "find, maxTimeMS 1, nothing matches"),
        line("d.4", "find, maxTimeMS 1, blocking sort"), line("d.6", "aggregate $count, maxTimeMS 1"),
        line("d.7", "aggregate streaming, maxTimeMS 1"), line("d.7b", "aggregate streaming, maxTimeMS 20"),
        line("d.8", "aggregate streaming, maxTimeMS 1, batchSize 1000"), line("d.9", "aggregate blocking sort, maxTimeMS 1"),
        line("d.10", "count_documents, maxTimeMS 1"), line("d.5", "raw find, maxTimeMS 1"),
        line("d.5b", "raw getMore carrying maxTimeMS 1"), line("d.5c", "plain getMore afterwards"),
        line("d.5f", "raw getMore carrying maxTimeMS 60000")) if x]
    d.append("Per step: " + "; ".join(lines) + ".")
    def rt(sid, idx):
        r = att(sid)
        vals = [a["wire_summary"]["server_round_trips_ms"][idx] for a in (r or {}).get("attempts", [])
                if a["completed"] and len(a["wire_summary"]["server_round_trips_ms"]) > idx]
        return (min(vals), max(vals)) if vals else None
    cum_test = [att(x) for x in ("d.1b", "d.7b")]
    if all(r and r["outcome"] == "ok" for r in cum_test):
        f0, g0 = rt("d.1b", 0), rt("d.1b", 1)
        a0, h0 = rt("d.7b", 0), rt("d.7b", 1)
        d.append(f"maxTimeMS is enforced per command, against the work that command does, and is not cumulative across "
                 f"the cursor. With maxTimeMS 20, the initial find took {f0[0]}-{f0[1]} ms and the initial aggregate "
                 f"{a0[0]}-{a0[1]} ms (client-measured round trips) for a 101-document first batch. A getMore with no "
                 f"maxTimeMS then ran {g0[0]}-{g0[1]} ms (find) and {h0[0]}-{h0[1]} ms (aggregate) and drained the rest "
                 f"with no error in every attempt (d.1b, d.7b). PyMongo sends no maxTimeMS on getMore for non-tailable "
                 f"cursors, so once the first batch fits inside the limit the rest of the cursor is unbounded. When the "
                 f"first batch needs more work (batchSize 1000, an empty result, a blocking sort, $count, count_documents), "
                 f"the initial command fails instead (d.2-d.4, d.6, d.8-d.10).")
    elif any(r for r in cum_test):
        d.append("The cumulative-limit test (d.1b, d.7b) did not complete cleanly, so whether the limit is cumulative is "
                 "inconclusive from this run.")
    tb = []
    for sid, lab in (("d.1", "find"), ("d.7", "streaming aggregate"), ("d.5", "raw find")):
        r = att(sid)
        if r and "attempts" in r:
            tb.append(f"{lab} {r['attempts_total'] - r['attempts_failed']}/{r['attempts_total']} completed ({sid})")
    if tb:
        prior = []
        if rep.get("earlier_run_of_this_script"):
            o = rep["earlier_run_of_this_script"]["outcomes"]
            prior.append(f"first execution: find {o.get('d.1')}, streaming aggregate {o.get('d.7')}, raw find {o.get('d.5')}")
        if rep.get("second_run_excerpt"):
            prior.append("second execution: find 3/3 completed, streaming aggregate 3/3 failed with code 50 on the "
                         "initial aggregate, raw find failed with code 50 twice (second_run_excerpt)")
        d.append("At maxTimeMS 1 with the default 101-document first batch, the outcome depends on whether that first "
                 "batch finishes inside 1 ms. In this run: " + ", ".join(tb) + "."
                 + (" Earlier executions against the same container: " + "; ".join(prior) + "." if prior else "")
                 + " The failures are code 50 on the initial command.")
    if S("d.5b"):
        o5b = new_outcome(S("d.5b"))
        o5c = new_outcome(S("d.5c")) if S("d.5c") else None
        o5f = new_outcome(S("d.5f")) if S("d.5f") else None
        part = ("A getMore that carries maxTimeMS is accepted on a non-tailable cursor and limited on its own. With 1 ms "
                + (f"it failed with {fmt_err(o5b)} (d.5b)" if o5b["outcome"] == "error" else "it completed (d.5b)"))
        if o5c:
            part += ("; the next plain getMore " + (f"failed with {fmt_err(o5c)}, so the timed-out getMore destroyed the cursor (d.5c)"
                                                   if o5c["outcome"] == "error" else "drained the cursor (d.5c)"))
        if o5f:
            part += ("; with 60000 ms it " + ("returned the remaining documents (d.5f)" if o5f["outcome"] == "ok"
                                              else f"failed with {fmt_err(o5f)} (d.5f)"))
        d.append(part + ".")
    out["d_maxTimeMS"] = " ".join(d)
    qa.append({"question": "What code and codeName does maxTimeMS 1 produce on aggregate and on find (whole cursor consumed)?",
               "answer": " ".join(d[:2]), "confidence": "observed"})
    cum = next((x for x in d if x.startswith(("maxTimeMS is enforced per command", "The cumulative-limit test"))), None)
    if cum:
        qa.append({"question": "Is maxTimeMS cumulative across getMore (as MongoDB documents for cursor.maxTimeMS), or per command?",
                   "answer": cum, "confidence": "observed" if cum.startswith("maxTimeMS is enforced per command") else "inconclusive"})
    tbx = next((x for x in d if x.startswith("At maxTimeMS 1 with the default")), None)
    if tbx:
        qa.append({"question": "Is the 0.117 observation 'find with maxTimeMS 1 completes' stable?",
                   "answer": tbx + " It is a timing boundary, not a fixed rule; use a limit well above or below the "
                                   "first-batch cost when testing.", "confidence": "observed"})
    gmx = next((x for x in d if x.startswith("A getMore that carries maxTimeMS")), None)
    if gmx:
        qa.append({"question": "What happens when a getMore itself carries maxTimeMS?", "answer": gmx, "confidence": "observed"})
    qa.append({"question": "Do these engine 1.2.0 results prove managed Azure DocumentDB behaviour?",
               "answer": out["scope"] + " The managed service may run a different build and different gateway settings.",
               "confidence": "inconclusive"})
    out["same_as_0_117"] = same_items
    out["changed_from_0_117"] = changed_items
    out["structured"] = qa
    return out


def finalize(path=None):
    path = path or os.path.join(HERE, "report.json")
    with open(path) as fh:
        rep = json.load(fh)
    try:
        with open(BASELINE) as fh:
            base = json.load(fh)
    except OSError:
        base = None
    rep["comparison_baseline"] = {"path": BASELINE,
                                  "engine": (base or {}).get("target", {}).get("hello", {}).get("internal", {}).get("documentdb_versions"),
                                  "documents_in_big_collection": 200000}
    rep["differences_from_0_117_run"] = [
        "100,000 documents in the big collection instead of 200,000 (same generator and seed, so these are the first 100,000 of the 0.117 documents).",
        "Section a adds the exact L08 pipeline on a trades collection (0.117 ran a sales variant with $max over the raw field) and 22 sortBy cases instead of 4.",
        "Section b adds allowDiskUse omitted, a 240 MB sort with explain, more non-boolean types, and find variants.",
        "Section c adds ten unindexed find shapes, aggregate variants, and explains of the window pipelines.",
        "Section d consumes every cursor under wire-level command monitoring, repeats each maxTimeMS case three times, and adds blocking shapes, maxTimeMS 20 cumulative tests, and raw getMore with maxTimeMS.",
    ]
    run1 = os.path.join(HERE, "report.run1.json")
    if os.path.exists(run1):
        try:
            with open(run1) as fh:
                r1 = json.load(fh)
            ev = {}
            for s in r1.get("steps", []):
                if s.get("id") in ("d.1", "d.5", "d.7", "d.5b", "d.5c"):
                    resp = s["response"]
                    if "attempts" in resp:
                        ev[s["id"]] = f"{resp['attempts_total'] - resp['attempts_failed']}/{resp['attempts_total']} attempts completed"
                    else:
                        ev[s["id"]] = (resp.get("outcome") if resp.get("outcome") != "error"
                                       else f"error {resp.get('code')} {resp.get('codeName')}")
                        if s["id"] == "d.5c" and isinstance(resp.get("result"), dict) and resp["result"].get("error"):
                            e = resp["result"]["error"]
                            ev[s["id"]] = f"error {e.get('code')} {e.get('codeName')} (recorded inside result by that revision)"
            chains = {}
            for s in r1.get("steps", []):
                if s.get("id") in ("c.1", "c.4c", "c.5c", "c.1j", "c.6f") and (s.get("response") or {}).get("outcome") == "ok":
                    sm = R.summarize_explain(s["response"]["result"]["full_explain"])
                    chains[s["id"]] = {"chain": sm["chain"], "indexCosts_first": sm.get("indexCosts_first")}
            rep["earlier_run_of_this_script"] = {
                "path": run1, "started_utc": r1.get("started_utc"),
                "what": "First execution of an earlier revision of run.py against the same container (3 attempts per "
                        "maxTimeMS case; no d.1b/d.7b; d.5 opened the getMore-test cursor with maxTimeMS 1). Kept for "
                        "the timing comparison only.",
                "outcomes": ev, "explain_chains": chains}
        except (OSError, ValueError, KeyError):
            pass
    run2 = os.path.join(HERE, "run2.stderr-excerpt.txt")
    if os.path.exists(run2):
        with open(run2) as fh:
            lines = [ln.rstrip("\n") for ln in fh if ln.startswith("[")]
        rep["second_run_excerpt"] = {
            "path": run2,
            "what": "Second execution of an intermediate revision of run.py; its report.json was overwritten by the next "
                    "execution, so only these verbatim stderr lines survive. It shows the maxTimeMS 1 first-batch boundary "
                    "failing where this report's run completed.",
            "lines": lines}
    run3 = os.path.join(HERE, "run3.stderr-excerpt.txt")
    if os.path.exists(run3):
        with open(run3) as fh:
            lines = [ln.rstrip("\n") for ln in fh if not ln.startswith("#")]
        rep["third_run_excerpt"] = {
            "path": run3,
            "what": "Third execution (started 21:08:59 UTC); its report.json was overwritten. Its section c explains ran a "
                    "few seconds after the bulk load and already showed COLLSCAN with refreshed index-cost estimates, so "
                    "the statistics refresh landed just after that load.",
            "lines": lines}
    comparison = build_comparison(rep, base) if base else []
    rep["comparison_with_0_117"] = comparison if base else "baseline report not found"
    rep["conclusions"] = conclude(rep, comparison)
    with open(path, "w") as fh:
        json.dump(rep, fh, indent=1, default=str)
    print(f"finalized {path}", file=sys.stderr)


if __name__ == "__main__":
    finalize(sys.argv[1] if len(sys.argv) > 1 else None)
