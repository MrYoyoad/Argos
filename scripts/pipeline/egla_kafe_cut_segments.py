#!/usr/bin/env python3
"""Cut per-turn single-speaker clips for decoding.

For each stream's segments.json, cut [t0,t1] from the appropriate side's crop (lossless source,
better than re-cutting the re-encoded stream) into a flat decode-input dir, named <seg_id>.mp4
(ASCII, matches the pipeline's seg-id regex). Also writes seg_meta.json mapping
seg_id -> {stem, scene, side, t0, t1} for later provenance + hypothesis merge.

Run the VSP pipeline on the output dir with SEGMENTATION_ENABLED=0 so each clip = one segment.
"""
import argparse
import json
import os
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/index.json")
    ap.add_argument("--streams-dir", default="/home/ubuntu/datasets/clients/egla_kafe/work/streams")
    ap.add_argument("--out-dir", required=True, help="flat decode-input dir for the clips")
    ap.add_argument("--stems", default=None, help="comma list; default = all built streams")
    ap.add_argument("--min-dur", type=float, default=0.6, help="skip clips shorter than this (s)")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    idx = {e["stem"]: e for e in json.load(open(args.index))["entries"]}
    stems = args.stems.split(",") if args.stems else None

    seg_meta = {}
    n_clips = 0
    n_skipped = 0
    for stem in sorted(os.listdir(args.streams_dir)):
        if stems and stem not in stems:
            continue
        segp = os.path.join(args.streams_dir, stem, f"{stem}__segments.json")
        if not os.path.exists(segp):
            continue
        entry = idx.get(stem)
        if not entry:
            print(f"[skip] {stem}: not in index", file=sys.stderr)
            continue
        segs = json.load(open(segp))["segments"]
        for s in segs:
            dur = s["t1"] - s["t0"]
            if dur < args.min_dur:
                n_skipped += 1
                continue
            crop = entry["existing_crops"].get(s["side"])
            if not crop or not os.path.exists(crop):
                print(f"[skip] {s['seg_id']}: no {s['side']} crop", file=sys.stderr)
                continue
            out = os.path.join(args.out_dir, f"{s['seg_id']}.mp4")
            # seek the (silent) crop and add a silent mono 16k audio track so downstream
            # normalization / Whisper / TSV audio-column see a well-formed video.
            cmd = ["ffmpeg", "-v", "error", "-y",
                   "-ss", f"{s['t0']:.3f}", "-i", crop,
                   "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono",
                   "-t", f"{dur:.3f}", "-map", "0:v", "-map", "1:a",
                   "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                   "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
                   "-movflags", "+faststart", out]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"[FAIL] {s['seg_id']}: {r.stderr[-200:]}", file=sys.stderr)
                continue
            seg_meta[s["seg_id"]] = {"stem": stem, "scene": entry["scene"],
                                     "script": entry["script"], "side": s["side"],
                                     "angle": entry["angle"],
                                     "speakers_in_name": entry["speakers_in_name"],
                                     "t0": s["t0"], "t1": s["t1"]}
            n_clips += 1
    meta_path = os.path.join(args.out_dir, "seg_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(seg_meta, f, ensure_ascii=False, indent=2)
    print(f"[cut] {n_clips} clips written to {args.out_dir} ({n_skipped} too short) ; meta -> {meta_path}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
