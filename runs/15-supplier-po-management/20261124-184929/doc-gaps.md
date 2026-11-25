# Documentation and tooling gaps: 15-supplier-po-management

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Beanie update validation behaviour

- **What was missing:** Clear, public documentation that states whether Beanie's update operations run Pydantic validators and, if not, the recommended application-layer pattern to validate updates.
- **Where the agent looked:** Searched repo files and Microsoft docs (quickstart) and noted 'searches_with_no_useful_result' in practice discovery: 'Azure DocumentDB beanie "validate Pydantic on update"' — no single authoritative page was found that explains best-practice for update validation with Beanie.
- **Effect on this build:** The sample implements create endpoints that use Pydantic models, but update endpoints were omitted. Uncertainty about whether updates would be validated by Beanie may have discouraged or mis-specified update endpoint design.
- **Suggested fix (learn_doc):** A short page in the Beanie quickstart or DocumentDB Python guidance titled 'Validating updates with Beanie' that explains: (1) whether beanie.update(...) and Document.set(...) run Pydantic validators; (2) recommended patterns for enforcing validation on updates (e.g. accept a Pydantic model DTO for updates, call model.parse_obj/update_local and then apply via replace/atomic update, or run manual validators); (3) example code for PATCH vs PUT with Beanie.

## [high] Dependency-version pins in quickstart

- **What was missing:** A prominent example in the Beanie quickstart (and in sample README) showing an explicit, tested set of pinned package versions for beanie/motor/pymongo/pydantic that are known to work together with the sample.
- **Where the agent looked:** Quickstart and indexing docs; discovered practice P07 recommends pinning, but the sample builder chose not to pin and experienced a runtime init_beanie TypeError.
- **Effect on this build:** Lack of pinned versions caused the seed/verification step to fail (Beanie init path error), preventing verification of index creation and aggregation results against the live cluster.
- **Suggested fix (discoverability):** Add a section 'Pinned package versions' to the Python Beanie quickstart and the sample README with a minimal reproducible requirements.txt block (example: beanie==X.Y.Z, motor==A.B.C, pymongo==M.N.O, pydantic-settings==P.Q) plus a short note explaining why pinning is important for verifying samples.

## [high] Seed script index creation / idempotent deploy step example

- **What was missing:** A canonical seed/deploy example that both creates seed data idempotently and explicitly provisions indexes (or shows beanie.ensure_indexes usage) with guidance on tolerating index build semantics in production.
- **Where the agent looked:** Quickstart and indexing docs; while models declare indexes, the sample relied on init_beanie and this wasn't verified due to the runtime error.
- **Effect on this build:** Without a clear pattern and an explicit index-create example, the sample left ambiguity about when and how indexes will be created and how that interacts with seed scripts, contributing to fragile verification.
- **Suggested fix (sample_or_quickstart):** Add a 'seed-and-index' script template: (1) call init_beanie, (2) call beanie's ensure_indexes or create_index API explicitly, (3) insert sample data only when absent, (4) show how to run the script twice safely. Provide a short note about unique-index building being foreground and recommended deploy-time behavior.

## [high] Decision to avoid pinning (model_default decisions)

- **What was missing:** A discoverable note in the sample quickstart that highlights the importance of pinning specific dependency versions for reproducible verification of samples.
- **Where the agent looked:** Quickstart docs; discovered practice P07 exists but the guidance is not always prominent to builders who pick 'latest'.
- **Effect on this build:** The builder chose unpinned dependencies and observed a runtime error; a prominent example would have prevented the issue.
- **Suggested fix (discoverability):** Add an explicit 'Reproducible installs' block to the Beanie quickstart and the DocumentDB Python sample guidance with a tested requirements.txt snippet and CI instructions to run pip install --use-feature=2020-resolver or similar reproducibility notes.

## [medium] Guidance on multi-document transactions

- **What was missing:** Clear guidance for sample authors on whether to avoid multi-document transactions or rely on them for correctness in Azure DocumentDB; practice P13 (prior_knowledge_only) indicates agent memory but no authoritative page was found explaining trade-offs for this service.
- **Where the agent looked:** Documentation and discovered practices; practice P13 is flagged prior_knowledge_only with no explicit Azure DocumentDB doc found in the discovery step.
- **Effect on this build:** The sample does not use transactions; lacking explicit service guidance may lead other builders to change modeling or add transactions without understanding service implications.
- **Suggested fix (learn_doc):** A short note on the main Azure DocumentDB docs: 'Transactions and modeling guidance' that states that Azure DocumentDB supports multi-document ACID transactions, when to avoid them for performance and modeling alternatives, and a code example showing a minimal transaction usage pattern for Motor/Beanie if needed.

