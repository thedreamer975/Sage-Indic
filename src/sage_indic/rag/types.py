"""Data types and schemas for Phase 2D: Retrieval-Augmented Evidence (RAG).

Defines:
- LicenseStatus and SourceType enumerations
- ContentHash value object
- SourceDocument schema (corpus specification compliant)
- DocumentChunk schema (recoverable offsets on normalized parent text)
- CorpusManifest schema
- RetrievalResult and EvidencePackage schemas (provenance-preserving data container)
- RetrievalConfig for swappable external components
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class LicenseStatus(str, Enum):
    """Explicit license verification status across discovery and review lifecycle."""

    DISCOVERED = "DISCOVERED"
    LICENSE_UNVERIFIED = "LICENSE_UNVERIFIED"
    UNVERIFIED = "UNVERIFIED"  # Backward-compatible alias
    LICENSE_REVIEWED = "LICENSE_REVIEWED"
    CONDITIONAL = "CONDITIONAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DO_NOT_USE = "DO_NOT_USE"


class SourceType(str, Enum):
    """Categorization of publisher-approved evidence sources."""

    SCHOLARLY = "SCHOLARLY"
    GOVERNMENT_OFFICIAL = "GOVERNMENT_OFFICIAL"
    CULTURAL_INSTITUTION = "CULTURAL_INSTITUTION"
    ENCYCLOPEDIC = "ENCYCLOPEDIC"
    NEWS_ARCHIVE = "NEWS_ARCHIVE"
    SYNTHETIC_TEST_ONLY = "SYNTHETIC_TEST_ONLY"


@dataclass(frozen=True)
class ContentHash:
    """Cryptographic content hash recording algorithm and hex digest."""

    algorithm: str
    digest: str

    def to_dict(self) -> dict[str, str]:
        return {"algorithm": self.algorithm, "digest": self.digest}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> ContentHash:
        return cls(algorithm=data["algorithm"], digest=data["digest"])


@dataclass
class SourceDocument:
    """Canonical source document record conforming to phase2d_corpus_spec.md."""

    document_id: str
    corpus_version: str
    source_name: str
    source_type: SourceType
    publisher: str
    title: str
    language: str
    script: str
    license_name: str
    license_status: LicenseStatus
    raw_text_ref: str
    raw_content_hash: ContentHash
    normalized_text_ref: str
    normalized_content_hash: ContentHash
    provenance_notes: str
    source_url: str | None = None
    source_record_id: str | None = None
    source_revision: str | None = None
    license_url: str | None = None
    license_evidence_url: str | None = None
    retrieved_at_utc: str | None = None
    published_at: str | None = None
    updated_at: str | None = None
    retrieval_eligible: bool = False
    eligibility_reason: str = "Pending human-reviewed inclusion decision."
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["source_type"] = self.source_type.value
        d["license_status"] = self.license_status.value
        d["raw_content_hash"] = self.raw_content_hash.to_dict()
        d["normalized_content_hash"] = self.normalized_content_hash.to_dict()
        return d


@dataclass
class DocumentChunk:
    """Deterministic chunk record with exact offsets into normalized parent text."""

    chunk_id: str
    document_id: str
    chunk_index: int
    char_start: int
    char_end: int
    text: str
    raw_text_ref: str
    normalized_text_ref: str
    source_name: str
    title: str
    content_hash: ContentHash
    offset_unit: str = "Unicode code points in the referenced normalized text"
    source_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["content_hash"] = self.content_hash.to_dict()
        return d


@dataclass
class CorpusManifest:
    """Versioned manifest summarizing an approved evidence corpus subset."""

    corpus_version: str
    created_at_utc: str
    document_count: int
    chunk_count: int
    documents: list[str] = field(default_factory=list)
    license_summary: dict[str, int] = field(default_factory=dict)
    script_summary: dict[str, int] = field(default_factory=dict)
    normalization_version: str = "1.0.0"
    chunker_version: str = "1.0.0"
    manifest_hash: ContentHash | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.manifest_hash:
            d["manifest_hash"] = self.manifest_hash.to_dict()
        return d


@dataclass(frozen=True)
class RetrievalConfig:
    """Configuration for retrieval execution (swappable, externalized)."""

    method: str = "BM25"
    top_k: int = 5
    similarity_metric: str = "cosine"
    model_name: str | None = None
    index_path: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Individual retrieved evidence item preserving full parent provenance."""

    rank: int
    score: float
    document_id: str
    chunk_id: str
    text: str
    title: str
    source_name: str
    publisher: str
    license_name: str
    char_start: int
    char_end: int
    content_hash: ContentHash
    corpus_version: str
    source_url: str | None = None
    license_evidence_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["content_hash"] = self.content_hash.to_dict()
        return d


@dataclass
class EvidencePackage:
    """Untrusted evidence payload bundled with query metadata and retrieval provenance.

    Retrieved content is strictly evidence DATA, never application control.
    """

    query_id: str
    query_text: str
    retrieval_method: str
    corpus_version: str
    results: list[RetrievalResult] = field(default_factory=list)
    config_fingerprint: str = ""
    is_safe_query: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "query_text": self.query_text,
            "retrieval_method": self.retrieval_method,
            "corpus_version": self.corpus_version,
            "results": [r.to_dict() for r in self.results],
            "config_fingerprint": self.config_fingerprint,
            "is_safe_query": self.is_safe_query,
            "metadata": self.metadata,
        }


class RelevanceGrade(int, Enum):
    """Relevance label schema conforming to Section 8 research specification.

    0 = Not relevant
    1 = Partially relevant
    2 = Fully relevant
    """

    NOT_RELEVANT = 0
    PARTIALLY_RELEVANT = 1
    FULLY_RELEVANT = 2


class QueryModality(str, Enum):
    """Script/language modality for Telugu factual retrieval evaluation."""

    NATIVE = "native"
    ROMANIZED = "romanized"
    CODE_MIXED = "code_mixed"


class AnnotationStatus(str, Enum):
    """Adjudication and review lifecycle state for evaluation items."""

    PENDING = "pending"
    HUMAN_VERIFIED = "human_verified"
    ADJUDICATED = "adjudicated"


@dataclass
class EvaluationQuery:
    """Machine-readable evaluation query record conforming to phase2d_evaluation_spec.md."""

    query_id: str
    query_text: str
    language: str = "te"
    modality: QueryModality = QueryModality.NATIVE
    query_family_id: str = ""
    query_provenance: str = ""
    variants: dict[str, str] = field(default_factory=dict)
    relevant_document_ids: list[str] = field(default_factory=list)
    relevant_chunk_ids: list[str] = field(default_factory=list)
    annotation_status: AnnotationStatus = AnnotationStatus.PENDING
    annotator_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["modality"] = self.modality.value
        d["annotation_status"] = self.annotation_status.value
        return d


@dataclass
class RelevanceJudgment:
    """Individual machine-readable relevance judgment and adjudication record."""

    query_id: str
    document_id: str
    chunk_id: str | None = None
    snippet: str = ""
    language: str = "te"
    script: str = "Telugu"
    annotator_scores: list[int] = field(default_factory=list)
    adjudicated_score: RelevanceGrade | None = None
    annotation_status: AnnotationStatus = AnnotationStatus.PENDING
    comments: str = ""
    provenance_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["annotation_status"] = self.annotation_status.value
        if self.adjudicated_score is not None:
            d["adjudicated_score"] = self.adjudicated_score.value
        return d

