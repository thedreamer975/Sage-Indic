"""Baseline A: Deterministic Lexical / Keyword Safety Filter.

This module implements a minimal, transparent keyword blacklist baseline
for Native Telugu, Romanized Telugu, and Code-Mixed text.
Its explicit purpose is to serve as an empirical weak baseline.
"""

from __future__ import annotations

import re

from sage_indic.normalize import normalize_text
from sage_indic.safety.types import (
    SafetyCategory,
    SafetyLabel,
    SafetyResult,
    SafetySignal,
)

# Documented minimal lexicon of safety-critical roots and toxic terms
LEXICAL_BLACKLIST: dict[str, tuple[SafetyCategory, str]] = {
    # Native Telugu roots
    "చంపు": (SafetyCategory.VIOLENCE_INCITEMENT, "kill root"),
    "చంపేయండి": (SafetyCategory.VIOLENCE_INCITEMENT, "kill imperative"),
    "చంపేస్తాను": (SafetyCategory.VIOLENCE_INCITEMENT, "kill future"),
    "నరుకు": (SafetyCategory.VIOLENCE_INCITEMENT, "hack/chop"),
    "నరకండి": (SafetyCategory.VIOLENCE_INCITEMENT, "hack imperative"),
    "దాడి": (SafetyCategory.VIOLENCE_INCITEMENT, "attack"),
    "ఆత్మహత్య": (SafetyCategory.SELF_HARM, "suicide"),
    "చావు": (SafetyCategory.SELF_HARM, "die"),
    "హింసించండి": (SafetyCategory.HATE_SPEECH_HARASSMENT, "torture imperative"),
    # Romanized Telugu roots & slurs
    "champestanu": (SafetyCategory.VIOLENCE_INCITEMENT, "kill romanized"),
    "champesthamu": (SafetyCategory.VIOLENCE_INCITEMENT, "kill romanized"),
    "champali": (SafetyCategory.VIOLENCE_INCITEMENT, "kill modal romanized"),
    "champesta": (SafetyCategory.VIOLENCE_INCITEMENT, "kill romanized"),
    "nariki": (SafetyCategory.VIOLENCE_INCITEMENT, "hack romanized"),
    "viragakotti": (SafetyCategory.VIOLENCE_INCITEMENT, "break bones romanized"),
    "sachipo": (SafetyCategory.SELF_HARM, "die/suicide romanized"),
    "lanja": (SafetyCategory.HATE_SPEECH_HARASSMENT, "slur romanized"),
    "kodaka": (SafetyCategory.HATE_SPEECH_HARASSMENT, "slur romanized"),
    "suicide": (SafetyCategory.SELF_HARM, "suicide english/codemix"),
    "poison": (SafetyCategory.SELF_HARM, "poison english/codemix"),
    # Code-mixed violence keywords
    "kill": (SafetyCategory.VIOLENCE_INCITEMENT, "kill english/codemix"),
    "murder": (SafetyCategory.VIOLENCE_INCITEMENT, "murder english/codemix"),
    "attack": (SafetyCategory.VIOLENCE_INCITEMENT, "attack english/codemix"),
    "torture": (SafetyCategory.VIOLENCE_INCITEMENT, "torture english/codemix"),
}


class LexicalSafetyFilter:
    """Baseline A: Case-normalized keyword filter with exact boundary matching."""

    def __init__(self, lexicon: dict[str, tuple[SafetyCategory, str]] | None = None) -> None:
        self.lexicon = lexicon or LEXICAL_BLACKLIST
        self.name = "Baseline_A_LexicalFilter"

    def predict(self, text: str) -> SafetyResult:
        """Classify input text based on exact keyword presence."""
        if not text or not text.strip():
            return SafetyResult(
                label=SafetyLabel.UNCERTAIN,
                confidence=0.5,
                method=self.name,
                metadata={"note": "Empty or whitespace-only input."},
            )

        norm = normalize_text(text).lower()

        # Find any matching keyword
        matched_signals: list[SafetySignal] = []
        for kw, (cat, desc) in self.lexicon.items():
            # Use regex word boundaries for Latin text, or substring presence for Indic
            is_latin = all(ord(c) < 128 for c in kw)
            pattern = rf"\b{re.escape(kw)}\b" if is_latin else re.escape(kw)

            if re.search(pattern, norm):
                matched_signals.append(
                    SafetySignal(
                        source="lexical_blacklist",
                        risk_score=1.0,
                        matched_term=kw,
                        category=cat,
                        explanation=f"Matched blacklisted term: {kw} ({desc})",
                    )
                )

        if matched_signals:
            top_signal = matched_signals[0]
            return SafetyResult(
                label=SafetyLabel.UNSAFE,
                confidence=0.95,
                method=self.name,
                category=top_signal.category,
                signals=matched_signals,
                metadata={"matched_keywords": [s.matched_term for s in matched_signals]},
            )

        return SafetyResult(
            label=SafetyLabel.SAFE,
            confidence=0.85,
            method=self.name,
            category=SafetyCategory.SAFE_GENERAL,
            signals=[],
            metadata={"matched_keywords": []},
        )
