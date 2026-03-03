#!/usr/bin/env python3
"""
Prepare blind evaluation batches for LLM-as-a-Judge evaluation of
fine-tuning experiment outputs.

Takes a report.csv from any eval (Baseline/ExpA/ExpB × any decode config)
and produces batch files in the same format as the baseline LLM judge study.

The key difference from the baseline study: we evaluate the SAME 224 val
segments across different checkpoints/configs. This allows direct comparison
of Claude's Y/P/N judgments across experiments.

Usage:
    python3 prepare_finetune_llm_eval.py \
        --report_csv /path/to/report.csv \
        --out_dir /path/to/llm_judge_output \
        --label "ExpA_r16_default"
"""

import argparse
import csv
import json
import os
import random

SEED = 42
BATCH_SIZE = 100


def load_report(csv_path):
    """Load report.csv from eval pipeline."""
    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def auto_classify(rows):
    """Auto-classify empty/trivially short hypotheses as N."""
    auto_n = []
    remaining = []

    for row in rows:
        utt_id = row.get("utt_id", row.get("display_name", ""))
        ref = row.get("ref", "").strip()
        hyp = row.get("hyp", "").strip()
        ref_words = len(ref.split()) if ref else 0
        hyp_words = len(hyp.split()) if hyp else 0

        if not hyp or hyp_words == 0:
            auto_n.append((utt_id, "empty_hypothesis"))
        elif hyp_words < 3 and ref_words > 5:
            auto_n.append((utt_id, "trivially_short"))
        else:
            remaining.append(row)

    return auto_n, remaining


def create_batches(rows, batch_size):
    """Shuffle and split into batches. No duplicates needed — smaller dataset."""
    rng = random.Random(SEED)

    items = []
    for r in rows:
        utt_id = r.get("utt_id", r.get("display_name", ""))
        ref = r.get("ref", "").strip()
        hyp = r.get("hyp", "").strip()
        items.append((utt_id, ref, hyp))

    rng.shuffle(items)

    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i : i + batch_size])

    return batches


def write_batch_files(batches, output_dir, label):
    """Write batch files in the same pipe-delimited format as baseline study."""
    batches_dir = os.path.join(output_dir, "batches")
    os.makedirs(batches_dir, exist_ok=True)

    n_batches = len(batches)

    for bi, batch in enumerate(batches):
        batch_num = bi + 1
        filename = f"batch_{batch_num:02d}.txt"
        filepath = os.path.join(batches_dir, filename)

        with open(filepath, "w") as f:
            f.write(
                f"BATCH {batch_num:02d}/{n_batches} | {len(batch)} pairs | "
                f"{label} | "
                f"Y=meaning conveyed, P=partial (annotate: P:preserved/-lost), N=meaning lost\n"
            )
            f.write("---\n")
            for idx, (utt_id, ref, hyp) in enumerate(batch):
                f.write(f"{idx + 1:03d}|{ref}|{hyp}\n")

        print(f"  Wrote {filepath} ({len(batch)} pairs)")


def write_batch_index(batches, output_dir):
    """Write JSON mapping (batch, index) -> utt_id."""
    index = {}
    for bi, batch in enumerate(batches):
        batch_num = bi + 1
        batch_key = f"batch_{batch_num:02d}"
        index[batch_key] = []
        for idx, (utt_id, ref, hyp) in enumerate(batch):
            index[batch_key].append({"index": idx + 1, "utt_id": utt_id})

    filepath = os.path.join(output_dir, "batch_index.json")
    with open(filepath, "w") as f:
        json.dump(index, f, indent=2)
    print(f"  Wrote {filepath}")


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
    parser = argparse.ArgumentParser(
        description="Prepare LLM-as-Judge batches for finetune eval"
    )
    parser.add_argument("--report_csv", required=True, help="Path to report.csv")
    parser.add_argument("--out_dir", required=True, help="Output directory")
    parser.add_argument("--label", required=True, help="Experiment label")
    args = parser.parse_args()

    print("=" * 60)
    print(f"LLM-as-a-Judge Batch Prep: {args.label}")
    print("=" * 60)

    rows = load_report(args.report_csv)
    print(f"\nLoaded {len(rows)} segments from {args.report_csv}")

    auto_n, remaining = auto_classify(rows)
    print(f"Auto-N: {len(auto_n)} (empty/short)")
    print(f"For LLM judgment: {len(remaining)}")

    batches = create_batches(remaining, BATCH_SIZE)
    print(f"Created {len(batches)} batch(es)")

    os.makedirs(args.out_dir, exist_ok=True)
    write_batch_files(batches, args.out_dir, args.label)
    write_batch_index(batches, args.out_dir)
    write_auto_judgments(auto_n, args.out_dir)

    print(f"\nReady for Claude-as-Judge evaluation.")
    print(f"Total: {len(rows)} segments ({len(auto_n)} auto-N + {len(remaining)} to judge)")


if __name__ == "__main__":
    main()
