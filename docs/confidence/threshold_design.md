# Confidence Threshold Design — Why 0.85 / 0.40

This document captures the design rationale for the per-word confidence
threshold cutoffs used by the green / yellow / red color coding in the
Argos client report. Companion to the
[Llama-2 confidence literature review](llama2_confidence_literature_review.md)
and the implementation in
[`compute_word_confidence.py`](../_research-tools/generators/compute_word_confidence.py).

---

## What each band MUST mean to a client

| Band | Color | Client interpretation | Reviewer action |
|------|-------|----------------------|-----------------|
| **HIGH** (≥0.85) | green | "Trust without review" | Skip |
| **MED** (0.40–0.85) | yellow | "Could be right, worth a glance" | Spot-check |
| **LOW** (<0.40) | red | "Model is guessing — likely wrong" | Verify |

These promises are the constraint. The thresholds are tuned to keep the
promises true on real data.

---

## The four forces that decide where to put the cutoffs

### 1. Empirical calibration is the truth

The right threshold is one where the band's *promise matches reality*.
If we tell the client "green = trust me," then words in the green band
should actually be correct **≥90% of the time**. If they're only 70%
correct, the green is a lie — and we lose all client trust the moment
they spot a wrong green word.

Calibration is measured per-band as

> P(word correct | model confidence in band)

This is what the 1,497-segment B3 decode is producing data for. After it
lands, we plot the calibration curve and decide whether to keep, tighten,
or loosen the thresholds.

### 2. LLaMA-2 is mildly over-confident

Per [literature review](llama2_confidence_literature_review.md):
LLaMA-2-class generative models exhibit ~5–15pp ECE
(Expected Calibration Error) in the 0.7–0.95 band, and RLHF / LoRA
fine-tuning makes this worse.

**Translation:** when the model reports `p = 0.85`, the empirical word
correctness is closer to **75–85%**, not 85%. A naively tight threshold
of 0.7 would mean reported-0.7 words are actually only ~55% correct —
not "trustworthy" by any client standard. **0.85 is about as low as we
can go and still defensibly call green "trust."**

### 3. Reviewer fatigue

If 50% of words land in red, reviewers burn out and stop using the
signal. We want red to be **small-but-real (5–15%)** so it's a useful
filter rather than a wall of work.

If 95% of words land in green, the reviewer never trusts green, because
"everything is green" is indistinguishable from "the system colored it
all green to look good." We want green to be **substantial but not
total (50–80%)** so the band is meaningful and the reviewer can lean on
it.

The yellow/medium band absorbs the rest. Its job is to be the
"spot-check" pile — small enough that reviewers can clear it, but
informative enough that the spot-checks pay off.

### 4. Cost of errors

If a wrong "trusted" green word is catastrophic (legal transcripts,
medical records, broadcast captions for the deaf and hard-of-hearing),
tighten green to 0.90+ — accept fewer green words to make every green
word more reliable.

If review is cheap (post-edit pipeline, internal tooling), loosen green
to 0.75 — get more pre-cleared words at the cost of slightly more
green-but-wrong cases.

**Our 0.85 is the safe middle.** It's the literature norm for
calibrated speech / NER / MT pipelines (Whisper, NeMo, OpenAI), and
it's defensible without making domain-specific assumptions about
client cost-of-error.

---

## What MAKES a word high vs medium vs low confidence

### HIGH — model has dominant signal

- Visemes look unambiguous on the lips. Common distinctive shapes
  ("the", "and", "you") that the model has seen millions of times.
- Strong language-prior reinforcement. After "president of the United"
  the next word is forced to "States" regardless of lip shape.
- Long preceding context narrows the candidate set to one.

### MED — model has a reasonable guess but real alternatives

- **Visually similar lip shapes.** "pat" / "bat" / "mat" / "map" are
  visemically identical — the model can't disambiguate from the lips
  alone, so it falls back to language prior and reports moderate
  confidence on whichever candidate the prior favors.
- Mid-frequency content words: most adjectives, verbs, common nouns.
- Words at sentence boundaries (less left-context to disambiguate).

### LOW — model is essentially picking among rivals

- **Named entities, proper nouns, rare vocabulary.** Out-of-distribution
  for the language prior; the model has no strong default.
- Numbers and dates. Many plausible candidates, weak prior.
- Words after a hesitation, a missed visual frame, or a profile angle.
- **Tokens at the start of a sentence** — systematically lower per
  literature (Kadavath 2022, Tian 2023). The aggregator should expect
  this.

---

## The dangerous case — why we capture entropy too

A model can be HIGH-confidence AND WRONG when it hallucinates fluent
text from its language prior with no real visual evidence backing it.
Raw max-softmax misses this case: the model says `p = 0.95` because
the language model loves that sentence, even though the lip shapes
were ambiguous.

**Entropy of the full distribution is a better hallucination signal.**
Hallucinations often have *medium* entropy (several plausible
continuations from the language prior) even when the chosen-token
max-softmax is high. Real visual signal usually corresponds to *low*
entropy: only one continuation is consistent with the lips.

**Implementation status:** as of this writing, `vsp_llm_decode.py`
captures per-token entropy and top-3 alternatives in the sidecar JSON.
The 1,497-segment B3 decode is producing the first cross-content
dataset to validate whether entropy improves over max-softmax in
practice. If P(correct | low-entropy) is meaningfully higher than
P(correct | high max-softmax), we will switch the band assignment to
use entropy or a margin signal (top-1 minus top-2) instead of, or
combined with, raw max-softmax.

---

## What we do when calibration says we're wrong

After the 1,497-segment data lands, expected outcomes and their
responses:

| Calibration finding | Response |
|---------------------|----------|
| P(correct \| green) ≥ 90% on full dataset | Keep 0.85 — promises hold. |
| P(correct \| green) is 80–90% | Footnote the deck: "green = ~85% reliable." |
| P(correct \| green) <80% on full dataset | Tighten green to 0.90 or 0.92. Re-render Obama demo. |
| **P(correct \| green) varies wildly by segment quality** | **Adopt a three-tier UI policy keyed on segment mean_prob (Trust / Salvage / Strip-coloring) — see below.** |
| Entropy beats max-softmax as a predictor | Switch coloring to use entropy gate; keep max-softmax in sidecar for archaeology. |
| Per-band performance is wildly different on different content types | Move toward per-domain thresholds (news vs interview vs YouTube vox-pop). |

The thresholds are not sacred. They are the current best guess given
limited data; they update when the data updates.

---

## What the 1,497-segment data actually said (May 2026)

The empirical answer to the calibration question above is **the fourth row
of the table**: P(correct | green) varies enormously with segment quality.
Stratified by the segment's own mean_prob bucket, on 23,261 aligned
hypothesis words across 1,427 segments:

| Segment mean_prob | P(correct \| green) | n green words |
|---|---|---|
| ≥ 0.85 (very high) | **92.8%** | 4,402 |
| 0.75–0.85 (high) | 83.8% | 3,828 |
| 0.65–0.75 (mid) | 69.6% | 2,129 |
| 0.55–0.65 (mid-low) | **41.3%** | 710 |
| 0.40–0.55 (low) | **21.8%** | 229 |
| < 0.40 (very low) | 18.2% | 11 |
| **Overall** | **80.6%** | 11,309 |

The flat-threshold answer ("green = trust") would be a lie about half
the time on segments with mean_prob below 0.65. The fix isn't tightening
the per-word threshold — it's recognizing that **the green band's promise
is only valid in segments that are themselves above a quality floor**.

### The three-tier policy (current operating points)

| Tier | Segment mean_prob | UI behavior | Why |
|---|---|---|---|
| **Trust** | ≥ 0.82 (T_safe) | Full coloring as designed; CONF_HIGH/CONF_MED unchanged | Green is ≥ 85% reliable here — the original promise holds |
| **Salvage** | 0.65 – 0.82 (T_salv 0.74) | Full coloring + visible "uncertain segment" banner | Green is 70–84% reliable; user can extract meaning if warned |
| **Strip-coloring** | < 0.65 | Plain grey text; NO color applied | Green is < 50% reliable here — coloring would mislead |

The boundary at **0.65** is the load-bearing one: below it, painting words green is a UI bug, not a feature. The boundary at **0.82** corresponds to the F1-max segment-level filter from
[`confidence_full_analysis.md` §10](confidence_full_analysis.md#10-extra-scatters--confidence-pairs-vs-hallucination-is-and-wer)
and the green-band 85%-reliability frontier from §11 — same threshold falling out of two independent analyses.

### Why this is not the final policy

These boundaries are tuned to **today's** model and training data:

- **LLaMA-2-7B over-confidence** (5–15pp ECE in the 0.7–0.95 band) inflates green leakage in low-confidence segments. Llama-3.1-8B and 3.3-70B have measurably better calibration, which would raise P(correct | green) uniformly and lower the strip-coloring boundary toward 0.55.
- **LoRA adapter trained on ~1,273 AVSpeech segments** — way below the 20K+ needed for stable numeric/entity generalization. The "billion → million" class of green leakage is a direct consequence: the model has not seen enough lip shapes for "billion" specifically, so it falls back to a fluent "million" with high softmax.
- **Beam aggregation (Mission 6) not yet deployed** — beam disagreement would catch most fluent-latch failures even when the chosen-beam softmax is high.

**Re-run [`analyze_band_reliability.py`](../_research-tools/generators/analyze_band_reliability.py) after each model upgrade.** The architecture (three tiers keyed on segment confidence) is permanent; the cut-points 0.65 / 0.74 / 0.82 will move as the model improves. Specifically expect them to tighten (i.e. T_strip drops, more segments earn coloring) as backbone, training data, and beam aggregation improve.

---

## What this means for the client meeting

**The deck currently uses 0.85 / 0.40, with the 33-Obama-segment
distribution as the most recent empirical anchor.** When asked "why
those numbers?" the answer is the four forces above, not "we picked
nice round defaults." The literature review provides the citation
trail; this document is the executive-summary reasoning.

If a sharp client asks why the green-band coverage on Obama is 82.9%
but only ~50% on the full 1,497-segment dataset (when that data
lands), the honest answer is: **Obama is exceptionally clean speech
(formal TV broadcast, frontal camera, professional speaker, mean WER
21%). The 1,497-segment dataset is real-world YouTube content with
mean WER 64% — the model is correctly less confident on it.** The
threshold is the same; what changes is the difficulty of the input.
That is exactly the behavior we want from a calibrated confidence
signal.
