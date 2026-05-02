# Lessons Learned — Band Rule v2 (Joint Conf + Beam Agreement)

**Date:** 2026-05-02
**Subject:** How the per-word confidence band rule was redesigned from a single-threshold (top-1 softmax ≥ 0.85) to a joint (top-1 × beam-agreement) gate, what we tried that didn't work, and what the data forced us to drop.

**Companion docs.**

- [confidence_shape_and_beam_disagree_design.md](confidence_shape_and_beam_disagree_design.md) — final design doc, fitted thresholds, implementation plan.
- [TRUST_DIAGNOSTIC.md](../../english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md) — empirical pass tests on the full 1,497-segment set.
- [threshold_design.md](threshold_design.md) — original 0.85 / 0.40 single-threshold rationale (now superseded for the green band; retained as the fallback when no agreement sidecar is available).
- [band_reliability_rollout_plan.md](band_reliability_rollout_plan.md) — three-tier (Trust / Salvage / Strip) UI policy; orthogonal to the band rule, both layers stay.

This doc is the narrative behind the change. Read it 6 months from now if you are wondering "why didn't we just keep the 0.85 threshold?" or "why did we drop the POS-aware idea?"

---

## 1. Setup — what triggered the work

Mission 6 (n-best aggregation) shipped in May 2026 with the headline
result that `hyp_vote_conf` reduced WER by ~2pp on the full set vs.
top-1. As a side-finding, the per-method calibration analysis surfaced
something uncomfortable: **inside the trust regime
(`sentence_confidence ≥ 0.85`), Pearson r between confidence and
content-word correctness was −0.020.** Effectively zero.

That was the trigger. Confidence at the segment level still works
(IS / WER stratification by `sentence_confidence` is monotonic with
healthy slope), but **inside the regime where we already paint words
green, the per-word softmax was no longer carrying word-level signal.**
A user pointing at a green word in a high-confidence segment was being
told something the model couldn't actually back up.

The earlier band-reliability rollout (March-May 2026) had already
produced the *segment-level* fix: the three-tier (Trust / Salvage /
Strip) policy keyed on `sentence_confidence`, which strips coloring
entirely below 0.65 because green leakage exceeds 50% there. That
fixed the worst case (green words in obviously-bad segments). It did
**not** fix the residual case: green words in a segment that itself
looks fine, but where the specific word is wrong.

The "billion → million" cell, the "1024 → 24" cell, the "2011 → 2000"
cell — all of these sit inside Trust-tier segments, painted green,
~96% softmax. They were the unsolved problem.

---

## 2. The first proposal — three legs

The first version of the proposal had **three legs**:

1. **Confidence trajectory shape clustering.** Cluster the
   per-position confidence trajectory (the sequence of softmax values
   across a segment) into archetypes — flat-high, U-shape (peak at
   start and end), valley (drop in the middle), monotonic-decline.
   Use the cluster label as an extra signal alongside the band rule.

2. **POS-aware thresholds.** Function words (the, of, and, is, was)
   have higher language-prior support, so the same 0.85 softmax means
   more for them. Content words (proper nouns, numbers, rare verbs)
   are where the model has thin signal. Split the green threshold:
   T_function ≈ 0.82, T_content ≈ 0.95.

3. **Beam-agreement.** Use the 19 alternative beams from the all-beams
   sidecar (Mission 6) — count what fraction of beams chose the same
   word at the same position — as a second confidence axis.

The placeholder thresholds I proposed: **green = top1_conf ≥ 0.95 AND
beam_agreement ≥ 0.82, yellow = … AND ≥ 0.60.** These were
*hand-picked* round numbers, not fitted to data. I flagged them as
placeholders but moved forward with the design as if they were
meaningful.

This was the first mistake.

---

## 3. Pushback — "is this actually useful?"

The user's response (paraphrased): trajectory shape feels redundant
with the existing segment-mean gate (which strips coloring below 0.65).
And the 0.95 / 0.82 thresholds were obviously hand-picked. *Is the
threshold idea even useful, or are we re-implementing the segment gate
under a different name?*

This was the right question. The honest answer was: I didn't know.
I had proposed three legs in parallel and pretended each pulled its
own weight. I needed to **check the data before committing to any
of them.**

---

## 4. The trust check — diagnostic before implementation

The fix was to write a small diagnostic script
([`diagnose_confidence_signals.py`](../_research-tools/generators/diagnose_confidence_signals.py))
that answered three concrete questions on the full set, with explicit
pass/fail criteria, *before* writing any production code.

Three pass criteria:

| Test | Question | Pass criterion |
|---|---|---|
| A — Independence | Are top1_conf and beam_agreement redundant? | Pearson r within content < 0.85 |
| B — Reliability curve | Can we fit POS-aware thresholds at P(correct) ≥ 0.85? | A bin exists with P ≥ 0.85 and n ≥ 50 |
| C — 2D rescue | Does beam-agreement add lift in the high-conf regime? | ≥ 15pp P(correct) lift, n ≥ 30 in each cell |

The script ran in ~1 minute on the full set (16,367 words above the
seg_mean ≥ 0.65 gate; function: 8,914, content: 7,297).

The lesson here, stated plainly: **trust-check before implementation
is non-negotiable for any policy change.** A 1-minute diagnostic
saved a day of writing code that would have shipped two of the three
legs as no-ops.

---

## 5. What the data said vs what we expected

The trust diagnostic returned a result that was substantially
different from the proposal. The honest comparison:

| Idea | Expected | Reality | Decision |
|---|---|---|---|
| Trajectory shape | Adds a third axis the segment gate misses | Largely redundant with segment mean (the outer Trust/Salvage/Strip already does the work) | **Dropped** |
| POS-aware thresholds | Headline lever — function vs content split moves the cuts | Curves nearly identical at high-P targets (T_function = 0.98 = T_content); the gap (~13pp) is in the 0.75–0.82 mid range that doesn't touch green | **Dropped as a headline** |
| Beam agreement | Supplementary tie-breaker | **+53pp lift** between (high-conf, high-agree) and (high-conf, low-agree). Roughly 2× more informative than top-1 conf at high conf. | **Ship — dominant signal** |
| 0.95 / 0.82 placeholder cuts | Roughly right | T_GREEN_CONF = 0.95 confirmed; the bigger lever was the agreement axis nobody had been using | **Refit from data, not from intuition** |

### 5.1 The headline number

P(correct | conf ≥ 0.95 ∧ agree ≥ 0.95) − P(correct | conf ≥ 0.95 ∧ agree < 0.50) = **+53.09pp** (n_hh=2783, n_hl=42).

Same model, same conf number, same word position, same segment
quality. The only difference is whether the other 19 beams supported
the choice. That delta is what the diagnostic killed two of the three
legs to expose.

### 5.2 The 2D content-word reliability table (Test C)

| top1_conf \ agree | 0.00+ | 0.50+ | 0.80+ | 0.95+ |
|---|---|---|---|---|
| **0.00+** | 0.14 (n=749) | 0.29 (n=551) | 0.32 (n=314) | 0.39 (n=510) |
| **0.65+** | 0.19 (n=83) | 0.38 (n=164) | 0.53 (n=204) | 0.57 (n=367) |
| **0.82+** | 0.26 (n=43) | 0.44 (n=71) | 0.64 (n=118) | 0.71 (n=328) |
| **0.90+** | 0.11 (n=27) | 0.47 (n=51) | 0.67 (n=103) | 0.77 (n=453) |
| **0.95+** | 0.40 (n=42) | 0.73 (n=70) | 0.84 (n=266) | 0.94 (n=2783) |

Read along the diagonal — this is the rule we're going to ship.

### 5.3 POS reliability — why we dropped it

| conf bin | P(correct) function | P(correct) content | Δ |
|---|---|---|---|
| 0.65 – 0.75 | 0.493 | 0.464 | +3pp |
| 0.75 – 0.82 | 0.642 | 0.511 | **+13pp** |
| 0.82 – 0.89 | 0.707 | 0.633 | +7pp |
| 0.89 – 0.95 | 0.748 | 0.692 | +6pp |
| 0.95 – 0.98 | 0.848 | 0.848 | 0pp |
| 0.98 – 1.00 | 0.936 | 0.937 | 0pp |

The POS gap is a real effect — but it is concentrated in the mid-conf
range (0.75–0.82) and **converges at 0pp by the green-band threshold.**
At any practical green-tier cut, splitting by POS does nothing. So we
don't.

### 5.4 The redundancy admission

The user was right that trajectory shape was redundant with the
segment-mean gate. The segment mean already captures most of what
trajectory clustering would have surfaced — flat-high segments are the
high-mean ones; valley segments are the mid-mean ones; monotonic
decline shows up in the mid-low band. Adding "trajectory shape" as a
third axis would have been a re-implementation of the outer tier
under a different name.

---

## 6. The bin-edge bug — diagnostic code can lie

First run of the diagnostic returned **FAIL** on Test C. The reported
high-conf-low-agree cell P(correct) was suspiciously low and the
sample count looked off. The pass criterion (≥15pp lift, n≥30 in each
cell) was being applied against a corrupted contingency table.

Root cause: a bin-handling bug in `diagnose_confidence_signals.py`
itself — the bin edges for the agreement axis were not aligned with
the cell-comparison logic. Cells were being collapsed across bin
boundaries inconsistently between the table renderer and the
pass-criteria evaluator.

Lesson: **even diagnostic code can lie.** Sanity-check the rendered
output table against the pass-criteria logic *manually* on at least
one cell. The fix here was to render the contingency table to
markdown, eyeball one cell (high-conf-high-agree, where we expected
~95% by intuition), and notice the number didn't match the
pass-criteria claim.

After fixing the bin alignment, Test C returned PASS with the +53pp
lift documented above.

The deeper lesson: **don't ship diagnostic results without verifying
the diagnostic.** A failing diagnostic that tells you to drop the
right idea (beam agreement) is worse than no diagnostic at all.

---

## 7. What changed in the design

The final rule, after the diagnostic landed:

```
def render_band(top1_conf, beam_agreement, segment_mean_conf, is_numeric):
    if segment_mean_conf < 0.65:
        return "strip"            # outer tier — unchanged
    if is_numeric:
        return "uncertain_styled" # never green — lip-reading can't disambiguate digits
    if top1_conf >= 0.95 and beam_agreement >= 0.80:
        return "green"            # P ≈ 0.85–0.94 empirically
    if top1_conf >= 0.65 and beam_agreement >= 0.50:
        return "yellow"           # P ≈ 0.40–0.80
    return "red"
```

What's gone vs the first proposal:

- POS split — **dropped**. Curves converge at the relevant operating point.
- Trajectory shape clustering — **dropped**. Redundant with the segment-mean gate.
- 0.82 conf threshold for green — **revised to 0.95**. Empirically fitted.
- 0.82 placeholder agreement threshold — **revised to 0.80**. Empirically fitted.
- Beam-agreement as supplementary tie-breaker — **promoted to the dominant axis**.

What's new:

- Numeric token clamp. Independent of conf and agreement, any token
  containing a digit or matching a number-word is rendered with
  explicit "visually unreliable" styling (never green). Lip-reading
  cannot disambiguate digits — the model's softmax there is never
  trustworthy regardless of value.

What's preserved:

- The segment-level Trust / Salvage / Strip gate (outer tier) is
  unchanged. The new rule operates *within* a tier-rendered segment.
- The 0.85 / 0.40 single-threshold rule remains the **fallback** when
  the agreement sidecar is missing — old reports continue to render
  with the old rule until they're regenerated.

---

## 8. Coverage — what the new rule costs us

The new rule is **stricter than the old** rule. Approximate coverage
counted across the full set (16,367 words, seg_mean ≥ 0.65):

| Band | Old rule (conf-only) | New rule (conf × agree) | Δ coverage |
|---|---|---|---|
| Green | ~60% | ~40% | **−20pp** |
| Yellow | ~25% | ~30% | +5pp |
| Red / strip | ~15% | ~30% | +15pp |

We lose ~20pp of green UI surface. **In exchange we eliminate the
known-unreliable subset** (the high-conf-low-agree cell that drove the
"billion → million" failures). Old greens were a mix of ~85% reliable
and ~40% reliable cells; new greens are uniformly 85–94% reliable.

The user's direction here was clear: prefer 85%+ uniform reliability
over more "green" UI surface that misleads. A green word that is
right 85% of the time is something a user can build trust on. A green
word that is right 40% of the time poisons the user's trust in every
other green word in the report.

---

## 9. Lessons

A short list of takeaways for future work on this pipeline.

1. **Trust-check before implementation is non-negotiable.** A 1-minute
   diagnostic with explicit pass/fail criteria saved a day of writing
   code that would have shipped two no-op legs. Whenever a proposal
   has multiple "axes" or "legs," fit each one against the data
   *before* coding any of them.

2. **Hand-picked thresholds are placeholders.** The 0.95 / 0.82
   placeholder values from the first proposal were one round number
   away from the real fitted values. They could just as easily have
   been one round number off, and shipped with a 5pp coverage error.
   Always fit thresholds from data — even if the fitted value lands
   on a round number.

3. **Reliability curves are the right framing.** Pearson r between
   confidence and correctness, on its own, masked the behavior. The
   reliability curve (P(correct) per bin) showed the same data in a
   form that made the right decision obvious. When two metrics
   disagree about whether a signal is useful, prefer the one that's
   actionable.

4. **Beam search produces "for free" signals we routinely throw
   away.** The 19 alternative beams sit in `nbest-{id}.json` after
   every decode. We had been discarding them and reporting only the
   top-1 confidence. Mission 6 captured them for ROVER / MBR; this
   work uses them as a second confidence axis. The lesson is more
   general: any signal the decoder produces "for free" deserves to be
   audited before it's discarded.

5. **When two signals are correlated but not co-linear, both are
   worth keeping.** Top-1 conf and beam-agreement have Pearson
   r = 0.58 within content words. That's high enough to look
   redundant on a scatter plot but low enough that joining them
   yields a 2D contingency table with cells the marginal cuts can't
   reach. The independence test (Test A) was the lever that let us
   keep both.

6. **Confident-hallucination cells are real and isolatable.** A model
   can be 95% confident *and* the other 19 beams disagreed. That
   cell exists, it's small (~1.5% of words), and it's where the
   worst user-facing failures live (`gonna→going`,
   `billion→million`, `1024→24`). Identifying and styling that cell
   distinctly is a UI win we couldn't have made with top-1 alone.

7. **Be willing to drop legs of a proposal that the data doesn't
   support.** I proposed three legs; the data killed two. The
   instinct to "ship all three because we already wrote the design"
   is wrong. Smaller, cleaner rules are better than feature-rich
   rules with marginal-effect components.

8. **The user's intuition that "shape is redundant" was right.** Worth
   stating as a structured lesson rather than a footnote: the user
   raised the concern that trajectory clustering would reproduce the
   segment-mean gate under a different name. The diagnostic confirmed
   it. **When the user pushes back on a leg of a proposal as
   redundant, that pushback is data — treat it as a hypothesis to
   test before the next code commit.**

9. **Diagnostic code can lie too.** The bin-edge bug in
   `diagnose_confidence_signals.py` initially returned FAIL on Test C.
   We almost dropped beam agreement on the basis of a buggy
   diagnostic. Sanity-check the rendered table against the
   pass-criteria logic, on at least one cell, every time.

10. **Document what's a maintenance burden vs what's a feature.** The
    fitted thresholds (0.95 / 0.80 / 0.65 / 0.50) are specific to
    Llama-2-7b at the current beam config. Any LLM swap forces a
    re-run of `diagnose_confidence_signals.py`. That's a maintenance
    burden the team owns going forward; documenting it explicitly in
    [confidence_shape_and_beam_disagree_design.md](confidence_shape_and_beam_disagree_design.md)
    §5 prevents the next engineer from treating the cuts as immutable
    constants.

---

## 10. Open questions left for the next round

These were flagged in the design doc and remain open:

- **Coverage vs precision tradeoff.** New rule drops green coverage
  from ~60% to ~40%. Worth re-validating against client feedback once
  the new bands ship — does the tighter green earn enough trust to
  offset the smaller surface?
- **Numeric styling.** Should the "uncertain styled" rendering for
  numbers be visually distinct (italic + grey) or just yellow-tier?
  Affects the design system; not a data question.
- **Backward compatibility.** Old reports were generated with the
  conf-only rule. Do we need to regenerate them for clients, or is
  the new rule applied only to new runs? Ops decision, not a
  research one.
- **Calibration via temperature scaling.** Llama-2-7b is mildly
  over-confident overall; temperature scaling would shift all bins
  together. Orthogonal to the agreement rule but worth a separate
  sprint once the new bands have been in production for a few weeks.

---

## 11. TL;DR for future readers

We thought POS and trajectory shape would matter. The data said they
don't, at the operating point that touches the green band. Beam
agreement, which we'd been throwing away, turned out to be twice as
informative as top-1 confidence at high confidence. The new rule is
simpler than the proposal (two axes instead of four), strictly more
reliable than the old rule (uniform 85%+ green vs mixed 40%/85%
green), and was delivered by a 1-minute trust-check before any
production code was written.

The single most important habit this exercise reinforced: **run the
diagnostic before you write the implementation.**

---

## 12. Post-shipment safety analysis (May 2 2026, full set)

After landing, we measured each band's empirical reliability under
both rules across all 23,261 words and 1,497 segments. Source data
in [SAFETY_ANALYSIS.md](../../english_full_nbest_eval/safety_analysis/SAFETY_ANALYSIS.md); generator at [analyze_band_safety.py](../_research-tools/generators/analyze_band_safety.py).

### Per-word

| Band | Old n / P(correct) | New n / P(correct) | ΔP |
|---|---|---|---|
| Green | 11,309 / **0.806** | 7,591 / **0.898** | **+9.2pp** |
| Yellow | 7,470 / 0.383 | 6,571 / 0.590 | **+20.7pp** |
| Red | 4,482 / 0.154 | 9,099 / 0.217 | +6.3pp |

The green improvement (+9.2pp) was the design target. The yellow improvement (+20.7pp) was a free win — under the old rule yellow was a wide 0.40–0.85 band that mixed signal and noise; the new yellow requires both `conf ≥ 0.65` *and* `agree ≥ 0.50`, which filters out the lowest-quality middle without re-tuning thresholds.

### Tier-stratified

| Tier | Old green P | New green P |
|---|---|---|
| Trust (seg_mean ≥ 0.82) | 0.924 | 0.953 |
| Salvage (0.65–0.82) | 0.798 | **0.891** |

The biggest reliability boost happens in Salvage segments — exactly where users were most exposed under the old single-threshold rule. Trust segments were already in good shape; the new rule mostly maintains them.

### POS reversal

Old rule: function green P=0.806, content green P=0.809 (tied). New rule: function P=0.894, content P=**0.904**. Content green is now slightly *more* reliable than function — the agreement gate removed the confident-hallucination content cell that was the whole motivation for the work.

### Numeric tokens — and why the hard cap is justified

Under the new rule **0 numbers are ever painted green** (vs 75 under the old rule, P=0.693). The hard cap was originally proposed on intuition ("lip-reading can't disambiguate digits"). Post-shipment, we tested whether the cap is justified empirically — i.e., do numbers that *would* meet the joint green criteria actually deliver the green-band promise?

| Numbers passing joint green criteria | n | P(correct) |
|---|---|---|
| conf ≥ 0.95 AND agree ≥ 0.80 (proposed green) | 39 | **0.744** |
| conf ≥ 0.95 AND agree ≥ 0.95 (strictest cell) | 31 | 0.742 |
| Content words at same threshold (reference) | 3,272 | 0.904 |
| Green-band promise | — | ≥ 0.85 |

Even at the strictest joint cell, numbers hit only ~74% reliability — 16pp behind content words and 11pp below the green-band's reliability promise. The cap is not arbitrary: numbers genuinely fail to clear the bar. They look confident to the model in ways the model's posterior cannot detect. The cap reflects an honest limit of the visual modality, not a UX preference.

### Sentence promise

Stratifying segments by fraction of words painted green under the new rule:

| Green fraction | n segs | P(NIV-Y) | P(hallu) | mean WER |
|---|---|---|---|---|
| 0.00–0.10 | 386 | 0.01 | 0.44 | 96.4% |
| 0.10–0.30 | 411 | 0.06 | 0.14 | 71.3% |
| 0.30–0.50 | 309 | 0.32 | 0.02 | 45.5% |
| 0.50–0.70 | 250 | 0.67 | 0.01 | 28.6% |
| 0.70–0.90 | 66 | 0.88 | 0.00 | 16.8% |
| 0.90–1.00 | 5 | **1.00** | 0.00 | 10.3% |

The 0.70–0.90 band climbs from 0.76 → 0.88 P(NIV-Y) vs the old rule. The 0.00–0.10 band drops its hallucination rate from 0.59 → 0.44 — old rule's bottom band was a thinner slice of cleanly-bad segments; new rule's bottom is broader and less catastrophic on average. Both directions are improvements.

The "≥90% green" cohort is now tiny (5 segments out of 1,427) but unanimously NIV-Y with 10.3% mean WER. A user who only reads mostly-green sentences will see fewer transcripts but the ones they see are reliable.

---

## 13. Client trust calibration — what fraction of useful content does the client actually pick up?

The natural client rule is "trust segments where most words are green." Formalised as "fraction-green ≥ T", this is the operational tradeoff:

| T (green-frac ≥) | Trusted | Useful caught | False positives | Recall | FPR | NIV-Y in trust |
|---|---|---|---|---|---|---|
| **30%** | 630 | 602 | 28 | **65.2%** | 5.6% | 52.5% |
| 50% | 321 | 312 | 9 | 33.8% | 1.8% | 72.0% |
| 70% | 71 | 70 | 1 | 7.6% | 0.2% | 88.7% |
| 90% | 5 | 5 | 0 | 0.5% | 0.0% | 100% |

**Recommended default: ≥ 30% green.** Surfaces 65% of useful content (602 of 924 NIV-Y+P segments) with 5.6% false-positive rate — about 1 misleading transcript per 22 trusted ones.

**Structural ceiling.** 322 useful segments (35% of NIV-Y+P) have green-fraction below 30% even under the new rule — segments where the model produced something useful via thin-agreement / mid-conf words. The band system fundamentally cannot reach them. Recovering them requires a different signal (LLM rerank, topic-conditional prior, semantic-coherence check) — that's the next iteration after this one.

Full analysis: [client_trust_calibration.md](client_trust_calibration.md). Generator: [analyze_client_trust_calibration.py](../_research-tools/generators/analyze_client_trust_calibration.py).
