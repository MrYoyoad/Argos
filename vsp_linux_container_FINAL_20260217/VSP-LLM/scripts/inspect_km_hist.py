#!/usr/bin/env python3
import argparse
import numpy as np
import os
import sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--km", required=True, help="Path to *.km file (e.g. train.km)")
    ap.add_argument("--k", type=int, default=200, help="Number of clusters (default: 200)")
    args = ap.parse_args()

    print(f"[INFO] KM file: {args.km}")
    if not os.path.isfile(args.km):
        print("[ERROR] File does not exist!", file=sys.stderr)
        sys.exit(1)

    with open(args.km, "r") as f:
        text = f.read().strip()

    if not text:
        print("[WARN] File is empty, no labels found.")
        return

    tokens = [t for t in text.split() if t.strip()]
    print(f"[INFO] Number of tokens in file: {len(tokens)}")

    labels = np.array([int(t) for t in tokens], dtype=np.int32)
    print(f"[INFO] Total labels (after int cast): {labels.size}")

    hist = np.bincount(labels, minlength=args.k)

    print("\ncluster_id\tcount")
    for i, c in enumerate(hist):
        print(f"{i}\t{c}")

if __name__ == "__main__":
    main()
