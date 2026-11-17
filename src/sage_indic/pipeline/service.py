"""Phase 2G query pipeline: detection -> safety -> retrieval -> verification -> composition."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sage_indic import __version__
from sage_indic.composition.composer import CompositionInputs, ResponseComposer
from sage_indic.composition.query_analysis import build_retrieval_expansion
from sage_indic.composition.types import (
    AnswerMode,
    AnswerResponse,
    LatencyMetadata,
    SafetyInfo,
)
from sage_indic.config import find_project_root, load_env_file
from sage_indic.detection import LanguageDetector
from sage_indic.generation.adapter import ExternalAPIProvider, GenerationAdapter
from sage_indic.generation.types import (
    GenerationConfig,
    GenerationError,
    GenerationProviderType,
    GenerationRequest,
)
from sage_indic.rag.normalizer import CodeMixedQueryNormalizer
from sage_indic.rag.retriever import BM25Retriever
from sage_indic.rag.types import (
    ContentHash,
    DocumentChunk,
    LicenseStatus,
    RetrievalConfig,
    SourceDocument,
)
from sage_indic.safety.guardrail import SageAwareSafetyGuardrail
from sage_indic.safety.types import SafetyLabel
from sage_indic.tokenizer import SageTokenizer

DEFAULT_CORPUS_VERSION = "2026.10-phase2d"


class _NeutralSemanticFallback:
    """Reduced safety mode when the multilingual semantic model is unavailable.

    The SAGE morphology + benign-context logic still runs; only the dense
    embedding signal is replaced by a constant low risk. The response/status
    explicitly reports that semantic safety is unavailable.
    """

    def predict_score(self, text: str) -> float:  # noqa: ARG002
        return 0.2


@dataclass
class CorpusData:
    """Loaded, immutable evidence corpus and its provenance metadata."""

    version: str
    documents: list[SourceDocument]
    chunks: list[DocumentChunk]


class SageQueryService:
    """Application service that runs the complete SAGE-Indic query pipeline."""

    def __init__(
        self,
        data_dir: Path | None = None,
        default_top_k: int = 8,
    ) -> None:
        load_env_file()
        self.project_root = find_project_root()
        self.data_dir = data_dir or Path(
            os.getenv("SAGE_DATA_DIR", str(self.project_root / "data"))
        )
        self.default_top_k = default_top_k
        self.detector = LanguageDetector()
        self.normalizer = CodeMixedQueryNormalizer(enable_bilingual_expansion=True)
        self.composer = ResponseComposer()

        self.corpus = self._load_corpus()
        self.tokenizer_name = "unicode_whitespace"
        tokenizer_fn = None
        model_path = Path(
            os.getenv(
                "SAGE_TOKENIZER_MODEL",
                str(self.project_root / "experiments" / "saved_models" / "sage_4000.json"),
            )
        )
        if model_path.is_file():
            try:
                sage_tokenizer = SageTokenizer()
                sage_tokenizer.load(model_path)
                tokenizer_fn = sage_tokenizer.encode
                self.tokenizer_name = f"SAGE({model_path.name})"
            except Exception:  # pragma: no cover - defensive fallback
                tokenizer_fn = None

        self.retriever = BM25Retriever(
            RetrievalConfig(
                method="BM25_SAGE_CodeMix",
                top_k=self.default_top_k,
                parameters={
                    "k1": 1.5,
                    "b": 0.75,
                    "normalizer": "CodeMixedQueryNormalizer",
                    "tokenizer": self.tokenizer_name,
                },
            ),
            tokenizer_fn=tokenizer_fn,
            normalizer=self.normalizer,
        )
        self.retriever.index_chunks(self.corpus.chunks)

        self.safety_guardrail, self.safety_mode, self.semantic_safety_available = (
            self._build_safety_guardrail()
        )
        self.provider_config = self._load_provider_config()
        self.provider_available, self.provider_probe_error = self.probe_provider()
        self.generation_adapter = self._build_generation_adapter()

    # ------------------------------------------------------------------
    # Corpus and provider setup
    # ------------------------------------------------------------------

    def _load_corpus(self) -> CorpusData:
        rag_dir = self.data_dir / "processed" / "rag"
        docs_path = rag_dir / "phase2d_documents.jsonl"
        chunks_path = rag_dir / "phase2d_chunks.jsonl"
        if not docs_path.is_file() or not chunks_path.is_file():
            raise FileNotFoundError(
                f"Evidence corpus not found under {rag_dir}. Expected "
                "phase2d_documents.jsonl and phase2d_chunks.jsonl."
            )

        documents: list[SourceDocument] = []
        doc_meta: dict[str, dict[str, Any]] = {}
        for line in docs_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            doc = SourceDocument(
                document_id=raw["document_id"],
                corpus_version=raw["corpus_version"],
                source_name=raw["source_name"],
                source_type=raw["source_type"],
                publisher=raw["publisher"],
                title=raw["title"],
                language=raw["language"],
                script=raw["script"],
                license_name=raw["license_name"],
                license_status=LicenseStatus(raw["license_status"]),
                raw_text_ref=raw["raw_text_ref"],
                raw_content_hash=ContentHash.from_dict(raw["raw_content_hash"]),
                normalized_text_ref=raw["normalized_text_ref"],
                normalized_content_hash=ContentHash.from_dict(raw["normalized_content_hash"]),
                provenance_notes=raw.get("provenance_notes", ""),
                source_url=raw.get("source_url"),
                source_record_id=raw.get("source_record_id"),
                source_revision=raw.get("source_revision"),
                license_url=raw.get("license_url"),
                license_evidence_url=raw.get("license_evidence_url"),
                retrieved_at_utc=raw.get("retrieved_at_utc"),
                published_at=raw.get("published_at"),
                updated_at=raw.get("updated_at"),
                retrieval_eligible=bool(raw.get("retrieval_eligible", False)),
                eligibility_reason=raw.get("eligibility_reason", ""),
                metadata=raw.get("metadata", {}),
            )
            documents.append(doc)
            doc_meta[doc.document_id] = raw

        chunks: list[DocumentChunk] = []
        for line in chunks_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            parent = doc_meta.get(raw["document_id"])
            if parent is None or not parent.get("retrieval_eligible", False):
                continue
            metadata = dict(raw.get("metadata", {}))
            metadata.update(
                {
                    "publisher": parent["publisher"],
                    "license_name": parent["license_name"],
                    "license_evidence_url": parent.get("license_evidence_url"),
                    "corpus_version": parent["corpus_version"],
                    "source_name": parent["source_name"],
                }
            )
            chunks.append(
                DocumentChunk(
                    chunk_id=raw["chunk_id"],
                    document_id=raw["document_id"],
                    chunk_index=raw["chunk_index"],
                    char_start=raw["char_start"],
                    char_end=raw["char_end"],
                    text=raw["text"],
                    raw_text_ref=raw["raw_text_ref"],
                    normalized_text_ref=raw["normalized_text_ref"],
                    source_name=parent["source_name"],
                    title=parent["title"],
                    content_hash=ContentHash.from_dict(raw["content_hash"]),
                    source_url=raw.get("source_url") or parent.get("source_url"),
                    metadata=metadata,
                )
            )

        eligible_docs = [d for d in documents if d.retrieval_eligible]
        version = eligible_docs[0].corpus_version if eligible_docs else DEFAULT_CORPUS_VERSION
        return CorpusData(version=version, documents=eligible_docs, chunks=chunks)

    def _build_safety_guardrail(self) -> tuple[SageAwareSafetyGuardrail, str, bool]:
        try:
            guardrail = SageAwareSafetyGuardrail()
            return guardrail, guardrail.method_name, True
        except Exception:
            guardrail = SageAwareSafetyGuardrail(classifier=_NeutralSemanticFallback())
            return (
                guardrail,
                "SAGE_ContextualGuardrail_LexicalOnlyFallback",
                False,
            )
    def _load_provider_config(self) -> dict[str, Any]:
        enabled_raw = os.getenv("SAGE_LLM_ENABLED", "auto").strip().lower()
        return {
            "enabled_setting": enabled_raw,
            "enabled": enabled_raw not in {"0", "false", "off", "no"},
            "base_url": os.getenv("SAGE_LLM_BASE_URL", "http://127.0.0.1:11434/v1"),
            "model": os.getenv("SAGE_LLM_MODEL", "llama3.2:1b"),
            "timeout_seconds": float(os.getenv("SAGE_LLM_TIMEOUT", "25")),
            "max_tokens": int(os.getenv("SAGE_LLM_MAX_TOKENS", "256")),
            "temperature": float(os.getenv("SAGE_LLM_TEMPERATURE", "0")),
            "api_key_env_var": os.getenv("SAGE_LLM_API_KEY_ENV") or None,
        }

    def _build_generation_adapter(self) -> GenerationAdapter:
        cfg = self.provider_config
        generation_config = GenerationConfig(
            provider=GenerationProviderType.API,
            model_name=cfg["model"],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
            timeout_seconds=cfg["timeout_seconds"],
            max_retries=0,
            api_base_url=cfg["base_url"],
            api_key_env_var=cfg["api_key_env_var"],
        )
        provider = ExternalAPIProvider(default_api_base=cfg["base_url"])
        return GenerationAdapter(config=generation_config, provider=provider)

    def probe_provider(self) -> tuple[bool, str | None]:
        if not self.provider_config["enabled"]:
            return False, "LLM use is disabled by SAGE_LLM_ENABLED."
        url = f"{self.provider_config['base_url'].rstrip('/')}/models"
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                payload = json.loads(response.read().decode("utf-8"))
            elapsed_ms = (time.perf_counter() - t0) * 1000
            models = [m.get("id") for m in payload.get("data", []) if isinstance(m, dict)]
            if models and self.provider_config["model"] not in models:
                return False, (
                    f"Provider reachable ({elapsed_ms:.0f} ms), but model "
                    f"'{self.provider_config['model']}' is not listed. Available: {models}."
                )
            return True, None
        except urllib.error.URLError as exc:
            return False, f"Provider unreachable: {exc.reason}"
        except (TimeoutError, json.JSONDecodeError) as exc:
            return False, f"Provider probe failed: {exc}"

    # ------------------------------------------------------------------
    # Query execution
    # ------------------------------------------------------------------

    def query(
        self,
        query_text: str,
        use_llm: bool | None = None,
        top_k: int | None = None,
    ) -> AnswerResponse:
        """Execute the complete pipeline for one user query."""
        started = time.perf_counter()
        request_id = f"REQ_{uuid.uuid4().hex[:10]}"
        query_text = (query_text or "").strip()
        effective_top_k = max(1, min(int(top_k or self.default_top_k), 10))

        t0 = time.perf_counter()
        input_rep = self.detector.detect(query_text)
        detection_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        safety_result = self.safety_guardrail.predict(input_rep.normalized_text)
        safety_ms = (time.perf_counter() - t0) * 1000
        safety = SafetyInfo(
            label=safety_result.label.value,
            method=self.safety_mode,
            confidence=safety_result.confidence,
            category=safety_result.category.value,
            notes=[
                signal.explanation
                for signal in safety_result.signals
                if signal.explanation
            ][:5],
        )
        if not self.semantic_safety_available:
            safety.notes.append(
                "Dense multilingual semantic safety model unavailable in this environment; "
                "context-aware lexical/morphological safety mode is active."
            )

        t0 = time.perf_counter()
        normalized = self.normalizer.normalize(input_rep.normalized_text)
        retrieval_query = normalized.expanded_query
        canonical_expansion = build_retrieval_expansion(input_rep.normalized_text)
        if canonical_expansion:
            retrieval_query = f"{retrieval_query} {canonical_expansion}"
        package = self.retriever.retrieve(
            query_id=request_id,
            query_text=retrieval_query,
            top_k=effective_top_k,
            is_safe_query=safety_result.label != SafetyLabel.UNSAFE,
        )
        retrieval_ms = (time.perf_counter() - t0) * 1000

        requested_mode = (
            AnswerMode.LLM
            if use_llm is True or (use_llm is None and self.provider_config["enabled"])
            else AnswerMode.DETERMINISTIC
        )
        # Default demo behaviour is deterministic: an unset preference never adds
        # seconds of model latency. Explicit true enables the optional LLM layer.
        if use_llm is None:
            requested_mode = AnswerMode.DETERMINISTIC

        draft = None
        generation_error: str | None = None
        generation_ms = 0.0
        provider_available = self.provider_available

        if requested_mode == AnswerMode.LLM and safety_result.label != SafetyLabel.UNSAFE:
            if not provider_available:
                generation_error = self.provider_probe_error or "LLM provider unavailable."
            else:
                t0 = time.perf_counter()
                try:
                    gen_request = GenerationRequest.from_evidence_package(
                        package,
                        language_category=input_rep.category,
                        max_chunks=effective_top_k,
                    )
                    gen_request.system_instruction = (
                        "You are a helpful Telugu-aware AI assistant. "
                        "When the supplied evidence passages are relevant, ground your answer strictly in them. "
                        "If the supplied evidence passages do not contain information for the user question, "
                        "answer the question directly using your general knowledge, clearly and concisely. "
                        "Do not invent synthetic citation tags. "
                        "Answer in the same language/script (Native Telugu, Romanized Telugu, or English) "
                        "as the user query where feasible. Keep the answer under 150 words."
                    )
                    draft = self.generation_adapter.generate(gen_request)
                except GenerationError as exc:
                    generation_error = f"{type(exc).__name__}: {exc}"
                except Exception as exc:  # pragma: no cover - safety net
                    generation_error = f"Unexpected generation error: {exc}"
                generation_ms = (time.perf_counter() - t0) * 1000

        latency = LatencyMetadata(
            detection_ms=round(detection_ms, 3),
            safety_ms=round(safety_ms, 3),
            retrieval_ms=round(retrieval_ms, 3),
            generation_ms=round(generation_ms, 3),
        )

        t0 = time.perf_counter()
        response = self.composer.compose(
            CompositionInputs(
                request_id=request_id,
                query=query_text,
                input_representation=input_rep,
                package=package,
                expanded_query=normalized.expanded_query,
                safety=safety,
                latency=latency,
                requested_mode=requested_mode,
                draft=draft,
                generation_error=generation_error,
                provider_available=provider_available,
                provider_name="openai-compatible",
                model_name=(
                    self.provider_config["model"]
                    if requested_mode == AnswerMode.LLM
                    else None
                ),
            )
        )
        composition_ms = (time.perf_counter() - t0) * 1000
        latency.composition_ms = round(composition_ms, 3)
        latency.total_ms = round((time.perf_counter() - started) * 1000, 3)
        return response

    # ------------------------------------------------------------------
    # Status / corpus metadata
    # ------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        provider_available, probe_error = self.probe_provider()
        self.provider_available = provider_available
        self.provider_probe_error = probe_error
        return {
            "service": "SAGE-Indic",
            "version": __version__,
            "corpus": {
                "loaded": bool(self.corpus.chunks),
                "version": self.corpus.version,
                "documents": len(self.corpus.documents),
                "chunks": len(self.corpus.chunks),
                "retrieval_eligible_only": True,
            },
            "retriever": {
                "indexed": self.retriever.is_indexed,
                "method": "BM25 + code-mix normalizer + " + self.tokenizer_name,
                "top_k": self.default_top_k,
                "tokenizer": self.tokenizer_name,
            },
            "llm": {
                "configured": self.provider_config["enabled"],
                "available": provider_available,
                "provider": "openai-compatible (Ollama-compatible)",
                "base_url": self.provider_config["base_url"],
                "model": self.provider_config["model"],
                "error": probe_error,
                "max_tokens": self.provider_config["max_tokens"],
                "temperature": self.provider_config["temperature"],
                "timeout_seconds": self.provider_config["timeout_seconds"],
            },
            "safety": {
                "method": self.safety_mode,
                "semantic_classifier_available": self.semantic_safety_available,
            },
            "deterministic_fallback": True,
            "default_generation_mode": "deterministic",
        }

    def corpus_documents(self) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for chunk in self.corpus.chunks:
            counts[chunk.document_id] = counts.get(chunk.document_id, 0) + 1
        return [
            {
                "document_id": doc.document_id,
                "title": doc.title,
                "source_name": doc.source_name,
                "publisher": doc.publisher,
                "license_name": doc.license_name,
                "license_status": doc.license_status.value,
                "source_url": doc.source_url,
                "source_revision": doc.source_revision,
                "chunk_count": counts.get(doc.document_id, 0),
                "language": doc.language,
                "script": doc.script,
            }
            for doc in self.corpus.documents
        ]


def create_service() -> SageQueryService:
    """Factory used by the API layer and smoke-test scripts."""
    return SageQueryService()
