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
