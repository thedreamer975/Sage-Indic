"""Development evaluation fixture and evaluation metrics for SAGE-Indic Language Detector.

NOTE: This is a DEVELOPMENT evaluation fixture for unit/regression testing and detector tuning.
It is NOT a benchmark claim.
"""

from typing import Any

from sage_indic.detection.detector import LanguageDetector, detect
from sage_indic.types import LanguageCategory

# Curated development evaluation examples covering all target forms and edge cases
DEV_EXAMPLES: list[dict[str, Any]] = [
    # 1. Native Telugu (TELUGU_NATIVE)
    {
        "text": "తెలుగు భాష చాలా అందమైనది.",
        "expected": LanguageCategory.TELUGU_NATIVE,
        "note": "Standard declarative Telugu sentence",
    },
    {
        "text": "నేను ఈరోజు హైదరాబాద్ వెళ్తున్నాను.",
        "expected": LanguageCategory.TELUGU_NATIVE,
        "note": "Common everyday conversational Telugu",
    },
    {
        "text": "మీరు ఎప్పుడు వస్తున్నారు?",
        "expected": LanguageCategory.TELUGU_NATIVE,
        "note": "Native Telugu question",
    },
    {
        "text": "ఆంధ్రప్రదేశ్ మరియు తెలంగాణ రాష్ట్రాలలో తెలుగు ప్రధాన భాష.",
        "expected": LanguageCategory.TELUGU_NATIVE,
        "note": "Informational Telugu with formal nouns",
    },
    {
        "text": "నమస్కారం, మీకు ఎలా సహాయం చేయగలను?",
        "expected": LanguageCategory.TELUGU_NATIVE,
        "note": "Formal greeting and query in Telugu script",
    },
    {
        "text": "సాహిత్యం, సంస్కృతి, చరిత్ర మనకు ఎంతో ముఖ్యం.",
        "expected": LanguageCategory.TELUGU_NATIVE,
        "note": "List of cultural concepts in Telugu script",
    },
    # 2. Romanized Telugu (ROMANIZED_TELUGU)
    {
        "text": "nenu ee roju Hyderabad velthunnanu",
        "expected": LanguageCategory.ROMANIZED_TELUGU,
        "note": "Romanized Telugu travel plan",
    },
    {
        "text": "meeru ela unnaru",
        "expected": LanguageCategory.ROMANIZED_TELUGU,
        "note": "Standard Romanized Telugu greeting",
    },
    {
        "text": "naaku ee vishayam gurinchi telusukoovali ani undi",
        "expected": LanguageCategory.ROMANIZED_TELUGU,
        "note": "Romanized Telugu desire/interest sentence",
    },
    {
        "text": "eeroju repu chala baga chepparu",
        "expected": LanguageCategory.ROMANIZED_TELUGU,
        "note": "Conversational praise in Romanized Telugu",
    },
    {
        "text": "atanu ekkada unnaado cheppandi",
        "expected": LanguageCategory.ROMANIZED_TELUGU,
        "note": "Romanized Telugu imperative request",
    },
    {
        "text": "deniki enduku antha aalasyam ayindi",
        "expected": LanguageCategory.ROMANIZED_TELUGU,
        "note": "Romanized Telugu question regarding delay",
    },
    # 3. Telugu-English Code-Mixed (TELUGU_ENGLISH_CODE_MIXED)
    {
        "text": "Nenu today office ki vellali.",
        "expected": LanguageCategory.TELUGU_ENGLISH_CODE_MIXED,
        "note": "Latin code-mix: Telugu pronouns/verbs + English nouns",
    },
    {
        "text": "Hyderabad lo traffic chaala heavy ga undi.",
        "expected": LanguageCategory.TELUGU_ENGLISH_CODE_MIXED,
        "note": "Latin code-mix with Telugu postpositions and adverbs",
    },
    {
        "text": "Ee project gurinchi next meeting lo discuss cheddamu.",
        "expected": LanguageCategory.TELUGU_ENGLISH_CODE_MIXED,
        "note": "Latin code-mix in technical workplace context",
    },
    {
        "text": "నేను today office కి వెళ్ళాలి.",
        "expected": LanguageCategory.TELUGU_ENGLISH_CODE_MIXED,
        "note": "Mixed script: Telugu script + English words",
    },
    {
        "text": "Hyderabad లో traffic చాలా heavy గా ఉంది.",
        "expected": LanguageCategory.TELUGU_ENGLISH_CODE_MIXED,
        "note": "Mixed script with Telugu script base and English loanwords",
    },
    {
        "text": "Ee problem ki solution create cheyandi please.",
        "expected": LanguageCategory.TELUGU_ENGLISH_CODE_MIXED,
        "note": "Latin code-mix with English polite particle",
    },
    # 4. English (ENGLISH)
    {
        "text": "What is the capital of India?",
        "expected": LanguageCategory.ENGLISH,
        "note": "Standard English factual question",
    },
    {
        "text": "Explain photosynthesis in simple terms.",
        "expected": LanguageCategory.ENGLISH,
        "note": "Standard English scientific prompt",
    },
    {
        "text": "How do transformer models handle long context windows?",
        "expected": LanguageCategory.ENGLISH,
        "note": "Technical English question",
    },
    {
        "text": "Please provide a list of historical dynasties in South Asia.",
        "expected": LanguageCategory.ENGLISH,
        "note": "English imperative instruction",
    },
    {
        "text": "The quick brown fox jumps over the lazy dog.",
        "expected": LanguageCategory.ENGLISH,
        "note": "English pangram",
    },
    # 5. Unknown / Edge Cases (UNKNOWN)
    {
        "text": "",
        "expected": LanguageCategory.UNKNOWN,
        "note": "Empty string",
    },
    {
        "text": "   \n\t   ",
        "expected": LanguageCategory.UNKNOWN,
        "note": "Whitespace only",
    },
    {
        "text": "123456 7890",
        "expected": LanguageCategory.UNKNOWN,
        "note": "Digits only",
    },
    {
        "text": "!@#$%^&*()_+",
        "expected": LanguageCategory.UNKNOWN,
        "note": "Punctuation/symbols only",
    },
    {
        "text": "zxqwv trpmk",
        "expected": LanguageCategory.UNKNOWN,
        "note": "Random non-lexical Latin characters",
    },
    {
        "text": "यह हिंदी भाषा का वाक्य है।",
        "expected": LanguageCategory.UNKNOWN,
        "note": "Devanagari script (outside Telugu/English scope)",
    },
]


def evaluate_detector(
    examples: list[dict[str, Any]] | None = None,
    detector: LanguageDetector | None = None,
) -> dict[str, Any]:
    """Run evaluation on the development dataset and compute performance metrics.

    Args:
        examples: List of example dictionaries (default is DEV_EXAMPLES).
        detector: LanguageDetector instance (default uses global detect).

    Returns:
        Dictionary containing overall accuracy, per-class metrics (precision, recall, F1),
        and error analysis.
    """
    data = examples if examples is not None else DEV_EXAMPLES
    det_fn = detector.detect if detector is not None else detect

    categories = [cat.value for cat in LanguageCategory]
    tp: dict[str, int] = {cat: 0 for cat in categories}
    fp: dict[str, int] = {cat: 0 for cat in categories}
    fn: dict[str, int] = {cat: 0 for cat in categories}
    support: dict[str, int] = {cat: 0 for cat in categories}

    total = len(data)
    correct = 0
    errors: list[dict[str, Any]] = []

    for item in data:
        text = item["text"]
        expected: LanguageCategory = item["expected"]
        exp_val = expected.value
        support[exp_val] += 1

        result = det_fn(text)
        pred_val = result.category.value

        if result.category == expected:
            correct += 1
            tp[exp_val] += 1
        else:
            fp[pred_val] += 1
            fn[exp_val] += 1
            errors.append(
                {
                    "text": text,
                    "expected": exp_val,
                    "predicted": pred_val,
                    "confidence": result.confidence,
                    "note": item.get("note", ""),
                }
            )

    accuracy = correct / total if total > 0 else 0.0

    per_class: dict[str, dict[str, float]] = {}
    for cat in categories:
        s = support[cat]
        p = tp[cat] / (tp[cat] + fp[cat]) if (tp[cat] + fp[cat]) > 0 else 0.0
        r = tp[cat] / (tp[cat] + fn[cat]) if (tp[cat] + fn[cat]) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        per_class[cat] = {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f1, 4),
            "support": s,
        }

    return {
        "total_examples": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "per_class": per_class,
        "errors": errors,
    }
