# After-AMOSI Deck — Logic & Claim-Correctness Audit

**Target:** `presentation_materials_20260224/Argos_VSP_AFTER_AMOSI_May2026.pptx` (89 slides; 9 hidden)
**Date:** 2026-05-07
**Auditor scope:** logic, framing, methodology faithfulness, inter-slide consistency, sentinel-claim review (NOT a numbers audit — that lives in `after_amosi_number_consistency.md`).

This audit is companion to `after_amosi_logic_fixes.md` (the actionable fix manifest). Findings are graded
`CONSISTENT` / `MISSING_CAVEAT` / `MISLEADING` / `INCONSISTENT` per slide.

---

## Per-Claim Review (Claims 1–10)

### CLAIM 1 — IS is design-time LLM-distilled, deterministic, free, reproducible (no LLM at evaluation time)

| Slide | Claim | Verdict |
|---|---|---|
| 27 (Why LLM as a Judge Is Not Enough) | "IS produces identical scores every time"; "IS is a fixed formula"; "IS runs offline — no API" | **CONSISTENT** |
| 28 (IS Signals 1) | Footer line: "Fully deterministic • $0 per evaluation" | **CONSISTENT** |
| 32 (IS in Action) | Component-by-component formula display | **CONSISTENT** |
| 17 (LLM-as-a-Judge gold standard) | "Used as gold standard to calibrate IS thresholds" — implies design-time use | **CONSISTENT** |
| 31 / 33 (PCA) | "PCA on 1,497 segments" — analysis on stored signal values | **CONSISTENT** |
| 17 / 26 (LLM Judge runs) | The Opus runs are explicitly evaluated at design/audit time, not embedded in IS | **CONSISTENT** |
| 43 / 44 (LLM Salvage) | "How a viewer recovers this" + "Prob 0.55/0.90/0.95" — the `Prob` column is from the deterministic decision tree, but the **slides do not state** that this is a Claude-DESIGNED 15-rule decision tree, not a runtime LLM call. A research peer reading slide 43/44 in isolation could plausibly think "Prob" is a runtime LLM call. | **MISSING_CAVEAT** |
| 85 (A4: LLM Salvage — Recoverable Segments, hidden) | "Decision tree: 15 rules, r=0.934 with IS." | **CONSISTENT** (caveat is here, but the visible slides 43/44 lack it) |

**Net:** Claim 1 is consistent except for slides 43/44, which use the word "Prob" (from `llm_context_prob`) without clarifying that this is a deterministic Claude-designed decision tree, not a runtime LLM call. The hidden A4 slide carries the caveat; the visible salvage slides do not.

---

### CLAIM 2 — NIV thresholds (IS≥3.80 / IS≥2.00; legacy IS≥3.0 deprecated)

| Slide | Claim | Verdict |
|---|---|---|
| 35 (Where WER Lies Most) | Uses NIV (IS≥3.80, IS≥2.00) as success criterion — but quotes "WER > 34%" for the Y operating point AND "WER > 40%" for the Y+P operating point. Source ([threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md) §6) gives **WER ≤ 77%** as the calibrated NIV WER threshold for Y+P, NOT 40%. | **INCONSISTENT** (factually wrong threshold quoted) |
| 11 (The Reality Gap) | "25.5% Useful by WER (<30%)" — **WER threshold is <30%**. NIV-calibrated Y operating point is WER ≤ 34% (κ=0.629). Slide 11 uses an uncalibrated cutoff in the same deck that elsewhere defines NIV as the standard. | **INCONSISTENT** with NIV framing in the rest of the deck. |
| 17 (LLM-Judge gold) | "κ = 0.690 (Y threshold) and κ = 0.818 (Y+P threshold)" — under "Methodology". A peer might initially read these as judge-self-κ; they are IS-vs-Opus agreement κ values. Wording is dense; a reader can resolve it from context. | **MISSING_CAVEAT** (label clarity) |
| 25 (IS / Judge disagree) | Bottom right: "NIV thresholds (IS ≥ 3.80 for Y, >= 2.00 for Y+P) define the operating points." | **CONSISTENT** |
| 36 / 38 (Oracle vs Realistic + Funnel) | NIV-Y 23.91% (MBR), NIV-Y+P 61.92% (MBR), and ALL 5 IS tiers shown with counts. The slide quotes both NIV thresholds. | **CONSISTENT** |
| 70 (Starting from 61.6%) | "61.6% useful output (IS ≥ 2.00)" — top-1 era number. Coexists with slides 36/38 that use MBR. Not labelled as top-1 baseline. | **MISLEADING** (denominator drift; see Claim 10) |
| 17 (table) | "Y+P (any useful) 971 64.9%" and slide 70 echoes "64.9% useful per Opus-as-a-Judge" — these are blind-v1 numbers, OK. | **CONSISTENT** |
| 36 (table) | Lists tier-1 to tier-5 IS distribution. Tier 3 = "Fair (2.0–2.99)" and Tier 1 = "Failed (<1.0)". The IS≥2.00 boundary is the NIV-Y+P operating point, but it is the floor of "Fair" — slide does not call this out. | **MISSING_CAVEAT** |
| 16 (What Literature Reports vs Users Get) | Quotes IS as the answer to WER's deficit, but does not introduce NIV threshold yet — relies on slide 25/35 to land it. OK as scaffolding. | **CONSISTENT** |
| 70 ("WER says 25.5% useful") | The 25.5% is WER<30% segments — see slide 11 issue; uncalibrated. | **INCONSISTENT** (re-states an uncalibrated WER cut as the WER baseline) |
| 71/72 (5-phase roadmap) | "+0.13 IS", "+0.40 IS" deltas, NIV-Y+P column — all stay in NIV frame. | **CONSISTENT** |
| 79 (Key Takeaways) | "61.6% useful output" — same denominator drift as slide 70. | **MISLEADING** |

**Net:** NIV is the active standard, but slides 11, 35, 70, and 79 use either uncalibrated WER thresholds or top-1 NIV numbers without flagging the operating-point/MBR shift. Slide 35's "WER > 40%" is the most concrete factual error.

---

### CLAIM 3 — PCA: 2 PCs, semantic NOT independent

| Slide | Claim | Verdict |
|---|---|---|
| 31 (Do 6 Signals Actually Measure 6 Things?) | Three columns: PC1 (68.4%), PC2 (19.5%), PC3 (5.1%). Body: "PC3 is below Kaiser threshold (eigenvalue 0.31)". | **MISLEADING** — visually presents 3 dimensions; the caveat about Kaiser is buried at the bottom. The audit doc canonical claim is "2 PCs". |
| 33 (Two Dimensions of Quality, PCA) | "PCA retains 2 principal components (Kaiser criterion)" — clean. | **CONSISTENT** |
| 82 (A3: IS Component Correlation, hidden) | Lists PC1 + PC2 only. | **CONSISTENT** |
| 83 (Appendix: PCA Loadings, hidden) | Full table with correct framing: "the old '3 dimensions' framing was wrong." | **CONSISTENT** |

**Net:** Slide 31 is the live (non-hidden) version of the PCA claim and visually presents 3 dimensions (3 columns, equally sized). Slide 33 is consistent. Recommend slide 31 demote PC3 (smaller card / "minor refinement, below Kaiser" overlay) so the deck doesn't show two contradictory PCA framings to the same audience.

---

### CLAIM 4 — MBR is the production default for displayed output (May 2 2026)

| Slide | Claim | Verdict |
|---|---|---|
| 3 (What was done? 2/2) | "Mission 6 shipped (May 1 2026): n-best aggregation across 5 methods (...); MBR promoted to production default May 2 2026"; "v3 LLM-as-Judge ... MBR Y+P = 71.1% vs baseline 68.4%" | **CONSISTENT** |
| 4 (Presentation Overview) | "MBR n-best aggregation (production default)" | **CONSISTENT** |
| 36 (Where the System Works) | "Oracle (MBR best-case)" — uses MBR | **CONSISTENT** |
| 38 (Funnel) | All four cards labelled MBR / "MBR Oracle" / NIV-Y+P (MBR) / Trust gate (joint conf+agreement post-decode) | **CONSISTENT** |
| 60 (N-best Aggregation v3 paired) | Reports the McNemar table | **CONSISTENT** |
| 61 (Why MBR Won) | Explains the (a) intra-rater 86.7% / 80% / 76.7% comparison and (b) per-word posterior compatibility argument | **CONSISTENT** |
| 70 (Starting from 61.6%) | Quotes 61.6% (top-1) and "971/1,497" (v1 blind judge). Does NOT mention MBR. | **INCONSISTENT** with the rest of the deck (back-references the pre-MBR baseline as if it were the active operating point). |
| 71 / 72 (Roadmap from 2.5 to 3.5) | Phase 2 is "N-best aggregation (ROVER/MBR) — vote across 20 beams". But slide 36/38 say MBR is *already* shipped, so the roadmap framing "we will do this" is **logically inconsistent** with "we already did this." Phase 2 should be either (a) re-framed as "MBR is shipped; voting variants are roadmap" or (b) acknowledge MBR + ROVER as two separate techniques where MBR ships and ROVER is future. | **INCONSISTENT** |
| 79 (Key Takeaways) | Doesn't mention MBR at all in the takeaways. Given that MBR is the headline production change of May 2 2026, this is a glaring omission. | **MISSING_CAVEAT** |
| 4 (Overview) | Maps MBR to §3 ("Where the System Works") — but the §3 slides 39–45 are all failure-mode taxonomy + LLM salvage; MBR is barely mentioned in §3 outside slides 36/38. The overview says "MBR n-best aggregation (production default)" sits in §3 but the actual §3 narrative is failure modes, not aggregation. The aggregation slides (60–62) live in §4. | **INCONSISTENT** outline-to-content mapping. |
| 64 / 65 / 66 (Obama demo) | Notes acknowledge "Obama decode predates VSP_NBEST=1, so the agreement-aware joint rule is not applied" — important caveat. Slide title 66 was retitled to "INSPECT (closest to STRIP in the Obama set)". | **CONSISTENT** (caveat is in notes; should it be on the slide body?) |

**Net:** MBR is consistent in §0/§3/§4 slides but the roadmap (slide 71) lists it as a "to do" — contradicting MBR's already-shipped status. Takeaways (slide 79) omit MBR entirely. Slide 70 uses pre-MBR baseline numbers without labelling.

---

### CLAIM 5 — Per-word band reliability is conditional on segment quality

| Slide | Claim | Verdict |
|---|---|---|
| 50 (Band Reliability Overall) | "Joint rule's biggest reliability gain is in GREEN: 89.8% vs 80.6% (+9.2pp)" — overall. | **CONSISTENT** |
| 51 (Green Reliability Depends on Segment Quality) | Stratified table: 96.4 / 91.7 / 86.1 (joint, ≥0.65 bins) → 41.3 / 21.8 / 18.2 (legacy, <0.65 bins) | **CONSISTENT** with caveat that joint-rule numbers below 0.65 are not currently computable from the diagnostic CSV; slide labels the caveat. |
| 54 (Three-Tier Policy) | Per-tier reliabilities 95.3% / 89.1% / 56.2% (Trust / Salvage / Strip green columns) | **CONSISTENT** |
| 55 (Per-Word Bands by NIV Outcome) | NIV-Y/P/N stratified bands (94/65/39, 80/41/20, 37/17/7) — but **uses CONF-ONLY rule per source band_reliability_by_niv.md**, not joint rule. Slide does not flag this explicitly. | **MISSING_CAVEAT** — band_reliability_by_niv.md opens with "the conditional reliability table below was computed against the conf-only band rule (`conf-high` ≥ 0.85)." Slide 55 does not state this; reader could assume joint rule. |
| 50 (header) | "Joint rule's green is the biggest gain." — fine, but slide does not warn that the same green can be 96% reliable in clean segments and 18% in noisy ones (covered by slide 51). Reader sees slide 50 first and may absorb "green is 89.8% reliable" as universal. | **MISSING_CAVEAT** (mitigated by slide 51 directly after) |
| 49 (Per-Word Bands Distribution) | Joint vs Legacy — clean. | **CONSISTENT** |

**Net:** Slide 55 is the load-bearing missing-caveat — the NIV stratification is conf-only data being displayed in a deck that has just shipped joint-rule. The slide title says "Per-Word Bands" with no rule disclosure.

---

### CLAIM 6 — Trust / Salvage / Strip three-tier policy

| Slide | Claim | Verdict |
|---|---|---|
| 53 (Three Calibrated Thresholds) | T_trust 0.89, T_safe 0.82, T_salvage 0.74, Strip 0.65 | **CONSISTENT** |
| 54 (Three-Tier Policy table) | Trust ≥0.82 / Salvage 0.65–0.82 / Strip <0.65 — note the Trust threshold is set at T_safe (0.82), not T_trust (0.89). | **MISSING_CAVEAT** — slides 53 and 54 use overlapping but non-identical threshold definitions. Slide 53 names FOUR thresholds (T_trust 0.89, T_safe 0.82, T_salvage 0.74, Strip 0.65). Slide 54 implements a THREE-tier policy (Trust = ≥0.82 = T_safe). The reader needs the connection: "Trust" tier in slide 54 is keyed at T_safe, not T_trust. Source [threshold_design.md](../confidence/threshold_design.md) §"three-tier policy" confirms this — but slides 53/54 do not explicitly say "Trust tier uses T_safe boundary." |
| 53 (footer) | "Thresholds are Llama-2-7b specific. Any LLM swap forces re-running diagnose_confidence_signals.py." | **CONSISTENT** with Claim 6 caveat. |
| 56 (Joint Confidence + Beam-Agreement) | "Llama-2-7b specific. Any LLM swap..." | **CONSISTENT** |
| 58 (Trust-Gate Operating Points) | Table at fraction-green ≥30% = 65.2% recall, 5.6% FPR. Audit JSON keys check out. | **CONSISTENT** |
| 64 / 65 / 66 (Obama Trust / Salvage / INSPECT) | Slide 66 title carries the caveat: "INSPECT (closest to STRIP in the Obama set; lowest mean_prob = 0.799)" — addresses the demo limitation directly. | **CONSISTENT** |

**Net:** Trust/Salvage/Strip is internally consistent but slides 53 and 54 should make the **T_safe = Trust-tier boundary** mapping explicit.

---

### CLAIM 7 — Tier-badge labels (production palette TRUST / INSPECT / DON'T BELIEVE vs research labels Trust / Salvage / Strip)

| Slide | Claim | Verdict |
|---|---|---|
| 53 / 54 / 64 / 65 / 67 / 68 (research labels) | Uses Trust / Salvage / Strip throughout | **CONSISTENT internally** |
| 66 (demo title) | "Demo - INSPECT (closest to STRIP in the Obama set...)" — uses BOTH production label "INSPECT" and research label "STRIP" in the same title | **MISLEADING** unless reader has the mapping. The deck never explicitly maps research-Salvage = production-INSPECT and research-Strip = production-DON'T BELIEVE. |
| 80 (Thank You) | "Trust / Salvage / Strip three-tier UI" | **CONSISTENT** with research labels |
| Speaker notes for slides 64-67 | Mix of "TIER: TRUST / SALVAGE / INSPECT / STRIP" — implies these are interchangeable. The body of slide 66 alone reconciles them. | **MISSING_CAVEAT** |

**Net:** The deck never explicitly states "research label X = production badge Y." Slide 66 does it inline by using both, which is a clue but not a definition. Recommend a one-line mapping where the tiers are first introduced (slide 53 or 54).

---

### CLAIM 8 — Demo segment caveats (Obama clips fall back to conf-only)

| Slide | Claim | Verdict |
|---|---|---|
| 64 / 65 / 66 (Obama demos) | Body: "[per-word colors load from the conf-only sidecar; VSP_NBEST=1 was not enabled at the April 30 decode]" | **CONSISTENT** |
| 67 / 68 (other demos: bernreuter/rogers, networking) | Slides claim "auto-flagged red under the joint rule" — this requires the agreement sidecar to have been run on these segments. Per slide 67 notes: "PV / will also flagged red under the joint conf+agreement rule (per render-log inspection)." So 67/68 are joint-rule enabled, 64–66 are conf-only. The deck should make this two-state demo set obvious. Slide 67 says "TIER: STRIP" in body — the "STRIP" badge is research-label only; production says DON'T BELIEVE. | **MISSING_CAVEAT** (mixing the two demo regimes; mixing production vs research labels) |
| 66 (INSPECT title) | Acknowledges no Obama segment hits the 0.65 strip threshold | **CONSISTENT** |

**Net:** Mixed demo regimes (conf-only vs joint) are not flagged in the section header. Slide 64–66 disclose at the per-slide level; slide 67/68 don't disclose the difference at all.

---

### CLAIM 9 — LLM-as-Judge methodology (v1 blind vs v3 dual-conf)

| Slide | Claim | Verdict |
|---|---|---|
| 17 (Gold Standard) | Claude Opus, blind, 1497 pairs. Y=23.0%. | **CONSISTENT** with v1 |
| 26 (Context Exposes) | Context-aware re-judging | **CONSISTENT** |
| 60 (v3 Judge Paired Tests) | Opus 4.7, dual-conf, 5988 verdicts. baseline Y=13.09%. | **CONSISTENT** with v3 |
| 62 (v1 vs v3 Prompt-Design Lesson) | v1 broken, v3 fixed | **CONSISTENT** |
| 38 (Funnel — "LLM Judge v3 Y+P 71.08% MBR; baseline 68.40%") | Claims "what an independent reviewer says is useful" — but **the v3 baseline 68.40% is NOT the same as the slide-17 v1 blind 64.9%**. Both are real numbers. Different judges (4.6 vs 4.7), different prompts (no conf vs dual-conf), different runs. | **MISLEADING** — slide 38 implies a single "LLM Judge says X" canonical voice, but v1 and v3 produce different baseline rates (64.9% vs 68.40%). The funnel reader sees "LLM Judge v3 Y+P 71.08%" without knowing this is from a different run than the gold standard introduced on slide 17. |
| 70 (WER Says / IS Says) | "64.9% useful per Opus-as-a-Judge (Y+P = 971/1,497)" — this is v1 blind. Coexists with slide 38's v3 numbers. | **INCONSISTENT** — same deck cites both v1 (64.9%) and v3 (68.40%) baseline as "what the judge says is useful." Reader cannot reconcile. |
| 79 (Takeaways) | "65% of videos produce useful output" — which run? | **MISSING_CAVEAT** |
| 88 (McNemar Tests, hidden) | All v3 numbers, captioned "Opus 4.7, v3 dual-conf prompt" | **CONSISTENT** |

**Net:** The deck uses two different LLM-judge runs (v1 blind for slide 17/26/70; v3 dual-conf for slide 38/60/61/62/88) without ever flagging that the baseline Y+P rate **differs by 3.5 pp between runs** because of model + prompt differences. Slide 38 implies seamless evolution from slide 17's "64.9%" to "71.08%" — but the baseline shifted from 64.9% (v1) to 68.40% (v3), and the headline Y+P=71.08% is +2.68 pp over v3 baseline (not +6.18 pp over v1).

---

### CLAIM 10 — Cross-config validation r=0.925: 16 configs were ALL top-1, NOT MBR

| Slide | Claim | Verdict |
|---|---|---|
| 70 (Starting from 61.6%) | "Validated across 16 decode configs"; "85% correlation between IS and Opus verdicts" — the 85% is r_pearson(IS, judge) for v1 blind on top-1 baseline. The 16 configs are top-1 parameter variants. The juxtaposition with "MBR Y+P = 71.1%" elsewhere in the deck (slide 3) creates a possible reader inference that MBR was part of the 16. Audit JSON: `cross_config_includes_mbr: False`. Slide does not state this. | **MISSING_CAVEAT** |
| 82 (A3: IS Component Correlation, hidden) | "Cross-Config Stability (16 configs)" — appendix; no MBR mention. | **CONSISTENT** with the caveat that this is top-1 only |

**Net:** Cross-config r=0.925 is a top-1 stability claim that the deck never explicitly flags as top-1 only. A peer asking "is MBR validated by your 16-config stability claim?" would correctly conclude "no, the v3 paired test is the validation for MBR." The deck should make this disjoint sourcing explicit.

---

## Per-Section Flow Review

### §1 The Problem (slides 5–14)

Argument: "lip-reading is hard ⇒ pipeline ⇒ but WER doesn't capture meaning ⇒ here's the reality gap."

- Slide 5 leads with "system + human reader outperforms expert lip readers (55–70% vs 45–52%)" — this is the conclusion of [human_expert_comparison.md](human_expert_comparison.md) §6, but the flow of slide 5 makes it look like an opening claim. Source says "<5% hallucination," slide says "near-zero hallucination risk" — borderline overstatement. **MINOR.**
- Slide 5 → slide 6 (visemes) → slide 7 (3 components) → slide 8 (data flow) — clean.
- Slide 9 (8-stage pipeline) — fine.
- Slide 10 ("paper vs reality") → slide 11 (reality gap with WER<30% bucketing) → slide 12 (admiral example) → slide 13 (diversity) → slide 14 (WER lies, IS=4.03 for WER=46.2%). The transition from WER buckets (slide 11, "<30%") to NIV-calibrated thresholds (slides 25, 35) is unannounced — reader sees two different cutoffs in the same deck. **MAJOR.**
- Slide 12 's example "the→a (harmless)" vs "Admiral McRae → animal migration (destructive)" is a great rhetorical setup. The chain to "we needed our own metric" is sound.

**Verdict:** §1 flow holds, but the WER<30% (slide 11) vs WER≤34% (NIV, slide 35) inconsistency must be reconciled.

### §2 How Do You Evaluate Lip-Reading? (slides 15–36)

Argument: "WER is broken ⇒ Judge gold ⇒ but Judge alone insufficient ⇒ here's IS ⇒ IS calibrated to NIV."

- Slide 16 (literature vs users) → slide 17 (Judge gold) → slide 18 (30-sample deep-dive) → slides 19–24 (six examples) → slide 25 (where IS and Judge disagree) → slide 26 (context exposes hidden failures) → slide 27 (why LLM judge isn't enough — leads into IS) → slides 28–30 (IS components) → slide 31 (PCA) → slide 32 (worked example) → slide 33 (PCA wrap) → slide 34 (model comparison radar) → slide 35 (gap chart) → slide 36 (oracle vs realistic).
- Logical break: **slide 27 says "Why LLM judge is not enough → here's IS"** but slide 17 has already shown the Judge as gold standard with κ values referenced to IS — meaning IS is presented BEFORE its rationale. The order is inverted. The deck would flow more cleanly if slide 27 came before slide 17, or if slide 17 were re-framed as "we used the Judge to calibrate IS thresholds." **MAJOR ordering issue.**
- Slide 34 (radar) is described in notes only; the body is a single line. Body adds nothing — could be removed or expanded.
- Slide 35 has the "WER > 40%" error noted under Claim 2.
- Slide 36 (Oracle vs Realistic): the side-by-side of MBR-IS (denominator 1497) vs Trust gate recall (denominator 1427, computed against the 1497-pair gold) creates a comparison-trap. Discussed at length under Claim 2 / Claim 4. **MAJOR.**

**Verdict:** Argument holds, but slide 27 sits 10 slides AFTER the IS scaffolding it's supposed to motivate; slide 36 has comparison-trap.

### §3 Where the System Works (slides 37–45)

Argument: "now we know the metric, here's where the system works and fails."

- Slide 37/38 (oracle vs realistic / funnel) → slide 39 (failure taxonomy) → slide 40/41 (taxonomy parts 1 and 2) → slide 42 (real examples) → slide 43/44 (LLM salvage examples) → slide 45 (A6 examples).
- The transition slides 36/37 are essentially the same content rendered twice. Slide 37 title "Where the System Works: Oracle vs Realistic" repeats slide 36 (also titled the same in the body); they're separated by the section divider but logically duplicate. Verify intent.
- Slide 44 (cooking) has "IS rates this a near-total failure (2.07)" — but IS = 2.07 is **above** the NIV-Y+P threshold of 2.00, meaning IS classifies it as marginally USEFUL, not "near-total failure." Slide text contradicts slide 25/35 framing. **MAJOR.**
- Slide 43 (semantic preservation example) shows IS 2.18 — same issue, called "WER over-punishes this," but IS=2.18 is above NIV-Y+P. The slide doesn't call out that NIV already partially captures this. **MISSING_CAVEAT.**
- Slide 41 (Failure Taxonomy 2/2) "Accumulated errors respond to N-best aggregation (ROVER/MBR)." But MBR is the production default per Claim 4. So the slide reads as if N-best aggregation is future, while elsewhere it's already shipped. **INCONSISTENT.**

**Verdict:** §3 has a self-contradiction with NIV thresholds (slides 43/44) and a tense issue with MBR (slide 41).

### §4 Confidence Without Ground Truth (slides 46–62)

Argument: "no GT in production ⇒ confidence layer ⇒ stratified reliability ⇒ trust gate ⇒ MBR adds 2.67pp Y+P."

- Slide 46 → 47 → 48 → 49 (band distributions) → 50 (overall reliability) → 51 (stratified by segment quality) → 52 (green leakage) → 53 (thresholds) → 54 (three-tier counts) → 55 (NIV-stratified bands) → 56 (joint rule) → 57 (beam agreement adds info) → 58 (trust-gate operating points) → 59 (Phase 2 = N-best) → 60 (v3 paired tests) → 61 (why MBR won) → 62 (v1 vs v3 prompt lesson).
- **Order issue**: slide 56 introduces the joint rule formula, but slides 49/50 already use the joint rule for their numbers (with "Joint" labels). The reader sees joint-rule data presented as fact 7 slides BEFORE the rule is defined. The natural order is: define rule → show distribution → show reliability. Current order is: show distribution → show reliability → THEN define rule. **MAJOR ordering issue.**
- Slide 56 / 57 quote "0.62 → 0.94 (32 pp)" P(correct) gap when ranging beam_agreement at top1_conf ≥ 0.95. Source [TRUST_DIAGNOSTIC.md](../../english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md) Test C row "0.95+" reports per-cell P(correct) = 0.40 / 0.73 / 0.84 / 0.94 across agreement bins (<0.40 / 0.40–0.60 / 0.60–0.80 / ≥0.80). Source [lessons_learned_band_rule_v2.md](../confidence/lessons_learned_band_rule_v2.md) §5 says "+53 pp lift" between (high-conf, high-agree) and (high-conf, low-agree). The "0.62 → 0.94 = 32 pp" claim does not match either source — the actual gap is 0.40 → 0.94 = 54 pp, or aggregated below-0.80 → ≥0.80 ≈ 0.77 → 0.94 ≈ 17 pp. The "0.62" appears to be a misquote from a different row (top1_conf 0.65+, agreement ≥0.80 = 0.62). **CRITICAL.**
- Slide 59 (Phase 2 = "Currently discarding 19 of 20 beam candidates") — this is FALSE in present tense; we already aggregate via MBR. The slide reads as Phase 2 is future ("Targets: Accumulated Errors", "Expected: 5–15% relative IS improvement"), but the next slide (60) reports the MEASURED v3 paired test results. **CRITICAL** tense / shipped-status inconsistency.
- Slide 62 (v1 vs v3) — well-presented. Caveat present.

**Verdict:** §4 has the rule-before-data ordering inversion AND a critical numerical discrepancy on slides 56/57 AND a critical tense bug on slide 59.

### §5 Demo + Future Directions (slides 63–80)

Argument: "demo + roadmap + Arabic + takeaways."

- Slide 63 demo trio → 64–66 Obama trio → 67/68 other demos → 69 section divider → 70 (starting from 61.6%) → 71 (5 phases) → 72 (IS roadmap) → 73 (LLM + prompts) → 74 (LLM upgrade) → 75 (fine-tuning limited gains) → 76/77/78 (Arabic) → 79 (takeaways) → 80 (thank you).
- Slide 63 first card: "consumers want a bigger smartphone" → "consumers will not upgrade their smartphone" — slide says "Meaning close, key verb flipped (IS 4.1)" but the meaning is **inverted**, not "close" — "want X" vs "will not [do X]" is opposite intent. IS 4.1 is the slide's own value but the rhetorical framing "meaning close" is wrong. **MAJOR.**
- Slide 70: "WER Says ... 9 out of 10 segments fail" — 25.5% useful means 74.5% fail; "9 out of 10" implies ~90% fail. Hyperbole. **MINOR but research-peers will catch.**
- Slide 70: "Validated across 16 decode configs" + "85% correlation between IS and Opus verdicts" — see Claim 10 (cross-config is top-1 only).
- Slide 71 "+0.13 IS (~35 segs)" / "+0.40 IS (~98 segs)" — the IS deltas are derived from a model that assumes phase gains are independent and additive. Slide 71 footer says "Combined target: IS 3.3–3.7 ... Phase deltas sum to +0.98 from 2.52 baseline. **Gains are multiplicative** (ICLR 2024 scaling law)." The footer says "multiplicative" but the math literally sums (2.52 + 0.13 + 0.40 + 0.35 + 0.10 = 3.50 = sum). Either the framing is wrong (additive in math, claimed multiplicative) or the cited scaling law is misapplied. Slide 72 confirms additive: "+0.13 → +0.53 → +0.98 from 2.52". **MAJOR.** "Multiplicative" misrepresents the cited literature.
- Slide 73 "7 strategies: topic context, word count, anti-hallucination, GER" — 4 strategies named, 7 promised. **MINOR rounding/list-incompleteness.**
- Slide 74 "VALLR (ICCV 2025): Llama 3.2-3B achieved 18.7% WER on LRS3 — beats our 7B Llama-2 (25.4%) with half the params" — this is on **LRS3**, not on our wild YouTube dataset. The slide's "Projected Impact" waterfall (-3 to -8pp WER) is for our YouTube data. Combining the LRS3 VALLR proof point with a YouTube projection is **apples-to-oranges**. The notes acknowledge "visual encoder is the primary bottleneck" but the slide body doesn't. **MAJOR.**
- Slide 75 "LoRA on 1,273 segments: IS 2.49 → 2.31 → 2.02 — fine-tuning made IS WORSE" — correct framing per [training-research-notes.md](../finetuning/training-research-notes.md). But "Bottleneck is data quantity (need 20K+)" is an inference, not a result of THIS experiment. The experiment shows fine-tuning failed at this data scale; the 20K+ inference is from external scaling-law literature. **MISSING_CAVEAT** about evidence base.
- Slide 76 / 77 / 78 (Arabic) — all roadmap, clearly framed as future. **CONSISTENT.**
- Slide 79 "Model performs well: ~65% of videos produce useful output" — see Claim 9 (ambiguous which Judge run). Also "37 bugs fixed" — provenance unclear (presumably from `vsp_linux_container_FINAL_20260217/`). The takeaway omits MBR (Claim 4).

**Verdict:** §5 has multiple claim issues — slide 71 multiplicative-vs-additive math; slide 74 LRS3 vs YouTube; slide 63 "meaning close" vs inverted; slide 70 "9 of 10 fail."

---

## Cause-Effect / "Therefore" Claims List

| Slide | "Therefore X" claim | Holds? |
|---|---|---|
| 5 (foot) | "System + human reader outperforms expert lip readers" | PASS (matches [human_expert_comparison.md](human_expert_comparison.md) §6 conclusion) |
| 6 (foot) | "Context is the ONLY disambiguation signal — this is why the LLM matters." | PASS (matches methodology §3) |
| 12 (foot) | "We needed our own metric — the Intelligibility Score." | PASS |
| 14 (foot) | "WER counts word edits. IS asks: did the viewer get the message?" | PASS |
| 16 (foot) | "Therefore we built a separate evaluation framework (IS) - next slide." | PASS |
| 17 (notes) | "Threshold sweep: Y+P peaks at IS>=2.0 (kappa=0.818, 91.5% agreement), not IS>=3.0 (kappa=0.521)" | PASS |
| 31 (foot) | "Together: 93% of variance in 3 components. Kaiser retains 2 (87.9%); PC3 adds nuance." | **FLAG** — visual treatment of slide 31 contradicts the verbal caveat (3 columns shown, says "2 retained"). |
| 35 (foot) | "IS WER correlates with IS (r≈−0.7) but not perfectly" | PASS |
| 38 (whole) | "WER → IS NIV → LLM Judge → Trust gate" implies a refining funnel | **FLAG** — different denominators and different metrics, not refinements of one. |
| 41 (foot) | "Accumulated errors respond to N-best aggregation (ROVER/MBR)." | **FLAG** — present-tense FUTURE for a SHIPPED feature. |
| 50 (foot) | "Joint rule's biggest reliability gain is in GREEN" | PASS |
| 51 (foot) | "Below 0.65, even green words are <50% reliable - which is why the strip-coloring boundary is set at 0.65." | PASS |
| 56 (foot) | "Single-axis conf misses the wide spread in this regime; the joint rule recovers it." | PASS in spirit |
| 57 (foot) | "Conf alone collapses two distinct populations into one green band - agreement separates them" | PASS in spirit |
| 59 (foot) | "Both are established ASR techniques with consistent 5-15% gains." | **FLAG** — generic literature claim retro-fitted to MBR-already-shipped narrative; we have a measured +2.67 pp Y+P, not a 5-15% relative IS gain. |
| 60 (foot) | "hyp_mbr +40 wins, p=0.00017" | PASS (matches audit + source) |
| 61 (foot) | "DECISION - ship pure hyp_mbr as default displayed output" | PASS |
| 62 (foot) | "LESSON: when prompting an LLM judge to compare hypotheses, ALWAYS provide the baseline reference's confidence too." | PASS (transferable lesson well-supported) |
| 71 (foot) | "Phase deltas sum to +0.98 ... Gains are multiplicative" | **FLAG** — sum and multiplicative are mutually exclusive; math is sum. |
| 73 (col 1) | "Llama 3.1 8B alone: -3 to -8pp WER" | PASS (notes carry justification; slide body should at least name the source range) |
| 74 (col 1) | "VALLR ... beats our 7B Llama-2 (25.4%) with half the params" | **FLAG** — LRS3 not YouTube; slide body doesn't say it. |
| 75 (foot) | "Bottleneck is data quantity (need 20K+), not parameter tuning" | **FLAG** — inference from external literature, not from this experiment. |
| 79 (foot) | "Model performs well: ~65% of videos produce useful output" | **FLAG** — which judge run / threshold? |

---

## Apples-to-Apples Comparison List

| Slides | Comparison | Fair? |
|---|---|---|
| 10 vs 11 | "Paper LRS3 25.4% WER" vs "1497 YouTube 64.1% WER" | **FAIR** — slide 10 explicitly says "different dataset" |
| 17 vs 38 / 60 | v1 blind judge Y+P=64.9% vs v3 dual-conf baseline Y+P=68.40% | **UNFAIR** — different judge models AND prompts; deck never flags this |
| 36 left vs 36 right | NIV-Y+P (denom 1497) vs Trust-gate recall (denom 1427) | **UNFAIR** — different denominators, slide doesn't reconcile in body. Notes do. |
| 38 funnel cards | WER 63.84% (avg per segment) vs 65.2% recall vs 71.08% Judge Y+P | **UNFAIR** — three different metrics styled as a refining funnel |
| 50 vs 51 | Overall band reliability 89.8% green vs stratified-by-quality 96.4–18.2% green | **FAIR** — slide 51 directly explains the conditioning |
| 51 (joint vs legacy bins) | Joint-rule values for ≥0.65 bins vs legacy-rule values for <0.65 bins | **FAIR-WITH-CAVEAT** — slide 51 footnotes the rule difference; reader can verify |
| 55 NIV stratification | NIV bands shown as if joint-rule | **UNFAIR** — band_reliability_by_niv.md is conf-only data; slide does not flag the rule |
| 62 v1 vs v3 | Same n-best methods, different prompts, opposite conclusions | **FAIR** — exactly the lesson |
| 63 demo trio | 3 segments labeled WER 28% / 56% / 100%, IS 4.1 / 2.9 / 0.8 | **FAIR** — well-chosen example contrast |
| 70 IS vs WER capture rates | "61.6% useful by IS" vs "25.5% useful by WER" | **UNFAIR** if WER cutoff is <30% (uncalibrated) but NIV-Y+P at IS≥2.00 is calibrated. Should be WER<77% for like-for-like comparison. |
| 74 VALLR vs ours | VALLR LRS3 18.7% vs Our 25.4% | **UNFAIR** — different time periods, "beats us" framing should clarify same-dataset comparison |
| 75 fine-tuning | Baseline IS 2.49 vs ExpA 2.31 vs ExpB 2.02 | **FAIR** |

---

## Sentinel-Phrase Audit

Searched for: "we proved", "we show", "this proves", "demonstrates", "production", "users can trust", "you can trust", "always", "never", "all", "none", "deterministic", "calibrated", "Oracle", "Realistic".

| Phrase | Slide(s) | Verdict |
|---|---|---|
| "Proved the model performs well" | 3 | Soft language ("performs well"), bounded by "65% of videos are useful by LLM judge" — **CONSISTENT** |
| "production default" | 3, 4, 36, 38, 61 | All refer to MBR. Per MEMORY.md `n_best_aggregation_findings`, MBR shipped May 2 2026 in container overlay; vsp_docker/ deferred. Slides treat container overlay = "production." Acceptable shorthand. |
| "fully deterministic" | 28 | Refers to IS formula. **CONSISTENT** with Claim 1. |
| "calibrated" | 17, 35, 53, 56, 58 | All refer to NIV thresholds or band reliability — accurate uses. |
| "Oracle vs Realistic" | 36, 37 | Defined: Oracle = MBR best-case, Realistic = Trust-gate output. **Defined once consistently.** Slide 36 title says "Oracle vs Realistic" but the body labels are "Oracle (MBR best-case)" and "Realistic (Trust-gate output)". OK. |
| "no single fix" | 39 | Bounded ("Failures are diverse"). **PASS** |
| "always" | 62 | "ALWAYS provide the baseline reference's confidence too" — bounded to LLM-as-judge prompt design. **PASS** |
| "near-zero hallucination risk" | 5 | Source says "<5%" — "near-zero" is a stretch. **MINOR.** |
| "9 out of 10 segments fail" | 70 | 74.5% fail by WER<30% — "9 out of 10" overstates by ~15 pp. **MINOR.** |
| "WER lies" | 14 | Soft hyperbole; slide self-evidently rhetorical. **PASS** |
| "Without exception", "every", "everything" | None used aggressively | **PASS** |
| "Bottleneck is data quantity" | 75 | Inference, not experiment-internal result. **MINOR caveat needed.** |

---

## Open Risks for Research-Peer Q&A

1. **"Why did your baseline Y+P go from 64.9% (slide 17) to 68.40% (slide 38)? Same 1497 segments?"** — Different judge model + different prompt. Deck doesn't flag.
2. **"Slide 31 says 3 PCs (PC1, PC2, PC3); slide 33 says 2 PCs. Which is it?"** — Slide 31 should demote PC3 visually.
3. **"Slide 35 quotes WER>40% as the Y+P operating point — but you also say IS≥2.00 maps to WER≤77%. Where did 40 come from?"** — uncalibrated cutoff.
4. **"Slide 56 says agreement adds 32 pp; your source paper says 54 pp. Which?"** — number doesn't match source.
5. **"Slide 59 says 'currently discarding 19 of 20 beam candidates' — but slide 36 says MBR is shipped. Which is it?"** — tense inconsistency.
6. **"Slide 74 cites VALLR LRS3 18.7% to justify a YouTube WER reduction projection. How does that translate?"** — same-dataset transfer assumption unstated.
7. **"Slide 71 footer says 'multiplicative' but the math sums. Which model are you using?"** — misuse of scaling-law term.
8. **"You say IS is design-time LLM-distilled; slide 43/44 show 'Prob 0.95' — is that a runtime LLM call?"** — `llm_context_prob` is the deterministic decision tree, not flagged on slides 43/44.
9. **"Why is the Trust-gate '65.2% recall' compared to '61.92% NIV-Y+P' on slide 36?"** — different denominators (1427 vs 1497), different metrics (recall vs capture rate).
10. **"Are the 16 cross-config experiments validating MBR?"** — No, they're top-1 only. Deck doesn't say.

---

## Summary Counts

- **CRITICAL** (factually wrong, peer would call out): **3** items (slide 35 WER>40%, slide 56/57 "32 pp / 0.62", slide 59 "currently discarding")
- **MAJOR** (misleading framing): **9** items (slide 31 PCA visual, slide 36/38 funnel comparison, slide 41 ROVER/MBR future tense, slide 44 IS 2.07 "near-total failure", slide 63 "meaning close" inverted, slide 70 baselines drift, slide 71 "multiplicative", slide 74 LRS3-to-YouTube transfer, slide 27 ordering)
- **MINOR** (missing caveat): **8** items (slide 5 "near-zero", slide 11 WER<30%, slide 17 κ label, slide 33/53/54 threshold mapping, slide 43/44 "Prob" attribution, slide 50 universal-green caveat, slide 55 conf-only stratification, slide 70 "9 of 10")
- **STYLE** (could tighten): **3** items (slide 34 body, slide 73 "7 strategies" unsourced, slide 79 takeaway omits MBR)

Companion: see [after_amosi_logic_fixes.md](after_amosi_logic_fixes.md) for slide-by-slide rewrite suggestions.
