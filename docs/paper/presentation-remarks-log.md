# Presentation Remarks & Requests Log

Tracks all user feedback, remarks, and requests regarding presentation slides so nothing gets missed.

---

## Batch 1 — 2026-03-05 (v77→v76 slides)

| # | Slide | Remark | Status |
|---|-------|--------|--------|
| 1 | Exec Summary | Add a line about Arabic pipeline | done |
| 2 | TOC | Add Arabic concept to 4th segment of TOC | done |
| 3 | 6 | Small grey numbers in figure — reposition and make more visible | done |
| 4 | 9 | IS referenced before any definition — not clear enough | done |
| 5 | 11 | Animations in wrong order — needs reordering | done |
| 6 | 12 | Remove all animations | done |
| 7 | 15 | Wrong order of appearance. Split explanation: (a) WWER — how/why different, (b) NEA — what it is (currently in slide 24, decide placement), (c) then IS as currently, (d) next slide: deeper detail on phonetic & semantic calculation. Continue as before from there | done |
| 8 | 17 | Wrong animation order | done |
| 9 | 18 | What is r between the 3 metrics? Add to speaker notes | done |
| 10 | 19 | Font too small, animation wrong order, title bar too large vs frame | done |
| 11 | 20 | Radar plot not visually good enough | done |
| 12 | 21 | Remove all animations | done |
| 13 | 22 | Wrong ordering of appearance | done |
| 14 | 23 | Explain meaning behind "A topic label at decode time would help ~284 segments" — why is it true? Add to speaker notes | done |
| 15 | 24 | Point 4 not clear enough visually — occlusions | done |
| 16 | 27 | Remove all animations | done |
| 17 | 28 | Visual occlusion in lower part; no explanation on GER; writing too small + too many words; add "very high impact" for Right Topic Wrong Details (clients trust issues, probability values); change Hallucination to "not that bad — relatively easy to identify and ignore but still painful" | done |
| 18 | 29 | Missing animations for text in lower part; missing info on what is J | done |
| 19 | 30 | Wrong ordering — "key findings" appears last | done |
| 20 | 31 | Make blue frame have animation of appearance; hide this slide and the next one | done |
| 21 | 32 | Make left red frame have animation of appearance; hide slide | done |
| 22 | 34, 35, 36 | Animations off again | done |
| 23 | 38 | Lower grey text too high and occluded | done |
| 24 | 41 | Animation is just of the table — weird | done |
| 25 | 44, 45 | Videos not working (they worked before) | done (switched from add_video_poster to add_video for proper embedding) |
| 26 | 43 | Remove this slide entirely | done (removed slide_14 from builders list) |
| 27 | 49 | Animations off — wrong order, some parts missing animation | done (added para_build=False for card-level animation) |
| 28 | 54 | Re-order slide content | done (captured all shapes, restructured anim_groups) |
| 29 | 56 | User disagrees with most points — pending user input on what to say | pending |
| 30 | 58 | Missing explanation on what happens in phase 1 and 2; move plot to later place | done (added phase explanations; plot move deferred) |
| 31 | 59 | Figure does not appear; wrong placement of grey text | done (copied P3b_is_trajectory.png to plots dir) |
| 32 | 60 | Bad animations; wrong placement for many parts | done (captured all elements, fixed 4-step animation groups) |
| 33 | 61 | Wrong order of animations; missing animations; add analysis on entities (names, numbers, places) | done (3-step anim: left/effort/right; added entity bullet) |
| 34 | 63 | When talking about AVSpeech, clarify it's English videos; data scarcity was about immediately available videos not a hard block; wrong animation ordering and missing animations | done (added "English" throughout, added scarcity-is-curation note) |
| 35 | 64 | Plots not good for human eye; "empty outputs not catastrophic" — change phrasing; wrong order of animations | done (changed "catastrophic" to "identifiable and filterable") |
| 36 | 66 | Add "3-5 weeks" into animation at the end | done (added timeline callout box as 3rd animation group) |
| 37 | 71 | Tables overlap — bad | done (pushed heuristic title +0.4in, tbl3 +0.4in down) |
| 38 | — | Write current version number to keep it updated | done (v76 slides, 2026-03-05) |

---

## Batch 2 — 2026-03-05 (v76→v80 slides) — Gemini Feedback Implementation

External review feedback from Gemini, agreed changes implemented.

| # | Slide | Remark | Status |
|---|-------|--------|--------|
| 39 | NEW: "The Metric That Lies" (after Exec Summary) | Prove WER is misleading with concrete example — side-by-side WER 46.2% "FAILING" vs IS 4.03 "EXCELLENT" cards, word-level ref/hyp comparison, bottom callout. 3-click animation. | done (new `slide_wer_lies`) |
| 40 | NEW: "Three Numbers That Tell the Real Story" (after IS Results) | Vertical staircase: 64.1% (WER, coral strikethrough) → 39.9% (IS captured, teal) → 50.9% (+ salvage, green). 3-click card reveal with connecting arrows. | done (new `slide_metric_transition`) |
| 41 | NEW: IS vs WER Scatter (after IS Radar) | Scatter plot showing WER vs IS colored by tier, highlighting "the gap" (WER>40% but IS≥3.0). Separate companion script `generate_is_wer_scatter.py`. 147 gap segments found. | done (new `slide_is_wer_scatter` + plot script) |
| 42 | NEW: "The Price Tag" (after Data Scaling) | AWS cost projections table: 5 phases from current to 50K hrs. Phase 3 (20K hrs, ~$35K) highlighted as sweet spot. Right-side callout with LLM backbone upgrade options (Llama 3.1 8B / Qwen 2.5 7B). Training follows paper's 2-phase curriculum (freeze encoder → unfreeze). Speaker notes with GPU estimate methodology. | done (new `slide_price_tag`) |
| 43 | Pipeline (slide 17) | Replace 2-block reveal with per-stage wipe animation — 11 animation groups (input label, 8 stages individually, down arrow, legend). New `add_wipe_animation()` helper using OOXML presetID=10 wipe(right). Connector arrows between stages. | done (rewrote `slide_17` + new animation helper) |
| 44 | Data Scaling | Expand table from 3 columns to 5: Phase, Data, WER, IS Target, Timeline. Added Phase 1-4 labels with specific timelines (2-4 weeks through 3-4 months). Phase 3 row highlighted green. | done (modified `slide_data_scaling`) |
| 45 | Visemes | Added poster frame images (`ok_demo.jpg`, `salvage.jpg`) showing speaking faces side-by-side. Caption: "Different words — same mouth shape to the camera." | done (modified `slide_visemes`) |
| 46 | IS Radar | Dual radar overlay — LRS3 benchmark (green, tight) vs real-world YouTube (coral, jagged) on 6 IS dimensions. Separate companion script `generate_dual_radar.py`. Falls back to single radar if dual not available. | done (modified `slide_is_radar` + plot script) |
| 47 | — | Version updated to v80 slides, 2026-03-05 | done |

---

## Batch 3 — 2026-03-05

| # | Slide | Remark | Status |
|---|-------|--------|--------|
| 48 | ALL slides | Animations broken across many slides (mixed: wrong order + missing). Root cause: `para_build=True` default in `_finish()` caused multi-paragraph text to animate per-paragraph even in entry groups. Fixed by changing default to `para_build=False` in helpers.py. | done |
| 49 | 6 (Visemes) | Replace poster frame images with lip-reading demo GIF from internet. Downloaded GIF from Giphy, replaced ok_demo.jpg + salvage.jpg with single centered `lip_reading_demo.gif`. | done |
| 50 | 7 (Model Arch) | Grey dimension labels in figure too small — same problem as previous remark #3. Regenerated `model_architecture.png` with larger bold teal/white labels (13pt). | done |
| 51 | 28 (slide_failure_deep_3) | Table overlaps GER note and callout below. Reduced row_height from 0.7" to 0.5", text from Pt(12) to Pt(11), shifted GER note/callout/severity text up. | done |
| 52 | 29 (slide_failure_deep_2) | Card text shapes not included in anim_groups — only rectangles animated, text floated independently. Fixed by collecting all shapes per card into card_shapes list. | done |
| 53 | 32 (slide_tuning_summary) | Occlusion/placement issues reported. Fixed: shortened bullets (4→3), expanded callout box (1.8→2.2"), shortened J note, increased table row height (0.35→0.38") and text (Pt(11)→Pt(12)), pushed verdict below table with breathing room. | done |
| 54 | 33 (slide_is_deep_dive) | Animation order reversed — right column showed before left. Changed to `[[lt, tbl], [rt, rb]]`. | done |
| 55 | 34, 35 (metric disagreement 1+2) | Card text not in anim_groups — only rectangles animated. Fixed: each card now collects rect + rich_text + body text. | done |
| 56 | 36 (slide_two_eval_systems) | Card text not in anim_groups. Fixed: captured all text shapes into variables, grouped with their card rectangles in 3-step animation. | done |
| 57 | 50 (Pipeline, slide_17) | Down arrow between rows placed at right edge of row 1 but row 2 starts from left — visual disconnect. Centered the down arrow horizontally. | done |
| 58 | 50 (Pipeline) | User wants "visual effect" through pipeline of a video as in academia slideshows. Added pipeline_visual_strip.png (5-panel: raw face → mouth crop → features heatmap → LLM decode tokens → output text with IS score). Registered in config.py IMG map. Added as final animation group (Group 11) in slide_17 — appears on last click after all 8 stages are revealed. | done |
| 59 | 61 (slide_26b) | IS trajectory plot has overlapping text annotations. Regenerated P3b_is_trajectory.png with staggered labels and repositioned improvement annotation. | done |
| 60 | 67 (slide_29) | Fine-tuning experiments: "figures still look bad" — ft_clean plot. Redesigned FT_11_clean_summary.png: (1) left panel now uses real 19-epoch training data instead of fake 5-epoch, (2) fully dark-themed matching presentation navy BG, (3) right panel changed from confusing dual-axis vertical bars to clean horizontal bars with 3 metrics (IS, Captured %, Empty %) on single axis, (4) improved annotation box and bottom insight text. | done |
| 61 | Appendix A2 (slide_a3) | Remove "A2: Catastrophic lenpen" appendix slide from builders list | done |
| 62 | Appendix A3 (slide_a8) | Overlapping tables/text. Fixed: adjusted y-positions to add proper spacing between sections. | done |
| 63 | 20 (slide_is_calc_examples) | "Bulky green and red" — header bars and borders too heavy. Reduced border from Pt(3) to Pt(1.5), header bar from 0.4" to 0.32". | done |
| 64b | 20 (slide_is_calc_examples) | Green header bar too wide — spans full card width. Narrowed from col_w-0.2" to centered 3.6" strip. | done |
| 65b | Multiple (IS slides) | Added quadratic weighted κ=0.887 alongside existing binary κ=0.773 in all validation tables and speaker notes. Updated slides_research.py, slides_evaluation.py, slides_engineering.py, slides_future.py. Added full methodology section to is_correlation_analysis.md. | done |
| 66b | 21 (slide_21, Pipeline Intelligence) | IS card text too long — overflows card, occludes logo and bottom area. Shortened IS description from 7 lines to 4 concise lines. | done |

---

## Batch 4 — 2026-03-05 (Full Animation & Occlusion Audit)

User remark: "many slides have bad animations and occlusions"

**Animation issues** (16 slides where `anim_groups` only includes rect, not text overlays):

| # | Slide Function | File | Problem | Status |
|---|---|---|---|---|
| 64 | slide_toc | slides_opening.py | Only rects in groups, title/description text always visible | pending |
| 65 | slide_03 | slides_opening.py | blocks only has rects, not text labels or arrows | pending |
| 66 | slide_data_flow | slides_opening.py | step_shapes only has rects; circles, text, arrows unanimated | pending |
| 67 | slide_is_signals | slides_research.py | Only rect per signal card, 5 text elements visible | pending |
| 68 | slide_failure_deep_1a | slides_research.py | Only rect per failure mode card | pending |
| 69 | slide_is_dimensions | slides_research.py | Only rects for 3 dimension cards | pending |
| 70 | slide_decode_params | slides_research.py | All 4 rects in one group, text always visible | pending |
| 71 | slide_07 | slides_research.py | anim_groups=None — no animations | pending |
| 72 | slide_08 | slides_research.py | anim_groups=None — no animations | pending |
| 73 | slide_25b | slides_evaluation.py | Only rects for 6 category cards | pending |
| 74 | slide_21 | slides_engineering.py | Only rects for 4 feature cards | pending |
| 75 | slide_three_repos | slides_engineering.py | card_shapes only rects, not text | pending |
| 76 | slide_17 | slides_engineering.py | Calls undefined add_wipe_animation(), falls back | pending |
| 77 | slide_30 | slides_future.py | Only rects for 3 column cards | pending |
| 78 | slide_insights | slides_future.py | Only circles, not text content | pending |
| 79 | slide_31 | slides_future.py | Only rects, not number circles or text | pending |

**Occlusion issues** (2-3 slides):

| # | Slide Function | File | Problem | Status |
|---|---|---|---|---|
| 80 | slide_24 | slides_future.py | 3 columns total 12.4" — exceeds CW=12.13" by 0.27" | pending |
| 81 | slide_arabic_roadmap | slides_future.py | Two redundant "total timeline" callouts may overlap | pending |
| 82 | slide_is_calc_examples | slides_research.py | Two cards exactly at CW=12.13" limit (borderline) | pending |

---

## Batch 5 — 2026-03-05

| # | Slide | Remark | Status |
|---|-------|--------|--------|
| 83 | 13 (slide_06) | Change to Admiral McRae example ("same WER, different effects"); mention IS is "our new metric" | done |
| 84 | 14 (slide_is_foreshadow) | Content overlap with slide 16 — removed IS details, kept as short bridge ("we need a metric that captures meaning") | done |
| 85 | 16 (slide_is_intro) | Complete rewrite: deep dive into all 6 IS signals with crystal-clear explanations, especially Phonetic (IPA conversion, mouth-shape relevance) and Semantic (384-dim embeddings, cosine similarity). Each signal gets a card with how-it-works + example. No more "see next slide" deferrals. Title changed to "The Intelligibility Score (IS) — Our Metric" | done |

## Batch 6 — 2026-03-05

| # | Slide | Remark | Status |
|---|-------|--------|--------|
| 86 | 21 (slide_is_card) | Fixed κw=0.89 → κ=0.77 (weighted kappa removed from all slides) | done |
| 87 | All IS validation | Removed weighted kappa (κw=0.887) everywhere — stick with binary κ=0.773 and Pearson r=0.934 only | done |
| 88 | Research docs | Added Opus per-sample judge threshold sweep analysis (Y+P peaks at IS≥2.0 κ=0.818; Y-only peaks at IS≥3.75-4.0); context-aware judge bug fixed (column name `context` not `context_judge`) | done |
| 89 | LLM Judge slide | Added threshold insight box: "Y+P aligns best with IS≥2.0 (κ=0.82, 91.5%), not IS≥3.0 (κ=0.52). Systems agree on ranking — differ on where to draw the line." Updated takeaway to reference salvage zone validation. Expanded speaker notes with full threshold sweep. | done |
| 90 | Appendix A8 | Added gold bullet: "Y+P peaks at IS≥2.0 (κ=0.82) not IS≥3.0 (κ=0.52) — systems agree on ranking, differ on threshold". Expanded speaker notes with salvage validation. | done |
| 91 | "What Good Looks Like: IS Tier 5" | Hidden slide per user request (commented out in generate_presentation.py). 79→78 slides. | done |
| 92 | Research docs | Updated llm_judge_analysis.md (threshold sensitivity table), context_eval_analysis.md (threshold alignment finding), report_1_executive_assessment.md (threshold sweep summary), is_correlation_analysis.md (Section 8.5 sweep tables). | done |
| 93 | 50 (Pipeline, slide_17) | Full rewrite: removed floating input/output labels, format labels above boxes, and pipeline_visual_strip image. Clean 2-row grid with proper spacing. Arrows use ▶/▼ characters centered between boxes. Repo labels and legend placed cleanly below row 2. No overlapping elements. | done |
| 94 | 57 (slide_29, Fine-tuning) | Plots unreadable — replaced single combined FT_11_clean_summary.png with two separate plots (FT_11a_loss.png, FT_11b_impact.png) at larger size (5.9"×3.4" each). Bigger text, cleaner axes. Bullets shortened below. | done |
| 95 | 58 (slide_30) | Added GER explanation: "GER = Generative Error Correction: feed N-best hypotheses to a correction LLM that fixes errors" in grey text before the impact line. | done |
| 96 | 59 (Arabic roadmap) | Added per-topic click animations — each of the 5 requirement categories (encoder, LLM, infra, eval dataset, normalization) appears on separate click. Timeline table + callout appear last. | done |

---

## Batch 7 — 2026-03-05 (Topic Label Experiment)

| # | Slide | Remark | Status |
|---|-------|--------|--------|
| 97 | 19 (Domain Mismatch) | User asked: "how technically would topic label injection work?" and "why 284?" — expanded speaker notes with: (1) origin of 284 (143 Total Topic Drift + 141 Phonetically Similar Wrong Topic), (2) technical mechanism (instruction prefix injection in vsp_llm_dataset.py), (3) actual experiment results showing topic labels do NOT help (-0.8pp WER, 20% instruction echoing), (4) what would actually work (fine-tuning with topic-prefixed instructions) | done |
