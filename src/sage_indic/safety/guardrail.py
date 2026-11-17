"""Proposed: SAGE-Aware Contextual Safety Guardrail.

Combines orthographic de-obfuscation, language/script detection,
SAGE morphological stem isolation, contextual benign disambiguation,
and dense multilingual semantic classification into a calibrated decision engine.
"""

from __future__ import annotations

import re
from typing import Any

from sage_indic.detection import LanguageDetector
from sage_indic.normalize import normalize_text
from sage_indic.safety.classifier import MultilingualSemanticClassifier
from sage_indic.safety.types import (
    SafetyCategory,
    SafetyLabel,
    SafetyResult,
    SafetySignal,
)
from sage_indic.tokenizer.morphology import segment_word_morphology

# High-risk violence and hate roots (used after morphological stem isolation)
CRITICAL_VIOLENCE_ROOTS: set[str] = {
    # Native Telugu roots
    "చంప",
    "చంపు",
    "నరక",
    "నరుక",
    "కొట్ట",
    "దాడి",
    "ఆత్మహత్య",
    "చావు",
    "హింస",
    # Romanized Telugu roots
    "champ",
    "narik",
    "naruk",
    "kott",
    "viragakott",
    "sachipo",
    "lanja",
    "kodaka",
    "suicide",
    # Code-mixed roots
    "kill",
    "murder",
    "attack",
    "torture",
}

# Contextual benign indicator patterns
BENIGN_CONTEXT_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Medical & toxicology
    (re.compile(r"(విషం\s+విరుగుడు|విష\s+ప్రభావం|వైద్యం|ఇంజెక్షన్|చికిత్స|డాక్టర్|ఆసుపత్రి)"), "medical_treatment_native"),
    (re.compile(r"\b(venom|antidote|medicine|treatment|doctor|hospital|dose|prescription|fever)\b", re.I), "medical_treatment_latin"),
    (re.compile(r"\bmandu\s+(theesukondi|tisukondi|veesukondi)\b", re.I), "medicine_colloquial"),
    # Historical warfare & academic
    (re.compile(r"(ప్రపంచ\s+యుద్ధం|1947|చరిత్ర|రాజ్యాంగం|సామ్రాజ్యం|యుద్ధాలు)"), "history_academic_native"),
    (re.compile(r"\b(world\s+war|history|historical|yuddham|yuddhalu|samrajyam|kurukshetra)\b", re.I), "history_academic_latin"),
    # Law enforcement & news reporting
    (re.compile(r"(పోలీసులు|కేసు\s+నమోదు|దర్యాప్తు|అరెస్ట్|కోర్టు|నిందితు)"), "law_enforcement_native"),
    (re.compile(r"\b(police|arrest|investigation|suspect|crime\s+rate|court|news\s+report)\b", re.I), "law_enforcement_latin"),
    # Computing terminology
    (re.compile(r"\b(kill\s+command|kill\s+switch|process\s+crash|operating\s+system)\b", re.I), "computing_term"),
    # Colloquial hyperbole / figurative idioms
    (re.compile(r"(పని|ఎండ|పరీక్షల?\s+భయం|weather|work\s+pressure).{0,25}(చంపుతోంది|champestondi)", re.I), "figurative_hyperbole"),
]

# Safe negation indicator patterns (verbal suffixes & negative markers indicating harm prevention/prohibition)
SAFE_NEGATION_PATTERNS: list[re.Pattern] = [
    re.compile(r"(కూడదు|వద్దు|వద్దని|రాదు|చేయకండి|చేయవద్దు|చెయ్యొద్దు|లేదు)"),
    re.compile(r"\b(koodadu|kudathu|vaddu|raadu|cheyakandi|cheyoddu|cheyaddu|don'?t|should not|must not|never)\b", re.I),
]


class SageAwareSafetyGuardrail:
    """Proposed representation-aware and context-sensitive safety guardrail."""

    def __init__(
        self,
        classifier: MultilingualSemanticClassifier | None = None,
        enable_morphology: bool = True,
        unsafe_threshold: float = 0.58,
        uncertain_lower: float = 0.40,
    ) -> None:
        self.classifier = classifier or MultilingualSemanticClassifier()
        self.detector = LanguageDetector()
        self.enable_morphology = enable_morphology
        self.unsafe_threshold = unsafe_threshold
        self.uncertain_lower = uncertain_lower
        self.method_name = "SAGE_ContextualGuardrail" if enable_morphology else "SAGE_Ablation_NoMorph"

    def deobfuscate(self, text: str) -> str:
        """Strip adversarial spacing, repeated characters, and punctuation delimiters."""
        s = text

        # 1. Whitespace spreading removal (e.g. 'c h a m p e s t a' or 'వా డి ని')
        # If words consist predominantly of single characters separated by spaces
        tokens = s.split()
        if len(tokens) >= 4 and sum(1 for t in tokens if len(t) == 1) / len(tokens) >= 0.70:
            s = "".join(tokens)

        # 2. Punctuation delimiter injection inside words (e.g. k*i*l*l, a.t.t.a.c.k, a_t_t_a_c_k)
        s = re.sub(r"(?<=[a-zA-Z\u0c00-\u0c7f])[.*_!](?=[a-zA-Z\u0c00-\u0c7f])", "", s)

        # 3. Leetspeak substitutions
        s = re.sub(r"\bk1ll\b", "kill", s, flags=re.I)
        s = re.sub(r"\bk!ll\b", "kill", s, flags=re.I)
        s = re.sub(r"\bmurd3r\b", "murder", s, flags=re.I)
        s = re.sub(r"\bch3st4\b", "chesta", s, flags=re.I)

        # 4. Collapse repeated characters (3 or more -> 1)
        s = re.sub(r"(.)\1{2,}", r"\1", s)

        return s

    def detect_benign_context(self, text: str) -> list[str]:
        """Detect presence of benign-sensitive contextual markers."""
        matches: list[str] = []
        for pat, tag in BENIGN_CONTEXT_PATTERNS:
            if pat.search(text):
                matches.append(tag)
        return matches

    def detect_safe_negation(self, text: str) -> bool:
        """Detect presence of negative verbal suffixes or markers preventing/forbidding harm."""
        return any(pat.search(text) for pat in SAFE_NEGATION_PATTERNS)

    def extract_morphological_stems(self, text: str) -> list[str]:
        """Extract morphological stems using SAGE affix separation."""
        words = text.split()
        stems: list[str] = []
        for w in words:
            clean_w = re.sub(r"[^\w\u0c00-\u0c7f-]", "", w)
            if not clean_w:
                continue
            if self.enable_morphology:
                segments = segment_word_morphology(clean_w, enable_affixes=True)
                for seg in segments:
                    if not seg.startswith("##"):
                        stems.append(seg.lower())
            else:
                stems.append(clean_w.lower())
        return stems

    def predict(self, text: str) -> SafetyResult:
        """Execute full representation-aware and context-sensitive safety classification."""
        if not text or not text.strip():
            return SafetyResult(
                label=SafetyLabel.UNCERTAIN,
                confidence=0.5,
                method=self.method_name,
                metadata={"note": "Empty or whitespace-only input."},
            )

        norm_text = normalize_text(text)
        deobf_text = self.deobfuscate(norm_text)

        # Language and script detection
        input_rep = self.detector.detect(norm_text)
        lang_category = input_rep.category.value

        signals: list[SafetySignal] = []

        # 1. Check Benign Context & Safe Negation Indicators
        benign_matches = self.detect_benign_context(norm_text) + self.detect_benign_context(deobf_text)
        has_benign_context = len(benign_matches) > 0
        has_safe_negation = self.detect_safe_negation(norm_text) or self.detect_safe_negation(deobf_text)

        # 2. Extract SAGE Morphological Stems
        stems = self.extract_morphological_stems(deobf_text)
        matched_violence_stems: list[str] = []
        for st in stems:
            for root in CRITICAL_VIOLENCE_ROOTS:
                if root in st or st.startswith(root):
                    matched_violence_stems.append(st)
                    break

        if matched_violence_stems:
            signals.append(
                SafetySignal(
                    source="sage_morphology" if self.enable_morphology else "surface_keyword",
                    risk_score=0.90,
                    matched_term=", ".join(matched_violence_stems[:3]),
                    category=SafetyCategory.VIOLENCE_INCITEMENT,
                    explanation=(
                        f"Isolated critical violence stem: {matched_violence_stems[:3]}"
                        if self.enable_morphology
                        else f"Matched surface violence keyword: {matched_violence_stems[:3]}"
                    ),
                )
            )

        # 3. Dense Multilingual Semantic Risk Score
        semantic_score = self.classifier.predict_score(deobf_text)
        signals.append(
            SafetySignal(
                source="multilingual_semantic",
                risk_score=semantic_score,
                category=SafetyCategory.VIOLENCE_INCITEMENT if semantic_score > 0.5 else SafetyCategory.SAFE_GENERAL,
                explanation=f"Dense multilingual embedding risk score: {semantic_score:.3f}",
            )
        )

        # 4. Contextual Decision Fusion
        fused_score = semantic_score
        if matched_violence_stems and not has_benign_context and not has_safe_negation:
            fused_score = max(fused_score, 0.85)
        elif not matched_violence_stems and not has_benign_context and not has_safe_negation and semantic_score <= 0.55:
            # If no critical violent stem is present and semantic risk is not high,
            # resolve embedding ambiguity (e.g. UNK collapse in native Telugu) to SAFE.
            fused_score = min(fused_score, 0.35)

        if has_safe_negation:
            # Negation flips violent intent to harmless prohibition (e.g., "చంపకూడదు" -> safe)
            fused_score = fused_score * 0.20
            signals.append(
                SafetySignal(
                    source="safe_negation_override",
                    risk_score=0.05,
                    category=SafetyCategory.SAFE_GENERAL,
                    explanation="Safe negation detected (prohibition/advice against harm); risk attenuated to SAFE.",
                )
            )

        if has_benign_context:
            # Attenuate risk score to prevent false positives on medical/historical/news content
            fused_score = fused_score * 0.35
            signals.append(
                SafetySignal(
                    source="benign_context_dampening",
                    risk_score=0.10,
                    category=SafetyCategory.BENIGN_SENSITIVE,
                    explanation=f"Benign context detected ({benign_matches}); risk attenuated.",
                )
            )

        # 5. Threshold Calibration & Abstention
        metadata: dict[str, Any] = {
            "fused_risk_score": round(fused_score, 4),
            "semantic_score": round(semantic_score, 4),
            "language_category": lang_category,
            "has_benign_context": has_benign_context,
            "benign_matches": benign_matches,
            "matched_violence_stems": matched_violence_stems,
            "morphology_enabled": self.enable_morphology,
        }

        if fused_score >= self.unsafe_threshold:
            label = SafetyLabel.UNSAFE
            confidence = min(0.99, 0.5 + (fused_score - self.unsafe_threshold))
            category = SafetyCategory.VIOLENCE_INCITEMENT
        elif fused_score <= self.uncertain_lower:
            label = SafetyLabel.SAFE
            confidence = min(0.99, 0.5 + (self.uncertain_lower - fused_score))
            category = SafetyCategory.BENIGN_SENSITIVE if has_benign_context else SafetyCategory.SAFE_GENERAL
        else:
            # Low confidence / ambiguous zone -> Abstain with UNCERTAIN
            label = SafetyLabel.UNCERTAIN
            confidence = 0.5
            category = SafetyCategory.AMBIGUOUS

        return SafetyResult(
            label=label,
            confidence=round(confidence, 4),
            method=self.method_name,
            language=lang_category,
            category=category,
            signals=signals,
            metadata=metadata,
        )
