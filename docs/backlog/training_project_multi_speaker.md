# End-of-Training-Phase Project — Multi-Speaker Lip-Reading

**5-day project**  ·  **Author:** Yoad Oxman

---

## Goal

Extend our lip-reading system so that a video with two speakers produces a clean, attributed transcript per speaker. Off-the-shelf tools only — no model training. Today the system silently mashes both speakers into one transcript, often attributed to the wrong person.

## Why it matters

- Most real-world video has more than one person — interviews, podcasts, meetings, news clips. The single-speaker assumption silently breaks all of these.
- Pilot customers have multi-speaker footage. Today we have to ask them to manually crop each speaker first — friction.
- A working multi-speaker demo is far more compelling than the single-speaker case.

## The work

Four steps, each one short:

- **Detect and track each face.** Off-the-shelf face detector (YOLO is the standard choice) per frame, off-the-shelf tracker to link the per-frame detections into persistent identities.
- **Get who-speaks-when from audio.** Off-the-shelf speaker-diarization tool (`pyannote` is the open-source standard) outputs labeled segments — *"speaker A from 0–3.5 s, speaker B from 3.5–5.2 s."*
- **Attribute audio segments to face tracks (the interesting research piece).** For each diarization segment, pick the face track with the most mouth movement during that interval. The researcher chooses the mouth-movement metric and the tie-breaker rule.
- **Run our pipeline per speaker and recombine.** Crop video + audio per identity, decode each, recombine into a timeline-ordered, per-speaker labeled transcript.

The researcher builds a small test set of 3–5 hand-labeled YouTube interview clips for evaluation.

## What the researcher learns

- How to use a third-party detection + tracking model in production — face detection per frame, persistent identities across frames, brief-occlusion handling, the full pipeline from library import to clean output.
- Speaker diarization in practice — what it does, where it works, where it fails.
- Aligning two independent segmentation systems (visual face tracks vs. audio speaker turns) — the same kind of fusion problem that comes up everywhere in production ML.
- Extending a multi-stage pipeline — running existing stages in parallel per identity and merging the outputs into a single timeline.

---

## Schedule (5 days, balanced)

| Day | Task |
|---|---|
| 1 | Read the repo. Get the face detector + tracker working on one test clip. Verify tracks are stable across the clip. |
| 2 | Install the diarization library and run it on the same clip's audio. Pick the test clips from YouTube and hand-label the first one. |
| 3 | Build the audio-to-face attribution logic. Test on the hand-labeled clip. Finish hand-labeling the remaining test clips. |
| 4 | Wire up per-speaker pipeline runs and the timeline-ordered recombination. End-to-end test on the hand-labeled clips. |
| 5 | Polish, edge-case handling (face out of frame, partial occlusion). Short write-up in `docs/features/`. |
