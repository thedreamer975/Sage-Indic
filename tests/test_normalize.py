"""Unit tests for SAGE-Indic text normalization."""

import unicodedata

from sage_indic.normalize import normalize_text


def test_normalize_empty_and_none() -> None:
    """Test handling of None, empty string, and whitespace-only strings."""
    assert normalize_text(None) == ""
    assert normalize_text("") == ""
    assert normalize_text("   \t  \n  ") == ""


def test_normalize_unicode_nfc() -> None:
    """Test Unicode NFC normalization of decomposed characters."""
    # Decomposed letter 'é' (e + combining acute accent U+0301)
    decomposed = "e\u0301"
    normalized = normalize_text(decomposed)
    assert normalized == "é"
    assert unicodedata.is_normalized("NFC", normalized)


def test_normalize_whitespace_and_newlines() -> None:
    """Test collapsing of redundant spaces and non-breaking spaces."""
    raw = "తెలుగు   భాష\u00a0\u00a0చాలా    అందమైనది.\n\n\nనేను   వస్తున్నాను."
    normalized = normalize_text(raw)
    assert normalized == "తెలుగు భాష చాలా అందమైనది.\nనేను వస్తున్నాను."


def test_normalize_control_characters_removed() -> None:
    """Test removal of non-printable control characters and bidi overrides."""
    raw = "Hello\x00\x08 World\x1f\u202a!\u202c"
    normalized = normalize_text(raw)
    assert normalized == "Hello World!"


def test_normalize_zero_width_spaces_removed() -> None:
    """Test stripping of zero-width spaces."""
    raw = "nenu\u200b ee\ufeff roju"
    normalized = normalize_text(raw)
    assert normalized == "nenu ee roju"


def test_normalize_telugu_valid_zwnj_preserved() -> None:
    """Test that valid Telugu virama + ZWNJ sequences are preserved for conjunct splitting."""
    # Telugu virama (\u0C4D) + ZWNJ (\u200C) + consonant (\u0C15)
    raw = "క్\u200cక"
    normalized = normalize_text(raw)
    assert "\u200c" in normalized
    assert normalized == "క్\u200cక"


def test_normalize_preserves_case_and_punctuation() -> None:
    """Test that English and Romanized case and punctuation are preserved."""
    raw = "Nenu Today Office Ki Vellali! Is it 10:30 AM?"
    normalized = normalize_text(raw)
    assert normalized == "Nenu Today Office Ki Vellali! Is it 10:30 AM?"
