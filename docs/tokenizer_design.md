# SAGE-Indic: Tokenizer Design Specification

**Document Version:** 1.0.0  
**Status:** Approved Research Specification  
**Authors:** SAGE-Indic Research Team  
**Focus:** Telugu Native Script, Romanized Telugu, and Telugu-English Code-Mixed Inputs  

---

## 1. What "SAGE" Stands For

Within the SAGE-Indic research framework:
- **SAGE (Project-Level):** **S**afe, **A**ware (Linguistically-Aware), **G**rounded, **E**vidence-Backed Indic LLM Pipeline.
- **SAGE Tokenizer (Component-Level):** **S**cript- & **A**ffix-**G**uided **E**ncoding — a hybrid, morphology-constrained subword tokenization strategy designed for agglutinative Indic languages.

---

## 2. Research Hypothesis ($H_1$)

> **Hypothesis ($H_1$):**  
> *Constraining statistical subword induction with deterministic orthographic syllable (akshara) integrity and high-frequency Telugu nominal/verbal affix boundaries prior to vocabulary pruning will:*  
> 1. *Significantly increase boundary alignment ($F1_{morph}$) with true linguistic morpheme boundaries compared to standard unconstrained BPE and Unigram tokenizers at the exact same vocabulary size ($V$).*  
> 2. *Reduce subword token fragmentation (fertility / tokens-per-word) on inflected native Telugu words and code-mixed Latin tokens with attached Telugu postpositions.*  
> 3. *Maintain lossless round-trip textual reconstruction without degrading character-level vocabulary coverage.*

---

## 3. Problem Statement & Motivation

Telugu is an agglutinative Dravidian language characterized by:
1. **Nominal Case Suffixation (Vibhakti):** Nouns attach multi-syllabic postpositions and case markers directly to base stems (e.g., `హైదరాబాద్` + `లో` = `హైదరాబాద్‌లో` [in Hyderabad]; `గది` + `నుంచి` = `గదినుంచి` [from the room]).
2. **Complex Verbal Conjugation:** Verbs conjugate with tense, aspect, person, number, and gender suffixes (e.g., `చేస్తున్నాను` [I am doing], `చేస్తున్నారు` [they are doing]).
3. **Orthographic Akshara Structure:** Native Telugu characters form consonant-vowel-virama clusters ($C^*V[M]$). Standard byte-level or unconstrained subword tokenizers frequently slice across combining vowel signs and conjunct virama markers (`\u0C4D`), producing malformed or unpronounceable subwords.
4. **Cross-Script Code-Mixing & Transliteration:** In Romanized Telugu and Telugu-English code-mixing, English nouns seamlessly attach Telugu suffixes (e.g., `office-ki`, `college-lo`, `heavy-ga`, `project-gurinchi`). Standard English/multilingual tokenizers fragment these hybrid words arbitrarily into unrelated English subword fragments.

---

## 4. Inadequacy of Standard BPE for Target Telugu Setting

Byte-Pair Encoding (BPE; Sennrich et al., 2016) is a greedy, frequency-based merge algorithm:
1. **Greedy Frequency Bias:** BPE merges character pairs based purely on global co-occurrence frequency in the training corpus. Because inflectional variations dilute word counts across thousands of surface forms, BPE merges frequent whole words but leaves moderately frequent inflected words severely fragmented into single characters or arbitrary substrings.
2. **Morpheme Boundary Crossing:** BPE bigram merges routinely span across the stem-affix boundary if that specific boundary bigram is common in frequent words, but fails on rare stems with the identical affix.
3. **Cross-Script Hybrid Fragmentation:** For code-mixed words like `officeki`, BPE splits into subwords based on Latin character statistics rather than recognizing `office` (English root) + `ki` (Telugu dative postposition), increasing token fertility.

---

## 5. Role of Unigram as a Strong Baseline

Unigram (Kudo, 2018) treats tokenization as a probabilistic language modeling problem:
- It initializes a large seed vocabulary and iteratively prunes subwords that minimize the increase in corpus loss (negative log-likelihood).
- During inference, it uses the Viterbi algorithm to find the globally optimal subword segmentation sequence $S^* = \arg\max_S \sum_{t \in S} \log P(t)$.
- Unigram is less prone to greedy merge errors than BPE and provides a competitive baseline for subword compression.

---

## 6. SAGE Tokenizer: Algorithmic Mechanism

SAGE introduces a **Two-Phase Constrained Subword Architecture**:

```
Input Raw String
      ↓
[ Phase 1: Conservative Normalization & Script Detection ]
      ↓
[ Phase 2: Linguistic Constraint & Affix Boundary Marking ]
  ├── 1. Native Akshara Boundary Preservation (C*V[M] clusters protected)
  ├── 2. Nominal & Verbal Affix Segmentation (Vibhakti / Pratyayalu extracted)
  └── 3. Code-Mixed Hybrid Splitting ([Root: Latin/En] + [Affix: Te])
      ↓
[ Phase 3: Constrained Statistical Subword Optimization ]
  ├── Base Vocabulary initialized with guaranteed Core Affixes & Single Aksharas
  └── Viterbi / EM Subword Optimization trained on pre-segmented structural units
      ↓
Deterministic SAGE Tokens (Lossless round-trip reconstruction)
```

### Exact SAGE Encoding Algorithm:
1. **Input Normalization:** Apply Unicode NFC and whitespace standardization via `normalize_text(text)`.
2. **Boundary-Constrained Pre-Segmentation:**
   - For Native Telugu tokens: Segment word into atomic akshara units and split off known high-frequency inflectional suffixes (e.g., `రాష్ట్రాలలో` $\rightarrow$ `రాష్ట్రాల` + `##లో`).
   - For Latin / Code-Mixed tokens: Identify English/Latin root and strip attached Telugu agglutinative postpositions (e.g., `officeki` $\rightarrow$ `office` + `##ki`, `heavyga` $\rightarrow$ `heavy` + `##ga`).
3. **Constrained Subword Inference:**
   - Execute statistical subword segmentation (Unigram model) **within** the pre-segmented constituent boundaries. Subword merges are strictly forbidden from crossing an explicit morphological or script boundary.
4. **Lossless Detokenization:**
   - Affix markers (e.g. `##` or SentencePiece underscore ` `) ensure exact, byte-for-byte lossless reconstruction of the original text.

---

## 7. Linguistic & Morphological Information Used

1. **Native Telugu Orthographic Syllables (Aksharas):**
   - Consonant clusters with virama + dependent vowel signs (`[\u0C15-\u0C39](\u0C4D[\u0C15-\u0C39])*[\u0C3E-\u0C4C]?[\u0C01-\u0C03]?`).
2. **High-Frequency Telugu Nominal Postpositions / Case Markers (Vibhakti):**
   - Native: `లో`, `కి`, `కు`, `తో`, `కోసం`, `నుంచి`, `నుండి`, `గురించి`, `మీద`, `కింద`, `వరకు`, `కన్నా`, `గా`, `లా`, `లు`, `ని`, `ను`.
   - Romanized: `lo`, `ki`, `ku`, `tho`, `to`, `kosam`, `nunchi`, `nundi`, `gurinchi`, `meeda`, `kinda`, `varaku`, `kanna`, `ga`, `la`, `lu`, `ni`, `nu`.
3. **High-Frequency Telugu Verbal Suffixes:**
   - Native: `త్తున్నాను`, `తున్నారు`, `తుంది`, `వాలి`, `యాలి`, `య్యాలి`, `డము`, `ద్దము`, `చేశాను`, `చేశారు`.
   - Romanized: `thunnanu`, `tunnanu`, `thunnaru`, `tunnaru`, `thundi`, `tundi`, `aali`, `ali`, `yali`, `yyali`, `ddamu`, `damu`, `chesanu`, `chesaru`.

---

## 8. Information SAGE Does NOT Use

- ❌ Does NOT use deep neural network parsers or black-box LLM APIs.
- ❌ Does NOT require full-coverage static dictionary lookup for every Telugu root.
- ❌ Does NOT use destructive transliteration or lossy phonetic mappings.
- ❌ Does NOT use syntactic dependency trees during inference (only during offline evaluation against treebanks).

---

## 9. Hyperparameters & Configuration

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `vocab_size` | int | 4000 | Target vocabulary capacity for matched comparison (evaluated at 2000 and 4000). |
| `enable_morph_presegmentation` | bool | True | Enforce morphological affix boundary constraints (False in ablation). |
| `enable_akshara_constraints` | bool | True | Prevent splitting inside atomic Telugu aksharas. |
| `character_coverage` | float | 0.9995 | Minimum character set coverage ratio. |
| `min_frequency` | int | 2 | Minimum frequency for candidate subword generation. |

---

## 10. Evaluation Metrics

1. **Efficiency Metrics:**
   - **Total Tokens ($N_{tok}$):** Total tokens generated over held-out test sets.
   - **Tokens Per Sentence ($T_{sent}$):** Mean tokens per sentence.
   - **Tokens Per Word ($T_{word}$):** Mean subword tokens per whitespace-delimited word.
   - **Compression Ratio ($CR$):** Total characters / Total tokens ($\text{chars}/\text{token}$).
2. **Linguistic Alignment Metrics (Derived Boundary Proxy):**
   - **Boundary Precision ($P_{morph}$):** Proportion of tokenizer-predicted subword boundaries that coincide with treebank syntactic/morphological token boundaries (derived from Universal Dependencies `UD_Telugu-MTG`).
   - **Boundary Recall ($R_{morph}$):** Proportion of treebank token boundaries detected by the tokenizer.
   - **Boundary F1 ($F1_{morph}$):** Harmonic mean of $P_{morph}$ and $R_{morph}$.
3. **Coverage & Robustness:**
   - **Unknown Token Rate ($R_{unk}$):** Proportion of `[UNK]` tokens on held-out text (must remain $0.0\%$).
   - Evaluated separately across Native Telugu, Romanized Telugu, and Code-Mixed test splits.

---

## 11. Falsification Criteria (Evidence Against the Hypothesis)

The hypothesis $H_1$ will be considered **NOT SUPPORTED** if:
1. SAGE achieves higher token fragmentation ($T_{word}$ is $> 15\%$ worse than Unigram/BPE) without a statistically significant gain ($> 5\%$ absolute) in morphological boundary F1 ($F1_{morph}$).
2. SAGE produces higher $R_{unk}$ or fails on round-trip detokenization.
3. SAGE shows zero measurable difference in boundary alignment compared to standard Unigram at the same vocabulary size.
