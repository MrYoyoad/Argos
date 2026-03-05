#!/usr/bin/env python3
import argparse
from collections import Counter
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Build cluster_counts file from a .km file (cluster IDs)."
    )
    parser.add_argument("--km", required=True, help="Path to input .km file")
    parser.add_argument("--out", required=True, help="Path to output .cluster_counts file")
    parser.add_argument("--k", type=int, required=True, help="Number of clusters (e.g., 200)")
    args = parser.parse_args()

    km_path = Path(args.km)
    out_path = Path(args.out)

    if not km_path.is_file():
        raise FileNotFoundError(f".km file not found: {km_path}")

    print(f"[build_flat_cluster_counts] Reading:  {km_path}")
    counts = Counter()

    with km_path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            for tok in line.split():
                try:
                    cid = int(tok)
                except ValueError:
                    continue
                counts[cid] += 1

    print(f"[build_flat_cluster_counts] Writing:  {out_path}")
    with out_path.open("w") as f:
        f.write(f"{args.k}\n")
        for cid in range(args.k):
            f.write(f"{cid} {counts.get(cid, 0)}\n")

    print("[build_flat_cluster_counts] Done.")

if __name__ == "__main__":
    main()
