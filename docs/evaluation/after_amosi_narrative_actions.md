# After-AMOSI May 2026 — Action List

Companion to [after_amosi_narrative_audit.md](after_amosi_narrative_audit.md). Pre-commit must-fix list, suggested cuts, suggested adds, suggested re-orderings.

---

## A. Must-fix before commit (ranked)

| Rank | Slide | What's wrong | One-line fix |
|---|---|---|---|
| 1 | 36 | Body contradicts notes: "Y+P peaks at IS ≥ 2.0 (κ=0.82) not IS ≥ 2.00 (κ=0.52)" — both thresholds are 2.00, the typo should read "IS ≥ 2.00 vs IS ≥ 3.00." Notes are correct. | Edit body to "Y+P peaks at IS ≥ 2.00 (κ=0.82) not IS ≥ 3.00 (κ=0.52)." |
| 2 | 67, 68 | Demo bodies claim joint-rule colouring without disclosing whether segment was VSP_NBEST=1 or fell back to conf-only. Slides 64–66 correctly disclose this; 67/68 do not. | Verify decode mode for bernreuter / routers segments; add body line "(joint rule)" or "(conf-only fallback — VSP_NBEST=1 not enabled)" to each. |
| 3 | all (50, 53, 56, 64, 65, 66, 67, 68) | "sequence_conf" appears on demo cards but is never defined in §4. Audience won't know what it is. | Either define on slide 47 (it's `mean_prob`?) or strip the term from the 5 demo cards. |
| 4 | 25 (and downstream 35, 70, 79) | "NIV" used in bodies / notes but never glossed on a slide. | Add a one-line definition on slide 25 ("NIV thresholds — calibrated against Opus blind judge: IS ≥ 3.80 = Y, IS ≥ 2.00 = Y+P"). |
| 5 | 11, 16, 46, 56 (and notes on 47, 57) | Hard "next slide" references in BODY text — break on reorder. | Replace with "the following slide" or remove the cross-reference. |
| 6 | 66 | Title "INSPECT (closest to STRIP)" front-loads STRIP; audience reads it as a STRIP example. Body and notes correctly call it Salvage. | Retitle to "Demo — Obama lowest-quality segment (Salvage tier, mean_prob 0.799)." |
| 7 | 26 | "INSPECT" tier name introduced on slide 66 but never defined in §4 (only Trust / Salvage / Strip on slide 54). | Either add INSPECT row to slide 54 or drop "INSPECT" label from slide 66. |
| 8 | 48, 59 | "Phase 1: Confidence Scoring — Surface the Good 65%" and "Phase 2: Exploit All 20 Hypotheses" use planning-slide framing ("Effort: 2-4 hours implementation," "Currently discarding 19 of 20") even though both have SHIPPED (announced on slide 3). | Reword to past tense: "Confidence Scoring (shipped April 30 2026)" and "N-best Aggregation (shipped May 1 2026)." Drop "Phase 1 / Phase 2." |
| 9 | 70 vs 37 vs §0 | Numbers 61.6% (top-1) and 61.92% (MBR-IS) and 64.9% (Opus blind) all coexist without reconciliation. Audience will ask "which is the headline?" | On slide 37, add explicit bridge: "Top-1: 61.6% Y+P; MBR aggregation: 61.92% (+0.3pp). Both calibrated against Opus blind 64.9%." |
| 10 | 36, 50, 53, 58, 60, 65, 66, 67, 68 | Title-case violators (technical lowercase "mean_prob", "v3", "n-best", "per-segment") — most are intentional but should be deliberate. | Confirm intentional; no edit needed (these are stylistically correct). |

---

## B. Suggested cuts (slides that don't earn their slot)

| Slide | Why cut | Where the content goes |
|---|---|---|
| 31 ("Do 6 Signals Actually Measure 6 Things?") | PCA story duplicated on slide 33 (cleaner) | Cut. Slide 33 retains. |
| 36 ("A8: LLM Judge × IS Tier Cross-Tabulation") | Cross-tab is appendix-grade; numbers (κ=0.690/0.818) already on slides 17, 25, 35 | Move to appendix. (Currently visible — un-hide nothing, just hide this.) |
| 39 ("Failure Mode Taxonomy" overview) | Slides 40 + 41 cover the same 5 categories with examples | Cut. 40 + 41 carry the load. |
| 41 ("Failure Mode Taxonomy 2/2") | Splitting 5 categories into 1/2 + 2/2 is unnecessary for peers | Merge into 40. |
| 45 ("A6: Failure Mode Examples") | Body literally says "One real example per failure category" with **no examples on the slide**. Examples are on 42, 43, 44 | Cut entirely. |
| 54 ("Three-Tier Policy — Per-Tier Counts and Reliability") | Insight already on 51 (stratified) and 53 (thresholds) | Cut OR cut 50; one of {50, 54} can go. |
| 72 ("IS Improvement Roadmap — From 2.5 to 3.5") | Same content as 71 in waterfall form. Peers will get message from one. | Cut. Slide 71 retains. |
| 78 ("Arabic Adaptation: What Changes") | Three slides for Arabic (76 + 77 + 78) is too many; 76 already covers what changes; 78 repeats with phase numbering | Merge into 76. |
| 82 (Appendix: A3 IS Component Correlation) | Redundant with 83 (more rigorous) | Drop. |
| 85 (Appendix: A4 LLM Salvage — Recoverable Segments) | Body too thin (no enumeration of the 6 categories) | Drop. |
| 86 (Appendix: A5 LLM Salvage — Curated Examples) | Body literally says "One real example per recovery category" with no examples | Drop. Content on 43–44. |
| 89 (Appendix: Two Environments) | Internal infra context, not for academic audience | Drop. |

**Total: 11 slides cut** (7 visible + 4 appendix). Deck: 89 → 78 (or 78 visible → 71 visible).

---

## C. Suggested adds (gaps the audience will notice)

**Constraint reminder: the user said DO NOT propose new content slides.** All adds below are body-line edits or definition glosses on existing slides, not new slides.

| Existing slide | Add | Why |
|---|---|---|
| 25 (or 17) | One-line gloss: "NIV = thresholds calibrated against Opus blind judge: IS ≥ 3.80 = Y, IS ≥ 2.00 = Y+P" | NIV appears 5+ times downstream without ever being defined on a body. |
| 47 | Define `sequence_conf` and `mean_prob` explicitly | Both terms are used on demo cards (64–68) without §4 ever defining them. |
| 54 | Add a 4th tier "INSPECT" or rename slide 66 to drop INSPECT | Tier name appears once in demo block as a 4th category that wasn't introduced. |
| 64, 65, 67, 68 | One body line each tying to a §4 number: "(this segment lands in TIER X — green is N% reliable per slide 54)" | Demo block doesn't currently cite §4 numbers, weakening the §3 → §4 → §5 thread. |
| 67, 68 | Body caveat on decode mode (joint vs conf-only) | Currently undisclosed; slides 64–66 disclose. |
| 9 (8-stage pipeline) | One body line: "Stages 6–7 from academic repo; stages 1–5 + 8 engineered from scratch" | Already in notes but not on body — peers may ask "what was novel engineering?" |

---

## D. Suggested re-orderings

| Move | From → To | Reason |
|---|---|---|
| Slide 13 ("Diversity of Inputs — Not LRS3") | After slide 13 → Before slide 10 | Currently the deck claims "64.1% WER" before justifying "we evaluate on harder data." Reverse the order: justify the harder distribution FIRST, then show the gap. |
| Slide 36 (cross-tab) | Visible §2 → Hidden appendix | Reference content; numbers already on 17, 25, 35. |
| §3 internal | 37 → 38 → (cut 39) → (merged 40+41) → 42 → 43 → 44 → (cut 45) | Tightens to 6 slides; restores the "where it works" → "where it fails" thread. |
| §4 internal | Drop "Phase 1" / "Phase 2" labels (slides 48, 59); reword as past-tense capability summaries | Phase labels are roadmap residue; both phases shipped. |
| §5 future block | 71 → (cut 72) → 73 → 74 → 75 → (76 + 78 merged) → 77 → 79 → 80 | 18 → 14 slides, 2 hours fits comfortably. |

---

## E. Section grades — final

| § | Grade | Net cut count | Top action |
|---|---|---|---|
| §0 | OK | 0 | Tighten slides 2 + 3 (or accept) |
| §1 | **Strong** | 0 | Reorder 13 before 10 |
| §2 | **Strong** | 2 (cut 31, demote 36) | Trim PCA repetition |
| §3 | **Weak as labelled** | 2 (cut 39 or 41, cut 45) | Rename or restructure |
| §4 | **Strong** | 1 (cut 50 or 54) | Drop "Phase" planning labels |
| §5 | OK | 2 (cut 72, merge 76+78) | Add §4 ties to demo cards |
| Appx | OK (4 of 9 keep) | 4 (cut 82, 85, 86, 89) | Drop thin appendices |

**Aggregate:** 11 slide cuts, ~10 body-level edits (caveat / definition / cross-ref), ~3 reorderings.

---

## F. Quick-fix checklist for the speaker (printable)

- [ ] Fix slide 36 body typo (κ=0.82 vs κ=0.52 thresholds — both labelled IS ≥ 2.00)
- [ ] Disclose decode mode on slides 67, 68 (joint vs conf-only)
- [ ] Define NIV on slide 25
- [ ] Define `sequence_conf` / `mean_prob` on slide 47
- [ ] Replace "next slide" with "the following slide" on slides 11, 16, 46, 56
- [ ] Retitle slide 66 to drop "STRIP" framing
- [ ] Reconcile INSPECT tier (add to 54 or drop from 66)
- [ ] Drop "Phase 1" / "Phase 2" planning frame on 48, 59 (both shipped)
- [ ] Bridge top-1 vs MBR numbers on slide 37
- [ ] Trim slide 74 notes from 270 → ~150 words
- [ ] Cut slides 31, 39, 45, 72; demote 36, 82, 85, 86, 89; merge 76+78
- [ ] Add §4 number ties to demo cards 64–68
