# General method: matching a known transcript to video (no audio, multi-speaker)

Distilled from the Egla-Kafe work and validated on 11 conversations. The problem: you have a
video of people reading an approximately-known script, and you need per-segment **reference text**
aligned to the video so you can score a lip-reading model — but the footage may have **no audio**
(so no Whisper forced-alignment) and **multiple speakers**.

## Pipeline

1. **Per-speaker crops.** If the source has multiple faces, isolate each speaker into a single-face
   crop. Reuse provided crops if available, else `make_speaker_crops.py` (detect faces → cluster by
   horizontal position → keep the side speakers, drop a constant center listener → stable square crop).

2. **Active-speaker turn detection (visual, audio-free).** `build_active_speaker_stream.py`:
   per crop, per frame, MediaPipe FaceMesh mouth-openness *variance* (speech oscillates the lips;
   a smile is a sustained stretch) → hysteretic turn assignment (min-dwell) → turn timeline +
   a stacked active-speaker stream. QC metric: fraction of frames where the shown speaker's mouth
   motion exceeds the hidden one's (target ≥0.8).

3. **Segment at turn boundaries** (NOT fixed time windows): each clip = one speaker's turn ⇒ each
   clip maps to one script line. (Feeding the whole stream continuously is worse — mid-clip
   speaker-cuts disrupt the model; see findings.)

4. **Lip-read** each clip with the model → hypotheses.

5. **Monotonic alignment to the transcript** (`align_script_to_segments.py`): global
   Needleman–Wunsch of the segment sequence to the script-turn sequence, scored by hypothesis↔turn
   token similarity + a structural bonus (speaker alternation / side→character). Order-preserving by
   construction; tolerates missed/extra turns via gaps; falls back to the structural diagonal when a
   hypothesis is garbage and flags it with low `align_conf`. **If the script is unknown among a few
   candidates, align to each and keep the highest-confidence** (auto-detect).

6. **Emit references**: write each segment's aligned script span as a `.wrd` reference; produce a
   review HTML (hyp | proposed ref | confidence, low-conf rows flagged) for a human gate.

7. **Score**: per-segment WER/WWER/IS, and — because per-segment is brutally harsh — a
   **conversation-level** score (concatenate hyps vs full script) and a **context-aware LLM judge**
   (whole sequence + viewer-context blurb → what a context-aware viewer actually understands).

8. **Per-person attribution** (optional): `egla_kafe_face_id.py` — ArcFace face clustering across
   videos + constraint-propagation naming from the known speaker pairs (no manual labels).

## When the general signal source is AUDIO
If the footage has usable audio, replace steps 2–4 with Whisper (gives word timestamps) and do the
same monotonic alignment of the ASR token stream to the known transcript. The matcher (step 5) is
identical; only the token-stream source changes (ASR vs lip-read).

## Where it degrades, and the levers
- **No audio + high WER + many tiny turns** → alignment leans on the structural prior; gate
  low-confidence turns for manual review (lever: turn-merging threshold, min-dwell).
- **Always-co-occurring speakers** break naive pair-intersection naming → solve globally by
  elimination (constraint propagation).
- **Profile/extreme angles** destroy the lip signal (45° ≈ unusable) → can't be recovered by
  alignment; flag by camera angle.
- **Short one-word turns** carry little lip signal and little context → expect N verdicts; not a
  matcher failure.

## Reusable entry points
`scripts/pipeline/`: `make_speaker_crops.py`, `build_active_speaker_stream.py`,
`egla_kafe_cut_segments.py`, `align_script_to_segments.py`, `egla_kafe_align_and_score.py`,
`egla_kafe_conversation_score.py`, `egla_kafe_context_judge.py`, `egla_kafe_face_id.py`,
`parse_dialogue_script.py`. Stats: `docs/_research-tools/generators/analyze_egla_kafe.py`.
