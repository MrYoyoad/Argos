# Overlap-Consistency Analysis — Did Twice-Decoded Overlap Regions Help?

**Date**: July 16, 2026 (Workstream X). **Question** (user's words): *"see if overlapping parts of the same video getting different outputs when splitted helped."* The English baseline set was pre-cut upstream into ≤12 s segments with ~2 s overlap, so every overlap region was decoded twice. This analysis measures, against references, whether the second reading helps.
**Generator**: [analyze_overlap_consistency.py](../_research-tools/generators/analyze_overlap_consistency.py) (CPU-only, existing artifacts, no decode).

**Answer in one paragraph.** The two decodes of the same ~2 s of footage disagree on **half their words** (50.9% of 452 aligned word pairs). When they disagree, the most common outcome is *both wrong* (43.5%) — but the neighbor's reading is correct where the primary's is wrong **27.2% of the time** (95/349 directed positions), rising to **50.6%** when the neighbor's word is production-green (conf ≥ 0.95 ∧ beam agreement ≥ 0.80; n=85). So yes — the second reading carries real, exploitable signal, but only under a confidence gate. Mission 6's `hyp_xseg_merge` never used it: it was a **complete no-op** on this set (0 neighbors for all 1,497 utts, a seg-metadata format mismatch), and simulating it with a corrected neighbor map shows it would have **broken 10× more words than it fixed** — the no-op accidentally protected production. Verdict: **NO-GO for auto-swap, GO (narrow) for an engine-gated L4 candidate layer** in the phonetic-substitution module.

## Data and scope

| Item | Value |
|---|---|
| Base videos / utterances | 1,374 / 1,497 |
| Videos with 2 overlapping segments | **123** (246 utts = 16.4% of the set; the other 1,251 videos are single-segment) |
| Overlap length | 2.02 s mean (2.00–2.05), from utt-name frame ranges ÷ per-segment fps |
| Second segment (B) duration | median **3.48 s**, all 123 < 6 s — B is always the short remainder cut |
| Words in any overlap window | 1,245 / 23,261 hyp words (**5.4%**) |

The overlap structure lives in the utt names (`{video}_{seg:02d}_{startframe:06d}_{endframe:06d}`, frames at source fps) — **not** in `segment_metadata.json`, which records every one of the 1,497 pre-cut clips as its own video with `num_segments: 1`. This is the root cause of the xseg no-op below.

## Method (and its honesty box)

No word timestamps exist, so word positions are approximated **uniformly over the segment duration** (word *i* of *n* has midpoint (i+0.5)/n × duration; a word is "in the overlap" if its midpoint falls in the window: last ~2 s of segment A, first ~2 s of segment B). The two extracted spans are aligned with `align_word_lists` (Levenshtein); analysis runs on aligned word pairs. Correctness of each word is judged against its own segment's reference via the same alignment. Two checks bound the approximation error:

1. **Ref-vs-ref calibration**: the same window extraction applied to the two segments' *references* (same audio, transcribed twice by Whisper) agrees at **83.3%** (499/599) — the ceiling achievable under this position approximation. Hyp-vs-hyp agreement (49.1%) is therefore genuinely low, not an artifact.
2. **±20% window sensitivity** (below). Note that shrinking both windows is geometrically adversarial — A keeps the *late* part of the overlap, B the *early* part, so ×0.8 windows only half-overlap each other; ref-vs-ref agreement drops to 60.3% for the same reason. Rates are stable in the ×1.0–×1.2 regime.

Residual caveat: 15.2% of disagreeing pairs are "both right on different ref words" — alignment offsets near window edges, not real disagreements. Rescue rates count only positions where the primary word is wrong and the neighbor offers a *different, correct* word.

## Q1 — How often do the two readings disagree?

Anchor = `hyp_top1` (the actual decode; also xseg's anchor). 97/123 pairs have words on both sides (truncated decodes leave 26 empty spans).

| Window | Aligned pairs | Agree | Disagree | Ref-vs-ref agree (ceiling) |
|---|---|---|---|---|
| ×0.8 | 348 | 31.3% | 68.7% | 60.3% |
| **×1.0** | **452** | **49.1%** | **50.9%** | **83.3%** |
| ×1.2 | 540 | 51.7% | 48.3% | 86.8% |
| ×1.0 on `hyp_mbr` (production text) | 473 | 49.7% | 50.3% | — |

Normalized by the ref-vs-ref ceiling, hyp agreement is ~52–60% of what perfect consistency would produce, across all windows. **The model reads the same lips differently half the time** — mostly because segment B decodes the same frames with far less context (3.5 s clip vs 12 s clip).

## Q2 — When they disagree, who wins?

At ×1.0, the 230 disagreeing pairs split: **A right 27.8%** (64), **B right 13.5%** (31), **both wrong 43.5%** (100), both-right-offset 15.2% (35).

Directed rescue rates ("primary word wrong at an aligned overlap position → neighbor offers a different, correct word"):

| Direction | n wrong | Rescued | Rate |
|---|---|---|---|
| A wrong → B rescues | 159 | 31 | 19.5% |
| B wrong → A rescues | 190 | 64 | **33.7%** |
| Pooled | 349 | 95 | **27.2%** |
| Pooled, sensitivity ×0.8 / ×1.2 | — | — | 39.1% / 31.7% |
| Pooled on `hyp_mbr` | 385 | 92 | 23.9% |

- **Strong direction asymmetry**: the long first segment rescues the short remainder far more than vice versa. Context length drives read quality; the extra reading helps the *weaker* segment most.
- **By primary segment NIV bucket**: N 23.0% (32/139), P 30.6% (49/160), Y 28.0% (14/50) — rescue signal is strongest in the useful mid-tier, consistent with the substitution module's "Trust-tier enhancer, not a rescue tool" doctrine.
- **Confidence makes the signal usable** (each of the 230 disagreeing pairs yields two directed primary/neighbor instances, 460 total; rows below condition on the neighbor word):

| Neighbor-word condition | n | Neighbor right | Self right | Neither |
|---|---|---|---|---|
| nb_conf > self_conf (xseg's swap rule) | 230 | 30.9% | 10.4% | 58.7% |
| nb_conf ≥ 0.95 | 95 | 47.4% | 9.5% | 43.2% |
| **nb GREEN (conf ≥ 0.95 ∧ agree ≥ 0.80)** | **85** | **50.6%** | **8.2%** | 41.2% |
| (on `hyp_mbr` text, nb_conf ≥ 0.95) | 77 | 53.2% | 3.9% | 42.9% |

A green neighbor word is **~6× more likely correct than the primary's word** in a disagreement. But even there, "neither is right" remains ~41% — candidates need arbitration, not blind swapping.

## Examples (two readings of the same frames, vs reference)

1. **`ktMebjnZiSE_3__ebdf1351`** — A: *"to make two different **versions of** the iphone 6s"* / B: *"i had two different **surgeries off** the aortic"* / ref: *"to make two different sized versions of the iphone"*. **A right ×4**; the 3.5 s remainder hallucinated a medical topic from the same lips.
2. **`-TDEPVnDiM8_10__3bbf3c2d`** — A tail: *"or something **and you**"* / B: *"maybe a knife **or something**"* / ref: *"(like maybe) a knife or something"*. **B right ×2** — B's head, mid-clip for B, catches words A's dying tail garbled.
3. **`qbSxADAbyXI_4__563e34b3`** — A: *"it was like the **real housewives**"* / B: *"at that time was like **30 bucks**"* / ref: *"at that time was **eighth grade pass**"*. Both wrong, **differently** — two independent hallucinations of the same footage.
4. **`eAgwWAlS0io_6__1a93c6f4`** — A: *"know is really **ativan**"* / B: *"you should know is will it take a"* / ref: *"know is really **diazepam**"*. Both wrong on the entity — a second reading does not rescue named-entity failures.
5. **`IH1KTmVi1BQ_0__295d8cb1`** — A: *"didn't have any **delay or dropped** or"* / B: *"didn't have any **land or drops** where **i**"* / ref: *"i didn't have any delays or drops when"*. Near-miss disagreement (`delay`/`land` vs ref `delays`); **B rescues** `i`.

## Q3 — `hyp_xseg_merge` re-examination

**What shipped did**: nothing. On disk, all 1,497 utts have `neighbors_considered: 0`, zero swaps, and `hyp_xseg_merge.text == hyp_top1` for 1,497/1,497. Root cause: `lib/nbest_aggregate.py::load_segment_neighbors` expects `{utt_id: {video_id, start_frame, end_frame}}`, but `segment_metadata.json` is keyed per pre-cut clip with `num_segments: 1` and no `video_id` field — every entry is skipped and the neighbor map comes back empty. (Mission 6's May-2 report line "no-op — the full dataset has no configured cross-segment overlap" was half right: the dataset **has** 123 real overlaps; the *metadata plumbing* doesn't expose them.)

**What it would have done** (simulation: same shipped function, top1 anchor + raw confs + LCS≥3 gate, with a corrected neighbor map built from utt-name frame ranges):

| Metric | Value |
|---|---|
| Directed edges / gated out by LCS<3 / fired | 246 / 114 / 97 |
| Swaps | 408 (4.2 per fired edge) |
| **Fixed / broke / neutral vs refs** | **18 / 192 / 198** (fix:break = 1:10.7) |
| Swaps inside the true ~2 s overlap window | 185/408 (45.3%) |
| In-window only: fixed / broke / neutral | 12 / 80 / 93 (1:6.7) |
| Capture of Q2's 95 available neighbor-wins | **6 (6.3%)** |

Two design flaws explain the damage: (a) it aligns **60-word edges** — here effectively whole segments — so 55% of swaps land outside the overlap on spuriously Levenshtein-paired words; (b) it swaps on **any** conf difference (0.98 vs 0.99 triggers), converting correct words into a higher-confidence neighbor's misreads. Even window-restricted it breaks 6.7× more than it fixes, and it captures almost none of the genuine wins. **The format-mismatch no-op accidentally protected production quality. Do not "fix" xseg by wiring up the neighbor map; retire the method in favor of L4 below.**

## Q4 — L4 recommendation

**NO-GO** for any automatic cross-segment swap (xseg-style): measured fix:break is 1:6.7 at best.

**GO (narrow)** for overlap-neighbor words as an **L4 candidate layer** in the phonetic-substitution module — candidates only, engine-arbitrated, never auto-applied:

- **Eligibility**: utt has an overlapping neighbor (derive pairs from utt-name frame ranges as in the generator — not from `segment_metadata.json`); extract both overlap spans with the uniform-position window; align spans with `align_word_lists`.
- **Candidate rule**: for an aligned pair where the words differ and the primary word is flagged (module flagging: 0.30 ≤ p < 0.95, not green), admit the neighbor word as an L4 candidate **only if the neighbor word is green (conf ≥ 0.95 ∧ beam agreement ≥ 0.80)**; weight = `nb_conf × nb_agreement` (measured precision at this gate: 50.6% right vs 8.2% for the incumbent, n=85).
- **Module invariants apply**: no numeric/entity introduction, MAX_SUBS_PER_SEG, segment-quality floor, engine verdict required.
- **Honest expected impact**: green-gated wins on this whole set = 43 words — a **~0.16pp WER-equivalent ceiling** (oracle: all 95 wins, 0.35pp), because only 123/1,374 videos have a second segment and overlap covers 5.4% of words. The layer earns its place on cost (trivial: two files already on disk) and on **forward coverage**: production-split long client videos give every interior segment *two* overlap windows (~2 s each per 12 s segment), roughly tripling per-segment reach vs this short-clip set.

## Verification

- **Span extraction spot-check (5 videos, printed by `--spot-check`)**: A-tail / B-head words visibly cover the same source frames, confirmed by both refs — e.g. `Id9amnm6s3s_0` A: *"…so yeah it was obviously"* / B: *"but so yeah it was obviously just a demo"* (refs both *"but so yeah it's you know it was obvious(ly)…"*); `xITCbZxwLn4_0` A: *"…and then again after"* / B: *"after the initial contamination"* (refs both *"…after the insurance examination"*). Metadata overlap 2.02–2.03 s in all five.
- **Independent recomputation (20 random pairs, separate script, `difflib.SequenceMatcher` instead of Levenshtein for both alignments)**: agreement 67.6% vs main 50.6% (difflib pairs fewer substitutions — it drops uneven replace-blocks as gaps, enriching for exact matches: 71 vs 81 aligned pairs); pooled rescue 35.9% (14/39) vs main 44.0% (22/50) on the same pairs; the direction asymmetry reproduces (A-rescued 1/15 vs B-rescued 13/24 under difflib; 4/18 vs 18/32 under main). Same qualitative conclusions under a different alignment implementation.

Reproduce: `/home/ubuntu/vsp-llm-yoad-venv/bin/python docs/_research-tools/generators/analyze_overlap_consistency.py --examples 12`
Inputs: `english_full_results/segment_metadata.json`, `english_full_nbest_eval/decode_output/hypo-172610.json` + `agreement-172610.json`, `english_full_nbest_eval/aggregated.json`, `english_full_nbest_eval/report/report.csv`.
