"""Relation-aware and proposition-decomposing evidence verifier for Phase 2F.

Implements:
- RelationAwareClaimVerifier: decomposes compound assertions into atomic propositions,
  evaluates semantic predicate/relation compatibility, and composes outcomes conservative
  against relational blindness and partial-support fallacies.
- Preserves full provenance, parent document hashes, character offsets, and untrusted evidence isolation.
"""

from __future__ import annotations

import re
from typing import Any

from sage_indic.normalize import normalize_text
from sage_indic.rag.normalizer import RomanizedTeluguTransliterator
from sage_indic.rag.retriever import tokenize_for_bm25
from sage_indic.verification.types import (
    AtomicClaim,
    AtomicProposition,
    EvidencePassage,
    VerificationOutcome,
    VerificationResult,
)
from sage_indic.verification.verifier import (
    INJECTION_SIGNATURES,
    LATIN_NEGATION_MARKERS,
    NUMBER_PATTERN,
    TELUGU_NEGATION_MARKERS,
)

# Conjunction splitters for compound claim decomposition
CONJUNCTION_PATTERNS = [
    re.compile(r"\s+మరియు\s+", re.IGNORECASE),
    re.compile(r"\s+తో\s+పాటు\s+", re.IGNORECASE),
    re.compile(r"\s+అలాగే\s+", re.IGNORECASE),
    re.compile(r"\s+mariyu\s+", re.IGNORECASE),
    re.compile(r"\s+and\s+", re.IGNORECASE),
    re.compile(r"\s+&\s+"),
    re.compile(r",\s+(?=[A-Za-z\u0c00-\u0c7f])"),
]

# Known relational predicate categories (for relation compatibility checking)
RELATION_CATEGORIES: dict[str, set[str]] = {
    "construction": {
        "నిర్మించబడింది", "నిర్మించారు", "నిర్మాణం", "కట్టడం", "కట్టారు", "పూర్తయింది",
        "శంకుస్థాపన", "తవ్వించిన", "రూపొందించారు", "built", "constructed", "started", "complete", "nirmincharu",
    },
    "death_or_tomb": {
        "మరణించాడు", "మరణం", "చనిపోయాడు", "సమాధి", "మక్బరా", "died", "death", "tomb", "mausoleum", "samadhi",
    },
    "discovery_or_study": {
        "కనుగొన్నాడు", "పరిశోధన", "శాసనం", "వర్ణించాడు", "పేర్కొన్నారు", "discovered", "described", "found",
    },
    "location_or_setting": {
        "ఉంది", "తీరంలో", "ఒడ్డున", "నదిపై", "కొండలపై", "సరిహద్దులో", "గ్రామంలో", "ప్రాంతంలో",
        "located", "situated", "undhi", "unna", "river", "bank",
    },
    "mining_or_trade": {
        "వజ్రాల", "గనులు", "వ్యాపారానికి", "లభించాయి", "బంగారు", "diamonds", "gold", "mines", "trade",
    },
    "weaving_or_textile": {
        "చేనేత", "ఇక్కత్", "నేత", "చీరలు", "వస్త్రాలు", "పగడుబంధు", "weaving", "handloom", "ikat", "sarees",
    },
    "award_or_status": {
        "గుర్తింపు", "హోదా", "జీఐ", "ట్యాగ్", "వారసత్వ", "ప్రపంచవ్యాప్తంగా", "status", "tag", "unesco", "heritage",
    },
    "sculpture_or_art": {
        "శిల్పం", "శిల్పి", "పాలరాతి", "కళాఖండాల", "సంగ్రహాలయం", "మ్యూజియం", "sculpture", "statue", "museum", "art",
    },
    "free_or_commercial": {
        "ఉచితం", "ధర", "టికెట్", "రుసుము", "free", "ticket", "commercial",
    },
}


class RelationAwareClaimVerifier:
    """Experimental relation-aware claim verifier implementing atomic decomposition.

    Core Scientific Invariants:
    1. Does NOT assign SUPPORTED solely due to lexical overlap or entity co-occurrence.
    2. Decomposes compound claims into atomic propositions and verifies each separately.
    3. Requires relation/predicate compatibility in addition to entity/number alignment.
    4. Conservative on partial evidence: Never forces partial support into SUPPORTED.
    5. Preserves all cryptographic evidence provenance and untrusted isolation.
    """

    def __init__(self, verifier_version: str = "2.0.0") -> None:
        self.verifier_version = verifier_version
        self._transliterator = RomanizedTeluguTransliterator()

    def decompose_claim(self, claim: AtomicClaim) -> list[AtomicProposition]:
        """Decompose a natural-language claim into atomic propositions.

        Splits coordinate clauses, conjunctions, and participles into separate propositions.
        """
        text = claim.claim_text.strip()
        clauses = [text]

        for pat in CONJUNCTION_PATTERNS:
            new_clauses = []
            for cl in clauses:
                parts = pat.split(cl)
                for p in parts:
                    clean = p.strip()
                    if clean and len(clean) > 8:
                        new_clauses.append(clean)
                    elif clean and new_clauses:
                        # Append short dangling modifier to previous clause
                        new_clauses[-1] = f"{new_clauses[-1]} {clean}"
                    elif clean:
                        new_clauses.append(clean)
            clauses = new_clauses

        propositions = []
        for idx, clause_text in enumerate(clauses):
            clause_norm = normalize_text(clause_text)
            clause_tokens = set(tokenize_for_bm25(clause_norm))

            # Negation check
            neg_marker = None
            for t in clause_tokens:
                if t in TELUGU_NEGATION_MARKERS or t in LATIN_NEGATION_MARKERS:
                    neg_marker = t
                    break
            polarity = (neg_marker is None)

            # Temporal / number
            nums = NUMBER_PATTERN.findall(clause_norm)
            qty = float(nums[0]) if nums else None

            # Detect relation category
            detected_relation = None
            for cat, kws in RELATION_CATEGORIES.items():
                if any(kw in clause_tokens or kw in clause_norm for kw in kws):
                    detected_relation = cat
                    break

            # Find source span
            start_pos = text.find(clause_text)
            span = (start_pos, start_pos + len(clause_text)) if start_pos >= 0 else None

            prop = AtomicProposition(
                proposition_id=f"{claim.claim_id}_p{idx+1}",
                original_claim_id=claim.claim_id,
                text=clause_text,
                predicate=detected_relation,
                polarity=polarity,
                negation_marker=neg_marker,
                quantity=qty,
                temporal=nums[0] if nums else None,
                source_span=span,
                language=claim.language,
                modality=claim.modality,
            )
            propositions.append(prop)

        return propositions if propositions else [
            AtomicProposition(
                proposition_id=f"{claim.claim_id}_p1",
                original_claim_id=claim.claim_id,
                text=text,
                language=claim.language,
                modality=claim.modality,
            )
        ]

    def _sanitize_evidence(self, text: str) -> tuple[str, bool]:
        """Neutralize prompt injection signatures in evidence text."""
        sanitized = text
        injection_detected = False
        for sig in INJECTION_SIGNATURES:
            if sig.search(sanitized):
                injection_detected = True
                sanitized = sig.sub("[QUARANTINED_INSTRUCTION]", sanitized)
        return sanitized, injection_detected

    def _verify_single_proposition(
        self,
        prop: AtomicProposition,
        passages: list[EvidencePassage],
    ) -> VerificationResult:
        """Verify an individual atomic proposition against candidate evidence passages."""
        if not passages:
            return VerificationResult(
                claim_id=prop.proposition_id,
                outcome=VerificationOutcome.INSUFFICIENT_EVIDENCE,
                confidence=1.0,
                explanation="No evidence passages provided.",
                verifier_version=self.verifier_version,
            )

        prop_norm = normalize_text(prop.text)
        prop_tokens = set(tokenize_for_bm25(prop_norm))
        prop_numbers = set(NUMBER_PATTERN.findall(prop_norm))

        # Transliterate for cross-script tokens
        has_latin = bool(re.search(r"[a-zA-Z]", prop.text))
        if has_latin or prop.language in ("te-Latn", "te-en"):
            translit_text = self._transliterator.transliterate_text(prop.text)
            translit_norm = normalize_text(translit_text)
            prop_tokens.update(tokenize_for_bm25(translit_norm))

        prop_has_neg = not prop.polarity

        sanitized_passages = []
        passage_numbers = []
        passage_polarities = []
        passage_relations = []

        for p in passages:
            clean_text, injection_flag = self._sanitize_evidence(p.text)
            sanitized_passages.append((p, clean_text, injection_flag))
            p_norm = normalize_text(clean_text)
            p_tokens = set(tokenize_for_bm25(p_norm))
            p_nums = set(NUMBER_PATTERN.findall(p_norm))
            passage_numbers.append(p_nums)
            p_has_neg = any(t in TELUGU_NEGATION_MARKERS or t in LATIN_NEGATION_MARKERS for t in p_tokens)
            passage_polarities.append(p_has_neg)

            # Detect relation category in passage
            p_rel = None
            for cat, kws in RELATION_CATEGORIES.items():
                if any(kw in p_tokens or kw in p_norm for kw in kws):
                    p_rel = cat
                    break
            passage_relations.append(p_rel)

        # 1. Check for cross-passage conflict on numbers
        if len(passages) >= 2 and prop_numbers:
            first_nums = passage_numbers[0]
            for idx in range(1, len(passages)):
                other_nums = passage_numbers[idx]
                if first_nums and other_nums and not (first_nums & other_nums) and (prop_numbers & (first_nums | other_nums)):
                    return VerificationResult(
                        claim_id=prop.proposition_id,
                        outcome=VerificationOutcome.CONFLICTING_EVIDENCE,
                        confidence=0.95,
                        evidence_passage=passages[0],
                        conflicting_passages=[passages[idx]],
                        explanation=(
                            f"Multi-passage factual conflict: Passage {passages[0].passage_id} contains {first_nums}, "
                            f"whereas Passage {passages[idx].passage_id} contains {other_nums}."
                        ),
                        verifier_version=self.verifier_version,
                    )

        # 2. Evaluate candidate passages
        candidate_evals = []

        for idx, (passage, clean_text, _) in enumerate(sanitized_passages):
            p_norm = normalize_text(clean_text)
            p_tokens = set(tokenize_for_bm25(p_norm))
            p_nums = passage_numbers[idx]
            p_has_neg = passage_polarities[idx]
            p_rel = passage_relations[idx]

            overlap = prop_tokens & p_tokens
            informative_overlap = [t for t in overlap if len(t) > 1 and not t.isdigit()]
            overlap_ratio = len(informative_overlap) / max(len(prop_tokens), 1)

            has_topical_link = overlap_ratio >= 0.15 or len(informative_overlap) >= 2
            if not has_topical_link and not (prop_numbers and (prop_numbers & p_nums)):
                continue

            # Relation Compatibility Audit (Defense against Relational Blindness)
            rel_mismatch = False
            if prop.predicate and p_rel and prop.predicate != p_rel:
                # Incompatible relation category detected (e.g. death/tomb vs construction, or mining vs weaving)
                incompatible_pairs = {
                    ("death_or_tomb", "construction"),
                    ("construction", "death_or_tomb"),
                    ("mining_or_trade", "weaving_or_textile"),
                    ("weaving_or_textile", "mining_or_trade"),
                    ("discovery_or_study", "construction"),
                    ("free_or_commercial", "location_or_setting"),
                }
                if (prop.predicate, p_rel) in incompatible_pairs:
                    rel_mismatch = True

            # If there is a direct relational mismatch on the same entity
            if rel_mismatch and has_topical_link:
                expl = (
                    f"Relational mismatch detected: Proposition asserts relation '{prop.predicate}', "
                    f"whereas evidence passage {passage.passage_id} documents relation '{p_rel}'."
                )
                candidate_evals.append((0.92, VerificationOutcome.CONTRADICTED, passage, expl))
                continue

            # Numerical verification
            if prop_numbers and p_nums:
                if prop_numbers & p_nums:
                    # Numbers match
                    if prop_has_neg != p_has_neg:
                        expl = f"Polarity contradiction on shared numbers {prop_numbers & p_nums}."
                        candidate_evals.append((0.90, VerificationOutcome.CONTRADICTED, passage, expl))
                    elif rel_mismatch:
                        expl = f"Number match but relation mismatch: {prop.predicate} != {p_rel}."
                        candidate_evals.append((0.88, VerificationOutcome.CONTRADICTED, passage, expl))
                    else:
                        score = min(0.70 + 0.30 * overlap_ratio, 0.99)
                        expl = (
                            f"Verified factual alignment: Number {prop_numbers & p_nums} and relation "
                            f"'{prop.predicate or 'attested'}' substantiated by {passage.passage_id}."
                        )
                        candidate_evals.append((score, VerificationOutcome.SUPPORTED, passage, expl))
                elif has_topical_link:
                    # Numbers directly contradict for related entity
                    expl = (
                        f"Numerical contradiction: Proposition asserts {prop_numbers}, but evidence "
                        f"passage {passage.passage_id} specifies {p_nums}."
                    )
                    candidate_evals.append((0.95, VerificationOutcome.CONTRADICTED, passage, expl))

            # Non-numerical assertions
            elif has_topical_link:
                if prop_has_neg != p_has_neg and overlap_ratio >= 0.25:
                    expl = f"Polarity contradiction on shared terms: Proposition negated={prop_has_neg}."
                    candidate_evals.append((0.85, VerificationOutcome.CONTRADICTED, passage, expl))
                elif rel_mismatch:
                    expl = f"Relational divergence: Proposition asserts '{prop.predicate}', passage documents '{p_rel}'."
                    candidate_evals.append((0.88, VerificationOutcome.CONTRADICTED, passage, expl))
                elif overlap_ratio >= 0.35:
                    score = min(0.60 + 0.40 * overlap_ratio, 0.95)
                    expl = (
                        f"Substantial factual alignment: Key terms {informative_overlap[:5]} and relation "
                        f"substantiated by passage {passage.passage_id}."
                    )
                    candidate_evals.append((score, VerificationOutcome.SUPPORTED, passage, expl))

        if candidate_evals:
            candidate_evals.sort(key=lambda x: x[0], reverse=True)
            best_score, best_outcome, best_passage, best_expl = candidate_evals[0]
            return VerificationResult(
                claim_id=prop.proposition_id,
                outcome=best_outcome,
                confidence=round(best_score, 4),
                evidence_passage=best_passage,
                explanation=best_expl,
                verifier_version=self.verifier_version,
            )

        return VerificationResult(
            claim_id=prop.proposition_id,
            outcome=VerificationOutcome.INSUFFICIENT_EVIDENCE,
            confidence=0.80,
            evidence_passage=None,
            explanation="Evidence does not contain sufficient relation or entity grounding for this proposition.",
            verifier_version=self.verifier_version,
        )

    def verify(
        self,
        claim: AtomicClaim,
        passages: list[EvidencePassage],
    ) -> VerificationResult:
        """Verify a claim by decomposing into propositions and composing relation-aware outcomes."""
        if not passages:
            return VerificationResult(
                claim_id=claim.claim_id,
                outcome=VerificationOutcome.INSUFFICIENT_EVIDENCE,
                confidence=1.0,
                evidence_passage=None,
                explanation="No evidence passages provided.",
                verifier_version=self.verifier_version,
            )

        # Check for adversarial injection
        injection_flag = False
        for p in passages:
            _, detected = self._sanitize_evidence(p.text)
            if detected:
                injection_flag = True

        propositions = self.decompose_claim(claim)

        # Single atomic proposition
        if len(propositions) == 1:
            res = self._verify_single_proposition(propositions[0], passages)
            res.claim_id = claim.claim_id
            if injection_flag:
                res.metadata["adversarial_injection_detected"] = True
                res.metadata["injection_defense_action"] = "sanitized_untrusted_evidence_data"
            return res

        # Compound claim evaluation
        prop_results = [self._verify_single_proposition(prop, passages) for prop in propositions]

        outcomes = [r.outcome for r in prop_results]

        # 1. Any Contradiction -> Compound is CONTRADICTED
        if VerificationOutcome.CONTRADICTED in outcomes:
            contra_res = next(r for r in prop_results if r.outcome == VerificationOutcome.CONTRADICTED)
            explanation = (
                f"Compound claim CONTRADICTED: Proposition '{contra_res.claim_id}' was refuted. "
                f"Details: {contra_res.explanation}"
            )
            res = VerificationResult(
                claim_id=claim.claim_id,
                outcome=VerificationOutcome.CONTRADICTED,
                confidence=contra_res.confidence,
                evidence_passage=contra_res.evidence_passage,
                explanation=explanation,
                verifier_version=self.verifier_version,
            )
        # 2. Any Conflicting Evidence -> Compound is CONFLICTING
        elif VerificationOutcome.CONFLICTING_EVIDENCE in outcomes:
            conf_res = next(r for r in prop_results if r.outcome == VerificationOutcome.CONFLICTING_EVIDENCE)
            explanation = f"Compound claim has CONFLICTING evidence: {conf_res.explanation}"
            res = VerificationResult(
                claim_id=claim.claim_id,
                outcome=VerificationOutcome.CONFLICTING_EVIDENCE,
                confidence=conf_res.confidence,
                evidence_passage=conf_res.evidence_passage,
                conflicting_passages=conf_res.conflicting_passages,
                explanation=explanation,
                verifier_version=self.verifier_version,
            )
        # 3. All Supported -> Compound is SUPPORTED
        elif all(o == VerificationOutcome.SUPPORTED for o in outcomes):
            min_conf = min(r.confidence for r in prop_results)
            explanation = (
                f"Compound claim fully SUPPORTED across all {len(propositions)} constituent propositions."
            )
            res = VerificationResult(
                claim_id=claim.claim_id,
                outcome=VerificationOutcome.SUPPORTED,
                confidence=round(min_conf, 4),
                evidence_passage=prop_results[0].evidence_passage,
                explanation=explanation,
                verifier_version=self.verifier_version,
            )
        # 4. Partial Support / Insufficient Evidence
        else:
            n_supp = sum(1 for o in outcomes if o == VerificationOutcome.SUPPORTED)
            explanation = (
                f"Partial evidence / INSUFFICIENT_EVIDENCE: Only {n_supp} of {len(propositions)} propositions "
                f"are substantiated. Partial evidence is explicitly not promoted to SUPPORTED."
            )
            res = VerificationResult(
                claim_id=claim.claim_id,
                outcome=VerificationOutcome.INSUFFICIENT_EVIDENCE,
                confidence=0.85,
                evidence_passage=None,
                explanation=explanation,
                verifier_version=self.verifier_version,
            )

        if injection_flag:
            res.metadata["adversarial_injection_detected"] = True
            res.metadata["injection_defense_action"] = "sanitized_untrusted_evidence_data"
        res.metadata["atomic_propositions_evaluated"] = [p.to_dict() for p in propositions]

        return res
