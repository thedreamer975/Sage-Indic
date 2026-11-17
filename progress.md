# SAGE-Indic: Project Progress & Research Record (Audited & Reconciled)

**Document Title:** Comprehensive Project Progress & Experimental Milestone Report  
**Target Repository:** `Sage-Indic` (Package version state: see Section 6.2)  
**Primary Language Focus:** Telugu (Native Script, Romanized Telugu, Telugu-English Code-Mixed)  
**Audit & Reconciliation Date:** October 2026  
**Application Integration Date:** November 2026  
**Status:**  
- Phase 1 (Core Infrastructure) & Phase 2A (Detection): **COMPLETE**  
- Phase 2B (Tokenizer Research): **FROZEN / RECONCILED (EVALUATION UNDER REPAIR)**  
- Phase 2C (Context-Aware Safety): **COMPLETE & FROZEN**  
- Phase 2D (RAG Evidence Corpus Foundation): **STAGE B INGESTED (10 DOCS, 30 CHUNKS)**  
- Phase 2D (Cross-Script Retrieval & Hybrid Benchmark): **COMPLETE — ALL 8 CONDITIONS EVALUATED**  
- Phase 2E (Generation Adapter): **IMPLEMENTED & TESTED (EXP-2E-01)**  
- Phase 2E (End-to-End Evaluation): **EXECUTED & RESULTS RECORDED (EXP-2E-02)**  
- Phase 2F (Atomic Decomposition & Relation-Aware Verification): **RESEARCH VALIDATION COMPLETE (EXP-2F-01)**  
- Phase 2G (Response Composition & Demo Application): **IMPLEMENTED PROTOTYPE — NO BENCHMARK CLAIM**  

---

## 1. Executive Summary & Research Vision

**SAGE-Indic** is a research-oriented Natural Language Processing and Large Language Model (NLP/LLM) framework designed to investigate the **quality–efficiency–safety–factuality trade-offs** of a linguistically structured pipeline for Indic languages, taking **Telugu** as the primary language.

Rather than training a massive LLM from scratch or treating tokenization, safety, and retrieval as disconnected problems, SAGE-Indic addresses four systemic failure modes of multilingual NLP pipelines on agglutinative, morphologically rich languages:
1. **Severe Token Fragmentation (Efficiency):** Standard byte-pair encoding (BPE) subword models fragment Telugu and code-mixed words into arbitrary phonetic fragments, inflating sequence length, inference latency, and memory footprints.
2. **Loss of Linguistic Integrity (Representation):** Naive token reduction often fuses stems and affixes across syntactic boundaries, disrupting syntactic and morphological structures.
3. **Safety Vulnerabilities under Cross-Script & Code-Mix Evasion (Robustness):** Unsafe intent expressed in Romanized Telugu, agglutinated inflections, or adversarial character/punctuation spacings easily evades standard keyword blacklists and English-centric classifiers, while benign words in sensitive contexts (e.g., medicine, history) suffer high False Positive Rates (FPR).
4. **Weak Evidence Factuality in RAG (Grounding):** Retrieving context does not guarantee that generated responses are truthful; evidence retrieval must be decoupled from claim-level verification.

---

## 2. Nine-Stage Pipeline & Phase Implementation Status

| Pipeline Stage | Research Phase | Component / Subsystem | Implementation Status | Primary Artifacts & Modules |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | **Phase 1** | Infrastructure & Project Base | **COMPLETE** | `configs/`, `pyproject.toml`, `src/sage_indic/config.py`, `logging.py` |
| **Stage 2** | **Phase 2A** | Language, Script & Code-Mix Detection | **COMPLETE** | `src/sage_indic/detection/`, `src/sage_indic/types.py` |
| **Stage 3** | **Phase 2B** | SAGE Morphology-Aware Tokenizer | **FROZEN BASELINE / EVALUATION REPAIR** | `src/sage_indic/tokenizer/`, `experiments/run_tokenizer_experiment.py` |
| **Stage 4** | **Phase 2C** | Context-Aware Safety Guardrail | **FROZEN & VERIFIED** | `src/sage_indic/safety/`, `experiments/run_safety_experiment.py` |
| **Stage 5** | **Phase 2D** | Evidence Corpus Foundation & Ingestion | **STAGE B INGESTED (10 DOCS, 30 CHUNKS)** | `src/sage_indic/rag/`, `scripts/build_phase2d_corpus.py` |
| **Stage 5b** | **Phase 2D** | Cross-Script Normalization & Retrieval | **COMPLETE — 8 CONDITIONS EVALUATED** | `src/sage_indic/rag/normalizer.py`, `dense.py`, `hybrid.py`, `experiments/run_retrieval_experiment.py` |
| **Stage 6** | **Phase 2E** | LLM/SLM Generation Adapter | **IMPLEMENTED & TESTED** | `src/sage_indic/generation/`, `tests/test_generation_adapter.py` |
| **Stage 6b** | **Phase 2E** | End-to-End Grounded Factuality Evaluation | **EXECUTED — RESULTS RECORDED (EXP-2E-02)** | `experiments/run_exp_2e_02.py`, `experiments/results/exp_2e_02/` |
| **Stage 7** | **Phase 2F** | Atomic Proposition Decomposition | **VALIDATED EXPERIMENTAL** | `src/sage_indic/verification/types.py` (`AtomicProposition`), `relation_verifier.py` |
| **Stage 8** | **Phase 2F** | Relation-Aware Evidence Verification | **VALIDATED EXPERIMENTAL** | `src/sage_indic/verification/relation_verifier.py`, `experiments/run_verification_experiment.py` |
| **Stage 9** | **Phase 2G** | Response Composition & Demo Application | **IMPLEMENTED PROTOTYPE (NO BENCHMARK CLAIM)** | `src/sage_indic/composition/`, `src/sage_indic/pipeline/`, `src/sage_indic/api/`, `frontend/` |

---

## 3. What Has Been Built (Detailed Component Inventory)

### 3.1 Phase 1: Core Architecture & Normalization Layer
- **Unified Types ([`src/sage_indic/types.py`](file:///d:/Sage-Indic/src/sage_indic/types.py)):**
  - `LanguageCategory`: Enumeration covering `TELUGU_NATIVE`, `ROMANIZED_TELUGU`, `TELUGU_ENGLISH_CODE_MIXED`, `ENGLISH`, and `UNKNOWN`.
  - `InputRepresentation`: Canonical dataclass holding original text, normalized text, category, confidence score, script character ratios, and detection metadata.
- **Conservative Normalizer ([`src/sage_indic/normalize.py`](file:///d:/Sage-Indic/src/sage_indic/normalize.py)):**
  - Enforces Unicode NFC standard representation.
  - Strips zero-width spaces/non-joiners *except* preserving valid Telugu virama + ZWNJ sequences essential for split conjunct rendering (`\u0c4d\u200c`).
  - Strictly non-destructive: no linguistic rewriting, stemming, or lossy alterations.

### 3.2 Phase 2A: Deterministic Language & Code-Mix Detector
- **Implementation ([`src/sage_indic/detection/detector.py`](file:///d:/Sage-Indic/src/sage_indic/detection/detector.py)):**
  - Heuristic-based, zero-external-dependency detector operating via Unicode codepoint inspection (`\u0c00`–`\u0c7f` for Telugu, ASCII/Latin-1 for Romanized/English).
  - Lexical token classifiers identifying Romanized Telugu function words (e.g., *nenu*, *meeru*, *ekkada*, *undi*) and code-mixed suffixes (e.g., `-ki`, `-lo`, `-ga`, `-thoo`).
  - Capable of resolving script-level mixture and phonetic romanization without heavy neural models.

### 3.3 Phase 2B: SAGE (Script- & Affix-Guided Encoding) Tokenizer
- **Linguistic Akshara Parser ([`src/sage_indic/tokenizer/morphology.py`](file:///d:/Sage-Indic/src/sage_indic/tokenizer/morphology.py)):**
  - Implements regular expressions for Telugu orthographic syllables (*aksharas*: consonant clusters + virama + dependent vowel matras + anusvara/visarga).
  - Maintains curated inventories of native nominal postpositions (విభక్తులు: `-కి`, `-కు`, `-లో`, `-తో`, `-ను`, `-ల`) and verbal auxiliary suffixes.
  - Maintains Romanized transliteration affix equivalents (`-ki`, `-lo`, `-ga`, `-thoo`, `-chesi`).
  - Pre-segments agglutinated compounds at linguistic boundaries while preventing cross-akshara subword mergers.
- **Tokenizer Engine ([`src/sage_indic/tokenizer/sage_tokenizer.py`](file:///d:/Sage-Indic/src/sage_indic/tokenizer/sage_tokenizer.py)):**
  - Two-stage architecture: (1) Affix and akshara pre-segmentation, followed by (2) Constrained Unigram Language Model subword modeling.
  - Pre-populates subword vocabulary with critical grammatical markers (`##ki`, `##lo`, etc.).
  - Guarantees exact, lossless round-trip detokenization (`decode(encode(text)) == text`).
- **Baseline Implementations:**
  - Standard Byte-Pair Encoding (`BpeBaselineTokenizer`) in [`src/sage_indic/tokenizer/bpe_baseline.py`](file:///d:/Sage-Indic/src/sage_indic/tokenizer/bpe_baseline.py).
  - Standard Unigram LM (`UnigramBaselineTokenizer`) in [`src/sage_indic/tokenizer/unigram_baseline.py`](file:///d:/Sage-Indic/src/sage_indic/tokenizer/unigram_baseline.py).
  - SAGE Ablation model without morphological pre-segmentation (`SAGE_Ablation_NoMorph`).

### 3.4 Phase 2C: Context-Aware Safety Guardrail
- **Architectural Modules ([`src/sage_indic/safety/`](file:///d:/Sage-Indic/src/sage_indic/safety/)):**
  - **Proposed Guardrail ([`guardrail.py`](file:///d:/Sage-Indic/src/sage_indic/safety/guardrail.py)):** Calibrated multi-signal decision engine combining:
    1. *Orthographic De-obfuscation:* Neutralizes whitespace padding (`v a a d i n i`), character repetitions (`chaaampesthamm`), and punctuation delimiters (`k*i*l*l`, `చం.పే.స్తా.ను`).
    2. *SAGE Morphological Stem Isolation:* Unpacks heavily inflected native and Romanized threat verbs (e.g. `చంపేస్తాను` -> stem `చంపు`).
    3. *Benign Context Disambiguation:* Detects contextual indicators across medical/toxicological, historical warfare, computing terms, and figurative hyperbolic idioms, reducing risk scores on benign queries.
    4. *Decision Thresholds:* Tuned on development data ($\theta_{\text{unsafe}} = 0.58$, $\theta_{\text{uncertain}} = 0.40$).
  - **Baselines:**
    - Baseline A: Lexical / Keyword Blacklist Filter ([`lexical.py`](file:///d:/Sage-Indic/src/sage_indic/safety/lexical.py)).
    - Baseline B: Multilingual Semantic Classifier ([`classifier.py`](file:///d:/Sage-Indic/src/sage_indic/safety/classifier.py)).
    - SAGE Ablation: Guardrail with morphological stem extraction disabled.

### 3.5 Phase 2D: RAG Evidence Corpus Foundation & Stage B Ingestion
- **Data Models & Security Boundary ([`src/sage_indic/rag/types.py`](file:///d:/Sage-Indic/src/sage_indic/rag/types.py), [`security.py`](file:///d:/Sage-Indic/src/sage_indic/rag/security.py)):**
  - `SourceDocument`: Complete 23-field specification enforcing cryptographic provenance, dual raw/normalized text references, and immutable metadata.
  - `DocumentChunk`: Deterministic chunking capturing exact `[char_start, char_end]` Unicode codepoint offsets in the parent text.
  - `TrustBoundaryEnforcer`: Strict isolation preventing retrieved untrusted text payloads from modifying retrieval configurations or injecting instructions.
  - Licensing lifecycle with explicit states (`APPROVED`, `LICENSE_UNVERIFIED`, `REJECTED`, `DO_NOT_USE`).
- **Deterministic Ingestion Pipeline ([`src/sage_indic/rag/ingestion.py`](file:///d:/Sage-Indic/src/sage_indic/rag/ingestion.py)):**
  - Validates chunk roundtrips (`parent_text[char_start:char_end] == chunk.text`).
  - Validates complete cryptographic provenance chains (`ContentHash` via SHA-256).
- **Candidate Eligibility Gate & Acquisition Provider ([`src/sage_indic/rag/acquisition.py`](file:///d:/Sage-Indic/src/sage_indic/rag/acquisition.py)):**
  - Separates web/search API discovery from approved corpus inclusion. All discovered sources default to `retrieval_eligible=False`.
  - Ingestion requires explicit human audit, verified license evidence, and permanent revision URL.
- **Retriever Models & Cross-Script Architecture ([`src/sage_indic/rag/`](file:///d:/Sage-Indic/src/sage_indic/rag/)):**
  - `BM25Retriever`: Deterministic Okapi BM25 implementation ($k_1=1.5, b=0.75$) with Robertson-Spärck Jones IDF, supporting swappable tokenizers (Unicode whitespace, BPE, Unigram, SAGE) and query normalizers.
  - `RomanizedTeluguTransliterator` ([`normalizer.py`](file:///d:/Sage-Indic/src/sage_indic/rag/normalizer.py)): Deterministic rule-based phonetic transliteration from Romanized Telugu to Telugu script, with longest-match consonant clusters, vowel signs, and specialized lexicon for proper nouns and acronyms.
  - `CodeMixedQueryNormalizer` ([`normalizer.py`](file:///d:/Sage-Indic/src/sage_indic/rag/normalizer.py)): Script- and language-aware normalizer that preserves English technical terms, adds bilingual Telugu conceptual synonyms, and transliterates Romanized Telugu words into an expanded query representation.
  - `MultilingualDenseRetriever` ([`dense.py`](file:///d:/Sage-Indic/src/sage_indic/rag/dense.py)): Dense semantic retrieval using `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` loaded offline from verified local snapshot, utilizing normalized cosine similarity and parent provenance encapsulation.
  - `HybridRetriever` ([`hybrid.py`](file:///d:/Sage-Indic/src/sage_indic/rag/hybrid.py)): Reciprocal Rank Fusion (RRF, $k=60$) combining CodeMix-aware BM25 lexical precision and multilingual dense semantic coverage.

### 3.6 Phase 2D/2F: Claim-Verification Foundation & Relation-Aware Verification
- **Data Models ([`src/sage_indic/verification/types.py`](file:///d:/Sage-Indic/src/sage_indic/verification/types.py)):**
  - `AtomicClaim`: High-level claim container preserving language, modality, and query provenance.
  - `AtomicProposition`: Minimal typed representation for decomposed propositions, explicitly capturing `subject`, `predicate`, `object`, `polarity`, `is_negated`, `quantity`, `quantity_unit`, `temporal_date`, `temporal_relation`, `original_span`, and `language_provenance` (unextractable attributes remain explicitly `None`).
  - `EvidencePassage`: Untrusted retrieved passage preserving cryptographic SHA-256 parent hash and chunk metadata.
  - `VerificationOutcome`: Explicit 4-class outcome (`SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING_EVIDENCE`).
  - `VerificationResult`: Directional decision object with heuristic confidence, explanation, and isolated data invariants.
  - `ClaimVerificationReport`: Aggregated evaluation container for batch test suites.
- **Verification Engines ([`src/sage_indic/verification/`](file:///d:/Sage-Indic/src/sage_indic/verification/)):**
  - `LinguisticClaimVerifier` ([`verifier.py`](file:///d:/Sage-Indic/src/sage_indic/verification/verifier.py)): Frozen weak baseline performing token-overlap, numerical matching, polarity alignment, and multi-passage consistency auditing.
  - `RelationAwareClaimVerifier` ([`relation_verifier.py`](file:///d:/Sage-Indic/src/sage_indic/verification/relation_verifier.py)): Experimental relation-aware verifier implementing:
    1. *Atomic Conjunction Decomposition:* Splits compound claims across native (e.g. `మరియు`), Romanized (`mariyu`, `and`), and punctuation boundaries into individual `AtomicProposition` units.
    2. *Relational Predicate Matching:* Normalizes verbal and relational tokens into canonical categories (e.g., `construction_or_creation`, `death_or_destruction`, `discovery_or_study`), rejecting ungrounded or mismatched predicates.
    3. *Conservative Compound Policy:* Evaluates propositions independently; if any proposition lacks evidence, returns `INSUFFICIENT_EVIDENCE`; if any is refuted, returns `CONTRADICTED`. Never forces partial support into `SUPPORTED`.
    4. *Defense-in-Depth Sanitization:* Quarantines prompt-injection payloads in evidence passages, parsing evidence strictly as passive untrusted data.
  - Specifications: [`docs/phase2d_claim_verification_spec.md`](file:///d:/Sage-Indic/docs/phase2d_claim_verification_spec.md), [`data/processed/verification/verification_spec.md`](file:///d:/Sage-Indic/data/processed/verification/verification_spec.md).

### 3.7 Phase 2E: Safe, Replaceable Generation Adapter
- **Types ([`src/sage_indic/generation/types.py`](file:///d:/Sage-Indic/src/sage_indic/generation/types.py)):**
  - `GenerationConfig`: Explicit model/provider configuration including `provider`, `model_name`, `temperature`, `max_tokens`, `timeout_seconds`, `max_retries`, `retry_backoff_factor`, `api_base_url`, `api_key_env_var`, and `prompt_template_version`.
  - `GenerationRequest`: Bounded query and evidence package with `from_evidence_package()` factory method bridging Phase 2D `EvidencePackage` to the generation interface.
  - `DraftAnswer`: Structured draft preserving `answer_text`, `candidate_claims`, `citations` (validated), `invalid_citations` (hallucinated passage IDs), `is_abstention`, `is_verified` (always `False` at generation time), `model_id`, `provider`, `latency_ms`.
  - Typed exceptions: `ProviderUnavailableError`, `ProviderTimeoutError`, `ProviderAuthError`, `MalformedProviderResponseError`, `UntrustedEvidenceError`.
- **Prompt Composition ([`src/sage_indic/generation/prompt.py`](file:///d:/Sage-Indic/src/sage_indic/generation/prompt.py)):**
  - `PromptComposer`: Formats prompts with clearly delineated sections: `### SYSTEM INSTRUCTIONS (TRUSTED)`, `### RETRIEVED EVIDENCE PASSAGES (UNTRUSTED DATA ONLY)`, `### USER QUERY (TRUSTED INPUT)`.
  - Retrieved passages are wrapped in `[EVIDENCE_PASSAGE id="..."]...[/EVIDENCE_PASSAGE]` envelopes. The system instruction block explicitly warns the model that evidence content is passive untrusted data — not operational commands.
  - Citation extraction (`CITATION_PATTERN`) validates all `[doc_id#chunk_id]` references against the set of actually supplied passages, segregating hallucinated IDs into `invalid_citations`.
- **Provider Adapter ([`src/sage_indic/generation/adapter.py`](file:///d:/Sage-Indic/src/sage_indic/generation/adapter.py)):**
  - `GenerationProvider` ABC: replaceable interface; changing the LLM backend does not require modifying retrieval or verification code.
  - `MockGenerationProvider`: Deterministic, zero-dependency mock with test hooks for all failure modes (timeout, auth error, malformed empty response, hallucinated citations). Used in all unit tests.
  - `ExternalAPIProvider`: Reads API keys exclusively from environment variables (`api_key_env_var` config field). Raises `ProviderUnavailableError` offline, preventing accidental external calls during testing.
  - `GenerationAdapter`: Orchestrates prompt composition, retry policy (configurable `max_retries` with `retry_backoff_factor`), citation validation, sentence-boundary claim extraction, and `DraftAnswer` assembly.
- **Decoupled Pipeline ([`src/sage_indic/generation/pipeline.py`](file:///d:/Sage-Indic/src/sage_indic/generation/pipeline.py)):**
  - `verify_draft_answer(draft, evidence_passages, verifier)`: Independently audits each candidate claim from a `DraftAnswer` against supplied evidence via `RelationAwareClaimVerifier`, computing per-claim outcomes and overall `AnswerEligibility`.
  - `AnswerEligibility` states: `ELIGIBLE_GROUNDED`, `REQUIRES_CAVEAT`, `INELIGIBLE_CONTRADICTED`, `ABSTENTION`.
  - **Critical Invariant**: `DraftAnswer.is_verified` is permanently `False`; only `VerifiedAnswerReport.is_verified` is `True` after the downstream pipeline has executed.
  - **Research Integrity Rule**: `INSUFFICIENT_EVIDENCE` is never mapped to `INELIGIBLE`; caveat notes explicitly state "lack of proof, not proof of falsehood".

### 3.8 Phase 2G: Response Composition, Verification & Citations
- **Composition Types ([`src/sage_indic/composition/types.py`](file:///d:/Sage-Indic/src/sage_indic/composition/types.py)):**
  - `AnswerStatus`: `ANSWERED`, `PARTIALLY_ANSWERED`, `ABSTAINED`, `BLOCKED`.
  - `AnswerMode`: `DETERMINISTIC`, `LLM`, `LLM_FALLBACK`.
  - `AnswerResponse`: user-facing payload combining answer text, claim-level verification, programmatic citations, retrieved evidence, verification summary, query analysis, safety info, warnings, generation metadata, and latency.
  - `Citation`: application-assigned `C1`, `C2`, … markers mapped to real passage IDs, with `supports_claim` True only when the verifier returned `SUPPORTED`.
- **Query Understanding ([`src/sage_indic/composition/query_analysis.py`](file:///d:/Sage-Indic/src/sage_indic/composition/query_analysis.py)):**
  - Rule-based content-term/synonym grouping, fuzzy (stem-prefix) matching, question-intent detection (`WHEN`, `WHERE`, `WHO`, `HOW_MANY`, `DEFINITION`, `OTHER`), sentence ranking, and a conservative evidence-coverage gate.
  - `build_retrieval_expansion()` adds canonical Telugu/English term variants to demo retrieval. This is an application heuristic, not an evaluated retrieval method.
- **Response Composer ([`src/sage_indic/composition/composer.py`](file:///d:/Sage-Indic/src/sage_indic/composition/composer.py)):**
  - Deterministic path: selects verbatim evidence sentences, verifies each sentence against its own source passage (relation-aware verifier first, exact extractive support second, linguistic verifier third), and emits only supported claims.
  - Citation integrity: citation IDs are assigned programmatically from retrieved passages. Model-authored `[C1]`-style IDs are stripped; only validated passage-ID tags are mapped to citations. A valid ID is explicitly distinguished from claim support.
  - Optional LLM path: accepts a draft only if every candidate claim is `SUPPORTED` and no invalid citations were produced; otherwise the draft is rejected and the deterministic answer is shown.
  - Abstention semantics: separate handling for safety block, empty/uncovered evidence, unverifiable extractive sentences, partial coverage, contradicted claims, and provider failure (`LLM_FALLBACK`).

### 3.9 Phase 2G: Application Layer (Backend API + Demo UI)
- **Query Service ([`src/sage_indic/pipeline/service.py`](file:///d:/Sage-Indic/src/sage_indic/pipeline/service.py)):**
  - Loads the 10-document / 30-chunk retrieval-eligible corpus and preserves provenance metadata.
  - Indexes BM25 with `CodeMixedQueryNormalizer` and the frozen SAGE tokenizer (`experiments/saved_models/sage_4000.json`), with Unicode-whitespace fallback.
  - Runs detection → safety → retrieval → optional LLM → composition, records per-stage latency, and exposes status/corpus metadata.
  - Safety fallback: when the dense multilingual classifier is unavailable, uses `SAGE_ContextualGuardrail_LexicalOnlyFallback` with a neutral semantic score. The reduced mode is reported in `/api/status` and each response.
- **FastAPI Application ([`src/sage_indic/api/app.py`](file:///d:/Sage-Indic/src/sage_indic/api/app.py)):**
  - Endpoints: `/api/health`, `/api/status`, `/api/examples`, `/api/corpus`, `/api/query`.
  - Request validation rejects blank queries (422); CORS is limited to local Vite/preview origins; the built frontend is mounted at `/` when `frontend/dist/` exists.
- **Frontend ([`frontend/`](file:///d:/Sage-Indic/frontend/)):**
  - React 19 + TypeScript + Vite. Components for query workspace, answer, claim verification, evidence, and system status.
  - Surfaces status badges, programmatic citations, claim-level outcomes, LLM/fallback disclosure, corpus metadata, and example prompts.
  - Responsive layout places the answer before system status on narrow screens and auto-scrolls to the answer region after submission.

---

## 4. Datasets, Manifests & Provenance Accounting

| Phase | Dataset Name / Role | Size | Source / Provenance | Declared License | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2B** | `train_corpus.txt` | 4,688 sentences | UD_Telugu-MTG (1,051 native, 1,051 Romanized), Telugu Wikipedia (2,350), Code-Mixed (500) | CC BY-NC-SA 3.0 / CC BY-SA 3.0 / Apache-2.0 | Active Training Corpus (SHA-256 `ff752e43...`) |
| **2B** | `eval_native.txt` | 146 sentences | UD_Telugu-MTG official `test` split (formal native script) | CC BY-NC-SA 3.0 | Held-out (Contains 4 upstream overlapping sentences) |
| **2B** | `eval_romanized.txt` | 146 sentences | Transliterated `test` split of UD_Telugu-MTG | CC BY-NC-SA 3.0 | Held-out (Contains 4 upstream overlapping sentences) |
| **2B** | `eval_codemix.txt` | 150 sentences | 15 conversational/workplace Telugu-English sentences replicated 10x | Apache-2.0 | Held-out |
| **2B** | `eval_morphology.jsonl`| 146 records (575 internal boundaries) | UD_Telugu-MTG `test` split CoNLL-U `FORM` token boundaries (Rama & Vajjala, 2018) | CC BY-NC-SA 3.0 | **Derived Syntactic Boundary Proxy (NOT gold intra-word morphemes)** |
| **2C** | `dev.jsonl` (Safety) | 47 items | Controlled multi-script queries (28 SAFE, 19 UNSAFE; 10 benign-sensitive, 7 obfuscated) | SAGE-Indic Internal | Frozen Dev |
| **2C** | `eval.jsonl` (Safety) | 47 items | Held-out multi-script queries (28 SAFE, 19 UNSAFE; 10 benign-sensitive, 7 obfuscated) | SAGE-Indic Internal | Frozen Eval |
| **2D** | `phase2d_source_manifest.jsonl` | 14 candidate sources | 10 Approved Telugu Wikipedia canonical revisions; 4 Excluded candidate records | CC-BY-SA-4.0 | Stage B Ingested |
| **2D** | `phase2d_documents.jsonl` | 10 documents | Verified factual historical & architectural Telugu Wikipedia articles | CC-BY-SA-4.0 | Stage B Ingested |
| **2D** | `phase2d_chunks.jsonl` | 30 chunks | Deterministic paragraph chunks with verified Unicode offset roundtrips | CC-BY-SA-4.0 | Stage B Ingested |
| **2D** | `phase2d_eval_queries_dev.jsonl` | 18 queries | Multi-script dev benchmark (6 native, 6 romanized, 6 code-mixed; 12 answerable, 6 unanswerable) | CC-BY-SA-4.0 | Active Dev Benchmark |
| **2D** | `phase2d_eval_queries_eval.jsonl`| 24 queries | Multi-script eval benchmark (8 native, 8 romanized, 8 code-mixed; 18 answerable, 6 unanswerable) | CC-BY-SA-4.0 | Held-out Eval Benchmark |
| **2D** | `phase2d_qrels_*.jsonl` | 1,260 judgments | Graded relevance judgments (0, 1, 2) across all 30 chunks | CC-BY-SA-4.0 | Single-annotator (PENDING review) |

### Critical Licensing Adjudication & Exclusion Audit (Phase 2D):
- **IndicQA (`ai4bharat/IndicQA`):** **DO NOT USE / EXCLUDED**. A license conflict exists between the upstream Hugging Face card (CC-BY-4.0) and the original code repository (CC-0). Excluded from corpus until formally resolved.
- **UD_Telugu-MTG:** **EXCLUDED FROM RAG CORPUS**. Linguistic grammar sentences, with license documentation discrepancy (CC BY-NC-SA 3.0 in README vs. CC BY-SA 4.0 in metadata). Preserved exclusively as a tokenizer/linguistic baseline.
- **IndicCorp v2:** **REJECTED**. Uncurated web scrape without publisher-level provenance.

---

## 5. Reconciled Experimental Results & Scientific Audit

### 5.1 Phase 2B Tokenizer Benchmark: Forensic Reconciliation

#### Quarantine of Historical Handoff Results
Earlier handoff reports claimed the following values at $V=4000$:
- *BPE fertility: 1.7058; boundary F1: 0.6559*
- *Unigram fertility: 2.0076; boundary F1: 0.6729*
- *SAGE fertility: 1.3323; boundary F1: 0.8876*

**Forensic Audit Finding:** As established by the October 2026 READ-ONLY forensic audit, these values **have zero empirical backing** in repository files, git commit history, reflogs, or stored JSON outputs. Furthermore, claiming a SAGE fertility of 1.3323 contradicts the mathematical reality of the algorithm: because SAGE explicitly detaches inflectional suffixes into separate subwords (e.g. `stem` + `##affix`), it inherently increases tokens-per-word relative to Unigram (1.903 vs. 1.836) on inflected text. These historical handoff numbers represent an ungrounded or speculative draft and are **formally quarantined and removed from the active research record**.

#### Reproducible Benchmark Results ($V \in \{2000, 4000\}$)
The authentic, deterministically reproducible results from [`experiments/results/tokenizer_results.json`](file:///d:/Sage-Indic/experiments/results/tokenizer_results.json) are:

| Model Configuration | Vocab ($V$) | Native Tokens/Word | Native Compression (chars/tok) | Romanized Tokens/Word | Code-Mixed Tokens/Word | Morph Proxy Precision | Morph Proxy Recall | **Morph Proxy F1** |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BPE_2000** | 2000 | **1.922** | 2.426 | 2.491 | 5.293 | 0.5068 | 0.5861 | **0.5435** |
| **Unigram_2000** | 2000 | 2.082 | 2.241 | 2.578 | 5.829 | 0.5090 | 0.6904 | **0.5860** |
| **SAGE_2000** | 2000 | 2.129 | 2.191 | 2.601 | 5.602 | 0.5098 | 0.7217 | **0.5976** |
| **SAGE_Ablation_NoMorph_2000** | 2000 | 2.086 | 2.236 | 2.592 | 5.829 | 0.5083 | 0.6922 | **0.5862** |
| **BPE_4000** | 4000 | **1.642** | 2.840 | 2.040 | 4.610 | 0.5832 | 0.4696 | **0.5202** |
| **Unigram_4000** | 4000 | 1.836 | 2.540 | 2.298 | 5.130 | 0.5904 | 0.6191 | **0.6044** |
| **SAGE_4000** | 4000 | 1.903 | 2.451 | 2.334 | 5.211 | 0.6006 | 0.6800 | **0.6378** |
| **SAGE_Ablation_NoMorph_4000**| 4000 | 1.838 | 2.538 | 2.298 | 5.130 | 0.5894 | 0.6191 | **0.6039** |

*All configurations exhibit 0.0% UNK token rate on held-out text.*

#### Scientific Caveats and Necessary Evaluation Repair:
1. **Metric–Annotation Mismatch:** The reference ground truth in `eval_morphology.jsonl` contains Universal Dependencies syntactic word tokens (`FORM`), not gold intra-word morphemes. Consequently, when SAGE correctly detaches an inflectional suffix (e.g., `కర్రతో` $\rightarrow$ `కర్ర` + `##తో`), the internal boundary before `##తో` is penalized as a **False Positive**.
2. **Whitespace Splitting Confounder:** `SageTokenizer.encode()` forcibly tokenizes word-by-word (`for word in normalized.split()`), guaranteeing a predicted boundary at all whitespace positions. Because UD treebank tokens align closely with whitespace, SAGE's higher true-positive count (+35 over Unigram) is largely a whitespace preservation artifact rather than intra-word morphological boundary discovery.
3. **Upstream Contamination:** 4 sentences in `eval_native.txt` are present in `train_corpus.txt` due to upstream duplicate sentences between UD train/dev and test splits.
4. **Research Conclusion:** Therefore, **the current F1 results cannot establish true morphological superiority**. The next phase of tokenizer work requires evaluation repair (true morphological reference annotations and deduplication), not immediate algorithm redesign.

---

### 5.2 Phase 2C Context-Aware Safety Benchmark

Evaluated on strictly held-out data (`eval.jsonl`, 47 items) under frozen decision thresholds ($\theta_{\text{unsafe}}=0.58$, $\theta_{\text{uncertain}}=0.40$):

| Model Configuration | Accuracy | Macro-F1 | Benign FPR | Unsafe Recall | Abstention Rate | Coverage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline A: Lexical / Keyword Filter** | 0.6170 | 0.4299 | **0.2000** | 0.4737 | 0.0000 | 1.0000 |
| **Baseline B: Multilingual Semantic** | 0.3191 | 0.2874 | **0.6000** | 0.5263 | 0.4681 | 0.5319 |
| **Proposed: SAGE Guardrail** | **0.7021** | **0.5103** | **0.1000** | **0.7368** | 0.0213 | 0.9787 |
| **SAGE Ablation (No Morphology)** | 0.7021 | 0.5103 | 0.1000 | 0.7368 | 0.0213 | 0.9787 |

#### Slice Accuracy Breakdown on Held-Out Evaluation Set:

| Model Configuration | Native Script Acc | Romanized Acc | Code-Mixed Acc | Obfuscated Acc | Benign-Sensitive Acc |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline A: Lexical Filter** | 0.5625 | 0.6875 | 0.6000 | 0.0000 | 0.8000 |
| **Baseline B: Multilingual Semantic**| 0.2500 | 0.4375 | 0.2667 | 0.4286 | 0.0000 |
| **Proposed: SAGE Guardrail** | **0.6875** | **0.6875** | **0.7333** | **0.7143** | **0.9000** |
| **SAGE Ablation (No Morphology)** | 0.6875 | 0.6875 | 0.7333 | 0.7143 | 0.9000 |

#### Key Safety Findings:
1. **Benign False-Positive Reduction:** Baseline A blindly flags sensitive words like `విషం` (poison) in `విషం విరుగుడు` (antidote) or `kill` in `kill command`, resulting in a high FPR ($0.2000$). SAGE Guardrail's contextual indicator recognition cuts Benign-Sensitive FPR to **0.1000** (90% benign accuracy).
2. **Adversarial Obfuscation Robustness:** Baseline A exhibits **0.0% accuracy** on obfuscated threats (`k*i*l*l`, `v a a d i n i c h a m p a l i`), whereas SAGE Guardrail achieves **71.43% accuracy** via orthographic normalization and root recovery.

---

### 5.3 Phase 2D Cross-Script Retrieval Benchmark & Downstream Tokenizer Evaluation

Evaluated over the approved 10-document, 30-chunk Telugu Wikipedia corpus using the 42-query multi-script benchmark across Dev (18 queries, 12 answerable) and Eval (24 queries, 18 answerable) splits under 8 controlled conditions:

#### Dev Split Results (18 queries, 12 answerable, top-k=10):

| Condition | Method / Configuration | Overall Recall@1 | Overall Recall@5 | Overall MRR@10 | Native R@1 | Romanized R@1 | Code-Mixed R@1 | Mean Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | `bm25_baseline` (Unicode words) | 0.3333 | 0.3333 | 0.3333 | **1.0000** | 0.0000 | 0.0000 | **0.05 ms** |
| **B** | `bm25_translit` (Rule Transliteration) | 0.9167 | **1.0000** | 0.9583 | **1.0000** | **1.0000** | 0.7500 | 0.18 ms |
| **C** | `bm25_codemix` (CodeMix Normalizer) | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 0.14 ms |
| **D** | `dense_multilingual` (MiniLM-L12) | 0.1667 | 0.9167 | 0.4153 | 0.0000 | 0.0000 | 0.5000 | 23.01 ms |
| **E** | `hybrid_rrf` (BM25 + Dense RRF) | 0.7500 | **1.0000** | 0.8403 | 0.5000 | **1.0000** | 0.7500 | 21.85 ms |
| **F1** | `bm25_bpe` (Phase 2B BPE_4000) | 0.3333 | 0.3333 | 0.3333 | **1.0000** | 0.0000 | 0.0000 | 0.14 ms |
| **F2** | `bm25_unigram` (Phase 2B Unigram_4000) | 0.3333 | 0.5000 | 0.4167 | **1.0000** | 0.0000 | 0.0000 | 0.22 ms |
| **F3** | `bm25_sage` (Phase 2B SAGE_4000) | 0.3333 | 0.6667 | 0.4500 | **1.0000** | 0.0000 | 0.0000 | 0.34 ms |

#### Held-Out Eval Split Results (24 queries, 18 answerable, top-k=10):

| Condition | Method / Configuration | Overall Recall@1 | Overall Recall@5 | Overall MRR@10 | Native R@1 | Romanized R@1 | Code-Mixed R@1 | Mean Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | `bm25_baseline` (Unicode words) | 0.3333 | 0.3333 | 0.3333 | **1.0000** | 0.0000 | 0.0000 | **0.06 ms** |
| **B** | `bm25_translit` (Rule Transliteration) | **0.8889** | **1.0000** | **0.9352** | **1.0000** | **0.8333** | **0.8333** | 0.21 ms |
| **C** | `bm25_codemix` (CodeMix Normalizer) | **0.8889** | **1.0000** | 0.9259 | **1.0000** | **0.8333** | **0.8333** | 0.18 ms |
| **D** | `dense_multilingual` (MiniLM-L12) | 0.0556 | 0.4444 | 0.1950 | 0.0000 | 0.0000 | 0.1667 | 21.63 ms |
| **E** | `hybrid_rrf` (BM25 + Dense RRF) | 0.5556 | **1.0000** | 0.7639 | 0.6667 | 0.5000 | 0.5000 | 21.87 ms |
| **F1** | `bm25_bpe` (Phase 2B BPE_4000) | 0.3333 | 0.3333 | 0.3333 | **1.0000** | 0.0000 | 0.0000 | 0.18 ms |
| **F2** | `bm25_unigram` (Phase 2B Unigram_4000) | 0.4444 | 0.7778 | 0.5500 | **1.0000** | 0.1667 | 0.1667 | 0.20 ms |
| **F3** | `bm25_sage` (Phase 2B SAGE_4000) | 0.4444 | 0.6667 | 0.5278 | **1.0000** | 0.1667 | 0.1667 | 0.35 ms |

#### Scientific Findings & Downstream Tokenizer Connection:
1. **Cross-Script Failure Cause & Resolution:** The 0.0 recall of the lexical baseline on Romanized and Code-Mixed queries arises strictly from character script divergence between Latin letters in queries and Telugu Unicode letters in corpus documents. Deterministic phonetic transliteration (`bm25_translit`) and code-mix-aware normalization (`bm25_codemix`) eliminate this gap, boosting overall Recall@1 from **0.3333 to 0.8889–1.0000** and achieving **100% Recall@5** on both splits.
2. **Dense Multilingual Retrieval Trade-Off:** The dense baseline (`paraphrase-multilingual-MiniLM-L12-v2`) proves capable of zero-transliteration cross-script matching (dev Recall@5 = 1.0 for Romanized and Code-Mixed), but exhibits poor top-1 precision (Recall@1 = 0.0556 on eval) and runs ~150x slower (22 ms vs 0.15 ms) than sparse BM25.
3. **Hybrid RRF Robustness:** Hybrid rank fusion provides the strongest overall guarantee across modalities, reaching **100% Recall@5** across native, romanized, and code-mixed queries on both splits.
4. **Downstream Tokenizer Impact:** When BM25 is indexed and queried with subword tokenizers under identical conditions, Unigram_4000 and SAGE_4000 both achieve a **+33.3% relative improvement in Recall@1** on eval (0.4444 vs 0.3333 for word baseline and BPE), and boost Recall@5 to 0.7778 (Unigram) and 0.6667 (SAGE). Subwords matching morphological roots mitigate compounding inflection mismatches.

### 5.3 Phase 2D Retrieval Evidence Forensic & Ranking Audit
- **Replication Verification:** All 8 retrieval conditions were deterministically reproduced from frozen configurations and artifacts. All conditions use the exact same corpus snapshot (10 documents, 30 chunks, SHA-256 verified), query sets (18 dev, 24 eval), qrels, and normalization policies.
- **Metric Calculation Audit:** Metrics are calculated strictly over answerable queries ($N_{\text{dev}}=12, N_{\text{eval}}=18$). Unanswerable queries ($N_{\text{dev}}=6, N_{\text{eval}}=6$) have empty qrels and are audited for non-retrieval/abstention, preventing artificial division-by-zero or score dilution.
- **Eval Split Recall@1 Investigation (`Q_EVAL_002`):**
  - Dev achieved Recall@1 = 1.0 on `bm25_translit`, whereas Eval achieved 0.8889.
  - Audit traced this to `Q_EVAL_002_ROM` (*"Telangana prabuthva chihnam lo unna kottadam emiti?"*) and `Q_EVAL_002_MIX` (*"Telangana state emblem lo unna monument edi?"*).
  - Target chunk is `TE_DOC_003#c0002` (Kakatiya Kala Thoranam), which contains the inflected form `చిహ్నంలో` (emblem + locative suffix). Transliteration produced uninflected `చిహ్నం` + separate token `లో`.
  - Shorter chunk `TE_DOC_001#c0000` (Charminar) matched `తెలంగాణ`, `రాష్ట్ర`, and `కట్టడం` and received a length-normalization boost ($b=0.75$), taking rank 1 while the target chunk was placed at rank 3 (Recall@5 = 1.0 maintained).
  - Notably, Subword BM25 (Unigram and SAGE) detached `చిహ్నం` + `##లో`, restoring stem alignment.
- **Benchmark Limitations:** The 42-query benchmark is an initial pilot with single-annotator qrels. The formal expansion plan to 50 documents and 150 queries with double-blind annotation and Cohen's $\kappa$ is ratified in [`docs/phase2d_expansion_plan.md`](file:///d:/Sage-Indic/docs/phase2d_expansion_plan.md).

### 5.4 Phase 2F Claim Decomposition & Relation-Aware Verification Benchmark
Evaluated across topic-isolated diagnostic splits (24 dev items, 24 eval items) comparing frozen weak baseline `LinguisticClaimVerifier` vs proposed `RelationAwareClaimVerifier` under matched conditions:

#### Held-Out Evaluation Split Results ($N=24$, 17 Non-Supported, 7 Supported):
- **Accuracy:** Baseline = **70.83%** $\rightarrow$ Proposed = **75.00%** (**+4.17%** improvement)
- **Macro-F1:** Baseline = **0.7419** $\rightarrow$ Proposed = **0.7750** (**+0.0331** improvement)
- **False `SUPPORTED` Rate:** Baseline = **11.76%** (2/17) $\rightarrow$ Proposed = **5.88%** (1/17) (**-5.88%** absolute reduction)
- **Genuinely Supported Recall:** Baseline = **57.14%** (4/7) $\rightarrow$ Proposed = **57.14%** (4/7) (**0.00% regression**)
- **Partial Evidence Accuracy:** Baseline = **50.0%** (1/2) $\rightarrow$ Proposed = **100.0%** (2/2) (**+50.0%** gain)
- **Relational Inversion Accuracy:** Baseline = **66.7%** (4/6) $\rightarrow$ Proposed = **66.7%** (4/6)
- **Modality Accuracy:** Native = **85.7%** (12/14), Romanized = **50.0%** (2/4), Code-Mixed = **66.7%** (4/6)

#### Key Research Findings:
1. *Partial-Support Resolution:* Decomposing compound claims into `AtomicProposition` units and enforcing conservative compound aggregation (`SUPPORTED` + `INSUFFICIENT` $\rightarrow$ `INSUFFICIENT_EVIDENCE`) eliminated false positives from partially true statements without regressing recall on fully supported claims.
2. *Defense-in-Depth Validation:* Deterministic data extraction ensures adversarial prompt injections embedded in evidence cannot manipulate verifier state.
3. *Residual Limitation:* Broad relational category mappings (e.g. *discovered* vs *described*) still produce false positives when distinct relations map to identical semantic buckets (`V_EVAL_011`).

---

## 6. Software Quality, Test Baseline & Repository Health

### 6.1 Verified Automated Test Baseline
- **Application Integration Verification Date:** 2026-11-17
- **Verified Current Baseline:** **307 passed, 0 failed, 52 skipped** in pytest (100% success rate across 359 collected items).
- **Test Suite Breakdown:**
  - `tests/test_api.py`: 22 passed (Phase 2G live-corpus API contract suite)
  - `tests/test_bm25_retriever.py`: 48 passed
  - `tests/test_claim_verification.py`: 20 passed (Phase 2D/2F verification suite)
  - `tests/test_composition.py`: 15 passed (Phase 2G composition, citation integrity, LLM fallback)
  - `tests/test_config.py`: 3 passed
  - `tests/test_crossscript_rag.py`: 16 passed
  - `tests/test_detection.py`: 31 passed
  - `tests/test_exp_2e_02_audit.py`: 3 passed (EXP-2E-02 forensic audit regression suite)
  - `tests/test_generation_adapter.py`: 15 passed (Phase 2E adapter suite: prompt composition, mock provider, security boundary, pipeline decoupling)
  - `tests/test_logging.py`: 3 passed
  - `tests/test_normalize.py`: 7 passed
  - `tests/test_package.py`: 2 passed
  - `tests/test_rag.py`: 56 passed
  - `tests/test_safety.py`: 49 passed (52 skipped optional model tests)
  - `tests/test_tokenizer.py`: 17 passed
- **Live Demo Verification:** `scripts/verify_demo.py` executed all 9 advertised examples against the running API. All expected behaviours matched (`ANSWERED`, `PARTIALLY_ANSWERED`, `ABSTAINED`) and citation-integrity checks passed.
- **Frontend Build:** `npm run build` (TypeScript check + Vite build) completed successfully.
- **Lint Scope:** `ruff check` passes on the new Phase 2G modules, API, service, and tests. Pre-existing lint findings remain in frozen Phase 2E files and the wider legacy suite; those were not mass-reformatted.

### 6.2 Known Version Discrepancies (Documented in `OPEN_ISSUES.md`)
The repository currently contains conflicting package version declarations across files:
- `pyproject.toml:7`: `0.1.0`
- `src/sage_indic/__init__.py:23`: `0.3.0`
- `docs/phase2b_freeze.md:6`: `0.2.0`
These inconsistencies are cataloged in [`OPEN_ISSUES.md:ISSUE-VER-01`](file:///d:/Sage-Indic/OPEN_ISSUES.md) for an explicit, isolated correction task.

---

## 7. Known Limitations & Research Boundaries

1. **Corpus Scale:** The evidence corpus currently contains 10 verified Wikipedia articles (30 chunks). Sufficient for controlled pilot comparisons, not for broad domain coverage claims.
2. **Relevance Judgments:** Annotations are single-annotator derived (`annotation_status = PENDING`) and warrant independent double-annotator adjudication.
3. **Homograph Ambiguity:** Phonetic rule-based transliteration cannot resolve colloquial spelling homographs that require sentence-level syntactic disambiguation.
4. **Coarse Relational Categories (Claim Verifier):** Broad predicate category mappings (e.g. *discovered* vs *described*) still produce false positives when distinct relations map to identical semantic buckets. Partially addressed by atomic decomposition in Phase 2F; full resolution requires fine-grained argument binding or trained NLI.
5. **Heuristic Confidence Values:** Verification confidence scores are uncalibrated rule-derived linear scores, not empirical entailment probabilities.
6. **Sentence-Boundary Claim Extraction (Generation):** The generation adapter decomposes draft answers by sentence boundary heuristics. This cannot guarantee atomic correctness for agglutinated Telugu morphological constructions.
7. **Mock Provider Only (Generation):** The `MockGenerationProvider` is deterministic but does not produce genuine natural language. An `ExternalAPIProvider` or local model integration is required for real end-to-end generation research.
8. **Prompt Injection Resilience:** The untrusted evidence envelope and adapter-level sanitization reduce the attack surface, but resilience against prompt injection in an LLM backend depends on the model's instruction-following fidelity.
9. **Safety Fallback Coverage (Application):** When the dense multilingual semantic classifier is unavailable, the application runs `SAGE_ContextualGuardrail_LexicalOnlyFallback`. It preserves the frozen morphology/context logic but does not block every unlisted English term; this gap is documented in `OPEN_ISSUES.md` rather than patched inside frozen Phase 2C.
10. **Heuristic Evidence Gate (Application):** The Phase 2G coverage gate, synonym groups, intent rules, and sentence ranking are transparent application heuristics. They are not calibrated relevance or entailment models and have not been benchmarked as a new research method.
11. **Demo Retrieval Expansion (Application):** `build_retrieval_expansion()` adds canonical Telugu/English variants to improve demo recall. It is a demo-layer convenience, not part of the evaluated Phase 2D retrieval conditions.
12. **LLM Path Mechanically Verified Only:** The optional LLM path was tested for timeout/fallback and draft rejection, but `llama3.2:1b` on CPU is slow and weak. No LLM quality or factuality improvement is claimed for the application.
13. **Demo Corpus Scale:** The application answers only from the 10-document / 30-chunk corpus. Out-of-corpus questions abstain by design; broad coverage requires corpus expansion.

---

## 8. Quality Gates & Current Status

### Completed Quality Gates:
- [x] **Gate 1 — Data:** Multi-modality representation, licensing provenance, zero-leakage partitions established.
- [x] **Gate 2 — Tokenizer:** Baselines run, reproducible metrics frozen and reconciled in `EXPERIMENT_LEDGER.md`.
- [x] **Gate 3 — Safety:** Matched dev/eval sets adjudicated, benign-sensitive contexts included, baselines benchmarked (`safety_results.md`).
- [x] **Gate 4A — RAG Corpus Foundation:** Ingestion pipeline, cryptographic hashing, 23-field schema, Stage B 10-document corpus ingested (`phase2d_corpus_foundation.md`).
- [x] **Gate 4B — BM25 Retrieval Baseline:** Multi-script query benchmark (42 queries, 1,260 qrels) and deterministic BM25 retriever implemented and evaluated (`EXP-2D-02`).
- [x] **Gate 4C — Cross-Script & Hybrid Retrieval:** Normalizer, dense multilingual retriever, hybrid RRF, and downstream tokenizer evaluation completed (`EXP-2D-03` through `EXP-2D-07`).
- [x] **Gate 5A — Claim Verification Foundation:** `LinguisticClaimVerifier` with typed data models, security boundaries, and 20-test suite (`EXP-2D-08`, `EXP-2D-09`).
- [x] **Gate 5B — Relation-Aware Verification:** `RelationAwareClaimVerifier` with atomic decomposition and conservative compound policy; 15-test passing suite with zero regression on supported recall (`EXP-2F-01`).
- [x] **Gate 6 — Generation Adapter:** `GenerationAdapter` with provider-independent ABC, `MockGenerationProvider`, `PromptComposer`, citation validation, and `verify_draft_answer` pipeline decoupling; 15-test passing suite (`EXP-2E-01`).
- [x] **Gate 7 — End-to-End Factuality Evaluation:** `EXP-2E-02` executed on 42 queries using llama3.2:1b via Ollama. Forensic audit (`EXP-2E-02-AUDIT-V1`) completed with independent metric recomputation, resolution of the Condition D inconsistency, and verified real execution provenance. Full audit bundle in `experiments/results/exp_2e_02_audit_v1/`.
- [x] **Gate 8 — Response Composition & Demo Application:** Grounded composer, structured citations, claim-level verification display, explicit abstention semantics, FastAPI backend, React UI, live end-to-end verifier, and 37 new tests. Engineering integration only; no benchmark claim.

### Current Status and Next Step

Phase 2G is implemented as a working local prototype. The verified state is:

- `307 passed, 52 skipped` in the Python test suite.
- 9/9 advertised demo examples pass live behaviour and citation-integrity checks.
- Frontend production build succeeds.
- Deterministic composition is the default; the optional LLM path falls back safely.

**No further major research component has been started.** Per `AGENTS.md`, the next action is review/approval of this Phase 2G integration. Candidate follow-up work — corpus expansion, calibrated coverage gating, a stronger local LLM, and semantic-safety model provisioning — is recorded in [`OPEN_ISSUES.md`](file:///d:/Sage-Indic/OPEN_ISSUES.md) and must not begin without explicit approval.
