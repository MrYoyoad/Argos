#!/usr/bin/env python3
"""Split RealTalk two-shot conversation videos into per-speaker face crops.

For each source video {id}.mp4 in /data/conversation_datasets/realtalk/data/english/videos/
this produces two derivative MP4s, {id}__p0.mp4 and {id}__p1.mp4, each cropped to a
single speaker. The crop is a constant window computed as the padded median bbox of
that speaker over the whole video (the studio framing is stable, so a constant crop
is robust and deterministic).

Why split: the VSP-LLM pipeline's MediaPipe stage picks the largest face per frame.
On a two-shot, that silently locks onto whichever face is bigger. Pre-splitting gives
each speaker a clean single-face stream the pipeline can process unambiguously.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from statistics import median

REALTALK_ROOT = Path("/data/conversation_datasets/realtalk/data/english")
OUT_ROOT = Path("/home/ubuntu/vsp_input_realtalk_demo/_per_speaker")

PAD_FRAC = 0.20
TARGET_FPS = 25
MIN_FACE_PX = 128  # below this width the mouth-crop quality degrades sharply


def load_labels(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def median_bbox(labels: dict, speaker: str) -> tuple[float, float, float, float] | None:
    xs1, ys1, xs2, ys2 = [], [], [], []
    for frame_data in labels.values():
        person = frame_data.get("people", {}).get(speaker)
        if not person:
            continue
        bbox = person.get("bbox")
        if not bbox or len(bbox) != 4:
            continue
        x1, y1, x2, y2 = bbox
        xs1.append(x1); ys1.append(y1); xs2.append(x2); ys2.append(y2)
    if not xs1:
        return None
    return median(xs1), median(ys1), median(xs2), median(ys2)


def active_fraction(labels: dict, speaker: str) -> float:
    total = sum(1 for v in labels.values() if v.get("current_speaker") is not None)
    if total == 0:
        return 0.0
    active = sum(1 for v in labels.values() if v.get("current_speaker") == speaker)
    return active / total


def probe_dims(video: Path) -> tuple[int, int]:
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=,:p=0",
        str(video),
    ], text=True).strip()
    w, h = out.split(",")
    return int(w), int(h)


def expand_and_clamp(bbox: tuple[float, float, float, float],
                     frame_w: int, frame_h: int,
                     pad_frac: float = PAD_FRAC) -> tuple[int, int, int, int]:
    """Expand bbox by pad_frac in each direction and clamp to frame. Returns (x, y, w, h)
    suitable for ffmpeg crop. All values rounded to even integers."""
    x1, y1, x2, y2 = bbox
    bw, bh = x2 - x1, y2 - y1
    pad_w, pad_h = bw * pad_frac, bh * pad_frac
    nx1 = max(0.0, x1 - pad_w)
    ny1 = max(0.0, y1 - pad_h)
    nx2 = min(float(frame_w), x2 + pad_w)
    ny2 = min(float(frame_h), y2 + pad_h)
    x = int(nx1) // 2 * 2
    y = int(ny1) // 2 * 2
    w = (int(nx2) - x) // 2 * 2
    h = (int(ny2) - y) // 2 * 2
    return x, y, w, h


def run_ffmpeg_crop(src: Path, dst: Path, x: int, y: int, w: int, h: int,
                    fps: int = TARGET_FPS) -> None:
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(src),
        "-vf", f"crop={w}:{h}:{x}:{y},fps={fps}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-ac", "1", "-ar", "16000",
        "-movflags", "+faststart",
        str(dst),
    ]
    subprocess.run(cmd, check=True)


def split_video(video_id: str, out_root: Path, dry_run: bool = False) -> dict:
    src = REALTALK_ROOT / "videos" / f"{video_id}.mp4"
    labels_path = REALTALK_ROOT / "speaker_labels" / f"{video_id}.json"
    if not src.exists():
        raise FileNotFoundError(src)
    if not labels_path.exists():
        raise FileNotFoundError(labels_path)

    labels = load_labels(labels_path)
    frame_w, frame_h = probe_dims(src)
    out_root.mkdir(parents=True, exist_ok=True)

    result = {"video_id": video_id, "frame_w": frame_w, "frame_h": frame_h, "speakers": {}}

    for speaker in ("p0", "p1"):
        bbox = median_bbox(labels, speaker)
        if bbox is None:
            print(f"[{video_id}] skip {speaker}: no detections", file=sys.stderr)
            continue
        x, y, w, h = expand_and_clamp(bbox, frame_w, frame_h)
        face_w = bbox[2] - bbox[0]
        if face_w < MIN_FACE_PX:
            print(f"[{video_id}] WARN {speaker} face width {face_w:.0f}px < {MIN_FACE_PX}px"
                  f" — proceeding but mouth crop quality may suffer", file=sys.stderr)

        dst = out_root / f"{video_id}__{speaker}.mp4"
        meta = {
            "source_id": video_id,
            "speaker": speaker,
            "median_bbox": list(bbox),
            "crop_xywh": [x, y, w, h],
            "median_face_width_px": face_w,
            "active_fraction": active_fraction(labels, speaker),
            "source_frame_size": [frame_w, frame_h],
        }
        result["speakers"][speaker] = meta

        if dry_run:
            print(f"[{video_id}] {speaker}: would crop {x},{y},{w}x{h} → {dst.name}")
            continue

        run_ffmpeg_crop(src, dst, x, y, w, h)
        meta_path = out_root / f"{video_id}__{speaker}.meta.json"
        with meta_path.open("w") as f:
            json.dump(meta, f, indent=2)
        print(f"[{video_id}] {speaker} → {dst} ({w}x{h}, face≈{face_w:.0f}px,"
              f" active {meta['active_fraction']:.0%})")

    return result


def discover_videos(only: list[str] | None) -> list[str]:
    vids_dir = REALTALK_ROOT / "videos"
    all_ids = sorted(p.stem for p in vids_dir.glob("*.mp4"))
    if only:
        missing = [i for i in only if i not in all_ids]
        if missing:
            raise SystemExit(f"unknown video ids: {missing}")
        return only
    return all_ids


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="+", help="restrict to these video ids")
    ap.add_argument("--dry-run", action="store_true", help="probe + report, don't encode")
    ap.add_argument("--out", type=Path, default=OUT_ROOT, help="output dir for per-speaker mp4s")
    args = ap.parse_args()

    out_root: Path = args.out

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("ffmpeg/ffprobe not found on PATH")

    ids = discover_videos(args.only)
    print(f"processing {len(ids)} videos → {out_root}")

    summary = {"out": str(out_root), "videos": []}
    for vid in ids:
        try:
            summary["videos"].append(split_video(vid, out_root, dry_run=args.dry_run))
        except Exception as e:
            print(f"[{vid}] FAIL: {e}", file=sys.stderr)
            summary["videos"].append({"video_id": vid, "error": str(e)})

    if not args.dry_run:
        out_root.mkdir(parents=True, exist_ok=True)
        summary_path = out_root / "split_summary.json"
        with summary_path.open("w") as f:
            json.dump(summary, f, indent=2)
        print(f"summary → {summary_path}")


if __name__ == "__main__":
    main()
