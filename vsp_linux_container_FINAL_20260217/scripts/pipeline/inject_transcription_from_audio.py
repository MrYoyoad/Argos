#!/usr/bin/env python3
"""Audio-aligned transcription injection.

When a client has an audio recording of the same content captured by their
silent VSP video (or an audio that overlaps in time with it), this CLI
clips that audio per segment, runs Whisper, and writes per-segment ``.wrd``
references into ``<input-dir>/.transcriptions/``. Those `.wrd` files are
matched 1:1 with segment videos by name and are auto-picked up by
``lib/asr.sh`` Step 0.6 on the next pipeline run.

Time alignment is given by two flags:
  --audio-start  T_a  (seconds in the supplied audio)
  --video-start  T_v  (seconds in the parent video)

These declare that audio time ``T_a`` corresponds to video time ``T_v``.
For a segment with window ``[v0, v1]`` (seconds in the parent video) the
clipped audio window is::

    delta_seg          = v0 - T_v
    clip_start_audio   = T_a + delta_seg
    clip_end_audio     = T_a + (v1 - T_v)

Defaults ``--audio-start 0 --video-start 0`` model the "audio is perfectly
aligned with video" case.

Usage:
    python3 inject_transcription_from_audio.py \\
        --video obama_speech.mp4 \\
        --audio my_recording.wav \\
        --audio-start 5 --video-start 0 \\
        [--input-dir /path/to/vsp_input] \\
        [--whisper-model medium] [--lang en] \\
        [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


PIPELINE_FPS = 25.0
VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi")


def parse_segment_id(segment_id: str) -> Tuple[str, int, int, int]:
    """Return (base_video_id, seg_idx, start_frame, end_frame). For
    non-segmented IDs, returns (segment_id, -1, -1, -1).

    Same format as VSP-LLM/scripts/make_burn.py:parse_segment_id."""
    parts = segment_id.split("_")
    if len(parts) < 4:
        return segment_id, -1, -1, -1
    try:
        end_frame = int(parts[-1])
        start_frame = int(parts[-2])
        seg_idx = int(parts[-3])
        base_video_id = "_".join(parts[:-3])
        return base_video_id, seg_idx, start_frame, end_frame
    except (ValueError, IndexError):
        return segment_id, -1, -1, -1


def _seg_time_window(stem: str) -> Tuple[float, float]:
    _, _, start_frame, end_frame = parse_segment_id(stem)
    if start_frame < 0 or end_frame < 0:
        return 0.0, 0.0
    return start_frame / PIPELINE_FPS, end_frame / PIPELINE_FPS


def discover_segments(parent_stem: str, search_dirs: Iterable[Path]) -> List[Path]:
    """Find every segment .mp4 whose name starts with the parent stem."""
    found: List[Path] = []
    seen: set = set()
    pattern = re.compile(
        rf"^{re.escape(parent_stem)}_\d{{2}}_\d{{6}}_\d{{6}}\.(?:mp4|mkv|mov|m4v|webm|avi)$",
        re.IGNORECASE,
    )
    for d in search_dirs:
        if not d.exists():
            continue
        for p in d.iterdir():
            if not p.is_file():
                continue
            if pattern.match(p.name) and p.name not in seen:
                seen.add(p.name)
                found.append(p)
    found.sort(key=lambda p: p.stem)
    return found


def ffprobe_duration(path: Path) -> float:
    """Return media duration in seconds (0.0 on failure)."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             str(path)],
            capture_output=True, text=True, check=False, timeout=30,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def normalize_words(text: str) -> List[str]:
    """Same normalization as TranscriptionManager.normalize_text: lowercase,
    keep alphanum + apostrophes, drop everything else."""
    out: List[str] = []
    for w in (text or "").lower().split():
        cleaned = "".join(c for c in w if c.isalnum() or c == "'")
        if cleaned:
            out.append(cleaned)
    return out


def clip_audio(audio_src: Path, start_sec: float, end_sec: float,
               dest: Path) -> bool:
    """ffmpeg-clip a wav window. Returns True on success."""
    duration = max(0.0, end_sec - start_sec)
    if duration <= 0:
        return False
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{start_sec:.3f}",
        "-t", f"{duration:.3f}",
        "-i", str(audio_src),
        "-ac", "1", "-ar", "16000",
        str(dest),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
        return dest.exists() and dest.stat().st_size > 0
    except subprocess.CalledProcessError as e:
        print(f"[ffmpeg] clip failed [{start_sec:.2f}-{end_sec:.2f}]: {e.stderr}",
              file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print(f"[ffmpeg] clip timed out [{start_sec:.2f}-{end_sec:.2f}]",
              file=sys.stderr)
        return False


def load_whisper(model_size: str):
    """Lazy import — Whisper is heavy and we want --dry-run to work without it."""
    import torch  # local import: keeps --dry-run cheap and CI-safe
    import whisper
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_size, device=device)
    return model, device


def transcribe_clip(model, device: str, clip_path: Path, lang: str) -> str:
    result = model.transcribe(
        str(clip_path), language=lang, fp16=(device == "cuda"),
    )
    return result.get("text", "")


def update_metadata(meta_file: Path, filename: str, *,
                    word_count: int, source_audio: str, audio_offset: float):
    """Append/update one entry in metadata.json. Re-reads from disk to avoid
    clobbering concurrent asr.sh updates (same pattern as TranscriptionManager)."""
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            meta = {"transcriptions": {}}
    else:
        meta = {"transcriptions": {}}
    meta.setdefault("transcriptions", {})
    now = datetime.utcnow().isoformat() + "Z"
    existing = meta["transcriptions"].get(filename, {})
    meta["transcriptions"][filename] = {
        "type": "audio-injected",
        "created_at": existing.get("created_at", now),
        "edited_at": now if existing else None,
        "word_count": word_count,
        "video_checksum": existing.get("video_checksum"),
        "source_audio": source_audio,
        "audio_offset": round(float(audio_offset), 3),
    }
    meta_file.parent.mkdir(parents=True, exist_ok=True)
    meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def default_segment_search_dirs(input_dir: Path) -> List[Path]:
    """Locations to scan for already-cut segment videos. Order is the same
    as lib/asr.sh / server.py:handle_get_segment_video."""
    home = Path(os.environ.get("HOME", "/home/ubuntu"))
    seg_dur = os.environ.get("SEGMENT_DURATION", "12")
    auto_avsr = home / "auto_avsr"
    return [
        auto_avsr / f"preprocessed_flat_seg{seg_dur}" / "fast_segments",
        auto_avsr / f"preprocessed_flat_seg{seg_dur}" / "flat" / f"flat_video_seg{seg_dur}s",
        input_dir,
    ]


def build_plan(parent_video: Path, audio: Path, audio_start: float,
               video_start: float, search_dirs: List[Path]) -> List[dict]:
    """Build the list of (segment, clip_start, clip_end) entries. Skips
    segments whose clip window falls entirely outside the audio duration."""
    audio_dur = ffprobe_duration(audio)
    segments = discover_segments(parent_video.stem, search_dirs)
    plan: List[dict] = []
    for seg in segments:
        v0, v1 = _seg_time_window(seg.stem)
        if v1 <= v0:
            plan.append({"segment": seg, "skip": "could-not-parse-frames",
                         "v0": v0, "v1": v1})
            continue
        delta0 = v0 - video_start
        delta1 = v1 - video_start
        clip0 = audio_start + delta0
        clip1 = audio_start + delta1
        if clip1 <= 0 or (audio_dur > 0 and clip0 >= audio_dur):
            plan.append({"segment": seg, "skip": "outside-audio",
                         "v0": v0, "v1": v1, "clip0": clip0, "clip1": clip1,
                         "audio_dur": audio_dur})
            continue
        # Trim ends to audio bounds so ffmpeg gets a valid window.
        clip0 = max(0.0, clip0)
        if audio_dur > 0:
            clip1 = min(audio_dur, clip1)
        plan.append({"segment": seg, "skip": None,
                     "v0": v0, "v1": v1, "clip0": clip0, "clip1": clip1,
                     "audio_dur": audio_dur})
    return plan


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--video", required=True, type=Path,
                        help="parent video filename (in --input-dir) whose "
                             "segments should be re-transcribed from audio")
    parser.add_argument("--audio", required=True, type=Path,
                        help="audio source file (wav/mp3/m4a/...)")
    parser.add_argument("--audio-start", type=float, default=0.0,
                        help="seconds in the audio that align with --video-start")
    parser.add_argument("--video-start", type=float, default=0.0,
                        help="seconds in the parent video that align with --audio-start")
    parser.add_argument("--input-dir", type=Path,
                        default=Path(os.environ.get("INPUT_DIR",
                                                    str(Path.home() / "vsp_input"))),
                        help="vsp_input directory (.transcriptions lives here)")
    parser.add_argument("--whisper-model", default="medium",
                        help="Whisper model size (default: medium, matches lib/asr.sh)")
    parser.add_argument("--lang", default="en", help="language code passed to Whisper")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the per-segment plan without ffmpeg/Whisper/writing")
    args = parser.parse_args(argv)

    parent = args.video
    if not parent.is_absolute():
        parent = args.input_dir / parent.name
    if not parent.exists():
        print(f"[error] parent video not found: {parent}", file=sys.stderr)
        return 2
    if not args.audio.exists():
        print(f"[error] audio file not found: {args.audio}", file=sys.stderr)
        return 2

    search_dirs = default_segment_search_dirs(args.input_dir)
    plan = build_plan(parent, args.audio, args.audio_start, args.video_start,
                      search_dirs)

    if not plan:
        print(f"[warn] no segments matching parent stem '{parent.stem}' under "
              f"{search_dirs}", file=sys.stderr)
        return 0

    print(f"Parent video: {parent.name}")
    print(f"Audio file:   {args.audio.name}")
    print(f"Alignment:    audio[{args.audio_start:.3f}s] ↔ video[{args.video_start:.3f}s]")
    print(f"Segments:     {len(plan)} found")
    if args.dry_run:
        print("--- DRY RUN ---")
        for entry in plan:
            seg = entry["segment"]
            if entry["skip"]:
                print(f"  SKIP {seg.name} ({entry['skip']})  v=[{entry['v0']:.2f}, {entry['v1']:.2f}]")
            else:
                print(f"  PLAN {seg.name}  v=[{entry['v0']:.2f}, {entry['v1']:.2f}]  "
                      f"a=[{entry['clip0']:.2f}, {entry['clip1']:.2f}]")
        return 0

    tx_dir = args.input_dir / ".transcriptions"
    tx_dir.mkdir(parents=True, exist_ok=True)
    meta_file = tx_dir / "metadata.json"

    print(f"Loading Whisper model: {args.whisper_model}")
    model, device = load_whisper(args.whisper_model)
    print(f"  device: {device}")

    n_written = 0
    n_skipped = 0
    n_failed = 0

    with tempfile.TemporaryDirectory(prefix="vsp-inject-") as tmp:
        tmp_dir = Path(tmp)
        for entry in plan:
            seg = entry["segment"]
            if entry["skip"]:
                print(f"  SKIP {seg.name} ({entry['skip']})")
                n_skipped += 1
                continue
            clip_path = tmp_dir / f"{seg.stem}.wav"
            if not clip_audio(args.audio, entry["clip0"], entry["clip1"], clip_path):
                print(f"  FAIL clip {seg.name}")
                n_failed += 1
                continue
            try:
                text = transcribe_clip(model, device, clip_path, args.lang)
            except Exception as e:
                print(f"  FAIL whisper {seg.name}: {e}")
                n_failed += 1
                continue
            words = normalize_words(text)
            wrd_path = tx_dir / f"{seg.stem}.wrd"
            wrd_path.write_text("\n".join(words) + ("\n" if words else ""),
                                encoding="utf-8")
            update_metadata(
                meta_file,
                filename=f"{seg.stem}{seg.suffix}",
                word_count=len(words),
                source_audio=args.audio.name,
                audio_offset=entry["clip0"],
            )
            n_written += 1
            preview = " ".join(words[:8])
            print(f"  OK   {seg.name}  -> {len(words)} words"
                  f"{(' / ' + preview + '...') if words else ''}")

    print("---")
    print(f"Written: {n_written}    Skipped: {n_skipped}    Failed: {n_failed}")
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
