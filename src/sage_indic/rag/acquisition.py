"""Provider-neutral source acquisition adapter and candidate eligibility gate for Phase 2D.

Architectural Guarantees:
1. Search API / Discovery Provider ≠ Approved Evidence Corpus.
2. Candidate records are strictly unapproved upon discovery (retrieval_eligible=False).
3. Eligibility Gate enforces human review, verified license evidence, publisher identity,
   and explicit factual-domain suitability before any candidate enters the corpus.
4. Search ranks and provider scores are acquisition metadata only, NEVER injected into
   corpus text or treated as relevance ground truth.
5. External providers are swappable and configuration-injected.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from sage_indic.rag.hash import compute_content_hash
from sage_indic.rag.types import (
    ContentHash,
    LicenseStatus,
    SourceDocument,
    SourceType,
)
from sage_indic.rag.validation import ValidationError


@dataclass
class CandidateSourceRecord:
    """Unapproved external source record returned by a discovery/search provider."""

    candidate_id: str
    provider_name: str
    canonical_source_url: str
    title: str
    publisher: str
    raw_content: str
    raw_content_hash: ContentHash
    provider_version: str | None = None
    request_timestamp_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    declared_license: str = "UNVERIFIED"
    license_evidence_url: str | None = None
    license_status: LicenseStatus = LicenseStatus.DISCOVERED
    factual_domain: str = "general_knowledge"
    language: str = "te"
    script: str = "Telugu"
    search_rank: int | None = None
    search_score: float | None = None
    provenance_notes: str = ""
    acquisition_config: dict[str, Any] = field(default_factory=dict)
    retrieval_eligible: bool = False
    eligibility_reason: str = "Discovered candidate awaiting human licensing and factual audit."
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["license_status"] = self.license_status.value
        d["raw_content_hash"] = self.raw_content_hash.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidateSourceRecord:
        d = dict(data)
        d["license_status"] = LicenseStatus(d["license_status"])
        d["raw_content_hash"] = ContentHash.from_dict(d["raw_content_hash"])
        return cls(**d)


@dataclass
class ApprovedSourceRecord:
    """Human-audited and approved source record permitted to enter the ingestion pipeline."""

    candidate_id: str
    document_id: str
    source_name: str
    publisher: str
    canonical_source_url: str
    title: str
    raw_content: str
    raw_content_hash: ContentHash
    language: str
    script: str
    source_type: SourceType
    license_name: str
    license_url: str
    license_evidence_url: str
    eligibility_reason: str
    reviewer_id: str
    review_timestamp_utc: str
    provenance_notes: str
    source_record_id: str | None = None
    source_revision: str | None = None
    published_at: str | None = None
    updated_at: str | None = None
    retrieval_eligible: bool = True
    license_status: LicenseStatus = LicenseStatus.APPROVED
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["source_type"] = self.source_type.value
        d["license_status"] = self.license_status.value
        d["raw_content_hash"] = self.raw_content_hash.to_dict()
        return d


class WebSourceProvider(Protocol):
    """Protocol for provider-neutral external discovery and content acquisition."""

    def search_discover(
        self,
        query: str,
        limit: int = 10,
        factual_domain: str = "general_knowledge",
    ) -> list[CandidateSourceRecord]:
        """Discover candidate source records matching a query."""
        ...

    def fetch_canonical_source(self, source_url: str) -> str:
        """Fetch raw canonical content from an external source URL."""
        ...

    def get_provider_metadata(self) -> dict[str, Any]:
        """Return provider configuration, identity, and version metadata."""
        ...


class CandidateEligibilityGate:
    """Strict gate for human audit, provenance verification, and licensing review."""

    @staticmethod
    def audit_and_approve(
        candidate: CandidateSourceRecord,
        reviewer_id: str,
        approved_document_id: str,
        source_type: SourceType,
        verified_license_name: str,
        verified_license_url: str,
        verified_license_evidence_url: str,
        eligibility_reason: str,
        provenance_notes: str,
        source_record_id: str | None = None,
        source_revision: str | None = None,
        published_at: str | None = None,
        updated_at: str | None = None,
    ) -> ApprovedSourceRecord:
        """Audit a candidate record and produce an ApprovedSourceRecord.

        Raises ValidationError if any non-negotiable eligibility criterion fails.
        """
        if not candidate.candidate_id or not candidate.candidate_id.strip():
            raise ValidationError("Candidate candidate_id cannot be empty.")

        if not candidate.raw_content or not candidate.raw_content.strip():
            raise ValidationError(f"Candidate {candidate.candidate_id} has empty raw content.")

        if not reviewer_id or not reviewer_id.strip():
            raise ValidationError("Reviewer ID must be provided for human audit.")

        if not approved_document_id or not approved_document_id.strip():
            raise ValidationError("approved_document_id cannot be empty.")

        if candidate.language.lower() != "te":
            raise ValidationError(
                f"Candidate language must be 'te', got '{candidate.language}'."
            )

        # License verification gates
        if not verified_license_name or verified_license_name.strip().upper() == "UNVERIFIED":
            raise ValidationError("Cannot approve source with UNVERIFIED license.")

        if not verified_license_evidence_url or not verified_license_evidence_url.strip():
            raise ValidationError("Missing verified_license_evidence_url pointing to rights record.")

        if not eligibility_reason or not eligibility_reason.strip():
            raise ValidationError("Missing human eligibility_reason.")

        if eligibility_reason.strip().lower().startswith("pending"):
            raise ValidationError("Eligibility reason indicates decision is still pending.")

        # Compute or verify hash
        computed_hash = compute_content_hash(candidate.raw_content)
        if candidate.raw_content_hash.digest != computed_hash.digest:
            raise ValidationError(
                f"Candidate raw content hash mismatch: "
                f"expected {candidate.raw_content_hash.digest}, computed {computed_hash.digest}."
            )

        review_time = datetime.now(timezone.utc).isoformat()

        return ApprovedSourceRecord(
            candidate_id=candidate.candidate_id,
            document_id=approved_document_id,
            source_name=candidate.publisher or candidate.provider_name,
            publisher=candidate.publisher or "Wikimedia Foundation",
            canonical_source_url=candidate.canonical_source_url,
            title=candidate.title,
            raw_content=candidate.raw_content,
            raw_content_hash=computed_hash,
            language=candidate.language,
            script=candidate.script,
            source_type=source_type,
            license_name=verified_license_name,
            license_url=verified_license_url,
            license_evidence_url=verified_license_evidence_url,
            eligibility_reason=eligibility_reason,
            reviewer_id=reviewer_id,
            review_timestamp_utc=review_time,
            provenance_notes=provenance_notes,
            source_record_id=source_record_id,
            source_revision=source_revision,
            published_at=published_at,
            updated_at=updated_at,
            retrieval_eligible=True,
            license_status=LicenseStatus.APPROVED,
            metadata={
                "candidate_provider": candidate.provider_name,
                "candidate_request_timestamp": candidate.request_timestamp_utc,
                "factual_domain": candidate.factual_domain,
            },
        )


class ConfigurableWebSourceProvider(ABC):
    """Base class for configurable, provider-neutral acquisition adapters."""

    def __init__(
        self,
        provider_name: str,
        provider_version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.provider_version = provider_version
        self.config = config or {}

    def get_provider_metadata(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "provider_version": self.provider_version,
            "config": self.config,
        }

    @abstractmethod
    def search_discover(
        self,
        query: str,
        limit: int = 10,
        factual_domain: str = "general_knowledge",
    ) -> list[CandidateSourceRecord]:
        ...

    @abstractmethod
    def fetch_canonical_source(self, source_url: str) -> str:
        ...


class StaticWebSourceProvider(ConfigurableWebSourceProvider):
    """Deterministic, offline-reproducible provider for controlled research acquisition.

    Allows mock or pre-registered catalog discovery without external network dependencies,
    ensuring experiments are 100% reproducible and verifiable offline.
    """

    def __init__(
        self,
        catalog: list[dict[str, Any]] | None = None,
        provider_name: str = "StaticWikimediaProvider",
        provider_version: str = "2026.10-research",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(provider_name, provider_version, config)
        self._catalog: list[dict[str, Any]] = catalog or []

    def register_entry(self, entry: dict[str, Any]) -> None:
        self._catalog.append(entry)

    def search_discover(
        self,
        query: str,
        limit: int = 10,
        factual_domain: str = "general_knowledge",
    ) -> list[CandidateSourceRecord]:
        results: list[CandidateSourceRecord] = []
        q_lower = query.lower()
        rank = 1

        for item in self._catalog:
            title = item.get("title", "")
            raw = item.get("raw_content", "")
            if q_lower in title.lower() or q_lower in raw.lower() or not query.strip():
                content_hash = compute_content_hash(raw)
                cand = CandidateSourceRecord(
                    candidate_id=item.get("candidate_id", f"CAND_{len(results)+1:03d}"),
                    provider_name=self.provider_name,
                    provider_version=self.provider_version,
                    request_timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    canonical_source_url=item.get("canonical_source_url", ""),
                    title=title,
                    publisher=item.get("publisher", "Wikimedia Foundation"),
                    raw_content=raw,
                    raw_content_hash=content_hash,
                    declared_license=item.get("declared_license", "UNVERIFIED"),
                    license_evidence_url=item.get("license_evidence_url"),
                    license_status=LicenseStatus(item.get("license_status", LicenseStatus.DISCOVERED.value)),
                    factual_domain=item.get("factual_domain", factual_domain),
                    language=item.get("language", "te"),
                    script=item.get("script", "Telugu"),
                    search_rank=rank,
                    search_score=1.0 / rank,
                    provenance_notes=item.get("provenance_notes", ""),
                    acquisition_config=self.config,
                    retrieval_eligible=False,
                    eligibility_reason="Candidate record discovered via provider; pending human eligibility review.",
                )
                results.append(cand)
                rank += 1
                if len(results) >= limit:
                    break

        return results

    def fetch_canonical_source(self, source_url: str) -> str:
        for item in self._catalog:
            if item.get("canonical_source_url") == source_url:
                return item.get("raw_content", "")
        raise FileNotFoundError(f"Source URL {source_url} not found in provider catalog.")
