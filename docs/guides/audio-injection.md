# Audio-aligned transcription injection

When a client has an audio recording of the same spoken content as a
silent VSP video — for example, a separate microphone capturing a
speech that the camera also recorded with no audio — the pipeline can
clip that audio per segment, run Whisper, and inject the result as the
manual reference for every segment of the parent video. The resulting
`.wrd` files are matched 1:1 with segment videos by name and are
auto-picked up by `lib/asr.sh` Step 0.6 on the next pipeline run.

## Why

Manually typing references for a 5-minute video can be 30+ segments
of laborious word-by-word transcription. If a clean audio of the
content exists, this CLI / UI form turns that into a single
multipart upload.

## Time alignment: two offsets

The hard part is telling the tool which slice of the audio corresponds
to which segment of the video. The convention is:

> `--audio-start T_a` and `--video-start T_v` declare that audio time
> `T_a` corresponds to video time `T_v`.

For a segment spanning `[v0, v1]` seconds in the parent video, the
clipped audio window is computed as

```
delta_seg          = v0 - T_v
clip_start_audio   = T_a + delta_seg
clip_end_audio     = T_a + (v1 - T_v)
```

### Worked example

Your phone started recording 5 seconds **before** the camera. The
video shows the first word at video time 0; you can hear the same
first word in the audio at audio time 5.

- `--audio-start 5 --video-start 0`
- Segment `[12, 24]` (the second segment of the parent) clips audio
  `[17, 29]`.

If instead the camera started 3 seconds before the audio:

- `--audio-start 0 --video-start 3` → segment `[12, 24]` clips audio
  `[9, 21]`.

If they are perfectly aligned, leave both defaults at `0`.

## EC2 / CLI walkthrough

Direct CLI invocation from EC2 (server-side or remote shell):

```bash
python3 /home/ubuntu/scripts/pipeline/inject_transcription_from_audio.py \
    --video obama_speech.mp4 \
    --audio /tmp/my_recording.wav \
    --audio-start 5 \
    --video-start 0 \
    --input-dir ~/vsp_input \
    --whisper-model medium
```

Add `--dry-run` first to see the per-segment plan:

```
Parent video: obama_speech.mp4
Audio file:   my_recording.wav
Alignment:    audio[5.000s] ↔ video[0.000s]
Segments:     8 found
--- DRY RUN ---
  PLAN obama_speech_00_000000_000299.mp4  v=[0.00, 11.96]  a=[5.00, 16.96]
  PLAN obama_speech_01_000150_000449.mp4  v=[6.00, 17.96]  a=[11.00, 22.96]
  ...
```

The CLI writes `.wrd` files into `<input-dir>/.transcriptions/` and
updates `<input-dir>/.transcriptions/metadata.json` entries with
`"type": "audio-injected"`, `"source_audio"`, and `"audio_offset"`.
The next pipeline run skips Whisper for any segment with a matching
`.wrd` (Step 0.6).

## Client / UI walkthrough

1. After running the segment-only preview ("Continue Pipeline" off,
   "Segment Only" on), the Segment Review screen shows each parent
   video with its segments.
2. Click **Inject from audio…** in the button row.
3. In the modal:
   - **Video** dropdown: pick the parent video whose segments you want
     to transcribe.
   - **Audio file**: upload the recording (WAV, MP3, M4A, FLAC, etc.).
   - **Audio start / Video start**: enter the two alignment offsets
     (see the section above). Leave at `0` for perfectly aligned
     audio.
   - **Whisper model**: defaults to `medium`. Pick `tiny` / `base` /
     `small` for faster turnaround on short recordings; `large` for
     best accuracy on long speeches.
4. Click **Run injection**. The modal blocks until Whisper finishes —
   typically tens of seconds for a one-minute audio, a few minutes for
   a multi-segment speech. The bottom of the modal shows a final
   summary line (`Written: N · Skipped: M · Failed: K`) and the full
   tail of the CLI log for diagnostics.
5. The Segment Review list refreshes; segments with a freshly
   injected `.wrd` will display an AUTO badge (the metadata says
   `audio-injected` but the UI's badge logic groups all non-manual
   entries as AUTO).
6. Click **Continue Pipeline** to proceed; the full pipeline will
   reuse the injected references instead of re-running Whisper on
   the silent video.

## Troubleshooting

- **"Whisper missing" / ModuleNotFoundError on the server**: the UI
  server must be launched from a venv that has `whisper` and `torch`
  installed. On EC2 that is the same venv that `lib/asr.sh` uses
  (`asr_venv`); on the container it is the bundled image.
- **All segments skipped with `outside-audio`**: the math says the
  computed clip window is past the end of your audio. Re-check the
  two offsets and the parent video's duration.
- **All segments fail with `clip failed`**: ffmpeg can't read the
  audio. Try re-encoding the source to WAV (`ffmpeg -i src.mp3
  -ar 16000 -ac 1 out.wav`) and re-upload.
- **Wrong language**: the CLI passes `--lang en` by default. For
  non-English audio, pass `--lang de` (etc.) directly to the CLI;
  the UI form currently hard-codes English.
- **Segment-name mismatch**: the CLI matches `<parent_stem>_NN_NNNNNN_NNNNNN.mp4`.
  If the parent video filename has changed since segmentation, the
  scan will return 0 segments — re-run the segment-only pass first.
- **Updating an existing transcription**: re-running the CLI on the
  same segments overwrites the `.wrd` files and bumps `edited_at`.
  Manual edits in the UI also overwrite — the last writer wins.
