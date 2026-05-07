# After-AMOSI Deck — Logic Fix Manifest

**Companion to:** [after_amosi_logic_audit.md](after_amosi_logic_audit.md)
**Date:** 2026-05-07
**Scope:** edits to existing slide text only (no new slides) unless flagged as adding a CRITICAL caveat.
**Severity:** `CRITICAL` (factually wrong) > `MAJOR` (misleading) > `MINOR` (missing caveat) > `STYLE` (tightening).
**Citations:** every fix below cites the source-of-truth doc whose text the slide is failing to honor.

Group order: §0 / §1 / §2 / §3 / §4 / §5. Within each group, sorted by severity then slide number.

---

## §0 — What was done (slides 2–4)

### Slide 4 (Presentation Overview) — MAJOR — outline-to-content mismatch

**Current text (§3 row):**
> 3. Where the System Works
> Oracle vs Realistic capture • Failure mode taxonomy • MBR n-best aggregation (production default)

**Issue:** "MBR n-best aggregation (production default)" is mapped to §3, but §3 (slides 39–45) actually contains failure-mode taxonomy + LLM salvage; the MBR aggregation slides are 60–62 (in §4). Reader expects §3 to be the MBR section.

**Suggested rewrite:**
> 3. Where the System Works
> Oracle vs Realistic capture (MBR + Trust gate) • Failure mode taxonomy • LLM salvage examples
>
> 4. Confidence Without Ground Truth
> Per-word conf + beam-agreement bands • Trust-gate operating points • MBR n-best aggregation (production default)

**Citation:** structural — slides 36/37/38 are oracle/funnel; slides 39–45 are taxonomy/salvage; slides 60–62 are aggregation.

---

## §1 — The Problem (slides 5–14)

### Slide 11 (The Reality Gap) — MINOR — uncalibrated WER cut in NIV-anchored deck

**Current text:**
> 25.5% Useful by WER (<30%)

**Issue:** WER<30% is uncalibrated; NIV calibrated WER threshold for Y is ≤34% (κ=0.629). Slide 35 references the NIV threshold; slide 11 uses an arbitrary cutoff.

**Suggested rewrite:**
> 25.5% Useful by WER (<30%, uncalibrated bucket — NIV-Y operating point is WER ≤ 34%)

Or simpler — change to NIV: "26.4% Useful by WER ≤ 34% (NIV-Y operating point)"

**Citation:** [docs/evaluation/threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md) §6 — "WER ≤ 34% (NIV-Y), κ=0.629".

### Slide 5 (What is VSP) — MINOR — "near-zero" overstates "<5%"

**Current text (footer):**
> System + human reader outperforms expert lip readers: 55–70% vs 45–52% word accuracy, with near-zero hallucination risk

**Issue:** Source says "<5%" — "near-zero" overstates.

**Suggested rewrite:**
> System + human reader outperforms expert lip readers: 55–70% vs 45–52% word accuracy; hallucination risk drops from 20.5% to under 5% with human filtering.

**Citation:** [docs/evaluation/human_expert_comparison.md](human_expert_comparison.md) §5 — "Hallucination risk: 20.5% (model) → <5% (model + context-aware human)".

---

## §2 — How Do You Evaluate Lip-Reading? (slides 15–36)

### Slide 35 (The Gap: Where WER Lies Most) — CRITICAL — uncalibrated WER threshold quoted

**Current text:**
> • 42 clearly conveyed (IS ≥ 3.80) but WER > 34%
> • 437 useful meaning (IS ≥ 2.00) but WER > 40%

**Issue:** The first bullet uses the NIV-Y WER threshold correctly. The second bullet quotes "WER > 40%" — but the calibrated NIV-Y+P WER threshold is **≤ 77%** (κ=0.777, [threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md) §6.4). 40% is not a calibrated cut, so 437 segments at IS≥2.00 ∩ WER>40% is not a "WER lies" frame at the calibrated operating point.

**Suggested rewrite:**
> • 42 clearly conveyed (IS ≥ 3.80) but WER > 34% (NIV-Y WER cutoff)
> • 85 useful meaning (IS ≥ 2.00) but WER > 77% (NIV-Y+P WER cutoff)

(The "85" count is `IS ≥ 2.00 ∩ WER > 77%` — needs to be re-extracted from the IS distribution; speaker should re-derive before re-rendering.)

**Citation:** [docs/evaluation/threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md) §6 — NIV-Y+P operating point is WER ≤ 77%.

### Slide 36 / 37 / 38 (Oracle vs Realistic / Funnel) — MAJOR — apples-to-oranges denominators

**Current text (slide 38 cards):**
> 63.84% WER (MBR; top-1: 64.05%)
> 61.92% NIV-Y+P (IS ≥ 2.00, MBR)
> 71.08% LLM Judge v3 Y+P (MBR Oracle; baseline 68.40%)
> 65.2% Trust gate ≥30% green • recall of useful, FPR 5.6%

**Issue:** Four cards in a vertical funnel imply progressive refinement. But:
- WER 63.84% is mean-of-segment word edit fraction (denom = 1497 × per-segment).
- NIV-Y+P 61.92% is share of 1497 segments classified useful by IS ≥ 2.00 (denom 1497).
- LLM Judge Y+P 71.08% is share of 1497 verdicts (denom 1497).
- Trust gate 65.2% is **recall of useful content within the 1427 non-empty segments** — a TPR, not a capture rate, and against a smaller denominator.

These are four different metrics; the deck stacks them as if "65.2% Trust gate" is the most refined version of "61.92% NIV-Y+P". A research peer will notice instantly.

**Suggested rewrite:**
- Either re-frame the slide as a TWO-axis comparison: Oracle (left) shows MBR WER + NIV + Judge as three lenses on the same 1497-segment population; Realistic (right) shows the Trust-gate output as a precision/recall trade-off in the per-segment safety frame (n=1427).
- Or add an explicit footer: "Oracle metrics evaluate all 1497 segments; Trust-gate is recall on 1427 non-empty segments."

**Minimum change** (preserving current layout): add a footer line:
> Oracle metrics measure capture across 1497 segments; the Trust-gate metric measures recall within 1427 non-empty segments under the joint conf+agreement rule.

**Citation:** [docs/evaluation/after_amosi_audit.json](after_amosi_audit.json) keys `niv_yp_pct_mbr`, `judge_v3_yp_pct_mbr`, `trustgate_new_t30_recall`, `trustgate_new_t30_n_trusted` (1427) — anomaly note already lives in audit.

### Slide 38 / 70 — MAJOR — v1 baseline (64.9%) and v3 baseline (68.40%) blended without disclosure

**Current text (slide 38):** "LLM Judge v3 Y+P 71.08% (MBR Oracle; baseline 68.40%)"
**Current text (slide 70):** "64.9% useful per Opus-as-a-Judge (Y+P = 971/1,497)"

**Issue:** Both baselines are correct in their own runs:
- v1 blind: Y+P = 64.9% (Opus 4.6, no conf in prompt) — slide 17 / 70.
- v3 dual-conf: Y+P = 68.40% (Opus 4.7, both confs in prompt) — slide 38 / 60 / 88.

Same 1497 segments, but different judge model + different prompt = different verdict rates. The deck never flags that "the LLM Judge" is two different runs.

**Suggested rewrite (slide 38 footer):**
> Card 3 baseline (68.40%) is the v3 dual-conf paired-test baseline (Opus 4.7); card 3's source contrast to the slide-17 v1 blind 64.9% gold standard reflects the prompt-design difference documented on slide 62.

**Suggested rewrite (slide 70 right column):**
> • 64.9% useful per Opus-as-a-Judge v1 blind (Y+P = 971/1,497, Opus 4.6, gold standard)
> • Updated v3 paired baseline: 68.40% (Opus 4.7, dual-conf prompt — see slide 60)

**Citation:** [docs/evaluation/llm_judge/llm_judge_analysis.md](llm_judge/llm_judge_analysis.md) §2 (v1, 64.9%) vs [docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md](llm_judge_nbest/llm_judge_nbest_analysis.md) Headline (v3, 68.40%).

### Slide 31 (Do 6 Signals Actually Measure 6 Things?) — MAJOR — visual contradicts verbal caveat

**Current layout:** Three columns (PC1: 68.4% / PC2: 19.5% / PC3: 5.1%) presented as equally-weighted dimensions. Footer says "Kaiser retains 2 (87.9%); PC3 adds nuance."

**Issue:** Visually the slide presents 3 dimensions; verbally it concedes only 2 are retained. Slide 33 (which takes the cleaner Claim-3 line: "PCA retains 2 principal components") will read as inconsistent with slide 31.

**Suggested rewrite:** demote PC3 to a smaller card, an inset, or a footnote: "PC3 (Entity Swing, 5.1%) sits below the Kaiser threshold and is shown only as a minor refinement, not a retained dimension."

Or simpler — drop PC3 from the body entirely and add it to slide 83 (hidden appendix), where the loadings table already presents PC1/PC2 only.

**Citation:** [docs/evaluation/is_pca_analysis.md](is_pca_analysis.md) §3.1 — "Kaiser criterion retains 2 components"; §5 explicitly debunks the 3-dimensions framing.

### Slide 27 (Why LLM as a Judge Is Not Enough) — MAJOR — order inversion vs §2 narrative

**Issue:** Slide 27 motivates IS as needed because LLM-as-a-Judge has gaps — but slide 17 has already presented the Judge as gold standard, and slides 19–24 already use IS values. The "why we need IS" argument lands 10 slides AFTER IS is already in use.

**Suggested fix:** move slide 27 before slide 28 (the first IS-component slide) is correct — but the actual *order issue* is that the Judge appears before the Judge's limitations. Recommend re-titling slide 17 to "LLM-as-a-Judge: Gold Standard for IS Calibration" so the reader knows from slide 17 that the Judge is being USED to calibrate IS, not being proposed as the production metric.

**Citation:** [docs/evaluation/why_is_not_just_llm_judge.md](why_is_not_just_llm_judge.md) "Bottom line: IS runs in production; LLM-as-a-Judge audits the IS framework."

### Slide 17 (LLM Judge Gold Standard) — MINOR — κ values labeled ambiguously

**Current text (Methodology box):**
> κ = 0.690 (Y threshold) and κ = 0.818 (Y+P threshold)

**Issue:** Without context, a reader could read these as judge-self-κ. They are IS-vs-Opus agreement κ at the NIV operating points.

**Suggested rewrite:**
> IS-vs-Judge agreement: κ = 0.690 at NIV-Y threshold (IS ≥ 3.80); κ = 0.818 at NIV-Y+P threshold (IS ≥ 2.00).

**Citation:** [docs/evaluation/threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md) Header table.

### Slide 33 (Two Dimensions of Quality, PCA) — STYLE — body restates header

The slide is clean but mostly redundant with slide 31. If slide 31 is fixed (PC3 demoted), slide 33 can be merged or removed.

---

## §3 — Where the System Works (slides 37–45)

### Slide 41 (Failure Taxonomy 2/2) — MAJOR — present-tense future for shipped feature

**Current text (footer):**
> Accumulated errors respond to N-best aggregation (ROVER/MBR). Signal loss is detectable and filterable — lowest priority to fix.

**Issue:** N-best MBR is shipped (May 2 2026, see slide 36/61). Phrasing "respond to N-best aggregation" reads as future plan.

**Suggested rewrite:**
> N-best MBR aggregation (production default since May 2 2026) targets accumulated errors; v3 paired tests show +2.7 pp Y+P over baseline (slide 60). Signal loss is detectable and filterable — lowest priority to fix.

**Citation:** [docs/beam-search/n_best_implementation.md](../beam-search/n_best_implementation.md) "Decision (May 2026): pure hyp_mbr is the default."

### Slide 44 (LLM Salvage: Domain Context) — MAJOR — IS 2.07 framed as "near-total failure" contradicts NIV-Y+P at IS≥2.00

**Current text:**
> Cooking Context — IS 2.07 — "IS rates this a near-total failure (2.07). But a viewer watching a cooking video sees..."

**Issue:** IS 2.07 is **above** the NIV-Y+P threshold (IS ≥ 2.00), meaning IS classifies it as marginally USEFUL, not "near-total failure." The slide directly contradicts the operating-point framing on slides 25/35.

**Suggested rewrite:**
> Cooking Context — IS 2.07 (just above NIV-Y+P) — "IS rates this marginally useful (2.07, just above the IS ≥ 2.00 useful-output threshold). A viewer watching the cooking video sees the presenter holding a pepper..."

**Citation:** [docs/evaluation/threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md) NIV-Y+P operating point.

### Slide 43 (LLM Salvage: Three Real Recoveries) — MINOR — "Prob 0.95" without source attribution

**Current text:** Each example shows "IS X.XX | Prob Y.YY".

**Issue:** "Prob" is `llm_context_prob` from a Claude-DESIGNED 15-rule decision tree (no runtime LLM). The slide does not say so. A reader sees "Prob 0.95" next to IS 2.55 and could plausibly infer a runtime LLM is producing the Prob score.

**Suggested rewrite (one-line footer):**
> "Prob" = llm_context_prob, a deterministic 15-rule decision tree designed by Claude at design time (no runtime LLM call). Source: [docs/evaluation/llm_salvage/llm_salvage_analysis.md](llm_salvage/llm_salvage_analysis.md).

Same fix for slide 44.

**Citation:** [docs/evaluation/llm_salvage/llm_salvage_analysis.md](llm_salvage/llm_salvage_analysis.md) opening — "deterministic 15-rule decision tree designed by Claude at design time (no LLM API calls at runtime)".

### Slide 36 (table) — MINOR — IS Tier 3 at IS=2.00 sits at the NIV-Y+P boundary

The IS distribution table on slide 36 lists Tier 3 as "Fair (2.0–2.99)". Tier 3 = NIV-Y+P pass; Tier 2 = NIV-Y+P fail. Recommend a vertical line in the visual or a one-word annotation: "Tier 3 floor = NIV-Y+P operating point (IS ≥ 2.00)."

---

## §4 — Confidence Without Ground Truth (slides 46–62)

### Slide 56 / 57 (Joint Rule / Beam Agreement Adds Independent Signal) — CRITICAL — quoted P(correct) gap "0.62 → 0.94 = 32 pp" does not match source

**Current text (slide 56 footer):**
> WHY ADD AGREEMENT? Beam agreement is ~2x more informative than top-1 conf at high confidence. At conf >= 0.95, ranging beam_agreement from 0.40 -> 1.00 takes P(correct) from 0.62 -> 0.94.

**Current text (slide 57 table):**
> P(correct) | agreement >= 0.80 | agreement < 0.80
> 0.94 | 0.62

**Issue:** Source [TRUST_DIAGNOSTIC.md](../../english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md) Test C row "0.95+" reports P(correct) per agreement bin = 0.40 (n=42, agreement <0.40), 0.73 (n=70, 0.40–0.60), 0.84 (n=266, 0.60–0.80), 0.94 (n=2783, ≥0.80). Source [lessons_learned_band_rule_v2.md](../confidence/lessons_learned_band_rule_v2.md) §5 reports a "+53 pp lift" between (high-conf, high-agree) and (high-conf, low-agree). The "0.62" appears in the row for top1_conf 0.65+, agreement ≥0.80 = 0.62 (n=589) — a **DIFFERENT row**.

The slide is conflating two cells from different top1_conf bins. The actual data:
- At top1_conf ≥ 0.95: low-agreement (<0.80) cells average ≈ 0.77 (weighted across 0.40, 0.73, 0.84 cells).
- At top1_conf ≥ 0.95: high-agreement (≥0.80) = 0.94.
- Gap ≈ 17 pp at the aggregate level, OR ≈ 54 pp comparing the lowest-agreement cell (0.40) to the highest (0.94).

**Suggested rewrite (slide 56 footer):**
> WHY ADD AGREEMENT? At top-1 conf ≥ 0.95, P(correct) ranges from 0.40 (agreement < 0.40) to 0.94 (agreement ≥ 0.80) — a 54 pp swing the conf-only signal cannot see. Aggregated across the agreement axis, agreement is ~2× more informative than top-1 conf at high conf.

**Suggested rewrite (slide 57 table):**
Replace the 0.62 / 0.94 row with the actual diagnostic-source data:
> top1_conf ≥ 0.95: agreement <0.40 → 0.40 (n=42); ≥0.80 → 0.94 (n=2783); 54 pp swing.

**Citation:** [docs/confidence/lessons_learned_band_rule_v2.md](../confidence/lessons_learned_band_rule_v2.md) §5 (the diagonal table); [trust_diagnostic/TRUST_DIAGNOSTIC.md](../../english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md) Test C "0.95+" row.

### Slide 59 (Phase 2: Exploit All 20 Hypotheses) — CRITICAL — present-tense FALSE about a SHIPPED feature

**Current text:**
> Currently discarding 19 of 20 beam candidates
> ROVER ... MBR ...
> Expected: 5–15% relative IS improvement
> Targets: Accumulated Errors (9.1%) — the "death by a thousand cuts" category

**Issue:** "Currently discarding 19 of 20" is FALSE — MBR has been the production default since May 2 2026 (slide 36/38/61). The slide presents Phase 2 as future research, then slide 60 immediately reports MEASURED v3 paired test results showing MBR +2.7 pp Y+P. Reader sees a contradictory chronology.

**Suggested rewrite:**
> Pre-May 2 2026, the pipeline kept only the top hypothesis. **Mission 6 shipped MBR aggregation as the production default on May 2 2026** — n-best aggregation across 5 methods.
> ROVER (alternative) and MBR (shipped) ...
> Measured v3 judge gain: +2.7 pp Y+P over baseline (slide 60); WER reduction −1.56 pp on hyp_vote_conf.
> Targets: Accumulated Errors (9.1%) primarily.

**Citation:** [docs/beam-search/n_best_implementation.md](../beam-search/n_best_implementation.md) "Decision (May 2026): pure hyp_mbr is the default displayed output."

### Slide 49–55 vs Slide 56 ordering — MAJOR — joint-rule data shown 7 slides before joint rule defined

**Issue:** Slides 49–54 already use "JOINT" / "LEGACY" labels for distributions and reliabilities. Slide 56 then defines what JOINT means (top1_conf ≥ 0.95 AND beam_agreement ≥ 0.80). A reader who reaches slide 49 cold has no idea what the JOINT column means.

**Suggested fix:** swap slide 56 to before slide 49. After "Phase 1: Surface the Good 65%" (slide 48), insert the joint-rule definition (current slide 56), then proceed to distribution + reliability (49 → 50 → 51 → 52 → 53 → 54 → 55), then transitional slides 57 (info gain) and 58 (operating points).

If reorder is too costly: add a one-line at top of slide 49: "Joint rule = top1_conf ≥ 0.95 AND beam_agreement ≥ 0.80 (defined in slide 56). Legacy = conf-only ≥ 0.85."

**Citation:** rule definition lives in [docs/confidence/threshold_design.md](../confidence/threshold_design.md) §"May 2 2026 update".

### Slide 53 / 54 (Three Calibrated Thresholds) — MINOR — T_safe vs Trust-tier mapping unstated

**Current state:** Slide 53 names FOUR thresholds (T_trust 0.89, T_safe 0.82, T_salvage 0.74, Strip 0.65). Slide 54 implements a THREE-tier policy (Trust = ≥0.82, i.e. T_safe).

**Issue:** Reader does not know "Trust" tier in slide 54 = T_safe boundary. The 0.89 (T_trust) value on slide 53 isn't operationalized.

**Suggested rewrite (slide 53 footer):**
> Operating policy uses T_safe (0.82) as the "Trust" tier boundary; T_trust (0.89) is reserved for higher-precision use cases.

Or — drop T_trust from slide 53 entirely and present the three operationalized thresholds.

**Citation:** [docs/confidence/threshold_design.md](../confidence/threshold_design.md) §"three-tier policy" — "Trust ≥ 0.82 (T_safe)".

### Slide 55 (Per-Word Bands by NIV Outcome) — MINOR — conf-only data presented in joint-rule deck

**Current text:** Table shows P(correct | green/yellow/red) by NIV tier — derived from band_reliability_by_niv.md, which **explicitly states** "the conditional reliability table below was computed against the conf-only band rule".

**Issue:** The deck has just shipped joint-rule (slide 56). Slide 55 silently uses conf-only data without flagging.

**Suggested rewrite (slide 55 footer):**
> Note: NIV-stratified band reliabilities computed against the conf-only band rule (P(correct | green/yellow/red) baseline). Joint-rule re-stratification by NIV is a follow-up; the qualitative gradient is expected to hold and tighten.

**Citation:** [docs/confidence/band_reliability_by_niv.md](../confidence/band_reliability_by_niv.md) opening note.

---

## §5 — Demo + Future Directions (slides 63–80)

### Slide 71 (Five Phases — IS 2.5 → 3.3–3.7) — MAJOR — "multiplicative" footer contradicts additive math

**Current text (footer):**
> Combined target: IS 3.3–3.7 (~80–85% useful Y+P). Phase deltas sum to +0.98 from 2.52 baseline. Gains are multiplicative (ICLR 2024 scaling law).

**Issue:** "Phase deltas sum to +0.98" (literal sum) vs "Gains are multiplicative" — mutually exclusive. Slide 72 confirms the math is additive (2.52 + 0.13 + 0.40 + 0.35 + 0.10 = 3.50). The cited "ICLR 2024 scaling law" (Biderman et al.) is about LoRA scaling, not about combining decode/aggregation/data-scaling phases.

**Suggested rewrite:**
> Combined target: IS 3.3–3.7 (~80–85% useful Y+P). Phase deltas are additive (sum +0.98 from 2.52 baseline). Where phases overlap (e.g., LLM upgrade + smart prompts both targeting Hallucination + Wrong Topic), the additive estimate is conservative — measured gains may be lower if categories saturate.

**Citation:** [docs/finetuning/training-research-notes.md](../finetuning/training-research-notes.md) and [docs/evaluation/llm_upgrade_analysis.md](llm_upgrade_analysis.md) — neither claims multiplicative across phases.

### Slide 63 (Demo: OK → Almost There → Hallucination) — MAJOR — "Meaning close" describes an inversion

**Current text (left card):**
> "consumers want a bigger smartphone" → "consumers will not upgrade their smartphone"
> Meaning close, key verb flipped (IS 4.1)

**Issue:** "want X" vs "will not [do X]" is a meaning **inversion**, not "close". Notes acknowledge "key verb is flipped" but the body says "Meaning close." A research peer reads this as IS-misclassification: IS=4.1 for an inverted-meaning hypothesis would be a real metric failure if the inversion is true. (Verify the actual IS calculation on this segment — if IS really is 4.1 for an inverted prediction, this is an IS bug worth highlighting; if not, the slide claim is wrong.)

**Suggested rewrite (option A, if IS=4.1 is correct):**
> "consumers want a bigger smartphone" → "consumers will not upgrade their smartphone"
> Verb inverted, but lexical overlap drives IS to 4.1 — illustrates a metric edge case (negation-blind).

**Suggested rewrite (option B, if IS is actually lower):**
> Re-derive the IS score and update the slide; "Meaning close" is misleading regardless.

**Citation:** verify against `english_full_nbest_eval/aggregated_is.json` for this segment.

### Slide 70 (Starting from 61.6%, Not 25%) — MAJOR — pre-MBR baseline + uncalibrated WER + cross-config implication

**Current text:**
> WER Says: 25.5% useful by WER • 9 out of 10 segments fail
> IS Says: 61.6% useful output (IS ≥ 2.00) • 64.9% useful per Opus-as-a-Judge (Y+P = 971/1,497) • Validated across 16 decode configs • 85% correlation between IS and Opus verdicts

**Issues:**
1. "9 out of 10 segments fail" — 25.5% useful means 74.5% fail; "9 out of 10" overstates by ~15 pp (would be 90%).
2. "61.6%" is top-1 NIV-Y+P; current MBR-NIV-Y+P is 61.92% (slide 36). Same ballpark, but with MBR shipped, the title number "61.6%" is the pre-MBR figure.
3. "Validated across 16 decode configs" — these are top-1 only (audit JSON: `cross_config_includes_mbr: False`). Implies MBR is in the validation, but it isn't.

**Suggested rewrite:**
> WER Says: 25.5% useful by WER<30% (uncalibrated; ~3 in 4 segments fail by this cut)
> IS Says:
> • 61.9% useful output (IS ≥ 2.00, MBR n-best); top-1 baseline 61.6%
> • 64.9% useful per Opus-as-Judge v1 blind (Y+P = 971/1,497, Opus 4.6, gold standard)
> • IS-component stability validated across 16 top-1 decode configs (r=0.925 across configs); MBR validation is the v3 paired Judge test (slide 60)
> • Pearson r = 0.85 between top-1 IS and Opus v1 verdicts

**Citation:** [docs/evaluation/is_cross_config_validation.md](is_cross_config_validation.md) §10.1 (16 configs are top-1 decode-parameter variants); [docs/evaluation/after_amosi_audit.json](after_amosi_audit.json) `cross_config_includes_mbr: False`.

### Slide 74 (LLM Upgrade: Why It Matters) — MAJOR — LRS3 proof point cited for YouTube projection

**Current text:**
> VALLR (ICCV 2025): Llama 3.2-3B achieved 18.7% WER on LRS3 — beats our 7B Llama-2 (25.4%) with half the params
> ...
> [Projected Impact waterfall]
> Current WER 64% → LLM swap alone −3–8 pp → + Smart prompts −5–10 pp → + 20K segments −10–15 pp → Target WER 35–40%

**Issue:** VALLR's 18.7% is on LRS3 (TED talks, controlled, frontal). Our 64% is on YouTube (wild, varied). Citing VALLR-on-LRS3 to justify YouTube WER reductions assumes LLM-quality improvement transfers across datasets — which is plausible but unstated. A research peer will ask: "Did VALLR demonstrate the gain on YouTube-equivalent data, or only LRS3?"

**Suggested rewrite (footer):**
> VALLR's 18.7% LRS3 result demonstrates LLM-architecture matters more than parameter count on benchmark data. The WER waterfall above projects the same architectural gain transferring to our YouTube distribution; the visual encoder bottleneck (frozen AV-HuBERT) is unchanged across datasets, so the LLM-side gain is dataset-relatively similar. Domain-transfer effects on the Hallucination + Wrong Topic categories are an empirical question pending Llama 3.1 8B retraining.

**Citation:** [docs/evaluation/llm_upgrade_analysis.md](llm_upgrade_analysis.md) "Reasoning: LLM swap targets Hallucination + Wrong Topic; visual bottleneck unchanged."

### Slide 79 (Key Takeaways) — MINOR — MBR omitted; "65% useful" ambiguous

**Current text:**
> 1. Rigorous assessment: 2.5× WER gap on 1,497 segments. Novel IS metric reveals 61.6% useful output (NIV Y+P), confirmed by LLM judge at 64.9%. Full failure analysis with improvement suggestions.
> 3. Model performs well: ~65% of videos produce useful output. IS metric shows high agreement with LLM judge and runs entirely on the standalone computer — no cloud dependency.

**Issues:**
1. MBR (the headline production change of May 2 2026) does not appear in the takeaways.
2. "65%" is a rough average of 64.9% (v1 blind) and 68.40% (v3 baseline) and 71.08% (v3 MBR). It's vague.

**Suggested rewrite:**
> 1. Rigorous assessment: 2.5× WER gap on 1,497 segments. Novel IS metric reveals 61.9% useful output (NIV Y+P, MBR), confirmed by LLM judge v3 at 71.08% (paired McNemar p = 0.00017 vs baseline 68.40%). Full failure analysis with improvement suggestions.
> 3. Model performs well after MBR: 71.1% LLM-Judge useful (v3 paired). IS metric shows high agreement with the v1 blind judge gold standard (κ=0.818 at NIV-Y+P) and runs entirely on the standalone computer — no cloud dependency.
> 4. Production layer shipped: MBR n-best aggregation (default since May 2 2026) + joint conf+agreement bands + Trust gate (65.2% recall at 5.6% FPR).

**Citation:** [docs/evaluation/after_amosi_audit.json](after_amosi_audit.json) `judge_v3_yp_pct_mbr: 71.07`, `judge_v3_yp_pct_baseline: 68.40`, `mcnemar_yp_p_mbr: 0.00017`.

### Slide 73 (Stronger LLM + Smart Prompts) — STYLE — "7 strategies" but only 4 named

**Current text:**
> 7 strategies: topic context, word count, anti-hallucination, GER

**Issue:** Lists 4, claims 7.

**Suggested rewrite:** Either name all 7 or drop the count.
> Smart Prompts (force multiplier): topic context, vocabulary lists, word count, anti-hallucination guards, phonetic hints, GER, anti-paraphrase prompts

**Citation:** verify against [docs/prompts/](../prompts/) — [Report 3](../prompts/report_3_prompt_engineering.md) lists 7 strategies if it exists; otherwise update count.

### Slide 75 (Fine-Tuning: Limited Data, Limited Gains) — MINOR — "20K+" inference vs experiment evidence

**Current text:**
> Bottleneck is data quantity (need 20K+), not parameter tuning

**Issue:** The 1,273-segment experiment shows fine-tuning failed; "need 20K+" is an inference from external scaling-law literature, not from THIS experiment. Some peers will distinguish "we did not have enough data" (true claim from this experiment) from "20K is the threshold" (claim from external sources).

**Suggested rewrite:**
> Bottleneck is data quantity. 1,273 segments is below the ~1K minimum for LoRA generalization (Biderman et al. ICLR 2024); literature suggests ~20K segments are needed for stable visual+language adaptation.

**Citation:** [docs/finetuning/training-research-notes.md](../finetuning/training-research-notes.md) §"data limitation" — explicitly attributes the 20K figure to scaling-law literature.

### Slide 34 (Model Comparison: IS Profiles) — STYLE — body line is empty

**Current body:** Single line description; no visible content beyond the radar chart referenced in notes.

**Suggested fix:** Either add a 1-sentence comparative observation drawn from the notes ("LRS3 collapses uniformly higher across all 6 axes; YouTube collapses on word-accuracy and NEA most"), or merge with slide 33.

---

## CRITICAL Items — Must-Fix Before Re-Render

1. **Slide 35:** "WER > 40%" should be "WER > 77%" (NIV-Y+P calibrated cut). [§2 above]
2. **Slide 56 / 57:** "0.62 → 0.94 / 32 pp" doesn't match source data. Replace with 0.40 → 0.94 / 54 pp from TRUST_DIAGNOSTIC.md Test C. [§4 above]
3. **Slide 59:** "Currently discarding 19 of 20 beam candidates" is FALSE post-May 2 2026; MBR shipped. Reframe as "pre-May 2 2026, the pipeline kept only top-1; Mission 6 shipped MBR." [§4 above]

---

## MAJOR Items (in slide order)

- Slide 4: outline §3 / §4 mapping mismatch.
- Slide 27 ordering vs Slide 17.
- Slide 31: PCA visual presents 3 dims; verbal says 2.
- Slide 36 / 38: oracle/realistic funnel mixes denominators (1497 vs 1427) and metrics (capture vs recall).
- Slide 38 / 70: v1 (64.9%) and v3 (68.40%) baselines coexist without disclosure.
- Slide 41: ROVER/MBR future tense for shipped feature.
- Slide 44: IS 2.07 framed as "near-total failure" contradicts NIV-Y+P at IS≥2.00.
- Slide 49–55 ordering: joint-rule data before joint-rule definition.
- Slide 63: "Meaning close" describes an inversion.
- Slide 70: pre-MBR baseline + uncalibrated WER + cross-config attribution.
- Slide 71: "multiplicative" footer contradicts additive math.
- Slide 74: LRS3 proof point cited for YouTube projection.

---

## MINOR Items (in slide order)

- Slide 5: "near-zero" overstates "<5%".
- Slide 11: WER<30% uncalibrated bucket.
- Slide 17: κ values labeled ambiguously.
- Slide 36: Tier 3 floor = NIV-Y+P unmarked.
- Slide 43 / 44: "Prob 0.95" without source attribution.
- Slide 50: universal-green caveat (mitigated by 51).
- Slide 53 / 54: T_safe = Trust-tier boundary unstated.
- Slide 55: conf-only data without rule disclosure.
- Slide 70: "9 out of 10 fail" hyperbole.
- Slide 75: "20K+" inference vs experiment.
- Slide 79: MBR omitted from takeaways.

---

## STYLE Items

- Slide 33: redundant with 31; merge after fixing 31.
- Slide 34: body is empty — add a one-line comparative observation.
- Slide 73: "7 strategies" count vs 4 named.
