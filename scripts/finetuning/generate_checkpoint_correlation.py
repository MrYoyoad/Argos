#!/usr/bin/env python3
"""
Analyze correlation between validation accuracy and Intelligibility Score (IS)
across training checkpoints.

Reads IS results from checkpoint eval directories and training logs,
computes Pearson/Spearman correlation, and generates a report.

Usage:
    python3 scripts/generate_checkpoint_correlation.py \
        --expa_dir /home/ubuntu/finetune_output_r16/checkpoint_correlation \
        --expb_dir /home/ubuntu/finetune_output_r64/checkpoint_correlation \
        --expa_log /home/ubuntu/finetune_output_r16/hydra_train.log \
        --expb_log /home/ubuntu/finetune_output_r64/hydra_train.log \
        --out_dir /home/ubuntu/docs/finetuning
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path


def parse_training_log(log_path):
    """Extract per-epoch validation accuracy from hydra_train.log."""
    val_accs = {}  # update_num -> val_accuracy
    train_accs = {}  # update_num -> train_accuracy

    with open(log_path) as f:
        for line in f:
            idx = line.find("{")
            if idx < 0:
                continue
            try:
                d = json.loads(line[idx:])
            except json.JSONDecodeError:
                continue

            if "test_accuracy" in d:
                update = d.get("test_num_updates", d.get("num_updates"))
                if update:
                    val_accs[int(update)] = float(d["test_accuracy"])

            if "train_accuracy" in d:
                update = d.get("train_num_updates", d.get("num_updates"))
                if update:
                    train_accs[int(update)] = float(d["train_accuracy"])

    return val_accs, train_accs


def find_nearest_accuracy(accs, target_update):
    """Find the accuracy value for the nearest update to target_update."""
    if not accs:
        return None
    # Exact match first
    if target_update in accs:
        return accs[target_update]
    # Find nearest
    nearest = min(accs.keys(), key=lambda u: abs(u - target_update))
    return accs[nearest]


def load_is_results(base_dir, updates):
    """Load IS results from checkpoint eval directories."""
    results = []
    base = Path(base_dir)

    for update in updates:
        ckpt_dir = base / f"ckpt_{update}"
        summary_file = ckpt_dir / "intelligibility" / "intelligibility_summary.json"

        if not summary_file.exists():
            print(f"  WARNING: Missing {summary_file}", file=sys.stderr)
            continue

        with open(summary_file) as f:
            summary = json.load(f)

        results.append({
            "update": update,
            "mean_is": summary.get("mean_is"),
            "median_is": summary.get("median_is"),
            "properly_captured_pct": summary.get("properly_captured_pct"),
            "n_segments": summary.get("n_segments"),
            "n_empty_hyp": summary.get("n_empty_hyp"),
            "llm_context_recoverable_pct": summary.get("llm_context_recoverable_pct"),
            "tier_distribution": summary.get("tier_distribution", {}),
        })

    return results


def compute_correlation(x, y):
    """Compute Pearson and Spearman correlation coefficients."""
    n = len(x)
    if n < 3:
        return {"pearson_r": None, "spearman_r": None, "n": n}

    # Pearson
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = (sum((xi - mean_x) ** 2 for xi in x)) ** 0.5
    std_y = (sum((yi - mean_y) ** 2 for yi in y)) ** 0.5

    pearson_r = cov / (std_x * std_y) if std_x > 0 and std_y > 0 else None

    # Spearman (rank correlation)
    def rank(values):
        sorted_vals = sorted(enumerate(values), key=lambda x: x[1])
        ranks = [0.0] * n
        for rank_idx, (orig_idx, _) in enumerate(sorted_vals):
            ranks[orig_idx] = rank_idx + 1
        return ranks

    rank_x = rank(x)
    rank_y = rank(y)

    # Spearman = Pearson on ranks
    mean_rx = sum(rank_x) / n
    mean_ry = sum(rank_y) / n
    cov_r = sum((rx - mean_rx) * (ry - mean_ry) for rx, ry in zip(rank_x, rank_y))
    std_rx = (sum((rx - mean_rx) ** 2 for rx in rank_x)) ** 0.5
    std_ry = (sum((ry - mean_ry) ** 2 for ry in rank_y)) ** 0.5

    spearman_r = cov_r / (std_rx * std_ry) if std_rx > 0 and std_ry > 0 else None

    return {"pearson_r": pearson_r, "spearman_r": spearman_r, "n": n}


def process_experiment(label, corr_dir, log_path, updates):
    """Process one experiment: load IS results, match with val accuracy."""
    print(f"\nProcessing {label}...")

    # Load IS results
    is_results = load_is_results(corr_dir, updates)
    if not is_results:
        print(f"  ERROR: No IS results found in {corr_dir}")
        return None

    # Load training log
    val_accs, train_accs = parse_training_log(log_path)

    # Match val accuracy to each checkpoint
    rows = []
    for r in is_results:
        update = r["update"]
        val_acc = find_nearest_accuracy(val_accs, update)
        train_acc = find_nearest_accuracy(train_accs, update)

        row = {
            "experiment": label,
            "update": update,
            "val_accuracy": val_acc,
            "train_accuracy": train_acc,
            "mean_is": r["mean_is"],
            "median_is": r["median_is"],
            "properly_captured_pct": r["properly_captured_pct"],
            "n_empty_hyp": r["n_empty_hyp"],
            "llm_context_recoverable_pct": r["llm_context_recoverable_pct"],
        }

        # Add tier percentages
        for tier_key in ["5_excellent", "4_good", "3_fair", "2_poor", "1_failed"]:
            tier_info = r["tier_distribution"].get(tier_key, {})
            row[f"tier_{tier_key}_pct"] = tier_info.get("pct", 0)

        rows.append(row)
        print(f"  Update {update}: val_acc={val_acc:.2f}%, train_acc={train_acc:.2f}%, IS={r['mean_is']:.3f}")

    # Compute correlations
    valid_rows = [r for r in rows if r["val_accuracy"] is not None and r["mean_is"] is not None]
    if len(valid_rows) >= 3:
        val_accs_list = [r["val_accuracy"] for r in valid_rows]
        is_list = [r["mean_is"] for r in valid_rows]
        corr = compute_correlation(val_accs_list, is_list)
        print(f"  Correlation (val_acc vs IS): Pearson r={corr['pearson_r']:.3f}, Spearman r={corr['spearman_r']:.3f}")
    else:
        corr = {"pearson_r": None, "spearman_r": None, "n": len(valid_rows)}
        print(f"  WARNING: Only {len(valid_rows)} valid rows — not enough for correlation")

    # Find best checkpoint by IS
    best_by_is = max(rows, key=lambda r: r["mean_is"] or 0)
    best_by_acc = max(rows, key=lambda r: r["val_accuracy"] or 0)

    return {
        "label": label,
        "rows": rows,
        "correlation": corr,
        "best_by_is": best_by_is,
        "best_by_acc": best_by_acc,
    }


def write_csv(all_rows, out_path):
    """Write combined CSV with all experiments and checkpoints."""
    if not all_rows:
        return

    fieldnames = list(all_rows[0].keys())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nCSV written: {out_path}")


def write_report(experiments, out_path):
    """Generate markdown report with correlation analysis."""
    lines = []
    lines.append("# Checkpoint-vs-IS Correlation Analysis")
    lines.append("")
    lines.append("## Question")
    lines.append("")
    lines.append("Does the checkpoint with the highest **validation token accuracy** (fairseq's")
    lines.append("`best_checkpoint_metric: accuracy`) also produce the highest **Intelligibility Score**?")
    lines.append("")
    lines.append("If not, we may be evaluating the wrong checkpoint from our fine-tuning experiments.")
    lines.append("")

    for exp in experiments:
        if exp is None:
            continue

        label = exp["label"]
        rows = exp["rows"]
        corr = exp["correlation"]
        best_is = exp["best_by_is"]
        best_acc = exp["best_by_acc"]

        lines.append(f"## {label}")
        lines.append("")

        # Results table
        lines.append("| Update | Val Acc (%) | Train Acc (%) | Mean IS | Captured (%) | Empty Hyp |")
        lines.append("|--------|:---:|:---:|:---:|:---:|:---:|")
        for r in sorted(rows, key=lambda x: x["update"]):
            is_best_is = " **" if r["update"] == best_is["update"] else ""
            is_best_acc = " *" if r["update"] == best_acc["update"] else ""
            val_acc = f"{r['val_accuracy']:.2f}" if r["val_accuracy"] else "?"
            train_acc = f"{r['train_accuracy']:.2f}" if r["train_accuracy"] else "?"
            mean_is = f"{r['mean_is']:.3f}" if r["mean_is"] else "?"
            captured = f"{r['properly_captured_pct']:.1f}" if r["properly_captured_pct"] else "?"
            empty = r.get("n_empty_hyp", "?")
            marker = ""
            if r["update"] == best_is["update"] and r["update"] == best_acc["update"]:
                marker = " (best acc + IS)"
            elif r["update"] == best_is["update"]:
                marker = " (best IS)"
            elif r["update"] == best_acc["update"]:
                marker = " (best acc)"
            lines.append(f"| {r['update']}{marker} | {val_acc} | {train_acc} | {mean_is} | {captured} | {empty} |")
        lines.append("")

        # Tier distribution table
        lines.append("**IS Tier Distribution by Checkpoint:**")
        lines.append("")
        lines.append("| Update | Excellent | Good | Fair | Poor | Failed |")
        lines.append("|--------|:---:|:---:|:---:|:---:|:---:|")
        for r in sorted(rows, key=lambda x: x["update"]):
            t5 = f"{r.get('tier_5_excellent_pct', 0):.1f}%"
            t4 = f"{r.get('tier_4_good_pct', 0):.1f}%"
            t3 = f"{r.get('tier_3_fair_pct', 0):.1f}%"
            t2 = f"{r.get('tier_2_poor_pct', 0):.1f}%"
            t1 = f"{r.get('tier_1_failed_pct', 0):.1f}%"
            lines.append(f"| {r['update']} | {t5} | {t4} | {t3} | {t2} | {t1} |")
        lines.append("")

        # Correlation
        lines.append("**Correlation (Val Accuracy vs Mean IS):**")
        lines.append("")
        if corr["pearson_r"] is not None:
            lines.append(f"- Pearson r = {corr['pearson_r']:.3f}")
            lines.append(f"- Spearman r = {corr['spearman_r']:.3f}")
            lines.append(f"- N = {corr['n']} checkpoints")
            lines.append("")

            # Interpretation
            r_abs = abs(corr["pearson_r"])
            if r_abs > 0.9:
                strength = "very strong"
            elif r_abs > 0.7:
                strength = "strong"
            elif r_abs > 0.5:
                strength = "moderate"
            elif r_abs > 0.3:
                strength = "weak"
            else:
                strength = "negligible"

            direction = "positive" if corr["pearson_r"] > 0 else "negative"

            lines.append(f"Interpretation: **{strength} {direction} correlation** between validation accuracy and IS.")
            lines.append("")
        else:
            lines.append("- Not enough data points for correlation analysis")
            lines.append("")

        # Best checkpoint analysis
        if best_is["update"] == best_acc["update"]:
            lines.append(f"**Conclusion**: The best-accuracy checkpoint (update {best_acc['update']}) is ALSO the best IS checkpoint. "
                         f"`checkpoint_best.pt` is correctly chosen.")
        else:
            lines.append(f"**FINDING**: Best accuracy checkpoint (update {best_acc['update']}, "
                         f"acc={best_acc['val_accuracy']:.2f}%, IS={best_acc['mean_is']:.3f}) "
                         f"is NOT the best IS checkpoint!")
            lines.append(f"")
            lines.append(f"Best IS checkpoint is update {best_is['update']} "
                         f"(acc={best_is['val_accuracy']:.2f}%, IS={best_is['mean_is']:.3f}).")
            lines.append(f"IS difference: {best_is['mean_is'] - best_acc['mean_is']:.3f}")
            lines.append(f"")
            lines.append(f"This suggests that `checkpoint_best.pt` may not be optimal for downstream IS evaluation.")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Overall conclusions
    lines.append("## Overall Conclusions")
    lines.append("")

    all_agree = all(
        exp["best_by_is"]["update"] == exp["best_by_acc"]["update"]
        for exp in experiments if exp is not None
    )

    if all_agree:
        lines.append("Across all experiments, the checkpoint with the highest validation accuracy also")
        lines.append("produced the highest IS. **Token accuracy is a reliable proxy for IS** in this setting,")
        lines.append("and `checkpoint_best.pt` is correctly chosen.")
    else:
        disagreements = [
            exp["label"] for exp in experiments
            if exp is not None and exp["best_by_is"]["update"] != exp["best_by_acc"]["update"]
        ]
        lines.append(f"In {len(disagreements)} experiment(s) ({', '.join(disagreements)}), the best-accuracy")
        lines.append("checkpoint did NOT produce the highest IS. This means **token accuracy is not a")
        lines.append("reliable proxy for IS**, and future experiments should evaluate IS directly when")
        lines.append("selecting the best checkpoint.")
    lines.append("")

    # Correlation summary
    lines.append("**Correlation Summary:**")
    lines.append("")
    lines.append("| Experiment | Pearson r | Spearman r | Agreement? |")
    lines.append("|-----------|:---:|:---:|:---:|")
    for exp in experiments:
        if exp is None:
            continue
        pr = f"{exp['correlation']['pearson_r']:.3f}" if exp['correlation']['pearson_r'] else "N/A"
        sr = f"{exp['correlation']['spearman_r']:.3f}" if exp['correlation']['spearman_r'] else "N/A"
        agree = "Yes" if exp["best_by_is"]["update"] == exp["best_by_acc"]["update"] else "**No**"
        lines.append(f"| {exp['label']} | {pr} | {sr} | {agree} |")
    lines.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Report written: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Checkpoint-IS correlation analysis")
    parser.add_argument("--expa_dir", required=True, help="Exp A checkpoint correlation dir")
    parser.add_argument("--expb_dir", required=True, help="Exp B checkpoint correlation dir")
    parser.add_argument("--expa_log", required=True, help="Exp A hydra_train.log")
    parser.add_argument("--expb_log", required=True, help="Exp B hydra_train.log")
    parser.add_argument("--out_dir", required=True, help="Output directory for report and CSV")
    args = parser.parse_args()

    updates = [320, 1000, 1500, 2000, 3000]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Process both experiments
    exp_a = process_experiment("Exp A (r=16)", args.expa_dir, args.expa_log, updates)
    exp_b = process_experiment("Exp B (r=64)", args.expb_dir, args.expb_log, updates)

    experiments = [e for e in [exp_a, exp_b] if e is not None]

    if not experiments:
        print("ERROR: No experiments produced results")
        sys.exit(1)

    # Write CSV
    all_rows = []
    for exp in experiments:
        all_rows.extend(exp["rows"])

    csv_path = out_dir / "checkpoint_correlation.csv"
    write_csv(all_rows, csv_path)

    # Write report
    report_path = out_dir / "checkpoint_correlation_report.md"
    write_report(experiments, report_path)

    print("\nDone!")


if __name__ == "__main__":
    main()
