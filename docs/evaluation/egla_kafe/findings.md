# Egla-Kafe (עגלת קפה) — active-speaker lip-reading evaluation

Status: **in progress** (scene1+2 full decode running; iPhone-vs-camera + full LLM-judge pending decode).
Pipeline + tooling validated end-to-end; numbers below are from the first validated conversation.

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

## Open items
- שפם / master per-file script (1 vs 2) — resolved via auto-detect (align-to-both); to be confirmed.
- Full scene1+2 scores + grouped stats (per scene/char/side/angle/speaker) once decode completes.
- Phase B: dynamic per-frame cropping + audio-visual ASD (masters have audio).
