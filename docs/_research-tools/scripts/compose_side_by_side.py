#!/usr/bin/env python3
"""Compose two per-speaker burned face clips into a side-by-side conversation panel.

Step 4 of the demo-deck pipeline produced two burned face clips per source video
(one per speaker, ~12s window, MBR-aggregated lip-read text overlaid as colored
subtitles). This script hstacks the two halves with the ORIGINAL two-shot's audio
re-attached, so the slide shows both faces simultaneously while the viewer hears
the actual back-and-forth conversation.

The two burned clips may have different crop sizes (e.g. 354x330 vs 376x344), so
we normalize each to a target height and pad to even widths before hstacking
(libx264 requires even dimensions). Audio comes ONLY from the source two-shot,
trimmed to the same [start, end] window with fast pre-input seek.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def probe_audio(path: Path) -> dict | None:
    """Return {sample_rate, channels, codec} for the first audio stream, or None."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate,channels,codec_name",
        "-of", "json",
        str(path),
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode()
    except subprocess.CalledProcessError:
        return None
    streams = json.loads(out).get("streams") or []
    if not streams:
        return None
    s = streams[0]
    return {
        "sample_rate": int(s.get("sample_rate", 0)) if s.get("sample_rate") else 0,
        "channels": int(s.get("channels", 0)) if s.get("channels") else 0,
        "codec": s.get("codec_name", ""),
    }


def probe_duration(path: Path) -> float | None:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode()
    except subprocess.CalledProcessError:
        return None
    dur = json.loads(out).get("format", {}).get("duration")
    try:
        return float(dur) if dur is not None else None
    except (TypeError, ValueError):
        return None


def build_ffmpeg_cmd(
    p0: Path,
    p1: Path,
    source: Path,
    start: float,
    end: float,
    out: Path,
    target_h: int,
) -> list[str]:
    filter_complex = (
        f"[0:v]scale=-2:{target_h},pad=ceil(iw/2)*2:ih:0:0[L];"
        f"[1:v]scale=-2:{target_h},pad=ceil(iw/2)*2:ih:0:0[R];"
        f"[L][R]hstack=inputs=2[v]"
    )
    return [
        "ffmpeg", "-y",
        # Burned clips are already trimmed to the window — no -ss needed.
        "-i", str(p0),
        "-i", str(p1),
        # Fast seek on the long source MP4 so we only decode the window.
        "-ss", f"{start}", "-to", f"{end}",
        "-i", str(source),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "2:a",
        "-c:v", "libx264", "-crf", "20", "-preset", "medium",
        "-c:a", "aac", "-ar", "44100", "-ac", "2",
        "-shortest",
        "-movflags", "+faststart",
        str(out),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--p0-burned", required=True, type=Path,
                    help="Burned face clip for speaker 0")
    ap.add_argument("--p1-burned", required=True, type=Path,
                    help="Burned face clip for speaker 1")
    ap.add_argument("--source-mp4", required=True, type=Path,
                    help="Original two-shot MP4 (audio source)")
    ap.add_argument("--start-sec", required=True, type=float,
                    help="Window start in source video (seconds)")
    ap.add_argument("--end-sec", required=True, type=float,
                    help="Window end in source video (seconds)")
    ap.add_argument("--out", required=True, type=Path,
                    help="Output composite MP4 path")
    ap.add_argument("--target-height", type=int, default=720,
                    help="Target height for each half before hstack (default: 720)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print ffmpeg command without executing")
    args = ap.parse_args()

    # Validate inputs.
    missing = []
    for label, p in (("--p0-burned", args.p0_burned),
                     ("--p1-burned", args.p1_burned),
                     ("--source-mp4", args.source_mp4)):
        if not p.exists():
            missing.append(f"{label}: {p}")
    if missing:
        print("ERROR: required input(s) not found:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 2

    if args.end_sec <= args.start_sec:
        print(f"ERROR: --end-sec ({args.end_sec}) must be > --start-sec ({args.start_sec})",
              file=sys.stderr)
        return 2

    if args.target_height <= 0 or args.target_height % 2 != 0:
        print(f"ERROR: --target-height must be a positive even integer (got {args.target_height})",
              file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)

    # Sanity checks (warnings only) — skip on dry-run since paths may be synthetic.
    if not args.dry_run:
        d0 = probe_duration(args.p0_burned)
        d1 = probe_duration(args.p1_burned)
        if d0 is not None and d1 is not None and abs(d0 - d1) > 0.1:
            print(f"WARNING: burned clip durations differ ({d0:.3f}s vs {d1:.3f}s); "
                  f"output will be limited by -shortest", file=sys.stderr)

        a = probe_audio(args.source_mp4)
        if a is None:
            print(f"WARNING: no audio stream detected in {args.source_mp4}",
                  file=sys.stderr)
        else:
            if a["sample_rate"] and a["sample_rate"] != 44100:
                print(f"WARNING: source sample rate is {a['sample_rate']} Hz "
                      f"(expected 44100)", file=sys.stderr)
            if a["channels"] and a["channels"] != 2:
                print(f"WARNING: source has {a['channels']} channel(s) "
                      f"(expected 2/stereo)", file=sys.stderr)

    cmd = build_ffmpeg_cmd(
        args.p0_burned, args.p1_burned, args.source_mp4,
        args.start_sec, args.end_sec, args.out, args.target_height,
    )

    if args.dry_run:
        # Quote args containing spaces for readability.
        printable = " ".join(f'"{a}"' if " " in a else a for a in cmd)
        print(printable)
        return 0

    print(f"[compose] {args.p0_burned.name} + {args.p1_burned.name} -> {args.out}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: ffmpeg failed with exit code {e.returncode}", file=sys.stderr)
        return e.returncode

    if not args.out.exists() or args.out.stat().st_size == 0:
        print(f"ERROR: expected output not produced: {args.out}", file=sys.stderr)
        return 1

    print(f"[compose] OK: {args.out} ({args.out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
