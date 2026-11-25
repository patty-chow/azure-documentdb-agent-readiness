# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 2 |
| operator | 1 |
| prompt | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:41:06+00:00

## D002 (build): I chose Python with FastAPI (single-process web service).

- **Instead of:** Node.js/Express; Python/FastAPI; Python/Flask
- **Because:** Python matches the prompt and installed environment; FastAPI provides easy file-upload endpoints and async support.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Use Python 3.10 or 3.11' and typical sample app; FastAPI is lightweight and suitable.
- **When:** 2026-11-25T05:41:33+00:00

## D003 (build): I chose the Hugging Face checkpoint 'openai/clip-vit-base-patch32' to produce 512-dimensional embeddings.

- **Instead of:** CLIP ViT-B/32 (512d); CLIP ViT-L/14 (768d); Custom smaller model
- **Because:** ViT-B/32 is a standard CLIP that produces 512-dim vectors and is widely available in transformers; keeps compute moderate for sample.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'CLIP model checkpoint not specified; ViT-B/32 commonly outputs 512-dim.'
- **When:** 2026-11-25T05:41:35+00:00

## D004 (build): I chose to use the documentdb_create_index MCP tool to create the vector-ivf index.

- **Instead of:** Create index via PyMongo createIndexes command; Use documentdb_create_index MCP tool
- **Because:** Using the MCP create_index tool ensures the index is created with DocumentDB-specific options without guessing PyMongo driver mapping; it also lets the MCP server verify index creation.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'documentdb MCP server is present with tools including documentdb_create_index' and vector-search skill shows createIndex examples.
- **When:** 2026-11-25T05:41:42+00:00

## D005 (build): I chose to use picsum.photos image URLs as permissive sample images for seeding.

- **Instead of:** Download sample images from Unsplash (requires API); Use picsum.photos (no API)
- **Because:** Simpler, no API keys, reproducible images via seed URL.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: sample images from permissive sources such as CC0/Unsplash; picsum provides simple seeded placeholder images without API keys.
- **When:** 2026-11-25T05:42:11+00:00
