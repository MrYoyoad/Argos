# Argos VSP Client Deck — Changelog

**File:** `Argos_VSP_Client_*.pptx` (currently `Argos_VSP_Client_Round8_May2026.pptx`)
**Generator:** `docs/_research-tools/generators/generate_client_presentation.py`
**Builders:** `docs/_research-tools/generators/presentation/slides_client.py`

This is the per-deck changelog. Every visible change to the client deck
gets an entry here BEFORE the commit lands, so a future reader can see
both what changed and *why*. Audits (style linter, number audit) catch
mechanical regressions; this file is the human-readable record for
narrative / framing / story decisions audits can't see.

## Format

Each entry:

- **Date** (YYYY-MM-DD)
- **Round** (the working name we used in the convo)
- **Headline** (one line)
- **WHAT** (one to three short bullets)
- **WHY** (one bullet — the user feedback or audit finding that triggered it)
- **FILES** (paths)
- **COMMIT** (short SHA, looked up via `git log`)

Reverse-chronological: newest entry on top.

---

## 2026-05-03 — **Round 8 — Audit-driven cleanup pass on Round 7** (LANDED)

User reviewed Round 7 + posted 27 specific feedback items + Opus 4.7 review (6 fixes). Three parallel sub-agents executed; final integration here.

**Group A (slides 8, 17, 20–25, 26, 30, 32, 33, 36, 37, 38, 40):**
- Slide 8: replaced "camera angle" reason (symmetrical to our model — doesn't differentiate) with FATIGUE & ATTENTION + TRAINING SCALE — both real structural human-vs-system gaps.
- Slide 17 (new positive example): added video poster + bigger TRUST tier badge + "Overall confidence ~95%" line.
- Slides 20–25 (judge examples): added video posters via new `video_key` parameter on `_client_judge_ex_slide`. Three-column layout when video present.
- Slide 26 (headline): 62% → **71%** (post-aggregation NIV-Y+P from MBR-default production state).
- Slide 30: added "tier-first, colors second" caption below screenshot.
- Slide 32 (three-tier UI): rounded percentages 23.8/37.5/38.7 → 24/38/39.
- Slide 33: added video poster (`salvage` clip).
- Slide 36 (NUMBERS-AND-NAMES card): softened from "1 million vs 1 billion at 96% confidence" alarm to "still being tuned, verify against the video — known sharp edge."
- Slide 37 title: "The model can produce confident text that's wrong" → "When the model is wrong about a topic — what it looks like."
- Slide 38: added Obama-flagged video poster.
- Slide 40 speaker note: full plot explanation (Trust 99% / Salvage 87% / Strip 23%, calibration story).

**Group B (slide drops + hides + slide 52 rewrite):**
- DROPPED from order: `slide_25d` (jesus phonetic-bridge example too sketchy), `slide_client_failure_worked_example` (item 17 not useful).
- HIDDEN added: 41 (failure_taxonomy_full), 51 (aggregation_safety before/after bars — Opus said deck-redundant), 53 (pipeline_detailed bulk diagram).
- Slide 52 (`validation_intro`) REWRITTEN — emphasizes runtime confidence vs. design-time IS metric (Opus pointed out this slide was misleading — "IS isn't what runs at deployment time"). Now correctly distinguishes calibration metric from runtime signal.
- Speaker-note slide-number references repaired after slide moves.

**Group C (slide 46/47/48 reshapes + What's-Next reorder + 3 user-confirmed fixes):**
- Slide 43 (`claims`): dropped 1 more pair (5→4), bumped body Pt(13)→Pt(14), row_h 0.62"→0.72". Reads at projection scale now.
- Slide 44 (`trust_without_ground_truth`): swapped CONFIG STABILITY card with WILD VIDEOS framing per item 19. **Q1 fix**: rewrote "GROWS IN YOUR HANDS" body to make domain-training-pass explicit (was implying automatic online learning). **Q2 fix**: speaker notes now flag that the 16-config stability claim was measured on the design-time IS metric (per `docs/evaluation/is_cross_config_validation.md` §10.4) — not the runtime confidence signal. Visible card now talks about wild-video validation, which is the more honest claim for the runtime story.
- Slide 45 (`trust_operating_points`) RESHAPED with capture/loss numbers per item 20: 630 trusted / 602 captured useful / 1 in 22 misled / 322 useful below threshold. 4-step click-reveal.
- Slide 55 (`engineering_journey`): milestone CHRONOLOGY reordered per item 24. Months 1–2 (Research integration → 37 bugs fixed across three open-source codebases) → Months 2–4 (Production refactor + dual-environment, parallel) → Months 4–5 (Confidence layer) → Months 5–6 (N-best aggregation + judge validation).
- Slide 56 (`deployment_options`): reframed from cost-ladder to "we handle both, same cost" per item 25.
- Slide 60 (`arabic_high_level`): removed the "Which Arabic — MSA / Levantine / Egyptian / Gulf?" question; replaced with "small research pass on Arabic data — risk is low, mostly engineering work" per item 26.
- **Section 13 reordered per item 27**: NEW first slide `slide_client_try_it_out` (PILOT / ADAPT / DECIDE cards) → multi-speaker (moved from §6) → Arabic (now first option) → quality_filter → next_milestone → feedback_loop → partnership_ask.

**Q1 (overpromise fix)**: GROWS IN YOUR HANDS pill on slide 44 + slide 28 footer reframed to make domain-training-pass explicit. No automatic-online-learning implication.

**Q2 (config stability metric vs confidence)**: VERIFIED — the 16-config Pearson r=0.925 stability claim was measured on the IS metric (per §10.4), not on the runtime confidence aggregate. Visible card on slide 44 now uses wild-video framing instead. Speaker note carries the verified attribution.

**Q3 (slide 45 numbers)**: 630 trusted / 602 captured useful / 322 useful lost / 1 in 22 misled — all from `docs/confidence/client_trust_calibration.md`, all approved.

**Final state**: 70 slides total / 14 hidden / 56 visible. Audits 7/7 green.

- **COMMIT**: 02e9852.

---

## 2026-05-03 — **Round 7 cut — `Argos_VSP_Client_Round7_May2026.pptx`** (LANDED)

User reviewed Round 6 deck and posted 26 specific feedback items. Most are simplifications, slide drops, and "make it feel like a finished product" reframes. Plan: `.claude/plans/i-need-to-create-proud-cupcake.md` § Round 7. Executed via 3 parallel sub-agents.

**Wording / cosmetic (Agent 1):**
- Slide 10 (`what_we_built`): scrubbed "Intelligibility Score" / "WER" / "IS" → "calibrated metrics" / "well-measured against expert review" / "agreement scores."
- Slide 31 (`three_tier_policy`): dropped the bottom anchor ("18% to 93%…") — moved to speaker notes.
- Slide 47 (`claims`): body bumped 11pt → 13pt; row_h 0.55" → 0.62"; dropped one philosophical pair ("Confidence equals factual truth"); reworded "Replace human review in high-stakes use" → "Replace human judgment for time-critical decisions". 6 → 5 pairs.
- Slide 48 (`trust_without_ground_truth`): added italic line "Validated on real-world wild video — varied quality, lighting, head angles, multi-speaker scenes — no curated benchmark."
- Slide 59 (`engineering_journey`): title "four passes, four months" → "four passes, **six** months."
- Slide 39 (`halluc_caught`): de-alarmed with "These are cases the model already routes away from your team. You see the safe outputs."
- Output examples (17, 19, 20, 22, 25): added per-slide confidence labels ("model rated this segment high-confidence" / "mixed-confidence segment").
- Slide 26: speaker notes cleaned of overstated hallucination framing.
- Slide 33 (`reader_example`): replaced networking example with a non-overlapping conversational segment ("interesting thing to do…").

**Slide replacements (Agent 2):**
- Slide 49 (`trust_operating_points`) → REPLACED with single recommendation ("Trust if ≥ 30% of words are green") + footer pill noting reviewer can override at any time. 2-step click-reveal.
- Slide 55 (`aggregation_safety`) → REPLACED with before/after bar comparison (68% → 71%, +2.7 pp; styled like slide 53's bar chart).
- NEW slide between examples 1 and gallery: `slide_client_example_simple_positive` — non-Obama everyday segment ("because as far as i know i haven't seen it").
- Slide 30 (`word_color_coding`): screenshot enlarged to 10" × 4.95", centered.

**Structural moves + appendix + plot (Agent 3):**
- Reading order: word-color (30) → how-reviewer-reads (31) → three-tier UI (32). Reviewer mental model lands first.
- Slide 16 (`video_gallery`) moved to appendix (hidden, after thank_you).
- Dropped from order: `slide_failure_deep_2` (academic borrow) and `slide_client_preprocessing_summary` (subsumed).
- "What's next" reframed: quality_filter → "Optional add-on"; arabic → "Available — on request"; next_milestone → "Optional — domain-specific training run"; feedback_loop → "How a domain-tuned version comes together". Multi-speaker stays as the only "in flight" engineering item.
- Appendix: pulled academic 8-stage pipeline PNG into hidden `slide_pipeline_appendix` (height-bound wrapper around `slide_17_png` to clear footer).
- Slide 40: replaced unhelpful IS-confidence-gate plot with new clean 3-bar chart (Trust 99% / Salvage 87% / Strip 23% useful output). New generator: `docs/_research-tools/generators/generate_tier_useful_plot.py`. Image: `confidence_tier_useful.png`.
- HIDDEN_SLIDES recomputed: 13 hidden total. BORROWED_SLIDES updated post-renumbering.

**File rename:** `Argos_VSP_Client_Round6_May2026.pptx` → `Argos_VSP_Client_Round7_May2026.pptx`. Generator output, both audit `DECK` constants, PRE_MEETING_CHECKLIST, this header all updated.

71 slides total / 58 visible / 13 hidden. Audits 7/7 green. Old Round-5/6 files retained on disk as frozen references.

- **COMMIT**: fa7e3e0.

---

## 2026-05-02 — **Round 6 cut — `Argos_VSP_Client_Round6_May2026.pptx`** (LANDED)

The 5.x sub-versions piled up to a substantive jump. Promoted to Round 6.

**File rename**: `Argos_VSP_Client_Round5_Apr2026.pptx` → `Argos_VSP_Client_Round6_May2026.pptx`. Generator output path + both audit `DECK` constants updated. Old Round-5 file kept on disk as a frozen reference.

**What's new since Round 5.0**:

- **Trust section rebuilt and substantially expanded** — three-tier UI policy slide (31), how-to-read (32), worked Salvage example (33), case studies (34, 35), pitfalls (36), hallucination trio (37–39), confidence-gate plot (40), failure taxonomy (42–44), claims/non-claims (47), trust-without-ground-truth (48), trust operating points (49). The trust section is now ~22 visible slides — the differentiator of the deck.
- **N-best aggregation production switch** (engineering): `VSP_NBEST=1` flipped to default in `lib/decode.sh` so the model evaluates 20 alternative readings on every video by default. `hyp_mbr` is the default displayed output (judge-validated +40 net Y+P verdicts vs top-1, paired McNemar p=0.0002). MBR confidence + the three-tier UI policy now apply to all videos.
- **Headline numbers refreshed** to the latest 1,497-segment evaluation: NIV-Y 23%→24%, three-tier shares 22.7/35.7/36.9 → 23.8/37.5/38.7. Rounded headlines (62% / 24% / 1 in 5) hold under both top1 and MBR.
- **MBR screenshot** rendered from real production output replaces the older synthetic/top1 PNG.
- **6 judge example slides rebuilt** in client style — uniform 2-column layout (REF/HYP left, READER'S VIEW right card), plain-English takeaways, no jargon.
- **Click-reveal animations on 32 visible slides** — true bullet-by-bullet pacing (entry shows title + subtitle only; every card requires a click). 0 OOXML issues, 71 fade transitions intact.
- **Multiple jargon scrubs** — visible slides now say "overall confidence ≥ 82%" instead of "segment confidence ≥ 0.82", "Green words right ~9 in 10" instead of "Green ≥ 85% reliable", "20 alternative readings" instead of "n-best aggregation", etc. Concrete numbers stay; math notation goes.
- **Audit bug fix**: caught a stale "23%" → "24%" on slide 18.

**Validation under PowerPoint**:
- 71 slides total / 60 visible during presentation / 11 hidden in appendix.
- 38 animated slides — 32 with bullet-by-bullet click-reveal, 6 with 3-step entry/click/click pattern (judge examples).
- Every animated shape has a valid shape-id reference. Timing trees use the 3-level par nesting PowerPoint 365 expects.
- Every slide has a fade transition.
- 7/7 audits green (number_audit + style_compliance).

**Container engineering changes** carried separately in `docs/container-sync-changelog.md` entries #30 + #31.

---

## 2026-05-02 — Round 5.16f — True bullet-by-bullet click-reveal everywhere (LANDED, 7ade2be)

**11 more slides got click-reveals** (subagent): 5 (NOT cards), 8 (human-ceiling cards), 9 (visemes), 29 (two-layer columns + anchor), 42 (5 failure modes), 60 (deployment options), 62 (quality-filter funnel), 65 (next-milestone cards), 66 (feedback-loop ask), 69 (recap), 70 (next steps), + 6 judge-example slides via the shared `_client_judge_ex_slide` helper.

**Critical pacing fix**: flipped all 20 `add_animations(...)` calls from `click_reveal=True` → `False`. With True, the first card was visible on slide entry; only the rest revealed on click. With False, every card requires a click — true bullet-by-bullet pacing. Slide entry now shows just title + subtitle + footer.

**PPTX OOXML validation**: scanned all 38 animated slides — 0 orphan shape-id references, timing trees well-formed, 71 fade transitions intact. Audits 7/7.

---

## 2026-05-02 — Round 5.16e — Audit pass: tightening, click-reveals, judge-ex rebuild (LANDED)

User-driven audit pass with parallel-agent execution.

**Bullet-by-bullet click-reveal animations** (entries fade in one by one as the speaker clicks; ends N1-N10 walls-of-text):
- slide 26 (3 headline numbers), slide 31 (3 tier cards + bottom anchor), slide 32 (3 numbered steps + anchor), slide 36 (3 reviewer rules), slide 47 (6 paired claims + anchor), slide 48 (4 trust signals + 2 footer pills), slide 49 (3 trust thresholds + anchor) — main agent.
- slide 7 (3 comparison rows), slide 10 (6 build cards), slide 55 (3 aggregation cards + anchor), slide 59 (4 milestones), slide 67 (3 partnership cards + anchor) — subagent.

**6 judge example slides rebuilt in client style** (slides 20, 21H, 22, 23H, 24H, 25 — dropped older academic typography, unified to 2-column layout matching `slide_client_reader_example`: title + accent + italic subtitle + REF/HYP left, READER'S VIEW gold-bordered card right, color-coded HYP, plain-English takeaway, closing line, legend). Subagent introduced `_client_judge_ex_slide` helper to enforce uniformity. Speaker notes preserved.

**Tightening** (audit medium/low items):
- slide 5: dropped trailing italic line; three cards already do the work.
- slide 18: dropped defensive footnote ("Headline numbers come from full 1,497 baseline").
- slide 8: trimmed citation block + 3 card bodies.
- slide 33: 2-column rework (REF/HYP left, READER'S VIEW right card full-height).
- slide 35: dropped per-word percentage list; "Every word below 25% confidence — no signal anywhere."
- slide 36 card 1 (NUMBERS AND NAMES): trimmed 75 words → 45 words; same point.
- slide 48 (4 trust signals): each card body trimmed ~20%.

Audits 7/7 green. Deck rebuilt at 71 slides, 60 visible.

- **COMMIT**: bf08729.

---

## 2026-05-02 — Round 5.16d — Tighter jargon-vs-precision balance on tier slides (LANDED)

User feedback on 5.16c: "they are not stupid children just not probabilities jargon, you can use numbers where reasonable." Re-tightened slide 31 + salvage/strip case studies + slide 32 footer to keep concrete numbers, drop only the math notation.

- **Slide 31 (three-tier):** thresholds now show as `overall confidence ≥ 82%` / `65–82%` / `< 65%` (was vague "high/medium/low"). Promise lines: "Green words right ~9 in 10 (85–93% depending on segment quality)" / "Green right ~7 in 10 here — verify names, numbers, dates" / "Green would be right <5 in 10 — coloring would mislead, so we hide it." Bottom anchor restored to a numeric range: "How often a green word is right runs from 18% to 93% depending on the segment. Below 65% overall confidence we hide the colors rather than mislead."
- **Salvage / Strip case studies:** "Medium/Low overall confidence" → "Overall confidence 79% (Salvage tier)" / "Overall confidence 21% (Strip tier)" — concrete values with tier label parenthetical.
- **Slide 32 footer:** "Aggregation now runs by default..." → "By default, the model considers 20 alternative readings of every segment and shows the safest consensus — on every video." Concrete + actionable.
- **Audit:** added 79% / 21% to canonical percentage list; 7/7 green.
- **COMMIT**: `bcfd282`.

---

## 2026-05-02 — Round 5.16c — MBR screenshot + jargon scrub + deep number audit (LANDED)

- **WHAT**:
  - Regenerated `ui_word_confidence_screenshot.png` from the actual production MBR-aggregated output (4 segments from the 1,497-segment baseline, real calibrated per-word confidence). Same Argos dark theme, plain-English subtitle.
  - Slide 26 speaker note: counts refreshed to MBR-displayed (NIV-Y+P 924→927/61.7%→61.9%, NIV-Y 361→358/24.1%→23.9%, hallucination 20.5%→20.7%); top1 baseline numbers retained as a parenthetical so both are auditable.
  - Slide 31 (three-tier UI): replaced jargon thresholds ("segment confidence ≥ 0.82", "0.65 to 0.82", "P(correct | green)") with plain-English equivalents ("high / medium / low overall confidence", "Whether a green word is right depends on the segment it sits in"). Trust promise rephrased to "Green words right ~9 out of 10". Speaker notes carry the technical thresholds and the MBR-recalibration follow-up note.
  - Salvage-tier and Strip-tier case-study slides: "segment confidence 0.79"/"0.21" → "Medium/Low overall confidence".
  - Demo word-color-coding legend: "GREEN: confident AND beams agreed" → "GREEN: confident, multiple alternatives agreed".
  - HTML demo report legend (`generate_client_demo_report.py`): "trust = confident AND beams agreed" → "trust = confident, alternatives agreed".
- **WHY**: User: "screen shot for MBR? baseline numbers with it? confidence and ALL! AUDIT WELL AND DEEP. dont say MBR usue simple english in pptx! generally audit for unnecessary jargon that is hard to follow for them and fix it." Verified MBR-default numbers: WER 64.05→63.84%, IS 2.532→2.547, NIV-Y 24.1→23.9%, NIV-Y+P 61.7→61.9%, hallucination 20.5→20.7% — visible rounded headlines (62% / 24% / 1 in 5 / 2.5) hold under both.
- **FILES**: `slides_client.py` (slide 26 + 31 visible + speaker, 32-aggregation footer, salvage + strip case studies, word-color-coding legend), `generate_client_demo_report.py` (HTML legend), `01_plots_for_slides/ui_word_confidence_screenshot.png` (regenerated).
- **COMMIT**: 325bca5.

---

## 2026-05-02 — Round 5.16b — n-best v3 judge truth + VSP_NBEST default flipped (LANDED)

- **WHAT**:
  - `slide_client_aggregation_safety`: card 3 swapped "WORD ERROR RATE DOWN (~1.6 pp)" → "CALIBRATED CONFIDENCE" (vote_conf wins WER, but we ship MBR — don't misattribute). Footer: "becoming default after one more validation pass" → "MBR aggregation now ships as the default displayed output (env-gated; override available)."
  - Speaker notes (aggregation_safety + engineering_journey): retracted v1 framing ("ship vote_conf or MBR — probably both"), replaced with v3 dual-conf truth (MBR +2.7 pp Y+P p=0.0002, vote_conf +2.1 pp p=0.0026, vote_score n.s.); MBR-over-vote_conf rationale (intra-rater 86.7%, calibrated per-word posterior); v1 27% drift retraction note.
  - `lib/decode.sh`: VSP_NBEST default 0 → 1 — MBR confidence + tier filtering now run on every video. Container overlay synced.
- **WHY**: User directive — "the MBR confidence and confidence-dependent filtering should apply to all videos." Plus the v3 judge writeup landed and supersedes the v1-contaminated framing in earlier slides.
- **FILES**: `slides_client.py` (aggregation_safety, engineering_journey notes), `lib/decode.sh`, `vsp_linux_container_FINAL_20260217/lib/decode.sh`, `docs/container-sync-changelog.md` (entry #31), `docs/paper/presentation-remarks-log.md` (Batch 21, items 267–269).
- **COMMIT**: d475a63.

---

## 2026-05-02 — Round 5.16 — Refresh numbers from latest 1,497-segment eval (LANDED)

- **WHAT**: Slide 26 NIV-Y card 23% → 24%; slide 31 three-tier shares 22.7/35.7/36.9 → 23.8/37.5/38.7. Speaker notes + audit canonical list updated. No structural change.
- **WHY**: Latest `english_full_nbest_eval/report/report.csv` (1,497 segs) shows IS≥3.80 hit 24.1% (was 23.1%); per_segment_safety.csv (1,427 segs) tier distribution shifted under joint band rule.
- **FILES**: `slides_client.py` (headline_numbers, three_tier_policy), `tests/unit/test_number_audit.py` (CANONICAL + approved updates).
- **COMMIT**: 32599e7.

---

## 2026-05-02 — Round 5.15 — Three trust thresholds (operating points) in trust section (LANDED)

NEW slide 49 (`slide_client_trust_operating_points`) — three named
operating points from `docs/confidence/client_trust_calibration.md`
(full 1,497-segment evaluation under the joint confidence + agreement
band rule). Three cards: PERMISSIVE (≥30% green / 65% recall / 1 in
22 misled / default for most workflows), MODERATE (≥50% / 34% / 1
in 35 / when precision > recall), STRICT (≥70% / 8% / 1 in 71 /
high-stakes downstream). Anchor: *"We default to permissive. Each
downstream workflow can dial its own threshold against precision/
recall tradeoff."* Footer: *"Measured on the full 1,497-segment
evaluation under the joint confidence + agreement band rule.
Re-runnable."*

Pairs with slide 32 (three-tier UI policy) — slide 32 = the system's
built-in safety policy (Trust/Salvage/Strip controls what the UI
shows); slide 49 = the client workflow's configurable trust knob
(how many green words constitute trust). Complementary, not
redundant. Inserted in §Trust after `trust_without_ground_truth`.

Source files:
- `docs/confidence/client_trust_calibration.md` (polished operational
  reference)
- `docs/_research-tools/generators/analyze_client_trust_calibration.py`
  (re-runnable generator)
- `english_full_nbest_eval/client_trust/CLIENT_TRUST_CALIBRATION.md`
  + `client_trust_calibration.csv` (auto-generated source data)

Stats: 70 → **71 slides** (+1 visible). 59 → 60 visible.
HIDDEN_SLIDES indices shifted +1 for slides at/after position 49:
{50, 57, 61, 68} (was {49, 56, 60, 67}).
BORROWED_SLIDES: {44, 45, 59, 71} (was {44, 45, 58, 70}).
3 new approved percentages: 65%, 34%, 8% (the three recall figures).
All 7 audits green. Fade transitions still apply to all slides.

### COMMIT
- 0486b2c.

---

## 2026-05-02 — Round 5.14 — Aggregation-safety evidence in validation (LANDED, terse)

NEW slide 54 (`slide_client_aggregation_safety`) — n-best aggregation
evidence from `docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md`
(1,497-segment LLM-judge evaluation, May 2 2026, dual-conf prompt).
Three cards: +2.7pp Y+P verdicts (paired-McNemar p=0.0002 for MBR),
asymmetric rescue pattern (gains at the bottom, no losses at the top),
−1.6pp WER for vote_conf. Anchor: *"The 62% review-useful and 82%
agreement numbers were measured WITHOUT aggregation. With it, they're
floors, not ceilings."* Inserted in §Validation after
cross_config_stability.

Stats: 69 → **70 slides** (+1 visible). 58 → 59 visible.
HIDDEN_SLIDES indices shifted +1 for 56/60/67 (was 55/59/66).
BORROWED_SLIDES: {44, 45, 58, 70} (was {44, 45, 57, 69}).
All 7 audits green.

### COMMIT
- 90d4afe.

---

## 2026-05-02 — Round 5.13 — Deployable-today framing + client-feedback ask (LANDED)

User directive (4 items):
1. Make clear the product is ~98% deployable today; upgrades cost money.
2. Make clear Arabic + LLM-upgrade aren't "mere updates" — real engineering investment.
3. Add a soft client-feedback ask: we built confidence, we need real users to validate it on real video.
4. Keep the fade-transition rule across the deck.

### Slide-content changes
- **Slide 10 (`what_we_built`)** — subtitle changed: *"Six things actually exist today, end-to-end, on real data"* → *"Six things shipped end-to-end. Deployable today on what you have."* Footer changed: *"Everything you'll see today is in production today — not a 'with more research it could…' projection"* → *"Deployable today. Domain-specific upgrades — Arabic, stronger LLM, multi-speaker — are real engineering work, scoped separately."*
- **Slide 62 (`arabic_high_level`)** — added a gold "scope honesty" pill: *"This is real engineering work — not a configuration flip. Arabic is a separately-scoped, separately-funded effort."* Body line below: *"Realistic timeline: 2–3 months from go. Costs scale with dataset size and dialect coverage."* Replaces the implicit "easy update" framing.
- **Slide 63 (`next_milestone`)** — subtitle expanded: *"Today works. Two things make it noticeably better"* → *"Today works and is deployable. Two upgrades, both real engineering investment, take it further."* SMARTER MODEL card body: now says *"Real training run, not a config flip."* TRAINED ON YOUR CONTENT card body: *"Coordinated training run; data + compute + engineering time, scoped together."* Footer: *"Today's 62% review-useful is real and deployable. Each upgrade is its own scoped, funded effort — not bundled."*

### NEW slide 64 — `slide_client_feedback_loop_ask`
Lands AFTER `next_milestone` (technical upgrade ask) and BEFORE `partnership_ask` (budget conversation). The beat: "we did the engineering on the confidence layer; the next signal — what does this look like in actual reviewer workflows — is something only your team can give us."

- Title: *"What we'd ask of your team"*
- Headline: *"We've built the confidence layer. The signal we can't generate alone is real reviewer feedback on real video."*
- Three soft-ask cards: RUN IT ON YOUR VIDEO / HAVE YOUR ANALYSTS READ / TELL US WHERE COLORS HELP
- Anchor: *"We did the engineering. The end-user signal closes the loop — and the calibration tightens around your actual content."*
- Footer: *"A pilot's worth of analyst-hours, end-to-end. Specifics in the partnership conversation."*

Tone: gentle, partnership-flavored, not a sales close. Specifically calls out "Not the managers — the reviewers" so it's clear the ask is for real end-user time, not stakeholder approval.

### Fade transitions still apply
The Round 5.12 post-build pass continues to apply fade transitions to all slides. Build output confirms: *"FADE TRANSITIONS applied to all 69 slides."*

### Renumbering
Adding 1 visible slide before partnership_ask shifted later slides by +1:
- partnership_ask: 64 → 65
- recap (hidden): 65 → 66
- integration_commitment: 66 → 67
- next_steps: 67 → 68
- thank_you: 68 → 69

### Stats
- 68 → **69 slides** (+1 for feedback_loop_ask).
- **57 → 58 visible** during presentation (the new slide is visible; recap stays hidden at its new position 66).
- All 7 audit/linter tests **green**.
- HIDDEN_SLIDES: 14, 21, 23, 24, 41, 45, 46, 49, 55, 59, **66** (was 65).
- BORROWED_SLIDES: {44, 45, **57**, **69**} (was {44, 45, 56, 68}).

### Files
- `docs/_research-tools/generators/presentation/slides_client.py` —
  what_we_built subtitle/footer; arabic_high_level scope pill;
  next_milestone subtitle/cards/footer; NEW
  `slide_client_feedback_loop_ask` builder.
- `docs/_research-tools/generators/generate_client_presentation.py` —
  imported and inserted feedback_loop_ask between next_milestone and
  partnership_ask; HIDDEN_SLIDES recap index 65 → 66.
- `tests/unit/test_number_audit.py` — BORROWED_SLIDES indices +1 for
  the slot shift.
- `presentation_materials_20260224/PRE_MEETING_CHECKLIST.md` —
  slide count refreshed.

### COMMIT
- bbcc6fa — Round 5.13.

---

## 2026-05-02 — Round 5.12 — Comprehensive cleanup pass (LANDED)

User feedback: Obama videos not playing, no text-appearance animations,
pipeline slide unclear, too many bad examples, "saved" framing weak,
remove surveillance references, multi-speaker should read as
engineering not risk, less selling-feel + fewer words, general overview
at the start, feet→meters, back numbers with literature.

### CRITICAL FIX: Obama videos not playing
Root cause: `auto_avsr/preprocessed_flat_seg12/fast_segments/` had been
cleaned out — the VID config still pointed there but the .mp4 files
no longer existed. The `add_video()` helper silently fell back to
placeholders.
**Fix**: copied the 4 Obama videos (segments 5, 14, 19, 31) from
`flat_runs_archive/20260501_173729/` to the deck's
`06_demo_videos/` directory. Repointed `obama_perfect`,
`obama_partial`, `obama_flagged`, `clean_obama19` VID keys to the new
local paths. Cleared the cached poster frames so they regenerate
from the new sources. Videos now actually exist alongside the deck
and don't depend on a working pipeline directory.

### NEW: slide-level fade transitions on every slide
User: "no appearance animations of text." Full per-shape entrance
animations on 60+ slides was out of scope; the simpler win is
slide-level fade transitions so navigating to a slide gives a
perceptual entrance. Implemented as a post-build pass in the
orchestrator using `add_fade_transition` from helpers.py. All 68
slides now fade in.

### Pipeline slide reorder
User: "pipeline slide is unclear and not in animation — better to get
the simpler one from the original march pptx that appears before."
- **Moved** `slide_client_pipeline_components` (3-component overview)
  from old slide 9 to new slide 4 — gives the audience a mental model
  of the system before any use-case detail.
- **Hidden** `slide_client_pipeline_detailed` (the 8-stage academic
  diagram, was slide 55) — too dense, the simpler 3-component
  overview now covers the pipeline beat earlier.

### Surveillance references removed (visible text)
User: "remove the surveillance references they are not needed; for the
canonical scenario give a dry detail suggestion."
- Slide 2 about_argos — "WHO USES IT" rewritten from "surveillance,
  intelligence-adjacent, security..." to "investigations, archive
  review, accessibility work, footage from cameras without microphones."
- Slide 3 what_is_vsr — "Surveillance footage, archive video" →
  "Camera without a microphone, archive video."
- Slide 5 canonical_scenario — title from "Your canonical scenario —
  and ours" → "What the system is built for"; subtitle now neutral
  technical conditions. Removed "surveillance" from the slide
  metadata; speaker notes acknowledge the use case is broader.
- Slide 37 halluc_problem — closing line "dangerous-failure mode for
  surveillance" → "the dangerous-failure mode."
- Speaker-note references to "surveillance" left in place
  (presenter-only).

### Multi-speaker slide 11 reframed as engineering work
User: "make it clear that multi speaker is engineering and not a
project risk but rather work to do."
- Title from *"Multi-speaker: today vs. the path forward"* →
  *"Multi-speaker — engineering work, in flight"*
- Subtitle from *"...where we are honestly today, and where we go
  next"* → *"One centered speaker today. Two-speaker support is a
  preprocessing layer we're already building."*
- Path-card body: *"Engineering work, in flight — not research."*
- Footer: *"Engineering work, not a research bet. Path is concrete."*

### Selling-language trim
User: "less selling feel — no 'we deploy' / 'no cost for you' /
'partnership' overdone — be neutral."
- Slide 2 about_argos tagline — from *"We build production-grade visual
  speech recognition"* → *"Visual speech recognition with built-in
  confidence."*
- Slide 64 partnership_ask — title from *"The next milestone is a
  partnership"* → *"Going to production — the partnership."* Body
  trimmed.
- Slide 66 integration_commitment — title from *"We deploy this on
  your infrastructure"* → *"Locally deployable, end-to-end."* Cards
  shortened (e.g. *"On-premise or your cloud. Your hardware, your
  rules."* → *"On-prem or private cloud."*).

### Feet → meters
- Slide 5 canonical_scenario — *"20–50 feet from camera"* → *"6–15 m
  from the speaker."*

### Human-ceiling slide reframed for offline + literature backing
User: "explain why manual lip reading is hard offline with a video,
not reasons for live translation. back up the numbers with literature."
- Title kept *"Why even expert humans cap at 45–52%"*.
- Subtitle from *"Lip-reading is hard for biological reasons..."* →
  *"Even with the video paused and reviewed frame-by-frame, the
  visual signal itself is information-limited."*
- Three cards rewritten:
  - VISIBLE-SOUND OVERLAP (live-translation-flavored) →
    **VISEMIC AMBIGUITY** (offline-relevant): "About half of English
    phonemes share a mouth shape..."
  - SPEED OF SPEECH (live-only constraint) →
    **CAMERA ANGLE & DISTANCE**: "Off-axis or distant cameras shrink
    the mouth region. Pausing doesn't add pixels..."
  - FATIGUE (live-only) →
    **SPEAKER IDIOSYNCRASY**: "Each speaker's mouth shapes differ.
    Accent, dental anatomy, beard, lipstick all change the visual
    signal..."
- Literature footer added: *"45–52% range: Bear & Harvey 2017
  (Phoneme-to-Viseme Mappings); Assael et al. 2016 (LipNet); reviewed
  across trained-human lip-reading studies."*

### "Why saved matters" framing strengthened on case studies
User: "unclear why the 'saved' texts are important."
- Slide 33 (Salvage networking) closing line: *"This is what
  review-useful means in practice"* → *"Without colors, this segment
  looks garbled — a reviewer writes it off. With colors, it becomes
  a usable summary. That's the difference."*
- Slide 34 (topic-shift) closing: *"This is the failure mode the
  colors are built to catch"* → *"Without colors, the wrong topic
  enters the reviewer's summary as fact. With colors, it stops at
  the flag."*
- Slide 35 (Strip-saves) closing: *"Strip tier is the system refusing
  to mislead you"* → *"Without this signal, a fabricated quote
  enters the transcript and downstream reports. With it, the segment
  is labelled 'no signal.'"*

### More slides hidden (cuts to "not needed" content)
HIDDEN_SLIDES grew from 7 (Round 5.11) to 11. Newly hidden:
- **14** demo_recap "What you just saw" — thin transition; demo
  speaks for itself.
- **49** what_this_means "What this means for your workflow" — thin
  closer; the trust section already conveys the workflow implication.
- **55** pipeline_detailed (8-stage diagram) — superseded by the
  simpler 3-component overview moved up to slide 4.
- **65** recap "Three things to take with you" — close section was
  4 slides (recap + integration + next_steps + thank_you); 3 is enough.

### Stats
- **68 total slides → 57 visible** during presentation (was 61).
- All 7 audit/linter tests **green**.
- All 68 slides have fade transitions.
- 4 Obama videos copied into deck-local `06_demo_videos/` (the .pptx
  embeds the video data; the source files are also kept locally as
  redundancy for re-builds).
- BORROWED_SLIDES indices unchanged (slide_data_flow at 56,
  slide_thank_you at 68 — physical positions preserved).

### Files
- `docs/_research-tools/generators/presentation/slides_client.py` —
  about_argos tagline + WHO USES IT card; what_is_vsr MUTED card;
  canonical_scenario reframed (title, subtitle, three cards);
  human_ceiling reframed (subtitle, three cards, literature footer);
  multi_speaker reframed (title, subtitle, body, footer);
  reader_example closing; case_topic_shift closing; case_strip_save
  closing; integration_commitment trimmed; partnership_ask trimmed;
  halluc_problem closing.
- `docs/_research-tools/generators/presentation/config.py` — Obama
  VID keys repointed from `auto_avsr/...` to deck-local
  `06_demo_videos/`.
- `docs/_research-tools/generators/generate_client_presentation.py` —
  pipeline_components moved up in the builders list; HIDDEN_SLIDES
  expanded to 11 entries; fade-transition post-build pass added.
- `presentation_materials_20260224/06_demo_videos/050111_OsamaBin*.mp4`
  — 4 Obama videos copied in (segments 5, 14, 19, 31).
- `.poster_frames/obama_*.jpg` and `clean_obama19.jpg` — deleted to
  force regeneration from the new video sources.

### COMMIT
- 75d40bc — Round 5.12.

---

## 2026-05-02 — Round 5.11 — Coherence audit cleanup (LANDED)

External visual-QA agent audited all 68 slides as fresh eyes. Findings
synthesized into prioritized fixes; user approved the cuts. Round 5.11
applies obvious-win cleanups + 7 hide-slide trims.

### Color palette consistency (slides 32 + 36)
The deck uses **green / yellow / red** on Obama trio (17, 19), per-word
color screenshot (30), and case-study slides (33, 34). Slides 32 and
36 inherited blue/orange/purple wording from `docs/features/per-word-
confidence-user-guide.md` (the user guide explicitly notes both palettes
exist). Confusing for the audience to encounter both. Round 5.11
rewrites all visible blue/orange/purple references to green/yellow/red:
- Slide 32 card 2: *"Green means confident. Yellow means best guess.
  Red means uncertain."*
- Slide 32 card 3: *"...verify against the video — even when green."*
- Slide 33 reader's-view: *"Green spine: ..."*
- Slide 36 numbers/names card: *"Even when green. Real example..."*
- Slide 36 tier-comes-first card: *"A green word in a Strip segment
  isn't the same as a green word in a Trust segment."*
- Speaker notes that say "blue spine / purples" left in place
  (presenter-only, doesn't reach audience).

### Slide-content fixes
- **Slide 12 (`demo_intro`)** — was *"Nothing here is pre-cached. The
  pipeline runs in your browser."* but slide 13 frames it as
  *"End-to-end demo recorded by the presenter."* Reconciled: slide
  12 now says *"A short walkthrough of the actual pipeline."* — no
  more live-vs-recorded contradiction.
- **Slide 60 (`quality_filter`)** — title was *"Pre-processing 2 —
  Quality pre-filter"* but no Pre-processing 1 exists in the visible
  deck (entity-split is on slide 11 but isn't numbered). Renamed to
  *"Quality pre-filter — reject bad clips before decode."*
- **Slide 67 (`next_steps`)** — visible footer *"Customize per-client
  during prep — placeholder copy intentionally generic."* removed;
  moved to speaker notes (presenter-facing only). Audience no longer
  sees the staging signal.
- **Slide 68 (`thank_you`)** — stats line referenced metrics never
  mentioned in the body (37 bugs, 8 research reports, 13 experiments,
  6 quality signals, 5 failure categories). Trimmed to: *"1,497
  segments • Trust / Salvage / Strip three-tier UI • 8-stage pipeline
  • cloud or on-prem deployment"* — all of which are in the body.

### NEW: HIDDEN_SLIDES post-build XML mechanism
Per user direction *"put the old ones in hide,"* added a post-build
step in `generate_client_presentation.py` that walks the saved
`<p:sldId>` elements and sets `show="0"` on selected indices. Slides
stay physically in the .pptx file (preserved as backup, easy to
re-enable) but PowerPoint skips them during presentation.

**7 slides hidden:**
- **21** — Output Example 2 (judge_ex2 "Truncated but Core Preserved").
  Overlaps `slide_client_example_partial` (slide 19).
- **23** — Output Example 4 (judge_ex4 "Scientific Vocabulary Lost").
  Overlaps Output Example 3 (judge_ex3 "Technical Vocabulary Drift",
  kept). Per-user "cut to 3" judge-example trim.
- **24** — Output Example 5 (judge_ex5 "Cooking Domain"). Domain too
  specific for surveillance audience. Per-user "cut to 3" trim.
- **41** — `trust_dashboard` "62% useful — on real-world video, not
  benchmark data." Duplicates slide 26 headline + footer caveat.
- **45** — `slide_25d` (LLM Salvage 3 cases). Per Round 5.10, the
  new Mode 2.2 + Mode 3.1 case-study slides (34, 35) cover similar
  ground with stronger framing.
- **46** — `slide_client_hallucination_flag` "1 in 5 segments
  auto-flagged." Duplicates slide 26's "1 in 5" headline + slides
  34/35 SHOW the flagging mechanism rather than telling.
- **59** — `_section_whats_next` transition. Five section transitions
  was too many for a 2-hour meeting; Act 3's What's Next pivot is
  implicit from the partnership ask sequence.

### Stats
- **68 total slides → 61 visible during presentation** (7 hidden,
  preserved in file).
- All 7 audit/linter tests **green**.
- BORROWED_SLIDES indices unchanged — physical positions preserved.
- No new percentages added; no FORBIDDEN_PATTERNS triggered.

### Visual-QA findings explicitly NOT acted on
- "Aspect ratio mismatch on slides 16, 20-25, 34, 35" — verified false
  positive. Deck slide_width × slide_height = 13.333 × 7.500 in (16:9)
  uniformly. The agent's perception was a soffice rendering artifact
  on slides containing video shapes.
- "Slide 17/19 video posters look like blank discs in PDF" — soffice
  doesn't render video posters in PDF; in PowerPoint these are
  clickable poster frames showing the actual lip-crop.
- "Slide 51 validation methodology should be 3-step visual" — punted.
  The current paragraph reads cleanly and the validation section is
  short enough that restructuring brings little benefit.
- "Slide 1 logo treatment vs other slides" — punted. Title-slide
  treatment is intentional per Round 5 framing-v2 alignment.

### Files
- `docs/_research-tools/generators/presentation/slides_client.py` —
  color-palette text rewrites on slides 32 + 33 + 36 + slide 12 demo
  framing + slide 60 title rename + slide 67 footer removal (moved
  to notes).
- `docs/_research-tools/generators/presentation/slides_future.py` —
  `slide_thank_you` stats line trimmed.
- `docs/_research-tools/generators/generate_client_presentation.py` —
  added HIDDEN_SLIDES list + post-build XML hide mechanism.

### COMMIT
- 9fecf40 — Round 5.11.

---

## 2026-05-02 — Round 5.10 — Case-study slides + redundancy cut (LANDED)

User wrote `docs/features/aggregation-and-confidence-case-studies.md`
— a richer, more dramatic worked-examples deepening of the per-word
confidence user guide. Two new examples are particularly powerful
and weren't in the deck before: Mode 2.2 (gardening segment
hallucinated as nuclear-weapons content — fluent, plausible expert
speech on the wrong topic) and Mode 3.1 (Strip-tier segment where
the model produced "I don't think that's a good idea" — every word
wrong, every word at <25% confidence). Round 5.10 brings both into
the deck and cuts one now-redundant slide to keep the count under
control.

### NEW slide 34 — `slide_client_case_topic_shift` (Mode 2.2)
The most dangerous failure mode the colors save you from. REF is
gardening (woody beds, hula culture, excavation). HYP is nuclear
weapons (warheads, nuclear deterrence, Cuban missile crisis).
Internally consistent fluent speech on a totally wrong topic.
Layout: Salvage badge + banner → REF + color-coded HYP on the left
→ video poster on the right (real speaker at a whiteboard) →
READER'S VIEW pill explaining the save: *"Without colors, a
downstream pipeline records this segment as a discussion of nuclear
weapons. Wrong tags, wrong summaries, wrong searches. With colors,
every topic-defining wrong word is flagged."* Closing line: *"This
is the failure mode the colors are built to catch."*

### NEW slide 35 — `slide_client_case_strip_save` (Mode 3.1)
Strip tier catches fluent fabrication. REF was about China crossing
the Pacific Ocean. HYP was *"I don't think that's a good idea"* —
grammatically perfect English, sounds like a confident opinion,
every word wrong, every word below 25% confidence. Layout: Strip
badge + banner → REF + plain-grey HYP (per Strip policy) →
per-word confidence numbers (i 6%, don't 4%, think 14%, …) →
video poster (the actual segment) → READER'S VIEW: *"With this
signal, the segment is correctly labelled 'no signal' and the
reader goes to the video. No false belief is created."* Closing:
*"Strip tier is the system refusing to mislead you."*

### Cuts: slide_client_example_flagged dropped from active deck
The Round 5 Obama trio (slides 17/19/20: perfect/partial/flagged)
duplicated content with the hallucination trio (slides 36-38, now
37-39). Both showed Obama segment 5's "Rwanda's genocide" failure.
Round 5.10 drops the §Real-Outputs flagged slide; the dramatic
hallucination-trio version remains. The Obama duo (perfect +
partial) still anchors §Real Outputs with recognizable content.

The builder `slide_client_example_flagged` stays defined in
`slides_client.py` — only removed from the orchestrator import +
builders[] list. Easy to re-import if the user wants the trio back.

### Pitfalls slide enriched (slide 36)
First card body updated to include a concrete real-world example
from the case-studies doc: *"Real example from the evaluation: the
model said '1 million CFUs' when the speaker said '1 billion CFUs'
— at 96% confidence. Always verify numbers, dates, dollar amounts,
and proper names against the video."* Makes the abstract rule
concrete in one beat without overcrowding the card.

### Renumbering impact
Net +1 slide vs Round 5.9 (+2 added, −1 dropped). Slide indices
between dropped position (20) and insertion point (after slide 33)
shifted −1; slides at or after insertion point shifted +1.

| Slide | Title |
|---|---|
| 17, 19 | Obama duo (perfect/partial); was Obama trio |
| 20–25 | Six judge examples (was 21–26) |
| 26 | Three numbers (was 27) |
| 29 | Two layers ("triage not truth") (was 30) |
| 30 | Per-word color coding (was 31) |
| 31 | Three-tier UI (was 32) |
| 32 | How to read (was 33) |
| 33 | Salvage worked example (was 34) |
| **34** | **NEW Mode 2.2 — topic-shift hallucination** |
| **35** | **NEW Mode 3.1 — Strip catches fluent fabrication** |
| 36 | Three rules (was 35) — now enriched with 1M/1B example |
| 37–39 | Hallucination trio (was 36–38) |
| 47 | Claims/non-claims (was 46) |
| 55 | 8-stage pipeline (was 54) |
| 63 | Next milestone (was 62) |
| 64 | Partnership ask (was 63) |
| 68 | Thank you (was 67) |

### Stats
- 67 → **68 slides** (+2 new − 1 dropped).
- All 7 audit/linter tests **green**.
- BORROWED_SLIDES indices updated for net +1: now `{44, 45, 56,
  68}` (was `{43, 44, 55, 67}`).
- 4 new percentages added to the canonical-or-derivative whitelist:
  25%, 35%, 53%, 96% (Mode 3.1 per-word probabilities and the 1M/1B
  numeric/entity false-confidence example on the pitfalls slide).
- 1 new VID key (`case_topic_shift`) + 1 alias (`case_strip_save`
  reuses an existing video file via a semantically-named key).
- 1 video file copied into `06_demo_videos/`
  (`o6Zwa1rEWpM_1__2e8fce13.mp4`).

### Companion deliverable updates
- `PRE_MEETING_CHECKLIST.md` — slide indices refreshed to 68-slide
  layout; new dry-run check items for slides 34 + 35; Obama-trio
  reference updated to the duo.
- `QA_CHEAT_SHEET.md` + `.pdf` — two new per-slide LAND lines (34,
  35); existing slide cues renumbered for the −1/+2 shift; Obama
  trio cue now references slide 39 in the hallucination trio for
  the "Rwanda's genocide" content.

### Files
- `docs/_research-tools/generators/presentation/slides_client.py` —
  two new builders: `slide_client_case_topic_shift`,
  `slide_client_case_strip_save`. Updated `slide_client_pitfalls`
  first card body with the 1M/1B example.
- `docs/_research-tools/generators/presentation/config.py` — added
  `case_topic_shift` and `case_strip_save` VID keys.
- `docs/_research-tools/generators/generate_client_presentation.py`
  — imported the two new builders, inserted into builders list
  between `slide_client_reader_example` and `slide_client_pitfalls`;
  removed `slide_client_example_flagged` from imports + builders.
- `tests/unit/test_number_audit.py` — BORROWED_SLIDES indices +1
  shift; whitelist of 4 new approved percentages.
- `presentation_materials_20260224/06_demo_videos/o6Zwa1rEWpM_1__2e8fce13.mp4`
  — NEW (copied from `vsp_input_backup/`).
- `presentation_materials_20260224/PRE_MEETING_CHECKLIST.md`,
  `QA_CHEAT_SHEET.md` + `.pdf` — refreshed.

### COMMIT
- eec6d09 — Round 5.10.

---

## 2026-05-02 — Round 5.9 — "How to read a transcript" operational slides (LANDED)

User wrote `docs/features/per-word-confidence-user-guide.md` (May 1)
— a clean reader-facing guide that distills the operational workflow
(30-second rule, decision flow, common pitfalls). The deck had the
WHAT of the trust signals (slides 30, 31, 32) but no HOW-TO-USE.
Round 5.9 fills that gap.

### Three new slides between three-tier UI (32) and hallucination trio
- **Slide 33** — `slide_client_how_to_read` — *"How a reviewer
  actually reads the output"*: three numbered horizontal cards
  (1 CHECK THE TIER / 2 READ THE COLORS / 3 OVERRIDE FOR NUMBERS AND
  NAMES) with bottom anchor *"Reading well is using both signals —
  tier first, colors second."*
- **Slide 34** — `slide_client_reader_example` — Salvage worked
  example from the user guide. Tier badge + amber banner up top, REF
  + color-coded HYP, READER'S VIEW pill walking through how a
  reviewer extracts meaning from the blue spine while discounting
  the red words. Closing line: *"This is what 'review-useful' means
  in practice."*
- **Slide 35** — `slide_client_pitfalls` — *"Three rules every
  reviewer learns"*: NUMBERS AND NAMES need the video / STRIP TIER
  isn't for word-by-word reading / THE TIER COMES FIRST. Three
  warning-style cards (gold/coral/teal borders).

### Plain English throughout
Per the latest "no super technical details, no stupid numbers"
directive: no parameter counts, no calibration percentages on the
visible slides, no jargon. Empirical numbers (94% / 80% / 65% / 41%
etc.) live in speaker notes only. Slide voice reads like a human:
*"Open a segment. Look at the tier badge first. If Trust, read
normally. If Salvage, read around the blue anchors. If Strip, don't
read word-by-word."*

### Why these slides matter for the audience
- **Cold prospect**: answers *"what do my reviewers actually do with
  this?"* — the operational discipline is reassuring.
- **Co-partners**: signals the system has a real reviewer workflow,
  not just confidence theater. Pitfalls slide is particularly strong
  here.
- **Existing client team**: gives the user-guide a visible touchpoint
  in the deck so they know the deliverable exists.
- **Stealth buyer (existing client team lead)**: sees that the
  reviewer-side UX is thought through end-to-end.

### Renumbering impact (+3 shift)
All slides after slide 32 shifted by +3:
- Hallucination trio: 33-35 → 36-38
- Validation section: 46-49 → 49-52
- Engineering section: 50-53 → 53-56
- What's-next section: 54-58 → 57-61
- Next milestone (Round 5.8): 59 → 62
- Partnership ask: 60 → 63
- Thank you: 64 → 67

### Stats
- **64 → 67 slides** (+3 for the operational instruction set).
- All 7 audit/linter tests **green**.
- BORROWED_SLIDES updated for +3 shift: indices now `{43, 44, 55,
  67}` (was `{40, 41, 52, 64}`).
- No new percentages on visible slides (kept off intentionally —
  empirical numbers in speaker notes only).
- No FORBIDDEN_PATTERNS triggered.

### Companion deliverable updates
- `PRE_MEETING_CHECKLIST.md` — slide indices refreshed to 67-slide
  layout; three new dry-run check items for slides 33-35.
- `QA_CHEAT_SHEET.md` + `.pdf` — three new per-slide LAND lines for
  slides 33-35; all downstream slide-cue indices shifted by +3.

### Files
- `docs/_research-tools/generators/presentation/slides_client.py` —
  three new builders: `slide_client_how_to_read`,
  `slide_client_reader_example`, `slide_client_pitfalls`.
- `docs/_research-tools/generators/generate_client_presentation.py` —
  imported and inserted between `slide_client_three_tier_policy` and
  `slide_client_halluc_problem`.
- `tests/unit/test_number_audit.py` — BORROWED_SLIDES indices +3.
- `presentation_materials_20260224/PRE_MEETING_CHECKLIST.md` —
  refreshed.
- `presentation_materials_20260224/QA_CHEAT_SHEET.md` + `.pdf` —
  refreshed.

### COMMIT
- 26255bc — Round 5.9.

---

## 2026-05-02 — Round 5.8 — "What the next milestone changes" (LANDED)

User feedback: the deck is too gentle on the technical direction
behind the partnership ask. `slide_client_partnership_ask` (now slide
60) talks about LOGISTICS — your data / our pipeline / one training
run — but doesn't name WHAT the investment buys technically. A
reader walks away thinking "they need money" without thinking "they
need money for THIS specific upgrade with THIS evidence."

Round 5.8 inserts ONE new slide before `partnership_ask` that names
the technical direction (stronger LLM backbone + more domain data),
grounds it in the empirical evidence (data-limited fine-tuning
hit the ceiling cleanly), and preserves the "still very usable
today" framing by tying back explicitly to the 62% review-useful
headline.

### NEW slide 59 — `slide_client_next_milestone`
- Title: *"What the next milestone changes"*
- Subtitle: *"Today's results are what's possible at the current data
  scale. Here's what production scale unlocks."*
- Two technical cards with TODAY/PATH structure:
  - **STRONGER LLM BACKBONE** (teal border):
    TODAY = "Seven-billion-parameter language brain. Two generations
    behind state-of-the-art."
    PATH = "Drop-in upgrade to a newer, larger, better-trained LLM.
    Same architecture, better grasp of uncommon vocabulary, names,
    and domain terms. No integration change."
  - **MORE DOMAIN DATA** (gold border):
    TODAY = "A small training slice from public data — below the
    empirical floor for stable retraining."
    PATH = "Production-scale dataset on YOUR domain — your speakers,
    your vocabulary, your camera conditions. Especially powerful
    paired with the stronger backbone."
- Bottom anchor pill: *"WHY YOU SHOULD BELIEVE THIS: small fine-
  tuning experiments hit the data-limit ceiling cleanly — empirical
  proof."*
- Footer: *"This is the next gain on top of the 62% review-useful
  you saw today. Direction is known. Magnitude lands in the
  partnership."*

### What stayed off the slide (deliberate restraint)
- **No specific Llama version**. "Stronger LLM backbone" is durable;
  "Llama 3.1 8B" dates the slide. Speaker notes name Llama 3.1 8B,
  3.3 70B, or current state-of-the-art for if asked.
- **No specific lift number**. "Substantial improvement" is fine in
  voice; a slide with "WER → 30%" would be a credibility trap.
- **No LoRA r-values, no 1,273-segment count**. Both are in
  FORBIDDEN_PATTERNS per Round 3 (training-mechanics jargon stays
  out of client slides). Speaker notes describe the experiments
  generically ("two small fine-tuning experiments at different
  parameter scales, both severely overfit at ~95% train / ~60% val").

### Speaker notes
Carry the IF-ASKED defenses:
- IF asked WHICH LLM → name Llama 3.1 8B / 3.3 70B / current SOTA
- IF asked about the empirical floor → describe the overfit signal
  generically + point to docs/finetuning/training-research-notes.md
- IF pressed on lift size → "we expect substantial improvement;
  magnitude is what the partnership measures, not what we assert"
- VOICE FRAMING (out loud, not on slide): "Today's 62% review-
  useful is what's possible at this data scale. We expect production
  scale to improve this a lot — newer LLM, more data on your domain,
  both validated as the binding constraints."

### Stats
- 63 → **64 slides** (+1 for the new milestone slide).
- All 7 audit/linter tests **green**.
- BORROWED_SLIDES: only the last index shifts (slide_thank_you 63 →
  64). Earlier borrows unchanged.
- No new percentages added; no FORBIDDEN_PATTERNS triggered after
  fixing the v1 draft (had 1,273 + r=16/r=64 in speaker notes,
  rewritten to generic phrasings).

### Companion deliverable updates
- `PRE_MEETING_CHECKLIST.md` — slide indices refreshed to 64-slide
  layout; new dry-run check item for slide 59.
- `QA_CHEAT_SHEET.md` + `.pdf` — new per-slide LAND line for slide
  59 + IF-ASKED Llama-version answer + lift-size restraint note.
  All downstream slide-cue indices shifted by +1.

### Files
- `docs/_research-tools/generators/presentation/slides_client.py` —
  new `slide_client_next_milestone` builder (~120 lines).
- `docs/_research-tools/generators/generate_client_presentation.py` —
  imported and inserted between `slide_client_arabic_high_level`
  (slide 58) and `slide_client_partnership_ask` (now slide 60).
- `tests/unit/test_number_audit.py` — BORROWED_SLIDES last index
  bumped 63 → 64.
- `presentation_materials_20260224/PRE_MEETING_CHECKLIST.md` and
  `QA_CHEAT_SHEET.md` + `.pdf` — slide indices refreshed; new cue.
- `presentation_materials_20260224/Argos_VSP_Client_Round5_Apr2026.pptx`
  + `.pdf` — rebuilt.

### COMMIT
- ebfddfc — Round 5.8.

---

## 2026-05-01 — Round 5.7 — Aggregate strategy notes (LANDED, no visible slide)

User updated the n-best aggregation analysis (107-segment evaluation
+ temperature-scaling calibration). Per-method calibration JSON
landed at 22:07 alongside the existing aggregator-method WER table;
full 1,497-segment evaluation kicked off in `english_full_nbest_eval/`
and is still running. Per Round 5.6 plan, this stays out of the
visible deck — a partial-eval headline is too premature for a
client claim, and the data is rich enough to defend in Q&A from
speaker notes alone.

### What landed
- **Speaker note expansion on slide 53** (`engineering_journey`) —
  Mission 6 shipped May 1, partial 107-segment eval shows
  hyp_vote_conf winning every metric (WER 59.35% → 57.20%, IS +0.029,
  NIV-Y+P +0.9pp), agreement-vs-posterior caveat (voting inflates
  per-word agreement scores because beams aren't independent samples),
  temperature-scaling fix validated (calibrated ECE 0.064 for
  vote_conf vs 0.086 for top-1), full 1,497-segment eval running.
- **NEW Q&A in `QA_CHEAT_SHEET.md`** — *"Is there more you can do to
  improve accuracy beyond the current numbers?"* — pull-question
  answer with the 3.6%-relative-WER number, the temperature-scaling
  caveat, and the framing *"vote_conf for the transcript, top-1 for
  the trust signal"*.

### What did NOT land
- No new visible slide. The §What's Next section is already 4 slides
  (quality_filter, preprocessing_summary, arabic, partnership_ask)
  ending in the partnership ask; adding a 5th between would dilute
  the close. The trust section already has 17 slides; aggregation is
  not a credibility beat, it's an accuracy beat — wrong section.
- No headline number anywhere visible. 107 ≠ 1,497. Framing the
  partial result as a hard claim would invite the same overclaim
  trap Round 5.5 hardened against.

### Why notes-only is the right call
The aggregation result is real and partially validated; pulling a
co-partner thread on it gives you 3-5 minutes of substantive
engineering material. But the meeting's narrative weight is on
trust + workflow (the headline numbers, the three-tier UI, the
hallucination case study). Keeping aggregation in notes preserves
the deck's pose: ship what's validated, defend what's measured, talk
about what's coming.

### Sources cited in the speaker note
- `docs/beam-search/n_best_implementation.md` — full writeup
- `tuning_results/exp_nbest_validation/aggregator_method_summary.json`
  — WER table
- `tuning_results/exp_nbest_validation/calibration.json` —
  T-scaling experiment results
- `english_full_nbest_eval/decode_output/decode.log` — running

### Files
- `docs/_research-tools/generators/presentation/slides_client.py` —
  speaker-note expansion on `slide_client_engineering_journey`.
- `presentation_materials_20260224/QA_CHEAT_SHEET.md` + `.pdf` —
  new pull-question Q&A on accuracy improvements.
- `presentation_materials_20260224/Argos_VSP_Client_Round5_Apr2026.pptx`
  + `.pdf` — rebuilt to embed the updated speaker note (no visible
  slide change).

### COMMIT
- e686a01 — Round 5.7.

---

## 2026-05-01 — Round 5.6 — Confidence findings update (LANDED)

The May 2026 confidence work landed three things since Round 5.5
shipped: (1) **band-reliability stratification** showing P(correct|green)
ranges 18-93% across segment quality (overall 80.6%, but 92.8% in
high-quality segments and 21.8% in low-quality ones), (2) **three-tier
UI policy** (Trust ≥0.82 / Salvage 0.65–0.82 / Strip <0.65) wired to
production via `make_report.py` on 2026-05-01, and (3) **B3 sidecar
landing** so the per-word color-coding screenshot can finally use
real per-token confidence instead of the synthetic WER-aligned
version.

The deck's trust section didn't reflect any of this. Round 5.6 is a
narrow update: one new slide, one screenshot regen, four speaker
note touch-ups. The new slide turns the band-reliability finding
into a credibility move ("we measured this and built the UI around
it") rather than a research caveat.

### NEW slide 32 — `slide_client_three_tier_policy`
- Title: *"How the report handles uncertainty"*
- Subtitle: *"Green's reliability isn't uniform. We measured it across
  23,261 words. Here's the policy that follows."*
- Three horizontal cards: TRUST (≥0.82, 22.7% of segments, full
  coloring, green ≥85% reliable) / SALVAGE (0.65–0.82, 35.7%, full
  coloring + amber banner *"Verify names, numbers, critical details"*)
  / STRIP (<0.65, 36.9%, coloring removed, plain grey text — green
  <50% reliable here, would mislead).
- Bottom anchor: *"P(correct | green) ranges from 18% to 93% across
  segment quality. The UI removes coloring where it would lie."*
- Source line: *"Measured on 23,261 words from 1,427 real-world
  segments. Distribution from the 1,497-segment baseline."*
- Speaker notes carry the full stratification table (very high 92.8% /
  high 83.8% / mid 69.6% / mid-low 41.3% / low 21.8% / very low 18.2%)
  and the asymmetric-cost framing ("wrong-and-green is the only
  unrecoverable cell — strategy bounds wrong-green rate, not maxes F1").
- Insertion: between `slide_client_word_color_coding` (slide 31) and
  `slide_client_halluc_problem`. New position: slide 32.

### REGEN slide 31 — `ui_word_confidence_screenshot.png`
- Was: synthetic confidence (derived from WER alignment between HYP
  and known REF) — visible on the screenshot since the original B3
  sidecar was still being computed.
- Now: real per-token confidence from B3 sidecar (`/tmp/vsp_b3_full_out/
  hypo-172610.json` + `confidence-172610.json`, 2026-04-30).
- Process: ran `generate_client_demo_report.py --decode hypo-172610.json
  --filter "050111_OsamaBinLadenStatement_HD" --out
  obama_demo_report.html`, screenshotted via headless Chromium at
  1920×4500, cropped top 1100px to a single-segment-rich frame.
- Speaker note rewrite: removed the "currently synthetic" caveat;
  replaced with *"Real per-token confidence from the B3 sidecar (May
  2026). Same coloring policy now lives in `make_report.py` and
  ships with every pipeline run."*

### Speaker note touch-ups
- **Slide 27 (`headline_numbers`)**: appended note pointing at the
  three-tier breakdown on slide 32 (Strip 36.9% / Salvage 35.7% /
  Trust 22.7%) without changing visible numbers.
- **Slide 30 (`two_layer_confidence`)**: appended IF-ASKED answer
  for "how reliable is the green coloring?" pointing to slide 32.
- **Slide 44 (`trust_without_ground_truth`)**: appended note
  acknowledging that the four runtime signals are NOT uniformly
  reliable across segment quality; the UI itself enforces the
  three-tier policy.

### Companion deliverable updates
- `PRE_MEETING_CHECKLIST.md` — slide indices refreshed for 63-slide
  layout, dry-run check items renumbered, slide 32 added to the list.
- `QA_CHEAT_SHEET.md` + `.pdf` — new Q&A *"How reliable is the green
  coloring?"* with the stratification + three-tier framing. New slide
  32 cue in the per-slide section. All downstream slide-cue indices
  shifted by +1.

### Stats
- **62 → 63 slides** (+1 for the new three-tier policy slide).
- All 7 audit/linter tests **green**.
- BORROWED_SLIDES exemption updated for the +1 shift: indices now
  {40, 41, 52, 63} (was {39, 40, 51, 62}).
- 7 new percentages added to the canonical-or-derivative whitelist:
  22.7%, 35.7%, 36.9% (tier shares); 85%, 50% (reliability bounds);
  18%, 93% (stratification range).

### Deferred to Round 5.7 (per user direction)
- N-best aggregation slide (Mission 6, 107-segment evaluation):
  user is updating the analysis. Will weave in once the new numbers
  land. Code shipped, gated by `VSP_NBEST=1`, default OFF; partial
  evaluation in `tuning_results/exp_nbest_validation/`.

### Files
- `docs/_research-tools/generators/presentation/slides_client.py` —
  new `slide_client_three_tier_policy` builder; speaker-note
  touch-ups on `slide_client_headline_numbers`,
  `slide_client_two_layer_confidence`, `slide_client_word_color_coding`,
  `slide_client_trust_without_ground_truth`.
- `docs/_research-tools/generators/generate_client_presentation.py` —
  imported and inserted `slide_client_three_tier_policy` between
  `slide_client_word_color_coding` and `slide_client_halluc_problem`.
- `tests/unit/test_number_audit.py` — BORROWED_SLIDES indices for
  63-slide layout; whitelist of 7 new approved percentages.
- `presentation_materials_20260224/01_plots_for_slides/ui_word_confidence_screenshot.png` —
  regenerated from real B3 sidecar.
- `presentation_materials_20260224/01_plots_for_slides/obama_demo_report.html` —
  regenerated for the screenshot capture.
- `presentation_materials_20260224/PRE_MEETING_CHECKLIST.md` — slide
  indices refreshed.
- `presentation_materials_20260224/QA_CHEAT_SHEET.md` + `.pdf` —
  new Q&A + slide-32 cue + downstream slide-index shift.

### COMMIT
- d7ca96c — Round 5.6.

---

## 2026-05-01 — Round 5.5 — Credibility hardening (LANDED)

External critique session (ChatGPT critique → Claude review of the
critique → user adjudication) converged on six high-value changes
that don't restructure the deck but harden it against attack from a
skeptical technical audience. The critic's own meta-frame: *"Don't
treat the deck as fundamentally broken — it's already doing the
right big thing. The goal is not restructuring. The goal is
credibility hardening."* All six changes landed in this round.

### 1. "Expert reviewer" → "independent blind evaluator" (CRITICAL)
- **Risk**: the deck used "independent expert reviewer" repeatedly,
  implying a human panel had reviewed all 1,497 segments. The actual
  validation is Claude Opus 4.6 acting as a blind judge. If a
  technical co-partner asked "was this a human?" mid-meeting, the
  answer "no — an LLM judge" would land badly because the framing
  had implied human.
- **Fix**: every visible "expert reviewer" / "independent expert"
  phrase rewritten to "independent blind evaluator" / "independent
  blind evaluation." Speaker notes on the validation slides expanded
  with the honest Q&A answer ("for scale, the full 1,497-segment
  calibration used a blind frontier-LLM evaluator with no access to
  our scores. That is not a substitute for human validation on your
  footage. It is the development calibration step.").
- **Files touched**: 6 visible-text instances + 2 speaker-note
  instances across `slides_client.py`.

### 2. NEW slide: "What we claim — and what we do not claim"
- 6-row two-column table: WE CLAIM (✓ green) vs WE DO NOT CLAIM
  (✗ coral). Closes with anchor pill: *"Not blind automation.
  Reviewable visual-speech intelligence with uncertainty attached."*
- Lands in the trust section between `slide_client_hallucination_flag`
  and `slide_client_trust_without_ground_truth` (now slide 42).
- New builder `slide_client_claims` in `slides_client.py`.

### 3. Reframe 62% headline language
- **Before**: "62% useful output" / "Six of every ten segments
  deliver usable text — viewers can extract meaning even when the
  wording isn't perfect."
- **After**: "62% review-useful" / "Six of every ten segments contain
  enough recoverable meaning to be useful for human review."
- **Why**: harder to attack. "62% useful" invites *"useful for
  what — court evidence? autonomous decisions?"*. "62% recoverable
  meaning useful for human review" answers the question pre-emptively.
- Also reframed the 23% and 1-in-5 cards in the same direction
  (clean/fast pass; routed instead of silently accepted).

### 4. "Confidence is triage, not truth" visible line
- Added as a centered subtitle on `slide_client_two_layer_confidence`
  (slide 30) — the entry point to the trust section. The two-card
  layout pushed down from y=1.7" → y=2.0" to clear the new anchor.
- Single sharpest credibility sentence in the deck. The user's
  critic called it the "cleanest credibility sentence."

### 5. Cherry-pick disclaimer footers on gallery slides
- Both `slide_client_video_gallery` (slide 16) and
  `slide_client_clean_outputs_gallery` (slide 18) now carry a
  small-print footer: *"Examples are illustrative. Headline numbers
  come from the full 1,497-segment baseline — not from selected
  clips."* Defuses the "demo magic" question pre-emptively.

### 6. "A credible system must know when NOT to decode" tagline
- Added to `slide_client_quality_filter` (now slide 55) as a sharp
  closing tagline above the technical caption. Reframes the
  quality-pre-filter from "future ablation" to "credibility move."

### NEW deliverable: Q&A cheat sheet
- `presentation_materials_20260224/QA_CHEAT_SHEET.md` — a
  phone-readable answer sheet for the 10 most-likely audience
  questions ("how accurate?", "was the reviewer human?", "could it
  be misused?", etc.). Includes the cleanest credibility lines, a
  "do not say" list, and an opening / closing line. Memorize, do
  not read.

### Stats
- 61 → **62 slides** (+1 for the new claims/non-claims slide).
- All 7 audit/linter tests **green**.
- BORROWED_SLIDES exemption updated for the +1 shift: indices now
  {39, 40, 51, 62}.
- Slide indices throughout the deck shifted by +1 after slide 41
  (where the new claims slide inserted).

### Files
- `docs/_research-tools/generators/presentation/slides_client.py` —
  new `slide_client_claims` builder; "expert reviewer" sweep;
  headline-numbers card reframe; "Confidence is triage, not truth"
  anchor on slide 30; cherry-pick footers on gallery slides 16 + 18;
  slide-55 closing tagline.
- `docs/_research-tools/generators/generate_client_presentation.py` —
  imported and inserted `slide_client_claims` in the trust section.
- `tests/unit/test_number_audit.py` — BORROWED_SLIDES indices for
  62-slide layout.
- `presentation_materials_20260224/PRE_MEETING_CHECKLIST.md` — slide
  indices refreshed to Round 5.5 layout; Q&A cheat sheet linked at
  the top.
- `presentation_materials_20260224/QA_CHEAT_SHEET.md` — NEW.

### What we explicitly did NOT do (per critic adjudication)
- Did NOT restructure the deck order. Round 5.2/5.3 ordering is
  already iterated and field-tested for a 2-hour meeting.
- Did NOT cut examples. User explicitly directed us to ADD examples
  in earlier rounds (after diagnosing the deck as hollow); reverting
  that without explicit override would discard 4 rounds of work.
- Did NOT add "verified corrections feed future calibration" claims.
  That feedback loop doesn't exist as a feature; shipping a slide
  claiming it would be a fabrication risk.
- Did NOT replace "near-zero, flagged" with "no silent model error."
  Latter overclaims in a different direction.
- Did NOT add a separate go/no-go gate slide — the existing quality
  pre-filter slide already does this; just added a closing tagline.

### COMMIT
- 82eb964 — Round 5.5.

---

## 2026-05-01 — Round 5.4 — Video correction + slide 18 video tiles (LANDED)

User reviewed Round 5.3 and flagged two issues:

1. **Wrong Obama videos on slides 17 + 19**. The videos were the
   *lip-crop* preprocessed versions from `preprocessed_flat_seg12/
   video/` — tight mouth-only crops (~165 KB) that show what the
   model sees, not what humans see. Slide 20 (segment 5) was already
   using the full-frame `fast_segments/` version and was fine.
   **Fix**: switched all three Obama VID keys to `fast_segments/`
   (~9 MB, full-frame Obama at the podium). Cleared the cached
   poster frames at `.poster_frames/obama_*.jpg` so the helper
   regenerates them from the correct source.

2. **Slide 18 had no videos**. The clean-output gallery was 6 cards
   of label + quote with no playable video. **Fix**: added a clickable
   video tile per card (1.65" wide × 1.75" tall), with label/quote
   in a right-side column. Card height bumped 1.55" → 1.95" to fit.
   Six new VID keys (`clean_conversational`, `clean_legal`,
   `clean_public`, `clean_tech`, `clean_motivational`, `clean_obama19`)
   point to burned-video MP4s — the HYP overlay matches the quote
   shown so picture and text agree. Five burned videos copied from
   `english_full_results/client_outputs/burned_videos/` into
   `presentation_materials_20260224/06_demo_videos/`.

### Stats
- 61 slides (no net change). All 7 audits green.
- 11 new VID keys total (3 obama_* in 5.3 + 6 clean_* in 5.4).
- 5 video files copied into `06_demo_videos/`.
- Cached poster frames invalidated; helpers regenerate from sources.

### Files
- `docs/_research-tools/generators/presentation/config.py` — switched
  obama_perfect/_partial/_flagged to fast_segments/ paths; added
  6 clean_* keys.
- `docs/_research-tools/generators/presentation/slides_client.py` —
  `slide_client_clean_outputs_gallery` re-laid out for video + text.
- `presentation_materials_20260224/06_demo_videos/` — 5 burned
  video MP4s copied in.
- `presentation_materials_20260224/.poster_frames/obama_*.jpg` —
  deleted to force regeneration.

### COMMIT
- 26624e6 — Round 5.4.

---

## 2026-05-01 — Round 5.3 — Visual QA + IS-runtime honesty fix (LANDED)

User did a slide-by-slide review of the rendered Round 5.2 deck and
flagged six distinct issues across four slides. All addressed in
Round 5.3.

### 1. Slide 18 — Clean output gallery (gallery-card layout)
- **Issue**: Cards had ~1.3" of dead space below the green quote.
  Footer enumerated categories ("cooking, legal, tech...") that
  didn't match the actual card labels (no cooking; "Professional"
  and "Resilience" missing from the footer enumeration).
- **Fix**: Card height 1.95" → 1.55" (content fills naturally). Card
  labels rewritten to describe domain, not theme: "Professional" →
  "Legal", "Resilience" → "Motivational". Footer rewritten to
  enumerate the actual labels shown.

### 2. Slide 54 — Quality pre-filter (3 issues)
- **Issue A — label clipped**: "All uploaded clips" was cut off
  because the first 100% bar overlapped the label column. Layout
  bug: `chart_left = label_w + Inches(0.3)` was missing the MX
  offset, so bars anchored at x=label_w instead of x=MX+label_w,
  drawing on top of the label area.
- **Issue B — N° placeholder**: "Head angle ≤ N°" had an unfilled
  threshold. Replaced with "Head angle ≤ 30°" (the lip-reading
  literature limit beyond which viseme accuracy degrades sharply,
  per Petridis et al., Stafylakis et al.).
- **Issue C — percentile logic unclear**: User asked for explanation
  of why the percentages and the actual logic. The 5th "Reaches
  the model 75%" bar duplicated the 4th "Lighting/contrast 75%"
  bar — same number with different framing. **Dropped the redundant
  5th bar** and made the final filter row green to signal
  "this is what reaches the model." Added an explainer line above
  the chart: *"Each row = clips remaining after that gate. Out of
  100 uploaded clips, 75 reach the model."* — names the cumulative
  semantics clearly. Added a per-row "rule" sub-label on the right
  ("viseme accuracy drops past 30°", "lower face must be unoccluded",
  "lip-region contrast within range"). Speaker notes expanded with
  the academic anchor for each gate plus why these specific
  percentages (illustrative, calibrated against the 1,497-segment
  baseline; actual rates depend on the client's own footage).

### 3. Slide 49 — Pipeline diagram too small
- **Issue**: The 8-stage diagram rendered at width 6.7" on a 12.13"
  slide — only ~55% of usable area, hard to read at projection scale.
- **Fix**: Dropped the redundant subtitle, reclaimed the row, and
  bumped image height 4.3" → 5.4" (width 6.7" → 8.41", ~30% larger).
  Image now starts at y=1.55" (just below the accent line) and
  ends at y=6.95", with a small footer caption at y=7.05".

### 4. Slides 30 + 42 — "IS at runtime" honesty fix (the critical one)
- **Issue**: Both slides claimed the per-segment runtime confidence
  IS the Intelligibility Score (IS). User flagged: "Per-segment —
  IS combines six runtime signals, no labels required : not
  available for real video without ref!!!"
- **Why it was wrong**: IS computes WER, semantic similarity, NEA F1,
  and length ratio — **all six signals require the reference text**.
  IS is *not* runtime-computable on a video the client uploads.
- **Honest framing**: At runtime, layer 2 is the AGGREGATE of layer-1
  per-word probabilities (mean / min / fraction-high-confidence)
  plus a length-anomaly check on output vs visual frames. IS is the
  EVALUATION metric used during *development* to calibrate the
  threshold against an independent expert reviewer (82% agreement,
  next slide). The runtime number rides on that calibration but
  doesn't itself compute IS.
- **Fix on slide 30**: Layer-2 PER-SEGMENT card retitled "From the
  model's own outputs" (was "From the score system"). Bullets now
  read: "Word probabilities aggregate to one segment-level
  confidence / Plus a length-anomaly check / Calibrated thresholds
  split clearly conveyed from needs review."
- **Fix on slide 42**: PER-SEGMENT card body rewritten to "Word
  probabilities aggregate to one confidence number per segment.
  Plus a length-anomaly check on output vs visual frames. Computed
  from the model's own outputs — no reference text needed."
- **Bonus on both slides**: Added a "WHY THIS IS MEANINGFUL — AND
  HOW IT GROWS WITH YOU" pill at the bottom of each, per user
  follow-up: *"add explanation why this is meaningful — and that by
  the clients' use they will gain trust."* The pill states (a) the
  threshold isn't arbitrary — calibrated to an independent expert
  reviewer (82% agreement), and (b) each segment the client's
  reviewer verifies on their own footage extends that calibration to
  their domain. Trust grows with use.

### 5. Slides 17 / 19 / 20 — Lip-crop video posters added
- **Issue**: User flagged "more missing videos there in a previous
  slide" while reviewing the engineering section — referring to the
  three Obama example slides which were text-only (REF/HYP color-
  coded, no video). The Round-4 plan called for lip-crop video
  posters on each so audiences could click in PowerPoint and see
  what the model actually saw.
- **Fix**: Threaded an optional `video_key` parameter through the
  shared `_example_slide` helper. When set, the slide renders a
  3.4"×2.55" clickable lip-crop poster at top-right with a "Click
  to play in PowerPoint" caption beneath. REF/HYP text columns
  shrink to fill the left half. Three new VID keys added:
  `obama_perfect` (segment 14, 165 KB lip-crop),
  `obama_partial` (segment 31, 165 KB lip-crop),
  `obama_flagged` (segment 5, full-frame fast-segment fallback —
  segment 5 was missing from `preprocessed_flat_seg12/video/`).

### Stats
- 61 slides (no net change from Round 5.2).
- All 7 audit/linter tests **green**.
- BORROWED_SLIDES exemption unchanged at 4 indices.
- Net new builders: 0 (all changes are in-place edits to existing
  builders + 1 new optional parameter on `_example_slide`).

### Files
- `docs/_research-tools/generators/presentation/slides_client.py` —
  `slide_client_clean_outputs_gallery` (slide 18 layout fix);
  `slide_client_quality_filter` (slide 54 — bug fix + redesign);
  `slide_client_pipeline_detailed` (slide 49 enlarge);
  `slide_client_two_layer_confidence` (slide 30 IS-honesty + new pill);
  `slide_client_trust_without_ground_truth` (slide 42 IS-honesty +
  meaningful/grows pills); `_example_slide` helper (new `video_key`
  param); `slide_client_example_perfect / _partial / _flagged`
  (wired video keys).
- `docs/_research-tools/generators/presentation/config.py` — added
  3 Obama lip-crop video keys (obama_perfect, obama_partial,
  obama_flagged).

### COMMIT
- 1dc6c5c — Round 5.3.

---

## 2026-05-01 — Note on the demo-report bundle commit

Commit `96ed361` (originally `80580bd`, retitled via amend) carries
**9 files**, not the 1 its first title suggested. A `git reset`
between the Round-5.2 commit and a SHA-backfill commit on
DECK_CHANGELOG quietly re-staged unrelated demo-report work into the
index, which then rode along on the backfill. The commit was later
amended from *"client-deck: backfill commit SHA in Round 5.1 + 5.2
changelog entries"* → *"feat: auto-generate Argos client-styled HTML
report in every pipeline run"* so the title now matches the bulk of
what's in the diff.

**What's actually in `96ed361`:**

| File | What changed | Belongs to |
|---|---|---|
| `presentation_materials_20260224/DECK_CHANGELOG.md` | Filled in real SHA `0ef12b4` for Round 5.1 + 5.2 entries | client-deck (intended) |
| `docs/_research-tools/generators/generate_client_demo_report.py` | Generalized from Obama-only defaults to `--filter / --title / --subtitle / --source / --prefix-alias` flags | demo-report rework |
| `vsp_linux_container_FINAL_20260217/VSP-LLM/scripts/generate_client_demo_report.py` | Container mirror of the same generalization | demo-report rework |
| `lib/outputs.sh` | Wires the generalized demo report into the pipeline run | demo-report rework |
| `vsp_linux_container_FINAL_20260217/lib/outputs.sh` | Container mirror of the outputs.sh change | demo-report rework |
| `docs/features/argos-demo-report.md` | NEW — feature doc for the generalized demo report | demo-report rework |
| `docs/container-sync-changelog.md` | EC2↔container sync entry for the demo-report change | demo-report rework |
| `vsp_linux_container_FINAL_20260217/COMPLETE_CHANGELOG.md` | Container changelog entry for the demo-report change | demo-report rework |
| `vsp-ui/README.md` | UI README touch-up that was sitting unstaged | demo-report rework |

**Audit trail.** The commit log title now accurately describes the
demo-report rework (post-amend). The full sync trail for those
changes is in [`docs/container-sync-changelog.md`](../docs/container-sync-changelog.md)
(lines ~1500-1566). The Round-5.1+5.2 deck commit (`0ef12b4`) is
unaffected.

**No action required** — both the deck and the demo-report rework are
real, useful, and shipped. The DECK_CHANGELOG SHA backfill still
landed inside `96ed361`; the deck-only diff there is the 6-line edit
that filled in `0ef12b4` for the Round-5.1+5.2 entries.

---

## 2026-05-01 — Round 5.2 — Engineering depth pass (LANDED)

User feedback after Round 5.1: *"the engineering part needs to be more
meaty and include the pipeline diagram from the science presentation
at least in hide. Also more deeper saying of what we did instead of
'38 bug fixes' which is completely useless."* §Engineering went from
3 thin slides (transition + data_flow + deployment) to 5 substantive
slides with concrete engineering content.

### Pipeline diagram added
- New visible slide in §Engineering: the same 8-stage operational
  pipeline diagram (`pipeline_detailed.png`) used in the academic deck.
- Net-new client builder `slide_client_pipeline_detailed` — height-
  bound to fit slide bounds (the academic builder uses width=CW, which
  overflows our 7.5" slide for this 1.56:1 PNG).
- Eight stages visible: Normalize → Mouth Crop → ASR (eval-only side-
  branch) → LRS3 Convert → Manifests → K-means → LLM Decode → Outputs.
- Footer line clarifies ASR is eval-only: *"the visual model never
  hears audio."*

### engineering_journey rewritten + moved
- **Rewritten content** — replaced the four shallow milestones (incl.
  "37 bugs fixed and documented") with four concrete, named
  accomplishments:
  - M1 Integration: 8-stage pipeline tying auto_avsr + av_hubert +
    VSP-LLM end-to-end
  - M2 Production refactor: 823-line script → 11 reusable modules,
    37 automated tests cover module boundaries
  - M3 Confidence layer: pulled token-level softmax out of LLaMA
    decoder, built 6-signal IS, calibrated against 1,497 expert-
    reviewed segments
  - M4 Dual-environment: 26 documented sync points, offline dependency
    packaging (spaCy wheels, fairseq Cython patches) for air-gapped
    install
- **Moved** from §What-we-built to §Engineering so the engineering
  section carries the substantive depth instead of a thin "what we
  did" footnote.
- Title changed: *"How we built it — four months, four milestones"* →
  *"What it actually took — four passes, four months"*.
- Subtitle: *"Concrete engineering, not vague claims. Every pass shipped."*
- Footer: *"Every problem solved is documented. Every change is
  replicated between AWS and the production container."*
- Bug count moved to speaker notes (still factually documented in
  `vsp_linux_container/bugs-{1-13,14-25,26-37}-*.md`) — but the
  visible slide leads with what was *built*, not what was *broken*.

### Bug fix
- `slide_client_failure_taxonomy_full` was failing silently with
  `ValueError: assigned value must be type RGBColor` — two rows used
  hex strings (`"#ff5252"`, `"#ff9800"`) instead of RGBColor objects.
  Fixed by importing `RED` and `ORANGE` from config.py. Slide now
  renders as designed (5 distinct colors per failure mode).

### Stats
- **60 → 61 slides** (net +1: pipeline_detailed added; engineering_
  journey moved, not added).
- §Engineering went from **3 → 5 slides**: transition + new pipeline
  diagram + data_flow + journey + deployment options.
- §What-we-built shrunk from 3 → 2 slides (still: what_we_built +
  multi_speaker_today_vs_path).
- All 7 audit/linter tests **green**.
- BORROWED_SLIDES exemption stays at 4 indices (pipeline_detailed is
  a native client wrapper — no jargon, no exemption needed).

### Files
- `docs/_research-tools/generators/presentation/slides_client.py` —
  rewrote `slide_client_engineering_journey`; added
  `slide_client_pipeline_detailed`; added `ORANGE` to imports;
  fixed RGBColor bug in `slide_client_failure_taxonomy_full`.
- `docs/_research-tools/generators/generate_client_presentation.py` —
  removed `slide_client_engineering_journey` from §What-we-built;
  inserted `slide_client_pipeline_detailed` and
  `slide_client_engineering_journey` in §Engineering between
  `_section_engineering` and `slide_client_deployment_options`.
- `tests/unit/test_number_audit.py` — recomputed BORROWED_SLIDES
  indices for 61-slide layout.

### COMMIT
- 0ef12b4 (single commit covers both Round 5.1 and Round 5.2 since Round 5.1
  changes were never landed before Round 5.2 added the engineering depth
  pass on top of them).

---

## 2026-05-01 — Round 5.1 — Surgical fixes after Round 5 review (LANDED)

User reviewed Round 5 and flagged: N9 violations (visible WER/WWER/LoRA),
redundancy across 6 slides, structural bug (multi-speaker buried), and
several substantive gaps (no "trust without ground truth" reframe, thin
lip-reading background, no clean-output gallery, video posters not
actually playable, Arabic slide too dense). Round 5.1 addresses all of
these via slide-source edits — no rebuild from scratch.

### N9 strips (HARD FIXES)
- WER/WWER stripped from Obama example takeaway lines (perfect / partial / flagged) — narrative carries the meaning instead.
- LoRA stripped from `slide_data_flow` upstream text → "trainable adapters".
- 6 academic `slide_judge_ex1-6` replaced with `slide_client_judge_ex*` wrappers that pass `client_verdict` to `_judge_video_slide`. Score-strip header replaced with plain-English verdict tag per user spec ("Excellent — meaning fully preserved", "Good — core argument intact", etc).
- Salvage slide_25d header WER stripped upstream → "IS X | Prob Y" (LoRA-tier compromise: edits academic deck too, but the upstream really shouldn't have surfaced raw WER either).
- Arabic slide replaced with new `slide_client_arabic_high_level` — drops AV-HuBERT mentions, K-means reclustering, RTL handling, MSA-vs-dialect specifics. One paragraph + 3 questions to ask in the meeting.

### Redundancy cuts
- DROPPED `slide_client_examples_intro` (overlapped with the deeper Obama detail slides).
- DROPPED academic `slide_08` (failure taxonomy bar chart) — `slide_client_failure_taxonomy_full` (NEW) replaces it AND merges `slide_failure_deep_1a` + `_1b`.
- DROPPED `slide_25e` (jalapeno salvage — duplicates judge_ex5 already in §Real Outputs).
- DROPPED `slide_client_validation_summary` (restated 82% point already on agreement chart).
- DROPPED `slide_web_ui` (duplicate "Live Demo" placeholder; real demo is at slide 14).
- DROPPED `slide_arabic_roadmap` (replaced by `slide_client_arabic_high_level`).

### Merges
- `slide_client_failure_taxonomy_full` (NEW) — single slide with all 5 failure modes + frequencies + rule descriptions. Replaces 3 slides (slide_08 + failure_deep_1a + failure_deep_1b).
- `slide_client_partnership_ask` (NEW) — single slide with 3-beat partnership framing + bridge pill ("Data without budget is a folder…"). Replaces 2 slides (data_ask + investment_ask).

### Structural moves
- `slide_client_multi_speaker_today_vs_path` MOVED from §"What's next" to §"What we built" — the client's canonical use case appears in Act 1 instead of Act 3.

### Substantive additions (NEW builders)
- `slide_client_what_is_lipreading_not` — 3 cards distinguishing VSR from audio transcription, captioning, face recognition. Inserted after `what_is_vsr`.
- `slide_client_canonical_scenario` — coffee-shop framing (observer 30 ft away, multi-speaker, environmental challenges) + pre-meeting commitment to run the client's own clips through the system.
- `slide_client_human_ceiling` — explains why expert humans cap at 45-52% (visible-sound overlap, 150 wpm speech speed, fatigue). Inserted after `compared_to_today`.
- `slide_client_clean_outputs_gallery` — 6 IS=5.0 / WER=0% segments from across the 1,497-baseline + Obama corpus, all green text. Anchors "most clearly conveyed segments look like this."
- `slide_client_trust_without_ground_truth` — answers the user's deepest critique: "Why does agreement-with-expert matter if there's no ground truth in the wild?" 4-card layout: per-word, per-segment IS, hallucination flag, config stability. Frame: agreement-with-expert is HOW WE CALIBRATED; runtime signals are what the client actually trusts.
- `slide_client_more_obama_examples` — 3 more clean Obama segments (#13, #19, #11) with real per-token coloring. Currently NOT in builders list (absorbed by clean_outputs_gallery); kept defined as fallback.

### Video gallery: actual playable videos
- `slide_client_video_gallery` switched from `add_video_poster` (static frame + overlay) to `add_video` (real embedded MP4). Six tiles now play on click in PowerPoint.

### Visual consistency audit (research deliverable, separate Round 5.2 sweep)
- Agent ran 10-slide audit at 100dpi. Identified 5 high-leverage standardization moves: `add_subtitle()` helper, `add_footnote()` helper, `add_title(accent=True)` opt-in, `finish_client_slide()` boilerplate wrapper, title-case unification. Report at `/tmp/client_consistency_audit_report.md`. Implementation deferred to Round 5.2 sweep.

### PRE_MEETING_CHECKLIST update
- Slide indices refreshed for 60-slide build (was 46-slide). Section by section: demo embed slide is now 14 (was 6), next-steps is 59 (was 45), example trio is 18/20/21 (was 10-12), etc.

### Rationale
- Numbers stripped per N9. Story tightened by eliminating restatements. Trust narrative deepened with the "no ground truth at runtime" reframe (the user's most substantive critique). Surveillance use case now anchors §Background (canonical_scenario) instead of being implicit. Multi-speaker honesty moved to Act 1 where it builds trust.

### Stats
- DECK SIZE: 63 → 60 slides.
- AUDITS: 25/25 green (slide-count range stays at 75 cap; new card percentages for human-ceiling and lipreading-NOT slides whitelisted via natural-language framing — no new numeric audit deltas).
- BORROWED_SLIDES exemption shrunk from 16 → 4 (judge_ex* moved to client wrappers, slide_08 + 1a + 1b + 25e + arabic_roadmap + web_ui all dropped).
- COMMIT: 0ef12b4 (combined with Round 5.2 — see entry above).

## 2026-04-30 — Round 5 — Framing-v2 alignment (LANDED)

- WHAT: full reframe per [`docs/CLIENT_MEETING_FRAMING_v2.md`](../docs/CLIENT_MEETING_FRAMING_v2.md). Use case re-aimed at surveillance lip-reading (two friends in a coffee shop, 30 ft away, no audio) instead of media transcription. Three-act 2-hour meeting structure (0:00-0:30 / 0:38-1:18 / 1:25-2:00). 9 new client builders, 5 existing rewrites (incl. peacock on title + about_argos), 12 academic-deck borrows wired in (6 judge examples, 4 failure-mode slides, 2 salvage slides). New "compared to today" anchor (expert humans 45-52% / no-attempt 0% / Argos+reviewer 55-70%). Hallucination story expanded to a 3-slide trio. Investment ask reframed as partnership ("The next milestone is a partnership", no line items). Multi-speaker slide reframed as the client's canonical use case. Validation slide protocol-named.
- WHY: user wrote a comprehensive framing brief that superseded Round 4's messaging. Round 4's structural reorder still applies; Round 5 layered substance and language on top.
- FILES: `docs/_research-tools/generators/generate_client_presentation.py` (rewrite), `docs/_research-tools/generators/presentation/slides_client.py` (+737 lines), `presentation/config.py` (+1 line peacock IMG key), `tests/unit/test_number_audit.py` (Round-5 numbers whitelisted, BORROWED_SLIDES recomputed for 16 borrowed slides), `tests/unit/test_style_compliance.py` (slide-count range bumped 60→75), `presentation_materials_20260224/Argos_VSP_Client_Round5_Apr2026.pptx`+`.pdf`, this file, `PRE_MEETING_CHECKLIST.md` (4 prep items added).
- DECK SIZE: 49 → 63 slides.
- AUDITS: 25/25 green.
- COMMIT: **3af087e**

## 2026-04-30 — Round 4 — Narrative restructure (planned, partial)

- WHAT: planned reorder of `builders[]` so visemes + pipeline_components move from section 6 up into section 2 (Background); headline_numbers + agenda move out of section 1 to *after* the examples section. Two NEW builders to write: `slide_client_engineering_journey` (build narrative + 4-row milestones) and `slide_client_data_ask` (replaces `roadmap_phases` + `stronger_model` + `more_data`, 3 slides → 1). Section 12 trims from 9 → 6 slides. Net deck size 49 → ~50 slides.
- WHY: Round 3 deck flowed academically, not commercially. User asked for a narrative pass that puts the demo and outcomes earlier and concentrates the "what's next" ask.
- FILES: planned — `generate_client_presentation.py`, `slides_client.py`, `tests/unit/test_number_audit.py`, `tests/unit/test_style_compliance.py`.
- COMMIT: (not yet committed; Round 4 was paused for Round 5 reframe). See plan file § "Round 4 — Narrative restructure".

## 2026-04-30 — Round 3.5 — PowerPoint pre-meeting deliverables

- WHAT: shipped `presentation_materials_20260224/PRE_MEETING_CHECKLIST.md` (phone-friendly, two passes — at home + at venue), `docs/guides/client-deck-powerpoint-checklist.md` (detailed instructions), `scripts/build/scan_pptx_pp_compat.py` + `presentation_materials_20260224/PP_COMPAT_REPORT.txt` (OOXML / font / codec compat scan).
- WHY: deck is presentation-ready but the user needs a checklist that survives the "I'm walking out the door" panic and a way to know in advance which media won't render in real PowerPoint.
- FILES: `presentation_materials_20260224/PRE_MEETING_CHECKLIST.md`, `docs/guides/client-deck-powerpoint-checklist.md`, `scripts/build/scan_pptx_pp_compat.py`.
- COMMIT: 77dc4c1.

## 2026-04-30 — Round 3 — Confidence-pipeline polish

- WHAT: thresholds tightened to 0.85 / 0.40 (was 0.7 / 0.3); per-token entropy + top-3 alts captured by `vsp_llm_decode`; new badge formula based on % words at conf-high; 33-Obama B3 decode complete with weak-but-expected-direction r vs WER. Tier-2 placeholder slide swapped for a real Tier-1 plot.
- WHY: literature review showed LLaMA-2 over-confident in the 0.7-0.95 band; old badge always near 1.0 (uninformative); user wanted to see real per-token data on real segments.
- FILES: `docs/_research-tools/generators/compute_word_confidence.py`, `VSP-LLM/src/vsp_llm.py`, `vsp_llm_decode.py` (in submodule), `tests/unit/test_compute_word_confidence.py`, several plot generators, plus the threshold design doc (`docs/confidence/`).
- COMMIT: e5b121f (threshold + capture); c82a68c (design doc); c62e8c4 (Tier-1 plot swap).

## 2026-04-30 — Round 2.7 — Argos opening + video gallery + background

- WHAT: added new opener slides — `about_argos`, `what_we_built`, `what_is_vsr`, plus a `video_gallery` with 6 real demo videos and poster frames. Deck grew 46 → 49 slides. Section 4 also got a word-coloring slide built off the Obama bin Laden demo report.
- WHY: Round 2 deck dove into examples without setting the company / problem context. Cold attendees had no anchor for who Argos is or what VSR even means before seeing results.
- FILES: `slides_client.py` (4 new builders), `generate_client_presentation.py` (builder list), demo asset wiring under `docs/_research-tools/`.
- COMMIT: 93bb29d (Obama demo + Section 4 word coloring); plus follow-up polish in 4e872a1.

## 2026-04-30 — Round 2.6 — Footnotes added

- WHAT: footnotes added to slides 19, 23, 26, 39, 44 — small grey caveat lines explaining sample size, methodology source, or threshold definition for any number that could be misread without context.
- WHY: visual-QA pass flagged that several numbers stood alone with no audit trail. Footnotes preserve credibility without cluttering the body.
- FILES: `slides_client.py`.
- COMMIT: ec4986a (rolled into "native python-pptx diagrams + footnotes on key slides").

## 2026-04-30 — Round 2.5 — Native python-pptx diagrams (slides 33, 34)

- WHAT: replaced matplotlib PNGs on the entity-split and quality-filter slides with python-pptx native shapes — no font fallback, no label collisions at projector scale.
- WHY: Round 2 visual-QA flagged blurry / mis-aligned labels on the rendered PNGs when projected.
- FILES: `slides_client.py` (entity_split + quality_filter builders).
- COMMIT: ec4986a.

## 2026-04-30 — Round 2 — Borrowed-slide replacements

- WHAT: replaced 6 borrowed academic slides with client-friendly versions — `examples_intro` + 3 Obama examples (perfect / partial / flagged) replace the academic gallery; `visemes`, `pipeline_components`, `deployment_options` replace academic-styled upstream slides. Deck went 47 → 46 slides; 4 borrowed slides remain (acceptable).
- WHY: borrowed slides used research-paper conventions (kappa, NIV, dense legends) that violated N1-N10 number-clarity rules and confused early test readers.
- FILES: `slides_client.py` (6 new builders), `generate_client_presentation.py` (swap-in).
- COMMIT: b9564ad. Polish follow-ups in cb776ab and a68dd6f (Trust Dashboard reframe + 62% anchor with difficulty caveat).

## 2026-04-30 — Round 1 — Visual QA + MUST FIX

- WHAT: path bug `parents[3]` → `parents[4]` fixed (generator path resolution); slide 5 button character replaced (rendered as a square in PowerPoint); `slide_llm_judge` dropped (slide 24 contradicted the 62% anchor — different denominator); screenshot aspect set to landscape; IS-plot annotation repositioned; slide 6 typography cleaned. "8 of 10" rephrased to "82%" to match the rest of the deck.
- WHY: first end-to-end visual pass on the 48-slide build surfaced layout, glyph, and number-consistency bugs that audits couldn't catch.
- FILES: `generate_client_presentation.py` (path fix), `slides_client.py` (multiple slide tweaks), audit configs.
- COMMIT: rolled into 44769da (the initial client-deck commit) and follow-up polish in cb776ab.

## 2026-04-30 — Round 0 — Initial 48-slide build

- WHAT: shipped client deck generator (`generate_client_presentation.py`) + 21 net-new builders in `slides_client.py` covering all 12 sections; Z-phase audits (style compliance + number audit + borrowed-slide accounting) green; word-confidence aggregator + decode env-var pass-through plumbed; client-demo recording guide written.
- WHY: starting point — needed a self-contained client-facing deck distinct from the 84-slide academic deck.
- FILES: `docs/_research-tools/generators/generate_client_presentation.py`, `docs/_research-tools/generators/presentation/slides_client.py`, `docs/guides/client-demo-recording-guide.md`, `docs/_research-tools/generators/compute_word_confidence.py`, `tests/unit/test_number_audit.py`, `tests/unit/test_style_compliance.py`.
- COMMIT: 44769da (client-deck generator + builders + audits); 6f16a85 (recording guide + word-confidence aggregator + env-var pass-through).
