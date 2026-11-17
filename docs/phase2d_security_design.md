# Phase 2D Security Design

**Status:** Threat model and design only. No retriever, security defense, or security evaluation has been implemented.

## Boundary and objective

Phase 2D ends with an evidence package. It does not call an LLM, execute retrieved text, verify claims, or generate an answer.

```text
USER QUERY
   ↓
Phase 2A representation metadata
   ↓
Phase 2C query safety gate
   ↓
Phase 2B SAGE representation (frozen/read-only)
   ↓
Phase 2D retrieval
   ↓
EVIDENCE PACKAGE: untrusted source data + provenance
   ↓
Phase 2E claim extraction / verification (future phase)
```

Retrieved content is evidence data, never application control. Preserve it as a typed field with source metadata; never parse it as configuration or allow it to change index paths, retrieval settings, ranking logic, tool permissions, or application instructions. Downstream consumption must keep control text and evidence in distinct channels/fields and quote or delimit evidence as untrusted data. This design statement does not establish downstream prompt-injection security.

## Threats and intended controls

| Threat | Proposed design control | Implementation status | Test/observation |
|---|---|---|---|
| Instruction-like or malicious text in a retrieved document | Treat document/chunk text as opaque evidence payload; do not execute, interpret, or merge it with retrieval configuration. Any later model consumer must label evidence untrusted and separate it from trusted control. | Not implemented; design only | No security test or result exists. Future retrieval trust-boundary evaluation should verify data/config separation and preserve quoted text. |
| Malicious metadata/config injection | Validate source metadata against a fixed schema; keep retrieval configuration separate from document metadata; reject/escape unexpected control-bearing fields. | Not implemented | No test/result exists. Test that document fields cannot mutate configuration or index selection. |
| Poisoned or irrelevant chunks | Human-approved source inclusion, source-quality notes, corpus versioning, duplicate detection, retrieval judgments, and per-result provenance. | Not implemented | No corpus or result exists. These controls cannot guarantee evidence accuracy or prevent ranking manipulation. |
| Misleading source attribution | Require source URL/ID, publisher, title, license evidence, original hash, and parent document linkage; do not render unverifiable attribution as verified. | Not implemented | No provenance integrity test has been run. Unknown fields remain explicitly unverified. |
| Duplicate/near-duplicate documents and source manipulation | Deterministic duplicate/leakage audit, preserve source identity/version links, report source concentration. | Not implemented | No leakage report has been generated. Deduplication must not erase provenance or conceal separate publishers. |
| Contradictory evidence | Return distinct source passages with provenance and source dates; do not collapse conflicting statements into a single “truth.” | Not implemented | Contradiction handling is not evaluated. Resolution belongs to human/Phase 2E process. |
| Stale evidence | Preserve publication/update/retrieval timestamps and corpus version; define source-specific freshness policy with human approval. | Not implemented | No freshness policy/source update check exists. Retrieval time is not proof content remains current. |
| Provenance loss through normalization, chunking, indexing, or packaging | Carry immutable document/chunk IDs, offsets, hashes, and parent metadata end-to-end; validate chunk slices against retained source text. | Not implemented | No round-trip/provenance test exists. |
| Retrieval manipulation through queries or ranking parameters | Keep config application-owned and fixed per run; record parameters and deterministic tie rules; treat query text as data. | Not implemented | No retrieval implementation or adversarial evaluation exists. |

## Evidence-package contract (proposed)

Each result should preserve `query_id`, rank, retrieval method/config version, score, `document_id`, `chunk_id`, exact returned text, source name/publisher/URL or record ID, title, license evidence pointer, offsets, content hash, and corpus version. Missing or unverified source fields must be explicit. Consumers must not receive a passage with source context silently stripped.

The evidence package is not a trust label, factuality verdict, license guarantee, or instruction stream. Scores express ranker behavior only.

## Retrieval trust-boundary evaluation (future)

Use a separate controlled fixture with instruction-like strings embedded in evidence text. Check that:

- the exact content remains a data field and is not executed or transformed into a command;
- source/document/chunk metadata and hashes remain linked;
- ordering is deterministic for fixed input/configuration;
- document metadata cannot alter config, index path, method, or top-k;
- provenance cannot be dropped while serializing the package.

Report observed checks and failures. This narrow deterministic test does not establish resistance of a future generation model to prompt injection. No attack fixture or result is created in this documentation-only step.
