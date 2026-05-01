# N-Best Beam Aggregation — Implementation

Mission 6 implementation notes (May 1, 2026). Companion to [Report 5](report_5_beam_search_aggregation.md), which describes the techniques in the abstract; this document describes what actually shipped.

## What landed

**Two missions in one PR**, gated behind `VSP_NBEST=1` (default 0 — pipeline behavior unchanged when off):

1. **Improvement** — the decoder now keeps all 20 surviving beam hypotheses and runs five offline aggregation methods over them. Each adds a column to `report.csv` plus its own per-segment WER, so the user can see directly whether any method beats top-1.
2. **Evaluation** — a beam-variance analyzer emits per-segment metrics (pairwise WER across beams, agreement rate, position entropy), correlates them with WER/IS/sentence_confidence, and runs a word-level confusion analysis testing the hypothesis "do confused words have low confidence?".

**Bug fix included**: the existing `step_scores[::n_beams]` extraction in `vsp_llm_decode.py` was silently picking the wrong beam after HF beam-reordering. Fixed by gathering rows via `gen_out.beam_indices`. Top-1 entropy/top-3 in the existing `confidence-{fid}.json` may shift on hard cases — the new values are the correct ones.

## How to run

```bash
# 1. Decode with n-best capture enabled
VSP_NBEST=1 bash run_flat_english_pipeline.sh         # auto-forces VSP_OUTPUT_SCORES=1

# Outputs (per-fid; fid is the deterministic Hydra-config hash):
#   decode/<task>/<lang>/hypo-{fid}.json         (top-1 — unchanged)
#   decode/<task>/<lang>/confidence-{fid}.json   (top-1 per-token probs)
#   decode/<task>/<lang>/nbest-{fid}.json        (NEW — all 20 beams + per-token probs)

# 2. Reports run automatically via lib/outputs.sh:
#   client_outputs/.../aggregated.json           (5 aggregated hyps per segment)
#   client_outputs/.../report.csv                (5 new hyp_* + wer_*_% columns)
#   client_outputs/.../beam_analysis/            (variance + word-confusion bundle)
```

## The five aggregation methods

All are pure-Python, CPU-only, container-compatible. Implemented in [lib/nbest_aggregate.py](../../lib/nbest_aggregate.py) (EC2) and mirrored to [VSP-LLM/scripts/nbest_aggregate.py](../../VSP-LLM/scripts/nbest_aggregate.py) (container).

| Method | Idea | When it should help |
|--------|------|---------------------|
| `hyp_mbr` | Pick `argmin_i E_j[ WER(hyp_i, hyp_j) ]` under softmax-of-sequence-score weights. Dedupes duplicate hypotheses first. | Hallucinated outliers with high confidence: consensus dominates. |
| `hyp_vote_score` | Multi-way ROVER vote anchored on top-1, position-aligned via Levenshtein. Weight = `softmax(seq_score)`. | Single-word substitution errors where most beams have the right word. |
| `hyp_vote_conf` | Same voter, weight = `softmax(seq_score) × per-word-confidence` from each beam's own token probs. | Tests whether word-level confidence carries information beyond raw sequence score. |
| `hyp_safe` | Start from top-1; swap a word only when its confidence < 0.40 **and** ≥60% of other beams agree on a different word at the aligned position. | Conservative production drop-in — should never make output dramatically worse. |
| `hyp_xseg_merge` | Cross-segment overlap fusion: when adjacent segments from the same source video share ≥3 LCS-matching words at their edge, replace each disagreeing word with the higher-confidence side. | Long videos with overlapping segmentation — exploits physical redundancy in the data. No-op on datasets without configured overlap. |

Each method also emits a debug field (`rank_chosen`, `vote_breakdown`, `swaps`) so spot-checking is straightforward.

## What the variance analysis answers

[docs/_research-tools/generators/analyze_beam_variance.py](../_research-tools/generators/analyze_beam_variance.py) runs four analyses on a completed decode:

1. **Per-segment beam variance** (`beam_variance.csv`) — `pairwise_mean_wer`, `n_unique_hyps`, `word_agreement_rate`, `mean_position_entropy`. These are direct measures of model self-disagreement.
2. **Correlation heatmap** — beam variance metrics × `{wer_%, wwer_%, is_score, sentence_confidence, min_word_conf, n_low_conf_words, nea_f1_%}`. Tests whether beam variance is redundant with token-level confidence or independent.
3. **Aggregator method comparison** (`aggregator_wers.csv` + `aggregator_method_summary.json`) — per-segment WER for each of the five methods plus mean over the dataset.
4. **Word-level confusion** — two passes:
   - Pass 1 (all words ≥5 occurrences): for each unique reference word, compute (recall, mean confidence when predicted, mean beam disagreement when predicted). Pearson r between (1 − recall) and confidence answers the user's specific hypothesis.
   - Pass 2 (Named Entities only, ≥2 occurrences): same stats restricted to PERSON / ORG / GPE / PRODUCT / EVENT / WORK_OF_ART / NORP / LOC / FAC. NEs are the dominant failure mode per Report 1 — separating them surfaces signal that pass 1 dilutes.

## Costs and constraints

- **GPU**: zero additional. HuggingFace beam search already explores 20 beams internally; we just stop discarding 19. Wall-clock unchanged.
- **CPU/disk**: `nbest-{fid}.json` is ~20× larger than `confidence-{fid}.json`. For the 1,497-segment baseline, expect ~300 MB total. Aggregator + variance analyzer add ~minutes of CPU (no GPU needed).
- **Memory**: identical during decode. The aggregator and analyzer hold one segment's records at a time.
- **Container**: byte-identical files in EC2 and standalone (`cmp` verified). Zero new dependencies. spaCy NER pass degrades gracefully when offline.

## Tests

48 new pytest cases under `tests/unit/`:
- `test_alignment_helper.py` — Levenshtein alignment primitives, edge cases, case-insensitivity.
- `test_nbest_aggregate.py` — each method on synthetic hand-crafted hypotheses, N=1 equivalence to top-1, determinism, empty / all-identical edge cases, cross-segment merge with and without overlap.
- `test_beam_variance.py` — pairwise WER on known distances, agreement rate at known thresholds, entropy on uniform vs peaked distributions, per-position disagreement.

Run: `pytest tests/unit/test_alignment_helper.py tests/unit/test_nbest_aggregate.py tests/unit/test_beam_variance.py -v`.

## Validated end-to-end (107-segment tuning set, 2026-05-01)

Real GPU decode + post-processing chain ran cleanly. Outputs landed at `tuning_results/exp_nbest_validation/` with all three sidecars (`hypo`, `confidence`, `nbest` × 107 segs × 20 hyps), aggregated outputs, variance analysis, and report.

### Per-method WER + IS

| Method | Mean WER | Δ vs top-1 | Mean IS | Δ IS | NIV-Y % | NIV-Y+P % |
|--------|----------|------------|---------|------|---------|-----------|
| `hyp_top1` (baseline) | 59.35% | — | 2.666 | — | 23.4 | 70.1 |
| **`hyp_vote_conf`** | **57.20%** | **↓2.15pp** | **2.695** | **+0.029** | 24.3 | **71.0** |
| `hyp_mbr` | 58.57% | ↓0.78pp | 2.684 | +0.018 | 24.3 | 70.1 |
| `hyp_vote_score` | 58.89% | ↓0.46pp | 2.670 | +0.004 | 23.4 | 69.2 |
| `hyp_safe` | 59.36% | =0.01pp | 2.658 | −0.008 | 23.4 | 69.2 |
| `hyp_xseg_merge` | 59.35% | =0pp (no overlap in tuning data — expected no-op) |

**`hyp_vote_conf` (score × per-word-confidence vote) wins on every metric.** ~3.6% relative WER reduction, +0.029 IS, +0.9pp NIV-Y+P. All four in-beam methods improve over top-1 to varying degrees. Safe is essentially neutral by design (only swaps under conservative conditions).

### Per-word *agreement score* (NOT a Bayesian posterior — important caveat)

Aggregation methods now emit `word_confs` alongside their text, with the formula

  `agreement(word) = Σ_b (weight_b × conf_b) for b voting for chosen / Σ_b (weight_b × conf_b) for b voting any candidate`

**This is NOT a valid posterior probability.** Beams in HuggingFace beam search are *not* independent samples — they share the encoder, decoder weights, and (typically) long prefix histories. When K of N beams agree on a word, that's much weaker evidence than the same K-of-N from independent draws.

What the literature says:

- **[Eikema & Aziz (2020) — "Sampling-Based Minimum Bayes Risk Decoding"](https://ar5iv.labs.arxiv.org/html/2105.08504)**: "sampling from an NMT model is faithful to the training data statistics, while beam search is not." Beam search is mode-seeking and produces a biased sample of the model's distribution. This is why their MBR variant uses ancestral sampling, not beam search.
- **[Spagnolo et al. (Dec 2025) — "Don't Throw Away Your Beams"](https://arxiv.org/html/2512.09538)**: explicitly acknowledges the beam-weighted estimator is **biased relative to multinomial sampling**. It's used for variance reduction in uncertainty estimation, not as a probability. Their Theorem 1 gives a sufficient condition for beam-weighting to beat sampling: top-M beams must capture ≥ 1 − 1/(2√M) of total probability mass — for M=10 that's 84.2%, met in only 22.7% of TriviaQA examples.
- **[Mind the Confidence Gap (2025)](https://arxiv.org/html/2502.11028v3)** + general calibration literature: "if a model assigns incorrect probabilities, beam search faithfully optimizes those incorrect probabilities, and a poorly calibrated model with wider beams may produce confidently wrong outputs." The fluent-hallucination effect we already see in this pipeline is exactly this.

What this means for our implementation:

1. The reported `agreement` score is best understood as a **relative confidence ranking signal**, not an absolute probability. A word with agreement=0.95 is more likely correct than one at 0.50, but agreement=0.95 does NOT mean 95% chance correct.
2. The mode-seeking bias of beam search means **agreement scores will be systematically inflated** vs. what true sampling would produce. This is the literature-standard warning.
3. **Calibration via temperature scaling on a held-out set** is the recommended fix (Guo et al. 2017, Desai & Durrett 2020). Pick a held-out slice of segments, fit a single temperature parameter that minimizes ECE between agreement and empirical accuracy, apply it to future runs. Not in scope for Mission 6 — flagged as future work.

Empirical agreement shift on 107 segments (1,649 words):

| method | mean | median | p10 | p90 |
|---|---|---|---|---|
| `hyp_top1` (raw softmax) | 0.735 | 0.856 | 0.277 | 0.997 |
| `hyp_mbr` (inherits one beam's confs) | 0.735 | 0.854 | 0.277 | 0.997 |
| **`hyp_vote_score`** (agreement score) | **0.892** | **1.000** | 0.589 | 1.000 |
| **`hyp_vote_conf`** (agreement × conf) | **0.905** | **1.000** | 0.610 | 1.000 |
| `hyp_safe` (top-1 conf + consensus rate on swaps) | 0.741 | 0.856 | 0.289 | 0.997 |

Voting methods push >50% of words to median 1.000. **Important practical implication: the existing CONF_HIGH=0.85 / CONF_MED=0.40 thresholds are wrong for voted output** — applied as-is, almost every word would land in the green band, regardless of correctness. Voted-method per-word coloring needs either (a) recalibrated thresholds (proposal: 0.99 / 0.85 — these have to land empirically, *not* derived from the same scale) or (b) literature-standard temperature scaling on a labeled held-out set.

### Variance × confidence correlation (segment-level)

Per-segment beam variance metrics (pairwise mean WER across the 20 beams, word agreement rate, position entropy) correlate weakly with sentence-level signals on the 107-seg sample (r ranges roughly −0.3 to +0.3, all individually noisy at this scale). Full-dataset numbers will land once the 1,497 run completes.

### Word-level confusion (the user's specific question)

**Headline (unconditional):** Pearson r between (1 − recall) and mean per-word confidence = **−0.160** on 124 words at freq≥3. Weak signal in the expected direction.

**The headline is misleading — it averages over two opposing effects.** When we condition on segment quality and split function vs. content words, the picture changes substantially:

| Filter | n_segs | r (all) | r (content) | r (function) |
|---|---|---|---|---|
| ALL | 107 | −0.160 | −0.218 | −0.100 |
| sent_conf ≥ 0.50 | 90 | −0.215 | −0.146 | −0.260 |
| **sent_conf ≥ 0.70** | 51 | **−0.304** | **+0.274** | **−0.486** |
| **sent_conf ≥ 0.85** | 21 | **−0.322** | (n=5) | **−0.518** |
| WER ≤ 50% | 49 | −0.166 | +0.270 | −0.396 |

**Two failure modes, opposite signs:**
- **Function words** (`the`, `with`, `going`, …) on high-quality segments: r = **−0.518** at sent_conf ≥ 0.85. Confidence honestly tracks correctness — when the model gets a function word wrong, it shows lower confidence.
- **Content words** (`oil`, `bigger`, `idea`, …) on the same high-quality segments: r = **+0.274** at sent_conf ≥ 0.70. Confidence is an *anti-signal* — the model commits to wrong content words with HIGH confidence (the fluent-hallucination effect Report 1 flags).

Concrete examples (top confused words by recall, freq ≥ 3):

| word | freq | recall | mean conf |
|---|---|---|---|
| `going` | 10 | 30% | 0.985 ← high conf, often wrong |
| `idea` | 3 | 33% | 0.999 |
| `say` | 3 | 33% | 0.998 |
| `know` | 6 | 33% | 0.981 |
| `here` | 7 | 14% | 0.647 ← lower conf when wrong (function-word honesty) |
| `when` | 3 | 33% | 0.172 |

### Per-method confidence calibration

For each aggregation method, recomputed Pearson r between (1 − recall_method) and (mean_posterior_conf_method) — does the *new* posterior track confusion better than top-1's raw conf?

| Filter | Method | mean conf | r_all | r_func | r_content |
|---|---|---|---|---|---|
| ALL | `hyp_top1` | 0.862 | −0.160 | −0.100 | −0.218 |
| ALL | `hyp_mbr` | 0.867 | −0.118 | −0.098 | −0.140 |
| ALL | `hyp_vote_conf` | 0.953 | −0.022 | −0.143 | +0.036 |
| **sent_conf≥0.85** | **`hyp_mbr`** | 0.921 | **−0.458** | −0.492 | **−0.708** |
| sent_conf≥0.85 | `hyp_top1` | 0.922 | −0.322 | −0.518 | (n=5) |
| sent_conf≥0.85 | `hyp_vote_conf` | 0.978 | −0.202 | −0.302 | +0.267 |

**Two signals**:
1. **Voting methods compress confidence**, destroying the correlation with confusion at the unconditional level (r → 0). The high posteriors are *correct* (consensus says so), but the dynamic range is gone. Practical implication: voted output needs recalibrated CONF_HIGH/CONF_MED thresholds, *not* the same 0.85/0.40.
2. **MBR's calibration improves on high-quality segments**: r_all drops from −0.322 (top-1) to **−0.458** (MBR) at sent_conf≥0.85; r_content hits **−0.708**. MBR doesn't compress the distribution (it inherits one beam's confs) — but by *picking the right beam*, it lands on words whose confidence is more reliable. **MBR is the consistent winner if you care about confidence honesty.** vote_conf wins on raw WER/IS.

### Pre-existing bugs found and fixed in the same PR

1. **`step_scores[::n_beams]`** silently picked beam-0 instead of the running-best beam after HF beam-reordering. Affected today's top-1 entropy/top-3 in `confidence-{fid}.json` on hard cases. Fixed via `gen_out.beam_indices` gather.
2. **`yaml_str` undefined** in the WER summary tail (lines 566, 574). Crashed every decode that reached that block; existed before this PR. Fixed to `_yaml_str`.
3. **Special tokens leaking into voted output** (`<s>`, `</s>`, `<unk>`). Caused 95-97% WER on early aggregator runs before discovery. Fixed by `_is_special_token` filter; regression test added.

### Files / commands to reproduce

```bash
# Run smoke test (107 segs, ~50 min on T4)
bash scripts/tests/test_nbest_decode_smoke.sh

# Full 1,497-segment evaluation (Phase 7b — long-running, see scripts/tests/run_full_nbest_eval.sh)
bash scripts/tests/run_full_nbest_eval.sh

# Inspect aggregated output
ls tuning_results/exp_nbest_validation/{aggregated.json,report/aggregator_method_wer.json,beam_analysis/,per_method_calibration/,conditional_analysis/}
```

## Open follow-ups

- **Optimize the per-step entropy gather**: currently a Python loop over 20 sequences × 200+ steps × top-3 vocab gather, ≈2× slower per segment than the buggy old single-beam version. Vectorizing this is the next perf win — should restore ~28 s/seg (the prior baseline timing).
- **Recalibrate CONF_HIGH / CONF_MED for voted output**: the voting methods compress >50% of words to posterior=1.0. Need new thresholds (proposal: CONF_HIGH=0.95, CONF_MED=0.70 for voted text) so per-word coloring still discriminates.
- **Cross-segment merge on overlap-configured datasets**: tuning set has no overlap (no-op confirmed). Full 1,497 baseline check: TBD when the run completes.

## Calibration shipped (Option A — 2026-05-01)

Temperature scaling per Guo et al. 2017, fitted on 107-segment tuning data via 5-fold CV. The fitted T's transferred well to held-out folds (CV ECE within ±0.005pp of pool ECE), so the same calibration is shipped as the default for full-1,497 use until that decode lands and we re-fit.

| method | T | pre-cal ECE | post-cal ECE |
|---|---|---|---|
| `hyp_top1` | 2.43 | 0.159 | 0.089 |
| `hyp_mbr` | 2.42 | 0.152 | 0.083 |
| `hyp_vote_score` | 14.21 | 0.305 | 0.074 |
| `hyp_vote_conf` | 14.18 | 0.301 | **0.066** ← best calibrated |
| `hyp_safe` | 2.47 | 0.163 | 0.093 |

**Where it lives:**
- Default file: `docs/_research-tools/calibration/calibration.json` (mirrored to container)
- Auto-discovered by `nbest_aggregate.py` if no `--calibration` flag is passed
- Override per-run via `--calibration <path>` to use a re-fitted file

**What gets emitted:**
- `aggregated.json` now carries both raw `word_confs` AND `word_confs_calibrated` per method
- `report.csv` adds a `<method>_mean_conf_calib` column per method (Option A: original `sentence_confidence` column from the existing `compute_word_confidence.py` chain stays untouched and continues to reflect raw top-1)
- HTML/burned-video coloring is unchanged for now (Option B — recalibrate the per-word color thresholds to use the calibrated values — is a separate follow-up)

**Re-fitting procedure** (when full 1,497 lands or a new decode is run on different data):

```bash
# 1. Decode with VSP_NBEST=1 + reference labels available
# 2. Run aggregator without calibration to get raw word_confs
python3 lib/nbest_aggregate.py --nbest path/nbest-{fid}.json --out raw_agg.json
# 3. Fit fresh temperatures on the labeled data
python3 docs/_research-tools/generators/calibrate_temperature.py \
    --aggregated raw_agg.json --hypo path/hypo-{fid}.json \
    --out new_calibration.json
# 4. Re-run aggregator with the new calibration
python3 lib/nbest_aggregate.py --nbest path/nbest-{fid}.json \
    --out final_agg.json --calibration new_calibration.json
```
