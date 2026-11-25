"""Compile findings/phase4/FILINGS.md from the consolidated filings in findings/phase4/filings/.

Each filing merges several phase-4 drafts into one issue, pull request or Learn feedback item.
This indexes them by repository for the owner's approve/hold decision. Nothing is filed here.

    python loop/phase4_filings.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
FILINGS = PROJECT / "findings" / "phase4" / "filings"
OUT = PROJECT / "findings" / "phase4" / "FILINGS.md"
REPO_TITLES = [
    ("abinav2307/azure-documentdb-agent-readiness", "The readiness pipeline (abinav2307/azure-documentdb-agent-readiness): ON HOLD, nothing is filed against the harness for now (owner decision 2026-11-25); share with its owner informally"),
    ("Azure/documentdb-agent-kit", "Azure/documentdb-agent-kit"),
    ("learn-docs", "Microsoft Learn: Azure DocumentDB pages (doc feedback)"),
    ("microsoft/documentdb-mcp", "microsoft/documentdb-mcp"),
]


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


def count_members(v: str) -> int:
    return len(re.findall(r"\d{3}-[a-z0-9-]+\.md", v))


def main() -> int:
    rows = []
    for f in sorted(FILINGS.glob("*.md")):
        fm = front_matter(f.read_text(encoding="utf-8"))
        if not fm:
            continue
        rows.append({"file": f, "id": fm.get("id", f.stem[:3]), "title": fm.get("title", f.stem), "repo": fm.get("repo", "other"),
                     "type": fm.get("type", ""), "status": fm.get("status", ""), "priority": fm.get("priority", "P3"),
                     "samples": fm.get("sample_count", ""), "members": count_members(fm.get("member_drafts", "")),
                     "open": fm.get("open_questions", "0"), "merged_from": fm.get("merged_from", "")})
    rows.sort(key=lambda r: (r["priority"], r["id"]))
    n_sme = sum(1 for r in rows if r["status"] == "needs_sme")
    L = ["# Phase 4 filings: consolidated issues and pull requests", "",
         f"{len(rows)} filings in `findings/phase4/filings/`, each merging the overlapping drafts the reviewer identified "
         f"(see REVIEW.md); first-pass filings that were merged again are archived in `filings/merged/`. {n_sme} carry status `needs_sme`: a claim in them needs an engineering or docs owner's answer "
         "before it goes public; the open questions are listed inside each file. Nothing has been filed. "
         "Sample counts come from one experiment run of 100 prompts and are stated as such in every filing.", ""]
    seen = set()
    for repo, heading in REPO_TITLES + [(r["repo"], r["repo"]) for r in rows if r["repo"] not in {x for x, _ in REPO_TITLES}]:
        if repo in seen:
            continue
        seen.add(repo)
        sub = [r for r in rows if r["repo"] == repo]
        if not sub:
            continue
        L += [f"## {heading}", "", "| Id | Pri | Status | Type | Samples | Drafts merged | Open q. | Title |", "|---|---|---|---|---|---|---|---|"]
        for r in sub:
            title = r["title"] + (f" (merges {r['merged_from']})" if r["merged_from"] else "")
            L.append(f"| [{r['id']}](filings/{r['file'].name}) | {r['priority']} | {r['status']} | {r['type']} | {r['samples']} | {r['members']} | {r['open']} | {title} |")
        L.append("")
    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"{len(rows)} filings -> {OUT.relative_to(PROJECT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
