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
| 244 | NEW: Same WER, Different Meaning | Added `slide_semantic_domain_gap` to slides_research.py — WER-matched LRS3 vs YouTube comparison. At same WER (20-40%), LRS3 has +0.143 higher semantic similarity but only +0.024 higher phonetic. Semantic/Phonetic ratio: LRS3=1.01 vs YouTube=0.87. Real examples + 3 root causes. Analysis: docs/evaluation/signal_distribution_analysis.md. Was removed in #246 sync but re-added by user request. Placed after scatter (slide 31), 84→85 slides | done |
| 245 | NEW: IS vs Opus Judge Disagreement (2 slides) | Created docx report (docs/evaluation/llm_judge/disagreement_analysis.docx) summarising all disagreements between IS and Opus judge for both blind and context-aware modes. Added 2 PPTX slides: (1) `slide_disagreement_blind` — two side-by-side cards (green=IS Too Harsh 19 cases, red=IS Too Generous 3 cases) with curated REF/HYP examples and root causes, 98.5% agreement stat; (2) `slide_disagreement_context` — compact transition matrix on left (230 downgrades vs 68 upgrades), IS=4.75 negation false positive on right ("a lover of"→"not a lover of"), domain swap examples. Placed after slide_context_eval (slides 34-35). 80→82 slides (84 total including hidden). Generator: generate_disagreement_analysis_docx.py | done |
| 246a | Generator sync — slide reordering | Updated generate_presentation.py builder list to match FINAL_PRESENTATION.pptx slide order. LLM Judge block (overview + 6 examples) moved to immediately after RESEARCH FINDINGS divider (slides 15-22); slide_is_motivation moved after judge examples (slide 23); failure taxonomy bar chart (slide_08) moved before deep-dives; slide_two_eval_systems moved to slide 32; slide_llm_context_engine moved between slide_30 and slide_30b (slide 67). Updated all imports accordingly | done |
| 246b | Generator sync — slides added/removed/unhidden | Removed slide_is_foreshadow (bridge slide) and slide_semantic_domain_gap (LRS3 vs YouTube, later re-added per #244). Unhidden 3 slides: slide_metric_disagreement (pt 1), slide_30 (Stronger LLM + Smart Prompts), slide_30b (LLM Upgrade: Why It Matters). Added slide_17_png (pipeline PNG diagram as full-slide image, extracted from FINAL slide 50, saved as pipeline_detailed.png in config.py). Final output: 82 builders → 84 slides (slide_is_intro produces 3 sub-slides internally) | done |
| 246c | Generator sync — opening slides text fixes | slide_what_was_done_1: bullets reworded ("proved insufficient" → "was the basic metric – which is unsatisfactory", "deployed to" → "migrated into a container on", "clear plan" → "clear future plan"), bullet size 14→17pt. slide_exec_summary: "3.5×" → "2.4×", "2.53" → "2.52". slide_06 title: "WER Is Blind to Meaning" → "Same WER, Different Effects". slide_02: added bottom text ("System + human reader outperforms expert lip readers: 55–70% vs 45–52%"). Typo in PPTX fixed (not preserved): slide 2 bullet 7 "clear future clear plan" → "clear future plan" | done |
| 246d | Generator sync — research & evaluation text fixes | slide_research_transition subtitle changed to 'What does "Working" mean, What Works, and Why'. slide_is_radar title "Expected IS Profiles" → "IS Profiles". slide_llm_judge_30 title "30-Sample Deep Dive" → "Deep Dive". slide_context_eval replaced with IS surrogate metric content (title: "IS: A Calibrated Surrogate Metric"). slide_25 title → "IS: A Calibrated Surrogate for LLM Judgment" | done |
| 246e | Generator sync — future slides text fixes | slide_24 title "Starting from 40%, Not 11%" → "Starting from 61.6%, Not 25%". slide_confidence_scoring "Surface the Good 40%" → "Surface the Good 65%" | done |
| 247 | NIV consistency pass — failure mode numbers | Updated stale IS < 3.0 failure-mode percentages to NIV IS < 2.0 across all slides and speaker notes: (1) slide_failure_deep_1b (37) notes: Accumulated Errors 24.4%→9.1%, Signal Loss 9.0%→13.9%; (2) slide_failure_deep_2 (38) text: Hallucination 12.3%→18.8%, Wrong Topic 31.6%→44.4%, Right Topic Wrong Details 22.7%→13.8%; (3) slide_28 (62) text+notes: Accumulated Errors 24.4%→9.1%; (4) slide_a13 (81) notes: Wrong Topic 31.6%→44.4% | done |
| 248 | NIV consistency pass — IS thresholds & values | Updated all remaining IS < 3.0 threshold references and stale IS values: (1) slide_26b (59) IS 2.53→2.52, "useful"→"captured"; (2) slide_data_scaling (63) IS 2.53→2.52; (3) slide_a8 (76) reverted PCA table to 3-dimensions per FINAL; (4) slide_a11 (79) reverted to IS ≥ 3.0 legacy metrics per FINAL; (5) slide_a11b (80) IS < 2.0→IS < 3.0 then back to IS < 2.0; (6) slide_a16 (82) threshold fix | done |
| 249 | NIV consistency pass — text content alignment | Aligned slide text to match FINAL_PRESENTATION.pptx exactly: (1) slide_is_wer_scatter (30) "WER > 77%"→"WER > 40%", added bottom text; (2) slide_is_calc_examples (28) bad segment values fixed (Phonetic 0.20→0.12, WWER 0.03→0.00, Length 0.78→0.25, IS 0.8→0.9); (3) slide_research_transition (14) removed subtitle; (4) slide_llm_judge (15) complete rewrite of right side — methodology bullets; (5) slide_llm_judge_30 (16) removed 2 extra bullets; (6) slide_is_deep_dive (39) PCA→cross-config bullets; (7) slide_metric_disagreement (40) shortened card text; (8) slide_two_eval_systems (32) "almost perfect"→"good", "NIV Y"→"IS Y"; (9) slide_llm_context_engine (67) text fix; (10) slide_07 (31) "Useful (Y+P)"→"Useful Output (Y+P)"; (11) slide_is_radar (29) removed legend text; (12) slide_30 (66) "architecture-compatible"→"drop-in"; (13) slide_30b (68) text fix | done |
| 250 | Final IS < 3.0 cleanup | Removed last two IS < 3.0 references: (1) slide_disagreement_blind (34) notes: "IS < 3.0"→"IS < 2.00" for both false negatives and false positives thresholds, "resolve most of these"→"define the operating points"; (2) slide_a11b (80) text: "IS < 3.0"→"IS < 2.0". Full PPTX scan confirms zero IS < 3 references remain in any slide text or speaker notes | done |
| 251 | Tables, plots & figures — comprehensive NIV update | Full audit of all tables, plots, and milestone numbers across all generator files. **Plot regenerated:** P3b_is_trajectory.png — replaced IS ≥ 3.0 threshold line with dual NIV lines (IS ≥ 2.00 teal "Useful Y+P", IS ≥ 3.80 green "Clearly Conveyed Y"), updated milestone percentages from old "captured" (39.9/48/58/65%) to NIV "useful" (61.6/72/83/90%). **Slide tables updated:** (1) slide_26b milestones: "48% captured"→"72% useful (Y+P)" etc; (2) slide_a8 heuristic validation table: replaced "Agreement 88.6%"/"Recall (IS≥3)" with "Agreement (IS ≥ 2.00) κ=0.818"/"Agreement (IS ≥ 3.80) κ=0.690"; (3) slide_a11 salvage table: "Metric capture (IS ≥ 3.0) 39.9%"/"Effective capture 50.9%" → "Useful output (IS ≥ 2.00) 61.6%"/"LLM Judge confirms (Y+P) 64.9%"; (4) slide_25c heuristic table: same threshold updates; (5) slide_26 phase targets: "filters to ≥ 3.0 subset"→"filters to high-confidence subset"; (6) slide_28: "above the 3.0 threshold"→"into clearly useful range (IS ≥ 3.80)"; (7) slide_24 bottom: "40% captured by IS"→"61.6% useful by IS (Y+P)"; (8) slide_26/26b notes: IS 2.53→2.52; (9) Future targets: "55-65% captured"→"85-90% useful Y+P". **Speaker notes:** replaced "88.6% agreement" with "κ=0.818 (Y+P)" in slides_research.py (3 locations), slides_evaluation.py (2 locations), slides_future.py (2 locations). **Validation text:** "Validated: 88.6% agreement with IS ≥ 3.0"→"IS vs Opus judge κ=0.818 (Y+P), κ=0.690 (Y)". **Non-PPTX generators updated:** generate_presentation_plots.py, generate_dual_radar.py (IS 2.53→2.52), generate_gemini_instructions.py (IS 2.53→2.52, old failure mode %, old thresholds throughout), generate_summary.py (40.1%→61.6%, IS ≥ 3.0→IS ≥ 2.00), generate_research_journal.py (~15 stale references), generate_intelligibility_methodology_docx.py, generate_llm_salvage_analysis.py, generate_disagreement_analysis_docx.py, analyze_llm_eval.py. Regenerated PPTX: 84 slides, comprehensive scan confirms zero stale IS ≥ 3.0 or old percentage references in any slide text or notes (4 contextually-correct historical references remain: slide 32 explaining "Old IS ≥ 3.0 wrongly rejected", slide 32/35 notes explaining threshold supersession) | done |
| 253 | STYLE_GUIDE.md — Visual Quality Guardrails | Added new section 7 "Visual Quality Guardrails" to STYLE_GUIDE.md codifying lessons from all 251 remarks into 37 numbered rules across 6 categories: Occlusion Prevention (O1-O8), Density Limits (D1-D6), Text Readability (T1-T7), Spacing & Layout (S1-S7), Data Freshness (F1-F4), Animation Structure (A1-A5). Added cross-references from PPTX Animation Rules and Plot Visual Conventions sections. Extended Cross-Format Rules table with docx applicability note. Renumbered TOC | done |
| 252 | Extended NIV update — recalculated data tables & radar chart | Recalculated ALL data-driven tables and plots from source CSV using IS ≥ 2.00 threshold. **Per-length filter table** (generate_research_journal.py): recalculated from llm_judge_results.csv — ≥5 words: 62.5%→65.6%, ≥10: 64.9%→68.5%, ≥20: 68.2%→71.8%. Column headers renamed "Captured %"→"Useful (NIV)", "Ctx LLM %"→"Judge Y+P". **Per-topic table** (generate_research_journal.py): all 11 topics recalculated — Business/Finance 56.5%→78.3%, DIY/Home 29.6%→40.7%, etc. **Length band table**: 31.7%→53.1% (5-10 words), 48.6%→68.2% (20+). **Fine-tuning comparison**: Captured IS≥3.0 38.4%/33.0%/25.4% → Useful IS≥2.00 61.6%/55.9%/50.5%. **LLM Judge agreement table**: replaced IS≥3.0 κ (0.565/0.521) with NIV κ (0.690/0.818). **P6 IS radar chart** (generate_presentation_plots.py): recalculated signal means for IS≥2.00 split — useful [0.62,0.73,0.59,0.58,0.59,0.97] vs non-useful [0.14,0.27,0.00,0.06,0.06,0.85]. Legend: "Captured"→"Useful", "Failed"→"Non-useful". **Finetune plots** (generate_finetune_plots.py): captured [38.4,33.5,25.9]→[61.6,55.9,50.5]. **Slide text**: topic tables in slides_research.py updated with correct IS values and NIV useful rates; NEA F1 split 74%/16%→59%/6%; domain text "57%/30% captured"→"78%/41% useful"; slides_opening.py exec summary notes "40%→61.6%"; slides_evaluation.py context false positives "IS>=3.0"→"IS≥3.80". All plots regenerated, PPTX regenerated (84 slides), final scan clean | done |
| 254 | IS calc example fix + hidden slides | Fixed bad segment IS calculation (slide 28) to use actual CSV data: Phonetic 0.12→0.20, WWER 0.00→0.03, LR 0.25→0.78, product 0.150→0.117, IS 0.9→0.8 (actual 0.81). Old LR product was mathematically wrong (0.25×0.15≠0.150). Fixed "properly captured"→"useful output" (slide 59), "Surface the good 40%"→"good 65%" (slide 60). Centralized slide hiding in generate_presentation.py hidden_builders set — 9 slides hidden: Executive Summary, WER Lies, IS Validation, Metrics Disagree pt1+pt2, Disagreement blind+context (new), Pipeline animated, LLM Upgrade. Matches FINAL_PRESENTATION.pptx user edits | done |
| 255 | Slide numbering fix + plot layout fixes | Fixed slide numbering completely off: (1) changed all hardcoded string labels ("26b", "25b", "25c", "25d", "25e", "14b") to auto-numbered `0` in slides_evaluation.py and slides_future.py; (2) added post-processing renumber step in generate_presentation.py that overwrites all bottom-left labels with sequential 1-76 + A1-A8 based on actual slide position. Fixed IS Improvement Roadmap plot (P3b_is_trajectory) x-axis text overlap: increased figsize from 10×6 to 10×6.8, reduced slide image width 8.0→7.6" to prevent overflow. Fixed LoRA loss curve (FT_11a_loss) x-axis "Epoch" label cut-off: added `labelpad=8` and `tight_layout(rect=[0, 0.03, 1, 1])` padding, increased slide plot_h 3.5→3.8" to reduce vertical squishing. Same bottom-padding fix applied to FT_11b_impact plot | done |
| 256 | Future plan trajectory — derive from taxonomy | Trajectory values in IS/WER plots and 5-phase staircase were hardcoded round numbers, not derived from the 574-segment failure taxonomy. Recalculated all values: **WER trajectory** 64→55→45→42 changed to 64→60→48→34 (47% relative, was 34%). **IS trajectory** 2.52→2.85→3.40→3.80 changed to 2.52→2.65→3.05→3.50 (+0.98 IS, was +1.28). **Useful rate** 61.6→72→83→90% changed to 61.6→65→73→82%. **5-phase staircase IS deltas** updated: Phase 1 +0.3→+0.0 (perceived only), Phase 2 +0.3-0.5→+0.13, Phase 3 +0.5-0.8→+0.40, Phase 4 +0.5-1.0→+0.35, Phase 5 +0.3-0.5→+0.10 (sum +0.98). Per-category signal profiles from signal_distribution_analysis.md §8 added to slide notes and llm_upgrade_analysis.md. Combined target IS 3.5-4.0→IS 3.3-3.7 (~80-85% useful). Also added missing InvWWER column to signal_distribution_analysis.md Section 8. Updated llm_upgrade_analysis.md Part 3 and Part 6 with NIV taxonomy counts and signal-profile annotations | done |

## Batch 18 — 2026-04-30 (Client Deck — April 2026)

| # | Slide(s) | Remark | Status |
|---|----------|--------|--------|
| 257 | NEW deck — Client Deck | User requested a NEW client-facing deck with positive, UI-led framing, distinct from the existing academic 84-slide deck. The two decks coexist: academic deck stays as-is for research audiences, client deck is a separate generator output tailored for prospective customers / non-technical stakeholders | done |
| 258 | Borrow-vs-build policy | When assembling the client deck, import existing slide builders from `presentation/slides_*.py` for any content that already exists (architecture, IS overview, signal radar, etc.). Only build net-new slide builders for genuinely-new client-deck content (UI screenshots, demo callouts, value-prop framing). Avoids drift and keeps a single source of truth for shared figures | done |
| 259 | v3 jargon strip | User feedback on v3 review: strip all research-internal jargon from visible slides — LoRA, the 1,273 / 20,000 segment counts, r=16, r=64, PCA, NIV, κ (kappa). Move any of these that must be retained into appendix slides only. Visible deck stays in plain customer-facing language | done |
| 260 | v3 Trust Dashboard reframe | Reframe the Trust Dashboard slide: drop the "useful with context" partial bucket from the headline visual (it confused reviewers). Anchor the headline number on **62% useful** with an explicit "these videos are difficult" caveat. Defer the conditional / context-aware plot until real Tier-2 confidence data lands from the B3 GPU decode currently in flight | done |
| 261 | General usefulness framing | Keep the 60% useful headline stat across the deck. Make it clear in surrounding copy and speaker notes that the videos we processed are quite difficult — real YouTube content with varied lighting, head angles, occlusions, and accents — not curated lab footage like LRS3. This sets expectations correctly without sounding defensive | done |
| 262 | Demo input choice | Use the Obama bin Laden announcement (May 1, 2011) as the live demo input. Rationale: globally recognizable, frontal-camera, clean speech, formal register, and already preprocessed in the pipeline so it can be played end-to-end without prep. Six segments curated for the demo report | done |

## Batch 19 — 2026-05-01 (Confidence — Band Reliability vs Segment Quality)

| # | Slide(s) / Doc | Remark | Status |
|---|----------------|--------|--------|
| 263 | confidence_full_analysis.md (Section 10, 11) | Add scatter plots like the existing hallucination scatter for OTHER confidence pairs (margin × min_word_prob, red-frac × green-frac, word_prob × entropy, mean_prob × p_std) and for continuous IS / WER targets, plus a precision-recall sweet-spot sweep. Identified `mean_prob >= 0.82` as the F1-max single-feature gate (F1=0.75 over NIV-Y, IS_kept=4.01, WER_kept=27.5%) | done |
| 264 | confidence_full_analysis.md (Section 11) | Per-word coloring is a third option between trust and drop, but only safe if green words remain reliable. User raised the "There were 2 people..." case — green word that's wrong inside an otherwise OK-looking segment misleads more than it informs. Stratified P(correct \| green) by segment mean_prob: collapses from 92.8% (high) → 18-22% (low). Three-tier policy: T_trust=0.82, T_salvage=0.74, strip-coloring below 0.65. Found 2,192 wrong-and-green words; 605 in low-confidence segments. Includes the "billion → million" off-by-1000× class. | done |
| 265 | All confidence reports + UI + slides | Roll out the three-tier policy across artifacts. Plan: [docs/confidence/band_reliability_rollout_plan.md](../confidence/band_reliability_rollout_plan.md). Caveat: thresholds and the strip-coloring boundary will change with better LLM (Llama-3.1 8B), domain-specific fine-tuning (20K+ AVSpeech segments), and beam-aggregation upgrades — the green-band leakage in low-confidence segments is a *symptom* of insufficient training signal on rare/numeric tokens, not a permanent property of the architecture. | pending |

## Batch 20 — 2026-05-02 (Confidence — Agreement-Aware Bands)

| # | Slide(s) / Doc | Remark | Status |
|---|----------------|--------|--------|
| 266 | Client deck (`slides_client.py`) word-color-coding slide + demo HTML report legend + reviewer-onboarding rules slide | User direction: "follow colors and understand what to trust based off this new method." Color legend updated across client-facing artifacts to reflect the new joint conf+agreement band rule (green = confident AND alternative beams agreed; yellow = some signal but not enough; red = avoid; numbers capped at yellow regardless of confidence — lip-reading cannot disambiguate digits). Updated `slide_client_word_color_coding` legend strip + speaker notes, the "What you just saw" recap bullet, the "NUMBERS AND NAMES" reviewer-onboarding card (now leads with the numeric cap, references the billion→million case), and the `generate_client_demo_report.py` HTML legend. CSS class names (`conf-high`/`conf-med`/`conf-low`) preserved — only explanatory prose changed. Background: [lessons_learned_band_rule_v2.md](../confidence/lessons_learned_band_rule_v2.md), source-of-truth design [confidence_shape_and_beam_disagree_design.md](../confidence/confidence_shape_and_beam_disagree_design.md), empirical validation [TRUST_DIAGNOSTIC.md](../../english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md). | done |

## Batch 21 — 2026-05-02 (Round 5.16 — n-best v3 judge truth + production switch)

| # | Slide(s) / Doc | Remark | Status |
|---|----------------|--------|--------|
| 267 | `slide_client_aggregation_safety` + `slide_client_engineering_journey` (notes) | Headline shift: Mission 6 status moves from "shipped, env-gated" to "shipped + judge-validated production switch — `hyp_mbr` is the default displayed output." Footer updated. Card 3 swapped from "WORD ERROR RATE DOWN (~1.6 pp)" — that win belongs to `hyp_vote_conf`, not the shipped method — to "CALIBRATED CONFIDENCE" framing the per-word posterior MBR emits (the actual production reason we picked MBR over vote_conf). Speaker notes rewritten: full v3 dual-conf judge numbers (MBR +2.7 pp Y+P p=0.0002, vote_conf +2.1 pp p=0.0026, vote_score n.s.); MBR-over-vote_conf rationale (intra-rater 86.7% vs 80%, calibrated posterior vs narrow [0.4,0.8] agreement score); v1 retraction note (27% drift on byte-identical text, archived under `judgments_v1/`). Source: [docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md](../evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md), [docs/beam-search/n_best_implementation.md](../beam-search/n_best_implementation.md) §"Final recommendation — ship pure MBR." | done |
| 268 | Headline numbers refresh — slide 26 + slide 31 | Latest 1,497-segment evaluation numbers landed: NIV-Y rose 23.1% → 24.1% (361 segs), three-tier UI distribution shifted to Trust 23.8% / Salvage 37.5% / Strip 38.7% (1,427 segs under joint band rule). Slide 26 NIV-Y card 23% → 24%; slide 31 three shares updated. Audit canonical list extended for both. | done |
| 269 | `lib/decode.sh` (production change, not a slide) | User direction: "the MBR confidence and confidence-dependent filtering should apply to all videos." Flipped `VSP_NBEST` default 0 → 1 so n-best aggregation runs on every pipeline invocation by default. Combined with entry #30 (MBR as default displayed output) and the existing tier classification in `make_report.py`, this means MBR confidence + the three-tier UI policy (Trust/Salvage/Strip) now apply to all videos, not only opt-in runs. Container overlay synced (`vsp_linux_container_FINAL_20260217/lib/decode.sh`); container-sync-changelog entry #31 logged. Disk cost ~120 MB per hour of video; wall-clock ~zero. Set `VSP_NBEST=0` to opt out. | done |

## 2026-05-03 — RealTalk demo dataset ingest

User asked me to assess `/data/conversation_datasets/` (RealTalk + AMI + EgoCom + Seamless) and produce demo clips for the deck. Decisions made:
- Demo clips for the deck only (not bulk eval / not fine-tuning).
- Multi-speaker handling: per-speaker pre-split using dataset bboxes, one source → two derivative streams.
- AMI skipped (resolution too marginal).
- Mode-B side-by-side with original two-shot audio confirmed as the chosen presentation format.
- Audio re-attached from the source two-shot, not mixed from per-speaker stems.
- Whisper concern: pipeline re-Whispers per segment as ground-truth ref; I confirmed alignment of dataset-Whisper vs pipeline-Whisper is not the cause of WER numbers (per-segment Whisper IS the ref).
- Deferred: EgoCom + Seamless downloads (to be scheduled later).

Deliverables: `presentation_materials_20260224/06_demo_videos/realtalk/` (30 burned face clips, 5 Mode-B composites, 75 frame snapshots, analysis md+json), curated picks at `realtalk_demo_picks.md`.

---

## 2026-05-03 — Demo recording script updated for live client meeting

User asked to launch the server and refresh the recording script for narrating live over a screen-recording in a client meeting. Server already running at http://127.0.0.1:8765.

Script updates ([docs/guides/client-demo-recording-guide.md](../guides/client-demo-recording-guide.md)):
- Scene 3 rewritten: word colors are now **blue/orange/purple** (not green/yellow/red) and tier badges **Trust/Salvage/Strip** added — both reflect the May 2 2026 production UI (joint conf + beam-agreement rule, MBR n-best as default display).
- Scene 3 now demos the Strip-tier "coloring removed" treatment explicitly — the system telling you *not* to trust a segment is half the story.
- Scene 4 adds the numbers/names/dates orange-cap rule (lip-reading can't disambiguate "fifteen" vs "fifty", "million" vs "billion").
- Pre-record checklist updated: must decode with `VSP_NBEST=1` for the joint rule + tier pills to render; staged input video must produce all three tiers (Trust + Salvage + Strip) so all three can be demoed.

---

## 2026-05-03 — Round v9 + v9.1 — Client deck end-to-end fixes pass

User reviewed Round 8.8 deck. Posted 17 specific fix items + 4 deliverables. Then a follow-up "no text-only example slides" rule. Then the "did you put the correct video for the slide" pushback that became v9.1.

### v9 fixes applied
1. **RealTalk slide overhauled** (#1+#2+#3): ▶ play caption added under each video tile, REF/HYP boxes enlarged 0.6"→0.85" (no more truncation), STRIP REF rewritten to "you'd buy something and say thanks marty oh when he died" for clearer narrative contrast vs HYP "when he died my daughter's tutor said to her", footer relabeled "Source: RealTalk conversational dataset.   BLUE = good (trust)   ORANGE = mid (review)   PURPLE = bad (don't trust)".
2. **Example 5 wrong video** (#4): initially removed the Obama placeholder and dropped the slide; v9.1 restored with the correct `judge_entity` clip (4D634qUi2BI bernreuter→rogers solar PV).
3. **Three-tier policy card numbers clearer** (#6): "Blue right ~7 in 10 here —" → "**9 out of 10 blue words are correct**" / "**7 out of 10 blue words are correct**" / "**Less than 5 in 10 would be right**".
4. **Slide 30 truncation** (#7): smaller hero video, REF/HYP boxes enlarged, font 13→11 on long HYP run.
5. **Example 11 unclear** (#8): added inline "WHAT THE SPEAKER ACTUALLY SAID" REF block above the colored hypothesis. v9.1 also added Obama segment 5 video tile to the right column.
6. **Trust threshold slide reframed** (#9 — IMPORTANT): headline now reads "**65% of segments deliver useful output**" + "Less than 5% of bad signals slip through as useful." 71% moved to footnote. 65% applied as baseline number across the deck (value-prop S3 also bumped).
7. **Slide 39 cross-config stability** (#10): title rewritten "Why the trust signal is stable across conditions".
8. **Deployment slide moved forward** (#11): now lands right after What We Built, before the demo+examples block.
9. **Restructure** (#12): section order is now early examples (E1 Obama Trust + E2 RealTalk) → tier explanation block → later examples (E3–E11). Audience learns the tier mental model after 2 examples, then reads the rest with that model in hand. Explicit "BLUE good / ORANGE mid / PURPLE bad" line on RealTalk slide.
10. **Arabic money explicit** (#13): title now "Arabic — three engineering phases (**funded engagement**)"; "On request" → "Available — funded engagement".
11. **next_steps slide dropped** (#14): generic placeholder cards.
12. **demo_recap colors** (#15): aligned to BLUE/ORANGE/PURPLE.
13. **Pre-meeting commitment sentence removed** (#17): "Before this meeting, we'll run 3-5 of YOUR clips through the system" + "Bring a clip when you can" both deleted from canonical_scenario.

### Deferred follow-up (logged in DECK_CHANGELOG; #16)
- Replace embedded UI screenshot on `slide_client_word_color_coding` with a fresh capture in the new blue/orange/purple palette.
- Repaint per-segment burned-in HYP overlays on demo MP4s (`06_demo_videos/`) — currently still green/yellow/red.
- Speaker-notes cleanup (~58 changelog-meta hits + 12 stale slide-N references). Surgical per-builder pass needed (not bulk regex — that destroyed file indentation last try).

### Deliverables produced
- `Argos_VSP_Client_v9_May2026.pptx` (66 slides / 52 visible / 14 appendix). 7/7 audit tests pass.
- `v9_MANUAL_FIX_GUIDE_for_old_pptx.md` — 13 prioritized by-hand fixes for Round 8 deck if v9 unavailable.
- `v9_NAVIGATION_GUIDE_for_existing_pptx.md` — slide-by-slide what-to-say + Q&A backstops.
- `.claude/plans/i-need-to-create-proud-cupcake.md` — Round v9 section appended.

---

## 2026-05-03 — Cheat sheet redo (one page)

| # | Request | Status |
|---|---------|--------|
| 1 | Redo `QA_CHEAT_SHEET.md` as a 1-page-max top-ideas-and-answers sheet (drop slide-by-slide notes, drop verbose framing, keep only top Q&A + lines to land + don't-say swaps) | done |

### Applied
- `QA_CHEAT_SHEET.md` shortened from 383 lines to ~50 lines: closing line, three anchor numbers, three lines-to-land, 13-row top Q&A table, don't-say→say swaps, pull-only block.
- `QA_CHEAT_SHEET.pdf` regenerated via `/tmp/build_cheatsheet_pdf.py` (reportlab) — single page, letter, dense tables.
- Per-slide talking points removed (they live in `v9_NAVIGATION_GUIDE_for_existing_pptx.md`, no need to duplicate).
