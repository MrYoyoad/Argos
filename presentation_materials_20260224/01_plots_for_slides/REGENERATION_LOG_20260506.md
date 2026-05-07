# MBR-IS Plot Regeneration Log — 2026-05-06

**Driver:** Production default switched from `hyp_top1` to `hyp_mbr` (Mission 6
shipped May 1 2026; entry #30 in agreement-aware bands lesson). The March 2026
presentation deck plots were built from top-1 IS — every IS-dependent figure
is regenerated here against MBR-aggregated data so the academic deck reflects
current production numbers.

## Authoritative data sources

| File | Used for |
|---|---|
| `/home/ubuntu/english_full_nbest_eval/aggregated_is.json` | per-segment IS / WER / tier under each method (hyp_top1, hyp_mbr, hyp_vote_score, hyp_vote_conf, hyp_safe, hyp_xseg_merge) |
| `/home/ubuntu/english_full_nbest_eval/report_v2/report.csv` | reference + per-method hypothesis text (needed to recompute IS components) |
| `/home/ubuntu/english_full_nbest_eval/safety_analysis/per_segment_safety.csv` | seg_mean_conf binning for stratified band reliability |
| `/home/ubuntu/docs/confidence/band_reliability_by_niv.md` | NIV-stratified P(correct \| band) numbers |
| `/home/ubuntu/docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md` | v3 judge Y / Y+P per method, McNemar p-values |

Cached intermediate (created by the regen script):
- `/home/ubuntu/english_full_nbest_eval/is_components_per_method.csv` — per-utt
  semantic / phonetic / WER / WWER / NEA / length under both `top1` and `mbr`
  (re-used by the radar plots; takes ~2 min to rebuild from scratch via
  sentence-transformers, so it is cached on disk).

## Driver script

`/home/ubuntu/docs/_research-tools/generators/regenerate_after_amosi_plots.py`

```
python3 docs/_research-tools/generators/regenerate_after_amosi_plots.py
# or, to skip the encoder-dependent radar plots:
python3 docs/_research-tools/generators/regenerate_after_amosi_plots.py --no-radar
```

The script writes a structured JSON log to `_regen_log.json` next to the PNGs
(parsed by the caller / rebuild scripts).

## Plots regenerated (overwrites of March PNGs, backed up to `_archive_march2026/`)

### 1. `P1_quality_tiers.png` — IS tier distribution

Source: `aggregated_is.json["summary"]["hyp_mbr"]`.

| Tier | Count (MBR) | % | Δ vs March (top-1) |
|---|---:|---:|---|
| 5 — Excellent (4.0-5.0) | **291** | 19.4% | +15 (was 276 / 18.4%) |
| 4 — Good (3.0-3.99) | **324** | 21.6% | +3 (was 321 / 21.4%) |
| 3 — Fair (2.0-2.99) | **312** | 20.8% | -13 (was 325 / 21.7%) |
| 2 — Poor (1.0-1.99) | **329** | 22.0% | -7 (was 336 / 22.4%) |
| 1 — Failed (0.0-0.99) | **241** | 16.1% | +2 (was 239 / 16.0%) |

Mean IS: 2.547 (was 2.532). NIV-Y+P: 61.9% (was 61.6%). NIV-Y: 23.9% (was 23.1%).
Net: MBR pulls density into the top tier and out of Fair (one tier up); rest is
flat. Headline narrative ("9 out of 10 need verification") is unchanged.

### 2. `P3b_is_trajectory.png` — IS by sorted segment rank

Replaces the March projected-improvement roadmap with an actual sorted-rank
trajectory comparing MBR vs top-1. Both lines are visible; MBR is consistently
slightly higher in the mid-range (2.0–4.0 IS band) where aggregation rescues
borderline segments.

Numbers shown on plot:
- 358 segments NIV-Y under MBR (vs 359 under top-1; tied)
- 927 segments NIV-Y+P under MBR (vs 923 under top-1; +4)

### 3. `P6_is_radar.png` — IS-component radar (useful vs failed)

Component values recomputed for `hyp_mbr` text via sentence-transformers
+ phonetic / NEA / WER pipeline.

| Signal | Useful (Y+P, n=927) | Non-useful (NIV-N, n=570) |
|---|---:|---:|
| Semantic | **0.62** (was 0.62) | 0.14 (was 0.14) |
| Phonetic | **0.73** (was 0.73) | 0.27 (was 0.27) |
| Inv WER | **0.59** (was 0.59) | 0.08 (was 0.00) |
| Inv WWER | **0.61** (was 0.58) | 0.10 (was 0.06) |
| NEA F1 | **0.60** (was 0.59) | 0.06 (was 0.06) |
| Length | **0.93** (was 0.97) | 0.74 (was 0.85) |

Captured-mean = 0.68 (was 0.68); failed-mean = 0.23 (was 0.23). MBR is more
generous on Inv WER inside NIV-N (0.08 vs 0.00 for top-1) — aggregation
recovers some words rather than producing empties. Layout updated to put the
green/red value pair inline under each category label so the labels no longer
collide.

### 4. `P6b_radar_dual.png` — LRS3 vs YouTube (MBR overlay)

LRS3 profile unchanged (separate decode run, `/tmp/lrs3_decode/`). YouTube
profile recomputed under MBR (mean across all 1,497 segments):

| Signal | LRS3 | YouTube top-1 (March) | YouTube MBR (now) |
|---|---:|---:|---:|
| Semantic | 0.779 | 0.58 | **0.44** |
| Phonetic | 0.794 | 0.52 | **0.56** |
| Inv WER | 0.689 | 0.36 | **0.40** |
| Inv WWER | 0.662 | 0.40 | **0.42** |
| NEA F1 | 0.683 | 0.39 | **0.39** |
| Length | 0.971 | 0.72 | **0.86** |

Note: the March YouTube row was a hand-curated approximation, not directly
computed; the MBR row is mean-over-all-segments under MBR. Both means come
from the same `is_components_per_method.csv`.

### 5. `P7_is_wer_scatter.png` — WER vs IS scatter, NIV gap regions

Source: per-segment `aggregated_is.json["per_segment"]["hyp_mbr"]`.

| Gap region | March (top-1) | MBR | Δ |
|---|---:|---:|---:|
| Y gap (IS≥3.80, WER>34%) | 50 | **52** | +2 |
| Y+P gap (IS≥2.00, WER>40%, IS<3.80) | 408 | **437** | +29 |

The gap regions widen modestly under MBR — aggregation moves segments into
the "useful but high-WER" band, exactly where the model wins on judge metrics
without winning on WER. Tier-coloured scatter regenerated from the new MBR
per-segment table.

## New plots created

### 6. `P_method_comparison.png` (NEW)

Violin + box per method showing IS distribution overlap. Mean IS: top-1 2.532,
MBR 2.547, vote_score 2.538, vote_conf 2.545. Subtitle line lists each method's
WER and NIV-Y+P. Built for `slide_mbr_decision` and
`slide_nbest_v3_judge_paired_tests`.

### 7. `P_band_reliability_stratified.png` (NEW)

P(correct | green) by segment mean_prob bin, with coverage on a second axis.
Bars: 18.2 / 21.8 / 41.3 / 69.6 / 83.8 / 92.8% across bins
<0.40 / 0.40-0.55 / 0.55-0.65 / 0.65-0.75 / 0.75-0.85 / ≥0.85. Reference
threshold lines at T_safe (85%), T_salvage (75%), Strip-coloring boundary
(50%). Coverage from `per_segment_safety.csv` (n=1,427 segments). Numbers
come from May 2026 stratification table in MEMORY.md / docs/confidence/.

### 8. `P_band_reliability_by_niv.png` (NEW)

3 NIV tiers × 3 bands grouped bar:
- NIV-Y: green 94.1%, yellow 65.2%, red 38.7%
- NIV-P: green 79.7%, yellow 41.2%, red 20.3%
- NIV-N: green 37.1%, yellow 16.9%, red 6.9%

Source: `docs/confidence/band_reliability_by_niv.md` (May 2 2026 entry).
Subtitle highlights the 62.5pp green-to-red spread inside useful content.

### 9. `P_v3_judge_paired.png` (NEW)

Y+P% per method with paired McNemar p-values:
- Top-1 baseline: 68.4%
- MBR: 71.1% (+40 wins, p=0.0002)
- Vote-score: 69.3% (+13, n.s.)
- Vote-conf: 70.5% (+31 wins, p=0.0026)

Y% (hatched bars beside): 13.1 / 13.9 / 14.0 / 12.5%. Subtitle: "MBR and
Vote-conf both significantly beat baseline on Y+P. MBR is shipped as
production default."

### 10. `P_failure_taxonomy.png` (NEW)

5-category bars with counts/percentages re-scaled to MBR NIV-N pool (570
segments under MBR vs 575 under top-1):
- Wrong Topic: 253 (44.4%)
- Hallucination: 107 (18.8%)
- Signal Loss: 79 (13.9%)
- Right Topic, Wrong Details: 79 (13.8%)
- Accumulated Errors: 52 (9.1%)

Categorical proportions are inherited from the March 574-segment top-1
taxonomy (`intelligibility_summary.json`); only the totals re-scale because
MBR's NIV-N count differs slightly. Footer note documents this.

### 11. `P_llm_salvage.png` (NEW)

Two-panel plot:
- Left: donut showing useful (61.9%, 927) / NIV-N salvageable (9.9%, 148) /
  non-recoverable (28.2%, 422). Effective capture rate = **71.8%** under MBR.
- Right: recovery type counts among the 460 metric-failed (IS<3.0) salvageable
  segments — Hidden Gems 29, Semantic Pres. 78, Phonetic Bridge 150,
  Entity-Preserved 85, Structure Match 309, WER Over-Punish. 173 (overlap
  allowed; counts add to >n_salvage).

The salvage heuristic is a deterministic 6-signal decision rule that
approximates the March `llm_context_prob` ≥ 0.5 cutoff using the IS components
already on hand (no LLM call needed, same design philosophy as the March
heuristic). Inside NIV-N specifically, 148 segments are salvageable — close to
the March top-1 number of 165, the small drop reflects MBR moving some
borderline segments out of NIV-N into NIV-P (where they no longer need
salvaging).

## IMG dictionary updates

Added to `/home/ubuntu/docs/_research-tools/generators/presentation/config.py`:
- `P_method_comparison`
- `P_band_reliability_stratified`
- `P_band_reliability_by_niv`
- `P_v3_judge_paired`
- `P_failure_taxonomy`
- `P_llm_salvage`

## Backups

March PNGs preserved at:
`/home/ubuntu/presentation_materials_20260224/01_plots_for_slides/_archive_march2026/`

Files backed up: P1_quality_tiers, P3b_is_trajectory, P6_is_radar,
P6b_radar_dual, P7_is_wer_scatter, P7_signal_by_tier, P8_signal_by_judge.

## Style compliance

All new plots follow `docs/_research-tools/generators/STYLE_GUIDE.md`:
- Dark navy `#0D1B2A` background for presentation-themed plots (radars,
  scatter, distribution); white background for analytical bars (failure
  taxonomy, salvage donut).
- Colour palette matched to existing deck (TEAL, CORAL, GREEN, GOLD, AMBER,
  BLUE, PURPLE).
- Calibri / matplotlib default; bold titles; italic subtitle footers; 200 DPI.

## Known limitations / follow-ups

- The salvage recovery-type counts use a heuristic derived from the IS
  components rather than the original `llm_context_prob` field (which is not
  recomputed for MBR). The March-vs-MBR comparison is therefore directional,
  not exact. If we need exact parity, re-run
  `generate_intelligibility_scores.py --hyp aggregated.json[hyp_mbr]` to
  recompute `llm_context_prob` per the original 15-rule decision tree.
- `P_band_reliability_stratified.png` plots the headline numbers from MEMORY
  (May 2026 sidecar). Coverage counts on the second axis come from
  `per_segment_safety.csv` (which has 1,427 segments not 1,497 — 70 segments
  drop out due to missing word_confidence rows). The P(correct|green) values
  themselves are not recomputed here.
- `P3b_is_trajectory.png` is now a sorted-rank chart, not the
  improvement-roadmap chart that the original `P3b_is_trajectory.png` rendered.
  Slide builders that referenced this image may need a caption tweak; image
  filename is preserved per the brief.
