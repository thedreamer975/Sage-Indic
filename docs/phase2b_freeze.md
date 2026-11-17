# SAGE-Indic: Phase 2B Tokenization Research Freeze

**Document Version:** 1.0.0  
**Phase Status:** Frozen & Accepted Implementation Baseline  
**Date:** 2026-09-29  
**Branch / Tag Baseline:** `main` (Package Version: `0.2.0`)

---

## 1. Executive Summary & Research Baseline

This document formally records the frozen state of **Phase 2B: Tokenization Research** for the SAGE-Indic project. 

The primary objective of Phase 2B was to evaluate whether linguistically structured subword tokenization (**SAGE Tokenizer**: Script- and Affix-Guided Encoding) provides higher morphological boundary alignment on Native Telugu, Romanized Telugu, and Telugu-English Code-Mixed text compared to standard Byte-Pair Encoding (BPE) and Unigram Language Model baselines under strictly matched conditions ($V \in \{2000, 4000\}$).

All models, datasets, evaluation metrics, and benchmark scripts are frozen as of this checkpoint.

---

## 2. Implementation Version & Repository Structure

- **Package Version:** `0.2.0` (`sage_indic`)
- **Core Library Dependencies:** `tokenizers>=0.20.0`, standard library (`re`, `unicodedata`, `json`, `pathlib`).
- **Frozen Modules:**
  - `src/sage_indic/tokenizer/base.py`: Minimal abstract `BaseTokenizer` defining `train`, `encode`, `encode_ids`, `decode`, `save`, `load`.
  - `src/sage_indic/tokenizer/bpe_baseline.py`: Matched Byte-Pair Encoding (`BpeBaselineTokenizer`).
  - `src/sage_indic/tokenizer/unigram_baseline.py`: Matched Unigram Language Model (`UnigramBaselineTokenizer`).
  - `src/sage_indic/tokenizer/morphology.py`: Deterministic Telugu orthographic akshara parser, nominal/verbal affix inventory, and segmentation logic.
  - `src/sage_indic/tokenizer/sage_tokenizer.py`: Constrained two-phase SAGE tokenizer with exact round-trip lossless detokenization.
  - `src/sage_indic/tokenizer/evaluation.py`: Token efficiency and boundary alignment evaluation utilities.
  - `scripts/prepare_tokenizer_data.py`: Corpus acquisition, normalization, transliteration, and partition script.
  - `experiments/run_tokenizer_experiment.py`: Matched-condition benchmark harness.

---

## 3. Dataset Provenance & Partition Sizes

All tokenizers were trained and evaluated on strictly isolated partitions without overlap.

### 3.1 Training Corpus (`data/processed/tokenizer/train_corpus.txt`)
- **Total Unique Sentences:** 4,688
- **Total Words:** 38,443
- **Total Characters:** 335,016
- **Corpus Sources:**
  1. *UD_Telugu-MTG Train & Dev Split:* 1,058 sentences (formal native syntax, CC BY-NC-SA 3.0).
  2. *UD_Telugu-MTG Synthesized Transliteration:* 1,058 sentences (Romanized Latin script).
  3. *Telugu Wikipedia (te.wikipedia.org):* 2,422 encyclopedic sentences across science, history, geography, and literature.
  4. *Conversational Telugu-English Code-Mixed Corpus:* 150 sentences.

### 3.2 Held-Out Evaluation Sets (`data/processed/tokenizer/`)
None of the evaluation sentences are present in the training set (zero data leakage).

| Dataset File | Size (Sentences) | Word Count | Script / Modality | Role |
| :--- | :--- | :--- | :--- | :--- |
| `eval_native.txt` | 146 | 721 | Native Telugu script | Monolingual token efficiency & fragmentation |
| `eval_romanized.txt` | 146 | 721 | Romanized Latin | Cross-script token inflation |
| `eval_codemix.txt` | 150 | 1,230 | Latin + Telugu script | Cross-script boundary preservation |
| `eval_morphology.jsonl`| 146 | 721 | Native Telugu script | Treebank syntactic boundary proxy alignment |

---

## 4. Methodology & Construction of `eval_morphology.jsonl`

To ensure absolute research integrity, the provenance, extraction methodology, and precise linguistic nature of `eval_morphology.jsonl` are documented below.

### 4.1 Source Fields
- **Source:** Universal Dependencies `UD_Telugu-MTG` official `test` split (`te_mtg-ud-test.conllu`), published by Rama & Vajjala (2018), based on the reference grammar of Krishnamurti & Gwynn (1985).
- **Extracted Fields:**
  - `# text =`: Full native sentence string.
  - `# translit =`: Romanized transliteration.
  - CoNLL-U Column 2 (`FORM`): Syntactic word tokens for every line where Column 1 (`ID`) is an integer.

### 4.2 Conversion to Character Offset Boundaries
1. Each sentence record in `eval_morphology.jsonl` stores `text` and `gold_morpheme_tokens` (the list of `FORM` strings from the CoNLL-U table).
2. During evaluation in `evaluate_morphological_alignment()`, the character end-offset of each token within the normalized text is computed via string indexing:
   $$\text{boundary} = \text{start\_pos}(\text{tok}) + \text{len}(\text{tok})$$
3. The sentence-final offset ($\text{len}(\text{text})$) is excluded, leaving only internal boundaries.
4. Total internal reference boundaries across the 146 test sentences:
   $$N_{\text{boundaries}} = 721 \text{ tokens} - 146 \text{ sentences} = 575 \text{ internal boundaries}$$

### 4.3 Classification: Derived Boundary Proxy (NOT True Intra-Word Morpheme Annotation)
- **Important Distinction:** In `UD_Telugu-MTG`, the `FORM` column represents **syntactic words, punctuation, and clitics** separated by treebank annotation rules. 
- The treebank does **not** split bound nominal case inflections into intra-word sub-tokens in the `FORM` field. For example, the inflected noun `కుక్కను` ("dog-accusative") is represented as a single `FORM` with morphological feature `Case=Acc`, not split into `కుక్క` + `ను`.
- **Verdict:** Therefore, `eval_morphology.jsonl` represents a **Derived Morphological / Syntactic Boundary Proxy**, rather than a true fine-grained intra-word morpheme boundary annotation. It measures whether subword models respect treebank syntactic word boundaries and avoid spurious cross-token fusions or excessive fragmentation.

### 4.4 Examples of Original Word, Annotation, and Boundary Positions

**Example 1: Word with attached accusative postposition**
- *Original Sentence:* `వాడు కుక్కను కర్రతో కొట్టేడు .`
- *UD `FORM` Tokens:* `["వాడు", "కుక్కను", "కర్రతో", "కొట్టేడు", "."]`
- *Derived Proxy Boundaries:* Character positions at end of `వాడు` (4), `కుక్కను` (11), `కర్రతో` (18), `కొట్టేడు` (26).
- *Observation:* Intra-word boundary between stem `కుక్క` and accusative `-ను` is NOT in the reference set because UD treats `కుక్కను` as a single syntactic word.

**Example 2: Sentence with punctuation and separated tokens**
- *Original Sentence:* `అంత పెద్ద పుస్తకం చదివేరా ?`
- *UD `FORM` Tokens:* `["అంత", "పెద్ద", "పుస్తకం", "చదివేరా", "?"]`
- *Derived Proxy Boundaries:* End of `అంత` (3), `పెద్ద` (8), `పుస్తకం` (16), `చదివేరా` (24).

---

## 5. Frozen Experimental Configurations

The benchmark evaluates four models across two matched vocabulary settings ($V = 2,000$ and $V = 4,000$):
1. **`BPE`**: Standard Byte-Pair Encoding (`tokenizers.models.BPE`) with Metaspace pre-tokenization.
2. **`Unigram`**: Standard Unigram Language Model (`tokenizers.models.Unigram`) with Metaspace pre-tokenization.
3. **`SAGE`**: Full proposed SAGE tokenizer (akshara-integrity regex pre-segmentation + nominal/verbal affix stripping + Unigram subword modeling).
4. **`SAGE_Ablation_NoMorph`**: SAGE with affix pre-segmentation disabled (isolates the effect of the morphological layer).

---

## 6. Official Benchmark Results

All models evaluated under strictly identical conditions on held-out test sets:

| Model Configuration | Vocab ($V$) | Native T/W | Native CR (chars/tok) | Romanized T/W | Code-Mixed T/W | Morph Proxy Prec | Morph Proxy Rec | **Morph Proxy F1** |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BPE_2000** | 2000 | 1.922 | 2.426 | 2.491 | 5.293 | 0.5068 | 0.5861 | **0.5435** |
| **Unigram_2000** | 2000 | 2.082 | 2.241 | 2.578 | 5.829 | 0.5090 | 0.6904 | **0.5860** |
| **SAGE_2000** | 2000 | 2.129 | 2.191 | 2.601 | 5.602 | 0.5098 | 0.7217 | **0.5976** |
| **SAGE_Ablation_NoMorph_2000** | 2000 | 2.086 | 2.236 | 2.592 | 5.829 | 0.5083 | 0.6922 | **0.5862** |
| **BPE_4000** | 4000 | 1.642 | 2.840 | 2.040 | 4.610 | 0.5832 | 0.4696 | **0.5202** |
| **Unigram_4000** | 4000 | 1.836 | 2.540 | 2.298 | 5.130 | 0.5904 | 0.6191 | **0.6044** |
| **SAGE_4000** | 4000 | 1.903 | 2.451 | 2.334 | 5.211 | 0.6006 | 0.6800 | **0.6378** |
| **SAGE_Ablation_NoMorph_4000** | 4000 | 1.838 | 2.538 | 2.298 | 5.130 | 0.5894 | 0.6191 | **0.6039** |

*Note: All configurations exhibited $0.0\%$ UNK rate on held-out text.*

### 6.1 Scientific Interpretation of Findings
1. **Hypothesis Evaluation:** The empirical results are **consistent with the hypothesis** that linguistically-guided pre-segmentation improves alignment with reference linguistic units. At $V=4,000$, SAGE achieves an observed improvement of $+0.1176$ in $F1$ over BPE and $+0.0334$ over Unigram.
2. **Ablation Insight:** When morphological pre-segmentation is disabled (`SAGE_Ablation_NoMorph_4000`), boundary F1 drops from $0.6378$ to $0.6039$, which is virtually identical to the Unigram baseline ($0.6044$). This ablation indicates that the deterministic affix-guided pre-segmentation layer is consistent with driving the observed improvement in alignment.
3. **Efficiency Trade-off:** SAGE's higher alignment incurs a modest $+3.6\%$ token overhead compared to Unigram (1.903 vs 1.836 tokens/word at $V=4000$), well within the $15\%$ maximum threshold established in the design specification.

---

## 7. Known Limitations

1. **Proxy Limitation:** As detailed in Section 4, the evaluation boundary set reflects treebank syntactic tokens rather than fine-grained intra-word morpheme annotations. A future study with a dedicated morphologically annotated lexeme treebank would provide direct sub-lexeme precision.
2. **Non-Concatenative Sandhi:** Telugu features euphonic sandhi transformations ($V_1 + V_2 \rightarrow V_3$) that alter stem-final and suffix-initial characters. SAGE currently applies concatenative affix stripping and does not invert morpho-phonological sandhi rules.
3. **Compound Words (Samasas):** Polysyllabic Sanskrit loan compounds without inflectional suffixes are treated as monolithic stems unless segmented by the statistical subword model.
4. **Scale:** The experiment was conducted on a controlled 4,688-sentence corpus for strict isolation and fast experimental iteration. Generalization to web-scale multi-gigabyte corpora remains to be tested in future phases.

---

## 8. Reproducibility Commands

To regenerate the entire dataset, train all models, recompute metrics, and verify all unit tests:

```bash
# 1. Regenerate processed training and evaluation data
python scripts/prepare_tokenizer_data.py

# 2. Execute end-to-end tokenizer benchmark and recreate results
python experiments/run_tokenizer_experiment.py

# 3. Verify linting, formatting, and unit tests
ruff check .
ruff format --check .
pytest
```

---

## 9. Checkpoint Conclusion

Phase 2B (Tokenization Research) is complete, frozen, and experimentally verified. No further modifications to the tokenizer implementations, vocabulary files, or tokenizer benchmark scripts are permitted without explicit justification and version bumping.
