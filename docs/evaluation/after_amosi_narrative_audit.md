# After-AMOSI May 2026 Deck — Narrative Audit

Target: `/home/ubuntu/presentation_materials_20260224/Argos_VSP_AFTER_AMOSI_May2026.pptx` (89 slides, 9 hidden appendix). Audience: ~12 research peers, 2-hour slot.
Audit date: 2026-05-06.

Headline grade: deck is **OK overall, weak in two specific places** (§3 is thinner than its label promises; §5 demo block is partly broken-down and partly tacked on). §1, §2, §4 are strong. Specifics below.

---

## Section grades (one-line each)

| § | Slides | Content | Grade |
|---|---|---|---|
| §0 | 1–4 | Opening + double "What was done" | OK — slides 2 & 3 partially redundant with §5 takeaways |
| §1 | 5–14 | Problem, visemes, pipeline, WER lies | **Strong** |
| §2 | 15–36 | Evaluation: judge, IS signals, PCA, cross-tab | **Strong, but bloated** (22 slides; PCA repeated, IS-vs-judge revisited 3× across 25/26/36) |
| §3 | 37–45 | Where the system works + failure modes + salvage | **Weak title vs content** — only 37/38 actually deliver "where it works"; 39–44 are failure analysis (great content, but mis-labelled section) |
| §4 | 46–62 | Confidence, bands, n-best, MBR | **Strong, slightly padded** (50 ↔ 51 ↔ 54 all relitigate green-band reliability) |
| §5 | 63–80 | Demo + future + Arabic + takeaways | OK — demo block 64–68 has caveats not on slides; future is clean |
| Appx | 81–89 | 9 hidden | 4 worth keeping, 3 too thin, 2 borderline |

---

## §0 Opening (slides 1–4)

- **Opening / middle / closing:** Has cover (1), 2-slide overview (2–3), TOC (4). That is one slide too many for an internal research audience that has not seen the prior March deck — slide 2 ("What was done? 1/2") and slide 3 ("What was done? 2/2") are essentially the abstract twice over, and most of those bullets are restated in §5 takeaways (slide 79).
- **Internal flow:** Slides 2–3 are bullet dumps. Slide 4 (TOC) lands the section — it would land harder if it came on slide 2.
- **Section length vs density:** 4 slides for an opening to peers is slightly heavy — peers want the TOC fast, not a pre-summary.
- **Redundancy:** Slide 2 bullet "Evaluated the model extensively, including designing a new metric that measures whether meaning is preserved" duplicates slide 79 takeaway #1. Slide 3 bullets on n-best, IS, container are all repeated downstream.
- **Gap:** None — section delivers. Just over-served.

---

## §1 The Problem (slides 5–14)

- **Opening / middle / closing:** Strong arc — opens with a 0% WER showcase video (5), develops visemes (6) → architecture (7–9) → benchmark gap (10–11) → metric critique (12, 14) with diversity context (13). Closes with the WER-vs-IS payoff slide (14).
- **Internal flow:** Mostly tight. One soft spot — slide 13 ("Diversity of Inputs — Not LRS3") sits AFTER slides 10–11 already gave the 64.1% headline, so the logic flips: we showed the gap before justifying why it exists. Reorder 13 → before 10 (or merge into 10).
- **Section length vs density:** 10 slides feels right.
- **Redundancy:** Slides 10 and 11 both carry the 64.1% / 25.4% framing. They're complementary (paper claim vs distribution) but the "2.5×" appears on both. Acceptable.
- **Gap:** None.

**Verdict:** Strong. Only nit is slide-13 placement.

---

## §2 Evaluation (slides 15–36)

This is the biggest, most important section. It runs **22 slides** (the user flagged this as a possible bloat risk and the audit confirms it).

- **Opening / middle / closing:** Opens with a divider (15) and a "what literature reports vs what users get" framing (16). Develops the LLM-as-Judge gold standard (17), 6 worked examples (18–24), agreement analysis (25–26), the rationale for IS over a runtime LLM judge (27), the 6 IS signal definitions (28–30), PCA collapse (31, 33), worked computation (32), radar comparison (34), the "WER lies" payoff (35), and a cross-tab (36). Closes well with the WER-overstates-failure number.
- **Internal flow:**
  - The 6 worked examples (19–24) are a great pedagogical block. They earn their slots.
  - Hard transition at slide 27 (LLM-judge rationale), then back into IS signals at 28. The reader has to switch frames: "judge vs IS" → "now let me explain IS internals." A one-line bridge in slide 27 would smooth this.
  - **PCA is repeated:** slide 31 ("Do 6 Signals Actually Measure 6 Things?") and slide 33 ("Two Dimensions of Quality") cover the same PC1=68.4%, PC2=19.5% finding with 90%+ overlapping language. The notes on slide 33 say "this slide and downstream narrative use 2 PCs only" — which suggests slide 33 was meant to *replace* slide 31 but both shipped. **One must be cut.** Slide 31 is more decorated; slide 33 is cleaner. Recommend cut slide 31, keep 33.
  - **IS-vs-Judge agreement is repeated:** slide 25 (where IS and judge disagree, 22 cases), slide 26 (context exposes failures), and slide 36 (cross-tab). Slide 36 is appendix-grade and ships visible — the κ=0.690/0.818 numbers also appear in 17 and 35. Demote 36 to appendix; the cross-tab is reference content.
- **Section length vs content density:** 22 slides for evaluation methodology is **too many** for 2-hour academic. Trimming slides 31 and 36 (and possibly merging 18 with 19) brings it to 19–20, which is appropriate.
- **Redundancies (concrete):**
  - PC1=68.4% / PC2=19.5%: slides 31, 33, 82 (hidden), 83 (hidden) — **4 instances**.
  - κ=0.690 / κ=0.818 NIV thresholds: slides 17, 25, 35, 36, 82 — **5 instances** of the same pair of numbers.
  - "Same WER, different effects" worked example: slide 12 + slide 16 both use the bernreuter / overhead-lights pair. Slide 16 reuses 12's premise.
- **Gaps:** Section delivers what it promises. No gap.

**Verdict:** Strong content, bloated by ~3 slides. Trim 31, 36 (move to appendix). Soften 26 (it's about an 11-case context-rescue analysis — interesting but not load-bearing for an internal audience).

---

## §3 Where the System Works (slides 37–45)

The user's brief calls this section "proof of capability + when/where the system delivers." The actual content of the 9 slides is split: **2 slides** (37, 38) deliver the headline "where it works"; **7 slides** (39–45) deliver failure-mode taxonomy and salvage examples. The label and the content disagree.

- **Opening / middle / closing:** Slide 37 ("Oracle vs Realistic") is the strongest slide in the section — it delivers exactly what the section promises. Slide 38 ("From Literature Metric to User-Trusted Output") is a 4-card waterfall and also delivers. Then the section pivots to failure modes (39, 40, 41, 42, 43, 44) and an appendix-style mini-overview (45).
- **Internal flow:** Slides 39 and 40 are essentially the same content — both are the "5 categories with their counts" overview. Slide 39 is a one-pager card view; slide 40 is the same content split into "Part 1." Slide 41 is "Part 2" — this 1/2 + 2/2 structure adds zero value for peers (the categories aren't long). **Merge 40 + 41 into one slide; cut 39.**
- **Section length vs content density:** Section is 9 slides but only 37–38 actually answer the section title. 39–44 are failure analysis — they're great content, but they belong in their OWN section, not under "where the system works." Either rename §3 to "Where it works AND where it fails" (more honest) or split.
- **Redundancies:**
  - 39 and 40 — see above (two views of the same 5-category breakdown).
  - Slide 42 ("Failure Modes: Real Examples") shows three categories' examples; slide 43 + 44 add 6 more salvage examples; slide 45 (visible "A6") is a thin pointer to the same content. **Slide 45 can be cut entirely** — its single body says "One real example per failure category" and the 6 examples are already on 43 and 44.
- **Gap:** The section title promises proof of capability, and slide 37 carries the load alone. The "65.2% recall at 5.6% FPR" is the headline number for the section, but it appears once (37) then is referenced again on 38. That's fine — but consider one slide explicitly captioned "headline: 65% useful at 5.6% FPR" that the audience will remember.

**Verdict:** Weak as labelled — content is mis-organized, not low-quality. Either rename or restructure.

---

## §4 Confidence Without Ground Truth (slides 46–62)

- **Opening / middle / closing:** Strong arc. Slide 46 sets the production motivation (no ground truth on user video). 47 introduces two layers. 48 is the mission-1 framing. 49–58 develop bands, leakage, thresholds, joint rule, agreement signal, trust gates. 59–62 cover n-best aggregation. Closes with "MBR won" (61) and a methodological lesson (62).
- **Internal flow:** Largely good. Concerns:
  - Slide 48 ("Phase 1: Confidence Scoring — Surface the Good 65%") looks like a planning slide ("Effort: 2–4 hours implementation") that should have been retired now that confidence has shipped. The framing "How It Works / What It Enables" reads as proposal language. **Either retire or rewrite as "Confidence Scoring (shipped April 30)."**
  - Slide 50 ("Band Reliability — Overall P(correct | band)") and slide 51 ("Green Reliability Depends on Segment Quality") and slide 54 ("Three-Tier Policy — Per-Tier Counts and Reliability") all hammer on the same insight: green isn't always reliable. They build on each other but the cumulative effect on a peer audience is overkill — peers will get this on slide 51. **Consider cutting 54** (its content is also implied by 53's three thresholds).
  - Slide 55 ("Per-Word Bands Stratified by NIV Outcome") is excellent and load-bearing — keep.
  - Slide 56 (joint rule) → 57 (why beam agreement helps) → 58 (per-segment trust gate) is a clean three-slide payoff. Keep all three.
  - Slide 59 ("Phase 2: Exploit All 20 Hypotheses") again uses planning-slide framing ("Currently discarding 19 of 20") even though aggregation has SHIPPED and §0 already announced it. **Reword as "N-best aggregation (shipped May 1)."**
- **Section length vs content density:** 17 slides for confidence is appropriate, but 50/51/54 collapse to 2 slides without loss. 17 → 15 is the right size.
- **Redundancies:**
  - 50, 51, 54 — all three carry "green reliability is conditional" stories. Concentrate on 51 (the stratified one) + 53 (the threshold table) + 55 (NIV stratified).
  - 56 and 57 both tell the joint-rule story; 56 sets the rule, 57 justifies the agreement axis. Both earn their slots. (No cut.)
- **Gap:** No gap.

**Verdict:** Strong. Trim 1–2 redundant band-reliability slides; reword the two "Phase 1 / Phase 2" planning slides to past-tense.

---

## §5 Demo + Future (slides 63–80)

The title is "Demo + Future" but the actual structure is: 1 demo intro (63), 5 demo cards (64–68), section transition (69), 5-phase roadmap (70–72), LLM upgrade (73–74), fine-tuning (75), Arabic (76–78), takeaways (79), thank you (80).

- **Opening / middle / closing:** OK arc. Slide 63 is a 3-video demo card that previews the demo block. Slides 64–68 are 5 single-segment demo slides (Obama trust / salvage / inspect, then bernreuter strip, then routers salvage). Slide 69 transitions to future. 70–78 cover the roadmap. 79 closes.
- **Demo block (64–68) — sanity check:**
  - **Caveat disclosure:** Slides 64, 65, 66 ALL have notes saying "Obama decode predates VSP_NBEST=1, so per-word bands are conf-only — not the joint rule." Slide 67 ("Strip") and 68 ("Salvage") describe the joint-rule colouring as if applied. **The render-log fact (per the user's brief) that obama_flagged shows INSPECT not STRIP is correctly disclosed in the slide title (66) and notes** — that part is honest. But: **none of the slide BODIES mention the conf-only fallback**, only the speaker notes. If notes aren't read aloud, the audience sees "Obama Trust Tier" with bands rendered and assumes joint-rule. **Add one body line on each Obama slide: "(per-word bands shown here are conf-only; this segment predates VSP_NBEST=1)."**
  - Slide 66 title runs to 80+ characters, breaking sentence-case (mid-sentence parens). Shorten to "Demo — INSPECT (Obama, lowest mean_prob 0.799)."
  - Slide 67 and 68 demo segments (bernreuter, routers) are repeats of the §2 worked examples (slides 19 and 21). The audience will recognize the text and feel the deja-vu unless told this is intentional. The notes do say "reframed for research" but the reuse should be acknowledged on the slide body.
  - **Tying back to §4:** The demo block CLAIMS to demonstrate the trust-gate / band-reliability concepts of §4 but does not mention the trust-gate operating point (30%-green default) or the band-reliability numbers (89.8% green) explicitly on any slide. The notes touch on it (slide 64: "audit-md:band_reliability_by_niv puts NIV-Y green at 94%"). **The demo would land harder if each card had a small "what this demonstrates" line tying back to §4 numbers.**
- **Future block (70–78):** Cleaner. Slide 70 ("Starting from 61.6%") is a mid-section reset; 71 is the 5-phase roadmap (note: 211-word notes — long but appropriate); 72 is the same content as a waterfall view; 73 / 74 develop LLM upgrade; 75 is fine-tuning; 76–78 are Arabic.
- **Redundancies (future block):**
  - Slide 71 and slide 72 deliver the same 5-phase content. 71 is a numbered list; 72 is the waterfall view. They earn separate slots in a research deck (one shows derivation, the other shows trajectory) but a peer audience will get the message on either alone. **One can be cut.** Recommend cut 72 (waterfall is denser, harder to deliver in 60s).
  - Slide 73 and slide 74 both cover LLM upgrade. 73 is the 3-column "force multiplier" story; 74 is a single-LLM-swap focus with the VALLR result. They overlap in content (Llama 3.1 8B drop-in, smart prompts, GER) but each has a unique payoff. **Borderline keep — but slide 74's notes are 270 words; cut to 150.**
  - Slide 76 and slide 78 both describe the Arabic adaptation steps (encoder fine-tune, LLM swap, K-means, eval data). Slide 77 ("AV-HuBERT not language-locked") sits between them as a justifying digression. **Three slides for Arabic is too many for 12 minutes** — the deck is supposed to leave the audience with "Arabic in 2–3 months, blockers known," not a deep technical dive. Recommend merge 76 + 78; keep 77 as the justifier; ends at 2 slides.
- **Section length vs density:** 18 slides is too long for the closing arc. Cuts: 72, possibly 76 or 78. Bring to 15.
- **Gap:** §5 doesn't actually deliver a connected narrative from "what we built" → "what we'd do next" → "Arabic." The Arabic block feels tacked on (the Arabic-adaptation idea was not foreshadowed in §0–§4). The brief promises this; the deck does it but mechanically. Acceptable.

**Verdict:** OK. Demo block needs body-level caveats; future block has 2 mergeable redundancies.

---

## Appendix (slides 81–89, all hidden)

| # | Title | Worth keeping hidden? | Verdict |
|---|---|---|---|
| 81 | A1: Homophenes — The Lip-Reading Problem | YES | Useful Q&A backup if "but how identical are the mouth shapes?" comes up. Body is thin but the role is clear. KEEP. |
| 82 | A3: IS Component Correlation | NO | One-pager on PCA + cross-config; redundant with 83 which is more rigorous. CUT — replaced by 83. |
| 83 | Appendix: PCA Loadings on the 6 IS Signals | YES | Rigorous PCA reference. KEEP. |
| 84 | Appendix: Human-IS Path B (Pre-Study Estimates) | YES | Strong Q&A backup if "how does this compare to a human lip-reader?" comes up. KEEP. |
| 85 | A4: LLM Salvage — Recoverable Segments | NO | Body is two short blocks ("58% of salvageable have moderate WER" + "6 Recovery Categories"). The 6 categories are not enumerated on the slide. Too thin to deserve a slot. CUT. |
| 86 | A5: LLM Salvage — Curated Examples | NO | Body literally says "One real example per recovery category" with no examples shown. CUT — content is on slides 43–44 already. |
| 87 | A9: Context Evaluation — Transition Details | YES | Rigorous Q&A backup if "did you do context-aware judging?" comes up. KEEP. |
| 88 | Appendix: McNemar Tests — N-Best Methods vs Baseline | YES | Rigorous statistical reference for slide 60. KEEP. |
| 89 | Two Environments: Development and Production | BORDERLINE | Internal infra context. Likely not asked by research peers. CUT for academic audience; useful for client deck only. |

**Should any be UN-hidden?** No — all hidden slides are reference / Q&A material. None elevate the main flow.

**Recommendation:** Cut 82, 85, 86, 89. Keep 81, 83, 84, 87, 88 (5 substantive backup slides).

---

## Cross-section consistency

### Number consistency (cross-checked numerically)

| Number | First mention | Reuses | Issues |
|---|---|---|---|
| 64.1% WER (top-1) | slide 10 | 11, 70 | OK |
| 63.84% WER (MBR) | slide 13 (notes), 38 | OK | OK — but slide 10 says 64.1% as headline; the MBR-aware update (63.84%) only appears on 13/38. Audience may ask "which?" — recommend a one-line note: "MBR shaves 0.2pp." |
| 61.6% useful (NIV Y+P) | slide 4 | 70, 71, 79 | OK |
| 61.92% (NIV Y+P, MBR) | slide 37 | 38 | OK — but 61.6% (top-1) and 61.92% (MBR) coexist in the deck without a "1.5pp from MBR" reconciliation. **Pick one as the headline; flag the other as MBR-aware.** Currently 61.6 is on §0 + future; 61.92 is on §3 — they look like inconsistent numbers. |
| 64.9% Y+P (Opus blind) | slide 17 | 35 (notes), 70 | OK |
| 71.08% Y+P (MBR, v3) | slide 3, 37, 38 | OK | Strong number, well-trafficked. |
| 65.2% recall / 5.6% FPR | slide 4, 37, 38, 58 | 4× | OK |
| κ=0.690 (Y) / κ=0.818 (Y+P) | slide 17 | 25, 35, 36, 82 | 5× — over-mentioned |
| IS 2.52 vs 2.547 | 70, 79 use 2.52; 37 uses 2.547 (MBR) | mixed | **Inconsistency.** Slide 37 says "Mean IS: 2.547 (top-1: 2.532)" but slide 70 says "IS 2.52" without distinguishing. The MEMORY auto-memory says baseline IS=2.52 and MBR=2.547 — these are real distinct numbers but the deck flips between them without a callout. |

### Metric framing inconsistencies

- **§3 introduces "Oracle vs Realistic"** as a top-level frame on slide 37 but §4 never uses these terms. §4 stays in "trust gate / operating point" language. Slide 38 bridges them, but the Oracle/Realistic frame isn't picked up later. Either commit to the frame across §3 → §4 or drop it.
- **§5 demo block** uses TIER labels (TRUST / SALVAGE / INSPECT / STRIP). §4 uses the same labels (slide 54). Good consistency. But INSPECT is introduced on slide 66 as a new tier name — §4 only defined Trust / Salvage / Strip. **INSPECT is a 4th label that wasn't defined**. Either add INSPECT to §4 (slide 54) or rename slide 66's tier.
- **Sequence_conf** appears on slides 64, 65, 66, 67, 68 ("sequence_conf high / mixed / low") but is NOT defined anywhere in §4 — it is not in slides 47–58. The audience will not know what this term means. Define it on slide 47 (it's the same as `mean_prob`?) or strip the term from the demo cards.
- **"NIV"** is introduced on slide 25 (notes) and used heavily downstream (35, 70, 79) but **never defined on a slide body**. Notes hint it stands for the "NIV thresholds" calibrated against Opus. Peers will not know what NIV means. Add a one-line gloss on slide 25.

### §3 headline number §4 revisits

- §3 headline: 65.2% recall at 5.6% FPR (slide 37, 38). §4 revisits with the SAME number on slide 58 — consistent. 
- §3 headline: 61.92% NIV-Y+P (MBR). §4 doesn't revisit this number. 
- §5 demo videos do NOT explicitly cite the trust-gate numbers from §4 — see §5 critique above.

### Cross-section flag

- **§4 Phase 1 / Phase 2 framing** (slides 48, 59) is inconsistent with §0 + §3 which already say "shipped." Sync to past-tense or remove the phase labels.

---

## Speaker notes audit

### Empty notes
None visible. All 89 slides have non-empty notes.

### Length distribution

- **Total visible (non-appendix) slides:** 80
- **Mean words/slide (visible):** 67
- **Median:** 60
- **<10 words (TOO SHORT):** 1 — slide 80 ("Thank You", 9 words). Acceptable for closing slide.
- **>200 words (LONG):** slides 71 (155), 73 (211), 74 (270). All in §5 future block. Slide 74 is the longest in the deck.
- **Notes/body imbalance:** slide 14 ("WER: The Metric That Lies") has only 17 words of notes but a dense body — reader gets minimal context. Either body or notes should expand.

### Citation quality

| Slide | Cites source? | Notes |
|---|---|---|
| 1, 2 | partial | Slide 2 notes cite `docs/confidence/band_reliability_by_niv.md` — good. |
| 3 | yes | cites `docs/beam-search/n_best_implementation.md`. |
| 4 | yes | cites `docs/evaluation/after_amosi_audit.md`. |
| 5 | yes | cites `docs/evaluation/human_is_estimation.md`. |
| 6 | no | No source — but content is well-known. |
| 7–9 | no | Acceptable (architecture descriptions). |
| 10–12 | no | Body and notes give 25.4% / 64.1% but **no cite to the underlying audit JSON or experiment table**. |
| 13 | yes | cites `docs/architecture.md`, `docs/evaluation/after_amosi_audit.md`. |
| 14 | no | Body claims IS 4.03 / WER 46.2% — no source. |
| 16 | yes | cites `docs/evaluation/after_amosi_audit.json`. |
| 17 | partial | numbers (κ=0.690, Y rate 23.0%) given without explicit source citation. |
| 19–24 | no | All 6 worked examples have IS / WER / judge numbers but no source. They're real but the notes don't say "from `docs/evaluation/llm_judge/...`" |
| 25 | partial | mentions analysis but no doc link. |
| 26 | partial | same. |
| 27 | no | the "12+ documented systematic biases" claim has no source. |
| 28–30 | no | IS signal definitions — formula details given but no `intelligibility_methodology.md` cite. |
| 31, 33 | yes (33) | 33 cites `is_pca_analysis.md`. 31 doesn't. |
| 35 | partial | numbers given without doc cite. |
| 36 | partial | κ=0.818, 91.5% cited without source path. |
| 37, 38 | yes | both cite `after_amosi_audit.md` (sections A, F, E). Excellent. |
| 39–44 | no | failure-mode taxonomy without source path. |
| 47 | yes | cites `confidence_full_analysis.md`, `lessons_learned_band_rule_v2.md`. Excellent. |
| 49 | yes | cites `after_amosi_audit.json` Section D. Good. |
| 50, 51, 53–58 | yes | All cite the audit JSON or the confidence subdocs. Excellent. |
| 60–62 | yes | cite `llm_judge_nbest_analysis.md`, `n_best_implementation.md`. Excellent. |
| 63–68 | partial | demo notes cite `slides_client.py` source (where the slides came from), not the data source. The IS / WER values for the demo segments have no audit cite. |
| 70–78 | partial | future-direction numbers (e.g., "VALLR 18.7% WER") cite paper but other numbers (Phase 2 expected +0.13, Phase 3 +0.40) have no source. Slide 71 notes do walk through the derivation, which is good — but the per-phase-IS-delta numbers have no audit-doc cite. |

**Summary:** §4 (confidence) has the best citation hygiene. §1 + §2 + §5 (worked examples and roadmap deltas) are weakest. **List of slides with body numbers but no source citation in notes:** 10, 11, 12, 14, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 35, 36, 39, 40, 41, 42, 43, 44, 63, 64, 65, 66, 67, 68, 70, 72, 73, 74, 75. That's 38 visible slides without source paths. For an internal academic audience this isn't fatal, but it leaves the deck non-self-contained.

### Notes contradicting body

- **Slide 26 body:** "230 downgrades vs 68 upgrades / Y→P dominant (138)." **Notes:** "230 downgrades vs 68 upgrades, Y to P dominant (138)." Consistent.
- **Slide 35 body:** "42 + 437 segments WER wrongly discards." **Notes:** "42 segments clearly conveyed... 437 useful." Consistent.
- **Slide 36 notes:** "Y+P aligns best with IS>=2.00 (kappa=0.818, 91.5% agreement)." **Body:** "Y+P peaks at IS ≥ 2.0 (κ=0.82) not IS ≥ 2.00 (κ=0.52)." **CONTRADICTION** — the body has an obvious typo ("≥ 2.0" vs "≥ 2.00" with different κ), should be **"IS ≥ 2.00 not IS ≥ 3.00"**. The notes are correct; the body is broken. **Fix slide 36 body.**
- **Slide 51 body:** "Below 0.65 (legacy rule only): 0.55-0.65: 41.3%." **Notes:** "JOINT-rule values for those bins are not currently recomputable. ... <0.65 bins ... are from the legacy CONF-ONLY rule." Consistent with the body caveat.
- **Slide 63 body:** "WER 100% IS 0.8 / 'carry strap' → 'holocaust denier'." **Notes:** "Right: 'carry strap' becomes 'holocaust denier' (hallucination, IS 0.8 - fluent but completely fabricated)." Consistent.
- **Slide 66 title:** "INSPECT (closest to STRIP in the Obama set; lowest mean_prob = 0.799)." **Body:** "TIER: INSPECT" + "mean_prob = 0.799 (just inside Salvage)." **Notes:** "production badge is INSPECT - the closest-to-STRIP example available." Consistent — but the body says "just inside Salvage" while the title says "closest to STRIP." These are reconcilable but might confuse — the segment is in Salvage tier (mean_prob > 0.65 strip boundary), but with the lowest mean_prob in the Obama dataset. The title makes it sound like a STRIP example, the body correctly says Salvage. **Reconcile body or title.**

### "Next slide / previous slide" references (will break on reorder)

| Slide | Reference | Risk |
|---|---|---|
| 4 | "5 sections, mapping to..." (notes) | Low — refers to TOC, no slide # |
| 11 | "But WER overstates failure — see next slide." (BODY) | **HIGH** — body text. Breaks if 11/12 reorder. |
| 16 | "Therefore we built a separate evaluation framework (IS - Intelligibility Score) - next slide." (BODY) | **HIGH** |
| 36 | "Next slide quantifies what the two layers separate." — wait, that's slide 47's notes. Let me recheck. |
| 46 | "Two layers of confidence (next slide): per-word from the LLM softmax, per-segment as the aggregate." (BODY) | **HIGH** |
| 47 | "Next slide quantifies what the two layers separate." (NOTES) | Medium |
| 51 | "see slide_band_reliability_stratified" (NOTES) | Low — internal slide name not number |
| 57 | "next slide quantifies" (BODY) | **HIGH** — wait, slide 56 body says "next slide quantifies." |
| 56 | "next slide quantifies" (BODY) | **HIGH** |

**Summary:** **6 visible slides have hard "next slide" / "previous slide" references in body text.** These all need defensive language: "the following slide," or just remove the cross-reference.

---

## Title sentence-case consistency

Dominant pattern: **Title Case** (88/89 slides). One outlier:

- **Slide 2 + 3:** "What was done? (1/2)" / "(2/2)" — sentence case. Doesn't match the Title Case norm. Either change to "What Was Done? (1/2)" or accept as casual opening.

Other notes:
- Slides 50, 53, 58, 60, 65, 66, 67, 68 are flagged as "MIX" or "SENT" by the auto-tagger. Most are intentional (lowercase "mean_prob" / "v3" / "n-best" / "per-segment" are proper technical lowercase — these are CORRECT, not errors). The classifier flagged them as breaks but they're stylistically correct.
- **Slide 66 title** is too long ("Demo - INSPECT (closest to STRIP in the Obama set; lowest mean_prob = 0.799)") — title-bar-overflow risk. Shorten.

**Verdict:** Sentence-case is consistent except slide 2 / 3, which are casual but acceptable.

---

## Pacing for 2 hours

89 slides / 120 min = **80s/slide on average**. With 20-min Q&A, that's **~60s/slide** on the talk. Below: slides flagged as too-dense (cut content) or too-sparse (merge).

| Slide | Density flag | Reason | Action |
|---|---|---|---|
| 5 | sparse | Body is 1 sentence; cover slide for a video. Notes are 113 words. | OK if video plays full 30–45s; otherwise merge. |
| 9 | dense | 8-stage pipeline diagram with 32 body elements. 60s is tight for diagram delivery + voiceover. | Allocate 90s. |
| 14 | sparse | 11 body elements but most are cells of a side-by-side card. Notes only 17 words. | Allocate 60s, but expand notes. |
| 15 | sparse | Section divider, 24-word notes. | 30s — banner only. |
| 19–24 | medium | Six worked examples, each ~8 body fields. | 50s each = 5 min total — reasonable. |
| 25 | dense | 13 body elements, two-column with judge analysis. Notes 135 words. | 90s. |
| 26 | dense | 10 body elements + IS=4.75 false positive sidebar. Notes 137 words. | 90s. |
| 31 | medium | PCA explanation. Cuts redundant with 33. | If kept, 60s. Recommend cut. |
| 33 | medium | Same PCA story, cleaner. | 60s. |
| 36 | medium | Cross-tab. | Move to appendix — saves a 60s slot. |
| 37 | dense | Oracle vs Realistic with tier breakdown — 23 body elements. | 90–120s — payoff slide of §3, deserves time. |
| 38 | medium | 4-card waterfall. 12 body elements. | 90s. |
| 41 | sparse | Just two failure categories (Signal Loss + Accumulated Errors), 11 body elements. | 30–45s — merge with 40 to recover time. |
| 45 | sparse | "One real example per failure category (5 categories):" with NO examples on slide. Body is 2 lines + "A2." | **CUT** — adds zero. |
| 50 | medium | Single-message slide on +9.2pp green. | 45s. |
| 54 | medium | Trust/Salvage/Strip table. | 60s. |
| 58 | medium | Trust-gate operating points. Notes 52 words. | 60s. |
| 60 | medium | McNemar paired tests. Body 5 bullets, notes 50 words. | 60s. |
| 63 | medium | 3-video demo card. Notes 119 words. | 90–120s if 3 videos play. |
| 64–68 | medium | 5 single-video demos. Each video plays 5–10s. | 60s each = 5 min. |
| 71 | dense | 5-phase roadmap, all on one slide, with derivation. Notes 155 words. | 120s — cannot deliver in 60. |
| 72 | medium | Same content as 71 in waterfall view. | **Recommend cut.** |
| 73 | dense | 3-column "force multiplier." Notes 211 words — author may try to read all of it. | 90s. |
| 74 | dense | LLM upgrade with VALLR + waterfall. Notes 270 words — speaker may run long. | 90s. **Trim notes.** |
| 75 | sparse | Fine-tuning, 2 short bullets. Notes 53 words. | 30s — could merge with 73 / 74. |
| 76 | medium | Arabic roadmap with 6 categories. | 60–90s. |
| 77 | sparse | AV-HuBERT not language-locked. 8 short bullets. | 45s. |
| 78 | medium | Arabic phases. | 60s. |
| 79 | medium | 4 takeaways. | 60s. |
| 80 | sparse | "Thank You." | 30s + Q&A. |

### Pacing math

- If we cut slides 31, 36, 39, 45, 54, 72, 76+78 merge → ~7 slides cut.
- Net deck: 89 → 82 visible (73 visible non-appendix → 66 visible).
- 66 visible × 75s = 82.5 min talk + 20 min Q&A = 102 min. Leaves a 18-min buffer for the dense slides (37, 71, 73, 74) that should run 90–120s.
- **Verdict:** With cuts, the deck fits 2 hours comfortably. Without cuts, the speaker will rush.

---

## Demo block sanity (slides 63–68)

Per the user's brief: "render-log: Obama clips fall back to conf-only (no VSP_NBEST=1) and `obama_flagged` shows INSPECT not STRIP. Are these caveats disclosed?"

| Slide | Caveat in body? | Caveat in notes? | Audience told what they're watching? |
|---|---|---|---|
| 63 | n/a (3-video card, not Obama) | yes (notes describe each video) | yes (each card has WER/IS overlay + caption) |
| 64 (Obama TRUST) | **NO body caveat** about conf-only fallback. Body says "[per-word colors load from the conf-only sidecar; VSP_NBEST=1 was not enabled at the April 30 decode]" — actually YES, this IS in the body. Good. | yes (notes elaborate) | yes |
| 65 (Obama SALVAGE) | yes — body says "[per-word colors load from the conf-only sidecar; 'said' substitution is the visible orange word]" | yes | yes |
| 66 (INSPECT) | yes — body has the caveat but the *title* says "INSPECT (closest to STRIP)" — the audience may take "STRIP" at face value. The notes correctly say "production badge is INSPECT" but the title front-loads STRIP. | yes (notes say "original client framing called this STRIP but mean_prob=0.799 puts it in Salvage band") | partially — title is ambiguous |
| 67 (STRIP) | NO conf-only caveat. The body claims "the entity-swap tokens 'rogers', 'pv', 'will' are auto-flagged red under the joint rule" — implying joint rule is applied. Was VSP_NBEST=1 enabled for THIS segment? | notes don't disclose. | partially — claim is joint-rule but it may be conf-only |
| 68 (SALVAGE - routers) | Same as 67 — body claims "per-word reds isolate the swaps" without saying which rule. | notes don't disclose. | partially |

**Verdict on disclosure:**
- Slides 64, 65, 66 correctly disclose the conf-only fallback in BODY text (good).
- Slides 67, 68 (bernreuter, routers) describe joint-rule colouring but don't disclose whether the segment was decoded with VSP_NBEST=1 or fell back. **Action needed:** verify these two segments' decode mode and add a body-level caveat if conf-only.
- Slide 66 title front-loads STRIP; reword to "Demo — Obama (lowest mean_prob, lands in Salvage tier)" to avoid the STRIP misread.

**Tying back to §4:** None of the demo cards explicitly cite the §4 numbers (89.8% green reliability, 65.2% recall, 5.6% FPR). Each card *implicitly* demonstrates band rendering and tier triage but doesn't say "this is the Trust tier from slide 54 — green is 95.3% reliable here." Add one tying line per card.

---

## Cross-references that will break on reorder

(Already enumerated under speaker-notes audit — repeated for action list.)

- Slide 11 body: "see next slide"
- Slide 16 body: "next slide"
- Slide 46 body: "next slide"
- Slide 56 body: "next slide quantifies"
- Slide 47 notes: "Next slide quantifies"
- Slide 57 body: implicit (no concrete reference but builds on 56)

All should be reworded "the following slide" or "we now turn to" — language that survives a slide-order edit.

---

## End-to-end summary table

| § | Strong | Weak | Cut count | Edit count |
|---|---|---|---|---|
| §0 | TOC clean | 2 + 3 redundant abstracts | 0 (acceptable) | 0 |
| §1 | Visemes + WER lies | slide 13 placement | 0 | 1 reorder |
| §2 | 6 worked examples | 22 slides; PCA 2× | 2 (31, 36) | 1 reorder |
| §3 | 37 + 38 nail the headline | 39 ↔ 40 redundant; 45 thin | 2 (39 or 40, 45) | rename section |
| §4 | Bands + n-best arc | "Phase 1/2" planning labels | 1 (54 or 50) | 2 retitle |
| §5 | future is clean | demo caveats only in notes; 71↔72 + 76↔78 redundant | 2 (72, 78 merged into 76) | 5 body adds |
| Appx | 81/83/84/87/88 useful | 82/85/86/89 thin | 4 | 0 |

**Total cuts proposed:** 11 slides (from 89 → 78). Of those, 7 are visible (89 - 9 hidden = 80 visible → 73 visible).
