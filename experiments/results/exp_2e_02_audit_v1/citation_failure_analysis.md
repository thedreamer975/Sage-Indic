# Citation Failure Analysis: EXP-2E-02

## 1. Objective and Audit Classification

In EXP-2E-02, a **0% citation validity rate** (0 valid citations, 2 invalid citations in Condition A) was reported. This audit establishes the exact breakdown across the six required forensic categories:

| Category | Description | Count (Cond A) | Percentage |
| :---: | :--- | :---: | :---: |
| **Cat 1** | **No citation emitted** | **40 / 42** | **95.2%** |
| **Cat 2** | **Citation emitted but malformed** | **0 / 42** | **0.0%** |
| **Cat 3** | **Citation refers to an unknown passage ID** | **2 / 42** | **4.8%** |
| **Cat 4** | **Citation refers to a known passage but unsupported claim** | **0 / 42** | **0.0%** |
| **Cat 5** | **Citation is valid and its associated claim is supported** | **0 / 42** | **0.0%** |
| **Cat 6** | **Cannot be determined from available records** | **0 / 42** | **0.0%** |
| **Total** | | **42 / 42** | **100.0%** |

---

## 2. Detailed Inspection of Category 3 Hallucinations

Two queries in Condition A emitted explicit passage citations matching the system's regex `r"\[([A-Za-z0-9_\-]+#[a-zA-Z0-9_\-]+)\]"`:

### Case 1: `Q_DEV_005_ROM`
- **Query:** `hyderabadi dum biryani ni moghalula kalam lo ela tayaruchesevaru?` (Unanswerable query).
- **Supplied Evidence Passages:**
  1. `TE_DOC_008#c0001` (Pochampally Ikat)
  2. `TE_DOC_008#c0002` (Pochampally Ikat GI tag)
  3. `TE_DOC_004#c0002` (Nagarjuna Sagar canal)
- **Model Output:**
  ```text
  hyderabadi dum biryani ni moghalula kalam lo ela tayaruchesevaru? [TE_DOC_006#c0002]

  తెలుగు పదాలు క్రీస్తు పూర్వ
  ```
- **Cited ID:** `TE_DOC_006#c0002`
- **Audit Analysis:**
  - `TE_DOC_006#c0002` exists in the broader Phase 2D corpus (Kalamalla Inscription), but was **NOT** supplied in the prompt's retrieved evidence envelope for `Q_DEV_005_ROM`.
  - The model hallucinated an unsupplied passage ID from parametric training weights or prior prompt context.
  - The citation parser correctly identified this as invalid (`invalid_citations: ["TE_DOC_006#c0002"]`).

### Case 2: `Q_EVAL_007_MIX`
- **Query:** `kuchipudi classical dance form andhra pradesh lo ekkada originate aindi` (Unanswerable query).
- **Supplied Evidence Passages:**
  1. `TE_DOC_007#c0001` (Salar Jung Museum)
  2. `TE_DOC_007#c0002` (Veiled Rebecca)
  3. `TE_DOC_002#c0002` (Golconda sound transmission)
- **Model Output:**
  ```text
  kuchipudi classical dance form andhra pradesh lo ekkada originate aindi

  [TE_DOC_001#c0001]
  ```
- **Cited ID:** `TE_DOC_001#c0001`
- **Audit Analysis:**
  - `TE_DOC_001#c0001` (Charminar construction) was **NOT** supplied in the evidence package for `Q_EVAL_007_MIX`.
  - The citation was properly flagged as hallucinated (`invalid_citations: ["TE_DOC_001#c0001"]`).

---

## 3. Root Cause Analysis: Why 0% Validity?

1. **Instruction Non-Compliance in Small Parameter Regimes:**
   The prompt explicit instruction (`SYSTEM_INSTRUCTIONS` Rule 2) stated:
   `Every factual statement in your answer MUST cite its supporting passage ID in brackets, e.g., [TE_DOC_001#c0000].`
   In 40 out of 42 queries, `llama3.2:1b` failed to generate any citation syntax whatsoever. At 1B parameters, small SLMs lack robust instruction adherence for structured bracketed syntax unless fine-tuned or heavily few-shot prompted.
2. **Impact of 80-Token Generation Cap:**
   The generation budget was capped at 80 tokens. In many Telugu native queries, the model spent all 80 tokens echoing the prompt or slowly generating complex Telugu Unicode syllables, exhausting its budget before reaching the end of the sentence where citations are typically placed.
3. **Absence of Regex or Parser Mismatches:**
   The parser regex in `PromptComposer.CITATION_PATTERN` was verified:
   `re.compile(r"\[([A-Za-z0-9_\-]+#[a-zA-Z0-9_\-]+)\]")`
   This pattern accurately matches all standard corpus passage IDs (`TE_DOC_XXX#cYYYY`). There are **no syntax parsing bugs**. The 0% metric reflects authentic model failure to generate valid citations.
