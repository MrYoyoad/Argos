# Beam-Agreement Aware Confidence Bands — Design

**Purpose.** Replace the current single-threshold per-word confidence policy with a two-signal rule that uses **top-1 confidence × beam-agreement** at each position. Validated empirically on the full 1,497-segment evaluation.

**Status.** Trust-check passed (May 2 2026, see [trust diagnostic](../../english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md)). Implementation is the next step.

**Companion docs.**
- [confidence_followups.md](confidence_followups.md) §4 — original "use all 20 beams" idea, now ready to ship.
- [threshold_design.md](threshold_design.md) — original three-tier band design that this proposal augments.
- [band_reliability_lesson.md](../../.claude/projects/-home-ubuntu/memory/band_reliability_lesson.md) — segment-level reliability stratification, retained as the outer gate.
- [docs/beam-search/n_best_implementation.md](../beam-search/n_best_implementation.md) — full-set finding that motivated the trust check.

---

## 1. What changed from the first draft

The first version of this proposal had three legs: confidence trajectory shape clustering, POS-aware thresholds, and beam-agreement. The trust diagnostic killed two of them and validated the third:

| Idea | Diagnostic result | Decision |
|---|---|---|
| Trajectory shape clustering | Largely redundant with segment mean (pre-existing band gate) | **Dropped** — segment mean already covers this |
| POS-aware (function vs content split) thresholds | Reliability curves nearly identical at high-P targets (T = 0.98 for both) | **Dropped as a headline** — small effect at the relevant operating point |
| Beam agreement as a second axis | **+53pp** P(correct) lift in the high-conf regime | **Ship** |

The simpler conclusion is the right one: **beam agreement is the dominant signal we haven't been using.** It does most of the work; everything else is gilding.

---

## 2. Evidence (full set, 1,497 segs, 16,367 words above seg_mean ≥ 0.65)

### 2.1 The two signals are not redundant

Pearson r between top1_conf and beam_agreement: **+0.58 overall, +0.60 within content, +0.55 within function.** Correlated, but not co-linear — adding agreement is genuinely two-dimensional.

### 2.2 Beam agreement carries more lift than top-1 conf

Reading the 2D content-word reliability table along the *vertical* axis (raise conf, fix agreement column) versus the *horizontal* axis (raise agreement, fix conf row):

| Move | P(correct) change | Direction |
|---|---|---|
| Raise conf 0.65 → 0.95 at agree<0.5 | 0.19 → 0.40 (+21pp) | small |
| Raise agree 0+ → 0.95 at conf 0+ | 0.14 → 0.39 (+25pp) | similar |
| Raise conf 0.65 → 0.95 at agree ≥ 0.95 | 0.57 → 0.94 (**+37pp**) | strong |
| Raise agree 0+ → 0.95 at conf ≥ 0.95 | 0.40 → 0.94 (**+54pp**) | **dominant** |

Within the high-confidence regime where users currently see green coloring, **agreement is roughly twice as informative as confidence**. A word with conf 0.65 + agree ≥ 0.95 (P=0.57) is *more reliable* than a word with conf ≥ 0.95 + agree < 0.50 (P=0.40).

### 2.3 The confident-hallucination cell is real and large

Content-word cell at top1_conf ≥ 0.95 *and* agreement < 0.50: **P(correct) = 0.40** (n=42). Same conf row at agreement ≥ 0.95: **P(correct) = 0.94** (n=2783). Same model, same conf number, same word position — the only difference is whether the other 19 beams supported the choice.

This is the `gonna → going` cell, the `billion → million` cell, the `1024 → 24` cell. All of them sit here.

### 2.4 POS-awareness is a smaller effect than expected

Comparing function vs content reliability curves at the same conf bins:

| conf bin | P(correct) function | P(correct) content | Δ |
|---|---|---|---|
| 0.65 – 0.75 | 0.493 | 0.464 | +3pp |
| 0.75 – 0.82 | 0.642 | 0.511 | **+13pp** |
| 0.82 – 0.89 | 0.707 | 0.633 | +7pp |
| 0.89 – 0.95 | 0.748 | 0.692 | +6pp |
| 0.95 – 0.98 | 0.848 | 0.848 | 0pp |
| 0.98 – 1.00 | 0.936 | 0.937 | 0pp |

POS difference exists but is concentrated in the mid-conf range and converges at high conf. At any practical green-tier threshold (≥ 0.95), **POS doesn't matter.** Skip it.

---

## 3. The rule

### 3.1 Production band logic

```
def render_band(top1_conf, beam_agreement, segment_mean_conf, is_numeric):
    # Outer gate: segment-level (unchanged from current band policy)
    if segment_mean_conf < 0.65:
        return "strip"

    # Hard rule: lip-reading cannot disambiguate digits
    if is_numeric:
        return "uncertain_styled"  # never green

    # Joint confidence + agreement rule
    if top1_conf >= 0.95 and beam_agreement >= 0.80:
        return "green"        # P(correct) ≈ 0.84-0.94 empirically
    if top1_conf >= 0.65 and beam_agreement >= 0.50:
        return "yellow"       # P(correct) ≈ 0.38-0.84 — "could be right"
    return "red"              # remaining cells
```

### 3.2 Coverage and reliability the rule would deliver

Counted across the full set (16,367 words, seg_mean ≥ 0.65):

| Band | Cells matched (content + function) | Approx P(correct) | Approx % of words |
|---|---|---|---|
| Green | conf ≥ 0.95 ∧ agree ≥ 0.80 | ~0.85–0.94 | ~40% |
| Yellow | conf ≥ 0.65 ∧ agree ≥ 0.50 (and not green) | ~0.40–0.80 | ~30% |
| Red / strip | rest | <0.40 | ~30% |

Compare current rule (conf ≥ 0.82 → green, no agreement check): green coverage ~60%, but ~25-30% of those greens are actually unreliable (the high-conf-low-agree cells). The new rule **drops green coverage by ~20pp but eliminates the unreliable subset.**

### 3.3 Numeric token rule

Independent of conf and agreement: any token containing a digit, or matching one of `{zero, one, two, ..., twenty, thirty, ..., hundred, thousand, million, billion, ...}`, is rendered with explicit "visually unreliable" styling. The full-set finding showed digits (`7`, `8`) and digit-words (`x`, `d`) hit 0% recall — lip-reading cannot disambiguate them, so the model's confidence is never trustworthy regardless of value.

---

## 4. Implementation plan

Three changes, in this order:

### 4.1 Build the per-word agreement signal (new script, ~1 hour)

**Script.** [`compute_word_agreement.py`](../_research-tools/generators/compute_word_agreement.py) (to be written).

Inputs: `nbest-{id}.json`, `confidence-{id}.json`, `hypo-{id}.json`.
Output: per-word table (utt_id, position, word, top1_conf, beam_agreement, is_numeric).

Reuses the same alignment logic as [diagnose_confidence_signals.py](../_research-tools/generators/diagnose_confidence_signals.py) — runtime ~1 minute on the full set.

### 4.2 Update the band rendering function (~1 hour)

**File to edit.** Whichever module owns `render_band` / band coloring in the report generator. The diagnostic table is the source-of-truth for the threshold values; pull them in as named constants:

```python
# Empirically fitted on 1,497-segment full set, May 2 2026.
# Source: english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md
T_GREEN_CONF = 0.95
T_GREEN_AGREE = 0.80
T_YELLOW_CONF = 0.65
T_YELLOW_AGREE = 0.50
T_SEGMENT_GATE = 0.65  # unchanged
```

### 4.3 Wire agreement through the existing pipeline (~1-2 hours)

The pipeline stages that produce the report currently consume `confidence-*.json` (per-word top-1 conf). They need access to the per-word agreement signal. Two options:

- **Option A** — emit `agreement-*.json` alongside `confidence-*.json` from §4.1's script as a sidecar. Report generator joins on `(utt_id, position)`.
- **Option B** — extend `confidence-*.json` schema to carry `beam_agreement` per token. More invasive, breaks file-format compatibility.

**Recommendation: Option A.** Strictly additive, doesn't touch decode-side code, easy to roll back.

### 4.4 Total scope

| Task | LOC | Time |
|---|---|---|
| §4.1 compute_word_agreement.py | ~150 | 1h |
| §4.2 band rule update | ~30 | 1h (incl. tests) |
| §4.3 wire sidecar through report generator | ~50 | 1-2h |
| Validation re-run on full set | — | 30min |
| **Total** | **~230** | **3-4 hours** |

---

## 5. What this does not address (and why that's OK)

- **Confidence trajectory shape** — segment mean already gates the policy at 0.65, which captures most of what shape clustering would have. Skip until evidence demands it.
- **POS-awareness** — converges with the joint rule at high reliability targets. Skip until evidence demands it.
- **Calibration via temperature scaling** — separate problem. The Llama-2 backbone is mildly over-confident overall; temperature scaling would shift all bins together. Orthogonal to the agreement rule. Worth a separate sprint.
- **Threshold drift across LLM swaps** — any thresholds we fit are specific to Llama-2-7b at the current beam config. A future LLM swap forces a re-fit. Document this as a maintenance burden, not a blocker.

---

## 6. Trust diagnostic — replication recipe

To re-validate any time the model, decoder, or beam config changes:

```bash
source vsp-llm-yoad-venv/bin/activate
python3 docs/_research-tools/generators/diagnose_confidence_signals.py \
  --nbest <run>/decode_output/nbest-*.json \
  --hypo  <run>/decode_output/hypo-*.json \
  --confidence <run>/decode_output/confidence-*.json \
  --out-dir <run>/trust_diagnostic
```

Pass criteria:
- A. r(top1_conf, beam_agreement) within content < 0.85 (independence).
- B. Content reliability curve fits at P ≥ 0.85 with n ≥ 50.
- C. P(correct) lift between (high-conf, high-agree) and (high-conf, low-agree) cells ≥ 15pp, with n ≥ 30 in each.

If any test fails on a new run, the threshold values must be re-fitted before shipping.

---

## 7. Open questions for the user before implementation

1. **Coverage vs precision tradeoff.** New rule drops green coverage from ~60% to ~40%. Is 85%+ uniform reliability worth losing 20pp of "green" UI surface? (My read: yes — current greens include a known-unreliable subset that misleads users. But this is your call.)
2. **Numeric handling.** Should the "uncertain styled" rendering for numbers be visually distinct (e.g. italic + grey) or just yellow-tier? Affects the design system.
3. **Backward compatibility.** Old reports were generated with the conf-only rule. Do we need to regenerate them, or is the new rule applied only to new runs?
