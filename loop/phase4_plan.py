"""Compile findings/phase4/PLAN.md from the draft files in findings/phase4/drafts/.

Each draft starts with a YAML-ish front matter block (title, repo, type, status, priority,
sample_count, findings, bucket, verdicts). This script indexes them by repository, ordered by
status, priority and sample count, so the owner can approve, hold or drop each one before anything
is filed. Nothing is filed by this script.

    python loop/phase4_plan.py [--critique findings/phase4/REVIEW.md]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DRAFTS = PROJECT / "findings" / "phase4" / "drafts"
OUT = PROJECT / "findings" / "phase4" / "PLAN.md"
STATUS_ORDER = {"ready": 0, "ready_with_edits": 1, "hold": 2, "drop": 3}
REPO_TITLES = {
    "learn-docs": "Microsoft Learn: Azure DocumentDB pages",
    "Azure/documentdb-agent-kit": "Azure/documentdb-agent-kit",
    "microsoft/documentdb-mcp": "microsoft/documentdb-mcp",
    "abinav2307/azure-documentdb-agent-readiness": "The readiness pipeline (abinav2307/azure-documentdb-agent-readiness)",
    "sample-prompts-spreadsheet": "The sample prompts themselves",
    "none": "No repository (notes)",
}


def front_matter(text: str) -> dict[str, str]:
    m = re.match(r"\s*---\s*\n(.*?)\n---", text, re.S)
    fm: dict[str, str] = {}
    if not m:
        return fm
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"^[A-Za-z_]+:", line):
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
        elif key and line.startswith((" ", "\t", "-")):
            fm[key] = (fm.get(key, "") + " " + line.strip()).strip()
    return fm


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--critique", help="Markdown file to include as the reviewer's notes")
    args = ap.parse_args()

    rows = []
    for f in sorted(DRAFTS.glob("*.md")):
        fm = front_matter(f.read_text(encoding="utf-8"))
        if not fm:
            continue
        try:
            n = int(re.sub(r"\D", "", fm.get("sample_count", "0")) or 0)
        except ValueError:
            n = 0
        rows.append({"file": f, "title": fm.get("title", f.stem), "repo": fm.get("repo", "none"), "type": fm.get("type", ""),
                     "status": fm.get("status", "hold"), "priority": fm.get("priority", "P3"), "samples": n,
                     "bucket": fm.get("bucket", ""), "verdicts": fm.get("verdicts", "")})
    rows.sort(key=lambda r: (STATUS_ORDER.get(r["status"], 9), r["priority"], -r["samples"]))

    L = ["# Phase 4 plan: proposed issues and pull requests", "",
         f"{len(rows)} drafts in `findings/phase4/drafts/`, built from the default-arm findings of the 100-sample run and "
         "verified by three independent checks each (already covered? premise true? would the maintainer accept?). "
         "Nothing has been filed. Mark each row approve / hold / drop; `ready_with_edits` means the verifiers' corrections "
         "were applied to the body.", ""]
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    L += ["| Status | Drafts |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(counts.items(), key=lambda kv: STATUS_ORDER.get(kv[0], 9))] + [""]
    if args.critique and Path(args.critique).is_file():
        L += ["## Reviewer's notes", "", Path(args.critique).read_text(encoding="utf-8").strip(), ""]
    for repo in list(REPO_TITLES) + sorted({r["repo"] for r in rows} - set(REPO_TITLES)):
        sub = [r for r in rows if r["repo"] == repo]
        if not sub:
            continue
        L += [f"## {REPO_TITLES.get(repo, repo)}", "", "| # | Pri | Status | Type | Samples | Title | Draft |", "|---|---|---|---|---|---|---|"]
        for r in sub:
            L.append(f"| {r['file'].stem[:2]} | {r['priority']} | {r['status']} | {r['type']} | {r['samples']} | {r['title']} | [{r['file'].name}](drafts/{r['file'].name}) |")
        L.append("")
    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"{len(rows)} drafts -> {OUT.relative_to(PROJECT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
