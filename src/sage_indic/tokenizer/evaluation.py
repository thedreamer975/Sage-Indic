"""Evaluation metrics and benchmarking runner for SAGE-Indic tokenizers."""

import json
from pathlib import Path
from typing import Any

from sage_indic.normalize import normalize_text
from sage_indic.tokenizer.base import BaseTokenizer


def compute_efficiency_metrics(tokenizer: BaseTokenizer, sentences: list[str]) -> dict[str, float]:
    """Compute token efficiency metrics over a list of sentences.

    Metrics:
    - total_tokens
    - total_words
    - total_chars
    - tokens_per_sentence
    - tokens_per_word (fertility)
    - compression_ratio (chars_per_token)
    - unk_count and unk_rate
    """
    total_tokens = 0
    total_words = 0
    total_chars = 0
    unk_count = 0

    for s in sentences:
        norm = normalize_text(s)
        if not norm:
            continue
        words = norm.split()
        total_words += len(words)
        total_chars += len(norm.replace(" ", ""))

        tokens = tokenizer.encode(norm)
        total_tokens += len(tokens)
        unk_count += sum(1 for t in tokens if t in ("<unk>", "[UNK]"))

    num_sents = max(1, len(sentences))
    total_tokens_safe = max(1, total_tokens)
    total_words_safe = max(1, total_words)

    return {
        "num_sentences": len(sentences),
        "total_tokens": total_tokens,
        "total_words": total_words,
        "tokens_per_sentence": round(total_tokens / num_sents, 3),
        "tokens_per_word": round(total_tokens / total_words_safe, 3),
        "compression_ratio": round(total_chars / total_tokens_safe, 3),
        "unk_count": unk_count,
        "unk_rate": round(unk_count / total_tokens_safe, 5),
    }


def compute_morphological_alignment(
    tokenizer: BaseTokenizer,
    annotated_records: list[dict[str, Any]],
) -> dict[str, float]:
    """Evaluate alignment between predicted subwords and gold morpheme boundaries.

    Args:
        tokenizer: Trained BaseTokenizer.
        annotated_records: List of dicts with 'text' and 'gold_morpheme_tokens'.

    Returns:
        dict with precision, recall, and f1 of morphological boundary detection.
    """
    tp = 0
    fp = 0
    fn = 0

    for record in annotated_records:
        text = normalize_text(record.get("text", ""))
        gold_tokens = record.get("gold_morpheme_tokens", [])
        if not text or not gold_tokens:
            continue

        # Extract gold character boundary offsets (intra-sentence character split positions)
        gold_boundaries: set[int] = set()
        current_idx = 0
        for tok in gold_tokens:
            pos = text.find(tok, current_idx)
            if pos != -1:
                end_pos = pos + len(tok)
                gold_boundaries.add(end_pos)
                current_idx = end_pos

        # Extract predicted subword boundaries
        pred_tokens = tokenizer.encode(text)
        pred_boundaries: set[int] = set()
        curr_pos = 0

        for tok in pred_tokens:
            # Clean token formatting (strip Metaspace ' ' or '##')
            clean_tok = tok.removeprefix(" ").removeprefix("##")
            if not clean_tok:
                continue
            pos = text.find(clean_tok, curr_pos)
            if pos != -1:
                end_pos = pos + len(clean_tok)
                pred_boundaries.add(end_pos)
                curr_pos = end_pos

        # Compare internal boundaries (ignore end of sentence)
        text_len = len(text)
        gold_set = {b for b in gold_boundaries if 0 < b < text_len}
        pred_set = {b for b in pred_boundaries if 0 < b < text_len}

        cur_tp = len(pred_set & gold_set)
        cur_fp = len(pred_set - gold_set)
        cur_fn = len(gold_set - pred_set)

        tp += cur_tp
        fp += cur_fp
        fn += cur_fn

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "boundary_precision": round(precision, 4),
        "boundary_recall": round(recall, 4),
        "boundary_f1": round(f1, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
    }


def evaluate_tokenizer(
    tokenizer: BaseTokenizer,
    eval_dir: str | Path,
) -> dict[str, Any]:
    """Run full benchmark evaluation across Native, Romanized, Code-Mix, and Morphology sets."""
    eval_path = Path(eval_dir)

    native_sents = eval_path.joinpath("eval_native.txt").read_text(encoding="utf-8").splitlines()
    romanized_sents = (
        eval_path.joinpath("eval_romanized.txt").read_text(encoding="utf-8").splitlines()
    )
    codemix_sents = eval_path.joinpath("eval_codemix.txt").read_text(encoding="utf-8").splitlines()

    morph_records = [
        json.loads(line)
        for line in eval_path.joinpath("eval_morphology.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    return {
        "vocab_size": tokenizer.get_vocab_size(),
        "native_telugu": compute_efficiency_metrics(tokenizer, native_sents),
        "romanized_telugu": compute_efficiency_metrics(tokenizer, romanized_sents),
        "code_mixed": compute_efficiency_metrics(tokenizer, codemix_sents),
        "morphological_alignment": compute_morphological_alignment(tokenizer, morph_records),
    }
