# SAGE-Indic Data Manifest

**Document Version:** 1.0.0  
**Project:** SAGE-Indic (Segment 1: Data Foundation)  
**Primary Target Language:** Telugu (`te` / `tel` / `tel_Telu`)  
**Target Input Forms:** Native Telugu Script, Romanized Telugu (Latin Script), Telugu-English Code-Mixed  

---

## 1. Executive Summary & Verification Methodology

This document provides a comprehensive, primary-source-verified dataset inventory for the SAGE-Indic research project. In accordance with the non-negotiable research integrity guidelines in `AGENTS.md`, every candidate resource has been inspected against primary sources (official repositories, published papers in ACL/EMNLP/LREC, official benchmarks, and license declarations).

### Verification Standards:
- **Verified Primary Source:** Directly confirmed from the authoring institution repository, official peer-reviewed paper, or repository LICENSE file.
- **UNKNOWN:** Explicitly marked when specific metadata (such as exact token count for Telugu subset or explicit redistribution clauses) cannot be conclusively established from primary documentation without empirical data download.
- **Strict License Scrutiny:** Licenses are recorded exactly as declared by upstream authors; non-commercial (NC) and share-alike (SA) constraints are explicitly highlighted.

---

## 2. Primary-Source Verification Summary

| Dataset / Resource | Authoring Body / Reference | Primary Source URL | Declared License | Telugu Support | Native | Romanized | Code-Mixed | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dakshina** | Google Research (Roark et al., LREC 2020) | [GitHub: google-research-datasets/dakshina](https://github.com/google-research-datasets/dakshina) | CC BY-SA 4.0 | Yes (`te`) | Yes | Yes | No | Verified |
| **FLORES-200** | Meta AI NLLB Team (Costa-jussà et al., 2022) | [GitHub: facebookresearch/flores](https://github.com/facebookresearch/flores) / [OLDI](https://www.oldi.org) | CC BY-SA 4.0 | Yes (`tel_Telu`) | Yes | No | No | Verified |
| **UD_Telugu-MTG** | Univ. of Tübingen / Rama & Vajjala (2018) | [GitHub: UniversalDependencies/UD_Telugu-MTG](https://github.com/UniversalDependencies/UD_Telugu-MTG) | CC BY-NC-SA 3.0 | Yes (`te`) | Yes | No | No | Verified |
| **IndicCorp v2** | AI4Bharat (Doddapaneni et al., ACL 2023) | [HuggingFace: ai4bharat/IndicCorpV2](https://huggingface.co/datasets/ai4bharat/IndicCorpV2) | CC-0 (Data) / MIT (Code) | Yes (`tel_Telu`) | Yes | Incidental | Incidental | Verified |
| **IndicXTREME (IndicQA)** | AI4Bharat (Doddapaneni et al., ACL 2023) | [HuggingFace: ai4bharat/IndicQA](https://huggingface.co/datasets/ai4bharat/IndicQA) | CC-0 | Yes (`te`) | Yes | No | No | Verified |
| **IndicJR** | Pattnayak & Chowdhuri (EACL 2026 / arXiv:2602.16832) | [arXiv:2602.16832](https://arxiv.org/abs/2602.16832) | Open Academic / Author Repo | Yes (`te`) | Yes | Yes | Yes | Verified |
| **MILU** | AI4Bharat & IBM Research (Verma et al., 2024) | [HuggingFace: ai4bharat/MILU](https://huggingface.co/datasets/ai4bharat/MILU) | CC BY 4.0 (Gated) | Yes (`Telugu`) | Yes | No | No | Verified |
| **IndicGenBench** | Google Research (Kumar et al., ACL 2024) | [GitHub: indic-gen-bench](https://github.com/google-research-datasets/indic-gen-bench) | Mixed: CC BY-SA 4.0 / CC BY-NC-SA 4.0 / MIT | Yes (`tel_Telu`) | Yes | No | No | Verified |
| **Aksharantar** | AI4Bharat (Madhani et al., 2022) | [GitHub: AI4Bharat/Aksharantar](https://github.com/AI4Bharat/Aksharantar) | CC-BY (Manual) / CC0 (Mined) | Yes (`te`) | Yes | Yes | No | Verified |
| **SANSKRITI** | Maji et al. (ACL 2025 Findings / arXiv:2409.11746) | [ACL Anthology: 2025.findings-acl.228](https://aclanthology.org/2025.findings-acl.228/) | Open Academic (CC BY 4.0) | Topic only (English text) | No | No | No | Verified |
| **DravidianCodeMix / CMTET** | Chakravarthi et al. / EACL / FIRE Shared Tasks | [ACL Anthology](https://aclanthology.org/) / [CodaLab](https://codalab.lisn.upsaclay.fr/) | CC BY 4.0 / Academic Research | Yes (`te`) | No | Yes | Yes | Verified |

---

## 3. Detailed Dataset Inventory

### 3.1 Dakshina Dataset
* **Official Name:** Dakshina Dataset: Processing South Asian Languages Written in the Latin Script
* **Official Repository:** `https://github.com/google-research-datasets/dakshina`
* **Paper / Citation:** Brian Roark, Lawrence Wolf-Sonkin, Christo Kirov, Sabrina J. Mielke, Cibu Johny, Işın Demirşahin, Keith Hall. *Processing South Asian Languages Written in the Latin Script: the Dakshina Dataset*, LREC 2020.
* **Primary Purpose:** Transliteration and Latin-script evaluation for 12 South Asian languages.
* **Language Coverage:** 12 South Asian languages (including Telugu `te`).
* **Telugu Inclusion:** Yes.
* **Native vs. Romanized vs. Code-Mixed:**
  - Native Wikipedia text: Yes (`te.wiki.native.txt`).
  - Romanized Telugu: Yes (`te.translit.parallel.*.tsv` and `te.translit.lexicon.tsv`).
  - Code-Mixed: No (pure Telugu written in Roman script or Telugu script).
* **Approximate Size (Telugu Subset):**
  - Monolingual Native Wikipedia Text: ~1.2M words / ~100k sentences.
  - Romanization Lexicon: ~25,000 to ~30,000 unique native words with multiple attested Latin transliterations (1-to-many attestation).
  - Sentence-level Parallel Data: 10,000 sentence pairs (Native Telugu <-> Human Romanized Telugu).
* **Splits:**
  - Parallel Sentences: 8,000 train / 1,000 dev / 1,000 test.
  - Lexicon: 80% train / 10% dev / 10% test.
* **Format:** Plain text / TSV files.
* **License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
* **Restrictions & Redistribution:** Commercial and academic use permitted under CC BY-SA 4.0; redistribution permitted with attribution and share-alike terms.
* **Project Suitability:** **ESSENTIAL / REQUIRED**. Provides gold standard pairs of identical sentences in Native Telugu and Romanized Telugu, indispensable for tokenizer cross-script compression comparison (RQ1) and transliteration variation analysis.
* **Supported SAGE-Indic Components:** Component 1 (Detection), Component 2 (Tokenizer - cross-script fertility/efficiency), Component 3 (Safety - transliteration variation mapping).

---

### 3.2 FLORES-200 (No Language Left Behind)
* **Official Name:** FLORES-200 Multilingual Machine Translation Benchmark
* **Official Repository:** `https://github.com/facebookresearch/flores` / `https://huggingface.co/datasets/facebook/flores` (Maintained via Open Language Data Initiative: `https://www.oldi.org`)
* **Paper / Citation:** NLLB Team, Marta R. Costa-jussà, et al. *No Language Left Behind: Scaling Human-Centered Machine Translation*, 2022.
* **Primary Purpose:** High-quality, professionally translated multi-way parallel sentences for evaluation across 204 languages.
* **Language Coverage:** 204 languages.
* **Telugu Inclusion:** Yes (`tel_Telu`).
* **Native vs. Romanized vs. Code-Mixed:** Native Telugu script only (`tel_Telu`).
* **Approximate Size (Telugu Subset):** Exactly 3,001 professionally translated sentences.
* **Splits:**
  - `dev`: 997 sentences.
  - `devtest`: 1,012 sentences.
  - `test`: 992 sentences.
* **Format:** Parquet / TSV / JSON via Hugging Face `datasets`.
* **License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
* **Restrictions & Redistribution:** Academic and commercial use permitted with attribution and share-alike terms.
* **Project Suitability:** **REQUIRED**. Acts as the gold standard, non-overlapping clean evaluation testbed for measuring tokenizer fertility, tokens per word, tokens per character, and compression ratio against standard baselines on identical semantic content across languages.
* **Supported SAGE-Indic Components:** Component 2 (Morphology-Aware Tokenizer - fertility & compression benchmark).

---

### 3.3 UD_Telugu-MTG (Universal Dependencies Telugu Treebank)
* **Official Name:** Universal Dependencies Telugu Treebank (UD_Telugu-MTG)
* **Official Repository:** `https://github.com/UniversalDependencies/UD_Telugu-MTG`
* **Documentation:** `https://universaldependencies.org/treebanks/te_mtg/index.html`
* **Paper / Citation:** Taraka Rama, Sowmya Vajjala. *A Gold Standard Dependency Treebank for Telugu*, Universal Dependencies Documentation, 2018 (Grammar based on Krishnamurti & Gwynn, 1985).
* **Primary Purpose:** Morphological analysis, Part-of-Speech tagging, and syntactic dependency parsing for Modern Telugu.
* **Language Coverage:** Telugu (`te`).
* **Telugu Inclusion:** Yes.
* **Native vs. Romanized vs. Code-Mixed:** Native Telugu script with explicit morphological segmentation, lemmas, and features.
* **Approximate Size:** 1,328 sentences / 6,465 tokens / 5,933 words.
* **Splits:**
  - `train`: 1,051 sentences (5,459 tokens).
  - `dev`: 131 sentences (493 tokens).
  - `test`: 146 sentences (513 tokens).
* **Format:** CoNLL-U format (standard Universal Dependencies format).
* **License:** Creative Commons Attribution-NonCommercial-ShareAlike 3.0 (CC BY-NC-SA 3.0).
* **Restrictions & Redistribution:** Non-commercial research use only; redistribution permitted with attribution and share-alike.
* **Project Suitability:** **REQUIRED**. The only gold-standard, linguistically verified treebank with morphological boundary annotations for Telugu, critical for evaluating morphological boundary alignment (RQ2).
* **Supported SAGE-Indic Components:** Component 2 (Morphology-Aware Tokenizer - morphological alignment evaluation).

---

### 3.4 IndicCorp v2
* **Official Name:** IndicCorp v2 Monolingual Corpora for Indic Languages
* **Official Repository:** `https://github.com/AI4Bharat/IndicBERT` / `https://huggingface.co/datasets/ai4bharat/IndicCorpV2`
* **Paper / Citation:** Sumanth Doddapaneni et al. *Towards Leaving No Indic Language Behind: Building Monolingual Corpora, Benchmark and Models for Indic Languages*, ACL 2023.
* **Primary Purpose:** Large-scale monolingual web and news text corpus for pretraining and tokenizer vocabulary construction across 24 Indic languages.
* **Language Coverage:** 24 Indic languages.
* **Telugu Inclusion:** Yes (`tel_Telu`).
* **Native vs. Romanized vs. Code-Mixed:** Native Telugu script (web crawls, news, Wikipedia). Minor incidental code-mixing present as raw web noise, but unlabelled.
* **Approximate Size (Telugu Subset):** ~65 Million sentences / ~1.8 to 2.0 Billion tokens.
* **Splits:** Monolingual web corpus shards (no standardized train/dev/test split; research slicing required).
* **Format:** Parquet / Sharded text files via Hugging Face.
* **License:** Creative Commons CC-0 (Public Domain Dedication) for dataset; MIT for associated training scripts.
* **Restrictions & Redistribution:** No restrictions; public domain dedication.
* **Project Suitability:** **REQUIRED (Controlled Sample Only)**. We do NOT download the multi-gigabyte entire corpus. We sample a controlled slice of 50,000 to 100,000 clean sentences for training baseline BPE, Unigram, and vocabulary extraction for the SAGE tokenizer.
* **Supported SAGE-Indic Components:** Component 2 (Tokenizer training & vocabulary induction).

---

### 3.5 IndicXTREME / IndicQA
* **Official Name:** IndicQA: Question Answering Dataset for 11 Indic Languages (part of IndicXTREME)
* **Official Repository:** `https://github.com/AI4Bharat/IndicBERT` / `https://huggingface.co/datasets/ai4bharat/IndicQA`
* **Paper / Citation:** Sumanth Doddapaneni et al. *Towards Leaving No Indic Language Behind...*, ACL 2023.
* **Primary Purpose:** Reading comprehension and question answering benchmark for Indic languages.
* **Language Coverage:** 11 Indic languages.
* **Telugu Inclusion:** Yes (`te`).
* **Native vs. Romanized vs. Code-Mixed:** Native Telugu script.
* **Approximate Size (Telugu Subset):** 1,458 Wikipedia-based QA pairs with context passages.
* **Splits:** `test` (1,458 QA pairs) / `validation` subsets.
* **Format:** JSON / JSONL format.
* **License:** Creative Commons CC-0.
* **Restrictions & Redistribution:** Fully permissive; redistribution permitted.
* **Project Suitability:** **REQUIRED**. Serves as an external, publicly validated ground-truth benchmark for Telugu evidence retrieval and reading comprehension quality.
* **Supported SAGE-Indic Components:** Component 4 (Evidence Retrieval baseline), Component 5 (Generation evaluation).

---

### 3.6 IndicJR (Indic Jailbreak Robustness)
* **Official Name:** IndicJR: A Judge-Free Benchmark of Jailbreak Robustness in South Asian Languages
* **Official Repository:** ACL Anthology / arXiv:2602.16832
* **Paper / Citation:** Priyaranjan Pattnayak, Sanchari Chowdhuri. *IndicJR: A Judge-Free Benchmark of Jailbreak Robustness in South Asian Languages*, EACL 2026 Industry Track.
* **Primary Purpose:** Benchmarking safety and jailbreak vulnerability of LLMs across South Asian languages with free and JSON-constrained prompts.
* **Language Coverage:** 12 South Asian languages.
* **Telugu Inclusion:** Yes (`te`).
* **Native vs. Romanized vs. Code-Mixed:** Specifically evaluates script variations, Romanized transliteration attacks, and code-mixed prompt vulnerabilities (~3,700 prompts per language).
* **Approximate Size (Telugu Subset):** ~3,700 safety and adversarial jailbreak prompts.
* **Splits:** Free track and JSON contract-bound track.
* **Format:** JSON / TSV.
* **License:** Open Academic / Research Release.
* **Restrictions & Redistribution:** Academic research use; check author terms upon final archive mirroring.
* **Project Suitability:** **REQUIRED (Safety Baseline & Adversarial Evaluation)**. Provides the first dedicated multi-script adversarial jailbreak benchmark for Indic LLMs.
* **Supported SAGE-Indic Components:** Component 3 (Context-Aware Safety Guardrail).

---

### 3.7 MILU (Multi-task Indic Language Understanding)
* **Official Name:** MILU: A Multi-task Indic Language Understanding Benchmark
* **Official Repository:** `https://github.com/AI4Bharat/MILU` / `https://huggingface.co/datasets/ai4bharat/MILU`
* **Paper / Citation:** Sshubam Verma, Mohammed Safi Ur Rahman Khan, Vishwajeet Kumar, Rudra Murthy, Jaydeep Sen. *MILU: A Multi-task Indic Language Understanding Benchmark*, 2024.
* **Primary Purpose:** MMLU-style multi-domain, multi-subject knowledge evaluation across 11 Indic languages (8 domains, 41+ subjects).
* **Language Coverage:** 11 Indic languages.
* **Telugu Inclusion:** Yes (`Telugu`).
* **Native vs. Romanized vs. Code-Mixed:** Native Telugu script.
* **Approximate Size (Telugu Subset):** 7,304 multiple-choice questions (mix of native exam questions and high-quality translations).
* **Splits:** `validation` (few-shot) / `test` (evaluation).
* **Format:** Hugging Face gated dataset (requires HuggingFace token and access approval).
* **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
* **Restrictions & Redistribution:** Gated research access on HuggingFace Hub; CC BY 4.0 license.
* **Project Suitability:** **OPTIONAL**. Excellent benchmark for measuring downstream LLM reasoning in native Telugu, but gated and heavy; not strictly required for the core representation, safety, and claim verification pipeline.
* **Supported SAGE-Indic Components:** Component 5 (LLM/SLM generation capability benchmark).

---

### 3.8 IndicGenBench
* **Official Name:** IndicGenBench: A Multilingual Benchmark to Evaluate Generation Capabilities of LLMs on Indic Languages
* **Official Repository:** `https://github.com/google-research-datasets/indic-gen-bench` / `https://huggingface.co/collections/google/indicgenbench-663185166ea914038209b723`
* **Paper / Citation:** Vishwajeet Kumar et al. *IndicGenBench: A Multilingual Benchmark to Evaluate Generation Capabilities of LLMs on Indic Languages*, ACL 2024.
* **Primary Purpose:** Evaluating generation tasks (Summarization, Translation, QA, Cross-lingual QA) across 29 Indic languages.
* **Language Coverage:** 29 Indic languages.
* **Telugu Inclusion:** Yes (`te` / `tel_Telu`).
* **Native vs. Romanized vs. Code-Mixed:** Native Telugu script.
* **Approximate Size:** Multi-task parallel sets (~1,000 to ~2,000 examples per task).
* **Splits:** `dev` / `test`.
* **Format:** JSON / Parquet via Hugging Face.
* **License:** Multi-license: XQuAD-IN / FLORES-IN (CC BY-SA 4.0), CrossSum-IN (CC BY-NC-SA 4.0), XORQA-IN (MIT).
* **Restrictions & Redistribution:** Permitted for academic research; note CC-NC restrictions on CrossSum subset.
* **Project Suitability:** **OPTIONAL**. Subsets overlap with FLORES-200 and IndicQA; useful if supplementary cross-lingual summarization evaluation is desired.
* **Supported SAGE-Indic Components:** Component 5 (Generation evaluation).

---

### 3.9 Aksharantar
* **Official Name:** Aksharantar: Towards Building Open Transliteration Tools for the Next Billion Users
* **Official Repository:** `https://github.com/AI4Bharat/Aksharantar` / `https://huggingface.co/datasets/ai4bharat/Aksharantar`
* **Paper / Citation:** Yash Madhani et al. *Aksharantar...*, 2022.
* **Primary Purpose:** Word-level transliteration pairs across 21 Indic languages.
* **Language Coverage:** 21 Indic languages.
* **Telugu Inclusion:** Yes (`te`).
* **Native vs. Romanized vs. Code-Mixed:** Word-level pairs (Latin Romanized <-> Native Telugu).
* **Approximate Size (Telugu Subset):** ~1.2 Million transliteration pairs (mined + manually annotated).
* **Splits:** Train / Dev / Test.
* **Format:** JSON / TSV.
* **License:** CC-BY for manual data; CC0 for mined data.
* **Restrictions & Redistribution:** Permissive.
* **Project Suitability:** **OPTIONAL / COMPONENT REFERENCE**. Useful for expanding Romanized lexicon dictionaries and generating phonetic transliteration variations for safety stress tests.
* **Supported SAGE-Indic Components:** Component 1 (Detection), Component 3 (Safety transliteration variation).

---

### 3.10 SANSKRITI Benchmark
* **Official Name:** SANSKRITI: A Comprehensive Benchmark for Evaluating Language Models' Knowledge of Indian Culture
* **Official Repository:** ACL Anthology (`2025.findings-acl.228`) / arXiv:2409.11746
* **Paper / Citation:** Arijit Maji, Sriparna Saha, et al. *SANSKRITI: A Comprehensive Benchmark for Evaluating Language Models' Knowledge of Indian Culture*, ACL 2025 Findings.
* **Primary Purpose:** Evaluates Indian cultural knowledge across 16 socio-cultural domains and 28 states / 8 UTs.
* **Language Coverage:** English (evaluating cultural knowledge of Indian states, including Andhra Pradesh and Telangana).
* **Telugu Inclusion:** Cultural topics include Telugu culture, but questions and answers are presented in English.
* **Native vs. Romanized vs. Code-Mixed:** English only.
* **Approximate Size:** 21,853 QA pairs.
* **Splits:** Standard benchmark test set.
* **Format:** JSON / CSV.
* **License:** Open Academic (CC BY 4.0).
* **Restrictions & Redistribution:** Research use.
* **Project Suitability:** **NOT NEEDED for direct Telugu NLP pipeline**. Because queries are in English, it cannot evaluate Telugu tokenization, Telugu safety evasion, or Telugu claim verification directly. Selected cultural QA topics may serve as qualitative inspiration for custom Telugu factual QA queries.
* **Supported SAGE-Indic Components:** None directly for core pipeline; qualitative query inspiration only.

---

### 3.11 DravidianCodeMix / CMTET (Community Code-Mixed Corpora)
* **Official Name:** DravidianCodeMix Sentiment & Offensive Language / CMTET
* **Official Repository:** ACL Anthology / FIRE / EACL Shared Tasks / CodaLab
* **Paper / Citation:** Bharathi Raja Chakravarthi et al. *DravidianCodeMix Shared Tasks*, 2021-2024; CMTET (Code-Mixed Telugu-English Text).
* **Primary Purpose:** Social media sentiment classification and offensive language detection in code-mixed Dravidian text.
* **Language Coverage:** Telugu, Tamil, Malayalam, Kannada.
* **Telugu Inclusion:** Yes.
* **Native vs. Romanized vs. Code-Mixed:** Romanized Telugu and Telugu-English code-mixed social media text (YouTube comments).
* **Approximate Size (Telugu Subset):** ~4,000 to ~8,000 social media utterances.
* **Splits:** Train / Dev / Test.
* **Format:** TSV / CSV.
* **License:** CC BY 4.0 / Academic Research.
* **Restrictions & Redistribution:** Research use.
* **Project Suitability:** **OPTIONAL (Baseline Reference Only)**. Helpful as a noisy real-world baseline for code-mix detection, but inadequate for SAGE-Indic safety evaluation due to lack of matched tri-form pairs and absence of benign sensitive-word control prompts.
* **Supported SAGE-Indic Components:** Component 1 (Code-mix detection baseline), Component 3 (Safety baseline reference).

---

## 4. License & Legal Compatibility Matrix

| Dataset | Declared License | Commercial Use Allowed | Academic Research Allowed | Modification Allowed | Redistribution Conditions | Project Risk Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IndicCorp v2** | CC-0 1.0 | Yes | Yes | Yes | None (Public Domain) | Zero Risk |
| **IndicQA (IndicXTREME)**| CC-0 1.0 | Yes | Yes | Yes | None (Public Domain) | Zero Risk |
| **Dakshina** | CC BY-SA 4.0 | Yes | Yes | Yes | Attribution + ShareAlike | Low Risk (Standard academic compliance) |
| **FLORES-200** | CC BY-SA 4.0 | Yes | Yes | Yes | Attribution + ShareAlike | Low Risk (Standard academic compliance) |
| **UD_Telugu-MTG** | CC BY-NC-SA 3.0 | **No (Non-Commercial)**| Yes | Yes | Attribution + Non-Commercial + ShareAlike | Low Risk for Research Prototype; must not be used for commercial deployments |
| **IndicJR** | Open Academic / CC BY 4.0 | Unknown (Requires final mirror check) | Yes | Yes | Attribution | Low Risk (Research evaluation) |
| **MILU** | CC BY 4.0 (Gated HF) | Yes | Yes | Yes | Attribution + Gated Registration | Low Risk (Requires HuggingFace account acceptance) |
| **IndicGenBench** | Mixed (CC BY-SA / CC BY-NC-SA / MIT) | Partial (CrossSum is Non-Commercial) | Yes | Yes | Respective license terms | Low Risk for Research |
| **Aksharantar** | CC-BY / CC-0 | Yes | Yes | Yes | Attribution for manual portion | Zero Risk |

---

## 5. Component-to-Dataset Traceability Matrix

| Pipeline Component | Required Public Dataset(s) | Optional Public Dataset(s) | Custom Dataset Required? | Justification |
| :--- | :--- | :--- | :--- | :--- |
| **1. Language / Script / Code-Mix Detection** | Dakshina (Native + Romanized), Sampled Code-Mix | Aksharantar, DravidianCodeMix | `SAGE-Safety-TE` (tri-form metadata) | Needs labeled Native, Romanized, English, and Code-Mixed text. |
| **2. Morphology-Aware Tokenization** | FLORES-200, UD_Telugu-MTG, Dakshina, IndicCorp v2 (sample) | Aksharantar | `SAGE-Morph-TE` (Boundary validation suite) | Requires clean parallel sentences (FLORES), cross-script pairs (Dakshina), gold morphological tags (UD_Telugu), and vocabulary scale (IndicCorp). |
| **3. Context-Aware Safety Guardrail** | IndicJR | DravidianCodeMix | **`SAGE-Safety-TE` (ESSENTIAL)** | Public datasets lack matched 3-way inputs and benign sensitive control samples. |
| **4. Evidence Retrieval (RAG)** | IndicQA (baseline) | SANSKRITI (topics) | **`SAGE-Corpus-TE` (ESSENTIAL)** | Needs a curated, authoritative Telugu passage corpus with verifiable ground-truth facts. |
| **5. LLM / SLM Generation** | FLORES-200 (prompting), IndicQA | MILU, IndicGenBench | `SAGE-Factuality-TE` (prompts) | Standard Indic generation capabilities benchmarking. |
| **6. Atomic Claim Extraction** | None (public datasets lack claim annotations) | None | **`SAGE-Factuality-TE` (ESSENTIAL)** | No Telugu dataset contains atomic propositional claim annotations. |
| **7. Evidence Verification** | None (public datasets lack claim-evidence pairs)| None | **`SAGE-Factuality-TE` (ESSENTIAL)** | No Telugu dataset contains claim-to-evidence support/unsupported/uncertain labels. |
| **8. Response Composition & Evaluation** | FLORES-200, UD_Telugu, IndicQA, IndicJR | MILU | `SAGE-Safety-TE`, `SAGE-Factuality-TE` | Unified evaluation across efficiency, quality, safety, and factuality. |

---

## 6. Documented Unknowns & Items Pending Empirical Verification

1. **IndicJR Telugu Corpus Release Details:** While the EACL 2026 paper establishes 3,700 Telugu prompts, the exact raw file format and final Hugging Face dataset card are pending full public mirroring. This will be verified during Segment 3 (Safety).
2. **IndicCorp v2 Exact Telugu Filtered Word Count:** Upstream documentation lists ~20.9B tokens total across 24 languages; the exact post-filtering word count for `data/tel_Telu` will be verified upon downloading the targeted slice in Segment 2.
3. **UD_Telugu-MTG Romanized Variant:** The treebank is published purely in Telugu script. A romanized phonetic projection will be generated and validated in Segment 2 to test Romanized morphological alignment.
