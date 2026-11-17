# SAGE-Indic — Phase 2D/2F Claim Verification Specification

**Specification Version:** 1.0.0  
**Status:** IMPLEMENTED & TESTED  
**Component:** Factuality & Evidence Verification Layer (`sage_indic.verification`)  
**Target Languages:** Native Telugu (`te`), Romanized Telugu (`te-Latn`), Code-Mixed Telugu-English (`te-en`)  

---

## 1. Research Motivation & Core Principles

In standard RAG systems, retrieval is frequently conflated with factual truth: if a passage is retrieved with high cosine similarity, the system implicitly treats the query or generated statement as verified. In SAGE-Indic, this conflation is strictly rejected:

1. **Retrieval Obtains Evidence, Not Truth:** Retrieved passages are candidate evidence chunks, not proof of factuality.
2. **Semantic Similarity $\neq$ Entailment:** Two sentences can share 95% semantic embedding similarity while asserting opposite facts (e.g., *"చార్మినార్ 1591 లో నిర్మించబడింది"* vs. *"చార్మినార్ 1591 లో నిర్మించలేదు"*).
3. **Directional Truth Preservation:** Verification requires establishing whether an evidence passage strictly entails (SUPPORTED), refutes (CONTRADICTED), or fails to substantiate (INSUFFICIENT_EVIDENCE) an atomic claim.
4. **Untrusted Evidence Boundary:** Passages retrieved from external sources must be treated strictly as passive data. Any prompt injection or imperative instructions embedded in evidence must be quarantined and prevented from influencing verifier outcomes.

---

## 2. Core Schemas & Types

The claim-verification subsystem implements four core types:

### 2.1 `AtomicClaim`
An individual, indivisible factual assertion to be audited against retrieved evidence.
- `claim_id: str`: Unique identifier.
- `claim_text: str`: Normalized assertion text.
- `source_query_id: str | None`: Provenance linking to parent query.
- `language: str`: Linguistic tag (`te`, `te-Latn`, `te-en`, `en`).
- `modality: str`: Input modality (`native`, `romanized`, `code_mixed`).
- `context_sentence: str | None`: Optional surrounding context from response.

### 2.2 `EvidencePassage`
An untrusted passage preserving cryptographic provenance from the retrieval layer.
- `passage_id: str`: Chunk ID (e.g., `TE_DOC_001#c0000`).
- `document_id: str`: Parent document identifier.
- `text: str`: Text content of the chunk.
- `content_hash: ContentHash`: SHA-256 cryptographic digest.
- `source_url: str | None`: Web provenance URL.
- `title: str`: Document title.

### 2.3 `VerificationOutcome` (Enumeration)
- `SUPPORTED`: Evidence directly substantiates the atomic claim with positive polarity and matching entities/dates/quantities.
- `CONTRADICTED`: Evidence directly refutes the claim (e.g., conflicting dates/numbers, opposing polarity, or negated relations).
- `INSUFFICIENT_EVIDENCE`: Evidence passages do not contain sufficient topical or entity grounding to substantiate or refute the claim.
- `CONFLICTING_EVIDENCE`: Multiple retrieved passages disagree with each other on the factual assertion.

### 2.4 `VerificationResult`
- `claim_id: str`: Target claim.
- `outcome: VerificationOutcome`: Adjudicated category.
- `confidence: float`: Bounded in $[0.0, 1.0]$. Represents the calibrated margin of entailment/contradiction (explicitly distinct from cosine similarity).
- `evidence_passage: EvidencePassage | None`: Best substantiating or refuting passage.
- `explanation: str`: Transparent linguistic rationale linking evidence to decision.
- `conflicting_passages: list[EvidencePassage]`: Mutually disagreeing passages when `CONFLICTING_EVIDENCE` is triggered.
- `is_untrusted_evidence_quarantined: bool`: Invariant tracking data isolation.

---

## 3. Verifier Architecture: `LinguisticClaimVerifier`

The baseline verifier implemented in `src/sage_indic/verification/verifier.py` provides deterministic, auditable verification:
1. **Adversarial Sanitization:** Runs regex pattern matching against known prompt-injection signatures (`ignore previous instructions`, `system: disregard`, `override outcome`). Detected patterns are replaced with `[QUARANTINED_INSTRUCTION]` and flagged in metadata.
2. **Cross-Script Expansion:** For Romanized and Code-mixed assertions, runs `RomanizedTeluguTransliterator` to expand claim tokens into native Telugu representations, enabling cross-script alignment against native Telugu evidence passages.
3. **Multi-Passage Conflict Detection:** Scans all retrieved chunks for conflicting numerical, chronological, or entity assertions regarding the claim.
4. **Numerical & Entity Verification:** Extracts dates, years, and quantities using `NUMBER_PATTERN`. Validates whether numbers in the claim align or conflict with numbers in topically relevant passages.
5. **Polarity & Negation Alignment:** Audits Telugu negation markers (`లేదు`, `కాదు`, `నిర్మించలేదు`, etc.) and Latin negation markers (`not`, `never`, `ledu`, `kaadu`) to catch semantic polarity reversals.

---

## 4. Evaluation Design & Metrics

### 4.1 Evaluation Dimensions

| Test Condition | Input Description | Expected Outcome |
| :--- | :--- | :--- |
| **True Affirmative** | Factual statement matching evidence passage | `SUPPORTED` |
| **Numerical Contradiction** | Statement with altered date, year, or quantity | `CONTRADICTED` |
| **Polarity Reversal** | Negated statement of an affirmed fact | `CONTRADICTED` |
| **Unrelated Passage** | Off-topic retrieval result provided as evidence | `INSUFFICIENT_EVIDENCE` |
| **Conflicting Chunks** | Two passages asserting differing years for same event | `CONFLICTING_EVIDENCE` |
| **Romanized Claim** | Valid claim expressed in Romanized Telugu | `SUPPORTED` |
| **Adversarial Injection** | Passage containing instruction to force "SUPPORTED" | Injection quarantined; outcome uncompromised |

### 4.2 Metrics

1. **Per-Class Precision, Recall, and Macro-F1:** Evaluated separately for `SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, and `CONFLICTING_EVIDENCE`.
2. **Denial Rate on Irrelevant Retrieval:** Percentage of irrelevant or ungrounded chunks correctly assigned `INSUFFICIENT_EVIDENCE` (Target $\ge 95\%$).
3. **Adversarial Neutralization Rate:** Percentage of injection payloads successfully sanitized without outcome hijacking (Target = 100%).
4. **Metric Separation:** Verification accuracy is reported completely independently of retrieval Recall@k to prevent confounding retrieval failures with verification errors.

---

## 5. Future Neural NLI Model Policy

If neural NLI models (e.g., XLM-RoBERTa-large-XNLI, IndicBERT-NLI) are introduced:
- **Language Coverage Warning:** Standard multilingual NLI models trained predominantly on English MNLI often perform poorly on complex Dravidian agglutinative morphology and Romanized colloquialisms.
- **Mandatory Target-Language Benchmarking:** No neural NLI model may be integrated into production without an audited Telugu evaluation report on native and code-mixed test suites.
- **Inference Latency & Fallback:** Neural models must implement timeout protection and fallback to `LinguisticClaimVerifier`.
