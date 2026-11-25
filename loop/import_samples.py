"""Turn the Azure DocumentDB Samples spreadsheet into one starter-prompt file per sample.

    python loop/import_samples.py <spreadsheet.xlsx> [--out samples]

Each sheet is an industry vertical. A sample begins on a row that has a title
plus an agent type or concepts; the next row carries its one-line description;
further rows in the Starter Prompt column are extra prompt paragraphs.

Writes samples/<vertical>/<NN>-<slug>.md (the prompt, nothing else, which is
what `main.py run` expects) and samples/index.json with the metadata.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from openpyxl import load_workbook

VERTICALS = {
    "Retail Samples": "retail",
    "Fintech Samples": "fintech",
    "Healthcare Samples": "healthcare",
    "Banking Samples": "banking",
    "Customer 360": "customer-360",
}


def slug(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:60].rstrip("-")


def parse_sheet(rows: list[tuple]) -> list[dict]:
    samples: list[dict] = []
    current: dict | None = None
    for title, agent, concepts, prompt in rows[1:]:
        title, agent, concepts, prompt = (str(c).strip() if c else "" for c in (title, agent, concepts, prompt))
        if title and (agent or concepts):
            current = {
                "title": title,
                "agent_type": "" if agent in ("", "—", "-") else agent,
                "concepts": concepts,
                "description": "",
                "prompt_paragraphs": [prompt] if prompt else [],
            }
            samples.append(current)
            continue
        if current is None:
            continue
        if title:
            current["description"] = (current["description"] + " " + title).strip()
        if prompt:
            current["prompt_paragraphs"].append(prompt)
    return samples


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx", type=Path)
    ap.add_argument("--out", type=Path, default=Path("samples"))
    args = ap.parse_args()

    wb = load_workbook(args.xlsx, read_only=True, data_only=True)
    index: list[dict] = []
    for ws in wb.worksheets:
        vertical = VERTICALS.get(ws.title, slug(ws.title))
        rows = [tuple(r[:4]) + (None,) * (4 - len(r)) for r in ws.iter_rows(values_only=True)]
        parsed = parse_sheet(rows)
        folder = args.out / vertical
        folder.mkdir(parents=True, exist_ok=True)
        for n, s in enumerate(parsed, 1):
            sample_id = f"{vertical}-{n:02d}"
            path = folder / f"{n:02d}-{slug(s['title'])}.md"
            path.write_text("\n\n".join(s["prompt_paragraphs"]).strip() + "\n", encoding="utf-8")
            index.append({
                "id": sample_id,
                "vertical": vertical,
                "title": s["title"],
                "agent_type": s["agent_type"],
                "concepts": s["concepts"],
                "description": s["description"],
                "prompt": str(path.as_posix()),
            })
        print(f"{ws.title:<20} {len(parsed):>3} samples -> {folder}")
    (args.out / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(index)} samples total -> {args.out / 'index.json'}")
    empty = [s["id"] for s in index if not Path(s["prompt"]).read_text().strip()]
    if empty:
        print("WARNING: empty prompts:", ", ".join(empty))


if __name__ == "__main__":
    main()
