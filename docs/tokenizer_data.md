# SAGE-Indic: Tokenizer Data Documentation

**Document Version:** 1.0.0  
**Status:** Complete  
**Date:** 2026-09-29  
**Output Directory:** `data/processed/tokenizer/`  

---

## 1. Overview & Provenance

To conduct a controlled, reproducible, and computationally tractable tokenizer study within the project timeline, a dedicated multi-form Telugu corpus was assembled from primary, verified sources in accordance with [AGENTS.md](file:///d:/Sage-Indic/AGENTS.md) and [docs/data_strategy.md](file:///d:/Sage-Indic/docs/data_strategy.md).

No multi-gigabyte uncurated web dumps were downloaded. All acquired text passes through the conservative normalization pipeline defined in [src/sage_indic/normalize.py](file:///d:/Sage-Indic/src/sage_indic/normalize.py) (Unicode NFC, whitespace normalization, control character removal, and Telugu virama ZWNJ preservation).

---

## 2. Dataset Sources & Licenses

| Source | Identifier / URL | License | Language / Script | Content Type |
| :--- | :--- | :--- | :--- | :--- |
| **UD_Telugu-MTG** | UniversalDependencies/UD_Telugu-MTG (Rama & Vajjala, 2018) | CC BY-NC-SA 3.0 | Native Telugu Script + Romanized Transliteration | Linguistically validated sentences with gold-standard morphological tokens and lemmas (Krishnamurti & Gwynn grammar). |
| **Wikipedia Telugu** | `te.wikipedia.org` via official MediaWiki API | CC BY-SA 3.0 | Native Telugu Script | Curated encyclopedic prose across geography, history, literature, and science. |
| **SAGE Code-Mixed Set**| SAGE-Indic project repository | Apache-2.0 | Telugu-English Code-Mixed (Latin & Mixed Scripts) | Workplace, everyday, technical, and academic code-mixed utterances with Telugu postpositions and verbal inflections. |

---

## 3. Corpus Partitions & Statistics

### 3.1 Training Corpus (`train_corpus.txt`)
- **Total Sentences:** 4,688 unique, non-empty sentences.
- **Composition:**
  - 1,051 sentences: Native Telugu from `UD_Telugu-MTG` (train split).
  - 1,051 sentences: Paired Romanized transliterations from `UD_Telugu-MTG` (train split).
  - 2,350 sentences: Clean native Telugu encyclopedic sentences from `te.wikipedia.org`.
  - 500 sentences: Controlled Telugu-English code-mixed training patterns.
- **Role:** Exclusively used for statistical subword vocabulary induction and merge learning across BPE, Unigram, and SAGE tokenizers.

### 3.2 Held-Out Evaluation Corpora (Strict Zero-Leakage Guarantee)
Under no circumstances are any evaluation sentences present in `train_corpus.txt`.

1. **`eval_native.txt` (Held-Out Native Telugu):**
   - **Size:** 146 sentences.
   - **Source:** `UD_Telugu-MTG` official `test` split (never seen in training).
   - **Role:** Evaluating subword token count, tokens per word, fertility, and compression ratio on native script.
2. **`eval_romanized.txt` (Held-Out Romanized Telugu):**
   - **Size:** 146 sentences.
   - **Source:** Romanized transliterations of `UD_Telugu-MTG` official `test` split.
   - **Role:** Evaluating cross-script fertility and compression on Romanized Telugu.
3. **`eval_codemix.txt` (Held-Out Code-Mixed Telugu-English):**
   - **Size:** 150 sentences.
   - **Source:** Dedicated held-out conversational, technical, and workplace code-mixed sentences.
   - **Role:** Evaluating subword fragmentation on hybrid code-mixed tokens (e.g. `officeki`, `heavyga`, `projectlo`).
4. **`eval_morphology.jsonl` (Derived Morphological/Syntactic Boundary Proxy):**
   - **Size:** 146 annotated records (721 treebank tokens, 575 internal boundary offsets).
   - **Source:** `UD_Telugu-MTG` official `test` split CoNLL-U `FORM` tokens (Rama & Vajjala, 2018).
   - **Nature of Annotation:** **Derived Boundary Proxy (NOT gold intra-word morpheme segmentation)**. UD CoNLL-U decomposes sentences into syntactic words, clitics, and punctuation; it does not split bound inflectional morphemes (e.g., `కుక్కను` is a single syntactic word token with morphological feature `Case=Acc`, not split into `కుక్క` + `ను`).
   - **Role:** Evaluating whether subword token boundaries align with treebank syntactic token boundaries without over-fragmentation or cross-token merging.

---

## 4. Reproducibility

To re-generate all training and evaluation files from scratch:

```bash
python scripts/prepare_tokenizer_data.py
```

All processed files are generated into `data/processed/tokenizer/`.
Large raw files are excluded from git via [.gitignore](file:///d:/Sage-Indic/.gitignore).
