"""SAGE-Indic: Linguistically-Aware, Safe and Evidence-Grounded Indic LLM Framework."""

from sage_indic.config import Settings, get_settings
from sage_indic.detection import LanguageDetector, detect
from sage_indic.logging import get_logger, setup_logging
from sage_indic.normalize import normalize_text
from sage_indic.types import InputRepresentation, LanguageCategory

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "InputRepresentation",
    "LanguageCategory",
    "LanguageDetector",
    "Settings",
    "detect",
    "get_logger",
    "get_settings",
    "normalize_text",
    "setup_logging",
]
