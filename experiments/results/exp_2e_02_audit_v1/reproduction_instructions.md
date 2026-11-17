# SAGE-Indic: EXP-2E-02 Forensic Audit Reproduction Instructions

## 1. Audit Identifier
- **Audit ID:** `EXP-2E-02-AUDIT-V1`
- **Target Experiment:** `EXP-2E-02` (End-to-End Grounded Factuality Evaluation)
- **Target Run Date:** 2026-10-16
- **Audit Execution Date:** 2026-10-18

---

## 2. Verified Dataset Hashes (SHA-256)

All underlying datasets verified against their cryptographic checksums:

| Dataset File | SHA-256 Digest | Status |
| :--- | :--- | :--- |
| `data/processed/rag/phase2d_chunks.jsonl` | `8a51ae3069b3f7336947d3ed972276fbd7378133d269aec2e8b0d7493797b543` | VERIFIED MATCH |
| `data/processed/rag/phase2d_eval_queries_dev.jsonl` | `aaf983b524147116b7289c681745d2d359b9299842524183e70b73f807998965` | VERIFIED MATCH |
| `data/processed/rag/phase2d_eval_queries_eval.jsonl`| `da26df140621b82b12567bdc29040768cb8241d258689f534c8ae4ce130c0609` | VERIFIED MATCH |
| `data/processed/verification/dev_verification.jsonl` | `2d4ed26b4a61c71834a229dac833a3fb6cdafa72dfca795d1c4733d10c6590df` | VERIFIED MATCH |
| `data/processed/verification/eval_verification.jsonl`| `2763b534068b2b4813701915f542d79fb04e7da4e3e461aef77805da293de682` | VERIFIED MATCH |

---

## 3. How to Independently Recompute Audit Metrics

To verify all recomputed figures from the raw per-query artifacts:

```bash
# 1. Run audit verification script directly against saved artifacts
python -c "
import json
with open('experiments/results/exp_2e_02/per_query_results.json', encoding='utf-8') as f:
    pq = json.load(f)
ans = [r for r in pq if r['is_answerable']]
print(f'Total: {len(pq)} | Ans: {len(ans)} | Hits: {sum(1 for r in ans if r[\"retrieval_hit\"])}/30')
print(f'Fact-Correct (Reported): {sum(1 for r in ans if r[\"fact_correct\"] is True)}/30')
print(f'Abstentions: {sum(1 for r in pq if r[\"is_abstention\"])}/42')
"
```

---

## 4. How to Run Audit Regression Tests

Run the test suite verifying that abstentions are never scored as fact-correct and that empty evidence is handled strictly:

```bash
# Run specific audit regression test suite
pytest tests/test_exp_2e_02_audit.py -v

# Run full project test suite
pytest
```
Expected output: All unit and regression tests pass (with 52 semantic classifier tests skipped if `transformers` is not installed).
