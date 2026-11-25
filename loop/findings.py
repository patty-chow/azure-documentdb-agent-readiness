"""Turn one pipeline run folder into triage findings for the product team.

    python loop/findings.py                  rebuild findings/ from every run under runs/
    python loop/findings.py runs/x/2026...   print the findings of one run

A finding is one thing an agent needed and could not get, with the repo that
should change (Learn docs, the Agent Kit, the DocumentDB MCP, or the sample
itself), the evidence path, and the proposed change. Nothing is created
outside this repository: findings/TRIAGE.md is for a person to read and pick
from.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
FINDINGS_DIR = PROJECT / "findings"

# Where a fix of each kind lands. The names are repositories or doc sets, not URLs.
TARGET_OF_FIX = {
    "learn_doc": "learn-docs",
    "discoverability": "learn-docs",
    "sample_or_quickstart": "learn-docs",
    "naming_or_disambiguation": "learn-docs",
    "agent_kit_rule": "agent-kit",
    "mcp_tool_or_description": "documentdb-mcp",
    "other": "other",
}
TARGET_REPO = {
    "learn-docs": "MicrosoftDocs (Azure DocumentDB pages on learn.microsoft.com)",
    "agent-kit": "Azure/documentdb-agent-kit",
    "documentdb-mcp": "microsoft/documentdb-mcp",
    "azure-mcp": "Azure/azure-mcp",
    "sample": "the generated sample (prompt or builder behaviour)",
    "other": "unassigned",
}
# Which MCP server a tool name belongs to, by prefix.
MCP_PREFIXES = {"documentdb_": "documentdb", "azure_": "azure", "learn_": "learn"}


@dataclass
class Finding:
    sample: str                 # run folder's sample slug
    run: str                    # run folder, relative to the repo
    stage: str                  # readiness | audit | build
    kind: str                   # doc_gap | confusion | information_gap | accelerator_missed | inventory | violated_practice | requirement
    target: str                 # learn-docs | agent-kit | documentdb-mcp | azure-mcp | sample | other
    priority: str               # high | medium | low
    topic: str
    detail: str
    proposed_change: str
    evidence: str


def _load(run_dir: Path, name: str) -> dict | None:
    path = run_dir / f"{name}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT).as_posix())
    except ValueError:
        return str(path)


def extract(run_dir: Path) -> list[Finding]:
    """Findings from one run folder. Missing stage files are skipped."""
    run_dir = run_dir.resolve()
    sample = run_dir.parent.name
    rel = _rel(run_dir)
    out: list[Finding] = []

    readiness = _load(run_dir, "02-readiness")
    if readiness:
        for c in readiness.get("confusions", []):
            if c.get("outcome") in ("correct", None):
                continue
            improvements = c.get("improvements") or []
            out.append(Finding(
                sample, rel, "readiness", "confusion",
                target="learn-docs" if c.get("confused_with") in ("none", "unknown") else "learn-docs",
                priority="high" if c.get("outcome") == "wrong" else "medium",
                topic=f"{c.get('question_id', '')} {c.get('question', '')}".strip()[:120],
                detail=f"Cold answer was {c.get('outcome')} (confused with {c.get('confused_with')}). "
                       f"Build risk: {c.get('build_risk', '')}",
                proposed_change=" | ".join(improvements) if improvements else c.get("why_the_confusion_arose", ""),
                evidence=f"{rel}/02-readiness.json confusions[{c.get('question_id', '')}]",
            ))
        for g in readiness.get("information_gaps", []):
            if isinstance(g, str):  # runs from before the title field existed
                g = {"title": "", "description": g}
            out.append(Finding(
                sample, rel, "readiness", "information_gap", "learn-docs", "medium",
                topic=(g.get("title") or g.get("description", ""))[:120],
                detail=g.get("description", ""), proposed_change="Document this where the agent looked.",
                evidence=f"{rel}/02-readiness.json information_gaps",
            ))
        for name in readiness.get("accelerators_missed", []):
            out.append(Finding(
                sample, rel, "readiness", "accelerator_missed", "agent-kit", "low",
                topic=str(name)[:120], detail="Exists and would have sped this build up, but was not installed.",
                proposed_change="Mention it in the kit's setup skill, or make the pipeline install it.",
                evidence=f"{rel}/02-readiness.json accelerators_missed",
            ))
        for r in readiness.get("inventory_recommendations", []):
            if r.get("worth_adding"):
                out.append(Finding(
                    sample, rel, "readiness", "inventory", "other", "low",
                    topic=str(r.get("name", ""))[:120], detail=r.get("recommendation", ""),
                    proposed_change=r.get("recommendation", ""),
                    evidence=f"{rel}/02-readiness.json inventory_recommendations",
                ))

    audit = _load(run_dir, "05-audit")
    if audit:
        for g in audit.get("doc_gaps", []):
            fix_type = g.get("proposed_fix_type", "other")
            out.append(Finding(
                sample, rel, "audit", "doc_gap", TARGET_OF_FIX.get(fix_type, "other"), g.get("priority", "medium"),
                topic=g.get("topic", "")[:120],
                detail=f"Missing: {g.get('what_was_missing', '')} Looked in: {g.get('where_searched', '')} "
                       f"Effect: {g.get('effect_on_this_build', '')}",
                proposed_change=f"[{fix_type}] {g.get('proposed_content', '')}",
                evidence=f"{rel}/doc-gaps.md",
            ))
        for c in audit.get("checks", []):
            if c.get("status") == "violated":
                out.append(Finding(
                    sample, rel, "audit", "violated_practice", "sample", "medium",
                    topic=c.get("topic") or c.get("category", ""),
                    detail=f"Violated: {c.get('practice', '')} Evidence: {c.get('evidence', '')}",
                    proposed_change=c.get("fix", ""), evidence=f"{rel}/05-audit.json checks",
                ))
            elif c.get("availability") in ("listed_not_found", "prior_knowledge_only") and c.get("what_would_help"):
                out.append(Finding(
                    sample, rel, "audit", "practice_not_public", "learn-docs", "low",
                    topic=c.get("topic") or c.get("category", ""),
                    detail=f"{c.get('availability')}: {c.get('practice', '')}",
                    proposed_change=c.get("what_would_help", ""), evidence=f"{rel}/05-audit.json checks",
                ))
        for r in audit.get("requirement_results", []):
            if r.get("status") in ("not_met", "partly_met") and r.get("cause") in ("skill_silent", "tool_unavailable"):
                out.append(Finding(
                    sample, rel, "audit", "requirement", "agent-kit" if r["cause"] == "skill_silent" else "documentdb-mcp",
                    "medium", topic=r.get("requirement", "")[:120],
                    detail=f"{r.get('status')} because {r.get('cause')}. {r.get('evidence', '')}",
                    proposed_change=r.get("smallest_fix", ""), evidence=f"{rel}/05-audit.json requirement_results",
                ))
    return out


def mcp_usage(run_dir: Path) -> dict:
    """Tool calls per MCP server and stage, from events.jsonl. Answers 'were the MCPs ever used?'."""
    counts: dict[str, Counter] = defaultdict(Counter)
    failures: Counter = Counter()
    path = run_dir / "events.jsonl"
    if not path.is_file():
        return {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        tool = str(e.get("tool", ""))
        server = next((s for p, s in MCP_PREFIXES.items() if tool.startswith(p)), "local")
        counts[server][e.get("stage", "?")] += 1
        if e.get("outcome") not in ("ok", None):
            failures[server] += 1
    return {s: {"by_stage": dict(c), "total": sum(c.values()), "failed": failures[s]} for s, c in counts.items()}


def run_dirs(runs_root: Path) -> list[Path]:
    return sorted(p for p in runs_root.glob("*/*") if p.is_dir() and (p / "run.json").is_file() or (p / "02-readiness.json").is_file())


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def write_triage(runs_root: Path, out_dir: Path = FINDINGS_DIR) -> tuple[int, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    all_findings: list[Finding] = []
    usage_rows: list[tuple[str, str, dict]] = []
    for rd in run_dirs(runs_root):
        all_findings += extract(rd)
        usage_rows.append((rd.parent.name, _rel(rd), mcp_usage(rd)))

    with (out_dir / "findings.jsonl").open("w", encoding="utf-8") as fh:
        for f in all_findings:
            fh.write(json.dumps(asdict(f), ensure_ascii=False) + "\n")

    # Group near-identical topics across samples so a gap hit by many runs rises to the top.
    groups: dict[tuple[str, str], list[Finding]] = defaultdict(list)
    for f in all_findings:
        groups[(f.target, _norm(f.topic)[:60])].append(f)
    order = {"high": 0, "medium": 1, "low": 2}

    lines = [
        "# Findings triage",
        "",
        f"{len(all_findings)} findings from {len(usage_rows)} runs, grouped by the repository that would change. "
        "Pick the ones to turn into PRs; nothing here has been filed anywhere. Regenerate with `python loop/findings.py`.",
        "",
    ]
    for target in ("agent-kit", "documentdb-mcp", "azure-mcp", "learn-docs", "sample", "other"):
        tgroups = sorted(
            ((k, v) for k, v in groups.items() if k[0] == target),
            key=lambda kv: (min(order.get(f.priority, 1) for f in kv[1]), -len(kv[1])),
        )
        if not tgroups:
            continue
        lines += [f"## {target}: {TARGET_REPO.get(target, target)}", "",
                  "| Pri | Samples | Topic | Proposed change | Evidence |", "|---|---|---|---|---|"]
        for (_, _), fs in tgroups:
            lead = sorted(fs, key=lambda f: order.get(f.priority, 1))[0]
            samples = sorted({f.sample for f in fs})
            shown = ", ".join(samples[:4]) + (f" +{len(samples) - 4}" if len(samples) > 4 else "")
            cell = lambda s: s.replace("|", "\\|").replace("\n", " ")[:240]
            lines.append(f"| {lead.priority} | {len(samples)} ({shown}) | {cell(lead.topic)} | {cell(lead.proposed_change)} | `{lead.evidence}` |")
        lines.append("")

    lines += ["## MCP usage per run", "", "Tool calls recorded in each run's events.jsonl, by server. "
              "A zero in documentdb or azure means the builder never touched that server.", "",
              "| Sample | Run | documentdb | azure | learn | local tools | failed calls |", "|---|---|---|---|---|---|---|"]
    for sample, rel, u in usage_rows:
        g = lambda s: u.get(s, {}).get("total", 0)
        failed = sum(v.get("failed", 0) for v in u.values())
        lines.append(f"| {sample} | `{rel}` | {g('documentdb')} | {g('azure')} | {g('learn')} | {g('local')} | {failed} |")
    (out_dir / "TRIAGE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(all_findings), len(usage_rows)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for f in extract(Path(sys.argv[1])):
            print(f"[{f.priority}] {f.target:<14} {f.kind:<18} {f.topic}")
        print(json.dumps(mcp_usage(Path(sys.argv[1])), indent=1))
    else:
        n, r = write_triage(PROJECT / "runs")
        print(f"{n} findings from {r} runs -> {FINDINGS_DIR / 'TRIAGE.md'}")
