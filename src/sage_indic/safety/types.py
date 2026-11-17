"""Data types and schemas for the SAGE-Indic Safety Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SafetyLabel(str, Enum):
    """Explicit 3-class safety decision schema supporting abstention."""

    SAFE = "SAFE"
    UNSAFE = "UNSAFE"
    UNCERTAIN = "UNCERTAIN"


class SafetyCategory(str, Enum):
    """Categorical risk taxonomy for safety signals."""

    VIOLENCE_INCITEMENT = "VIOLENCE_INCITEMENT"
    HATE_SPEECH_HARASSMENT = "HATE_SPEECH_HARASSMENT"
    SELF_HARM = "SELF_HARM"
    BENIGN_SENSITIVE = "BENIGN_SENSITIVE"
    AMBIGUOUS = "AMBIGUOUS"
    SAFE_GENERAL = "SAFE_GENERAL"


@dataclass(frozen=True)
class SafetySignal:
    """Individual safety signal extracted during evaluation."""

    source: str
    risk_score: float
    matched_term: str | None = None
    category: SafetyCategory = SafetyCategory.SAFE_GENERAL
    explanation: str = ""


@dataclass
class SafetyResult:
    """Comprehensive safety evaluation result."""

    label: SafetyLabel
    confidence: float
    method: str
    language: str | None = None
    category: SafetyCategory = SafetyCategory.SAFE_GENERAL
    signals: list[SafetySignal] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
