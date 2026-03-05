#!/usr/bin/env python3
import argparse
import os
from collections import Counter


def read_lines(path):
    with open(path, "r") as f:
        return [ln.rstrip("\n") for ln in f]


def main():
    p = argparse.ArgumentParser(
        description="Make simple 433h-style manifest (tsv + wrd + dict) "
                    "from flat_to_lrs3_preperation output."
    )
    p.add_argument(
        "--root",
        required=True,
        help="Root that contains file.list, label.list, nframes.video, and flat/ folder "
             "(e.g. /home/ubuntu/auto_avsr/arabic_flat_preprocessed)",
    )
    p.add_argument(
        "--split",
        default="test",
        help="Name of split to create (default: test). "
             "Outputs <split>.tsv and <split>.wrd",
    )
    p.add_argument(
        "--out-dir",
        default=None,
        help="Where to write tsv/wrd/dict (default: <root>/433h_data)",
    )
    p.add_argument(
        "--video-subdir",
        default="flat/flat_video_seg4s",
        help="Subdir under root where the .mp4 segments live "
             '(default: "flat/flat_video_seg4s")',
    )
    args = p.parse_args()

    root = os.path.abspath(args.root)
    out_dir = args.out_dir or os.path.join(root, "433h_data")
    os.makedirs(out_dir, exist_ok=True)

    file_list_path = os.path.join(root, "file.list")
    label_list_path = os.path.join(root, "label.list")
    nframes_path = os.path.join(root, "nframes.video")

    if not os.path.isfile(file_list_path):
        raise FileNotFoundError(file_list_path)
    if not os.path.isfile(label_list_path):
        raise FileNotFoundError(label_list_path)
    if not os.path.isfile(nframes_path):
        raise FileNotFoundError(nframes_path)

    ids = read_lines(file_list_path)
    labels = read_lines(label_list_path)

    if len(ids) != len(labels):
        raise RuntimeError(
            f"file.list and label.list length mismatch: "
            f"{len(ids)} vs {len(labels)}"
        )

    # nframes.video usually has lines like: "<id> <nframes>"
    nframes = []
    with open(nframes_path, "r") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            parts = ln.split()
            try:
                n = int(parts[-1])
            except ValueError:
                raise RuntimeError(f"Could not parse nframes from line: {ln}")
            nframes.append(n)

    if len(nframes) != len(ids):
        raise RuntimeError(
            f"nframes.video length mismatch: {len(nframes)} vs {len(ids)}"
        )

    # -----------------------------
    # Write <split>.tsv
    # -----------------------------
    video_root = os.path.join(root, args.video_subdir)
    tsv_path = os.path.join(out_dir, f"{args.split}.tsv")

    with open(tsv_path, "w") as f:
        # First line: root directory containing the videos
        f.write(video_root + "\n")
        # Lines: "<relative_path>\t<nframes>"
        for fid, nf in zip(ids, nframes):
            rel_path = f"{fid}.mp4"   # relative to video_root
            f.write(f"{rel_path}\t{nf}\n")

    print(f"Wrote TSV: {tsv_path}")

    # -----------------------------
    # Write <split>.wrd  (one sentence per line)
    # -----------------------------
    wrd_path = os.path.join(out_dir, f"{args.split}.wrd")
    with open(wrd_path, "w") as f:
        for sent in labels:
            # Keep as-is (Arabic is fine). If you want lowercase, you can add .lower()
            f.write(sent.strip() + "\n")
    print(f"Wrote WRD: {wrd_path}")

    # -----------------------------
    # Build dict.wrd.txt from labels
    # -----------------------------
    counter = Counter()
    for sent in labels:
        for tok in sent.strip().split():
            if tok:
                counter[tok] += 1

    dict_path = os.path.join(out_dir, "dict.wrd.txt")
    with open(dict_path, "w") as f:
        # Sort by frequency (desc), then lexicographically
        for tok, freq in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
            f.write(f"{tok} {freq}\n")
    print(f"Wrote DICT: {dict_path}")

    print("\nDone. 433h-style manifest written to:", out_dir)


if __name__ == "__main__":
    main()
