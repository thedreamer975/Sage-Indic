"""Multilingual Dense Vector Retriever for Phase 2D.

Implements dense semantic search using sentence-transformers models:
- Default model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (Apache 2.0 license).
- Supports offline loading from local cache snapshot.
- Normalizes embeddings and uses cosine similarity.
- Strictly adheres to BaseRetriever interface, tie-breaking rules, provenance contracts,
  and TrustBoundaryEnforcer security boundaries.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

from sage_indic.rag.retriever import BaseRetriever
from sage_indic.rag.types import (
    DocumentChunk,
    RetrievalConfig,
    RetrievalResult,
)

# Standard local cache location for paraphrase-multilingual-MiniLM-L12-v2 snapshot
DEFAULT_LOCAL_SNAPSHOT = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
    / "snapshots"
    / "86741b4e3f5cb7765a600d3a3d55a0f6a6cb443d"
)


class MultilingualDenseRetriever(BaseRetriever):
    """Dense vector retriever using multilingual sentence embeddings.

    Parameters (configured via config):
        model_name: model identifier or local snapshot path.
        top_k: number of chunks to retrieve (default: 5).
        parameters:
            batch_size: int = 32
            min_score: float = -1.0 (cosine similarity ranges [-1.0, 1.0])
    """

    def __init__(self, config: RetrievalConfig) -> None:
        super().__init__(config)
        params = config.parameters or {}
        self.batch_size: int = int(params.get("batch_size", 32))
        self.min_score: float = float(params.get("min_score", -1.0))

        self._chunks: list[DocumentChunk] = []
        self._embeddings: np.ndarray | None = None
        self._model = None
        self._is_indexed: bool = False

    def _ensure_model_loaded(self) -> None:
        if self._model is not None:
            return

        from sentence_transformers import SentenceTransformer

        model_path = self.config.model_name
        # Fall back to local verified snapshot if path does not exist
        if not model_path or not Path(model_path).exists():
            if DEFAULT_LOCAL_SNAPSHOT.exists():
                model_path = str(DEFAULT_LOCAL_SNAPSHOT)
            else:
                model_path = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

        self._model = SentenceTransformer(model_path)

    @property
    def is_indexed(self) -> bool:
        return self._is_indexed

    @property
    def corpus_size(self) -> int:
        return len(self._chunks)

    def index_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Compute and store normalized dense embeddings for document chunks."""
        self._chunks = list(chunks)
        if not self._chunks:
            self._embeddings = None
            self._is_indexed = True
            return

        self._ensure_model_loaded()
        texts = [chunk.text for chunk in self._chunks]
        # Normalize embeddings for cosine similarity via dot product
        raw_embs = self._model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        self._embeddings = np.array(raw_embs, dtype=np.float32)
        self._is_indexed = True

    def search(
        self,
        query_text: str,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """Search indexed chunks using cosine similarity."""
        if not self._is_indexed or not self._chunks or self._embeddings is None:
            return []

        if not query_text or not query_text.strip():
            return []

        effective_k = top_k if top_k is not None else self.config.top_k
        if effective_k <= 0:
            return []

        self._ensure_model_loaded()
        q_emb = self._model.encode(
            [query_text],
            show_progress_bar=False,
            normalize_embeddings=True,
        )[0]

        # Cosine similarities = dot product of normalized vectors
        scores = np.dot(self._embeddings, q_emb)

        # Deterministic sorting key: (-score, document_id, chunk_index, chunk_id)
        scored_items: list[tuple[float, int]] = []
        for idx, score in enumerate(scores):
            f_score = float(score)
            if f_score >= self.min_score:
                scored_items.append((f_score, idx))

        def sort_key(item: tuple[float, int]) -> tuple[float, str, int, str]:
            score, idx = item
            chunk = self._chunks[idx]
            return (-score, chunk.document_id, chunk.chunk_index, chunk.chunk_id)

        scored_items.sort(key=sort_key)
        top_items = scored_items[:effective_k]

        results: list[RetrievalResult] = []
        for rank, (score, idx) in enumerate(top_items, start=1):
            chunk = self._chunks[idx]
            result = RetrievalResult(
                rank=rank,
                score=round(score, 6),
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                title=chunk.title,
                source_name=chunk.source_name,
                publisher=chunk.metadata.get("publisher", chunk.source_name),
                license_name=chunk.metadata.get("license_name", "CC-BY-SA-4.0"),
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                content_hash=chunk.content_hash,
                corpus_version=chunk.metadata.get("corpus_version", "2026.10-phase2d"),
                source_url=chunk.source_url,
                license_evidence_url=chunk.metadata.get("license_evidence_url", None),
                metadata=dict(chunk.metadata),
            )
            results.append(result)

        return results
