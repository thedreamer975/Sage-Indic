"""Data types and schemas for Phase 2D/2F: Atomic Claim Verification.

Defines:
- VerificationOutcome enumeration: SUPPORTED, CONTRADICTED, INSUFFICIENT_EVIDENCE, CONFLICTING_EVIDENCE
- AtomicClaim: decomposed atomic factual statement with language and query provenance
- EvidencePassage: untrusted evidence passage maintaining parent document and chunk provenance
- VerificationResult: audited decision object with confidence, explanation, and evidence link
- ClaimVerificationReport: aggregated evaluation container for claim veracity audits
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from sage_indic.rag.types import ContentHash, RetrievalResult


class VerificationOutcome(str, Enum):
    """Categorization of evidence verification outcome for an atomic claim."""

    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"


@dataclass(frozen=True)
class AtomicClaim:
    """An individual, indivisible factual assertion to be verified against evidence."""

    claim_id: str
    claim_text: str
    source_query_id: str | None = None
    language: str = "te"  # "te" (native), "te-Latn" (romanized), "te-en" (code-mixed), "en"
    modality: str = "native"
    context_sentence: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AtomicProposition:
    """A minimal, typed atomic factual statement extracted from a natural-language claim.

    Fields that cannot be reliably extracted remain None.
    Explicitly prevents hallucinating or inventing structured facts from ambiguous text.
    """

    proposition_id: str
    original_claim_id: str
    text: str
    subject: str | None = None
    predicate: str | None = None
    object_val: str | None = None
    polarity: bool = True  # True = affirmative, False = negated
    negation_marker: str | None = None
    quantity: float | int | None = None
    unit: str | None = None
    temporal: str | None = None
    source_span: tuple[int, int] | None = None
    language: str = "te"
    modality: str = "native"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidencePassage:
    """An untrusted evidence passage preserving cryptographic parent provenance."""

    passage_id: str  # chunk_id
    document_id: str
    text: str
    content_hash: ContentHash
    source_url: str | None = None
    char_start: int = 0
    char_end: int = 0
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_retrieval_result(cls, res: RetrievalResult) -> EvidencePassage:
        """Create an EvidencePassage from a verified RetrievalResult."""
        return cls(
            passage_id=res.chunk_id,
            document_id=res.document_id,
            text=res.text,
            content_hash=res.content_hash,
            source_url=res.source_url,
            char_start=res.char_start,
            char_end=res.char_end,
            title=res.title,
            metadata=dict(res.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["content_hash"] = self.content_hash.to_dict()
        return d


@dataclass
class VerificationResult:
    """Audit record of a claim verification decision.

    Confidence Score Meaning:
    - Bounded in [0.0, 1.0].
    - Represents the estimated probability / calibrated margin of entailment or contradiction.
    - Explicitly NOT semantic cosine similarity: semantic similarity measures topical relatedness,
      whereas entailment requires strict directional truth preservation.
    """

    claim_id: str
    outcome: VerificationOutcome
    confidence: float
    evidence_passage: EvidencePassage | None = None
    explanation: str = ""
    conflicting_passages: list[EvidencePassage] = field(default_factory=list)
    verifier_version: str = "1.0.0"
    is_untrusted_evidence_quarantined: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "claim_id": self.claim_id,
            "outcome": self.outcome.value,
            "confidence": round(self.confidence, 4),
            "evidence_passage": self.evidence_passage.to_dict() if self.evidence_passage else None,
            "explanation": self.explanation,
            "conflicting_passages": [p.to_dict() for p in self.conflicting_passages],
            "verifier_version": self.verifier_version,
            "is_untrusted_evidence_quarantined": self.is_untrusted_evidence_quarantined,
            "metadata": dict(self.metadata),
        }
        return d


@dataclass
class ClaimVerificationReport:
    """Aggregate audit report evaluating verification outcomes across a claim suite."""

    suite_name: str
    timestamp_utc: str
    total_claims: int
    n_supported: int
    n_contradicted: int
    n_insufficient: int
    n_conflicting: int
    accuracy: float
    results: list[VerificationResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite_name": self.suite_name,
            "timestamp_utc": self.timestamp_utc,
            "total_claims": self.total_claims,
            "n_supported": self.n_supported,
            "n_contradicted": self.n_contradicted,
            "n_insufficient": self.n_insufficient,
            "n_conflicting": self.n_conflicting,
            "accuracy": round(self.accuracy, 4),
            "results": [r.to_dict() for r in self.results],
            "metadata": dict(self.metadata),
        }
