# SAGE-Indic — Corpus and Benchmark Expansion Plan (Phase 2D/2E)

**Document Version:** 1.0.0  
**Status:** PROPOSED & RATIFIED FOR IMPLEMENTATION  
**Focus Language:** Telugu (`te`, `te-Latn`, `te-en`)  
**Parent PRD Requirement:** Phase 2D Retrieval Validation & Benchmark Scaling  

---

## 1. Executive Summary & Scientific Motivation

The Phase 2D pilot benchmark evaluated 8 retrieval configurations across 10 approved native Telugu documents (31 chunks) using 42 queries (14 base queries $\times$ 3 scripts: Native, Romanized, Code-Mixed). While this pilot successfully demonstrated that lexical BM25 drops to 0.0 Recall@1 on Romanized/Code-mixed queries and that cross-script normalization restores Recall@1 to 0.8889–1.0, the pilot has clear scientific limitations:
1. **Corpus Size:** 31 chunks is too small to test high-density false-positive rejection.
2. **Domain Bias:** 80% of documents focus on Telangana/Andhra monuments and geography.
3. **Single-Annotator Pilot:** Pilot qrels were constructed by a single annotator without multi-annotator inter-rater agreement measurement.
4. **Leakage Risk:** A 10-document corpus has limited topic diversity between development and evaluation splits.

This plan details a concrete, license-compliant expansion strategy to scale the benchmark to **50 documents (~180–220 chunks)** and **150 multi-script queries**, incorporating independent human adjudication and topic-isolated evaluation.

---

## 2. Source Selection Criteria & Provenance

To guarantee scientific reproducibility and copyright compliance, no content will be scraped arbitrarily. All documents must satisfy:
- Explicit open-access licensing (CC-BY-SA 4.0, CC-BY-SA 3.0, or Open Government / Public Domain).
- Immutable provenance: exact source URL, publication timestamp, revision ID, and cryptographic SHA-256 hash.
- High linguistic quality: native Telugu prose without machine-translation artifacts.

### 2.1 Target Domains & Topic Distribution

| Domain | Target Docs | Target Chunks | Candidate Sources | Justification |
| :--- | :--- | :--- | :--- | :--- |
| **Monuments & History** | 10 (existing) | 31 (existing) | Telugu Wikipedia (CC-BY-SA) | Cultural heritage, baseline evaluation |
| **Agriculture & Climate** | 12 | 45–55 | ANGRAU extension archives, AP/Telangana Rythu Seva portals, Wiki | Crucial for rural Telugu informational queries |
| **Science & Technology** | 10 | 35–45 | Telugu Vigyan portal, Telugu Wiki (Space, Computing) | Tests transliterated technical terminology |
| **Literature & Arts** | 10 | 35–45 | C.P. Brown Academy open texts, Telugu Wiki (Prabandha, Kavitrayam) | Rich classical morphology, tests subword segmentation |
| **Civic & Public Services** | 8 | 25–35 | MeeSeva public guidelines, State portal open archives | Procedural queries, eligibility criteria |
| **Total** | **50** | **170–210** | Provenance-locked public sources | Balanced cross-domain benchmark |

---

## 3. Query Suite Design & Script Variations

The expanded benchmark will define **50 unique informational intents**, yielding **150 evaluated queries** across three modalities:
1. **Native Telugu (`te`):** Standard Telugu Unicode script.
2. **Romanized Telugu (`te-Latn`):** Phonetically variable Latin-script transliterations reflecting realistic mobile chat input (e.g., varying *dh*, *th*, geminates, and short/long vowels).
3. **Code-Mixed (`te-en`):** Conversational Telugu incorporating English technical and domain nouns (e.g., *"wheat crop yield entha untundi?"*).

### 3.1 Query Difficulty Taxonomies

To prevent synthetic ceiling effects (where every query matches uniquely on a single rare keyword):
- **Single-Fact Retrieval (40%):** Pinpoints a single entity, date, or numerical measure.
- **Compositional / Multi-Chunk (25%):** Requires synthesizing evidence across two related chunks from the same document.
- **Lexical Divergence / Paraphrastic (20%):** The query expresses the information need using synonyms or colloquial idioms with zero unigram overlap with the source passage.
- **Genuinely Unanswerable Queries (15%):** Queries addressing plausible entities that are completely absent from the corpus (e.g., modern space missions or non-existent historical events). Evaluates rejection capability and prevents hallucinated false positives.

---

## 4. Annotation & Independent Adjudication Protocol

### 4.1 Double-Annotator Review Pipeline

1. **Candidate Mining:** For each query, a candidate pool of top-20 chunks is retrieved by pooling all baseline systems (BM25, Normalized BM25, Subword BM25, and Dense Embedding).
2. **Primary Annotation ($A_1$):** Native Telugu annotator labels candidate passages on a 3-point relevance scale:
   - `2` (Directly Answers): Contains complete factual information needed.
   - `1` (Partially Relevant): Contains related context but incomplete for full answer.
   - `0` (Irrelevant): Off-topic or does not substantiate the claim.
3. **Secondary Independent Review ($A_2$):** A second native Telugu annotator independently scores the same candidate pool in a blind evaluation (without seeing $A_1$'s labels or retrieval rankings).
4. **Inter-Annotator Agreement Calculation:**
   - Compute Cohen's $\kappa$ on binary relevance ($2 \to 1$, $0/1 \to 0$).
   - Target: Cohen's $\kappa \ge 0.75$.
5. **Adjudication:** Cases where $|A_1 - A_2| \ge 1$ are adjudicated by a third senior linguist. Chunks with persistent ambiguity are tagged as indeterminate and excluded from strict binary metrics.

---

## 5. Development vs. Held-Out Evaluation Partitioning

To prevent data contamination and hyperparameter overfitting:
- **Corpus-Level Partition:** Documents are assigned strictly to Development (60%) or Held-Out Evaluation (40%) partitions by domain. No document or chunk spans both splits.
- **Development Suite (30 intents = 90 queries):** Used for calibrating transliteration rules, tokenization thresholds, dense similarity margins, and verification thresholds.
- **Held-Out Evaluation Suite (20 intents = 60 queries):** Strictly held blind. Evaluated only once per model release for final scientific publication.

---

## 6. Implementation Milestones & Governance

1. **Acquisition & Verification (Milestone 1):** Ingest 40 new documents, verify SHA-256 hashes, generate chunk manifests, and enforce trust boundary isolation.
2. **Annotation Campaign (Milestone 2):** Double-blind annotation of 150 queries, compute $\kappa$, generate unified `qrels.tsv`.
3. **Reproducibility Run (Milestone 3):** Run 8 retrieval conditions and claim verifier on expanded benchmark; publish versioned JSON records to `experiments/results/`.
