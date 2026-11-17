# SAGE-Indic: EXP-2E-02 Reproduction Instructions

## Experiment Identifier
- **ID:** `EXP-2E-02`
- **Component:** End-to-End Grounded Factuality Evaluation
- **Execution Date:** 2026-10-16

## Execution Environment
- **Operating System:** Windows (Platform: `win32`)
- **Python Version:** `3.12.6`
- **Provider Used:** `api`
- **Model Identifier:** `llama3.2:1b`
- **API Base:** `http://127.0.0.1:11434/v1`

## Exact Reproduction Command
```bash
python experiments/run_exp_2e_02.py --provider api --model llama3.2:1b --api-base http://127.0.0.1:11434/v1 --split both --max-tokens 80
```

## Dataset Files Verified by SHA-256
- `phase2d_chunks.jsonl`: `8a51ae3069b3f7336947d3ed972276fbd7378133d269aec2e8b0d7493797b543`
- `phase2d_eval_queries_dev.jsonl`: `aaf983b524147116b7289c681745d2d359b9299842524183e70b73f807998965`
- `phase2d_eval_queries_eval.jsonl`: `da26df140621b82b12567bdc29040768cb8241d258689f534c8ae4ce130c0609`
- `dev_verification.jsonl`: `2d4ed26b4a61c71834a229dac833a3fb6cdafa72dfca795d1c4733d10c6590df`
- `eval_verification.jsonl`: `2763b534068b2b4813701915f542d79fb04e7da4e3e461aef77805da293de682`
