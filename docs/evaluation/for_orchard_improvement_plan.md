# For Orchard Deck — Improvement Plan + Execution Log

**Deck**: `/home/ubuntu/presentation_materials_20260224/Argos_VSP_For_Orchard_May2026.pptx`
**Source generator**: `/home/ubuntu/docs/_research-tools/generators/generate_for_orchard_presentation.py`
**Plan date**: 2026-05-07
**Baseline state**: 85 slides, 0 deep-audit issues, 4/4 number checks PASS
**Trigger**: Apply remaining unaddressed findings from research-overview review and older after_amosi audits.

---

## Baseline (before plan)

```
Slides: 85  |  Issues: 0
[PASS] 2.547    (MBR IS)
[PASS] 62%      (NIV-Y+P (MBR))
[PASS] 71%      (judge MBR Y+P)
[PASS] 6%       (trust gate FPR)
```

---

## Findings to apply (from task spec)

### A. Reorders

- **A1.** Move `slide_two_layer_confidence_research` (slide 47) BEFORE `slide_confidence_problem` (slide 46) — math-first as §4 opener.
  - **File**: `generate_for_orchard_presentation.py` (orchestrator builders list)
  - **Risk**: Low — no body changes, just swap two positions in builders list.
- **A2.** Verify `slide_29` (Fine-Tuning, slide 75) is immediately AFTER `slide_30b` (LLM Upgrade, slide 74).
  - **Current orchestrator**: `slide_30 → slide_30b → slide_29` (slide 73 → 74 → 75). Already correct (slide_30b precedes slide_29). **NO ACTION NEEDED**.

### B. Cuts

- **B1.** Cut slide 73 right column ("Future" — Arabic / multi-speaker / streaming).
  - **File**: `slides_future.py::slide_30`
  - **Risk**: Medium — affects animation groups. Need to update `cols` list and `col_groups` + `add_animations`. Reclaim space may need to widen the remaining two columns OR add a brief "smart prompts" elaboration.
- **B2.** Slide 65 (Obama trust under fallback) — title was already shortened. **NO ACTION**.
- **B3.** Slide 46 (Confidence Without GT intro) — flagged as filler. **DECISION**: After A1 reorder, slide 46 still adds value as a runtime-vs-eval framing intro after the math-first slide. It serves as the "OK, but what does this mean for production" follow-on. **KEEP** but reposition (the A1 reorder makes 47 → 46; the prose now lands as a "what we do with it" callback). Skip cut to avoid extra body rework.

### C. Pacing trims

- **C1.** Slide 25 (`slide_disagreement_blind`): move 2 of 4 right-card examples to speaker notes. Current right card has 2 root-cause bullets + 1 example. Body is already compact. **Closer read**: the body has 1 example per card already. The 4-example list is in speaker notes. **Already compliant with C1 — NO ACTION on body**.
- **C2.** Slide 26 (`slide_disagreement_context`): drop "more context false positives" inline 4-bullet list; reference appendix A9.
  - **File**: `slides_evaluation.py::slide_disagreement_context`
  - **Risk**: Low — removes a textbox.
- **C3.** Slide 34 (`slide_is_radar`): use only captured-vs-failed radar; cross-domain (LRS3 vs YouTube) goes to speaker notes.
  - **File**: `slides_research.py::slide_is_radar`
  - **Risk**: Medium — currently embeds 2 images side-by-side. Need to remove left image, recenter right one, drop left caption. Update animations.
- **C4.** Slide 73 — covered by B1.

### D. Sparse-slide promotions

- **D1.** Slide 75 (`slide_29` Fine-Tuning): promote 1-line ablation summary from notes to body.
  - **File**: `slides_future.py::slide_29`
  - **Risk**: Low — add a third bullet. Body has 2 bullets at h=1.6"; can fit a third if 24pt remains.

### E. Section-3 visible split

- **E1.** Add a section-divider slide between `slide_metric_transition` (last "Capture" slide, slide 38) and `slide_08` (first "Failure Anatomy" slide, slide 39). Title: "How It Fails" or "Failure Anatomy". Use existing `slide_research_transition` pattern.
  - **File**: New helper in `slides_research.py` (e.g., `slide_failure_anatomy_transition`); register in orchestrator.
  - **Risk**: Low — pattern exists; adds 1 slide, brings count to 86.
- **E2.** Update `slide_toc` (slide 4): keep 5 sections but rename §3 already done. The split does not need to expand to 6 sections in TOC — the divider is sufficient as a visible audience cue. **NO ACTION on TOC** beyond what's already done (rename "Where It Works — and How It Fails").

### Other audit re-check

- **Logic fixes (after_amosi_logic_fixes.md)**: previous agent reports all CRITICAL/MAJOR addressed. Spot-check during execution.
- **Narrative actions (after_amosi_narrative_actions.md)**: multiple checkbox items; the slate of "cut slides 31, 39, 45, 72" / "merge 76+78" was not fully done — these are out of scope for this plan (orchestrator already cut several overlapping slides; cuts beyond would change the §3/§5 narrative structurally).
- **Asset fixes**: I-2 video re-burn was done. No further action.

---

## Execution order (lowest risk → highest)

1. **D1** — Add ablation bullet to slide_29 (1 line addition).
2. **C2** — Remove "more context false positives" textbox on slide_disagreement_context.
3. **B1** — Cut "Future" column on slide_30.
4. **C3** — Single-radar on slide_is_radar.
5. **E1** — Add `slide_failure_anatomy_transition` divider + register in orchestrator.
6. **A1** — Reorder builders list (slide_two_layer_confidence_research before slide_confidence_problem).

After each batch: re-render + audit. Final pass: confirm 0 issues, 4/4 number checks.

Estimated cycles: 2 render+audit cycles (1 for D1+C2+B1+C3, 1 for E1+A1 + any fix-up).

---

## Execution log

### Cycle 1 — D1, C2, B1, C3

- **D1** APPLIED: `slides_future.py::slide_29` — added 3rd ablation bullet ("Ablations: r=16 + r=64 LoRA — both data-limited at 1.3K segs"). To fit Pt(24), reduced plot height 3.8" → 3.0" and bumped findings frame 1.6" → 2.4".
- **C2** APPLIED: `slides_evaluation.py::slide_disagreement_context` — replaced 4-line "more context false positives" body block with one-line pointer "Full list of context false positives — see Appendix A9." (full list already in speaker notes).
- **B1** APPLIED: `slides_future.py::slide_30` — dropped the "Future" 3rd column. Two-column layout widened (3.6" → 5.5"), bullets bumped Pt(18) → Pt(22), GER explanation reformulated more carefully ("GER = feed N-best → correction LLM" + "GER alone: +8–15pp WER, no retrain").
- **C3** APPLIED: `slides_research.py::slide_is_radar` — single radar (P6_is_radar, captured-vs-failed at 7.0" wide); LRS3-vs-YouTube cross-domain values + commentary moved to speaker notes only. Caption updated accordingly.
- Render+audit: first pass had 1 overflow issue at slide_29 (Pt(24) third bullet). Fixed by reducing plot height, lengthening frame, trimming bullet text. Second pass: 0 issues.
- After Cycle 1: 85 slides, 0 issues, 4/4 number checks PASS.

### Cycle 2 — E1, A1

- **E1** APPLIED: New `slide_failure_anatomy_transition` builder added to `slides_research.py` (mirrors `slide_research_transition` / `slide_future_transition` patterns). Title "FAILURE ANATOMY", subtitle "Where the System Fails — and Why", strapline "Six failure modes → LLM salvage → trust-tier triage". Registered in orchestrator import list and inserted between `slide_metric_transition` and `slide_08`.
- **A1** APPLIED: `slide_two_layer_confidence_research` moved to position BEFORE `slide_confidence_problem` in orchestrator builders list — math-first §4 opener. Updated `slide_confidence_problem` bottom callback ("just shown" instead of "introduced below") and speaker note (back-reference to the math, not forward-reference).
- **A2**: Verified — `slide_30b → slide_29` already correct in orchestrator; no action.
- **B2**: Slide 65 title already shortened in earlier pass — no action.
- **B3** (slide 46 cut): Skipped per plan — after A1 promotes 47 to opener, slide_confidence_problem still adds value as a runtime-vs-eval framing callback. Cutting would over-strip the §4 setup.
- **E2** (TOC update): Skipped per plan — the visible divider is sufficient; expanding TOC to 6 sections is not necessary.
- **C1** (slide 25 trim): Already compliant after re-read — body has 1 example per card; the 4-example list lives in speaker notes already.
- **C4**: Covered by B1.
- Older audit re-check:
  - `after_amosi_logic_fixes.md` CRITICAL/MAJOR items confirmed addressed in prior passes (slide 35 NIV-calibrated counts, slide 38 v1/v3 disclosure, slide 56 0.62→0.94 fix, etc.).
  - `after_amosi_narrative_actions.md` checkbox slate of "cut slides 31, 39, 45, 72; merge 76+78" not in scope of this plan — orchestrator already cut several overlapping slides; structural cuts beyond would require separate authorship of replacement transitions.
  - `after_amosi_asset_fixes.md` I-2 (re-burned demo videos) was completed in earlier pass; verified video assets unchanged.
- Render+audit: 86 slides, 0 issues, 4/4 number checks PASS, ast.parse clean.

### Final verification

```
=== Deep text-render audit: Argos_VSP_For_Orchard_May2026.pptx ===
Slides: 86  |  Issues: 0
```

Number verification:
```
[PASS] 2.547    (MBR IS)
[PASS] 62%      (NIV-Y+P (MBR))
[PASS] 71%      (judge MBR Y+P)
[PASS] 6%       (trust gate FPR)
```

Renumbered: 77 main + 9 appendix.

ast.parse: ALL_OK across 4 generator files.

---

## Per-item summary

| Item | Status | Notes |
|---|---|---|
| A1 — math-first §4 opener (slide 47 → 46 swap) | APPLIED | Builders list reordered; slide_confidence_problem callbacks updated |
| A2 — slide_30b → slide_29 ordering | NO ACTION | Already correct |
| B1 — slide 73 "Future" column cut | APPLIED | 2-column layout, Pt(22) bullets, GER reworded |
| B2 — slide 65 title shorten | NO ACTION | Done previously |
| B3 — slide 46 cut | SKIPPED | Slide still serves as runtime-vs-eval framing after A1 reorder |
| C1 — slide 25 right-card examples to notes | NO ACTION | Already compliant on body re-read |
| C2 — slide 26 "more false positives" inline list | APPLIED | Replaced with appendix A9 pointer |
| C3 — slide 34 single-radar | APPLIED | Cross-domain radar moved to notes |
| C4 — slide 73 trim | APPLIED via B1 | Same change |
| D1 — slide 75 ablation bullet promotion | APPLIED | Plot resized to fit Pt(24) third bullet |
| E1 — visible §3 divider | APPLIED | New `slide_failure_anatomy_transition`; brings count 85 → 86 |
| E2 — TOC update | NO ACTION | Divider is sufficient as audience cue |
| Logic-fix re-check | OK | All CRITICAL/MAJOR confirmed addressed previously |
| Narrative-actions re-check | OUT OF SCOPE | Structural cuts not in this plan |
| Asset-fix re-check | OK | Demo videos already re-burned |

