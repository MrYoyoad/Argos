#!/usr/bin/env python3
"""Create stratified train/val split from english_full_results manifests.

Splits 1,497 segments into ~85% train / ~15% validation, stratified by
intelligibility tier (1-5) so the validation set is representative.

Output goes to /home/ubuntu/finetune_data/ with:
  train.tsv, train.wrd, train.cluster_counts
  test.tsv, test.wrd, test.cluster_counts
"""

import csv
import json
import os
import random
import sys

SEED = 42
VAL_FRACTION = 0.15

# Paths
SCORES_CSV = "/home/ubuntu/docs/evaluation/intelligibility/intelligibility_scores.csv"
MANIFEST_TSV = "/home/ubuntu/english_full_results/manifests/train.tsv"
MANIFEST_WRD = "/home/ubuntu/english_full_results/manifests/train.wrd"
CLUSTER_COUNTS = "/home/ubuntu/english_full_results/flat_labels/train.cluster_counts"
OUT_DIR = "/home/ubuntu/finetune_data"


def main():
    random.seed(SEED)

    # Read intelligibility tiers
    tiers = {}
    with open(SCORES_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tiers[row["utt_id"]] = int(row["intelligibility_tier"])

    # Read manifest TSV (first line is root path "/")
    with open(MANIFEST_TSV) as f:
        root_line = f.readline()
        tsv_lines = f.readlines()

    # Read word labels
    with open(MANIFEST_WRD) as f:
        wrd_lines = f.readlines()

    # Read cluster counts
    with open(CLUSTER_COUNTS) as f:
        cc_lines = f.readlines()

    n = len(tsv_lines)
    assert n == len(wrd_lines) == len(cc_lines), (
        f"Line count mismatch: tsv={n}, wrd={len(wrd_lines)}, cc={len(cc_lines)}"
    )

    # Group indices by tier
    tier_groups = {1: [], 2: [], 3: [], 4: [], 5: []}
    missing_tier = 0
    for i, line in enumerate(tsv_lines):
        utt_id = line.strip().split("\t")[0]
        tier = tiers.get(utt_id)
        if tier is None:
            missing_tier += 1
            tier = 3  # default to middle tier if missing
        tier_groups[tier].append(i)

    if missing_tier > 0:
        print(f"Warning: {missing_tier} segments missing from intelligibility scores, assigned tier 3")

    # Stratified split
    train_idx = []
    val_idx = []
    for tier, indices in sorted(tier_groups.items()):
        random.shuffle(indices)
        n_val = max(1, round(len(indices) * VAL_FRACTION))
        val_idx.extend(indices[:n_val])
        train_idx.extend(indices[n_val:])

    train_idx.sort()
    val_idx.sort()

    print(f"Total segments: {n}")
    print(f"Train: {len(train_idx)}, Val: {len(val_idx)}")
    print(f"Split ratio: {len(train_idx)/n:.1%} / {len(val_idx)/n:.1%}")
    print()

    # Print tier distribution
    for tier in sorted(tier_groups.keys()):
        tier_set = set(tier_groups[tier])
        n_train = sum(1 for i in train_idx if i in tier_set)
        n_val = sum(1 for i in val_idx if i in tier_set)
        print(f"  Tier {tier}: {len(tier_groups[tier])} total -> {n_train} train, {n_val} val ({n_val/len(tier_groups[tier]):.1%} val)")

    # Write output files
    os.makedirs(OUT_DIR, exist_ok=True)

    def write_split(prefix, indices):
        with open(os.path.join(OUT_DIR, f"{prefix}.tsv"), "w") as f:
            f.write(root_line)
            for i in indices:
                f.write(tsv_lines[i])

        with open(os.path.join(OUT_DIR, f"{prefix}.wrd"), "w") as f:
            for i in indices:
                f.write(wrd_lines[i])

        with open(os.path.join(OUT_DIR, f"{prefix}.cluster_counts"), "w") as f:
            for i in indices:
                f.write(cc_lines[i])

    write_split("train", train_idx)
    write_split("test", val_idx)

    # Also copy dict.wrd.txt (needed by fairseq)
    dict_src = os.path.join(os.path.dirname(MANIFEST_TSV), "dict.wrd.txt")
    if os.path.exists(dict_src):
        import shutil
        shutil.copy2(dict_src, os.path.join(OUT_DIR, "dict.wrd.txt"))
        print(f"\nCopied dict.wrd.txt to {OUT_DIR}/")

    # Save split metadata
    metadata = {
        "seed": SEED,
        "val_fraction": VAL_FRACTION,
        "total_segments": n,
        "train_segments": len(train_idx),
        "val_segments": len(val_idx),
        "tier_distribution": {
            str(tier): {
                "total": len(tier_groups[tier]),
                "train": sum(1 for i in train_idx if i in set(tier_groups[tier])),
                "val": sum(1 for i in val_idx if i in set(tier_groups[tier])),
            }
            for tier in sorted(tier_groups.keys())
        },
    }
    with open(os.path.join(OUT_DIR, "split_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nOutput written to {OUT_DIR}/")
    print(f"  train.tsv, train.wrd, train.cluster_counts")
    print(f"  test.tsv, test.wrd, test.cluster_counts")
    print(f"  dict.wrd.txt, split_metadata.json")


if __name__ == "__main__":
    main()
