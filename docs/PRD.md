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

  Stage   Component                     Expected Output
  ------- ----------------------------- ------------------------------------------------
  1       User Query                    Native / Romanized / code-mixed text
  2       Language + Script Detection   Input characteristics
  3       SAGE Tokenizer                Efficient, linguistically-aware representation
  4       Safety Layer                  Safe / unsafe / uncertain + risk
  5       Retriever                     Relevant evidence
  6       LLM / SLM                     Draft answer
  7       Claim Extraction              Atomic factual claims
  8       Evidence Verification         Supported / unsupported / uncertain
  9       Response Composer             Final answer + evidence + caveats

------------------------------------------------------------------------

# 10. Functional Requirements

## FR-01 --- Accept User Input

The system shall accept text input in:

-   Telugu script.
-   Romanized Telugu.
-   Telugu-English code-mixed form.

### Acceptance Criteria

-   A valid text query can be submitted.
-   The original query is preserved for display/logging.
-   The system does not require users to manually select their language.

------------------------------------------------------------------------

## FR-02 --- Detect Input Form

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

## FR-03 --- Baseline Tokenizers

The evaluation framework shall support comparison against:

-   BPE.
-   Unigram.
-   Relevant Indic tokenizer baseline(s).
-   Proposed SAGE tokenizer.

The project proposal specifically identifies recent Indic tokenization
work and MUTANT-Indic as relevant baselines.

## FR-04 --- Morphology-Aware Tokenizer

The SAGE tokenizer shall incorporate morphological/linguistic signals
with the objective of avoiding unnecessary fragmentation.

The tokenizer should preserve useful linguistic structure rather than
optimizing solely for token count.

## FR-05 --- Tokenizer Output

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

## FR-06 --- Tokenizer Evaluation

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

## FR-07 --- Context-Aware Safety Detection

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

## FR-08 --- Input Variation Coverage

The safety evaluation shall include:

-   native Telugu,
-   Romanized Telugu,
-   Telugu-English code mixing,
-   spelling variation,
-   transliteration variation.

## FR-09 --- Benign Sensitive Contexts

The safety dataset shall include benign examples containing sensitive
terms so that keyword filtering is not artificially rewarded.

## FR-10 --- Safety Baselines

Compare:

1.  Keyword filtering.
2.  Multilingual safety classifier.
3.  Proposed representation-aware/context-aware SAGE safety layer.

## FR-11 --- Safety Decision

The system should not automatically treat every uncertain case as unsafe
during research evaluation.

The research system must preserve the distinction between:

-   safe,
-   unsafe,
-   uncertain.

This enables measurement of false positives and false negatives.

------------------------------------------------------------------------

# 13. Retrieval-Augmented Generation Requirements

## FR-12 --- Curated Evidence Corpus

The system shall use a curated authoritative corpus for the RAG
knowledge base.

The source selection should consider:

-   authority,
-   relevance,
-   licensing,
-   language coverage,
-   freshness where applicable.

## FR-13 --- Evidence Retrieval

Given a safe query, the retriever shall return relevant evidence
passages.

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

## FR-14 --- Retrieval Evaluation

Retrieval should be evaluated independently where appropriate.

The project proposal identifies:

-   multilingual embeddings,
-   reranking,
-   retrieval evaluation

as strategies for improving weak retrieval.

------------------------------------------------------------------------

# 14. Generation Requirements

## FR-15 --- LLM / SLM Generation

The system shall use an existing multilingual LLM/SLM for
application-level generation.

Training a large LLM from scratch is outside scope.

## FR-16 --- Draft Answer

The generation stage shall receive:

-   original user query,
-   relevant retrieved evidence,
-   relevant system instructions,
-   safety decision/context where appropriate.

The output is a draft answer that proceeds to factuality verification.

------------------------------------------------------------------------

# 15. Claim Extraction Requirements

## FR-17 --- Atomic Claim Extraction

The system shall split the draft answer into factual/atomic claims.

Example conceptual output:

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

## FR-18 --- Claim-Level Verification

Each extracted claim shall be compared against retrieved evidence.

Expected statuses:

``` text
SUPPORTED
UNSUPPORTED
UNCERTAIN
```

## FR-19 --- Evidence Association

Where possible, every supported claim should have an evidence reference.

Conceptual representation:

``` json
{
  "claim_id": "C1",
  "status": "SUPPORTED",
  "evidence_ids": ["E2", "E4"],
  "confidence": 0.0
}
```

## FR-20 --- Unsupported Claims

The response composer shall be able to:

-   remove unsupported claims,
-   qualify them,
-   flag them,
-   or otherwise prevent them from being presented as confidently
    supported facts.

The exact policy shall be determined experimentally.

## FR-21 --- Human Validation

A sample of verifier outputs shall be manually validated to estimate
verifier reliability.

------------------------------------------------------------------------

# 17. Response Composer Requirements

## FR-22 --- Final Answer Composition

The final response shall combine:

-   generated answer content,
-   evidence references,
-   factuality status,
-   appropriate caveats.

Conceptual response:

``` json
{
  "answer": "...",
  "evidence": [
    {
      "id": "E1",
      "source": "...",
      "title": "..."
    }
  ],
  "claims": [
    {
      "text": "...",
      "status": "SUPPORTED"
    }
  ],
  "caveats": []
}
```

## FR-23 --- Evidence Transparency

The UI should make it possible for the evaluator/user to understand
which evidence supports a claim.

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

# 42. Quality Gates

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

# 43. Limitations to Explicitly Report

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

# 44. Future Extensions

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

# 45. Final Research Success Criteria

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

# 46. One-Sentence Product Definition

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


