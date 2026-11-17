"""Security and trust-boundary enforcement for Phase 2D.

Core Invariants:
1. Retrieved text is strictly EVIDENCE DATA, never CONTROL.
2. Document text or metadata cannot alter:
   - Retrieval parameters (top-k, similarity metric)
   - Configuration or index selection
   - Tool permissions or system instructions
   - Filesystem paths
3. Separation of control plane (RetrievalConfig) from data plane (EvidencePackage).
4. Explicit documentation: This module enforces deterministic trust-boundary invariants;
   it does NOT claim LLM prompt-injection resistance for future generation stages.
"""

from __future__ import annotations

from typing import Any

from sage_indic.rag.types import (
    EvidencePackage,
    RetrievalConfig,
    RetrievalResult,
)


class SecurityViolationError(PermissionError):
    """Raised when an untrusted payload attempts to breach the control boundary."""


class TrustBoundaryEnforcer:
    """Enforces strict isolation between application control configuration and evidence data."""

    def __init__(self, config: RetrievalConfig) -> None:
        # Configuration is application-owned, immutable
        self._config = config

    @property
    def config(self) -> RetrievalConfig:
        return self._config

    def create_evidence_package(
        self,
        query_id: str,
        query_text: str,
        results: list[RetrievalResult],
        is_safe_query: bool = True,
        extra_metadata: dict[str, Any] | None = None,
    ) -> EvidencePackage:
        """Encapsulate retrieved evidence in a strictly typed, unexecuted data payload.

        Ensures:
        - Results cannot alter top_k or retrieval method in config.
        - System instructions/commands inside text remain inert strings.
        - Provenance is fully preserved.
        """
        # Ensure results do not exceed authorized top_k
        capped_results = results[: self._config.top_k]

        # Fingerprint configuration to detect unauthorized mutation
        config_fingerprint = f"{self._config.method}:{self._config.top_k}:{self._config.similarity_metric}"

        # Clean metadata dictionary
        safe_meta = {
            "enforced_top_k": self._config.top_k,
            "security_layer": "deterministic_trust_boundary",
            "trust_level": "UNTRUSTED_EVIDENCE_DATA",
        }
        if extra_metadata:
            # Prevent metadata keys from overriding control parameters
            for k, v in extra_metadata.items():
                if k not in {"config", "method", "top_k", "index_path", "system_prompt"}:
                    safe_meta[k] = v

        corpus_version = capped_results[0].corpus_version if capped_results else "EMPTY"

        return EvidencePackage(
            query_id=query_id,
            query_text=query_text,
            retrieval_method=self._config.method,
            corpus_version=corpus_version,
            results=capped_results,
            config_fingerprint=config_fingerprint,
            is_safe_query=is_safe_query,
            metadata=safe_meta,
        )

    def assert_no_config_mutation(
        self,
        package: EvidencePackage,
        expected_config: RetrievalConfig,
    ) -> None:
        """Verify that evidence package data did not mutate application retrieval config."""
        expected_fingerprint = (
            f"{expected_config.method}:{expected_config.top_k}:{expected_config.similarity_metric}"
        )
        if package.config_fingerprint != expected_fingerprint:
            raise SecurityViolationError(
                f"Configuration fingerprint mismatch: expected {expected_fingerprint}, got {package.config_fingerprint}"
            )

        if len(package.results) > expected_config.top_k:
            raise SecurityViolationError(
                f"Evidence package contains {len(package.results)} results, exceeding top_k {expected_config.top_k}"
            )
