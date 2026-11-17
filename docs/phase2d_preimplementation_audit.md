# Phase 2D Preimplementation Audit

**Audit date:** 2026-10-02  
**Scope:** Repository/data/dependency audit and proposed retrieval experiment only. No Phase 2D implementation or experiment has been started.

## Executive status

The repository has reusable input-representation, text-normalization, safety-result, configuration, experiment, and test conventions. It has no retrieval package, evidence corpus, retrieval evaluation query set, or Phase 2D results. The paths configured for a future custom corpus exist only as `.gitkeep` placeholders.

**Implementation readiness: STOP pending research/source decisions.** A corpus and relevance judgments are required to make retrieval evaluation meaningful. No verified Telugu evidence corpus or retrieval labels are present. The external IndicQA references also conflict on license: the local manifest states CC-0 while the current AI4Bharat Hugging Face card states CC-BY-4.0. This needs source and intended-use verification before data acquisition or corpus construction. This audit does not resolve the discrepancy or authorize source selection.

## Audit scope and repository findings

Inspected the requested `AGENTS.md`, `docs/PRD.md`, `docs/phase2b_freeze.md`, `docs/safety_design.md`, and `docs/safety_data.md`, plus the repository's `src/`, `tests/`, `data/`, `experiments/`, and `configs/` trees and `README.md`, `pyproject.toml`, `docs/data_strategy.md`, and `docs/data_manifest.md`.

The requested root files `phase2c_audit.md` and `safety_adjudication_audit.md` were not found. Their absence is not evidence that an audit/adjudication did not occur; it means those records could not be inspected from this checkout.

Relevant paths present:

- Input and shared types: `src/sage_indic/types.py`, `src/sage_indic/normalize.py`, `src/sage_indic/detection/`
- Safety API: `src/sage_indic/safety/types.py`, `src/sage_indic/safety/guardrail.py`
- Settings and project configs: `src/sage_indic/config.py`, `configs/default.yaml`, `configs/data.yaml`
- Existing test and experiment conventions: `tests/`, `experiments/run_tokenizer_experiment.py`, `experiments/run_safety_experiment.py`
- Present data: tokenizer train/evaluation text and safety dev/eval JSONL only. `data/custom/corpus/`, `data/custom/factuality/`, and other custom directories contain `.gitkeep` files, not datasets.
- No RAG/retriever implementation or RAG evaluation artifacts were found in `src/`, `tests/`, or `experiments/`.

## A. Existing architecture

### Input entry and representation

There is no end-user application or conversational UI. The library-level input entry point for classification is `sage_indic.detection.detect(text)` / `LanguageDetector.detect(text)` in `src/sage_indic/detection/detector.py`. It returns the frozen `InputRepresentation` dataclass from `src/sage_indic/types.py`, containing original and normalized text, a `LanguageCategory`, confidence, character/token ratios, and metadata.

The implemented enum values are `TELUGU_NATIVE`, `ROMANIZED_TELUGU`, `TELUGU_ENGLISH_CODE_MIXED`, `ENGLISH`, and `UNKNOWN`. Detection is heuristic and deterministic. It can provide a modality label and normalized text to a retriever, but it does not translate Romanized Telugu to Telugu script or establish semantic equivalence. Its output must be treated as a signal, not a retrieval-quality claim.

**Configuration inconsistency to resolve when integration is designed:** `configs/default.yaml` uses `TELUGU_ENGLISH_CODEMIX`; the implemented enum uses `TELUGU_ENGLISH_CODE_MIXED`. No config edit is made in this audit.

### Existing normalization

`sage_indic.normalize.normalize_text` performs NFC normalization, whitespace/control cleanup, and conservative text handling. It is an existing candidate for a reproducible normalization condition. Its application to stored documents must preserve a separately recoverable raw text; the function itself does not implement corpus storage or provenance.

### Phase 2C output

`SageAwareSafetyGuardrail.predict(text)` returns `SafetyResult` (`label`, confidence, method, language, category, signals, metadata), defined in `src/sage_indic/safety/types.py`. This is a clean possible interface for recording the safety disposition of a user query before retrieval. `docs/safety_design.md` also discusses applying safety assessment to retrieved context, but Phase 2D must not change the frozen safety research or treat its result as proof that a retrieved passage is trustworthy. Retrieved-document trust must be enforced separately at the retrieval/evidence boundary.

No single end-to-end request orchestrator currently connects detection, safety, retrieval, generation, or verification. Phase 2D should accept an `InputRepresentation` or raw query through a narrow library interface and remain limited to returning ranked evidence with provenance and an explicit untrusted-data boundary. It should not add generation, claim extraction, verification, or UI behavior.

### Configuration and artifact conventions

`configs/default.yaml` and `configs/data.yaml` are the existing YAML convention. `src/sage_indic/config.py` provides environment-based `Settings` and project paths; it does not currently parse YAML. `experiments/` contains Python experiment entry points and `experiments/results/` contains JSON outputs. `pyproject.toml` defines pytest and Ruff settings. Use these conventions for any later approved Phase 2D work; do not assume a YAML parser is installed.

## B. Existing dependencies and runtime

| Item | Audit finding |
|---|---|
| Python requirement | `pyproject.toml` declares Python `>=3.10`; `README.md` says tested on Python 3.12. The accessible bundled workspace runtime reports Python 3.12.14. |
| Declared runtime dependency | `tokenizers>=0.20.0` only. |
| Declared development dependencies | `pytest>=8.0.0`, `ruff>=0.4.0` under the optional `dev` group. |
| Tokenizer library | Hugging Face `tokenizers` is declared; not importable in the accessible bundled runtime checked for this audit. Frozen tokenizer source/artifacts are present and must remain untouched. |
| Test/lint framework | pytest and Ruff are configured in `pyproject.toml`; neither is importable in the accessible bundled runtime checked. Existing Python bytecode/cache files do not establish that the tools are available now. |
| Retrieval libraries | No BM25, Whoosh, Tantivy, or other retrieval package is declared or importable in the checked runtime. |
| Embedding/model libraries | `sentence-transformers`, `transformers`, `torch`, and `sentencepiece` are not importable in the checked runtime. No embedding model is configured or stored in the repository. |
| Vector stores/databases | No FAISS, Chroma, Qdrant client, or similar package is declared/importable. No database is present or justified by this small prototype audit. |
| Other libraries checked | `numpy` and `pandas` are importable in the bundled runtime; neither is declared by the project for production use. `PyYAML` is not importable. |

The package availability observation is limited to the bundled Python runtime exposed to this audit. `py` was not available in the shell, and no project virtual environment was identified in the repository inventory. The repository dependency declarations, rather than the bundled workspace runtime, are the authoritative record of project requirements. No packages were installed.

## C. Existing datasets and corpus state

### Verified existing repository data

“Verified” here means the files are present and their repository role is documented; it does not certify their external source licensing or suitability as a retrieval corpus.

- `data/processed/tokenizer/`: `train_corpus.txt`, native/Romanized/code-mixed evaluation text, and morphology evaluation JSONL, used by the frozen tokenizer phase.
- `data/processed/safety/`: `dev.jsonl` and `eval.jsonl`, documented as internal controlled safety evaluation data.
- `experiments/results/`: tokenizer and safety JSON results, unrelated to Phase 2D retrieval performance.
- `configs/data.yaml`: declares intended external datasets and schemas, including IndicQA and a future `sage_corpus_te` path; declarations are not downloaded data, source verification, or license evidence.

These are not retrieval relevance judgments and must not be repurposed or described as Phase 2D query/evaluation labels without a separate, documented methodology.

### Unknown/unverified in the checkout

- Whether any referenced external dataset has been downloaded outside tracked/repository-visible paths.
- Whether the PRD/data-manifest dataset descriptions and license statements remain accurate. In particular, the local manifest says IndicQA is CC-0; its current Hugging Face card reports CC-BY-4.0.
- Whether any IndicQA questions, passages, or sources are suitable as an independent retrieval test after inspection of exact records and split design.
- Whether candidate sources meet the human requirement for authority, license compatibility, and factual scope.
- Whether native/Romanized/code-mixed evaluation queries and human relevance judgments can be produced from approved sources.

### Data that must be acquired or created before a meaningful retrieval experiment

1. **Knowledge corpus:** a documented, approved Telugu evidence collection with source-level provenance, source/license review, stable document IDs, and recoverable raw text. No such collection currently exists in `data/`.
2. **Evaluation queries and relevance judgments:** separate from corpus documents, with query ID/text, modality, source/provenance, relevant document IDs, judgment method, and graded or binary relevance definition. No such set currently exists.
3. **Controlled trust-boundary fixtures:** synthetic, clearly labeled test fixtures can be created for deterministic testing, but they must not be mixed into the factual knowledge corpus or presented as factual evidence.
4. **Romanized and code-mixed query conditions:** need documented human-authored/annotated or source-derived inputs, with judgment provenance. Automatically generated variants must be explicitly labeled and cannot silently become human ground truth.

## D. External data requirements and candidate source register

The following register records candidates for human/source review, not approved corpus selection. Accessed/checked on 2026-10-02. No candidate has been downloaded into the repository.

| Name | Original source / URL | Language and script | License | Purpose | Availability | Provenance requirements | Verification status |
|---|---|---|---|---|---|---|---|
| IndicQA (`ai4bharat/IndicQA`) | AI4Bharat dataset card/files: [Hugging Face](https://huggingface.co/datasets/ai4bharat/IndicQA); source paper/code context: [AI4Bharat IndicBERT](https://github.com/AI4Bharat/IndicBERT) | Telugu subset (`te`); native-script status should be checked against actual rows before use. | HF card currently displays CC-BY-4.0. Local `docs/data_manifest.md` says CC-0. | Candidate for a Telugu query/task source only after schema, split, passage and leakage inspection. It is not yet established as a retrieval benchmark or corpus. | Public dataset card and Telugu JSON file are visible; no local copy. | Preserve original dataset/version/revision, split, row ID, question/context fields, source references, transformations, and license notice. Human review required for retrieval relevance suitability. | Telugu availability and displayed card license verified from current HF listing. **License conflict with local manifest: NOT VERIFIED for intended use.** Retrieval suitability, exact evaluation split/labels, and field-level provenance: NOT VERIFIED. |
| Indic-Rag-Suite (`ai4bharat/Indic-Rag-Suite`) | AI4Bharat Hugging Face dataset card: [Hugging Face](https://huggingface.co/datasets/ai4bharat/Indic-Rag-Suite) | Lists `te` among 18 languages; per-row script and query modality require inspection. | Card lists MIT; underlying Wikipedia content rights and redistribution conditions require separate verification. | Candidate for inspecting source-linked Telugu paragraphs and machine-generated queries as a possible *pilot/weakly supervised* resource. Do not treat generated judgments as human ground truth. | Public listing; one large train split is described. No local copy. | Preserve original revision and per-row `wiki_id`, URL, title, language, paragraph, generated question/answer, model attribution, and transformation history; deduplicate documents and queries. | Card reports Wikipedia + Llama 3.3 70B and fields including paragraph/title/wiki_id/URL; these fields are card claims, not independently row-audited. MIT display verified on listing; underlying-source/license compatibility, model/query quality, per-row provenance, and evaluation suitability: NOT VERIFIED. |
| Dakshina | Google Research archived repository: [README](https://github.com/google-research-datasets/dakshina/blob/master/README.md) | Telugu (`te`): native Telugu Wikipedia text, Latin-script romanization lexicon, and parallel sentence data. | Repository states CC BY-SA 4.0. | Possible resource for investigating Romanized query normalization; not a factual retrieval relevance benchmark or authoritative corpus by itself. | Public archive/release described by its repository; not present locally. | Keep release/version, source split, native/romanized pair IDs, attribution/license, and any normalization derivation. | Language contents, data types, and declared license verified in upstream README. Suitability for query normalization and downstream rights review: NOT VERIFIED. |

**Corpus decision:** no proposed external source is approved here as the project’s authoritative knowledge corpus. A human must select an appropriate source set and verify publisher/source authority and intended-use licensing. The “SAGE-Corpus-TE” path/schema mentioned in `configs/data.yaml` and `docs/data_strategy.md` is a planned custom artifact, not existing evidence.

## E. Proposed Phase 2D experiment (not executed)

### Research task and hypotheses

**Task:** Given a Telugu factual information need and a fixed, versioned evidence corpus, rank corpus chunks that are relevant to the query, preserving document/chunk provenance. Stop at an evidence package; do not generate an answer or verify claims.

**Hypotheses (not findings):**

- H1: lexical retrieval provides a reproducible baseline, but performance may vary by modality and vocabulary overlap.
- H2: dense retrieval may improve semantic matching if an embedding model’s Telugu coverage, identity, license, and local availability are verified.
- H3: normalization/representation-aware conditions may change retrieval rankings, but the existing detector and normalizer do not perform transliteration and cannot be assumed to improve performance.
- H4: explicit metadata propagation and immutable retrieval configuration can preserve provenance and prevent retrieved content from changing retrieval settings in this non-generative layer.

### Query types and data split

Use factual information needs in native Telugu, Romanized Telugu, and Telugu-English code-mixed Telugu. Preserve the modality label and query source for each record. English-only/other-language expansion is out of scope.

No retrieval train set is required for a fixed, non-learning lexical baseline. Keep a development query set for selecting configuration and a sealed evaluation query set for final measurement. If a model is trained/fine-tuned or any settings are learned, define a separate training partition before use. Query variants derived from the same underlying information need must remain grouped in one split to avoid cross-modality leakage.

The current repository provides neither corpus nor relevant-document labels, so query counts/splits cannot yet be specified honestly. Human relevance judgments should identify relevant document IDs independently of retrieved ranking, record annotator/method and adjudication, and distinguish binary from graded relevance. Automatically generated labels must be named and analyzed separately.

### Baselines, conditions, and chunking

1. **Lexical baseline:** BM25 over a documented, deterministic tokenizer. Tokenization, normalization, BM25 parameters, tie-breaking, and candidate set must be recorded. The current environment has no BM25 package; a dependency choice or a small in-repository implementation is a later implementation decision, not made here.
2. **Dense baseline:** conditional only. First verify exact model identity/version, primary source, Telugu language/script evidence, license, model availability, and reproducible inference. No current embedding model meets this audit’s verification threshold; therefore dense retrieval is not presently justified for implementation.
3. **Representation/normalization condition:** compare raw text with existing conservative `normalize_text` output and, if an explicit method is later approved and implemented, a separately named representation-aware condition. `InputRepresentation` is metadata plus normalized text, not a transliterator. Do not call it transliteration-aware retrieval without implementing and evaluating that method.
4. **Chunking:** preserve whole-document baseline where feasible and compare at least two predeclared deterministic character-budget chunk sizes with fixed overlap. The concrete budgets/overlap must be chosen after inspecting corpus lengths and query needs; do not call any value optimal without measurements. Store source/document/chunk IDs, offsets, raw text reference, and hashes.

### Metrics and reporting

Report Recall@1/5/10, MRR, and nDCG@10 only if the finalized judgment design supports them. State binary/graded relevance, unjudged-document handling, tie behavior, `k`, and evaluation unit. Report each metric by native Telugu, Romanized Telugu, code-mixed Telugu, and overall; by retrieval method, query condition, chunk configuration, and corpus version. These are proposed measurements; there are no Phase 2D values yet.

### Ablations and error analysis

- Raw query vs existing conservative normalization: isolates the effect of normalization.
- Lexical vs verified dense method, only if dense-model verification and dependency decision succeed: isolates sparse lexical vs embedding ranking.
- Whole-document vs the predeclared chunk conditions: isolates segmentation effects.
- Any Romanized/code-mix-aware normalizer only after an implementation and source of transformations are approved; isolate that method rather than attributing effects to the existing detector.

Inspect per-modality misses, lexical misses, normalization changes, chunk boundary misses, duplicate-source effects, and provenance failures. Record observed evidence and score/rank from actual runs; do not invent representative failures before the experiment.

### Leakage checks

Before scoring, report exact duplicate documents/queries, normalized duplicate content, query-to-document exact/near-duplicate matches, repeated source URLs, cross-split query-family overlap, and evaluation text copied into the indexed corpus. Preserve reports and the matching method/thresholds. The evaluation labels must not be embedded into corpus text or exposed to indexing/ranking.

### Retrieval trust-boundary evaluation

Use a separate controlled fixture with benign evidence text containing instruction-like strings. Check that returned text remains data, all provenance fields remain intact, ordering is deterministic, and configuration/index parameters are unchanged before/after retrieval. Keep this evaluation separate from claims about generation-time prompt-injection resistance: Phase 2D has no generation behavior, and deterministic retrieval tests cannot establish complete prompt-injection security.

### Anticipated failure modes (hypotheses only)

- Telugu morphological/orthographic variation reduces lexical overlap.
- Romanized spelling variation causes poor lexical matching.
- Mixed Telugu-English query terms split evidence signals across scripts/languages.
- Normalization erases useful distinctions or fails to bridge transliterations.
- Chunk boundaries separate query terms from relevant evidence.
- Duplicated/near-duplicated sources dominate top ranks or inflate apparent recall.
- Source metadata or offsets are lost during chunking/index round trips.
- Model documentation does not adequately establish Telugu retrieval capability.

These are test targets, not observed failures.

## Decisions required before implementation

1. Human approval of an authoritative, licensed evidence corpus and source list, with source-level provenance requirements.
2. Resolution of the IndicQA license discrepancy and inspection of its exact Telugu schema/splits before considering it for evaluation.
3. Creation or approval of modality-specific retrieval queries and independent relevance judgments.
4. Confirmation that the accessible Python/package environment for the project can provide the approved evaluation and test tooling.
5. If dense retrieval is desired, verification of a specific model’s Telugu evidence, version, license, and availability before selection.

Until these are resolved, do not acquire or represent data as approved, choose a dense model, implement retrieval, run retrieval experiments, or report retrieval results. No frozen Phase 2B/2C code, data, models, benchmarks, or conclusions were modified during this audit.

## Addendum — source-resolution design review (2026-10-02)

The documentation-only resolution review is in `phase2d_data_audit.md`, `phase2d_corpus_spec.md`, `phase2d_evaluation_spec.md`, `phase2d_security_design.md`, and `phase2d_human_review.md`.

### Phase interfaces and freeze boundary

- Phase 2A supplies `InputRepresentation` through `LanguageDetector.detect` / `sage_indic.detection.detect`; it does not transliterate Romanized Telugu.
- Phase 2C supplies `SafetyResult` through `SageAwareSafetyGuardrail.predict`; safety classification does not certify evidence provenance or factuality.
- Phase 2B `SageTokenizer.encode` and `encode_ids` provide frozen subword representations. They are not retrieval embeddings or proven retrieval terms; any retrieval use would be a separately measured condition.
- `docs/phase2b_freeze.md` says tokenizer modules, vocab/model files, datasets, metrics, and benchmark scripts are frozen. This includes the tokenizer processed datasets/artifacts and `experiments/saved_models/` plus tokenizer experiment outputs/scripts. Phase 2C materials to preserve include `data/processed/safety/dev.jsonl`, `data/processed/safety/eval.jsonl`, safety experiment/results, labels, evaluation conclusions, and frozen thresholds/rules recorded in the safety documents.
- Configuration convention is YAML under `configs/`, but `src/sage_indic/config.py` does not parse YAML. No dependency is selected here.

### Source findings and dispositions

- IndicQA remains **UNRESOLVED — DO NOT USE**: the current AI4Bharat HF card displays CC-BY-4.0, whereas the AI4Bharat IndicBERT repository says datasets from that work are CC-0. The local manifest's CC-0 statement is not enough to resolve the direct-source conflict or derivative redistribution conditions.
- UD_Telugu-MTG also requires license clarification: its upstream README narrative states CC BY-NC-SA 3.0 while machine-readable metadata states CC BY-SA 4.0. The local manifest repeats the former. Exclude pending authoritative clarification.
- FLORES-200 and Dakshina have verified upstream CC BY-SA 4.0 declarations, but their translation/transliteration/Wikipedia-derived roles do not make them approved factual evidence collections.
- UD Telugu-English-TECT is a code-switching linguistic treebank, not factual evidence. Its repository metadata says CC BY-SA 4.0; source-text rights lineage still requires review.
- IndicCorp v2 and Indic-Rag-Suite do not qualify as approved authoritative factual evidence corpora on this audit: source-level rights/provenance and/or generated QA relevance remain unresolved.
- No verified and human-approved factual Telugu source set or retrieval relevance labels exist in the repository. `RELEVANCE JUDGMENTS: NOT YET CREATED`.

The addendum does not authorize acquisition, implementation, experiments, or use of these candidates. Human decisions listed in `phase2d_human_review.md` remain prerequisites.
