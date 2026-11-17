"""Conservative evidence normalization for Phase 2D corpus ingestion.

Implementation Version: 1.0.0
Normative Constraints:
1. RAW content is strictly preserved and never mutated in place.
2. Normalized content is stored as an immutable, separate derived representation.
3. Normalization is strictly conservative:
   - Standard Unicode NFC normalization.
   - Preserves all meaningful Telugu characters, aksharas, viramas, and diacritics.
   - Preserves valid ZWNJ occurrences in Telugu (virama + ZWNJ) while removing orphaned artifacts.
   - Non-destructive whitespace standardization.
4. ABSOLUTELY NO:
   - Linguistic rewriting
   - Paraphrasing
   - Summarization
   - Machine translation
   - Factual "correction" or hallucinated expansion
"""

from __future__ import annotations

from sage_indic.normalize import normalize_text

EVIDENCE_NORMALIZER_VERSION = "1.0.0"


class EvidenceNormalizer:
    """Conservative normalizer for Telugu factual evidence documents."""

    def __init__(self, unicode_form: str = "NFC") -> None:
        self.unicode_form = unicode_form
        self.version = EVIDENCE_NORMALIZER_VERSION

    def normalize(self, raw_text: str) -> str:
        """Derive conservative normalized text from raw source text.

        Preserves:
        - Exact Telugu Unicode characters and conjuncts
        - Case in Latin/Code-mixed segments
        - Meaningful punctuation and sentence boundaries
        - Paragraph structure (newlines)

        Args:
            raw_text: Original unaltered source text string.

        Returns:
            Normalized text suitable for deterministic offset-based chunking.
        """
        if not raw_text:
            return ""

        # Delegate to repository conservative normalizer
        return normalize_text(raw_text, unicode_form=self.unicode_form)


def normalize_corpus_text(raw_text: str, unicode_form: str = "NFC") -> str:
    """Convenience functional interface for conservative corpus normalization."""
    return EvidenceNormalizer(unicode_form=unicode_form).normalize(raw_text)
