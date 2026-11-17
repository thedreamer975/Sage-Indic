"""Decoupled generation-to-verification pipeline for Phase 2E.

Strictly preserves the separation between:
1. Generated draft answer (unverified model output)
2. Extracted candidate claims
3. Retrieved evidence passages (untrusted data)
4. Independent verification decisions
5. Final answer eligibility determination

CRITICAL RESEARCH INTEGRITY RULE:
An unverified draft answer is NEVER marked as verified by the generator.
INSUFFICIENT_EVIDENCE must NEVER be represented as proof that a claim is false.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from sage_indic.generation.types import DraftAnswer
from sage_indic.verification.relation_verifier import RelationAwareClaimVerifier
from sage_indic.verification.types import (
    EvidencePassage,
    VerificationOutcome,
    VerificationResult,
)


class AnswerEligibility(str, Enum):
    """Eligibility status of a generated answer for user presentation."""

    ELIGIBLE_GROUNDED = "ELIGIBLE_GROUNDED"  # All claims fully supported by evidence
    REQUIRES_CAVEAT = "REQUIRES_CAVEAT"  # Contains ungrounded or partially supported claims
    INELIGIBLE_CONTRADICTED = "INELIGIBLE_CONTRADICTED"  # Contains contradicted factual claims
    ABSTENTION = "ABSTENTION"  # Explicit evidence abstention (no evidence or unanswerable)


@dataclass
class VerifiedAnswerReport:
    """Audit report integrating draft generation with independent claim verification."""

    draft: DraftAnswer
    claim_results: list[VerificationResult]
    overall_eligibility: AnswerEligibility
    fully_supported_count: int
    contradicted_count: int
    insufficient_count: int
    conflicting_count: int
    is_verified: bool = True  # True only AFTER independent verification has executed!
    caveat_notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft": self.draft.to_dict(),
            "claim_results": [r.to_dict() for r in self.claim_results],
            "overall_eligibility": self.overall_eligibility.value,
            "fully_supported_count": self.fully_supported_count,
            "contradicted_count": self.contradicted_count,
            "insufficient_count": self.insufficient_count,
            "conflicting_count": self.conflicting_count,
            "is_verified": self.is_verified,
            "caveat_notes": self.caveat_notes,
            "metadata": self.metadata,
        }


def verify_draft_answer(
    draft: DraftAnswer,
    evidence_passages: list[EvidencePassage],
    verifier: RelationAwareClaimVerifier | None = None,
) -> VerifiedAnswerReport:
    """Independently audit each claim in a DraftAnswer against supplied evidence passages.

    Keeps generation and verification strictly decoupled.
    """
    active_verifier = verifier or RelationAwareClaimVerifier()

    # 1. Handle Explicit Abstention
    if draft.is_abstention:
        return VerifiedAnswerReport(
            draft=draft,
            claim_results=[],
            overall_eligibility=AnswerEligibility.ABSTENTION,
            fully_supported_count=0,
            contradicted_count=0,
            insufficient_count=0,
            conflicting_count=0,
            is_verified=True,
            caveat_notes=["Answer is an explicit abstention due to lack of evidence."],
        )

    # 2. Verify each extracted candidate claim
    claim_results: list[VerificationResult] = []
    supported_cnt = 0
    contradicted_cnt = 0
    insufficient_cnt = 0
    conflicting_cnt = 0

    for claim in draft.candidate_claims:
        res = active_verifier.verify(claim, evidence_passages)
        claim_results.append(res)

        if res.outcome == VerificationOutcome.SUPPORTED:
            supported_cnt += 1
        elif res.outcome == VerificationOutcome.CONTRADICTED:
            contradicted_cnt += 1
        elif res.outcome == VerificationOutcome.INSUFFICIENT_EVIDENCE:
            insufficient_cnt += 1
        elif res.outcome == VerificationOutcome.CONFLICTING_EVIDENCE:
            conflicting_cnt += 1

    # 3. Determine overall answer eligibility and caveats
    caveats: list[str] = []

    # Flag invalid or hallucinated citations
    if draft.invalid_citations:
        caveats.append(
            f"Model cited non-existent or unsupplied passage IDs: {draft.invalid_citations}. "
            "Citations do not establish entailment."
        )

    if contradicted_cnt > 0:
        eligibility = AnswerEligibility.INELIGIBLE_CONTRADICTED
        caveats.append(f"{contradicted_cnt} claim(s) directly contradicted by supplied evidence.")
    elif conflicting_cnt > 0:
        eligibility = AnswerEligibility.REQUIRES_CAVEAT
        caveats.append(f"{conflicting_cnt} claim(s) subject to conflicting evidence in corpus.")
    elif insufficient_cnt > 0:
        eligibility = AnswerEligibility.REQUIRES_CAVEAT
        caveats.append(
            f"{insufficient_cnt} claim(s) lack sufficient supporting evidence in corpus. "
            "Note: INSUFFICIENT_EVIDENCE indicates lack of proof, not proof of falsehood."
        )
    elif supported_cnt > 0 and supported_cnt == len(draft.candidate_claims):
        eligibility = AnswerEligibility.ELIGIBLE_GROUNDED
    else:
        eligibility = AnswerEligibility.REQUIRES_CAVEAT
        caveats.append("No claims were affirmatively supported by evidence.")

    return VerifiedAnswerReport(
        draft=draft,
        claim_results=claim_results,
        overall_eligibility=eligibility,
        fully_supported_count=supported_cnt,
        contradicted_count=contradicted_cnt,
        insufficient_count=insufficient_cnt,
        conflicting_count=conflicting_cnt,
        is_verified=True,
        caveat_notes=caveats,
    )
