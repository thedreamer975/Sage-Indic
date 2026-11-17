"""Phase 2E: Safe, Replaceable Generation Adapter.

Exports:
- GenerationConfig, GenerationProviderType, GenerationRequest, DraftAnswer
- GenerationError, ProviderUnavailableError, ProviderTimeoutError, ProviderAuthError, MalformedProviderResponseError
- PromptComposer
- GenerationProvider, MockGenerationProvider, ExternalAPIProvider, GenerationAdapter
- AnswerEligibility, VerifiedAnswerReport, verify_draft_answer
"""

from sage_indic.generation.adapter import (
    ExternalAPIProvider,
    GenerationAdapter,
    GenerationProvider,
    MockGenerationProvider,
    RawGenerationOutput,
)
from sage_indic.generation.pipeline import (
    AnswerEligibility,
    VerifiedAnswerReport,
    verify_draft_answer,
)
from sage_indic.generation.prompt import PromptComposer
from sage_indic.generation.types import (
    DraftAnswer,
    GenerationConfig,
    GenerationError,
    GenerationProviderType,
    GenerationRequest,
    MalformedProviderResponseError,
    ProviderAuthError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    UntrustedEvidenceError,
)

__all__ = [
    "GenerationConfig",
    "GenerationProviderType",
    "GenerationRequest",
    "DraftAnswer",
    "GenerationError",
    "ProviderUnavailableError",
    "ProviderTimeoutError",
    "ProviderAuthError",
    "MalformedProviderResponseError",
    "UntrustedEvidenceError",
    "PromptComposer",
    "GenerationProvider",
    "MockGenerationProvider",
    "ExternalAPIProvider",
    "RawGenerationOutput",
    "GenerationAdapter",
    "AnswerEligibility",
    "VerifiedAnswerReport",
    "verify_draft_answer",
]
