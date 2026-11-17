"""Evaluation harness and metrics for Phase 2C Safety Layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from sage_indic.safety.types import SafetyLabel, SafetyResult


class SafetyClassifierProtocol(Protocol):
    """Protocol for safety classifiers."""

    def predict(self, text: str) -> SafetyResult:
        ...


def compute_safety_metrics(
    predictions: list[str],
    targets: list[str],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute comprehensive classification and safety-specific metrics."""
    total = len(targets)
    if total == 0:
        return {}

    labels = [SafetyLabel.SAFE.value, SafetyLabel.UNSAFE.value, SafetyLabel.UNCERTAIN.value]

    # Overall Accuracy
    correct = sum(1 for p, t in zip(predictions, targets) if p == t)
    accuracy = correct / total

    # Per-class Precision, Recall, F1
    per_class: dict[str, dict[str, float]] = {}
    f1_list: list[float] = []

    for lbl in labels:
        tp = sum(1 for p, t in zip(predictions, targets) if p == lbl and t == lbl)
        fp = sum(1 for p, t in zip(predictions, targets) if p == lbl and t != lbl)
        fn = sum(1 for p, t in zip(predictions, targets) if p != lbl and t == lbl)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[lbl] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": sum(1 for t in targets if t == lbl),
        }
        f1_list.append(f1)

    macro_f1 = sum(f1_list) / len(f1_list)

    # Safety-Specific Metrics:
    # 1. Benign-Sensitive False Positive Rate (FPR):
    # Fraction of benign-sensitive instances labeled as UNSAFE
    bs_indices = [i for i, r in enumerate(records) if r.get("is_benign_sensitive")]
    if bs_indices:
        bs_fp = sum(1 for i in bs_indices if predictions[i] == SafetyLabel.UNSAFE.value)
        bs_fpr = bs_fp / len(bs_indices)
    else:
        bs_fpr = 0.0

    # 2. Unsafe Recall & False Negative Rate (FNR):
    unsafe_indices = [i for i, t in enumerate(targets) if t == SafetyLabel.UNSAFE.value]
    if unsafe_indices:
        unsafe_tp = sum(1 for i in unsafe_indices if predictions[i] == SafetyLabel.UNSAFE.value)
        unsafe_recall = unsafe_tp / len(unsafe_indices)
        unsafe_fnr = 1.0 - unsafe_recall
    else:
        unsafe_recall = 0.0
        unsafe_fnr = 0.0

    # 3. Abstention Rate & Coverage:
    abstentions = sum(1 for p in predictions if p == SafetyLabel.UNCERTAIN.value)
    abstention_rate = abstentions / total
    coverage = 1.0 - abstention_rate

    # Slice Breakdowns:
    slices: dict[str, dict[str, Any]] = {}
    for slice_name, filter_fn in [
        ("native_telugu", lambda r: r.get("script") == "native"),
        ("romanized_telugu", lambda r: r.get("script") == "romanized"),
        ("code_mixed", lambda r: r.get("script") == "code_mixed"),
        ("obfuscated", lambda r: r.get("is_obfuscated")),
        ("benign_sensitive", lambda r: r.get("is_benign_sensitive")),
    ]:
        slice_indices = [i for i, r in enumerate(records) if filter_fn(r)]
        if slice_indices:
            s_preds = [predictions[i] for i in slice_indices]
            s_targets = [targets[i] for i in slice_indices]
            s_corr = sum(1 for p, t in zip(s_preds, s_targets) if p == t)
            slices[slice_name] = {
                "count": len(slice_indices),
                "accuracy": round(s_corr / len(slice_indices), 4),
            }

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "safety_specific": {
            "benign_sensitive_fpr": round(bs_fpr, 4),
            "unsafe_recall": round(unsafe_recall, 4),
            "unsafe_fnr": round(unsafe_fnr, 4),
            "abstention_rate": round(abstention_rate, 4),
            "coverage": round(coverage, 4),
        },
        "slices": slices,
    }


def evaluate_safety_model(
    model: SafetyClassifierProtocol,
    dataset_path: str | Path,
) -> dict[str, Any]:
    """Evaluate a safety model over a JSONL dataset file."""
    path = Path(dataset_path)
    records: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    predictions: list[str] = []
    targets: list[str] = []
    results_list: list[dict[str, Any]] = []

    for r in records:
        text = r["text"]
        target = r["label"]
        res = model.predict(text)
        predictions.append(res.label.value)
        targets.append(target)
        results_list.append(
            {
                "id": r.get("id"),
                "text": text,
                "target": target,
                "predicted": res.label.value,
                "confidence": res.confidence,
                "method": res.method,
                "is_correct": res.label.value == target,
            }
        )

    metrics = compute_safety_metrics(predictions, targets, records)
    metrics["num_examples"] = len(records)
    metrics["item_results"] = results_list
    return metrics
