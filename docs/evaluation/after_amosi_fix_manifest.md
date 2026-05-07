# Argos VSP — Post-AMOSI Fix Manifest

**Target deck**: `/home/ubuntu/presentation_materials_20260224/Argos_VSP_AFTER_AMOSI_May2026.pptx`

**Generated**: 2026-05-06.

Read-only audit; no fixes have been applied. Slide-builder function names are
inferred from the slide titles — the canonical set is in
`/home/ubuntu/docs/_research-tools/generators/presentation/slides/`. Severity
ladder for an academic peer audience: BLOCKER (deck breaks visibly during
presentation), MAJOR (unmistakable cosmetic embarrassment), MINOR (only the
auditor will notice).

---

## P0 — BLOCKER fixes (all 8 must be resolved before showtime)

### 1. Slide 53 — `slide_three_thresholds`: Table 4 right-edge off-canvas

- **Severity**: BLOCKER (LAYOUT)
- **Symptom**: `Table 4` bbox right=13.70 in, canvas right=13.33 in. Right-most column **clips off the slide** when projected.
- **Fix**: Reduce table width to ≤12.73 in (the standard content-area right edge after MX=0.6 in margins). Either narrow the right-most column or set `table_width = SLIDE_W - 2*MX`.
- **Function**: likely `slide_three_thresholds` (or `slide_three_calibrated_thresholds`).

### 2. Slide 60 — `slide_nbest_aggregation_v3`: Table 5 right-edge off-canvas + vertical overlap

- **Severity**: BLOCKER (LAYOUT)
- **Symptom**: `Table 5` bbox right=13.70 in (clips), AND its bottom (4.55) cuts into the right-side `TextBox 6` whose top is 4.45.
- **Fix**: (a) cap table width to 6.0 in (left column anchored at 7.30 in → right edge 13.30 in), (b) shift table top from 2.05 → 1.95 OR shrink table height by 0.15 in to clear `TextBox 6`. Best fix: snap to the same `right_card` bbox the rest of the deck uses for two-column layouts.

### 3. Slide 63 — `slide_demo_three_videos`: Animation orphan `spid='7'` and `spid='10'`

- **Severity**: BLOCKER (ANIMATION)
- **Symptom**: `<p:spTgt spid="7"/>` and `<p:spTgt spid="10"/>` reference shape ids that don't exist on this slide (existing ids: 2, 3, 5, 6, 8, 9, 11, 12, 13, 14, 15). PowerPoint emits a "missing animation target" warning and may skip click-step.
- **Fix**: in the slide-builder, after the shape that should be animated is created, capture its `shape_id` immediately and use that captured id in the `add_click_step()` call rather than hard-coding numeric ids. If shapes 7 and 10 were intentionally deleted, drop the corresponding entries from `seq` / `paraBuild` lists.

### 4–8. Slides 64, 65, 66, 67, 68 — `slide_demo_obama_trust` / `slide_demo_obama_salvage` / `slide_demo_inspect` / `slide_demo_strip` / `slide_demo_salvage_tech`: Animation orphan `spid='7'`

- **Severity**: BLOCKER (ANIMATION) — 5 slides, identical pattern.
- **Symptom**: All five slides have shape ids 2–6, 8–14 (i.e. id 7 is missing) but their animation timing references `spid='7'`.
- **Root cause**: A "Rectangle 6" (or similar) was deleted from these slides during a content edit, but the animation timing wasn't updated.
- **Fix**: Two options:
  - (recommended) Re-stitch the timing block after shape construction — iterate live shapes, build the click sequence from `shape.shape_id` of currently-existing shapes only.
  - Or: delete the offending `spTgt @spid="7"` entries from `<p:timing>` on these 5 slides.

---

## P1 — MAJOR layout fixes (cosmetic show-stoppers)

### 9. Slide 16 — `slide_literature_metrics_problem`: TextBox 6 / TextBox 7 overlap 36%

- **Severity**: MAJOR (OVERLAP)
- **Symptom**: WER bullet block sits on top of the failure-modes commentary.
- **Fix**: shift `TextBox 7` down by ~0.4 in or move into a right-hand column.

### 10. Slide 50 — `slide_band_reliability_overall`: TextBox 6 / TextBox 7 overlap 48%

- **Severity**: MAJOR (OVERLAP)
- **Symptom**: caveat block (`All numbers from audit JSON…`) sits over the headline insight (`Joint rule's biggest reliability…`).
- **Fix**: move caveat to footer band (top=6.20+) or reduce its width and right-anchor it.

### 11. Slide 56 — `slide_joint_band_rule`: TextBox 14 / TextBox 15 overlap 48%

- **Severity**: MAJOR (OVERLAP)
- **Symptom**: "Llama-2-7b specific…" footnote overlays "WHY ADD AGREEMENT?" headline by half.
- **Fix**: same pattern — move caveat to a dedicated bottom strip or shrink + right-justify.

### 12. Slide 60 — `slide_nbest_aggregation_v3`: TextBox 6 / TextBox 7 overlap 45%

- **Severity**: MAJOR (OVERLAP)
- **Symptom**: bullet block over audit-keys footer.
- **Fix**: pin audit-keys text to top=6.30, height=0.3 in.

### 13. Slide 61 — `slide_mbr_default`: TextBox 7 / TextBox 8 overlap **95%**

- **Severity**: MAJOR (OVERLAP) — this is the worst overlap on the deck.
- **Symptom**: "MBR mean per-word conf 0.867…" body text and "Wired via make_report.py --display-method…" body text are stacked at nearly the same coordinates. One of the two is invisible.
- **Fix**: drop one of the two TextBoxes (likely the duplicated "Wired via…" line meant to live in the footer); or move it to top=6.30 footer band.

### 14. Slide 83 — `slide_pca_loadings_appendix` (HIDDEN): TextBox 9 / TextBox 11 overlap 72%

- **Severity**: MAJOR (OVERLAP)
- **Symptom**: source-citation textbox sits on top of the slide-num label "A5".
- **Fix**: same fix as the demo-block pattern — shrink source-citation width or shift up by 0.15 in.

### 15. Slide 88 — `slide_mcnemar_appendix` (HIDDEN): TextBox 7 / TextBox 9 overlap 92%

- **Severity**: MAJOR (OVERLAP)
- **Symptom**: caveat textbox over the slide-num label "A10".
- **Fix**: pin caveat top to 6.20 in and width ≤ 11 in (clear of the slide-num label at left=0.60, top=7.12).

### 16. Slides 64, 65, 66, 67, 68 — same `slide_demo_*` builder family: TextBox 11 / TextBox 13 overlap 72%

- **Severity**: MAJOR (OVERLAP) — 5 slides.
- **Symptom**: "Research observation" body text covers the bottom-left slide-number label "62"/"63"/"64"/"65"/"66".
- **Fix**: shrink the "Research observation" block height OR shift it up by ~0.4 in. Should not collide with the page-num footer at (0.60, 7.12).

---

## P2 — MAJOR style fixes (font readability)

### 17. Slide 37 — `slide_07` (Oracle vs Realistic): 14 shapes at 11pt

- **Severity**: MAJOR (STYLE) — 14 instances on one slide
- **Fix**: bump tier-counter and card-headline body sizes from 11pt to 12pt minimum (preferably 14pt for headline rows). The two-card layout has enough horizontal real estate to support 14pt without rebreaking.

### 18. Slides 41, 42, 43, 44 — LLM-salvage three-example blocks: 21 shapes at 9–10pt each

- **Severity**: MAJOR (STYLE) — **84 total shapes across 4 slides** at 9–10pt. Note: slides 41, 42, 43 are INHERITED from the March master (carries over the same problem); slide 44 is new but uses the same template.
- **Fix** (single template change): in the slide-builder for `slide_06_failure_examples` / `slide_llm_salvage_three`, raise the per-card REF/PRED/INSIGHT body font from 9–10pt to 12pt. Either (a) trim text to fit at 12pt, or (b) widen each card to 4.0 in (currently 3 in 3-column layout) and split into 2-column 2-row grid, or (c) drop one of the three examples per slide and let the remaining two breathe at 14pt.
- Critical for an academic talk: the salvage examples are *the* most-cited content and the audience will want to read them.

### 19. Slide 59 — `slide_phase2_nbest`: TextBox 13 at **8pt** (worst on deck)

- **Severity**: MAJOR (STYLE)
- **Symptom**: Citation footer ("ROVER: Fiscus (1997), NIST | MBR Decoding…") at 8pt.
- **Fix**: raise to 10pt minimum (citations) or move to a "References" final slide.

### 20. Slides 64–68 — REFERENCE / HYPOTHESIS section labels at 10pt

- **Severity**: MAJOR (STYLE) — 10 shapes across 5 slides.
- **Fix**: raise from 10pt → 12pt minimum. These are visual section dividers; they should be more prominent than the body text, not less.

### 21. Slides 50, 51, 52, 53, 55, 56, 57, 58, 60, 61 — confidence/n-best section: TextBox at 11pt

- **Severity**: MAJOR (STYLE) — ~20 shapes total at 11pt.
- **Fix**: bulk pass — anything tagged with `body_p11` style should map to `body_p12` minimum. 11pt looks crisp on a laptop preview but is on the edge for a 2-hour academic projection.

### 22. Slides 71 (5-Phase Roadmap), 73 (Stronger LLM): 8pt citation footers

- **Severity**: MAJOR (STYLE)
- **Fix**: raise to 10pt or move citations into a single "References" slide.

---

## P1.5 — Slide-numbering inconsistencies (visible-but-A-labelled / hidden-but-numeric-labelled)

### 23. Slide 36 — visible but labelled "A1"

- **Severity**: MAJOR (STRUCTURE)
- **Symptom**: slide carries `A1` in the bottom-left number label, but slide is unhidden and visible in main flow.
- **Content**: "A8: LLM Judge × IS Tier Cross-Tabulation" — promoted from old appendix.
- **Fix**: re-run `add_slide_num` with the main-deck counter (probably `36`).

### 24. Slide 45 — visible but labelled "A2"

- **Severity**: MAJOR (STRUCTURE)
- **Symptom**: `A2` label on a visible slide ("A6: Failure Mode Examples").
- **Fix**: relabel to its main-deck index (probably `44`).

### 25. Slide 89 — hidden but labelled "79"

- **Severity**: MINOR (STRUCTURE)
- **Symptom**: appendix slide ("Two Environments") carries a main-deck label "79".
- **Fix**: relabel to `A11` for consistency with neighbours.

(Net effect of #23–25: visible slide numbering should run 1, 2, …, 35, 36 (currently A1), 37, …, 44 (currently A2), 45, …, 80; appendix A1–A11 on slides 81–89.)

---

## P3 — MINOR / cosmetic (not show-stoppers)

- 80+ "no corner logo" MINOR flags across the deck — every slide post-title-slide is missing the ~0.35 in corner logo per the `add_logo` helper. This is a uniform omission, so not jarring, but worth a single bulk pass.
- ~12 "speaker notes have no source citation" MINORs — academic-talk leniency applies; only worth fixing if the notes will be published.
- ~15 "body % vs notes %" mismatch heuristic flags — these are mostly false positives (the heuristic is too tight; e.g. body says "65% useful" notes mention "60% / 80%"); skip unless reviewing notes.
- 1 MINOR "TextBox 28 within 0.03 in of right edge" on slide 37 — visually invisible but technically inside the safe-margin band.

---

## Suggested fix order (single PR/commit)

1. **Demo-block animation cleanup** (slides 63–68): single helper rewrite that re-stitches `<p:timing>` from live shape ids. Resolves 6 of 8 BLOCKERs.
2. **Two off-canvas tables** (slides 53, 60): cap table widths to fit canvas. Resolves remaining 2 BLOCKERs.
3. **Slide-number label fix** (slides 36, 45, 89): single `add_slide_num` argument override. Cosmetic but obvious to academic audience.
4. **Slide 61 TextBox 7/8 95% overlap**: drop the duplicate/footer textbox.
5. **Salvage-example slides 41–44 font bump**: 9–10pt → 12pt template change. Single biggest readability win.
6. **Demo-block REFERENCE/HYPOTHESIS labels** (slides 64–68): 10pt → 12pt.
7. **Citation footers** (slides 59, 71, 73): 8pt → 10pt or move to a References slide.
8. **Caveat-block overlaps** (slides 16, 50, 56, 60, 83, 88): pin caveats to footer band.

After applying these, expected post-fix counts:
- BLOCKER: 0 (from 8)
- MAJOR: ≤ 30 (from 218; the bulk of MAJORs are the 84 9–10pt + 5 demo-overlap that get cleaned by template changes)
- MINOR: 190 (mostly logo + notes-citation, which are systemic)
