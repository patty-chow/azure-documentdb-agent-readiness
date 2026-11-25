#!/usr/bin/env python
"""Tight one-line-per-step view of report.json: exact error fields kept, ok results summarized."""
import json
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests-1.2/query-behaviour/report.json"
r = json.load(open(P))


def cut(s, n):
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def e_txt(e):
    lab = e.get("errorLabels")
    return f"{e.get('code')} {e.get('codeName')}: {e.get('errmsg') or e.get('message')}; errorLabels {lab if lab else 'none'}"


def resp(s):
    x = s["response"]
    if "attempts" in x:
        a = x["attempts"][0]
        ws = a["wire_summary"]
        done = x["attempts_total"] - x["attempts_failed"]
        f = [t for t in x["attempts"] if not t["completed"]]
        out = f"{done}/{x['attempts_total']} completed"
        if f:
            fc = f[0]["wire_summary"]["failed_commands"]
            out += f"; failed on {fc[0]['command'] if fc else '?'}: " + e_txt(f[0]["error"])
        out += f"; getMore x{ws['getMore_count']} maxTimeMS {','.join(ws['getMore_maxTimeMS_values']) or '-'}; batches {ws['batch_lens']}"
        return out
    if x.get("outcome") == "error":
        return "error " + e_txt(x)
    res = x.get("result")
    if isinstance(res, dict) and "summary" in res:
        sm = res["summary"]
        fe = sm.get("first_executionStats") or {}
        ic = sm.get("indexCosts_first") or {}
        out = (f"{sm['chain']}; COLLSCAN {'yes' if sm['has_COLLSCAN'] else 'no'}"
               + (f"; top docsExamined {fe.get('totalDocsExamined')} nReturned {fe.get('nReturned')}" if fe else "")
               + (f"; deepest {sm.get('max_node_totalDocsExamined')}" if sm.get("max_node_totalDocsExamined") not in (None, fe.get("totalDocsExamined")) else "")
               + (f"; filtered {sm.get('max_node_totalDocsRemovedByRuntimeFilter')}" if sm.get("max_node_totalDocsRemovedByRuntimeFilter") else "")
               + (f"; loops {sm['max_actualLoops']}" if sm.get("max_actualLoops") else "")
               + (f"; _id_ cost sel {ic.get('selectivity')} corr {ic.get('correlation', '-')}" if ic else ""))
        if res.get("sort_nodes"):
            sn = [n for n in res["sort_nodes"] if "executionStats" in n["path"]][:1]
            if sn:
                out += f"; SORT usedDisk {sn[0].get('usedDisk')} sortMethod {sn[0].get('sortMethod')} sizeEst {sn[0].get('totalDataSizeSortedBytesEstimate')}"
        return out
    if isinstance(res, dict) and "samples" in res:
        return (f"{res['first_chain']} -> {res['last_chain']} after {res['changed_after_bulk_load_s']} s; "
                f"{len(res['samples'])} samples")
    return cut(json.dumps(res, ensure_ascii=False), 150)


def cmd(s):
    c = s["command"]
    c = c.replace("  # database t_query", "")
    return cut(c, 95)


steps = [{"step": cut(s["step"], 80), "command": cmd(s), "response": cut(resp(s), 215), "reading": cut(s["reading"], 190)}
         for s in r["steps"]]
print(json.dumps(steps, ensure_ascii=False, indent=0))
