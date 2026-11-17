"""Reproducible evaluation runner for Phase 2D/2F claim-verification benchmarks.

Evaluates and compares:
- Baseline: LinguisticClaimVerifier (frozen weak baseline)
- Experimental: RelationAwareClaimVerifier (atomic proposition decomposition & relation matching)

Across:
- data/processed/verification/dev_verification.jsonl
- data/processed/verification/eval_verification.jsonl

Computes:
1. 4x4 Confusion Matrix (SUPPORTED, CONTRADICTED, INSUFFICIENT_EVIDENCE, CONFLICTING_EVIDENCE).
2. Per-class Precision, Recall, and F1.
3. Macro-F1 and Overall Accuracy.
4. Recall on Genuinely Supported Claims (ensuring conservative abstention is not false improvement).
5. False SUPPORTED Analysis (critical safety error metric).
6. Relational Mismatch & Partial Evidence subset metrics.
7. Modality Breakdown (Native, Romanized, Code-Mixed).
8. Score distributions and runtime latency.
9. Versioned JSON artifact generation in experiments/results/.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any

from sage_indic.rag.types import ContentHash
from sage_indic.verification import (
    AtomicClaim,
    EvidencePassage,
    LinguisticClaimVerifier,
    RelationAwareClaimVerifier,
    VerificationOutcome,
    VerificationResult,
)

# Reconfigure stdout for UTF-8 on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUTCOMES = [
    VerificationOutcome.SUPPORTED.value,
    VerificationOutcome.CONTRADICTED.value,
    VerificationOutcome.INSUFFICIENT_EVIDENCE.value,
    VerificationOutcome.CONFLICTING_EVIDENCE.value,
]


def load_benchmark(file_path: Path) -> list[dict[str, Any]]:
    items = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


def run_evaluation(
    dataset_path: Path,
    output_dir: Path,
    verifier_name: str = "relation_aware",
    verifier_version: str = "2.0.0",
) -> tuple[dict[str, Any], Path]:
    """Execute claim verification evaluation over a dataset with specified verifier."""
    items = load_benchmark(dataset_path)

    if verifier_name == "relation_aware":
        verifier = RelationAwareClaimVerifier(verifier_version=verifier_version)
    elif verifier_name == "linguistic":
        verifier = LinguisticClaimVerifier(verifier_version=verifier_version)
    else:
        raise ValueError(f"Unknown verifier: {verifier_name}")

    confusion_matrix: dict[str, dict[str, int]] = {
        gold: {pred: 0 for pred in OUTCOMES} for gold in OUTCOMES
    }

    per_class_tp: dict[str, int] = {c: 0 for c in OUTCOMES}
    per_class_fp: dict[str, int] = {c: 0 for c in OUTCOMES}
    per_class_fn: dict[str, int] = {c: 0 for c in OUTCOMES}
    per_class_support: dict[str, int] = {c: 0 for c in OUTCOMES}

    modality_stats: dict[str, dict[str, int]] = {
        "native": {"total": 0, "correct": 0},
        "romanized": {"total": 0, "correct": 0},
        "code_mixed": {"total": 0, "correct": 0},
    }

    diagnostic_subset_stats: dict[str, dict[str, int]] = {
        "relational_mismatch": {"total": 0, "correct": 0},
        "partial_evidence": {"total": 0, "correct": 0},
        "direct_support": {"total": 0, "correct": 0},
        "numerical_contradiction": {"total": 0, "correct": 0},
        "polarity_contradiction": {"total": 0, "correct": 0},
        "conflicting_passages": {"total": 0, "correct": 0},
        "unrelated_evidence": {"total": 0, "correct": 0},
        "distractor_high_overlap": {"total": 0, "correct": 0},
        "adversarial_injection": {"total": 0, "correct": 0},
    }

    scores_by_outcome: dict[str, list[float]] = {c: [] for c in OUTCOMES}

    false_supported_items: list[dict[str, Any]] = []
    evaluation_records: list[dict[str, Any]] = []

    t0 = time.perf_counter()

    for item in items:
        claim_dict = item["claim"]
        passages_list = item["passages"]
        gold_outcome = item["gold_outcome"]
        modality = claim_dict.get("modality", "native")
        diag_type = item.get("diagnostic_type", "unknown")

        claim = AtomicClaim(
            claim_id=claim_dict["claim_id"],
            claim_text=claim_dict["claim_text"],
            language=claim_dict.get("language", "te"),
            modality=modality,
        )

        passages = [
            EvidencePassage(
                passage_id=p["passage_id"],
                document_id=p["document_id"],
                text=p["text"],
                content_hash=ContentHash.from_dict(p["content_hash"]),
                source_url=p.get("source_url"),
                title=p.get("title", ""),
            )
            for p in passages_list
        ]

        result: VerificationResult = verifier.verify(claim, passages)
        pred_outcome = result.outcome.value

        confusion_matrix[gold_outcome][pred_outcome] += 1
        per_class_support[gold_outcome] += 1
        scores_by_outcome[pred_outcome].append(result.confidence)

        is_correct = (gold_outcome == pred_outcome)
        if modality in modality_stats:
            modality_stats[modality]["total"] += 1
            if is_correct:
                modality_stats[modality]["correct"] += 1

        if diag_type in diagnostic_subset_stats:
            diagnostic_subset_stats[diag_type]["total"] += 1
            if is_correct:
                diagnostic_subset_stats[diag_type]["correct"] += 1

        if is_correct:
            per_class_tp[gold_outcome] += 1
        else:
            per_class_fn[gold_outcome] += 1
            per_class_fp[pred_outcome] += 1

        # Check for False SUPPORTED trap
        if gold_outcome != VerificationOutcome.SUPPORTED.value and pred_outcome == VerificationOutcome.SUPPORTED.value:
            false_supported_items.append({
                "example_id": item["example_id"],
                "diagnostic_type": diag_type,
                "claim": claim.claim_text,
                "gold_outcome": gold_outcome,
                "pred_outcome": pred_outcome,
                "confidence": result.confidence,
                "explanation": result.explanation,
                "annotation_notes": item.get("annotation_notes"),
            })

        evaluation_records.append({
            "example_id": item["example_id"],
            "diagnostic_type": diag_type,
            "claim_id": claim.claim_id,
            "claim_text": claim.claim_text,
            "modality": modality,
            "gold_outcome": gold_outcome,
            "pred_outcome": pred_outcome,
            "confidence": result.confidence,
            "is_correct": is_correct,
            "explanation": result.explanation,
            "adversarial_injection_present": item.get("adversarial_injection_present", False),
            "adversarial_injection_detected": result.metadata.get("adversarial_injection_detected", False),
        })

    elapsed_ms = (time.perf_counter() - t0) * 1000
    mean_latency_ms = elapsed_ms / len(items) if items else 0.0

    # Metrics computation
    total_examples = len(items)
    correct_count = sum(per_class_tp.values())
    accuracy = correct_count / total_examples if total_examples > 0 else 0.0

    class_metrics = {}
    f1_list = []
    for c in OUTCOMES:
        tp = per_class_tp[c]
        fp = per_class_fp[c]
        fn = per_class_fn[c]
        support = per_class_support[c]

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        if support > 0:
            f1_list.append(f1)

        class_metrics[c] = {
            "support": support,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
        }

    macro_f1 = sum(f1_list) / len(f1_list) if f1_list else 0.0

    # Modality accuracies
    modality_acc = {}
    for mod, counts in modality_stats.items():
        modality_acc[mod] = {
            "total": counts["total"],
            "correct": counts["correct"],
            "accuracy": round(counts["correct"] / counts["total"], 4) if counts["total"] > 0 else 0.0,
        }

    # Diagnostic subset accuracies
    subset_acc = {}
    for diag, counts in diagnostic_subset_stats.items():
        if counts["total"] > 0:
            subset_acc[diag] = {
                "total": counts["total"],
                "correct": counts["correct"],
                "accuracy": round(counts["correct"] / counts["total"], 4),
            }

    # Score summary
    score_summaries = {}
    for c, scs in scores_by_outcome.items():
        if scs:
            score_summaries[c] = {
                "count": len(scs),
                "mean": round(sum(scs) / len(scs), 4),
                "min": round(min(scs), 4),
                "max": round(max(scs), 4),
            }
        else:
            score_summaries[c] = {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0}

    non_supported_gold = total_examples - per_class_support[VerificationOutcome.SUPPORTED.value]
    false_supported_rate = len(false_supported_items) / non_supported_gold if non_supported_gold > 0 else 0.0
    genuine_supported_recall = class_metrics[VerificationOutcome.SUPPORTED.value]["recall"]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    split_name = dataset_path.stem

    result_summary = {
        "experiment_id": f"exp_2d_verification_{verifier_name}_{split_name}_{timestamp}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(dataset_path),
        "split": split_name,
        "verifier_name": verifier_name,
        "verifier_version": verifier_version,
        "total_examples": total_examples,
        "overall_accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "genuine_supported_recall": round(genuine_supported_recall, 4),
        "mean_latency_ms": round(mean_latency_ms, 2),
        "class_metrics": class_metrics,
        "confusion_matrix": confusion_matrix,
        "modality_performance": modality_acc,
        "diagnostic_subset_performance": subset_acc,
        "false_supported_metrics": {
            "count": len(false_supported_items),
            "total_non_supported_ground_truth": non_supported_gold,
            "false_supported_rate": round(false_supported_rate, 4),
            "items": false_supported_items,
        },
        "score_distribution_heuristic": score_summaries,
        "records": evaluation_records,
    }

    # Save artifact
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{result_summary['experiment_id']}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result_summary, f, indent=2, ensure_ascii=False)

    return result_summary, out_file


def print_report(summary: dict[str, Any], out_path: Path) -> None:
    print("\n" + "=" * 80)
    print(f"SAGE-Indic Claim Verification: {summary['verifier_name'].upper()} on {summary['split'].upper()}")
    print("=" * 80)
    print(f"Dataset: {summary['dataset_path']}")
    print(f"Total Examples:            {summary['total_examples']}")
    print(f"Overall Accuracy:          {summary['overall_accuracy'] * 100:.2f}%")
    print(f"Macro-F1 Score:            {summary['macro_f1']:.4f}")
    print(f"Genuinely Supported Recall:{summary['genuine_supported_recall'] * 100:.2f}%")
    print(f"False SUPPORTED Rate:      {summary['false_supported_metrics']['count']} / {summary['false_supported_metrics']['total_non_supported_ground_truth']} ({summary['false_supported_metrics']['false_supported_rate']*100:.1f}%)")
    print(f"Mean Latency per Claim:    {summary['mean_latency_ms']:.2f} ms")

    print("\n--- Per-Class Metrics ---")
    print(f"{'Class':<25} {'Support':<8} {'Precision':<11} {'Recall':<11} {'F1':<11}")
    print("-" * 66)
    for c, m in summary["class_metrics"].items():
        print(f"{c:<25} {m['support']:<8} {m['precision']:<11.4f} {m['recall']:<11.4f} {m['f1_score']:<11.4f}")

    print("\n--- 4x4 Confusion Matrix (Rows: Gold, Cols: Predicted) ---")
    header = f"{'Gold / Pred':<24} " + " ".join(f"{c[:8]:>8}" for c in OUTCOMES)
    print(header)
    print("-" * len(header))
    for gold in OUTCOMES:
        row = f"{gold:<24} " + " ".join(f"{summary['confusion_matrix'][gold][pred]:>8}" for pred in OUTCOMES)
        print(row)

    print("\n--- Diagnostic Subsets Accuracy ---")
    for diag, stats in summary["diagnostic_subset_performance"].items():
        print(f"{diag:<28}: {stats['correct']}/{stats['total']} ({stats['accuracy']*100:.1f}%)")

    print("\n--- Modality Breakdown ---")
    for mod, stats in summary["modality_performance"].items():
        print(f"{mod:<15}: {stats['correct']}/{stats['total']} ({stats['accuracy']*100:.1f}%)")

    if summary["false_supported_metrics"]["count"] > 0:
        print("\n--- False SUPPORTED Error Traces ---")
        for item in summary["false_supported_metrics"]["items"]:
            print(f"- [{item['example_id']} | {item['diagnostic_type']}] Gold: {item['gold_outcome']}")
            print(f"  Claim: {item['claim']}")
            print(f"  Confidence: {item['confidence']} | Reason: {item['explanation']}")

    print("\nArtifact saved to:", out_path)
    print("=" * 80 + "\n")


def print_comparison_table(
    base_summary: dict[str, Any],
    exp_summary: dict[str, Any],
    split_name: str,
) -> None:
    """Print paired comparative table between baseline and experimental verifiers."""
    print("\n" + "=" * 80)
    print(f"PAIRED COMPARISON: Baseline (Linguistic) vs Experimental (Relation-Aware) [{split_name.upper()}]")
    print("=" * 80)
    print(f"{'Metric':<35} {'Baseline':<14} {'RelationAware':<16} {'Delta':<12}")
    print("-" * 77)

    acc_base = base_summary["overall_accuracy"] * 100
    acc_exp = exp_summary["overall_accuracy"] * 100
    d_acc = acc_exp - acc_base
    print(f"{'Overall Accuracy (%)':<35} {acc_base:>12.2f}% {acc_exp:>14.2f}% {d_acc:>+10.2f}%")

    f1_base = base_summary["macro_f1"]
    f1_exp = exp_summary["macro_f1"]
    d_f1 = f1_exp - f1_base
    print(f"{'Macro-F1 Score':<35} {f1_base:>13.4f} {f1_exp:>15.4f} {d_f1:>+11.4f}")

    rec_base = base_summary["genuine_supported_recall"] * 100
    rec_exp = exp_summary["genuine_supported_recall"] * 100
    d_rec = rec_exp - rec_base
    print(f"{'Genuinely Supported Recall (%)':<35} {rec_base:>12.2f}% {rec_exp:>14.2f}% {d_rec:>+10.2f}%")

    fs_base = base_summary["false_supported_metrics"]["false_supported_rate"] * 100
    fs_exp = exp_summary["false_supported_metrics"]["false_supported_rate"] * 100
    d_fs = fs_exp - fs_base
    print(f"{'False SUPPORTED Rate (%)':<35} {fs_base:>12.2f}% {fs_exp:>14.2f}% {d_fs:>+10.2f}%")

    fs_cnt_base = base_summary["false_supported_metrics"]["count"]
    fs_cnt_exp = exp_summary["false_supported_metrics"]["count"]
    print(f"{'False SUPPORTED Count':<35} {fs_cnt_base:>13} {fs_cnt_exp:>15} {fs_cnt_exp - fs_cnt_base:>+11}")

    # Specific Target Failure Modes
    if "relational_mismatch" in base_summary["diagnostic_subset_performance"] and "relational_mismatch" in exp_summary["diagnostic_subset_performance"]:
        rm_base = base_summary["diagnostic_subset_performance"]["relational_mismatch"]["accuracy"] * 100
        rm_exp = exp_summary["diagnostic_subset_performance"]["relational_mismatch"]["accuracy"] * 100
        print(f"{'Relational Mismatch Acc (%)':<35} {rm_base:>12.2f}% {rm_exp:>14.2f}% {rm_exp - rm_base:>+10.2f}%")

    if "partial_evidence" in base_summary["diagnostic_subset_performance"] and "partial_evidence" in exp_summary["diagnostic_subset_performance"]:
        pe_base = base_summary["diagnostic_subset_performance"]["partial_evidence"]["accuracy"] * 100
        pe_exp = exp_summary["diagnostic_subset_performance"]["partial_evidence"]["accuracy"] * 100
        print(f"{'Partial Evidence Acc (%)':<35} {pe_base:>12.2f}% {pe_exp:>14.2f}% {pe_exp - pe_base:>+10.2f}%")

    lat_base = base_summary["mean_latency_ms"]
    lat_exp = exp_summary["mean_latency_ms"]
    print(f"{'Mean Latency per Claim (ms)':<35} {lat_base:>10.2f} ms {lat_exp:>12.2f} ms {lat_exp - lat_base:>+8.2f} ms")
    print("=" * 80 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate and compare claim verifiers on verification benchmarks.")
    parser.add_argument("--split", choices=["dev", "eval", "both"], default="both", help="Split to evaluate.")
    parser.add_argument("--verifier", choices=["linguistic", "relation_aware", "both"], default="both", help="Verifier to test.")
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/results"), help="Results output directory.")
    args = parser.parse_args()

    data_dir = Path("data/processed/verification")
    splits = ["dev", "eval"] if args.split == "both" else [args.split]

    for s in splits:
        path = data_dir / f"{s}_verification.jsonl"
        if not path.exists():
            print(f"Error: {path} does not exist.", file=sys.stderr)
            continue

        if args.verifier == "both":
            base_summary, base_file = run_evaluation(path, args.output_dir, verifier_name="linguistic", verifier_version="1.0.0")
            print_report(base_summary, base_file)

            exp_summary, exp_file = run_evaluation(path, args.output_dir, verifier_name="relation_aware", verifier_version="2.0.0")
            print_report(exp_summary, exp_file)

            print_comparison_table(base_summary, exp_summary, s)
        else:
            ver_version = "1.0.0" if args.verifier == "linguistic" else "2.0.0"
            summary, out_file = run_evaluation(path, args.output_dir, verifier_name=args.verifier, verifier_version=ver_version)
            print_report(summary, out_file)


if __name__ == "__main__":
    main()
