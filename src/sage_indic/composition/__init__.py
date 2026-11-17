"""Phase 2G: Evidence-grounded response composition and structured citations."""

from sage_indic.composition.composer import CompositionInputs, ResponseComposer
from sage_indic.composition.types import (
    AnswerClaim,
    AnswerMode,
    AnswerResponse,
    AnswerStatus,
    Citation,
    GenerationMetadata,
    LatencyMetadata,
    QueryAnalysis,
    QueryIntent,
    RetrievedEvidence,
    SafetyInfo,
    VerificationSummary,
)

__all__ = [
    "AnswerClaim",
    "AnswerMode",
    "AnswerResponse",
    "AnswerStatus",
    "Citation",
    "CompositionInputs",
    "GenerationMetadata",
    "LatencyMetadata",
    "QueryAnalysis",
    "QueryIntent",
    "ResponseComposer",
    "RetrievedEvidence",
    "SafetyInfo",
    "VerificationSummary",
]
