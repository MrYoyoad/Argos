# Why IS — Not Just LLM-as-a-Judge

> **Note (March 2026):** This document uses the legacy IS ≥ 3.0 threshold (40.1% captured). Current NIV thresholds supersede this: IS ≥ 2.00 = 61.6% useful (κ=0.818), IS ≥ 3.80 = 23.1% clearly conveyed (κ=0.690). See [threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md).

## The Problem

LLM-as-a-Judge (e.g., Claude Opus evaluating ref/hyp pairs) provides rich holistic assessment but cannot serve as the **sole** evaluation metric for a production VSP system. The Intelligibility Score (IS) fills five critical gaps.

---

## 1. Deployment Constraint

IS runs on bare Python — no GPU, no API key, no internet. A defense or enterprise client operating the VSP pipeline on an **air-gapped workstation** can score every segment in milliseconds. LLM-as-a-Judge requires either a cloud API or a local LLM; neither is available in that environment.

## 2. Determinism and Reproducibility

IS produces the **exact same score** every time, on every machine. LLM judges are inherently non-deterministic — the same input can yield different verdicts across runs due to sampling variance. Our intra-rater reliability measured 86.7%, meaning ~13% of scores change on re-evaluation (Zheng et al., 2023). For a benchmark tracked across model versions, you need a fixed ruler that does not wobble.

## 3. Continuous Signal vs. Coarse Ordinal

LLM-as-a-Judge naturally produces categorical labels (Y / P / N). Forcing it to output a 1–5 float introduces calibration noise and prompt sensitivity (Liu et al., 2023). IS is a weighted **continuous score** (0.0–5.0) derived from 6 complementary signals, enabling fine-grained regression analysis, threshold tuning, and statistical testing (t-tests, effect sizes) that a 3-level label cannot support.

## 4. Known Biases

Academic literature documents at least **12 systematic biases** in LLM judges: position bias, verbosity bias, and self-enhancement bias among the most prominent (Wang et al., 2024; Panickssery et al., 2024). IS, as a fixed formula, has none. Our own data confirms the LLM judge measures a *different construct* — simultaneously more conservative on full success (23% Y vs. 40% IS >= 3) and more generous on partial credit (65% Y+P vs. 51% salvage).

## 5. Decomposability and Interpretability

IS breaks into 6 named components (WER, WWER, semantic similarity, phonetic overlap, entity accuracy, length ratio), each mapping to a specific failure mode. When IS drops, you can diagnose **why** — word accuracy vs. meaning vs. hallucination length. An LLM judge returns a verdict and a rationale paragraph, but you cannot query `WHERE semantic < 0.3 AND phonetic > 0.7` against it.

---

## Complementary, Not Competing

| Role | IS | LLM-as-a-Judge |
|------|-----|-----------------|
| Purpose | Operational metric | Validation oracle |
| Cost | $0, deterministic | API / GPU per call |
| Deployable offline | Yes | No |
| Granularity | Continuous 0–5 | Categorical Y/P/N |
| Diagnosable | 6 components | Free-text rationale |
| Bias-free | Yes (fixed formula) | No (12+ known biases) |

**Bottom line**: IS runs in production; LLM-as-a-Judge audits the IS framework and catches edge cases the formula misses (e.g., our 165 salvageable segments). You need both — one to deploy, one to validate.

---

## References

- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* NeurIPS 2023. [arXiv:2306.05685](https://arxiv.org/abs/2306.05685)
- Liu, Y. et al. (2023). *G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment.* EMNLP 2023. [arXiv:2303.16634](https://arxiv.org/abs/2303.16634)
- Wang, P. et al. (2024). *Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge.* [arXiv:2410.02736](https://arxiv.org/abs/2410.02736)
- Panickssery, A. et al. (2024). *Self-Preference Bias in LLM-as-a-Judge.* [arXiv:2410.21819](https://arxiv.org/abs/2410.21819)
- Wolfe, C. R. (2024). *Using LLMs for Evaluation.* [Substack](https://cameronrwolfe.substack.com/p/llm-as-a-judge)
- Yan, E. (2024). *Evaluating the Effectiveness of LLM-Evaluators.* [eugeneyan.com](https://eugeneyan.com/writing/llm-evaluators/)
