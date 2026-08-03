# Filming a Two-Person Conversation for Lip Reading

**Who this is for:** anyone filming a scripted two-person conversation for us — no technical background needed.
**What you need:** one or two phones, two stands (or stacks of books), a printed script, and about 20 minutes.
**Scripts:** [conversation_scripts/script_orchard.md](conversation_scripts/script_orchard.md) and [conversation_scripts/script_everyday.md](conversation_scripts/script_everyday.md).

---

## 1. Why this protocol exists

The system reads **lips only** — it never listens to the sound, so everything depends on how clearly the mouth is visible on camera. Every rule below comes from a measured experiment on real footage, not from guesswork.

---

## 2. Setup A — two phones, one per speaker (best quality)

Each speaker gets their own phone, filming only them.

1. Put each phone on a tripod or stand at **eye level**, about **1 to 1.5 meters** from its speaker.
2. Each phone frames its **own** speaker only. The face should fill **at least one third of the frame height** — closer is better than wider.
3. Speakers sit or stand **angled toward their own camera**, not toward each other. You are talking to each other, but your face points at your own phone.
4. Start **both phones recording**, then do **one single loud hand clap** where **both cameras can see it**. This clap is how we line the two videos up later — do not skip it.
5. Only then begin the script.

Phone settings: 1080p at 25 or 30 fps is enough (see rule 1 below). Lock focus/exposure on the face if your camera app allows it.

## 3. Setup B — one camera, both speakers visible

One phone films both speakers at once.

1. Sit **side by side**, both facing the camera — **not** turned toward each other.
2. Sit close together, so both faces stay **big** in the frame (each face still around one third of the frame height if possible).
3. Camera at eye level, straight on, 1 to 1.5 meters away.
4. The system automatically detects **who is talking**, as long as only one person talks at a time.

Setup A gives better quality; use Setup B when only one phone is available.

## 4. Shared rules (these are measured, not preferences)

1. **Face size beats camera quality.** The system shrinks every mouth to the same small size internally, so 4K gives nothing over 1080p. What matters is that the mouth is large **in the frame**: face at least **1/3 of the frame height** (mouth roughly 100 pixels tall). 1080p at 25/30 fps is enough.
2. **Look straight at the camera.** Head-on faces decode far better than a 30° angle, and at 45° the system almost completely fails. Camera at eye level, face pointed at or near the lens while talking.
3. **One speaker at a time — always.** Footage that cuts between speakers mid-sentence failed badly in testing. Never talk over each other, and leave a clear **1 to 1.5 second silent pause** between turns — the system uses mouth movement to find where each turn starts and ends.
4. **Speak in long, full sentences at a natural pace.** Full sentences decode better than short fragments. Do not slow down or over-articulate, and do not rush — talk like you normally would.
5. **No names, no numbers.** The system gets names and places wrong essentially every time, and numbers come out systematically wrong. The scripts are written without them — do not improvise any in.
6. **Keep the mouth clear.** No chewing, smiling, or laughing while talking. No hands, mugs, or microphones in front of the mouth. If a heavy beard or mustache can be avoided (shave or pick another speaker), avoid it — mustached speakers scored worst in our tests.
7. **Light the face, not the background.** Never sit with a window or bright light behind you — the face turns into a dark shape. Face a window or lamp instead.
8. **Send the original files only.** Videos must come straight off the camera — via cable or AirDrop. **Never send through WhatsApp** or similar chat apps: they recompress the video and destroy the lip detail. No screen recordings, no edited or re-exported versions.

## 5. Recording session flow

1. **Start recording** on all cameras.
2. **Clap once**, loudly, in view of every camera (Setup A: both; Setup B: just the one).
3. **Slate:** one speaker says the date and scene name out loud ("third of August, orchard script, take one"). The sound is thrown away later, so this is only for our bookkeeping — the clap is what actually matters.
4. **Read the script.** Keep the pauses between turns. If someone stumbles, pause, then restart that turn from its beginning — do not stop the recording.
5. **Do two full takes** of the script, back to back. Clap again between takes.
6. **Stop recording and transfer the original files** by cable or AirDrop. Name them with the date and setup if you can (for example `aug03_setupA_speakerA.mp4`).

## 6. Cue card — print this box

```
────────────────────────────────────────────────
          LIP-READING FILMING — CUE CARD

 1. FACE THE CAMERA — straight on, at eye level.
 2. FILL THE FRAME — face at least 1/3 of the picture.
 3. ONE SPEAKER AT A TIME — never talk over each other.
 4. PAUSE 1-1.5 SECONDS between turns, in silence.
 5. FULL SENTENCES, NORMAL PACE — no slow-motion, no rushing.
 6. MOUTH STAYS CLEAR — no hands, mugs, chewing, or laughing.
 7. LIGHT ON YOUR FACE — never a window behind you.
 8. SEND ORIGINALS ONLY — cable or AirDrop, never WhatsApp.

 Before the script: ONE LOUD CLAP in view of all cameras.
────────────────────────────────────────────────
```

## 7. Dry-run validation loop (our team — technical)

The scripts are **vocabulary-checked**, not just eyeballed: every spoken line was passed through
`docs/_research-tools/scripts/check_script_vocab.py` against `docs/_research-tools/datasets/lrs3_safe_vocab.csv`
(LRS3 training-vocabulary frequency + measured per-word decode accuracy from the B3 diagnostic and the 1,497-segment benchmark). Both scripts exit with **zero flags** (no out-of-vocab words, no entities, no numbers, no historically low-accuracy words).

That makes the scripts *likely* to decode — the dry run turns the claim into a measurement:

1. **Film a quick test take** in-house (Setup B is fine; one phone, two people, the cue card rules).
2. **Run it through the pipeline** (`run_flat_english_pipeline.sh`) and pull the per-segment report.
3. **Align per-word decode output against the script**, turn by turn. Any word wrong in *both* takes is a candidate for replacement, regardless of what the vocab CSV said.
4. **Swap failing words** for safe-list synonyms, re-run `check_script_vocab.py` (must exit 0 again), and issue the script as v2.
5. Repeat once if needed. Ship v2 (or v3) to the client with the protocol doc and cue card.

Keep the test-take decode report next to the script version it validated, under `docs/tuning/experiments/` per the file-placement rules.
