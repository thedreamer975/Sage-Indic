"""EXP-2E-02: Reproducible End-to-End Grounded Factuality Evaluation Runner.

Executes controlled end-to-end evaluation of SAGE-Indic, connecting:
1. Retrieval (BM25 CodeMix-Aware vs BM25 Baseline)
2. Evidence-grounded Generation (llama3.2:1b via Ollama / ExternalAPIProvider, with deterministic mock fallback)
3. Sentence-boundary claim extraction
4. Independent verification (RelationAwareClaimVerifier vs LinguisticClaimVerifier)
5. Strict answer-eligibility determination
6. Citation and provenance validation

Conditions:
- Condition A: SAGE-Indic Pipeline (CodeMix-Aware BM25 + Generation + RelationAwareClaimVerifier)
- Condition B: Verification Baseline (Same generated drafts as Condition A + LinguisticClaimVerifier)
- Condition C: Lexical Baseline Retrieval (Unnormalized BM25 + Generation + RelationAwareClaimVerifier)
- Condition D: No-Evidence Ablation (Empty evidence -> Strict abstention evaluation)

Outputs versioned artifacts to experiments/results/exp_2e_02/.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

# Ensure stdout uses UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from sage_indic.generation import (
    AnswerEligibility,
    DraftAnswer,
    ExternalAPIProvider,
    GenerationAdapter,
    GenerationConfig,
    GenerationProviderType,
    GenerationRequest,
    MockGenerationProvider,
    PromptComposer,
    VerifiedAnswerReport,
    verify_draft_answer,
)
from sage_indic.rag import (
    BM25Retriever,
    CodeMixedQueryNormalizer,
    ContentHash,
    DocumentChunk,
    EvidencePackage,
    RetrievalConfig,
    RetrievalResult,
)
from sage_indic.types import LanguageCategory
from sage_indic.verification import (
    AtomicClaim,
    EvidencePassage,
    LinguisticClaimVerifier,
    RelationAwareClaimVerifier,
    VerificationOutcome,
)

# ---------------------------------------------------------------------------
# Constants & File Paths
# ---------------------------------------------------------------------------

CHUNKS_PATH = REPO_ROOT / "data" / "processed" / "rag" / "phase2d_chunks.jsonl"
DEV_QUERIES_PATH = REPO_ROOT / "data" / "processed" / "rag" / "phase2d_eval_queries_dev.jsonl"
EVAL_QUERIES_PATH = REPO_ROOT / "data" / "processed" / "rag" / "phase2d_eval_queries_eval.jsonl"
DEV_VERIF_PATH = REPO_ROOT / "data" / "processed" / "verification" / "dev_verification.jsonl"
EVAL_VERIF_PATH = REPO_ROOT / "data" / "processed" / "verification" / "eval_verification.jsonl"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "experiments" / "results" / "exp_2e_02"

# Curated essential facts for answerable query families
QUERY_FAMILY_GROUND_TRUTH = {
    "QF_DEV_001": {
        "target_doc": "TE_DOC_001",
        "primary_chunk": "TE_DOC_001#c0001",
        "essential_keywords": ["1591", "కులీ కుతుబ్ షా", "మహమ్మద్ కులీ"],
        "essential_fact_en": "Built in 1591 by Muhammad Quli Qutb Shah",
        "linked_verif_id": "V_DEV_001",
    },
    "QF_DEV_002": {
        "target_doc": "TE_DOC_004",
        "primary_chunk": "TE_DOC_004#c0001",
        "essential_keywords": ["నెహ్రూ", "జవహర్‌లాల్ నెహ్రూ", "1955", "డిసెంబరు 10"],
        "essential_fact_en": "Foundation laid by Prime Minister Jawaharlal Nehru on 10 Dec 1955",
        "linked_verif_id": "V_DEV_002",
    },
    "QF_DEV_003": {
        "target_doc": "TE_DOC_007",
        "primary_chunk": "TE_DOC_007#c0002",
        "essential_keywords": ["బెంజోని", "గియోవన్నీ బెంజోని", "1876", "Benzoni"],
        "essential_fact_en": "Sculpted by Italian sculptor Giovanni Maria Benzoni in 1876",
        "linked_verif_id": "V_DEV_003",
    },
    "QF_DEV_004": {
        "target_doc": "TE_DOC_010",
        "primary_chunk": "TE_DOC_010#c0002",
        "essential_keywords": ["మిషన్ కాకతీయ", "కాకతీయ", "చెరువుల"],
        "essential_fact_en": "Mission Kakatiya launched for restoring irrigation tanks",
        "linked_verif_id": "V_DEV_004",
    },
    "QF_DEV_005": {
        "target_doc": None,
        "primary_chunk": None,
        "essential_keywords": [],
        "essential_fact_en": "Unanswerable - Dum Biryani preparation in Mughal era not in corpus",
        "linked_verif_id": None,
    },
    "QF_DEV_006": {
        "target_doc": None,
        "primary_chunk": None,
        "essential_keywords": [],
        "essential_fact_en": "Unanswerable - Amaravati Buddhist stupa marble uniqueness not in corpus",
        "linked_verif_id": None,
    },
    "QF_EVAL_001": {
        "target_doc": "TE_DOC_002",
        "primary_chunk": "TE_DOC_002#c0001",
        "essential_keywords": ["బాలా హిస్సార్", "బాలాహిస్సార్", "Bala Hissar"],
        "essential_fact_en": "Clapping at Fateh Darwaza entry is heard at Bala Hissar (highest point)",
        "linked_verif_id": "V_EVAL_001",
    },
    "QF_EVAL_002": {
        "target_doc": "TE_DOC_003",
        "primary_chunk": "TE_DOC_003#c0002",
        "essential_keywords": ["కీర్తి తోరణం", "కాకతీయ కళాతోరణం", "తోరణం", "కళాతోరణం"],
        "essential_fact_en": "Kakatiya Kala Thoranam / Kirti Thoranam included in official emblem of Telangana",
        "linked_verif_id": "V_EVAL_002",
    },
    "QF_EVAL_003": {
        "target_doc": "TE_DOC_005",
        "primary_chunk": "TE_DOC_005#c0002",
        "essential_keywords": ["2021", "యునెస్కో", "ప్రపంచ వారసత్వ"],
        "essential_fact_en": "UNESCO World Heritage site status recognized in July 2021",
        "linked_verif_id": "V_EVAL_003",
    },
    "QF_EVAL_004": {
        "target_doc": "TE_DOC_006",
        "primary_chunk": "TE_DOC_006#c0001",
        "essential_keywords": ["575", "6వ శతాబ్దం", "రేనాటి చోళులు"],
        "essential_fact_en": "Kalamalla inscription dates to 575 CE (6th century, Renati Cholas)",
        "linked_verif_id": "V_EVAL_004",
    },
    "QF_EVAL_005": {
        "target_doc": "TE_DOC_008",
        "primary_chunk": "TE_DOC_008#c0002",
        "essential_keywords": ["2004", "జీఐ ట్యాగ్", "భౌగోళిక గుర్తింపు"],
        "essential_fact_en": "Pochampally Ikat handloom textiles received GI tag in 2004",
        "linked_verif_id": "V_EVAL_005",
    },
    "QF_EVAL_006": {
        "target_doc": "TE_DOC_009",
        "primary_chunk": "TE_DOC_009#c0002",
        "essential_keywords": ["ఆనంద నిలయం", "ఆనందనిలయం", "Ananda Nilayam"],
        "essential_fact_en": "Gold vimana gopuram over the sanctum sanctorum is called Ananda Nilayam",
        "linked_verif_id": "V_EVAL_006",
    },
    "QF_EVAL_007": {
        "target_doc": None,
        "primary_chunk": None,
        "essential_keywords": [],
        "essential_fact_en": "Unanswerable - Kuchipudi dance village origin not in corpus",
        "linked_verif_id": None,
    },
    "QF_EVAL_008": {
        "target_doc": None,
        "primary_chunk": None,
        "essential_keywords": [],
        "essential_fact_en": "Unanswerable - Kaleshwaram barrage count not in corpus",
        "linked_verif_id": None,
    },
}


def compute_file_sha256(path: Path) -> str:
    if not path.exists():
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def load_corpus_chunks(path: Path) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            chunk = DocumentChunk(
                chunk_id=c["chunk_id"],
                document_id=c["document_id"],
                chunk_index=c["chunk_index"],
                char_start=c["char_start"],
                char_end=c["char_end"],
                text=c["text"],
                raw_text_ref=c["raw_text_ref"],
                normalized_text_ref=c["normalized_text_ref"],
                source_name=c["source_name"],
                title=c["title"],
                content_hash=ContentHash(
                    algorithm=c["content_hash"]["algorithm"],
                    digest=c["content_hash"]["digest"],
                ),
                source_url=c.get("source_url"),
                metadata=c.get("metadata", {}),
            )
            chunks.append(chunk)
    return chunks


def load_evaluation_manifest(split: str = "both") -> list[dict[str, Any]]:
    splits = ["dev", "eval"] if split == "both" else [split]
    manifest: list[dict[str, Any]] = []

    for s in splits:
        path = DEV_QUERIES_PATH if s == "dev" else EVAL_QUERIES_PATH
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                q = json.loads(line)
                qid = q["query_id"]
                qf = q["query_family_id"]
                mod = q.get("modality", "native")
                is_answerable = len(q.get("relevant_chunk_ids", [])) > 0

                # Resolve language category
                if mod == "native":
                    lang_cat = LanguageCategory.TELUGU_NATIVE
                elif mod == "romanized":
                    lang_cat = LanguageCategory.ROMANIZED_TELUGU
                elif mod == "code_mixed":
                    lang_cat = LanguageCategory.TELUGU_ENGLISH_CODE_MIXED
                else:
                    lang_cat = LanguageCategory.UNKNOWN

                gt = QUERY_FAMILY_GROUND_TRUTH.get(qf, {})

                manifest.append(
                    {
                        "query_id": qid,
                        "query_text": q["query_text"],
                        "split": s,
                        "query_family_id": qf,
                        "modality": mod,
                        "language_category": lang_cat,
                        "is_answerable": is_answerable,
                        "relevant_document_ids": q.get("relevant_document_ids", []),
                        "relevant_chunk_ids": q.get("relevant_chunk_ids", []),
                        "target_doc": gt.get("target_doc"),
                        "primary_chunk": gt.get("primary_chunk"),
                        "essential_keywords": gt.get("essential_keywords", []),
                        "essential_fact_en": gt.get("essential_fact_en", ""),
                        "linked_verif_id": gt.get("linked_verif_id"),
                        "annotation_status": q.get("annotation_status", "pilot_single_annotator"),
                    }
                )

    return manifest


def check_fact_correctness(answer_text: str, essential_keywords: list[str]) -> bool:
    """Checks whether the generated text contains the essential keywords for the answerable query."""
    if not essential_keywords:
        return False
    lower_ans = answer_text.lower()
    for kw in essential_keywords:
        if kw.lower() in lower_ans:
            return True
    return False


def run_condition_evaluation(
    manifest: list[dict[str, Any]],
    retriever: BM25Retriever | None,
    adapter: GenerationAdapter,
    condition_name: str,
    top_k: int = 3,
    use_no_evidence: bool = False,
    cache: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Runs end-to-end retrieval, generation, and dual-verifier audits for a given condition."""
    results: list[dict[str, Any]] = []
    rel_verifier = RelationAwareClaimVerifier()
    ling_verifier = LinguisticClaimVerifier()
    cache = cache if cache is not None else {}

    for item in manifest:
        qid = item["query_id"]
        qtext = item["query_text"]
        lang_cat = item["language_category"]
        is_answerable = item["is_answerable"]
        split = item["split"]
        mod = item["modality"]

        t0_retrieval = time.perf_counter()
        if use_no_evidence or retriever is None:
            retrieved_results: list[RetrievalResult] = []
            passages: list[EvidencePassage] = []
            ret_latency_ms = 0.0
            retrieval_hit = False
        else:
            pkg = retriever.retrieve(query_id=qid, query_text=qtext, top_k=top_k)
            ret_latency_ms = (time.perf_counter() - t0_retrieval) * 1000
            retrieved_results = pkg.results
            passages = [EvidencePassage.from_retrieval_result(r) for r in retrieved_results]

            # Check if primary target chunk was retrieved in top-k
            primary_chunk = item.get("primary_chunk")
            retrieval_hit = primary_chunk in [r.chunk_id for r in retrieved_results] if primary_chunk else False

        # Build Generation Request
        req = GenerationRequest(
            query_id=qid,
            query_text=qtext,
            language_category=lang_cat,
            evidence_passages=passages,
            max_tokens=adapter.config.max_tokens,
            temperature=adapter.config.temperature,
        )

        # Check generation cache to ensure exact reproducibility and eliminate redundant provider invocations
        cache_key = f"{condition_name}::{qid}::{adapter.config.model_name}"
        cached_text = cache.get(cache_key)

        t0_gen = time.perf_counter()
        if cached_text is not None:
            # Reconstruct draft using cached text
            valid_cits, invalid_cits = adapter.composer.extract_and_validate_citations(cached_text, passages)
            is_abstention, abstention_reason = adapter._check_abstention(cached_text, req)
            candidate_claims = adapter._extract_candidate_claims(
                request_id=f"CACHED_{qid}",
                query_id=qid,
                answer_text=cached_text,
                language_category=lang_cat,
            )
            lang_str, mod_str = adapter._resolve_language_modality(lang_cat)
            draft = DraftAnswer(
                request_id=f"CACHED_{qid}",
                query_id=qid,
                answer_text=cached_text,
                language=lang_str,
                modality=mod_str,
                candidate_claims=candidate_claims,
                citations=valid_cits,
                invalid_citations=invalid_cits,
                unsupported_aspects=[],
                is_abstention=is_abstention,
                abstention_reason=abstention_reason,
                model_id=adapter.config.model_name,
                provider="api_cached",
                latency_ms=0.0,
                is_verified=False,
            )
            gen_latency_ms = (time.perf_counter() - t0_gen) * 1000
        else:
            draft = adapter.generate(req)
            gen_latency_ms = draft.latency_ms
            cache[cache_key] = draft.answer_text

        # Enforce Draft Invariant
        assert draft.is_verified is False, "CRITICAL ERROR: draft.is_verified must be False immediately after generation!"

        # Audit with RelationAwareClaimVerifier
        t0_verif_rel = time.perf_counter()
        rel_report = verify_draft_answer(draft, passages, verifier=rel_verifier)
        verif_rel_latency_ms = (time.perf_counter() - t0_verif_rel) * 1000

        # Audit with LinguisticClaimVerifier (baseline)
        t0_verif_ling = time.perf_counter()
        ling_report = verify_draft_answer(draft, passages, verifier=ling_verifier)
        verif_ling_latency_ms = (time.perf_counter() - t0_verif_ling) * 1000

        # Factual answer check
        fact_correct = check_fact_correctness(draft.answer_text, item["essential_keywords"]) if is_answerable else None

        # Determine Error Classification
        if not is_answerable:
            if draft.is_abstention or rel_report.overall_eligibility == AnswerEligibility.ABSTENTION:
                error_class = "CORRECT_ABSTENTION"
            elif rel_report.insufficient_count > 0 and rel_report.fully_supported_count == 0:
                error_class = "CAVEATED_UNANSWERABLE"
            else:
                error_class = "UNSUPPORTED_HALLUCINATION_ON_UNANSWERABLE"
        else:
            if not retrieval_hit:
                error_class = "RETRIEVAL_MISS"
            elif draft.is_abstention:
                error_class = "INCORRECT_ABSTENTION"
            elif draft.invalid_citations:
                error_class = "CITATION_HALLUCINATION"
            elif rel_report.contradicted_count > 0:
                error_class = "CONTRADICTION"
            elif rel_report.overall_eligibility == AnswerEligibility.ELIGIBLE_GROUNDED and fact_correct:
                error_class = "CORRECT_GROUNDED"
            elif rel_report.overall_eligibility == AnswerEligibility.ELIGIBLE_GROUNDED and not fact_correct:
                error_class = "FALSE_SUPPORTED_OFF_TARGET"
            elif rel_report.overall_eligibility == AnswerEligibility.REQUIRES_CAVEAT and fact_correct:
                error_class = "CORRECT_PARTIALLY_GROUNDED"
            else:
                error_class = "UNGROUNDED_OR_INSUFFICIENT"

        results.append(
            {
                "query_id": qid,
                "split": split,
                "modality": mod,
                "query_family_id": item["query_family_id"],
                "query_text": qtext,
                "is_answerable": is_answerable,
                "condition": condition_name,
                "retrieved_chunk_ids": [r.chunk_id for r in retrieved_results],
                "retrieval_hit": retrieval_hit,
                "retrieval_latency_ms": ret_latency_ms,
                "draft_answer_text": draft.answer_text,
                "is_abstention": draft.is_abstention,
                "abstention_reason": draft.abstention_reason,
                "valid_citations": draft.citations,
                "invalid_citations": draft.invalid_citations,
                "claims_count": len(draft.candidate_claims),
                "claims": [c.to_dict() for c in draft.candidate_claims],
                "generation_latency_ms": gen_latency_ms,
                "fact_correct": fact_correct,
                "error_classification": error_class,
                # Relation-Aware Verifier Audit
                "relation_aware": {
                    "eligibility": rel_report.overall_eligibility.value,
                    "supported_count": rel_report.fully_supported_count,
                    "contradicted_count": rel_report.contradicted_count,
                    "insufficient_count": rel_report.insufficient_count,
                    "conflicting_count": rel_report.conflicting_count,
                    "caveat_notes": rel_report.caveat_notes,
                    "latency_ms": verif_rel_latency_ms,
                    "claim_outcomes": [r.outcome.value for r in rel_report.claim_results],
                },
                # Linguistic Baseline Verifier Audit
                "linguistic_baseline": {
                    "eligibility": ling_report.overall_eligibility.value,
                    "supported_count": ling_report.fully_supported_count,
                    "contradicted_count": ling_report.contradicted_count,
                    "insufficient_count": ling_report.insufficient_count,
                    "conflicting_count": ling_report.conflicting_count,
                    "caveat_notes": ling_report.caveat_notes,
                    "latency_ms": verif_ling_latency_ms,
                    "claim_outcomes": [r.outcome.value for r in ling_report.claim_results],
                },
            }
        )

    return results


def aggregate_condition_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Computes comprehensive aggregate metrics across splits and modalities."""
    total_queries = len(results)
    if total_queries == 0:
        return {}

    answerable_items = [r for r in results if r["is_answerable"]]
    unanswerable_items = [r for r in results if not r["is_answerable"]]

    n_ans = len(answerable_items)
    n_unans = len(unanswerable_items)

    # Retrieval metrics on answerable queries
    retrieval_hits = sum(1 for r in answerable_items if r["retrieval_hit"])
    recall_hit_rate = (retrieval_hits / n_ans) if n_ans > 0 else 0.0

    # Fact correctness on answerable queries
    fact_correct_cnt = sum(1 for r in answerable_items if r["fact_correct"] is True)
    fact_correct_rate = (fact_correct_cnt / n_ans) if n_ans > 0 else 0.0

    # Abstention metrics
    total_abstentions = sum(1 for r in results if r["is_abstention"])
    correct_abstentions = sum(1 for r in unanswerable_items if r["is_abstention"])
    incorrect_abstentions = sum(1 for r in answerable_items if r["is_abstention"])

    correct_abstention_rate = (correct_abstentions / n_unans) if n_unans > 0 else 0.0
    incorrect_abstention_rate = (incorrect_abstentions / n_ans) if n_ans > 0 else 0.0

    # Citation metrics
    total_cits = sum(len(r["valid_citations"]) + len(r["invalid_citations"]) for r in results)
    valid_cits = sum(len(r["valid_citations"]) for r in results)
    invalid_cits = sum(len(r["invalid_citations"]) for r in results)
    citation_validity_rate = (valid_cits / total_cits) if total_cits > 0 else 1.0
    citation_hallucination_rate = (invalid_cits / total_cits) if total_cits > 0 else 0.0

    # Verifier metrics comparison (Relation-Aware vs Linguistic)
    rel_eligibility_counts = Counter_eligibility(results, "relation_aware")
    ling_eligibility_counts = Counter_eligibility(results, "linguistic_baseline")

    rel_total_claims = sum(len(r["claims"]) for r in results)
    rel_supported_claims = sum(r["relation_aware"]["supported_count"] for r in results)
    rel_contradicted_claims = sum(r["relation_aware"]["contradicted_count"] for r in results)
    rel_insufficient_claims = sum(r["relation_aware"]["insufficient_count"] for r in results)

    ling_supported_claims = sum(r["linguistic_baseline"]["supported_count"] for r in results)
    ling_contradicted_claims = sum(r["linguistic_baseline"]["contradicted_count"] for r in results)
    ling_insufficient_claims = sum(r["linguistic_baseline"]["insufficient_count"] for r in results)

    # Modality breakdown
    modalities = ["native", "romanized", "code_mixed"]
    modality_breakdown = {}
    for m in modalities:
        m_items = [r for r in results if r["modality"] == m]
        m_ans = [r for r in m_items if r["is_answerable"]]
        m_unans = [r for r in m_items if not r["is_answerable"]]
        modality_breakdown[m] = {
            "total_queries": len(m_items),
            "answerable_queries": len(m_ans),
            "unanswerable_queries": len(m_unans),
            "retrieval_hits": sum(1 for r in m_ans if r["retrieval_hit"]),
            "retrieval_hit_rate": (sum(1 for r in m_ans if r["retrieval_hit"]) / len(m_ans)) if m_ans else 0.0,
            "fact_correct": sum(1 for r in m_ans if r["fact_correct"] is True),
            "fact_correct_rate": (sum(1 for r in m_ans if r["fact_correct"] is True) / len(m_ans)) if m_ans else 0.0,
            "correct_abstentions": sum(1 for r in m_unans if r["is_abstention"]),
            "relation_aware_eligible_grounded": sum(
                1 for r in m_items if r["relation_aware"]["eligibility"] == "ELIGIBLE_GROUNDED"
            ),
            "relation_aware_requires_caveat": sum(
                1 for r in m_items if r["relation_aware"]["eligibility"] == "REQUIRES_CAVEAT"
            ),
        }

    # Split breakdown (dev vs eval)
    split_breakdown = {}
    for s in ["dev", "eval"]:
        s_items = [r for r in results if r["split"] == s]
        s_ans = [r for r in s_items if r["is_answerable"]]
        s_unans = [r for r in s_items if not r["is_answerable"]]
        split_breakdown[s] = {
            "total_queries": len(s_items),
            "answerable_queries": len(s_ans),
            "unanswerable_queries": len(s_unans),
            "retrieval_hits": sum(1 for r in s_ans if r["retrieval_hit"]),
            "retrieval_hit_rate": (sum(1 for r in s_ans if r["retrieval_hit"]) / len(s_ans)) if s_ans else 0.0,
            "fact_correct": sum(1 for r in s_ans if r["fact_correct"] is True),
            "fact_correct_rate": (sum(1 for r in s_ans if r["fact_correct"] is True) / len(s_ans)) if s_ans else 0.0,
            "correct_abstentions": sum(1 for r in s_unans if r["is_abstention"]),
            "relation_aware_eligible_grounded": sum(
                1 for r in s_items if r["relation_aware"]["eligibility"] == "ELIGIBLE_GROUNDED"
            ),
        }

    # Latencies
    mean_ret_latency = sum(r["retrieval_latency_ms"] for r in results) / total_queries
    mean_gen_latency = sum(r["generation_latency_ms"] for r in results) / total_queries
    mean_verif_latency = sum(r["relation_aware"]["latency_ms"] for r in results) / total_queries

    return {
        "total_queries": total_queries,
        "answerable_queries_count": n_ans,
        "unanswerable_queries_count": n_unans,
        "retrieval_hits_on_answerable": retrieval_hits,
        "retrieval_hit_rate_on_answerable": round(recall_hit_rate, 4),
        "fact_correct_answers_count": fact_correct_cnt,
        "fact_correct_rate_on_answerable": round(fact_correct_rate, 4),
        "total_abstentions": total_abstentions,
        "correct_abstentions_count": correct_abstentions,
        "correct_abstention_rate": round(correct_abstention_rate, 4),
        "incorrect_abstentions_count": incorrect_abstentions,
        "incorrect_abstention_rate": round(incorrect_abstention_rate, 4),
        "citations_total": total_cits,
        "citations_valid": valid_cits,
        "citations_invalid": invalid_cits,
        "citation_validity_rate": round(citation_validity_rate, 4),
        "citation_hallucination_rate": round(citation_hallucination_rate, 4),
        "relation_aware": {
            "eligibility_distribution": rel_eligibility_counts,
            "total_claims": rel_total_claims,
            "supported_claims_count": rel_supported_claims,
            "supported_claims_rate": round(rel_supported_claims / rel_total_claims, 4) if rel_total_claims else 0.0,
            "contradicted_claims_count": rel_contradicted_claims,
            "insufficient_claims_count": rel_insufficient_claims,
        },
        "linguistic_baseline": {
            "eligibility_distribution": ling_eligibility_counts,
            "total_claims": rel_total_claims,
            "supported_claims_count": ling_supported_claims,
            "supported_claims_rate": round(ling_supported_claims / rel_total_claims, 4) if rel_total_claims else 0.0,
            "contradicted_claims_count": ling_contradicted_claims,
            "insufficient_claims_count": ling_insufficient_claims,
        },
        "modality_breakdown": modality_breakdown,
        "split_breakdown": split_breakdown,
        "latency_profile_ms": {
            "mean_retrieval_ms": round(mean_ret_latency, 2),
            "mean_generation_ms": round(mean_gen_latency, 2),
            "mean_verification_ms": round(mean_verif_latency, 2),
            "mean_pipeline_total_ms": round(mean_ret_latency + mean_gen_latency + mean_verif_latency, 2),
        },
    }


def Counter_eligibility(results: list[dict[str, Any]], verifier_key: str) -> dict[str, int]:
    counts = {
        "ELIGIBLE_GROUNDED": 0,
        "REQUIRES_CAVEAT": 0,
        "INELIGIBLE_CONTRADICTED": 0,
        "ABSTENTION": 0,
    }
    for r in results:
        e = r[verifier_key]["eligibility"]
        counts[e] = counts.get(e, 0) + 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="EXP-2E-02 End-to-End Evaluation")
    parser.add_argument("--provider", choices=["api", "mock"], default="api", help="Generation provider backend")
    parser.add_argument("--api-base", default="http://127.0.0.1:11434/v1", help="OpenAI-compatible API base URL")
    parser.add_argument("--model", default="llama3.2:1b", help="Model name")
    parser.add_argument("--max-tokens", type=int, default=80, help="Max output tokens for generation")
    parser.add_argument("--temperature", type=float, default=0.0, help="Generation temperature")
    parser.add_argument("--split", choices=["dev", "eval", "both"], default="both", help="Evaluation split")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory to save artifacts")
    parser.add_argument("--top-k", type=int, default=3, help="Number of evidence chunks retrieved")
    parser.add_argument("--skip-provider-check", action="store_true", help="Skip proactive provider liveness probe")

    args = parser.parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("================================================================================")
    print("SAGE-Indic — EXP-2E-02: Reproducible End-to-End Grounded Factuality Evaluation")
    print("================================================================================")
    print(f"Timestamp:       {datetime.now(timezone.utc).isoformat()}")
    print(f"Provider:        {args.provider}")
    print(f"Model ID:        {args.model}")
    print(f"API Base:        {args.api_base}")
    print(f"Split:           {args.split}")
    print(f"Output Directory:{output_dir}")
    print()

    # 1. Dataset Provenance & File Hashes
    dataset_hashes = {
        "phase2d_chunks.jsonl": compute_file_sha256(CHUNKS_PATH),
        "phase2d_eval_queries_dev.jsonl": compute_file_sha256(DEV_QUERIES_PATH),
        "phase2d_eval_queries_eval.jsonl": compute_file_sha256(EVAL_QUERIES_PATH),
        "dev_verification.jsonl": compute_file_sha256(DEV_VERIF_PATH),
        "eval_verification.jsonl": compute_file_sha256(EVAL_VERIF_PATH),
    }

    print("Dataset Provenance SHA-256 Hashes:")
    for fn, h in dataset_hashes.items():
        print(f"  {fn:<35}: {h[:16]}...{h[-8:]}")
    print()

    # 2. Load Corpus and Build Manifest
    print("Loading Phase 2D corpus chunks and building evaluation manifest...")
    chunks = load_corpus_chunks(CHUNKS_PATH)
    manifest = load_evaluation_manifest(split=args.split)
    print(f"Loaded {len(chunks)} document chunks and {len(manifest)} evaluation queries.")
    print()

    # 3. Index Retrievers
    print("Initializing Retrievers:")
    print("  1. Condition A/B: BM25 with CodeMixedQueryNormalizer (bilingual expansion enabled)")
    norm = CodeMixedQueryNormalizer(enable_bilingual_expansion=True)
    cfg_codemix = RetrievalConfig(method="BM25_CodeMixAware", top_k=args.top_k, parameters={"k1": 1.5, "b": 0.75})
    retriever_codemix = BM25Retriever(cfg_codemix, normalizer=norm)
    retriever_codemix.index_chunks(chunks)

    print("  2. Condition C: BM25 Baseline (Sparse lexical Unicode NFC, no cross-script normalizer)")
    cfg_baseline = RetrievalConfig(method="BM25_Baseline", top_k=args.top_k, parameters={"k1": 1.5, "b": 0.75})
    retriever_baseline = BM25Retriever(cfg_baseline)
    retriever_baseline.index_chunks(chunks)
    print()

    # 4. Initialize Generation Adapter
    g_config = GenerationConfig(
        provider=GenerationProviderType.API if args.provider == "api" else GenerationProviderType.MOCK,
        api_base_url=args.api_base,
        model_name=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout_seconds=20.0,
        max_retries=1,
    )

    # Provider verification probe
    active_provider_backend = args.provider
    if args.provider == "api" and not args.skip_provider_check:
        print(f"Testing connectivity to real provider at {args.api_base} with model '{args.model}'...")
        try:
            test_adapter = GenerationAdapter(config=g_config)
            test_req = GenerationRequest(
                query_id="PROBE",
                query_text="ping",
                language_category=LanguageCategory.TELUGU_NATIVE,
                evidence_passages=[],
                max_tokens=5,
            )
            # generate with empty evidence triggers abstention response without external call,
            # so we test direct provider call:
            raw_out = test_adapter.provider.generate("Ping test", test_req, g_config)
            print(f"Provider operational! Probe latency: {raw_out.latency_ms:.1f}ms")
        except Exception as e:
            print(f"WARNING: Provider connectivity failed: {e}")
            print("Falling back to deterministic MockGenerationProvider to allow offline completion.")
            g_config = GenerationConfig(
                provider=GenerationProviderType.MOCK,
                model_name="mock-sage-indic-v1",
                temperature=0.0,
                max_tokens=args.max_tokens,
            )
            active_provider_backend = "mock_fallback"

    adapter = GenerationAdapter(config=g_config)
    print(f"Generation Adapter initialized with backend: {active_provider_backend}")
    print()

    # Load generation response cache if present
    cache_path = output_dir / "generation_cache.json"
    cache: dict[str, str] = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            print(f"Loaded {len(cache)} cached provider responses from {cache_path.name}")
        except Exception as e:
            print(f"Could not load cache: {e}")

    # ---------------------------------------------------------------------------
    # Condition A: SAGE-Indic Pipeline
    # ---------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("Executing Condition A: SAGE-Indic Pipeline (CodeMix BM25 + Generation + RelationAware)")
    print("--------------------------------------------------------------------------------")
    results_cond_a = run_condition_evaluation(
        manifest=manifest,
        retriever=retriever_codemix,
        adapter=adapter,
        condition_name="Condition_A_SAGE_Indic",
        top_k=args.top_k,
        use_no_evidence=False,
        cache=cache,
    )
    print(f"Completed Condition A: {len(results_cond_a)} queries evaluated.")

    # Save cache after Condition A
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------------------------------------------------------------------------
    # Condition B: Verification Baseline (Paired comparison on identical drafts)
    # ---------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("Executing Condition B: Verification Baseline (LinguisticClaimVerifier on Condition A Drafts)")
    print("--------------------------------------------------------------------------------")
    # Condition B is already computed side-by-side inside run_condition_evaluation!
    # In each record in results_cond_a, 'relation_aware' and 'linguistic_baseline' are audited on identical drafts.
    print("Condition B results extracted directly from paired verification audits.")

    # ---------------------------------------------------------------------------
    # Condition C: Lexical Baseline Retrieval (Sparse unnormalized BM25)
    # ---------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("Executing Condition C: Lexical Baseline Retrieval (Unnormalized BM25 + Generation)")
    print("--------------------------------------------------------------------------------")
    results_cond_c = run_condition_evaluation(
        manifest=manifest,
        retriever=retriever_baseline,
        adapter=adapter,
        condition_name="Condition_C_Lexical_Baseline",
        top_k=args.top_k,
        use_no_evidence=False,
        cache=cache,
    )
    print(f"Completed Condition C: {len(results_cond_c)} queries evaluated.")

    # Save cache after Condition C
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------------------------------------------------------------------------
    # Condition D: No-Evidence Ablation
    # ---------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("Executing Condition D: No-Evidence Ablation (Empty evidence -> Abstention testing)")
    print("--------------------------------------------------------------------------------")
    results_cond_d = run_condition_evaluation(
        manifest=manifest,
        retriever=None,
        adapter=adapter,
        condition_name="Condition_D_No_Evidence_Ablation",
        top_k=0,
        use_no_evidence=True,
        cache=cache,
    )
    print(f"Completed Condition D: {len(results_cond_d)} queries evaluated.")
    print()

    # ---------------------------------------------------------------------------
    # Compute Aggregate Metrics
    # ---------------------------------------------------------------------------
    metrics_cond_a = aggregate_condition_metrics(results_cond_a)
    metrics_cond_c = aggregate_condition_metrics(results_cond_c)
    metrics_cond_d = aggregate_condition_metrics(results_cond_d)

    # ---------------------------------------------------------------------------
    # Condition A vs Condition B Paired Analysis
    # ---------------------------------------------------------------------------
    paired_comparison = {
        "total_queries": len(manifest),
        "relation_aware": metrics_cond_a["relation_aware"],
        "linguistic_baseline": metrics_cond_a["linguistic_baseline"],
        "eligibility_shift": {
            "grounded_to_caveat": sum(
                1
                for r in results_cond_a
                if r["linguistic_baseline"]["eligibility"] == "ELIGIBLE_GROUNDED"
                and r["relation_aware"]["eligibility"] == "REQUIRES_CAVEAT"
            ),
            "caveat_to_grounded": sum(
                1
                for r in results_cond_a
                if r["linguistic_baseline"]["eligibility"] == "REQUIRES_CAVEAT"
                and r["relation_aware"]["eligibility"] == "ELIGIBLE_GROUNDED"
            ),
            "identical_decisions": sum(
                1
                for r in results_cond_a
                if r["linguistic_baseline"]["eligibility"] == r["relation_aware"]["eligibility"]
            ),
        },
    }

    # ---------------------------------------------------------------------------
    # Condition A vs Condition C Retrieval Comparison
    # ---------------------------------------------------------------------------
    retrieval_comparison = {
        "condition_a_codemix_recall_hit_rate": metrics_cond_a["retrieval_hit_rate_on_answerable"],
        "condition_c_baseline_recall_hit_rate": metrics_cond_c["retrieval_hit_rate_on_answerable"],
        "condition_a_fact_correct_rate": metrics_cond_a["fact_correct_rate_on_answerable"],
        "condition_c_fact_correct_rate": metrics_cond_c["fact_correct_rate_on_answerable"],
        "modality_retrieval_hits": {
            "native": {
                "condition_a": metrics_cond_a["modality_breakdown"]["native"]["retrieval_hits"],
                "condition_c": metrics_cond_c["modality_breakdown"]["native"]["retrieval_hits"],
            },
            "romanized": {
                "condition_a": metrics_cond_a["modality_breakdown"]["romanized"]["retrieval_hits"],
                "condition_c": metrics_cond_c["modality_breakdown"]["romanized"]["retrieval_hits"],
            },
            "code_mixed": {
                "condition_a": metrics_cond_a["modality_breakdown"]["code_mixed"]["retrieval_hits"],
                "condition_c": metrics_cond_c["modality_breakdown"]["code_mixed"]["retrieval_hits"],
            },
        },
    }

    # ---------------------------------------------------------------------------
    # Error Taxonomy & Audit
    # ---------------------------------------------------------------------------
    error_taxonomy = {}
    for r in results_cond_a:
        err = r["error_classification"]
        error_taxonomy[err] = error_taxonomy.get(err, 0) + 1

    error_analysis_data = {
        "error_classification_counts": error_taxonomy,
        "queries_with_invalid_citations": [
            {"query_id": r["query_id"], "invalid": r["invalid_citations"]}
            for r in results_cond_a
            if r["invalid_citations"]
        ],
        "contradicted_queries": [
            {"query_id": r["query_id"], "notes": r["relation_aware"]["caveat_notes"]}
            for r in results_cond_a
            if r["relation_aware"]["contradicted_count"] > 0
        ],
        "unanswerable_query_evaluations": [
            {
                "query_id": r["query_id"],
                "is_abstention": r["is_abstention"],
                "eligibility": r["relation_aware"]["eligibility"],
                "answer_text": r["draft_answer_text"],
            }
            for r in results_cond_a
            if not r["is_answerable"]
        ],
    }

    # ---------------------------------------------------------------------------
    # Save All Required Versioned Artifacts
    # ---------------------------------------------------------------------------
    config_record = {
        "experiment_id": "EXP-2E-02",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "provider": active_provider_backend,
        "model_id": args.model,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "top_k_evidence": args.top_k,
        "split_evaluated": args.split,
        "dataset_hashes": dataset_hashes,
        "system_info": {
            "python_version": sys.version,
            "platform": sys.platform,
        },
    }

    (output_dir / "config.json").write_text(json.dumps(config_record, indent=2), encoding="utf-8")
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "per_query_results.json").write_text(
        json.dumps(results_cond_a, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "aggregate_metrics.json").write_text(
        json.dumps(
            {
                "condition_a_sage_indic": metrics_cond_a,
                "condition_c_lexical_baseline": metrics_cond_c,
                "condition_d_no_evidence_ablation": metrics_cond_d,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "comparison_tables.json").write_text(
        json.dumps(
            {
                "paired_verifier_comparison_A_vs_B": paired_comparison,
                "retrieval_comparison_A_vs_C": retrieval_comparison,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "error_analysis.json").write_text(
        json.dumps(error_analysis_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ---------------------------------------------------------------------------
    # Write Markdown Reproduction Instructions
    # ---------------------------------------------------------------------------
    repro_text = f"""# SAGE-Indic: EXP-2E-02 Reproduction Instructions

## Experiment Identifier
- **ID:** `EXP-2E-02`
- **Component:** End-to-End Grounded Factuality Evaluation
- **Execution Date:** {datetime.now(timezone.utc).strftime("%Y-%m-%d")}

## Execution Environment
- **Operating System:** Windows (Platform: `{sys.platform}`)
- **Python Version:** `{sys.version.split()[0]}`
- **Provider Used:** `{active_provider_backend}`
- **Model Identifier:** `{args.model}`
- **API Base:** `{args.api_base}`

## Exact Reproduction Command
```bash
python experiments/run_exp_2e_02.py --provider {args.provider} --model {args.model} --api-base {args.api_base} --split {args.split} --max-tokens {args.max_tokens}
```

## Dataset Files Verified by SHA-256
- `phase2d_chunks.jsonl`: `{dataset_hashes["phase2d_chunks.jsonl"]}`
- `phase2d_eval_queries_dev.jsonl`: `{dataset_hashes["phase2d_eval_queries_dev.jsonl"]}`
- `phase2d_eval_queries_eval.jsonl`: `{dataset_hashes["phase2d_eval_queries_eval.jsonl"]}`
- `dev_verification.jsonl`: `{dataset_hashes["dev_verification.jsonl"]}`
- `eval_verification.jsonl`: `{dataset_hashes["eval_verification.jsonl"]}`
"""
    (output_dir / "reproduction_instructions.md").write_text(repro_text, encoding="utf-8")

    # ---------------------------------------------------------------------------
    # Console Summary Table
    # ---------------------------------------------------------------------------
    print("================================================================================")
    print("EXP-2E-02 Execution Summary & Key Findings")
    print("================================================================================")
    print(f"Total Queries Evaluated:               {metrics_cond_a['total_queries']}")
    print(f"  - Answerable Queries:                {metrics_cond_a['answerable_queries_count']}")
    print(f"  - Unanswerable Queries:              {metrics_cond_a['unanswerable_queries_count']}")
    print()
    print("1. Retrieval Performance on Answerable Queries:")
    print(
        f"  - Condition A (CodeMix BM25):        {metrics_cond_a['retrieval_hits_on_answerable']} / {metrics_cond_a['answerable_queries_count']} ({metrics_cond_a['retrieval_hit_rate_on_answerable']*100:.1f}%)"
    )
    print(
        f"  - Condition C (Baseline BM25):       {metrics_cond_c['retrieval_hits_on_answerable']} / {metrics_cond_c['answerable_queries_count']} ({metrics_cond_c['retrieval_hit_rate_on_answerable']*100:.1f}%)"
    )
    print(f"    - Native: Condition A = {metrics_cond_a['modality_breakdown']['native']['retrieval_hits']} / {metrics_cond_a['modality_breakdown']['native']['answerable_queries']} | Condition C = {metrics_cond_c['modality_breakdown']['native']['retrieval_hits']} / {metrics_cond_c['modality_breakdown']['native']['answerable_queries']}")
    print(f"    - Romanized: Condition A = {metrics_cond_a['modality_breakdown']['romanized']['retrieval_hits']} / {metrics_cond_a['modality_breakdown']['romanized']['answerable_queries']} | Condition C = {metrics_cond_c['modality_breakdown']['romanized']['retrieval_hits']} / {metrics_cond_c['modality_breakdown']['romanized']['answerable_queries']}")
    print(f"    - Code-Mixed: Condition A = {metrics_cond_a['modality_breakdown']['code_mixed']['retrieval_hits']} / {metrics_cond_a['modality_breakdown']['code_mixed']['answerable_queries']} | Condition C = {metrics_cond_c['modality_breakdown']['code_mixed']['retrieval_hits']} / {metrics_cond_c['modality_breakdown']['code_mixed']['answerable_queries']}")
    print()
    print("2. End-to-End Answer Correctness (Essential Fact Coverage):")
    print(
        f"  - Condition A (CodeMix BM25 + Gen):  {metrics_cond_a['fact_correct_answers_count']} / {metrics_cond_a['answerable_queries_count']} ({metrics_cond_a['fact_correct_rate_on_answerable']*100:.1f}%)"
    )
    print(
        f"  - Condition C (Baseline BM25 + Gen): {metrics_cond_c['fact_correct_answers_count']} / {metrics_cond_c['answerable_queries_count']} ({metrics_cond_c['fact_correct_rate_on_answerable']*100:.1f}%)"
    )
    print()
    print("3. Abstention Fidelity:")
    print(
        f"  - Correct Abstention (Unanswerable): {metrics_cond_a['correct_abstentions_count']} / {metrics_cond_a['unanswerable_queries_count']} ({metrics_cond_a['correct_abstention_rate']*100:.1f}%)"
    )
    print(
        f"  - Condition D (No-Evidence Ablation):{metrics_cond_d['total_abstentions']} / {metrics_cond_d['total_queries']} ({metrics_cond_d['total_abstentions']/metrics_cond_d['total_queries']*100:.1f}%)"
    )
    print()
    print("4. Verifier Comparison (Condition A vs Condition B on Identical Drafts):")
    print(f"  - Relation-Aware Supported Claims:   {metrics_cond_a['relation_aware']['supported_claims_count']} / {metrics_cond_a['relation_aware']['total_claims']}")
    print(f"  - Linguistic Baseline Supported:     {metrics_cond_a['linguistic_baseline']['supported_claims_count']} / {metrics_cond_a['linguistic_baseline']['total_claims']}")
    print(f"  - Relation-Aware Eligibility:        {metrics_cond_a['relation_aware']['eligibility_distribution']}")
    print(f"  - Linguistic Baseline Eligibility:   {metrics_cond_a['linguistic_baseline']['eligibility_distribution']}")
    print(f"  - Decision Divergences (A vs B):     {paired_comparison['eligibility_shift']}")
    print()
    print(f"All artifacts persisted successfully in: {output_dir}")
    print("================================================================================")


if __name__ == "__main__":
    main()
