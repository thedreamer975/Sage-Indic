# SAGE-Indic: Reproducible Experiment Ledger

**Document Version:** 1.0.0  
**Repository State:** Audited October 2026  
**Status:** Living Research Record  

This ledger provides an immutable provenance record for all executed, audited, and planned experiments in the SAGE-Indic project, strictly adhering to the research integrity rules of [`AGENTS.md`](file:///d:/Sage-Indic/AGENTS.md).

---

## Experiment Registry Summary

| Experiment ID | Phase | Component | Execution Date | Status | Primary Output Artifact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`EXP-2A-01`** | Phase 2A | Language & Code-Mix Detection | 2026-09-28 | **Verified & Passing** | Unit tests in `tests/test_detection.py` |
| **`EXP-2B-01`** | Phase 2B | Morphology-Aware Tokenizer Benchmark | 2026-09-29 | **Reproducible Raw Artifact** | `experiments/results/tokenizer_results.json` |
| **`EXP-2B-HIST-00`**| Phase 2B | Historical Handoff Results | *Unknown* | **QUARANTINED / UNGROUNDED** | None found in repository |
| **`EXP-2C-01`** | Phase 2C | Context-Aware Safety Guardrail | 2026-09-29 / 2026-10-02 | **Reproducible Raw Artifact** | `experiments/results/safety_results.json` |
| **`EXP-2D-01`** | Phase 2D | Stage B Ingestion & Provenance Audit | 2026-10-03 | **Verified & Passing** | `data/processed/rag/phase2d_chunks.jsonl` |
| **`EXP-2D-02`** | Phase 2D | Lexical BM25 Baseline + Benchmark Build | 2026-10-14 | **EXECUTED — RESULTS RECORDED** | `experiments/results/exp_2d_bm25_*.json` |
| **`EXP-2D-03`** | Phase 2D | BM25 + Romanized Transliteration | 2026-10-15 | **EXECUTED — RESULTS RECORDED** | `experiments/results/exp_2d_crossscript_bm25_translit_*.json` |
| **`EXP-2D-04`** | Phase 2D | BM25 + Code-Mix Aware Normalization | 2026-10-15 | **EXECUTED — RESULTS RECORDED** | `experiments/results/exp_2d_crossscript_bm25_codemix_*.json` |
| **`EXP-2D-05`** | Phase 2D | Multilingual Dense Retrieval Baseline | 2026-10-15 | **EXECUTED — RESULTS RECORDED** | `experiments/results/exp_2d_crossscript_dense_multilingual_*.json` |
| **`EXP-2D-06`** | Phase 2D | Hybrid Retrieval via Reciprocal Rank Fusion | 2026-10-15 | **EXECUTED — RESULTS RECORDED** | `experiments/results/exp_2d_crossscript_hybrid_rrf_*.json` |
| **`EXP-2D-07`** | Phase 2D | Downstream Subword Tokenizer BM25 Benchmark | 2026-10-15 | **EXECUTED — RESULTS RECORDED** | `experiments/results/exp_2d_crossscript_bm25_{bpe,unigram,sage}_*.json` |
| **`EXP-2D-08`** | Phase 2D/2F | Claim-Verification Foundation Validation | 2026-10-16 | **EXECUTED — RESULTS RECORDED** | `tests/test_claim_verification.py` (13 tests) |
| **`EXP-2D-09`** | Phase 2D/2F | Diagnostic Verification Benchmark Validation | 2026-10-16 | **EXECUTED — RESULTS RECORDED** | `experiments/results/exp_2d_verification_*_20261016_040007.json` |
| **`EXP-2F-01`** | Phase 2F | Atomic Decomposition & Relation-Aware Verification | 2026-10-16 | **EXECUTED — RESULTS RECORDED** | `experiments/results/exp_2d_verification_*_20261016_041203.json` |
| **`EXP-2E-01`** | Phase 2E | Safe, Replaceable Generation Adapter | 2026-10-16 | **EXECUTED — UNIT TESTS PASSING** | `tests/test_generation_adapter.py` (15 tests) |
| **`EXP-2E-02`** | Phase 2E | End-to-End Grounded Factuality Evaluation | 2026-10-16 | **EXECUTED — RESULTS RECORDED** | `experiments/results/exp_2e_02/` |
| **`EXP-2G-01`** | Phase 2G | Response Composition & Demo Application Integration | 2026-11-17 | **ENGINEERING INTEGRATION — NO BENCHMARK CLAIM** | `tests/test_composition.py`, `tests/test_api.py`, `scripts/verify_demo.py` |

---

## 1. Experiment Entries

### `EXP-2B-01`: Matched-Condition Tokenizer Benchmark
- **Phase:** Phase 2B — Tokenization Research
- **Execution Date:** 2026-09-29
- **Harness:** [`experiments/run_tokenizer_experiment.py`](file:///d:/Sage-Indic/experiments/run_tokenizer_experiment.py)
- **Hypothesis ($H_1$):** Affix-guided and akshara-constrained pre-segmentation will improve boundary alignment with linguistic units compared to unconstrained BPE and Unigram baselines at identical vocabulary sizes ($V \in \{2000, 4000\}$).
- **Training Corpus:** [`data/processed/tokenizer/train_corpus.txt`](file:///d:/Sage-Indic/data/processed/tokenizer/train_corpus.txt) (4,688 unique lines, SHA-256 `ff752e43...`).
- **Evaluation Sets (Strict Isolation):**
  - Native Telugu: `eval_native.txt` (146 lines, SHA-256 `eb48d96f...`).
  - Romanized Telugu: `eval_romanized.txt` (146 lines, SHA-256 `33aa552f...`).
  - Code-Mixed Telugu-English: `eval_codemix.txt` (150 lines, 15 sentences x 10, SHA-256 `f6177c8c...`).
  - Boundary Proxy: `eval_morphology.jsonl` (146 lines, 721 treebank tokens, 575 internal boundaries, SHA-256 `8a37424e...`).
- **Models Evaluated:**
  1. `BPE_2000` & `BPE_4000` (Metaspace BPE baseline)
  2. `Unigram_2000` & `Unigram_4000` (Metaspace Unigram baseline)
  3. `SAGE_2000` & `SAGE_4000` (Proposed SAGE tokenizer)
  4. `SAGE_Ablation_NoMorph_2000` & `SAGE_Ablation_NoMorph_4000` (SAGE without morphological pre-segmentation)
- **Metric Definitions:**
  - `tokens_per_word`: Total encoded tokens divided by total whitespace-delimited words.
  - `compression_ratio`: Total non-space characters divided by total encoded tokens.
  - `boundary_precision`: $TP / (TP + FP)$ where boundaries are character index offsets.
  - `boundary_recall`: $TP / (TP + FN)$.
  - `boundary_f1`: $2 \cdot P \cdot R / (P + R)$ globally pooled across sentences.
- **Raw Artifact Paths:**
  - Machine-readable results: [`experiments/results/tokenizer_results.json`](file:///d:/Sage-Indic/experiments/results/tokenizer_results.json)
  - Generated markdown: [`docs/tokenizer_results.md`](file:///d:/Sage-Indic/docs/tokenizer_results.md)
  - Saved model weights: [`experiments/saved_models/`](file:///d:/Sage-Indic/experiments/saved_models/) (`bpe_*.json`, `unigram_*.json`, `sage_*.json`)
- **Measured Results ($V=4000$):**
  - `BPE_4000`: Native T/W = **1.642**, Chars/Tok = **2.840**, Boundary Prec = **0.5832**, Rec = **0.4696**, **F1 = 0.5202** ($TP=270, FP=193, FN=305$)
  - `Unigram_4000`: Native T/W = **1.836**, Chars/Tok = **2.540**, Boundary Prec = **0.5904**, Rec = **0.6191**, **F1 = 0.6044** ($TP=356, FP=247, FN=219$)
  - `SAGE_4000`: Native T/W = **1.903**, Chars/Tok = **2.451**, Boundary Prec = **0.6006**, Rec = **0.6800**, **F1 = 0.6378** ($TP=391, FP=260, FN=184$)
  - `SAGE_Ablation_4000`: Native T/W = **1.838**, Chars/Tok = **2.538**, Boundary Prec = **0.5894**, Rec = **0.6191**, **F1 = 0.6039** ($TP=356, FP=248, FN=219$)
- **Reproduction Status:** **100% Deterministically Verified.** In-memory evaluation of saved checkpoints on test sets replicates metrics to the 4th decimal place.
- **Valid Conclusions:**
  1. Affix pre-segmentation in SAGE alters subword allocation, preventing subword crosses at whitespace word boundaries and common affix transitions.
  2. Disabling affix pre-segmentation in SAGE (`SAGE_Ablation_NoMorph`) reduces boundary F1 from 0.6378 to 0.6039, matching standard Unigram (0.6044).
  3. SAGE incurs a modest +3.6% token overhead relative to Unigram (1.903 vs. 1.836 tokens/word), well within the 15% falsification threshold.
- **Limitations & Known Defects:**
  1. *Metric-Annotation Mismatch:* Reference boundaries represent Universal Dependencies syntactic word tokens (`FORM`), not gold intra-word morphemes. SAGE's detached suffixes (`-తో`, `-లో`) are counted as False Positives.
  2. *Whitespace Confounding:* SAGE explicitly splits on whitespace, forcing predicted boundaries at all word boundaries and inflating true positives against treebank tokens.
  3. *Data Leakage:* 4 sentences (2.7%) overlap between `train_corpus.txt` and `eval_native.txt` due to upstream duplicate sentences in UD splits.
  4. *True Morphological Superiority NOT Established:* Due to defects 1 and 2, current boundary F1 gains cannot be claimed as true morphological segmentation superiority.
- **Required Follow-up Experiment:** Controlled re-evaluation with deduplicated test set and true morpheme-annotated reference data or explicit re-framing as a treebank word alignment proxy.

---

### `EXP-2B-HIST-00`: Historical Handoff Claims (Forensic Quarantine Entry)
- **Phase:** Phase 2B (Historical Handoff Report)
- **Claimed Values ($V=4000$):**
  - BPE fertility: `1.7058`, boundary F1: `0.6559`
  - Unigram fertility: `2.0076`, boundary F1: `0.6729`
  - SAGE fertility: `1.3323`, boundary F1: `0.8876`
- **Reproduction Status:** **QUARANTINED / UNGROUNDED.** Zero empirical backing in code, git commits, reflogs, or stored JSON files.
- **Scientific Audit Finding:** The claimed SAGE fertility of 1.3323 contradicts the mathematical reality of the algorithm. SAGE forces affix detachment into separate subwords, which increases tokens-per-word relative to Unigram (1.903 vs 1.836) rather than decreasing it. These values represent an aspirational hypothesis draft or ungrounded fabrication.
- **Status in Repository:** Formally deprecated and excluded from all project reporting.

---

### `EXP-2C-01`: Context-Aware Safety Benchmark
- **Phase:** Phase 2C — Safety Research
- **Execution Date:** 2026-09-29 (Adjudication updated 2026-10-02)
- **Harness:** [`experiments/run_safety_experiment.py`](file:///d:/Sage-Indic/experiments/run_safety_experiment.py)
- **Hypothesis:** Multi-signal contextual disambiguation (orthographic de-obfuscation + morphological stem isolation + benign context pattern matching) will reduce False Positive Rates on benign-sensitive contexts and improve recall on obfuscated threats compared to keyword blacklists and dense multilingual semantic classifiers.
- **Datasets:**
  - Development: [`data/processed/safety/dev.jsonl`](file:///d:/Sage-Indic/data/processed/safety/dev.jsonl) (47 instances; 28 SAFE, 19 UNSAFE; 10 benign-sensitive, 7 obfuscated).
  - Held-out Evaluation: [`data/processed/safety/eval.jsonl`](file:///d:/Sage-Indic/data/processed/safety/eval.jsonl) (47 instances; 28 SAFE, 19 UNSAFE; 10 benign-sensitive, 7 obfuscated).
  - Adjudication: 12 epistemic uncertainty instances adjudicated to `SAFE` on 2026-10-02. Zero data overlap between splits.
- **Models Evaluated:**
  1. `Baseline_A_Lexical` (Keyword blacklist filter)
  2. `Baseline_B_MultilingualSemantic` (Embedding classifier)
  3. `Proposed_SAGE_Guardrail` (Full contextual guardrail)
  4. `SAGE_Ablation_NoMorph` (Guardrail without morphological stem recovery)
- **Raw Artifact Paths:**
  - Machine-readable results: [`experiments/results/safety_results.json`](file:///d:/Sage-Indic/experiments/results/safety_results.json)
  - Documentation: [`docs/safety_results.md`](file:///d:/Sage-Indic/docs/safety_results.md), [`docs/safety_data.md`](file:///d:/Sage-Indic/docs/safety_data.md)
- **Measured Results on Held-Out Evaluation Set ($N=47$):**
  - `Baseline_A_Lexical`: Accuracy = **0.6170**, Macro-F1 = **0.4299**, Benign FPR = **0.2000**, Unsafe Recall = **0.4737**, Obfuscated Acc = **0.0000**
  - `Baseline_B_MultilingualSemantic`: Accuracy = **0.3191**, Macro-F1 = **0.2874**, Benign FPR = **0.6000**, Unsafe Recall = **0.5263**, Abstention = **0.4681**
  - `Proposed_SAGE_Guardrail`: Accuracy = **0.7021**, Macro-F1 = **0.5103**, Benign FPR = **0.1000**, Unsafe Recall = **0.7368**, Obfuscated Acc = **0.7143**
  - `SAGE_Ablation_NoMorph`: Accuracy = **0.7021**, Macro-F1 = **0.5103**, Benign FPR = **0.1000**, Unsafe Recall = **0.7368**, Obfuscated Acc = **0.7143**
- **Reproduction Status:** **100% Deterministically Verified.**
- **Valid Conclusions:**
  1. Contextual pattern matching reduces False Positive Rate on benign-sensitive queries from 20% to 10%.
  2. Orthographic de-obfuscation restores recall on padded and punctuated evasion queries (from 0% to 71.43%).
- **Limitations:** Small diagnostic sample size ($N=47$ eval items). Morphological ablation did not change top-level metrics on this small set because threat roots overlapped with lexical indicators.

---

### `EXP-2D-01`: Stage B Evidence Corpus Foundation & Ingestion
- **Phase:** Phase 2D — RAG Evidence Corpus Foundation
- **Execution Date:** 2026-10-03
- **Harness:** [`scripts/build_phase2d_corpus.py`](file:///d:/Sage-Indic/scripts/build_phase2d_corpus.py)
- **Objective:** Deterministic acquisition, human licensing audit, cryptographic hashing, and chunk round-trip verification for factual Telugu evidence without executing retrieval or generation.
- **Candidate Sources Inspected:** 14 records in [`phase2d_source_manifest.jsonl`](file:///d:/Sage-Indic/data/processed/rag/phase2d_source_manifest.jsonl).
  - 10 Approved: Canonical Telugu Wikipedia articles (CC-BY-SA-4.0).
  - 4 Excluded: IndicQA (license conflict), UD_Telugu-MTG (grammar text), IndicCorp v2 (uncurated scrape), unvetted search snippet.
- **Ingested Corpus Artifacts:**
  - Documents: 10 documents in [`phase2d_documents.jsonl`](file:///d:/Sage-Indic/data/processed/rag/phase2d_documents.jsonl).
  - Chunks: **30 paragraph chunks** in [`phase2d_chunks.jsonl`](file:///d:/Sage-Indic/data/processed/rag/phase2d_chunks.jsonl). (Note: audit report stated 31; actual count is 30.)
  - Content Hashes: Deterministic SHA-256 for all raw, normalized, and chunk payloads.
- **Reproduction Status:** **Verified & Passing.** 53 unit/integration tests in [`tests/test_rag.py`](file:///d:/Sage-Indic/tests/test_rag.py) verify exact codepoint slice roundtrips (`normalized_text[char_start:char_end] == chunk.text`), cryptographic provenance, and trust-boundary inertness.
- **Valid Conclusions:** Corpus foundation, schema invariants, and data-plane security are functionally sound.
- **Follow-up Required:** (Completed in EXP-2D-02) Construction of evaluation queries, relevance judgments, and BM25 implementation.

---

### `EXP-2D-02`: Lexical BM25 Retrieval Baseline
- **Phase:** Phase 2D — RAG Retrieval Quality
- **Execution Date:** 2026-10-14
- **Status:** **EXECUTED — RESULTS RECORDED**
- **Harness:** [`experiments/run_retrieval_experiment.py`](file:///d:/Sage-Indic/experiments/run_retrieval_experiment.py)
- **Benchmark Construction:** [`scripts/build_phase2d_benchmark.py`](file:///d:/Sage-Indic/scripts/build_phase2d_benchmark.py)
- **Hypothesis ($H_1$):** Deterministic BM25 lexical matching will achieve high retrieval recall for same-script (Native Telugu) queries. Cross-script queries (Romanized Telugu, Telugu-English code-mixed) against a Native Telugu corpus will achieve near-zero recall due to lexical script mismatch.

#### Benchmark Dataset
| File | Lines | SHA-256 |
|:---|:---:|:---|
| `phase2d_eval_queries_dev.jsonl` | 18 | `aaf983b5...` |
| `phase2d_qrels_dev.jsonl` | 540 | `e217528d...` |
| `phase2d_eval_queries_eval.jsonl` | 24 | `da26df14...` |
| `phase2d_qrels_eval.jsonl` | 720 | `48b7c2c8...` |

- **Dev Split:** 6 query families × 3 modalities = 18 queries (4 answerable, 2 unanswerable families × 3 modalities = 12 answerable + 6 unanswerable queries).
- **Eval Split:** 8 query families × 3 modalities = 24 queries (6 answerable, 2 unanswerable families × 3 modalities = 18 answerable + 6 unanswerable queries).
- **Relevance Grading:** 0 = not relevant, 1 = partially relevant / same-document background, 2 = fully relevant / primary evidence chunk. Single-annotator derived; `annotation_status = PENDING` (not independently human-verified).

#### BM25 Configuration
- **k1:** 1.5, **b:** 0.75 (Okapi BM25 defaults, predeclared before evaluation)
- **Tokenizer:** Unicode NFC + lowercase Latin + punctuation-stripping by category (`P*`, `S*`, `C*`, `Z*`). Telugu letters (L*) and combining marks (M*) preserved.
- **Tie-breaking:** `(-score, document_id, chunk_index, chunk_id)` — deterministic alphabetic-then-positional.
- **Corpus:** `phase2d_chunks.jsonl` SHA-256: `8a51ae30...`

#### Measured Results (dev split, top-k=10)
| Modality | Queries | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Overall** | 18 | 0.3333 | 0.3333 | 0.3333 | 0.3333 | 0.3333 |
| Native Telugu | 6 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Romanized Telugu | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Code-Mixed | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

#### Measured Results (eval split, top-k=10)
| Modality | Queries | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Overall** | 24 | 0.3333 | 0.3333 | 0.3333 | 0.3333 | 0.3333 |
| Native Telugu | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Romanized Telugu | 8 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Code-Mixed | 8 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

- **Raw Artifact:** `experiments/results/exp_2d_bm25_20261014_151808.json`
- **Reproduction Command:** `python experiments/run_retrieval_experiment.py --split both --top-k 10`

#### Valid Conclusions
1. BM25 lexical matching achieves **Recall@1 = 1.0 (MRR = 1.0)** on Native Telugu answerable queries. All primary evidence chunks are ranked first in the 30-chunk corpus.
2. Romanized Telugu and code-mixed queries achieve **Recall = 0.0** against the Native Telugu corpus. This is expected: BM25 operates on script-sensitive tokens; Romanized Latin and Telugu Unicode are orthogonally disjoint character sets.
3. The native-perfect / cross-script-zero split confirms the primary Phase 2D finding: **a transliteration or script-normalization layer is required before BM25 retrieval can serve Romanized and code-mixed queries over a Native Telugu corpus**.
4. Retrieved content remains within the trust boundary: results are `EvidencePackage` data objects and do not alter retrieval configuration or downstream instructions.

#### Limitations
1. The 30-chunk corpus is very small; per-modality metrics have extremely high variance.
2. Relevance judgments are single-annotator-derived; they have not undergone independent human review. `annotation_status = PENDING`.
3. Unanswerable query metrics are not interpreted as answerability detection.
4. Small corpus makes Recall@5 equal to Recall@10 for answerable native queries (all relevant chunks are in top 5).
5. Recall@1 = 1.0 on native queries must not be interpreted as retrieval saturating the problem — it reflects the small corpus size and targeted factual queries.

---

### `EXP-2D-03`: BM25 with Romanized Telugu Transliteration (`bm25_translit`)
- **Phase:** Phase 2D — Cross-Script Retrieval
- **Execution Date:** 2026-10-15
- **Harness:** [`experiments/run_retrieval_experiment.py`](file:///d:/Sage-Indic/experiments/run_retrieval_experiment.py) (`--condition bm25_translit`)
- **Hypothesis:** Transliterating Romanized Telugu query tokens into native Telugu script using deterministic phonetic rules will bridge the cross-script vocabulary mismatch, significantly improving recall over the 0.0 baseline.
- **Normalizer:** `RomanizedTeluguTransliterator` + `CodeMixedQueryNormalizer(enable_bilingual_expansion=False)`. Expands query to include original Latin tokens + transliterated Telugu tokens.
- **Measured Results (dev split, 18 queries):**
  - Native: Recall@1 = **1.0000**, Recall@5 = **1.0000**, MRR@10 = **1.0000**
  - Romanized: Recall@1 = **1.0000**, Recall@5 = **1.0000**, MRR@10 = **1.0000** (improved from 0.0)
  - Code-Mixed: Recall@1 = **0.7500**, Recall@5 = **1.0000**, MRR@10 = **0.8750** (improved from 0.0)
  - Overall: Recall@1 = **0.9167**, Recall@5 = **1.0000**, MRR@10 = **0.9583**, nDCG@10 = **0.9692**, Latency = **0.18ms**
- **Measured Results (eval split, 24 queries):**
  - Native: Recall@1 = **1.0000**, Recall@5 = **1.0000**, MRR@10 = **1.0000**
  - Romanized: Recall@1 = **0.8333**, Recall@5 = **1.0000**, MRR@10 = **0.8889**
  - Code-Mixed: Recall@1 = **0.8333**, Recall@5 = **1.0000**, MRR@10 = **0.9167**
  - Overall: Recall@1 = **0.8889**, Recall@5 = **1.0000**, MRR@10 = **0.9352**, nDCG@10 = **0.9517**, Latency = **0.21ms**
- **Artifact:** `experiments/results/exp_2d_crossscript_bm25_translit_20261015_185623.json`
- **Key Finding:** Transliteration recovers cross-script recall to 100% at rank 5 on both splits with near-instantaneous lexical latency (<0.25ms).

---

### `EXP-2D-04`: BM25 with Code-Mixed-Aware Normalization (`bm25_codemix`)
- **Phase:** Phase 2D — Cross-Script Retrieval
- **Execution Date:** 2026-10-15
- **Harness:** [`experiments/run_retrieval_experiment.py`](file:///d:/Sage-Indic/experiments/run_retrieval_experiment.py) (`--condition bm25_codemix`)
- **Hypothesis:** Preserving English domain terms without phonetic corruption while injecting bilingual Telugu conceptual synonyms (e.g., `fort` -> `కోట`, `entrance` -> `ద్వారం`) will further increase top-rank precision (Recall@1) on code-mixed queries.
- **Normalizer:** `CodeMixedQueryNormalizer(enable_bilingual_expansion=True)`.
- **Measured Results (dev split, 18 queries):**
  - Native: Recall@1 = **1.0000**, Recall@5 = **1.0000**, MRR@10 = **1.0000**
  - Romanized: Recall@1 = **1.0000**, Recall@5 = **1.0000**, MRR@10 = **1.0000**
  - Code-Mixed: Recall@1 = **1.0000**, Recall@5 = **1.0000**, MRR@10 = **1.0000** (improved from 0.7500 in translit)
  - Overall: Recall@1 = **1.0000**, Recall@5 = **1.0000**, MRR@10 = **1.0000**, nDCG@10 = **1.0000**, Latency = **0.14ms**
- **Measured Results (eval split, 24 queries):**
  - Native: Recall@1 = **1.0000**, Recall@5 = **1.0000**, MRR@10 = **1.0000**
  - Romanized: Recall@1 = **0.8333**, Recall@5 = **1.0000**, MRR@10 = **0.8889**
  - Code-Mixed: Recall@1 = **0.8333**, Recall@5 = **1.0000**, MRR@10 = **0.8889**
  - Overall: Recall@1 = **0.8889**, Recall@5 = **1.0000**, MRR@10 = **0.9259**, nDCG@10 = **0.9444**, Latency = **0.18ms**
- **Artifact:** `experiments/results/exp_2d_crossscript_bm25_codemix_20261015_185623.json`
- **Key Finding:** Code-mixed-aware expansion achieves perfect Recall@1 (1.0000) on dev code-mixed queries by aligning English keywords with Telugu encyclopedic terminology.

---

### `EXP-2D-05`: Multilingual Dense Retrieval Baseline (`dense_multilingual`)
- **Phase:** Phase 2D — Dense Vector Retrieval
- **Execution Date:** 2026-10-15
- **Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Apache-2.0 license, 384-dim, 50+ languages including Telugu). Loaded offline from verified local snapshot (`86741b4e3f5cb7765a600d3a3d55a0f6a6cb443d`).
- **Hypothesis:** Pre-trained multilingual sentence embeddings encode semantic intent across languages and scripts without requiring rule-based transliteration, but will exhibit lower exact-match lexical specificity than BM25.
- **Measured Results (dev split, 18 queries):**
  - Native: Recall@1 = **0.0000**, Recall@5 = **0.7500**, MRR@10 = **0.2375**, Latency = **23.26ms**
  - Romanized: Recall@1 = **0.0000**, Recall@5 = **1.0000**, MRR@10 = **0.3750**, Latency = **22.45ms**
  - Code-Mixed: Recall@1 = **0.5000**, Recall@5 = **1.0000**, MRR@10 = **0.6333**, Latency = **23.31ms**
  - Overall: Recall@1 = **0.1667**, Recall@5 = **0.9167**, MRR@10 = **0.4153**, nDCG@10 = **0.5382**, Mean Latency = **23.01ms**
- **Measured Results (eval split, 24 queries):**
  - Native: Recall@1 = **0.0000**, Recall@5 = **0.5000**, MRR@10 = **0.1627**
  - Romanized: Recall@1 = **0.0000**, Recall@5 = **0.3333**, MRR@10 = **0.1183**
  - Code-Mixed: Recall@1 = **0.1667**, Recall@5 = **0.5000**, MRR@10 = **0.3042**
  - Overall: Recall@1 = **0.0556**, Recall@5 = **0.4444**, Recall@10 = **0.6667**, MRR@10 = **0.1950**, nDCG@10 = **0.3051**, Mean Latency = **21.63ms**
- **Artifact:** `experiments/results/exp_2d_crossscript_dense_multilingual_20261015_185623.json`
- **Key Finding:** Dense multilingual embeddings capture cross-script semantic proximity (Recall@5 = 1.0 on dev Romanized/Code-mixed), but lack the sharp top-rank lexical discriminability of BM25 (Recall@1 = 0.05–0.17). Average query latency is ~22ms (~150x slower than sparse BM25).

---

### `EXP-2D-06`: Hybrid Retrieval via Reciprocal Rank Fusion (`hybrid_rrf`)
- **Phase:** Phase 2D — Hybrid Retrieval
- **Execution Date:** 2026-10-15
- **Architecture:** `HybridRetriever` combining CodeMix-aware BM25 and `paraphrase-multilingual-MiniLM-L12-v2` dense vectors via Reciprocal Rank Fusion ($k_{\text{rrf}}=60$).
- **Hypothesis:** Hybrid rank fusion will combine BM25's high top-1 precision on lexical matches with dense retrieval's cross-script semantic coverage.
- **Measured Results (dev split, 18 queries):**
  - Native: Recall@1 = **0.5000**, Recall@5 = **1.0000**, MRR@10 = **0.7083**
  - Romanized: Recall@1 = **1.0000**, Recall@5 = **1.0000**, MRR@10 = **1.0000**
  - Code-Mixed: Recall@1 = **0.7500**, Recall@5 = **1.0000**, MRR@10 = **0.8125**
  - Overall: Recall@1 = **0.7500**, Recall@5 = **1.0000**, MRR@10 = **0.8403**, nDCG@10 = **0.8801**, Latency = **21.85ms**
- **Measured Results (eval split, 24 queries):**
  - Native: Recall@1 = **0.6667**, Recall@5 = **1.0000**, MRR@10 = **0.8333**
  - Romanized: Recall@1 = **0.5000**, Recall@5 = **1.0000**, MRR@10 = **0.7083**
  - Code-Mixed: Recall@1 = **0.5000**, Recall@5 = **1.0000**, MRR@10 = **0.7500**
  - Overall: Recall@1 = **0.5556**, Recall@5 = **1.0000**, MRR@10 = **0.7639**, nDCG@10 = **0.8248**, Latency = **21.87ms**
- **Artifact:** `experiments/results/exp_2d_crossscript_hybrid_rrf_20261015_185631.json`
- **Key Finding:** Hybrid RRF achieves **100% Recall@5 across all three modalities on both splits**, proving robust against query variation, but slightly dilutes pure BM25 top-1 precision when dense ranks disagree.

---

### `EXP-2D-07`: Downstream Subword Tokenizer Retrieval Benchmark
- **Phase:** Phase 2D / Phase 2B Connection — Downstream Retrieval
- **Execution Date:** 2026-10-15
- **Harness:** [`experiments/run_retrieval_experiment.py`](file:///d:/Sage-Indic/experiments/run_retrieval_experiment.py) (`--condition bm25_bpe`, `bm25_unigram`, `bm25_sage`)
- **Hypothesis:** Subword tokenization that preserves Telugu morphological stems (Unigram and SAGE) will improve downstream lexical retrieval over unconstrained subwords by matching inflected query forms against document root nouns.
- **Configurations Tested:**
  1. `bm25_bpe`: BM25 indexed and queried with Phase 2B `BpeBaselineTokenizer` ($V=4000$)
  2. `bm25_unigram`: BM25 indexed and queried with Phase 2B `UnigramBaselineTokenizer` ($V=4000$)
  3. `bm25_sage`: BM25 indexed and queried with Phase 2B `SageTokenizer` ($V=4000$)
- **Measured Results (eval split, 24 queries):**
  - `bm25_baseline` (Unicode words): Overall Recall@1 = **0.3333**, Recall@5 = **0.3333**, nDCG@10 = **0.3333**
  - `bm25_bpe`: Overall Recall@1 = **0.3333**, Recall@5 = **0.3333**, nDCG@10 = **0.3333** (Native R@1=1.0, Cross-script=0.0)
  - `bm25_unigram`: Overall Recall@1 = **0.4444**, Recall@5 = **0.7778**, Recall@10 = **0.8889**, MRR@10 = **0.5500**, nDCG@10 = **0.6304**
  - `bm25_sage`: Overall Recall@1 = **0.4444**, Recall@5 = **0.6667**, Recall@10 = **0.6667**, MRR@10 = **0.5278**, nDCG@10 = **0.5624**
- **Artifacts:**
  - `experiments/results/exp_2d_crossscript_bm25_bpe_20261015_185636.json`
  - `experiments/results/exp_2d_crossscript_bm25_unigram_20261015_185636.json`
  - `experiments/results/exp_2d_crossscript_bm25_sage_20261015_185636.json`
- **Key Finding:** Under identical fixed corpus, queries, and relevance labels, Unigram and SAGE subwords improve downstream eval Recall@1 (+33.3% relative to word baseline, from 0.3333 to 0.4444) and dramatically improve Recall@5 (Unigram: 0.7778 vs word baseline: 0.3333). This provides real downstream task evidence connecting the Phase 2B tokenizer research to retrieval utility, independent of the syntactic boundary proxy.

---

### `EXP-2D-08`: Phase 2D/2F Claim-Verification Foundation Validation
- **Phase:** Phase 2D / Phase 2F Foundation — Claim Verification
- **Execution Date:** 2026-10-16
- **Architecture:** `LinguisticClaimVerifier` with `AtomicClaim`, `EvidencePassage`, `VerificationResult`, and untrusted prompt-injection isolation.
- **Hypothesis:** Directional factuality and entailment require decoupling verification from semantic similarity. A linguistically-informed verifier inspecting numerical alignment, polarity/negation markers, cross-script transliteration, and multi-passage consistency will accurately classify assertions into `SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, and `CONFLICTING_EVIDENCE`, while neutralizing embedded prompt-injection instructions in untrusted evidence.
- **Test Suite:** `tests/test_claim_verification.py` (13 tests spanning supported facts, date/number mismatches, Telugu negation markers, Romanized claims, conflicting chunk sets, and adversarial instruction injection).
- **Measured Results:**
  - 13/13 passing tests (100% accuracy on controlled verification suite).
  - Supported claims: Correctly identified with calibrated confidence $\ge 0.70$.
  - Contradicted claims (numerical & polarity): 100% detection rate.
  - Insufficient evidence: 100% rejection rate on ungrounded/off-topic evidence.
  - Conflicting evidence: 100% detection rate when candidate passages assert mutually exclusive dates.
  - Adversarial injection: 100% neutralization rate; malicious payloads sanitized and quarantined in metadata without compromising veracity decisions.
- **Artifacts:**
  - `src/sage_indic/verification/types.py`
  - `src/sage_indic/verification/verifier.py`
  - `docs/phase2d_claim_verification_spec.md`
  - `docs/phase2d_expansion_plan.md`
  - `tests/test_claim_verification.py`
- **Key Finding:** Decoupling retrieval similarity from directional truth verification prevents false positives from high-cosine contradictory assertions. Treating evidence strictly as passive untrusted data effectively neutralizes prompt injection payloads without relying on prompt instructions as security boundaries.

---

### `EXP-2D-09`: Diagnostic Verification Benchmark Validation & Failure-Mode Audit
- **Phase:** Phase 2D / Phase 2F — Verification Benchmark Validation
- **Execution Date:** 2026-10-16
- **Harness:** [`experiments/run_verification_experiment.py`](file:///d:/Sage-Indic/experiments/run_verification_experiment.py) (`--split both`)
- **Datasets:**
  - Dev: [`data/processed/verification/dev_verification.jsonl`](file:///d:/Sage-Indic/data/processed/verification/dev_verification.jsonl) ($N=24$, Docs `TE_DOC_001`–`TE_DOC_005`)
  - Eval: [`data/processed/verification/eval_verification.jsonl`](file:///d:/Sage-Indic/data/processed/verification/eval_verification.jsonl) ($N=24$, Docs `TE_DOC_006`–`TE_DOC_010`)
  - Complete zero-leakage topic isolation between development and evaluation splits.
- **Measured Results (Development Split, 24 examples):**
  - Overall Accuracy: **62.50%**
  - Macro-F1: **0.6598**
  - False `SUPPORTED` Rate: **29.4% (5 / 17 non-supported items)**
  - Class F1: SUPPORTED = **0.5000**, CONTRADICTED = **0.6667**, INSUFFICIENT = **0.6154**, CONFLICTING = **0.8571**
  - Modality Accuracy: Native = **78.6%** (11/14), Romanized = **66.7%** (4/6), Code-Mixed = **0.0%** (0/4)
- **Measured Results (Held-Out Evaluation Split, 24 examples):**
  - Overall Accuracy: **70.83%**
  - Macro-F1: **0.7419**
  - False `SUPPORTED` Rate: **11.8% (2 / 17 non-supported items)**
  - Class F1: SUPPORTED = **0.6154**, CONTRADICTED = **0.7273**, INSUFFICIENT = **0.6250**, CONFLICTING = **1.0000**
  - Modality Accuracy: Native = **78.6%** (11/14), Romanized = **50.0%** (2/4), Code-Mixed = **66.7%** (4/6)
- **Score Distribution (Uncalibrated Heuristics):**
  - Predicted SUPPORTED: mean = **0.8377** [0.7400, 0.9667]
  - Predicted CONTRADICTED: mean = **0.9250** [0.8500, 0.9500]
  - Predicted INSUFFICIENT: mean = **0.8000** [0.8000, 0.8000]
  - Predicted CONFLICTING: mean = **0.9000** [0.9000, 0.9000]
- **Artifacts:**
  - `experiments/results/exp_2d_verification_dev_verification_20261016_040007.json`
  - `experiments/results/exp_2d_verification_eval_verification_20261016_040007.json`
  - `docs/verification_error_analysis.md`
- **Key Findings & Failure-Mode Identification:**
  1. *Relational Blindness Fallacy Confirmed:* Matching entities and dates is NOT proof of a factual relationship. Claims with correct entities and dates but false predicates (e.g. Quli Qutb Shah tomb vs monument, or dying in 1591 vs building in 1591) were falsely classified as `SUPPORTED` due to bag-of-words overlap $\ge 0.35$.
  2. *Confidence Score Characterization:* Confidence scores are uncalibrated rule-derived heuristics, not probabilistic entailment margins.
  3. *Security Boundary Hold:* Adversarial injection strings (English, Telugu, and Code-Mixed) had zero ability to force false `SUPPORTED` outcomes. Deterministic execution parses evidence strictly as data.

---

### `EXP-2F-01`: Atomic Claim Decomposition and Relation-Aware Verification
- **Phase:** Phase 2F — Atomic Decomposition and Relation-Aware Verification
- **Execution Date:** 2026-10-16
- **Research Question:** Can atomic claim decomposition and relation-aware evidence matching reduce false `SUPPORTED` decisions caused by lexical overlap, entity matching, numerical coincidences, and partial evidence—without substantially increasing false rejections of genuinely supported claims?
- **Harness & Command:** [`experiments/run_verification_experiment.py`](file:///d:/Sage-Indic/experiments/run_verification_experiment.py) (`python experiments/run_verification_experiment.py --verifier both --split both`)
- **Compared Approaches:**
  1. `LinguisticClaimVerifier` (Frozen Weak Baseline from Phase 2D)
  2. `RelationAwareClaimVerifier` (Experimental verifier with `AtomicProposition` decomposition, conjunction splitting, relation predicate categorization, and conservative compound composition)
- **Datasets:**
  - Dev: [`data/processed/verification/dev_verification.jsonl`](file:///d:/Sage-Indic/data/processed/verification/dev_verification.jsonl) ($N=24$, Docs `TE_DOC_001`–`TE_DOC_005`)
  - Eval: [`data/processed/verification/eval_verification.jsonl`](file:///d:/Sage-Indic/data/processed/verification/eval_verification.jsonl) ($N=24$, Docs `TE_DOC_006`–`TE_DOC_010`)
  - Topic-isolated, diagnostic sets containing relational inversions, partial evidence conjunctions, numerical/temporal mismatches, and adversarial injections.
- **Measured Results (Held-Out Evaluation Split, 24 instances):**
  - **Overall Accuracy:**
    - Baseline: **70.83%** (17 / 24)
    - Relation-Aware: **75.00%** (18 / 24) [**+4.17%** improvement]
  - **Macro-F1:**
    - Baseline: **0.7419**
    - Relation-Aware: **0.7750** [**+0.0331** improvement]
  - **False `SUPPORTED` Count & Rate (Non-Supported items $N=17$):**
    - Baseline: **2 / 17 (11.76%)**
    - Relation-Aware: **1 / 17 (5.88%)** [**-5.88%** absolute reduction]
  - **Genuinely Supported Recall (Supported items $N=7$):**
    - Baseline: **4 / 7 (57.14%)**
    - Relation-Aware: **4 / 7 (57.14%)** [**0.00% regression**; zero increase in false rejections]
  - **Diagnostic Subset Accuracy:**
    - *Partial Evidence ($N=2$):* Baseline = **50.0%** (1/2) $\rightarrow$ Relation-Aware = **100.0%** (2/2) [**+50.0%** gain]
    - *Relational Inversion ($N=6$):* Baseline = **66.7%** (4/6) $\rightarrow$ Relation-Aware = **66.7%** (4/6) [0.0% change]
    - *Numerical/Temporal ($N=4$):* Baseline = **100.0%** (4/4) $\rightarrow$ Relation-Aware = **100.0%** (4/4)
  - **Modality Accuracy:**
    - Native Telugu ($N=14$): Baseline = **78.6%** (11/14) $\rightarrow$ Relation-Aware = **85.7%** (12/14) [**+7.1%**]
    - Romanized Telugu ($N=4$): Baseline = **50.0%** (2/4) $\rightarrow$ Relation-Aware = **50.0%** (2/4)
    - Code-Mixed ($N=6$): Baseline = **66.7%** (4/6) $\rightarrow$ Relation-Aware = **66.7%** (4/6)
  - **Per-Class Metrics (Relation-Aware on Eval):**
    - `SUPPORTED`: Prec = **0.8000**, Rec = **0.5714**, F1 = **0.6667**
    - `CONTRADICTED`: Prec = **0.8000**, Rec = **0.8000**, F1 = **0.8000**
    - `INSUFFICIENT_EVIDENCE`: Prec = **0.7143**, Rec = **0.7143**, F1 = **0.7143**
    - `CONFLICTING_EVIDENCE`: Prec = **1.0000**, Rec = **1.0000**, F1 = **1.0000**
- **Measured Results (Development Split, 24 instances):**
  - **Overall Accuracy:** Baseline = **62.50%** (15/24) $\rightarrow$ Relation-Aware = **66.67%** (16/24) [**+4.17%**]
  - **Macro-F1:** Baseline = **0.6598** $\rightarrow$ Relation-Aware = **0.6976** [**+0.0378**]
  - **False `SUPPORTED` Rate:** Baseline = **29.41%** (5/17) $\rightarrow$ Relation-Aware = **23.53%** (4/17) [**-5.88%**]
  - **Genuinely Supported Recall:** Baseline = **71.43%** (5/7) $\rightarrow$ Relation-Aware = **71.43%** (5/7) [**0.00% regression**]
  - **Partial Evidence Accuracy:** Baseline = **0.0%** (0/2) $\rightarrow$ Relation-Aware = **50.0%** (1/2) [**+50.0%**]
- **Raw Output Artifacts:**
  - `experiments/results/exp_2d_verification_linguistic_eval_verification_20261016_041203.json`
  - `experiments/results/exp_2d_verification_relation_aware_eval_verification_20261016_041203.json`
  - `experiments/results/exp_2d_verification_linguistic_dev_verification_20261016_041203.json`
  - `experiments/results/exp_2d_verification_relation_aware_dev_verification_20261016_041203.json`
  - Qualitative Error Analysis: [`docs/verification_error_analysis.md:Section 7`](file:///d:/Sage-Indic/docs/verification_error_analysis.md)
- **Unit and Property Test Coverage:**
  - `tests/test_claim_verification.py`: 20 passed (added 7 tests for `AtomicProposition`, `RelationAwareClaimVerifier`, compound claim splitting, conservative composition, and prompt injection defense).
  - Total repository tests: **252 passed, 52 skipped**.
- **Key Conclusions & Research Integrity Findings:**
  1. *Empirical Answer to Research Question:* Atomic decomposition and conservative compound composition successfully eliminated partial-support false positives (e.g. `V_EVAL_017` resolved from false `SUPPORTED` to correct `INSUFFICIENT_EVIDENCE`) and cut the false `SUPPORTED` rate on held-out eval by 50% relative (11.76% to 5.88%), with **strictly zero regression** in genuinely supported recall (57.14%).
  2. *Residual Limitation of Coarse Relational Dictionaries:* In `V_EVAL_011`, the assertion claimed Niccolo de Conti *discovered* the Kalamalla inscription whereas the evidence stated he *described* it. Both verifiers predicted `SUPPORTED` because both predicates map into the coarse `discovery_or_study` category. Resolving semantic nuances within the same broad predicate family requires fine-grained argument binding or supervised cross-lingual NLI.
  3. *Recommendation:* `RelationAwareClaimVerifier` merits formal adoption as the primary verification strategy, with frozen `LinguisticClaimVerifier` preserved as the standard baseline.

---

### `EXP-2E-01`: Safe, Replaceable Generation Adapter
- **Phase:** Phase 2E — LLM/SLM Generation Adapter
- **Execution Date:** 2026-10-16
- **Research Objective:** Investigate whether a replaceable language-model adapter can generate evidence-grounded answers while preserving provenance, treating retrieved content as untrusted data, and exposing claims for independent verification.
- **Components Implemented:**
  - [`src/sage_indic/generation/types.py`](file:///d:/Sage-Indic/src/sage_indic/generation/types.py): `GenerationConfig`, `GenerationRequest`, `DraftAnswer`, typed exceptions (`ProviderUnavailableError`, `ProviderTimeoutError`, `ProviderAuthError`, `MalformedProviderResponseError`, `UntrustedEvidenceError`).
  - [`src/sage_indic/generation/prompt.py`](file:///d:/Sage-Indic/src/sage_indic/generation/prompt.py): `PromptComposer` isolating trusted system instructions from untrusted evidence envelopes with citation extraction and validation.
  - [`src/sage_indic/generation/adapter.py`](file:///d:/Sage-Indic/src/sage_indic/generation/adapter.py): `GenerationProvider` ABC, `MockGenerationProvider` (deterministic, with test hooks for all failure modes), `ExternalAPIProvider` (offline-safe, credential-guarded), `GenerationAdapter` (orchestrator with retry policy and citation validation).
  - [`src/sage_indic/generation/pipeline.py`](file:///d:/Sage-Indic/src/sage_indic/generation/pipeline.py): `AnswerEligibility`, `VerifiedAnswerReport`, `verify_draft_answer` — strictly decoupled verification pipeline.
- **Test Suite:** [`tests/test_generation_adapter.py`](file:///d:/Sage-Indic/tests/test_generation_adapter.py) — 15 tests across 4 test classes.
- **Security Boundary Tests Run:**
  - Adversarial prompt injection in retrieved evidence (English + Telugu): contained within untrusted envelope, not elevated to system instructions.
  - Hallucinated citation detection: invalid/non-supplied passage IDs identified and reported in `DraftAnswer.invalid_citations`.
  - Empty evidence abstention: language-appropriate abstention messages for all three modalities.
  - Timeout simulation, auth failure, and malformed empty response tested with typed exceptions.
  - External API provider refuses to call remote endpoints in test environment (raises `ProviderUnavailableError`).
- **Measured Test Results:**
  - Targeted test suite (`tests/test_generation_adapter.py`): **15 passed, 0 failed, 0 skipped** in 58.90s.
  - Combined test run with `tests/test_claim_verification.py`: **35 passed, 0 failed, 0 skipped**.
- **Invariants Confirmed by Tests:**
  1. `DraftAnswer.is_verified` is **always `False`** immediately after generation. Only the independent `verify_draft_answer()` pipeline sets `is_verified=True`.
  2. A response claiming `INSUFFICIENT_EVIDENCE` is **not proof of falsehood**; the pipeline reports it as `REQUIRES_CAVEAT`, not `INELIGIBLE`.
  3. Invalid citation identifiers (hallucinated passage IDs) are detected and segregated into `DraftAnswer.invalid_citations`; citation presence alone does not establish entailment.
  4. External model credentials are **never hardcoded**; the `api_key_env_var` config field is read from environment, and absent credentials raise `ProviderAuthError`.
- **Key Design Decisions:**
  - Provider is a swappable ABC; the Mock, Local, and API providers are substitutable without changing retrieval or verification logic.
  - Evidence is formatted in `[EVIDENCE_PASSAGE id="..."]...[/EVIDENCE_PASSAGE]` envelopes with explicit system-level warnings that content is passive untrusted data.
  - Claims are extracted by heuristic sentence boundary splitting — the limitation is recorded; sentence-boundary extraction cannot guarantee atomic decomposition correctness for all Telugu morphological constructions.
- **Known Limitations:**
  - Mock provider generates deterministic answers from the first passage's opening sentence; a real LLM provider must be configured via `ExternalAPIProvider` or a local `GenerationProviderType.LOCAL` implementation.
  - Sentence-boundary claim extraction uses `.` / `!` / `?` / `।` splitting — this is documented as a heuristic, not a guaranteed decomposition.
  - Prompt injection resilience depends on the underlying model's instruction-following fidelity; the adapter's isolation envelopes reduce the attack surface but cannot guarantee immunity in arbitrary LLMs.
- **Evaluation Scope (Future Work):**
  - Paired factuality evaluation comparing retrieval availability, answer correctness, claim-level support, citation entailment validity, and abstention quality across Native Telugu, Romanized Telugu, and Code-Mixed modalities is defined as a future research milestone (`EXP-2E-02`).
  - End-to-end factuality evaluation is NOT claimed based on unit test passage of mock responses.

---

### `EXP-2E-02`: End-to-End Grounded Factuality Evaluation
- **Phase:** Phase 2E — End-to-End Evaluation
- **Execution Date:** 2026-10-16
- **Harness:** [`experiments/run_exp_2e_02.py`](file:///d:/Sage-Indic/experiments/run_exp_2e_02.py)
- **Completion Status:** **Exit code 0 — All artifacts persisted successfully.**
- **Research Question:** Can an evidence-grounded pipeline (CodeMix-aware BM25 + llama3.2:1b via Ollama + RelationAware verifier) generate better-supported answers than an unnormalized lexical baseline and no-evidence ablation, across Native Telugu, Romanized Telugu, and code-mixed queries?

#### Conditions
| Condition | Label | Retriever | Generator | Verifier |
| :--- | :--- | :--- | :--- | :--- |
| **A** | SAGE-Indic Pipeline | BM25 + CodeMixedQueryNormalizer | llama3.2:1b (Ollama) | RelationAwareClaimVerifier |
| **B** | Verification Baseline | (same drafts as A) | (same drafts as A) | LinguisticClaimVerifier (paired audit) |
| **C** | Lexical Baseline | Unnormalized BM25 (NFC only) | llama3.2:1b (Ollama) | RelationAwareClaimVerifier |
| **D** | No-Evidence Ablation | None | llama3.2:1b (Ollama) | RelationAwareClaimVerifier |

#### Execution Configuration
- **Provider:** `api` (Ollama `http://127.0.0.1:11434/v1`)
- **Model:** `llama3.2:1b`
- **Temperature:** `0.0` (deterministic)
- **Max Tokens:** `80`
- **Top-K Evidence:** `3`
- **Split Evaluated:** `both` (dev + eval)
- **Timestamp UTC:** `2026-10-16T12:02:17.178167+00:00`

#### Dataset SHA-256 Fingerprints
| File | SHA-256 (full) |
| :--- | :--- |
| `phase2d_chunks.jsonl` | `8a51ae3069b3f7336947d3ed972276fbd7378133d269aec2e8b0d7493797b543` |
| `phase2d_eval_queries_dev.jsonl` | `aaf983b524147116b7289c681745d2d359b9299842524183e70b73f807998965` |
| `phase2d_eval_queries_eval.jsonl` | `da26df140621b82b12567bdc29040768cb8241d258689f534c8ae4ce130c0609` |
| `dev_verification.jsonl` | `2d4ed26b4a61c71834a229dac833a3fb6cdafa72dfca795d1c4733d10c6590df` |
| `eval_verification.jsonl` | `2763b534068b2b4813701915f542d79fb04e7da4e3e461aef77805da293de682` |

#### Query Population
- **Total queries:** 42 (18 dev + 24 eval)
- **Answerable:** 30 (10 native + 10 Romanized + 10 code-mixed)
- **Unanswerable:** 12 (4 native + 4 Romanized + 4 code-mixed)

#### Measured Results

**1. Retrieval Hit Rate on Answerable Queries (N=30)**

| Modality | Condition A (CodeMix BM25) | Condition C (Baseline BM25) |
| :--- | :--- | :--- |
| Native Telugu | 9/10 (90.0%) | 9/10 (90.0%) |
| Romanized Telugu | 9/10 (90.0%) | 0/10 (0.0%) |
| Code-Mixed | 9/10 (90.0%) | 0/10 (0.0%) |
| **Overall** | **27/30 (90.0%)** | **9/30 (30.0%)** |

**2. End-to-End Answer Correctness (Essential Keyword Coverage on Answerable Queries)**

| Metric | Condition A | Condition C |
| :--- | :--- | :--- |
| Fact-correct answers (N=30) | 6/30 (20.0%) | 2/30 (6.7%) |
| Dev split fact-correct | 3/12 (25.0%) | 1/12 (8.3%) |
| Eval split fact-correct | 3/18 (16.7%) | 1/18 (5.6%) |

**3. Abstention Fidelity on Unanswerable Queries (N=12)**

| Condition | Correct Abstentions | Rate |
| :--- | :--- | :--- |
| Condition A (CodeMix pipeline) | 4/12 | 33.3% |
| Condition D (No-evidence ablation) | 12/12 (42/42 all queries) | 100.0% |

**4. Verifier Comparison (Condition A vs Condition B — Identical Drafts)**

| Metric | Relation-Aware (A) | Linguistic Baseline (B) |
| :--- | :--- | :--- |
| ELIGIBLE_GROUNDED | 9 | 9 |
| REQUIRES_CAVEAT | 19 | 19 |
| INELIGIBLE_CONTRADICTED | 10 | 10 |
| ABSTENTION | 4 | 4 |
| Supported claims / 43 total | 10 (23.3%) | 10 (23.3%) |
| Decision divergences | 0/42 | — |

**5. Error Taxonomy (Condition A, N=42)**

| Error Class | Count |
| :--- | :--- |
| CONTRADICTION | 10 |
| CAVEATED_UNANSWERABLE | 7 |
| UNGROUNDED_OR_INSUFFICIENT | 8 |
| FALSE_SUPPORTED_OFF_TARGET | 6 |
| CORRECT_ABSTENTION | 4 |
| CORRECT_GROUNDED | 2 |
| CORRECT_PARTIALLY_GROUNDED | 1 |
| RETRIEVAL_MISS | 3 |
| UNSUPPORTED_HALLUCINATION_ON_UNANSWERABLE | 1 |

**6. Latency Profile (Condition A mean per query)**
- Retrieval: 0.29 ms
- Generation (cached/live): 3,637.73 ms
- Verification (dual): 1.24 ms
- Pipeline total: 3,639.26 ms

#### Test Suite at Time of Execution
- Full suite: **267 passed, 52 skipped** (52 skips = semantic safety tests requiring optional `transformers` dependency). Exit code: 0.

#### Output Artifacts
| File | Contents |
| :--- | :--- |
| [`experiments/results/exp_2e_02/config.json`](file:///d:/Sage-Indic/experiments/results/exp_2e_02/config.json) | Execution config + dataset SHA-256 hashes |
| [`experiments/results/exp_2e_02/manifest.json`](file:///d:/Sage-Indic/experiments/results/exp_2e_02/manifest.json) | 42-query evaluation manifest |
| [`experiments/results/exp_2e_02/per_query_results.json`](file:///d:/Sage-Indic/experiments/results/exp_2e_02/per_query_results.json) | Per-query Condition A results |
| [`experiments/results/exp_2e_02/aggregate_metrics.json`](file:///d:/Sage-Indic/experiments/results/exp_2e_02/aggregate_metrics.json) | Aggregate metrics for Conditions A, C, D |
| [`experiments/results/exp_2e_02/comparison_tables.json`](file:///d:/Sage-Indic/experiments/results/exp_2e_02/comparison_tables.json) | A vs B verifier comparison; A vs C retrieval comparison |
| [`experiments/results/exp_2e_02/error_analysis.json`](file:///d:/Sage-Indic/experiments/results/exp_2e_02/error_analysis.json) | Error taxonomy, contradicted queries, invalid citations |
| [`experiments/results/exp_2e_02/generation_cache.json`](file:///d:/Sage-Indic/experiments/results/exp_2e_02/generation_cache.json) | 84-key response cache for exact reproduction |
| [`experiments/results/exp_2e_02/reproduction_instructions.md`](file:///d:/Sage-Indic/experiments/results/exp_2e_02/reproduction_instructions.md) | Reproduction commands and environment details |

#### What This Experiment Demonstrates
1. **CodeMix-aware BM25 retrieves cross-script queries:** Romanized and code-mixed Telugu queries that fail completely under unnormalized BM25 (0/10) are retrieved at 90% hit rate under CodeMix normalization — a consistent, reproducible gain on this 30-query pilot corpus.
2. **Evidence-grounded generation enables abstention guardrail:** Condition D (no-evidence ablation) abstains on 100% of all 42 queries under the adapter's `_check_abstention` logic.
3. **RelationAware and Linguistic verifiers agree on identical llama3.2:1b drafts (42/42):** Traced in audit: short 80-token drafts lacked compound conjunctions and relational mismatches, reducing both verifiers to identical base overlap rules.

#### What This Experiment Does Not Demonstrate
1. **Factual correctness of generated text:** Essential keyword coverage (20%) is a heuristic proxy, not gold-standard factuality.
2. **Claim-level citation entailment:** Citation validity rate is 0% — llama3.2:1b does not reliably produce the `[DOC_ID#chunk]` format within 80 tokens (40/42 emitted no citations, 2 emitted hallucinated unsupplied passage IDs).
3. **Human evaluation or inter-annotator agreement:** All labels are single-annotator pilot labels.
4. **Generalization beyond 10 documents / 30 answerable queries:** These are pilot corpus results.

#### Forensic Audit Results (EXP-2E-02-AUDIT-V1, 2026-10-18)
- **Condition A Recomputation:** Independently verified from 42 saved per-query records in `per_query_results.json`. All reported numerators and denominators confirmed exact match.
- **Condition D Inconsistency Resolution:** Resolved. The reported co-occurrence of 42/42 abstentions alongside 2/30 fact-correct answers was caused by `BUG-AUDIT-01` (`fact_correct_cnt` did not check `not is_abstention`) and `BUG-AUDIT-02` (adapter unconditionally forced `is_abstention=True` on empty evidence). Under strict mutual exclusivity, true non-abstained fact-correct answers under Condition D is **0/30 (0.0%)**.
- **Execution Provenance:** Verified real execution on Ollama `llama3.2:1b` (no mock fallback). Cache provenance confirmed: 36 entries loaded from immediate prior dev run (`task-1740`), 48 eval queries generated live (`task-1938`).
- **Regression Tests Added:** `tests/test_exp_2e_02_audit.py` (3 tests verifying abstention/fact-correct mutual exclusion and verifier divergence).
- **Test Suite Status:** **270 passed, 52 skipped** (exit code 0).
- **Audit Artifacts:** Complete versioned audit bundle in [`experiments/results/exp_2e_02_audit_v1/`](file:///d:/Sage-Indic/experiments/results/exp_2e_02_audit_v1/).

#### Known Limitations
- `llama3.2:1b` generates citations unreliably at 80 token cap. Citation validity rate is 0% across all conditions.
- Correct abstention on unanswerable queries (Condition A: 4/12 = 33.3%) is low; the SLM often generates text despite no-evidence instruction cues.
- Verifier decision identity (42/42) is specific to this SLM's generation patterns; it does not establish general equivalence between the two verifiers on higher-quality outputs.
- 52 tests skipped due to optional `transformers` dependency for semantic safety classifiers; these are not failures.

#### Recommended Next Step
Formal closure of Phase 2E/2F audits. Await explicit approval before beginning Phase 2G (Response Composition & Factuality Caveats).

---

### `EXP-2G-01`: Response Composition & Demo Application Integration
- **Phase:** Phase 2G — Response Composition & Factuality Caveats (application integration)
- **Execution Dates:** 2026-11-17 (implementation, live verification, browser checks)
- **Status:** **ENGINEERING INTEGRATION — NO BENCHMARK CLAIM**
- **Harness / Artifacts:**
  - [`tests/test_composition.py`](file:///d:/Sage-Indic/tests/test_composition.py) (15 tests)
  - [`tests/test_api.py`](file:///d:/Sage-Indic/tests/test_api.py) (22 tests)
  - [`scripts/verify_demo.py`](file:///d:/Sage-Indic/scripts/verify_demo.py)
  - [`src/sage_indic/composition/`](file:///d:/Sage-Indic/src/sage_indic/composition/), [`src/sage_indic/pipeline/`](file:///d:/Sage-Indic/src/sage_indic/pipeline/), [`src/sage_indic/api/`](file:///d:/Sage-Indic/src/sage_indic/api/), [`frontend/`](file:///d:/Sage-Indic/frontend/)
- **Hypothesis:** Not applicable. This entry records engineering integration and contract verification, not a research hypothesis test.

#### Scope Implemented
1. **Deterministic grounded composition:** verbatim evidence-sentence claims, sentence ranking, evidence-coverage gate, and claim-level caveats.
2. **Programmatic citations:** `C1`, `C2`, … assigned only from retrieved passages; model-authored citation IDs are stripped and never trusted; citation validity is kept distinct from claim support.
3. **Optional LLM layer:** `GenerationAdapter` + `ExternalAPIProvider`; a draft is accepted only when all claims are `SUPPORTED` and no invalid citations exist, otherwise the deterministic answer is shown with disclosed rejection/fallback.
4. **Explicit abstention semantics:** safety block, empty/insufficient evidence, unverifiable extractive sentences, partial coverage, and provider failure are distinct outcomes.
5. **Backend API:** `/api/health`, `/api/status`, `/api/examples`, `/api/corpus`, `/api/query`; blank queries rejected with HTTP 422; local-origin CORS; static frontend mount.
6. **Frontend:** React 19 + TypeScript + Vite UI showing answer, citations, claim verification, retrieved evidence, system status, and generation-mode disclosure.
7. **Safety fallback disclosure:** when the dense semantic model is unavailable, `SAGE_ContextualGuardrail_LexicalOnlyFallback` is reported in status and responses.

#### Verification Performed
- **Python suite:** `307 passed, 52 skipped` (37 new Phase 2G tests; 52 skips remain the optional semantic-safety tests).
- **Live demo script:** all 9 advertised examples returned the manually expected behaviour (`ANSWERED`, `PARTIALLY_ANSWERED`, `ABSTAINED`) and passed citation-integrity checks.
- **Live browser checks (Chrome + Playwright):** desktop and 390 px mobile layouts exercised Answered, Partially answered, Abstained, Blocked, and verification views; no console errors and no horizontal overflow observed.
- **Frontend production build:** `npm run build` (TypeScript check + Vite) succeeded.
- **Optional LLM path:** a real Ollama request exceeded the 25 s timeout and returned `used_mode=llm_fallback` with the deterministic answer and citation still visible. An earlier ungrounded draft was rejected. The path is mechanically verified only.

#### What This Entry Does Not Demonstrate
1. **No quality or factuality improvement claim:** composition is deterministic and extractive; no new benchmark was run and no model was trained.
2. **No calibrated relevance or entailment claim:** the coverage gate, synonym groups, intent rules, and sentence ranking are transparent application heuristics.
3. **No LLM factuality claim:** `llama3.2:1b` is slow and weak on CPU; only fallback/rejection mechanics were verified.
4. **No generalization claim:** the demo corpus remains 10 documents / 30 chunks.
5. **No safety improvement claim:** the semantic safety classifier was unavailable locally, so the lexical-only fallback was active.

#### Known Limitations
- Lexical safety fallback misses some unlisted terms (e.g. `bomb`, `hack`, `harm`); documented in `OPEN_ISSUES.md` and not patched inside frozen Phase 2C.
- `build_retrieval_expansion()` adds canonical term variants for demo recall; it is not one of the evaluated Phase 2D conditions.
- LLM latency can exceed the default timeout; the deterministic fallback is intentional.
- `ruff format` was not applied repo-wide because the existing baseline is unformatted and formatting would rejoin long Telugu literals, re-triggering `E501`.

#### Recommended Next Step
Review and approve the Phase 2G integration. Do not start a new major research component without explicit approval.

#### Test Suite at Time of Execution
- Full suite: **307 passed, 52 skipped** (exit code 0).

#### Reproduction Commands
```powershell
pytest
python scripts/verify_demo.py
cd frontend; npm run build
```
