"""Provider-independent generation adapter and mock implementation for Phase 2E.

Defines:
- GenerationProvider (ABC): Base interface for generation backends.
- MockGenerationProvider: Deterministic, offline mock provider with test hooks for failure modes.
- ExternalAPIProvider: Generic OpenAI/vLLM compatible provider with strict secret handling and retries.
- GenerationAdapter: High-level controller orchestrating prompt composition, provider invocation,
  citation validation, claim decomposition, and invariant enforcement.

INVARIANT:
DraftAnswer.is_verified is ALWAYS False. Generation must never mark its own responses as verified.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sage_indic.generation.prompt import PromptComposer
from sage_indic.generation.types import (
    DraftAnswer,
    GenerationConfig,
    GenerationError,
    GenerationProviderType,
    GenerationRequest,
    MalformedProviderResponseError,
    ProviderAuthError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from sage_indic.types import LanguageCategory
from sage_indic.verification.types import AtomicClaim, EvidencePassage


@dataclass
class RawGenerationOutput:
    """Raw output returned by a low-level generation provider."""

    text: str
    model_id: str
    provider: str
    latency_ms: float
    raw_response: dict[str, Any] = field(default_factory=dict)


class GenerationProvider(ABC):
    """Abstract interface for generation backends (Mock, Local, API)."""

    @abstractmethod
    def generate(self, prompt: str, request: GenerationRequest, config: GenerationConfig) -> RawGenerationOutput:
        """Execute text generation for the given prompt and configuration."""


class MockGenerationProvider(GenerationProvider):
    """Deterministic, zero-dependency mock generation provider for reproducible testing.

    Includes test hooks to simulate timeouts, authentication failures, malformed outputs,
    and invalid citations.
    """

    def __init__(
        self,
        canned_responses: dict[str, str] | None = None,
        simulate_timeout: bool = False,
        simulate_auth_error: bool = False,
        simulate_malformed: bool = False,
        simulate_invalid_citation: bool = False,
        model_id: str = "mock-sage-indic-v1",
    ) -> None:
        self.canned_responses = canned_responses or {}
        self.simulate_timeout = simulate_timeout
        self.simulate_auth_error = simulate_auth_error
        self.simulate_malformed = simulate_malformed
        self.simulate_invalid_citation = simulate_invalid_citation
        self.model_id = model_id

    def generate(self, prompt: str, request: GenerationRequest, config: GenerationConfig) -> RawGenerationOutput:
        t0 = time.perf_counter()

        # 1. Test Failure Mode Simulations
        if self.simulate_timeout:
            raise ProviderTimeoutError(f"Mock provider simulated timeout after {config.timeout_seconds}s.")

        if self.simulate_auth_error:
            raise ProviderAuthError("Mock provider simulated authentication failure.")

        if self.simulate_malformed:
            return RawGenerationOutput(
                text="",  # Empty or invalid response
                model_id=self.model_id,
                provider="mock",
                latency_ms=(time.perf_counter() - t0) * 1000,
            )

        # 2. Check for canned explicit response
        if request.query_id in self.canned_responses:
            text = self.canned_responses[request.query_id]
            latency = (time.perf_counter() - t0) * 1000
            return RawGenerationOutput(text=text, model_id=self.model_id, provider="mock", latency_ms=latency)

        # 3. Handle Empty Evidence Case (Strict Abstention)
        if not request.evidence_passages:
            if request.language_category == LanguageCategory.TELUGU_NATIVE:
                text = "అందించిన ఆధారాలలో ఈ ప్రశ్నకు సమాధానం ఇవ్వడానికి తగిన ఆధారాలు లేవు."
            elif request.language_category == LanguageCategory.ROMANIZED_TELUGU:
                text = "Andinchina aadharalalo ee prasnaku samadhanam ivvadaniki thagina aadharalu levu."
            elif request.language_category == LanguageCategory.TELUGU_ENGLISH_CODE_MIXED:
                text = "Supplied evidence lo ee question ki answer ivvadaniki information ledu."
            else:
                text = "Insufficient evidence provided to answer the query."

            latency = (time.perf_counter() - t0) * 1000
            return RawGenerationOutput(text=text, model_id=self.model_id, provider="mock", latency_ms=latency)

        # 4. Synthesize Grounded Mock Answer from Top Passage
        top_passage = request.evidence_passages[0]
        pid = top_passage.passage_id
        if self.simulate_invalid_citation:
            pid = "INVALID_HALLUCINATED_DOC#c9999"

        # Deterministically extract the first factual sentence from the passage
        first_sentence = top_passage.text.split(".")[0].strip()
        if not first_sentence:
            first_sentence = top_passage.text.strip()

        # Build grounded response with explicit citation
        text = f"{first_sentence} [{pid}]."

        latency = (time.perf_counter() - t0) * 1000
        return RawGenerationOutput(
            text=text,
            model_id=self.model_id,
            provider="mock",
            latency_ms=latency,
            raw_response={"simulated": True, "top_passage_id": top_passage.passage_id},
        )


class ExternalAPIProvider(GenerationProvider):
    """Replaceable external model provider adapter (e.g. vLLM, Ollama, OpenAI-compatible).

    CRITICAL RULES:
    1. Secrets must be read from environment variables; NEVER hardcoded.
    2. Zero external calls in unit test runs.
    3. Handles timeouts, connection errors, and retries gracefully.
    """

    def __init__(self, default_api_base: str = "http://localhost:8000/v1") -> None:
        self.default_api_base = default_api_base

    def generate(self, prompt: str, request: GenerationRequest, config: GenerationConfig) -> RawGenerationOutput:
        api_base = config.api_base_url or self.default_api_base

        headers = {"Content-Type": "application/json"}
        # Check for authentication if env var is specified
        if config.api_key_env_var:
            api_key = os.environ.get(config.api_key_env_var)
            if not api_key:
                raise ProviderAuthError(
                    f"Required API key environment variable '{config.api_key_env_var}' is not set."
                )
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }

        url = f"{api_base.rstrip('/')}/chat/completions"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=config.timeout_seconds) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                latency = (time.perf_counter() - t0) * 1000

                choices = resp_data.get("choices", [])
                if not choices:
                    raise MalformedProviderResponseError("Provider response did not contain 'choices'.")
                text = choices[0].get("message", {}).get("content", "")
                return RawGenerationOutput(
                    text=text,
                    model_id=config.model_name,
                    provider="api",
                    latency_ms=latency,
                    raw_response=resp_data,
                )
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise ProviderAuthError(f"HTTP {e.code} Authentication failure: {e}")
            elif e.code == 408:
                raise ProviderTimeoutError(f"HTTP 408 Request timeout: {e}")
            else:
                raise ProviderUnavailableError(f"HTTP {e.code} error from API provider at '{url}': {e}")
        except TimeoutError as e:
            raise ProviderTimeoutError(f"Request to '{url}' timed out after {config.timeout_seconds}s.")
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError) or "timed out" in str(e.reason).lower():
                raise ProviderTimeoutError(f"Request to '{url}' timed out: {e.reason}")
            raise ProviderUnavailableError(f"External API provider at '{api_base}' is unreachable: {e.reason}")
        except json.JSONDecodeError as e:
            raise MalformedProviderResponseError(f"Failed to decode provider JSON response: {e}")
        except GenerationError:
            raise
        except Exception as e:
            raise ProviderUnavailableError(f"Unexpected provider error: {e}")


class GenerationAdapter:
    """High-level evidence-grounded generation adapter.

    Orchestrates:
    - Prompt composition with untrusted data isolation.
    - Configured provider invocation with retry policy.
    - Citation extraction and validation against supplied evidence.
    - Candidate claim decomposition for downstream verification.
    - Strict enforcement of the is_verified=False invariant.
    """

    def __init__(
        self,
        config: GenerationConfig | None = None,
        provider: GenerationProvider | None = None,
        composer: PromptComposer | None = None,
    ) -> None:
        self.config = config or GenerationConfig()
        self.composer = composer or PromptComposer(prompt_version=self.config.prompt_template_version)

        if provider is not None:
            self.provider = provider
        elif self.config.provider == GenerationProviderType.MOCK:
            self.provider = MockGenerationProvider(model_id=self.config.model_name)
        elif self.config.provider == GenerationProviderType.API:
            self.provider = ExternalAPIProvider()
        else:
            self.provider = MockGenerationProvider(model_id=self.config.model_name)

    def generate(self, request: GenerationRequest) -> DraftAnswer:
        """Generate an evidence-grounded draft answer with extracted candidate claims."""
        request_id = f"GEN_{uuid.uuid4().hex[:8]}"

        # 1. Compose grounded prompt with untrusted data boundary
        prompt = self.composer.compose_prompt(request)

        # 2. Invoke provider with retry policy
        output = self._invoke_with_retry(prompt, request)

        # 3. Validate response
        answer_text = output.text.strip()
        if not answer_text:
            raise MalformedProviderResponseError("Provider returned an empty or blank answer text.")

        # 4. Extract and validate citations
        valid_cits, invalid_cits = self.composer.extract_and_validate_citations(
            answer_text, request.evidence_passages
        )

        # 5. Check for abstention indicators. Keep the model's own abstention
        # separate from the adapter's empty-evidence guard (BUG-AUDIT-02).
        is_abstention, abstention_reason = self._check_abstention(answer_text, request)
        model_abstained = abstention_reason is not None and abstention_reason.startswith(
            "Explicit evidence abstention"
        )
        abstention_source = "not_abstained"
        if model_abstained:
            abstention_source = "model_marker"
        elif is_abstention:
            abstention_source = "no_evidence"

        # 6. Extract candidate claims for independent downstream verification
        candidate_claims = self._extract_candidate_claims(
            request_id=request_id,
            query_id=request.query_id,
            answer_text=answer_text,
            language_category=request.language_category,
        )

        # Map language category to standard ISO / modality strings
        lang_str, modality_str = self._resolve_language_modality(request.language_category)

        # 7. Assemble DraftAnswer (Enforcing is_verified=False)
        return DraftAnswer(
            request_id=request_id,
            query_id=request.query_id,
            answer_text=answer_text,
            language=lang_str,
            modality=modality_str,
            candidate_claims=candidate_claims,
            citations=valid_cits,
            invalid_citations=invalid_cits,
            unsupported_aspects=[],
            is_abstention=is_abstention,
            abstention_reason=abstention_reason,
            model_abstained=model_abstained,
            abstention_source=abstention_source,
            model_id=output.model_id,
            provider=output.provider,
            latency_ms=output.latency_ms,
            is_verified=False,  # CRITICAL INVARIANT: NEVER MARK SELF AS VERIFIED!
            metadata={
                "supplied_evidence_count": len(request.evidence_passages),
                "prompt_version": self.composer.prompt_version,
                "temperature": self.config.temperature,
            },
        )

    def _invoke_with_retry(self, prompt: str, request: GenerationRequest) -> RawGenerationOutput:
        """Execute provider with configurable retry backoff on transient errors."""
        max_attempts = max(1, self.config.max_retries + 1)
        last_error: Exception | None = None

        for attempt in range(max_attempts):
            try:
                return self.provider.generate(prompt, request, self.config)
            except (ProviderTimeoutError, ProviderUnavailableError) as err:
                last_error = err
                if attempt < max_attempts - 1:
                    backoff = self.config.retry_backoff_factor * (attempt + 1)
                    time.sleep(min(backoff, 2.0))
                else:
                    raise err
            except GenerationError:
                # Do not retry auth errors or non-transient errors
                raise

        raise last_error or GenerationError("Generation failed after maximum retries.")

    def _check_abstention(self, answer_text: str, request: GenerationRequest) -> tuple[bool, str | None]:
        """Detect whether the answer is an explicit non-affirmative abstention."""
        abstention_markers = [
            "ఆధారాలు లేవు",
            "సమాచారం లేదు",
            "aadharalu levu",
            "information ledu",
            "insufficient evidence",
            "cannot be answered",
            "not enough information",
            "not mentioned",
        ]
        lower_text = answer_text.lower()
        for marker in abstention_markers:
            if marker in lower_text:
                return True, f"Explicit evidence abstention marker detected: '{marker}'."

        if not request.evidence_passages:
            return True, "No evidence passages supplied."

        return False, None

    def _extract_candidate_claims(
        self,
        request_id: str,
        query_id: str,
        answer_text: str,
        language_category: LanguageCategory,
    ) -> list[AtomicClaim]:
        """Decompose draft answer into candidate atomic claims for verification.

        Note: If claim decomposition is imprecise, claims preserve the original sentence span
        and record language metadata rather than guessing structured representations.
        """
        # Split on sentence boundaries (Telugu full-stop, Romanized '.', '!', '?')
        cleaned_text = re.sub(r"\[[A-Za-z0-9_\-]+#[a-zA-Z0-9_\-]+\]", "", answer_text)  # Remove citation tags for text
        sentences = [s.strip() for s in re.split(r"[.!?।]+", cleaned_text) if s.strip()]

        claims: list[AtomicClaim] = []
        lang_str, modality_str = self._resolve_language_modality(language_category)

        for idx, sentence in enumerate(sentences):
            # Exclude trivial non-factual disclaimers
            if len(sentence) < 5:
                continue

            claim_id = f"{request_id}_C{idx+1:02d}"
            claims.append(
                AtomicClaim(
                    claim_id=claim_id,
                    claim_text=sentence,
                    source_query_id=query_id,
                    language=lang_str,
                    modality=modality_str,
                    context_sentence=sentence,
                    metadata={"extractor": "sentence_boundary_heuristic", "index": idx},
                )
            )

        return claims

    def _resolve_language_modality(self, cat: LanguageCategory) -> tuple[str, str]:
        """Map LanguageCategory to ISO code and human-readable modality string."""
        if cat == LanguageCategory.TELUGU_NATIVE:
            return "te", "native"
        elif cat == LanguageCategory.ROMANIZED_TELUGU:
            return "te-Latn", "romanized"
        elif cat in (LanguageCategory.TELUGU_ENGLISH_CODE_MIXED, LanguageCategory.ENGLISH):
            return "te-en", "code_mixed"
        return "te", "unknown"
