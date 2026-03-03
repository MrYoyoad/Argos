#!/usr/bin/env python3
"""
Analyze LLM-as-a-Judge results across fine-tuning experiments.

Merges judgment files from multiple experiments, computes per-experiment
Y/P/N rates, agreement with IS scores, and cross-experiment comparison.

Usage:
    python3 analyze_finetune_llm_eval.py \
        --experiments Baseline=/path/to/baseline/llm_judge \
                      ExpA_r16=/path/to/expa/llm_judge \
                      ExpB_r64=/path/to/expb/llm_judge \
        --out_dir /path/to/output
"""

import argparse
import csv
import json
import os
import re
from collections import Counter


def load_batch_index(judge_dir):
    """Load batch_index.json -> dict mapping utt_id -> (batch, index)."""
    index_file = os.path.join(judge_dir, "batch_index.json")
    if not os.path.exists(index_file):
        return {}
    with open(index_file) as f:
        index = json.load(f)

    utt_map = {}
    for batch_key, items in index.items():
        for item in items:
            utt_map[item["utt_id"]] = (batch_key, item["index"])
    return utt_map


def parse_judgment_line(line):
    """Parse '001,Y' or '001,P:key+struct/-sem' into (index, code, raw)."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.split(",", 1)
    if len(parts) < 2:
        return None

    try:
        idx = int(parts[0])
    except ValueError:
        return None

    raw = parts[1].strip()
    code = raw[0] if raw else "?"

    return (idx, code, raw)


def load_judgments(judge_dir):
    """Load all judgment files -> dict mapping utt_id -> (code, raw)."""
    judgments = {}

    # Load batch index
    utt_map = load_batch_index(judge_dir)
    index_file = os.path.join(judge_dir, "batch_index.json")
    if os.path.exists(index_file):
        with open(index_file) as f:
            batch_index = json.load(f)
    else:
        batch_index = {}

    # Load judgment files
    judgments_dir = os.path.join(judge_dir, "judgments")
    if not os.path.exists(judgments_dir):
        return judgments

    for filename in sorted(os.listdir(judgments_dir)):
        if not filename.endswith("_judgments.txt"):
            continue

        batch_key = filename.replace("_judgments.txt", "")
        batch_items = batch_index.get(batch_key, [])
        idx_to_utt = {item["index"]: item["utt_id"] for item in batch_items}

        filepath = os.path.join(judgments_dir, filename)
        with open(filepath) as f:
            for line in f:
                parsed = parse_judgment_line(line)
                if parsed is None:
                    continue
                idx, code, raw = parsed
                utt_id = idx_to_utt.get(idx)
                if utt_id:
                    judgments[utt_id] = (code, raw)

    # Load auto-judgments
    auto_file = os.path.join(judge_dir, "auto_judgments.csv")
    if os.path.exists(auto_file):
        with open(auto_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                judgments[row["utt_id"]] = (row["judgment"], row["judgment"])

    return judgments


def load_is_scores(judge_dir):
    """Try to load IS scores from nearby intelligibility dir."""
    # Look for intelligibility_scores.csv in parent or sibling dirs
    parent = os.path.dirname(judge_dir)
    candidates = [
        os.path.join(parent, "intelligibility", "intelligibility_scores.csv"),
        os.path.join(parent, "..", "intelligibility", "intelligibility_scores.csv"),
    ]
    for path in candidates:
        if os.path.exists(path):
            scores = {}
            with open(path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    scores[row["utt_id"]] = {
                        "is_score": float(row.get("intelligibility_score", 0)),
                        "tier": int(row.get("intelligibility_tier", 0)),
                    }
            return scores
    return {}


def compute_experiment_stats(judgments):
    """Compute Y/P/N distribution for one experiment."""
    counts = Counter(code for code, raw in judgments.values())
    total = sum(counts.values())

    return {
        "total": total,
        "Y": counts.get("Y", 0),
        "P": counts.get("P", 0),
        "N": counts.get("N", 0),
        "Y_pct": 100 * counts.get("Y", 0) / total if total > 0 else 0,
        "P_pct": 100 * counts.get("P", 0) / total if total > 0 else 0,
        "N_pct": 100 * counts.get("N", 0) / total if total > 0 else 0,
        "YP_pct": 100 * (counts.get("Y", 0) + counts.get("P", 0)) / total if total > 0 else 0,
    }


def compute_agreement(judgments_a, judgments_b):
    """Compute agreement between two sets of judgments on shared utt_ids."""
    shared = set(judgments_a.keys()) & set(judgments_b.keys())
    if not shared:
        return {"n": 0}

    exact = sum(1 for uid in shared if judgments_a[uid][0] == judgments_b[uid][0])
    # Lenient: Y+P vs N
    lenient = sum(
        1
        for uid in shared
        if (judgments_a[uid][0] in "YP") == (judgments_b[uid][0] in "YP")
    )

    return {
        "n": len(shared),
        "exact_agreement": exact / len(shared) if shared else 0,
        "lenient_agreement": lenient / len(shared) if shared else 0,
    }


def write_comparison_report(experiments, out_dir):
    """Generate markdown comparison report."""
    lines = []
    lines.append("# Claude-as-Judge: Fine-Tuning Experiment Comparison")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("Claude Opus 4.6 evaluated hypothesis-reference pairs from each experiment")
    lines.append("using the same 3-level protocol as the baseline study:")
    lines.append("- **Y**: Meaning clearly conveyed")
    lines.append("- **P**: Partial — some meaning preserved, key info lost/distorted")
    lines.append("- **N**: Wrong topic, hallucination, empty, or misleading")
    lines.append("")

    # Summary table
    lines.append("## Judgment Distribution by Experiment")
    lines.append("")
    lines.append("| Experiment | Total | Y | P | N | Y% | P% | N% | Y+P% |")
    lines.append("|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    for label, data in experiments.items():
        stats = data["stats"]
        lines.append(
            f"| {label} | {stats['total']} | {stats['Y']} | {stats['P']} | {stats['N']} | "
            f"{stats['Y_pct']:.1f} | {stats['P_pct']:.1f} | {stats['N_pct']:.1f} | {stats['YP_pct']:.1f} |"
        )
    lines.append("")

    # Per-segment comparison (if multiple experiments share utt_ids)
    exp_labels = list(experiments.keys())
    if len(exp_labels) >= 2:
        lines.append("## Cross-Experiment Agreement")
        lines.append("")
        lines.append("| Pair | Shared | Exact Agree | Lenient Agree |")
        lines.append("|------|:---:|:---:|:---:|")

        for i, lab_a in enumerate(exp_labels):
            for lab_b in exp_labels[i + 1 :]:
                agreement = compute_agreement(
                    experiments[lab_a]["judgments"], experiments[lab_b]["judgments"]
                )
                if agreement["n"] > 0:
                    lines.append(
                        f"| {lab_a} vs {lab_b} | {agreement['n']} | "
                        f"{agreement['exact_agreement']:.1%} | {agreement['lenient_agreement']:.1%} |"
                    )
        lines.append("")

        # Per-segment movement analysis
        lines.append("## Per-Segment Movement Analysis")
        lines.append("")
        lines.append("How did individual segments change between experiments?")
        lines.append("")

        for i, lab_a in enumerate(exp_labels):
            for lab_b in exp_labels[i + 1 :]:
                ja = experiments[lab_a]["judgments"]
                jb = experiments[lab_b]["judgments"]
                shared = set(ja.keys()) & set(jb.keys())
                if not shared:
                    continue

                # Count transitions
                transitions = Counter()
                for uid in shared:
                    transitions[f"{ja[uid][0]}→{jb[uid][0]}"] += 1

                lines.append(f"### {lab_a} → {lab_b}")
                lines.append("")
                lines.append("| Transition | Count | % | Interpretation |")
                lines.append("|-----------|:---:|:---:|---------------|")

                interp = {
                    "Y→Y": "stable success",
                    "Y→P": "degraded",
                    "Y→N": "broken",
                    "P→Y": "improved to success",
                    "P→P": "stable partial",
                    "P→N": "degraded",
                    "N→Y": "recovered",
                    "N→P": "improved to partial",
                    "N→N": "stable failure",
                }

                for trans in ["Y→Y", "Y→P", "Y→N", "P→Y", "P→P", "P→N", "N→Y", "N→P", "N→N"]:
                    count = transitions.get(trans, 0)
                    pct = 100 * count / len(shared) if shared else 0
                    lines.append(f"| {trans} | {count} | {pct:.1f}% | {interp.get(trans, '')} |")
                lines.append("")

                # Net improvement
                improved = transitions.get("N→Y", 0) + transitions.get("N→P", 0) + transitions.get("P→Y", 0)
                degraded = transitions.get("Y→N", 0) + transitions.get("Y→P", 0) + transitions.get("P→N", 0)
                net = improved - degraded
                lines.append(f"**Net movement**: {improved} improved, {degraded} degraded, net = {'+' if net >= 0 else ''}{net}")
                lines.append("")

    # Conclusions
    lines.append("## Conclusions")
    lines.append("")

    if len(exp_labels) >= 2:
        best_label = max(experiments.keys(), key=lambda k: experiments[k]["stats"]["Y_pct"])
        best_yp = max(experiments.keys(), key=lambda k: experiments[k]["stats"]["YP_pct"])
        lines.append(f"- **Highest Y% (strict success)**: {best_label} ({experiments[best_label]['stats']['Y_pct']:.1f}%)")
        lines.append(f"- **Highest Y+P% (any useful output)**: {best_yp} ({experiments[best_yp]['stats']['YP_pct']:.1f}%)")
    lines.append("")

    report_path = os.path.join(out_dir, "finetune_llm_judge_comparison.md")
    with open(report_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Report: {report_path}")


def write_comparison_csv(experiments, out_dir):
    """Write CSV with per-experiment stats."""
    csv_path = os.path.join(out_dir, "finetune_llm_judge_comparison.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["experiment", "total", "Y", "P", "N", "Y_pct", "P_pct", "N_pct", "YP_pct"],
        )
        writer.writeheader()
        for label, data in experiments.items():
            row = {"experiment": label}
            row.update(data["stats"])
            writer.writerow(row)
    print(f"CSV: {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze finetune LLM-as-Judge results")
    parser.add_argument(
        "--experiments",
        nargs="+",
        required=True,
        help="Label=dir pairs, e.g. Baseline=/path/to/llm_judge",
    )
    parser.add_argument("--out_dir", required=True, help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    experiments = {}
    for exp_arg in args.experiments:
        label, judge_dir = exp_arg.split("=", 1)
        print(f"\nLoading {label} from {judge_dir}...")
        judgments = load_judgments(judge_dir)
        stats = compute_experiment_stats(judgments)
        print(f"  {stats['total']} segments: Y={stats['Y']} P={stats['P']} N={stats['N']}")
        experiments[label] = {"judgments": judgments, "stats": stats, "dir": judge_dir}

    write_comparison_csv(experiments, args.out_dir)
    write_comparison_report(experiments, args.out_dir)
    print("\nDone!")


if __name__ == "__main__":
    main()
