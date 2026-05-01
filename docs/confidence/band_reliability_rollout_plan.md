# Band Reliability Rollout Plan

**Date opened:** 2026-05-01
**Source finding:** [confidence_full_analysis.md §11](confidence_full_analysis.md#11-two-tier-policy--when-can-the-user-salvage-a-bad-segment-from-the-per-word-coloring)
**Source script:** [`analyze_band_reliability.py`](../_research-tools/generators/analyze_band_reliability.py)
**Backing data:** [`band_reliability_by_segment_quality.csv`](band_reliability_by_segment_quality.csv), [`green_leakage_examples.csv`](green_leakage_examples.csv)

## The change in one paragraph

The green band's promise ("trust this word") only holds when the *segment* it lives in is also high-confidence. Stratified by segment mean_prob, P(correct | green word) ranges from **92.8%** (segments with mean_prob ≥ 0.85) down to **22%** (segments with mean_prob 0.40–0.55) and **18%** (mean_prob < 0.40, n=11). The current pipeline paints uniformly regardless of segment quality — so a user looking at green words in a bad segment is being actively misled. The fix is a **three-tier UI policy** keyed on segment mean_prob, not a flat threshold.

## The three tiers

| Tier | Segment mean_prob | UI | Banner | Volume |
|---|---|---|---|---|
| **Trust** | ≥ 0.82 | Full coloring | (none) | 28% of corpus |
| **Salvage** | 0.65 – 0.82 | Full coloring + uncertainty banner | "Reading carefully — verify names, numbers, critical details" | ~38% of corpus |
| **Strip** | < 0.65 | **Plain grey text — coloring stripped** | "Model is unsure — text may not be reliable, even where it looks confident" | ~34% of corpus |

The "strip below 0.65" line is the genuine UI bug fix. Everything above is graduated trust signaling.

## Why this is not the final answer

These thresholds are tuned to the **current model + current training data**. The green-band leakage in low-confidence segments is a *symptom* of three solvable bottlenecks:

1. **Backbone LLM (LLaMA-2-7B).** LLaMA-2 is mildly over-confident with ECE 5–15pp in the 0.7–0.95 band. Llama-3.1-8B and Llama-3.3-70B have measurably better calibration out of the box. Switching the backbone narrows the gap between "model says 0.95" and "actually 0.95% correct," which raises P(correct | green) uniformly across the segment-quality spectrum.

2. **Training-data scale and domain coverage.** The current LoRA adapter saw ~1,273 AVSpeech segments — below the ~20K needed for stable generalization. Numbers, proper nouns, and domain-specific vocabulary are exactly the tokens where green leakage is highest (see [green_leakage_examples.csv](green_leakage_examples.csv)). With 20K+ segments and curriculum that includes numeric / entity-rich content, the model stops needing to "fall back to a fluent number" when it lacks signal — it has seen enough numeric lip shapes to be honestly uncertain when uncertain.

3. **Beam aggregation (Mission 6).** The current pipeline reports confidence on the *chosen* beam only. Beam disagreement is a powerful out-of-band signal that would catch the "billion → million" failure even when the chosen-beam softmax is high. With all-20-beams capture (planned), we can flag high-prob-but-disagreed tokens and demote them out of the green band before the user sees them.

**Practical upshot:** treat 0.82 / 0.74 / 0.65 as **today's** numbers, not a permanent law. Re-run [`analyze_band_reliability.py`](../_research-tools/generators/analyze_band_reliability.py) after each of these upgrades and shift the policy. Specifically expect:

| Upgrade | Predicted shift in green reliability |
|---|---|
| Backbone → Llama-3.1-8B | P(correct \| green) +3 to +6pp uniformly; T_safe drops toward 0.78 |
| 20K+ AVSpeech segments | P(correct \| green) on numeric/entity tokens +10 to +20pp; "billion → million" class shrinks |
| Beam-disagreement gate | Removes most fluent-latch failures from green; T_strip can drop toward 0.55 |
| Domain-specific finetune (e.g., medical, legal) | T_safe potentially drops to 0.72 *within domain*, rises elsewhere |

The architecture of the policy (three tiers keyed on segment confidence) outlives the specific numbers. The numbers will change as the system improves.

## Rollout — sequenced by blast radius

### Phase 1 — Documentation (low-risk, high-leverage)

Update written artefacts so future work starts from the corrected mental model.

- [x] [`confidence_full_analysis.md`](confidence_full_analysis.md) §11 — primary writeup ✅ done
- [ ] [`threshold_design.md`](threshold_design.md) — add segment-conditional reading of the green band; the "What we do when calibration says we're wrong" table needs the new "P(correct | green) varies by segment quality" row
- [ ] [`report_4_confidence_scoring.md`](report_4_confidence_scoring.md) (and `.docx`/`.pdf`) — add the band-reliability finding as a section near the calibration discussion. Re-export PDF/DOCX after edits
- [ ] [`confidence_full_analysis.tex`](confidence_full_analysis.tex) — mirror §11 in LaTeX, regenerate `.pdf`
- [ ] Add `green_leakage_examples.csv` to the data appendix in `report_4_*.docx`

### Phase 2 — Reporting code (medium risk, requires testing)

Compute and surface the segment-tier classification in the per-segment outputs that already ship.

- [ ] [`VSP-LLM/scripts/make_report.py`](../../VSP-LLM/scripts/make_report.py) — add a `tier` column to `report.csv`: `Trust` / `Salvage` / `Strip` based on `sentence_confidence` (= mean_prob). One enum, three values.
- [ ] [`VSP-LLM/scripts/make_report.py`](../../VSP-LLM/scripts/make_report.py) — when rendering `report.html`:
   - **Trust tier:** existing per-word coloring as today (CONF_HIGH=0.85 / CONF_MED=0.40 unchanged)
   - **Salvage tier:** existing per-word coloring + a coloured banner above the segment row ("Model uncertainty banner")
   - **Strip tier:** render hyp text in plain grey; *do not* apply confidence colors
- [ ] Add a legend entry in `report.html` explaining the three tiers
- [ ] Sync the same change into [`vsp_linux_container_FINAL_20260217/VSP-LLM/scripts/make_report.py`](../../vsp_linux_container_FINAL_20260217/VSP-LLM/scripts/make_report.py) per CLAUDE.md sync rule
- [ ] Update [`docs/container-sync-changelog.md`](../container-sync-changelog.md) with the diff
- [ ] Re-run pipeline on a small sample (10 segments spanning the three tiers) to verify rendering

### Phase 3 — UI (medium risk, user-visible)

Reflect the three-tier view in the live UI so end-users see the right thing.

- [ ] [`vsp-ui/app/static/`](../../vsp-ui/app/static/) — add CSS class for the salvage banner and a "stripped" segment style (plain grey, no confidence colors applied)
- [ ] [`vsp-ui/app/services/`](../../vsp-ui/app/services/) — Python service that reads `report.csv`, attaches the `tier` field, and emits per-segment HTML conditioned on tier
- [ ] Verify on a real run: take an end-to-end pipeline output and inspect a Trust, Salvage, and Strip segment side-by-side in the browser

### Phase 4 — Slides / decks (visible to clients)

The current confidence slide pitches a *single* per-word coloring promise. Update it to show graduated trust.

- [ ] Beamer presentation — add one slide after the existing confidence reliability slide showing the band-reliability-by-segment-quality plot (the same `conf_band_reliability_combined.png` we generated)
- [ ] PPTX presentation — same addition
- [ ] Client deck (April 2026) — soften the per-word coloring framing to mention the segment-confidence dependency; if not enough room, drop to one footnote
- [ ] Add a slide note: "This will change with better LLM / more domain data / beam aggregation — these thresholds are not permanent."

### Phase 5 — Memory & lessons (lightweight, persistent)

So future work doesn't relitigate this.

- [x] `MEMORY.md` topic file: `band_reliability_lesson.md` ✅ added in this changeset
- [x] `lessons-learned-doc-generation.md`: add the asymmetric-cost section ✅ added in this changeset
- [x] `MEMORY.md` key numbers: add P(correct | green, bucket) and the three thresholds ✅ added in this changeset

## What changes if we rollback or skip

| If we skip... | Cost |
|---|---|
| Phase 1 (docs) | Future Claude / future engineer makes the same wrong recommendation as Section 10's first draft; "0.82 segment threshold = good enough" gets repeated in client decks |
| Phase 2 (report.csv tier column) | UI work in Phase 3 has no data to key on; we either re-derive the tier in JS or do nothing. Cost: high. **Phase 2 is the load-bearing change** |
| Phase 3 (UI) | The end-user sees green words on bad segments and may be misled — the original problem persists |
| Phase 4 (slides) | Client meetings continue claiming "green = trust, period." When a sharp client points to a green-but-wrong word in a bad segment, we have no story. |
| Phase 5 (memory) | Future tuning passes don't know to stratify by segment quality; we lose this learning |

## Owner suggestions

| Phase | Suggested owner | ETA |
|---|---|---|
| 1 (docs) | Whoever next opens a confidence report | 1 day |
| 2 (make_report.py) | Pipeline engineer; touches both EC2 + container sync | 2-3 days |
| 3 (UI) | UI-side engineer; depends on Phase 2 | 3-5 days |
| 4 (slides) | Whoever runs the next client meeting | 1-2 days |
| 5 (memory) | This changeset | done |

## Re-validation cadence

Re-run [`analyze_band_reliability.py`](../_research-tools/generators/analyze_band_reliability.py) and refresh the thresholds:

- After every backbone LLM swap (Llama-2 → Llama-3.x → ...)
- After every fine-tuning round that touches the visual encoder or LoRA adapter
- After Mission 6 (beam aggregation) lands — beam disagreement may move T_strip lower
- Quarterly during steady state, against the latest full-dataset decode

If P(correct | green, very-low-bucket) ever rises above 50% after a model upgrade, **revisit the strip-coloring boundary** — the user can probably tolerate coloring at lower segment confidence than 0.65 with the new model.

## Summary

A five-line change to [`make_report.py`](../../VSP-LLM/scripts/make_report.py) and a CSS class in the UI implement the most important part. The doc updates are book-keeping. **The numerical thresholds will move with the model**; the policy structure is permanent.
