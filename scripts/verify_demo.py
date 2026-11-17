"""End-to-end verification for a running SAGE-Indic demo.

Usage (backend must already be running):

    python scripts/verify_demo.py
    python scripts/verify_demo.py --base-url http://127.0.0.1:8000

The script executes every advertised example against the live API, checks the
manually stated expected behaviour, and validates citation integrity. It does
not compare answer wording: every answer is produced live by the pipeline.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request

EXPECTED_STATUS = {
    "answer": "ANSWERED",
    "partial": "PARTIALLY_ANSWERED",
    "abstain": "ABSTAINED",
}

MARKER = re.compile(r"\[(C\d+)\]")
PASSAGE_TAG = re.compile(r"\[[A-Za-z0-9_\-]+#[A-Za-z0-9_\-]+\]")


def request_json(base_url: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    url = f"{base_url.rstrip('/')}{path}"
    data = None
    headers = {"Accept": "application/json"}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def check_citations(body: dict) -> list[str]:
    problems: list[str] = []
    citations = body.get("citations", [])
    claims = body.get("answer_claims", [])
    evidence = body.get("retrieved_evidence", [])

    citation_ids = [citation["citation_id"] for citation in citations]
    if len(citation_ids) != len(set(citation_ids)):
        problems.append("duplicate citation IDs")

    known = set(citation_ids)
    evidence_ids = {item["evidence_id"] for item in evidence}
    claim_ids = {claim["claim_id"] for claim in claims}

    for citation in citations:
        if citation["evidence_id"] not in evidence_ids:
            problems.append(f"citation {citation['citation_id']} references missing evidence")
        if not set(citation["claim_ids"]) <= claim_ids:
            problems.append(f"citation {citation['citation_id']} references missing claims")
        if citation["supports_claim"] and citation["verification_status"] != "SUPPORTED":
            problems.append(f"citation {citation['citation_id']} claims support without SUPPORTED")

    for claim in claims:
        if not set(claim["citation_ids"]) <= known:
            problems.append(f"claim {claim['claim_id']} references unknown citations")

    markers = set(MARKER.findall(body.get("answer_text", "")))
    if not markers <= known:
        problems.append(f"answer text cites unknown IDs: {sorted(markers - known)}")
    if PASSAGE_TAG.search(body.get("answer_text", "")):
        problems.append("answer text leaks internal passage IDs")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Exercise the optional LLM layer for every example (slow on local models).",
    )
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    failures: list[str] = []

    try:
        status_code, health = request_json(args.base_url, "/api/health")
        status_code, status = request_json(args.base_url, "/api/status")
        _, examples_payload = request_json(args.base_url, "/api/examples")
        _, corpus = request_json(args.base_url, "/api/corpus")
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"FAIL: backend not reachable at {args.base_url}: {exc}")
        return 1

    print(f"Backend: {args.base_url}")
    print(f"  health: {health.get('status')} (corpus_loaded={health.get('corpus_loaded')})")
    print(
        "  corpus: "
        f"{corpus.get('document_count')} documents / {corpus.get('chunk_count')} chunks"
    )
    print(
        "  retriever: "
        f"{status.get('retriever', {}).get('method')} "
        f"(indexed={status.get('retriever', {}).get('indexed')})"
    )
    print(
        "  safety: "
        f"{status.get('safety', {}).get('method')} "
        f"(semantic={status.get('safety', {}).get('semantic_classifier_available')})"
    )
    print(
        "  llm: "
        f"available={status.get('llm', {}).get('available')} "
        f"model={status.get('llm', {}).get('model')}"
    )

    examples = examples_payload.get("examples", [])
    print(f"\nRunning {len(examples)} advertised example queries (live pipeline):\n")
    header = f"{'expected':<22} {'actual':<19} {'ms':>7} {'ev':>3} {'clm':>3} {'cit':>3}  query"
    print(header)
    print("-" * len(header))

    for example in examples:
        started = time.perf_counter()
        try:
            _, body = request_json(
                args.base_url,
                "/api/query",
                {
                    "query": example["query"],
                    "use_llm": bool(args.use_llm),
                    "top_k": 8,
                },
            )
        except (urllib.error.URLError, TimeoutError) as exc:
            failures.append(f"{example['id']}: request failed: {exc}")
            print(
                f"{'request failed':<22} {'-':<19} {'-':>7} {'-':>3} {'-':>3} "
                f"{'-':>3}  {example['query']}"
            )
            continue

        elapsed_ms = (time.perf_counter() - started) * 1000
        expected = EXPECTED_STATUS.get(example["expected_behavior"])
        actual = body["answer_status"]
        if expected is not None and actual != expected:
            failures.append(
                f"{example['id']}: expected {expected}, got {actual} "
                f"({body.get('abstention_reason') or body.get('query_analysis')})"
            )

        if actual in {"ANSWERED", "PARTIALLY_ANSWERED"}:
            if not body.get("citations"):
                failures.append(f"{example['id']}: no citations on an answered response")
            if not body["verification_summary"]["all_claims_supported"]:
                failures.append(f"{example['id']}: not all claims are supported")
        else:
            if body.get("citations") or body.get("answer_claims"):
                failures.append(
                    f"{example['id']}: abstained response still carries claims/citations"
                )

        for problem in check_citations(body):
            failures.append(f"{example['id']}: {problem}")

        print(
            f"{expected or '?':<22} {actual:<19} {elapsed_ms:>7.0f} "
            f"{len(body.get('retrieved_evidence', [])):>3} "
            f"{len(body.get('answer_claims', [])):>3} "
            f"{len(body.get('citations', [])):>3}  {example['query']}"
        )

    # Default mode must remain deterministic when use_llm is omitted.
    _, default_body = request_json(
        args.base_url, "/api/query", {"query": "గోల్కొండ కోట ఎక్కడ ఉంది?"}
    )
    if default_body["generation_metadata"]["used_mode"] != "deterministic":
        failures.append("default query did not use deterministic composition")

    print()
    if failures:
        print(f"FAILED: {len(failures)} problem(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASSED: all advertised behaviours and citation-integrity checks succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
