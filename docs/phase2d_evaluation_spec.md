# Phase 2D Retrieval Evaluation Specification

**Status:** Proposed methodology only. Queries, relevance labels, corpus, and results do not yet exist.

## Research question

Can retrieval provide relevant, provenance-preserving Telugu evidence to support downstream factual answering while keeping retrieved evidence separate from instruction execution?

Phase 2D measures ranking and evidence/provenance handling. Retrieval does not prove a passage true, verify a claim, or generate an answer. Those functions remain outside this phase.

## Existing interfaces and boundary

- **Input representation (Phase 2A):** `InputRepresentation` from `sage_indic.detection.detect(text)` / `LanguageDetector.detect(text)`: original text, normalized text, category, confidence, and metadata. It does not translate or transliterate Romanized Telugu.
- **Safety result (Phase 2C):** `SafetyResult` from `SageAwareSafetyGuardrail.predict(text)`: label, confidence, method, language, signals, and metadata. It may gate whether the user query proceeds; it does not establish source trust or factuality. Keep the Phase 2C implementation/results frozen.
- **SAGE representation (Phase 2B):** existing `SageTokenizer` implements `encode(text) -> list[str]` and `encode_ids(text) -> list[int]`; frozen vocabularies/configuration must be consumed read-only. These subword representations are not automatically suitable retrieval terms or embeddings. A retrieval comparison using them is a hypothesis requiring measurement.
- **Configuration:** YAML files under `configs/` are project convention, but `src/sage_indic/config.py` does not currently parse YAML. Environment-based path/settings behavior exists. Integration must resolve the actual loader without silently adding a dependency.

No Phase 2D orchestration currently wires these outputs together. Any eventual interface should accept the explicit representations/results without changing earlier phases and return evidence only.

## Corpus and evaluation artifacts

The corpus and query/annotation set are distinct immutable artifacts. The corpus is specified in [phase2d_corpus_spec.md](phase2d_corpus_spec.md). The query set must contain:

```json
{
  "query_id": "stable query identifier",
  "query": "human-authored or source-derived query text",
  "language": "te",
  "script_modality": "native | romanized | code_mixed",
  "query_family_id": "groups equivalent cross-form needs for split control",
  "query_provenance": "authoring/source record and transformations",
  "relevant_document_ids": [],
  "document_relevance": [],
  "annotation_status": "human_verified | automatically_derived | pending",
  "annotator_notes": "document annotation process; no invented labels"
}
```

If chunk-level relevance is used, include separately adjudicated `relevant_chunk_ids` and the rationale for chunk boundaries. An empty example list above is schema notation, not a label record.

**Current state:** `RELEVANCE JUDGMENTS: NOT YET CREATED`. `data/` contains no Phase 2D query set or evidence corpus. Do not use the tokenizer/safety evaluation sets as retrieval relevance ground truth.

## Query construction and annotation

- Use factual information needs from the human-approved Telugu domain/source scope.
- Collect native Telugu, Romanized Telugu, and Telugu-English code-mixed versions with human-reviewed meaning equivalence. Record whether each is authored directly or derived/translated/transliterated; do not describe a derived query as native-authored.
- Group semantic variants of one information need under `query_family_id`; keep that family within one split to prevent leakage.
- Prefer a small fixed corpus that can be exhaustively judged. For each query, annotators inspect the complete eligible corpus before ranking is run and label each document independently of method output. If this is infeasible, predeclare a pooling procedure, pool depth, unjudged treatment, and residual recall limitation before evaluation.
- Use two independent annotators for relevance where feasible and adjudicate disagreements; preserve initial labels, adjudication, and rationale. Human reviewers decide ambiguous factual equivalence and source appropriateness.
- A proposed graded scheme is 0 = not relevant, 1 = partially relevant/contextual, 2 = directly relevant evidence. Human approval is required before use. If binary relevance is selected, document the rule instead and do not report graded interpretations.
- Keep answer strings or dataset “gold answers” out of corpus/index text. Record source provenance for every query and every judgment.

## Splits and leakage controls

For fixed BM25 over a fixed corpus, no model-training split is needed. Use a development query family set to make predeclared configuration decisions and a sealed evaluation family set for final reporting. If retrieval parameters or a dense model are trained/tuned, introduce a training partition and keep it distinct from dev/eval.

Before scoring, produce a leakage report covering exact and normalized duplicates, document/document near duplicates, query/query duplicates, query-to-corpus exact/near matches, source URL duplicates, cross-split family overlap, and copied evaluation text/labels in the indexed material. Declare normalization, similarity method/threshold, and limitations. Do not repair leakage silently; document exclusions and preserve the report.

## Retrieval conditions (not implemented)

### Baseline

**Lexical BM25-style ranking** over eligible corpus text. Predeclare tokenizer, Unicode/whitespace normalization, term treatment, BM25 parameters, top-k, score direction, deterministic tie-breaking, and candidate corpus version. A BM25 package is not currently declared/available in the checked workspace runtime; dependency vs small implementation remains an engineering choice after approval.

### Proposed comparisons

- **Raw query vs conservative normalization:** use existing `normalize_text` only as a separately named condition. It is not a Romanization transliterator.
- **SAGE representation-aware condition:** only if justified with the frozen tokenizer and measured as its own retrieval-term representation. Do not claim it improves retrieval in advance.
- **Dense retrieval:** conditional. No specific model has yet been verified for Telugu identity, language/script coverage, licensing, version, availability, or reproducibility. Do not implement or compare dense retrieval until those checks pass and a human approves it.
- **Chunking:** compare whole-document retrieval where practical against at least two predeclared deterministic chunk conditions. Fix boundaries/configuration before final evaluation and report corpus version and chunk size/overlap.

No reranker, generator, LLM wrapper, or claim verifier is in scope.

## Input and candidate pool

Each trial uses one query record plus its explicit modality and condition. Retrieval candidates are only `retrieval_eligible` documents/chunks from one immutable corpus version. Query families and labels are unavailable to the retriever. Native evidence corpus use against Romanized or code-mixed queries is cross-script/cross-form retrieval and must be reported separately from native/native same-script retrieval.

## Metrics and definitions

Primary unit: relevant **documents**, to avoid artificially penalizing or rewarding chunk fragmentation. For chunk retrieval, map ranked chunks to unique parent document IDs in first-occurrence order before document-level metrics. If human chunk judgments exist, report chunk metrics separately.

- **Recall@K:** number of judged relevant documents present in top K unique retrieved documents divided by the number of relevant documents for that query.
- **MRR:** mean reciprocal rank of the first relevant document per query; zero if none is retrieved.
- **nDCG@10:** DCG of the top 10 unique documents using human-approved graded relevance divided by ideal DCG for the same query; use only if graded judgments are approved and available.
- **Hit@K:** proportion of queries with at least one relevant document in top K; optional descriptive metric, not a replacement for recall.
- **Precision@K:** optional only when the whole candidate set is judged or the protocol specifies how unjudged items are handled.

Proposed report: Recall@1/5/10, MRR, nDCG@10 if supported. Report macro average over queries within each modality and overall, with query counts and uncertainty intervals when the sample size supports them. Define the interval method in advance. No metric values are available or claimed.

## Modality and script slices

| Query condition | Evidence script | Retrieval relation | Current data support |
|---|---|---|---|
| Native Telugu | Native Telugu | Same-script/native | No Phase 2D corpus or labels exist. |
| Romanized Telugu | Native Telugu | Cross-script/cross-form | Dakshina provides romanization material, but it is not approved factual evidence or a retrieval benchmark. No judged queries exist. |
| Telugu-English code-mixed | Native Telugu | Cross-form/mixed-to-native | UD Telugu-English-TECT is a linguistic treebank, not factual evidence; license/source lineage also needs review. No judged queries exist. |
| Romanized Telugu | Romanized Telugu evidence | Same-script Latin | No approved Romanized factual evidence corpus exists. Do not report this slice unless one is human-approved and acquired. |
| Code-mixed Telugu-English | Code-mixed evidence | Same-form | No approved code-mixed factual evidence corpus exists. Do not report this slice unless one is human-approved and acquired. |

Report modality on query, corpus script/modalities, and same/cross-script relation separately. Do not infer that a Telugu dataset supports Romanized or code-mixed retrieval solely from its Telugu language tag.

## Controls and result records

Each eventual run must record query/corpus versions, source manifest, method and tokenizer, all retrieval parameters, query-normalization condition, SAGE tokenizer artifact/version if used, model/version/license if dense retrieval is later approved, chunk configuration, top-k, deterministic tie-breaking, random seed if relevant, timestamp, leakage report, per-query ranked IDs/scores, metrics, failures, and software/runtime versions. Keep raw per-query output so aggregates can be independently recomputed.

No query construction, labels, retrieval run, or result artifact was made during this design task.
