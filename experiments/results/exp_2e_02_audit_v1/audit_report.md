# Forensic Audit Report: EXP-2E-02 End-to-End Grounded Factuality Evaluation

**Audit Identifier:** `EXP-2E-02-AUDIT-V1`  
**Target Artifact Directory:** `experiments/results/exp_2e_02/`  
**Audit Directory:** `experiments/results/exp_2e_02_audit_v1/`  
**Execution Date of Target Experiment:** 2026-10-16  
**Audit Completion Date:** 2026-10-18  
**Auditor:** SAGE-Indic Autonomous Forensic Verification Agent  

---

## 1. Executive Summary

This forensic audit evaluates the reproducibility, data integrity, metric validity, and execution provenance of **EXP-2E-02**, the first end-to-end evaluation connecting retrieval, evidence-grounded generation, claim extraction, and dual verification.

### Core Audit Findings:
1. **Reported Condition A Metrics Match Raw Records:** Recomputation of Condition A metrics from the 42 saved records in `per_query_results.json` matches the reported `aggregate_metrics.json` across all metrics.
2. **Condition D Inconsistency Resolved (Confirmed Bug):** The contradiction where Condition D reported **42/42 (100%) abstentions** while simultaneously claiming **2/30 (6.67%) fact-correct answers** was traced to two distinct software defects:
   - *Defect A (Metric Aggregation Bug):* In `aggregate_condition_metrics()`, `fact_correct_cnt` sums all answerable items where `fact_correct is True` without checking `not r["is_abstention"]`.
   - *Defect B (Unconditional Abstention Assignment):* In `GenerationAdapter._check_abstention()`, `is_abstention` was unconditionally forced to `True` whenever `request.evidence_passages` was empty, even though `llama3.2:1b` attempted to answer from parametric memory and emitted text matching essential keywords for 2 Native queries.
3. **Execution Provenance Verified:** The experiment genuinely executed `llama3.2:1b` via an OpenAI-compatible API on Ollama (`http://127.0.0.1:11434/v1`). No fallback to `MockGenerationProvider` occurred.
4. **Citation Failure Root Cause Established:** 0% citation validity is an authentic model behavioral limitation (40/42 queries emitted no citations; 2 emitted hallucinated, out-of-context passage IDs).
5. **Zero Verifier Divergence Explained:** Both verifiers executed independently. The 0/42 divergence occurred because short 80-token model drafts contained exclusively single propositions without conjunctions or relational predicate conflicts, reducing both verifiers to identical base overlap rules.
6. **Artifact Persistence Omissions:** Condition C and Condition D per-query evaluations were omitted from `per_query_results.json`, and Condition D cache was omitted from `generation_cache.json`. Original experiment files remain strictly untouched; all findings are versioned in `exp_2e_02_audit_v1/`.

---

## 2. Original vs. Independently Recomputed Metrics

### Condition A: SAGE-Indic Pipeline (CodeMix BM25 + Gen + RelationAware)

| Metric | Original Reported | Independently Recomputed | Raw Fraction | Discrepancy / Audit Note |
| :--- | :---: | :---: | :---: | :--- |
| **Total Evaluated Queries** | 42 | **42** | 42 / 42 | Exact match; 42 unique IDs |
| **Answerable Denominator** | 30 | **30** | 30 / 42 | Exact match |
| **Unanswerable Denominator** | 12 | **12** | 12 / 42 | Exact match |
| **Native Modality Count** | 14 | **14** | 14 / 42 | Exact match (10 ans, 4 unans) |
| **Romanized Modality Count** | 14 | **14** | 14 / 42 | Exact match (10 ans, 4 unans) |
| **Code-Mixed Modality Count**| 14 | **14** | 14 / 42 | Exact match (10 ans, 4 unans) |
| **Retrieval Hits (Answerable)**| 27 (90.0%) | **27 (90.0%)** | 27 / 30 | Exact match |
| **Fact-Correct Answers (Reported Def)** | 6 (20.0%) | **6 (20.0%)** | 6 / 30 | Exact match under keyword regex |
| **Fact-Correct Answers (Strict Non-Abstained)** | N/A | **6 (20.0%)** | 6 / 30 | Identical in Cond A (all 6 were non-abstaining) |
| **Total Abstentions** | 4 (9.5%) | **4 (9.5%)** | 4 / 42 | Exact match |
| **Correct Abstentions (Unanswerable)** | 4 (33.3%) | **4 (33.3%)** | 4 / 12 | Exact match |
| **Incorrect Abstentions (Answerable)** | 0 (0.0%) | **0 (0.0%)** | 0 / 30 | Exact match |
| **Total Citations Emitted** | 2 | **2** | 2 | Exact match |
| **Valid Citations** | 0 | **0** | 0 / 2 | Exact match |
| **Invalid Citations** | 2 | **2** | 2 / 2 | Exact match |
| **Citation Validity Rate** | 0.0% | **0.0%** | 0 / 2 | Exact match |
| **Citation Hallucination Rate**| 100.0% | **100.0%** | 2 / 2 | Exact match |
| **RelationAware Eligibility: Grounded** | 9 | **9** | 9 / 42 | Exact match |
| **RelationAware Eligibility: Caveat** | 19 | **19** | 19 / 42 | Exact match |
| **RelationAware Eligibility: Contradicted** | 10 | **10** | 10 / 42 | Exact match |
| **RelationAware Eligibility: Abstention** | 4 | **4** | 4 / 42 | Exact match |
| **Total Atomic Claims Evaluated** | 43 | **43** | 43 | Exact match |
| **Supported Claims** | 10 (23.26%) | **10 (23.26%)** | 10 / 43 | Exact match |
| **Contradicted Claims** | 10 (23.26%) | **10 (23.26%)** | 10 / 43 | Exact match |
| **Insufficient Evidence Claims**| 19 (44.19%) | **19 (44.19%)** | 19 / 43 | Exact match |

---

## 3. Resolution of Condition D No-Evidence Inconsistency

### The Inconsistency:
In `aggregate_metrics.json` and the executive summary:
- `total_abstentions: 42` (100.0%)
- `fact_correct_answers_count: 2` (6.67% of 30 answerable queries)

### Investigation & Root Cause:
1. In `src/sage_indic/generation/adapter.py` lines 346–347:
   ```python
   if not request.evidence_passages:
       return True, "No evidence passages supplied."
   ```
   When Condition D runs with `use_no_evidence=True` (`evidence_passages=[]`), `_check_abstention()` unconditionally sets `is_abstention = True` on the `DraftAnswer` object.
2. In `experiments/run_exp_2e_02.py` lines 386–388:
   ```python
   fact_correct = check_fact_correctness(draft.answer_text, item["essential_keywords"]) if is_answerable else None
   ```
   `check_fact_correctness()` was invoked on `draft.answer_text` without verifying whether `draft.is_abstention` was False.
3. In `aggregate_condition_metrics()` line 482:
   ```python
   fact_correct_cnt = sum(1 for r in answerable_items if r["fact_correct"] is True)
   ```
   The metric summed all answerable queries where `r["fact_correct"] is True` without excluding abstaining answers.
4. Because the LLM was prompted with empty evidence, it nonetheless generated text for Native Telugu queries (`QF_DEV_004_NAT` and `QF_EVAL_002_NAT`) where the model's output coincidentally contained the essential keywords from its parametric memory.
5. **Conclusion:**
   - Under a logically consistent definition of fact-correct retrieval-augmented answering, an abstaining answer **cannot** be counted as fact-correct.
   - Condition D true fact-correct answers: **0 / 30 (0.0%)**.
   - Condition D true abstention count: 42 / 42 if relying on adapter forcing, but substantively the model hallucinated text and 3 invalid citations in Condition D rather than strictly abstaining.

---

## 4. Summary of Identified Defects and Systemic Issues

| Issue ID | Severity | Component | Description |
| :--- | :--- | :--- | :--- |
| **BUG-AUDIT-01** | High | Metric Aggregation | `fact_correct_cnt` counted abstaining answers if raw text contained keywords. |
| **BUG-AUDIT-02** | Medium | Generation Adapter | `_check_abstention` unconditionally forces `is_abstention=True` on empty evidence, hiding model hallucination. |
| **BUG-AUDIT-03** | Medium | Reproducibility | `per_query_results.json` omitted Condition C and Condition D per-query records. |
| **BUG-AUDIT-04** | Low | Reproducibility | `generation_cache.json` omitted saving after Condition D, losing Condition D raw generations from disk cache. |
| **LIM-AUDIT-01** | High | Evaluation Design | 80-token cap truncated Telugu script output, suppressing full sentence composition and citation emission. |
| **LIM-AUDIT-02** | High | Evaluation Design | Evaluation examples did not elicit compound coordinate claims, leaving relation-aware verifier unexercised. |
