"""Phase 2D: Retrieval-Augmented Evidence (RAG) Corpus Foundation Layer."""

from sage_indic.rag.acquisition import (
    ApprovedSourceRecord,
    CandidateEligibilityGate,
    CandidateSourceRecord,
    ConfigurableWebSourceProvider,
    StaticWebSourceProvider,
    WebSourceProvider,
)
from sage_indic.rag.chunking import (
    FixedBudgetChunker,
    ParagraphChunker,
)
from sage_indic.rag.hash import (
    compute_content_hash,
    verify_content_hash,
)
from sage_indic.rag.ingestion import (
    CorpusIngestionPipeline,
    IngestionResult,
)
from sage_indic.rag.dense import (
    DEFAULT_LOCAL_SNAPSHOT,
    MultilingualDenseRetriever,
)
from sage_indic.rag.hybrid import HybridRetriever
from sage_indic.rag.normalize import (
    EVIDENCE_NORMALIZER_VERSION,
    EvidenceNormalizer,
    normalize_corpus_text,
)
from sage_indic.rag.normalizer import (
    CodeMixedQueryNormalizer,
    NormalizedQuery,
    RomanizedTeluguTransliterator,
)
from sage_indic.rag.retriever import (
    BaseRetriever,
    BM25Retriever,
    DenseRetriever,
    RetrieverProtocol,
    tokenize_for_bm25,
)
from sage_indic.rag.security import (
    SecurityViolationError,
    TrustBoundaryEnforcer,
)
from sage_indic.rag.types import (
    AnnotationStatus,
    ContentHash,
    CorpusManifest,
    DocumentChunk,
    EvaluationQuery,
    EvidencePackage,
    LicenseStatus,
    QueryModality,
    RelevanceGrade,
    RelevanceJudgment,
    RetrievalConfig,
    RetrievalResult,
    SourceDocument,
    SourceType,
)
from sage_indic.rag.validation import (
    ValidationError,
    check_source_eligibility,
    validate_chunk_roundtrip,
    validate_corpus_manifest,
    validate_evaluation_query,
    validate_provenance_chain,
    validate_relevance_judgment,
    validate_source_document,
)

__all__ = [
    "AnnotationStatus",
    "ApprovedSourceRecord",
    "BM25Retriever",
    "BaseRetriever",
    "CandidateEligibilityGate",
    "CandidateSourceRecord",
    "CodeMixedQueryNormalizer",
    "ConfigurableWebSourceProvider",
    "ContentHash",
    "CorpusIngestionPipeline",
    "CorpusManifest",
    "DEFAULT_LOCAL_SNAPSHOT",
    "DenseRetriever",
    "DocumentChunk",
    "EVIDENCE_NORMALIZER_VERSION",
    "EvidenceNormalizer",
    "EvidencePackage",
    "EvaluationQuery",
    "FixedBudgetChunker",
    "HybridRetriever",
    "IngestionResult",
    "LicenseStatus",
    "MultilingualDenseRetriever",
    "NormalizedQuery",
    "ParagraphChunker",
    "QueryModality",
    "RelevanceGrade",
    "RelevanceJudgment",
    "RetrievalConfig",
    "RetrievalResult",
    "RetrieverProtocol",
    "RomanizedTeluguTransliterator",
    "SecurityViolationError",
    "SourceDocument",
    "SourceType",
    "StaticWebSourceProvider",
    "TrustBoundaryEnforcer",
    "ValidationError",
    "WebSourceProvider",
    "check_source_eligibility",
    "compute_content_hash",
    "normalize_corpus_text",
    "tokenize_for_bm25",
    "validate_chunk_roundtrip",
    "validate_corpus_manifest",
    "validate_evaluation_query",
    "validate_provenance_chain",
    "validate_relevance_judgment",
    "validate_source_document",
    "verify_content_hash",
]
