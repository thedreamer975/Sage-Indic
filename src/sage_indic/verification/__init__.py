"""Claim-verification subsystem for SAGE-Indic (Phase 2D/2F).

Provides modular, verifiable interfaces and deterministic linguistic verification
for atomic claims against untrusted retrieved evidence packages.
"""

from sage_indic.verification.relation_verifier import RelationAwareClaimVerifier
from sage_indic.verification.types import (
    AtomicClaim,
    AtomicProposition,
    ClaimVerificationReport,
    EvidencePassage,
    VerificationOutcome,
    VerificationResult,
)
from sage_indic.verification.verifier import (
    ClaimVerifierProtocol,
    LinguisticClaimVerifier,
)

__all__ = [
    "AtomicClaim",
    "AtomicProposition",
    "EvidencePassage",
    "VerificationOutcome",
    "VerificationResult",
    "ClaimVerificationReport",
    "ClaimVerifierProtocol",
    "LinguisticClaimVerifier",
    "RelationAwareClaimVerifier",
]
