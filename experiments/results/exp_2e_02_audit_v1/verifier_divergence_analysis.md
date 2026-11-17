# Verifier Divergence Analysis: EXP-2E-02

## 1. Objective and Core Finding

In EXP-2E-02, the paired evaluation between Condition A (`RelationAwareClaimVerifier`) and Condition B (`LinguisticClaimVerifier`) reported:
- **0 / 42 eligibility divergences**
- **0 / 43 claim outcome divergences**

This forensic audit investigates whether the zero-divergence outcome is an instrumentation defect, a state-sharing bug, or a legitimate reflection of the evaluation inputs.

**Audit Conclusion:**
The zero divergence is **NOT** a code bug, state overwriting defect, or shared-reference anomaly. Both verifiers were invoked independently and executed correctly. The zero divergence occurs because the generated answers from `llama3.2:1b` (capped at 80 tokens) consisted almost exclusively of **single-clause fragments, prompt echoes, or safety refusals**, which completely failed to trigger the compound conjunction splitting and relational incompatibility rules where `RelationAwareClaimVerifier` diverges from `LinguisticClaimVerifier`.

---

## 2. End-to-End Execution Trace

### A. Independent Instantiation
In `experiments/run_exp_2e_02.py` (lines 296–297):
```python
rel_verifier = RelationAwareClaimVerifier()
ling_verifier = LinguisticClaimVerifier()
```
Two distinct class instances from separate modules (`src/sage_indic/verification/relation_verifier.py` and `src/sage_indic/verification/verifier.py`) are created.

### B. Independent Invocations
In `run_exp_2e_02.py` (lines 376–384):
```python
# Audit with RelationAwareClaimVerifier
t0_verif_rel = time.perf_counter()
rel_report = verify_draft_answer(draft, passages, verifier=rel_verifier)
verif_rel_latency_ms = (time.perf_counter() - t0_verif_rel) * 1000

# Audit with LinguisticClaimVerifier (baseline)
t0_verif_ling = time.perf_counter()
ling_report = verify_draft_answer(draft, passages, verifier=ling_verifier)
verif_ling_latency_ms = (time.perf_counter() - t0_verif_ling) * 1000
```
- Both calls pass the same `draft` and `passages` objects.
- Each invocation independently calls `verify_draft_answer`.
- Latencies are timed separately: `mean_verification_ms` was 0.40 ms for Relation-Aware vs 0.40 ms for Linguistic.

### C. Distinct Dictionary Preservation
In `run_exp_2e_02.py` (lines 438–458):
The outputs of `rel_report` and `ling_report` are recorded under two independent keys in each per-query result record:
- `r["relation_aware"]`
- `r["linguistic_baseline"]`
Neither field overwrites or references the other.

---

## 3. Linguistic and Architectural Root Cause

The two verifiers diverge under specific linguistic conditions:
1. **Compound Proposition Splitting:** `RelationAwareClaimVerifier.decompose_claim()` splits claims containing conjunction patterns (` మరియు `, ` తో పాటు `, ` అలాగే `, ` and `, `, `).
2. **Relational Predicate Incompatibility:** `RelationAwareClaimVerifier` checks whether the claimed relation predicate belongs to an incompatible category against the passage relation (e.g., asserting `construction` when evidence states `death_or_tomb`).
3. **Conservative Composition:** If any sub-proposition is contradicted, the compound claim is marked `CONTRADICTED`; if partially supported, it remains `INSUFFICIENT_EVIDENCE`.

### Forensic Claim Audit (43 claims across 42 queries):
- **Claim Length & Structure:** Because `llama3.2:1b` was constrained to 80 tokens, answers were truncated fragments (e.g. `Q_DEV_001_NAT చార్మినార్ నిర్మాణం చార్మినార్ చతురస్రా` or `గోల్కొండ కోట ప్రవేశ ద్వారం వద్ద చప్పట్లు కొడిత`).
- **Conjunction Count:** Zero claims contained valid coordinate clauses linked by conjunctions that met the minimum clause length threshold (>8 characters per clause without syntax truncation).
- **Sub-proposition count:** All 43 claims decomposed into exactly **1 atomic proposition**, identical to the claim itself (`len(propositions) == 1`).
- **Reduction to Base Logic:** When `len(propositions) == 1` and no relational category conflict is triggered, `_verify_single_proposition()` applies the exact same token overlap, numerical alignment, and negation rules as `LinguisticClaimVerifier`.

Because the generator never produced compound, relationally rich assertions, the evaluation suite did not exercise the specialized divergence capabilities of `RelationAwareClaimVerifier`.

---

## 4. Evaluation Suite Recommendation

Zero divergence is an accurate measurement on this specific generator's outputs, but represents an **evaluation suite limitation**:
- To measure divergence between relation-aware and baseline verifiers, evaluation sets must include or elicit **compound, relationally varied assertions** (e.g., through targeted multi-hop or predicate-substitution synthetic probes, as in Phase 2F offline unit tests where the two verifiers differ significantly).
