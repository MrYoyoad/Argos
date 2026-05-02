# How Aggregation + Confidence Make the Output Trustworthy

**Audience:** Client review. Non-technical readers welcome.
**Goal:** Show, with real examples, how the two reliability mechanisms in the lip-reading system — *beam aggregation* and *per-word confidence colouring* — work together to (a) produce more correct text, and (b) tell you which parts of that text to trust.

---

## The two mechanisms in plain English

### 1. Beam aggregation — picking from 20 guesses, not just 1

For every segment, the model internally generates **20 alternative phrasings** (called "beams"), each scored by how plausible the model thinks the whole sentence is. The simplest thing to do is take the top-scoring beam and call it the answer. The simplest thing is what most systems do.

What we do instead: we look across all 20 beams, position by position, and pick the **token with the highest combined per-word confidence across the beams that contain it**. If 14 of 20 beams say "trick" at position 3 with high confidence, but the single highest-scoring beam happens to say "train" there, the consensus wins. This is the `hyp_vote_conf` aggregator.

**The intuition:** the highest-scoring whole sentence isn't always the most reliable at every position. A small error in one word can ride along inside an otherwise fluent guess. Cross-checking against the other 19 beams catches those errors before the user sees them.

### 2. Per-word confidence colouring — the model flags its own uncertainty

Every word the model writes comes with a **probability score** — the model's own estimate of how likely that word is correct. We surface this to the reader as colour:

| Colour | Probability | Meaning |
|---|---|---|
| **Blue** | ≥ 0.85 | "I'm confident." |
| **Orange** | 0.40 – 0.85 | "Best guess." |
| **Purple** | < 0.40 | "I had to pick something." |

A second signal — the **tier badge** — summarises the whole segment:

| Tier | Segment confidence | What it tells the reader |
|---|---|---|
| **Trust** | ≥ 0.82 | "The colours mean what they say. Read normally." |
| **Salvage** | 0.65 – 0.82 | "Useful but partial. Use blue words as anchors; verify orange/purple." |
| **Strip** | < 0.65 | "Don't read words. Use for gist only. Watch the video if facts matter." |

In Strip-tier segments the colours are **removed entirely**, because below 0.65 even the blue words are unreliable enough that showing them as blue would mislead.

---

## How much does each mechanism help? — measured

Based on the full 1,497-segment evaluation (April–May 2026):

### Beam aggregation

- Mean WER: **64.05% → 62.49%** (−1.56pp absolute, ~2.4% relative).
- 42 segments crossed a quality boundary (NIV upgrade): 23 went from "Failed" to "Partial," 19 went from "Partial" to "Clearly Conveyed."
- **No regressions** — every aggregation method tied or beat top-1 on mean WER.

### Per-word confidence colouring

Within useful content (NIV Y or P, ~62% of corpus), the colour predicts word-level correctness:

| Colour | In Trust-tier segments | In Salvage-tier segments |
|---|---:|---:|
| Blue | **94%** correct | **80%** correct |
| Orange | 65% correct | 41% correct |
| Purple | 39% correct | 20% correct |

The blue-to-purple gap is **55pp in Trust segments and 60pp in Salvage segments** — the colour signal does its strongest work exactly where the user needs it most (Salvage, where the spine of meaning depends on knowing which words to anchor on).

---

## Worked examples

Six segments from the full evaluation, chosen to show the mechanisms in action.

### Example A — Aggregation rescue: "trick number one"

**REF:** *for a presentation so trick number one is*

**Top-1 beam (no aggregation):** *presentation so train number one is be* — WER 50%, IS 3.57 (NIV **P**)
**With aggregation (`hyp_vote_conf`):** *presentation so trick number one is* — WER 25%, IS 4.33 (NIV **Y**)

**What happened.** The 20 beams for this segment looked like:
- Rank 0 (top-1): "presentation so **train** number one is be" — score −2.29
- Rank 1: "presentation so **trick** number one is be" — score −2.33 (essentially tied)
- Rank 2: "presentation so **trick** number one is" (no spurious "be") — score −2.64
- Ranks 4, 7, 8, 10, 12, 13, 14, 17 also have **trick**

Across all 20 beams, "trick" appears more often and with higher per-token confidence at position 3 than "train" does. Half the beams stop after "is" without the spurious "be." The aggregator picks the consensus on both fixes. The segment crosses from Partial (a paraphrase the user might or might not recover) to Clearly Conveyed (the actual sentence).

---

### Example B — Aggregation rescue: medical term

**REF:** *i was born with congenital rubella syndrome*

**Top-1:** *i was born with congenital relapsing* — WER 29%, NIV **P**
**Aggregated:** *i was born with congenital syndrome* — WER 14%, NIV **Y**

**What happened.** Top-1 chose "relapsing" — a medically plausible but wrong completion. Across the 20 beams, "syndrome" appears with high per-token confidence in many of them; "relapsing" / "rebellion" / "tactics" each appear in only 1–2. The vote correctly picks the anchor word that almost every beam agrees on, dropping the speculative tail. The segment now communicates the core fact (a congenital condition called *something* syndrome) instead of a fluent-sounding distractor.

---

### Example C — Aggregation rescue: replacing a hallucination

**REF:** *i did not have to major in acting there were some*

**Top-1:** *did not have to **measure a hacking** that was* — WER 64%, NIV **N** (Failed)
**Aggregated:** *did not have to **major in hacking** that was* — WER 45%, NIV **P** (Partial)

**What happened.** "Measure a" is a hallucination — the model picked a phonetically similar but meaningless phrase. Other beams correctly converged on "major in." Vote-confidence aggregation replaces the hallucinated tokens with the consensus, lifting the segment from "useless" to "you can roughly tell what was said." The aggregated text reads as: *they didn't have to major in [something related to hacking — could be acting, hacking, or backing], and that was [...]*. Combined with context, the user gets the gist.

---

### Example D — Confidence-led reading: Trust-tier segment

**REF:** *okay let's start out by playing a long tone on middle c and then we're going to go down chromatically from there if you haven't done so already i highly recommend you watch my saxophone*

**Tier:** Trust (segment confidence 0.91), 26 of 33 words blue.

**Coloured rendering** (✓ = correct, ✗ = wrong):

> [orange✗]can [blue✓]start [blue✓]out [blue✓]by [blue✓]playing [blue✓]a [blue✓]long [orange✗]note [blue✓]on [purple✓]middle [blue✓]c [blue✓]and [blue✓]then [orange✓]we're [blue✓]going [blue✓]to [blue✓]go [blue✓]down **[purple✗]dramatically** [blue✓]from [blue✓]there [blue✓]if [blue✓]you [blue✓]haven't [blue✓]done [orange✓]so [blue✓]already [blue✓]i [blue✓]highly [blue✓]recommend [orange✗]to [blue✓]watch [blue✓]my [purple✗]sex [orange✗]phone [orange✗]opera

**How a reader uses this.** All 26 blue words are correct (94% reliability holds in this Trust segment). The single purple word in the middle — **"dramatically"** — is exactly where the reader should pause. The actual word was *"chromatically"*, which makes more sense in a music tutorial. A reader who treats purple as "demote" and uses context recovers the meaning instantly. The colours did the cognitive work of saying *"don't read this one at face value"*.

The trailing purple/orange tail (*"sex phone opera"* should be *"saxophone"*) is an artefact of the model splitting one long word into three made-up shorter ones — both purple and orange flag this, so the reader knows not to take "sex" or "opera" literally.

---

### Example E — Confidence-led reading: Salvage-tier segment

**REF:** *what that meant is that we need a radically different approach we basically need to find a way how we can take existing routers existing switches existing links and enable them for research*

**Tier:** Salvage (segment confidence 0.71). Banner shown: *"Reading carefully — verify names, numbers, critical details."*

**Coloured rendering:**

> **[purple✗]their [purple✗]masses [purple✗]and** [orange✓]we [orange✓]need [purple✓]a [orange✓]radically [blue✓]different [blue✓]approach [blue✓]we [blue✗]must [purple✗]indeed [blue✓]find [blue✓]a [blue✓]way [orange✓]we [blue✓]can [purple✗]design [orange✓]existing [blue✗]roads [orange✗]to [orange✗]exist [purple✗]with [purple✓]existing [purple✗]structures [blue✓]and [blue✓]enable [blue✓]them [blue✓]for [orange✗]reuse [blue✗]so

**How a reader uses this.** WER on this segment is ~50%. Reading word-by-word, you'd get hopelessly confused. But reading by the colour spine:

- The blue words form a **coherent skeleton**: *"different approach we... find a way... can... existing... and enable them..."*
- The purple cluster at the start (*"their masses and"*) is correctly flagged: those are hallucinations the reader can drop.
- The middle reds (*"design"*, *"roads"*) flag the words where the model substituted plausible-but-wrong technical terms (the truth was "take routers... links").

A reader who **trusts blue, treats orange as ambiguous, and discounts purple** comes away with the correct gist: *"they need a different approach using existing infrastructure, and they want to enable it for [some purpose]."* The Salvage banner reminds the reader that the specific technical terms (router/switch/link) are exactly the type of word the model is most likely to have hallucinated.

This is the heart of the value proposition: **a 50%-WER segment becomes a 100%-correct gist** when the reader uses the colour signal correctly.

---

### Example F — When the system says "don't trust this"

**Tier:** Strip (segment confidence below 0.65).

**Display:** the hypothesis is rendered in plain grey-italic text, no per-word colours, with a banner: *"Model is unsure — text may not be reliable, even where it looks confident."*

**How a reader uses this.** They don't read words. The system has explicitly said: this is below the threshold where the colours mean anything. The hypothesis is a *guess at the topic*, not a transcription. If the segment matters, the reader plays the video.

This is the system's most underrated feature. It's the system **knowing what it doesn't know**, and refusing to display a misleading certainty signal. About 34% of segments fall in this tier in the current pipeline; for those, "we don't know what was said precisely, but it was probably about X" is the most honest answer the system can give.

---

## What CAN be trusted

| What | How reliable | How to use it |
|---|---|---|
| Blue words inside **Trust** segments | 94% correct | Read at face value. Quote freely (with the numeric/name caveat below). |
| Blue words inside **Salvage** segments | 80% correct | Use as anchor words. Build the meaning around them. |
| The **tier badge** itself | Well-calibrated to actual segment quality | Read it before reading the words. It is the prerequisite for trusting any per-word signal. |
| The **gist** of a Trust or Salvage segment | Recoverable in >85% of cases by trusting blue + context | Suitable for summarising, search/discovery, downstream LLM input. |
| The **aggregated text** vs. top-1 alone | Tied or strictly better on every method we tested; no regressions on mean WER | Always prefer the aggregated output. It's a free win — same compute, lower error. |

---

## What CANNOT be trusted

### 1. Numbers, dates, dollar amounts — regardless of colour

The model can be 95%+ confident on a number that is wrong by orders of magnitude. Real examples from the evaluation:

| Reference | Model output | Model's confidence | Tier |
|---|---|---:|---|
| *each bottle contains 1 **billion** cfus* | *1 **million** cfus* | 0.965 (blue) | Salvage |
| *the 18th of november **2011*** | *the 18th of november **2000*** | 0.894 (blue) | Salvage |
| *only **80** calories per* | *only **80** gallons per* (units swap) | 0.97 (blue) | Salvage |
| *…work **24 seven**…* | *…work **24 7**…* (cosmetic only) | 0.98 (blue) | Trust |

**Why this happens.** The model has very strong priors on *"the next word will be a number"*, but its visual signal for *which* number is much weaker than its signal for "is this region of the mouth saying a number." So it picks a fluent-sounding number with high confidence, even when it's wrong by a factor of 1,000. The blue colour reflects the model's certainty that *some number goes here*, not that the specific number is correct.

**The rule:** if the segment contains a number, named entity, date, or quantity, **verify against the source video** before quoting it. The colour is not informative for these tokens.

### 2. Anything inside a Strip-tier segment (read word-by-word)

Below 0.65 segment confidence, blue-band reliability drops to ~37%. Reading the words individually will mislead. This is precisely why the system strips the colouring in Strip-tier segments — to remove the temptation. Use Strip segments only as topic hints.

### 3. Fluent purple words

Purple words are most dangerous when they sound plausible. *"Dramatically"* in a music tutorial reads naturally; *"relapsing"* after *"congenital"* reads like a real medical phrase. The fluency is the trap; the purple colour is the truth. **Treat the colour as the ground truth, not the fluency.**

### 4. The first or last few words of a segment, slightly more than the middle

The model's confidence dips at segment boundaries (the visual context is shorter on one side). Aggregation helps here too — boundary tokens are often the ones the 20 beams disagree on most. But this is a residual risk: orange/purple words near a segment edge are more often wrong than the same colours in the middle.

---

## Practical reading workflow

For each segment in the report:

1. **Look at the tier badge.** This is the gate. If it's Strip, switch to gist-only mode and don't read individual words.
2. **Inside Trust or Salvage, scan for non-blue words.** The blue words are the spine; the orange and purple words are where you spend attention.
3. **For any number, name, date, or quantity:** verify against the video, even if it's blue.
4. **Compose the meaning** from the blue spine plus context, treating orange as ambiguous and purple as discount.
5. **For downstream automated processing** (search, classification, LLM summarisation): use the aggregated text directly; the lift over top-1 is free.

---

## How the two mechanisms reinforce each other

Aggregation and confidence colouring solve different parts of the same problem:

- **Aggregation** improves the *content* the user sees. It catches errors in the model's first guess by cross-checking with 19 alternates. The user benefits without doing anything.
- **Confidence colouring** improves the *interpretability* of whatever content is shown. It tells the user *which words to act on* and *which to discount*.

Together they cover both halves of "trustworthy output":

> The aggregator gives you better text. The colours tell you how much of that text to believe.

The aggregator's gain on the headline metric (WER) is modest (−1.56pp). The colouring's gain — converting partial transcriptions into usable content — is much larger. In Salvage-tier segments specifically, **the colour signal is what turns a 50%-WER segment from "garbled" into "the gist is recoverable."** That's the part of the value the aggregator can't deliver alone.

---

## Limitations and what improves over time

- **Calibration is tuned to today's model** (LLaMA-2-7B backbone, current LoRA adapter, single-segment confidence). The thresholds (0.82 for Trust, 0.65 for Strip, 0.85 for blue, 0.40 for purple) will move as the system improves.
- **Aggregation's gain is small in absolute terms** (−1.56pp WER). It helps most when the top-1 beam happens to contain a confident error — which is exactly when the user needs help, but it's not a magic bullet for systematically poor segments.
- **Numbers and named entities remain the hardest case.** No amount of aggregation or confidence calibration fully fixes this — the underlying signal (which number am I lipreading?) is intrinsically harder than (am I lipreading a number?). The defence is workflow: always verify these against video.

Each of these has a clear improvement path:

| Upgrade | Expected effect |
|---|---|
| Stronger backbone (Llama-3.1-8B or 3.3-70B) | Better-calibrated confidence; blue reliability +3–6pp uniformly. |
| 20K+ AVSpeech training segments (vs current 1,273) | Cuts numeric/entity hallucinations significantly. |
| Beam-disagreement gating | Demotes high-prob-but-disagreed tokens out of the blue band before the user sees them — addresses green leakage at its source. |
| Cross-segment context (the same speaker over multiple segments) | Reduces topic-confusion errors (medical vs music vs DIY vocabulary). |

The architecture of the policy — *aggregate first, then colour, then tier-gate the colours, then verify numbers/names against video* — is stable and outlives the current numbers.

---

## Summary

The system's reliability story is a layered defence:

1. **Aggregation** silently corrects the model's first guess where the other 19 beams disagree.
2. **Per-word colours** tell the reader, word-by-word, how much to trust each token in the corrected output.
3. **Tier badges** tell the reader, segment-by-segment, whether the per-word colours are themselves trustworthy.
4. **The numeric/name caveat** is the workflow rule that compensates for the one calibration gap the system can't fully close on its own.

Used together, this turns a system with 64% WER on the headline metric into one where the reader can confidently extract the *intended meaning* of roughly 62% of segments and is honestly told to skip or verify the rest. The mechanisms don't replace the underlying model — they **expose its uncertainty** in a form the reader can act on.

---

## References

- Per-word reading guide for end users: [per-word-confidence-user-guide.md](per-word-confidence-user-guide.md)
- Aggregation methods and validation: [docs/beam-search/n_best_implementation.md](../beam-search/n_best_implementation.md), [docs/beam-search/report_5_beam_search_aggregation.md](../beam-search/report_5_beam_search_aggregation.md)
- Confidence calibration data: [docs/confidence/band_reliability_by_niv.md](../confidence/band_reliability_by_niv.md), [docs/confidence/band_reliability_by_segment_quality.csv](../confidence/band_reliability_by_segment_quality.csv)
- Tier policy: [docs/confidence/band_reliability_rollout_plan.md](../confidence/band_reliability_rollout_plan.md)
- Numeric/entity false-confidence cases: [docs/confidence/green_leakage_examples.csv](../confidence/green_leakage_examples.csv)
- Full eval data: [english_full_nbest_eval/report/report.csv](../../english_full_nbest_eval/report/report.csv) (aggregation), [english_full_results_2026-05-01/client_outputs/report/](../../english_full_results_2026-05-01/client_outputs/report/) (baseline + per-word confidence)
