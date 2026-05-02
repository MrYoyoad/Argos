# Band Reliability Stratified by NIV Outcome

**Date:** 2026-05-02
**Question:** Within useful content (NIV Y or P), does the per-word confidence flag (green/yellow/red) actually help a user separate trustworthy words from unreliable ones?
**Answer:** Yes — strongly. The reliability gradient from green to red is **62.5pp** within useful content, and the gradient is steepest exactly where it is most needed (NIV-P).

## Method

- 23,261 words across 1,427 segments from the May 1 baseline run (`english_full_results_2026-05-01/`).
- Per-word band: `conf_class` from `word_confidence.json` (`conf-high → green`, `conf-med → yellow`, `conf-low → red`). Bands are derived from the per-token softmax probability emitted at decode.
- Per-word correctness: canonical Levenshtein alignment via [`hyp_word_correctness`](../_research-tools/generators/_alignment.py#L77) — same definition used by [`band_reliability_by_segment_quality.csv`](band_reliability_by_segment_quality.csv). A word is "correct" iff it aligns to a reference word at the same position with the same surface form (case-insensitive).
- NIV outcome: `Y` if IS ≥ 3.80, `P` if 2.00 ≤ IS < 3.80, `N` if IS < 2.00.

## Headline numbers

### Within useful content (NIV Y+P combined, ~62% of corpus)

| Band | Words | P(correct) | P(wrong) |
|---|---:|---:|---:|
| Green | 9,815 (58%) | **87.2%** | 12.8% |
| Yellow | 4,994 (29%) | **48.9%** | 51.1% |
| Red | 2,126 (13%) | **24.7%** | 75.3% |

Green-to-red spread = 62.5pp. The flag carries strong information about word-level reliability *within* a segment that the user has already been told is "useful".

### Stratified by NIV tier

| Band | NIV Y (IS ≥ 3.80) | NIV P (2.00 ≤ IS < 3.80) | NIV N (IS < 2.00) |
|---|---:|---:|---:|
| Green | 94.1% (4,830 / 5,135) | 79.7% (3,732 / 4,680) | 37.1% (555 / 1,494) |
| Yellow | 65.2% (1,038 / 1,591) | 41.2% (1,402 / 3,403) | 16.9% (419 / 2,476) |
| Red | 38.7% (196 / 507) | 20.3% (329 / 1,619) | 6.9% (163 / 2,356) |

Backing CSV: [band_reliability_by_niv.csv](band_reliability_by_niv.csv).

## Interpretation

**Inside NIV-Y (clearly conveyed).** The text is mostly correct anyway. Only ~10% of words are non-green, so the flagging mostly tells the user *which 1–2 words to re-read*, not which to ignore. Even reds are 39% correct, so the UI message should be "demote, don't delete." The flag's main value here is alerting the user to a misheard word inside an otherwise reliable transcript — for example, "dramatically" flagged red where the truth was "chromatically."

**Inside NIV-P (partial).** This is where the flag does the heaviest lifting:
- Green = 80% reliable — a backbone of trustworthy anchor words the user can build meaning around.
- Yellow = 41% (a coin flip) — exactly the right thing for the UI banner "verify this."
- Red = 20% (1 in 5) — strong "discount this" signal. A user reading "trust greens, skim yellows, ignore reds" recovers a coherent paraphrase from the green anchors plus context, which is what NIV-P represents in practice.

**Inside NIV-N.** Even green is only 37% reliable, which is why the current Strip policy strips the coloring entirely below segment mean_prob 0.65 — the green band would actively mislead. This finding is consistent with the existing [band_reliability_rollout_plan.md](band_reliability_rollout_plan.md): the segment-conditional gating is the load-bearing UI rule, and the per-band flag carries information *within* the tiers where it's allowed to render.

## Implication for the UI

The current three-tier policy (Trust ≥ 0.82 / Salvage 0.65–0.82 / Strip < 0.65, keyed on segment mean_prob) is correctly suppressing flag rendering in the cases where the flag would mislead (NIV-N–like segments). What this analysis adds: even within the Salvage tier (≈ NIV-P), the within-band reliability gap (80% / 41% / 20%) is large enough that the flag is doing real work — not just decoration. Users can act on band differences inside Salvage, not only on the segment-level banner.

The yellow band specifically deserves to keep its current UI treatment of "ambiguous." Calling it green-equivalent would be wrong (it is half-wrong in P); calling it red-equivalent would be wrong (it is 65% right in Y). Yellow as "stop and check" is well-calibrated.

## Concrete examples

**NIV-Y, IS = 4.21 — saxophone tutorial** (`P1RQi6YG1Xg_0__2ff3529d_00_000000_000300`)
- REF: `okay let's start out by playing a long tone on middle c and then we're going to go down chromatically from there if you haven't done so already i highly recommend you watch my saxophone`
- 26/26 green words correct. Yellow flags include "can" (was "okay"), "note" (was "tone"). Red flag "dramatically" (was "chromatically"). User who pauses on red recovers the correct meaning.

**NIV-P, IS = 3.02 — networking research** (`c6eBrYor21I_10__70697c08_00_000000_000350`)
- REF: `we need a radically different approach we basically need to find a way how we can take existing routers existing switches existing links and enable them for research`
- HYP starts with three reds ("their", "masses", "and") — all hallucinations. Green words "different approach we... find a way... can ... and enable them" carry the meaning. Reds correctly flag 7/9 wrong words.

## Caveats

- Bands are derived from current LLaMA-2-7B + current LoRA adapter. As noted in [band_reliability_rollout_plan.md](band_reliability_rollout_plan.md), better calibration (Llama-3.1-8B), more training data (20K+ AVSpeech segments), and beam-disagreement gating will all shift the within-band reliabilities upward and let the thresholds tighten.
- "Correctness" here is exact alignment match. Semantically-equivalent paraphrases (e.g., "saxophone" → "sax phone" tokenized into two words, both flagged red) count as wrong even though the meaning is recovered. This understates the true UI value of the flag.
- The `:rep` / `:ins` / `:ok` tags in `report.csv`'s `hyp_tagged` column use a *different* (positional) definition of correctness — see [VSP-LLM/scripts/make_report.py:67-94](../../VSP-LLM/scripts/make_report.py#L67-L94). Do not confuse those tags with the canonical alignment-based correctness used here.
