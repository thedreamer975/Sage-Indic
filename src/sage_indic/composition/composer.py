"""Deterministic evidence-grounded response composition (Phase 2G).

Design contract:

* The deterministic layer is the default and always works without an LLM.
* Evidence sentences are selected and quoted verbatim; the composer never invents
  factual content for the deterministic answer.
* Citation objects are created only from passages supplied to the current request.
* A citation whose ID exists but whose passage does not support the claim is
  represented as unsupported, never as valid support.
* An optional LLM draft is used only if every extracted claim is verifiable against
  the supplied evidence and the draft invents no citation IDs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sage_indic.composition.query_analysis import (
    SentenceCandidate,
    analyse_query,
    evidence_is_sufficient,
)
from sage_indic.composition.types import (
    AnswerClaim,
    AnswerMode,
    AnswerResponse,
    AnswerStatus,
    Citation,
    GenerationMetadata,
    LatencyMetadata,
    QueryAnalysis,
    RetrievedEvidence,
    SafetyInfo,
    VerificationSummary,
)
from sage_indic.generation.types import DraftAnswer
from sage_indic.rag.types import EvidencePackage, RetrievalResult
from sage_indic.types import InputRepresentation, LanguageCategory
from sage_indic.verification.relation_verifier import RelationAwareClaimVerifier
from sage_indic.verification.types import (
    AtomicClaim,
    EvidencePassage,
    VerificationOutcome,
    VerificationResult,
)
from sage_indic.verification.verifier import LinguisticClaimVerifier


@dataclass
class CompositionInputs:
    """All inputs required to compose one user-facing answer."""

    request_id: str
    query: str
    input_representation: InputRepresentation
    package: EvidencePackage
    expanded_query: str = ""
    safety: SafetyInfo = field(default_factory=SafetyInfo)
    latency: LatencyMetadata = field(default_factory=LatencyMetadata)
    requested_mode: AnswerMode = AnswerMode.DETERMINISTIC
    draft: DraftAnswer | None = None
    generation_error: str | None = None
    provider_available: bool = False
    provider_name: str = "none"
    model_name: str | None = None


_DETERMINISTIC_LEAD_IN = {
    LanguageCategory.TELUGU_NATIVE: "సేకరించిన ఆధారాల ఆధారంగా:",
    LanguageCategory.ROMANIZED_TELUGU: "Sekarinchina aadhaaraala prakaaram:",
    LanguageCategory.TELUGU_ENGLISH_CODE_MIXED: "Retrieved evidence prakaram:",
    LanguageCategory.ENGLISH: "Based on the supplied evidence:",
    LanguageCategory.UNKNOWN: "Based on the supplied evidence:",
}

_ABSTENTION_TEXT = {
    LanguageCategory.TELUGU_NATIVE: (
        "సేకరించిన పత్రాలలో ఈ ప్రశ్నకు సమాధానం ఇవ్వడానికి సరిపడిన ఆధారాలు లభించలేదు."
    ),
    LanguageCategory.ROMANIZED_TELUGU: (
        "Sekarinchina documents lo ee prashnaki samadhanam ivvadaniki "
        "saripadina aadhaaraalu labhinchalēdu."
    ),
    LanguageCategory.TELUGU_ENGLISH_CODE_MIXED: (
        "Retrieved documents lo is question ki answer ivvadaniki sufficient evidence ledu."
    ),
    LanguageCategory.ENGLISH: (
        "The retrieved corpus does not contain sufficient evidence to answer this question."
    ),
    LanguageCategory.UNKNOWN: (
        "The retrieved corpus does not contain sufficient evidence to answer this question."
    ),
}

_PARTIAL_CAVEAT = {
    LanguageCategory.TELUGU_NATIVE: (
        "గమనిక: ప్రశ్నలోని కొన్ని అంశాలకు మాత్రమే ఆధారాలు లభించాయి; మిగిలిన అంశాలు ధృవీకరించబడలేదు."
    ),
    LanguageCategory.ROMANIZED_TELUGU: (
        "Gamanika: prashnaloni konni amshaalaki matrame aadhaaraalu labhayaayi; "
        "migilina amshaalu verify cheyabadaledu."
    ),
    LanguageCategory.TELUGU_ENGLISH_CODE_MIXED: (
        "Note: evidence covers only part of the question; remaining aspects could not be verified."
    ),
    LanguageCategory.ENGLISH: (
        "Note: evidence covers only part of the question; remaining aspects could not be verified."
    ),
    LanguageCategory.UNKNOWN: (
        "Note: evidence covers only part of the question; remaining aspects could not be verified."
    ),
}

_CITATION_MARKER = re.compile(r"\[([A-Za-z0-9_\-]+#[A-Za-z0-9_\-]+)\]")


class ResponseComposer:
    """Builds a structured, citation-backed ``AnswerResponse``."""

    def __init__(
        self,
        relation_verifier: RelationAwareClaimVerifier | None = None,
        linguistic_verifier: LinguisticClaimVerifier | None = None,
    ) -> None:
        self.relation_verifier = relation_verifier or RelationAwareClaimVerifier()
        self.linguistic_verifier = linguistic_verifier or LinguisticClaimVerifier()

    def compose(self, inputs: CompositionInputs) -> AnswerResponse:
        """Compose the final response from retrieval, verification, and optional generation."""
        modality = inputs.input_representation.category
        results = inputs.package.results
        analysis, selected, _groups, _intent = analyse_query(
            inputs.input_representation.normalized_text,
            inputs.expanded_query or inputs.input_representation.normalized_text,
            results,
        )
        sufficient, sufficiency_reason = evidence_is_sufficient(analysis, results, selected)

        retrieved = [
            self._to_retrieved_evidence(result, selected_ids={s.evidence_id for s in selected})
            for result in results
        ]
        passages = [EvidencePassage.from_retrieval_result(r) for r in results]
        passage_by_id = {p.passage_id: p for p in passages}

        warnings: list[str] = []
        generation = GenerationMetadata(
            requested_mode=inputs.requested_mode,
            used_mode=AnswerMode.DETERMINISTIC,
            provider=inputs.provider_name,
            model=inputs.model_name,
            provider_available=inputs.provider_available,
        )

        if inputs.safety.label == "UNSAFE":
            response = self._abstain(
                inputs,
                analysis,
                retrieved,
                status=AnswerStatus.BLOCKED,
                reason="Query was blocked by the safety layer: " + ", ".join(inputs.safety.notes),
                warnings=warnings,
                generation=generation,
            )
            return response

        if not sufficient:
            warnings.append(sufficiency_reason)
            # If user requested LLM mode and a draft was produced, provide the parametric general answer
            # with an explicit out-of-corpus disclaimer and empty citations.
            if inputs.requested_mode == AnswerMode.LLM and inputs.draft is not None and inputs.draft.answer_text.strip():
                generation.used_mode = AnswerMode.LLM
                generation.fallback_used = False
                disclaimer = self._ungrounded_disclaimer(modality)
                final_answer = f"{disclaimer}\n\n{inputs.draft.answer_text.strip()}"
                warnings.append(
                    "No supporting evidence found in corpus. Response provided from general "
                    "model knowledge without verified corpus citations."
                )
                return AnswerResponse(
                    request_id=inputs.request_id,
                    original_query=inputs.query,
                    detected_modality=modality,
                    detected_modality_confidence=inputs.input_representation.confidence,
                    normalized_query=inputs.input_representation.normalized_text,
                    answer_text=final_answer,
                    answer_status=AnswerStatus.ANSWERED,
                    answer_claims=[],
                    citations=[],
                    retrieved_evidence=retrieved,
                    verification_summary=VerificationSummary(
                        evidence_coverage=0.0,
                        notes=[sufficiency_reason, "General knowledge response (out-of-corpus)."],
                    ),
                    abstention_reason=None,
                    generation_metadata=generation,
                    query_analysis=analysis,
                    safety=inputs.safety,
                    warnings=warnings,
                    latency_metadata=inputs.latency,
                )

            response = self._abstain(
                inputs,
                analysis,
                retrieved,
                status=AnswerStatus.ABSTAINED,
                reason=sufficiency_reason,
                warnings=warnings,
                generation=generation,
            )
            return response

        # 1. Deterministic candidate claims: verbatim evidence sentences.
        deterministic_claims, deterministic_citations = self._verify_extractive_claims(
            selected, passage_by_id
        )
        supported_det = [c for c in deterministic_claims if c.verification_status == "SUPPORTED"]
        if not supported_det:
            warnings.append("Selected evidence sentences could not be verified as claims.")
            response = self._abstain(
                inputs,
                analysis,
                retrieved,
                status=AnswerStatus.ABSTAINED,
                reason="Evidence sentences were retrieved but could not be verified.",
                warnings=warnings,
                generation=generation,
            )
            return response

        coverage_partial = analysis.evidence_coverage < 1.0
        status_det = (
            AnswerStatus.PARTIALLY_ANSWERED
            if coverage_partial or len(supported_det) < len(deterministic_claims)
            else AnswerStatus.ANSWERED
        )
        answer_text_det = self._build_extractive_answer(
            modality,
            supported_det,
            deterministic_citations,
            partial=status_det == AnswerStatus.PARTIALLY_ANSWERED,
        )

        # 2. Optional LLM layer. A draft is accepted only when fully grounded.
        final_claims = deterministic_claims
        final_citations = deterministic_citations
        final_answer = answer_text_det
        status = status_det

        if inputs.requested_mode == AnswerMode.LLM:
            if inputs.generation_error:
                generation.fallback_used = True
                generation.fallback_reason = inputs.generation_error
                generation.used_mode = AnswerMode.LLM_FALLBACK
                warnings.append(
                    "LLM provider unavailable; deterministic evidence-grounded answer used."
                )
            elif inputs.draft is not None:
                accepted, draft_claims, draft_citations, reasons = self._evaluate_llm_draft(
                    inputs.draft, passages
                )
                if accepted:
                    final_claims = draft_claims
                    final_citations = draft_citations
                    final_answer = self._attach_citation_markers(
                        inputs.draft.answer_text,
                        draft_claims,
                        draft_citations,
                    )
                    status = AnswerStatus.ANSWERED
                    generation.used_mode = AnswerMode.LLM
                else:
                    generation.fallback_used = True
                    generation.draft_rejected = True
                    generation.rejection_reasons = reasons
                    generation.used_mode = AnswerMode.LLM_FALLBACK
                    generation.raw_draft_kept_internally = True
                    warnings.append(
                        "LLM draft was rejected because it was not fully grounded in the "
                        "supplied evidence. The deterministic answer is shown instead."
                    )
            else:
                generation.fallback_used = True
                generation.fallback_reason = "No draft was produced."
                generation.used_mode = AnswerMode.LLM_FALLBACK
                warnings.append("No LLM draft was produced; deterministic answer used.")

        summary = self._summarise(final_claims, final_citations, analysis)
        used_ids = {c.evidence_id for c in final_citations}
        for evidence in retrieved:
            evidence.used_in_answer = evidence.evidence_id in used_ids

        if status == AnswerStatus.PARTIALLY_ANSWERED:
            warnings.append("Answer covers only part of the question; see claim-level caveats.")

        return AnswerResponse(
            request_id=inputs.request_id,
            original_query=inputs.query,
            detected_modality=modality,
            detected_modality_confidence=inputs.input_representation.confidence,
            normalized_query=inputs.input_representation.normalized_text,
            answer_text=final_answer,
            answer_status=status,
            answer_claims=final_claims,
            citations=final_citations,
            retrieved_evidence=retrieved,
            verification_summary=summary,
            abstention_reason=None,
            generation_metadata=generation,
            query_analysis=analysis,
            safety=inputs.safety,
            warnings=warnings,
            latency_metadata=inputs.latency,
        )

    # ------------------------------------------------------------------
    # Deterministic extractive composition
    # ------------------------------------------------------------------

    def _verify_extractive_claims(
        self,
        selected: list[SentenceCandidate],
        passage_by_id: dict[str, EvidencePassage],
    ) -> tuple[list[AnswerClaim], list[Citation]]:
        claims: list[AnswerClaim] = []
        citations: list[Citation] = []
        citation_by_evidence: dict[str, Citation] = {}

        for idx, candidate in enumerate(selected, start=1):
            source = passage_by_id.get(candidate.evidence_id)
            if source is None:
                continue
            claim_id = f"CLM_{idx:02d}"
            claim = AtomicClaim(
                claim_id=claim_id,
                claim_text=candidate.sentence,
                language="te",
                modality="native",
                metadata={"selection": "extractive_sentence", "score": candidate.score},
            )
            result = self._verify_claim(claim, [source])

            citation = citation_by_evidence.get(source.passage_id)
            if citation is None and result.evidence_passage is not None:
                citation = self._make_citation(
                    f"C{len(citations) + 1}",
                    result.evidence_passage,
                    result,
                    [claim_id],
                )
                citation_by_evidence[source.passage_id] = citation
                citations.append(citation)
            elif citation is not None:
                citation.claim_ids.append(claim_id)

            claims.append(
                AnswerClaim(
                    claim_id=claim_id,
                    text=candidate.sentence,
                    verification_status=result.outcome.value,
                    evidence_ids=[source.passage_id],
                    citation_ids=[citation.citation_id] if citation else [],
                    explanation=result.explanation,
                    caveat=self._claim_caveat(result),
                    confidence=round(result.confidence, 4),
                )
            )

        return claims, citations

    def _build_extractive_answer(
        self,
        modality: LanguageCategory,
        claims: list[AnswerClaim],
        citations: list[Citation],
        partial: bool,
    ) -> str:
        lead = _DETERMINISTIC_LEAD_IN.get(
            modality, _DETERMINISTIC_LEAD_IN[LanguageCategory.ENGLISH]
        )
        citation_by_claim = {
            claim_id: citation.citation_id
            for citation in citations
            for claim_id in citation.claim_ids
        }
        parts: list[str] = []
        for claim in claims:
            marker = citation_by_claim.get(claim.claim_id)
            parts.append(f"{claim.text} [{marker}]" if marker else claim.text)
        answer = f"{lead} " + " ".join(parts)
        if partial:
            answer += " " + _PARTIAL_CAVEAT.get(modality, _PARTIAL_CAVEAT[LanguageCategory.ENGLISH])
        return answer

    # ------------------------------------------------------------------
    # Optional LLM evaluation
    # ------------------------------------------------------------------

    def _evaluate_llm_draft(
        self,
        draft: DraftAnswer,
        passages: list[EvidencePassage],
    ) -> tuple[bool, list[AnswerClaim], list[Citation], list[str]]:
        reasons: list[str] = []
        if draft.invalid_citations:
            reasons.append(
                "Draft cited passage IDs not supplied to this request: "
                f"{draft.invalid_citations}"
            )
        if draft.abstention_source == "model_marker":
            reasons.append("Draft was an explicit model abstention despite available evidence.")
        if not draft.candidate_claims:
            reasons.append("Draft contained no verifiable factual claim.")
        if reasons:
            return False, [], [], reasons

        claims: list[AnswerClaim] = []
        citations: list[Citation] = []
        citation_by_evidence: dict[str, Citation] = {}
        unsupported = 0

        for claim in draft.candidate_claims:
            result = self._verify_claim(claim, passages)
            if result.outcome != VerificationOutcome.SUPPORTED:
                unsupported += 1
                reasons.append(
                    f"Claim '{claim.claim_text[:80]}' was {result.outcome.value}: "
                    f"{result.explanation}"
                )
                continue

            evidence = result.evidence_passage
            if evidence is None:
                unsupported += 1
                reasons.append(
                    f"Claim '{claim.claim_text[:80]}' had no supporting evidence passage."
                )
                continue

            citation = citation_by_evidence.get(evidence.passage_id)
            if citation is None:
                citation = self._make_citation(
                    f"C{len(citations) + 1}", evidence, result, [claim.claim_id]
                )
                citation_by_evidence[evidence.passage_id] = citation
                citations.append(citation)
            elif claim.claim_id not in citation.claim_ids:
                citation.claim_ids.append(claim.claim_id)

            claims.append(
                AnswerClaim(
                    claim_id=claim.claim_id,
                    text=claim.claim_text,
                    verification_status=result.outcome.value,
                    evidence_ids=[evidence.passage_id],
                    citation_ids=[citation.citation_id],
                    explanation=result.explanation,
                    caveat=None,
                    confidence=round(result.confidence, 4),
                )
            )

        if unsupported:
            return False, [], [], reasons
        if not claims:
            return False, [], [], ["Draft produced no supported claim."]
        return True, claims, citations, []

    def _attach_citation_markers(
        self,
        text: str,
        claims: list[AnswerClaim],
        citations: list[Citation],
    ) -> str:
        """Replace valid passage-ID tags with citation IDs, or append missing markers."""
        citation_by_claim = {
            claim_id: citation.citation_id
            for citation in citations
            for claim_id in citation.claim_ids
        }
        passage_to_citation = {
            citation.evidence_id: citation.citation_id for citation in citations
        }

        def replace_tag(match: re.Match[str]) -> str:
            passage_id = match.group(1)
            if passage_id not in passage_to_citation:
                return ""
            return f"[{passage_to_citation[passage_id]}]"

        # Remove citation IDs authored by the model itself. An ID such as ``[C1]``
        # may collide with a programmatic citation for a different passage, so
        # model-written IDs are never trusted; only passage-ID tags that map to a
        # verified citation survive.
        without_model_ids = re.sub(r"\[C\d+\]", "", text)
        cleaned = _CITATION_MARKER.sub(replace_tag, without_model_ids).strip()
        missing = [
            claim for claim in claims if claim.claim_id in citation_by_claim
        ]
        if missing and not re.search(r"\[C\d+\]", cleaned):
            markers = " ".join(
                f"[{citation_by_claim[claim.claim_id]}]" for claim in missing
            )
            cleaned = f"{cleaned} {markers}"
        return cleaned

    # ------------------------------------------------------------------
    # Verification helpers
    # ------------------------------------------------------------------

    def _verify_claim(
        self,
        claim: AtomicClaim,
        passages: list[EvidencePassage],
    ) -> VerificationResult:
        """Run relation-aware verification, with a conservative fallback.

        If the heuristic relation verifier cannot decide but the claim is an exact
        substring of a supplied passage, the claim is an extractive span of that
        evidence. That is recorded explicitly as ``extractive_span`` rather than
        being silently upgraded.
        """
        result = self.relation_verifier.verify(claim, passages)
        if result.outcome == VerificationOutcome.SUPPORTED:
            return result

        for passage in passages:
            if claim.claim_text.strip() and claim.claim_text.strip() in passage.text:
                return VerificationResult(
                    claim_id=claim.claim_id,
                    outcome=VerificationOutcome.SUPPORTED,
                    confidence=1.0,
                    evidence_passage=passage,
                    explanation=(
                        "Claim is a verbatim extractive span of the supplied evidence passage "
                        "(exact substring match); no generative addition is present."
                    ),
                    verifier_version=f"{self.relation_verifier.verifier_version}+extractive_span",
                    metadata={"verification_method": "extractive_span"},
                )

        linguistic = self.linguistic_verifier.verify(claim, passages)
        if linguistic.outcome == VerificationOutcome.SUPPORTED:
            return linguistic
        return result

    @staticmethod
    def _claim_caveat(result: VerificationResult) -> str | None:
        if result.outcome == VerificationOutcome.CONTRADICTED:
            return (
                "This claim is contradicted by the supplied evidence and is not "
                "presented as fact."
            )
        if result.outcome == VerificationOutcome.INSUFFICIENT_EVIDENCE:
            return (
                "The supplied evidence does not establish this claim; absence of proof "
                "is not proof of falsehood."
            )
        if result.outcome == VerificationOutcome.CONFLICTING_EVIDENCE:
            return (
                "Supplied passages conflict on this point; the conflict is reported "
                "rather than resolved."
            )
        return None

    def _make_citation(
        self,
        citation_id: str,
        passage: EvidencePassage,
        result: VerificationResult,
        claim_ids: list[str],
    ) -> Citation:
        return Citation(
            citation_id=citation_id,
            evidence_id=passage.passage_id,
            document_id=passage.document_id,
            chunk_id=passage.passage_id,
            title=passage.title,
            source_name=str(passage.metadata.get("source_name", "")),
            publisher=str(passage.metadata.get("publisher", "")),
            license_name=str(passage.metadata.get("license_name", "")),
            source_url=passage.source_url,
            quoted_text=passage.text,
            char_start=passage.char_start,
            char_end=passage.char_end,
            claim_ids=list(claim_ids),
            verification_status=result.outcome.value,
            supports_claim=result.outcome == VerificationOutcome.SUPPORTED,
        )

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    def _to_retrieved_evidence(
        self,
        result: RetrievalResult,
        selected_ids: set[str],
    ) -> RetrievedEvidence:
        return RetrievedEvidence(
            evidence_id=result.chunk_id,
            rank=result.rank,
            score=result.score,
            document_id=result.document_id,
            chunk_id=result.chunk_id,
            title=result.title,
            source_name=result.source_name,
            publisher=result.publisher,
            license_name=result.license_name,
            license_url=result.license_evidence_url,
            source_url=result.source_url,
            text=result.text,
            char_start=result.char_start,
            char_end=result.char_end,
            content_hash=result.content_hash,
            selected=result.chunk_id in selected_ids,
        )

    def _summarise(
        self,
        claims: list[AnswerClaim],
        citations: list[Citation],
        analysis: QueryAnalysis,
    ) -> VerificationSummary:
        counts = {outcome.value: 0 for outcome in VerificationOutcome}
        for claim in claims:
            if claim.verification_status in counts:
                counts[claim.verification_status] += 1
        all_supported = bool(claims) and all(
            claim.verification_status == VerificationOutcome.SUPPORTED.value for claim in claims
        )
        return VerificationSummary(
            total_claims=len(claims),
            supported_count=counts[VerificationOutcome.SUPPORTED.value],
            contradicted_count=counts[VerificationOutcome.CONTRADICTED.value],
            insufficient_count=counts[VerificationOutcome.INSUFFICIENT_EVIDENCE.value],
            conflicting_count=counts[VerificationOutcome.CONFLICTING_EVIDENCE.value],
            all_claims_supported=all_supported,
            cited_evidence_count=len({c.evidence_id for c in citations}),
            evidence_coverage=analysis.evidence_coverage,
            notes=[],
        )

    def _abstain(
        self,
        inputs: CompositionInputs,
        analysis: QueryAnalysis,
        retrieved: list[RetrievedEvidence],
        status: AnswerStatus,
        reason: str,
        warnings: list[str],
        generation: GenerationMetadata,
    ) -> AnswerResponse:
        modality = inputs.input_representation.category
        text = _ABSTENTION_TEXT.get(modality, _ABSTENTION_TEXT[LanguageCategory.ENGLISH])
        if inputs.generation_error:
            generation.fallback_used = True
            generation.fallback_reason = inputs.generation_error
            generation.used_mode = AnswerMode.LLM_FALLBACK
        if inputs.safety.label == "UNSAFE":
            text = (
                "ఈ ప్రశ్న భద్రతా పరిమితుల కారణంగా నిరోధించబడింది."
                if modality == LanguageCategory.TELUGU_NATIVE
                else "This query was blocked by the safety policy."
            )
        return AnswerResponse(
            request_id=inputs.request_id,
            original_query=inputs.query,
            detected_modality=modality,
            detected_modality_confidence=inputs.input_representation.confidence,
            normalized_query=inputs.input_representation.normalized_text,
            answer_text=text,
            answer_status=status,
            answer_claims=[],
            citations=[],
            retrieved_evidence=retrieved,
            verification_summary=VerificationSummary(
                evidence_coverage=analysis.evidence_coverage,
                notes=[reason],
            ),
            abstention_reason=reason,
            generation_metadata=generation,
            query_analysis=analysis,
            safety=inputs.safety,
            warnings=warnings,
            latency_metadata=inputs.latency,
        )

    @staticmethod
    def _ungrounded_disclaimer(modality: LanguageCategory) -> str:
        if modality == LanguageCategory.TELUGU_NATIVE:
            return (
                "⚠️ గమనిక: సేకరించిన అధికారిక పత్రాలలో ఈ ప్రశ్నకు ఆధారాలు లభించలేదు. "
                "ఈ క్రింది సమాధానం మోడల్ యొక్క సాధారణ పరిజ్ఞానం (parametric knowledge) "
                "నుండి ఇవ్వబడింది; దీనికి ధృవీకరించబడిన ఆధారాలు లేవు."
            )
        elif modality == LanguageCategory.ROMANIZED_TELUGU:
            return (
                "⚠️ Gamanika: Sekarinchina documents lo ee prashnaki evidence labhinchaledu. "
                "Ee answer model yokka general knowledge nunchi ivvabadindi; "
                "verified citations levu."
            )
        else:
            return (
                "⚠️ Note: No verified evidence passages found in the approved corpus. "
                "The following answer is generated from general model knowledge "
                "without verified citations."
            )
