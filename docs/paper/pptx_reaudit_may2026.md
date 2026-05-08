# PPTX Re-Audit — Argos_VSP_For_Orchard_May2026.pptx
**Date:** 2026-05-08  
**Scope:** 79 non-hidden slides (indices 1–79; slides 80–88 are appendix, hidden)  
**Tool:** python-pptx programmatic scan + full text inspection

---

## Executive Summary

The batch of fixes was partially successful. The specific items listed as fixed are verified clean with **one exception**: `κ = 0.818` persists on **slide 18** (the methodology bullet for the v1 blind judge — it was fixed on slides 35 and 78 but missed on 18). Beyond that exception, the main body of each fix is confirmed.

The re-audit found a **broader, pre-existing pattern**: a large portion of the presentation uses 20 pt body text rather than the 24 pt floor. This affects 30+ slides and is the biggest outstanding structural issue. These were not newly introduced — they reflect the original generator default — and were not addressed in the batch fix.

**Issues found:**
- **D1 Font floor**: 1 residual `< 24pt` fix missed (slide 18, κ bullet). Beyond that, pervasive 20 pt body text on 30+ slides remains (pre-existing, not introduced by the batch).
- **D2 Overlaps**: Structural overlaps persist on multiple slides, consistent with the intentional stacked-card layout pattern. Most are card-label-inside-card (expected). True text-over-text overlaps remain on slides 17, 34, 40, 58, 72, 75 (see details below).
- **D3 Bullet count**: 5 shapes still exceed the 4-bullet cap: slides 2, 3, 34, 61 (×2). Slides 2 and 3 have 6 bullets each.
- **D4 Accuracy**: `κ = 0.818` still present on slide 18 (should be `0.816`). All other forbidden strings clean.
- **D5 Story arc**: Confirmed clean. Slide 45 = "Confidence Without Ground Truth" (problem framing) correctly precedes slide 46 = "Two Layers of Confidence" (solution). Section dividers at slides 16, 38, 68 in place.
- **D6 Detail density**: Several slides carry bullets or annotations above 10 words. Most are quote excerpts or example annotations (not primary bullets); the primary content slides are borderline acceptable.
- **D7 Graphics**: All 79 non-hidden slides have at least one embedded image. No missing-placeholder issues found.
- **D8 Notes**: All 79 slides have substantive speaker notes (>20 chars). No gaps.

**Priority fix list:** 3 actionable items (D4 is the only hard-accuracy error; D3 and D1/18 are polish).

---

## Verification of Batch Fixes

| Fix | Status |
|-----|--------|
| Font floor slides 17, 24, 75 | **PARTIAL** — Slide 24 and 75 body bullets are now 24 pt. Slide 17 still has 18 pt non-italic quote labels ("REF:"/"HYP:") and 22/20 pt section text (details below). |
| Layout overlaps slides 7, 15, 18, 25, 27, 28, 30, 34, 40, 45→46, 58, 73 | **PARTIAL** — Overlaps reduced. Residual overlaps at slides 17, 40, 58, 73, 75 (see D2 details). |
| `r=0.85` removed from slides 35 and 69 | **PASS** — Not found on either slide. |
| `κ=0.818→0.816` on slides 35 and 78 | **PASS** — Both slides now show `0.816`. |
| Slide 47 thresholds `T_safe=0.82 / T_trust=0.89` | **PASS** — Both values confirmed on slide 47 TextBox 4 and TextBox 6. |
| Slide order: confidence_problem (45) before two_layer (46) | **PASS** — Slide 45 = "Confidence Without Ground Truth", slide 46 = "Two Layers of Confidence". |
| Arabic slides 76/77 cut to 4 bullets | **PASS** — Each slide now has exactly 4 single-bullet shapes (1 bullet per shape, 4 shapes). |

---

## Dimension-by-Dimension Results

### D1 — Font Sizes

**Result: FAIL (residual issue on slide 18; systemic 20 pt pattern pre-existing)**

**Hard violation (accuracy-critical):**
- **Slide 18, TextBox 8**: bullet reads `"κ = 0.690 (Y threshold) and κ = 0.818 (Y+P threshold)"` — the `0.818` value is also a D4 accuracy issue (see below). Should be `0.816`.

**Systemic 20 pt pattern (pre-existing, affects 30+ slides):**

The presentation body text floor is set to **20 pt** in the slide generator, not 24 pt. Affected shape categories:

| Category | Slides | Verdict |
|----------|--------|---------|
| Section overview bullets (slide overview nav) | 4 | Below floor |
| Pipeline stage labels / diagram labels | 9, 10 | Compact diagram — borderline |
| Failure-mode category headers | 40, 41, 43, 44 | 20 pt headers |
| Demo tier labels ("TIER: TRUST", "HYPOTHESIS") | 6, 63–67 | Compact UI mock — borderline |
| Primary content bullets | 11, 46, 47, 48, 53, 61 | Below floor |
| Roadmap/phase labels | 70, 71 | 18–20 pt |

**Specific non-italic sub-24pt items that are NOT exempt captions:**
- Slide 4: all 5 section-overview bullets at 20 pt
- Slide 11: body bullets at 20 pt
- Slide 17: "Partial / useful" (22 pt), "Topic hijack / dangerous" (22 pt), REF/HYP quote lines (18 pt non-italic), "Therefore we built IS" (20 pt non-italic bold)
- Slide 34: footnote bullets at 15 pt (5 bullets, see D3)
- Slide 36: "LLM Judge Y+P" annotation at 18 pt; stat labels at 20 pt
- Slide 39: failure-mode bar chart labels at 18 pt
- Slides 69, 71: IS trajectory labels at 18 pt
- Slide 72: body bullets at 22 pt

**Exempt (per STYLE_GUIDE rules):**
- Bottom-left slide-number labels (12 pt) — all 79 slides
- Italic captions/footnotes at 18–20 pt throughout (chart companions, source citations)

**Summary:** The 24 pt floor was not applied uniformly in the original generator. The "fixed" slides (17, 24, 75) now have their primary bullets at 24 pt, but secondary/supporting text (quote lines, footnotes, labels) remains below floor. This is a generator-level issue requiring a sweep pass to be fully resolved.

---

### D2 — OOXML Layout Overlaps

**Result: PARTIAL PASS (intentional card-stack patterns are expected; residual true text-over-text overlaps remain)**

Most flagged overlaps are intentional stacked-card designs where:
- A header label sits at the top of a card rect and the body text starts slightly below
- Ref/Hyp quote blocks are layered with commentary text beneath

**True text-over-text overlaps that are likely rendering problems:**

| Slide | Overlap | Y-overlap |
|-------|---------|-----------|
| 17 | Content text boxes 10/11, 12/14, 14/15, 15/16 cascade downward | 0.12"–0.35" |
| 40 | Rule text + example arrows overlap (0.35") | 0.35" |
| 58 | ROVER bullet block + MBR results block (0.80") | 0.80" |
| 72 | Section header "LLM Upgrade" + body bullets (0.45") | 0.45" |
| 75 | Four column blocks (4 pairs each 0.98" overlap) — columns visually overlap | up to 0.98" |

**Slide 75 is the most severe:** four column text boxes (TextBox 4–8) each overlap their neighbor by ~0.98". This is a layout problem — the columns are stacked vertically but their Y ranges substantially overlap, meaning text from one column likely renders over the next.

Slides 20–24, 30, 31, 43, 44, 46, 48, 50, 51, 55, 61 show overlaps that appear to be intentional stacked card patterns (header → body → footnote within a card block) — these are expected.

---

### D3 — Bullet Count

**Result: FAIL (5 shapes exceed 4-bullet cap)**

| Slide | Shape | Bullets | Content |
|-------|-------|---------|---------|
| 2 | TextBox 4 | **6** | "What was done?" overview bullets |
| 3 | TextBox 4 | **6** | Key findings overview bullets |
| 34 | TextBox 5 | **5** | NIV explanation footnote block |
| 61 | TextBox 6 | **5** | v1 judge comparison (left column) |
| 61 | TextBox 9 | **5** | v3 judge comparison (right column) |

Slides 2 and 3 are the overview/agenda slides; 6 bullets may be intentional for completeness but violates the STYLE_GUIDE 4-bullet cap. Slides 34 and 61 carry 5 tightly-packed analytical bullets — each could lose 1 bullet by merging or cutting a less critical point.

---

### D4 — Accuracy

**Result: FAIL (one remaining stale value)**

| Slide | Issue | Current | Should Be |
|-------|-------|---------|-----------|
| **18** | TextBox 8, bullet 3 | `κ = 0.818 (Y+P threshold)` | `κ = 0.816` |

All other forbidden patterns confirmed absent:
- `r=0.85`: not found on any non-hidden slide
- `≥0.8 trust`: not found
- `Effort: 2`: not found
- `60% to ~20%`: not found
- Slides 35 and 78: correctly show `0.816`
- Slide 47: correctly shows `T_safe=0.82, T_trust=0.89`

**Note on slide 18:** The value `0.818` appears in a methodology description ("Used as gold standard to calibrate IS thresholds"). Per MEMORY, `0.818` was from a slightly different IS computation run; the canonical recomputed value is `0.816`. The same fix applied to slides 35 and 78 was missed here.

---

### D5 — Story Arc

**Result: PASS**

Slide sequence is coherent. Section dividers confirmed:
- Slide 16: "RESEARCH FINDINGS — Understanding What does 'Working' mean, What Works, and Why"
- Slide 38: "FAILURE ANATOMY — Where the System Fails and Why"
- Slide 68: "FUTURE DIRECTIONS — From Analysis to Action"

Title sequence flows logically: intro (1–15) → research findings (16–37) → failure anatomy (38–44) → confidence/aggregation (45–67) → future directions (68–79).

Slide 45 ("Confidence Without Ground Truth" — problem framing) correctly precedes slide 46 ("Two Layers of Confidence" — solution). The swap fix is confirmed in place.

**No slides appear to be in the wrong order or missing from the narrative.**

---

### D6 — Detail Density

**Result: BORDERLINE (several slides exceed 8 words per bullet but most are quote annotations)**

The slides most at risk from density overload:

| Slide | Issue | Worst item |
|-------|-------|-----------|
| 28 | 29-word technical explanation of SBERT embedding | "1. Reference and hypothesis become 384-dim sentence embeddings via SBERT (all-MiniLM-L6-v2)..." |
| 30 | 20–26 word PCA explanations | "All 5 content signals load equally (0.43–0.47). Semantic is NOT independent..." |
| 55 | 30-word "WHY ADD AGREEMENT?" block | Single dense run-on |
| 78 | 5 bullets each 15–19 words | Takeaways slide packs a lot |

Most long items on other slides (15–22) are quote excerpts (REF/HYP pairs) which are inherently long — these are not bullets, they are data examples, and don't violate the spirit of the 8-word cap.

Slides 28, 30, 55, 78 contain genuine body text bullets that exceed 8 words and could be trimmed.

---

### D7 — Graphics / Visuals

**Result: PASS**

All 79 non-hidden slides have at least one embedded image. No shapes with "Picture N" placeholder names indicating broken image links were found. The LibreOffice caveat (images rendering as "Picture N...") does not apply — images are properly embedded in the OOXML package.

---

### D8 — Notes Coverage

**Result: PASS**

All 79 non-hidden slides have substantive speaker notes (>20 chars). Key results slides have detailed notes:
- Slide 11 (benchmark): 855 chars
- Slide 18 (LLM judge gold standard): 1,546 chars
- Slide 36 (oracle vs realistic): 1,412 chars
- Slide 58 (N-best aggregation): 657 chars
- Slide 70 (5-phase roadmap): 2,237 chars
- Slide 78 (key takeaways): 1,665 chars

No key slides are missing notes.

---

## Priority Fix List

These are the remaining actionable items, ranked by importance:

### P1 — Accuracy (must fix before presenting)
**Slide 18, TextBox 8:** Change `κ = 0.818 (Y+P threshold)` → `κ = 0.816 (Y+P threshold)`

This is the same fix already applied to slides 35 and 78 — it was missed on slide 18.

### P2 — Bullet Count (polish)
**Slides 2 and 3:** Each has 6 bullets. To comply with the 4-bullet cap, consider:
- Slide 2: Merge "Built end-to-end pipeline" + "Migrated to standalone container" into one bullet
- Slide 3: Merge "Mission 6 shipped: MBR n-best is default" + "v3 Judge MBR Y+P 71% vs base 68%, p=0.00017" into one bullet

**Slides 34 and 61:** 5 bullets each. Slide 34 NIV footnote could drop the "IS beats WER by +0.06 κ" bullet (already shown in the scatter plot). Slide 61 left column could drop the "Bias: against n-best variants" bullet (redundant given the Y+P result stated above it).

### P3 — Font Floor sweep (generator-level)
The 20 pt body text pattern is pervasive (30+ slides). The STYLE_GUIDE floor is 24 pt. A generator-level fix is needed to bump all non-exempt non-italic body runs from 20 pt → 24 pt. Key slides with the most visible 20 pt body text:
- Slides 4, 11, 17, 40, 46, 47, 48, 53, 61, 72 (primary body bullets at 20 pt)
- Slide 17 additionally has 18 pt non-italic REF/HYP quote lines and 22 pt category headers

**Note:** Slide 34 has 15 pt bullets (the NIV footnote block) — this is severe and should be bumped to 24 pt or moved to notes.

### P4 — Layout overlap (slide 75 most severe)
Slide 75 has 4 column text boxes with ~0.98" Y overlap each. This means the columns are visually stacked rather than side-by-side. Verify the layout renders correctly in PowerPoint — if the columns are on the correct X positions they may visually not overlap even if their Y ranges do. If they do visually overlap, the column spacing needs adjustment.

---

## Dimensions Summary Table

| Dimension | Result | Issues Remaining |
|-----------|--------|-----------------|
| D1 Font floor (24pt) | **FAIL** | Pervasive 20pt body text; 15pt on slide 34; 18pt on slides 17, 36, 39, 41–44, 54, 69, 71 |
| D2 OOXML overlaps | **PARTIAL** | Residual real overlaps: slides 17, 40, 58, 72, 75 (severe) |
| D3 Bullet count | **FAIL** | Slides 2, 3 (6 bullets); slides 34, 61 (5 bullets) |
| D4 Accuracy | **FAIL** | Slide 18: κ=0.818 should be 0.816 |
| D5 Story arc | **PASS** | Clean |
| D6 Detail density | **BORDERLINE** | Slides 28, 30, 55, 78 have long body bullets; quote lines are expected |
| D7 Graphics | **PASS** | All slides have images |
| D8 Notes | **PASS** | All 79 slides have substantive notes |
