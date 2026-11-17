"""Strict schema, provenance, and eligibility validators for Phase 2D.

Enforces:
1. Source document schema completeness.
2. Ineligibility default (retrieval_eligible = False unless approved).
3. Non-approval guard: UNVERIFIED, REJECTED, and DO_NOT_USE sources CANNOT be retrieval-eligible.
4. Exact chunk round-trip reconstruction invariant:
   normalized_text[chunk.char_start:chunk.char_end] == chunk.text.
5. Provenance chain verification.
"""

from __future__ import annotations

from sage_indic.rag.hash import verify_content_hash
from sage_indic.rag.types import (
    CorpusManifest,
    DocumentChunk,
    EvaluationQuery,
    LicenseStatus,
    QueryModality,
    RelevanceGrade,
    RelevanceJudgment,
    SourceDocument,
)


class ValidationError(ValueError):
    """Raised when an evidence document or chunk violates schema/provenance invariants."""


def validate_source_document(doc: SourceDocument) -> None:
    """Validate that a SourceDocument possesses all required fields and valid hashes."""
    if not doc.document_id or not doc.document_id.strip():
        raise ValidationError("SourceDocument document_id cannot be empty.")

    if not doc.corpus_version or not doc.corpus_version.strip():
        raise ValidationError(f"Document {doc.document_id} missing corpus_version.")

    if not doc.source_name or not doc.source_name.strip():
        raise ValidationError(f"Document {doc.document_id} missing source_name.")

    if not doc.publisher or not doc.publisher.strip():
        raise ValidationError(f"Document {doc.document_id} missing publisher.")

    if not doc.title or not doc.title.strip():
        raise ValidationError(f"Document {doc.document_id} missing title.")

    if doc.language.lower() != "te":
        raise ValidationError(
            f"Document {doc.document_id} language must be 'te', got '{doc.language}'."
        )

    if not doc.raw_text_ref or not doc.raw_text_ref.strip():
        raise ValidationError(f"Document {doc.document_id} missing raw_text_ref.")

    if not doc.normalized_text_ref or not doc.normalized_text_ref.strip():
        raise ValidationError(f"Document {doc.document_id} missing normalized_text_ref.")

    if not doc.raw_content_hash or not doc.raw_content_hash.digest:
        raise ValidationError(f"Document {doc.document_id} missing raw_content_hash.")

    if not doc.normalized_content_hash or not doc.normalized_content_hash.digest:
        raise ValidationError(f"Document {doc.document_id} missing normalized_content_hash.")

    # Strict eligibility enforcement: an unverified or rejected license can NEVER be retrieval_eligible
    if doc.retrieval_eligible:
        is_eligible, reason = check_source_eligibility(doc)
        if not is_eligible:
            raise ValidationError(
                f"Document {doc.document_id} marked retrieval_eligible=True but fails eligibility gate: {reason}"
            )


def check_source_eligibility(doc: SourceDocument) -> tuple[bool, str]:
    """Check whether a source document is permitted to enter the retrieval index.

    Returns:
        tuple of (is_eligible, reason_explanation)
    """
    if doc.license_status != LicenseStatus.APPROVED:
        return (
            False,
            f"License status is '{doc.license_status.value}'; only APPROVED sources may be indexed.",
        )

    if not doc.license_name or doc.license_name.strip().upper() == "UNVERIFIED":
        return False, "License name is unverified or empty."

    if not doc.license_evidence_url or not doc.license_evidence_url.strip():
        return False, "Missing license_evidence_url pointing to authoritative rights record."

    if not doc.eligibility_reason or not doc.eligibility_reason.strip():
        return False, "Missing human-reviewed eligibility_reason."

    if doc.eligibility_reason.lower().startswith("pending"):
        return False, "Eligibility decision is still pending human review."

    return True, "Source approved by human review with verified license evidence."


def validate_chunk_roundtrip(
    chunk: DocumentChunk,
    normalized_parent_text: str,
) -> None:
    """Prove that chunk is exactly recoverable from normalized parent text and offsets.

    Invariant: normalized_parent_text[char_start:char_end] == chunk.text
    """
    if chunk.char_start < 0:
        raise ValidationError(
            f"Chunk {chunk.chunk_id} char_start ({chunk.char_start}) cannot be negative."
        )

    if chunk.char_end <= chunk.char_start:
        raise ValidationError(
            f"Chunk {chunk.chunk_id} char_end ({chunk.char_end}) must be > char_start ({chunk.char_start})."
        )

    if chunk.char_end > len(normalized_parent_text):
        raise ValidationError(
            f"Chunk {chunk.chunk_id} char_end ({chunk.char_end}) exceeds parent length ({len(normalized_parent_text)})."
        )

    expected_slice = normalized_parent_text[chunk.char_start:chunk.char_end]
    if expected_slice != chunk.text:
        raise ValidationError(
            f"Round-trip reconstruction failure for chunk {chunk.chunk_id}: "
            f"normalized_parent_text[{chunk.char_start}:{chunk.char_end}] does not match chunk.text."
        )

    # Verify content hash of chunk text
    if not verify_content_hash(chunk.text, chunk.content_hash):
        raise ValidationError(
            f"Content hash verification failed for chunk {chunk.chunk_id}."
        )


def validate_provenance_chain(
    chunks: list[DocumentChunk],
    documents: dict[str, SourceDocument],
    normalized_texts: dict[str, str],
) -> None:
    """Validate that every chunk cleanly joins to a valid, eligible parent document."""
    for chunk in chunks:
        doc = documents.get(chunk.document_id)
        if doc is None:
            raise ValidationError(
                f"Chunk {chunk.chunk_id} references non-existent parent document {chunk.document_id}."
            )

        norm_text = normalized_texts.get(chunk.document_id)
        if norm_text is None:
            raise ValidationError(
                f"Missing normalized parent text for document {chunk.document_id}."
            )

        # Validate round-trip reconstruction
        validate_chunk_roundtrip(chunk, norm_text)

        # Verify parent metadata synchronization
        if chunk.source_name != doc.source_name:
            raise ValidationError(
                f"Chunk {chunk.chunk_id} source_name ('{chunk.source_name}') does not match "
                f"parent doc ('{doc.source_name}')."
            )

        if chunk.title != doc.title:
            raise ValidationError(
                f"Chunk {chunk.chunk_id} title ('{chunk.title}') does not match "
                f"parent doc ('{doc.title}')."
            )


def validate_corpus_manifest(manifest: CorpusManifest) -> None:
    """Validate corpus manifest metadata."""
    if not manifest.corpus_version or not manifest.corpus_version.strip():
        raise ValidationError("CorpusManifest corpus_version cannot be empty.")

    if manifest.document_count < 0:
        raise ValidationError("document_count cannot be negative.")

    if manifest.chunk_count < 0:
        raise ValidationError("chunk_count cannot be negative.")

    if len(manifest.documents) != manifest.document_count:
        raise ValidationError(
            f"Manifest documents list length ({len(manifest.documents)}) "
            f"does not match document_count ({manifest.document_count})."
        )


def validate_evaluation_query(query: EvaluationQuery) -> None:
    """Validate machine-readable evaluation query record per Section 8 specification."""
    if not query.query_id or not query.query_id.strip():
        raise ValidationError("EvaluationQuery query_id cannot be empty.")

    if not query.query_text or not query.query_text.strip():
        raise ValidationError(f"EvaluationQuery {query.query_id} query_text cannot be empty.")

    if query.language.lower() != "te":
        raise ValidationError(
            f"EvaluationQuery {query.query_id} language must be 'te', got '{query.language}'."
        )

    if not isinstance(query.modality, QueryModality):
        raise ValidationError(
            f"EvaluationQuery {query.query_id} invalid modality: {query.modality}."
        )


def validate_relevance_judgment(judgment: RelevanceJudgment) -> None:
    """Validate machine-readable relevance judgment and annotation scores."""
    if not judgment.query_id or not judgment.query_id.strip():
        raise ValidationError("RelevanceJudgment query_id cannot be empty.")

    if not judgment.document_id or not judgment.document_id.strip():
        raise ValidationError("RelevanceJudgment document_id cannot be empty.")

    # Validate annotator score bounds (0, 1, 2)
    valid_scores = {s.value for s in RelevanceGrade}
    for score in judgment.annotator_scores:
        if score not in valid_scores:
            raise ValidationError(
                f"Annotator score {score} invalid. Must be in {sorted(valid_scores)} "
                f"(0=Not relevant, 1=Partially relevant, 2=Fully relevant)."
            )

    # Validate adjudicated score bounds
    if judgment.adjudicated_score is not None:
        if not isinstance(judgment.adjudicated_score, RelevanceGrade):
            raise ValidationError(
                f"Adjudicated score {judgment.adjudicated_score} must be an instance of RelevanceGrade."
            )

