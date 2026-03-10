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
| 40 | NEW: "Three Numbers That Tell the Real Story" (after IS Results) | Vertical staircase: 64.1% (WER, coral strikethrough) → 40.1% (IS captured, teal) → 51.1% (+ salvage, green). 3-click card reveal with connecting arrows. | done (new `slide_metric_transition`) |
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

---

## Batch 8 — 2026-03-05 (User Review Feedback)

| # | Slide | Remark | Status |
|---|-------|--------|--------|
| 98 | 9 (slide_04, Benchmark) | Simply emphasize that the dataset is different, more difficult — too much words. Reduced from 6 bullets to 3, removed detailed characteristic lists, kept core contrast (LRS3 curated vs YouTube real-world) and numbers (25.4% vs 64.1%). Simplified bottom text and speaker notes. | done |
| 99 | 10 (slide_eval_dataset) | Hide — commented out from builders list | done |
| 100 | 12 (slide_wer_explained) | Hide — commented out from builders list | done |
| 101 | 16 (slide_is_intro) | Split into 3 slides: (A) WER+WWER+Length, (B) Semantic Similarity, (C) Phonetic+NEA. Original function now calls all three. | done |
| 102 | 17 (slide_is_signals) | Remove — commented out from builders list (merged into split) | done |
| 103 | 19 (slide_is_dimensions) | Remove — commented out from builders list | done |
| 104 | 21 (slide_is_radar) | Refocused on model comparison: Llama-2 (current), Llama 3.1 8B (expected), VALLR 3B (best case). Title: "Model Comparison: Expected IS Profiles". Projected profiles, not measured. | done |
| 105 | 24 (slide_metric_transition) | Review the samples manually — let me see them and decide myself | pending |
| 106 | 25 (slide_10, Root Causes) | Hide — commented out from builders list | done |
| 107 | 26 (slide_domain_mismatch) | Hide — commented out from builders list | done |
| 108 | 31 (slide_failure_deep_3) | Fixed colors: consistent severity gradient (LGRAY→YELLOW→ORANGE→RED), CORAL for category column, border width standardized to Pt(1.5) | done |
| 109 | 32 (slide_tuning_summary) | Hide — commented out from builders list | done |
| 110 | 33 (slide_is_deep_dive) | State the conclusions | done |
| 111 | 37 (slide_llm_judge) | Fix the animation/appearance order | done |
| 112 | 40 (slide_25, Salvage) | Convey goal is a lower bound for our metric. Use only LLM-as-a-judge, drop the heuristic completely. The more salvageable by LLM is not actually improvement — that's not the message | done |
| 113 | 41 (slide_25b) | Hide — commented out from builders list | done |
| 114 | 44 (slide_25c) | Hide — commented out from builders list | done |
| 115 | 55 (slide_dual_env) | Removed "26" big number and label, moved bullet list up to fill gap, updated speaker notes | done |
| 116 | 59, 60 (slide_26, slide_26b) | Each phase now links to failure mode categories with percentages and expected IS improvement. Trajectory milestones annotated with failure mode targets. | done |
| 117 | 61, 62 (slide_confidence_scoring, slide_27) | Merged key content into confidence_scoring, slide_27 now brief 4-bullet summary | done |
| 118 | General | Too much text and numbers — applied across all modified slides (simplified text, added conclusions, one concept per slide) | done |
| 119 | General | Explain experiments in simple terms — applied to tuning, fine-tuning, and roadmap slides | done |
| 120 | General | Test additional language models — slide_is_radar now shows 3 model profiles; slide_30 and slide_a10 already list alternatives | done |
| 121 | General | Provide references for future methods suggested — known methods, papers. Added footnote refs (Pt 8, gray italic) to slides 26, 28, 30, data_scaling: ROVER (Fiscus 1997), MBR (Kumar & Byrne 2004), VALLR (Park et al. 2025), GER (Chen et al. 2024), Chinchilla (Hoffmann et al. 2022), LoRA Scaling (Biderman et al. 2024), AVSpeech (Ephrat et al. 2018) | done |
| 122 | 65 (slide_price_tag) | Clarify exactly which training is being discussed | done |
| 123 | 66 (slide_29, Fine-Tuning) | Graphs are not visible | done |
| 124 | 68 (slide_arabic_roadmap) | Create a more relaxed timeline, give it more thought, unknowns, bottlenecks | done |
| 128 | 59-60 (slide_26 + slide_26b) | Show where/how/why each metric improvement is expected — link to failure modes, extent, contribution | done |
| 129 | 61-62 (slide_confidence_scoring + slide_27) | Shorten together — too much detail; merged key content into confidence_scoring, made slide_27 brief summary | done |
| 125 | Videos slide (slide_14b) | What is the point of each video? Give more nice examples out of the 6 provided. Reduced from 8 to 6 videos (dropped entity_success/entity_destroy), added descriptive captions explaining what each video demonstrates, updated speaker notes with narrative explanation | done |
| 126 | Various | Fixed occlusions: slide_arabic_roadmap (timeline box moved below topics), slide_a8 (tbl3 overflow past slide bottom fixed, elements repositioned), slide_a16 (table width rebalanced), slide_a17 (annotation gap fixed) | done |
| 127 | 19 (slide_domain_mismatch) | Topic label experiment: updated speaker notes with final 284/284 results + control group (100 good segments). Control shows 0% echo rate vs 24% on bad segments — model only echoes when visual signal is weak | done |
| 130 | slide_llm_judge | Too many tables/correlations. Removed IS Tier cross-tab (already in appendix A16). Removed threshold insight box with kappa values. Added plain-language takeaway instead. Simplified correlation label to "85% correlation". Moved all r, kappa, threshold stats to speaker notes. | done |
| 131 | slide_two_eval_systems | Too many tables/correlations. Removed r=0.934 and kappa=0.773 from visible slide. Replaced with "88.6% agreement" plain language. Simplified agreement matrix labels to "System A/B says good/bad". Kept worked example. Moved all statistical details to speaker notes. | done |
| 132 | slide_is_weight_rationale | Too many tables/correlations. Removed r>0.79, r=0.93, kappa=0.77 from visible slide. Replaced with plain language ("these four signals measure the same thing", "88% agreement with expert judgment"). Removed right-column bullet list. Kept 3 dimension cards full-width. Moved all statistical details to speaker notes. | done |
| 133 | slide_failure_deep_3 | Too many tables/correlations. Reduced table from 4 columns to 2 (Category with % and Fix). Removed Severity column (colors convey this). Shortened fix descriptions to 2-3 words each. Removed GER footnote and verbose callout. Added conclusion: "Each roadmap phase targets a different failure category." Moved GER definition and severity details to speaker notes. | done |
| 134 | slide_failure_deep_3 | Re-added Impact column (3 columns: Category, Impact, Fix). Severity colors applied to both Category and Impact columns. Col widths: 4.0/3.8/4.33. | done |
| 135 | slide_context_eval | Hidden — too many tables. Commented out from builders list. | done |
| 136 | slide_14b | Replaced "perfect" (0% WER) and "halluc" (100% WER) videos with "phonetic_bridge" (65% WER, YELLOW) and "wer_broken" (82% WER, ORANGE). Kept "nearmiss" (admiral/animal). Updated speaker notes. | done |
| 137 | slide_is_radar | Removed VALLR 3B legend card entirely. Widened remaining 2 cards (col_w 4.0→5.5, gap 0.06→0.5). Updated _finish call and speaker notes. | done |
| 138 | slide_17 (Pipeline) | (1) Down arrow was centered on slide but should flow from stage 4→stage 5. Replaced centered ▼ with ▼ aligned under stage 4 + ◀ entry arrow before stage 5 on row 2. (2) Added red outline box around stages 6-7 with label "Existed in academic repo". Updated helpers.py add_rect to support fill_color=None (transparent). Updated speaker notes. | done |
| 139 | slide_26, slide_30 | Remove all VALLR references (4 locations): slide_26 references footnote, slide_30 Future column bullet, slide_30 references footnote, slide_30 speaker notes | done |
| 140 | slide_data_scaling | Larger table text (Pt(11)→Pt(13)), wider columns, split animation groups (table and callout separate), added realistic training note below AVSpeech callout | done |
| 141 | slide_arabic_roadmap | (1) AV-HuBERT explanation: why fine-tuning needed (English visemes vs Arabic phonemes). (2) Shorter timeline: 6→4 rows, merged steps. (3) Reduced total estimate 4-6→3-5 months. (4) Fixed occlusions: reduced topic spacing (0.85→0.75), moved timeline box and bottom note up. (5) Updated speaker notes. | done |
| 142 | slide_29 (Fine-Tuning) | Verified ft_loss and ft_impact image keys in config.py point to correct paths (FT_11a_loss.png, FT_11b_impact.png) | done |
| 143 | Pipeline / Live Demo | Add IS + LLM-as-a-Judge scoring to pipeline output (Stage 8). IS score now appears in HTML report per-segment with color coding. Full IS analysis (intelligibility_scores.csv + intelligibility_summary.json) generated automatically after decode. | done |
| 144 | Pipeline Reports | Make IS scoring EC2-only: `--compute-is` flag added to make_report.py, passed only when ENV_TYPE=ec2 in outputs.sh. Full IS analysis also gated to EC2. Container version unaffected. | done |
| 145 | 19, future_directions, generators | Reframe "topic label would help" claim — experiment proved it doesn't help without fine-tuning. Changed to "topic-aware fine-tuning needed" across slides, analysis docs, and generators | done |

---

## Batch 10 — 2026-03-05 (Density Audit Fixes)

User performed a density audit of slides with too many elements, tables, or bullets.

| # | Slide | Remark | Status |
|---|-------|--------|--------|
| 146 | slide_context_eval (hidden) | Decluttered from 3 tables to 1: removed comparison table (blind vs context) and summary stats table. Transition matrix enlarged (7" wide, Pt(14), centered) as hero element. Added headline stat above ("Y+P: 64.9% → 62.1%"). 3 key-finding bullets below at Pt(14). Moved full comparison data to speaker notes. Fixed float EMU from centering math. Slide remains hidden per user request. | done |
| 147 | slide_data_scaling | Trimmed left-column bullets from 6 to 4: dropped "Fine-tune experiments confirmed: small data = overfitting" (redundant with table) and "Data scarcity is a curation bottleneck" (weakens momentum). Bumped remaining bullets from Pt(13) to Pt(14), reduced height allocation (3.5" → 3.0") for breathing room. | done |
| 148 | slide_11 (Named Entity Accuracy) | Hidden — commented out from builders list. Removed click-reveal animations (anim_groups set to None). 70→69 slides. | done |
| 149 | slide_metric_disagreement (When Metrics Disagree) | Hidden — commented out from builders list. 69→68 slides. | done |
| 150 | slides 31-32 (slide_25 + slide_llm_context_engine) | Swapped order: slide_25 (IS lower bound / salvage overview) now comes before slide_llm_context_engine (LLM as context engine). First explains the judge, then explains why LLM context matters. | done |
| 151 | slide_14b (Video Gallery) | Replaced "nearmiss" (probiotics segment) with "admiral" (Admiral McRae → animal migratory, WER 33%). Added "admiral" video key to config.py. Updated caption and speaker notes. | done |
| 152 | slide_15 (Demo Trio) | Replaced "nearmiss" video with "vitamin_d" ("vitamin d deficiency" → "empathy deficiency", WER 50%) — better near-miss example with phonetically plausible substitution that changes meaning. Added "vitamin_d" video key to config.py. | done |
| 153 | slide_17 (8-Stage Pipeline) | Full redesign: rounded-corner boxes, larger arrows (Pt(14)), ▼ connector properly centered under stage 4, ↳ flow indicator at row 2 start, "Existed in academic repo" label moved ABOVE red outline (no longer crowds legend), repo attribution merged to single centered line, cleaner legend spacing. | done |
| 154 | slide_26b (IS Roadmap) | Enlarged trajectory plot from 7.0" to 8.0" width, shifted milestones right to accommodate. | done |

---

## Pipeline Bug Reports — 2026-03-06

| # | Area | Remark | Status |
|---|------|--------|--------|
| 155 | Pipeline / IS Scoring | No IS column in UI report — `ENV_TYPE` never set because `run_flat_english_pipeline.sh` didn't source `lib/config.sh`. Fixed: added `source "${HOME}/lib/config.sh"` at pipeline start. | done |
| 156 | Pipeline / Springer Fox | `springer_fox_with_hyp.mp4` in vsp_input is a burned lip-crop output (224x224), not a raw source video. Face detector can't find a face in a mouth crop → empty hypothesis. User needs to replace with the original raw video. | noted |
| 157 | Pipeline / Overlap Selection | Overlapping 2s segments produce different decode quality in overlap zones. Analysis of 33 Obama segments: 13/21 overlaps have a clear quality winner (7 prev, 6 next). A post-decode "best-of overlap" merge step could improve output. Related to Mission 6 (ROVER/MBR). | noted |

---

## Batch 11 — 2026-03-06

| # | Slide | Remark | Status |
|---|-------|--------|--------|
| 158 | 15 (slide_is_intro_b) | "Weight: 25%" callout box widened from 3.5"/3.1" to 4.8"/4.4" to prevent text clipping | done |
| 159 | 20 (slide_is_wer_scatter) | Make the scatter plot larger — custom layout with 7.7" plot area | done |
| 160 | 23 (slide_failure_deep_1a) | Split into 2 slides (1a: categories 1-3, 1b: categories 4-5 + salvage insight bar) | done |
| 161 | slide_metric_disagreement | Restore only slide_metric_disagreement (When Metrics Disagree: WER>>WWER patterns). Removed show='0' hide flag. Other slides (slide_11, slide_is_dimensions, slide_tuning_summary) kept hidden per batch 8 | done |
| 162 | slide_14b (Video Gallery) | Row 1 changed to bogo/nearmiss/entity_success (positive examples, no reuse from opening). Row 2 kept phonetic_bridge/admiral/topic_drift | done |
| 163 | slide_17 (Pipeline) | Replaced ▶ with → arrows, removed extra chevrons mid/right, single centered ↓ between rows | done |
| 164 | 48 (slide_24) | Narrowed text 3.4", enlarged image to 5.2" | done |
| 165 | slide_26b (IS Improvement) | Increased card spacing, taller annotation cards (1.05"), text Pt(11)/WHITE instead of Pt(9)/LGRAY | done |
| 166 | slide_price_tag | Table widened to 11.8", text Pt(12), row_height 0.48". Added 5-point cost methodology in speaker notes | done |
| 167 | FT_11a_loss.png | Annotation box "Val: 2.39 → 4.12 (+72%)" occluded by legend — moved down to y=0.72 | done |
| 168 | slide_17 (Pipeline) | Fix stage order: swap ASR/Mouth Crop to match real pipeline (Normalize→Mouth Crop→ASR→LRS3). Change K-means subtitle from "Feature extraction" to "Feature clustering". Replace centered ↓ with L-shaped connector (thin teal lines + ▼ arrowhead) flowing from stage 4 to stage 5. Update speaker notes | done |

---

## Batch 12 — 2026-03-07

| # | Slide | Remark | Status |
|---|-------|--------|--------|
| 169 | 22 (slide_metric_transition) | Last number should be Opus-as-a-Judge Y+P=64.9%, not heuristic 50.9%. Changed third card to "64.9%" with "Opus-as-a-Judge confirms: Y+P = 971/1,497" | done |
| 170 | 19 (slide_is_radar) | Remove model description cards below radar, just put inline legend. Move full model descriptions to speaker notes | done |
| 171 | 23-24 (failure_deep_1a/1b) | Reorder failure categories by impact (from slide 27 table): Right Topic Wrong Details → Wrong Topic → Hallucination → Accumulated → Signal Loss. Updated colors to match severity gradient. Also reordered slide 27 table to match | done |
| 172 | 29 (slide_metric_disagreement) | Hide — commented out from builders list | done |
| 173 | 31 (slide_two_eval_systems) | Replace expert heuristic with Opus-as-a-Judge throughout. Changed card title, bullets (Y+P=64.9%), agreement table (Opus Y/P vs N), worked example, speaker notes | done |
| 174 | 38 (slide_15) | Change near-miss from vitamin_d (IS 2.5) to admiral (IS 2.96) — closer to success threshold. Updated title to "OK → Almost There → Hallucination" | done |
| 175 | 45 (slide_web_ui) | Replaced placeholder with demo announcement — big play icon, "We will now run the full pipeline live", three feature cards (Drag & Drop, 8 Stages, IS Scoring) | done |
| 176 | 43 (slide_19) | Hide — commented out from builders list | done |
| 177 | 46 (slide_21) | Replaced speaker notes with detailed explanation of smart overlap handling: 2s configurable overlap, best-of-overlap merge by beam score, Obama analysis (13/21 overlaps had clear winner) | done |
| 178 | 50 (slide_24) | Replace heuristic numbers with Opus-as-a-Judge: "64.9% useful per Opus-as-a-Judge (Y+P = 971/1,497)", "85% correlation between IS and Opus verdicts" | done |
| 179 | 52 (slide_26b) | Fixed milestone card spacing: increased vertical spacing (1.2→1.25"), taller cards (1.05→1.10"), shifted start up (0.55→0.45") | done |
| 180 | 53 (slide_confidence_scoring) | Removed "Business/Finance segments (57% captured) get highest scores" bullet | done |
| 181 | 57 (slide_price_tag) | Simplified: 7-col table → 5-col table (Investment/Data/Cost/Timeline/IS), 5 rows → 4 rows. Renamed phases to plain language (Quick win/Medium/Full/Maximum). Simplified speaker notes to 4 clear tiers with plain explanation | done |
| 182 | 58 (slide_29) | Fine-tune figure text hidden — reduced plot height (4.0→3.5"), increased text area, bumped font (14→15pt) | done |
| 183 | 59 (slide_30) | Added speaker note explaining why 3-8pp from LLM change: 128K vocab (4x), 15T tokens (7.5x), better disambiguation of homophenes, stronger world knowledge | done |
| 184 | ALL | Made slide numbering consistent — section dividers now auto-numbered so PPTX position = displayed number | done |

## Batch 13 — 2026-03-07

| # | Slide | Remark | Status |
|---|-------|--------|--------|
| 185 | NEW (slide_30b) | Add detailed LLM upgrade analysis slide after slide_30: capability gap table (MMLU, vocab, context, training data), VALLR evidence (18.7% WER with smaller Llama 3), failure mode recovery estimates per category, combined WER projections. PPTX only (no beamer). Also wrote full analysis doc at docs/evaluation/llm_upgrade_analysis.md | done |
| 185 | 6 (slide_visemes) | Changed GIF from lip_reading_demo.gif to mom-yelling.gif (user uploaded) | done |
| 186 | 15 + 14b | Admiral video used twice — keep admiral on gallery (slide 14b), replaced with vitamin_d on demo trio (slide 15). Fixed WER/IS numbers (WER 50%, IS 2.4), improved description, used CORAL color for middle slot | done |
| 187 | 58 (slide_29) | Fine-tune plot (FT_11b_impact) text covered by legend — moved legend to lower-left; also moved "Best (epoch 2)" annotation in FT_11a_loss below trendlines | done |
| 188 | ALL | Generated 36 new demo videos with burned hypothesis overlay from 1,497 segments (8 per IS tier). Total pool now 50 videos | done |
| 189 | slide_30b | Decluttered: removed dense 5-row failure mode table (multiline cells clipped), bottom insight paragraph, and reference line. Replaced right column with clean WER waterfall (5 stacked cards). Left column: capability table + compact VALLR box + drop-in note | done |
| 190 | NEW (slide_30c) | Hidden backup slide with full failure mode recovery detail: 6-row table (segments, %, LLM impact, expected recovery per category), insight box explaining disambiguation, scaling law note, references. Commented out in builders list for Q&A backup | done |
| 189 | 15 (trio) | Final trio: smartphone (IS 4.1, "want bigger smartphone"→"will not upgrade") + street_photo (IS 2.9, near-miss) + halluc (IS 0.1). Replaced ok_demo with smartphone for slightly better left slot (~4.1 vs 3.8) | done |
| 190 | 14b (gallery) | Swapped 5 of 6 videos (kept admiral): convention (IS 4.1), marilyn (IS 3.9), music_play (IS 3.9), spelling_smell (IS 1.9), doxology (IS 0.2) | done |
| 191 | NEW (7 slides) | Convert 30-sample LLM Judge report to PPTX: 1 summary slide (slide_llm_judge_30) + 6 consecutive video example slides (slide_judge_ex1-6). Examples span IS 4.55 to 1.79 — mid-range, interesting cases: named entity swap, truncation, tech vocab drift, scientific vocab lost, cooking domain confusion, topic hijack. Each slide has large embedded video (left) + ref/hyp text + metrics + annotation (right). Placed after slide_context_eval, before Salvage section. Total slides: 75→77 | done |
| 192 | IS calc card + 6 files | "carry strap" hallucination segment had wrong IS values across files: calc card showed Length Ratio 1.00 (actual 0.78), IS ranged from 0.1 to 0.9 across files (actual 0.813→rounds to 0.8). Fixed: slides_research.py (calc card + failure mode card), slides_evaluation.py (table), curated_examples.tex, generate_gemini_instructions.py, PRESENTATION_PLAN.md. Also corrected Phonetic Sim (0.12→0.20), Inv WWER (0.00→0.03) in the calc card | done |
| 193 | "3 dimensions" slides | User flagged: "3 independent dimensions (PCA)" claim was never actually PCA — it was correlation clustering mislabeled. Ran actual PCA: Kaiser retains 2 PCs (signal quality 68.4%, output length 19.5%). Semantic loads on PC1 alongside word-accuracy signals — NOT independent. Fixed 12+ files: Beamer (02_research_findings, 05_appendix), PPTX generators (slides_evaluation, slides_research, slides_future), STYLE_GUIDE, CLAUDE.md, intelligibility_methodology, is_correlation_analysis, why_is_not_just_llm_judge, generate_gemini_instructions. Created new doc: docs/evaluation/is_pca_analysis.md | done |

---

## Batch 14 — 2026-03-08 (NIV Threshold Update — 23 Items on PRESNETATION_AFTER_NIV.pptx)

Post-Niv revision. Applied 23 changes to the ground-truth PPTX via `scripts/update_niv_presentation.py`. Output: `Argos_VSP_Final.pptx` (76 slides, 71 visible).

| # | Slide(s) | Remark | Status |
|---|----------|--------|--------|
| 194 | 2-3 | Professional language rewrite — minimal grammar cleanup, white text + teal keywords only | done |
| 195 | ALL | Page numbering — sequential 1-N for visible slides only | done |
| 196 | ~20 slides | Global NIV threshold update: IS ≥ 3.0 → IS ≥ 3.80 (Y) / IS ≥ 2.00 (Y+P). Updated all text + notes | done |
| 197 | 16 | LLM-as-a-Judge expanded — filled "More explanation here! For claude" placeholder with methodology | done |
| 198 | 17 | 30-sample slide — replaced placeholder with stratified sample table + key findings | done |
| 199 | 18 | IS motivation — filled empty slide with 5 reasons from why_is_not_just_llm_judge.md | done |
| 200 | 22 | PCA narrative fix — corrected speaker notes: 2 PCs not 3, covariance clustering ≠ PCA | done |
| 201 | 23 | Bad IS sample — fixed Length Ratio 1.00 → 0.25 for carry-strap example | done |
| 202 | 24 | Radar chart — regenerated from generate_dual_radar.py with measured LRS3 values, embedded new PNG | done |
| 203 | NEW (hidden) | Metrics disagreement Part 1 — re-added 4 pattern cards as hidden slide before Part 2 | done |
| 204 | 27 | Two Systems — added full NIV threshold table (IS + WER at both Y and Y+P levels) | done |
| 205 | 11 | LRS3 reproduction — added "could not fully reproduce, best result 32% WER" | done |
| 206 | 22 | Weight rationale — added sensitivity analysis to speaker notes (<0.15 avg IS change) | done |
| 207 | 28 | Three Numbers reframed — "how many videos useful": 25.5% (WER) / 61.6% (IS) / 64.9% (Judge) | done |
| 208 | 36 | Surrogate — retitled "IS: A Calibrated Surrogate for LLM Judgment", updated NIV numbers | done |
| 209 | 25 | WER-IS gap — updated with all 4 NIV thresholds, IS beats WER at both levels | done |
| 210 | 58, 60-62 | LLM swap → training required — reframed across 4 slides, removed "1-2 hours setup" | done |
| 211 | 63 | Arabic risk downgrade — "RISK" → "minor integration", timeline 3-5 → 2-3 months | done |
| 212 | 43 | Pipeline ASR separation — ASR as side-branch with "evaluation only" annotation | done |
| 213 | 7 | Human expert animation — click-reveal "system + human > expert lip reader" on demo slide | done |
| 214 | NEW (64-65) | Arabic deep-dive — 2 new slides: AV-HuBERT language explanation + What Changes table | done |
| 215 | 66 | Key takeaways — updated 4 points, de-emphasized data bottleneck, added IS vs WER comparison | done |
| 216 | 58 | Price tag — "Free upgrade: swap LLM" → "LLM upgrade + adapter retraining" | done |
| 217 | 24, 40, 54 | Fix 3 page-number overlaps — moved bottom-row content up ~0.3" to clear page numbers on radar legend (S24), gallery captions (S40), and roadmap insight (S54) | done |

## Batch 15 — 2026-03-08 (PCA Story Slide + Radar Fix)

| # | Slide(s) | Remark | Status |
|---|----------|--------|--------|
| 218 | 22 | Replace "6 Signals, 2 Dimensions (PCA)" content with the PCA story: title → "Do 6 Signals Actually Measure 6 Things?", reframed as a question/answer narrative. Same layout (2 stacked cards + green italic + gold bottom). Updated PC descriptions, key implication ("weights barely matter, r=0.999"), and speaker notes with full PCA story | done |
| 219 | Radar (Model Comparison) | Grey subtitle text covered by radar graph — moved image down 0.2" | done |
| 220 | Failure Taxonomy (2/2) | Remove "Impact order: Right Topic Wrong Details → ..." grey bottom text | done |
| 221 | Failure Modes: Impact & Fixes | Move slide from after taxonomy (Section 4) to after "LLM Upgrade: Why It Matters" (Section 8) | done |
| 218 | IS in Action (two segments) | Bad segment arithmetic wrong: Phonetic 0.029→0.030, Inv WWER 0.004→0.005, sum 0.80→0.81 | done |
| 220 | 2 (What is VSP?) | Yellow and grey text overlapping — deleted grey subtitle and grey caption, enlarged video (4.3→4.8"), moved up to y=1.8" | done |

## Batch 16 — 2026-03-08 (Stale PPTX Image Fix)

| # | Slide(s) | Remark | Status |
|---|----------|--------|--------|
| 221 | 20 (The Gap: Where WER Lies Most) | PPTX had stale embedded scatter plot showing old IS >= 3.0 threshold ("147 segments"). Regenerated P7_is_wer_scatter.png and rebuilt PPTX — now shows NIV thresholds (IS >= 3.80 Y gap: 42 segments, IS >= 2.00 Y+P gap: 437 segments) | done |
| 222 | Two Evaluation Systems, One Framework | Update from old IS >= 3.0 confusion matrix to NIV thresholds. IS card now shows two operating points (IS >= 3.80 = 23.1%, IS >= 2.00 = 61.6%). Agreement matrix updated to NIV Y+P (883/39/88/487, κ=0.818). Two worked examples: NIV Y ("chord"→"court", IS 3.84) and NIV Y+P ("reason and logic", IS 2.94 — old threshold wrongly rejected). Speaker notes updated with NIV rationale | done |
| 223 | Failure Taxonomy (1/2) | Title "1. Right Topic, Wrong Details (22.7%)" wrapping to 2nd row — widened name column 3.8→4.8", moved grey description text down 0.04" | done |
| 224 | When Metrics Disagree / AV-HuBERT / Arabic Adaptation | All three slides had white background (unreadable white text on white). Fixed `clear_slide_content` to explicitly set navy background after clearing shapes | done |
| 225 | Five Insights That Inform the Roadmap | Remove this slide entirely — removed from slide list in generate_presentation.py (77→76 slides) | done |
| 226 | slide_17 (8-Stage Pipeline) | ASR as side-branch: moved "3. ASR" out of main row 1 flow. Row 1 now: Normalize → Mouth Crop →→ LRS3 Convert (long arrow). ASR drops from branch point between slots 2-3, with coral-colored L-connector going to Outputs + "evaluation only" annotation. L-connector from LRS3 to Manifests routes below ASR. Speaker notes explain ASR provides reference transcriptions for evaluation only | done |

## Batch 17 — 2026-03-08 (Cost Slide: Emphasize Data Scale)

| # | Slide(s) | Remark | Status |
|---|----------|--------|--------|
| 227 | The Price Tag: What It Costs to Improve | User noted the VSP-LLM paper already fine-tuned AV-HuBERT (freeze 18K steps, unfreeze 12K steps — 25.4% WER). Tier 3 "sweet spot" was described as if encoder adaptation was new, but it's the paper's existing recipe. Restructured table: "What Changes" column replaces "Timeline", tiers 3-4 now framed as "paper's recipe ×46 data" and "paper's recipe ×115 data" to emphasize data scale is the real variable. Sweet spot callout updated to reference paper's exact recipe (433 hrs → 20K hrs = 46×). Speaker notes rewritten with key insight that encoder adaptation is not new | done |
| 228 | Arabic Adaptation: What Changes (update_niv script) | Two empty bullet strings ("") creating blank bullet points between the component list and phase list, and between phase list and bottleneck line. Removed both empty bullets | done |
| 229 | 20 (slide_is_calc_examples) | Bad Segment card in PPTX had stale numbers from old build (Phonetic 0.12, Inv WWER 0.00, Length Ratio 0.25×0.15=0.150 — arithmetic wrong). Source code already had correct values (remark #192/#218). Regenerated PPTX to pick up fixes | done |
| 230 | 22 (6 Signals, 3 Dimensions) | Slide still showed old wrong "3 dimensions" story (Word Accuracy 60%, Meaning Preservation 28%, Output Sanity 9%). Needed PCA story: 2 principal components (PC1 Signal Quality 68.4%, PC2 Output Length 19.5% = 87.9%). Rewrote all visual content + notes in both PPTX (update_niv script) and Beamer | done |
| 231 | 18 (Why LLM as a Judge Is Not Enough) | Content overlapping with title — text shapes stacking on top of each other. Root cause: function searched for empty text box but didn't clear existing shapes. Rebuilt slide from scratch with clear_slide_content(), 5 reason cards in 2-column grid with card backgrounds (NAVY2), proper title/subtitle/accent line spacing | done |
| 232 | 17 (LLM Judge: 30-Sample Deep Dive) | Slide had no proper table structure — just monospaced text pretending to be a table, generic bullet points with no actual examples. Rebuilt with: (1) proper python-pptx stats table on left (6 rows, dark cells), (2) 6-example ref/hyp table on right with merged verdict/WER/IS cells, color-coded Y/P/N verdicts, real data from examples_summary.json, (3) gold insight callouts at bottom highlighting key disagreement patterns | done |
| 233 | 33→63 (Failure Modes: Impact & What Fixes Them) | Slide was supposed to move from after taxonomy (Section 4) to after "LLM Upgrade: Why It Matters" (Section 8) per remark #221, but move was never implemented. Added `move_slide()` function to update_niv_presentation.py. Slide now at position 63 after LLM Upgrade slide 62 | done |
| 234 | 22 (6 Signals, 3 Dimensions → 3 Principal Components) | Previous fix (#230) only showed PC1+PC2 and repurposed box 3 as "Key Insight". User wanted all 3 PCs shown. Updated box 3 to PC3: Entity Swing (5.1%, NEA F1, below Kaiser threshold eigenvalue 0.31). Bottom line now reads "93% of variance in 3 components; Kaiser retains 2 (87.9%); PC3 adds nuance" | done |
| 235 | 17 (slide_17 pipeline) | ASR side-branch fix from remark #212 was only applied as manual PPTX binary patch — Python generator still had ASR inline. Subsequent PPTX regeneration (remark #229) overwrote the fix. Rewrote slide_17() in slides_engineering.py: row 1 main flow Normalize→Mouth Crop→LRS3 Convert (long arrow spans gap), ASR drops as side-branch with coral connectors + "evaluation only" label, coral L-connector from ASR to Outputs. Also updated generate_pipeline_diagram.py (PNG) with same layout, auto_avsr bracket moved above row 1, LRS3→Manifests elbow routed left of ASR box | done |
| 236 | Price Tag: What It Costs to Improve | Emphasis was still on AV-HuBERT fine-tuning as if it's new — paper already does this. Table was 5 columns × 4 rows, too crowded. Simplified to 3 columns (Training Data / Cost / Expected IS) × 3 rows. Removed "What Changes" and "Investment" columns. Framing line now states paper's recipe already works, only data scale varies. Sweet spot callout replaced with "Key insight" box emphasizing 433 hrs → 20-50K hrs. LLM swap condensed to single-line callout. Speaker notes updated | done |
| 237 | 51 (Five Insights That Inform the Roadmap) | Slide was supposed to be removed per remark #225 but persisted in PPTX because update_niv_presentation.py never deleted it. Added `delete_slide()` function and called it in main(). Slide deleted, 75 slides remain (70 visible) | done |
| 238 | 62 (LLM Upgrade: Why It Matters) | Hide slide. Added hide_slide() call in update_niv_presentation.py. 71→69 visible slides | done |
| 239 | AV-HuBERT: Why It's Not Language-Locked + Arabic Adaptation: What Changes | Both slides: (1) bullets appear one-by-one on click (individual animated text boxes), (2) colors upgraded from flat LGRAY to WHITE text with TEAL ▸ bullet markers, matching rest of presentation's color scheme | done |
| 240 | Generator sync audit | Audited remarks #227-239 for persistence across both PPTX pipelines. Found Arabic deep-dive slides (#214/#239) existed only in update_niv_presentation.py. Added `slide_arabic_avhubert()` and `slide_arabic_changes()` to slides_future.py + generate_presentation.py builders list. All other remarks verified synced: #234 (PC3) already in generator, #236 (Price Tag) already in both, #237/#238 (deletion/hide) already excluded from generator | done |
| 241 | LLM Judge: 30-Sample Deep Dive | Added hidden backup slide (slide_judge_report_screenshot) with cropped HTML report screenshot showing ~16 rows of the 30-sample report with color-coded word diffs, Y/P/N badges, and metrics. Image saved to 01_plots_for_slides/llm_judge_report_30_screenshot.png. Slide is commented out in builders list — uncomment to show if needed during Q&A. Image key "llm_judge_report" added to config.py | done |
| 242 | Multiple slides (comprehensive generator sync) | Synced all NIV-only changes to generator source code: (1) slide_07 title "40.1% Properly Captured" → "61.6% Useful Output", IS threshold 3.0→2.00 throughout; (2) Radar chart: "projected profiles" → "measured profiles", legend updated LRS3/YouTube framing, speaker notes rewritten with measured values; (3) Three Numbers slide: 64.1%/40.1%/64.9% → 25.5%/61.6%/64.9% with "how many videos useful" framing, strikethrough removed; (4) IS deep dive table: "Captured (IS≥3) 40.1%" → "Useful (IS≥2) 61.6%"; (5) Key takeaways slide_31: "40% properly captured, 51% with LLM salvage" → "61.6% useful (NIV Y+P), 64.9% confirmed by LLM judge"; (6) LLM swap terminology fixed in slides_evaluation.py: "drop-in swap" → "architecture-compatible", "Setup 1-2 hours" → "Requires adapter retraining"; (7) slides_opening.py slide_03: "swappable/drop-in/trivial 1-2 hour" → "upgradeable/architecture-compatible/requires retraining"; (8) Human expert note moved to slide_02 (video slide) speaker notes per user direction; (9) LRS3 reproduction comment added to slide_04 speaker notes; (10) "Conservative Lower Bound" → "Calibrated Surrogate Metric" in slides_evaluation.py; (11) Salvage appendix table: "Metric capture 40.1%/Effective capture 51.1%" → "Useful output 61.6%/LLM Judge 64.9%"; (12) All stale 40.1%/51.1%/39.9% removed from slides_future.py milestone and speaker notes. Regenerated both PPTXs | done |
| 243 | Slide 08 (Failure Mode Taxonomy) + deep-dive 1a/1b + slides_future.py | Recomputed all failure mode numbers for IS < 2.00 threshold (574 segments, was 900 at IS < 3.0). New breakdown: Wrong Topic 44.4% (255), Hallucination 18.8% (108), Signal Loss 13.9% (80), Right Topic Wrong Details 13.8% (79), Accumulated Errors 9.1% (52). Reordered all slides by new ranking. Updated roadmap phases, LLM upgrade detail table, impact table, speaker notes throughout both slides_research.py and slides_future.py | done |
| 244 | NEW: Same WER, Different Meaning | Added new slide `slide_semantic_domain_gap` showing WER-matched LRS3 vs YouTube comparison. At same WER (20-40%), LRS3 has +0.143 higher semantic similarity but only +0.024 higher phonetic. Semantic/Phonetic ratio: LRS3=1.01 (meaning tracks sound) vs YouTube=0.87 (meaning degrades 13% faster). Includes real examples: LRS3 "14-16 hours"→"40-60 hours" (numbers wrong, meaning intact) vs YouTube "admiral mcrae"→"animal migratory" (same sounds, different topic). Three root causes in speaker notes: visual encoder familiarity, vocabulary density, LLM prior anchoring. Placed after IS vs WER scatter, before IS results. 78→80 slides. Analysis: docs/evaluation/signal_distribution_analysis.md | done |
| 245 | NEW: IS vs Opus Judge Disagreement (2 slides) | Created docx report (docs/evaluation/llm_judge/disagreement_analysis.docx) summarising all disagreements between IS and Opus judge for both blind and context-aware modes. Added 2 PPTX slides: (1) `slide_disagreement_blind` — two side-by-side cards (green=IS Too Harsh 19 cases, red=IS Too Generous 3 cases) with curated REF/HYP examples and root causes, 98.5% agreement stat; (2) `slide_disagreement_context` — compact transition matrix on left (230 downgrades vs 68 upgrades), IS=4.75 negation false positive on right ("a lover of"→"not a lover of"), domain swap examples. Placed after slide_context_eval (slides 34-35). 80→82 slides (84 total including hidden). Generator: generate_disagreement_analysis_docx.py | done |
| 246 | Generator sync to FINAL_PRESENTATION.pptx | Comprehensive sync of generate_presentation.py to match the user's manually-edited FINAL_PRESENTATION.pptx (82 slides). **Manual changes found in user's PPTX vs generator output:** (A) **Slide reordering**: LLM Judge block (6 examples + overview) moved from after IS methodology to immediately after RESEARCH FINDINGS divider (slides 15-22); slide_is_motivation moved after judge examples (slide 23); failure taxonomy bar chart (slide_08) moved before deep-dives instead of after; slide_two_eval_systems moved to slide 32; slide_llm_context_engine moved between slide_30 and slide_30b (slide 67). (B) **Slides removed**: slide_is_foreshadow (bridge slide) deleted; slide_semantic_domain_gap (LRS3 vs YouTube) deleted. (C) **Slides unhidden**: slide_metric_disagreement (pt 1), slide_30 (Stronger LLM), slide_30b (LLM Upgrade quantified). (D) **Text edits in PPTX**: slide_what_was_done_1 bullets reworded ("proved insufficient" → "was the basic metric – which is unsatisfactory", "deployed to" → "migrated into a container on", "clear plan" → "clear future plan"), bullet size 14→17pt; slide_exec_summary "3.5×" → "2.4×", "2.53" → "2.52"; slide_06 title "WER Is Blind to Meaning" → "Same WER, Different Effects"; slide_research_transition subtitle "What Works, What Fails, and Why" → 'What does "Working" mean, What Works, and Why'; slide_24 title "Starting from 40%, Not 11%" → "Starting from 61.6%, Not 25%"; slide_confidence_scoring "Surface the Good 40%" → "Surface the Good 65%"; slide_context_eval replaced with IS surrogate metric content (title: "IS: A Calibrated Surrogate Metric"); slide_25 title → "IS: A Calibrated Surrogate for LLM Judgment"; slide_is_radar title "Expected IS Profiles" → "IS Profiles"; slide_llm_judge_30 title "30-Sample Deep Dive" → "Deep Dive". (E) **Content added**: slide_02 bottom text ("System + human reader outperforms expert lip readers: 55–70% vs 45–52%"); PPTX slide 50 pipeline PNG (detailed diagram with file-type labels and ASR as side-branch). (F) **Typo in PPTX** (fixed, not preserved): slide 2 bullet 7 "clear future clear plan" → "clear future plan". **Generator changes applied:** Updated generate_presentation.py builder order + imports; all text fixes in slides_opening.py, slides_research.py, slides_evaluation.py, slides_future.py; new slide_17_png in slides_engineering.py; pipeline_detailed.png saved + added to config.py. Final output: 84 slides (82 base + 2 new disagreement slides) | done |
