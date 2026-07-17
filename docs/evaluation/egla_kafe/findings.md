# Egla-Kafe (עגלת קפה) — active-speaker lip-reading evaluation

Status: **complete** (June 25, 2026). Scene1+2 full decode, iPhone-vs-camera comparison,
context-aware LLM judge, significance tests, and word-category trust analysis all done;
deliverables (deck, per-video PDF, 21 said-vs-heard videos, clips, plots) built the same day.

## What was built
Active-speaker → decode → align → score → judge pipeline for the client conversations
(`scripts/pipeline/*egla_kafe*`, `build_active_speaker_stream.py`, `align_script_to_segments.py`,
`make_speaker_crops.py`, `analyze_egla_kafe.py`, `egla_kafe_context_judge.py`; 17 unit tests).

- **Active-speaker stream** (no audio on footage → visual): per-crop FaceMesh mouth-openness
  *variance* (speech oscillates; a smile is a sustained stretch) → hysteretic turn detection →
  single stacked stream + per-turn segments. All 11 scene1+2 streams: **alternation 1.0**,
  voiced-consistency mean 0.79; שפם streams 0.78–0.89.
- **Text↔video alignment** (the hard part): segments cut at **turn boundaries** (NOT 12 s windows,
  so each clip = one script line). No audio → no forced alignment; instead a monotonic
  Needleman–Wunsch alignment of the segment sequence to the known alternating script, scored by
  hypothesis↔line similarity + a side→character bonus. Falls back to the structural diagonal when
  content is garbage; flags low-confidence turns.

## Validation — `s1_tomer_yoad_1` (Emma & Jake, 48 turns)
- Alignment **side-consistency = 1.00**, 45/48 turns matched; references correct by inspection
  (e.g. "technically i forgot where i put my passport" exact; "the conflict and the 20th" → 20th;
  "i'm the reason you are getting on the right plane" near-exact).
- **Per-segment model performance is weak on this footage**: WER **91.8%**, IS **2.18**,
  captured (IS≥3) **24%** — worse than the LRS3-style English baseline (WER 64.1 / IS 2.53).
  Non-native English + real-world outdoor screen-recording is harder. The model catches content
  keywords (passport, 19th/20th, "present on the last day", airline) but mangles function words.
- **Per-speaker split (real finding)**: left (Tomer→Emma) WER **71.8%** / IS **2.50** vs
  right (Yoad→Jake) WER **109%** / IS **1.90**.

## Context-aware sequence-level LLM judge (the "what can be understood" eval)
Judge = Claude Opus 4.8 in-session (no API key on box; matches repo's prepare→judge→collect flow).
Given the whole ordered hypothesis sequence + a viewer-context blurb ("Emma & Jake, airport,
flight"), it assesses per-turn understandability (Y/P/N) using cross-turn redundancy + context.

**s1_tomer_yoad_1 result:** the full plot is recoverable — *Jake booked the wrong return date
(19th vs conference ending 20th); Emma catches it; he must fix it with the airline.*
Context-aware **Y+P ≈ 46%** of turns convey useful meaning vs the per-segment captured **24%** —
whole-sequence + context roughly **doubles** intelligibility. Failures are one-word reactions
(no lip signal, no context to recover). See `work/eval/judge/judgments/s1_tomer_yoad_1.json`.

**All 11 conversations (context-judge, Claude Opus 4.8 in-session, holistic):** mean context-aware
**Y+P 36.9%** / Y 15.2% — roughly double the per-segment captured rate (~12–24%). Two patterns:
- **Scene 2 (Military) 44.4% ≫ Scene 1 (Emma/Jake) 30.7%** — the military script's distinctive
  content words ("biggest problem", "communications", "options", "three hours", "small mistakes
  become big problems", "military life is action movies") survive lip-reading and are recoverable
  with context; the airport dialogue is more generic/recoverable-poor.
- Best: `s2_tomer_ido_1` 62.5% (frontal Military); worst: `s1_yoad_tal_z45` 11.5% (45° profile).
Verdicts in `work/eval/judge/judgments/`, summary `work/eval/judge/context_judge_summary.json`.

## Full scene1+2 results (448 turns, 11 conversations) — per-segment
Overall WER **122%**, IS **1.55**, NIV-Y+P **24.8%** (per-segment metric is brutal on this footage).
Speaker attribution is rigorous via face-ID (`face_id.json`, constraint-propagation naming, 19/21
videos verified) — NOT filename guesses.

**Per-speaker (lip-readability):** Tomer WER 104% / IS 1.97 / Y+P 37.6% (best) > Yoad 112% / 1.50 /
24.7% > Tal 160% / 1.19 / 12.2% > Ido 145% / 1.11 / 7.7%. Individual face/articulation dominates.

**Per-angle (clean finding):** front WER 118% / IS 1.62 / Y+P 27.4% ≫ 30° 133% / 1.24 / 16.7% ≫
45° 158% / 1.03 / **3.2%**. Lip-reading collapses as the face turns to profile (model is frontal-trained).

Per-scene: scene1 119.8% / 1.50, scene2 125.2% / 1.62 (similar).

## Recovery ceiling under filtering (scene1+2 per-turn) — the key result
Filtering by static conditions helps only modestly; filtering by where the model *locks on* is
transformative — revealing a high ceiling hidden under the pessimistic average.

| Filter | n | WER | IS | useful IS≥2 | clear IS≥3 |
|---|---|---|---|---|---|
| ALL | 411 | 122% | 1.55 | 25% | 12% |
| front only | 350 | 118% | 1.62 | 27% | 13% |
| front + Tomer/Yoad | 266 | 107% | 1.74 | 32% | 17% |
| front + Tomer | 125 | 104% | 1.97 | 38% | 22% |
| front + Tomer + Military | 58 | 101% | 2.18 | 41% | 29% |
| **locked on (align_conf≥0.4)** | 93 | **63%** | **3.04** | **75%** | **50%** |
| **front + best spk + locked on** | 74 | **61%** | **3.16** | **81%** | **55%** |

**Takeaway:** when the model is confident it performs at the **LRS3 English benchmark (WER ~61% vs
64%)** with 75–81% useful / ~50% clear. The model isn't incapable on this footage — it only *locks
on* ~20% of the time (coverage problem, not capability). Product implication: **confidence-gate**
(deliver the segments the model is sure about; flag the rest) rather than chase the average.
**Deployable gate confirmed** — gating by the model's OWN `sentence_confidence` (no reference needed)
reproduces the ceiling and quantifies the recovery/coverage tradeoff:

| gate (model conf) | keeps | WER | IS | useful IS≥2 | clear IS≥3 |
|---|---|---|---|---|---|
| ALL | 100% | 122% | 1.55 | 25% | 12% |
| ≥0.5 | 47% | 107% | 1.99 | 39% | 22% |
| ≥0.6 | 25% | 90% | 2.34 | 55% | 32% |
| ≥0.7 | 10% | 65% | 2.86 | 70% | 45% |
| ≥0.8 | 3% | 41% | 3.54 | 92% | 67% |

The model *knows when it's right*. Operating points: conf≥0.7 → English-benchmark quality (WER 65%,
70% useful) keeping top 10%; conf≥0.6 → 55% useful keeping a quarter. **Bottom line: the 122% average
is a coverage problem, not capability — frontal high-res capture + confidence-gating turns this into
a reliable stream on the subset that matters** (the project's Trust/Salvage/Strip philosophy,
confirmed on client data).

## Is the poor WER an alignment problem? (disentangled)
Tested directly. Verdict: **a scoring-granularity artifact inflates the number, but the model is the
bottleneck — NOT script↔video misalignment.**

| WER measure | value | isolates |
|---|---|---|
| per-turn (short 1-word refs) | 135% | granularity blow-up |
| per-segment (production alignment) | 120% | what was reported |
| **conversation-level (alignment-FREE concat)** | **86%** | **truest model floor** |
| position-free oracle (cherry-pick best line/seg) | 81% | absolute floor |

- The 120→86 gap (~34pp) is a **per-short-segment scoring artifact**, not model error → headline the
  alignment-free **86%** (and IS / context-judge), not 120%.
- It is **not** a script↔video alignment error: conversation-level WER (no mapping at all) is still 86%;
  hyp/ref **word ratio = 0.96** (not verbose → genuine substitutions); and where the model is confident
  WER is 65% (alignment correct there). Failures concentrate on low-confidence, hallucinated, un-alignable
  output — no alignment can fix output that corresponds to no line.
- Over-segmentation is real (51 detected turns vs 48 script) but the many-to-one turn-oracle does not beat
  86%; alignment is second-order. Conclusion unchanged: input-quality + confidence-gating are the levers.

## What can you understand after gating? — per word-category trust (all 778 segs)
For green (high-confidence) words, P(correct) by category, and coverage (recall) of reference words:

| category | P(correct\|green) | n | recovered (green) |
|---|---|---|---|
| NOUN (common) | **82%** | 65 | 11% |
| NUMBER/date | 73% | 22 | 7% |
| VERB | 65% | 37 | 5% |
| ADJ/ADV | 53% | 45 | 5% |
| FUNCTION | 54% | 127 | 5% |
| **ENTITY (names/places)** | **0%** | 2/8 | **0%** |

**Interpretation — what a gated output actually gives you:**
1. A **topical skeleton, not sentences**: green common-nouns are reliable (~82%) but only ~10% of nouns
   said are recovered → a scatter of trustworthy content words a reader fuses with context (≈ the 37%
   context-judge recovery), not full intelligible text.
2. **Names/places are a black hole AND dangerous**: 0% recovered, and the model emits confident
   hallucinated entities — "Abu **dhabi**" (0.997), "**states**" (0.991), "Wikipedia". Never trust a
   proper noun from this model.
3. **Numbers ~73% green but unsafe**: confident-wrong leaks + the project's billion→million / 1024→24
   class mean a confident number still needs verification.
4. **Verbs/modifiers/grammar ~53–65% even when green** → you get *what it's about*, not exactly
   *what happened*.

Bottom line: trust the **common-noun topic skeleton** (+ rough numbers), reconstruct the **gist with
context**, but do **not** trust any name/place/precise claim, and expect only ~10% word coverage.
Tool: `scripts/pipeline/egla_kafe_word_category_trust.py`; data: `work/eval/word_category_trust_ALL.json`.

## Stacked-stream vs per-turn input (conversation-level, scene1+2)
Tested whether feeding the whole conversation as ONE continuous active-speaker stream (≈12s windows
that cut across speakers) beats decoding clean per-speaker turn clips. **It is worse:**

| Input regime | WER | IS | NEA-F1 |
|---|---|---|---|
| per-turn (one speaker/clip) | **86.2%** | **1.79** | **31%** |
| stacked stream (12s windows, mid-clip cuts) | 90.6% | 1.09 | 9% |

Mid-clip speaker/position cuts disrupt the lip-reader (not trained on identity jumps); entity recovery
collapses. **Conclusion: clean per-speaker turn segmentation is the better input for this model**, even
though the "one continuous stream" framing is intuitive. (Also note: conversation-level WER 86% ≪
per-segment 122% — the per-segment metric is far harsher than the whole-conversation view.)

## iPhone 4K vs client-camera (same שפם scene) — DONE
Controlled test of capture quality. Script auto-detected per video (yoad_amosi→scene1,
amosi_ido & masters→scene2). The iPhone footage is **dramatically more lip-readable**:

| Source | n | WER | IS | NEA-F1 | useful IS≥2 | clear IS≥3 | align_conf |
|---|---|---|---|---|---|---|---|
| **iPhone 4K** (~1200px native) | 153 | 155% | **1.51** | 20% | **29%** | **13.7%** | 0.33–0.38 |
| **client camera** (380px screen-rec) | 133 | 165% | **0.88** | 10% | 11% | **0.8%** | 0.07–0.14 |

IS +72%, entities 2×, useful ~3×, **clearly-conveyed 17×** (14% vs 0.8%). The client camera here is
a 380px screen-recording of a composite (with UI chrome) — near-unusable; the iPhone is sharp,
frontal, native 4K. (Not a pure-resolution test — different capture setups — but the direction is
unambiguous and large.) Confirms the angle finding: **the model is dominated by input quality
(resolution / frontality / articulation)** far more than anything tunable downstream.
**July 17 update**: the pure-resolution test now exists — [resolution_ablation.md](resolution_ablation.md)
downscaled the same 175 iPhone segments 4K→2K→1080p and found **no measurable change** (all paired
tests n.s.; clean 1080p with 30–56px mouths scores IS 1.59 vs the screen-recs' 0.88). The camera
gap is a capture-chain problem (screen-record generations, mouth px in frame), not the resolution
number.

### File forensics — the "client camera" files are screen recordings, not camera output (Jul 13 2026)
ffprobe on the raw client files vs the iPhone masters settles what the pipeline actually received:

| Property | iPhone master (IMG_6825) | client files (שפם / סצנה 1-2) |
|---|---|---|
| Resolution | 3840×2160 (standard 4K) | **1258×696, 1268×674, 1102×650, 1104×664** — every file a different non-standard size |
| Codec / bitrate | HEVC, 24.9 Mbps (single encode) | h264, **3.0–3.7 Mbps** (camera encode → screen display → screen-rec re-encode) |
| Frame content | clean camera image | **viewer-app UI visible in pixels**: zoom slider, yellow targeting-circle overlay, watermark icon |

Non-standard, per-file-varying resolutions are the signature of window captures (someone resized the
viewer window between recordings); no camera records at 1258×696. In the wide shot inside that window,
faces are ~60–90 px tall → mouths ~20–30 px, below what the mouth-crop pipeline needs; the lip signal
is destroyed before decode. Notably the viewer has a zoom control, so **the camera's native stream may
carry more resolution than was ever exported** — the model has never seen this camera's true output.
Implication for the client ask, in order of cost: (1) export original files from the camera system
(may make a re-shoot unnecessary), (2) re-shoot pilot recording natively. Frontality remains an
independent lever either way (front-vs-45° was measured on iPhone-quality footage).

## Statistical significance & calibration (Mann-Whitney U on is_score, bootstrap 95% CIs)
Tool: `docs/_research-tools/generators/egla_kafe_significance.py` → `work/eval/significance.json`.
Deck plots: `docs/_research-tools/generators/egla_kafe_deck_plots.py` → `deliverables/plots/`.
Scored segments only (empty-reference turns excluded): scene1+2 n=410, שפם-run n=286.

| Contrast | groups (mean IS [95% CI]) | diff | p (MW-U) | verdict |
|---|---|---|---|---|
| iPhone-4K vs client-camera | 1.51 [1.31,1.71] vs 0.88 [0.77,0.99] | +0.63 | **2.3e-05** | **significant** |
| Military (s2) vs Emma/Jake (s1) | 1.62 [1.45,1.79] vs 1.50 [1.36,1.64] | +0.12 | 0.38 | **n.s.** (IS sees no scene gap; context-judge gap is real) |
| angle front vs 45° | 1.62 [1.50,1.75] vs 1.03 [0.76,1.39] | +0.59 | **2.0e-03** | **significant** |
| angle front vs 30° | 1.62 vs 1.24 [0.94,1.61] | +0.38 | 0.055 | borderline (small n=30) |
| Tomer vs Yoad / Tal / Ido | 1.97 vs 1.50 / 1.19 / 1.11 | +0.47/+0.78/+0.86 | 1.8e-04 / 8e-07 / 6e-04 | **Tomer sig. beats all three** |

- **Capture quality and frontality are the only statistically robust levers.** iPhone-vs-camera and
  front-vs-45° are real; the Military-vs-Emma/Jake IS gap is **not** significant at the per-segment level
  (the +14pp context-judge advantage comes from distinctive *content words* surviving + cross-turn
  redundancy, not from higher per-segment IS — state it that way, don't overclaim a scene effect on IS).
- **Confidence gate (own word-prob, scene1+2):** ALL→IS 1.55/25% useful; ≥0.6→2.34/55% (keeps 25%);
  ≥0.7→2.86/70%, WER 65% (keeps 10%); ≥0.8→3.54/92% (keeps 3%). Reproduces the canonical operating points.
- **Calibration (3,617 aligned words, both runs):** confidence is well-**ranked** (empirical P(exact-word
  correct) rises monotonically 7%→45% across prob buckets) so the gate works for *selection*, but raw
  probabilities run **optimistic at the exact-word level** (0.95-bucket words are correct only ~45% of the
  time). Headline the gate's relative selection power, not the absolute probability number.

## July 2026 follow-up package — the "guessing game" bundle (Jul 16 2026)

`deliverables/EglaKafe_guessing_game_20260716.zip` — 7 videos × the triple (`__clean.mp4` /
`__model_read.mp4` / `__transcript.html`) + client README. Selection (deliberate mix, not a
highlight reel): top-3 iPhone 4K (img_6825, img_6824, img_6822) + the two worn-mustache scenes
(img_6821, img_6823) + the two best client-camera scenes (s2_tomer_ido_1, s1_tomer_yoad_1).
Audio stripped everywhere (`-an`); neutral side labels ("Left/Right speaker"); the hyp-only
renderer never opens alignment/scripts, so reference leakage is impossible by construction
(QA: ffprobe 0 audio streams on all 14 mp4s; zero hits for labels/names/script lines/external
refs across all .ass + .html).

- **MBR anchoring**: display text = `hyp_mbr` via the new `word_confidence_mbr.json` sidecars —
  aligns the package with the May-2026 production default. Texts differ in places from the
  July-13 said-vs-heard bundle (top-1-anchored); intended, per user decision.
- **Phonetic substitution shipped (GO)**: the dual-engine agreement arm passed the binding gate
  (fixed ≥ 3× broke, ΔWER ≤ 0, 0 entity/number introductions, rate ≤ 5%) — verdict + full arms
  in [phonetic_substitution_eval.md](phonetic_substitution_eval.md). Exactly **2 corrections
  ship**, both on s1_tomer_yoad_1: `figured`→`forgot°`, `on`→`of°` — marked subtly (orange +
  degree sign, never green) with a one-line legend in that video's transcript only.
- Related analyses: [overlap_consistency_analysis.md](../../beam-search/overlap_consistency_analysis.md)
  (did overlapping split decodes help; L4 narrow-GO); [resolution_ablation.md](resolution_ablation.md)
  (**done Jul 17** — 4K→2K→1080p paired sweep on the 175 iPhone segments: resolution changes nothing
  measurable; mouth-px framing and original-file exports are the levers).

## Open items
- שפם / master per-file script (1 vs 2) — resolved via auto-detect (align-to-both); to be confirmed.
- Full scene1+2 scores + grouped stats (per scene/char/side/angle/speaker) once decode completes.
- Phase B: dynamic per-frame cropping + audio-visual ASD (masters have audio).
- ~~Resolution ablation report~~ — **done Jul 17 2026**: [resolution_ablation.md](resolution_ablation.md).
