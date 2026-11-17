"""Structured response schemas for Phase 2G: Evidence-Grounded Response Composition.

The schemas deliberately keep four concepts separate:

1. ``RetrievedEvidence`` - untrusted passages supplied by the retriever.
2. ``AnswerClaim`` - an atomic statement extracted from an answer candidate.
3. ``Citation`` - a reference to a supplied passage, with an explicit flag saying
   whether that passage supports the claim (a valid ID is NOT proof of support).
4. ``AnswerResponse`` - the user-facing, serialisable result of the pipeline.

No field in this module fabricates confidence, citation validity, or factuality.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from sage_indic.rag.types import ContentHash
from sage_indic.types import LanguageCategory


class AnswerStatus(str, Enum):
    """User-facing status of a composed answer."""

    ANSWERED = "ANSWERED"
    PARTIALLY_ANSWERED = "PARTIALLY_ANSWERED"
    ABSTAINED = "ABSTAINED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class AnswerMode(str, Enum):
    """Which generation layer produced the visible answer."""

    DETERMINISTIC = "deterministic"
    LLM = "llm"
    LLM_FALLBACK = "llm_fallback"


class QueryIntent(str, Enum):
    """Coarse deterministic question type used for evidence sentence ranking."""

    WHEN = "WHEN"
    WHERE = "WHERE"
    WHO = "WHO"
    HOW_MANY = "HOW_MANY"
    DEFINITION = "DEFINITION"
    GENERAL = "GENERAL"


@dataclass
class RetrievedEvidence:
    """A retrieved passage exposed to the UI with full parent provenance."""

    evidence_id: str
    rank: int
    score: float
    document_id: str
    chunk_id: str
    title: str
    source_name: str
    publisher: str
    license_name: str
    license_url: str | None
    source_url: str | None
    text: str
    char_start: int
    char_end: int
    content_hash: ContentHash
    selected: bool = False
    used_in_answer: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["content_hash"] = self.content_hash.to_dict()
        return d


@dataclass
class AnswerClaim:
    """An atomic claim shown to the user together with its verification outcome."""

    claim_id: str
    text: str
    verification_status: str
    evidence_ids: list[str] = field(default_factory=list)
    citation_ids: list[str] = field(default_factory=list)
    explanation: str = ""
    caveat: str | None = None
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Citation:
    """Structured citation attached by the application, never by the language model.

    ``supports_claim`` is only True when the verifier returned SUPPORTED for the
    claim/evidence association. ``citation_id`` + ``chunk_id`` validity alone is
    explicitly insufficient.
    """

    citation_id: str
    evidence_id: str
    document_id: str
    chunk_id: str
    title: str
    source_name: str
    publisher: str
    license_name: str
    source_url: str | None = None
    quoted_text: str = ""
    char_start: int = 0
    char_end: int = 0
    claim_ids: list[str] = field(default_factory=list)
    verification_status: str = "INSUFFICIENT_EVIDENCE"
    supports_claim: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationSummary:
    """Aggregate verification state for the answer as a whole."""

    total_claims: int = 0
    supported_count: int = 0
    contradicted_count: int = 0
    insufficient_count: int = 0
    conflicting_count: int = 0
    all_claims_supported: bool = False
    cited_evidence_count: int = 0
    evidence_coverage: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GenerationMetadata:
    """Diagnostic metadata about optional LLM use and deterministic fallback."""

    requested_mode: AnswerMode = AnswerMode.DETERMINISTIC
    used_mode: AnswerMode = AnswerMode.DETERMINISTIC
    provider: str = "none"
    model: str | None = None
    provider_available: bool = False
    fallback_used: bool = False
    fallback_reason: str | None = None
    draft_rejected: bool = False
    rejection_reasons: list[str] = field(default_factory=list)
    raw_draft_kept_internally: bool = False
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["requested_mode"] = self.requested_mode.value
        d["used_mode"] = self.used_mode.value
        return d


@dataclass
class LatencyMetadata:
    """Measured stage latencies in milliseconds. Values are actual measurements."""

    detection_ms: float = 0.0
    safety_ms: float = 0.0
    retrieval_ms: float = 0.0
    composition_ms: float = 0.0
    generation_ms: float = 0.0
    total_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyInfo:
    """Safety decision attached to a response for transparency."""

    label: str = "SAFE"
    method: str = "not_run"
    confidence: float | None = None
    category: str = "SAFE_GENERAL"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QueryAnalysis:
    """Deterministic query understanding used for evidence selection."""

    intent: QueryIntent = QueryIntent.GENERAL
    content_terms: list[str] = field(default_factory=list)
    matched_terms: list[str] = field(default_factory=list)
    missing_terms: list[str] = field(default_factory=list)
    evidence_coverage: float = 0.0
    expanded_query: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["intent"] = self.intent.value
        return d


@dataclass
class AnswerResponse:
    """Complete user-facing response returned by the SAGE-Indic query pipeline."""

    request_id: str
    original_query: str
    detected_modality: LanguageCategory
    detected_modality_confidence: float
    normalized_query: str
    answer_text: str
    answer_status: AnswerStatus
    answer_claims: list[AnswerClaim] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    retrieved_evidence: list[RetrievedEvidence] = field(default_factory=list)
    verification_summary: VerificationSummary = field(default_factory=VerificationSummary)
    abstention_reason: str | None = None
    generation_metadata: GenerationMetadata = field(default_factory=GenerationMetadata)
    query_analysis: QueryAnalysis = field(default_factory=QueryAnalysis)
    safety: SafetyInfo = field(default_factory=SafetyInfo)
    warnings: list[str] = field(default_factory=list)
    latency_metadata: LatencyMetadata = field(default_factory=LatencyMetadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "original_query": self.original_query,
            "detected_modality": self.detected_modality.value,
            "detected_modality_confidence": round(self.detected_modality_confidence, 4),
            "normalized_query": self.normalized_query,
            "answer_text": self.answer_text,
            "answer_status": self.answer_status.value,
            "answer_claims": [c.to_dict() for c in self.answer_claims],
            "citations": [c.to_dict() for c in self.citations],
            "retrieved_evidence": [e.to_dict() for e in self.retrieved_evidence],
            "verification_summary": self.verification_summary.to_dict(),
            "abstention_reason": self.abstention_reason,
            "generation_metadata": self.generation_metadata.to_dict(),
            "query_analysis": self.query_analysis.to_dict(),
            "safety": self.safety.to_dict(),
            "warnings": list(self.warnings),
            "latency_metadata": self.latency_metadata.to_dict(),
        }
