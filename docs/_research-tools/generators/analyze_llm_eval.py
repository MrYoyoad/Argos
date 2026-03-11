#!/usr/bin/env python3
"""
Analyze LLM-as-a-Judge evaluation results.

Merges judgment files with intelligibility_scores.csv and computes:
- Agreement with IS framework (confusion matrices, kappa, F1)
- Agreement with llm_context_prob heuristic
- Correlations with all continuous metrics
- Disagreement analysis with curated examples
- Intra-rater reliability on duplicate pairs
- Partial judgment tag analysis
- Gold standard capture rate

Usage:
    python3 analyze_llm_eval.py
"""

import csv
import json
import math
import os
import re
from collections import Counter, defaultdict

# Paths
BASE_DIR = "/home/ubuntu/docs/evaluation/llm_judge"
JUDGMENTS_DIR = os.path.join(BASE_DIR, "judgments")
BATCH_INDEX = os.path.join(BASE_DIR, "batch_index.json")
AUTO_JUDGMENTS = os.path.join(BASE_DIR, "auto_judgments.csv")
SCORES_CSV = "/home/ubuntu/docs/evaluation/intelligibility/intelligibility_scores.csv"
OUTPUT_CSV = os.path.join(BASE_DIR, "llm_judge_results.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "llm_judge_summary.json")
OUTPUT_MD = os.path.join(BASE_DIR, "llm_judge_analysis.md")
EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")


def load_scores():
    """Load intelligibility_scores.csv into dict keyed by utt_id."""
    scores = {}
    with open(SCORES_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores[row["utt_id"]] = row
    return scores


def load_batch_index():
    """Load batch_index.json."""
    with open(BATCH_INDEX, "r") as f:
        return json.load(f)


def parse_judgment(text):
    """Parse a judgment string into (code, preserved_tags, lost_tags).
    Returns (code, preserved_list, lost_list) where code is Y/P/N.
    """
    text = text.strip()
    if text == "Y":
        return ("Y", [], [])
    if text == "N":
        return ("N", [], [])
    if text.startswith("P:"):
        annotation = text[2:]
        preserved = []
        lost = []
        parts = annotation.split("/")
        if len(parts) >= 1:
            preserved = [t for t in parts[0].split("+") if t]
        for part in parts[1:]:
            lost.extend([t.lstrip("-") for t in part.split("-") if t])
        return ("P", preserved, lost)
    return (text, [], [])


def load_judgments(batch_index):
    """Load all judgment files, resolve to utt_ids.
    Returns dict: utt_id -> (code, preserved, lost)
    Also returns list of (utt_id, code, is_duplicate) for reliability.
    """
    judgments = {}
    all_entries = []  # for reliability analysis

    for batch_key in sorted(batch_index.keys()):
        batch_num = batch_key.split("_")[1]
        jfile = os.path.join(JUDGMENTS_DIR, f"batch_{batch_num}_judgments.txt")
        if not os.path.exists(jfile):
            print(f"  WARNING: {jfile} not found, skipping")
            continue

        # Parse judgment file
        jdata = {}
        with open(jfile, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Format: NNN,JUDGMENT
                idx_str, _, judgment_str = line.partition(",")
                try:
                    idx = int(idx_str.strip())
                except ValueError:
                    continue
                jdata[idx] = judgment_str.strip()

        # Map to utt_ids
        for entry in batch_index[batch_key]:
            idx = entry["index"]
            utt_id = entry["utt_id"]
            is_dup = entry["is_duplicate"]

            if idx in jdata:
                code, preserved, lost = parse_judgment(jdata[idx])
                all_entries.append((utt_id, code, preserved, lost, is_dup))
                if not is_dup:
                    judgments[utt_id] = (code, preserved, lost)
                elif utt_id not in judgments:
                    # Only use duplicate if we don't have original yet
                    judgments[utt_id] = (code, preserved, lost)

    # Load auto-judgments
    with open(AUTO_JUDGMENTS, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            utt_id = row["utt_id"]
            judgments[utt_id] = ("N", [], [])

    return judgments, all_entries


def compute_reliability(all_entries):
    """Compute intra-rater reliability on duplicate pairs."""
    # Group entries by utt_id
    by_utt = defaultdict(list)
    for utt_id, code, preserved, lost, is_dup in all_entries:
        by_utt[utt_id].append((code, is_dup))

    duplicated = {uid: codes for uid, codes in by_utt.items() if len(codes) >= 2}
    if not duplicated:
        return {"n_duplicates": 0, "exact_agreement": 0.0, "lenient_agreement": 0.0}

    exact = 0
    lenient = 0  # Y+P vs N
    total = len(duplicated)

    for uid, codes in duplicated.items():
        c1, c2 = codes[0][0], codes[1][0]
        if c1 == c2:
            exact += 1
        # Lenient: Y and P both count as "positive"
        pos = {"Y", "P"}
        if (c1 in pos) == (c2 in pos):
            lenient += 1

    return {
        "n_duplicates": total,
        "exact_agreement": round(exact / total, 3) if total > 0 else 0,
        "lenient_agreement": round(lenient / total, 3) if total > 0 else 0,
        "exact_count": exact,
        "lenient_count": lenient,
    }


def cohens_kappa(matrix_2x2):
    """Compute Cohen's kappa from a 2x2 confusion matrix [[a,b],[c,d]]."""
    a, b = matrix_2x2[0]
    c, d = matrix_2x2[1]
    n = a + b + c + d
    if n == 0:
        return 0.0
    po = (a + d) / n
    pe = ((a + b) * (a + c) + (c + d) * (b + d)) / (n * n)
    if pe == 1.0:
        return 1.0
    return round((po - pe) / (1 - pe), 4)


def pearson_r(xs, ys):
    """Compute Pearson correlation coefficient."""
    n = len(xs)
    if n < 3:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs) / n)
    sy = math.sqrt(sum((y - my) ** 2 for y in ys) / n)
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
    return round(cov / (sx * sy), 4)


def spearman_rho(xs, ys):
    """Compute Spearman rank correlation."""
    def rank(vals):
        indexed = sorted(enumerate(vals), key=lambda x: x[1])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(indexed):
            j = i
            while j < len(indexed) and indexed[j][1] == indexed[i][1]:
                j += 1
            avg_rank = (i + j - 1) / 2.0 + 1
            for k in range(i, j):
                ranks[indexed[k][0]] = avg_rank
            i = j
        return ranks

    rx = rank(xs)
    ry = rank(ys)
    return pearson_r(rx, ry)


def analyze_tags(judgments):
    """Analyze preserved/lost tag distributions for P judgments."""
    preserved_counts = Counter()
    lost_counts = Counter()
    profile_counts = Counter()
    total_p = 0

    for utt_id, (code, preserved, lost) in judgments.items():
        if code != "P":
            continue
        total_p += 1
        for tag in preserved:
            preserved_counts[tag] += 1
        for tag in lost:
            lost_counts[tag] += 1
        profile = f"P:{'+'.join(sorted(preserved))}/{'-'.join(sorted(lost))}"
        profile_counts[profile] += 1

    return {
        "total_p": total_p,
        "preserved_counts": dict(preserved_counts.most_common()),
        "lost_counts": dict(lost_counts.most_common()),
        "top_profiles": dict(profile_counts.most_common(15)),
    }


def build_merged_data(scores, judgments):
    """Merge scores with judgments. Returns list of merged row dicts."""
    merged = []
    for utt_id, score_row in scores.items():
        code = "MISSING"
        preserved = []
        lost = []
        if utt_id in judgments:
            code, preserved, lost = judgments[utt_id]
        judgment_full = code
        if code == "P" and preserved:
            judgment_full = f"P:{'+'.join(preserved)}/{'-'.join(lost)}"
        row = dict(score_row)
        row["llm_judge"] = code
        row["llm_judge_full"] = judgment_full
        row["llm_judge_numeric"] = 1.0 if code == "Y" else (0.5 if code == "P" else 0.0)
        merged.append(row)
    return merged


def compute_confusion_3x5(merged):
    """Compute 3x5 matrix: LLM (Y/P/N) x IS tier (1-5)."""
    matrix = [[0] * 5 for _ in range(3)]  # [Y/P/N][tier1-5]
    code_map = {"Y": 0, "P": 1, "N": 2}
    for row in merged:
        code = row["llm_judge"]
        tier = int(row.get("intelligibility_tier", 0))
        if code in code_map and 1 <= tier <= 5:
            matrix[code_map[code]][tier - 1] += 1
    return matrix


def select_examples(merged, category, n=10):
    """Select curated examples for a given disagreement category."""
    candidates = []
    for row in merged:
        code = row["llm_judge"]
        is_score = float(row.get("intelligibility_score", 0))
        llm_prob = float(row.get("llm_context_prob", 0))

        if category == "llm_yes_is_fail":
            if code == "Y" and is_score < 3.0:
                candidates.append((abs(is_score - 3.0), row))
        elif category == "llm_no_is_pass":
            if code == "N" and is_score >= 3.0:
                candidates.append((is_score, row))
        elif category == "partial_showcase":
            if code == "P":
                candidates.append((abs(is_score - 2.5), row))
        elif category == "agreement_yes":
            if code == "Y" and is_score >= 4.0:
                candidates.append((is_score, row))
        elif category == "agreement_no":
            if code == "N" and is_score < 1.5:
                candidates.append((1.0 / max(is_score, 0.01), row))

    candidates.sort(key=lambda x: -x[0])
    return [c[1] for c in candidates[:n]]


def format_example(row, idx):
    """Format a single example for markdown output."""
    lines = []
    lines.append(f"### Example {idx}")
    lines.append(f"- **REF:** {row.get('ref', 'N/A')}")
    lines.append(f"- **HYP:** {row.get('hyp', 'N/A')}")
    lines.append(f"- **LLM Judge:** {row.get('llm_judge_full', 'N/A')}")
    lines.append(f"- **IS:** {row.get('intelligibility_score', 'N/A')} ({row.get('intelligibility_label', '')})")
    lines.append(f"- **llm_context_prob:** {row.get('llm_context_prob', 'N/A')} ({row.get('llm_context_reason', '')})")
    lines.append(f"- **WER:** {row.get('wer_%', 'N/A')}%")
    lines.append("")
    return "\n".join(lines)


def write_examples(merged):
    """Write curated example files."""
    os.makedirs(EXAMPLES_DIR, exist_ok=True)

    # LLM=Y but IS<3.0
    examples_yes_fail = select_examples(merged, "llm_yes_is_fail", 10)
    with open(os.path.join(EXAMPLES_DIR, "disagreement_llm_yes_is_fail.md"), "w") as f:
        f.write("# LLM Judge Says YES, but IS < 3.0\n\n")
        f.write("These segments convey the reference meaning despite poor metric scores.\n")
        f.write("They validate the 'LLM salvage' hypothesis.\n\n")
        for i, row in enumerate(examples_yes_fail, 1):
            f.write(format_example(row, i))

    # LLM=N but IS>=3.0
    examples_no_pass = select_examples(merged, "llm_no_is_pass", 10)
    with open(os.path.join(EXAMPLES_DIR, "disagreement_llm_no_is_pass.md"), "w") as f:
        f.write("# LLM Judge Says NO, but IS >= 3.0\n\n")
        f.write("These segments have good metric scores but fail to convey meaning.\n")
        f.write("They represent IS false positives.\n\n")
        for i, row in enumerate(examples_no_pass, 1):
            f.write(format_example(row, i))

    # Partial showcase
    examples_partial = select_examples(merged, "partial_showcase", 10)
    with open(os.path.join(EXAMPLES_DIR, "partial_judgment_showcase.md"), "w") as f:
        f.write("# Partial Judgment Showcase\n\n")
        f.write("These segments partially convey meaning. Annotations show what's preserved vs lost.\n\n")
        for i, row in enumerate(examples_partial, 1):
            f.write(format_example(row, i))

    # Agreement showcase
    examples_agree_y = select_examples(merged, "agreement_yes", 5)
    examples_agree_n = select_examples(merged, "agreement_no", 5)
    with open(os.path.join(EXAMPLES_DIR, "agreement_showcase.md"), "w") as f:
        f.write("# Agreement Showcase\n\n")
        f.write("## Strong YES Agreement (LLM=Y, IS >= 4.0)\n\n")
        for i, row in enumerate(examples_agree_y, 1):
            f.write(format_example(row, i))
        f.write("## Strong NO Agreement (LLM=N, IS < 1.5)\n\n")
        for i, row in enumerate(examples_agree_n, 1):
            f.write(format_example(row, i + 5))

    # JSON summary of all examples
    all_examples = {
        "llm_yes_is_fail": [
            {k: v for k, v in row.items() if k in
             ("utt_id", "ref", "hyp", "llm_judge", "llm_judge_full",
              "intelligibility_score", "intelligibility_tier", "intelligibility_label",
              "llm_context_prob", "wer_%", "semantic_sim")}
            for row in examples_yes_fail
        ],
        "llm_no_is_pass": [
            {k: v for k, v in row.items() if k in
             ("utt_id", "ref", "hyp", "llm_judge", "llm_judge_full",
              "intelligibility_score", "intelligibility_tier", "intelligibility_label",
              "llm_context_prob", "wer_%", "semantic_sim")}
            for row in examples_no_pass
        ],
        "partial_showcase": [
            {k: v for k, v in row.items() if k in
             ("utt_id", "ref", "hyp", "llm_judge", "llm_judge_full",
              "intelligibility_score", "intelligibility_tier", "intelligibility_label",
              "llm_context_prob", "wer_%", "semantic_sim")}
            for row in examples_partial
        ],
        "agreement_yes": [
            {k: v for k, v in row.items() if k in
             ("utt_id", "ref", "hyp", "llm_judge", "llm_judge_full",
              "intelligibility_score", "intelligibility_tier", "intelligibility_label",
              "llm_context_prob", "wer_%", "semantic_sim")}
            for row in examples_agree_y
        ],
        "agreement_no": [
            {k: v for k, v in row.items() if k in
             ("utt_id", "ref", "hyp", "llm_judge", "llm_judge_full",
              "intelligibility_score", "intelligibility_tier", "intelligibility_label",
              "llm_context_prob", "wer_%", "semantic_sim")}
            for row in examples_agree_n
        ],
    }
    with open(os.path.join(EXAMPLES_DIR, "examples_summary.json"), "w") as f:
        json.dump(all_examples, f, indent=2)

    return len(examples_yes_fail), len(examples_no_pass), len(examples_partial)


def write_results_csv(merged):
    """Write merged results CSV."""
    if not merged:
        return
    fieldnames = list(merged[0].keys())
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)


def main():
    print("=" * 60)
    print("LLM-as-a-Judge Analysis")
    print("=" * 60)

    # Load data
    print("\nLoading data...")
    scores = load_scores()
    print(f"  Loaded {len(scores)} score rows")

    batch_index = load_batch_index()
    judgments, all_entries = load_judgments(batch_index)
    print(f"  Loaded {len(judgments)} judgments (including auto-classified)")

    # Coverage check
    missing = [uid for uid in scores if uid not in judgments]
    print(f"  Missing judgments: {len(missing)}")

    # Merge
    print("\nMerging data...")
    merged = build_merged_data(scores, judgments)
    # Filter out MISSING
    n_missing = sum(1 for r in merged if r["llm_judge"] == "MISSING")
    print(f"  Merged: {len(merged)} rows ({n_missing} missing judgments)")

    # Distribution
    dist = Counter(r["llm_judge"] for r in merged)
    print(f"\nJudgment Distribution:")
    for code in ["Y", "P", "N", "MISSING"]:
        if code in dist:
            pct = dist[code] / len(merged) * 100
            print(f"  {code}: {dist[code]} ({pct:.1f}%)")

    # ============================================================
    # CAPTURE RATES
    # ============================================================
    total = len(merged)
    n_y = dist.get("Y", 0)
    n_p = dist.get("P", 0)
    n_n = dist.get("N", 0)
    strict_rate = n_y / total
    lenient_rate = (n_y + n_p) / total

    print(f"\nCapture Rates:")
    print(f"  Strict (Y only): {n_y}/{total} = {strict_rate:.1%}")
    print(f"  Lenient (Y+P):   {n_y + n_p}/{total} = {lenient_rate:.1%}")
    is_gte3 = sum(1 for r in merged if float(r.get("intelligibility_score", 0)) >= 3.0)
    print(f"  IS >= 3.0:       {is_gte3}/{total} = {is_gte3/total:.1%}")

    # ============================================================
    # AGREEMENT WITH IS FRAMEWORK
    # ============================================================
    print("\n--- Agreement with IS Framework ---")

    # Strict: Y vs P+N compared with IS >= 3.0
    # [LLM_pos & IS_pos, LLM_pos & IS_neg]
    # [LLM_neg & IS_pos, LLM_neg & IS_neg]
    strict_tp = sum(1 for r in merged if r["llm_judge"] == "Y" and float(r.get("intelligibility_score", 0)) >= 3.0)
    strict_fp = sum(1 for r in merged if r["llm_judge"] == "Y" and float(r.get("intelligibility_score", 0)) < 3.0)
    strict_fn = sum(1 for r in merged if r["llm_judge"] != "Y" and float(r.get("intelligibility_score", 0)) >= 3.0)
    strict_tn = sum(1 for r in merged if r["llm_judge"] != "Y" and float(r.get("intelligibility_score", 0)) < 3.0)

    strict_matrix = [[strict_tp, strict_fp], [strict_fn, strict_tn]]
    strict_kappa = cohens_kappa(strict_matrix)
    strict_accuracy = (strict_tp + strict_tn) / total if total > 0 else 0
    strict_precision = strict_tp / (strict_tp + strict_fp) if (strict_tp + strict_fp) > 0 else 0
    strict_recall = strict_tp / (strict_tp + strict_fn) if (strict_tp + strict_fn) > 0 else 0
    strict_f1 = 2 * strict_precision * strict_recall / (strict_precision + strict_recall) if (strict_precision + strict_recall) > 0 else 0

    print(f"\n  Strict (LLM Y vs IS>=3.0):")
    print(f"    TP={strict_tp} FP={strict_fp} FN={strict_fn} TN={strict_tn}")
    print(f"    Accuracy: {strict_accuracy:.3f}")
    print(f"    Precision: {strict_precision:.3f}")
    print(f"    Recall: {strict_recall:.3f}")
    print(f"    F1: {strict_f1:.3f}")
    print(f"    Kappa: {strict_kappa}")

    # Lenient: Y+P vs N compared with IS >= 3.0
    lenient_tp = sum(1 for r in merged if r["llm_judge"] in ("Y", "P") and float(r.get("intelligibility_score", 0)) >= 3.0)
    lenient_fp = sum(1 for r in merged if r["llm_judge"] in ("Y", "P") and float(r.get("intelligibility_score", 0)) < 3.0)
    lenient_fn = sum(1 for r in merged if r["llm_judge"] == "N" and float(r.get("intelligibility_score", 0)) >= 3.0)
    lenient_tn = sum(1 for r in merged if r["llm_judge"] == "N" and float(r.get("intelligibility_score", 0)) < 3.0)

    lenient_matrix = [[lenient_tp, lenient_fp], [lenient_fn, lenient_tn]]
    lenient_kappa = cohens_kappa(lenient_matrix)
    lenient_accuracy = (lenient_tp + lenient_tn) / total if total > 0 else 0
    lenient_precision = lenient_tp / (lenient_tp + lenient_fp) if (lenient_tp + lenient_fp) > 0 else 0
    lenient_recall = lenient_tp / (lenient_tp + lenient_fn) if (lenient_tp + lenient_fn) > 0 else 0
    lenient_f1 = 2 * lenient_precision * lenient_recall / (lenient_precision + lenient_recall) if (lenient_precision + lenient_recall) > 0 else 0

    print(f"\n  Lenient (LLM Y+P vs IS>=3.0):")
    print(f"    TP={lenient_tp} FP={lenient_fp} FN={lenient_fn} TN={lenient_tn}")
    print(f"    Accuracy: {lenient_accuracy:.3f}")
    print(f"    Precision: {lenient_precision:.3f}")
    print(f"    Recall: {lenient_recall:.3f}")
    print(f"    F1: {lenient_f1:.3f}")
    print(f"    Kappa: {lenient_kappa}")

    # 3x5 confusion matrix
    matrix_3x5 = compute_confusion_3x5(merged)
    print(f"\n  3x5 Matrix (Y/P/N x Tier 1-5):")
    print(f"         Tier1  Tier2  Tier3  Tier4  Tier5")
    for i, label in enumerate(["Y", "P", "N"]):
        row_str = "  ".join(f"{v:5d}" for v in matrix_3x5[i])
        print(f"    {label}:  {row_str}")

    # ============================================================
    # AGREEMENT WITH llm_context_prob HEURISTIC
    # ============================================================
    print("\n--- Agreement with llm_context_prob ---")
    heur_tp = sum(1 for r in merged if r["llm_judge"] == "Y" and float(r.get("llm_context_prob", 0)) >= 0.5)
    heur_fp = sum(1 for r in merged if r["llm_judge"] == "Y" and float(r.get("llm_context_prob", 0)) < 0.5)
    heur_fn = sum(1 for r in merged if r["llm_judge"] != "Y" and float(r.get("llm_context_prob", 0)) >= 0.5)
    heur_tn = sum(1 for r in merged if r["llm_judge"] != "Y" and float(r.get("llm_context_prob", 0)) < 0.5)
    heur_matrix = [[heur_tp, heur_fp], [heur_fn, heur_tn]]
    heur_kappa = cohens_kappa(heur_matrix)
    heur_accuracy = (heur_tp + heur_tn) / total if total > 0 else 0

    print(f"  Strict (LLM Y vs heur>=0.5):")
    print(f"    TP={heur_tp} FP={heur_fp} FN={heur_fn} TN={heur_tn}")
    print(f"    Accuracy: {heur_accuracy:.3f}")
    print(f"    Kappa: {heur_kappa}")

    # ============================================================
    # CORRELATIONS
    # ============================================================
    print("\n--- Correlations ---")
    llm_numeric = [r["llm_judge_numeric"] for r in merged]
    metrics = {
        "intelligibility_score": "IS",
        "semantic_sim": "Semantic Sim",
        "phonetic_sim": "Phonetic Sim",
        "wer_%": "WER",
        "wwer_%": "WWER",
        "llm_context_prob": "llm_context_prob",
    }
    correlations = {}
    for col, label in metrics.items():
        vals = []
        llm_vals = []
        for r in merged:
            try:
                v = float(r.get(col, 0))
                vals.append(v)
                llm_vals.append(r["llm_judge_numeric"])
            except (ValueError, TypeError):
                continue
        if len(vals) > 10:
            r_val = pearson_r(llm_vals, vals)
            rho_val = spearman_rho(llm_vals, vals)
            correlations[col] = {"pearson_r": r_val, "spearman_rho": rho_val}
            print(f"  {label:20s}: r={r_val:.4f}  rho={rho_val:.4f}")

    # ============================================================
    # INTRA-RATER RELIABILITY
    # ============================================================
    print("\n--- Intra-Rater Reliability ---")
    reliability = compute_reliability(all_entries)
    print(f"  Duplicate pairs: {reliability['n_duplicates']}")
    print(f"  Exact agreement: {reliability['exact_agreement']:.1%} ({reliability.get('exact_count', 0)}/{reliability['n_duplicates']})")
    print(f"  Lenient agreement: {reliability['lenient_agreement']:.1%} ({reliability.get('lenient_count', 0)}/{reliability['n_duplicates']})")

    # ============================================================
    # TAG ANALYSIS
    # ============================================================
    print("\n--- Partial Judgment Tag Analysis ---")
    tag_analysis = analyze_tags(judgments)
    print(f"  Total P judgments: {tag_analysis['total_p']}")
    print(f"\n  Preservation frequency:")
    for tag, count in sorted(tag_analysis["preserved_counts"].items(), key=lambda x: -x[1]):
        pct = count / tag_analysis["total_p"] * 100 if tag_analysis["total_p"] > 0 else 0
        print(f"    {tag:8s}: {count:4d} ({pct:.1f}%)")
    print(f"\n  Loss frequency:")
    for tag, count in sorted(tag_analysis["lost_counts"].items(), key=lambda x: -x[1]):
        pct = count / tag_analysis["total_p"] * 100 if tag_analysis["total_p"] > 0 else 0
        print(f"    {tag:8s}: {count:4d} ({pct:.1f}%)")

    # ============================================================
    # DISAGREEMENT ANALYSIS
    # ============================================================
    print("\n--- Disagreement Analysis ---")
    llm_y_is_fail = sum(1 for r in merged if r["llm_judge"] == "Y" and float(r.get("intelligibility_score", 0)) < 3.0)
    llm_n_is_pass = sum(1 for r in merged if r["llm_judge"] == "N" and float(r.get("intelligibility_score", 0)) >= 3.0)
    print(f"  LLM=Y but IS<3.0 (salvage validated): {llm_y_is_fail}")
    print(f"  LLM=N but IS>=3.0 (IS false positives): {llm_n_is_pass}")

    # Topic analysis
    print("\n--- Topic-Level Agreement ---")
    topic_data = defaultdict(lambda: {"Y": 0, "P": 0, "N": 0, "total": 0})
    for r in merged:
        topic = r.get("topic", "Unknown")
        code = r["llm_judge"]
        if code in ("Y", "P", "N"):
            topic_data[topic][code] += 1
            topic_data[topic]["total"] += 1

    for topic in sorted(topic_data.keys()):
        d = topic_data[topic]
        if d["total"] < 10:
            continue
        y_rate = d["Y"] / d["total"] * 100
        p_rate = d["P"] / d["total"] * 100
        n_rate = d["N"] / d["total"] * 100
        print(f"  {topic:30s}: Y={y_rate:5.1f}%  P={p_rate:5.1f}%  N={n_rate:5.1f}%  (n={d['total']})")

    # ============================================================
    # WRITE OUTPUTS
    # ============================================================
    print("\n--- Writing Outputs ---")

    # Results CSV
    write_results_csv(merged)
    print(f"  Wrote {OUTPUT_CSV}")

    # Examples
    n_yf, n_np, n_ps = write_examples(merged)
    print(f"  Wrote examples/ ({n_yf} yes-fail, {n_np} no-pass, {n_ps} partial)")

    # Summary JSON
    summary = {
        "metadata": {
            "model": "baseline",
            "n_segments": total,
            "date": "2026-03-03",
            "judge": "claude-opus-4-6",
        },
        "auto_classified": {
            "empty_N": sum(1 for r in merged if r.get("hyp", "").strip() == ""),
            "trivial_N": n_n - sum(1 for r in merged if r.get("hyp", "").strip() == ""),
        },
        "judgment_distribution": {
            "Y": n_y,
            "P": n_p,
            "N": n_n,
            "Y_pct": round(n_y / total * 100, 1),
            "P_pct": round(n_p / total * 100, 1),
            "N_pct": round(n_n / total * 100, 1),
        },
        "capture_rates": {
            "strict_Y": round(strict_rate, 4),
            "lenient_YP": round(lenient_rate, 4),
            "is_gte3": round(is_gte3 / total, 4),
            "salvage": 0.509,
        },
        "agreement_vs_is": {
            "strict_kappa": strict_kappa,
            "strict_accuracy": round(strict_accuracy, 4),
            "strict_precision": round(strict_precision, 4),
            "strict_recall": round(strict_recall, 4),
            "strict_f1": round(strict_f1, 4),
            "lenient_kappa": lenient_kappa,
            "lenient_accuracy": round(lenient_accuracy, 4),
            "lenient_precision": round(lenient_precision, 4),
            "lenient_recall": round(lenient_recall, 4),
            "lenient_f1": round(lenient_f1, 4),
        },
        "agreement_vs_heuristic": {
            "strict_kappa": heur_kappa,
            "strict_accuracy": round(heur_accuracy, 4),
        },
        "correlations": {k: v["pearson_r"] for k, v in correlations.items()},
        "intra_rater": reliability,
        "confusion_3x5": matrix_3x5,
        "disagreements": {
            "llm_y_is_fail": llm_y_is_fail,
            "llm_n_is_pass": llm_n_is_pass,
        },
        "tag_analysis": {
            "total_p": tag_analysis["total_p"],
            "preserved_frequency": tag_analysis["preserved_counts"],
            "lost_frequency": tag_analysis["lost_counts"],
            "top_profiles": tag_analysis["top_profiles"],
        },
    }
    with open(OUTPUT_JSON, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Wrote {OUTPUT_JSON}")

    # ============================================================
    # WRITE ANALYSIS REPORT
    # ============================================================
    print("\nWriting analysis report...")
    md = []
    md.append("# LLM-as-a-Judge Gold Standard Evaluation")
    md.append("")
    md.append("## Section 1: Methodology")
    md.append("")
    md.append("### Judgment Protocol")
    md.append("")
    md.append("Claude Opus 4.6 evaluated 1,497 hypothesis-reference pairs from the baseline VSP model ")
    md.append("using a 3-level scale:")
    md.append("")
    md.append("| Code | Label | Definition |")
    md.append("|------|-------|------------|")
    md.append("| **Y** | Yes | Meaning clearly conveyed |")
    md.append("| **P** | Partial | Some meaning preserved, but key info lost or distorted |")
    md.append("| **N** | No | Wrong topic, hallucination, empty, or misleading |")
    md.append("")
    md.append("**Blind evaluation:** Batch files contained only reference + hypothesis text. No WER, IS, ")
    md.append("tier, or other metrics were visible during judging to prevent anchoring bias.")
    md.append("")
    md.append("**Conservative tie-breaking:** Y vs P -> P; P vs N -> N.")
    md.append("")
    md.append(f"**Pre-classification:** {summary['auto_classified']['empty_N']} empty-hypothesis pairs auto-classified as N.")
    md.append("")
    md.append(f"**Batches:** 15 batches of ~100 pairs each, shuffled with fixed seed (42).")
    md.append("")
    md.append(f"### Intra-Rater Reliability")
    md.append("")
    md.append(f"30 duplicate pairs were embedded across batches (6 per IS tier).")
    md.append("")
    md.append(f"- **Exact agreement:** {reliability['exact_agreement']:.1%} ({reliability.get('exact_count', 0)}/30)")
    md.append(f"- **Lenient agreement (Y+P vs N):** {reliability['lenient_agreement']:.1%} ({reliability.get('lenient_count', 0)}/30)")
    md.append("")

    md.append("## Section 2: Gold Standard Capture Rate")
    md.append("")
    md.append("| Metric | Count | Rate |")
    md.append("|--------|-------|------|")
    md.append(f"| **LLM Judge: Y (strict)** | {n_y} | **{strict_rate:.1%}** |")
    md.append(f"| **LLM Judge: Y+P (lenient)** | {n_y + n_p} | **{lenient_rate:.1%}** |")
    md.append(f"| IS >= 3.0 | {is_gte3} | {is_gte3/total:.1%} |")
    md.append(f"| Useful output (IS >= 2.00) | 922 | 61.6% |")
    md.append("")
    md.append("### Judgment Distribution")
    md.append("")
    md.append("| Judgment | Count | % |")
    md.append("|----------|-------|-----|")
    md.append(f"| Y (meaning conveyed) | {n_y} | {n_y/total*100:.1f}% |")
    md.append(f"| P (partial) | {n_p} | {n_p/total*100:.1f}% |")
    md.append(f"| N (meaning lost) | {n_n} | {n_n/total*100:.1f}% |")
    md.append("")

    md.append("## Section 3: Agreement with IS Framework")
    md.append("")
    md.append("### Strict: LLM Y vs IS >= 3.0")
    md.append("")
    md.append("|  | IS >= 3.0 | IS < 3.0 |")
    md.append("|--|-----------|----------|")
    md.append(f"| **LLM Y** | {strict_tp} | {strict_fp} |")
    md.append(f"| **LLM P+N** | {strict_fn} | {strict_tn} |")
    md.append("")
    md.append(f"- Accuracy: {strict_accuracy:.3f}")
    md.append(f"- Precision: {strict_precision:.3f}")
    md.append(f"- Recall: {strict_recall:.3f}")
    md.append(f"- F1: {strict_f1:.3f}")
    md.append(f"- Cohen's kappa: {strict_kappa}")
    md.append("")
    md.append("### Lenient: LLM Y+P vs IS >= 3.0")
    md.append("")
    md.append("|  | IS >= 3.0 | IS < 3.0 |")
    md.append("|--|-----------|----------|")
    md.append(f"| **LLM Y+P** | {lenient_tp} | {lenient_fp} |")
    md.append(f"| **LLM N** | {lenient_fn} | {lenient_tn} |")
    md.append("")
    md.append(f"- Accuracy: {lenient_accuracy:.3f}")
    md.append(f"- Precision: {lenient_precision:.3f}")
    md.append(f"- Recall: {lenient_recall:.3f}")
    md.append(f"- F1: {lenient_f1:.3f}")
    md.append(f"- Cohen's kappa: {lenient_kappa}")
    md.append("")

    md.append("### 3x5 Breakdown: LLM Judge x IS Tier")
    md.append("")
    md.append("| LLM | Tier 1 (Failed) | Tier 2 (Poor) | Tier 3 (Fair) | Tier 4 (Good) | Tier 5 (Excellent) |")
    md.append("|-----|-----------------|---------------|---------------|---------------|-------------------|")
    for i, label in enumerate(["Y", "P", "N"]):
        cells = " | ".join(str(v) for v in matrix_3x5[i])
        md.append(f"| **{label}** | {cells} |")
    md.append("")

    md.append("## Section 4: Agreement with llm_context_prob Heuristic")
    md.append("")
    md.append("|  | Heuristic >= 0.5 | Heuristic < 0.5 |")
    md.append("|--|------------------|-----------------|")
    md.append(f"| **LLM Y** | {heur_tp} | {heur_fp} |")
    md.append(f"| **LLM P+N** | {heur_fn} | {heur_tn} |")
    md.append("")
    md.append(f"- Accuracy: {heur_accuracy:.3f}")
    md.append(f"- Cohen's kappa: {heur_kappa}")
    md.append("")

    md.append("## Section 5: Correlation Analysis")
    md.append("")
    md.append("LLM judge encoded as Y=1, P=0.5, N=0.")
    md.append("")
    md.append("| Metric | Pearson r | Spearman rho |")
    md.append("|--------|-----------|-------------|")
    for col, label in metrics.items():
        if col in correlations:
            c = correlations[col]
            md.append(f"| {label} | {c['pearson_r']:.4f} | {c['spearman_rho']:.4f} |")
    md.append("")

    md.append("## Section 6: Partial Judgment Analysis")
    md.append("")
    md.append(f"Total P judgments: {tag_analysis['total_p']}")
    md.append("")
    md.append("### Preservation Frequency")
    md.append("")
    md.append("| Tag | Count | % of P |")
    md.append("|-----|-------|--------|")
    for tag, count in sorted(tag_analysis["preserved_counts"].items(), key=lambda x: -x[1]):
        pct = count / tag_analysis["total_p"] * 100 if tag_analysis["total_p"] > 0 else 0
        md.append(f"| {tag} | {count} | {pct:.1f}% |")
    md.append("")
    md.append("### Loss Frequency")
    md.append("")
    md.append("| Tag | Count | % of P |")
    md.append("|-----|-------|--------|")
    for tag, count in sorted(tag_analysis["lost_counts"].items(), key=lambda x: -x[1]):
        pct = count / tag_analysis["total_p"] * 100 if tag_analysis["total_p"] > 0 else 0
        md.append(f"| {tag} | {count} | {pct:.1f}% |")
    md.append("")
    md.append("### Most Common P Profiles")
    md.append("")
    md.append("| Profile | Count |")
    md.append("|---------|-------|")
    for profile, count in list(tag_analysis["top_profiles"].items())[:10]:
        md.append(f"| `{profile}` | {count} |")
    md.append("")

    md.append("## Section 7: Disagreement Deep Dive")
    md.append("")
    md.append(f"- **LLM=Y but IS<3.0** (salvage validated): {llm_y_is_fail} segments")
    md.append(f"- **LLM=N but IS>=3.0** (IS false positives): {llm_n_is_pass} segments")
    md.append("")
    md.append("See `examples/` directory for curated disagreement examples:")
    md.append("- `disagreement_llm_yes_is_fail.md` — model output is useful despite bad metrics")
    md.append("- `disagreement_llm_no_is_pass.md` — metrics are too generous")
    md.append("- `partial_judgment_showcase.md` — the boundary zone")
    md.append("- `agreement_showcase.md` — validation of IS framework")
    md.append("")

    md.append("## Section 8: Topic-Level Analysis")
    md.append("")
    md.append("| Topic | Y% | P% | N% | n |")
    md.append("|-------|----|----|----|---|")
    for topic in sorted(topic_data.keys()):
        d = topic_data[topic]
        if d["total"] < 10:
            continue
        y_rate = d["Y"] / d["total"] * 100
        p_rate = d["P"] / d["total"] * 100
        n_rate = d["N"] / d["total"] * 100
        md.append(f"| {topic} | {y_rate:.1f} | {p_rate:.1f} | {n_rate:.1f} | {d['total']} |")
    md.append("")

    md.append("## Section 9: Implications")
    md.append("")
    md.append("### IS Threshold Calibration")
    md.append("")
    md.append(f"The IS >= 3.0 threshold captures {is_gte3/total:.1%} of segments as 'properly captured.' ")
    md.append(f"The LLM judge assigns Y (clear meaning) to {strict_rate:.1%} and Y+P to {lenient_rate:.1%}.")
    md.append("")
    if strict_rate < is_gte3 / total:
        md.append("The LLM strict rate is **lower** than IS >= 3.0, suggesting IS may be slightly generous ")
        md.append("at the boundary. However, including P judgments (lenient) likely aligns more closely.")
    else:
        md.append("The LLM strict rate is **higher** than IS >= 3.0, suggesting IS may be too conservative.")
    md.append("")
    md.append("### Effective Capture Rate")
    md.append("")
    md.append(f"The gold standard LLM lenient capture rate of {lenient_rate:.1%} compares with:")
    md.append(f"- IS >= 3.0: {is_gte3/total:.1%}")
    md.append(f"- Useful output (IS >= 2.00): 61.6%")
    md.append("")

    with open(OUTPUT_MD, "w") as f:
        f.write("\n".join(md))
    print(f"  Wrote {OUTPUT_MD}")

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
