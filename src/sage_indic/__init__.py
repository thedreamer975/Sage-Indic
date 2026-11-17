"""SAGE-Indic: Linguistically-Aware, Safe and Evidence-Grounded Indic LLM Framework."""

from sage_indic.config import Settings, get_settings
from sage_indic.detection import LanguageDetector, detect
from sage_indic.logging import get_logger, setup_logging
from sage_indic.normalize import normalize_text
from sage_indic.safety import (
    LexicalSafetyFilter,
    MultilingualSemanticClassifier,
    SageAwareSafetyGuardrail,
    SafetyCategory,
    SafetyLabel,
    SafetyResult,
)
from sage_indic.tokenizer import (
    BaseTokenizer,
    BpeBaselineTokenizer,
    SageTokenizer,
    UnigramBaselineTokenizer,
)
from sage_indic.types import InputRepresentation, LanguageCategory

from sage_indic.generation import (
    AnswerEligibility,
    DraftAnswer,
    GenerationAdapter,
    GenerationConfig,
    GenerationProviderType,
    GenerationRequest,
    MockGenerationProvider,
    VerifiedAnswerReport,
    verify_draft_answer,
)
from sage_indic.verification import (
    AtomicClaim,
    AtomicProposition,
    EvidencePassage,
    LinguisticClaimVerifier,
    RelationAwareClaimVerifier,
    VerificationOutcome,
    VerificationResult,
)

__version__ = "0.3.0"

__all__ = [
    "__version__",
    "BaseTokenizer",
    "BpeBaselineTokenizer",
    "InputRepresentation",
    "LanguageCategory",
    "LanguageDetector",
    "LexicalSafetyFilter",
    "MultilingualSemanticClassifier",
    "SageAwareSafetyGuardrail",
    "SafetyCategory",
    "SafetyLabel",
    "SafetyResult",
    "SageTokenizer",
    "Settings",
    "UnigramBaselineTokenizer",
    "detect",
    "get_logger",
    "get_settings",
    "normalize_text",
    "setup_logging",
    "AtomicClaim",
    "AtomicProposition",
    "EvidencePassage",
    "LinguisticClaimVerifier",
    "RelationAwareClaimVerifier",
    "VerificationOutcome",
    "VerificationResult",
    "GenerationConfig",
    "GenerationProviderType",
    "GenerationRequest",
    "DraftAnswer",
    "MockGenerationProvider",
    "GenerationAdapter",
    "AnswerEligibility",
    "VerifiedAnswerReport",
    "verify_draft_answer",
]
