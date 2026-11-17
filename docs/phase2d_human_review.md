# Phase 2D Human Review Decisions

**Status:** Decisions below are pending. No source or implementation is approved by this document.

## Data/source decisions

- [ ] Select and approve factual domains and evidence inclusion criteria for a small Telugu corpus.
- [ ] Approve each specific publisher/source, document collection, source version, and whether its material is authoritative enough for the intended question types.
- [ ] Review the source’s actual license, source-text rights, attribution, modification, share-alike/noncommercial terms, and whether storing or redistributing raw/normalized/chunked text or derived artifacts is allowed.
- [ ] Resolve the IndicQA CC-0 vs CC-BY-4.0 conflict with an authoritative record. Until then, keep it excluded.
- [ ] Resolve the UD Telugu-MTG conflict between README narrative and machine-readable license metadata before any use.
- [ ] Decide whether any resource is permitted only for query construction, representation experiments, evaluation, or actual corpus text; these roles must not be conflated.
- [ ] Approve retention, access, and distribution of source files, hashes, attribution/license records, and corpus artifacts.

## Query and annotation decisions

- [ ] Approve factual information needs and domain coverage for the retrieval benchmark.
- [ ] Decide how native Telugu, Romanized Telugu, and Telugu-English code-mixed versions will be obtained and human-checked for equivalent intent; approve whether derived variants are acceptable and how they will be identified.
- [ ] Approve corpus/query split and query-family grouping policy before inspecting final metrics.
- [ ] Approve the human annotation protocol, relevance scale, annotator count, disagreement/adjudication process, and treatment of unanswerable or out-of-corpus questions.
- [ ] Decide whether full-corpus judgments are feasible or a pooled protocol is required; approve pooling depth and residual limitations before evaluation.
- [ ] Review ambiguous source relevance and any proposed removal of documents or queries.

## Method and engineering decisions

- [ ] Approve document/chunk schema and provenance minimums, normalization policy, hash format, and corpus versioning.
- [ ] Approve chunk boundary candidates after corpus inspection; do not select an “optimal” setting absent measurement.
- [ ] Approve BM25 implementation/dependency choice after environment review.
- [ ] Decide whether dense retrieval is in scope. If yes, approve a specific verified model only after identity, Telugu coverage evidence, license, version, and availability are recorded.
- [ ] Approve whether frozen SAGE subword tokens are a retrieval condition; preserve Phase 2B artifacts and treat any retrieval benefit as an untested hypothesis until measured.
- [ ] Approve metric set, top-k values, document-vs-chunk evaluation unit, averaging/uncertainty method, and leakage thresholds before the sealed run.
- [ ] Review trust-boundary fixture design and the limits of its security claims.

## Phase transition

- [ ] Explicitly approve Phase 2D implementation after source/provenance and relevance-label blockers are resolved.
- [ ] Explicitly approve any future transition beyond Phase 2D; completion of retrieval does not authorize Phase 2E or Phase 2F.

## Recommended first implementation step after approval

After an approved source manifest and intended-use terms exist, implement **deterministic corpus ingestion, raw/normalized separation, metadata validation, content hashing, and document/chunk provenance checks** for only the approved subset. Add tests for those invariants and produce a corpus manifest. Do not build a retriever until the corpus is reviewable and the separate query/relevance annotation plan is approved.
