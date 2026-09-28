"""Interactive demonstration and development evaluation runner for SAGE-Indic Language Detector."""

import sys

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from sage_indic import detect
from sage_indic.detection.dev_dataset import evaluate_detector


def run_demo() -> None:
    print("=" * 70)
    print("SAGE-Indic: Language & Script Detection Demonstration")
    print("=" * 70)

    sample_queries = [
        "తెలుగు భాష చాలా అందమైనది.",
        "నేను ఈరోజు హైదరాబాద్ వెళ్తున్నాను.",
        "nenu ee roju Hyderabad velthunnanu",
        "meeru ela unnaru",
        "What is the capital of India?",
        "Explain photosynthesis in simple terms.",
        "Nenu today office ki vellali.",
        "Hyderabad lo traffic chaala heavy ga undi.",
        "నేను today office కి వెళ్ళాలి.",
        "Hyderabad లో traffic చాలా heavy గా ఉంది.",
        "!@#$% 12345",
        "zxqwv trpmk",
    ]

    for q in sample_queries:
        res = detect(q)
        print(f"\nInput:       {q}")
        print(f"Normalized:  {res.normalized_text}")
        print(f"Category:    {res.category.value}")
        print(f"Confidence:  {res.confidence:.3f}")
        print(
            f"Telugu Ratio:{res.telugu_char_ratio:.3f} | "
            f"Latin Ratio: {res.latin_char_ratio:.3f} | "
            f"En Token Ratio: {res.english_token_ratio:.3f}"
        )

    print("\n" + "=" * 70)
    print("Development Dataset Evaluation Results")
    print("=" * 70)

    metrics = evaluate_detector()
    print(f"Total Examples: {metrics['total_examples']}")
    print(f"Correct:        {metrics['correct']}")
    print(f"Overall Acc:    {metrics['accuracy'] * 100:.2f}%\n")
    print("Per-Class Metrics:")
    print(f"{'Category':<30} | {'Prec':<6} | {'Recall':<6} | {'F1':<6} | {'Support':<6}")
    print("-" * 65)
    for cat, m in metrics["per_class"].items():
        prec = m["precision"]
        rec = m["recall"]
        f1_score = m["f1"]
        supp = m["support"]
        print(f"{cat:<30} | {prec:<6.2f} | {rec:<6.2f} | {f1_score:<6.2f} | {supp:<6}")


if __name__ == "__main__":
    run_demo()
