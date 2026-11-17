"""Data types and schemas for Phase 2E: Safe, Replaceable Generation Adapter.

Defines:
- GenerationConfig: configuration for provider selection, timeouts, retries, and model parameters.
- GenerationRequest: validated query and bounded evidence package input.
- DraftAnswer: structured draft containing generated text, extracted claim candidates, citations, and abstention status.
- Typed exceptions for provider lifecycle, timeouts, authentication, and malformed outputs.

INVARIANT: DraftAnswer.is_verified is ALWAYS False upon generation.
The generation adapter must NEVER mark its own response as verified.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from sage_indic.rag.types import ContentHash, EvidencePackage, RetrievalResult
from sage_indic.types import LanguageCategory
from sage_indic.verification.types import AtomicClaim, EvidencePassage


class GenerationProviderType(str, Enum):
    """Supported provider backends for generation."""

    MOCK = "mock"
    LOCAL = "local"
    API = "api"


@dataclass(frozen=True)
class GenerationConfig:
    """Explicit configuration for generation adapter and provider."""

    provider: GenerationProviderType = GenerationProviderType.MOCK
    model_name: str = "mock-sage-indic-v1"
    temperature: float = 0.0  # Greedy/deterministic decoding by default
    max_tokens: int = 512
    timeout_seconds: float = 10.0
    max_retries: int = 2
    retry_backoff_factor: float = 1.5
    api_base_url: str | None = None
    api_key_env_var: str | None = None
    prompt_template_version: str = "1.0.0"
    max_evidence_chunks: int = 5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationRequest:
    """Bounded, provenance-preserving request for evidence-grounded generation."""

    query_id: str
    query_text: str
    language_category: LanguageCategory = LanguageCategory.TELUGU_NATIVE
    evidence_passages: list[EvidencePassage] = field(default_factory=list)
    system_instruction: str | None = None
    max_tokens: int = 512
    temperature: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_evidence_package(
        cls,
        package: EvidencePackage,
        language_category: LanguageCategory = LanguageCategory.TELUGU_NATIVE,
        max_chunks: int = 5,
    ) -> GenerationRequest:
        """Construct request from an existing Phase 2D EvidencePackage."""
        passages: list[EvidencePassage] = []
        for res in package.results[:max_chunks]:
            passages.append(EvidencePassage.from_retrieval_result(res))

        return cls(
            query_id=package.query_id,
            query_text=package.query_text,
            language_category=language_category,
            evidence_passages=passages,
            metadata={"corpus_version": package.corpus_version, "retrieval_method": package.retrieval_method},
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["language_category"] = self.language_category.value
        return d


@dataclass
class DraftAnswer:
    """Structured generation draft returned by the generation adapter.

    CRITICAL INVARIANT:
    is_verified is immutable False at generation time. Verification is a separate downstream stage.
    """

    request_id: str
    query_id: str
    answer_text: str
    language: str  # "te", "te-Latn", "te-en", "en"
    modality: str  # "native", "romanized", "code_mixed"
    candidate_claims: list[AtomicClaim] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)  # Validated supplied passage_ids
    invalid_citations: list[str] = field(default_factory=list)  # Hallucinated / missing passage_ids
    unsupported_aspects: list[str] = field(default_factory=list)
    is_abstention: bool = False
    abstention_reason: str | None = None
    # Distinguishes a model's own abstention from an adapter-level empty-evidence
    # guard. Empty evidence MUST NOT be reported as a successful model abstention.
    model_abstained: bool = False
    abstention_source: str | None = None  # "model_marker" | "no_evidence" | "not_abstained"
    model_id: str = "mock-sage-indic-v1"
    provider: str = "mock"
    latency_ms: float = 0.0
    is_verified: bool = False  # NEVER True at generation time!
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["candidate_claims"] = [c.to_dict() for c in self.candidate_claims]
        return d


# ---------------------------------------------------------------------------
# Typed Generation Exceptions
# ---------------------------------------------------------------------------


class GenerationError(Exception):
    """Base exception for all generation adapter errors."""


class ProviderUnavailableError(GenerationError):
    """Raised when the requested model provider service is unreachable or not configured."""


class ProviderTimeoutError(GenerationError):
    """Raised when provider invocation exceeds the configured timeout."""


class ProviderAuthError(GenerationError):
    """Raised when required credentials are missing, invalid, or unauthorized."""


class MalformedProviderResponseError(GenerationError):
    """Raised when provider returns invalid JSON, empty content, or contract violations."""


class UntrustedEvidenceError(GenerationError):
    """Raised when evidence package fails security boundary checks or contains malformed data."""
