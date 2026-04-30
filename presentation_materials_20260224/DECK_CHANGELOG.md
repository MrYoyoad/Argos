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

## 2026-04-30 — Round 5 — Framing-v2 alignment (in flight)

- WHAT: not yet committed. Round 5 operationalises [`docs/CLIENT_MEETING_FRAMING_v2.md`](../docs/CLIENT_MEETING_FRAMING_v2.md): re-aim the deck at surveillance lip-reading (two friends in a coffee shop, observer 30 ft away, no audio) instead of media transcription; add a "compared to today" slide (expert human 45-52% / don't-do-it 0% / Argos + reviewer 55-70%); rewrite section openers per the framing doc.
- WHY: user wrote a comprehensive framing brief that supersedes Round 4's messaging. Round 4's structural reorder still applies; Round 5 layers substance and language on top.
- FILES: planned — `docs/_research-tools/generators/presentation/slides_client.py`, `docs/_research-tools/generators/generate_client_presentation.py`, this changelog.
- COMMIT: (pending) — see [`/.claude/plans/i-need-to-create-proud-cupcake.md`](../.claude/plans/i-need-to-create-proud-cupcake.md) § "Round 5".

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
