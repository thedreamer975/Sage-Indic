"""Phase 2G response-composition tests: citations, abstention, LLM acceptance.

These tests exercise the composer directly with hand-built evidence packages so
that each invariant is checked without depending on retrieval scores.
"""

from __future__ import annotations

import re

import pytest

from sage_indic.composition.composer import CompositionInputs, ResponseComposer
from sage_indic.composition.types import (
    AnswerMode,
    AnswerStatus,
    SafetyInfo,
)
from sage_indic.generation.types import DraftAnswer
from sage_indic.rag.types import ContentHash, EvidencePackage, RetrievalResult
from sage_indic.types import InputRepresentation, LanguageCategory
from sage_indic.verification.types import AtomicClaim

CHUNK_GOLCONDA = "TE_DOC_002#c0000"
CHUNK_CHARMINAR = "TE_DOC_001#c0001"

GOLCONDA_TEXT = (
    "గోల్కొండ కోట హైదరాబాదు పశ్చిమ భాగంలో ఉన్న ఒక పురాతన కోట. "
    "ఇది చారిత్రక ప్రదేశం."
)
CHARMINAR_CLAIM = (
    "ఈ కట్టడాన్ని క్రీస్తు శకం 1591 లో కుతుబ్ షాహీ వంశానికి చెందిన "
    "ఐదవ సుల్తాన్ మహమ్మద్ కులీ కుతుబ్ షా నిర్మించారు."
)
CHARMINAR_TEXT = CHARMINAR_CLAIM
GOLCONDA_HISTORY_TEXT = (
    "గోల్కొండ కోట హైదరాబాదు పశ్చిమ భాగంలో ఉంది. "
    "గోల్కొండ కోట చారిత్రక ప్రదేశం."
)


def make_result(
    chunk_id: str,
    document_id: str,
    title: str,
    text: str,
    rank: int = 1,
    score: float = 4.0,
) -> RetrievalResult:
    return RetrievalResult(
        rank=rank,
        score=score,
        document_id=document_id,
        chunk_id=chunk_id,
        text=text,
        title=title,
        source_name="Test evidence source",
        publisher="Test publisher",
        license_name="CC BY-SA 4.0",
        char_start=0,
        char_end=len(text),
        content_hash=ContentHash(algorithm="sha256", digest="0" * 64),
        corpus_version="test-corpus",
        metadata={
            "source_name": "Test evidence source",
            "publisher": "Test publisher",
            "license_name": "CC BY-SA 4.0",
        },
    )


def make_inputs(
    query: str,
    results: list[RetrievalResult],
    *,
    category: LanguageCategory = LanguageCategory.TELUGU_NATIVE,
    requested_mode: AnswerMode = AnswerMode.DETERMINISTIC,
    draft: DraftAnswer | None = None,
    generation_error: str | None = None,
    provider_available: bool = False,
    safety: SafetyInfo | None = None,
) -> CompositionInputs:
    package = EvidencePackage(
        query_id="REQ_TEST",
        query_text=query,
        retrieval_method="BM25_test",
        corpus_version="test-corpus",
        results=results,
    )
    representation = InputRepresentation(
        original_text=query,
        normalized_text=query,
        category=category,
        confidence=0.9,
        telugu_char_ratio=1.0 if category == LanguageCategory.TELUGU_NATIVE else 0.0,
        latin_char_ratio=1.0 if category != LanguageCategory.TELUGU_NATIVE else 0.0,
        english_token_ratio=0.0,
    )
    return CompositionInputs(
        request_id="REQ_TEST",
        query=query,
        input_representation=representation,
        package=package,
        safety=safety or SafetyInfo(label="SAFE", method="test"),
        requested_mode=requested_mode,
        draft=draft,
        generation_error=generation_error,
        provider_available=provider_available,
        provider_name="test-provider",
        model_name="test-model" if requested_mode != AnswerMode.DETERMINISTIC else None,
    )


def assert_citation_integrity(response) -> None:  # type: ignore[no-untyped-def]
    """Every visible citation/marker must resolve to supplied evidence and a claim."""
    citation_ids = [citation.citation_id for citation in response.citations]
    assert len(citation_ids) == len(set(citation_ids)), "duplicate citation IDs"

    known_citations = {citation.citation_id: citation for citation in response.citations}
    retrieved_ids = {item.evidence_id for item in response.retrieved_evidence}
    claim_by_id = {claim.claim_id: claim for claim in response.answer_claims}

    for citation in response.citations:
        # A citation may only point at evidence supplied for this request.
        assert citation.evidence_id in retrieved_ids
        assert citation.chunk_id == citation.evidence_id
        assert citation.claim_ids, "citation is not attached to any claim"
        for claim_id in citation.claim_ids:
            assert claim_id in claim_by_id
        if citation.supports_claim:
            assert citation.verification_status == "SUPPORTED"

    for claim in response.answer_claims:
        for citation_id in claim.citation_ids:
            assert citation_id in known_citations
        if claim.verification_status == "SUPPORTED":
            # Extractive claims must remain verbatim spans of their cited passage.
            for citation_id in claim.citation_ids:
                assert claim.text.strip() in known_citations[citation_id].quoted_text

    markers = set(re.findall(r"\[(C\d+)\]", response.answer_text))
    assert markers <= set(known_citations), f"answer cites unknown IDs: {markers}"


def test_answer_carries_only_supplied_citations() -> None:
    composer = ResponseComposer()
    response = composer.compose(
        make_inputs(
            "గోల్కొండ కోట ఎక్కడ ఉంది?",
            [
                make_result(
                    CHUNK_GOLCONDA,
                    "TE_DOC_002",
                    "గోల్కొండ కోట",
                    GOLCONDA_TEXT,
                )
            ],
        )
    )

    assert response.answer_status == AnswerStatus.ANSWERED
    assert response.verification_summary.supported_count == 1
    assert response.verification_summary.all_claims_supported is True
    assert [citation.evidence_id for citation in response.citations] == [CHUNK_GOLCONDA]
    assert response.citations[0].supports_claim is True
    assert "[C1]" in response.answer_text
    assert_citation_integrity(response)


def test_multiple_claims_share_one_citation_for_one_passage() -> None:
    composer = ResponseComposer()
    response = composer.compose(
        make_inputs(
            "గోల్కొండ కోట చరిత్ర గురించి చెప్పు",
            [
                make_result(
                    CHUNK_GOLCONDA,
                    "TE_DOC_002",
                    "గోల్కొండ కోట",
                    GOLCONDA_HISTORY_TEXT,
                )
            ],
        )
    )

    assert response.answer_status == AnswerStatus.ANSWERED
    assert len(response.citations) == 1
    assert len(response.citations[0].claim_ids) == len(response.answer_claims)
    assert len(response.answer_claims) == 2
    assert_citation_integrity(response)


def test_no_evidence_abstains_without_citations() -> None:
    composer = ResponseComposer()
    response = composer.compose(make_inputs("ఫ్రాన్స్ రాజధాని ఏది?", []))

    assert response.answer_status == AnswerStatus.ABSTAINED
    assert response.citations == []
    assert response.answer_claims == []
    assert "[C" not in response.answer_text
    assert response.abstention_reason
    reason = response.abstention_reason.lower()
    assert "passage" in reason or "evidence" in reason or "ఆధార" in response.abstention_reason


def test_unsafe_query_is_blocked_without_answer_claims() -> None:
    composer = ResponseComposer()
    response = composer.compose(
        make_inputs(
            "ఒకరిని ఎలా చంపాలి?",
            [
                make_result(
                    CHUNK_GOLCONDA,
                    "TE_DOC_002",
                    "గోల్కొండ కోట",
                    GOLCONDA_TEXT,
                )
            ],
            safety=SafetyInfo(
                label="UNSAFE",
                method="test",
                category="VIOLENCE",
                notes=["Isolated critical violence stem: ['చంపాలి']"],
            ),
        )
    )

    assert response.answer_status == AnswerStatus.BLOCKED
    assert response.citations == []
    assert response.answer_claims == []
    assert "safety" in (response.abstention_reason or "").lower()


def test_partial_coverage_is_marked_partial() -> None:
    composer = ResponseComposer()
    response = composer.compose(
        make_inputs(
            "Charminar height and entry fee enti?",
            [
                make_result(
                    CHUNK_CHARMINAR,
                    "TE_DOC_001",
                    "చార్మినార్",
                    "చార్మినార్ ఎత్తు 56 మీటర్లు.",
                )
            ],
            category=LanguageCategory.TELUGU_ENGLISH_CODE_MIXED,
        )
    )

    assert response.answer_status == AnswerStatus.PARTIALLY_ANSWERED
    assert response.query_analysis.evidence_coverage < 1.0
    assert "entry" in response.query_analysis.missing_terms
    assert response.abstention_reason is None
    assert_citation_integrity(response)


def test_provider_failure_falls_back_and_reports_reason() -> None:
    composer = ResponseComposer()
    response = composer.compose(
        make_inputs(
            "గోల్కొండ కోట ఎక్కడ ఉంది?",
            [make_result(CHUNK_GOLCONDA, "TE_DOC_002", "గోల్కొండ కోట", GOLCONDA_TEXT)],
            requested_mode=AnswerMode.LLM,
            generation_error="GenerationError: provider timeout",
            provider_available=False,
        )
    )

    assert response.answer_status == AnswerStatus.ANSWERED
    assert response.generation_metadata.used_mode == AnswerMode.LLM_FALLBACK
    assert response.generation_metadata.fallback_used is True
    assert "timeout" in (response.generation_metadata.fallback_reason or "")
    assert response.generation_metadata.draft_rejected is False
    assert_citation_integrity(response)


def test_empty_evidence_is_not_reported_as_model_abstention() -> None:
    composer = ResponseComposer()
    response = composer.compose(
        make_inputs(
            "ఫ్రాన్స్ రాజధాని ఏది?",
            [],
            requested_mode=AnswerMode.LLM,
            provider_available=True,
        )
    )

    assert response.answer_status == AnswerStatus.ABSTAINED
    assert response.generation_metadata.draft_rejected is False
    assert "model" not in response.generation_metadata.used_mode.value
    assert response.abstention_reason
    assert "no retrieved passage" in response.abstention_reason.lower()


def test_grounded_llm_draft_is_accepted() -> None:
    composer = ResponseComposer()
    draft = DraftAnswer(
        request_id="REQ_TEST",
        query_id="REQ_TEST",
        answer_text=f"చార్మినార్ 1591 లో నిర్మించబడింది [{CHUNK_CHARMINAR}].",
        language="te",
        modality="native",
        candidate_claims=[
            AtomicClaim(
                claim_id="CLM_01",
                claim_text=CHARMINAR_CLAIM,
                language="te",
                modality="native",
            )
        ],
        citations=[CHUNK_CHARMINAR],
        model_id="fake-model",
        provider="fake-provider",
        abstention_source="not_abstained",
    )

    response = composer.compose(
        make_inputs(
            "చార్మినార్ ఎప్పుడు నిర్మించారు?",
            [make_result(CHUNK_CHARMINAR, "TE_DOC_001", "చార్మినార్", CHARMINAR_TEXT)],
            requested_mode=AnswerMode.LLM,
            draft=draft,
            provider_available=True,
        )
    )

    assert response.answer_status == AnswerStatus.ANSWERED
    assert response.generation_metadata.used_mode == AnswerMode.LLM
    assert response.generation_metadata.draft_rejected is False
    assert "[C1]" in response.answer_text
    assert_citation_integrity(response)


def test_ungrounded_llm_draft_is_rejected_and_not_shown() -> None:
    composer = ResponseComposer()
    deterministic_answer = composer.compose(
        make_inputs(
            "చార్మినార్ ఎప్పుడు నిర్మించారు?",
            [make_result(CHUNK_CHARMINAR, "TE_DOC_001", "చార్మినార్", CHARMINAR_TEXT)],
        )
    ).answer_text

    draft = DraftAnswer(
        request_id="REQ_TEST",
        query_id="REQ_TEST",
        answer_text="చార్మినార్ 1700 లో నిర్మించబడింది [C1].",
        language="te",
        modality="native",
        candidate_claims=[
            AtomicClaim(
                claim_id="CLM_01",
                claim_text="చార్మినార్ 1700 లో నిర్మించబడింది.",
                language="te",
                modality="native",
            )
        ],
        citations=["C1"],
        model_id="fake-model",
        provider="fake-provider",
        abstention_source="not_abstained",
    )

    response = composer.compose(
        make_inputs(
            "చార్మినార్ ఎప్పుడు నిర్మించారు?",
            [make_result(CHUNK_CHARMINAR, "TE_DOC_001", "చార్మినార్", CHARMINAR_TEXT)],
            requested_mode=AnswerMode.LLM,
            draft=draft,
            provider_available=True,
        )
    )

    assert response.generation_metadata.used_mode == AnswerMode.LLM_FALLBACK
    assert response.generation_metadata.draft_rejected is True
    assert response.generation_metadata.rejection_reasons
    assert "1700" not in response.answer_text
    assert response.answer_text == deterministic_answer
    assert_citation_integrity(response)


def test_llm_fabricated_passage_id_is_rejected() -> None:
    composer = ResponseComposer()
    draft = DraftAnswer(
        request_id="REQ_TEST",
        query_id="REQ_TEST",
        answer_text="చార్మినార్ 1591 లో నిర్మించబడింది [TE_DOC_999#c9999].",
        language="te",
        modality="native",
        candidate_claims=[
            AtomicClaim(
                claim_id="CLM_01",
                claim_text=CHARMINAR_CLAIM,
                language="te",
                modality="native",
            )
        ],
        invalid_citations=["TE_DOC_999#c9999"],
        provider="fake-provider",
        abstention_source="not_abstained",
    )

    response = composer.compose(
        make_inputs(
            "చార్మినార్ ఎప్పుడు నిర్మించారు?",
            [make_result(CHUNK_CHARMINAR, "TE_DOC_001", "చార్మినార్", CHARMINAR_TEXT)],
            requested_mode=AnswerMode.LLM,
            draft=draft,
            provider_available=True,
        )
    )

    assert response.generation_metadata.draft_rejected is True
    assert any(
        "TE_DOC_999#c9999" in reason
        for reason in response.generation_metadata.rejection_reasons
    )
    assert "TE_DOC_999" not in response.answer_text
    assert_citation_integrity(response)


def test_model_authored_citation_ids_are_not_trusted() -> None:
    """A model-written [C1] must not be attached to an arbitrary passage."""
    composer = ResponseComposer()
    draft = DraftAnswer(
        request_id="REQ_TEST",
        query_id="REQ_TEST",
        answer_text="గోల్కొండ కోట హైదరాబాదు పశ్చిమ భాగంలో ఉంది [C1].",
        language="te",
        modality="native",
        candidate_claims=[
            AtomicClaim(
                claim_id="CLM_01",
                claim_text="గోల్కొండ కోట హైదరాబాదు పశ్చిమ భాగంలో ఉన్న ఒక పురాతన కోట.",
                language="te",
                modality="native",
            )
        ],
        provider="fake-provider",
        abstention_source="not_abstained",
    )

    response = composer.compose(
        make_inputs(
            "గోల్కొండ కోట ఎక్కడ ఉంది?",
            [make_result(CHUNK_GOLCONDA, "TE_DOC_002", "గోల్కొండ కోట", GOLCONDA_TEXT)],
            requested_mode=AnswerMode.LLM,
            draft=draft,
            provider_available=True,
        )
    )

    assert response.generation_metadata.used_mode == AnswerMode.LLM
    assert_citation_integrity(response)
    # The only visible marker must be the programmatically derived citation.
    assert set(re.findall(r"\[(C\d+)\]", response.answer_text)) == {"C1"}


def test_model_abstention_draft_is_rejected_despite_evidence() -> None:
    composer = ResponseComposer()
    draft = DraftAnswer(
        request_id="REQ_TEST",
        query_id="REQ_TEST",
        answer_text="సరిపడిన ఆధారాలు లేవు.",
        language="te",
        modality="native",
        candidate_claims=[],
        is_abstention=True,
        model_abstained=True,
        abstention_source="model_marker",
        provider="fake-provider",
    )

    response = composer.compose(
        make_inputs(
            "గోల్కొండ కోట ఎక్కడ ఉంది?",
            [make_result(CHUNK_GOLCONDA, "TE_DOC_002", "గోల్కొండ కోట", GOLCONDA_TEXT)],
            requested_mode=AnswerMode.LLM,
            draft=draft,
            provider_available=True,
        )
    )

    assert response.answer_status == AnswerStatus.ANSWERED
    assert response.generation_metadata.draft_rejected is True
    assert response.generation_metadata.used_mode == AnswerMode.LLM_FALLBACK
    assert any(
        "abstention" in reason.lower()
        for reason in response.generation_metadata.rejection_reasons
    )


def test_response_serialisation_keeps_enum_values() -> None:
    composer = ResponseComposer()
    response = composer.compose(
        make_inputs(
            "గోల్కొండ కోట ఎక్కడ ఉంది?",
            [make_result(CHUNK_GOLCONDA, "TE_DOC_002", "గోల్కొండ కోట", GOLCONDA_TEXT)],
        )
    )
    payload = response.to_dict()
    assert payload["answer_status"] == "ANSWERED"
    assert payload["detected_modality"] == "TELUGU_NATIVE"
    assert payload["query_analysis"]["intent"] == "WHERE"
    assert isinstance(payload["citations"], list)


@pytest.mark.parametrize(
    "query,text,expected",
    [
        ("గోల్కొండ కోట ఎక్కడ ఉంది?", GOLCONDA_TEXT, AnswerStatus.ANSWERED),
        ("ఫ్రాన్స్ రాజధాని ఏది?", CHARMINAR_TEXT, AnswerStatus.ABSTAINED),
    ],
)
def test_answer_vs_abstain_boundary(query: str, text: str, expected: AnswerStatus) -> None:
    composer = ResponseComposer()
    response = composer.compose(
        make_inputs(
            query,
            [make_result(CHUNK_GOLCONDA, "TE_DOC_002", "గోల్కొండ కోట", text)],
        )
    )
    assert response.answer_status == expected
