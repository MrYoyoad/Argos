#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path

import torch

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi"}

FALLBACK_WORDS = ["no", "audio"]  # written one-per-line into .wrd


def has_audio_stream(video_path: Path) -> bool:
    """
    Returns True iff ffprobe detects at least one audio stream.
    Safe for video-only mp4s.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "json",
        str(video_path),
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if p.returncode != 0:
            return False
        data = json.loads(p.stdout or "{}")
        return bool(data.get("streams"))
    except Exception:
        return False


def load_whisper_model(model_size: str, download_root: str = None):
    import whisper

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_size, device=device, download_root=download_root)
    return model, device


def run_whisper(model, device: str, video_path: Path, lang: str):
    return model.transcribe(str(video_path), language=lang, fp16=(device == "cuda"))


def normalize_text(t: str, lower: bool = True, collapse_spaces: bool = True) -> str:
    t = (t or "").strip()
    if lower:
        t = t.lower()
    if collapse_spaces:
        t = " ".join(t.split())
    return t


def tokenize(text: str, mode: str):
    if mode == "whitespace":
        return [tok for tok in text.split() if tok]
    if mode == "alnum":
        return re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", text)
    raise ValueError("Unknown tokenize mode")


def write_fallback_wrd(path: Path):
    path.write_text("\n".join(FALLBACK_WORDS) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser("Make per-video .wrd (no timing) from a FLAT folder")
    ap.add_argument("--in_videos", required=True, help="FLAT folder of videos (no recursion)")
    ap.add_argument("--out_wrd", required=True, help="Output folder for .wrd files")
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--tokenize", default="alnum", choices=["alnum", "whitespace"])
    ap.add_argument("--lower", action="store_true")
    ap.add_argument("--keep_json", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--download_root", default=None, help="Path to Whisper model cache directory")
    args = ap.parse_args()

    in_dir = Path(args.in_videos)
    out_dir = Path(args.out_wrd)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_entries = list(in_dir.iterdir())
    print(f"[DEBUG] {in_dir} entries: {len(all_entries)}")

    vids = sorted([p for p in all_entries if p.is_file() and p.suffix.lower() in VIDEO_EXTS])
    print(f"[INFO] Found {len(vids)} video files to transcribe")

    if not vids:
        print("[WARN] No videos found")
        return

    model, device = load_whisper_model(args.model, download_root=args.download_root)

    for v in vids:
        wrd_path = out_dir / (v.stem + ".wrd")

        if wrd_path.exists() and not args.overwrite:
            print("[SKIP] exists:", wrd_path)
            continue

        # 1) Hard guarantee: if no audio stream -> write fallback tokens
        if not has_audio_stream(v):
            write_fallback_wrd(wrd_path)
            print(f"[NO-AUDIO-STREAM] {v.name} -> wrote fallback .wrd ({' '.join(FALLBACK_WORDS)})")
            continue

        print("[ASR]", v)
        try:
            result = run_whisper(model, device, v, args.lang)

            text = normalize_text(
                result.get("text", ""),
                lower=args.lower,
                collapse_spaces=True,
            )
            words = tokenize(text, mode=args.tokenize)

            # 2) If Whisper produces no text/words -> write fallback tokens
            if not text or len(words) == 0:
                write_fallback_wrd(wrd_path)
                print(f"[EMPTY-ASR] {v.name} -> wrote fallback .wrd ({' '.join(FALLBACK_WORDS)})")
            else:
                wrd_path.write_text("\n".join(words) + "\n", encoding="utf-8")
                print("  ->", wrd_path)

            if args.keep_json:
                (out_dir / (v.stem + ".whisper.json")).write_text(
                    json.dumps(result, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

        except Exception as e:
            # 3) Fail-soft: never crash pipeline
            write_fallback_wrd(wrd_path)
            print(f"[ERROR] Whisper failed on {v.name}: {e}")
            print(f"        wrote fallback .wrd ({' '.join(FALLBACK_WORDS)}) and continuing")

    print("[DONE] .wrd generation complete:", out_dir)


if __name__ == "__main__":
    main()