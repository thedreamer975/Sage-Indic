# SAGE-Indic: How to Run This Project

**Repository:** Sage-Indic
**Primary Language:** Telugu (Native Script · Romanized · Code-Mixed)
**Last Updated:** 2026-11-17

This guide covers environment setup, running the test suite, launching the local
demo application (FastAPI backend + React frontend), executing each research
experiment runner, and using the Python APIs directly.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Local LLM Setup (Ollama)](#3-local-llm-setup-ollama)
4. [Running Tests](#4-running-tests)
5. [Running the Demo Application](#5-running-the-demo-application-backend--frontend)
6. [Experiment Runners](#6-experiment-runners)
7. [Python API Quick Reference](#7-python-api-quick-reference)
8. [Reproducing EXP-2E-02](#8-reproducing-exp-2e-02)
9. [Known Issues and Environment Notes](#9-known-issues--environment-notes)

---

## 1. Prerequisites

| Requirement | Minimum Version | Notes |
| :--- | :--- | :--- |
| Python | 3.10+ | Tested on 3.12.6 |
| pip | Latest | `python -m pip install --upgrade pip` |
| Git | Any | For cloning |
| Node.js | 18+ | Required only for the React/Vite frontend |
| Ollama | Any | **Only** for optional LLM paraphrasing |

> **Optional:** `transformers` (Hugging Face) is required only for the semantic safety classifier
> tests. The full test suite runs without it — 52 tests are skipped with a clear message if absent.

---

## 2. Installation

### Clone and install (editable mode)

```powershell
git clone https://github.com/thedreamer975/Sage-Indic.git
cd Sage-Indic

# Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# OR: source .venv/bin/activate    # Linux / macOS

# Install the package and all dependencies in editable mode
pip install -e .

# Optional: install development / test dependencies
pip install -e ".[dev]"

# Optional: install backend API dependencies (FastAPI + Uvicorn)
pip install -e ".[app,dev]"

# Optional: install frontend dependencies
cd frontend
npm install
cd ..
```

### Verify installation

```python
python -c "import sage_indic; print(sage_indic.__version__)"
```

### Environment variables

All secrets are loaded from environment variables — nothing is hardcoded. Create a `.env` file
in the repository root if needed:

```
# .env -- only required if using the optional LLM layer
# SAGE_LLM_ENABLED=auto          # auto | true | false
# SAGE_LLM_BASE_URL=http://127.0.0.1:11434/v1
# SAGE_LLM_MODEL=llama3.2:1b
# SAGE_LLM_TIMEOUT=25
# SAGE_LLM_MAX_TOKENS=256
# SAGE_LLM_TEMPERATURE=0.0

# Remote OpenAI-compatible provider only:
# SAGE_LLM_API_KEY_ENV=OPENAI_API_KEY
# OPENAI_API_KEY=sk-...
```

All secrets are read from environment variables; none are committed. The
frontend uses `VITE_API_BASE_URL` only when it is not served by the same origin.
See [`.env.example`](.env.example) for the complete template.

Ollama (local, no API key required) is the recommended backend for generation. See Section 3.

---

## 3. Local LLM Setup (Ollama)

The local demo application and the end-to-end evaluation (`EXP-2E-02`) can use a
running Ollama server. The application works fully without Ollama; the LLM layer is
an optional paraphrase path with a deterministic fallback.

### Install Ollama

Download from <https://ollama.com/download> for your OS.

### Pull the model used in the canonical experiment

```powershell
ollama pull llama3.2:1b
```

### Start the server

```powershell
ollama serve
# Default endpoint: http://127.0.0.1:11434
```

Ollama exposes an OpenAI-compatible `/v1/chat/completions` endpoint automatically. Verify it
is running:

```powershell
curl http://127.0.0.1:11434/v1/models
```

> If Ollama is unavailable, the experiment runner falls back to `MockGenerationProvider`
> automatically. All artifacts are still written using deterministic mock responses.

---

## 4. Running Tests

The test suite requires no external model — it uses deterministic mock providers and offline
data fixtures.

### Run all tests

```powershell
pytest
```

### Run with verbose output

```powershell
pytest -v
```

### Run a specific test file

```powershell
pytest tests/test_detection.py
pytest tests/test_bm25_retriever.py
pytest tests/test_claim_verification.py
pytest tests/test_composition.py
pytest tests/test_api.py
pytest tests/test_generation_adapter.py
pytest tests/test_safety.py
pytest tests/test_tokenizer.py
pytest tests/test_rag.py
pytest tests/test_crossscript_rag.py
```

### Expected result

```
307 passed, 52 skipped in ~57s
```

The 52 skipped tests are semantic safety classifier tests that require `transformers`.
They are **not** failures. The 37 tests added for Phase 2G are
`tests/test_composition.py` (15) and `tests/test_api.py` (22).

---

## 5. Running the Demo Application (Backend + Frontend)

The research pipeline is exposed as a local FastAPI service with a React/Vite UI.
The application demonstrates the frozen modules end to end. It is **not** a new
benchmark and produces no research metrics.

### 5.1 Start the backend

```powershell
uvicorn sage_indic.api.app:app --host 127.0.0.1 --port 8000
```

On startup the service:

1. Loads the 10-document / 30-chunk evidence corpus from `data/processed/rag/`.
2. Indexes it with BM25 + `CodeMixedQueryNormalizer` + the frozen SAGE tokenizer
   (`experiments/saved_models/sage_4000.json`, falling back to Unicode whitespace if absent).
3. Builds the SAGE safety guardrail.
4. Probes the optional LLM endpoint once.

A successful load logs `SAGE-Indic service ready (corpus=30 chunks)`.

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/api/health` | GET | Liveness and corpus-loaded flag |
| `/api/status` | GET | Corpus, retriever, safety, and LLM status |
| `/api/examples` | GET | Nine demo prompts (prompts only, never stored answers) |
| `/api/corpus` | GET | Retrieval-eligible documents and chunk counts |
| `/api/query` | POST | Run the full detection → safety → retrieval → verification → composition pipeline |

Interactive OpenAPI docs: <http://127.0.0.1:8000/docs>

Example request:

```powershell
curl -X POST http://127.0.0.1:8000/api/query `
  -H "Content-Type: application/json" `
  -d '{"query":"Charminar eppudu nirmincharu?","use_llm":false,"top_k":8}'
```

`answer_status` is one of `ANSWERED`, `PARTIALLY_ANSWERED`, `ABSTAINED`, or `BLOCKED`.
Citations (`C1`, `C2`, …) are generated only from retrieved passages; the response
also lists claim-level verification outcomes and the retrieved evidence.

### 5.2 Start the frontend (development)

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` to `http://127.0.0.1:8000`.
The UI exposes the answer, claim verification, citations, retrieved evidence,
pipeline status, and optional LLM disclosure.

### 5.3 Production build (single server)

```powershell
cd frontend
npm run build
```

If `frontend/dist/` exists when the backend starts, FastAPI serves it at
<http://127.0.0.1:8000>. Rebuild after frontend changes and restart the backend.
API routes take precedence over the static mount.

### 5.4 Verify the live demo

With the backend running:

```powershell
python scripts/verify_demo.py
# or: python scripts/verify_demo.py --base-url http://127.0.0.1:8000
```

The script executes all nine advertised examples against the live API and checks
the manually stated expected behaviour (`answer`, `partial`, `abstain`) plus
citation integrity. It does not compare answer wording, because every answer is
produced live by the pipeline. Expected summary:

```
PASSED: all advertised behaviours and citation-integrity checks succeeded.
```

### 5.5 Optional LLM paraphrase

The default mode is deterministic. Tick **Use optional LLM** in the UI or send
`"use_llm": true` to enable the paraphrase layer. A draft is accepted only if all
of its claims verify as `SUPPORTED` and it invents no citation IDs; otherwise the
deterministic extractive answer is shown and the rejection is disclosed. Provider
timeouts, unreachable endpoints, and ungrounded drafts all fall back without
breaking the response. The frozen adapter requires an explicit `true`; an omitted
`use_llm` never adds model latency.

---

## 6. Experiment Runners

All runners write versioned JSON artifacts to `experiments/results/`.

### 6.1 Phase 2B: Tokenizer Benchmark

```powershell
python experiments/run_tokenizer_experiment.py
```

Evaluates BPE, Unigram, and SAGE tokenizers at vocabulary sizes 2000 and 4000 on Native
Telugu, Romanized Telugu, and Code-Mixed test sets.

**Outputs:**
- `experiments/results/tokenizer_results.json` — machine-readable metrics
- `docs/tokenizer_results.md` — human-readable table

**Metrics:** tokens/word, compression ratio, boundary precision/recall/F1.

> **Known limitation:** The boundary evaluation proxy uses UD syntactic tokens, not gold
> intra-word morpheme boundaries. Results are reported with this caveat (`ISSUE-RV-01`).

---

### 6.2 Phase 2C: Safety Evaluation

```powershell
python experiments/run_safety_experiment.py
```

Evaluates the rule-based lexical safety guardrail on the 94-instance Telugu safety dataset
(47 dev, 47 eval).

**Outputs:**
- `experiments/results/safety_results.json`
- `docs/safety_results.md`

**Metrics:** Precision, Recall, F1, FPR, FNR by script and category.

---

### 6.3 Phase 2D: Retrieval Benchmark

```powershell
python experiments/run_retrieval_experiment.py
```

Runs all 8 cross-script retrieval conditions on the 42-query / 30-chunk pilot benchmark.

**Conditions evaluated:**
1. BM25 Baseline (unnormalized)
2. BM25 + Romanized Transliteration
3. BM25 + CodeMix-Aware Normalization
4. BM25 + SAGE Tokenizer
5. BM25 + BPE Tokenizer
6. BM25 + Unigram Tokenizer
7. Multilingual Dense Retrieval (`paraphrase-multilingual-MiniLM-L12-v2`)
8. Hybrid RRF (BM25 CodeMix + Dense)

**Outputs** (timestamped): `experiments/results/exp_2d_crossscript_*_<timestamp>.json`

**Metrics:** Recall@1, Recall@3, Recall@5, MRR@10, nDCG@10.

> Conditions 7 and 8 require: `pip install sentence-transformers`

---

### 6.4 Phase 2F: Verification Benchmark

```powershell
python experiments/run_verification_experiment.py
```

Evaluates both verifiers on the 34-fixture held-out benchmark.

**Outputs** (timestamped): `experiments/results/exp_2d_verification_*_<timestamp>.json`

**Metrics:** Accuracy, per-class precision/recall/F1, false SUPPORTED rate.

---

### 6.5 Phase 2E: End-to-End Factuality Evaluation

```powershell
# Requires Ollama running with llama3.2:1b (see Section 3)
python experiments/run_exp_2e_02.py --split both
```

**Available flags:**

| Flag | Default | Description |
| :--- | :--- | :--- |
| `--split` | `both` | `dev`, `eval`, or `both` |
| `--model` | `llama3.2:1b` | Ollama model identifier |
| `--api-base` | `http://127.0.0.1:11434/v1` | Provider endpoint |
| `--temperature` | `0.0` | Generation temperature |
| `--max-tokens` | `80` | Maximum tokens per generation |
| `--top-k` | `3` | Evidence passages retrieved |

**Outputs** (`experiments/results/exp_2e_02/`):

| File | Contents |
| :--- | :--- |
| `config.json` | Execution config + SHA-256 dataset fingerprints |
| `manifest.json` | 42-query evaluation manifest |
| `per_query_results.json` | Per-query Condition A predictions |
| `aggregate_metrics.json` | Aggregate metrics for Conditions A, C, D |
| `comparison_tables.json` | A vs B verifier; A vs C retrieval comparison |
| `error_analysis.json` | Error taxonomy and contradiction audit |
| `generation_cache.json` | Cached LLM responses for exact reproduction |
| `reproduction_instructions.md` | Self-contained reproduction guide |

> **Caching:** Responses are cached by `{condition}::{query_id}::{model}`. Rerunning uses
> the cache — no LLM calls for already-evaluated queries.

**Fallback:** If Ollama is unreachable, the runner uses `MockGenerationProvider` and
continues deterministically.

---

## 7. Python API Quick Reference

### 7.1 Language Detection

```python
from sage_indic.detection import TeluguCodeMixDetector
from sage_indic.types import LanguageCategory

detector = TeluguCodeMixDetector()

result = detector.detect("\u0c1a\u0c3e\u0c30\u0c4d\u0c2e\u0c3f\u0c28\u0c3e\u0c30\u0c4d \u0c1a\u0c3e\u0c32\u0c3e \u0c2a\u0c3e\u0c24 \u0c15\u0c1f\u0c4d\u0c1f\u0c21\u0c02")
print(result.category)    # LanguageCategory.TELUGU_NATIVE
print(result.confidence)  # float in [0, 1]

result = detector.detect("Charminar chala pata kattadam")
print(result.category)    # LanguageCategory.ROMANIZED_TELUGU

result = detector.detect("Charminar \u0c1a\u0c3e\u0c32\u0c3e beautiful")
print(result.category)    # LanguageCategory.TELUGU_ENGLISH_CODE_MIXED
```

### 7.2 Normalization

```python
from sage_indic.normalize import TeluguNormalizer

normalizer = TeluguNormalizer()
normalized = normalizer.normalize("\u0c1a\u0c3e\u0c30\u0c4d\u0c2e\u0c3f\u0c28\u0c3e\u0c30\u0c4d\u200b")  # strips invalid ZWS
```

### 7.3 Safety Guardrail

```python
from sage_indic.safety import SageAwareSafetyGuardrail

guardrail = SageAwareSafetyGuardrail()
result = guardrail.classify("\u0c2e\u0c02\u0c26\u0c41\u0c32\u0c41 \u0c35\u0c47\u0c38\u0c41\u0c15\u0c4b\u0c35\u0c21\u0c02 \u0c0e\u0c32\u0c3e")  # benign medical
print(result.label)       # "SAFE" or "UNSAFE"
print(result.confidence)  # float

# Ablation mode (disables morphology pre-processing)
ablation = SageAwareSafetyGuardrail(ablation_mode=True)
```

### 7.4 BM25 Retrieval

```python
from sage_indic.rag import BM25Retriever
from sage_indic.rag.types import CorpusChunk

chunks = [
    CorpusChunk(
        chunk_id="DOC001#c0001",
        document_id="DOC001",
        text="\u0c1a\u0c3e\u0c30\u0c4d\u0c2e\u0c3f\u0c28\u0c3e\u0c30\u0c4d \u0c39\u0c48\u0c26\u0c30\u0c3e\u0c2c\u0c3e\u0c26\u0c4d \u0c32\u0c4b \u0c09\u0c02\u0c26\u0c3f",
        source_url="https://example.com/doc001",
        content_hash="abc123",
        char_start=0,
        char_end=35,
    )
]

retriever = BM25Retriever()
retriever.index(chunks)

package = retriever.retrieve(query_id="Q001", query_text="\u0c1a\u0c3e\u0c30\u0c4d\u0c2e\u0c3f\u0c28\u0c3e\u0c30\u0c4d", top_k=3)
for r in package.results:
    print(r.chunk_id, r.score, r.rank)
```

### 7.5 CodeMix-Aware Retrieval

```python
from sage_indic.rag import BM25Retriever
from sage_indic.rag.normalizer import CodeMixedQueryNormalizer

normalizer = CodeMixedQueryNormalizer(enable_bilingual_expansion=True)
retriever = BM25Retriever(query_normalizer=normalizer)
retriever.index(chunks)

# Romanized query retrieves Telugu-script corpus
package = retriever.retrieve(
    query_id="Q001_ROM",
    query_text="Charminar ela nirminchabadindi",
    top_k=3,
)
```

### 7.6 Generation Adapter

```python
from sage_indic.generation import (
    GenerationAdapter, GenerationConfig,
    GenerationRequest, GenerationProviderType,
)
from sage_indic.generation.types import EvidencePassage
from sage_indic.types import LanguageCategory

# Mock provider (no external service required)
config = GenerationConfig(provider=GenerationProviderType.MOCK)
adapter = GenerationAdapter(config=config)

# Real provider via Ollama
config = GenerationConfig(
    provider=GenerationProviderType.API,
    model_name="llama3.2:1b",
    api_base="http://127.0.0.1:11434/v1",
    temperature=0.0,
    max_tokens=80,
)
adapter = GenerationAdapter(config=config)

passages = [
    EvidencePassage(
        passage_id="DOC001#c0001",
        text="\u0c1a\u0c3e\u0c30\u0c4d\u0c2e\u0c3f\u0c28\u0c3e\u0c30\u0c4d 1591 \u0c32\u0c4b \u0c28\u0c3f\u0c30\u0c4d\u0c2e\u0c3f\u0c02\u0c1a\u0c2c\u0c21\u0c3f\u0c02\u0c26\u0c3f.",
        source_id="DOC001",
    )
]

request = GenerationRequest(
    query_id="Q001",
    query_text="\u0c1a\u0c3e\u0c30\u0c4d\u0c2e\u0c3f\u0c28\u0c3e\u0c30\u0c4d \u0c0e\u0c2a\u0c4d\u0c2a\u0c41\u0c21\u0c41 \u0c28\u0c3f\u0c30\u0c4d\u0c2e\u0c3f\u0c02\u0c1a\u0c2c\u0c21\u0c3f\u0c02\u0c26\u0c3f?",
    language_category=LanguageCategory.TELUGU_NATIVE,
    evidence_passages=passages,
    max_tokens=80,
    temperature=0.0,
)

draft = adapter.generate(request)
assert draft.is_verified is False  # Always False until independently verified
print(draft.answer_text)
print(draft.candidate_claims)
print(draft.citations)
```

### 7.7 Claim Verification

```python
from sage_indic.verification import (
    verify_draft_answer,
    RelationAwareClaimVerifier,
    LinguisticClaimVerifier,
)

verifier = RelationAwareClaimVerifier()   # proposed method
# verifier = LinguisticClaimVerifier()   # baseline

report = verify_draft_answer(draft, passages, verifier=verifier)
print(report.overall_eligibility)      # AnswerEligibility enum
print(report.fully_supported_count)
print(report.contradicted_count)
print(report.insufficient_count)

for result in report.claim_results:
    print(result.claim.text, "->", result.outcome, result.confidence)
```

### 7.8 Query Service and Composition

```python
from sage_indic.pipeline.service import SageQueryService

service = SageQueryService()
response = service.query("Charminar eppudu nirmincharu?", use_llm=False, top_k=8)

print(response.answer_status.value)   # ANSWERED | PARTIALLY_ANSWERED | ABSTAINED | BLOCKED
print(response.answer_text)
for citation in response.citations:
    print(citation.citation_id, citation.evidence_id, citation.verification_status)
for claim in response.answer_claims:
    print(claim.claim_id, claim.verification_status, claim.text)
print(response.verification_summary.to_dict())
print(response.generation_metadata.used_mode.value)  # deterministic | llm | llm_fallback
```

The service performs detection, safety, code-mix-normalized retrieval, sentence
selection, extractive claim verification, and composition. `AnswerResponse.to_dict()`
is the exact JSON returned by `POST /api/query`.

---

## 8. Reproducing EXP-2E-02

```powershell
# 1. Start Ollama (optional -- cache covers already-evaluated queries)
ollama serve

# 2. Run the experiment
python experiments/run_exp_2e_02.py --split both --model llama3.2:1b

# 3. Quick results inspection
python -c "import json,pathlib; m=json.loads(pathlib.Path('experiments/results/exp_2e_02/aggregate_metrics.json').read_text()); a=m['condition_a_sage_indic']; c=m['condition_c_lexical_baseline']; print('Cond A retrieval hit rate:', a['retrieval_hit_rate_on_answerable']); print('Cond C retrieval hit rate:', c['retrieval_hit_rate_on_answerable']); print('Cond A fact-correct rate:', a['fact_correct_rate_on_answerable'])"

# 4. Forensic Audit (EXP-2E-02-AUDIT-V1) Recomputation
pytest tests/test_exp_2e_02_audit.py -v
python -c "import json, pathlib; m=json.loads(pathlib.Path('experiments/results/exp_2e_02_audit_v1/recomputed_metrics.json').read_text()); print('Audited Cond A hits:', m['condition_a_sage_indic']['retrieval_hits_on_answerable'], '/ 30'); print('Audited Cond A fact-correct:', m['condition_a_sage_indic']['fact_correct_answers_count_reported_definition'], '/ 30')"
```

### Dataset integrity verification

```powershell
python -c "
import hashlib, pathlib
files = [
    'data/processed/rag/phase2d_chunks.jsonl',
    'data/processed/rag/phase2d_eval_queries_dev.jsonl',
    'data/processed/rag/phase2d_eval_queries_eval.jsonl',
    'data/processed/rag/dev_verification.jsonl',
    'data/processed/rag/eval_verification.jsonl',
]
for f in files:
    h = hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
    print(pathlib.Path(f).name, h)
"
```

Expected hashes are recorded in `experiments/results/exp_2e_02/config.json`.

---

## 9. Known Issues & Environment Notes

| Issue | Details |
| :--- | :--- |
| **52 skipped safety tests** | Require `pip install transformers`. Not failures. |
| **Dense retriever** | Requires `pip install sentence-transformers` |
| **Semantic safety model unavailable** | If the local multilingual sentence-transformer snapshot is incomplete, the app runs `SAGE_ContextualGuardrail_LexicalOnlyFallback`. Morphology/context logic still runs; the dense signal is neutral. Disclosed in `/api/status` and in each response. |
| **Lexical safety fallback gaps** | The fallback does not block every unlisted term (e.g. some English variants such as `bomb`, `hack`, `harm`). This is a documented Phase 2C limitation, not a new regression. |
| **LLM citation format** | `llama3.2:1b` rarely produces reliable `[DOC_ID#chunk]` tags. The app never trusts model-authored citation IDs; model drafts are accepted only when fully verified, otherwise the deterministic answer is shown. |
| **LLM latency** | Ollama on CPU can exceed the 25 s default timeout, producing `used_mode=llm_fallback`. The deterministic answer remains visible. Increase `SAGE_LLM_TIMEOUT` or use a stronger model if needed. |
| **Corpus scale** | 10 documents / 30 chunks. Queries outside this corpus correctly abstain rather than fabricate. |
| **`/health` returns 404** | Only `/api/health` is implemented. External pollers should use `/api/health`. |
| **Package version discrepancy** | `pyproject.toml` declares `0.1.0`, `__init__.py` declares `0.3.0`. Known issue (`ISSUE-VER-01`); does not affect functionality. |
| **Windows path separators** | All scripts use `pathlib.Path` and are Windows-compatible. |

---

## Project Structure

```
Sage-Indic/
├── src/sage_indic/           # Main package
│   ├── detection/            # Language and script detection
│   ├── tokenizer/            # SAGE tokenizer + BPE/Unigram baselines
│   ├── safety/               # Context-aware safety guardrail
│   ├── rag/                  # BM25, dense, hybrid retrieval + normalizers
│   ├── generation/           # Generation adapter, prompt composer
│   ├── verification/         # Claim verification (Linguistic + RelationAware)
│   ├── composition/          # Phase 2G response composition + query analysis
│   ├── pipeline/             # End-to-end query service
│   └── api/                  # FastAPI application
├── frontend/                 # React + TypeScript + Vite demo UI
├── tests/                    # Test suite (307 passed, 52 skipped)
├── experiments/              # Experiment runners and saved results
│   ├── run_tokenizer_experiment.py
│   ├── run_safety_experiment.py
│   ├── run_retrieval_experiment.py
│   ├── run_verification_experiment.py
│   ├── run_exp_2e_02.py      # End-to-end evaluation
│   └── results/              # All versioned experiment outputs
├── data/processed/           # Processed corpora and evaluation sets
├── docs/                     # Research documentation
├── scripts/                  # Data preparation + verify_demo.py
├── EXPERIMENT_LEDGER.md      # Immutable research record
├── OPEN_ISSUES.md            # Known limitations and defects
├── progress.md               # Research milestone tracker
└── HOW_TO_RUN.md             # This file
```
