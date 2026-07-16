#!/usr/bin/env python3
"""egla_kafe_resolution_prep.py — build the resolution-ablation condition trees (Workstream R).

Quantifies decode-quality change when the SAME true-4K footage enters the pipeline at lower
resolution. Three conditions under /home/ubuntu/datasets/clients/egla_kafe_resolution/:

    res4k_ctrl  scale 1.0   controls for the extra encode generation + 10-bit -> 8-bit
    res2k       scale 2/3   1300px crops -> 866px (1200 -> 800)
    res1080     scale 0.5   1300px crops -> 650px (1200 -> 600)

Source of truth: the 10 hand-made 4K speaker crops of the 5 iPhone masters (img_6821..img_6825
x left/right), found via the original index's `existing_crops` (h264 1300x1300 / 1200x1200
yuv420p10le 30fps, Hebrew paths). Each condition gets:

    dataset/README.md                       provenance paragraph
    work/crops_src/img_682X__{left,right}.mp4   downscaled 8-bit crops (ASCII paths)
    work/streams/img_682X/img_682X__segments.json  byte-identical copy of the original run's
                                            segmentation -> seg_ids identical across conditions
                                            AND vs the existing 4K baseline (run_shaam_all)
    work/eval/index.json                    the 5 master entries, existing_crops -> crops_src
    work/eval/{face_id.json,script_scene1.json,script_scene2.json}  copied (align stage inputs)
    eval_config.json                        orchestrator config, stages segments/decode/align/score
    prep_manifest.json                      factor, src->dst, ffprobe in/out, exact commands

Segmentation is held FIXED by construction (segments.json copied, streams stage skipped):
egla_kafe_cut_segments.py reads crops from index `existing_crops` and segments.json from
work/streams/<stem>/ — the only inputs the `segments` stage needs.

Run:  python3 scripts/pipeline/egla_kafe_resolution_prep.py            # all 3 conditions
      python3 ... --conditions res2k --force                           # re-encode subset
Idempotent: existing crop files that ffprobe-verify are skipped unless --force.
"""
import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from fractions import Fraction

ORIG_ROOT = "/home/ubuntu/datasets/clients/egla_kafe"
ORIG_INDEX = f"{ORIG_ROOT}/work/eval/index.json"
ORIG_CONFIG = f"{ORIG_ROOT}/eval_config.json"
ORIG_STREAMS = f"{ORIG_ROOT}/work/streams"
ORIG_EVAL = f"{ORIG_ROOT}/work/eval"
ORIG_DECODE_IN = f"{ORIG_ROOT}/work/decode/in_shaam_all"  # 4K baseline run's decode input
BASE = "/home/ubuntu/datasets/clients/egla_kafe_resolution"

MASTER_STEMS = ["img_6821", "img_6822", "img_6823", "img_6824", "img_6825"]
# factor expression exactly as substituted into the ffmpeg scale filter
CONDITIONS = {"res4k_ctrl": "1.0", "res2k": "2/3", "res1080": "0.5"}
EVAL_COPY_FILES = ["face_id.json", "script_scene1.json", "script_scene2.json"]
MIN_DUR = 0.6  # mirrors egla_kafe_cut_segments.py --min-dur default

FFMPEG_TEMPLATE = ('ffmpeg -y -i SRC -vf "scale=trunc(iw*F/2)*2:trunc(ih*F/2)*2:flags=lanczos" '
                   '-c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -an '
                   '-movflags +faststart DST')


def ffprobe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_frames",
         "-show_entries", "format=duration", "-of", "json", path],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"ffprobe failed on {path}: {r.stderr[-300:]}")
    d = json.loads(r.stdout)
    s = d["streams"][0]
    return {"codec": s["codec_name"], "w": int(s["width"]), "h": int(s["height"]),
            "pix_fmt": s["pix_fmt"], "fps": s["r_frame_rate"],
            "nb_frames": int(s.get("nb_frames", 0)),
            "duration": round(float(d["format"]["duration"]), 3)}


def expected_dim(src_dim, factor_expr):
    """Replicate ffmpeg's trunc(dim*F/2)*2 for the factor expressions we use."""
    f = Fraction(factor_expr) if "/" in factor_expr else Fraction(str(float(factor_expr)))
    return math.floor(src_dim * f / 2) * 2


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def encode_crop(src, dst, factor_expr, force):
    """Run the exact spec ffmpeg command. Returns (cmd_str, skipped)."""
    vf = f"scale=trunc(iw*{factor_expr}/2)*2:trunc(ih*{factor_expr}/2)*2:flags=lanczos"
    cmd = ["ffmpeg", "-y", "-i", src, "-vf", vf, "-c:v", "libx264", "-crf", "16",
           "-preset", "slow", "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", dst]
    cmd_str = " ".join(c if " " not in c else f'"{c}"' for c in cmd)
    if not force and os.path.exists(dst):
        try:
            p_src, p_dst = ffprobe(src), ffprobe(dst)
            if (p_dst["w"] == expected_dim(p_src["w"], factor_expr)
                    and p_dst["h"] == expected_dim(p_src["h"], factor_expr)
                    and p_dst["pix_fmt"] == "yuv420p"
                    and p_dst["nb_frames"] == p_src["nb_frames"]):
                return cmd_str, True
        except SystemExit:
            pass  # broken partial file -> re-encode
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg failed for {dst}:\n{r.stderr[-800:]}")
    print(f"    encoded {os.path.basename(dst)} in {time.time()-t0:.0f}s", file=sys.stderr)
    return cmd_str, False


def readme_text(cond, factor_expr):
    return (f"# egla_kafe_resolution / {cond}\n\n"
            f"Resolution-ablation condition (Workstream R, July 2026). The 10 hand-made 4K "
            f"speaker crops of iPhone masters IMG_6821..IMG_6825 (left/right, h264 "
            f"1300x1300 / 1200x1200 yuv420p10le 30fps, from "
            f"`datasets/clients/egla_kafe/dataset/קטעי "
            f"דוברים/שפם 4K/`) were re-encoded "
            f"with scale factor **{factor_expr}** via "
            f"`{FFMPEG_TEMPLATE.replace('F', factor_expr)}` — one extra lossy h264 generation "
            f"and a 10-bit -> 8-bit conversion that ALL three conditions share (res4k_ctrl "
            f"isolates exactly that, so any res2k/res1080 delta beyond res4k_ctrl is "
            f"attributable to resolution alone). Turn segmentation is held fixed: the original "
            f"run's per-stem `img_682X__segments.json` files are copied verbatim, so the 175 "
            f"seg_ids are byte-identical across conditions and vs the existing 4K baseline "
            f"(`work/eval/run_shaam_all`), enabling paired statistics. Encoded crops live in "
            f"`work/crops_src/` (ASCII paths); this dataset/ dir intentionally holds only this "
            f"README. Built by `scripts/pipeline/egla_kafe_resolution_prep.py`; see "
            f"`../prep_manifest.json` for exact commands and ffprobe records.\n")


def build_condition(cond, factor_expr, orig_index, orig_cfg, force, jobs):
    print(f"\n=== condition {cond} (factor {factor_expr}) ===", file=sys.stderr)
    root = os.path.join(BASE, cond)
    crops_dir = os.path.join(root, "work", "crops_src")
    eval_dir = os.path.join(root, "work", "eval")
    for d in (os.path.join(root, "dataset"), crops_dir, eval_dir,
              os.path.join(root, "work", "streams"), os.path.join(root, "work", "decode"),
              os.path.join(root, "deliverables")):
        os.makedirs(d, exist_ok=True)

    # dataset/README.md
    with open(os.path.join(root, "dataset", "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_text(cond, factor_expr))

    entries = [e for e in orig_index["entries"] if e["stem"] in MASTER_STEMS]
    if len(entries) != len(MASTER_STEMS):
        raise SystemExit(f"expected {len(MASTER_STEMS)} master entries in {ORIG_INDEX}, "
                         f"got {len(entries)}")

    # 1) encode crops (parallel across files; x264 also threads internally)
    tasks = []  # (entry, side, src, dst)
    for e in entries:
        for side in ("left", "right"):
            src = e["existing_crops"][side]
            if not (src and os.path.exists(src)):
                raise SystemExit(f"missing source crop for {e['stem']} {side}: {src}")
            dst = os.path.join(crops_dir, f"{e['stem']}__{side}.mp4")
            tasks.append((e, side, src, dst))
    crop_records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        futs = {ex.submit(encode_crop, src, dst, factor_expr, force): (e, side, src, dst)
                for e, side, src, dst in tasks}
        for fut in concurrent.futures.as_completed(futs):
            e, side, src, dst = futs[fut]
            cmd_str, skipped = fut.result()
            p_src, p_dst = ffprobe(src), ffprobe(dst)
            exp_w, exp_h = expected_dim(p_src["w"], factor_expr), expected_dim(p_src["h"], factor_expr)
            errs = []
            if (p_dst["w"], p_dst["h"]) != (exp_w, exp_h):
                errs.append(f"dims {p_dst['w']}x{p_dst['h']} != expected {exp_w}x{exp_h}")
            if p_dst["pix_fmt"] != "yuv420p":
                errs.append(f"pix_fmt {p_dst['pix_fmt']} != yuv420p")
            if p_dst["nb_frames"] != p_src["nb_frames"]:
                errs.append(f"nb_frames {p_dst['nb_frames']} != src {p_src['nb_frames']}")
            if errs:
                raise SystemExit(f"crop verify FAILED {dst}: " + "; ".join(errs))
            crop_records.append({"stem": e["stem"], "side": side, "src": src, "dst": dst,
                                 "src_probe": p_src, "dst_probe": p_dst,
                                 "expected": {"w": exp_w, "h": exp_h},
                                 "cmd": cmd_str, "reused_existing": skipped})
            print(f"  [ok] {e['stem']}__{side}: {p_src['w']}x{p_src['h']} {p_src['pix_fmt']} "
                  f"-> {p_dst['w']}x{p_dst['h']} {p_dst['pix_fmt']}"
                  f"{' (existing, verified)' if skipped else ''}", file=sys.stderr)
    crop_records.sort(key=lambda r: (r["stem"], r["side"]))

    # 2) copy segments.json per stem (byte-identical -> identical seg_ids)
    seg_records, expected_ids = {}, set()
    for stem in MASTER_STEMS:
        src = os.path.join(ORIG_STREAMS, stem, f"{stem}__segments.json")
        ddir = os.path.join(root, "work", "streams", stem)
        os.makedirs(ddir, exist_ok=True)
        dst = os.path.join(ddir, f"{stem}__segments.json")
        shutil.copy2(src, dst)
        segs = json.load(open(src))["segments"]
        keep = [s for s in segs if s["t1"] - s["t0"] >= MIN_DUR]
        expected_ids.update(s["seg_id"] for s in keep)
        seg_records[stem] = {"src": src, "dst": dst, "sha256": sha256(src),
                             "n_segments": len(segs), "n_ge_min_dur": len(keep)}
        if sha256(dst) != seg_records[stem]["sha256"]:
            raise SystemExit(f"segments.json copy mismatch for {stem}")

    # parity precheck vs the existing 4K baseline decode input (run_shaam_all)
    orig_clips = {os.path.splitext(b)[0] for b in os.listdir(ORIG_DECODE_IN)
                  if b.startswith("img_") and b.endswith(".mp4")}
    if expected_ids != orig_clips:
        raise SystemExit(f"seg_id parity precheck failed: segments.json-derived ids "
                         f"({len(expected_ids)}) != baseline in_shaam_all img_* clips "
                         f"({len(orig_clips)}); diff={sorted(expected_ids ^ orig_clips)[:5]}")
    print(f"  [ok] segments.json x{len(MASTER_STEMS)} copied; {len(expected_ids)} seg_ids "
          f">= {MIN_DUR}s, parity with 4K baseline decode input", file=sys.stderr)

    # 3) copy eval-side inputs the align stage reads (scripts-dir + face-id)
    copied = []
    for name in EVAL_COPY_FILES:
        src = os.path.join(ORIG_EVAL, name)
        if not os.path.exists(src):
            raise SystemExit(f"missing eval input {src}")
        shutil.copy2(src, os.path.join(eval_dir, name))
        copied.append(name)
    print(f"  [ok] eval inputs copied: {', '.join(copied)}", file=sys.stderr)

    # 4) hand-built index.json: the 5 master entries, existing_crops -> condition crops
    new_entries = []
    for e in entries:
        ne = dict(e)
        ne["existing_crops"] = {
            side: os.path.join(crops_dir, f"{e['stem']}__{side}.mp4")
            for side in ("left", "right")}
        new_entries.append(ne)
    with open(os.path.join(eval_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"n": len(new_entries), "entries": new_entries},
                  f, ensure_ascii=False, indent=2)

    # 5) eval_config.json for the orchestrator
    cfg = {
        "name": f"egla_kafe_res_{cond}",
        "dataset_root": root,
        "work_root": os.path.join(root, "work"),
        "deliverables_root": os.path.join(root, "deliverables"),
        "golden_kmeans": "/home/ubuntu/golden_weights/baseline_20260218/flat_kmeans_200.bin",
        "venv_prep": orig_cfg["venv_prep"],
        "venv_full": orig_cfg["venv_full"],
        "vsp_dir": orig_cfg["vsp_dir"],
        "stages": ["segments", "decode", "align", "score"],
    }
    with open(os.path.join(root, "eval_config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")

    # 6) prep_manifest.json
    manifest = {
        "condition": cond,
        "factor_expr": factor_expr,
        "factor_float": round(float(Fraction(factor_expr)), 6),
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prep_tool": os.path.abspath(__file__),
        "ffmpeg_cmd_template": FFMPEG_TEMPLATE,
        "source_index": ORIG_INDEX,
        "expected_clip_count": len(expected_ids),
        "min_dur_s": MIN_DUR,
        "segments_copied": seg_records,
        "eval_files_copied": copied,
        "crops": crop_records,
        "notes": ("segmentation held fixed (segments.json copied byte-identical from the "
                  "original run) -> seg_ids identical across conditions and vs the 4K "
                  "baseline run_shaam_all; res4k_ctrl (factor 1.0) controls for the extra "
                  "h264 generation + 10->8-bit shared by all conditions"),
    }
    with open(os.path.join(root, "prep_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  [done] {cond}: {len(crop_records)} crops, manifest -> "
          f"{os.path.join(root, 'prep_manifest.json')}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--conditions", default=",".join(CONDITIONS),
                    help=f"comma subset of {list(CONDITIONS)}")
    ap.add_argument("--force", action="store_true", help="re-encode even if dst verifies")
    ap.add_argument("--jobs", type=int, default=2, help="parallel ffmpeg encodes")
    args = ap.parse_args()

    orig_index = json.load(open(ORIG_INDEX, encoding="utf-8"))
    orig_cfg = json.load(open(ORIG_CONFIG, encoding="utf-8"))
    for cond in args.conditions.split(","):
        if cond not in CONDITIONS:
            raise SystemExit(f"unknown condition {cond!r}; choose from {list(CONDITIONS)}")
        build_condition(cond, CONDITIONS[cond], orig_index, orig_cfg, args.force, args.jobs)
    print("\n[prep] all conditions built OK", file=sys.stderr)


if __name__ == "__main__":
    main()
