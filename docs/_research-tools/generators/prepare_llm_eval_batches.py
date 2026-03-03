#!/usr/bin/env python3
"""
Prepare blind evaluation batches for LLM-as-a-Judge evaluation.

Reads intelligibility_scores.csv, auto-classifies empty/trivial pairs,
shuffles remaining pairs, embeds duplicate pairs for reliability checking,
and writes batch files for Claude Code to evaluate.

Usage:
    python3 prepare_llm_eval_batches.py
"""

import csv
import json
import os
import random

# Configuration
SEED = 42
BATCH_SIZE = 100
N_DUPLICATES = 30  # duplicates for intra-rater reliability (6 per IS tier)
INPUT_CSV = "/home/ubuntu/docs/evaluation/intelligibility/intelligibility_scores.csv"
OUTPUT_DIR = "/home/ubuntu/docs/evaluation/llm_judge"
BATCHES_DIR = os.path.join(OUTPUT_DIR, "batches")
MIN_HYP_WORDS_FOR_SHORT = 3  # hyp with fewer words than this AND ref > 5 words = auto N


def load_data(csv_path):
    """Load all rows from intelligibility_scores.csv."""
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


def auto_classify(rows):
    """
    Auto-classify trivially judgeable pairs.
    Returns (auto_N, auto_Y, remaining) where auto_N/auto_Y are lists of
    (utt_id, reason) and remaining is list of row dicts.
    """
    auto_n = []
    remaining = []

    for row in rows:
        utt_id = row["utt_id"]
        ref = row["ref"].strip()
        hyp = row["hyp"].strip()
        ref_words = len(ref.split()) if ref else 0
        hyp_words = len(hyp.split()) if hyp else 0

        if not hyp or hyp_words == 0:
            auto_n.append((utt_id, "empty_hypothesis"))
        elif hyp_words < MIN_HYP_WORDS_FOR_SHORT and ref_words > 5:
            auto_n.append((utt_id, "trivially_short"))
        else:
            remaining.append(row)

    return auto_n, remaining


def select_duplicates(rows, n_per_tier=6):
    """
    Select pairs for duplication across batches (for intra-rater reliability).
    Selects n_per_tier from each IS tier (1-5).
    """
    by_tier = {str(t): [] for t in range(1, 6)}
    for row in rows:
        tier = row.get("intelligibility_tier", "0")
        if tier in by_tier:
            by_tier[tier].append(row)

    rng = random.Random(SEED + 1)  # separate seed for duplicate selection
    duplicates = []
    for tier in sorted(by_tier.keys()):
        pool = by_tier[tier]
        n = min(n_per_tier, len(pool))
        duplicates.extend(rng.sample(pool, n))

    return duplicates


def create_batches(rows, duplicates, batch_size):
    """
    Shuffle rows and split into batches.
    Duplicates are inserted into different batches at random positions.
    Returns list of batches, where each batch is a list of (utt_id, ref, hyp, is_duplicate).
    """
    rng = random.Random(SEED)

    # Build main list
    main_items = [(r["utt_id"], r["ref"].strip(), r["hyp"].strip(), False) for r in rows]
    rng.shuffle(main_items)

    # Split into batches
    batches = []
    for i in range(0, len(main_items), batch_size):
        batches.append(list(main_items[i : i + batch_size]))

    # Insert duplicates into different batches
    # For each duplicate, find which batch it's already in, then insert into a different batch
    dup_utt_ids = {r["utt_id"] for r in duplicates}
    dup_items = [(r["utt_id"], r["ref"].strip(), r["hyp"].strip(), True) for r in duplicates]

    rng2 = random.Random(SEED + 2)
    for dup_item in dup_items:
        dup_utt_id = dup_item[0]
        # Find which batch has the original
        original_batch_idx = None
        for bi, batch in enumerate(batches):
            if any(item[0] == dup_utt_id for item in batch):
                original_batch_idx = bi
                break

        # Pick a different batch
        candidates = [i for i in range(len(batches)) if i != original_batch_idx]
        if candidates:
            target_batch = rng2.choice(candidates)
            insert_pos = rng2.randint(0, len(batches[target_batch]))
            batches[target_batch].insert(insert_pos, dup_item)

    return batches


def write_batch_files(batches, output_dir):
    """Write batch files in the compact pipe-delimited format."""
    os.makedirs(output_dir, exist_ok=True)
    n_batches = len(batches)

    for bi, batch in enumerate(batches):
        batch_num = bi + 1
        filename = f"batch_{batch_num:02d}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            f.write(
                f"BATCH {batch_num:02d}/{n_batches} | {len(batch)} pairs | "
                f"Y=meaning conveyed, P=partial (annotate: P:preserved/-lost), N=meaning lost\n"
            )
            f.write("---\n")
            for idx, (utt_id, ref, hyp, is_dup) in enumerate(batch):
                f.write(f"{idx + 1:03d}|{ref}|{hyp}\n")

        print(f"  Wrote {filepath} ({len(batch)} pairs)")


def write_batch_index(batches, output_dir):
    """Write JSON mapping (batch, index) -> utt_id with duplicate flags."""
    index = {}
    for bi, batch in enumerate(batches):
        batch_num = bi + 1
        batch_key = f"batch_{batch_num:02d}"
        index[batch_key] = []
        for idx, (utt_id, ref, hyp, is_dup) in enumerate(batch):
            index[batch_key].append(
                {"index": idx + 1, "utt_id": utt_id, "is_duplicate": is_dup}
            )

    filepath = os.path.join(output_dir, "batch_index.json")
    with open(filepath, "w") as f:
        json.dump(index, f, indent=2)
    print(f"  Wrote {filepath}")
    return index


def write_auto_judgments(auto_n, output_dir):
    """Write CSV of auto-classified pairs."""
    filepath = os.path.join(output_dir, "auto_judgments.csv")
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["utt_id", "judgment", "reason"])
        for utt_id, reason in auto_n:
            writer.writerow([utt_id, "N", reason])
    print(f"  Wrote {filepath} ({len(auto_n)} auto-N)")


def main():
    print("=" * 60)
    print("LLM-as-a-Judge Batch Preparation")
    print("=" * 60)

    # Load data
    print(f"\nLoading data from {INPUT_CSV}...")
    rows = load_data(INPUT_CSV)
    print(f"  Loaded {len(rows)} rows")

    # Auto-classify
    print("\nAuto-classifying trivial pairs...")
    auto_n, remaining = auto_classify(rows)
    print(f"  Auto-N: {len(auto_n)} (empty/trivially short)")
    print(f"  Remaining for LLM judgment: {len(remaining)}")

    # Select duplicates for reliability
    print(f"\nSelecting {N_DUPLICATES} duplicates for intra-rater reliability...")
    duplicates = select_duplicates(remaining, n_per_tier=6)
    print(f"  Selected {len(duplicates)} duplicates across {len(set(r['intelligibility_tier'] for r in duplicates))} tiers")
    for tier in sorted(set(r["intelligibility_tier"] for r in duplicates)):
        count = sum(1 for r in duplicates if r["intelligibility_tier"] == tier)
        print(f"    Tier {tier}: {count} duplicates")

    # Create batches
    print(f"\nCreating batches (target size: {BATCH_SIZE})...")
    batches = create_batches(remaining, duplicates, BATCH_SIZE)
    total_items = sum(len(b) for b in batches)
    print(f"  Created {len(batches)} batches")
    print(f"  Total items (including {len(duplicates)} duplicates): {total_items}")
    for bi, batch in enumerate(batches):
        n_dups = sum(1 for item in batch if item[3])
        print(f"    Batch {bi+1:02d}: {len(batch)} pairs ({n_dups} duplicates)")

    # Write outputs
    print(f"\nWriting batch files to {BATCHES_DIR}/...")
    write_batch_files(batches, BATCHES_DIR)

    print(f"\nWriting batch index...")
    write_batch_index(batches, OUTPUT_DIR)

    print(f"\nWriting auto-judgments...")
    write_auto_judgments(auto_n, OUTPUT_DIR)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total segments: {len(rows)}")
    print(f"  Auto-classified N: {len(auto_n)}")
    print(f"  To judge manually: {len(remaining)}")
    print(f"  Duplicates embedded: {len(duplicates)}")
    print(f"  Total batch items: {total_items}")
    print(f"  Number of batches: {len(batches)}")
    print(f"\nReady for evaluation. Read each batch file and write judgments.")


if __name__ == "__main__":
    main()
