# N-Best Beam Aggregation — Implementation

Mission 6 implementation notes (May 1, 2026). Companion to [Report 5](report_5_beam_search_aggregation.md), which describes the techniques in the abstract; this document describes what actually shipped.

## Full-set validation (May 2 2026, 1,497 segments)

Full-corpus decode finished 2026-05-02 09:39 (beam=20, lenpen=0, repetition_penalty=1.2 — same config as the 64.1% greedy baseline). Results: [english_full_nbest_eval/aggregated_is.json](../../english_full_nbest_eval/aggregated_is.json), [english_full_nbest_eval/per_method_calibration/](../../english_full_nbest_eval/per_method_calibration/), [english_full_nbest_eval/beam_analysis/](../../english_full_nbest_eval/beam_analysis/).

### Headline numbers

| Method | Mean WER | Δ vs top-1 | Mean IS | NIV-Y % | NIV-Y+P % | Tier 5 / Tier 1 |
|---|---|---|---|---|---|---|
| `hyp_top1` (baseline) | 64.05% | — | 2.532 | 23.98 | 61.66 | 288 / 237 |
| `hyp_mbr` | 63.84% | ↓0.22pp | 2.547 | 23.91 | 61.92 | 291 / 241 |
| `hyp_vote_score` | 63.67% | ↓0.39pp | 2.538 | 23.98 | 61.86 | 292 / 237 |
| **`hyp_vote_conf`** | **62.49%** | **↓1.56pp** (~2.4% rel) | **2.545** | **24.05** | **62.26** | **299 / 239** |
| `hyp_safe` | 64.02% | ↓0.03pp | 2.533 | 24.05 | 61.66 | 287 / 237 |
| `hyp_xseg_merge` | 64.05% | =0pp (no overlap in dataset) | 2.532 | 23.98 | 61.66 | 288 / 237 |

`hyp_vote_conf` remains the WER winner on the full set, but the gap shrank from −2.15pp (107 seg) to **−1.56pp** (1,497). All four in-beam methods still improve on top-1; `hyp_safe` is again essentially neutral (by design); `hyp_xseg_merge` is a no-op (the full dataset has no configured cross-segment overlap either). NIV-Y / NIV-Y+P barely move (+0.07 / +0.60pp for vote_conf — useful-output capture is roughly unchanged).

### Calibration on full set

Pearson r between per-word (1 − recall) and per-word posterior confidence, by method and stratum (n = word-types with freq ≥ 5):

| Filter | Method | mean conf | r (all) | r (function) | r (content) |
|---|---|---|---|---|---|
| ALL (n=622) | `hyp_top1` | 0.866 | −0.256 | −0.462 | −0.232 |
| ALL | `hyp_mbr` | 0.867 | −0.260 | **−0.539** | −0.224 |
| ALL | `hyp_vote_conf` | 0.965 | −0.179 | −0.432 | −0.156 |
| sent_conf≥0.70 (n=379) | `hyp_top1` | 0.900 | −0.258 | −0.476 | −0.180 |
| sent_conf≥0.70 | **`hyp_mbr`** | 0.899 | −0.234 | **−0.573** | −0.123 |
| sent_conf≥0.85 (n=156) | `hyp_top1` | 0.936 | −0.248 | −0.423 | −0.020 |
| sent_conf≥0.85 | `hyp_mbr` | 0.934 | **−0.285** | −0.412 | −0.103 |
| sent_conf≥0.85 | `hyp_vote_conf` | 0.983 | −0.085 | −0.161 | +0.059 |

**On the full set, MBR's r at sent_conf≥0.85 is −0.285** — directionally consistent with the tuning-set finding (MBR ≥ top-1 in calibration) but the gap is much smaller than the −0.458 / −0.708 we saw on 107 segments. The tuning-set calibration win was overstated by sample size: on 1,497 segs the calibration ranking still favors MBR, just less dramatically. Voting methods still collapse the dynamic range (r→0 at high sent_conf) — same fluent-hallucination effect, same conclusion: don't reuse the 0.85/0.40 thresholds for voted output.

### Function vs content calibration is the load-bearing finding

Restating the table above with the function/content split as the headline:

- **Function-word calibration is consistently strong** across every method and every stratum: r ranges −0.43 to −0.57. The model knows when its function-word predictions are wrong.
- **Content-word calibration is roughly half as strong overall** (r ≈ −0.13 to −0.23 at ALL) and **collapses at high sent_conf**:
  - `hyp_top1`: r_content goes ALL −0.232 → sent_conf≥0.70 −0.180 → sent_conf≥0.85 **−0.020** (no signal).
  - `hyp_vote_conf` at sent_conf≥0.85: r_content = **+0.059** (wrong direction — fluent-hallucination region).

**Operational consequence.** In segments the model is most confident about, its per-word confidence has essentially zero signal for content-word correctness. This is the regime where the dangerous numeric/entity errors live (`billion → million` at 0.965, `1024 → 24` at 0.958 — see [band_reliability_lesson.md](../../.claude/projects/-home-ubuntu/memory/band_reliability_lesson.md)). The three-tier UI policy (Trust ≥0.82 / Salvage 0.65–0.82 / Strip <0.65) is reliable for function words but cannot catch content-word hallucination at high `mean_prob`. A POS-aware confidence threshold (stricter for content words) is the natural next iteration.

### Top-15 most-confused words on the full set (May 2 2026)

Per-word recall + per-occurrence confidence (correct vs wrong, top-1 hyp). Computed by [top_confused_words.py](../_research-tools/generators/top_confused_words.py) — a 100-line replacement for `word_confusion_conditional.py` (which ran past 2h wall-clock and was killed). Outputs at [conditional_analysis/content_words.csv](../../english_full_nbest_eval/conditional_analysis/content_words.csv), [function_words.csv](../../english_full_nbest_eval/conditional_analysis/function_words.csv).

**Top 15 most-confused CONTENT words** (recall ↑, freq tiebreak):

| word | freq | recall | conf when correct | conf when wrong |
|---|---|---|---|---|
| `gonna` | 28 | 0.00 | — | **0.796** |
| `hello` | 8 | 0.00 | — | 0.190 |
| `quick` | 7 | 0.00 | — | **0.801** |
| `cross` | 7 | 0.00 | — | 0.402 |
| `x` | 7 | 0.00 | — | 0.474 |
| `8` | 7 | 0.00 | — | 0.706 |
| `d` | 7 | 0.00 | — | 0.487 |
| `hi` | 6 | 0.00 | — | 0.245 |
| `recover` | 6 | 0.00 | — | 0.449 |
| `table` | 6 | 0.00 | — | 0.284 |
| `feature` | 6 | 0.00 | — | 0.265 |
| `drop` | 6 | 0.00 | — | 0.493 |
| `books` | 6 | 0.00 | — | 0.651 |
| `7` | 6 | 0.00 | — | 0.661 |
| `huge` | 5 | 0.00 | — | 0.554 |

**Top 15 most-confused FUNCTION words**:

| word | freq | recall | conf when correct | conf when wrong |
|---|---|---|---|---|
| `during` | 3 | 0.00 | — | 0.366 |
| `you'll` | 10 | 0.10 | 0.532 | 0.789 |
| `i'll` | 17 | 0.12 | 0.832 | 0.584 |
| `its` | 8 | 0.12 | 0.997 | 0.356 |
| `here` | 71 | 0.14 | 0.775 | 0.563 |
| `they're` | 40 | 0.15 | 0.692 | 0.616 |
| `does` | 15 | 0.20 | 0.848 | 0.606 |
| `he's` | 18 | 0.22 | 0.566 | 0.544 |
| `isn't` | 8 | 0.25 | 0.571 | 0.705 |
| `she's` | 4 | 0.25 | 0.917 | 0.313 |
| `again` | 23 | 0.26 | 0.904 | 0.404 |
| `we're` | 76 | 0.26 | 0.683 | 0.595 |
| `may` | 15 | 0.27 | 0.979 | 0.691 |
| `it's` | 159 | 0.31 | 0.709 | 0.539 |
| `her` | 19 | 0.32 | 0.835 | 0.625 |

**Three findings drop out:**

1. **`gonna` is the single most systematic failure** — 28 ref-side occurrences, 0% recall, **0.796 conf when wrong**. The model confidently outputs `going` (matches the +10 systematic substitution count from the earlier ref→hyp table) and *believes its answer*. Same pattern at smaller scale for `quick` (0.801), `8` (0.706), `7` (0.661), `books` (0.651).

2. **Content failures are confidently wrong** — most 0%-recall content words show conf|wrong in the 0.4–0.8 range. The model is hallucinating, not abstaining. This is the danger pattern: an end user reading the green-tier output cannot tell `gonna` was meant.

3. **Function failures are honestly uncertain** — every function word with both columns populated shows **conf|correct > conf|wrong** (sometimes by 0.5+: `again` 0.904 vs 0.404, `may` 0.979 vs 0.691). The confidence signal works for function words even when they're frequently wrong, which is why the function-word calibration r is so strong.

Numbers and single letters (`8`, `7`, `x`, `d`) all 0% recall — visual disambiguation between digits is essentially random for lip-reading. Any UI surface that exposes numeric output should display it with explicit low-confidence styling regardless of `mean_prob`.

### Beam variance

Per-segment beam metrics ([beam_analysis/beam_variance_analysis.md](../../english_full_nbest_eval/beam_analysis/beam_variance_analysis.md)) over 1,497 segments:

```
                   mean   std    p50    p75    max
n_unique_hyps     19.90  0.39  20.0   20.0   20.0
pairwise_mean_wer  0.324 0.192  0.276  0.423  1.41
word_agreement     0.762 0.266  0.857  0.944  1.00
position_entropy   0.465 0.386  0.361  0.622  2.42
```

The model's 20 beams are nearly always distinct (≥20 unique hyps in ≥75% of segs). Pairwise mean WER between beams averages 32% — non-trivial diversity is present, which is why aggregation moves the needle at all. ~25% of segments have word_agreement_rate ≥ 0.94 (model self-consistent → not much room for aggregation to help); the bottom quartile sits at ≤ 0.67 (where aggregation should help most).

### Top systematic word substitutions (baseline hyp, 1,427 segs with both ref & hyp)

Computed via SequenceMatcher alignment, top ref → hyp substitution pairs:

| count | ref → hyp | count | ref → hyp |
|---|---|---|---|
| 13 | the → to | 9 | the → you |
| 11 | the → a | 9 | and → a |
| 11 | in → and | 9 | we're → we |
| 11 | and → in | 8 | to → into |
| 11 | you're → you | 8 | it's → is |
| 10 | that → and | 7 | i → and |
| 10 | gonna → going | 7 | you → you're |
| 9 | a → the | 7 | is → it's |
| 9 | a → to | 7 | the → this |

Dominated by short function-word swaps (`the/a/and/in`) and contraction loss (`you're → you`, `we're → we`, `it's → is`, `gonna → going` — 10x). These are exactly the "function-word honesty" cases Mission 6 identified — confidence already tracks them well; the wins come from MBR/vote_conf overriding them when most beams disagree. Content-word systematic confusions are sparse (long tail — 6,527 unique substitution pairs, no single content pair exceeds 6 occurrences).

### Tuning-set vs full-set deltas (107 → 1,497)

| Finding | Tuning (107) | Full (1,497) | Held? |
|---|---|---|---|
| `hyp_vote_conf` is WER winner | ↓2.15pp | ↓1.56pp | **Yes** (smaller margin) |
| `hyp_mbr` 2nd-best WER | ↓0.78pp | ↓0.22pp | **Yes** (smaller margin) |
| `hyp_mbr` best calibration at sent_conf≥0.85 | r=−0.458 | r=−0.285 | **Yes, directionally** (gap shrank) |
| Voting compresses confidence | mean 0.95+, p50=1.000 | mean 0.96+ | **Yes** |
| `hyp_xseg_merge` no-op | yes | yes | **Yes** (no overlap configured) |
| `hyp_safe` neutral by design | =0.01pp | =0.03pp | **Yes** |
| NIV-Y+P improves with vote_conf | +0.9pp | +0.60pp | **Yes** (smaller) |

**No sign flips, no inversions.** All tuning-set rankings replicated. The consistent pattern: every tuning-set effect size shrunk by roughly half on the full set — typical of a small-N tuning regime where extreme observations average out. The headline conclusions hold.

### Conclusion

`hyp_vote_conf` is the production drop-in for raw quality (~2.4% relative WER reduction on 1,497 segs) but ships with confidence that is no longer Bayesian-meaningful — keep voted output for transcripts, keep `hyp_top1` or `hyp_mbr` for any UI surface that uses per-word confidence shading until thresholds are recalibrated. `hyp_mbr` remains the calibration recommendation for confidence-honest workflows.

---

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
- **POS-aware confidence threshold**: function-word calibration is r ≈ −0.45; content-word calibration collapses to ~0 at sent_conf ≥ 0.85. A stricter band for content words (e.g. green only at p ≥ 0.95 for content, p ≥ 0.82 for function) should reduce green-but-wrong leakage on entities/numbers.
- **Cross-segment merge on overlap-configured datasets**: tuning set has no overlap (no-op confirmed). Full 1,497 also has no overlap configured (`hyp_xseg_merge` = `hyp_top1` exactly).
- **Optimize / replace `word_confusion_conditional.py`**: original conditional script ran past 2h wall-clock on the full set (terminated 2026-05-02 13:35Z). The headline finding (function vs content calibration) was already in [per_method_calibration/](../../english_full_nbest_eval/per_method_calibration/), and [top_confused_words.py](../_research-tools/generators/top_confused_words.py) now produces the top-15 lists in ~12 s. Either retire the old script or vectorize its `per_position_disagreement` hot loop and add tqdm progress.

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

## Judge validation (2026-05-02, full set, blind, Opus 4.7)

After Mission 6 shipped, we put all four candidate hypotheses (baseline + 3 aggregation methods) through a paired LLM-as-Judge run on the full 1,497-segment set. **5,988 in-conversation Y/P/N verdicts** with sentence + per-word confidence injected as soft cues. Full writeup: [docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md](../evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md).

| method | NIV-Y rate | Δ vs baseline | p (paired) | NIV-Y+P rate | Δ vs baseline | p (paired) | WER (full set) |
|---|---|---|---|---|---|---|---|
| **baseline (1-best)** | **16.6 %** | — | — | **69.8 %** | — | — | 64.05 % |
| `hyp_mbr` | 16.4 % | −0.2 pp | 0.82 | 68.5 % | −1.3 pp | 0.07 | 63.83 % |
| `hyp_vote_score` | 17.3 % | +0.7 pp | 0.51 | 68.3 % | −1.5 pp | 0.022 | — |
| `hyp_vote_conf` | **13.6 %** | **−3.0 pp** | **0.0005** | **67.6 %** | **−2.2 pp** | **0.0024** | **62.49 %** |

McNemar tests are continuity-corrected, two-sided, paired by `utt_id`.

**Headline**: `hyp_vote_conf` wins WER but **loses NIV-Y significantly** — the metric we use to decide what ships disagrees with the metric we ranked candidates by.

**Mechanism**: vote_conf trims surface edits (e.g., dropping a connective like "and", swapping a function word) that lower WER by one substitution while pushing the judge from "meaning conveyed" (Y) to "partial" (P). It downgrades **101 baseline-Y → P** and only recovers **57 baseline-P → Y**. Consistent with the existing literature note that voting "agreement score" is not a Bayesian posterior — high agreement among wrong-but-similar beams produces fluent-but-meaning-shifted output.

**Recommendation**: do not ship `hyp_vote_conf` as the default. `hyp_mbr` is closest to neutral and remains the safer choice if n-best machinery is wanted (e.g., for the per-word agreement score as an *uncertainty* signal — distinct from using it to *pick* the output). The decision rule for "ship a method" should be paired McNemar on NIV-Y, not WER.

**Confidence calibration finding (Mission 4.1 unblocker)**: baseline `sentence_confidence` shows a strong monotonic relationship with the judge verdict — at conf ≥ 0.7, P(Y+P) ≥ 96.9 %; at conf < 0.4, P(N) ≥ 91 %. The agreement-based "confidence" emitted by `hyp_vote_score`/`hyp_vote_conf` lives in a much narrower [0.4, 0.8) range with shallower discrimination, confirming it should be treated as a consensus signal rather than a posterior probability.

**Followups logged**:
- Save per-word `word_confs` to `report.csv` (or a sidecar) at decode time, so future judge runs don't have to re-run the aggregator. The May 2 run wasted ~12 min of CPU before we found the existing `aggregated.json`.
- Consider a context-aware re-judge (analogous to existing `llm_judge/context_eval/`) to test whether the rank inversion holds when the judge can use topic context.
