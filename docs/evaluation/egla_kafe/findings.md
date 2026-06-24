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

## Full scene1+2 results (448 turns, 11 conversations) — per-segment
Overall WER **122%**, IS **1.55**, NIV-Y+P **24.8%** (per-segment metric is brutal on this footage).
Speaker attribution is rigorous via face-ID (`face_id.json`, constraint-propagation naming, 19/21
videos verified) — NOT filename guesses.

**Per-speaker (lip-readability):** Tomer WER 104% / IS 1.97 / Y+P 37.6% (best) > Yoad 112% / 1.50 /
24.7% > Tal 160% / 1.19 / 12.2% > Ido 145% / 1.11 / 7.7%. Individual face/articulation dominates.

**Per-angle (clean finding):** front WER 118% / IS 1.62 / Y+P 27.4% ≫ 30° 133% / 1.24 / 16.7% ≫
45° 158% / 1.03 / **3.2%**. Lip-reading collapses as the face turns to profile (model is frontal-trained).

Per-scene: scene1 119.8% / 1.50, scene2 125.2% / 1.62 (similar).

## iPhone vs client-camera (planned, prerequisites running)
The שפם scene exists in both: **iPhone 4K masters** (`שפם 4K` crops, ~1200px from 3840×2160) and
**client-camera** screen-recordings (`שפם` crops, 380px). A controlled test of video-quality effect
on lip-reading. שפם script (1 vs 2) is auto-detected by aligning each video to both scripts and
taking the higher-confidence match. Streams built; decode + comparison pending the scene1+2 run.

## Open items
- שפם / master per-file script (1 vs 2) — resolved via auto-detect (align-to-both); to be confirmed.
- Full scene1+2 scores + grouped stats (per scene/char/side/angle/speaker) once decode completes.
- Phase B: dynamic per-frame cropping + audio-visual ASD (masters have audio).
