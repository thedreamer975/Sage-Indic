# SAGE-Indic: 2-Day Medium-Scale Project Extension Plan

**Document Version:** 1.0.0  
**Target Timeline:** 48 Hours  
**Focus:** Telugu Corpus Expansion (Wikipedia API), Advanced Model Upgrades (Kaggle GPU / vLLM / Cloud SLMs), Context-Aware Safety Hardening, and Hybrid Grounded-Parametric Generation.  
**Date:** 2026-11-18  

---

## 1. Executive Summary & Research Rationale

The initial research prototype of SAGE-Indic established the mathematical foundation and end-to-end interface for:
1. Script and code-mix detection across Native, Romanized, and Code-Mixed Telugu.
2. SAGE morphological tokenization.
3. Strict deterministic evidence-grounded claim verification.

However, to substantiate the project's empirical research claims and support realistic open question-answering, the following gaps must be closed:
1. **Corpus Scale:** The current demonstration corpus of 10 documents (30 chunks) is too narrow. A user asking about prominent cultural figures (e.g., *"శ్రీకృష్ణదేవరాయలు ఎవరు?"*) triggers a complete abstention because the corpus lacks relevant passages.
2. **Model Capability & Latency:** The local `llama3.2:1b` model running on CPU suffers from severe Telugu token fragmentation, weak reasoning, and frequent 25-second timeouts.
3. **Safety Evaluation Scale:** The current 94-sample safety evaluation set must be expanded to a medium-scale benchmark (500+ samples) incorporating community datasets (HOLD-Telugu, Sandalphon, 2025 Abusive dataset) and explicit morphological safe negation.
4. **Interaction Contract:** When a query is out-of-corpus, the system should not abruptly refuse to answer; instead, it should provide a general answer while clearly flagging that no verified corpus references exist.

This plan details a concrete, high-velocity 48-hour roadmap to scale the dataset, upgrade model serving via Kaggle GPU, and implement hybrid generation.

---

## 2. Model Selection Analysis: Why Llama 3.2:1B Was Used & Why We Must Upgrade

### 2.1 The Original Rationale for `llama3.2:1b`
* **Zero Infrastructure Cost:** At ~1.23 billion parameters (quantized to ~1.3 GB in 4-bit), it fits inside 2 GB of RAM on any consumer laptop without requiring a dedicated GPU.
* **OpenAI-Compatible Local API:** Served via Ollama on `http://127.0.0.1:11434/v1`, allowing local execution without external API credentials or cloud accounts.
* **Developer Prototyping:** Ideal for wiring up the `ExternalAPIProvider` interface and confirming request/response JSON serialization.

### 2.2 Why `llama3.2:1b` Fails for SAGE-Indic (Root Causes)
1. **Extreme Telugu Token Fragmentation (Fertility):**
   * Llama's tokenizer is optimized primarily for English and Western European languages. A single Telugu syllable or word often splits into 4 to 8 byte-level subword tokens.
   * *Consequence:* The effective context window is severely reduced, and the model struggles to preserve Telugu grammar, case markers, and morphological semantics.
2. **Limited Pretraining Representation:**
   * Telugu constitutes less than 0.05% of Llama's pretraining corpus. The model cannot reliably generate coherent Native or Romanized Telugu without hallucinations.
3. **CPU Latency & Timeouts:**
   * On consumer laptop CPUs without GPU acceleration, inference takes 25 to 35 seconds per prompt. This triggered the `ProviderTimeoutError: Request timed out after 25.0s` observed in the web UI.
4. **Research Validity:**
   * A 1B English-centric model cannot validate research hypotheses regarding Telugu factuality or atomic claim extraction.

---

## 3. Recommended Model Replacements & Kaggle GPU Architecture

To achieve fluent Telugu generation, sub-second latency, and rigorous factuality, we upgrade from local CPU inference to GPU-accelerated serving.

### 3.1 Model Evaluation Matrix for Telugu

| Model | Parameters | Native Telugu Quality | Tokenizer Fertility (Telugu) | VRAM Required | Recommended Serving Platform |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen 2.5 7B Instruct** | 7.6B | **Exceptional** | **Low (152k vocab)** | ~5.5 GB (4-bit) / ~15 GB (fp16) | **Kaggle T4 GPU (vLLM / Ollama)** |
| **Sarvam-1 (2B)** | 2.0B | **Very High (Indic Native)** | **Extremely Low (Indic-tuned)** | ~2.5 GB (4-bit) / ~4.5 GB (fp16) | **Kaggle T4 or Local GPU** |
| **Gemma 2 9B Instruct** | 9.2B | **High** | Medium (256k vocab) | ~6.5 GB (4-bit) / ~18 GB (fp16) | Kaggle T4 x2 (vLLM) |
| **Llama 3.1 8B Instruct** | 8.0B | Moderate-High | High (128k vocab) | ~5.8 GB (4-bit) / ~16 GB (fp16) | Kaggle T4 (vLLM / Ollama) |
| **Gemini 1.5/2.0 Flash (API)** | Undisclosed | **State of the Art** | Native optimized | 0 GB (Cloud) | Direct API (OpenAI-compatible) |
| **Groq (Llama 3.3 70B)** | 70B | High | High | 0 GB (Cloud) | Direct API (Sub-second speed) |

> [!IMPORTANT]
> **Primary Recommendation:** 
> 1. **Kaggle GPU Option:** Serve **Qwen 2.5 7B Instruct** or **Sarvam-1 2B** via vLLM on a free Kaggle T4 notebook.
> 2. **Instant Zero-Setup Alternative:** Use **Gemini Flash** or **Groq** via their OpenAI-compatible endpoint for development speed, switching to Kaggle for open-weights evaluation.

### 3.2 Connecting SAGE-Indic to Kaggle GPU via Tunnel

```
Local SAGE-Indic Application (127.0.0.1:8000)
             │
             │ HTTP POST /v1/chat/completions (OpenAI compatible)
             ▼
[Secure Tunnel: Cloudflare Tunnel / ngrok]
             │
             ▼
[Kaggle Notebook with NVIDIA Tesla T4 (16 GB VRAM)]
      └─ vLLM or Ollama Server
           └─ Serving Qwen 2.5 7B Instruct (Q4_K_M)
                └─ Ultra-fast generation (< 800 ms per query)
```

#### Step-by-Step Kaggle Server Setup:
1. Open a Kaggle notebook with **GPU T4 x2** enabled (30 free hours/week).
2. Install serving engine:
   ```bash
   pip install vllm pyngrok
   ```
3. Start the vLLM OpenAI-compatible server:
   ```bash
   python -m vllm.entrypoints.openai.api_server \
       --model Qwen/Qwen2.5-7B-Instruct \
       --port 8000 \
       --gpu-memory-utilization 0.90 \
       --max-model-len 4096 &
   ```
4. Expose via ngrok or Cloudflare tunnel:
   ```python
   from pyngrok import ngrok
   tunnel = ngrok.connect(8000)
   print("Public SAGE endpoint:", tunnel.public_url)
   ```
5. Update local `.env`:
   ```bash
   SAGE_LLM_ENABLED=true
   SAGE_LLM_BASE_URL=https://<your-ngrok-id>.ngrok-free.app/v1
   SAGE_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
   SAGE_LLM_TIMEOUT=15
   ```
The SAGE-Indic `ExternalAPIProvider` connects immediately with zero code changes!

---

## 4. Medium-Scale Corpus Expansion Plan: Telugu Wikipedia Ingestion

### 4.1 Target Scale & Domain Distribution

We scale the corpus from **10 documents (30 chunks)** to **500 curated documents (~4,000 to 6,000 chunks)**.

| Domain | Target Articles | Example Topics | Research Justification |
| :--- | :--- | :--- | :--- |
| **History & Dynasties** | 120 | శ్రీకృష్ణదేవరాయలు, విజయనగర సామ్రాజ్యం, కాకతీయులు, శాతవాహనులు, కుతుబ్ షాహీలు | Resolves out-of-corpus queries for major historical entities. |
| **Culture, Arts & Literature** | 100 | అష్టదిగ్గజాలు, అన్నమయ్య, పోతన, త్యాగరాజు, కూచిపూడి, సంక్రాంతి | Evaluates cultural factuality and Telugu literary expressions. |
| **Geography & Heritage Sites** | 100 | తిరుమల, అమరావతి, నాగార్జున సాగర్, భద్రాచలం, లేపాక్షి | Factual entity retrieval across geographical coordinates. |
| **Science, Health & Medicine** | 90 | ఔషధ మొక్కలు, పాము కాటు చికిత్స, ప్రాథమిక చికిత్స, వైరాలజీ | Essential for testing benign-sensitive safety disambiguation. |
| **Modern Biographies & News** | 90 | ప్రముఖ శాస్త్రవేత్తలు, నాయకులు, విద్యాసంస్థలు | Factual claim verification with numerical and date anchors. |

### 4.2 Ingestion Architecture (`scripts/ingest_telugu_wikipedia.py`)

Using the official Wikimedia REST API (`https://te.wikipedia.org/w/api.php`) ensuring 100% legal compliance and research provenance:
1. **Filter & Sanitize:** Strip Wikipedia markup, navigation sidebars, and citations; preserve section headings.
2. **Permanent Provenance:** Store document title, article URL, revision `oldid`, publisher ("Wikimedia Foundation / Telugu Wikipedia Contributors"), and `CC-BY-SA-4.0` license metadata.
3. **Deterministic Paragraph Chunking:** Segment into 300–600 character passages with character offsets `char_start` and `char_end`.
4. **Cryptographic Integrity:** Compute SHA-256 hash for raw article text, normalized text, and each generated chunk.
5. **BM25 Re-indexing:** Index all chunks into `BM25Retriever` with the `CodeMixedQueryNormalizer`.

---

## 5. Context-Aware Safety Improvements & Dataset Scaling

### 5.1 Safety Dataset Scaling (Medium Scale)

We expand `data/processed/safety/` from 94 samples to **500+ verified samples** (250 Dev, 250 Eval), balancing classes across all three input modalities:

```
Total Safety Benchmark (500 samples)
├── Native Telugu (170 samples)
├── Romanized Telugu (170 samples)
└── Telugu-English Code-Mixed (160 samples)
```

Each split maintains:
* **`SAFE` (60%):** Standard general queries + 25% **Benign-Sensitive** queries (medical poison antidotes, historical warfare, figurative hyperbole like *"work killing me"*).
* **`UNSAFE` (40%):** Violence incitement, harassment, targeted slurs, and suicide prompts.
* **Adversarial Subset (15%):** Spaced words (`c h a m p e s t a`), leetspeak (`k1ll`), punctuation injection (`k*i*l*l`).

### 5.2 Enhancements to `SageAwareSafetyGuardrail`
1. **Safe Negation Detection:**
   * Detect bound negative verbal suffixes (`-కూడదు`, `-వద్దు`, `-రాదు`, `-లేవు`).
   * *Example:* `ఎవరినీ చంపకూడదు` ("Must not kill anyone") is classified as **SAFE**, overriding the violence root `చంప`.
2. **Transliteration Normalization (Sandalphon Finding):**
   * Pre-map frequent Romanized phonetic variations (`champesthamu` $\rightarrow$ `champestanu`, `kodatham` $\rightarrow$ `kottadam`) into canonical root keys.
3. **Lexicon Bootstrapping:**
   * Ingest root seeds from `Cleanword` and `HOLD-Telugu` into `CRITICAL_VIOLENCE_ROOTS` while filtering out general polysemic words (`మందు`, `విషం`, `యుద్ధం`) that belong exclusively to contextual disambiguation.

---

## 6. Hybrid Grounded-Parametric Generation Architecture

To address the issue where out-of-corpus queries (like Sri Krishnadevarayalu) return a hard rejection, we implement **Hybrid Mode** in `composer.py`:

```
User Query
    │
    ▼
[Safety Guardrail] ──(UNSAFE)──> Refusal Message
    │ (SAFE)
    ▼
[BM25 Retrieval & Sufficiency Check]
    │
    ├─────────────────────────────────────────┐
    │ Case A: Evidence Found (Coverage > 0)   │ Case B: Out-of-Corpus (Coverage == 0)
    ▼                                         ▼
[Grounded Answer Composition]             [Parametric Knowledge Generation]
- Verbatim or LLM paraphrased              - LLM answers from general training
- Inline citations [C1], [C2]              - Citations: [] (Empty)
- Status: ANSWERED                         - Status: UNGROUNDED_GENERAL_KNOWLEDGE
- Verified claims badge                    - Prominent UI Disclaimer:
                                             "⚠️ సేకరించిన పత్రాలలో ఆధారాలు లభించలేదు. 
                                              ఈ సమాధానం సాధారణ మోడల్ జ్ఞానం నుండి ఇవ్వబడింది."
```

---

## 7. Hour-by-Hour 48-Hour Execution Roadmap

### Day 1: Data Ingestion, Corpus Scaling & Safety Hardening

| Timeframe | Phase | Concrete Deliverables | Invariant / Validation Check |
| :--- | :--- | :--- | :--- |
| **Hours 00–04** | Wikipedia API Harvester | Implement `scripts/ingest_telugu_wikipedia.py` using MediaWiki API to fetch 500 verified articles (including Vijayanagara, Krishnadevaraya, Kakatiyas). | Check CC-BY-SA 4.0 license, permanent `oldid` storage, and valid UTF-8. |
| **Hours 04–08** | Ingestion & BM25 Index | Generate normalized texts, compute SHA-256 chunk hashes, output `phase2d_chunks.jsonl`, and rebuild BM25 index. | Ingestion roundtrip invariant: `normalized_text[start:end] == chunk.text`. |
| **Hours 08–14** | Safety Dataset Expansion | Expand `dev.jsonl` and `eval.jsonl` from 94 to 500 balanced items using HOLD-Telugu, Sandalphon, and benign-sensitive pairs. | Zero data leakage between dev and eval splits; verify exact 50/50 balance. |
| **Hours 14–18** | Safety Guardrail Logic | Implement safe negation (`-కూడదు`), transliteration pre-mapping, and Cleanword root integration in `guardrail.py`. | Run `tests/test_safety.py`. Ensure benign FPR $\le 5\%$. |
| **Hours 18–24** | Corpus & Safety Validation | Run retrieval tests on 50 synthetic queries (Native, Romanized, Code-Mixed) against the new 500-doc corpus. | Confirm query *"శ్రీకృష్ణదేవరాయలు ఎవరు?"* returns top-3 relevant chunks. |

### Day 2: Kaggle GPU Bridge, Hybrid Generation & Evaluation

| Timeframe | Phase | Concrete Deliverables | Invariant / Validation Check |
| :--- | :--- | :--- | :--- |
| **Hours 24–28** | Kaggle GPU Notebook | Launch Kaggle T4 notebook with vLLM serving `Qwen/Qwen2.5-7B-Instruct` (or `sarvamai/sarvam-1`). Configure ngrok tunnel. | Verify OpenAI endpoint responds with valid JSON in $< 1.0$s latency. |
| **Hours 28–32** | SAGE Integration | Update `.env` to point `SAGE_LLM_BASE_URL` to the Kaggle tunnel. Verify `probe_provider()` in `service.py`. | Provider probe succeeds; latency metadata captured accurately. |
| **Hours 32–38** | Hybrid Response Mode | Update `composer.py` and `service.py` to support `UNGROUNDED_GENERAL_KNOWLEDGE` status with UI warning badge when coverage is 0. | No synthetic citation IDs created on out-of-corpus queries; `citations=[]`. |
| **Hours 38–42** | Web UI Updates | Update `frontend/src/App.tsx` and `types.ts` to render the ungrounded disclaimer banner and highlight normalized input across all scripts. | Test UI on localhost:8000 across Native, Romanized, and Code-Mixed queries. |
| **Hours 42–48** | End-to-End Evaluation & Ledger | Run full test suite, execute benchmark evaluation, record metrics in `EXPERIMENT_LEDGER.md`, and freeze documentation. | All unit tests pass; 100% reproducible run script logged. |

---

## 8. Risk Management & Fallback Contingencies

1. **Kaggle GPU Session Timeout (12-hour limit):**
   * *Mitigation:* The Kaggle tunnel script can be restarted with one click.
   * *Fallback:* SAGE-Indic already supports direct API fallbacks (Groq, Together, or Gemini Flash via OpenAI-compatible endpoints) configured with a single environment variable (`SAGE_LLM_BASE_URL`).
2. **Wikipedia Ingestion Noise:**
   * *Mitigation:* Filter out stub pages, disambiguation pages, and category lists; require minimum 400 characters of clean prose per article.
3. **Strict Research Boundary:**
   * *Invariant:* Never present an out-of-corpus answer as verified evidence. The `UNGROUNDED` flag must remain strictly visible in the UI and data payloads.