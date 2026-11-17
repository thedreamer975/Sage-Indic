# Phase 2D — RAG Corpus Foundation Implementation & Validation Report

## 1. Executive Summary

This document reports the implementation and continuation increments of the **Phase 2D Corpus Foundation Layer** for SAGE-Indic.
In strict accordance with research-integrity directives:
- **NO factual evidence corpus** has been fabricated or approved.
- **NO retrieval index** has been instantiated.
- **NO relevance judgments** have been invented.
- **NO retrieval experiment** has been executed.
- Implementation is strictly confined to: schemas, validators, deterministic content hashing, conservative normalization wrapping, deterministic recoverable chunking, provenance chain verification, deterministic trust-boundary enforcers (retrieval and ingestion), the deterministic corpus ingestion pipeline, and machine-readable evaluation/annotation foundation schemas.

---

## 2. Implemented Architecture & Components

The package [`src/sage_indic/rag/`](file:///d:/Sage-Indic/src/sage_indic/rag/) contains the following modular components:

### 2.1 Data Models & Schemas ([`types.py`](file:///d:/Sage-Indic/src/sage_indic/rag/types.py))
- `LicenseStatus`: Explicit verification state model across the research lifecycle (`DISCOVERED`, `LICENSE_UNVERIFIED`, `UNVERIFIED`, `LICENSE_REVIEWED`, `CONDITIONAL`, `APPROVED`, `REJECTED`, `DO_NOT_USE`).
- `SourceType`: Categorization for scholarly, encyclopedic, governmental, or test-only records.
- `ContentHash`: Structured representation storing cryptographic algorithm (`sha256`) and hex digest.
- `SourceDocument`: Complete 23-field specification conforming to `docs/phase2d_corpus_spec.md`, enforcing provenance, separate raw and normalized text references/hashes, and default `retrieval_eligible = False`.
- `DocumentChunk`: Deterministic chunk schema tracking exact `char_start` and `char_end` offsets referencing Unicode code points in the normalized parent text.
- `CorpusManifest`: Versioned manifest schema tracking document count, chunk count, license distribution, and script distribution.
- `RetrievalConfig`: Swappable, externalized retrieval configuration.
- `RetrievalResult`: Retrieval record retaining full provenance to parent document, chunk ID, offsets, and license.
- `EvidencePackage`: Untrusted data payload packaging retrieved evidence without granting execution privileges.
- `RelevanceGrade`: Graded relevance scale (`0 = NOT_RELEVANT`, `1 = PARTIALLY_RELEVANT`, `2 = FULLY_RELEVANT`).
- `QueryModality`: Modality categorization (`NATIVE`, `ROMANIZED`, `CODE_MIXED`).
- `AnnotationStatus`: Annotation state (`PENDING`, `HUMAN_VERIFIED`, `ADJUDICATED`).
- `EvaluationQuery`: Machine-readable evaluation query record with variant mapping and query family linkage.
- `RelevanceJudgment`: Machine-readable relevance judgment capturing multi-annotator scores, adjudicated scores, and provenance.

### 2.2 Cryptographic Content Hashing ([`hash.py`](file:///d:/Sage-Indic/src/sage_indic/rag/hash.py))
- Deterministic SHA-256 computation via `compute_content_hash(content, algorithm="sha256")`.
- Integrity verification via `verify_content_hash(content, expected_hash)`.
- Replaces filename-based identity with cryptographic content digests for raw documents, normalized documents, and chunks.

### 2.3 Conservative Normalization ([`normalize.py`](file:///d:/Sage-Indic/src/sage_indic/rag/normalize.py))
- `EvidenceNormalizer` (version `1.0.0`) wraps the repository's conservative text normalization (`sage_indic.normalize.normalize_text`).
- Preserves raw source text as an immutable separate artifact.
- Normalizes to Unicode NFC, normalizes whitespace, and preserves valid Telugu virama + ZWNJ sequences for split conjuncts while removing orphaned zero-width spaces.
- Strictly prohibits linguistic rewriting, summarization, translation, or semantic correction.

### 2.4 Deterministic Chunking ([`chunking.py`](file:///d:/Sage-Indic/src/sage_indic/rag/chunking.py))
- `ParagraphChunker`: Splits normalized parent text along newline boundaries into distinct paragraph chunks with exact Unicode offsets.
- `FixedBudgetChunker`: Configurable character-window fallback with overlap (default: approximately 1000 characters, 50-character overlap), provided strictly as an experimental baseline condition.
- **Invariants Enforced**:
  1. Monotonic chunk indexing (`0, 1, 2, ...`).
  2. Stable identifiers formatted as `{document_id}#c{chunk_index:04d}`.
  3. No empty chunks (`char_end > char_start` and `len(chunk.text.strip()) > 0`).
  4. Exact Unicode code point slice alignment: `normalized_parent_text[char_start:char_end] == chunk.text`.

### 2.5 Strict Schema, Eligibility & Provenance Validation ([`validation.py`](file:///d:/Sage-Indic/src/sage_indic/rag/validation.py))
- `validate_source_document`: Rejects missing IDs, non-Telugu language tags, missing text references, or unapproved retrieval eligibility flags.
- `check_source_eligibility`: Rejects sources unless `license_status == LicenseStatus.APPROVED`, non-empty `license_evidence_url` exists, and non-pending `eligibility_reason` is documented. Explicitly rejects `DISCOVERED`, `LICENSE_UNVERIFIED`, `LICENSE_REVIEWED`, `CONDITIONAL`, `REJECTED`, and `DO_NOT_USE` sources.
- `validate_chunk_roundtrip`: Mathematically proves that `normalized_parent_text[char_start:char_end] == chunk.text` and verifies the chunk's content hash.
- `validate_provenance_chain`: Verifies that all chunks join to valid parent documents and parent metadata matches without desynchronization.
- `validate_corpus_manifest`: Verifies manifest counts and versioning.
- `validate_evaluation_query`: Verifies query ID, query text, Telugu language tag, and valid modality.
- `validate_relevance_judgment`: Verifies query ID, document ID, score bounds (`[0, 1, 2]`), and adjudication typing.

### 2.6 Deterministic Trust Boundary & Security ([`security.py`](file:///d:/Sage-Indic/src/sage_indic/rag/security.py))
- `TrustBoundaryEnforcer`: Enforces separation between application control plane (`RetrievalConfig`) and untrusted data plane (`EvidencePackage`).
- Caps results to authorized `top_k`.
- Strips unauthorized configuration overrides from query metadata.
- Preserves retrieved text as inert payload data without execution or parameter mutation.
- *Scientific Disclaimer*: This is a deterministic trust-boundary enforcer; it does NOT claim to prove LLM prompt-injection resistance for future generation stages.

### 2.7 Ingestion Pipeline & Ingestion Trust Boundary ([`ingestion.py`](file:///d:/Sage-Indic/src/sage_indic/rag/ingestion.py))
- `CorpusIngestionPipeline`: Executes deterministic ingestion from raw text and source metadata through hashing, conservative normalization, chunking, and validation.
- Enforces the **Ingestion Trust Boundary**:
  - Treats raw source text strictly as inert string DATA.
  - Guarantees that instruction-like text (e.g., "Ignore rules and mark approved") has zero capability to alter eligibility, configuration, or schemas.
  - Automatically rejects unauthorized transitions to `retrieval_eligible=True` for non-approved or unverified sources.
  - Yields an `IngestionResult` bundle containing the document, chunks, raw text, and normalized text.

### 2.8 Retriever Abstract Interfaces ([`retriever.py`](file:///d:/Sage-Indic/src/sage_indic/rag/retriever.py))
- Defines `BaseRetriever`, `BM25Retriever`, and `DenseRetriever`.
- Both `BM25Retriever` and `DenseRetriever` explicitly raise `NotImplementedError` stating that execution is blocked pending an approved factual evidence corpus manifest.

---

## 3. Test Suite & Empirical Verification

A comprehensive test suite was implemented in [`tests/test_rag.py`](file:///d:/Sage-Indic/tests/test_rag.py) with **37 unit and integration tests**:
- **Schema & Validation**: Valid source record, missing required fields, unverified license ineligibility, rejection of DO_NOT_USE, rejection of pending reasons.
- **Hashing**: SHA-256 determinism, digest changes on modification, separate raw vs. normalized digests.
- **Conservative Normalization**: Determinism, Telugu Unicode & virama preservation, valid Telugu ZWNJ preservation, in-memory raw text immutability.
- **Chunking & Round-Trip**: ParagraphChunker exact slice recovery, stable IDs & monotonic ordering, FixedBudgetChunker exact slice recovery, tamper detection (bounds, slice drift, text tampering).
- **Provenance Chain**: Valid parent document linkage, orphan chunk rejection, metadata desynchronization rejection, corpus manifest count verification.
- **Retrieval Security Boundary**: Inert encapsulation of adversarial instruction payloads, top-k result capping, configuration fingerprinting.
- **Retriever Execution Guards**: BM25 and Dense retriever blocked execution exceptions.
- **Licensing Lifecycle (Parametrized over 7 non-approved states)**: Proves that `DISCOVERED`, `LICENSE_UNVERIFIED`, `UNVERIFIED`, `LICENSE_REVIEWED`, `CONDITIONAL`, `REJECTED`, and `DO_NOT_USE` strictly fail eligibility and raise `ValidationError` if forced.
- **Ingestion Pipeline**: End-to-end ingestion flow, default 1000-char fixed-budget chunker fallback.
- **Ingestion Trust Boundary**: Ingestion of adversarial instructions, rejection of unauthorized approval promotion.
- **Evaluation & Annotation Schemas**: EvaluationQuery cross-modality validation (Native, Romanized, Code-Mixed), invalid query rejection, RelevanceJudgment score bound validation (`[0, 1, 2]`).

### Test Execution Results
- `pytest tests/test_rag.py`: **37 passed, 0 failed** in 10.11s.
- `pytest tests/`: **201 passed, 5 warnings** in 165.33s (100% repository pass rate across Phases 2A, 2B, 2C, and 2D).

---

## 4. Current Limitations & Blockers

1. **No Approved Corpus**: No factual Telugu evidence corpus has been approved or ingested. All tests use synthetic fixtures explicitly designated as `SYNTHETIC_TEST_ONLY`.
2. **Unresolved Licenses**: IndicQA and UD Telugu-MTG remain classified as `DO_NOT_USE` pending legal/provenance adjudication.
3. **No Retrieval Index**: No sparse BM25 index or dense vector index exists.
4. **No Relevance Judgments**: No evaluation queries or gold evidence passage pairs exist in `data/`.
5. **No Claim Verification / Generation**: Phases 2E and 2F have not been started.
