# Phase 2D Evidence Corpus Specification

**Status:** Design proposal only. No corpus or source has been approved or created.

## Objective

Maintain a small, reproducible collection of Telugu-language factual documents selected from human-approved, source-identifiable publishers. The corpus exists only as a retrieval candidate pool. Inclusion does not establish that a statement is true; downstream verification belongs to Phase 2E.

Corpus source choice, topic coverage, and licensing approval are human decisions. Current candidates and unresolved terms are recorded in [phase2d_data_audit.md](phase2d_data_audit.md). No candidate there is currently approved as the factual evidence corpus.

## Evidence corpus and evaluation set are separate

The evidence corpus stores source documents and derived chunks. The evaluation set stores queries and independent human relevance judgments that point to corpus document/chunk IDs. Do not put query text, answer keys, relevance labels, or annotations into the indexed evidence text or metadata visible to the retriever.

## Proposed storage model

Keep a source-document record and a chunk record separately, in versioned UTF-8 JSONL files or another approved transparent format. Store original/raw content separately from normalized content; the original must be recoverable. No example values below represent actual sources or documents.

### Source-document fields

```json
{
  "document_id": "stable corpus-local identifier",
  "corpus_version": "version identifier",
  "source_name": "verified publisher or dataset name",
  "source_type": "publisher-approved source category",
  "publisher": "verified publisher",
  "source_url": "canonical page or dataset URL, when one exists",
  "source_record_id": "publisher/dataset stable identifier, when one exists",
  "source_revision": "release, commit, edition, or NOT APPLICABLE with reason",
  "title": "source title exactly as published",
  "language": "te",
  "script": "native | romanized | code_mixed | other verified value",
  "license_name": "exact source-declared license or UNVERIFIED",
  "license_url": "source license URL or UNVERIFIED",
  "license_evidence_url": "exact page/file supporting the license claim",
  "retrieved_at_utc": "acquisition timestamp, if fetched",
  "published_at": "source publication date or null with reason",
  "updated_at": "source update date or null with reason",
  "raw_text_ref": "content-addressed reference to original text",
  "raw_content_hash": "hash algorithm and digest of exact raw bytes/text",
  "normalized_text_ref": "content-addressed reference to normalized text",
  "normalized_content_hash": "hash algorithm and digest",
  "provenance_notes": "record IDs, extraction route, attribution, and transformation history",
  "retrieval_eligible": false,
  "eligibility_reason": "human-reviewed inclusion decision"
}
```

`retrieval_eligible` must remain false until source provenance, license, language/script, and inclusion review are complete. Unknown metadata is written explicitly as `UNVERIFIED`/null with a reason; never infer publisher, license, or dates.

### Chunk fields

```json
{
  "chunk_id": "stable corpus-local identifier",
  "document_id": "parent document identifier",
  "chunk_index": 0,
  "char_start": 0,
  "char_end": 0,
  "offset_unit": "Unicode code points in the referenced normalized text",
  "text": "exact normalized slice for these offsets",
  "raw_text_ref": "parent raw-text reference",
  "normalized_text_ref": "parent normalized-text reference",
  "source_name": "copied from verified parent metadata",
  "source_url": "copied from verified parent metadata when available",
  "title": "copied from verified parent metadata",
  "content_hash": "hash algorithm and digest of exact chunk text"
}
```

The chunk does not replace the source record. Parent provenance and license fields must remain joinable by immutable `document_id`; retrieval results must expose at least document ID, chunk ID, title, source name, source URL/record ID, license, offsets, and content hash.

## Document and normalization rules

- Preserve publisher/document boundaries and source identifiers; do not concatenate unrelated pages into one source document.
- Preserve raw bytes/text and source metadata before normalization. Normalized text is a separate derived representation.
- Use only conservative, documented Unicode and whitespace normalization after human review. Never remove meaningful Telugu code points or erase source formatting needed to interpret context.
- Record normalization implementation/version and hashes. Never use normalized text as a substitute for the original.
- Do not add machine-generated summaries, factual paraphrases, or answer text to evidence documents.
- Exclude records with unresolved provenance, unclear rights, unverifiable source attribution, or unsupported source language claims.

## Chunking rules

- Deterministic, versioned chunking, stable ordering, explicit offsets in the normalized parent text, and no empty chunks.
- Prefer document-native sections/paragraphs when their boundaries are recoverable; compare with fixed character-budget chunking only as an evaluation condition.
- Select chunk sizes/overlap after corpus inspection and pre-register them before evaluation. Do not claim an optimal size without measurements.
- Each chunk must be exactly recoverable from its parent text and offsets. Verify this invariant during ingestion and retrieval round-trip tests.
- Keep title and other parent metadata attached to each chunk/result, but do not duplicate evaluation labels into the index.

## Inclusion criteria (proposed; human approval required)

- Telugu factual content in the approved scope, with script/modality identified from the actual record.
- A stable primary source URL or record identifier and verifiable publisher/source attribution.
- Explicit, source-backed license/reuse terms compatible with the human-approved research use and any planned redistribution.
- Sufficient document context and publication/update information to identify stale content.
- A documented reason the source is appropriate evidence for the chosen factual domain.

## Exclusion criteria (proposed)

- Unknown or conflicting license/provenance, missing source identity, untraceable copied text, or source terms not approved.
- Pure linguistic examples, translation pairs, sentiment/social-media samples, generated answers, and tokenizer training text as factual evidence absent a separately justified use.
- Duplicate or near-duplicate documents unless preserved as explicit source/version relationships and controlled analytically.
- Retrieved content that consists only of instructions, advertisements, unsupported commentary, or generated text with no human-approved factual source basis.
- Text whose language/script is assumed from a dataset label rather than checked.

## Licensing and provenance gate

For each source, retain exact source name, publisher, canonical URL/ID, release/revision, license name and URL, license evidence snapshot/reference, retrieval timestamp, original and normalized hashes, attribution text, transformations, and eligibility decision. A dataset-level label is not enough if document-level content comes from third parties. Keep attribution and license obligations with redistributed derived material where required; if applicability is unclear, mark `UNVERIFIED — DO NOT USE` and ask the human reviewer to resolve it.

## Versioning and reproducibility

Corpus versions are immutable. A content, source, license, normalization, or chunk-boundary change creates a new corpus version. Record source manifest, acquisition timestamps, software/config versions, hash algorithm, document/chunk counts only after an actual ingestion, and a machine-readable change report. This specification contains no counts because no corpus exists.
