# Argos VSP — Post-AMOSI Audit Diff (vs March 2026 master)

Generated 2026-05-06. Compares the freshly rendered academic deck
`Argos_VSP_AFTER_AMOSI_May2026.pptx` (89 slides, 9 hidden) against the
March 2026 master `Argos_VSP_Final_84slides_Mar2026.pptx` (84 slides, 10
hidden). Reference audit JSONs:

- New: `/home/ubuntu/docs/evaluation/pptx_visual_audit_after_amosi.json`
- Old: `/home/ubuntu/docs/evaluation/pptx_visual_audit.json`

Audit script: `/home/ubuntu/scripts/audit_pptx_visual_structure.py`.

---

## 1. BLOCKER count — new vs old

| Deck | BLOCKERs | Notes |
|------|----------|-------|
| Old master (`Final_84slides_Mar2026`) | **4** | 1 anim orphan slide 7, 2 anim orphans slides 47/48, 1 off-canvas Picture slide 52 |
| New deck (`AFTER_AMOSI_May2026`) | **8** | 2 off-canvas tables (53, 60), 6 anim orphans on demo slides (63, 64, 65, 66, 67, 68) |

Goal of "zero new BLOCKERs" was **NOT met** — 8 BLOCKERs (one regressed, six new on demo block, the off-canvas regression is on a different shape than the old one).

### BLOCKER list (new deck)

| # | Slide | Title | Category | Description |
|---|-------|-------|----------|-------------|
| 1 | 53 | Three Calibrated Thresholds on Segment mean_prob | LAYOUT | `Table 4` bbox right=13.70 in, canvas right=13.33 in (over by 0.37 in) |
| 2 | 60 | N-best Aggregation: v3 Judge Paired Tests | LAYOUT | `Table 5` bbox right=13.70 in (over by 0.37 in); also vertically overlaps the right-side TextBox 6 (table bottom 4.55, textbox top 4.45) |
| 3 | 63 | Demo: OK → Almost There → Hallucination | ANIMATION | Animation references `spid='7'` and `spid='10'` — no shapes with those ids on the slide (ids run 2,3,5,6,8,9,11-15) |
| 4 | 64 | Demo - Obama Trust Tier | ANIMATION | Animation references `spid='7'` — no such shape (ids 2,3,4,5,6,8,9,10,11,12,13,14) |
| 5 | 65 | Demo - Obama Salvage Tier (partial recovery) | ANIMATION | Same `spid='7'` orphan |
| 6 | 66 | Demo - INSPECT … (lowest mean_prob = 0.799) | ANIMATION | Same `spid='7'` orphan |
| 7 | 67 | Demo - Strip: entity swap auto-flagged | ANIMATION | Same `spid='7'` orphan |
| 8 | 68 | Demo - Salvage: technical vocabulary drift | ANIMATION | Same `spid='7'` orphan |

Root cause for the demo-block orphans: each slide's shape ids skip `7` (jumping 6 → 8). The shape was deleted in the slide builder but the animation timing block still has a `spTgt @spid="7"` entry. PowerPoint will throw a "missing target" warning when these slides advance.

---

## 2. MAJOR issues introduced by the new content

Targeted slides per the audit brief: 13, 16, 31, 33, 37, 38, 44–62, 64–68, 83, 84, 88.

### Slide 13 — Diversity of Inputs — Not LRS3 (NEW)

- 1 MAJOR: `TextBox 6` body font 11pt ("Sample lip-reading frame…")
- 1 MINOR: no corner logo

### Slide 16 — What the AVSR Literature Reports vs What Users Get (NEW)

- 1 MAJOR overlap: `TextBox 6` ("• WER (Word Error Rate)…") and `TextBox 7` ("All three failure modes…") overlap by **36%** of smaller bbox — this is a layout collision, not text-on-card.
- 1 MINOR overlap: `TextBox 14` & `TextBox 15` overlap by 30% (REF/HYP block over commentary).
- 1 MINOR notes mismatch (body shows 25%, notes only 50%).

### Slide 31 — Do 6 Signals Actually Measure 6 Things? (PCA)

- 0 MAJOR. 3 MINORs (logo, notes citation, body 87% vs notes 5/19/68/93%).
- Two-PC framing renders cleanly.

### Slide 33 — Two Dimensions of Quality (PCA)

- 0 MAJOR. 1 MINOR (no corner logo). Clean.

### Slide 37 — Where the System Works: Oracle vs Realistic (NEW two-card)

- **14 MAJOR style violations**: this slide uses 11pt body text on every card title and every tier counter (TextBox 5/9/12/16/17/19/20/22/23/25/26/28/29/31). Every shape that should carry the "headline" of a card is sub-12pt.
- 1 MINOR layout: `TextBox 28` is 0.03 in from right edge.

### Slide 38 — From Literature Metric to User-Trusted Output (NEW transition)

- 0 MAJOR. 1 MINOR (no corner logo). Clean.

### Slide 44 — LLM Salvage: Domain Context Fills the Gaps (NEW)

- **21 MAJOR style violations** — every TextBox (6/7/8/9/10/11/12/15/16/17/18/19/20/21/24/25/26/27/28/29/30) is at 9–10pt. This is the densest font failure on the deck.
- 6 MINOR overlaps (Reference/Prediction labels overlap their own body text).

### Slides 45–49 (the appendix-style + confidence intro slides)

- **Slide 45** — A6: Failure Mode Examples. Hidden? **No**. Numbered "A2" but visible — see numbering issue below. Otherwise clean.
- **Slide 46** — Confidence Without Ground Truth. Clean.
- **Slide 47** — Two Layers of Confidence. Clean.
- **Slide 48** — Phase 1: Confidence Scoring. Clean.
- **Slide 49** — Per-Word Confidence Bands - Distribution. Clean.

### Slides 50–58 (confidence band + threshold slides — heaviest density risk)

- **Slide 50** — Band Reliability. 1 MAJOR overlap (`TextBox 6` & `TextBox 7` overlap by **48%**) — caveat-text collides with main bullet block. 1 MAJOR style 11pt.
- **Slide 51** — Green Reliability Depends on Segment Quality. 2 MAJOR style (11pt + 9pt caveat). 1 MINOR overlap caveat over headline (15%).
- **Slide 52** — Green Leakage. 3 MAJOR style — example annotations all at 11pt.
- **Slide 53** — Three Calibrated Thresholds. **BLOCKER (Table 4 off-canvas)**. 1 MAJOR style (11pt). 1 MINOR overlap (24%).
- **Slide 54** — Three-Tier Policy. Clean.
- **Slide 55** — Per-Word Bands Stratified by NIV Outcome. 2 MAJOR style (11pt) + 1 MINOR overlap (27%).
- **Slide 56** — Joint Confidence + Beam-Agreement Band Rule. 1 MAJOR style + 1 MAJOR overlap (`TextBox 14` + `TextBox 15` overlap by **48%**).
- **Slide 57** — Beam Agreement Adds Independent Signal. 1 MAJOR style (11pt diagnostic-script footer).
- **Slide 58** — Trust-Gate Operating Points. 1 MAJOR style (11pt audit-keys footer).

### Slides 59–62 (n-best aggregation + judge-prompt-design)

- **Slide 59** — Phase 2: Exploit All 20 Hypotheses. 3 MAJOR style — citations footer at **8pt** (the smallest font on the deck), and "ROVER" / "MBR" headings at 11pt.
- **Slide 60** — N-best Aggregation: v3 Judge. **BLOCKER (Table 5 off-canvas)**. 2 MAJOR style + 1 MAJOR overlap (TextBox 6 + 7 overlap **45%**).
- **Slide 61** — Why MBR Won the Default-Display Slot. 1 MAJOR style + 1 MAJOR overlap (`TextBox 7` & `TextBox 8` overlap by **95%** — body text on top of body text).
- **Slide 62** — v1 vs v3 Judge: A Prompt-Design Lesson. Clean.

### Slides 64–68 (NEW demo block)

Each of these 5 slides has the same pattern (so I list the per-slide issue once):

- BLOCKER: orphan animation `spid='7'`.
- 2 MAJOR style: `REFERENCE` / `HYPOTHESIS` headers at 10pt.
- 1 MAJOR overlap: `TextBox 11` (research observation) overlaps `TextBox 13` (slide-num "62"/"63"/…) by **72%** — the observation block runs over the bottom-left slide-number label.
- 2 MAJOR VIDEO: false positives (the audit script's `rglob` shadowed top-level files with `_archive_pre_may6/` duplicates of same name; embedded videos all match top-level files correctly). **Ignore — script bug, not a deck bug.**

### Slide 83 — Appendix: PCA Loadings (HIDDEN, NEW)

- 2 MAJOR style (11pt body + 11pt source line).
- 1 MAJOR overlap: `TextBox 9` (source) and `TextBox 11` (slide-num "A5") overlap by **72%** — same pattern as demo slides where body text covers the slide-number label.

### Slide 84 — Appendix: Human-IS Path B (HIDDEN, NEW)

- 1 MAJOR style (11pt caveat). Otherwise clean.

### Slide 88 — Appendix: McNemar Tests (HIDDEN, NEW)

- 1 MAJOR style (11pt caveat).
- 1 MAJOR overlap: `TextBox 7` & `TextBox 9` (slide-num "A10") overlap by **92%** — text-over-num issue again.
- 1 MINOR notes citation.

---

## 3. MAJOR issues inherited from the March master

Mapping old-deck slide indices to new-deck content:

| New | Old (Mar) | Title | Old issues that carried over |
|-----|-----------|-------|------------------------------|
| 13 | (NEW) | Diversity of Inputs | n/a — net new |
| 16 | (NEW) | Literature vs Users | n/a — net new |
| 31 | 27 | Do 6 Signals Measure 6 Things? | none MAJOR |
| 33 | (NEW) | Two Dimensions of Quality (PCA) | n/a — net new |
| 37 | (NEW) | Oracle vs Realistic two-card | n/a — net new |
| 38 | (NEW) | Literature → User-Trusted transition | n/a — net new |
| 42 | 40 | Failure Modes: Real Examples | INHERITED — 21 MAJOR style (9–10pt) was already in old deck |
| 43 | n/a | (LLM Salvage: Three Real Recoveries) | INHERITED — old slide 45 had 21 MAJORs; new slide 43 has the same 9pt/10pt pattern |
| 44 | 46 | LLM Salvage: Domain Context Fills the Gaps | INHERITED — same 21-MAJOR style block |
| 63 | 48 | Demo: OK → Almost There → Hallucination | INHERITED BLOCKER — old slide 48 also had orphan-anim spid='4'/'7'/'10' |
| 64–68 | (NEW) | Demo - Obama / Strip / Salvage block | n/a — net new (but inherits the demo-block style choices) |
| 81 (hidden A1) | 77 | Homophenes | none MAJOR new |
| 82 (hidden A3) | 78 | IS Component Correlation | none MAJOR new |
| 83 (hidden) | (NEW) | PCA Loadings | n/a — net new |
| 84 (hidden) | (NEW) | Human-IS Path B | n/a — net new |
| 88 (hidden) | (NEW) | McNemar Tests | n/a — net new |

---

## 4. Slides cleared (old issues now resolved)

| Old slide | Title | Old severity | Status in new deck |
|-----------|-------|--------------|--------------------|
| 7 | What is Visual Speech Processing? | BLOCKER (anim orphan spid='4') | **Cleared** — corresponding new slide 5 has 0 BLOCKERs |
| 47 | Curated Examples — Video Gallery | BLOCKER (5 anim orphans) | **Cleared** — replaced by slides 19–24 (single-example judge slides), no orphans |
| 52 | 8-Stage Automated Pipeline | BLOCKER (Picture 3 off-canvas) | **Cleared** — pipeline slide rebuilt; no off-canvas in new deck (off-canvas is now on tables 53/60 instead) |

---

## 5. Font violations — every shape with body text < 12pt (new deck)

**Total: 174 shapes flagged**. 11pt is the dominant violation; 9–10pt clusters appear on the LLM salvage example blocks (slides 41-44) and the demo-block REFERENCE/HYPOTHESIS headers (64–68); 8pt appears once on slide 59 (`TextBox 13`, "ROVER: Fiscus (1997), NIST | MBR Decod…") and once on slide 73 (`TextBox 12`, citation footer).

**Worst clusters** (counts of <12pt shapes per slide):

| Slide | Title | <12pt shape count | Smallest pt |
|-------|-------|-------------------|-------------|
| 41 | (LLM Salvage 1/3) | 21 | 9pt |
| 42 | Failure Modes: Real Examples | 21 | 9pt |
| 43 | (LLM Salvage 2/3) | 21 | 9pt |
| 44 | LLM Salvage: Domain Context | 21 | 9pt |
| 37 | Oracle vs Realistic | 14 | 11pt |
| 64–68 | Demo block (×5) | 2 each | 10pt |
| 59 | Phase 2: Exploit All 20 Hypotheses | 3 | **8pt** ← worst |
| 73 | Stronger LLM + Smart Prompts | 1 | **8pt** |
| 71 | (Phase 1–5 roadmap) | 6 | 8pt |
| 53 | Three Calibrated Thresholds | 1 | 11pt |
| 56 | Joint Confidence + Beam | 1 | 11pt |
| 60 | N-best Aggregation v3 Judge | 2 | 10pt |
| 50, 51, 52, 55, 57, 58, 61 | (confidence section) | 1–3 each | 9–11pt |

(Full row-level listing is in `pptx_visual_audit_after_amosi.json` — every entry with category="STYLE" and "below 12pt" in description.)

For an academic talk projected on a 4K screen at 12 ft, the 9–10pt blocks on slides 41–44 are the audience-readability risk; 11pt is a borderline judgment call but acceptable on dense slides if there's contrast.

---

## 6. Title-truncation risk (titles > 70 chars)

Only **one** slide in the new deck:

| Slide | Length | Title |
|-------|--------|-------|
| 66 | 76 chars | "Demo - INSPECT (closest to STRIP in the Obama set; lowest mean_prob = 0.799)" |

Per the brief, this was a known truncation. In the rendered deck the title still spans 76 chars. The title-bar shape on this slide (per the layout audit) is `TextBox 1` at width 12.13 in, so on a standard 16:9 widescreen it should fit at 28pt — but in compatibility-mode rendering or smaller projection windows it will wrap to two lines. Recommended fix below.

---

## 7. Video tile verification

Cross-referenced against `06_demo_videos/` **top-level only** (the audit script's `rglob` produces false positives because of `_archive_pre_may6/` shadows; corrected results below):

| Slide | Title | media partname | Embedded size | Top-level disk file | OK? |
|-------|-------|----------------|---------------|---------------------|-----|
| 19 | Judge Example 1: Named Entity Swap | media2.mp4 | 1,375,351 | 4D634qUi2BI_0__93a9f2b4_with_hyp.mp4 | YES |
| 20 | Judge Example 2: Truncated but Core | media3.mp4 | 1,045,892 | VfJ-6nQAmtk_22__4a7cbfd1_with_hyp.mp4 | YES |
| 21 | Judge Example 3: Technical Vocab | media4.mp4 | 2,540,214 | c6eBrYor21I_10__70697c08_Part1_with_hyp.mp4 | YES |
| 22 | Judge Example 4: Scientific Vocab | media5.mp4 | 2,330,286 | 9HanJOCw2Sc_11__19c7ec4e_with_hyp.mp4 | YES |
| 23 | Judge Example 5: Cooking Domain | media6.mp4 | 751,137 | a2CS82VZyO4_7__a6316c95_with_hyp.mp4 | YES |
| 24 | Judge Example 6: Topic Hijack | media7.mp4 | 3,290,665 | tUcgHemnJiQ_0__2fc132c1_with_hyp.mp4 | YES |
| 63 | Demo: OK → … → Hallucination | media8.mp4 | 2,796,612 | ktMebjnZiSE_3__ebdf1351_with_hyp.mp4 | YES |
| 63 | "" | media9.mp4 | 463,500 | 2HddWQse8Mw_0__8ecb0409_with_hyp.mp4 | YES |
| 63 | "" | media10.mp4 | 1,333,853 | 00MUdHQ7GGY_8__b1480c7a_with_hyp.mp4 | YES |
| 64 | Demo - Obama Trust Tier | media11.mp4 | 3,119,635 | 050111_OsamaBinLadenStatement_HD_14_004195_004555.mp4 | YES |
| 65 | Demo - Obama Salvage Tier | media12.mp4 | 3,128,275 | 050111_OsamaBinLadenStatement_HD_31_009290_009650.mp4 | YES |
| 66 | Demo - INSPECT | media13.mp4 | 2,520,000 | 050111_OsamaBinLadenStatement_HD_05_001498_001858.mp4 | YES |
| 67 | Demo - Strip: entity swap | media2.mp4 | 1,375,351 | 4D634qUi2BI_0__93a9f2b4_with_hyp.mp4 | YES |
| 68 | Demo - Salvage: technical vocab | media4.mp4 | 2,540,214 | c6eBrYor21I_10__70697c08_Part1_with_hyp.mp4 | YES |

Slides 9 (pipeline), 14 (visemes GIF), 18, 42 (failure examples), 47 (video gallery), 73 (web UI?) — **no media relationships found** on those slides. They use pictures (PNG/GIF), not embedded videos. This is consistent with the layout brief.

**Verdict**: every embedded video is wired to an existing top-level mp4. The 10 audit "VIDEO MAJOR" warnings on slides 64-68 are false positives caused by the `audit_pptx_visual_structure.py:list_video_files()` `rglob` walking `_archive_pre_may6/` and overwriting the top-level same-name files in the size-index dict.

---

## 8. Hidden-slides correctness

**Expected**: exactly 9 hidden, all appendix.

**Actual** (slides 81–89, all hidden):

| New idx | Slide-num label | Title | Hidden? |
|---------|-----------------|-------|---------|
| 81 | A3 | A1: Homophenes — The Lip-Reading Problem | YES |
| 82 | A4 | A3: IS Component Correlation | YES |
| 83 | A5 | Appendix: PCA Loadings on the 6 IS Signals | YES |
| 84 | A6 | Appendix: Human-IS Path B (Pre-Study Estimates) | YES |
| 85 | A7 | A4: LLM Salvage — Recoverable Segments | YES |
| 86 | A8 | A5: LLM Salvage — Curated Examples | YES |
| 87 | A9 | A9: Context Evaluation — Transition Details | YES |
| 88 | A10 | Appendix: McNemar Tests — N-Best Methods vs Baseline | YES |
| 89 | 79 | Two Environments: Development and Production | YES |

**Hidden count: 9 — correct.**

But there are **slide-number labelling inconsistencies** (cosmetic show-stopper for academic talk):

- **Slide 36** (visible) labelled "A1" but this is content `A8: LLM Judge × IS Tier Cross-Tabulation` — appendix label on a promoted-to-main slide.
- **Slide 45** (visible) labelled "A2" but this is content `A6: Failure Mode Examples` — same issue.
- **Slide 89** (hidden) labelled "79" — appendix-content slide carries a main-deck label.

The label sequence in slide-order should be: 1–35 (matching), then 36 (currently "A1"), 37–N (currently 36–78), then A1–A11 in appendix. Re-labelling needs to fix slides 36, 45 and appendix.

Per the brief, the previously-hidden academic-content slides:

- "Executive Summary" — old slide 4 was hidden, NEW deck has corresponding content woven into slides 1–4 as the "What was done?" intro. Confirmed not hidden in new deck.
- "WER: The Metric That Lies" — old slide 5 was hidden; new deck has slide 35 "The Gap: Where WER Lies Most" — visible.
- "Where IS and the Judge Disagree" — old slide 34 was hidden; new deck has slide 25 "Where IS and the Judge Disagree" — visible.
- "Context Exposes Hidden Failures" — old slide 35 was hidden; new deck has slide 26 "Context Exposes Hidden Failures" — visible.

All four were promoted as required. **Pass.**

---

## 9. Animation flow — orphan check summary

| Severity | Count | Slides |
|----------|-------|--------|
| BLOCKER orphan-anim | 6 | 63, 64, 65, 66, 67, 68 |
| MINOR para-build flag | 0 | n/a |
| MINOR multi-card no-anim | (a few — not BLOCKER level) | various |

The animation flow works on slides 1–62 (no orphan refs). The demo block (63–68) needs the timing block scrubbed to drop `spTgt @spid="7"` (and on 63, also `"10"`).

---

## 10. Issue totals — old vs new

| Severity | Old `Final_84slides_Mar2026` | New `AFTER_AMOSI_May2026` | Δ |
|----------|------------------------------|---------------------------|---|
| BLOCKER | 4 | **8** | +4 |
| MAJOR | 183 | **218** | +35 |
| MINOR | 193 | **190** | −3 |
| TOTAL | 380 | **416** | +36 |
