# How to Read a Lip-Read Transcript: User Guide to Per-Word Confidence

**Audience:** Anyone reading the system's output — analysts, domain experts, downstream users. You do not need to know how the model works.

**The point:** The transcript tells you twice how much to trust it. Once at the segment level (a small badge), once at the word level (each word's color). This guide explains how to use both, in order, on a single segment.

---

## Scope — applies to all videos, past and future

The **joint conf + beam-agreement band rule** (described below) is the canonical rule for word coloring across the project. It applies to:

- **Future videos**: any pipeline run with `VSP_NBEST=1` produces a `nbest-{fid}.json` sidecar; stage 8 (`outputs.sh::run_outputs`) automatically computes per-word beam agreement and re-paints `word_confidence.json` under the joint rule. No flag to set, no opt-in. This is the default behavior on EC2 and in the container overlay (`vsp_linux_container_FINAL_20260217/`).
- **Past videos** (decoded before May 2 2026): existing reports on disk were painted under the old conf-only rule. **Re-run stage 8 to apply the joint rule retroactively** — no re-decode required, the existing `nbest-{fid}.json` and `confidence-{fid}.json` sidecars are sufficient. Recipe at the bottom of this guide.
- **Videos decoded without `VSP_NBEST=1`**: no `nbest-{fid}.json` sidecar exists, so the joint rule cannot be computed. The pipeline silently falls back to the conf-only rule for these. To upgrade, re-decode with `VSP_NBEST=1` (which also produces the n-best aggregator outputs).

> The joint rule is **not** an experimental opt-in. It is the production default as of May 2 2026. Reports painted under the old conf-only rule (typically dated April 30 – May 1) should be regenerated when convenient.

---

## TL;DR — The 30-second rule

When you open a transcript card, look at things in this order:

1. **Tier badge** — a coloured pill labeled **Trust**, **Salvage**, or **Strip**.
2. **Word colours** — each word is **blue** (high), **orange** (medium), or **purple** (low). In **Strip** segments, the colours are removed and the text is grey-italic.
3. **Read accordingly:**

| Tier badge | What it means | How to read |
|---|---|---|
| **Trust** | Segment is solidly transcribed | Read normally. Pause only on orange/purple words. |
| **Salvage** | Useful but partial | Use **blue words as the spine** of the meaning. Treat orange as ambiguous; treat purple as likely wrong. |
| **Strip** | Unreliable | Skim for *gist only*. Do **not** quote individual words. Watch the video if facts matter. |

**Special rule that overrides everything:** numbers, names, dates, dollar amounts. The model's confidence on these is *not* well-calibrated even when blue. Always verify against the source video before using them.

---

## Why two signals?

The system has two different things to report:

- **Tier (segment-level):** "How much should you trust this whole segment as a coherent statement?" Computed from the segment's average per-word probability.
- **Colour (word-level):** "How sure was the model about *this specific word*?" Computed from the model's softmax probability on that token.

A segment can be high-tier overall but contain one purple word in the middle. Or it can be Salvage-tier with most words blue and a few orange. The two signals carry independent information — read both.

---

## The colour key

| Colour | Probability | What the model is saying |
|---|---|---|
| **Blue** (high) | ≥ 0.85 | "I'm confident this is the right word." |
| **Orange** (medium) | 0.40 – 0.85 | "This is my best guess, but I'm not sure." |
| **Purple** (low) | < 0.40 | "I had to pick something. This is a placeholder." |

In some report skins (e.g. the client demo) the same bands are rendered as **green / yellow / red** instead of blue / orange / purple. The meaning is identical.

---

## What the colours actually predict (calibration)

Measured on 23,261 words across 1,427 real segments. "Correct" = matches the ground-truth word at that position.

**Inside Trust-tier segments (most of "useful" content):**

| Colour | % correct | Read it as |
|---|---:|---|
| Blue | ~94% | Take it at face value (but: numbers/names rule below). |
| Orange | ~65% | Likely right, but worth a glance at the video. |
| Purple | ~39% | Probably wrong; demote in your reading. |

**Inside Salvage-tier segments:**

| Colour | % correct | Read it as |
|---|---:|---|
| Blue | ~80% | A reliable anchor. Build the meaning around blue words. |
| Orange | ~41% | Coin flip. Treat as ambiguous; cross-check via context. |
| Purple | ~20% | Treat as wrong unless context obviously rescues it. |

**Inside Strip-tier segments:** the system removes the colouring on purpose because even blue words drop to ~37% reliable in this regime. Reading the words individually misleads you. Use the segment as a hint about *what was probably being talked about*, not as a source of facts.

The pattern: the colour signal is **strongest** exactly where you need it most — inside Salvage-tier segments, where the gap between "reliable backbone" and "discount this" is widest.

---

## Decision flow on one segment

```
┌─────────────────────────────────────────────────┐
│ Open the segment card.                          │
└─────────────────────────────────────────────────┘
                       │
                       ▼
              What is the tier?
                       │
       ┌───────────────┼─────────────────┐
       ▼               ▼                 ▼
    TRUST           SALVAGE             STRIP
       │               │                 │
       ▼               ▼                 ▼
 Read as if      Read for meaning    Read for gist.
 normal text.    around blue         Don't quote
 Pause only      anchors.            individual words.
 on orange or    Verify orange       Watch the video
 purple words.   and purple via      if any facts
                 context or video.   matter.
       │               │                 │
       └───────────────┴─────────────────┘
                       │
                       ▼
        Does the text contain a number,
        a proper noun, a date, an amount?
                       │
                       ▼
            YES → verify against video
            regardless of colour or tier.
```

---

## Worked examples

### Example 1 — Trust tier, one purple word

> **Tier: Trust** (segment confidence 0.91)
>
> *okay let's start out by playing a long* **note** *on* *middle c and then we're going to go down* **dramatically** *from there...*
>
> (orange: "note", purple: "dramatically"; everything else blue)

**How to read it:** The blue words give you the meaning — a music tutorial, starting on middle C, going down a scale. Orange "note" is probably right (the original was actually "tone" — close enough that the tutorial still makes sense). Purple "dramatically" is the one to pause on; in fact the original was "chromatically." A reader who treats purple as "demote" recovers the correct meaning instantly: *of course it's chromatically, not dramatically — this is a music tutorial.* The colours did their job.

### Example 2 — Salvage tier, mixed bands

> **Tier: Salvage** (segment confidence 0.71). *Banner: "Reading carefully — verify names, numbers, critical details."*
>
> *...we need a* **radically** *different approach we* **must** *find a way we can* **design** *existing* **roads** *to exist with existing structures and enable them for research...*
>
> (blue: "different approach", "find a way", "existing", "and enable them"; orange: "radically", "we"; purple: "their", "masses", "must", "design", "roads")

**How to read it:** The blue spine — *"different approach... find a way... existing... enable them..."* — tells you the segment is about adapting existing infrastructure for research. Two of the purple words ("design", "roads") are wrong (the original was "take routers ... switches ... links"), but a reader who correctly discounts the purples and trusts only the blues recovers a faithful gist: *they need a new approach that uses existing components for research*. The colour signal converts a 50%-WER segment into a usable summary.

### Example 3 — Strip tier

> **Tier: Strip** (segment confidence 0.52). *Banner: "Model is unsure — text may not be reliable, even where it looks confident."*
>
> *(text shown in plain grey italics, no per-word colouring)*

**How to read it:** Don't read individual words. The hypothesis as a whole is a *guess at the topic*, not a transcription. Use it as a starting point for "this segment seems to be about X" and watch the video if X matters.

---

## When to use what mode

| Your task | Trust | Salvage | Strip |
|---|---|---|---|
| **Quote verbatim** in a report | Quote blue words freely; verify orange/purple in source | Quote only blue words, and only after spot-checking the video | Don't quote |
| **Summarize the gist** | Use the transcript as-is | Summarize from blue anchors plus context | Use only as a topic hint |
| **Extract a specific fact** (number, name, date) | Verify against video regardless of colour | Verify against video | Watch the video |
| **Bulk-skim** a long video | Read normally | Read normally; mentally bracket non-blue words | Skip or skim |

---

## Common mistakes

- **Treating blue as a guarantee.** It is ~94% in Trust segments and ~80% in Salvage. The remaining percentage tends to concentrate on numbers, named entities, and rare words — exactly where errors are most costly. *Always verify those classes specifically.*
- **Treating purple as "definitely wrong" in a Trust segment.** Inside Trust, even purple is ~39% right. Use it as a "look at this carefully" flag, not an "ignore" flag.
- **Reading a Strip segment word-by-word.** The whole point of stripping the colour is that the per-word signal is misleading at this confidence level. Read for gist, not for words.
- **Ignoring the tier badge.** A blue word in a Strip segment is *not* the same as a blue word in a Trust segment — its empirical reliability is roughly half. The tier is the prerequisite for trusting any per-word signal.

---

## What changes over time

The thresholds in this guide (0.82, 0.65, 0.85, 0.40) are calibrated to the current system (LLaMA-2-7B backbone, current LoRA adapter, single-beam confidence). Future upgrades — a stronger backbone, more training data, beam-disagreement signals — will improve calibration and let the thresholds tighten. The *shape* of the policy (tier first, then colour, with a special rule for numbers/names) is stable. The exact cutoffs will move.

When in doubt, the source video is always available and is always the ground truth.

---

## Where this comes from

- Tier policy: [docs/confidence/band_reliability_rollout_plan.md](../confidence/band_reliability_rollout_plan.md)
- Joint conf + beam-agreement band rule design: [docs/confidence/confidence_shape_and_beam_disagree_design.md](../confidence/confidence_shape_and_beam_disagree_design.md)
- Lessons learned (why the rule was changed): [docs/confidence/lessons_learned_band_rule_v2.md](../confidence/lessons_learned_band_rule_v2.md)
- Calibration numbers (NIV-stratified): [docs/confidence/band_reliability_by_niv.md](../confidence/band_reliability_by_niv.md)
- Calibration numbers (segment-mean-prob-stratified): [docs/confidence/band_reliability_by_segment_quality.csv](../confidence/band_reliability_by_segment_quality.csv)
- Implementation: [VSP-LLM/scripts/make_report.py:110-205](../../VSP-LLM/scripts/make_report.py#L110-L205) (tier classification, CSS, legend)
- Container sync entry: [docs/container-sync-changelog.md](../container-sync-changelog.md) entry #29 (joint rule shipping) and #30 (MBR as default displayed output).

---

## Retroactive application — applying the joint rule to past videos

If you have transcripts on disk that were generated before May 2 2026 (or with the conf-only band rule), you can regenerate the reports under the joint rule **without re-decoding**. The decode-time sidecars (`hypo-{fid}.json`, `confidence-{fid}.json`, `nbest-{fid}.json` if `VSP_NBEST=1` was set) are sufficient.

The fast path: re-run stage 8 only — no re-decode, no re-segmentation. From a typical `outputs/<run-id>/` directory:

```bash
# EC2:
cd /home/ubuntu
source lib/outputs.sh
run_outputs   /path/to/outputs/<run-id>/decode_dir   /path/to/outputs/<run-id>/report

# Container:
cd /workspace
source lib/outputs.sh
run_outputs   /path/to/outputs/<run-id>/decode_dir   /path/to/outputs/<run-id>/report
```

If the prior decode was run **without** `VSP_NBEST=1`, no `nbest-{fid}.json` exists and the joint rule cannot be computed retroactively — the pipeline will silently fall back to the conf-only rule. To upgrade those segments, re-decode with `VSP_NBEST=1`. (Decoding is the expensive step; aggregation and report generation are minutes.)

To bulk-regenerate all archived reports under a single root:

```bash
for run in /path/to/outputs/*/; do
  decode="$run/decode_dir"
  report="$run/report"
  [ -d "$decode" ] && [ -d "$report" ] || continue
  echo "Regenerating $run ..."
  ( source /home/ubuntu/lib/outputs.sh && run_outputs "$decode" "$report" ) || echo "  failed: $run"
done
```

This same approach applies to MBR shipping (`hyp_mbr` as the displayed hyp) — re-running stage 8 picks up both the joint band rule **and** the MBR-default output, so a single retroactive pass aligns past videos with the current production behavior.
