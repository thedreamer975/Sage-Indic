"""Retrieval models and interfaces for Phase 2D.

Implements:
- RetrieverProtocol: typing protocol for evidence retrieval returning an EvidencePackage.
- BaseRetriever: abstract base class for evidence retrievers.
- BM25Retriever: deterministic sparse lexical BM25 ranking model with Robertson-Spärck Jones IDF.
- DenseRetriever: interface placeholder for future dense vector retriever (blocked).
"""

from __future__ import annotations

import math
import unicodedata
from abc import ABC, abstractmethod
from collections import Counter
from typing import Protocol

from sage_indic.rag.types import (
    DocumentChunk,
    EvidencePackage,
    RetrievalConfig,
    RetrievalResult,
)


def tokenize_for_bm25(text: str) -> list[str]:
    """Deterministic, dependency-free Unicode tokenizer for BM25.

    1. Normalizes text using Unicode NFC form and converts Latin characters to lowercase.
    2. Strips punctuation, symbols, and control codes (Unicode categories P*, S*, C*, Z*)
       while strictly preserving letters (L*) including Telugu consonants/vowels,
       combining marks (M*) including Telugu matras, viramas, and anusvara, and numbers (N*).
    3. Splits on whitespace boundaries.
    """
    if not text:
        return []
    norm = unicodedata.normalize("NFC", text.lower())
    cleaned: list[str] = []
    for ch in norm:
        cat = unicodedata.category(ch)
        if cat.startswith(("P", "S", "C", "Z")):
            cleaned.append(" ")
        else:
            cleaned.append(ch)
    return [t for t in "".join(cleaned).split() if t]


class RetrieverProtocol(Protocol):
    """Protocol for evidence retrievers."""

    def retrieve(
        self,
        query_id: str,
        query_text: str,
        top_k: int | None = None,
    ) -> EvidencePackage:
        ...


class BaseRetriever(ABC):
    """Abstract base class for Phase 2D retrievers."""

    def __init__(self, config: RetrievalConfig) -> None:
        self.config = config

    @abstractmethod
    def index_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Build or update the retrieval index from approved document chunks."""
        ...

    @abstractmethod
    def search(
        self,
        query_text: str,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """Execute retrieval search and return ranked results with parent provenance."""
        ...

    def retrieve(
        self,
        query_id: str,
        query_text: str,
        top_k: int | None = None,
        is_safe_query: bool = True,
    ) -> EvidencePackage:
        """Execute retrieval and encapsulate in trust-boundary EvidencePackage."""
        from sage_indic.rag.security import TrustBoundaryEnforcer

        results = self.search(query_text=query_text, top_k=top_k)
        enforcer = TrustBoundaryEnforcer(self.config)
        return enforcer.create_evidence_package(
            query_id=query_id,
            query_text=query_text,
            results=results,
            is_safe_query=is_safe_query,
        )


class BM25Retriever(BaseRetriever):
    """Deterministic sparse lexical BM25 retriever for Phase 2D.

    Implements standard Okapi BM25 with Robertson-Spärck Jones IDF:
        IDF(q) = ln(1 + (N - n(q) + 0.5) / (n(q) + 0.5))
        Score(D, Q) = sum_{q in Q} IDF(q) * (f(q, D) * (k1 + 1)) / (f(q, D) + k1 * (1 - b + b * (|D| / avgdl)))

    Parameters (configured via config.parameters):
        k1: float = 1.5 (term frequency saturation)
        b: float = 0.75 (document length normalization)
        min_score: float = 0.0 (minimum score threshold)
        return_zero_scores: bool = False (whether to return 0-score chunks if matches < top_k)
    """

    def __init__(
        self,
        config: RetrievalConfig,
        tokenizer_fn: Any = None,
        normalizer: Any = None,
    ) -> None:
        super().__init__(config)
        params = config.parameters or {}
        self.k1: float = float(params.get("k1", 1.5))
        self.b: float = float(params.get("b", 0.75))
        self.min_score: float = float(params.get("min_score", 0.0))
        self.return_zero_scores: bool = bool(params.get("return_zero_scores", False))
        self.tokenizer_fn = tokenizer_fn or tokenize_for_bm25
        self.normalizer = normalizer

        self._chunks: list[DocumentChunk] = []
        self._doc_lens: list[int] = []
        self._doc_tfs: list[dict[str, int]] = []
        self._df: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._avgdl: float = 0.0
        self._is_indexed: bool = False

    @property
    def is_indexed(self) -> bool:
        """Return True if index_chunks has been executed."""
        return self._is_indexed

    @property
    def corpus_size(self) -> int:
        """Return the count of indexed document chunks."""
        return len(self._chunks)

    def index_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Build or update the BM25 inverted index from document chunks.

        Preserves source chunks without in-place mutation.
        """
        self._chunks = list(chunks)
        n_docs = len(self._chunks)

        if n_docs == 0:
            self._doc_lens = []
            self._doc_tfs = []
            self._df = {}
            self._idf = {}
            self._avgdl = 0.0
            self._is_indexed = True
            return

        self._doc_lens = []
        self._doc_tfs = []
        df_counter: Counter[str] = Counter()

        for chunk in self._chunks:
            tokens = self.tokenizer_fn(chunk.text)
            self._doc_lens.append(len(tokens))
            tf = Counter(tokens)
            self._doc_tfs.append(dict(tf))
            for term in tf:
                df_counter[term] += 1

        self._df = dict(df_counter)
        self._avgdl = sum(self._doc_lens) / n_docs if n_docs > 0 else 0.0

        # Precompute Robertson-Spärck Jones IDF
        self._idf = {}
        for term, doc_freq in self._df.items():
            self._idf[term] = math.log(1.0 + (n_docs - doc_freq + 0.5) / (doc_freq + 0.5))

        self._is_indexed = True

    def search(
        self,
        query_text: str,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """Execute BM25 retrieval search and return ranked results with parent provenance.

        Tie-breaking rule:
            (-score, document_id, chunk_index, chunk_id)
        """
        if not self._is_indexed or not self._chunks:
            return []

        if not query_text or not query_text.strip():
            return []

        effective_query = query_text
        if self.normalizer is not None:
            norm_res = self.normalizer.normalize(query_text)
            effective_query = (
                norm_res.expanded_query
                if hasattr(norm_res, "expanded_query")
                else str(norm_res)
            )

        query_tokens = self.tokenizer_fn(effective_query)
        if not query_tokens:
            return []

        q_tf = Counter(query_tokens)
        effective_k = top_k if top_k is not None else self.config.top_k
        if effective_k <= 0:
            return []

        n_docs = len(self._chunks)
        scores: list[tuple[float, int]] = []

        for idx in range(n_docs):
            doc_len = self._doc_lens[idx]
            doc_tf = self._doc_tfs[idx]
            score = 0.0

            if self._avgdl > 0:
                len_norm = 1.0 - self.b + self.b * (doc_len / self._avgdl)
            else:
                len_norm = 1.0

            for q_term in q_tf:
                if q_term in doc_tf:
                    tf = doc_tf[q_term]
                    idf = self._idf.get(q_term, 0.0)
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * len_norm
                    score += idf * (numerator / denominator)

            if score > self.min_score or self.return_zero_scores:
                scores.append((score, idx))

        # Sort with deterministic tie-breaking:
        # (-score, chunk.document_id, chunk.chunk_index, chunk.chunk_id)
        def sort_key(item: tuple[float, int]) -> tuple[float, str, int, str]:
            score, idx = item
            chunk = self._chunks[idx]
            return (-score, chunk.document_id, chunk.chunk_index, chunk.chunk_id)

        scores.sort(key=sort_key)
        top_items = scores[:effective_k]

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


class DenseRetriever(BaseRetriever):
    """Dense vector retriever for Phase 2D.

    When config.model_name is not configured, raises NotImplementedError to enforce
    blocking of unconfigured dense execution.
    When a verified model_name or snapshot path is provided, delegates to MultilingualDenseRetriever.
    """

    def __init__(self, config: RetrievalConfig) -> None:
        super().__init__(config)
        self._delegate = None
        if config.model_name:
            from sage_indic.rag.dense import MultilingualDenseRetriever

            self._delegate = MultilingualDenseRetriever(config)

    @property
    def is_indexed(self) -> bool:
        if self._delegate is not None:
            return self._delegate.is_indexed
        return False

    @property
    def corpus_size(self) -> int:
        if self._delegate is not None:
            return self._delegate.corpus_size
        return 0

    def index_chunks(self, chunks: list[DocumentChunk]) -> None:
        if self._delegate is None:
            raise NotImplementedError(
                "Dense vector indexing is blocked: No approved factual evidence corpus exists."
            )
        self._delegate.index_chunks(chunks)

    def search(
        self,
        query_text: str,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        if self._delegate is None:
            raise NotImplementedError(
                "Dense vector search is blocked: No approved evidence corpus exists."
            )
        return self._delegate.search(query_text, top_k=top_k)
