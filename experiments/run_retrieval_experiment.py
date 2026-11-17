"""Phase 2D: Controlled Cross-Script Retrieval Benchmark Experiment Runner.

Evaluates evidence retrieval over the Phase 2D corpus and query benchmark under controlled conditions:
- Condition A: bm25_baseline (sparse lexical baseline with Unicode NFC tokenization)
- Condition B: bm25_translit (BM25 with Romanized Telugu transliteration)
- Condition C: bm25_codemix (BM25 with code-mixed-aware normalization preserving English terms and adding synonyms)
- Condition D: dense_multilingual (multilingual dense retrieval baseline using paraphrase-multilingual-MiniLM-L12-v2)
- Condition E: hybrid_rrf (reciprocal rank fusion combining BM25 and dense retrieval)
- Condition F1: bm25_bpe (downstream tokenizer experiment with Phase 2B BPE_4000)
- Condition F2: bm25_unigram (downstream tokenizer experiment with Phase 2B Unigram_4000)
- Condition F3: bm25_sage (downstream tokenizer experiment with Phase 2B SAGE_4000)

Usage:
    python experiments/run_retrieval_experiment.py [--condition bm25_baseline|bm25_translit|bm25_codemix|dense_multilingual|hybrid_rrf|bm25_bpe|bm25_unigram|bm25_sage|all] [--split dev|eval|both] [--top-k 10]

Outputs versioned results to experiments/results/exp_2d_crossscript_<condition>_YYYYMMDD_HHMMSS.json.
Never overwrites historical results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
# Ensure sage_indic is on sys.path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from sage_indic.rag import (
    BM25Retriever,
    CodeMixedQueryNormalizer,
    ContentHash,
    DEFAULT_LOCAL_SNAPSHOT,
    DocumentChunk,
    HybridRetriever,
    MultilingualDenseRetriever,
    RetrievalConfig,
    RomanizedTeluguTransliterator,
    tokenize_for_bm25,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CORPUS_CHUNKS_PATH = REPO_ROOT / "data" / "processed" / "rag" / "phase2d_chunks.jsonl"
DEV_QUERIES_PATH = REPO_ROOT / "data" / "processed" / "rag" / "phase2d_eval_queries_dev.jsonl"
DEV_QRELS_PATH = REPO_ROOT / "data" / "processed" / "rag" / "phase2d_qrels_dev.jsonl"
EVAL_QUERIES_PATH = REPO_ROOT / "data" / "processed" / "rag" / "phase2d_eval_queries_eval.jsonl"
EVAL_QRELS_PATH = REPO_ROOT / "data" / "processed" / "rag" / "phase2d_qrels_eval.jsonl"
RESULTS_DIR = REPO_ROOT / "experiments" / "results"

BM25_K1 = 1.5
BM25_B = 0.75
CORPUS_VERSION = "2026.10-phase2d"
MODALITIES = ["native", "romanized", "code_mixed"]

CONDITIONS = [
    "bm25_baseline",
    "bm25_translit",
    "bm25_codemix",
    "dense_multilingual",
    "hybrid_rrf",
    "bm25_bpe",
    "bm25_unigram",
    "bm25_sage",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_chunks(path: Path) -> list[DocumentChunk]:
    chunks = []
    for line in path.open(encoding="utf-8"):
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


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def build_retriever_for_condition(
    condition: str,
    top_k: int,
) -> tuple[object, dict[str, str]]:
    """Build the retrieval model for a specific experimental condition."""
    metadata = {"condition": condition}

    if condition == "bm25_baseline":
        cfg = RetrievalConfig(
            method="BM25",
            top_k=top_k,
            parameters={"k1": BM25_K1, "b": BM25_B},
        )
        retriever = BM25Retriever(cfg)
        metadata["description"] = "Sparse lexical BM25 baseline with Unicode NFC whitespace tokenization"
        return retriever, metadata

    if condition == "bm25_translit":
        normalizer = CodeMixedQueryNormalizer(enable_bilingual_expansion=False)
        cfg = RetrievalConfig(
            method="BM25_Translit",
            top_k=top_k,
            parameters={"k1": BM25_K1, "b": BM25_B, "normalizer": "RomanizedTeluguTransliterator"},
        )
        retriever = BM25Retriever(cfg, normalizer=normalizer)
        metadata["description"] = "BM25 with deterministic Romanized Telugu transliteration"
        return retriever, metadata

    if condition == "bm25_codemix":
        normalizer = CodeMixedQueryNormalizer(enable_bilingual_expansion=True)
        cfg = RetrievalConfig(
            method="BM25_CodeMixAware",
            top_k=top_k,
            parameters={"k1": BM25_K1, "b": BM25_B, "normalizer": "CodeMixedQueryNormalizer"},
        )
        retriever = BM25Retriever(cfg, normalizer=normalizer)
        metadata["description"] = "BM25 with code-mixed-aware normalization preserving English and adding synonyms"
        return retriever, metadata

    if condition == "dense_multilingual":
        model_path = str(DEFAULT_LOCAL_SNAPSHOT) if DEFAULT_LOCAL_SNAPSHOT.exists() else "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        cfg = RetrievalConfig(
            method="Dense_Multilingual",
            top_k=top_k,
            model_name=model_path,
            parameters={"similarity": "cosine", "model": "paraphrase-multilingual-MiniLM-L12-v2"},
        )
        retriever = MultilingualDenseRetriever(cfg)
        metadata["description"] = "Dense semantic retrieval with paraphrase-multilingual-MiniLM-L12-v2"
        metadata["model_license"] = "Apache-2.0"
        return retriever, metadata

    if condition == "hybrid_rrf":
        normalizer = CodeMixedQueryNormalizer(enable_bilingual_expansion=True)
        bm25_cfg = RetrievalConfig(
            method="BM25",
            top_k=top_k * 2,
            parameters={"k1": BM25_K1, "b": BM25_B},
        )
        bm25_ret = BM25Retriever(bm25_cfg, normalizer=normalizer)

        model_path = str(DEFAULT_LOCAL_SNAPSHOT) if DEFAULT_LOCAL_SNAPSHOT.exists() else "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        dense_cfg = RetrievalConfig(
            method="Dense",
            top_k=top_k * 2,
            model_name=model_path,
        )
        dense_ret = MultilingualDenseRetriever(dense_cfg)

        hybrid_cfg = RetrievalConfig(
            method="Hybrid_RRF",
            top_k=top_k,
            parameters={"k_rrf": 60, "lexical_top_k": top_k * 2, "dense_top_k": top_k * 2},
        )
        retriever = HybridRetriever(hybrid_cfg, bm25_ret, dense_ret)
        metadata["description"] = "Hybrid retrieval: Reciprocal Rank Fusion (RRF, k=60) of CodeMix BM25 + Multilingual Dense"
        return retriever, metadata

    if condition.startswith("bm25_"):
        tok_type = condition.split("_")[1]  # bpe, unigram, sage
        model_file = REPO_ROOT / "experiments" / "saved_models" / f"{tok_type}_4000.json"
        if not model_file.exists():
            raise FileNotFoundError(f"Tokenizer model not found: {model_file}")

        if tok_type == "bpe":
            from sage_indic.tokenizer import BpeBaselineTokenizer
            tok = BpeBaselineTokenizer()
        elif tok_type == "unigram":
            from sage_indic.tokenizer import UnigramBaselineTokenizer
            tok = UnigramBaselineTokenizer()
        elif tok_type == "sage":
            from sage_indic.tokenizer import SageTokenizer
            tok = SageTokenizer()
        else:
            raise ValueError(f"Unknown tokenizer type: {tok_type}")

        tok.load(model_file)
        cfg = RetrievalConfig(
            method=f"BM25_{tok_type.upper()}_4000",
            top_k=top_k,
            parameters={"k1": BM25_K1, "b": BM25_B, "tokenizer": f"{tok_type}_4000"},
        )
        retriever = BM25Retriever(cfg, tokenizer_fn=tok.encode)
        metadata["description"] = f"BM25 retrieval indexed and queried with Phase 2B {tok_type.upper()}_4000 subwords"
        metadata["vocab_size"] = "4000"
        return retriever, metadata

    raise ValueError(f"Unknown condition: {condition}")


def compute_metrics(
    queries: list[dict],
    qrels: list[dict],
    retriever: object,
    top_k: int,
) -> dict:
    """Compute Recall@1, Recall@5, Recall@10, MRR@10, nDCG@10, latency over queries."""
    qrel_by_query_doc: dict[str, dict[str, int]] = {}
    for r in qrels:
        qid = r["query_id"]
        did = r["document_id"]
        score = r.get("adjudicated_score", 0)
        if qid not in qrel_by_query_doc:
            qrel_by_query_doc[qid] = {}
        qrel_by_query_doc[qid][did] = max(qrel_by_query_doc[qid].get(did, 0), score)

    per_query: list[dict] = []
    latencies: list[float] = []

    for q in queries:
        qid = q["query_id"]
        modality = q.get("modality", "native")
        is_answerable = len(q.get("relevant_document_ids", [])) > 0

        # Execute retrieval with latency profiling
        start_t = time.perf_counter()
        results = retriever.search(q["query_text"], top_k=top_k)
        lat_ms = (time.perf_counter() - start_t) * 1000.0
        latencies.append(lat_ms)

        # Deduplicate to unique document IDs in ranked order
        seen_docs: dict[str, int] = {}
        doc_grade_at_rank: list[int] = []
        for r in results:
            did = r.document_id
            if did not in seen_docs:
                grade = qrel_by_query_doc.get(qid, {}).get(did, 0)
                seen_docs[did] = grade
                doc_grade_at_rank.append(grade)

        doc_rel_ids = {
            did for did, grade in qrel_by_query_doc.get(qid, {}).items() if grade >= 1
        }
        n_relevant_docs = len(doc_rel_ids)

        def recall_at_k(k: int) -> float | None:
            if n_relevant_docs == 0:
                return None
            hits = sum(1 for g in doc_grade_at_rank[:k] if g >= 1)
            return hits / n_relevant_docs

        def mrr() -> float:
            for rank, g in enumerate(doc_grade_at_rank, 1):
                if g >= 1:
                    return 1.0 / rank
            return 0.0

        def ndcg_at_k(k: int) -> float | None:
            if n_relevant_docs == 0:
                return None
            actual_grades = doc_grade_at_rank[:k]
            ideal_grades = sorted(
                qrel_by_query_doc.get(qid, {}).values(), reverse=True
            )[:k]
            dcg = sum(g / math.log2(i + 2) for i, g in enumerate(actual_grades))
            idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal_grades))
            return dcg / idcg if idcg > 0 else 0.0

        top_retrieved = [
            {"chunk_id": r.chunk_id, "document_id": r.document_id, "score": r.score}
            for r in results[:10]
        ]

        per_query.append({
            "query_id": qid,
            "modality": modality,
            "is_answerable": is_answerable,
            "n_relevant_docs": n_relevant_docs,
            "recall_at_1": recall_at_k(1),
            "recall_at_5": recall_at_k(5),
            "recall_at_10": recall_at_k(10),
            "mrr_at_10": mrr() if is_answerable else None,
            "ndcg_at_10": ndcg_at_k(10),
            "latency_ms": round(lat_ms, 2),
            "top_retrieved": top_retrieved,
        })

    def safe_mean(vals: list[float | None]) -> float | None:
        valid = [v for v in vals if v is not None]
        return sum(valid) / len(valid) if valid else None

    def split_by(key: str, value) -> list[dict]:
        return [pq for pq in per_query if pq.get(key) == value]

    def aggregate(subset: list[dict]) -> dict:
        return {
            "n_queries": len(subset),
            "recall_at_1": safe_mean([pq["recall_at_1"] for pq in subset]),
            "recall_at_5": safe_mean([pq["recall_at_5"] for pq in subset]),
            "recall_at_10": safe_mean([pq["recall_at_10"] for pq in subset]),
            "mrr_at_10": safe_mean([pq["mrr_at_10"] for pq in subset]),
            "ndcg_at_10": safe_mean([pq["ndcg_at_10"] for pq in subset]),
            "mean_latency_ms": safe_mean([pq["latency_ms"] for pq in subset]),
        }

    overall = aggregate(per_query)
    answerable = aggregate(split_by("is_answerable", True))
    unanswerable = aggregate(split_by("is_answerable", False))
    by_modality = {m: aggregate(split_by("modality", m)) for m in MODALITIES}

    return {
        "overall": overall,
        "answerable": answerable,
        "unanswerable": unanswerable,
        "by_modality": by_modality,
        "per_query": per_query,
    }


def run_split(
    split_name: str,
    queries_path: Path,
    qrels_path: Path,
    chunks: list[DocumentChunk],
    top_k: int,
    chunks_hash: str,
    condition: str,
) -> dict:
    """Run retrieval evaluation for one split under specified condition."""
    print(f"\n[{split_name} | {condition}] Loading queries from {queries_path}...")
    queries = load_jsonl(queries_path)
    qrels = load_jsonl(qrels_path)

    retriever, meta = build_retriever_for_condition(condition, top_k)
    t0 = time.perf_counter()
    retriever.index_chunks(chunks)
    index_time_s = time.perf_counter() - t0
    print(f"[{split_name} | {condition}] Index built over {len(chunks)} chunks in {index_time_s:.2f}s.")

    metrics = compute_metrics(queries, qrels, retriever, top_k)

    queries_hash = file_sha256(queries_path)
    qrels_hash = file_sha256(qrels_path)

    print(f"\n[{split_name} | {condition}] === Results ===")
    overall = metrics["overall"]
    print(f"  Overall ({overall['n_queries']} queries, mean lat={overall['mean_latency_ms']:.2f}ms): "
          f"Recall@1={overall['recall_at_1']:.4f}, "
          f"Recall@5={overall['recall_at_5']:.4f}, "
          f"Recall@10={overall['recall_at_10']:.4f}, "
          f"MRR@10={overall['mrr_at_10']:.4f}, "
          f"nDCG@10={overall['ndcg_at_10']:.4f}")

    for modality in MODALITIES:
        m = metrics["by_modality"][modality]
        if m["n_queries"] == 0:
            continue
        r1 = m["recall_at_1"]
        r5 = m["recall_at_5"]
        mrr = m["mrr_at_10"]
        lat = m["mean_latency_ms"]
        print(f"  [{modality:12s}] n={m['n_queries']}: Recall@1={r1 if r1 is not None else 'N/A':.4f}, "
              f"Recall@5={r5 if r5 is not None else 'N/A':.4f}, MRR@10={mrr if mrr is not None else 'N/A':.4f}, "
              f"Latency={lat:.2f}ms")

    return {
        "split": split_name,
        "condition": condition,
        "condition_metadata": meta,
        "queries_file": str(queries_path),
        "queries_sha256": queries_hash,
        "qrels_file": str(qrels_path),
        "qrels_sha256": qrels_hash,
        "corpus_chunks_sha256": chunks_hash,
        "n_queries": len(queries),
        "n_qrels": len(qrels),
        "top_k": top_k,
        "index_time_seconds": round(index_time_s, 4),
        "metrics": {
            "overall": overall,
            "answerable": metrics["answerable"],
            "unanswerable": metrics["unanswerable"],
            "by_modality": metrics["by_modality"],
        },
        "per_query": metrics["per_query"],
    }


def run_condition_experiment(
    condition: str,
    split_choice: str,
    top_k: int,
    chunks: list[DocumentChunk],
    chunks_hash: str,
) -> Path:
    """Run evaluation for a single condition and persist versioned JSON."""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"exp_2d_crossscript_{condition}_{timestamp}.json"

    experiment_record: dict = {
        "experiment_id": f"EXP-2D-{condition.upper()}-{timestamp}",
        "run_timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        "condition": condition,
        "corpus_version": CORPUS_VERSION,
        "corpus_chunks_file": str(CORPUS_CHUNKS_PATH),
        "corpus_chunks_sha256": chunks_hash,
        "corpus_size_chunks": len(chunks),
        "top_k": top_k,
        "limitations": [
            "30-chunk corpus is small pilot benchmark; high variance in subgroup confidence intervals.",
            "Relevance judgments are single-annotator derived with annotation_status=PENDING.",
            "Unanswerable query ranking metrics are computed for diagnostic completeness but NOT interpreted as answerability classification.",
            "BM25 cross-script matching relies on normalizer/transliterator mapping quality.",
        ],
        "splits": [],
    }

    if split_choice in ("dev", "both"):
        split_result = run_split("dev", DEV_QUERIES_PATH, DEV_QRELS_PATH, chunks, top_k, chunks_hash, condition)
        experiment_record["splits"].append(split_result)

    if split_choice in ("eval", "both"):
        split_result = run_split("eval", EVAL_QUERIES_PATH, EVAL_QRELS_PATH, chunks, top_k, chunks_hash, condition)
        experiment_record["splits"].append(split_result)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(experiment_record, f, ensure_ascii=False, indent=2)

    print(f"\n[DONE] Condition {condition} results saved to: {out_path}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2D Cross-Script Retrieval Benchmark")
    parser.add_argument(
        "--condition",
        choices=CONDITIONS + ["all"],
        default="all",
        help="Which retrieval/normalization condition to evaluate.",
    )
    parser.add_argument(
        "--split",
        choices=["dev", "eval", "both"],
        default="both",
        help="Which benchmark split to evaluate.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of results to retrieve per query.",
    )
    args = parser.parse_args()

    if not CORPUS_CHUNKS_PATH.exists():
        print(f"ERROR: Corpus chunks not found at {CORPUS_CHUNKS_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading corpus from {CORPUS_CHUNKS_PATH}...")
    chunks = load_chunks(CORPUS_CHUNKS_PATH)
    chunks_hash = file_sha256(CORPUS_CHUNKS_PATH)
    print(f"Loaded {len(chunks)} chunks. SHA-256: {chunks_hash}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    conditions_to_run = CONDITIONS if args.condition == "all" else [args.condition]
    print(f"Executing {len(conditions_to_run)} condition(s): {', '.join(conditions_to_run)}")

    saved_paths = []
    for cond in conditions_to_run:
        print(f"\n{'='*70}\nRunning Condition: {cond}\n{'='*70}")
        p = run_condition_experiment(cond, args.split, args.top_k, chunks, chunks_hash)
        saved_paths.append(p)

    print(f"\n{'='*70}\nAll experiments completed successfully!")
    for p in saved_paths:
        print(f" - {p}")


if __name__ == "__main__":
    main()
