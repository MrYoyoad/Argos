#!/usr/bin/env python3
"""
enhance_videos.py — adaptive CLAHE + brightness normalization for lip-reading.

Per-video: samples mean luma, computes offset to target ~128,
applies CLAHE on Y channel (local adaptive contrast), mild unsharp mask.
Uses ffmpeg for I/O, OpenCV for per-frame processing.

Usage:
    python3 enhance_videos.py <input_dir> <output_dir>
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

TARGET_LUMA = 128.0          # target mean Y luma after normalization
CLAHE_CLIP = 2.5             # CLAHE clip limit (2-3 typical for faces)
CLAHE_GRID = 8               # tile grid size (smaller = more local)
SHARP_SIGMA = 2.0            # unsharp mask Gaussian sigma
SHARP_AMOUNT = 0.5           # blend: 0=off, 1.0=full sharpening
MAX_BRIGHTNESS_OFFSET = 0.20 # cap offset at ±51 luma units


def get_video_info(path: str) -> dict:
    out = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', path],
        capture_output=True, text=True)
    info = json.loads(out.stdout)
    vs = next(s for s in info['streams'] if s['codec_type'] == 'video')
    fps_num, fps_den = map(int, vs['r_frame_rate'].split('/'))
    return {'w': int(vs['width']), 'h': int(vs['height']), 'fps': fps_num / fps_den}


def sample_mean_luma(path: str, w: int, h: int, max_frames: int = 40) -> float:
    """Sample up to max_frames evenly-spaced gray frames, return mean luma."""
    cmd = [
        'ffmpeg', '-i', path,
        '-vf', 'select=not(mod(n\\,6))',
        '-vframes', str(max_frames),
        '-f', 'rawvideo', '-pix_fmt', 'gray',
        '-loglevel', 'error', 'pipe:1'
    ]
    proc = subprocess.run(cmd, capture_output=True)
    raw = proc.stdout
    frame_size = w * h
    if len(raw) < frame_size:
        return TARGET_LUMA
    n_frames = len(raw) // frame_size
    arr = np.frombuffer(raw[:n_frames * frame_size], dtype=np.uint8)
    return float(arr.mean())


def enhance_video(src: str, dst: str) -> None:
    info = get_video_info(src)
    w, h, fps = info['w'], info['h'], info['fps']
    frame_size = w * h * 3

    mean_luma = sample_mean_luma(src, w, h)
    raw_offset = (TARGET_LUMA - mean_luma) / 255.0
    brightness_offset = max(-MAX_BRIGHTNESS_OFFSET, min(MAX_BRIGHTNESS_OFFSET, raw_offset))
    offset_px = int(brightness_offset * 255)

    print(f"  [ENHANCE] {Path(src).name}: mean_luma={mean_luma:.1f}, "
          f"offset={offset_px:+d}px", flush=True)

    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=(CLAHE_GRID, CLAHE_GRID))

    decode_cmd = [
        'ffmpeg', '-i', src,
        '-f', 'rawvideo', '-pix_fmt', 'bgr24',
        '-loglevel', 'error', 'pipe:1'
    ]
    encode_cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo', '-pix_fmt', 'bgr24',
        '-s', f'{w}x{h}', '-r', str(fps),
        '-i', 'pipe:0',
        '-i', src,        # audio from original
        '-map', '0:v', '-map', '1:a?',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '17',
        '-c:a', 'aac', '-ac', '1', '-ar', '16000',
        '-movflags', '+faststart',
        '-loglevel', 'error', dst
    ]

    decoder = subprocess.Popen(decode_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    encoder = subprocess.Popen(encode_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    try:
        while True:
            raw = decoder.stdout.read(frame_size)
            if len(raw) < frame_size:
                break
            frame = np.frombuffer(raw, dtype=np.uint8).reshape((h, w, 3)).copy()

            # CLAHE on Y channel only — preserves color, boosts local contrast
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            y, cr, cb = cv2.split(ycrcb)
            y_eq = clahe.apply(y)

            # Global brightness offset (capped)
            if offset_px != 0:
                y_eq = np.clip(y_eq.astype(np.int16) + offset_px, 0, 255).astype(np.uint8)

            # Unsharp mask to sharpen lip/mouth edges
            if SHARP_AMOUNT > 0:
                blur = cv2.GaussianBlur(y_eq, (0, 0), SHARP_SIGMA)
                y_eq = cv2.addWeighted(y_eq, 1.0 + SHARP_AMOUNT, blur, -SHARP_AMOUNT, 0)

            result = cv2.cvtColor(cv2.merge([y_eq, cr, cb]), cv2.COLOR_YCrCb2BGR)
            encoder.stdin.write(result.tobytes())

    except BrokenPipeError:
        pass
    finally:
        decoder.stdout.close()
        decoder.wait()
        encoder.stdin.close()
        encoder.wait()

    if encoder.returncode != 0:
        raise RuntimeError(f"Encoder failed for {Path(src).name}")


def main():
    ap = argparse.ArgumentParser(
        description='Enhance videos for lip-reading via CLAHE + brightness normalization')
    ap.add_argument('input_dir', help='Directory of input videos')
    ap.add_argument('output_dir', help='Directory for enhanced output videos')
    args = ap.parse_args()

    inp = Path(args.input_dir)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    exts = {'.mp4', '.MP4', '.mov', '.MOV', '.mkv', '.MKV', '.avi', '.AVI', '.webm', '.WEBM'}
    videos = sorted(v for v in inp.iterdir() if v.is_file() and v.suffix in exts)

    if not videos:
        print(f"  [ENHANCE] No videos found in {inp}", flush=True)
        return

    ok = fail = 0
    for v in videos:
        dst = out / (v.stem + '.mp4')
        try:
            enhance_video(str(v), str(dst))
            ok += 1
        except Exception as e:
            print(f"  [WARN] Enhancement failed for {v.name}: {e} — copying raw", flush=True)
            import shutil
            shutil.copy2(str(v), str(dst))
            fail += 1

    print(f"  [ENHANCE] Done: {ok} enhanced, {fail} fallback-copied", flush=True)


if __name__ == '__main__':
    main()
