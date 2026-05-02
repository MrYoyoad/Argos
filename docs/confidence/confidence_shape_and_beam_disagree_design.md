# Confidence Shape & Beam Disagreement — Design for Catching Confident Hallucinations

**Purpose.** Design doc for two confidence signals that the current per-word band system does not use: **shape of confidence through a sentence** and **beam disagreement vs top-1 confidence**. Both are aimed at the same failure mode — *confidently wrong content words* — that the n-best full-set evaluation showed is unreachable by raising the per-word confidence threshold alone.

**Status.** Proposal, not shipped. All required data already exists in [english_full_nbest_eval/](../../english_full_nbest_eval/). Implementation effort estimated at ~1 day (not counting deep tuning).

**Companion docs.** Builds directly on:
- [confidence_followups.md](confidence_followups.md) — earlier brainstorm; sections #2 (trajectory) and #4 (use all 20 beams) are formalized here into runnable analyses with predicted outputs.
- [band_reliability_by_segment_quality.csv](band_reliability_by_segment_quality.csv) — the per-band stratified reliability table this work would extend.
- [threshold_design.md](threshold_design.md) — the original three-tier-band design that this proposal would augment, not replace.
- [docs/beam-search/n_best_implementation.md](../beam-search/n_best_implementation.md) — full-set finding that motivates this work (content-word calibration r = −0.020 at sent_conf ≥ 0.85).

---

## 1. The problem in one paragraph

Per-word top-1 confidence is **honest for function words and dishonest for content words**. The full-set Pearson r between (1−recall) and per-word confidence is roughly −0.46 for function words (consistent across every sent_conf stratum) but only −0.23 for content words overall, collapsing to **−0.02 at sent_conf ≥ 0.85** — essentially zero signal. The dangerous numeric/entity errors (`billion → million` at conf 0.965, `1024 → 24` at 0.958, `gonna → going` at 0.796) live exactly in this regime. Raising the per-word green threshold does not catch them because the underlying signal is flat in that range. We need a *different* signal.

---

## 2. Two signals we haven't used yet

### 2a. Confidence shape through a sentence

**Why it might work.** Today the band system uses two scalars: per-word confidence and segment mean confidence. It does not use the *trajectory* — how confidence rises, dips, plateaus, or collapses across the sentence. A small set of recurring patterns is plausible:

- **Smooth high plateau** — model confident throughout. Probably reliable.
- **U-shape / mid-dip** — high at start and end, dips on a content word in the middle. The dip likely flags a lip-reading failure that the LLM smoothed over with context. Even if the dip is at conf 0.7 (still "yellow"-passing), it is anomalously low for *this* sentence.
- **Late collapse** — confident through the start, drops over the second half. Model lost the thread; later content is unreliable.
- **Early collapse** — drops fast and stays low. Sentence-wide disaster.
- **High plateau with a single high spike** — uniform-high punctuated by a 0.99-confident content word. Possibly an LLM-driven fluent hallucination committed against weak visual evidence.

The scalar segment mean blurs all of these into one number. A *shape signature* would not.

**What we'd compute per segment.** A small fixed-length feature vector:

- `conf_mean`, `conf_std`, `conf_min`, `conf_max`, `conf_range`
- Position of the minimum within the sentence, normalized 0–1 (early/mid/late)
- Slope of a linear fit: `conf ~ position`
- Number of confidence "dips" (positions where conf < segment mean − 1σ)
- Maximum local drop: largest `conf[i−1] − conf[i]` over adjacent positions
- Position-relative z-score for each word: `(conf[i] − segment_mean) / segment_std`

The per-word z-score is the new feature most likely to be useful: a word with absolute conf 0.85 inside a sentence whose mean is 0.95 has z = −2.0 — flag-worthy even though 0.85 looks "green" by the absolute scale.

**What we'd cluster.** Run k-means or HDBSCAN over the per-segment feature vector for k ∈ {3..6}. Inspect cluster centroids and per-cluster WER / IS / NIV-Y rates. A useful clustering will produce 4–6 visibly distinct shape archetypes with materially different reliability profiles.

### 2b. Beam-disagreement × top-1 confidence cross

**Why it might work.** With 20 beams we can ask not just "how confident is the model in *this* word" but also "how much did the 20 beams *agree* at this position." These two signals capture different things:

- **Top-1 conf** = softmax probability of the chosen token under the chosen prefix. Reflects how peaked this position is *given the path the model already committed to*.
- **Beam agreement** = fraction of the top-20 beams that emitted the same word at this position. Reflects how robust the choice is *across alternative paths*.

A 2×2 cross gives us four cells:

| top-1 conf | beam agreement | What it likely means |
|---|---|---|
| HIGH | HIGH | Real signal — beams converged + model committed. Trust. |
| HIGH | **LOW** | **Confident hallucination** — model committed but other beams explored very different alternatives at this position. The `gonna → going` cell. |
| LOW | HIGH | Rare — usually an artifact of low-overall-confidence segments where everything is low. |
| LOW | LOW | Honest uncertainty. |

The high-conf-low-agreement cell is where the dangerous content errors should concentrate. We already compute `mean_beam_disagree` in [analyze_beam_variance.py](../_research-tools/generators/analyze_beam_variance.py), but we haven't yet correlated it with correctness *conditional on* high top-1 confidence.

**What we'd compute.** For every word in the top-1 hypothesis:
- top-1 conf (from `confidence-172610.json`)
- beam-agreement = fraction of 20 beams that contain this word at this aligned position (from `nbest-172610.json`)
- aligned correctness vs ref (from `hypo-172610.json`)
- POS tag (function vs content)

Then a 2D reliability table: P(correct) binned by (top1_conf, beam_agreement) cells, separately for function and content words.

The expected outcome is a sharp diagonal for function words (high top1 + high agreement → reliable, anything else → less reliable) but a *flat top-1 axis* for content words rescued only by the agreement axis. If the table looks like that, beam-agreement is the missing signal.

---

## 3. Concrete analysis pipeline

All inputs are already on disk from the May 2 full-set decode:

- `english_full_nbest_eval/decode_output/confidence-172610.json` — per-token probs/entropy for top-1 (14.5 MB)
- `english_full_nbest_eval/decode_output/nbest-172610.json` — all 20 beam outputs with text + scores (387 MB)
- `english_full_nbest_eval/decode_output/hypo-172610.json` — top-1 hyp + ref pairs (455 KB)
- `english_full_nbest_eval/report/report.csv` — per-segment WER / IS / NIV labels

### 3.1 Per-segment shape features (~1 hour to write)

**Script.** `docs/_research-tools/generators/segment_shape_features.py`

**Inputs.** `confidence-*.json`, `report.csv`.

**Per-segment computation.** Iterate top-1 word-level confidences (use `_word_confs_for_utt` from `analyze_beam_variance.py`). Compute the 11 features listed in §2a. Emit one CSV row per segment.

**Outputs.**
- `english_full_nbest_eval/shape_analysis/segment_shape_features.csv` — wide-form CSV.
- `english_full_nbest_eval/shape_analysis/per_word_z_scores.csv` — long-form: one row per word with `utt_id`, `position`, `word`, `conf`, `seg_mean`, `seg_std`, `z`, `is_function_word`, `correct`.

### 3.2 Shape clustering + reliability table (~1 hour)

**Script.** `docs/_research-tools/generators/cluster_shape_archetypes.py`

**Inputs.** `segment_shape_features.csv`, `report/report.csv`.

**Processing.** Standardize features (subtract median, divide by IQR per feature). Run k-means for k ∈ {3, 4, 5, 6}. For each k, report inertia + silhouette + per-cluster mean WER / IS / NIV-Y rate. Pick the k whose centroids are most interpretable (probably 4–5).

**Outputs.**
- `english_full_nbest_eval/shape_analysis/shape_clusters.csv` — per-segment cluster assignment.
- `english_full_nbest_eval/shape_analysis/shape_cluster_centroids.csv` — feature centroids per cluster.
- `english_full_nbest_eval/shape_analysis/shape_cluster_reliability.md` — narrative table: cluster → archetype name → mean WER / IS / NIV-Y / N segments / 5 example utt_ids.
- `english_full_nbest_eval/shape_analysis/cluster_trajectory_plots.png` — overlay of normalized confidence trajectories per cluster, faceted.

### 3.3 Per-word z-score reliability (~30 min)

**Script.** Extension to `cluster_shape_archetypes.py`.

**Processing.** Bin words by `z` (the per-word z-score from §3.1). For each bin, compute P(correct), separately for function and content words. Compare against the same bins for absolute confidence.

**Output.**
- `english_full_nbest_eval/shape_analysis/z_score_reliability.csv` — bin → P(correct | content), P(correct | function), N.

**Headline question this answers.** Does z-score (relative position) predict correctness *better than* absolute conf for content words at sent_conf ≥ 0.85?

### 3.4 Beam-agreement × top-1 conf cross (~1 hour)

**Script.** `docs/_research-tools/generators/beam_agreement_cross.py`

**Inputs.** `nbest-*.json`, `confidence-*.json`, `hypo-*.json`.

**Processing.** For each segment:
1. Get top-1 hyp + per-word confs.
2. Get the 20 beam hyps. Align each beam to top-1 (use `align_word_lists`). Compute per-position beam-agreement = fraction of 20 beams whose aligned position emits the same word as top-1.
3. Align top-1 to ref. Mark each top-1 word correct/wrong.
4. Tag each word with its POS class (function vs content via the existing `FUNCTION_WORDS` set).

Emit per-word rows: `utt_id, position, word, top1_conf, beam_agreement, is_correct, is_function_word`.

**Then bin.** Build a 2D table: rows = top1_conf bins (0.4, 0.6, 0.8, 0.9, 0.95, 0.99), cols = agreement bins (0.5, 0.7, 0.85, 0.95, 1.0). Cell value = P(correct), cell N = number of words. Build separately for function and content.

**Outputs.**
- `english_full_nbest_eval/shape_analysis/beam_agreement_per_word.csv` — long-form.
- `english_full_nbest_eval/shape_analysis/agreement_x_conf_table.md` — the 2D tables (function + content) with cell P(correct) and N.
- `english_full_nbest_eval/shape_analysis/agreement_x_conf_heatmap.png` — visualization.

**Pass criterion for shipping.** P(correct | content & top1≥0.95 & agreement≥0.95) is materially higher than P(correct | content & top1≥0.95 & agreement<0.5) — by at least 15 percentage points, with N ≥ 30 in each cell.

---

## 4. Hypotheses to test (predicted ranges)

| Hypothesis | Predicted result | Why we expect it |
|---|---|---|
| Per-word z < −1.5 predicts content-word errors better than abs conf < 0.7 | r(z, correct) ≈ +0.30 vs r(abs, correct) ≈ +0.15 for content at sent_conf ≥ 0.85 | Z is normalized away from segment-level fluency, isolating local visual failures |
| 4–5 distinct shape archetypes emerge with WER spread of >10pp | k=4 best by silhouette; cluster WER spans 30%–80% | Confidence trajectories are a low-dimensional manifold; failure modes cluster |
| `gonna`-class (high top1, low agreement) cell exists for content | P(correct) ≈ 0.5 in cell vs ≈ 0.85 in (high, high) | Beams explored alternatives, top-1 committed; this is the literal definition of `gonna→going` |
| Function words show no top1-vs-agreement asymmetry | Both axes correlate similarly with correctness | Function-word calibration already works; little marginal signal from agreement |
| The agreement axis adds the most lift in the high-top1 regime | Reliability lift from agreement biggest at top1 ≥ 0.9, smaller below | Agreement is mostly informative when conf is already saying "I'm sure" |

If all five replicate, we have the basis for a POS+shape+agreement-aware band policy.

---

## 5. Implementation sketch

```
docs/_research-tools/generators/
├── segment_shape_features.py        # §3.1, ~150 lines
├── cluster_shape_archetypes.py      # §3.2 + §3.3, ~250 lines
└── beam_agreement_cross.py          # §3.4, ~200 lines
```

All three follow the same shape as existing analysis scripts in that folder (argparse, numpy/pandas, write CSV + markdown). Reuse `_alignment.align_word_lists` for §3.4 and `analyze_beam_variance._word_confs_for_utt` for §3.1.

**Order of operations.**

1. Run §3.1 first (feeds §3.2 and §3.3).
2. Run §3.4 in parallel (independent of shape features).
3. Run §3.2 + §3.3.
4. Hand-inspect cluster archetypes; rename clusters meaningfully.
5. Decide whether to write the agreement-aware band policy in §6.

**Compute budget.** The full-set inputs are ~400 MB total; everything fits in RAM. End-to-end runtime estimate: §3.1 ≈ 2 min, §3.2 ≈ 1 min, §3.3 ≈ 30 s, §3.4 ≈ 5 min (does the most alignment work). Total under 10 min wall-clock.

**Negative-result handling.** If §3.4 fails its pass criterion (no big cell-difference), shape clustering may still be useful as a segment-level filter (§3.3). If both fail, we publish a "negative result" note to confidence_followups.md and move on — sunk cost ≈ 1 day.

---

## 6. UI integration sketch (only relevant if §3.4 passes)

The current per-word band rule is a single threshold on `top1_conf` gated by segment-level `mean_prob`. A successful experiment would extend this to a **3-input rule** for content words:

```python
def render_band(word, top1_conf, beam_agreement, is_function_word, segment_mean_prob):
    if segment_mean_prob < 0.65:
        return "strip"  # unchanged

    if is_function_word:
        # Existing thresholds work — confidence is honest
        if top1_conf >= 0.82: return "green"
        if top1_conf >= 0.65: return "yellow"
        return "red"

    # Content word — require agreement to back up confidence
    if top1_conf >= 0.95 and beam_agreement >= 0.85: return "green"
    if top1_conf >= 0.82 or beam_agreement >= 0.85: return "yellow"
    return "red"
```

Numbers (digit tokens, number-words, units) get a parallel hard rule independent of all confidence signals: always render with explicit "visually unreliable" styling, because lip-reading cannot disambiguate digits.

The actual thresholds would be fitted from the §3.4 reliability table once the data is in. The values above are placeholders for the design.

---

## 7. What could go wrong

- **Beam-agreement might not actually carry independent information from top-1 conf.** If they correlate at r ≈ 0.95, the cross is a single signal in disguise. (Pre-test: just measure r between the two columns first; if too high, the proposal collapses.)
- **Shape clusters might be dominated by sentence length.** Easy mitigation: include length as a covariate and standardize per-length-bucket if needed.
- **Per-word z-score is undefined for one-word segments.** Skip them in §3.3 — they're rare and shouldn't drive policy anyway.
- **Aligning all 20 beams to top-1 is the most expensive step.** If it's slow, cache aligned positions per (utt, beam) pair — already amortizable across all downstream cuts.
- **Threshold drift.** Any thresholds we fit are specific to this LLM (Llama-2-7b) and this beam config (beam=20, lenpen=0). A future fine-tuning experiment changes the calibration curves and forces a re-fit. Document this as a maintenance burden.

---

## 8. Decision

Run §3.1, §3.2, §3.4 first. Spend a half-day. If §3.4's pass criterion is met, proceed with §6 UI integration as the main payoff. If not, publish §3.2's clusters (segment-level filter) and stop.

Open questions for the user:

1. Is half a day of analyst time the right investment, or should we wait until a stronger LLM (Llama 3.1 8B+) is online — at which point the underlying calibration curves change and any thresholds we fit now expire?
2. Do we have any held-out unseen-content data to validate the thresholds, or do we need to split the 1,497 set into fit/test halves?
3. Does the team want shape clusters surfaced in the client report (as an additional "segment quality archetype" tag) or kept as an internal diagnostic only?
