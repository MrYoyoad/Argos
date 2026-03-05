#!/usr/bin/env python3
"""
Generate a comprehensive comparison report from fine-tuning evaluation sweeps.

Reads intelligibility_summary.json from multiple eval directories and produces:
  - A comparison CSV with all metrics side-by-side
  - A markdown report with analysis

Usage:
    python3 scripts/generate_finetune_comparison.py \
        --results baseline=/path/to/baseline/eval_sweep \
                  ExpA_r16=/path/to/expA/eval_sweep \
                  ExpB_r64=/path/to/expB/eval_sweep \
        --out_dir docs/finetuning/experiments
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional


def load_summary(summary_path: Path) -> Optional[dict]:
    """Load an intelligibility_summary.json file."""
    if not summary_path.exists():
        return None
    with open(summary_path) as f:
        return json.load(f)


def extract_metrics(summary: dict) -> dict:
    """Extract key metrics from an IS summary."""
    if summary is None:
        return {}

    n = summary.get("n_segments", 0)
    n_empty = summary.get("n_empty_hyp", 0)
    n_nonempty = n - n_empty

    # Tier distribution
    dist = summary.get("tier_distribution", {})

    # Failure modes
    fm = summary.get("failure_modes", {})
    hall_count = fm.get("hallucination", {}).get("count", 0)
    hall_rate = (hall_count / n_nonempty * 100) if n_nonempty > 0 else 0

    # Signal stats
    ss = summary.get("signal_stats", {})

    return {
        "n_segments": n,
        "n_empty": n_empty,
        "empty_pct": (n_empty / n * 100) if n > 0 else 0,
        "mean_is": summary.get("mean_is", None),
        "median_is": summary.get("median_is", None),
        "std_is": summary.get("std_is", None),
        "properly_captured_pct": summary.get("properly_captured_pct", None),
        "mean_wer": _invert_signal(ss.get("inverse_wer", {}).get("mean")),
        "mean_wwer": _invert_signal(ss.get("inverse_wwer", {}).get("mean")),
        "mean_nea_f1": _scale_signal(ss.get("nea_f1", {}).get("mean")),
        "mean_semantic_sim": ss.get("semantic_similarity", {}).get("mean"),
        "mean_phonetic_sim": ss.get("phonetic_similarity", {}).get("mean"),
        "mean_length_ratio": ss.get("length_ratio", {}).get("mean"),
        "hallucination_count": hall_count,
        "hallucination_rate": hall_rate,
        "tier_5_pct": dist.get("5_excellent", {}).get("pct", 0),
        "tier_4_pct": dist.get("4_good", {}).get("pct", 0),
        "tier_3_pct": dist.get("3_fair", {}).get("pct", 0),
        "tier_2_pct": dist.get("2_poor", {}).get("pct", 0),
        "tier_1_pct": dist.get("1_failed", {}).get("pct", 0),
        "tier_5_n": dist.get("5_excellent", {}).get("count", 0),
        "tier_4_n": dist.get("4_good", {}).get("count", 0),
        "tier_3_n": dist.get("3_fair", {}).get("count", 0),
        "tier_2_n": dist.get("2_poor", {}).get("count", 0),
        "tier_1_n": dist.get("1_failed", {}).get("count", 0),
    }


def _invert_signal(val) -> Optional[float]:
    """Convert inverse WER signal (0-5 scale) back to WER percentage."""
    if val is None:
        return None
    # The IS engine scales: inv_wer = max(0, 1 - wer/100) * 5
    # So wer = (1 - val/5) * 100
    return round((1 - val / 5) * 100, 1)


def _scale_signal(val) -> Optional[float]:
    """Convert NEA F1 signal (0-5 scale) back to percentage."""
    if val is None:
        return None
    # nea_f1_signal = (nea_f1 / 100) * 5
    return round(val / 5 * 100, 1)


def find_configs(sweep_dir: Path) -> List[str]:
    """Find all config subdirectories in a sweep directory."""
    configs = []
    for d in sorted(sweep_dir.iterdir()):
        if d.is_dir() and (d / "intelligibility" / "intelligibility_summary.json").exists():
            configs.append(d.name)
    # Also check if the sweep_dir itself has direct results (non-sweep eval)
    if (sweep_dir / "intelligibility" / "intelligibility_summary.json").exists():
        configs.insert(0, ".")
    return configs


def generate_comparison_csv(
    results: Dict[str, Path], out_path: Path
) -> List[dict]:
    """Generate a CSV comparing all experiments and configs."""
    rows = []

    for label, sweep_dir in results.items():
        sweep_dir = Path(sweep_dir)
        configs = find_configs(sweep_dir)

        for config in configs:
            if config == ".":
                summary_path = sweep_dir / "intelligibility" / "intelligibility_summary.json"
                config_label = "default"
            else:
                summary_path = sweep_dir / config / "intelligibility" / "intelligibility_summary.json"
                config_label = config

            summary = load_summary(summary_path)
            metrics = extract_metrics(summary)

            row = {"experiment": label, "decode_config": config_label}
            row.update(metrics)
            rows.append(row)

    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return rows


def fmt(val, suffix="", decimals=1) -> str:
    """Format a value for markdown display."""
    if val is None:
        return "_pending_"
    if isinstance(val, float):
        return f"{val:.{decimals}f}{suffix}"
    return f"{val}{suffix}"


def find_best(rows: List[dict], metric: str, lower_is_better: bool = False) -> str:
    """Find the experiment with the best value for a metric."""
    valid = [(r, r.get(metric)) for r in rows if r.get(metric) is not None]
    if not valid:
        return "N/A"
    if lower_is_better:
        best = min(valid, key=lambda x: x[1])
    else:
        best = max(valid, key=lambda x: x[1])
    return f"{best[0]['experiment']} ({best[0]['decode_config']})"


def generate_markdown_report(rows: List[dict], out_path: Path) -> None:
    """Generate a markdown comparison report."""
    # Group by decode_config=default for the main comparison
    default_rows = [r for r in rows if r["decode_config"] == "default"]
    all_configs = sorted(set(r["decode_config"] for r in rows))

    lines = []
    lines.append("# Fine-Tuning Comparison Report")
    lines.append("")
    lines.append("**Date**: March 2026")
    lines.append("**GPU**: Tesla T4 (16GB VRAM)")
    lines.append("**Dataset**: 1,273 train / 224 val segments (AVSpeech YouTube, stratified by IS tier)")
    lines.append("**Encoder**: Frozen throughout")
    lines.append("")

    # Main comparison (default decode params)
    lines.append("## Default Decode Parameters (beam=20, lenpen=0)")
    lines.append("")
    lines.append("| Metric | " + " | ".join(r["experiment"] for r in default_rows) + " | Best |")
    lines.append("|--------|" + "|".join("---" for _ in default_rows) + "|------|")

    metrics_table = [
        ("Mean IS (0-5)", "mean_is", "", False),
        ("Median IS", "median_is", "", False),
        ("Properly Captured (%)", "properly_captured_pct", "%", False),
        ("WER (%)", "mean_wer", "%", True),
        ("WWER (%)", "mean_wwer", "%", True),
        ("NEA F1 (%)", "mean_nea_f1", "%", False),
        ("Hallucination Rate (%)", "hallucination_rate", "%", True),
        ("Empty Output (%)", "empty_pct", "%", True),
    ]

    for label, key, suffix, lower_better in metrics_table:
        vals = " | ".join(fmt(r.get(key), suffix) for r in default_rows)
        best = find_best(default_rows, key, lower_better)
        lines.append(f"| **{label}** | {vals} | {best} |")

    lines.append("")

    # Tier distribution
    lines.append("## IS Tier Distribution (Default Decode)")
    lines.append("")
    lines.append("| Tier | " + " | ".join(r["experiment"] for r in default_rows) + " |")
    lines.append("|------|" + "|".join("---" for _ in default_rows) + "|")

    tiers = [
        ("5 — Excellent (4.0-5.0)", "tier_5"),
        ("4 — Good (3.0-3.99)", "tier_4"),
        ("3 — Fair (2.0-2.99)", "tier_3"),
        ("2 — Poor (1.0-1.99)", "tier_2"),
        ("1 — Failed (0.0-0.99)", "tier_1"),
    ]

    for tier_label, prefix in tiers:
        vals = " | ".join(
            f"{fmt(r.get(f'{prefix}_pct'), '%')} ({r.get(f'{prefix}_n', '?')})"
            for r in default_rows
        )
        lines.append(f"| {tier_label} | {vals} |")

    lines.append("")

    # Hyperparameter sweep comparison (per experiment)
    if len(all_configs) > 1:
        lines.append("## Decode Hyperparameter Sweep")
        lines.append("")

        experiments = sorted(set(r["experiment"] for r in rows))
        for exp in experiments:
            exp_rows = [r for r in rows if r["experiment"] == exp]
            if len(exp_rows) <= 1:
                continue

            lines.append(f"### {exp}")
            lines.append("")
            lines.append("| Config | Mean IS | Properly Captured | WER | WWER | NEA F1 | Hallucination | Empty |")
            lines.append("|--------|---------|-------------------|-----|------|--------|---------------|-------|")

            for r in exp_rows:
                lines.append(
                    f"| {r['decode_config']} "
                    f"| {fmt(r.get('mean_is'))} "
                    f"| {fmt(r.get('properly_captured_pct'), '%')} "
                    f"| {fmt(r.get('mean_wer'), '%')} "
                    f"| {fmt(r.get('mean_wwer'), '%')} "
                    f"| {fmt(r.get('mean_nea_f1'), '%')} "
                    f"| {fmt(r.get('hallucination_rate'), '%')} "
                    f"| {fmt(r.get('empty_pct'), '%')} |"
                )

            lines.append("")

    # Analysis
    lines.append("## Analysis")
    lines.append("")

    if default_rows:
        # Find best overall
        best_is_row = max(
            (r for r in default_rows if r.get("mean_is") is not None),
            key=lambda r: r["mean_is"],
            default=None,
        )
        if best_is_row:
            lines.append(f"### Best Overall")
            lines.append(f"**{best_is_row['experiment']}** achieved the highest mean IS "
                         f"of {fmt(best_is_row.get('mean_is'))} with default decode parameters.")
            lines.append("")

        # Delta analysis
        if len(default_rows) >= 2:
            baseline = default_rows[0]
            lines.append("### Improvement Over Baseline")
            lines.append("")
            for r in default_rows[1:]:
                b_is = baseline.get("mean_is")
                r_is = r.get("mean_is")
                if b_is is not None and r_is is not None:
                    delta = r_is - b_is
                    direction = "improvement" if delta > 0 else "regression"
                    lines.append(f"- **{r['experiment']}**: IS {fmt(r_is)} "
                                 f"(Δ {delta:+.3f}, {direction})")
            lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    lines.append("_To be filled after reviewing results._")
    lines.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(
        description="Generate fine-tuning comparison report"
    )
    parser.add_argument(
        "--results",
        nargs="+",
        required=True,
        help="label=path pairs, e.g. Baseline=/path/to/sweep ExpA=/path/to/sweep",
    )
    parser.add_argument(
        "--out_dir",
        required=True,
        help="Output directory for comparison report",
    )
    args = parser.parse_args()

    # Parse label=path pairs
    results = {}
    for item in args.results:
        if "=" not in item:
            parser.error(f"Expected label=path format, got: {item}")
        label, path = item.split("=", 1)
        results[label] = Path(path)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate comparison CSV
    csv_path = out_dir / "finetune_comparison.csv"
    rows = generate_comparison_csv(results, csv_path)
    print(f"Comparison CSV: {csv_path} ({len(rows)} rows)")

    # Generate markdown report
    md_path = out_dir / "comparison_report.md"
    generate_markdown_report(rows, md_path)
    print(f"Markdown report: {md_path}")

    # Print summary table
    default_rows = [r for r in rows if r["decode_config"] == "default"]
    if default_rows:
        print("\n=== Quick Summary (Default Decode) ===\n")
        print(f"{'Experiment':<20} {'Mean IS':>8} {'Captured':>10} {'WER':>8} {'WWER':>8} {'NEA F1':>8}")
        print("-" * 72)
        for r in default_rows:
            print(
                f"{r['experiment']:<20} "
                f"{fmt(r.get('mean_is')):>8} "
                f"{fmt(r.get('properly_captured_pct'), '%'):>10} "
                f"{fmt(r.get('mean_wer'), '%'):>8} "
                f"{fmt(r.get('mean_wwer'), '%'):>8} "
                f"{fmt(r.get('mean_nea_f1'), '%'):>8}"
            )


if __name__ == "__main__":
    main()
