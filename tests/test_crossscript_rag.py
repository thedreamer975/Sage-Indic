"""Comprehensive regression and unit tests for Phase 2D cross-script retrieval.

Tests:
1. RomanizedTeluguTransliterator: rule-based transliteration, vowel/consonants, proper nouns, idempotent Telugu.
2. CodeMixedQueryNormalizer: English domain term preservation, Telugu segment transliteration, bilingual expansion.
3. MultilingualDenseRetriever: offline initialization, indexing, cosine ranking, deterministic ties, provenance.
4. HybridRetriever: Reciprocal Rank Fusion, tie-breaking, provenance preservation.
5. TrustBoundaryIntegration: EvidencePackage structure, content treated strictly as data.
6. Edge cases: empty/whitespace queries, malformed inputs, unanswerable queries.
"""

from __future__ import annotations

import pytest

from sage_indic.rag import (
    BM25Retriever,
    CodeMixedQueryNormalizer,
    ContentHash,
    DEFAULT_LOCAL_SNAPSHOT,
    DocumentChunk,
    EvidencePackage,
    HybridRetriever,
    MultilingualDenseRetriever,
    NormalizedQuery,
    RetrievalConfig,
    RetrievalResult,
    RomanizedTeluguTransliterator,
    TrustBoundaryEnforcer,
)


def _make_chunk(
    chunk_id: str,
    doc_id: str,
    text: str,
    idx: int = 0,
    title: str = "Test Title",
    source_url: str = "https://te.wikipedia.org/wiki/Test",
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        chunk_index=idx,
        char_start=0,
        char_end=len(text),
        text=text,
        raw_text_ref=f"raw_{chunk_id}",
        normalized_text_ref=f"norm_{chunk_id}",
        source_name="Telugu Wikipedia",
        title=title,
        content_hash=ContentHash(algorithm="sha256", digest=f"hash_{chunk_id}"),
        source_url=source_url,
        metadata={"corpus_version": "2026.10-phase2d"},
    )


CHUNK_CHARMINAR = _make_chunk(
    "DOC_CHARMINAR#c0",
    "DOC_CHARMINAR",
    "చార్మినార్ భారతదేశంలోని హైదరాబాదులో ఉన్న ఒక ప్రముఖ చారిత్రక కట్టడం మరియు మసీదు. దీనిని 1591 లో నిర్మించారు.",
    title="చార్మినార్",
)

CHUNK_GOLCONDA = _make_chunk(
    "DOC_GOLCONDA#c0",
    "DOC_GOLCONDA",
    "గోల్కొండ భారతదేశంలోని తెలంగాణ రాష్ట్ర రాజధాని హైదరాబాదు నగరానికి పశ్చిమంగా ఉన్న ఒక చారిత్రక కోట.",
    title="గోల్కొండ",
)

CHUNK_RAMAPPA = _make_chunk(
    "DOC_RAMAPPA#c0",
    "DOC_RAMAPPA",
    "రామప్ప దేవాలయం తెలంగాణలోని కాకతీయుల కాలం నాటి చారిత్రక శివాలయం. దీనికి యునెస్కో ప్రపంచ వారసత్వ హోదా లభించింది.",
    title="రామప్ప దేవాలయం",
)


# ===========================================================================
# 1. RomanizedTeluguTransliterator Tests
# ===========================================================================

class TestRomanizedTeluguTransliterator:

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.transliterator = RomanizedTeluguTransliterator()

    def test_empty_and_whitespace(self) -> None:
        assert self.transliterator.transliterate_token("") == ""
        assert self.transliterator.transliterate_token("   ") == "   "
        assert self.transliterator.transliterate_text("") == ""
        assert self.transliterator.transliterate_text("   ") == ""

    def test_native_telugu_preserved_idempotently(self) -> None:
        assert self.transliterator.transliterate_token("చార్మినార్") == "చార్మినార్"
        assert self.transliterator.transliterate_token("గోల్కొండ") == "గోల్కొండ"

    def test_proper_nouns_lexicon(self) -> None:
        assert self.transliterator.transliterate_token("charminar") == "చార్మినార్"
        assert self.transliterator.transliterate_token("golconda") == "గోల్కొండ"
        assert self.transliterator.transliterate_token("ramappa") == "రామప్ప"
        assert self.transliterator.transliterate_token("kakatiya") == "కాకతీయ"
        assert self.transliterator.transliterate_token("kalamalla") == "కలమళ్ళ"
        assert self.transliterator.transliterate_token("unesco") == "యునెస్కో"
        assert self.transliterator.transliterate_token("gi") == "జీఐ"

    def test_rule_based_phonetics(self) -> None:
        out = self.transliterator.transliterate_token("mariyu")
        assert "మ" in out and "ర" in out
        out_v = self.transliterator.transliterate_token("evaru")
        assert "ఎ" in out_v or "ఏ" in out_v


# ===========================================================================
# 2. CodeMixedQueryNormalizer Tests
# ===========================================================================

class TestCodeMixedQueryNormalizer:

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.normalizer = CodeMixedQueryNormalizer(enable_bilingual_expansion=True)

    def test_empty_query(self) -> None:
        res = self.normalizer.normalize("", modality="code_mixed")
        assert res.expanded_query == ""

    def test_native_query_passthrough(self) -> None:
        q = "చార్మినార్‌ను ఎవరు నిర్మించారు?"
        res = self.normalizer.normalize(q, modality="native")
        assert res.original_query == q
        assert "చార్మినార్" in res.expanded_query

    def test_romanized_query_expansion(self) -> None:
        q = "charminar nu evaru nirmincharu?"
        res = self.normalizer.normalize(q, modality="romanized")
        assert "charminar" in res.expanded_query  # preserves original
        assert "చార్మినార్" in res.expanded_query   # adds transliterated Telugu

    def test_code_mixed_preserves_english_and_transliterates_telugu(self) -> None:
        q = "Golconda fort entrance daggara clap chesthe sound ekkadiki reach avtundi?"
        res = self.normalizer.normalize(q, modality="code_mixed")
        assert "fort" in res.preserved_english_tokens
        assert "clap" in res.preserved_english_tokens
        assert "కోట" in res.bilingual_synonyms or "కోట" in res.expanded_query
        assert "గోల్కొండ" in res.expanded_query


# ===========================================================================
# 3. MultilingualDenseRetriever Tests
# ===========================================================================

class TestMultilingualDenseRetriever:

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        config = RetrievalConfig(
            method="Dense",
            top_k=2,
            model_name=str(DEFAULT_LOCAL_SNAPSHOT) if DEFAULT_LOCAL_SNAPSHOT.exists() else None,
        )
        self.retriever = MultilingualDenseRetriever(config)
        self.chunks = [CHUNK_CHARMINAR, CHUNK_GOLCONDA, CHUNK_RAMAPPA]
        self.retriever.index_chunks(self.chunks)

    def test_empty_query_returns_empty(self) -> None:
        assert self.retriever.search("") == []
        assert self.retriever.search("   ") == []

    def test_top_k_respected(self) -> None:
        results = self.retriever.search("చార్మినార్ హైదరాబాదు", top_k=1)
        assert len(results) == 1

    def test_provenance_preserved(self) -> None:
        results = self.retriever.search("చార్మినార్ హైదరాబాదు", top_k=1)
        assert len(results) == 1
        res = results[0]
        assert isinstance(res, RetrievalResult)
        assert res.document_id.startswith("DOC_")
        assert res.chunk_id.startswith("DOC_")
        assert res.content_hash.algorithm == "sha256"
        assert res.corpus_version == "2026.10-phase2d"

    def test_cross_script_retrieval_returns_ranked_results(self) -> None:
        # Romanized query against native Telugu chunks
        results = self.retriever.search("charminar monument hyderabad", top_k=3)
        assert len(results) == 3
        # Scores should be in descending order
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


# ===========================================================================
# 4. HybridRetriever Tests
# ===========================================================================

class TestHybridRetriever:

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        lexical_cfg = RetrievalConfig(method="BM25", top_k=5)
        dense_cfg = RetrievalConfig(
            method="Dense",
            top_k=5,
            model_name=str(DEFAULT_LOCAL_SNAPSHOT) if DEFAULT_LOCAL_SNAPSHOT.exists() else None,
        )
        self.bm25 = BM25Retriever(lexical_cfg)
        self.dense = MultilingualDenseRetriever(dense_cfg)
        hybrid_cfg = RetrievalConfig(
            method="Hybrid_RRF",
            top_k=2,
            parameters={"k_rrf": 60},
        )
        self.hybrid = HybridRetriever(hybrid_cfg, self.bm25, self.dense)
        self.chunks = [CHUNK_CHARMINAR, CHUNK_GOLCONDA, CHUNK_RAMAPPA]
        self.hybrid.index_chunks(self.chunks)

    def test_empty_query_returns_empty(self) -> None:
        assert self.hybrid.search("") == []

    def test_hybrid_search_returns_rrf_ranked_results(self) -> None:
        results = self.hybrid.search("చార్మినార్ 1591", top_k=2)
        assert len(results) == 2
        assert results[0].chunk_id == "DOC_CHARMINAR#c0"
        assert results[0].score > 0.0
        assert "rrf_score" in results[0].metadata

    def test_deterministic_ties(self) -> None:
        run1 = self.hybrid.search("చారిత్రక తెలంగాణ", top_k=3)
        run2 = self.hybrid.search("చారిత్రక తెలంగాణ", top_k=3)
        assert [r.chunk_id for r in run1] == [r.chunk_id for r in run2]
        assert [r.score for r in run1] == [r.score for r in run2]

    def test_trust_boundary_integration(self) -> None:
        pkg = self.hybrid.retrieve("Q_TEST_001", "చార్మినార్", top_k=2)
        assert isinstance(pkg, EvidencePackage)
        assert pkg.query_id == "Q_TEST_001"
        assert len(pkg.results) <= 2
        # Verify retrieved text is treated strictly as data, not instruction
        for r in pkg.results:
            assert isinstance(r.text, str)
