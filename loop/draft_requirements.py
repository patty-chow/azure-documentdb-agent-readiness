"""Draft a reference requirements file for every sample that has none.

    python loop/draft_requirements.py              draft the missing ones
    python loop/draft_requirements.py --ids retail-03 --overwrite

The pipeline scores a finished sample against requirements/<prompt-stem>.md, which
the builder never sees. The first section (what the starter prompt asks for) is
drafted by the model from the sample's title, description, concepts and prompt.
The second section (what every gallery sample needs) is copied verbatim from the
existing retail example so it is identical across samples. Review the drafts
before phase 2 builds: they are a starting point, not a verdict.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
INDEX = PROJECT / "samples" / "index.json"
REQUIREMENTS = PROJECT / "requirements"
EXAMPLE = REQUIREMENTS / "retail-semantic-search.md"

INSTRUCTIONS = """You write reference requirements for a sample app in the Azure DocumentDB Samples Gallery.
Azure DocumentDB is Microsoft's managed MongoDB-compatible document database (compute tiers M30 and up,
resource type Microsoft.DocumentDB/mongoClusters). It is not Amazon DocumentDB and not Azure Cosmos DB for MongoDB (RU).

Given a sample's title, description, concepts and starter prompt, list what a publishable version must do
to satisfy the starter prompt. Rules:
- One requirement per bullet, each a distinct behaviour a reviewer can check in the code. 5 to 10 bullets.
- Only requirements the starter prompt asks for or clearly implies. Do not add generic hygiene items;
  a shared section appended later already requires environment-variable configuration, a reused client,
  a seed script, unit tests, pinned dependencies, infrastructure as code and a README.
- Name the language, framework, driver or ODM, agent framework, and DocumentDB feature the prompt names,
  exactly as it names them. Name the embedding model only if the prompt does.
- "Using the DocumentDB skill" at the start of a prompt refers to guidance installed in the coding agent,
  not to a component of the app. Never turn it into a requirement.
- State requirements at the level of detail the prompt uses. Never invent field names, collection names,
  route paths, status codes, function or tool names, index keys or output-field lists the prompt does not
  give; where a detail is needed to make a bullet checkable, write it as an example in parentheses
  ("e.g. ..."), not as the requirement.
- The agent type, the concept list and the prompt's descriptive phrases ("policy agent", "aggregation
  tool", "agent memory", "Single-agent", "Orchestration") describe roles and architecture, not
  identifiers. Require the role or component to exist and behave as described, never that code, names or
  strings match that wording exactly.
- Do not add error handling, retries, idempotency, concurrency protection, input validation, empty-result
  handling, logging or compliance safeguards unless the prompt asks for them. A requirement describes what
  the prompt asks the app to do, not how a production system would harden it.
- Do not require a value to be configurable, parameterised or exposed as a setting unless the prompt says
  so; a constant in code satisfies a prompt that gives no parameter.
- Do not require tests, demo or end-to-end scripts, example invocations, seed or sample data, citations,
  provenance metadata, document ids in outputs, structured logging of intermediate results or exposed
  internals "so a reviewer can verify". The auditor reads the code; a behaviour the code performs is
  already checkable.
- Do not write a separate bullet about connecting to Azure DocumentDB, where the connection string comes
  from, or that operations "really" target Azure DocumentDB. Name the driver or ODM inside the bullet
  that first uses it.
- Never add a bullet that restates an earlier one as a prohibition ("not client-side", "not simulated",
  "rather than ..."), as an assurance ("ensure that ...") or as a consequence of it.
- Service facts. Vector search in Azure DocumentDB means a cosmosSearch index of kind vector-ivf,
  vector-hnsw or vector-diskann on the embedding field, created in code and queried with $search /
  cosmosSearch (similarity COS, L2 or IP); embeddings are stored on documents, there are no index files.
  Full-text search uses a search index created with createSearchIndexes and queried with $search, never
  $text. There is no Atlas API, no "binary embedding" option and no "MongoDB API" account; the service is
  a cluster. When the prompt names vector search, the similarity runs in the database, not in app code,
  and one bullet requires the vector index to be created with dimensions matching the embedding model.
  Multi-document transactions use a session (withTransaction, or start/commit/abort).
- Use the name "Azure DocumentDB" for the service.
- Output only the bullets, each starting with "- ". No heading, no preamble."""


def gallery_section() -> str:
    text = EXAMPLE.read_text(encoding="utf-8")
    marker = "## What a gallery sample also needs"
    section = text[text.index(marker):].rstrip() + "\n"
    # The example is a retail catalog; the shared section must read the same for every vertical.
    return section.replace("loads sample products", "loads sample data").replace("for the catalog size", "for the sample's data size")


def make_client():
    from azure.identity import AzureCliCredential, get_bearer_token_provider
    from dotenv import load_dotenv
    from openai import AzureOpenAI
    import os

    load_dotenv(PROJECT / ".env")
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    model = os.environ["FACTORY_MODEL"]
    key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    if key:
        client = AzureOpenAI(azure_endpoint=endpoint, api_key=key, api_version="2024-12-01-preview")
    else:
        provider = get_bearer_token_provider(AzureCliCredential(), "https://cognitiveservices.azure.com/.default")
        client = AzureOpenAI(azure_endpoint=endpoint, azure_ad_token_provider=provider, api_version="2024-12-01-preview")
    return client, model


def draft(client, model: str, sample: dict) -> str:
    prompt_text = (PROJECT / sample["prompt"]).read_text(encoding="utf-8").strip()
    user = (f"Title: {sample['title']}\nAgent type: {sample['agent_type'] or 'not stated'}\n"
            f"Concepts: {sample['concepts']}\nDescription: {sample['description']}\n\nStarter prompt:\n{prompt_text}")
    response = client.chat.completions.create(
        model=model, max_completion_tokens=4000,
        messages=[{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": user}],
    )
    bullets = [ln.strip() for ln in (response.choices[0].message.content or "").splitlines() if ln.strip().startswith("- ")]
    if len(bullets) < 3:
        raise RuntimeError(f"model returned {len(bullets)} bullets")
    header = (
        f"# Reference requirements: {sample['title']}\n\n"
        "> Drafted by the model from the sample's title, description, concepts and starter prompt, then\n"
        "> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which\n"
        "> lines the starter prompt will miss, and the auditor checks each line against what was built.\n"
        ">\n"
        "> One requirement per bullet, each something a reviewer can check in the code.\n\n"
        "## What the starter prompt asks for\n\n"
    )
    return header + "\n".join(bullets) + "\n\n" + gallery_section()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--parallel", type=int, default=5)
    args = ap.parse_args()

    samples = json.loads(INDEX.read_text(encoding="utf-8"))
    todo = []
    for s in samples:
        if args.ids and s["id"] not in args.ids:
            continue
        target = REQUIREMENTS / f"{Path(s['prompt']).stem}.md"
        if target.is_file() and not args.overwrite:
            continue
        todo.append((s, target))
    print(f"{len(todo)} requirements file(s) to draft")
    if not todo:
        return 0

    client, model = make_client()
    failures = 0
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = {pool.submit(draft, client, model, s): (s, target) for s, target in todo}
        for fut in as_completed(futures):
            s, target = futures[fut]
            try:
                target.write_text(fut.result(), encoding="utf-8")
                count = len(re.findall(r"^- ", target.read_text(encoding="utf-8").split("## What a gallery")[0], re.M))
                print(f"  ok   {s['id']:<16} {count:>2} prompt requirements -> {target.relative_to(PROJECT)}")
            except Exception as exc:
                failures += 1
                print(f"  FAIL {s['id']:<16} {type(exc).__name__}: {exc}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
