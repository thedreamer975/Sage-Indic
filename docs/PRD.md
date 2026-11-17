# SAGE-Indic --- Product Requirements Document (PRD)

**Project:** SAGE-Indic\
**Full Name:** A Linguistically-Aware, Safe and Evidence-Grounded LLM
Framework for Native and Code-Mixed Indic Languages\
**Primary Language:** Telugu\
**Target Input Forms:** Native Telugu, Romanized Telugu, Telugu-English
code-mixed text\
**Document Type:** Product Requirements + Research/Engineering
Specification\
**Status:** Research Prototype / B.Tech Research Project\
**Primary Goal:** Build a reproducible end-to-end pipeline that improves
Indic-language representation efficiency while evaluating safety
robustness and evidence-grounded factuality in one system.

------------------------------------------------------------------------

## 1. Executive Summary

SAGE-Indic is a research-oriented LLM pipeline designed for
Indic-language users, with Telugu as the primary case study.

The system addresses four connected problems:

1.  **Token inefficiency** --- Indic text, especially morphologically
    rich Telugu and Romanized/code-mixed forms, can be fragmented
    inefficiently by standard subword tokenizers.
2.  **Morphological representation** --- reducing token count alone is
    insufficient if useful linguistic structure is lost.
3.  **Safety gaps** --- unsafe intent may be expressed through Telugu
    script, Romanized Telugu, Telugu-English code mixing, spelling
    variation, or transliteration variation and may therefore evade
    simple safety filters.
4.  **Weak factual grounding** --- retrieval-augmented generation (RAG)
    provides evidence but does not guarantee that every generated claim
    is supported by the retrieved evidence.

SAGE-Indic therefore combines:

``` text
User Query
    ↓
Language / Script / Code-Mix Detection
    ↓
SAGE Morphology-Aware Tokenizer
    ↓
Context-Aware Safety Layer
    ↓
Evidence Retriever
    ↓
LLM / SLM
    ↓
Claim Extraction
    ↓
Claim-Level Evidence Verification
    ↓
Response Composer
    ↓
Final Answer + Evidence + Factuality Status + Caveats
```

The project is explicitly **not** intended to train a large language
model from scratch. The tokenizer is the primary representation-level
research component. Existing multilingual LLMs/SLMs may be used for
generation, safety, and RAG experiments, while a small controlled
language model may be used where necessary to study tokenizer behavior.

The central research question is:

> **Can linguistically-aware representation make Indic LLM systems more
> efficient without sacrificing language quality, while context-aware
> safety and evidence verification make their outputs more reliable?**

The expected contribution is not to claim that tokenization, safety, or
RAG is individually new. The contribution is the controlled design and
evaluation of their interaction on native, Romanized, and code-mixed
Telugu.

------------------------------------------------------------------------

# 2. Problem Statement

LLMs and multilingual NLP systems do not always process Indic languages
as efficiently and reliably as high-resource languages.

Telugu presents several challenges:

-   It is morphologically rich.
-   Users may write Telugu in native Telugu script.
-   Users may write Telugu using Latin/Roman characters.
-   Users may mix Telugu and English within the same sentence.
-   Spelling and transliteration can vary significantly in informal
    input.
-   Standard tokenization may fragment words unnecessarily.
-   Safety mechanisms designed primarily around standard-script or
    English inputs may fail under Romanization, code mixing, and
    variation.
-   RAG can retrieve relevant information while the generator may still
    produce unsupported claims.

SAGE-Indic treats these problems as parts of one practical system rather
than isolated tasks.

------------------------------------------------------------------------

# 3. Product Vision

SAGE-Indic should provide a research-grade prototype where a Telugu user
can submit:

-   Native Telugu text
-   Romanized Telugu text
-   Telugu-English code-mixed text

and receive an answer that is:

-   linguistically represented efficiently,
-   checked for unsafe intent,
-   grounded in retrieved evidence,
-   decomposed into factual claims,
-   verified against evidence,
-   and accompanied by appropriate evidence/factuality information.

The system should also expose enough intermediate information for
researchers to measure and reproduce each component.

------------------------------------------------------------------------

# 4. Research Objectives

## 4.1 Primary Objectives

### O1 --- Efficient Indic Representation

Develop a morphology-aware tokenizer/tokenization strategy that attempts
to reduce unnecessary token fragmentation while preserving linguistic
quality.

### O2 --- Robust Safety

Evaluate whether representation-aware/context-aware safety detection
improves robustness across:

-   native Telugu,
-   Romanized Telugu,
-   Telugu-English code mixing,
-   controlled spelling variation,
-   controlled transliteration variation.

### O3 --- Evidence-Grounded Generation

Build a RAG pipeline that retrieves evidence and then performs
claim-level verification instead of assuming that retrieval alone
guarantees factuality.

### O4 --- Unified Evaluation

Evaluate token efficiency, linguistic quality, inference efficiency,
safety, and factuality within the same experimental framework.

------------------------------------------------------------------------

# 5. Research Questions

## RQ1 --- Tokenization

Can morphology-aware tokenization reduce token fragmentation for Telugu
native, Romanized, and code-mixed inputs without degrading language
quality?

## RQ2 --- Linguistic Alignment

Does incorporating morphological/linguistic structure improve alignment
between token boundaries and meaningful linguistic boundaries?

## RQ3 --- Safety

Does a representation-aware/context-aware safety layer detect unsafe
intent more robustly than keyword filtering and a general multilingual
safety classifier across different Telugu input forms?

## RQ4 --- Factuality

Does claim-level verification after RAG reduce unsupported claims
compared with:

-   LLM-only,
-   LLM + RAG?

## RQ5 --- Trade-offs

What is the practical trade-off among:

-   token efficiency,
-   language quality,
-   inference cost,
-   safety robustness,
-   factuality?

## RQ6 --- Component Contribution

How much does each SAGE component contribute when removed individually?

------------------------------------------------------------------------

# 6. Scope

## 6.1 In Scope

### Language

-   Telugu as the primary language.
-   Native Telugu script.
-   Romanized Telugu.
-   Telugu-English code-mixed input.

### Core Research Components

1.  Language/script/code-mix detection.
2.  Morphology-aware tokenizer.
3.  Context-aware safety guardrail.
4.  Evidence retrieval.
5.  LLM/SLM generation.
6.  Claim extraction.
7.  Claim-level evidence verification.
8.  Response composition.
9.  Baseline and ablation evaluation.

### Evaluation

-   Token efficiency.
-   Morphological alignment.
-   Language/task quality.
-   Latency.
-   Throughput.
-   Memory/VRAM where measurable.
-   Safety precision/recall/F1.
-   False-positive rate.
-   False-negative rate.
-   Robustness across input forms.
-   Claim support rate.
-   Unsupported-claim rate.
-   Answer-level factuality.
-   Evidence precision/recall where defined.
-   Overall quality--efficiency--safety--factuality trade-off.

## 6.2 Out of Scope

The following are explicitly outside the initial project boundary:

-   Training a large LLM from scratch.
-   Supporting every Indic language in the first implementation.
-   Building a general-purpose commercial chatbot.
-   Claiming that the tokenizer, safety layer, or RAG methodology is
    individually novel.
-   Replacing existing multilingual LLMs.
-   Building a massive proprietary corpus when suitable public/curated
    resources can be used.
-   Optimizing solely for minimum token count.
-   Optimizing solely for maximum blocking of unsafe content.

Other Indic languages may be explored as future work after Telugu
evaluation is complete.

------------------------------------------------------------------------

# 7. Target Users

## 7.1 Primary User --- Telugu End User

A user who asks questions using:

-   Telugu script,
-   Romanized Telugu,
-   Telugu-English code mixing.

The user primarily cares about receiving a useful, safe, and trustworthy
answer.

## 7.2 Researcher / Evaluator

A researcher needs access to:

-   intermediate pipeline outputs,
-   token statistics,
-   safety predictions,
-   retrieved evidence,
-   generated claims,
-   verification status,
-   evaluation metrics,
-   experiment configurations.

## 7.3 Project Administrator / Developer

The developer needs to:

-   load datasets,
-   configure models,
-   run experiments,
-   compare baselines,
-   execute ablations,
-   inspect errors,
-   reproduce reported results.

------------------------------------------------------------------------

# 8. Product Principles

## 8.1 Quality Before Raw Compression

A lower token count is useful only when language quality remains
acceptable.

## 8.2 Intent Before Keywords

Safety should not be based only on a harmful-word blacklist.

Benign contexts containing sensitive words must be represented in the
evaluation set.

## 8.3 Retrieval Is Not Verification

RAG retrieves evidence.

The verification stage determines whether generated claims are actually
supported by that evidence.

## 8.4 Reproducibility

Every major experiment should record:

-   dataset version,
-   tokenizer configuration,
-   model configuration,
-   random seed where applicable,
-   evaluation configuration,
-   metric outputs.

## 8.5 Telugu First

Telugu is the primary research setting. Additional Indic languages are
extensions/future work rather than requirements for the initial release.

------------------------------------------------------------------------

# 9. High-Level System Architecture

``` text
                         ┌──────────────────────┐
                         │      User Query      │
                         │ Telugu / Romanized / │
                         │    Code-Mixed       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                     ┌──────────────────────────┐
                     │ Language / Script /      │
                     │ Code-Mix Detection       │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │ SAGE Tokenizer           │
                     │ Morphology-Aware         │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │ Context-Aware Safety     │
                     │ Guardrail                │
                     └────────────┬─────────────┘
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
              Unsafe / Uncertain              Safe
                   │                             │
                   ▼                             ▼
             Safe Response /             Evidence Retriever
             Safety Handling                    │
                                                 ▼
                                      ┌────────────────────┐
                                      │ Retrieved Evidence │
                                      └─────────┬──────────┘
                                                │
                                                ▼
                                      ┌────────────────────┐
                                      │ LLM / SLM          │
                                      │ Draft Answer       │
                                      └─────────┬──────────┘
                                                │
                                                ▼
                                      ┌────────────────────┐
                                      │ Claim Extraction   │
                                      └─────────┬──────────┘
                                                │
                                                ▼
                                      ┌────────────────────┐
                                      │ Evidence           │
                                      │ Verification       │
                                      └─────────┬──────────┘
                                                │
                                 ┌──────────────┼──────────────┐
                                 │              │              │
                              Supported     Unsupported     Uncertain
                                 │              │              │
                                 └──────────────┴──────────────┘
                                                │
                                                ▼
                                      ┌────────────────────┐
                                      │ Response Composer  │
                                      └─────────┬──────────┘
                                                │
                                                ▼
                                      Final Answer +
                                      Evidence +
                                      Factuality Status +
                                      Caveats
```

The architecture follows the nine-stage pipeline specified in the
project proposal:

  Stage   Component                     Expected Output                                   Implementation Status
  ------- ----------------------------- ------------------------------------------------ -----------------------------------------------------------------
  1       User Query                    Native / Romanized / code-mixed text              IMPLEMENTED
  2       Language + Script Detection   Input characteristics                             IMPLEMENTED
  3       SAGE Tokenizer                Efficient, linguistically-aware representation   IMPLEMENTED & FROZEN (EVALUATION UNDER REPAIR)
  4       Safety Layer                  Safe / unsafe / uncertain + risk                  IMPLEMENTED & FROZEN
  5       Retriever                     Relevant evidence                                 IMPLEMENTED (BM25 + CodeMix + SAGE; 8 conditions evaluated)
  6       LLM / SLM                     Draft answer                                      IMPLEMENTED (OPTIONAL, PROVIDER-INDEPENDENT)
  7       Claim Extraction              Atomic factual claims                             IMPLEMENTED (HEURISTIC + EXTRACTIVE)
  8       Evidence Verification         Supported / unsupported / uncertain               IMPLEMENTED (PHASE 2F RELATION-AWARE)
  9       Response Composer             Final answer + evidence + caveats                 IMPLEMENTED (PHASE 2G DEMO PROTOTYPE)

------------------------------------------------------------------------

# 10. Functional Requirements

## FR-01 --- Accept User Input [IMPLEMENTED]

The system shall accept text input in:

-   Telugu script.
-   Romanized Telugu.
-   Telugu-English code-mixed form.

### Acceptance Criteria

-   A valid text query can be submitted.
-   The original query is preserved for display/logging.
-   The system does not require users to manually select their language.

------------------------------------------------------------------------

## FR-02 --- Detect Input Form [IMPLEMENTED]

The system shall identify relevant characteristics of the input.

### Expected labels

At minimum:

``` text
TELUGU_NATIVE
TELUGU_ROMANIZED
ENGLISH
TELUGU_ENGLISH_CODEMIX
UNKNOWN / MIXED
```

The exact final label taxonomy may be refined during implementation.

### Acceptance Criteria

-   Detection result is available to downstream components.
-   The result includes confidence where the selected detector supports
    it.
-   The original query is not modified destructively.

------------------------------------------------------------------------

# 11. SAGE Tokenizer Requirements

## FR-03 --- Baseline Tokenizers [IMPLEMENTED]

The evaluation framework shall support comparison against:

-   BPE.
-   Unigram.
-   Relevant Indic tokenizer baseline(s).
-   Proposed SAGE tokenizer.

The project proposal specifically identifies recent Indic tokenization
work and MUTANT-Indic as relevant baselines.

## FR-04 --- Morphology-Aware Tokenizer [IMPLEMENTED / UNDER EVALUATION]

The SAGE tokenizer shall incorporate morphological/linguistic signals
with the objective of avoiding unnecessary fragmentation.

The tokenizer should preserve useful linguistic structure rather than
optimizing solely for token count.

## FR-05 --- Tokenizer Output [IMPLEMENTED]

For each input, the system should be able to expose:

``` json
{
  "text": "...",
  "tokens": ["..."],
  "token_count": 0,
  "tokens_per_word": 0.0,
  "tokens_per_character": 0.0
}
```

Additional tokenizer metadata may include:

-   token boundaries,
-   morphological boundaries,
-   fertility,
-   compression/efficiency ratio.

## FR-06 --- Tokenizer Evaluation [IMPLEMENTED / UNDER EVALUATION REPAIR]

The tokenizer experiment shall measure:

-   total token count,
-   tokens per word,
-   tokens per character,
-   token fertility,
-   efficiency/compression ratio,
-   latency/throughput,
-   memory where measurable,
-   downstream task quality,
-   morphological boundary alignment.

------------------------------------------------------------------------

# 12. Safety Layer Requirements

## FR-07 --- Context-Aware Safety Detection [IMPLEMENTED]

The safety layer shall classify intent rather than relying exclusively
on keyword matching.

Possible output:

``` json
{
  "label": "safe | unsafe | uncertain",
  "risk": "low | medium | high",
  "confidence": 0.0
}
```

The exact risk taxonomy is implementation-dependent and should be
finalized before evaluation.

## FR-08 --- Input Variation Coverage [IMPLEMENTED]

The safety evaluation shall include:

-   native Telugu,
-   Romanized Telugu,
-   Telugu-English code mixing,
-   spelling variation,
-   transliteration variation.

## FR-09 --- Benign Sensitive Contexts [IMPLEMENTED]

The safety dataset shall include benign examples containing sensitive
terms so that keyword filtering is not artificially rewarded.

## FR-10 --- Safety Baselines [IMPLEMENTED]

Compare:

1.  Keyword filtering.
2.  Multilingual safety classifier.
3.  Proposed representation-aware/context-aware SAGE safety layer.

## FR-11 --- Safety Decision [IMPLEMENTED]

The system should not automatically treat every uncertain case as unsafe
during research evaluation.

The research system must preserve the distinction between:

-   safe,
-   unsafe,
-   uncertain.

This enables measurement of false positives and false negatives.

------------------------------------------------------------------------

# 13. Retrieval-Augmented Generation Requirements

## FR-12 --- Curated Evidence Corpus [STAGE B INGESTED / PARTIALLY IMPLEMENTED]

The system shall use a curated authoritative corpus for the RAG
knowledge base.

The source selection should consider:

-   authority,
-   relevance,
-   licensing,
-   language coverage,
-   freshness where applicable.

## FR-13 --- Evidence Retrieval [IMPLEMENTED - BM25 + CODEMIX + SAGE]

Given a safe query, the retriever shall return relevant evidence
passages.

Implemented in `src/sage_indic/rag/` and wired through the Phase 2G query service with
BM25, `CodeMixedQueryNormalizer`, and the frozen SAGE tokenizer. Dense and hybrid RRF
retrievers are also available and were evaluated in Phase 2D (`EXP-2D-03`–`EXP-2D-07`).

Expected retrieval object:

``` json
{
  "query": "...",
  "results": [
    {
      "document_id": "...",
      "title": "...",
      "source": "...",
      "text": "...",
      "score": 0.0
    }
  ]
}
```

## FR-14 --- Retrieval Evaluation [IMPLEMENTED - 8 CONDITIONS EVALUATED]

Retrieval should be evaluated independently where appropriate.

The project proposal identifies:

-   multilingual embeddings,
-   reranking,
-   retrieval evaluation

as strategies for improving weak retrieval.

Phase 2D evaluated eight controlled conditions on a 42-query / 30-chunk pilot benchmark
with code-mix-aware BM25 reaching 100% Recall@5 on both dev and eval splits (see
`EXP-2D-02`–`EXP-2D-07` and `progress.md` Section 5.3).

# 14. Generation Requirements

## FR-15 --- LLM / SLM Generation [IMPLEMENTED - PROVIDER-INDEPENDENT ADAPTER]

The system shall use an existing multilingual LLM/SLM for application-level generation.
Training a large LLM from scratch is outside scope.

Implemented in `src/sage_indic/generation/` as a provider-independent adapter (`GenerationProvider` ABC) with:
- `MockGenerationProvider`: Deterministic offline provider for all unit tests.
- `ExternalAPIProvider`: OpenAI-compatible API provider with environment-variable-only credentials.
- `GenerationAdapter`: Orchestrates prompt composition, retry policy (configurable `max_retries`, `retry_backoff_factor`), citation validation, and candidate claim extraction.
- `GenerationConfig`: Fully externalized model/provider configuration (model name, temperature, timeout, retries, API endpoint, credential env var).

## FR-16 --- Draft Answer [IMPLEMENTED - STRUCTURED DRAFT WITH PROVENANCE]

The generation stage receives:
- Original user query and `LanguageCategory` (Native Telugu, Romanized Telugu, Code-Mixed).
- Bounded retrieved evidence passages, each with `passage_id`, `document_id`, `content_hash`, `source_url`, `char_start`, `char_end`.
- System instructions (in `PromptComposer`).

The output is a `DraftAnswer` containing:
- `answer_text`: Generated text grounded in evidence.
- `candidate_claims`: Sentence-boundary-extracted `AtomicClaim` list for downstream verification.
- `citations`: Validated passage IDs cited in the answer.
- `invalid_citations`: Hallucinated passage IDs not in the supplied evidence set.
- `is_abstention` + `abstention_reason`: Explicit abstention for unanswerable queries.
- `is_verified = False`: **Invariant — the adapter never marks its own response as verified.**

Prompts separate trusted system instructions from untrusted evidence data using `[EVIDENCE_PASSAGE id="..."]...[/EVIDENCE_PASSAGE]` envelopes with explicit passive-data warnings.

------------------------------------------------------------------------

# 15. Claim Extraction Requirements

## FR-17 --- Atomic Claim Extraction [IMPLEMENTED - HEURISTIC SENTENCE BOUNDARY]

The system shall split the draft answer into factual/atomic claims for independent verification.
Implemented in `GenerationAdapter._extract_candidate_claims()` via sentence boundary heuristics (`[.!?।]+`).
Each sentence becomes an `AtomicClaim` with `claim_id`, `claim_text`, `language`, `modality`, and `extractor` metadata.

**Documented Limitation:** Sentence-boundary decomposition cannot guarantee atomic decomposition correctness for agglutinated Telugu morphological constructions. Claim extraction at this stage is a heuristic preprocessing step, not a semantic decomposition guarantee.

Example output:

``` json
{
  "claims": [
    {
      "claim_id": "C1",
      "text": "Claim one..."
    },
    {
      "claim_id": "C2",
      "text": "Claim two..."
    }
  ]
}
```

The goal is to evaluate claims individually rather than treating the
entire answer as a single factual unit.

------------------------------------------------------------------------

# 16. Evidence Verification Requirements

## FR-18 --- Claim-Level Verification [IMPLEMENTED - PHASE 2F RELATION-AWARE]

Each extracted atomic claim shall be compared against retrieved evidence using directional entailment and contradiction verification.
Implemented in `src/sage_indic/verification/` via:
- `LinguisticClaimVerifier`: Frozen weak baseline inspecting numerical alignment, polarity, transliteration, and multi-passage consistency.
- `RelationAwareClaimVerifier`: Relation-aware verifier decomposing claims into typed `AtomicProposition` structures, performing relation category matching, enforcing conservative compound-claim policies (never forcing partial support into `SUPPORTED`), and isolating untrusted prompt injections.

Expected statuses:

``` text
SUPPORTED
CONTRADICTED
INSUFFICIENT_EVIDENCE
CONFLICTING_EVIDENCE
```

## FR-19 --- Evidence Association [IMPLEMENTED - FOUNDATION]

Where possible, every supported claim preserves a cryptographic reference to the substantiating evidence passage (`EvidencePassage`, parent document ID, chunk ID, SHA-256 `ContentHash`, source URL, and character offsets). Conflicting passages are explicitly linked in `VerificationResult.conflicting_passages`.

Concrete representation:

``` json
{
  "claim_id": "C1",
  "outcome": "SUPPORTED",
  "confidence": 0.95,
  "evidence_passage": {
    "passage_id": "TE_DOC_001#c0000",
    "document_id": "TE_DOC_001",
    "content_hash": {"algorithm": "sha256", "digest": "..."}
  },
  "explanation": "Direct factual alignment: Numbers {1591} verified in evidence.",
  "is_untrusted_evidence_quarantined": true
}
```

## FR-20 --- Unsupported Claims [IMPLEMENTED - PHASE 2G]

The response composer shall be able to:

-   remove unsupported claims,
-   qualify them,
-   flag them,
-   or otherwise prevent them from being presented as confidently
    supported facts.

Implemented policy in `src/sage_indic/composition/composer.py`:

-   Only claims whose verification outcome is `SUPPORTED` are used to build the
    deterministic answer.
-   `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, and `CONFLICTING_EVIDENCE` claims are not
    presented as facts; the response carries claim-level caveats and the overall status
    becomes `PARTIALLY_ANSWERED` or `ABSTAINED`.
-   An optional LLM draft is rejected unless every extracted claim is `SUPPORTED` and no
    invalid citation IDs were produced. The deterministic extractive answer is shown instead.
-   If no selected evidence sentence can be verified, the response abstains rather than
    presenting the sentence.

The policy is deterministic and inspectable. It is an application policy, not a
calibrated entailment guarantee.

## FR-21 --- Human Validation & Diagnostic Benchmarking [VALIDATED - PHASE 2F COMPARISON]

A diagnostic verification benchmark was implemented across topic-isolated splits (24 dev items, 24 eval items) in `data/processed/verification/`.
Empirical evaluation in `EXP-2F-01` established:
- Overall Accuracy: Baseline 70.83% $\rightarrow$ Relation-Aware **75.00%** on held-out eval (+4.17%)
- Macro-F1: Baseline 0.7419 $\rightarrow$ Relation-Aware **0.7750** (+0.0331)
- False `SUPPORTED` Rate: Baseline 11.76% (2/17) $\rightarrow$ Relation-Aware **5.88%** (1/17) (50% relative reduction)
- Genuinely Supported Recall: Maintained at **57.14%** (4/7) with strictly **0.00% regression**
- Partial Evidence Accuracy: Baseline 50.0% $\rightarrow$ Relation-Aware **100.0%** (2/2)
- Defense-in-depth: Adversarial prompt injections neutralized by deterministic parsing and sanitization.
- Identified Residual Limitation: Coarse relational categories (e.g. *discovered* vs *described*) still require fine-grained argument binding or calibrated NLI.

------------------------------------------------------------------------

# 17. Response Composer Requirements

## FR-22 --- Final Answer Composition [IMPLEMENTED - PHASE 2G DEMO PROTOTYPE]

The final response shall combine:

-   generated answer content,
-   evidence references,
-   factuality status,
-   appropriate caveats.

Implemented by `SAGEQueryService` + `ResponseComposer` and exposed through
`POST /api/query`. The actual response object is:

``` json
{
  "request_id": "REQ_...",
  "original_query": "...",
  "detected_modality": "TELUGU_NATIVE",
  "detected_modality_confidence": 0.98,
  "normalized_query": "...",
  "answer_text": "...",
  "answer_status": "ANSWERED",
  "answer_claims": [
    {
      "claim_id": "CLM_01",
      "text": "...",
      "verification_status": "SUPPORTED",
      "evidence_ids": ["TE_DOC_001#c0001"],
      "citation_ids": ["C1"],
      "caveat": null
    }
  ],
  "citations": [
    {
      "citation_id": "C1",
      "evidence_id": "TE_DOC_001#c0001",
      "document_id": "TE_DOC_001",
      "chunk_id": "TE_DOC_001#c0001",
      "title": "...",
      "source_url": "...",
      "supports_claim": true
    }
  ],
  "retrieved_evidence": [],
  "verification_summary": {},
  "abstention_reason": null,
  "generation_metadata": {
    "requested_mode": "deterministic",
    "used_mode": "deterministic",
    "fallback_used": false
  },
  "query_analysis": {},
  "safety": {},
  "warnings": [],
  "latency_metadata": {}
}
```

`answer_status` is one of `ANSWERED`, `PARTIALLY_ANSWERED`, `ABSTAINED`, or `BLOCKED`.
`generation_metadata.used_mode` is one of `deterministic`, `llm`, or `llm_fallback`.
Citation IDs are assigned only from retrieved passages; model-authored citation IDs are
never trusted.

## FR-23 --- Evidence Transparency [IMPLEMENTED - PHASE 2G UI]

The UI should make it possible for the evaluator/user to understand
which evidence supports a claim.

Implemented in `frontend/`:

-   The answer shows programmatic citation markers (`C1`, `C2`, …).
-   Each citation lists the passage ID, document title, publisher, license, source URL,
    quoted evidence span, and whether the verifier marked it as supporting the claim.
-   A verification view shows claim text, claim-level outcome, confidence, evidence IDs,
    and caveats.
-   A status view reports corpus size, retriever, safety mode (including lexical-only
    fallback), and optional LLM availability.
-   Citation-ID validity is presented separately from claim support; an existing ID is
    not treated as proof that the passage supports the claim.

------------------------------------------------------------------------

# 18. Dataset Requirements

Dataset selection must consider:

-   language coverage,
-   licensing,
-   annotation quality,
-   relevance to the exact experiment.

A project-specific evaluation set is essential because existing
resources may not cover all three target input forms simultaneously.

## 18.1 Candidate Resources

  -----------------------------------------------------------------------------
  Resource                Intended Use                  Priority
  ----------------------- ----------------------------- -----------------------
  AI4Bharat / Indic       Indic corpora, language       High
  resources               resources,                    
                          transliteration-related       
                          resources                     

  IndicCorp / IndicCorp   Large Telugu/Indic corpus and High
  v2                      tokenizer work                

  IndicGLUE / IndicXTREME Indic downstream language     High
                          tasks                         

  MILU                    Indian-language               High
                          knowledge/understanding       
                          evaluation                    

  IndicGenBench           Indic-language generation     Medium--High
                          evaluation                    

  SANSKRITI               Indian cultural/regional      Medium--High
                          knowledge and grounded QA     

  IndicJR                 Indic/South Asian safety and  High
                          jailbreak robustness          

  FLORES-200              Multilingual/translation      Medium
                          auxiliary evaluation          

  Dakshina                Native vs Latin-script Indic  High
                          text/transliteration analysis 

  Custom Telugu Safety    Matched                       Essential
  Set                     native/Romanized/code-mixed   
                          safe and unsafe prompts       

  Custom Telugu           Evidence-backed questions +   Essential
  Factuality Set          claim annotations             

  Curated authoritative   RAG knowledge base            Essential
  corpus                                                
  -----------------------------------------------------------------------------

The final dataset selection must be verified for licensing,
accessibility, exact coverage, and suitability before implementation.

------------------------------------------------------------------------

# 19. Custom Dataset Design

## 19.1 Telugu Safety Evaluation Set

The project shall create a matched evaluation set covering:

### Input Forms

``` text
Native Telugu
Romanized Telugu
Telugu-English Code-Mixed
```

### Variation Types

``` text
Standard wording
Spelling variation
Transliteration variation
Context variation
```

### Intent Categories

The final categories must be defined before annotation.

The dataset must contain both:

-   safe/benign examples,
-   unsafe examples.

### Important Requirement

Include benign examples that contain sensitive words.

This prevents a simple keyword filter from appearing artificially
strong.

------------------------------------------------------------------------

# 20. Custom Factuality Dataset

The project shall create a set containing:

-   evidence-backed questions,
-   authoritative evidence,
-   expected factual claims,
-   generated answers,
-   claim-level annotations.

Each evaluation example should ideally maintain a trace:

``` text
Question
   ↓
Evidence
   ↓
Generated Answer
   ↓
Extracted Claims
   ↓
Human/Gold Verification
```

------------------------------------------------------------------------

# 21. Experimental Methodology

## 21.1 Tokenizer Study

### Step 1 --- Corpus Preparation

Build a controlled Telugu corpus containing:

-   native-script samples,
-   Romanized samples,
-   code-mixed samples.

### Step 2 --- Train/Evaluate Tokenizers

Compare:

``` text
BPE
Unigram
Relevant Indic tokenizer baseline
SAGE Tokenizer
```

### Step 3 --- Measure

Measure:

-   token count,
-   tokens/word,
-   tokens/character,
-   token fertility,
-   latency,
-   throughput,
-   memory where measurable,
-   downstream task quality,
-   morphological boundary alignment.

### Step 4 --- Quality Constraint

A tokenizer should not be considered successful merely because it
produces fewer tokens.

Lower token count is useful only if language quality remains acceptable.

------------------------------------------------------------------------

# 22. Safety Experiment

## Baselines

``` text
B1 — Keyword Filtering
B2 — Multilingual Safety Classifier
B3 — SAGE Representation-Aware Safety Layer
```

## Test Conditions

``` text
Native Telugu
Romanized Telugu
Telugu-English Code-Mix
Spelling Variation
Transliteration Variation
```

## Required Measurements

-   Precision
-   Recall
-   F1
-   False-positive rate
-   False-negative rate
-   Robustness by input form

------------------------------------------------------------------------

# 23. Factuality Experiment

The project shall compare:

``` text
F1 — LLM Only
F2 — LLM + RAG
F3 — LLM + RAG + Claim Verification
```

## Required Procedure

1.  Submit question.
2.  Retrieve evidence where applicable.
3.  Generate answer.
4.  Extract atomic claims.
5.  Compare claims with evidence.
6.  Assign:
    -   supported,
    -   unsupported,
    -   uncertain.
7.  Perform human validation on a sample.

## Required Metrics

-   Claim support rate.
-   Unsupported-claim rate.
-   Answer-level factuality.
-   Evidence precision/recall where defined.

------------------------------------------------------------------------

# 24. Baseline Matrix

  Research Area   Baseline                   SAGE Variant
  --------------- -------------------------- --------------------------
  Tokenization    BPE                        SAGE tokenizer
  Tokenization    Unigram                    SAGE tokenizer
  Tokenization    Relevant Indic tokenizer   SAGE tokenizer
  Safety          Keyword filter             SAGE safety
  Safety          Multilingual classifier    SAGE safety
  Grounding       LLM-only                   LLM + RAG + verification
  Grounding       LLM + RAG                  LLM + RAG + verification

------------------------------------------------------------------------

# 25. Ablation Studies

Ablation is mandatory for determining whether each component contributes
to the final system.

## 25.1 Input-Form Ablation

Evaluate separately:

``` text
Native Telugu
Romanized Telugu
Telugu-English Code-Mix
```

## 25.2 Component Ablation

Remove one component at a time.

Examples:

``` text
Full SAGE
- Tokenizer
- Safety Layer
- RAG
- Claim Verification
```

## 25.3 Grounding Ablation

``` text
LLM
LLM + RAG
LLM + RAG + Claim Verification
```

## 25.4 Safety Ablation

``` text
Keyword
Multilingual Classifier
SAGE Safety
```

------------------------------------------------------------------------

# 26. Evaluation Metrics

## 26.1 Token Efficiency

-   Token count.
-   Tokens/word.
-   Tokens/character.
-   Token fertility.
-   Efficiency/compression ratio.

## 26.2 Linguistic Quality

-   Morphological boundary alignment.
-   Task accuracy.
-   Task F1.
-   Loss/perplexity where appropriate.

## 26.3 Inference Efficiency

-   Latency.
-   Throughput.
-   Memory/VRAM.
-   Token-based compute/cost estimate.

## 26.4 Safety

-   Precision.
-   Recall.
-   F1.
-   False-positive rate.
-   False-negative rate.
-   Robustness across input forms.

## 26.5 Factuality

-   Claim support rate.
-   Unsupported-claim rate.
-   Answer-level factuality.
-   Evidence precision/recall where defined.

## 26.6 Overall Evaluation

The system shall report the:

> **Quality--Efficiency--Safety--Factuality trade-off**

rather than optimizing a single metric.

------------------------------------------------------------------------

# 27. Non-Functional Requirements

## NFR-01 --- Reproducibility

Experiments must be reproducible using documented configurations and
fixed dataset/model versions where applicable.

## NFR-02 --- Observability

The research prototype should expose intermediate outputs for debugging:

-   detected input type,
-   tokens,
-   safety result,
-   retrieved documents,
-   generated answer,
-   extracted claims,
-   verification result.

## NFR-03 --- Modularity

Each major research component should be replaceable independently.

Recommended component boundaries:

``` text
language_detection/
tokenizer/
safety/
retrieval/
generation/
claim_extraction/
verification/
evaluation/
```

## NFR-04 --- Configurability

Models, datasets, tokenizer parameters, retrieval parameters, and
evaluation settings should be configurable rather than hard-coded.

## NFR-05 --- Resource Awareness

The project must remain feasible for an undergraduate research team.

Large-scale LLM pretraining is prohibited by project scope.

## NFR-06 --- Traceability

For a generated answer, the system should make it possible to trace:

``` text
Query
→ Safety Decision
→ Retrieved Evidence
→ Generated Answer
→ Claims
→ Evidence Verification
→ Final Answer
```

------------------------------------------------------------------------

# 28. Suggested Repository Structure

``` text
sage-indic/
│
├── README.md
├── PRD.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
├── .env.example
│
├── configs/
│   ├── tokenizer.yaml
│   ├── safety.yaml
│   ├── retrieval.yaml
│   ├── generation.yaml
│   └── evaluation.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── tokenizer/
│   ├── safety/
│   ├── factuality/
│   └── corpus/
│
├── src/
│   └── sage_indic/
│       ├── __init__.py
│       │
│       ├── detection/
│       │   ├── language_detector.py
│       │   ├── script_detector.py
│       │   └── code_mix_detector.py
│       │
│       ├── tokenizer/
│       │   ├── base.py
│       │   ├── bpe_baseline.py
│       │   ├── unigram_baseline.py
│       │   ├── indic_baseline.py
│       │   ├── morphology.py
│       │   └── sage_tokenizer.py
│       │
│       ├── safety/
│       │   ├── keyword_baseline.py
│       │   ├── multilingual_baseline.py
│       │   └── sage_guardrail.py
│       │
│       ├── retrieval/
│       │   ├── index.py
│       │   ├── retriever.py
│       │   └── reranker.py
│       │
│       ├── generation/
│       │   └── generator.py
│       │
│       ├── claims/
│       │   └── extractor.py
│       │
│       ├── verification/
│       │   ├── verifier.py
│       │   └── evidence_matcher.py
│       │
│       ├── pipeline/
│       │   └── sage_pipeline.py
│       │
│       └── evaluation/
│           ├── tokenizer_metrics.py
│           ├── safety_metrics.py
│           ├── factuality_metrics.py
│           ├── latency_metrics.py
│           └── ablations.py
│
├── experiments/
│   ├── tokenizer/
│   ├── safety/
│   ├── factuality/
│   └── ablations/
│
├── notebooks/
│   ├── 01_data_analysis.ipynb
│   ├── 02_tokenizer_analysis.ipynb
│   ├── 03_safety_analysis.ipynb
│   └── 04_factuality_analysis.ipynb
│
├── tests/
│   ├── test_detection.py
│   ├── test_tokenizer.py
│   ├── test_safety.py
│   ├── test_retrieval.py
│   ├── test_claims.py
│   ├── test_verification.py
│   └── test_pipeline.py
│
├── scripts/
│   ├── prepare_data.py
│   ├── train_tokenizer.py
│   ├── build_index.py
│   ├── run_evaluation.py
│   └── run_ablation.py
│
├── results/
│   ├── tokenizer/
│   ├── safety/
│   ├── factuality/
│   └── ablations/
│
└── app/
    ├── backend/
    └── frontend/
```

This structure is a recommended engineering organization derived from
the required research components; it is not a mandated structure from
the proposal.

------------------------------------------------------------------------

# 29. Core Pipeline API Contract

A unified pipeline should conceptually expose:

``` python
result = sage_pipeline.run(
    query=user_query
)
```

Expected result:

``` json
{
  "input": {
    "text": "...",
    "language": "TELUGU",
    "script": "TELUGU",
    "form": "NATIVE"
  },
  "tokenization": {
    "tokens": [],
    "token_count": 0
  },
  "safety": {
    "label": "safe",
    "risk": "low",
    "confidence": 0.0
  },
  "retrieval": {
    "evidence": []
  },
  "generation": {
    "draft_answer": "..."
  },
  "claims": [
    {
      "claim_id": "C1",
      "text": "...",
      "status": "SUPPORTED",
      "evidence_ids": ["E1"]
    }
  ],
  "final_response": {
    "answer": "...",
    "caveats": [],
    "evidence": []
  }
}
```

The exact API schema may evolve during implementation.

------------------------------------------------------------------------

# 30. Research Data Flow

## Input

``` text
Raw User Query
```

## Detection

``` text
Language
Script
Code-Mixing
```

## Representation

``` text
Morphology-Aware Tokens
```

## Safety

``` text
Safe / Unsafe / Uncertain
```

## Retrieval

``` text
Relevant Evidence
```

## Generation

``` text
Draft Answer
```

## Claim Processing

``` text
Atomic Claims
```

## Verification

``` text
Supported / Unsupported / Uncertain
```

## Final Output

``` text
Answer
+
Evidence
+
Factuality Status
+
Caveats
```

------------------------------------------------------------------------

# 31. User Interface Requirements

The demonstration interface should show the complete research pipeline
rather than only a chatbot-style final answer.

## 31.1 Query Panel

Display:

-   text input,
-   submit action,
-   detected input form.

## 31.2 Tokenization Panel

Display:

-   token count,
-   tokenized representation,
-   relevant token statistics.

## 31.3 Safety Panel

Display:

-   safety label,
-   risk,
-   confidence where available.

## 31.4 Evidence Panel

Display:

-   retrieved evidence,
-   source/title,
-   retrieval score where available.

## 31.5 Answer Panel

Display:

-   generated/final answer.

## 31.6 Factuality Panel

Display:

-   extracted claims,
-   support status,
-   associated evidence,
-   unsupported/uncertain claims.

The interface is primarily a demonstration and research-inspection tool,
not the main research contribution.

------------------------------------------------------------------------

# 32. Error Analysis Requirements

Error analysis is mandatory.

The project should categorize failures such as:

## Tokenizer Errors

-   excessive fragmentation,
-   incorrect morphological segmentation,
-   loss of linguistic structure,
-   poor handling of Romanization,
-   poor handling of code mixing.

## Safety Errors

-   unsafe input classified as safe,
-   safe input classified as unsafe,
-   failure under spelling variation,
-   failure under transliteration variation,
-   code-mix robustness failures.

## Retrieval Errors

-   irrelevant evidence,
-   insufficient evidence,
-   language mismatch,
-   weak ranking.

## Generation Errors

-   unsupported statement,
-   incorrect synthesis,
-   missing evidence,
-   evidence misinterpretation.

## Verification Errors

-   supported claim marked unsupported,
-   unsupported claim marked supported,
-   uncertainty incorrectly resolved.

------------------------------------------------------------------------

# 33. Risk Register

  -------------------------------------------------------------------------
  Risk                    Impact                  Mitigation
  ----------------------- ----------------------- -------------------------
  Tokenizer reduces       High                    Optimize
  tokens but harms                                quality--efficiency
  language quality                                trade-off rather than
                                                  token count alone

  Safety layer            High                    Measure false positives
  over-blocks benign                              and include benign
  content                                         sensitive-word contexts

  Safety misses           High                    Matched
  Romanized/code-mixed                            multilingual/input-form
  unsafe intent                                   evaluation

  Retriever returns weak  High                    Curated sources,
  evidence                                        multilingual embeddings,
                                                  reranking and retrieval
                                                  evaluation

  Verifier makes          High                    Evidence-based
  incorrect decisions                             verification + human
                                                  validation on held-out
                                                  sample

  Dataset does not cover  High                    Build custom Telugu
  all input forms                                 evaluation sets

  Project scope becomes   High                    Keep Telugu as primary
  too large                                       language

  Large-model training    High                    Use existing multilingual
  becomes infeasible                              LLM/SLM and small
                                                  controlled models where
                                                  needed

  Lower token count is    Medium                  Report linguistic quality
  mistaken for overall                            and downstream metrics
  improvement                                     alongside efficiency

  Existing datasets have  High                    Verify licenses before
  unsuitable licensing                            use and maintain dataset
                                                  provenance
  -------------------------------------------------------------------------

------------------------------------------------------------------------

# 34. Security and Safety Research Boundaries

The system is intended for safety research and evaluation.

The project should:

-   evaluate safety robustness,
-   preserve safe/unsafe/uncertain distinctions,
-   avoid relying exclusively on keyword blacklists,
-   test benign sensitive contexts,
-   record false positives and false negatives,
-   keep safety evaluation datasets appropriately controlled.

The research should focus on evaluating and improving defensive
robustness rather than generating harmful operational content.

------------------------------------------------------------------------

# 35. Acceptance Criteria

The project is considered functionally complete when all of the
following are satisfied.

## A. Input Handling

-   [ ] Native Telugu input works.
-   [ ] Romanized Telugu input works.
-   [ ] Telugu-English code-mixed input works.
-   [ ] Language/script/code-mix characteristics are exposed.

## B. Tokenizer

-   [ ] BPE baseline implemented/evaluated.
-   [ ] Unigram baseline implemented/evaluated.
-   [ ] Relevant Indic baseline evaluated.
-   [ ] SAGE tokenizer implemented.
-   [ ] Token statistics collected.
-   [ ] Morphological alignment evaluated.
-   [ ] Language-quality impact measured.

## C. Safety

-   [ ] Keyword baseline implemented.
-   [ ] Multilingual classifier baseline evaluated.
-   [ ] SAGE safety layer implemented.
-   [ ] Native Telugu evaluated.
-   [ ] Romanized Telugu evaluated.
-   [ ] Code-mixed Telugu evaluated.
-   [ ] Spelling variation evaluated.
-   [ ] Transliteration variation evaluated.
-   [ ] Benign sensitive contexts included.
-   [ ] Precision/recall/F1 reported.
-   [ ] False-positive/false-negative rates reported.

## D. RAG

-   [ ] Curated authoritative corpus created.
-   [ ] Retrieval pipeline implemented.
-   [ ] Evidence returned with metadata.
-   [ ] Retrieval evaluated where applicable.

## E. Factuality

-   [ ] LLM-only baseline evaluated.
-   [ ] LLM + RAG evaluated.
-   [ ] LLM + RAG + verification evaluated.
-   [ ] Claim extraction implemented.
-   [ ] Claim support status produced.
-   [ ] Human validation performed on a sample.
-   [ ] Unsupported and uncertain claims reported separately.

## F. Ablations

-   [ ] Input-form ablation completed.
-   [ ] Component ablation completed.
-   [ ] Grounding ablation completed.
-   [ ] Safety baseline comparison completed.

## G. Reproducibility

-   [ ] Dataset versions recorded.
-   [ ] Configuration files committed.
-   [ ] Experiment commands documented.
-   [ ] Results saved in structured form.
-   [ ] Random seeds documented where applicable.
-   [ ] Evaluation scripts reproducible.

## H. Demonstration

-   [ ] End-to-end query pipeline works.
-   [ ] Safety result visible.
-   [ ] Evidence visible.
-   [ ] Final answer visible.
-   [ ] Claim-level factuality visible.

------------------------------------------------------------------------

# 36. Definition of Done

SAGE-Indic is considered research-complete when:

1.  The end-to-end pipeline operates on the three target Telugu input
    forms.
2.  The proposed tokenizer is compared fairly with selected baselines.
3.  Token efficiency and linguistic quality are jointly evaluated.
4.  Safety is tested across script, Romanization, code mixing, and
    controlled variation.
5.  RAG is evaluated separately from claim verification.
6.  Claim-level factuality is evaluated against retrieved evidence.
7.  Baselines and ablations are completed.
8.  Quantitative results are recorded.
9.  Error analysis identifies both improvements and failure cases.
10. The system can reproduce the final reported experiments.
11. A demonstration interface shows:

``` text
Query → Safety → Evidence → Answer → Factuality
```

12. A final thesis/report documents methodology, results, limitations,
    and research findings.

------------------------------------------------------------------------

# 37. Research Deliverables

The project shall produce:

## D1 --- SAGE Tokenizer

A prototype morphology-aware tokenizer/tokenization strategy for Telugu
and selected input forms.

## D2 --- Telugu Safety Evaluation Set

A native/Romanized/code-mixed safety dataset with evaluation scripts.

## D3 --- Curated Evidence Corpus

A trusted corpus suitable for the RAG experiments.

## D4 --- RAG Pipeline

A working retrieval and generation pipeline.

## D5 --- Claim-Level Factuality Module

A verifier that associates generated claims with evidence and classifies
them as:

-   supported,
-   unsupported,
-   uncertain.

## D6 --- Reproducible Evaluation Framework

Baselines, metrics, experiment configurations, and ablation scripts.

## D7 --- Demonstration Interface

A UI demonstrating:

``` text
Query
→ Safety
→ Evidence
→ Answer
→ Factuality Status
```

## D8 --- Research Report / Thesis

The final report shall include:

-   research motivation,
-   literature review,
-   methodology,
-   datasets,
-   baselines,
-   experiments,
-   quantitative results,
-   ablations,
-   error analysis,
-   limitations,
-   future work.

------------------------------------------------------------------------

# 38. Suggested Development Phases

## Phase 0 --- Research Setup

### Goals

-   Finalize research questions.
-   Verify datasets and licenses.
-   Finalize evaluation protocol.
-   Establish reproducible environment.

### Output

``` text
Dataset inventory
Experiment specification
Initial repository
Baseline configuration
```

------------------------------------------------------------------------

## Phase 1 --- Data and Input Analysis

### Goals

-   Collect/prepare Telugu native text.
-   Collect/prepare Romanized Telugu.
-   Collect/prepare code-mixed Telugu.
-   Analyze script and linguistic characteristics.
-   Establish baseline tokenization statistics.

### Output

``` text
Controlled Telugu corpus
Input-form analysis
Initial tokenization report
```

------------------------------------------------------------------------

## Phase 2 --- Tokenizer Research

### Goals

-   Implement baseline tokenizers.
-   Develop morphology-aware representation.
-   Train/evaluate SAGE tokenizer.
-   Measure token efficiency.
-   Measure morphological alignment.
-   Evaluate downstream language quality.

### Output

``` text
Tokenizer prototype
Tokenizer benchmark
Tokenizer error analysis
```

------------------------------------------------------------------------

## Phase 3 --- Safety Research

### Goals

-   Prepare matched safety dataset.
-   Implement keyword baseline.
-   Evaluate multilingual safety baseline.
-   Implement SAGE safety layer.
-   Test variation robustness.

### Output

``` text
Safety dataset
Safety benchmark
False-positive/false-negative analysis
```

------------------------------------------------------------------------

## Phase 4 --- RAG

### Goals

-   Curate authoritative corpus.
-   Build retrieval index.
-   Implement retrieval.
-   Add optional reranking.
-   Evaluate retrieval quality.

### Output

``` text
Evidence corpus
Retriever
Retrieval evaluation
```

------------------------------------------------------------------------

## Phase 5 --- Generation + Claim Verification

### Goals

-   Integrate multilingual LLM/SLM.
-   Generate evidence-conditioned answers.
-   Extract atomic claims.
-   Verify claims against retrieved evidence.
-   Add final response composition.

### Output

``` text
End-to-end factuality pipeline
Claim-level evidence mapping
Verifier evaluation
```

------------------------------------------------------------------------

## Phase 6 --- Unified Evaluation

### Goals

Run:

``` text
Tokenizer comparison
Safety comparison
Factuality comparison
Input-form ablation
Component ablation
```

### Output

``` text
Final metrics
Ablation tables
Error analysis
Trade-off analysis
```

------------------------------------------------------------------------

## Phase 7 --- Demonstration + Research Report

### Goals

-   Build demonstration UI.
-   Integrate full pipeline.
-   Document reproducibility.
-   Prepare thesis/report.
-   Prepare research figures/tables.

### Output

``` text
Working demo
Reproducible repository
Final thesis/report
Research results
```

------------------------------------------------------------------------

# 39. Experiment Tracking Requirements

Every experiment should record at minimum:

``` yaml
experiment_id:
date:
dataset:
dataset_version:
input_form:
model:
tokenizer:
tokenizer_version:
safety_model:
retriever:
reranker:
generation_model:
verification_method:
seed:
hardware:
metrics:
notes:
```

Results should be stored in machine-readable format where practical.

Recommended:

``` text
results/
├── tokenizer/
├── safety/
├── factuality/
└── ablations/
```

------------------------------------------------------------------------

# 40. Recommended Experiment Naming

Use deterministic names.

Examples:

``` text
tok_bpe_native_telugu_v1
tok_unigram_romanized_v1
tok_sage_codemix_v1

safety_keyword_native_v1
safety_multilingual_romanized_v1
safety_sage_codemix_v1

fact_llm_only_v1
fact_llm_rag_v1
fact_llm_rag_verify_v1

ablation_no_tokenizer_v1
ablation_no_safety_v1
ablation_no_rag_v1
ablation_no_verifier_v1
```

------------------------------------------------------------------------

# 41. Result Reporting Format

## Tokenizer Table

  --------------------------------------------------------------------------------
  System     Input        Tokens   Tokens/Word   Tokens/Char    Quality    Latency
             Form                                                       
  ---------- -------- ---------- ------------- ------------- ---------- ----------
  BPE        Native          ---           ---           ---        ---        ---

  Unigram    Native          ---           ---           ---        ---        ---

  Indic      Native          ---           ---           ---        ---        ---
  Baseline                                                              

  SAGE       Native          ---           ---           ---        ---        ---
  --------------------------------------------------------------------------------

Equivalent tables should be created for Romanized and code-mixed inputs.

## Safety Table

  System         Input Form     Precision   Recall    F1   FPR   FNR
  -------------- ------------ ----------- -------- ----- ----- -----
  Keyword        Native               ---      ---   ---   ---   ---
  Multilingual   Native               ---      ---   ---   ---   ---
  SAGE           Native               ---      ---   ---   ---   ---

## Factuality Table

  Configuration                Support Rate   Unsupported Rate   Answer Factuality
  -------------------------- -------------- ------------------ -------------------
  LLM Only                              ---                ---                 ---
  LLM + RAG                             ---                ---                 ---
  LLM + RAG + Verification              ---                ---                 ---

These are result templates, not target values.

------------------------------------------------------------------------

# 42. Research Evaluation Framework and Audit Reconciliation

To maintain scientific integrity and prevent ungrounded claims, all experimental evaluations in SAGE-Indic must adhere to the audited research framework established in October 2026.

## 42.1 Tokenizer Evaluation and Baselines

### Baseline Comparisons ($V=4000$)
Empirical comparison of tokenization strategies on Telugu native text must report standard efficiency (tokens/word, characters/token) and morphological alignment. Historical draft results claiming a fertility of 1.3323 and F1 of 0.8876 have been quarantined as mathematically unsupported and ungrounded. The audited, reproducible baseline results on `eval_native.txt` (148 sentences) are:

| Tokenizer Model | Tokens/Word | Chars/Token | Boundary Proxy F1 | Status |
|:---|:---:|:---:|:---:|:---|
| **BPE** | 1.642 | 4.896 | 0.5202 | Verified Baseline |
| **Unigram** | 1.836 | 4.378 | 0.6044 | Verified Baseline |
| **SAGE (Rule Affix + Unigram)** | 1.903 | 4.225 | 0.6378 | Under Evaluation Repair |
| **SAGE Ablation (No-Morphology)** | 1.838 | 4.373 | 0.6039 | Verified Ablation |

*Physical Trade-off Analysis:* SAGE's explicit affix detachment splits inflected word forms (e.g., `stem` + `##affix`), which mathematically increases token count and tokens-per-word relative to standard subwords. F1 gains over Unigram (+0.0334) are primarily driven by whitespace pre-tokenization boundary preservation rather than verified subword morpheme discovery.

### Evaluation Repair and Leakage Decontamination
1. **Reference Ground Truth:** Current reference boundaries derive from Universal Dependencies (`UD_Telugu-MTG`) syntactic word tokens (`FORM`), which do not annotate intra-word morphemes. Detaching affixes is penalized as a false positive against syntactic words. A dedicated gold intra-word morpheme boundary benchmark must be created.
2. **Data Leakage Decontamination:** Four sentences in `eval_native.txt` overlap with the training corpus due to upstream UD treebank duplication (2.7% split contamination). Future controlled re-evaluation must use a strictly decontaminated split.
3. **Controlled Scope:** The immediate next tokenizer milestone is evaluation repair and controlled re-evaluation, not ungrounded algorithm redesign.

## 42.2 Retrieval Evaluation Across Scripts (Phase 2D)

### Multi-Script Retrieval Corpus and Queries
1. **Corpus Foundation:** The knowledge base foundation consists of 10 approved, verified Wikipedia articles segmented into 30 content chunks with SHA-256 provenance tracking.
2. **Current Implementation Status:** `BM25Retriever`, `MultilingualDenseRetriever`, and `HybridRetriever` are implemented. A 42-query multi-script benchmark with 1,260 qrels and eight controlled conditions was executed (`EXP-2D-02`–`EXP-2D-07`). Code-mix-aware BM25 reached 100% Recall@5 on both dev and eval splits. Results remain pilot-scale (single annotator, 30 chunks).
3. **Benchmark Suite:** The multi-script query suite contains native, Romanized, and code-mixed queries, including unanswerable controls:
   - Native Telugu queries against ingested passages.
   - Romanized Telugu transliterations.
   - Telugu-English code-mixed queries.
4. **Metrics Reported:** Deterministic IR metrics:
   - Mean Reciprocal Rank (MRR@10)
   - Normalized Discounted Cumulative Gain (nDCG@5, nDCG@10)
   - Recall@k ($k \in \{1, 3, 5\}$)
   - Mean Latency per query (ms)

## 42.3 Context-Aware Safety Regression Evaluation

Safety evaluation requires continuous regression testing across five linguistic variations to prevent keyword brittleness:
1. **Matched Variation Testing:** Every unsafe intent must be evaluated across Native Telugu, Romanized Telugu, Telugu-English code mixing, spelling variants, and transliteration variants.
2. **Benign Context Defense:** Evaluation suites must include benign sensitive cases (medical contexts, educational discussions, non-violent political terms) to measure False Positive Rate (FPR). Simple keyword filters produce unacceptably high FPR on benign contexts.
3. **Audited Baseline:** The verified baseline on `eval_safety.jsonl` (76 cases) establishes that context-aware classification significantly outperforms keyword filtering on Romanized and code-mixed evasions while protecting benign contexts.

## 42.4 Evidence-Based Claim Verification (Phase 2F Validated)

Retrieval of relevant passages does not establish output truthfulness. Factuality verification requires:
1. **Atomic Claim Extraction:** Decomposing generated output into verifiable proposition units. Implemented heuristically via sentence boundaries; Phase 2G additionally uses verbatim evidence sentences for deterministic composition.
2. **Entailment Verification:** Assessing premise-to-hypothesis support using the four-class outcomes `SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING_EVIDENCE`. Evaluated in `EXP-2F-01`.
3. **Unsupported Claim Mitigation:** Preventing ungrounded claims from reaching the final response through rejection, qualification, flagging, or suppression. Implemented in the Phase 2G composer; LLM drafts are accepted only when fully supported.

## 42.5 Ablations, Provenance, and Reproducibility

Every research milestone must satisfy:
1. **Deterministic Experiment Ledger:** All experiments must be logged in `EXPERIMENT_LEDGER.md` with git commit hash, exact configuration, dataset split hashes, raw artifact paths, and reproduction commands.
2. **Component Ablations:** Proposed modules (e.g., morphological rules in tokenization, context analysis in safety, reranking in retrieval) must be ablated against un-augmented baselines under identical seeds.
3. **Explicit Limitation Reporting:** Measured failures, proxy mismatches, and data leakage must be acknowledged directly in reports rather than hidden.

## 42.6 ACM Special Issue Positioning (Open Research Decision)

The target publication venue (e.g., ACM Special Issue on Knowledge-Informed / Neuro-Symbolic / Trustworthy Indic NLP) emphasizes principled integration of symbolic knowledge and neural pipelines.
- *Open Decision:* The exact alignment with knowledge-informed or symbolic reasoning—specifically whether morphological affixes constitute symbolic knowledge priors, or whether external knowledge graphs are required for factuality verification—remains an open research-design decision pending review of the official call for papers.
- *Constraint:* The project team shall not claim premature compliance with every special-issue requirement until the official call is reviewed and an aligned implementation is empirically demonstrated.

------------------------------------------------------------------------

# 43. Quality Gates

The team should not advance to the next research phase without meeting
basic quality gates.

## Gate 1 --- Data

-   Input forms represented.
-   Licensing/provenance documented.
-   Train/evaluation separation established where applicable.

## Gate 2 --- Tokenizer

-   Baselines run.
-   SAGE tokenizer runs.
-   Metrics reproducible.

## Gate 3 --- Safety

-   Matched evaluation set available.
-   Benign sensitive contexts included.
-   Baseline comparison possible.

## Gate 4 --- RAG

-   Evidence can be retrieved.
-   Evidence metadata preserved.
-   Retrieval can be evaluated independently.

## Gate 5 --- Verification

-   Claims can be extracted.
-   Claims can be mapped to evidence.
-   Supported/unsupported/uncertain states are produced.

## Gate 6 --- Research Evaluation

-   Baselines complete.
-   Ablations complete.
-   Error analysis complete.

------------------------------------------------------------------------

# 44. Limitations to Explicitly Report

The final report should acknowledge:

1.  Telugu is the primary case study.
2.  Results may not generalize directly to every Indic language.
3.  Romanized Telugu has substantial spelling/transliteration variation.
4.  Morphological annotation may be limited.
5.  Safety evaluation depends on dataset coverage and annotation
    quality.
6.  Claim verification can itself make mistakes.
7.  Retrieval quality affects downstream factuality.
8.  Token-count reduction does not automatically imply better language
    understanding.
9.  Existing model behavior may constrain conclusions about the
    tokenizer.
10. The project is a research prototype rather than a production-scale
    multilingual LLM platform.

------------------------------------------------------------------------

# 45. Future Extensions

Potential future work includes:

-   extending from Telugu to additional Indic languages,
-   multilingual morphology-aware tokenization,
-   larger-scale safety evaluation,
-   broader code-mixing combinations,
-   improved claim verification,
-   adaptive retrieval,
-   multilingual evidence alignment,
-   efficiency-aware model serving,
-   additional Indic benchmarks,
-   larger controlled language-model studies.

These are future extensions and should not expand the initial
implementation scope unless the core Telugu experiments are complete.

------------------------------------------------------------------------

# 46. Final Research Success Criteria

The project should not define success as:

> "Our tokenizer produces the fewest tokens."

It should instead answer, with quantitative evidence:

1.  How much token fragmentation can be reduced?
2.  Does the reduction preserve linguistic quality?
3.  Does morphology-aware representation behave differently across
    native, Romanized, and code-mixed Telugu?
4.  Does the safety layer remain robust under those input variations?
5.  Does RAG reduce unsupported content?
6.  Does claim verification reduce unsupported claims further?
7.  What are the costs in latency, memory, or compute?
8.  Which components provide measurable benefit?
9.  Where does the system fail?
10. What is the resulting quality--efficiency--safety--factuality
    trade-off?

The final contribution should therefore be a **measured, reproducible
research framework**, not merely a chatbot demonstration.

------------------------------------------------------------------------

# 47. One-Sentence Product Definition

> **SAGE-Indic is a Telugu-first research pipeline that combines
> linguistically-aware tokenization, context-aware safety detection,
> retrieval-augmented generation, and claim-level evidence verification
> to study the trade-off between efficiency, language quality, safety,
> and factual reliability for native, Romanized, and code-mixed Indic
> language input.**

------------------------------------------------------------------------

# Appendix A --- Proposal Traceability

The following requirements are directly traceable to the supplied
SAGE-Indic project proposal.

  Proposal Area                        PRD Coverage
  ------------------------------------ ----------------------------
  Problem statement                    Sections 2--4
  Research gaps G1--G4                 Sections 5, 11, 12, 16, 25
  Language/script/code-mix detection   Section 10
  Morphology-aware tokenizer           Section 11
  Context-aware safety                 Section 12
  RAG + claim verification             Sections 13--16
  Nine-stage architecture              Section 9
  Candidate datasets                   Section 18
  Tokenizer methodology                Section 21
  Safety methodology                   Section 22
  Factuality methodology               Section 23
  Metrics                              Section 26
  Baselines                            Section 24
  Ablations                            Section 25
  Implementation boundary              Sections 6 and 35
  Expected deliverables                Section 37
  Risks                                Section 33
  Telugu-first research direction      Sections 6, 44, 45

------------------------------------------------------------------------


