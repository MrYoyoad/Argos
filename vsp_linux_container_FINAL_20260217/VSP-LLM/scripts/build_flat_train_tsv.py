#!/usr/bin/env python3
import argparse
import os
import subprocess
import wave
import contextlib

def read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        required=True,
        help="Root of the preprocessed flat dataset (e.g. /home/ubuntu/auto_avsr/arabic_flat_preprocessed)",
    )
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    video_dir = os.path.join(root, "video")
    audio_dir = os.path.join(root, "audio")
    tsv_dir   = os.path.join(root, "433h_data")
    tsv_path  = os.path.join(tsv_dir, "train.tsv")

    print(f"[INFO] ROOT     = {root}")
    print(f"[INFO] video_dir= {video_dir}")
    print(f"[INFO] audio_dir= {audio_dir}")
    print(f"[INFO] tsv_path = {tsv_path}")

    # sanity checks
    file_list_path    = os.path.join(root, "file.list")
    nframes_video_path = os.path.join(root, "nframes.video")

    if not os.path.exists(file_list_path):
        raise FileNotFoundError(f"Missing file.list at {file_list_path}")
    if not os.path.exists(nframes_video_path):
        raise FileNotFoundError(f"Missing nframes.video at {nframes_video_path}")
    if not os.path.isdir(video_dir):
        raise FileNotFoundError(f"Missing video/ dir at {video_dir} (symlink to flat/flat_video_seg4s)")

    ids = read_lines(file_list_path)
    nframes_video = [int(x) for x in read_lines(nframes_video_path)]

    if len(ids) != len(nframes_video):
        raise ValueError(f"file.list has {len(ids)} lines but nframes.video has {len(nframes_video)}")

    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(tsv_dir, exist_ok=True)

    print(f"[INFO] {len(ids)} segments found; building WAVs (if needed) and train.tsv ...")

    def ensure_wav(video_path, audio_path):
        """Create audio_path from video_path if it doesn't exist, using ffmpeg."""
        if os.path.exists(audio_path):
            return
        cmd = [
            "ffmpeg",
            "-v", "error",
            "-y",
            "-i", video_path,
            "-ac", "1",      # mono
            "-ar", "16000",  # 16kHz
            audio_path,
        ]
        print(f"[ffmpeg] {os.path.basename(video_path)} -> {os.path.basename(audio_path)}")
        subprocess.run(cmd, check=True)

    def count_samples(wav_path):
        with contextlib.closing(wave.open(wav_path, "rb")) as wf:
            return wf.getnframes()

    with open(tsv_path, "w", encoding="utf-8") as out:
        # first line: root placeholder (as in preprocessed_flat_seg4)
        out.write("/\n")
        for fid, n_v in zip(ids, nframes_video):
            vpath = os.path.join(video_dir, fid + ".mp4")
            apath = os.path.join(audio_dir, fid + ".wav")

            if not os.path.exists(vpath):
                raise FileNotFoundError(f"Video not found: {vpath}")

            ensure_wav(vpath, apath)
            n_samples = count_samples(apath)

            out.write(f"{fid}\t{vpath}\t{apath}\t{n_v}\t{n_samples}\n")

    print(f"[OK] Wrote {tsv_path}")
    print("[OK] Format matches preprocessed_flat_seg4 (5 columns).")

if __name__ == "__main__":
    main()
