# Confidence Scoring — Follow-Up Ideas

User-flagged ideas for after the client meeting (not blocking the 48-hour deadline).
Captured 2026-04-30 while the 1,497-segment decode was running.

## 1. Average word confidence vs IS, vs WER

**Idea.** Plot mean per-word probability against IS score and against WER for the
full 1,497-segment dataset. Look for the staircase / threshold the data
naturally produces.

**Why it matters.** Tells us whether segment-aggregated word confidence is a
useful per-segment quality signal in its own right (vs. just for the per-word
green/yellow/red coloring). If r(mean_word_prob, IS) is strong, we have a
runtime confidence signal that doesn't require running the full IS pipeline.

**Status today.** Pipeline exists ([analyze_confidence_distribution.py](../_research-tools/generators/analyze_confidence_distribution.py)) — just needs the full 1,497-segment confidence sidecar to land.

**Initial signal from the 33-Obama-segment subset.** Pearson r(mean_word_prob, WER) = −0.21, r(min_word_prob, WER) = −0.25. Weak but expected direction. Narrow speaker slice, expect stronger r on the diverse 1,497-segment baseline.

---

## 2. Confidence trajectory through a video — good vs bad

**Idea.** For each segment, plot per-word probability as a function of word
position (or time). Compare the trajectory shape on segments that succeeded
(low WER) vs failed (high WER).

**Hypotheses to test:**
- Failed segments may have an **early collapse** — model loses the thread
  partway through and never recovers.
- Failed segments may have a **flat-but-low profile** — model is uncertain
  throughout.
- Successful segments may have **dips at named entities or rare vocabulary**
  but recover quickly.
- Sentence-initial tokens are systematically lower (per the literature
  review) — this should appear as a left-side dip on every segment.

**Why it matters.** If failures have a distinctive trajectory, we can
flag a segment as "going off the rails" mid-decode rather than waiting for
the final transcript. Possible runtime intervention: cut the beam, restart
from the last confident point, or fall back to a different decoding
strategy.

**Status today.** Need the 1,497-segment sidecar + a new plot generator.
Roughly 30 minutes of code once the data is in.

---

## 3. Normalized confidence — top-1 vs top-2, vs rest of mass

**Idea.** Instead of (or in addition to) raw max-softmax probability,
compute:
- **Top-1 / top-2 ratio** — how dominant is the chosen token vs the
  next-best alternative?
- **Top-1 / sum-of-rest** — how much probability mass did the chosen token
  capture vs everything else?
- **Entropy** of the full distribution at each position — high entropy =
  high uncertainty.
- **Margin** = `p_top1 - p_top2` — common in active-learning literature.

**Why it matters.** Raw softmax is **mildly over-confident** for LLaMA-2
(per literature review: 5-15pp ECE). A normalized signal may be better
calibrated to actual error rate. Margin and entropy are well-studied
calibration alternatives.

**What we already have.** The decode-side plumbing already saves `top3_alts`
in the per-token JSON for each token (see `vsp_llm_decode.py` — it stores
top-k alternatives alongside the chosen token). So the data is there; just
need a new aggregator that derives margin / entropy / mass-ratio from it.

**Note from literature review:** [docs/confidence/llama2_confidence_literature_review.md](llama2_confidence_literature_review.md) recommends temperature
scaling on a labeled held-out slice as a one-shot calibration step. Worth
running once the 1,497-segment data is in.

---

## 4. Use all 20 beam-search hypotheses, not just top-1

**Idea.** The decoder runs beam search with `num_beams=20`. We currently
discard 19 of them and keep only the chosen sequence. Use all 20 to:
- Compute **diversity** at each position — how different are the 20 beams?
  Low diversity → high confidence.
- **Vote** at the word level — if 18 of 20 beams agree on a word, that's a
  stronger signal than top-1 softmax.
- **Minimum-Bayes-risk (MBR) decoding** — pick the hypothesis that minimizes
  expected error against the rest. Often beats top-1 in WER terms.
- **N-best rescoring** — feed the 20 beams to a second model (LM or human-
  preference scorer) and pick the best one.

**What it requires.** A bigger change to `vsp_llm_decode.py`: currently it
returns only `outputs.sequences[0]` per segment. Need to capture all 20.
The HuggingFace `generate()` call already produces them when `num_return_sequences=num_beams`. The `confidence-{fid}.json` schema needs to grow to hold all 20 hypos with their per-token confidence trails.

**Why it matters.** Beam-search agreement is the cheapest, highest-signal
confidence boost we have access to. Reduces hallucination rate on segments
where multiple beams converge on the same wrong answer (the worst failure
mode per literature). MBR has shown +1-3 BLEU / -3-5% WER in MT and ASR.

**Status today.** Out of scope for the 48h deadline. Strong candidate for
the next sprint.

---

## Cross-cutting recommendation

Run all four of these against the same 1,497-segment confidence sidecar
once it lands. The data collection (the GPU run) is the expensive part;
the analyses themselves are minutes-of-code each. Doing them all in one
sprint after the client meeting will give us the deepest confidence-scoring
write-up for whatever follow-up the meeting produces.
