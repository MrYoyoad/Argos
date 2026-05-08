# PPTX Audit — Argos_VSP_For_Orchard_May2026.pptx

**Date:** 2026-05-08  
**Scope:** All 79 non-hidden slides, visual inspection via LibreOffice PNGs  
**Dimensions:** story coherence, detail density, visibility, story arc, example quality, graphics/animations, notes, accuracy

---

## Executive Summary

The deck is mostly well-built. The narrative arc is coherent and the headline numbers are accurate. However there are **3 critical visibility violations** (slides 17, 24, 75 with ~10–12pt text — far below the 24pt floor), **12 real layout/overlap bugs** where text elements visually collide, **1 stale accuracy issue** on slide 47 (pre-calibration confidence thresholds), and **1 unverified stat** repeated on slides 35 and 69 (r=0.85 IS vs Opus, not in any source document).

---

## 1. CRITICAL — Font Size Violations (STYLE_GUIDE 24pt floor)

| Slide | Title | Issue |
|-------|-------|-------|
| 17 | What the AVSR Literature Reports vs What Users Get | ~10–12pt throughout. Two-column format with tiny bullet text and inline REF/HYP examples. Unreadable at presentation distance. |
| 24 | Where IS and Judge Disagree | ~12–14pt throughout. Two-card layout ("IS Too Harsh" / "IS Too Generous") with sub-examples at near-illegible size. |
| 75 | Arabic Pipeline: Replication Roadmap | ~10–12pt. Dense 3-column table with step/effort/risks rows. Entire slide is unreadable beyond front row. |

**Fix:** For each slide, either bump all text to ≥24pt (may require cutting content) or split into two slides.

---

## 2. REAL LAYOUT BUGS (Text overlaps in PowerPoint)

These are position-based overlaps visible in OOXML coordinates — not LibreOffice rendering artifacts.

| Slide | Title | Bug |
|-------|-------|-----|
| 7 | The Invisible Problem: Visemes | Third bullet "Context is the ONLY disambiguation…" is fully hidden behind the viseme table. |
| 15 | WER: The Metric That Lies | The 46% / 4.03 score cards sit too low, visually colliding with the Reference/Prediction lines below. Last word of Prediction text cut off. |
| 18 | LLM-as-a-Judge: Gold Standard | Third left-column bullet ("3-level verdict: Y / P") overlapped by "Results (Blind: 1,497 Pairs)" header and table. |
| 25 | Context Exposes Hidden Failures | "80% stable across modes" bullet overlaps "knowledge reveals vocabulary failures" text; bottom banner overlaps right card content. |
| 27 | IS Signals: Word Accuracy & Length | Top banner text wraps to "and length" on line 2, hidden behind first content card. |
| 28 | IS Signals: Semantic Similarity | "signal" wrap-line in top box partially hidden behind the "How It Works" card. |
| 30 | Do 6 Signals Actually Measure 6 Things? | PC1 card description overflows into PC2 card header area. |
| 34 | The Gap: Where WER Lies Most | Subtitle text (NIV-calibrated description) overlaps with the large "75 + 68" headline. |
| 40 | Failure Mode Taxonomy (1/2) | Subtitle text hidden behind first content card; "Ordered by impact" footer overlaps card 3 bottom. |
| 45 | Two Layers of Confidence | In the PER-SEGMENT card, "mean log-probability over the segment" label overlaps with the formula text. |
| 58 | N-best Aggregation: From One to All 20 | Subtitle sentence cut off mid-word; yellow "MBR beats base 68%" banner overlaps card boundary. |
| 73 | LLM Upgrade: Why It Matters | VALLR green evidence box overlaps the italic footer ("Same hidden dim (4096) — adapter retraining required"). |

---

## 3. ACCURACY ISSUES

### 3a. Stale slide — Slide 47 "Confidence Scoring (shipped)"
- Shows thresholds `≥0.8 trust | <0.4 flag` — these are pre-calibration approximations.
- Shipped values: T_trust=0.89, T_safe=0.82, strip boundary=0.65.
- "Effort: 2–4 hours" bullet is stale roadmap text; this feature shipped Apr 30.
- "Reduces perceived error rate from 60% to ~20%" — based on old thresholds; at T_safe=0.82 the green P(correct) is 90%, implying ~10% error.
- **Fix:** Update thresholds to match slides 52–53 (the authoritative calibration slides), remove the "Effort" bullet.

### 3b. Unverified stat — Slides 35 and 69: "Pearson r=0.85 (IS vs Opus)"
- MEMORY has r=0.934 (expert heuristic), r=0.925 (cross-config). Neither is 0.85.
- The 0.85 value does not appear in any docs/evaluation/ file checked.
- **Fix:** Verify from `docs/evaluation/is_correlation_analysis.md` or remove/replace with a confirmed value.

### 3c. Minor — Slide 78 Key Takeaways: "IS—judge κ=0.818 at NIV-Y+P"
- MEMORY (2026-05-06 audit): exact MBR κ=0.796; exact top-1 κ=0.816. The 0.818 was the historical approximate.
- In the takeaway slide this is a minor rounding issue. Low priority.

### 3d. Confirmed accurate (spot-checks passed)
- Slide 36: NIV-Y+P 61.92%, NIV-Y 23.9%, IS 2.547, Judge Y+P 71.1% p=0.0002, Trust-gate 65.2%/5.6%, tier counts 291/324/312/329/241 — all match MEMORY exactly.
- Slide 37: WER MBR 63.84%, NIV-Y+P 61.92%, Judge Y+P 71.08%, Trust 65.2% — all correct.
- Slides 52–53: T_trust=0.89, T_safe=0.82, T_salvage=0.74, strip<0.65 — correct.
- Slide 57: ≥30% green = 630 trusted, Recall 65%, FPR 6% — correct.
- Slides 59–60: MBR +40 Y+P wins p=0.00017, vote_conf +31 p=0.00257 — correct.
- Slide 74: IS 2.49 → 2.31 → 2.02 for fine-tuning — matches MEMORY.

---

## 4. STORY & NARRATIVE

### What works well
- The 5-section arc (Problem → Evaluation → Proof → Confidence → Future) is clear and coherced.
- Section divider slides (16, 38, 68) provide clean psychological breaks.
- The "Oracle vs Realistic" framing on slide 36 is the cleanest entry point to results.
- The WER-lies narrative (slides 13–15) builds intuition well before introducing IS.

### Issues
| Issue | Slide(s) | Severity |
|-------|----------|----------|
| Slide 46 ("Confidence Without Ground Truth" — the motivation) comes *after* slide 45 ("Two Layers of Confidence" — the solution). The problem setup arrives after the answer. | 45→46 | Moderate |
| Slide 47 ("Confidence Scoring shipped") uses stale thresholds, making §4 internally inconsistent with slides 52–57. | 47 | High (see §3a) |
| Arabic section (slides 75–77) has 7 bullets per slide — exceeds the 4-bullet STYLE_GUIDE cap. Content reads as a technical spec, not a story. | 76, 77 | Moderate |
| Demo section has 6 individual clip slides (62–67). Could become monotonous; consider dropping slide 64 (Obama conf-only fallback is the weakest example) or merging 62/64 into a triptych. | 62–67 | Low |

---

## 5. EXAMPLE QUALITY

| Slides | Assessment |
|--------|-----------|
| 13 (Same WER, Different Effects) | Excellent. Concrete and memorable. |
| 20–23 (Judge Examples 1/3/5/6) | Good variety: entity swap, vocabulary drift, domain confusion, topic hijack. Left half is empty video area (intentional — video plays). The metrics header and "Reference:" label are very tight vertically; this is readable but borderline. |
| 41 (Failure Modes: Real Examples) | Excellent 3-column layout, well-labelled. |
| 43–44 (LLM Salvage: Three Recoveries / Domain Context) | Both excellent — concrete ref/hyp pairs with clear recovery narrative. |
| 51 (Green Leakage) | Excellent: billion→million (0.965), 1024→24 (0.958), 2011→2000 (0.894) are the right level of detail. |
| 62–67 (Demo tier clips) | Good tier coverage. Slide 64 (Obama, conf-only fallback) is weaker than the others because it shows a fallback mode, not the production path. |
| 6 (Clean speech demo) | Good anchor example opening the deck, sets bar high. |

---

## 6. GRAPHICS & VISUALS

### Broken image placeholders (LibreOffice only — normal, show in PowerPoint)
Slides with embedded images that render as "Picture N…" in LibreOffice: 1, 7, 8, 11, 12, 14, 33, 34, 39, 50, 54, 59, 69, 70, 71, 73, 74. These are all expected — LibreOffice doesn't resolve embedded PPTX image streams the same way PowerPoint does.

### Pipeline diagram — Slide 10 (8-Stage Automated Pipeline)
Text inside stage boxes clips in LibreOffice: "& ROI" cut in box 2, "transcription" partially cut in box 3, "clustering" cut in box 6. This *may* also clip in PowerPoint if boxes use fixed-height shapes without auto-fit. Recommend verifying in PowerPoint directly.

### PCA slide — Slide 32 (Two Dimensions of Quality)
Clean, two-card layout with 68%/20% large numbers. Good visual hierarchy. No issues.

### Band reliability slides (48–50)
Slide 48 comparison table (joint vs legacy) is dense (4 columns) but readable at 24pt. Slide 49 clean 3-row table. Slide 50 broken image on left but right-side table is clear.

---

## 7. SPEAKER NOTES (Footer Text Audit)

Footer/italic text was audited from PNG rendering. Most slides have informative footers. Key notes:

| Slide | Footer quality |
|-------|---------------|
| 6 | "Reference and prediction are identical (WER 0%). 27 of 29 per-word confidence bands GREEN — the model is sure, and it's right." — Excellent. |
| 15 | "WER counts edits. IS asks: did the viewer get it?" — Good punchy takeaway. |
| 35 | "All numbers from audit JSON keys..." — technical reference footer, appropriate. |
| 52 | "Thresholds are Llama-2-7b specific; LLM swap = re-fit needed." — Important caveat, correctly placed. |
| 57 | "Calibrated under joint conf+agreement rule." — Good provenance note. |
| 73 | Footer partially hidden by overlapping VALLR box (see Layout Bugs §2). |

---

## 8. SECTION ARC PROPORTIONS

| Section | Slides | Notes |
|---------|--------|-------|
| §0 Opening + overview | 1–4 | 4 slides — concise, appropriate |
| §1 The Problem | 5–15 | 11 slides — slight padding (slide 47 spans into confidence prematurely) |
| §2 Evaluation (IS + Judge) | 16–35 | 20 slides — long but each slide earns its place; IS signal deep dives (27–29) could be trimmed for 60-min version |
| §3 Proof | 36–44 | 9 slides — well-paced |
| §4 Confidence | 45–61 | 17 slides — heaviest section; appropriate for Orchard audience interested in reliability |
| §5 Demo | 62–67 | 6 video slides — could trim to 4 |
| §6 Future | 68–77 | 10 slides — fine |
| Closing | 78–79 | 2 slides — clean |

---

## Priority Fix List

### Must Fix Before Presenting
1. **Slide 17, 24, 75** — bump text to ≥24pt (or split slides). Audience can't read these.
2. **Slide 47** — update thresholds to shipped values (0.82/0.65), remove "Effort" bullet.
3. **Slide 7** — fix viseme table Y position so third bullet isn't hidden.
4. **Slide 18** — fix table Y position so all three left-column bullets are visible.
5. **Slide 34** — fix subtitle Y/height so it doesn't overlap headline.
6. **Slide 58** — shorten subtitle text box or reduce font so sentence doesn't overflow.

### Fix Before Recording / High-Visibility Review
7. **Slides 35, 69** — verify or remove r=0.85 stat.
8. **Slides 15, 25, 27, 28, 30, 40, 45, 73** — fix remaining overlap issues.
9. **Slide 10** — verify pipeline box clipping in actual PowerPoint.
10. **Slide 46→45 order** — consider swapping to problem-first ordering.

### Low Priority
11. **Slide 78** — κ=0.818 → 0.816 (cosmetic).
12. **Slides 76–77** — reduce to 4 bullets each per STYLE_GUIDE.
