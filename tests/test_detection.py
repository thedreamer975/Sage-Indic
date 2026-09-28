"""Unit and regression tests for SAGE-Indic language, script, and code-mix detection."""

import pytest

from sage_indic.detection import LanguageDetector, detect
from sage_indic.detection.dev_dataset import evaluate_detector
from sage_indic.types import LanguageCategory


class TestNativeTeluguDetection:
    """Test cases for Native Telugu script inputs."""

    @pytest.mark.parametrize(
        "text",
        [
            "తెలుగు భాష చాలా అందమైనది.",
            "నేను ఈరోజు హైదరాబాద్ వెళ్తున్నాను.",
            "మీరు ఎప్పుడు వస్తున్నారు?",
            "నమస్కారం, మీకు ఎలా సహాయం చేయగలను?",
            "ఆంధ్రప్రదేశ్ మరియు తెలంగాణ రాష్ట్రాలలో తెలుగు ప్రధాన భాష.",
        ],
    )
    def test_native_telugu_sentences(self, text: str) -> None:
        result = detect(text)
        assert result.category == LanguageCategory.TELUGU_NATIVE
        assert result.telugu_char_ratio >= 0.85
        assert result.latin_char_ratio == 0.0
        assert result.confidence >= 0.85
        assert result.is_telugu is True
        assert result.is_code_mixed is False


class TestRomanizedTeluguDetection:
    """Test cases for Romanized Telugu inputs."""

    @pytest.mark.parametrize(
        "text",
        [
            "nenu ee roju Hyderabad velthunnanu",
            "meeru ela unnaru",
            "naaku ee vishayam gurinchi telusukoovali ani undi",
            "eeroju repu chala baga chepparu",
            "atanu ekkada unnaado cheppandi",
            "deniki enduku antha aalasyam ayindi",
        ],
    )
    def test_romanized_telugu_sentences(self, text: str) -> None:
        result = detect(text)
        assert result.category == LanguageCategory.ROMANIZED_TELUGU
        assert result.latin_char_ratio >= 0.80
        assert result.telugu_char_ratio == 0.0
        assert result.confidence >= 0.70
        assert result.is_telugu is True
        assert result.is_code_mixed is False


class TestEnglishDetection:
    """Test cases for English inputs."""

    @pytest.mark.parametrize(
        "text",
        [
            "What is the capital of India?",
            "Explain photosynthesis in simple terms.",
            "How do transformer models handle long context windows?",
            "Please provide a list of historical dynasties in South Asia.",
            "The quick brown fox jumps over the lazy dog.",
        ],
    )
    def test_english_sentences(self, text: str) -> None:
        result = detect(text)
        assert result.category == LanguageCategory.ENGLISH
        assert result.latin_char_ratio >= 0.80
        assert result.telugu_char_ratio == 0.0
        assert result.english_token_ratio >= 0.50
        assert result.confidence >= 0.70
        assert result.is_telugu is False
        assert result.is_code_mixed is False


class TestCodeMixedDetection:
    """Test cases for Telugu-English code-mixed inputs."""

    @pytest.mark.parametrize(
        "text",
        [
            "Nenu today office ki vellali.",
            "Hyderabad lo traffic chaala heavy ga undi.",
            "Ee project gurinchi next meeting lo discuss cheddamu.",
            "Ee problem ki solution create cheyandi please.",
        ],
    )
    def test_latin_code_mixed_sentences(self, text: str) -> None:
        result = detect(text)
        assert result.category == LanguageCategory.TELUGU_ENGLISH_CODE_MIXED
        assert result.is_telugu is True
        assert result.is_code_mixed is True
        assert result.confidence >= 0.65

    @pytest.mark.parametrize(
        "text",
        [
            "నేను today office కి వెళ్ళాలి.",
            "Hyderabad లో traffic చాలా heavy గా ఉంది.",
        ],
    )
    def test_mixed_script_code_mixed_sentences(self, text: str) -> None:
        result = detect(text)
        assert result.category == LanguageCategory.TELUGU_ENGLISH_CODE_MIXED
        assert result.is_telugu is True
        assert result.is_code_mixed is True
        assert result.telugu_char_ratio > 0.10
        assert result.latin_char_ratio > 0.10


class TestEdgeCasesAndUnknown:
    """Test edge cases, empty strings, non-alphabetic inputs, and unknown text."""

    def test_empty_string(self) -> None:
        result = detect("")
        assert result.category == LanguageCategory.UNKNOWN
        assert result.confidence == 1.0
        assert result.is_telugu is False

    def test_none_input(self) -> None:
        result = detect(None)
        assert result.category == LanguageCategory.UNKNOWN
        assert result.is_telugu is False

    def test_whitespace_only(self) -> None:
        result = detect("   \t  \n  ")
        assert result.category == LanguageCategory.UNKNOWN
        assert result.is_telugu is False

    def test_punctuation_only(self) -> None:
        result = detect("!@#$%^&*()_+-=[]{};:'\",.<>/?")
        assert result.category == LanguageCategory.UNKNOWN
        assert result.is_telugu is False

    def test_numbers_only(self) -> None:
        result = detect("1234567890 9876543210")
        assert result.category == LanguageCategory.UNKNOWN
        assert result.is_telugu is False

    def test_unrecognized_latin_gibberish(self) -> None:
        result = detect("zxqwv trpmk bjfd")
        assert result.category == LanguageCategory.UNKNOWN
        assert result.is_telugu is False

    def test_non_telugu_indic_script(self) -> None:
        result = detect("यह हिंदी भाषा का वाक्य है।")
        assert result.category == LanguageCategory.UNKNOWN
        assert result.is_telugu is False

    def test_custom_detector_thresholds(self) -> None:
        detector = LanguageDetector(telugu_script_threshold=0.90)
        result = detector.detect("తెలుగు భాష")
        assert result.category == LanguageCategory.TELUGU_NATIVE


class TestDevelopmentDatasetEvaluation:
    """Evaluate the detector on the full curated development set."""

    def test_dev_evaluation_accuracy_and_f1(self) -> None:
        metrics = evaluate_detector()
        assert metrics["total_examples"] >= 25
        # The deterministic detector should pass all curated development examples
        assert metrics["accuracy"] == 1.0
        assert len(metrics["errors"]) == 0

        # Verify all 5 categories have 1.0 F1 score on the development set
        for _cat, cat_metrics in metrics["per_class"].items():
            assert cat_metrics["support"] > 0
            assert cat_metrics["f1"] == 1.0
