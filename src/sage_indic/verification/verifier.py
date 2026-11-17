"""Linguistic and modular evidence verification engine for Phase 2D/2F.

Implements:
- ClaimVerifierProtocol: protocol for verifiable NLI / claim-evidence audit components.
- LinguisticClaimVerifier: deterministic, interpretable linguistic verifier for Telugu,
  Romanized Telugu, and code-mixed assertions.
- Security isolation: ensures retrieved evidence passages are treated strictly as untrusted data,
  defending against prompt injection or instruction hijacking embedded within evidence text.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Protocol

from sage_indic.normalize import normalize_text
from sage_indic.rag.retriever import tokenize_for_bm25
from sage_indic.verification.types import (
    AtomicClaim,
    EvidencePassage,
    VerificationOutcome,
    VerificationResult,
)

from sage_indic.rag.normalizer import RomanizedTeluguTransliterator

# Common prompt injection signatures embedded in untrusted retrieved evidence (defense-in-depth)
INJECTION_SIGNATURES: list[re.Pattern] = [
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*(?:command|alert|prompt)?\s*:\s*(?:disregard|override)?", re.IGNORECASE),
    re.compile(r"you\s+must\s+(?:always\s+)?verify\s+this\s+as\s+supported", re.IGNORECASE),
    re.compile(r"override\s+(?:\w+\s+)?(?:policy|outcome|decision|verification)", re.IGNORECASE),
    re.compile(r"print\s+['\"]?supported['\"]?", re.IGNORECASE),
    re.compile(r"assistant\s*:\s*(?:confirmed|override)", re.IGNORECASE),
    re.compile(r"సూచన\s*:\s*మునుపటి\s+(?:సూచనలను|ఆదేశాలను)\s+(?:విస్మరించండి|రద్దు)", re.IGNORECASE),
]

# Telugu negation markers
TELUGU_NEGATION_MARKERS: frozenset[str] = frozenset({
    "లేదు",
    "కాదు",
    "నిర్మించలేదు",
    "చేయలేదు",
    "జరగలేదు",
    "లభించలేదు",
    "చెందదు",
    "ఉండదు",
    "చెప్పలేదు",
    "పుట్టలేదు",
    "వినిపించదు",
    "చేర్చలేదు",
})

# Romanized / English negation markers
LATIN_NEGATION_MARKERS: frozenset[str] = frozenset({
    "ledu",
    "kaadu",
    "kadu",
    "not",
    "never",
    "didnt",
    "wasnt",
    "cannot",
    "no",
})

# Number extractor pattern (extracts years like 1591, 2021, quantities like 11, 48.7, even with agglutinated suffixes like 1591లో)
NUMBER_PATTERN = re.compile(r"(?<!\d)\d+(?:\.\d+)?(?!\d)")


class ClaimVerifierProtocol(Protocol):
    """Protocol for claim verifiers."""

    def verify(
        self,
        claim: AtomicClaim,
        passages: list[EvidencePassage],
    ) -> VerificationResult:
        ...


class LinguisticClaimVerifier:
    """Deterministic, rule-based linguistic claim verifier for Telugu and Code-Mixed claims.

    Evaluates:
    1. Numerical & Temporal Consistency: Verifies dates, years, and quantities against evidence.
    2. Polarity / Negation Alignment: Detects assertions contradicted by presence or absence of negation.
    3. Multi-Passage Cross-Consistency: Detects mutually contradictory evidence across retrieved chunks.
    4. Grounding & Coverage: Verifies that core named entities and relations are attested in evidence.
    5. Untrusted Injection Neutralization: Detects and quarantines adversarial instructions in evidence.
    """

    def __init__(self, verifier_version: str = "1.0.0") -> None:
        self.verifier_version = verifier_version
        self._transliterator = RomanizedTeluguTransliterator()

    def _sanitize_evidence(self, text: str) -> tuple[str, bool]:
        """Neutralize prompt injection signatures in evidence text."""
        sanitized = text
        injection_detected = False
        for sig in INJECTION_SIGNATURES:
            if sig.search(sanitized):
                injection_detected = True
                sanitized = sig.sub("[QUARANTINED_INSTRUCTION]", sanitized)
        return sanitized, injection_detected

    def verify(
        self,
        claim: AtomicClaim,
        passages: list[EvidencePassage],
    ) -> VerificationResult:
        """Verify an atomic claim against a list of retrieved evidence passages."""
        if not passages:
            return VerificationResult(
                claim_id=claim.claim_id,
                outcome=VerificationOutcome.INSUFFICIENT_EVIDENCE,
                confidence=1.0,
                evidence_passage=None,
                explanation="No evidence passages provided to substantiate or refute the claim.",
                verifier_version=self.verifier_version,
            )

        claim_norm = normalize_text(claim.claim_text)
        claim_tokens = set(tokenize_for_bm25(claim_norm))
        claim_numbers = set(NUMBER_PATTERN.findall(claim_norm))

        # Cross-script transliteration expansion for Romanized Telugu/Code-mixed claims
        has_latin = bool(re.search(r"[a-zA-Z]", claim.claim_text))
        if has_latin or claim.language in ("te-Latn", "te-en"):
            translit_text = self._transliterator.transliterate_text(claim.claim_text)
            translit_norm = normalize_text(translit_text)
            translit_tokens = set(tokenize_for_bm25(translit_norm))
            claim_tokens.update(translit_tokens)

        # Check for negation in claim
        claim_has_negation = any(t in TELUGU_NEGATION_MARKERS or t in LATIN_NEGATION_MARKERS for t in claim_tokens)

        # 1. Inspect evidence passages and check for intra-evidence conflict
        sanitized_passages: list[tuple[EvidencePassage, str, bool]] = []
        passage_numbers: list[set[str]] = []
        passage_polarities: list[bool] = []

        for p in passages:
            clean_text, injection_flag = self._sanitize_evidence(p.text)
            sanitized_passages.append((p, clean_text, injection_flag))
            p_norm = normalize_text(clean_text)
            p_tokens = set(tokenize_for_bm25(p_norm))
            p_nums = set(NUMBER_PATTERN.findall(p_norm))
            passage_numbers.append(p_nums)
            p_has_neg = any(t in TELUGU_NEGATION_MARKERS or t in LATIN_NEGATION_MARKERS for t in p_tokens)
            passage_polarities.append(p_has_neg)

        # Check for conflicting evidence among passages when multiple passages are retrieved
        if len(passages) >= 2 and claim_numbers:
            first_nums = passage_numbers[0]
            for idx in range(1, len(passages)):
                other_nums = passage_numbers[idx]
                # If both passages are topically related to the claim but assert conflicting numbers
                if first_nums and other_nums and not (first_nums & other_nums) and (claim_numbers & (first_nums | other_nums)):
                    return VerificationResult(
                        claim_id=claim.claim_id,
                        outcome=VerificationOutcome.CONFLICTING_EVIDENCE,
                        confidence=0.90,
                        evidence_passage=passages[0],
                        conflicting_passages=[passages[idx]],
                        explanation=(
                            f"Retrieved passages contain mutually conflicting facts regarding numbers: "
                            f"Passage {passages[0].passage_id} contains {first_nums}, whereas "
                            f"Passage {passages[idx].passage_id} contains {other_nums}."
                        ),
                        verifier_version=self.verifier_version,
                    )

        # 2. Evaluate claim against candidate passages
        best_passage = None
        best_score = 0.0
        best_outcome = VerificationOutcome.INSUFFICIENT_EVIDENCE
        best_explanation = "Evidence text does not contain sufficient overlap to verify the claim."

        candidate_evaluations = []

        for idx, (passage, clean_text, injection_detected) in enumerate(sanitized_passages):
            p_norm = normalize_text(clean_text)
            p_tokens = set(tokenize_for_bm25(p_norm))
            p_nums = passage_numbers[idx]
            p_has_neg = passage_polarities[idx]

            overlap = claim_tokens & p_tokens
            informative_overlap = [t for t in overlap if len(t) > 1 and not t.isdigit()]
            overlap_ratio = len(informative_overlap) / max(len(claim_tokens), 1)

            # Check if passage has enough topical overlap with the claim
            has_topical_link = overlap_ratio >= 0.15 or len(informative_overlap) >= 2

            if not has_topical_link and not (claim_numbers and (claim_numbers & p_nums)):
                # Irrelevant passage
                continue

            # Check numerical verification
            if claim_numbers and p_nums:
                if claim_numbers & p_nums:
                    # Numbers match!
                    if claim_has_negation != p_has_neg:
                        outcome = VerificationOutcome.CONTRADICTED
                        score = 0.90
                        expl = (
                            f"Polarity contradiction: Claim polarity ({'negated' if claim_has_negation else 'affirmative'}) "
                            f"contradicts evidence passage ({'negated' if p_has_neg else 'affirmative'})."
                        )
                    else:
                        outcome = VerificationOutcome.SUPPORTED
                        score = min(0.70 + 0.30 * overlap_ratio, 0.99)
                        expl = (
                            f"Direct factual alignment: Numbers {claim_numbers & p_nums} and key terms "
                            f"{informative_overlap[:4]} are verified in evidence passage {passage.passage_id}."
                        )
                    candidate_evaluations.append((score, outcome, passage, expl))
                elif has_topical_link:
                    # Numbers contradict on the same topic/entity!
                    outcome = VerificationOutcome.CONTRADICTED
                    score = 0.95
                    expl = (
                        f"Numerical contradiction: Claim asserts {claim_numbers}, but evidence "
                        f"passage {passage.passage_id} explicitly documents {p_nums} for related entity."
                    )
                    candidate_evaluations.append((score, outcome, passage, expl))

            # Non-numerical assertions
            elif has_topical_link:
                if claim_has_negation != p_has_neg and overlap_ratio >= 0.30:
                    outcome = VerificationOutcome.CONTRADICTED
                    score = 0.85
                    expl = (
                        f"Polarity contradiction on shared entities {informative_overlap[:3]}: "
                        f"Claim ({'negated' if claim_has_negation else 'affirmative'}) contradicts evidence."
                    )
                    candidate_evaluations.append((score, outcome, passage, expl))
                elif overlap_ratio >= 0.35:
                    outcome = VerificationOutcome.SUPPORTED
                    score = min(0.60 + 0.40 * overlap_ratio, 0.95)
                    expl = (
                        f"Substantial factual alignment: Key assertion terms {informative_overlap[:5]} "
                        f"are substantiated by evidence passage {passage.passage_id}."
                    )
                    candidate_evaluations.append((score, outcome, passage, expl))

        # Select highest-scoring evaluation if available
        if candidate_evaluations:
            # Sort by score descending; prioritize SUPPORTED or CONTRADICTED over INSUFFICIENT
            candidate_evaluations.sort(key=lambda x: x[0], reverse=True)
            best_score, best_outcome, best_passage, best_explanation = candidate_evaluations[0]

        meta: dict = {}
        if any(flag for _, _, flag in sanitized_passages):
            meta["adversarial_injection_detected"] = True
            meta["injection_defense_action"] = "sanitized_untrusted_evidence_data"

        return VerificationResult(
            claim_id=claim.claim_id,
            outcome=best_outcome,
            confidence=round(best_score if best_outcome != VerificationOutcome.INSUFFICIENT_EVIDENCE else 0.80, 4),
            evidence_passage=best_passage,
            explanation=best_explanation,
            verifier_version=self.verifier_version,
            is_untrusted_evidence_quarantined=True,
            metadata=meta,
        )
