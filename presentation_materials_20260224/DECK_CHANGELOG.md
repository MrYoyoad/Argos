# Argos VSP Client Deck — Changelog

**File:** `Argos_VSP_Client_*.pptx` (currently `Argos_VSP_Client_49slides_Apr2026.pptx`)
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
