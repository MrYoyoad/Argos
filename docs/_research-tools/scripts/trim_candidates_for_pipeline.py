#!/usr/bin/env python3
"""Trim each row in realtalk_candidates.csv to a 12 s clip aligned with the
pipeline's segment phase, so the pipeline only has to decode the candidate
windows (one segment per input file) instead of every 12 s slice across each
full per-speaker stream.

Output naming: `{per_speaker_id}__win{start_sec:04d}.mp4` (zero-padded so sort
order matches start time). One MP4 per candidate row; same per_speaker stream
may produce multiple clips if it has multiple candidates.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

PER_SPEAKER_DIR = Path("/home/ubuntu/vsp_input_realtalk_demo/_per_speaker")
DEFAULT_CSV = Path("/home/ubuntu/presentation_materials_20260224/06_demo_videos/realtalk_candidates.csv")
DEFAULT_OUT = Path("/home/ubuntu/vsp_input_realtalk_demo/candidate_clips")
WINDOW_SEC = 12.0


def trim(src: Path, start: float, dur: float, dst: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{start:.3f}",
        "-i", str(src),
        "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-ac", "1", "-ar", "16000",
        "-movflags", "+faststart",
        str(dst),
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--per-speaker-dir", type=Path, default=PER_SPEAKER_DIR)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(args.csv.open()))
    print(f"trimming {len(rows)} candidates → {args.out}")

    written = 0
    for r in rows:
        per_id = r["per_speaker_id"]
        start = float(r["start_sec"])
        src = args.per_speaker_dir / f"{per_id}.mp4"
        if not src.exists():
            print(f"  SKIP {per_id} (no per-speaker mp4 at {src})", file=sys.stderr)
            continue
        dst = args.out / f"{per_id}__win{int(start):04d}.mp4"
        if dst.exists():
            print(f"  exists: {dst.name}")
            continue
        try:
            trim(src, start, WINDOW_SEC, dst)
            written += 1
            print(f"  ✓ {dst.name}")
        except subprocess.CalledProcessError as e:
            print(f"  FAIL {dst.name}: {e}", file=sys.stderr)

    print(f"\nwrote {written} clips to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
