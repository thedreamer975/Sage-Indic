# SAGE-Indic: Open Issues and Research Backlog

**Document Version:** 1.1.0  
**Repository State:** Audited October 2026; Phase 2G integration November 2026  
**Status:** Active Research Tracking  

This ledger records all identified scientific limitations, data defects, contract mismatches, and engineering backlog items established during the October 2026 READ-ONLY audits. Items are grouped by thematic area and must be addressed via explicit, isolated tasks.

---

## 1. Research Validity Issues

| Issue ID | Severity | Component | Summary | Current Evidence / File References | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-RV-01** | **CRITICAL** | Tokenizer Evaluation | **Metric–Annotation Mismatch:** Reference dataset (`eval_morphology.jsonl`) contains Universal Dependencies syntactic word tokens (`FORM`), not gold intra-word morphemes. Correctly detached affixes (`-తో`, `-లో`) are penalized as False Positives. | [`src/sage_indic/tokenizer/evaluation.py:79-116`](file:///d:/Sage-Indic/src/sage_indic/tokenizer/evaluation.py#L79-L116), [`docs/phase2b_freeze.md:81-85`](file:///d:/Sage-Indic/docs/phase2b_freeze.md#L81-L85) | Confirmed Defect |
| **ISSUE-RV-02** | **HIGH** | Tokenizer Evaluation | **Confounding Whitespace Advantage:** `SageTokenizer.encode()` splits by Python whitespace (`normalized.split()`), forcing predicted boundaries at all whitespace positions. This inflates true positive counts against whitespace-aligned treebank tokens. | [`src/sage_indic/tokenizer/sage_tokenizer.py:106`](file:///d:/Sage-Indic/src/sage_indic/tokenizer/sage_tokenizer.py#L106) | Confirmed Defect |
| **ISSUE-RV-03** | **MEDIUM** | Tokenizer Data | **Upstream Train/Eval Overlap (Data Contamination):** 4 evaluation sentences (2.7% of the 146 held-out test set) appear in `train_corpus.txt` due to upstream sentence duplication in `UD_Telugu-MTG` train/dev and test splits. | [`scripts/prepare_tokenizer_data.py:196-225`](file:///d:/Sage-Indic/scripts/prepare_tokenizer_data.py#L196-L225), sentences: *'నేను బీదవాణ్ణి .', 'నేను రేపు వస్తాను .', 'దేవుడు అంతటా ఉన్నాడు .', 'అతనికి తెలుగు వచ్చు .'* | Confirmed Defect |
| **ISSUE-RV-04** | **CRITICAL** | Documentation | **Historical Ghost Results:** Earlier handoff claims (BPE fertility 1.7058, F1 0.6559; Unigram fertility 2.0076, F1 0.6729; SAGE fertility 1.3323, F1 0.8876) have zero empirical backing in code, git history, or artifacts, and contradict algorithm physics. Must be quarantined from all manuscripts. | Audited across git tree, reflogs, and commit history. | Quarantined / Invalid |

---

## 2. Tokenizer Issues

| Issue ID | Severity | Component | Summary | Current Evidence / File References | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-TOK-01** | **HIGH** | Evaluation Harness | **Subword Offset Finding Risk:** `compute_morphological_alignment()` locates subword spans using `text.find(clean_tok, curr_pos)`. If `clean_tok` is empty (e.g. standalone Metaspace token ` `), `curr_pos` does not advance, risking index misalignment. | [`src/sage_indic/tokenizer/evaluation.py:96-103`](file:///d:/Sage-Indic/src/sage_indic/tokenizer/evaluation.py#L96-L103) | Open |
| **ISSUE-TOK-02** | **LOW** | Morphology Rules | **Duplicate Verbal Suffix Entry:** The verbal suffix `"తున్నారు"` is duplicated in the tuple. | [`src/sage_indic/tokenizer/morphology.py:45,47`](file:///d:/Sage-Indic/src/sage_indic/tokenizer/morphology.py#L45-L47) | Open |
| **ISSUE-TOK-03** | **MEDIUM** | Morphology Rules | **Non-Concatenative Sandhi Transformations:** SAGE currently applies concatenative affix stripping and does not invert morpho-phonological vowel merger rules ($V_1 + V_2 \rightarrow V_3$). | [`docs/phase2b_freeze.md:138`](file:///d:/Sage-Indic/docs/phase2b_freeze.md#L138) | Known Limitation |
| **ISSUE-TOK-04** | **LOW** | Tokenizer Model | **Compound Words (Samasas):** Polysyllabic Sanskrit loan compounds without inflectional suffixes are treated as monolithic stems unless segmented by statistical subword model. | [`docs/phase2b_freeze.md:139`](file:///d:/Sage-Indic/docs/phase2b_freeze.md#L139) | Known Limitation |

---

## 3. Retrieval (Phase 2D) Issues

| Issue ID | Severity | Component | Summary | Current Evidence / File References | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-RET-01** | **BLOCKER** | Retrieval Evaluation | **Missing Query & Relevance Dataset:** Resolved via `scripts/build_phase2d_benchmark.py` generating 42 queries and 1,260 qrels across dev (18 queries) and eval (24 queries) splits. | [`data/processed/rag/phase2d_eval_queries_*.jsonl`](file:///d:/Sage-Indic/data/processed/rag/) | **RESOLVED** |
| **ISSUE-RET-02** | **BLOCKER** | Retrieval Algorithm | **Retriever Implementations are Blocked Stubs:** Resolved. `BM25Retriever`, `MultilingualDenseRetriever`, and `HybridRetriever` implemented with full provenance contracts and security boundaries. | [`src/sage_indic/rag/retriever.py`](file:///d:/Sage-Indic/src/sage_indic/rag/retriever.py), [`dense.py`](file:///d:/Sage-Indic/src/sage_indic/rag/dense.py), [`hybrid.py`](file:///d:/Sage-Indic/src/sage_indic/rag/hybrid.py) | **RESOLVED** |
| **ISSUE-RET-03** | **HIGH** | Retrieval Benchmark | **Missing Experiment Harness:** Resolved. `experiments/run_retrieval_experiment.py` implemented supporting 8 controlled conditions with versioned JSON outputs. | [`experiments/run_retrieval_experiment.py`](file:///d:/Sage-Indic/experiments/run_retrieval_experiment.py) | **RESOLVED** |
| **ISSUE-RET-04** | **MEDIUM** | Data Licensing | **External Dataset License Discrepancies:** IndicQA has conflicting upstream licenses (CC-BY-4.0 on HF card vs. CC-0 in author repo); IndicCorp v2 lacks publisher-level provenance. Both are excluded from the factual evidence corpus. | [`data/processed/rag/phase2d_source_manifest.jsonl:11-13`](file:///d:/Sage-Indic/data/processed/rag/phase2d_source_manifest.jsonl#L11-L13) | Quarantined / Excluded |
| **ISSUE-RET-05** | **LOW** | Corpus Scale | **Corpus Stage B Size:** Current evidence corpus contains 10 verified encyclopedic articles (30 chunks). While sufficient for pilot benchmark validation, broad domain coverage requires gradual expansion. | [`data/processed/rag/phase2d_documents.jsonl`](file:///d:/Sage-Indic/data/processed/rag/phase2d_documents.jsonl) | Known Limitation |
| **ISSUE-RET-06** | **MEDIUM** | Cross-Script Normalizer | **Transliteration Ambiguity for Romanized Homographs:** Deterministic rule-based phonetic transliteration resolves high-frequency forms but cannot disambiguate phonetically ambiguous homographs without syntactic context. | [`src/sage_indic/rag/normalizer.py`](file:///d:/Sage-Indic/src/sage_indic/rag/normalizer.py) | Active Research Backlog |
| **ISSUE-RET-07** | **LOW** | System Latency | **Dense vs Lexical Latency Gap:** Multilingual dense retrieval incurs ~22ms per query compared to ~0.15ms for BM25 with normalizer. Hybrid RRF inherits dense latency (~22ms). | Measured in `EXP-2D-05` and `EXP-2D-06` | Known Trade-off |
| **ISSUE-RET-08** | **MEDIUM** | Benchmark Scale | **Generalization Boundary:** While comparative trends are consistent between dev and eval splits, the 42-query benchmark is a pilot evaluation. Large-scale claims require broader independent topic evaluation. | Evaluation specifications | Known Limitation |
| **ISSUE-RET-09** | **MEDIUM** | Benchmark Annotations | **Single-Annotator Pilot Labels:** Pilot benchmark relevance judgments were produced by a single annotator. Formal expansion to 50 documents / 150 queries requires double-blind annotation and Cohen's $\kappa$ reporting as specified in `docs/phase2d_expansion_plan.md`. | [`docs/phase2d_expansion_plan.md`](file:///d:/Sage-Indic/docs/phase2d_expansion_plan.md) | Expansion Specification Ratified |

---

## 4. Claim Verification (Phase 2D/2F) Issues

| Issue ID | Severity | Component | Summary | Current Evidence / File References | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-VERIF-01** | **HIGH** | Neural NLI Generalization | **Target-Language Neural NLI Calibration:** Generic multilingual NLI models (e.g. XLM-RoBERTa, IndicBERT) require target-language fine-tuning on Telugu before deployment. Untested neural NLI models cannot be assumed reliable without Telugu-specific benchmark validation. | [`docs/phase2d_claim_verification_spec.md`](file:///d:/Sage-Indic/docs/phase2d_claim_verification_spec.md) | Policy Enforced |
| **ISSUE-VERIF-02** | **LOW** | Lexical Verifier | **Complex Figurative Refutations:** Rule-based verification accurately detects numerical, polarity, entity, and multi-passage conflicts, but cannot resolve complex implicit metaphorical refutations without full syntactic parsing. | [`src/sage_indic/verification/verifier.py`](file:///d:/Sage-Indic/src/sage_indic/verification/verifier.py) | Known Limitation |
| **ISSUE-VERIF-03** | **HIGH** | Verifier Failure Mode | **Partial-Support Inflation via Bag-of-Words:** Addressed in Phase 2F via `RelationAwareClaimVerifier` with atomic conjunction decomposition and conservative compound composition. Partial evidence accuracy improved from 50% to 100% on eval, cutting false `SUPPORTED` rate from 11.8% to 5.88% with zero regression on genuine supported recall. | [`docs/verification_error_analysis.md`](file:///d:/Sage-Indic/docs/verification_error_analysis.md), `EXP-2F-01` | **PARTIALLY RESOLVED** |
| **ISSUE-VERIF-04** | **MEDIUM** | Verifier Scoring | **Heuristic Uncalibrated Verification Confidence:** The confidence score returned by verifiers is derived from uncalibrated linear heuristic formulas, not a probabilistic entailment margin. It must not be cited as a calibrated probability. | [`src/sage_indic/verification/verifier.py:212,240`](file:///d:/Sage-Indic/src/sage_indic/verification/verifier.py#L212), `EXP-2D-09`, `EXP-2F-01` | Known Limitation |
| **ISSUE-VERIF-05** | **HIGH** | Relational Extraction | **Coarse Predicate Categories & Argument Inversion:** Rule-based predicate categorization groups semantically distinct actions into broad categories (e.g. *discovered* vs *described* both in `discovery_or_study`). Resolving within-category directional mismatches requires fine-grained argument binding or target-language calibrated NLI. | `V_EVAL_011`, [`docs/verification_error_analysis.md:Section 7`](file:///d:/Sage-Indic/docs/verification_error_analysis.md) | Active Research Backlog |

---

## 4. Safety (Phase 2C) Issues

| Issue ID | Severity | Component | Summary | Current Evidence / File References | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-SAF-01** | **MEDIUM** | Safety Dataset | **Diagnostic Dataset Scale:** Safety evaluation set comprises 94 total instances (47 dev, 47 eval), designed for diagnostic edge-case stress testing rather than statistical significance at web-scale. | [`docs/safety_data.md:98-103`](file:///d:/Sage-Indic/docs/safety_data.md#L98-L103) | Known Limitation |
| **ISSUE-SAF-02** | **LOW** | Safety Dataset | **Dialect Diversity:** Colloquial native expressions primarily represent Coastal Andhra and Telangana colloquialisms; Rayalaseema and tribal dialects are underrepresented. | [`docs/safety_data.md:102`](file:///d:/Sage-Indic/docs/safety_data.md#L102) | Known Limitation |
| **ISSUE-SAF-03** | **LOW** | Test Suite | **Pytest Deprecation Warnings:** 5 class-scoped fixtures in `tests/test_safety.py` trigger `PytestRemovedIn10Warning` because instance attributes are used without `@classmethod`. | [`tests/test_safety.py`](file:///d:/Sage-Indic/tests/test_safety.py) warnings summary | Open Maintenance |

---

## 5. Versioning and Interface Issues

| Issue ID | Severity | Component | Summary | Current Evidence / File References | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-VER-01** | **MEDIUM** | Project Packaging | **Package Version Discrepancies:** `pyproject.toml` declares `0.1.0`, `src/sage_indic/__init__.py` declares `0.3.0`, while freeze documentation and `progress.md` cite `0.2.0`. | [`pyproject.toml:7`](file:///d:/Sage-Indic/pyproject.toml#L7), [`src/sage_indic/__init__.py:23`](file:///d:/Sage-Indic/src/sage_indic/__init__.py#L23), [`docs/phase2b_freeze.md:6`](file:///d:/Sage-Indic/docs/phase2b_freeze.md#L6) | Open |
| **ISSUE-VER-02** | **MEDIUM** | Configuration | **Language Category Enum Discrepancy:** `configs/default.yaml` uses `TELUGU_ENGLISH_CODEMIX`, whereas `src/sage_indic/types.py` implements `TELUGU_ENGLISH_CODE_MIXED`. | [`configs/default.yaml:2`](file:///d:/Sage-Indic/configs/default.yaml#L2), [`src/sage_indic/types.py:10`](file:///d:/Sage-Indic/src/sage_indic/types.py#L10) | Open |
| **ISSUE-VER-03** | **LOW** | Configuration | **YAML Parsing vs Environment Loader:** Repository contains YAML configs (`configs/default.yaml`, `configs/data.yaml`), but `src/sage_indic/config.py` only reads `.env` variables and does not parse YAML files. | [`src/sage_indic/config.py`](file:///d:/Sage-Indic/src/sage_indic/config.py) | Open |

---

## 6. ACM Paper Alignment & Scholarly Positioning

| Issue ID | Severity | Component | Summary | Current Evidence / File References | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-ACM-01** | **HIGH** | Paper Alignment | **Knowledge-Guided Representation Claim:** Current SAGE tokenizer implements heuristic affix pre-segmentation. To align strongly with special-issue themes on knowledge-guided NLP, affix dictionaries and akshara rules must be formally situated as symbolic morphological domain knowledge constraining statistical subword inference. | [`docs/tokenizer_design.md:56-86`](file:///d:/Sage-Indic/docs/tokenizer_design.md#L56-L86) | Strategic Decision Pending |
| **ISSUE-ACM-02** | **HIGH** | Paper Alignment | **Evidence Verification vs Factuality:** The paper must avoid conflating retrieval quality with response factuality. Retrieval evidence is untrusted data; factual reliability requires atomic claim verification against retrieved evidence passages (Phases 2E–2F). | [`AGENTS.md`](file:///d:/Sage-Indic/AGENTS.md), [`docs/PRD.md:699-740`](file:///d:/Sage-Indic/docs/PRD.md#L699-L740) | Architecture Invariant |
| **ISSUE-ACM-03** | **MEDIUM** | Paper Alignment | **Empirical Claims Integrity:** Papers must report the reproducible tokens/word (1.903) and boundary F1 (0.6378) at $V=4000$ alongside acknowledged limitations regarding treebank boundary proxy annotations. Under no circumstances should ghost values (1.3323 fertility, 0.8876 F1) appear in scholarly drafts. | Audited baseline. | Research Integrity Rule |

---

## 7. Generation Adapter (Phase 2E) Issues

| Issue ID | Severity | Component | Summary | Current Evidence / File References | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-GEN-01** | **MEDIUM** | Claim Extraction | **Sentence-Boundary Decomposition Correctness:** The current `_extract_candidate_claims()` method in `GenerationAdapter` splits answers at `.`, `!`, `?`, `।` boundaries. This cannot guarantee atomic decomposition for agglutinated Telugu constructions where a single grammatical sentence may contain multiple distinct factual claims. | [`src/sage_indic/generation/adapter.py`](file:///d:/Sage-Indic/src/sage_indic/generation/adapter.py#L167-L200) | Known Limitation / Research Backlog |
| **ISSUE-GEN-02** | **HIGH** | Real LLM Integration | **Mock Provider Does Not Produce Natural Language:** `MockGenerationProvider` generates deterministic answers by extracting the first sentence of the top evidence passage. Real end-to-end factuality research requires integrating a real LLM provider (`ExternalAPIProvider` or a local quantized model) with actual Telugu generation capability. End-to-end factuality evaluation is NOT claimed on mock responses. | [`EXP-2E-01`](file:///d:/Sage-Indic/EXPERIMENT_LEDGER.md) | Known Limitation / Future Milestone |
| **ISSUE-GEN-03** | **MEDIUM** | Prompt Injection Resilience | **Model-Dependent Injection Resistance:** The adapter's `[EVIDENCE_PASSAGE]` envelopes and `PromptComposer` system warning reduce the attack surface for adversarial content in retrieved passages. However, resilience depends on the underlying LLM's instruction-following fidelity; no universal immunity is claimed. Tests verify the adapter's envelope structure and sanitization, not arbitrary model behavior. | [`src/sage_indic/generation/prompt.py`](file:///d:/Sage-Indic/src/sage_indic/generation/prompt.py), `tests/test_generation_adapter.py::TestSecurityBoundary` | Known Limitation (Documented in Tests) |
| **ISSUE-GEN-04** | **LOW** | Evaluation Design | **End-to-End Factuality Evaluation — AUDITED:** `EXP-2E-02` completed 2026-10-16 on 42 queries using llama3.2:1b via Ollama. Forensic audit (`EXP-2E-02-AUDIT-V1`) confirmed Condition A 90% retrieval hit rate vs 30% baseline (Condition C), and 20% vs 6.7% fact-correct rate. Audit resolved Condition D anomaly: 42/42 abstentions reported alongside 2/30 fact-correct answers was caused by lack of abstention guard in `aggregate_condition_metrics` and unconditional `is_abstention=True` in adapter; true non-abstained fact-correct count under Condition D is 0/30. Zero verifier divergence (42/42) traced to short 80-token fragments containing no compound conjunctions. Full audit artifacts in `experiments/results/exp_2e_02_audit_v1/`. | `EXP-2E-02`, `EXP-2E-02-AUDIT-V1` | **AUDITED & QUALIFIED** |

---

## 8. Forensic Audit (EXP-2E-02) Issues

| Issue ID | Severity | Component | Summary | Current Evidence / File References | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-AUDIT-01** | **HIGH** | Metric Aggregation | **Abstention–Fact-Correct Overlap:** `check_fact_correctness()` and `aggregate_condition_metrics()` did not verify `not r["is_abstention"]`, allowing abstaining answers containing coincidental keywords to be counted as fact-correct. Regression test added. | [`experiments/run_exp_2e_02.py:274-282,482`](file:///d:/Sage-Indic/experiments/run_exp_2e_02.py#L274-L282), [`tests/test_exp_2e_02_audit.py`](file:///d:/Sage-Indic/tests/test_exp_2e_02_audit.py) | Confirmed Defect / Regression Test Added |
| **BUG-AUDIT-02** | **MEDIUM** | Generation Adapter | **Unconditional Abstention Assignment on Empty Evidence:** `_check_abstention()` unconditionally assigned `is_abstention=True` when `not request.evidence_passages`, masking whether the LLM actually followed the instruction to state lack of evidence or emitted hallucinations. | [`src/sage_indic/generation/adapter.py:346-347`](file:///d:/Sage-Indic/src/sage_indic/generation/adapter.py#L346-L347) | Confirmed Defect |
| **BUG-AUDIT-03** | **MEDIUM** | Reproducibility | **Omission of Conditions C & D Per-Query Records:** `run_exp_2e_02.py` line 915 persists only `results_cond_a` to `per_query_results.json`. Per-query records for Conditions C and D were not saved to disk. | [`experiments/run_exp_2e_02.py:915-917`](file:///d:/Sage-Indic/experiments/run_exp_2e_02.py#L915-L917) | Open Improvement |
| **BUG-AUDIT-04** | **LOW** | Reproducibility | **Omission of Cache Save After Condition D:** `run_exp_2e_02.py` line 800 omits saving `generation_cache.json` after Condition D, causing Condition D LLM responses to be omitted from the disk cache. | [`experiments/run_exp_2e_02.py:791-801`](file:///d:/Sage-Indic/experiments/run_exp_2e_02.py#L791-L801) | Open Improvement |
| **LIM-AUDIT-01** | **HIGH** | Evaluation Design | **80-Token Truncation Impact:** The 80-token cap severely truncated Telugu native answers, causing prompt repetition and preventing full sentence completion and citation tag emission. | [`experiments/results/exp_2e_02_audit_v1/execution_provenance.md`](file:///d:/Sage-Indic/experiments/results/exp_2e_02_audit_v1/execution_provenance.md) | Documented Limitation |
| **LIM-AUDIT-02** | **HIGH** | Evaluation Design | **Verifier Divergence Under-Exercised:** The 42 pilot queries and short generations did not elicit compound coordinate claims with relational conflicts, causing RelationAware and Linguistic verifiers to produce identical (0 divergence) decisions. | [`experiments/results/exp_2e_02_audit_v1/verifier_divergence_analysis.md`](file:///d:/Sage-Indic/experiments/results/exp_2e_02_audit_v1/verifier_divergence_analysis.md) | Documented Limitation |

---

## 9. Phase 2G Application Integration Issues

| Issue ID | Severity | Component | Summary | Current Evidence / File References | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-APP-01** | **MEDIUM** | Safety Fallback | **Lexical-Only Fallback Coverage Gap:** When the dense multilingual semantic classifier is unavailable, the app runs `SAGE_ContextualGuardrail_LexicalOnlyFallback`. The fallback preserves frozen morphology/context logic but does not block every unlisted term (e.g. some English variants such as `bomb`, `hack`, `harm`). Detected stem-based threats (e.g. `చంపాలి`, `kill`) are still blocked. | [`src/sage_indic/pipeline/service.py`](file:///d:/Sage-Indic/src/sage_indic/pipeline/service.py), [`src/sage_indic/safety/`](file:///d:/Sage-Indic/src/sage_indic/safety/) | Known Limitation / Frozen Phase 2C |
| **ISSUE-APP-02** | **MEDIUM** | Evidence Gate | **Heuristic Coverage Gate:** `evidence_is_sufficient()` uses coverage thresholds (0.67 with ≥2 matched groups, or 0.50 with a title/≥2-term match) plus a single-entity exception. This is a transparent application heuristic, not a calibrated relevance or answerability model. | [`src/sage_indic/composition/query_analysis.py`](file:///d:/Sage-Indic/src/sage_indic/composition/query_analysis.py) | Active Research Backlog |
| **ISSUE-APP-03** | **LOW** | Demo Retrieval | **Demo-Layer Canonical Expansion:** `build_retrieval_expansion()` appends canonical Telugu/English term variants for demo recall. It is not one of the evaluated Phase 2D retrieval conditions and must not be reported as an experimental gain. | [`src/sage_indic/composition/query_analysis.py`](file:///d:/Sage-Indic/src/sage_indic/composition/query_analysis.py) | Documented Demo Shortcut |
| **ISSUE-APP-04** | **MEDIUM** | Optional LLM | **Latency and Draft Quality:** `llama3.2:1b` on CPU can exceed the 25 s default timeout, producing `llm_fallback`. The LLM path was mechanically verified (timeout fallback and ungrounded-draft rejection) but not shown to improve answer quality or factuality. | [`src/sage_indic/pipeline/service.py`](file:///d:/Sage-Indic/src/sage_indic/pipeline/service.py), [`src/sage_indic/composition/composer.py`](file:///d:/Sage-Indic/src/sage_indic/composition/composer.py) | Known Limitation |
| **ISSUE-APP-05** | **LOW** | Demo Corpus | **Corpus Scale:** The demo answers only from 10 documents / 30 chunks. Out-of-corpus queries abstain by design; broad domain coverage requires corpus expansion. | [`data/processed/rag/phase2d_chunks.jsonl`](file:///d:/Sage-Indic/data/processed/rag/phase2d_chunks.jsonl) | Known Limitation |
| **ISSUE-APP-06** | **LOW** | API Surface | **Health Endpoint Naming:** Only `/api/health` exists; a plain `/health` request returns 404. External pollers should use `/api/health`, or an alias should be added in a future isolated change. | [`src/sage_indic/api/app.py`](file:///d:/Sage-Indic/src/sage_indic/api/app.py) | Open Maintenance |
| **ISSUE-APP-07** | **LOW** | Lint/Format Baseline | **Formatter Not Applied Repo-Wide:** `ruff format --check` reports six Phase 2G files, but formatting would rejoin long Telugu string literals and re-trigger `E501`. `ruff check` passes on the new Phase 2G modules; pre-existing findings remain in frozen files and the legacy suite. | `ruff check` / `ruff format --check` output, 2026-11-17 | Open Maintenance |
