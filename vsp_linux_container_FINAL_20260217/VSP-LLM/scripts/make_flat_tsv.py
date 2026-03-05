import os
import argparse

def main():
    p = argparse.ArgumentParser(
        description="Create <split>.tsv from file.list + nframes.video for flat LRS3-style data."
    )
    p.add_argument("--root", required=True,
                   help="Root LRS3-style dir (has file.list, nframes.video, and video/ symlink).")
    p.add_argument("--split", default="train",
                   help="Split name to use in <split>.tsv (default: train).")
    p.add_argument("--out-dir", default=None,
                   help="Output dir for TSV (default: <root>/433h_data).")
    args = p.parse_args()

    root = os.path.abspath(args.root)
    split = args.split

    file_list_path = os.path.join(root, "file.list")
    nframes_path   = os.path.join(root, "nframes.video")

    if not os.path.exists(file_list_path):
        raise FileNotFoundError(f"Missing file.list at {file_list_path}")
    if not os.path.exists(nframes_path):
        raise FileNotFoundError(f"Missing nframes.video at {nframes_path}")

    with open(file_list_path, "r") as f:
        ids = [ln.strip() for ln in f if ln.strip()]

    with open(nframes_path, "r") as f:
        nframes = [ln.strip() for ln in f if ln.strip()]

    if len(ids) != len(nframes):
        raise RuntimeError(
            f"Length mismatch: {len(ids)} ids vs {len(nframes)} frame counts"
        )

    out_dir = args.out_dir or os.path.join(root, "433h_data")
    os.makedirs(out_dir, exist_ok=True)

    tsv_path = os.path.join(out_dir, f"{split}.tsv")
    print(f"Writing TSV to: {tsv_path}")
    print(f"Root (first line) = {root}")

    with open(tsv_path, "w") as out_f:
        # First line: data root
        out_f.write(root + "\n")
        # Each subsequent line: <relative/path>\t<n_frames>
        for vid, nf in zip(ids, nframes):
            rel_path = os.path.join("video", vid + ".mp4")
            out_f.write(f"{rel_path}\t{nf}\n")

    print(f"Done. Wrote {len(ids)} entries.")

if __name__ == "__main__":
    main()
