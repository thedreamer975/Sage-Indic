"""Typed representation and data models for SAGE-Indic input layer."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LanguageCategory(str, Enum):
    """Categorization of input language and script form."""

    TELUGU_NATIVE = "TELUGU_NATIVE"
    ROMANIZED_TELUGU = "ROMANIZED_TELUGU"
    TELUGU_ENGLISH_CODE_MIXED = "TELUGU_ENGLISH_CODE_MIXED"
    ENGLISH = "ENGLISH"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class InputRepresentation:
    """Minimal typed representation for an input query or text passage."""

    original_text: str
    normalized_text: str
    category: LanguageCategory
    confidence: float
    telugu_char_ratio: float
    latin_char_ratio: float
    english_token_ratio: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_telugu(self) -> bool:
        """Return True if the text contains meaningful Telugu in native or romanized form."""
        return self.category in (
            LanguageCategory.TELUGU_NATIVE,
            LanguageCategory.ROMANIZED_TELUGU,
            LanguageCategory.TELUGU_ENGLISH_CODE_MIXED,
        )

    @property
    def is_code_mixed(self) -> bool:
        """Return True if the text is classified as code-mixed."""
        return self.category == LanguageCategory.TELUGU_ENGLISH_CODE_MIXED
