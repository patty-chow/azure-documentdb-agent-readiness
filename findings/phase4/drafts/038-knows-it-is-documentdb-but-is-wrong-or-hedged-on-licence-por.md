---
title: "No action: model prior on DocumentDB engine licence/portability is already corrected by Learn overview and Agent Kit"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 3
findings: 3
bucket: confusion-Q15
verdicts:
  skipped: note-only
---

# Note only: DocumentDB engine licence/portability prior is already corrected by the sources

In 3 of 100 samples, gpt-5-mini's cold answer to readiness Q15 named the engine but hedged on whether it is open source and implied it cannot run elsewhere (graded partly_wrong, confused_with open_source_documentdb). In all three runs the grounded answer corrected this from the Learn overview ("Open source, with no SSPL", "Multicloud and hybrid"), the /oss page and the Agent Kit README/AGENTS.md; the kit's local-deployment skill covers the DocumentDB Gateway image (MongoDB 10260, PostgreSQL 9712) and dev/prod parity. No generated README shipped a wrong licence or portability claim, and no audit doc_gap recorded one.

Optional harness observation: the cold-quiz grader emits "improvements" even when its own grounding links already contain the proposed text, which inflates learn-docs gap counts.

## Skip reason
Model prior already corrected by existing sources before the build stage; the requested Learn and kit text already exists. Only residual is a pipeline-grader tweak, not a target-repo change.

## Verification
- skipped: note-only (checks not run per stage instructions). Skip reason is strong and evidence-backed, so status is drop.

## Finding ids
- F2432
- F2718
- F3400
