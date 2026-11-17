"""API surface tests for the SAGE-Indic demo backend.

The tests use the real corpus and the frozen SAGE tokenizer when available, so
they also smoke-test the complete deterministic pipeline.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sage_indic.api.app import create_app
from sage_indic.config import find_project_root
from sage_indic.pipeline.service import SageQueryService


@pytest.fixture(scope="module")
def client() -> TestClient:
    service = SageQueryService()
    with TestClient(create_app(service)) as test_client:
        yield test_client


def assert_wire_citation_integrity(payload: dict) -> None:
    citation_ids = [citation["citation_id"] for citation in payload["citations"]]
    assert len(citation_ids) == len(set(citation_ids))
    known = set(citation_ids)
    evidence_ids = {item["evidence_id"] for item in payload["retrieved_evidence"]}
    claim_ids = {claim["claim_id"] for claim in payload["answer_claims"]}

    for citation in payload["citations"]:
        assert citation["evidence_id"] in evidence_ids
        assert set(citation["claim_ids"]) <= claim_ids
    for claim in payload["answer_claims"]:
        assert set(claim["citation_ids"]) <= known
    markers = set(re.findall(r"\[(C\d+)\]", payload["answer_text"]))
    assert markers <= known


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["corpus_loaded"] is True


def test_status_reports_real_runtime_modes(client: TestClient) -> None:
    response = client.get("/api/status")
    assert response.status_code == 200
    body = response.json()
    assert body["corpus"]["documents"] > 0
    assert body["corpus"]["chunks"] > 0
    assert body["retriever"]["indexed"] is True
    assert body["default_generation_mode"] == "deterministic"
    assert body["deterministic_fallback"] is True
    assert "method" in body["safety"]


def test_examples_are_prompts_not_stored_answers(client: TestClient) -> None:
    response = client.get("/api/examples")
    assert response.status_code == 200
    body = response.json()
    assert len(body["examples"]) >= 9
    assert "answers are generated live" in body["note"].lower()
    for example in body["examples"]:
        assert example["query"]
        assert "answer" not in example


def test_corpus_metadata_serialises_license_status(client: TestClient) -> None:
    response = client.get("/api/corpus")
    assert response.status_code == 200
    body = response.json()
    assert body["document_count"] == len(body["documents"])
    assert body["chunk_count"] > 0
    for document in body["documents"]:
        assert isinstance(document["license_status"], str)
        assert document["chunk_count"] > 0


@pytest.mark.parametrize(
    "query,expected_status,expected_modality",
    [
        ("గోల్కొండ కోట ఎక్కడ ఉంది?", "ANSWERED", "TELUGU_NATIVE"),
        ("Golconda fort ekkada undi?", "ANSWERED", "ROMANIZED_TELUGU"),
        (
            "Golconda fort location gurinchi cheppu",
            "ANSWERED",
            "TELUGU_ENGLISH_CODE_MIXED",
        ),
        ("చార్మినార్ ఎప్పుడు నిర్మించారు?", "ANSWERED", "TELUGU_NATIVE"),
        ("Charminar eppudu nirmincharu?", "ANSWERED", "ROMANIZED_TELUGU"),
        (
            "Charminar construction date gurinchi cheppu",
            "ANSWERED",
            "TELUGU_ENGLISH_CODE_MIXED",
        ),
    ],
)
def test_answerable_queries_across_modalities(
    client: TestClient,
    query: str,
    expected_status: str,
    expected_modality: str,
) -> None:
    response = client.post("/api/query", json={"query": query, "use_llm": False, "top_k": 8})
    assert response.status_code == 200
    body = response.json()
    assert body["answer_status"] == expected_status
    assert body["detected_modality"] == expected_modality
    assert body["citations"], "an answered query must carry at least one citation"
    assert body["verification_summary"]["all_claims_supported"] is True
    assert body["generation_metadata"]["used_mode"] == "deterministic"
    assert body["generation_metadata"]["draft_rejected"] is False
    assert re.search(r"\[C\d+\]", body["answer_text"])
    assert_wire_citation_integrity(body)


def test_unanswerable_query_abstains_without_citations(client: TestClient) -> None:
    response = client.post(
        "/api/query", json={"query": "ఫ్రాన్స్ రాజధాని ఏది?", "use_llm": False}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer_status"] == "ABSTAINED"
    assert body["citations"] == []
    assert body["answer_claims"] == []
    assert body["abstention_reason"]
    assert body["generation_metadata"]["draft_rejected"] is False


def test_partially_answerable_query_is_partial(client: TestClient) -> None:
    response = client.post(
        "/api/query",
        json={"query": "Charminar height and entry fee enti?", "use_llm": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer_status"] == "PARTIALLY_ANSWERED"
    assert body["query_analysis"]["evidence_coverage"] < 1.0
    assert "entry" in body["query_analysis"]["missing_terms"]
    assert body["citations"]
    assert_wire_citation_integrity(body)


def test_unsafe_query_is_blocked(client: TestClient) -> None:
    response = client.post(
        "/api/query", json={"query": "ఒకరిని ఎలా చంపాలి?", "use_llm": False}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer_status"] == "BLOCKED"
    assert body["safety"]["label"] == "UNSAFE"
    assert body["citations"] == []
    assert body["answer_claims"] == []


def test_deterministic_mode_is_default_without_use_llm(client: TestClient) -> None:
    response = client.post("/api/query", json={"query": "గోల్కొండ కోట ఎక్కడ ఉంది?"})
    assert response.status_code == 200
    body = response.json()
    assert body["generation_metadata"]["requested_mode"] == "deterministic"
    assert body["generation_metadata"]["used_mode"] == "deterministic"


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "valid", "top_k": 0},
        {"query": "valid", "top_k": 11},
        {"query": "x" * 1001},
    ],
)
def test_invalid_requests_are_rejected(client: TestClient, payload: dict) -> None:
    response = client.post("/api/query", json=payload)
    assert response.status_code == 422


def test_unknown_api_route_returns_json_404(client: TestClient) -> None:
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_cors_allows_configured_frontend_origin(client: TestClient) -> None:
    response = client.options(
        "/api/query",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_built_frontend_is_served_when_present(client: TestClient) -> None:
    dist = Path(find_project_root()) / "frontend" / "dist"
    if not dist.is_dir():
        pytest.skip("frontend/dist not built in this environment")
    response = client.get("/")
    assert response.status_code == 200
    assert '<div id="root">' in response.text
