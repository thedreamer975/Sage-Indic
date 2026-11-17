"""SAGE-Indic Safety Layer Package."""

from sage_indic.safety.classifier import MultilingualSemanticClassifier
from sage_indic.safety.evaluation import compute_safety_metrics, evaluate_safety_model
from sage_indic.safety.guardrail import SageAwareSafetyGuardrail
from sage_indic.safety.lexical import LexicalSafetyFilter
from sage_indic.safety.types import (
    SafetyCategory,
    SafetyLabel,
    SafetyResult,
    SafetySignal,
)

__all__ = [
    "LexicalSafetyFilter",
    "MultilingualSemanticClassifier",
    "SageAwareSafetyGuardrail",
    "SafetyCategory",
    "SafetyLabel",
    "SafetyResult",
    "SafetySignal",
    "compute_safety_metrics",
    "evaluate_safety_model",
]
