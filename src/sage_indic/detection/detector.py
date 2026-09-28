"""Deterministic Language, Script, and Code-Mix Detector for SAGE-Indic."""

from typing import Any

from sage_indic.detection.heuristics import (
    WORD_TOKEN_PATTERN,
    check_token_type,
    extract_script_counts,
)
from sage_indic.normalize import normalize_text
from sage_indic.types import InputRepresentation, LanguageCategory


class LanguageDetector:
    """Lightweight, deterministic language and code-mix detector for Telugu and English.

    Uses Unicode character properties and lexical-morphological heuristics.
    Requires no external dependencies, neural models, or third-party APIs.
    """

    def __init__(
        self,
        telugu_script_threshold: float = 0.85,
        script_mix_threshold: float = 0.12,
    ) -> None:
        self.telugu_script_threshold = telugu_script_threshold
        self.script_mix_threshold = script_mix_threshold

    def detect(self, text: str | None) -> InputRepresentation:
        """Detect the language category and extract representation metrics for input text.

        Args:
            text: Raw input string.

        Returns:
            InputRepresentation containing normalized text, detected category,
            confidence score, character ratios, and detection metadata.
        """
        raw_text = text if text is not None else ""
        normalized = normalize_text(raw_text)

        # 1. Edge Case: Empty, whitespace-only, or non-alphabetic inputs
        telugu_chars, latin_chars, other_alpha, total_chars = extract_script_counts(normalized)
        alpha_chars = telugu_chars + latin_chars + other_alpha

        if alpha_chars == 0:
            return InputRepresentation(
                original_text=raw_text,
                normalized_text=normalized,
                category=LanguageCategory.UNKNOWN,
                confidence=1.0 if total_chars == 0 else 0.5,
                telugu_char_ratio=0.0,
                latin_char_ratio=0.0,
                english_token_ratio=0.0,
                metadata={
                    "reason": "non_alphabetic_or_empty",
                    "total_chars": total_chars,
                    "alpha_chars": 0,
                },
            )

        telugu_char_ratio = telugu_chars / alpha_chars
        latin_char_ratio = latin_chars / alpha_chars
        other_char_ratio = other_alpha / alpha_chars

        # 2. Case A: Dominantly Native Telugu Script
        if telugu_char_ratio >= self.telugu_script_threshold:
            confidence = min(1.0, 0.80 + 0.20 * telugu_char_ratio)
            return InputRepresentation(
                original_text=raw_text,
                normalized_text=normalized,
                category=LanguageCategory.TELUGU_NATIVE,
                confidence=round(confidence, 3),
                telugu_char_ratio=round(telugu_char_ratio, 3),
                latin_char_ratio=round(latin_char_ratio, 3),
                english_token_ratio=0.0,
                metadata={
                    "detection_method": "script_unicode_telugu",
                    "telugu_chars": telugu_chars,
                    "latin_chars": latin_chars,
                },
            )

        # 3. Case B: Mixed-Script (Telugu script + Latin script co-occurring)
        if (
            telugu_char_ratio >= self.script_mix_threshold
            and latin_char_ratio >= self.script_mix_threshold
        ):
            # Compute token-level English ratio for the Latin portions
            tokens = [t for t in WORD_TOKEN_PATTERN.findall(normalized) if not t.isdigit()]
            en_tokens = sum(1 for t in tokens if check_token_type(t)[0] in ("ENGLISH", "HYBRID"))
            en_ratio = en_tokens / len(tokens) if tokens else 0.0

            return InputRepresentation(
                original_text=raw_text,
                normalized_text=normalized,
                category=LanguageCategory.TELUGU_ENGLISH_CODE_MIXED,
                confidence=0.95,
                telugu_char_ratio=round(telugu_char_ratio, 3),
                latin_char_ratio=round(latin_char_ratio, 3),
                english_token_ratio=round(en_ratio, 3),
                metadata={
                    "detection_method": "mixed_script_cooccurrence",
                    "telugu_char_ratio": round(telugu_char_ratio, 3),
                    "latin_char_ratio": round(latin_char_ratio, 3),
                },
            )

        # 4. Case C: Dominantly Latin Script (English, Romanized Telugu, or Latin Code-Mixed)
        if latin_char_ratio >= 0.80:
            tokens = [t for t in WORD_TOKEN_PATTERN.findall(normalized) if not t.isdigit()]
            if not tokens:
                return InputRepresentation(
                    original_text=raw_text,
                    normalized_text=normalized,
                    category=LanguageCategory.UNKNOWN,
                    confidence=0.5,
                    telugu_char_ratio=round(telugu_char_ratio, 3),
                    latin_char_ratio=round(latin_char_ratio, 3),
                    english_token_ratio=0.0,
                    metadata={"reason": "no_valid_word_tokens"},
                )

            te_count = 0
            en_count = 0
            hybrid_count = 0
            unk_count = 0
            token_details: list[dict[str, Any]] = []

            for tok in tokens:
                ttype, root = check_token_type(tok)
                if ttype == "TELUGU":
                    te_count += 1
                elif ttype == "ENGLISH":
                    en_count += 1
                elif ttype == "HYBRID":
                    hybrid_count += 1
                else:
                    unk_count += 1
                token_details.append({"token": tok, "type": ttype, "root": root})

            total_tokens = len(tokens)
            effective_en = en_count + (0.5 * hybrid_count)
            effective_te = te_count + (0.5 * hybrid_count)
            en_token_ratio = effective_en / total_tokens

            # Rule C1: Latin Code-Mixed
            # Triggered if explicit hybrid tokens exist (e.g. 'officeki', 'heavyga'), OR
            # both Telugu markers and English words are present in a multi-token utterance
            is_codemixed = (
                hybrid_count >= 1
                or (te_count >= 1 and en_count >= 1)
                or (te_count >= 1 and unk_count >= 1 and total_tokens >= 3 and en_count >= 1)
            )

            if (
                is_codemixed
                and (te_count > 0 or hybrid_count > 0)
                and (en_count > 0 or hybrid_count > 0)
            ):
                confidence = min(0.95, 0.65 + 0.08 * (te_count + en_count + hybrid_count))
                return InputRepresentation(
                    original_text=raw_text,
                    normalized_text=normalized,
                    category=LanguageCategory.TELUGU_ENGLISH_CODE_MIXED,
                    confidence=round(confidence, 3),
                    telugu_char_ratio=round(telugu_char_ratio, 3),
                    latin_char_ratio=round(latin_char_ratio, 3),
                    english_token_ratio=round(en_token_ratio, 3),
                    metadata={
                        "detection_method": "latin_code_mix_lexical",
                        "telugu_tokens": te_count,
                        "english_tokens": en_count,
                        "hybrid_tokens": hybrid_count,
                        "token_details": token_details,
                    },
                )

            # Rule C2: Romanized Telugu
            if effective_te > 0 and effective_te >= effective_en:
                confidence = min(0.95, 0.70 + 0.08 * te_count)
                return InputRepresentation(
                    original_text=raw_text,
                    normalized_text=normalized,
                    category=LanguageCategory.ROMANIZED_TELUGU,
                    confidence=round(confidence, 3),
                    telugu_char_ratio=round(telugu_char_ratio, 3),
                    latin_char_ratio=round(latin_char_ratio, 3),
                    english_token_ratio=round(en_token_ratio, 3),
                    metadata={
                        "detection_method": "romanized_telugu_lexical",
                        "telugu_tokens": te_count,
                        "english_tokens": en_count,
                        "token_details": token_details,
                    },
                )

            # Rule C3: English
            if effective_en > 0 and effective_te == 0:
                confidence = min(0.98, 0.75 + 0.05 * en_count)
                return InputRepresentation(
                    original_text=raw_text,
                    normalized_text=normalized,
                    category=LanguageCategory.ENGLISH,
                    confidence=round(confidence, 3),
                    telugu_char_ratio=round(telugu_char_ratio, 3),
                    latin_char_ratio=round(latin_char_ratio, 3),
                    english_token_ratio=round(en_token_ratio, 3),
                    metadata={
                        "detection_method": "english_lexical",
                        "english_tokens": en_count,
                        "token_details": token_details,
                    },
                )

            # Rule C4: Unrecognized Latin tokens (e.g. random consonants, unknown language)
            return InputRepresentation(
                original_text=raw_text,
                normalized_text=normalized,
                category=LanguageCategory.UNKNOWN,
                confidence=0.40,
                telugu_char_ratio=round(telugu_char_ratio, 3),
                latin_char_ratio=round(latin_char_ratio, 3),
                english_token_ratio=0.0,
                metadata={
                    "detection_method": "unrecognized_latin",
                    "unknown_tokens": unk_count,
                },
            )

        # 5. Case D: Other non-Telugu/non-Latin dominant script or unclassified
        return InputRepresentation(
            original_text=raw_text,
            normalized_text=normalized,
            category=LanguageCategory.UNKNOWN,
            confidence=0.60 if other_char_ratio > 0.5 else 0.30,
            telugu_char_ratio=round(telugu_char_ratio, 3),
            latin_char_ratio=round(latin_char_ratio, 3),
            english_token_ratio=0.0,
            metadata={
                "detection_method": "unsupported_script_or_unclassified",
                "other_char_ratio": round(other_char_ratio, 3),
            },
        )


# Global default detector instance
_DEFAULT_DETECTOR = LanguageDetector()


def detect(text: str | None) -> InputRepresentation:
    """Public convenience function to detect language form and representation metrics.

    Args:
        text: Raw input string.

    Returns:
        InputRepresentation dataclass.
    """
    return _DEFAULT_DETECTOR.detect(text)
