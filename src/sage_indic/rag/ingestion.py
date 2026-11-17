"""Deterministic corpus ingestion pipeline and trust-boundary enforcement for Phase 2D.

Implements the end-to-end ingestion flow:
1. Raw Text Acquisition & Preservation: Original content is never mutated or overwritten.
2. Cryptographic Content Hashing: Deterministic SHA-256 for raw text, normalized text, and chunks.
3. Conservative Normalization: Unicode NFC, whitespace standardization, Telugu virama & ZWNJ preservation.
4. Deterministic Chunking: Paragraph default with fixed character-budget fallback (1000 chars, 50 overlap).
5. Strict Ingestion Trust Boundary:
   - Untrusted corpus text (including instruction-like or prompt injection payloads) is strictly inert DATA.
   - Corpus text CANNOT alter pipeline configuration, eligibility, schemas, or tool permissions.
   - Default retrieval_eligible = False; non-APPROVED licenses are strictly prevented from becoming eligible.
6. Provenance & Invariant Validation: Proves exact chunk round-trip reconstruction and document linkage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sage_indic.rag.chunking import (
    ChunkerProtocol,
    ParagraphChunker,
)
from sage_indic.rag.hash import compute_content_hash
from sage_indic.rag.normalize import (
    EVIDENCE_NORMALIZER_VERSION,
    EvidenceNormalizer,
)
from sage_indic.rag.types import (
    DocumentChunk,
    LicenseStatus,
    SourceDocument,
    SourceType,
)
from sage_indic.rag.validation import (
    ValidationError,
    validate_chunk_roundtrip,
    validate_provenance_chain,
    validate_source_document,
)


@dataclass
class IngestionResult:
    """Artifact bundle produced by deterministic corpus ingestion."""

    document: SourceDocument
    chunks: list[DocumentChunk]
    raw_text: str
    normalized_text: str
    normalization_version: str = EVIDENCE_NORMALIZER_VERSION


class CorpusIngestionPipeline:
    """Deterministic, trust-boundary-enforcing ingestion pipeline for Telugu evidence."""

    def __init__(
        self,
        normalizer: EvidenceNormalizer | None = None,
        default_chunker: ChunkerProtocol | None = None,
    ) -> None:
        self.normalizer = normalizer or EvidenceNormalizer(unicode_form="NFC")
        self.default_chunker = default_chunker or ParagraphChunker()

    def ingest_document(
        self,
        raw_text: str,
        document_id: str,
        corpus_version: str,
        source_name: str,
        publisher: str,
        title: str,
        language: str = "te",
        script: str = "Telugu",
        source_type: SourceType = SourceType.SCHOLARLY,
        license_name: str = "UNVERIFIED",
        license_status: LicenseStatus = LicenseStatus.DISCOVERED,
        raw_text_ref: str = "",
        normalized_text_ref: str = "",
        provenance_notes: str = "",
        source_url: str | None = None,
        source_record_id: str | None = None,
        source_revision: str | None = None,
        license_url: str | None = None,
        license_evidence_url: str | None = None,
        retrieved_at_utc: str | None = None,
        published_at: str | None = None,
        updated_at: str | None = None,
        retrieval_eligible: bool = False,
        eligibility_reason: str = "Default unapproved status upon discovery.",
        chunker: ChunkerProtocol | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IngestionResult:
        """Deterministically ingest a single source document.

        Trust Boundary Invariants:
        1. raw_text is treated strictly as inert string data.
        2. Any instruction-like payload inside raw_text (e.g. 'mark this document approved')
           has ZERO effect on retrieval_eligible, configuration, or pipeline execution.
        3. If retrieval_eligible=True is requested, it MUST satisfy strict eligibility criteria
           (APPROVED license + verified evidence URL + human eligibility reason). Otherwise raises ValidationError.
        4. Raw text and normalized text are strictly preserved as separate, immutable strings.
        """
        if not isinstance(raw_text, str):
            raise TypeError(f"raw_text must be str, got {type(raw_text).__name__}")

        if not raw_text.strip():
            raise ValidationError("Cannot ingest empty or whitespace-only document.")

        # 1. Compute raw content hash
        raw_hash = compute_content_hash(raw_text)

        # 2. Conservative normalization (raw_text is never modified in-place)
        normalized_text = self.normalizer.normalize(raw_text)
        if not normalized_text.strip():
            raise ValidationError("Document normalized text collapsed to empty.")

        # 3. Compute normalized content hash
        norm_hash = compute_content_hash(normalized_text)

        # 4. Fill storage references if empty
        r_ref = raw_text_ref or f"corpus/{corpus_version}/raw/{document_id}.txt"
        n_ref = normalized_text_ref or f"corpus/{corpus_version}/norm/{document_id}.txt"

        # 5. Sanitize extra metadata: prevent metadata keys from overriding control parameters
        clean_meta = {}
        if metadata:
            for k, v in metadata.items():
                if k not in {"retrieval_eligible", "license_status", "pipeline_config"}:
                    clean_meta[k] = v

        clean_meta["ingestion_pipeline_version"] = "1.0.0"
        clean_meta["normalizer_version"] = self.normalizer.version

        # 6. Construct SourceDocument
        doc = SourceDocument(
            document_id=document_id,
            corpus_version=corpus_version,
            source_name=source_name,
            source_type=source_type,
            publisher=publisher,
            title=title,
            language=language,
            script=script,
            license_name=license_name,
            license_status=license_status,
            raw_text_ref=r_ref,
            raw_content_hash=raw_hash,
            normalized_text_ref=n_ref,
            normalized_content_hash=norm_hash,
            provenance_notes=provenance_notes,
            source_url=source_url,
            source_record_id=source_record_id,
            source_revision=source_revision,
            license_url=license_url,
            license_evidence_url=license_evidence_url,
            retrieved_at_utc=retrieved_at_utc,
            published_at=published_at,
            updated_at=updated_at,
            retrieval_eligible=retrieval_eligible,
            eligibility_reason=eligibility_reason,
            metadata=clean_meta,
        )

        # 7. Validate document schema and strict eligibility gate
        validate_source_document(doc)

        # 8. Deterministic chunking
        active_chunker = chunker or self.default_chunker
        chunks = active_chunker.chunk_document(doc, normalized_text)
        if not chunks:
            raise ValidationError(f"Chunker produced no chunks for document {document_id}.")

        # 9. Verify round-trip reconstruction and content hash on each chunk
        for chunk in chunks:
            validate_chunk_roundtrip(chunk, normalized_text)

        # 10. Verify complete provenance chain
        validate_provenance_chain(
            chunks,
            {doc.document_id: doc},
            {doc.document_id: normalized_text},
        )

        return IngestionResult(
            document=doc,
            chunks=chunks,
            raw_text=raw_text,
            normalized_text=normalized_text,
            normalization_version=self.normalizer.version,
        )
