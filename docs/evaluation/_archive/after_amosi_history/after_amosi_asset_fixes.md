# Argos VSP AFTER_AMOSI Deck — Asset Fix Action List

**Audit:** [after_amosi_asset_integrity.md](after_amosi_asset_integrity.md)
**Inventory:** [after_amosi_asset_inventory.csv](after_amosi_asset_inventory.csv)
**Audit date:** 2026-05-06

The deck is presentation-ready. None of the items below block playback. They are ordered by narrative impact for an academic audience.

## Critical (broken video, missing plot)

**None.** All 15 embedded videos play (h264, audio, 1280×720, valid duration). All 7 deck-embedded regenerated plots are the May 6 versions (verified by SHA-256, not the March archive).

## Important (caption mismatch, stale plot, narrative inconsistency)

### I-1. Slide 65 title says "Salvage Tier" but the video badge says TRUST

- **What:** Slide 65 title reads `Demo - Obama Salvage Tier (partial recovery)`. The embedded video (`050111_..._31_009290_009650.mp4`, mtime 2026-05-06) renders a **TRUST** (blue) badge top-right because Obama seg 31 has mean_prob=0.920 — well above the 0.82 TRUST threshold under the conf-only fallback rule.
- **Why it happened:** Render-log Note A — Obama corpus was decoded before `VSP_NBEST=1` became standard, so no per-token beam-agreement scores exist; `classify_joint` falls back to conf-only `classify` which lands at TRUST. No way to reach SALVAGE on this segment without re-decoding the Obama corpus with n-best (hours on GPU).
- **Status:** Disclosed inside the slide body and notes ("[per-word colors load from the conf-only sidecar; VSP_NBEST=1 was not enabled at the April 30 decode]"), but the slide *title* still claims "Salvage Tier".
- **Fix options:**
  - (a) Retitle the slide to acknowledge the mismatch, e.g. `Demo - Obama Best-Available Salvage Example (badge=TRUST under conf-only fallback)` or `Demo - Obama #31: would be SALVAGE under joint rule (currently TRUST under conf-only fallback)`.
  - (b) Replace the slide-65 video with a non-Obama segment that genuinely lands at SALVAGE (e.g. one of the realtalk_* clips that already exist in `06_demo_videos/realtalk/`). Trade-off: breaks the Obama-themed visual continuity of slides 64-66.
- **Recommendation:** Option (a) is lower-risk and preserves the trio narrative. The slide body is already honest about the data limitation; the title just needs to match.
- **Owner:** deck author / `slides_evaluation.py::slide_demo_obama_partial`

### I-2. Slides 5, 20, 22, 23, 24, 63 (×3) carry pre-May-6 plain-caption renders

- **What:** 8 video shapes still use the older render style: white-on-black caption box, no tier badge, no per-word coloring.
- **Slides affected:**
  - 5 (`What is Visual Speech Processing?` — IEa7qEkMvfQ_3, mtime 2026-02-24)
  - 20, 22, 23, 24 (Judge Examples 2, 4, 5, 6 — VfJ-6nQAmtk / 9HanJOCw2Sc / a2CS82VZyO4 / tUcgHemnJiQ, mtime 2026-03-07)
  - 63 (`OK → Almost There → Hallucination` triplet — ktMebjnZiSE / 2HddWQse8Mw / 00MUdHQ7GGY, mtime Feb–Mar 2026)
- **Why it matters:** The new May-6 renders (slides 19, 21, 64-68) all carry tier badges and per-word color highlighting. When the talk reaches slide 64's "Demo - Obama Trust Tier" with a vivid TRUST badge, the audience has already seen unbadged demos on slides 5, 20, 22, 23, 24, 63 — the badge doesn't read as "always present, here's its value" but as "appearing for the first time mid-deck".
- **Why this happened:** The May 6 re-render scope was explicitly the 8 academic-deck demo clips (3 Obama + 2 judge + 3 realtalk). The other 7 academic-deck videos (slides 5, 20, 22, 23, 24, 63 triplet) were not in scope and have no decode artifacts (`VSP_NBEST=1`, agreement sidecar) to drive a re-burn.
- **Fix options:**
  - (a) Re-burn judge_film, judge_cortisol, judge_jalapeno, judge_lights against the existing v2 sidecar at `english_full_nbest_eval/word_confidence_v2.json` (same source as judge_entity / judge_router used for slides 19, 21, 67, 68). The pipeline already exists; a single `make_burn.py` invocation per clip.
  - (b) Same for the slide-63 triplet (00MUdHQ7GGY, 2HddWQse8Mw, ktMebjnZiSE), which all live in the english_full corpus and should have agreement sidecars available.
  - (c) Slide 5's perfect-demo clip (IEa7qEkMvfQ_3) is the trickier one — it's from a separate January / Feb decode. Worst case, leave it as the only unbadged opener (the slide doesn't claim a tier so it's narratively safe).
  - (d) Take no action and use slide 64 as the talk's first explicit "this is what TRUST looks like" beat — but rehearse the framing.
- **Recommendation:** Do (a) and (b) before the talk if the GPU minutes are available; ~30 min total work. They reuse already-decoded n-best artifacts. If skipped, prepare a verbal disclaimer between slide 24 and slide 63 ("from this point on you'll see the production tier badge").

### I-3. Slide 67 quotes mean_prob ≈ 0.71; actual is 0.624

- **What:** Slide 67 body reads `WER 18.2% / IS 4.55 / sequence_conf mixed / mean_prob ~ 0.71  (Salvage→Strip on key tokens)`. The per-segment record in `english_full_nbest_eval/report_v2/report.csv` shows mean_word_prob = **0.624** (and seg_mean_conf = 0.127).
- **Why it matters:** 0.624 is below the 0.65 strip-coloring boundary, which is exactly why the joint rule paints the segment STRIP / DON'T BELIEVE — and the slide title correctly says "Strip: entity swap auto-flagged". So the qualitative claim is right, just the number is wrong (0.71 → 0.62).
- **Fix:** Update the slide 67 body line to `mean_prob ~ 0.62 (below the 0.65 strip-coloring boundary — flagged red on rogers/pv/will)`. This sharpens the narrative ("the production threshold catches it") rather than weakening it.
- **Owner:** `slides_evaluation.py::slide_demo_judge_entity`. Same fix pattern not needed for slides 64/65/66/68 — those mean_prob values match render-log numbers within rounding.

### I-4. Four regenerated plots are orphaned (not embedded in any slide)

- **What:** `P6_is_radar.png`, `P_method_comparison.png`, `P_failure_taxonomy.png`, `P_llm_salvage.png` were regenerated on May 6 (all referenced in the IMG dict at lines 43, 52, 56, 57) but no slide actually embeds them.
- **Why it matters:** Bandwidth was spent regenerating them; they reflect MBR numbers that are now unused. If the talk improvises and someone asks "do you have a method-comparison plot?" the file exists at `/home/ubuntu/presentation_materials_20260224/01_plots_for_slides/P_method_comparison.png` and could be screen-shared, but it's not in the slide flow.
- **Fix:** Either (a) confirm with the deck author that these were intentionally cut and remove them from the IMG dict to avoid future confusion, or (b) add 1-2 backup slides in the Appendix that surface them (e.g. P_method_comparison fits naturally next to the existing v3-judge plot on slide 60).
- **Recommendation:** Low priority. Note in `DECK_CHANGELOG.md` that these four PNGs were prepared but not embedded.

## Optional (cosmetic, missing audio, awkward poster frame, etc.)

### O-1. Poster frames embedded by python-pptx default

PowerPoint stores a still poster image alongside each video shape. Inventory shows 15 poster JPGs (image2/image8/image10/image22-24, etc.) auto-generated by python-pptx at insertion time. They render as the visible thumbnail before the video plays. Spot checks (slides 64-68) show the poster faithfully captures frame 0 of each video (Obama at the podium / news anchor / TED-style speaker), which is fine. **No action.**

### O-2. Logo image1.jpg appears on 85 of 89 slides

`image1.jpg` (WhiteLogo.jpeg, 237 KB) is embedded as a PICTURE on every content slide (85 occurrences in the inventory). This is intentional — the logo is the deck's standing brand mark. PowerPoint deduplicates the part on disk so this costs ~237 KB total in the package, not 85× that. **No action.**

### O-3. Two `with_hyp` videos used twice (judge_entity, judge_router)

- `judge_entity` (4D634qUi2BI) appears on slide 19 (Judge Example 1 — narrative slide) and slide 67 (Demo - Strip — research-tier slide).
- `judge_router` (c6eBrYor21I) appears on slide 21 (Judge Example 3) and slide 68 (Demo - Salvage).

This is intentional dual-use: each clip is shown once in the linguistic-phenomenon section (judge examples) and again in the tier-demo section (Round 5/6 slide bank). PowerPoint deduplicates the MP4 part so the package only carries one copy of each. **No action.**

### O-4. Slide 5 narration drift

The May-6 re-render scope explicitly excluded slide 5's intro clip; the slide body says "33 words about health insurance, WER 0%" and the clip plays accordingly with a plain caption. If the speaker walks through tier badges before slide 5 ends, the missing badge here will look like an oversight. **Mitigation:** rehearse the intro to position slide 5 as "before we introduce the tier system" rather than "tier=TRUST". Or re-burn IEa7qEkMvfQ_3 against whatever decode sidecar is available (per item I-2 option c).

## Smoke-test checklist for day-of

- [ ] Open the deck in PowerPoint (Windows/Mac, NOT LibreOffice — LO has video-codec issues with these h264 files).
- [ ] Click each video slide (5, 19-24, 63, 64-68) and verify playback starts within 2 s.
- [ ] Confirm audio plays on slides 64, 65, 66 (Obama clips) and 67/68 (judge clips).
- [ ] Verify the v3-judge paired plot on slide 60 shows MBR=71.08% (not the older 71.1%, depending on rounding) and the band-reliability NIV plot on slide 55 shows 87.2 / 48.9 / 24.7%.
- [ ] If the room projector is below 1280×720, downsize the deck or test the videos look acceptable at the projector's native resolution.

## Cross-reference

- Source render log (videos): `/home/ubuntu/presentation_materials_20260224/06_demo_videos/RENDER_LOG_20260506.md`
- Source regen log (plots): `/home/ubuntu/presentation_materials_20260224/01_plots_for_slides/REGENERATION_LOG_20260506.md`
- IMG/VID dict: `/home/ubuntu/docs/_research-tools/generators/presentation/config.py`
- Frame extracts (audit-time): `/tmp/audit/frames/slide{NNN}_{media}.png`
