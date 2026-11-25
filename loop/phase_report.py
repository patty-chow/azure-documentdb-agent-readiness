"""Summarize the loop's runs into findings/PHASE-REPORT.md.

    python loop/phase_report.py                 all arms
    python loop/phase_report.py --arm control   one arm

Reads runs/loop-state.json and each run folder's 02-readiness.json and
05-audit.json. Per sample: latest run per arm, how far it went, verdicts and
score. Across samples: score distribution per vertical, how often each cold
question was answered wrongly, blocked samples with their blockers, build and
audit verdict counts. The findings triage (findings/TRIAGE.md) is the other
half: it says what to fix; this says how the agents did.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
STATE = PROJECT / "runs" / "loop-state.json"
INDEX = PROJECT / "samples" / "index.json"
OUT = PROJECT / "findings" / "PHASE-REPORT.md"
STAGE_ORDER = {"review": 1, "readiness": 2, "build": 3, None: 4}


def load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def score_of(entry: dict) -> int | None:
    raw = entry.get("verdicts", {}).get("readiness_score")
    try:
        return int(str(raw).split()[0])
    except (ValueError, AttributeError, IndexError):
        return None


def latest_per_sample(state: dict, arm: str | None) -> dict[str, dict]:
    """Furthest-reaching finished run (exit 0 or 4) per sample (and arm), else the latest attempt."""
    best: dict[str, dict] = {}
    for e in state["runs"]:
        if arm and e["arm"] != arm:
            continue
        key = e["id"] if arm else f"{e['id']}|{e['arm']}"
        cur = best.get(key)
        # Exit 4 (audit failed) is a finished run too: a failed audit outranks a readiness-only run.
        def rank_of(r: dict) -> tuple:
            done = r.get("exit_code") in (0, 4)
            return (done, STAGE_ORDER.get(r.get("stop_after"), 4) if done else 0, r["started"])
        rank, cur_rank = rank_of(e), (rank_of(cur) if cur else None)
        if cur is None or rank > cur_rank:
            best[key] = e
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm")
    args = ap.parse_args()
    state = load(STATE) or {"runs": []}
    index = {s["id"]: s for s in load(INDEX) or []}
    latest = latest_per_sample(state, args.arm)

    rows = []
    confusions: Counter = Counter()
    confusion_runs = 0
    question_text: dict[str, str] = {}
    blocked: list[tuple[str, list[str]]] = []
    audits: Counter = Counter()
    builds: Counter = Counter()
    violated: Counter = Counter()
    mcp_zero_builds: list[str] = []
    for key, e in sorted(latest.items()):
        sid = e["id"]
        s = index.get(sid, {})
        sc = score_of(e)
        rows.append((sid, e["arm"], s.get("vertical", sid.rsplit("-", 1)[0]), s.get("title", e.get("title", "")),
                     e.get("exit_code"), e.get("stop_after") or "audit", e.get("verdicts", {}), sc, e.get("minutes")))
        run_dir = PROJECT / e["run_dir"] if e.get("run_dir") else None
        if not run_dir or not run_dir.is_dir():
            continue
        r = load(run_dir / "02-readiness.json")
        if r:
            confusion_runs += 1
            for c in r.get("confusions", []):
                qid = c.get("question_id", "?")
                question_text.setdefault(qid, c.get("question", ""))
                if c.get("outcome") not in ("correct", None):
                    confusions[qid] += 1
            if r.get("verdict") == "blocked":
                blocked.append((sid, r.get("blockers", [])))
        a = load(run_dir / "05-audit.json")
        if a:
            audits[a.get("verdict", "?")] += 1
            for c in a.get("checks", []):
                if c.get("status") == "violated":
                    violated[c.get("topic") or c.get("category", "?")] += 1
        b = load(run_dir / "03-build.json")
        if b:
            builds[b.get("status", "?")] += 1

    scores = [r[7] for r in rows if r[7] is not None]
    by_vertical: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        if r[7] is not None:
            by_vertical[r[2]].append(r[7])

    L = [f"# Phase report{f' (arm {args.arm})' if args.arm else ''}", "",
         f"{len(rows)} samples with a run. {sum(1 for r in rows if r[4] == 0)} finished with exit 0; "
         f"{sum(1 for r in rows if r[4] not in (0, None))} failed; {sum(1 for r in rows if r[4] is None)} unfinished. "
         f"Regenerate with `python loop/phase_report.py`.", ""]
    if scores:
        L += ["## Readiness confidence", "",
              f"{len(scores)} scored. Min {min(scores)}, median {statistics.median(scores):.0f}, mean {statistics.mean(scores):.1f}, max {max(scores)}. "
              "Bands: High 80 and above, Medium 60 to 79, Low below 60.", "",
              "| Vertical | Samples | Mean | Min | Max | High | Medium | Low |", "|---|---|---|---|---|---|---|---|"]
        for v, s in sorted(by_vertical.items()):
            L.append(f"| {v} | {len(s)} | {statistics.mean(s):.1f} | {min(s)} | {max(s)} | {sum(x >= 80 for x in s)} | {sum(60 <= x < 80 for x in s)} | {sum(x < 60 for x in s)} |")
        L.append("")
    if confusion_runs:
        L += ["## What the model got wrong before reading anything", "",
              f"Cold-quiz questions whose answer from memory was wrong, partly wrong or outdated, across {confusion_runs} readiness reports.", "",
              "| Question | Wrong in | Share |", "|---|---|---|"]
        for qid, n in confusions.most_common():
            # Q items are the fixed quiz; S items are written per sample, so only their slot is comparable.
            label = question_text.get(qid, "")[:110] if qid.startswith("Q") else "(sample-specific question in this slot)"
            L.append(f"| {qid} {label} | {n}/{confusion_runs} | {100 * n // confusion_runs}% |")
        L.append("")
    if blocked:
        L += ["## Blocked samples", "", "Readiness said the sample cannot be built as written.", ""]
        for sid, bl in blocked:
            L.append(f"- **{sid}** ({index.get(sid, {}).get('title', '')})")
            for b in bl:
                L.append(f"  - {b[:400]}")
        L.append("")
    if builds or audits:
        L += ["## Build and audit", "",
              f"Build status: {dict(builds)}. Audit verdict: {dict(audits)}.", ""]
        if violated:
            L += ["Most violated practices across audits:", "", "| Practice | Builds |", "|---|---|"]
            for t, n in violated.most_common(15):
                L.append(f"| {t} | {n} |")
            L.append("")
    L += ["## Per sample", "", "| Sample | Arm | Title | Reached | Exit | Review | Readiness | Score | Build | Audit | Min |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for sid, arm, vert, title, code, reached, v, sc, mins in rows:
        L.append(f"| {sid} | {arm} | {title[:40]} | {reached} | {code} | {v.get('prompt_review', '')} | {v.get('readiness', '')} | "
                 f"{sc if sc is not None else ''} | {v.get('build', '')} | {v.get('audit', '')} | {mins if mins is not None else ''} |")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{len(rows)} samples -> {OUT.relative_to(PROJECT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
