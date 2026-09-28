"""Conservative text normalization for SAGE-Indic.

Performs:
- Standard Unicode normalization (NFC default).
- Non-destructive whitespace normalization.
- Control character and redundant zero-width artifact cleaning.
- Preserves original semantics, case, and meaningful punctuation.
"""

import re
import unicodedata

# Unicode spaces to convert to ASCII space
_UNICODE_SPACES_PATTERN = re.compile(r"[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]")

# Non-printable control characters excluding \n (0x0A) and \t (0x09)
_CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F\u202A-\u202E]")

# Orphaned zero-width spaces
_ZERO_WIDTH_SPACES_PATTERN = re.compile(r"[\u200B\uFEFF]")

# Pattern to find valid ZWNJ occurrences in Telugu (virama + ZWNJ + Telugu character)
_TELUGU_VALID_ZWNJ_PATTERN = re.compile(r"(?<=\u0C4D)\u200C(?=[\u0C00-\u0C7F])")


def normalize_text(text: str | None, unicode_form: str = "NFC") -> str:
    """Conservatively normalize text for language detection and downstream processing.

    Args:
        text: Input string or None.
        unicode_form: Unicode normalization form ('NFC', 'NFD', 'NFKC', 'NFKD'). Default is 'NFC'.

    Returns:
        Conservatively normalized string. Original semantics and punctuation are preserved.
    """
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    # 1. Unicode normalization (NFC ensures consistent combining character representation)
    normalized = unicodedata.normalize(unicode_form, text)

    # 2. Strip non-printable control characters and bidi overrides
    normalized = _CONTROL_CHARS_PATTERN.sub("", normalized)

    # 3. Strip invisible zero-width spaces
    normalized = _ZERO_WIDTH_SPACES_PATTERN.sub("", normalized)

    # 4. Handle ZWNJ: preserve only valid Telugu conjunct breaks, remove isolated ones
    # Temporarily replace valid ZWNJ with a placeholder
    placeholder = "\ue000"
    normalized = _TELUGU_VALID_ZWNJ_PATTERN.sub(placeholder, normalized)
    # Remove any remaining (orphaned) ZWNJ / ZWJ
    normalized = normalized.replace("\u200c", "").replace("\u200d", "")
    # Restore valid ZWNJ
    normalized = normalized.replace(placeholder, "\u200c")

    # 5. Standardize Unicode whitespace
    normalized = _UNICODE_SPACES_PATTERN.sub(" ", normalized)

    # 6. Normalize multiple consecutive spaces/tabs into a single space, collapsing empty lines
    lines = normalized.splitlines()
    cleaned_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
    result_lines = [line for line in cleaned_lines if line]

    return "\n".join(result_lines)
