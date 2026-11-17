"""Hybrid Retriever combining lexical BM25 and dense semantic retrieval for Phase 2D.

Implements Reciprocal Rank Fusion (RRF):
    RRF_score(d) = sum_{m in models} 1.0 / (k_rrf + rank_m(d))
Standard k_rrf = 60 (Cormack et al., 2009).
Preserves parent document and chunk provenance, deterministic tie-breaking, and TrustBoundaryEnforcer integration.
"""

from __future__ import annotations

from typing import Any

from sage_indic.rag.retriever import BaseRetriever
from sage_indic.rag.types import (
    DocumentChunk,
    RetrievalConfig,
    RetrievalResult,
)


class HybridRetriever(BaseRetriever):
    """Hybrid evidence retriever combining lexical (BM25) and dense semantic models.

    Parameters (via config.parameters):
        k_rrf: int = 60 (Reciprocal Rank Fusion smoothing constant)
        lexical_top_k: int = 20 (candidate pool size for lexical retriever)
        dense_top_k: int = 20 (candidate pool size for dense retriever)
    """

    def __init__(
        self,
        config: RetrievalConfig,
        lexical_retriever: BaseRetriever,
        dense_retriever: BaseRetriever,
    ) -> None:
        super().__init__(config)
        self.lexical_retriever = lexical_retriever
        self.dense_retriever = dense_retriever
        params = config.parameters or {}
        self.k_rrf: int = int(params.get("k_rrf", 60))
        self.lexical_top_k: int = int(params.get("lexical_top_k", 20))
        self.dense_top_k: int = int(params.get("dense_top_k", 20))

    @property
    def is_indexed(self) -> bool:
        return (
            getattr(self.lexical_retriever, "is_indexed", False)
            and getattr(self.dense_retriever, "is_indexed", False)
        )

    def index_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Index chunks into both component retrievers."""
        self.lexical_retriever.index_chunks(chunks)
        self.dense_retriever.index_chunks(chunks)

    def search(
        self,
        query_text: str,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """Execute hybrid search using Reciprocal Rank Fusion (RRF)."""
        if not query_text or not query_text.strip():
            return []

        effective_k = top_k if top_k is not None else self.config.top_k
        if effective_k <= 0:
            return []

        # Run component retrievals
        lexical_results = self.lexical_retriever.search(
            query_text, top_k=self.lexical_top_k
        )
        dense_results = self.dense_retriever.search(
            query_text, top_k=self.dense_top_k
        )

        # Map chunk_id to best result object and compute RRF scores
        chunk_map: dict[str, RetrievalResult] = {}
        rrf_scores: dict[str, float] = {}

        for rank, res in enumerate(lexical_results, start=1):
            cid = res.chunk_id
            chunk_map[cid] = res
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.k_rrf + rank))

        for rank, res in enumerate(dense_results, start=1):
            cid = res.chunk_id
            if cid not in chunk_map:
                chunk_map[cid] = res
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.k_rrf + rank))

        # Deterministic sorting key: (-rrf_score, document_id, chunk_index, chunk_id)
        def sort_key(cid: str) -> tuple[float, str, str]:
            res = chunk_map[cid]
            return (-rrf_scores[cid], res.document_id, res.chunk_id)

        sorted_cids = sorted(rrf_scores.keys(), key=sort_key)
        top_cids = sorted_cids[:effective_k]

        fused_results: list[RetrievalResult] = []
        for rank, cid in enumerate(top_cids, start=1):
            base_res = chunk_map[cid]
            fused_score = round(rrf_scores[cid], 6)
            fused_meta = dict(base_res.metadata)
            fused_meta["rrf_score"] = fused_score
            fused_res = RetrievalResult(
                rank=rank,
                score=fused_score,
                document_id=base_res.document_id,
                chunk_id=base_res.chunk_id,
                text=base_res.text,
                title=base_res.title,
                source_name=base_res.source_name,
                publisher=base_res.publisher,
                license_name=base_res.license_name,
                char_start=base_res.char_start,
                char_end=base_res.char_end,
                content_hash=base_res.content_hash,
                corpus_version=base_res.corpus_version,
                source_url=base_res.source_url,
                license_evidence_url=base_res.license_evidence_url,
                metadata=fused_meta,
            )
            fused_results.append(fused_res)

        return fused_results
