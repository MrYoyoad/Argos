#!/usr/bin/env python3
"""
Prepare context-aware evaluation batches for LLM-as-a-Judge re-evaluation.

Same structure as prepare_llm_eval_batches.py but with a different header
instruction. The ref+hyp format is identical — context comes from the judge's
own reasoning about the domain/topic, not from explicit labels.

Uses the SAME 30 duplicate pairs from the blind pass for cross-condition
reliability measurement.

Usage:
    python3 prepare_context_eval_batches.py
"""

import csv
import json
import os
import random

# Configuration — MUST match blind pass
SEED = 42
BATCH_SIZE = 100
N_DUPLICATES = 30
INPUT_CSV = "/home/ubuntu/docs/evaluation/intelligibility/intelligibility_scores.csv"
BLIND_INDEX = "/home/ubuntu/docs/evaluation/llm_judge/batch_index.json"
OUTPUT_DIR = "/home/ubuntu/docs/evaluation/llm_judge/context_eval"
BATCHES_DIR = os.path.join(OUTPUT_DIR, "batches")
MIN_HYP_WORDS_FOR_SHORT = 3


def load_data(csv_path):
    with open(csv_path, "r") as f:
        return list(csv.DictReader(f))


def auto_classify(rows):
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


def get_blind_duplicate_utt_ids(blind_index_path):
    """Extract the 30 duplicate utt_ids from the blind pass batch_index.json."""
    with open(blind_index_path, "r") as f:
        idx = json.load(f)
    dup_ids = set()
    for batch_key, entries in idx.items():
        for e in entries:
            if e.get("is_duplicate"):
                dup_ids.add(e["utt_id"])
    return dup_ids


def select_duplicates_matching_blind(rows, blind_dup_ids):
    """Select the same duplicate rows as the blind pass."""
    duplicates = []
    for row in rows:
        if row["utt_id"] in blind_dup_ids:
            duplicates.append(row)
    return duplicates


def create_batches(rows, duplicates, batch_size):
    rng = random.Random(SEED)
    main_items = [(r["utt_id"], r["ref"].strip(), r["hyp"].strip(), False) for r in rows]
    rng.shuffle(main_items)

    batches = []
    for i in range(0, len(main_items), batch_size):
        batches.append(list(main_items[i : i + batch_size]))

    dup_items = [(r["utt_id"], r["ref"].strip(), r["hyp"].strip(), True) for r in duplicates]

    rng2 = random.Random(SEED + 2)
    for dup_item in dup_items:
        dup_utt_id = dup_item[0]
        original_batch_idx = None
        for bi, batch in enumerate(batches):
            if any(item[0] == dup_utt_id for item in batch):
                original_batch_idx = bi
                break
        candidates = [i for i in range(len(batches)) if i != original_batch_idx]
        if candidates:
            target_batch = rng2.choice(candidates)
            insert_pos = rng2.randint(0, len(batches[target_batch]))
            batches[target_batch].insert(insert_pos, dup_item)

    return batches


def write_batch_files(batches, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    n_batches = len(batches)

    for bi, batch in enumerate(batches):
        batch_num = bi + 1
        filename = f"context_batch_{batch_num:02d}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            f.write(
                f"CONTEXT-AWARE EVALUATION | BATCH {batch_num:02d}/{n_batches} | "
                f"{len(batch)} pairs\n"
            )
            f.write(
                "Consider the likely topic/domain of each reference. Judge whether a viewer\n"
                "with that domain context would understand the hypothesis.\n"
                "Y=meaning conveyed, P=partial (annotate: P:preserved/-lost), N=meaning lost\n"
            )
            f.write("---\n")
            for idx, (utt_id, ref, hyp, is_dup) in enumerate(batch):
                f.write(f"{idx + 1:03d}|{ref}|{hyp}\n")

        print(f"  Wrote {filepath} ({len(batch)} pairs)")


def write_batch_index(batches, output_dir):
    index = {}
    for bi, batch in enumerate(batches):
        batch_num = bi + 1
        batch_key = f"context_batch_{batch_num:02d}"
        index[batch_key] = []
        for idx, (utt_id, ref, hyp, is_dup) in enumerate(batch):
            index[batch_key].append(
                {"index": idx + 1, "utt_id": utt_id, "is_duplicate": is_dup}
            )

    filepath = os.path.join(output_dir, "context_batch_index.json")
    with open(filepath, "w") as f:
        json.dump(index, f, indent=2)
    print(f"  Wrote {filepath}")


def write_auto_judgments(auto_n, output_dir):
    filepath = os.path.join(output_dir, "context_auto_judgments.csv")
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["utt_id", "judgment", "reason"])
        for utt_id, reason in auto_n:
            writer.writerow([utt_id, "N", reason])
    print(f"  Wrote {filepath} ({len(auto_n)} auto-N)")


def main():
    print("=" * 60)
    print("Context-Aware LLM-as-a-Judge Batch Preparation")
    print("=" * 60)

    print(f"\nLoading data from {INPUT_CSV}...")
    rows = load_data(INPUT_CSV)
    print(f"  Loaded {len(rows)} rows")

    print("\nAuto-classifying trivial pairs...")
    auto_n, remaining = auto_classify(rows)
    print(f"  Auto-N: {len(auto_n)}")
    print(f"  Remaining for judgment: {len(remaining)}")

    print(f"\nLoading blind-pass duplicate IDs from {BLIND_INDEX}...")
    blind_dup_ids = get_blind_duplicate_utt_ids(BLIND_INDEX)
    print(f"  Found {len(blind_dup_ids)} duplicate utt_ids from blind pass")

    duplicates = select_duplicates_matching_blind(remaining, blind_dup_ids)
    print(f"  Matched {len(duplicates)} duplicates in remaining data")

    print(f"\nCreating batches (target size: {BATCH_SIZE})...")
    batches = create_batches(remaining, duplicates, BATCH_SIZE)
    total_items = sum(len(b) for b in batches)
    print(f"  Created {len(batches)} batches, {total_items} total items")
    for bi, batch in enumerate(batches):
        n_dups = sum(1 for item in batch if item[3])
        print(f"    Batch {bi+1:02d}: {len(batch)} pairs ({n_dups} duplicates)")

    print(f"\nWriting batch files to {BATCHES_DIR}/...")
    write_batch_files(batches, BATCHES_DIR)

    print(f"\nWriting batch index...")
    write_batch_index(batches, OUTPUT_DIR)

    print(f"\nWriting auto-judgments...")
    write_auto_judgments(auto_n, OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total segments: {len(rows)}")
    print(f"  Auto-classified N: {len(auto_n)}")
    print(f"  To judge manually: {len(remaining)}")
    print(f"  Duplicates (same as blind): {len(duplicates)}")
    print(f"  Total batch items: {total_items}")
    print(f"  Number of batches: {len(batches)}")


if __name__ == "__main__":
    main()
