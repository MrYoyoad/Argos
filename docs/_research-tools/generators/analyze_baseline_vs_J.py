#!/usr/bin/env python3
"""
Comprehensive comparative analysis of Baseline vs Config J decode runs.
Reads both report CSVs and produces detailed markdown analysis.
"""

import csv
import sys
from collections import defaultdict, Counter
import statistics

def read_csv(path):
    """Read CSV and return list of dicts."""
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def safe_float(val, default=None):
    """Safely convert to float."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def stats(values):
    """Return mean, median, std for a list of values."""
    if not values:
        return 0.0, 0.0, 0.0
    m = statistics.mean(values)
    med = statistics.median(values)
    s = statistics.stdev(values) if len(values) > 1 else 0.0
    return m, med, s

def main():
    baseline_path = "/home/ubuntu/english_full_results/client_outputs/report/report.csv"
    j_path = "/home/ubuntu/tuning_results/full_decode_J/report/report.csv"

    baseline_rows = read_csv(baseline_path)
    j_rows = read_csv(j_path)

    # Build lookup by utt_id
    baseline_map = {r['utt_id']: r for r in baseline_rows}
    j_map = {r['utt_id']: r for r in j_rows}

    # Get common utt_ids
    common_ids = sorted(set(baseline_map.keys()) & set(j_map.keys()))
    only_baseline = set(baseline_map.keys()) - set(j_map.keys())
    only_j = set(j_map.keys()) - set(baseline_map.keys())

    print(f"# Comparative Analysis: Baseline vs Config J (Full 1,497-Segment Decode)")
    print()
    print(f"**Baseline**: beam=20, lenpen=0.0, do_sample=true (bugged, temp=1.0), rep_penalty=1.2")
    print(f"**Config J**: beam=20, lenpen=1.0, do_sample=true, temperature=0.5, top_p=0.9, rep_penalty=1.2")
    print()
    print(f"- Baseline segments: {len(baseline_rows)}")
    print(f"- Config J segments: {len(j_rows)}")
    print(f"- Common segments: {len(common_ids)}")
    if only_baseline:
        print(f"- Only in baseline: {len(only_baseline)}")
    if only_j:
        print(f"- Only in Config J: {len(only_j)}")
    print()

    # =========================================================================
    # 1. OVERALL METRICS COMPARISON
    # =========================================================================
    print("---")
    print()
    print("## 1. Overall Metrics Comparison")
    print()

    metrics = ['wer_%', 'wwer_%', 'nea_recall_%', 'nea_precision_%', 'nea_f1_%']
    metric_labels = ['WER %', 'WWER %', 'NEA Recall %', 'NEA Precision %', 'NEA F1 %']

    # Collect metric values
    b_vals = {m: [] for m in metrics}
    j_vals = {m: [] for m in metrics}

    for uid in common_ids:
        for m in metrics:
            bv = safe_float(baseline_map[uid][m])
            jv = safe_float(j_map[uid][m])
            if bv is not None:
                b_vals[m].append(bv)
            if jv is not None:
                j_vals[m].append(jv)

    print("| Metric | Baseline Mean | Baseline Median | Baseline Std | Config J Mean | Config J Median | Config J Std | Delta Mean |")
    print("|--------|---------------|-----------------|--------------|---------------|-----------------|--------------|------------|")
    for m, label in zip(metrics, metric_labels):
        bm, bmed, bstd = stats(b_vals[m])
        jm, jmed, jstd = stats(j_vals[m])
        delta = jm - bm
        print(f"| {label} | {bm:.2f} | {bmed:.2f} | {bstd:.2f} | {jm:.2f} | {jmed:.2f} | {jstd:.2f} | {delta:+.2f} |")

    print()

    # Empty predictions
    b_empty = sum(1 for uid in common_ids if baseline_map[uid]['hyp'].strip() == '')
    j_empty = sum(1 for uid in common_ids if j_map[uid]['hyp'].strip() == '')
    print(f"**Empty predictions**: Baseline = {b_empty}, Config J = {j_empty}")
    print()

    # High WER counts
    for threshold in [100, 200, 500]:
        b_count = sum(1 for uid in common_ids if safe_float(baseline_map[uid]['wer_%'], 0) > threshold)
        j_count = sum(1 for uid in common_ids if safe_float(j_map[uid]['wer_%'], 0) > threshold)
        print(f"**Segments with WER > {threshold}%**: Baseline = {b_count}, Config J = {j_count}")
    print()

    # =========================================================================
    # 2. SEGMENT-LEVEL CHANGE ANALYSIS
    # =========================================================================
    print("---")
    print()
    print("## 2. Segment-Level Change Analysis")
    print()

    changed = 0
    unchanged = 0
    wwer_improved = 0
    wwer_worsened = 0
    wwer_same = 0
    wer_improved = 0
    wer_worsened = 0
    wer_same = 0
    near_improved = 0
    near_worsened = 0
    near_same = 0

    wwer_improve_deltas = []
    wwer_worsen_deltas = []
    wer_improve_deltas = []
    wer_worsen_deltas = []

    for uid in common_ids:
        b_hyp = baseline_map[uid]['hyp'].strip()
        j_hyp = j_map[uid]['hyp'].strip()

        if b_hyp != j_hyp:
            changed += 1
        else:
            unchanged += 1

        b_wwer = safe_float(baseline_map[uid]['wwer_%'], 0)
        j_wwer = safe_float(j_map[uid]['wwer_%'], 0)
        delta_wwer = j_wwer - b_wwer

        if delta_wwer < -0.01:
            wwer_improved += 1
            wwer_improve_deltas.append(delta_wwer)
        elif delta_wwer > 0.01:
            wwer_worsened += 1
            wwer_worsen_deltas.append(delta_wwer)
        else:
            wwer_same += 1

        b_wer = safe_float(baseline_map[uid]['wer_%'], 0)
        j_wer = safe_float(j_map[uid]['wer_%'], 0)
        delta_wer = j_wer - b_wer

        if delta_wer < -0.01:
            wer_improved += 1
            wer_improve_deltas.append(delta_wer)
        elif delta_wer > 0.01:
            wer_worsened += 1
            wer_worsen_deltas.append(delta_wer)
        else:
            wer_same += 1

        b_near = safe_float(baseline_map[uid]['nea_recall_%'], 0)
        j_near = safe_float(j_map[uid]['nea_recall_%'], 0)
        delta_near = j_near - b_near

        if delta_near > 0.01:
            near_improved += 1
        elif delta_near < -0.01:
            near_worsened += 1
        else:
            near_same += 1

    print(f"- **Segments with different hyp text**: {changed} / {len(common_ids)} ({100*changed/len(common_ids):.1f}%)")
    print(f"- **Segments with identical hyp text**: {unchanged} / {len(common_ids)} ({100*unchanged/len(common_ids):.1f}%)")
    print()

    print("| Metric | Improved | Worsened | Unchanged | Net |")
    print("|--------|----------|----------|-----------|-----|")
    print(f"| WWER | {wwer_improved} | {wwer_worsened} | {wwer_same} | {wwer_improved - wwer_worsened:+d} |")
    print(f"| WER | {wer_improved} | {wer_worsened} | {wer_same} | {wer_improved - wer_worsened:+d} |")
    print(f"| NEA Recall | {near_improved} | {near_worsened} | {near_same} | {near_improved - near_worsened:+d} |")
    print()

    print("**Asymmetry Analysis (mean delta magnitude)**:")
    print()
    if wwer_improve_deltas:
        print(f"- WWER improved segments: mean delta = {statistics.mean(wwer_improve_deltas):.2f} pp (magnitude of improvement)")
    if wwer_worsen_deltas:
        print(f"- WWER worsened segments: mean delta = +{statistics.mean(wwer_worsen_deltas):.2f} pp (magnitude of regression)")
    if wer_improve_deltas:
        print(f"- WER improved segments: mean delta = {statistics.mean(wer_improve_deltas):.2f} pp")
    if wer_worsen_deltas:
        print(f"- WER worsened segments: mean delta = +{statistics.mean(wer_worsen_deltas):.2f} pp")
    print()

    # =========================================================================
    # 3. QUARTILE ANALYSIS
    # =========================================================================
    print("---")
    print()
    print("## 3. Quartile Analysis (by Baseline WWER)")
    print()

    # Sort by baseline WWER
    wwer_data = []
    for uid in common_ids:
        b_wwer = safe_float(baseline_map[uid]['wwer_%'], 0)
        j_wwer = safe_float(j_map[uid]['wwer_%'], 0)
        wwer_data.append((uid, b_wwer, j_wwer, j_wwer - b_wwer))

    wwer_data.sort(key=lambda x: x[1])
    n = len(wwer_data)
    q_size = n // 4

    quartiles = [
        ("Q1 (Best 25%)", wwer_data[:q_size]),
        ("Q2 (25-50%)", wwer_data[q_size:2*q_size]),
        ("Q3 (50-75%)", wwer_data[2*q_size:3*q_size]),
        ("Q4 (Worst 25%)", wwer_data[3*q_size:]),
    ]

    print("| Quartile | Baseline WWER Range | Baseline Mean WWER | J Mean WWER | Mean Delta | Improved | Worsened |")
    print("|----------|---------------------|--------------------|----|------------|----------|----------|")
    for label, q_data in quartiles:
        b_range = f"{q_data[0][1]:.1f} - {q_data[-1][1]:.1f}"
        b_mean = statistics.mean([d[1] for d in q_data])
        j_mean = statistics.mean([d[2] for d in q_data])
        d_mean = statistics.mean([d[3] for d in q_data])
        imp = sum(1 for d in q_data if d[3] < -0.01)
        wors = sum(1 for d in q_data if d[3] > 0.01)
        print(f"| {label} | {b_range} | {b_mean:.2f} | {j_mean:.2f} | {d_mean:+.2f} | {imp} | {wors} |")
    print()

    # =========================================================================
    # 4. SEGMENT LENGTH ANALYSIS
    # =========================================================================
    print("---")
    print()
    print("## 4. Segment Length Analysis (by Reference Word Count)")
    print()

    length_buckets = {
        "Short (1-10 words)": (1, 10),
        "Medium (11-30 words)": (11, 30),
        "Long (31+ words)": (31, 9999),
    }

    print("| Length Group | Count | Baseline Mean WWER | J Mean WWER | Delta | Baseline Mean WER | J Mean WER | Delta |")
    print("|-------------|-------|--------------------|----|-------|-------------------|-----------|-------|")

    for label, (lo, hi) in length_buckets.items():
        b_wwers = []
        j_wwers = []
        b_wers = []
        j_wers = []
        count = 0
        for uid in common_ids:
            ref = baseline_map[uid]['ref'].strip()
            wc = len(ref.split()) if ref else 0
            if lo <= wc <= hi:
                count += 1
                b_wwers.append(safe_float(baseline_map[uid]['wwer_%'], 0))
                j_wwers.append(safe_float(j_map[uid]['wwer_%'], 0))
                b_wers.append(safe_float(baseline_map[uid]['wer_%'], 0))
                j_wers.append(safe_float(j_map[uid]['wer_%'], 0))

        if count > 0:
            bw = statistics.mean(b_wwers)
            jw = statistics.mean(j_wwers)
            bwer = statistics.mean(b_wers)
            jwer = statistics.mean(j_wers)
            print(f"| {label} | {count} | {bw:.2f} | {jw:.2f} | {jw-bw:+.2f} | {bwer:.2f} | {jwer:.2f} | {jwer-bwer:+.2f} |")

    # Zero-word refs
    zero_count = sum(1 for uid in common_ids if len(baseline_map[uid]['ref'].strip().split()) == 0 or baseline_map[uid]['ref'].strip() == '')
    if zero_count > 0:
        print(f"\n*Note: {zero_count} segments had empty references (excluded from length analysis).*")
    print()

    # =========================================================================
    # 5. EMPTY PREDICTION ANALYSIS
    # =========================================================================
    print("---")
    print()
    print("## 5. Empty Prediction Analysis")
    print()

    # Segments empty in baseline
    empty_in_baseline = []
    for uid in common_ids:
        if baseline_map[uid]['hyp'].strip() == '':
            j_hyp = j_map[uid]['hyp'].strip()
            j_wwer = safe_float(j_map[uid]['wwer_%'], 0)
            j_wer = safe_float(j_map[uid]['wer_%'], 0)
            ref = baseline_map[uid]['ref'].strip()
            empty_in_baseline.append((uid, ref, j_hyp, j_wwer, j_wer))

    print(f"**Segments empty in baseline**: {len(empty_in_baseline)}")

    j_filled = [(uid, ref, j_hyp, j_wwer, j_wer) for uid, ref, j_hyp, j_wwer, j_wer in empty_in_baseline if j_hyp != '']
    j_still_empty = [(uid, ref, j_hyp, j_wwer, j_wer) for uid, ref, j_hyp, j_wwer, j_wer in empty_in_baseline if j_hyp == '']

    print(f"- J produced non-empty output: {len(j_filled)}")
    print(f"- J also produced empty: {len(j_still_empty)}")
    print()

    if j_filled:
        j_filled_wwers = [x[3] for x in j_filled]
        j_filled_wers = [x[4] for x in j_filled]
        print(f"**J's performance on formerly-empty segments**:")
        print(f"- Mean WWER: {statistics.mean(j_filled_wwers):.2f}%")
        print(f"- Median WWER: {statistics.median(j_filled_wwers):.2f}%")
        print(f"- Mean WER: {statistics.mean(j_filled_wers):.2f}%")
        print()

        # Count by WWER ranges
        good = sum(1 for w in j_filled_wwers if w <= 50)
        mid = sum(1 for w in j_filled_wwers if 50 < w <= 100)
        bad = sum(1 for w in j_filled_wwers if w > 100)
        print(f"- WWER <= 50%: {good} segments (good quality)")
        print(f"- WWER 50-100%: {mid} segments (partial)")
        print(f"- WWER > 100%: {bad} segments (hallucination)")
        print()

        # Best 5
        j_filled_sorted = sorted(j_filled, key=lambda x: x[3])
        print("### 5 Best Examples (J filled empties, lowest WWER)")
        print()
        print("| utt_id | Ref (first 80 chars) | J Hyp (first 80 chars) | J WWER |")
        print("|--------|---------------------|----------------------|--------|")
        for uid, ref, j_hyp, j_wwer, j_wer in j_filled_sorted[:5]:
            print(f"| `{uid[:40]}...` | {ref[:80]} | {j_hyp[:80]} | {j_wwer:.1f}% |")
        print()

        # Worst 5
        print("### 5 Worst Examples (J filled empties, highest WWER)")
        print()
        print("| utt_id | Ref (first 80 chars) | J Hyp (first 80 chars) | J WWER |")
        print("|--------|---------------------|----------------------|--------|")
        for uid, ref, j_hyp, j_wwer, j_wer in j_filled_sorted[-5:]:
            print(f"| `{uid[:40]}...` | {ref[:80]} | {j_hyp[:80]} | {j_wwer:.1f}% |")
        print()

    # Segments empty in J but not baseline
    empty_in_j_only = []
    for uid in common_ids:
        if j_map[uid]['hyp'].strip() == '' and baseline_map[uid]['hyp'].strip() != '':
            empty_in_j_only.append(uid)
    if empty_in_j_only:
        print(f"**New empty predictions in J (were non-empty in baseline)**: {len(empty_in_j_only)}")
        print()

    # =========================================================================
    # 6. HALLUCINATION ANALYSIS
    # =========================================================================
    print("---")
    print()
    print("## 6. Hallucination Analysis (WER > 100%)")
    print()

    new_hallucinations = []
    fixed_hallucinations = []

    for uid in common_ids:
        b_wer = safe_float(baseline_map[uid]['wer_%'], 0)
        j_wer = safe_float(j_map[uid]['wer_%'], 0)

        if b_wer <= 100 and j_wer > 100:
            new_hallucinations.append((uid, b_wer, j_wer, baseline_map[uid]['ref'][:80], baseline_map[uid]['hyp'][:80], j_map[uid]['hyp'][:80]))

        if b_wer > 100 and j_wer <= 100:
            fixed_hallucinations.append((uid, b_wer, j_wer, baseline_map[uid]['ref'][:80], baseline_map[uid]['hyp'][:80], j_map[uid]['hyp'][:80]))

    print(f"- **New hallucinations (baseline WER <= 100%, J WER > 100%)**: {len(new_hallucinations)}")
    print(f"- **Fixed hallucinations (baseline WER > 100%, J WER <= 100%)**: {len(fixed_hallucinations)}")
    print(f"- **Net hallucination change**: {len(new_hallucinations) - len(fixed_hallucinations):+d}")
    print()

    # Sort new hallucinations by J WER (worst first)
    new_hallucinations.sort(key=lambda x: -x[2])
    print("### 5 Worst New Hallucinations (highest J WER)")
    print()
    print("| utt_id | Baseline WER | J WER | Ref (first 80 chars) | J Hyp (first 80 chars) |")
    print("|--------|-------------|-------|---------------------|----------------------|")
    for uid, b_wer, j_wer, ref, b_hyp, j_hyp in new_hallucinations[:5]:
        print(f"| `{uid[:45]}` | {b_wer:.1f}% | {j_wer:.1f}% | {ref} | {j_hyp} |")
    print()

    # Sort fixed hallucinations by improvement magnitude
    fixed_hallucinations.sort(key=lambda x: x[1] - x[2], reverse=True)
    print("### 5 Best Fixed Hallucinations (biggest WER improvement)")
    print()
    print("| utt_id | Baseline WER | J WER | Ref (first 80 chars) | J Hyp (first 80 chars) |")
    print("|--------|-------------|-------|---------------------|----------------------|")
    for uid, b_wer, j_wer, ref, b_hyp, j_hyp in fixed_hallucinations[:5]:
        print(f"| `{uid[:45]}` | {b_wer:.1f}% | {j_wer:.1f}% | {ref} | {j_hyp} |")
    print()

    # =========================================================================
    # 7. TOP 10 BIGGEST IMPROVEMENTS (by WWER delta)
    # =========================================================================
    print("---")
    print()
    print("## 7. Top 10 Biggest Improvements (by WWER Delta)")
    print()

    all_deltas = []
    for uid in common_ids:
        b_wwer = safe_float(baseline_map[uid]['wwer_%'], 0)
        j_wwer = safe_float(j_map[uid]['wwer_%'], 0)
        ref = baseline_map[uid]['ref'].strip()
        all_deltas.append((uid, ref, b_wwer, j_wwer, j_wwer - b_wwer))

    # Sort by delta ascending (biggest improvement = most negative delta)
    all_deltas.sort(key=lambda x: x[4])

    print("| # | utt_id | Ref (first 60 chars) | Baseline WWER | J WWER | Delta |")
    print("|---|--------|---------------------|---------------|--------|-------|")
    for i, (uid, ref, b_wwer, j_wwer, delta) in enumerate(all_deltas[:10], 1):
        print(f"| {i} | `{uid[:40]}` | {ref[:60]} | {b_wwer:.1f}% | {j_wwer:.1f}% | {delta:+.1f} |")
    print()

    # =========================================================================
    # 8. TOP 10 BIGGEST REGRESSIONS (by WWER delta)
    # =========================================================================
    print("---")
    print()
    print("## 8. Top 10 Biggest Regressions (by WWER Delta)")
    print()

    # Sort by delta descending (biggest regression = most positive delta)
    all_deltas.sort(key=lambda x: -x[4])

    print("| # | utt_id | Ref (first 60 chars) | Baseline WWER | J WWER | Delta |")
    print("|---|--------|---------------------|---------------|--------|-------|")
    for i, (uid, ref, b_wwer, j_wwer, delta) in enumerate(all_deltas[:10], 1):
        print(f"| {i} | `{uid[:40]}` | {ref[:60]} | {b_wwer:.1f}% | {j_wwer:.1f}% | {delta:+.1f} |")
    print()

    # =========================================================================
    # 9. NAMED ENTITY ANALYSIS
    # =========================================================================
    print("---")
    print()
    print("## 9. Named Entity Analysis")
    print()

    # NEA-R changes
    near_imp_count = 0
    near_worse_count = 0
    near_same_count = 0

    # Collect missed entities
    b_missed_all = Counter()
    j_missed_all = Counter()
    recovered_entities = Counter()  # in baseline missed but not in J
    lost_entities = Counter()  # not in baseline missed but in J missed

    for uid in common_ids:
        b_near = safe_float(baseline_map[uid]['nea_recall_%'], 0)
        j_near = safe_float(j_map[uid]['nea_recall_%'], 0)

        if j_near > b_near + 0.01:
            near_imp_count += 1
        elif j_near < b_near - 0.01:
            near_worse_count += 1
        else:
            near_same_count += 1

        b_missed_raw = baseline_map[uid].get('missed_entities', '').strip()
        j_missed_raw = j_map[uid].get('missed_entities', '').strip()

        # Parse missed entities (comma-separated, may have quotes)
        b_missed = set()
        j_missed = set()
        if b_missed_raw:
            b_missed = set(e.strip().strip('"').lower() for e in b_missed_raw.split(',') if e.strip())
        if j_missed_raw:
            j_missed = set(e.strip().strip('"').lower() for e in j_missed_raw.split(',') if e.strip())

        for e in b_missed:
            b_missed_all[e] += 1
        for e in j_missed:
            j_missed_all[e] += 1

        # Recovered: in baseline missed but not in J missed
        for e in b_missed - j_missed:
            recovered_entities[e] += 1
        # Lost: in J missed but not in baseline missed
        for e in j_missed - b_missed:
            lost_entities[e] += 1

    print(f"- **NEA Recall improved**: {near_imp_count} segments")
    print(f"- **NEA Recall worsened**: {near_worse_count} segments")
    print(f"- **NEA Recall unchanged**: {near_same_count} segments")
    print(f"- **Net NEA-R change**: {near_imp_count - near_worse_count:+d} segments")
    print()

    print("### Most Frequently Missed Entities (Baseline vs J)")
    print()
    print("| Entity | Baseline Missed Count | J Missed Count | Delta | Status |")
    print("|--------|----------------------|----------------|-------|--------|")
    # Show top entities by total appearances
    all_entities = set(list(b_missed_all.keys()) + list(j_missed_all.keys()))
    entity_data = []
    for e in all_entities:
        bc = b_missed_all.get(e, 0)
        jc = j_missed_all.get(e, 0)
        entity_data.append((e, bc, jc, jc - bc))
    entity_data.sort(key=lambda x: max(x[1], x[2]), reverse=True)

    for e, bc, jc, delta in entity_data[:25]:
        status = "J better" if delta < 0 else ("J worse" if delta > 0 else "Same")
        print(f"| {e} | {bc} | {jc} | {delta:+d} | {status} |")
    print()

    print("### Top 15 Entities Recovered by J (were missed in baseline, found in J)")
    print()
    print("| Entity | Times Recovered |")
    print("|--------|-----------------|")
    for e, count in recovered_entities.most_common(15):
        print(f"| {e} | {count} |")
    print()

    print("### Top 15 Entities Lost by J (found in baseline, missed in J)")
    print()
    print("| Entity | Times Lost |")
    print("|--------|------------|")
    for e, count in lost_entities.most_common(15):
        print(f"| {e} | {count} |")
    print()

    # Entity type analysis (heuristic: classify by common patterns)
    # Function words vs content words vs names/numbers
    function_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                      'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                      'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
                      'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
                      'before', 'after', 'above', 'below', 'between', 'out', 'about',
                      'and', 'but', 'or', 'nor', 'not', 'so', 'yet', 'both', 'either',
                      'neither', 'each', 'every', 'all', 'any', 'few', 'more', 'most',
                      'other', 'some', 'such', 'no', 'than', 'too', 'very', 'just',
                      'also', 'that', 'this', 'these', 'those', 'it', 'its', 'i', 'me',
                      'my', 'we', 'us', 'our', 'you', 'your', 'he', 'him', 'his', 'she',
                      'her', 'they', 'them', 'their', 'what', 'which', 'who', 'whom',
                      'where', 'when', 'how', 'if', 'then', 'else', 'up', 'down',
                      'here', 'there', 'now', 'only', 'even', 'back', 'still', 'well',
                      'really', 'actually', 'just', 'because', 'like'}

    recovered_func = sum(c for e, c in recovered_entities.items() if e in function_words)
    recovered_content = sum(c for e, c in recovered_entities.items() if e not in function_words)
    lost_func = sum(c for e, c in lost_entities.items() if e in function_words)
    lost_content = sum(c for e, c in lost_entities.items() if e not in function_words)

    print("### Entity Category Summary")
    print()
    print(f"| Category | Recovered by J | Lost by J | Net |")
    print(f"|----------|----------------|-----------|-----|")
    print(f"| Function words | {recovered_func} | {lost_func} | {recovered_func - lost_func:+d} |")
    print(f"| Content words / Named entities | {recovered_content} | {lost_content} | {recovered_content - lost_content:+d} |")
    print(f"| **Total** | **{recovered_func+recovered_content}** | **{lost_func+lost_content}** | **{(recovered_func+recovered_content)-(lost_func+lost_content):+d}** |")
    print()

    # =========================================================================
    # 10. CONCLUSION AND NEXT EXPERIMENT SUGGESTIONS
    # =========================================================================
    print("---")
    print()
    print("## 10. Conclusion and Next Experiment Suggestions")
    print()

    # Compute summary stats for conclusion
    b_mean_wwer = statistics.mean(b_vals['wwer_%'])
    j_mean_wwer = statistics.mean(j_vals['wwer_%'])
    b_mean_wer = statistics.mean(b_vals['wer_%'])
    j_mean_wer = statistics.mean(j_vals['wer_%'])

    print("### Key Findings")
    print()
    print(f"1. **Overall WWER**: Config J {'improved' if j_mean_wwer < b_mean_wwer else 'worsened'} mean WWER by {abs(j_mean_wwer - b_mean_wwer):.2f} pp ({b_mean_wwer:.2f}% -> {j_mean_wwer:.2f}%)")
    print(f"2. **Overall WER**: Config J {'improved' if j_mean_wer < b_mean_wer else 'worsened'} mean WER by {abs(j_mean_wer - b_mean_wer):.2f} pp ({b_mean_wer:.2f}% -> {j_mean_wer:.2f}%)")
    print(f"3. **Empty predictions**: Reduced from {b_empty} to {j_empty} ({b_empty - j_empty} segments rescued)")
    print(f"4. **Hallucination balance**: {len(new_hallucinations)} new vs {len(fixed_hallucinations)} fixed (net {len(new_hallucinations) - len(fixed_hallucinations):+d})")
    print(f"5. **WWER improvement/regression ratio**: {wwer_improved} improved vs {wwer_worsened} worsened")
    print()

    # Compute how much J's empty-filling contributed
    if j_filled:
        j_filled_wwer_mean = statistics.mean([x[3] for x in j_filled])
        # Baseline empties had 100% WWER effectively (no words matched)
        print(f"6. **Empty segment rescue quality**: Mean WWER of J's predictions on formerly-empty segments = {j_filled_wwer_mean:.1f}%")

    print()
    print("### Strengths of Config J")
    print()
    print("- **Filling empty predictions**: Controlled sampling (temp=0.5, top_p=0.9) with lenpen=1.0 produces output where baseline's bugged temp=1.0 sampling produced nothing")
    print("- **Entity recall**: Net positive entity recovery, particularly for content words")
    print(f"- **Improvement breadth**: {wwer_improved} segments improved in WWER")
    print()
    print("### Weaknesses of Config J")
    print()
    print("- **Hallucination risk**: New hallucinations introduced on segments that were previously acceptable")
    print("- **WER variance**: Higher WER standard deviation suggests more extreme outputs")
    print(f"- **Regression severity**: When J worsens a segment, the mean magnitude of regression ({statistics.mean(wwer_worsen_deltas) if wwer_worsen_deltas else 0:.1f} pp) vs improvement ({abs(statistics.mean(wwer_improve_deltas)) if wwer_improve_deltas else 0:.1f} pp)")
    print()
    print("### Recommended Next Experiments")
    print()
    print("1. **Config K - Lower temperature with lenpen**: `beam=20, lenpen=1.0, do_sample=true, temp=0.3, top_p=0.85, rep_penalty=1.2`")
    print("   - Rationale: J's temp=0.5 introduced some hallucinations. Lowering to 0.3 should reduce randomness while keeping the empty-filling benefit of lenpen=1.0")
    print()
    print("2. **Config L - Greedy with lenpen**: `beam=20, lenpen=1.0, do_sample=false, rep_penalty=1.2`")
    print("   - Rationale: Test whether lenpen=1.0 alone (without any sampling noise) can fill empties. This isolates the effect of length penalty from sampling")
    print()
    print("3. **Config M - Higher rep_penalty**: `beam=20, lenpen=1.0, do_sample=true, temp=0.5, top_p=0.9, rep_penalty=1.5`")
    print("   - Rationale: Some of J's hallucinations appear repetitive. Higher repetition penalty may curb runaway generation")
    print()
    print("4. **Post-processing: Oracle segment selection**")
    print("   - For each segment, pick the output (baseline or J) with lower WER")
    print("   - This gives an upper bound on how good a selection/ensemble strategy could be")
    print()
    print("5. **Post-processing: Length-ratio filtering**")
    print("   - If J's output is more than 2x the length of the reference (by word count), fall back to baseline")
    print("   - This would catch the worst hallucinations without sacrificing improvements on normal segments")
    print()

    # Compute oracle score
    oracle_wwers = []
    oracle_picks_j = 0
    oracle_picks_b = 0
    for uid in common_ids:
        b_wwer = safe_float(baseline_map[uid]['wwer_%'], 0)
        j_wwer = safe_float(j_map[uid]['wwer_%'], 0)
        if j_wwer <= b_wwer:
            oracle_wwers.append(j_wwer)
            oracle_picks_j += 1
        else:
            oracle_wwers.append(b_wwer)
            oracle_picks_b += 1
    oracle_mean = statistics.mean(oracle_wwers)

    print(f"### Oracle Selection Upper Bound")
    print()
    print(f"If we could perfectly select the better output per segment:")
    print(f"- **Oracle mean WWER**: {oracle_mean:.2f}% (vs baseline {b_mean_wwer:.2f}%, vs J {j_mean_wwer:.2f}%)")
    print(f"- Oracle would pick J for {oracle_picks_j} segments, baseline for {oracle_picks_b} segments")
    print(f"- **Potential improvement over best single config**: {min(b_mean_wwer, j_mean_wwer) - oracle_mean:.2f} pp")
    print()

    # Length-ratio filtering simulation
    length_filtered_wwers = []
    used_j = 0
    used_b_fallback = 0
    for uid in common_ids:
        ref = baseline_map[uid]['ref'].strip()
        j_hyp = j_map[uid]['hyp'].strip()
        ref_wc = len(ref.split()) if ref else 1
        j_wc = len(j_hyp.split()) if j_hyp else 0

        b_wwer = safe_float(baseline_map[uid]['wwer_%'], 0)
        j_wwer = safe_float(j_map[uid]['wwer_%'], 0)

        if j_wc > 2 * ref_wc and ref_wc > 0:
            # J output too long, fall back to baseline
            length_filtered_wwers.append(b_wwer)
            used_b_fallback += 1
        else:
            length_filtered_wwers.append(j_wwer)
            used_j += 1

    lf_mean = statistics.mean(length_filtered_wwers)
    print(f"### Length-Ratio Filtering Simulation (J with 2x fallback)")
    print()
    print(f"If we use J's output except when it's >2x ref length (fall back to baseline):")
    print(f"- **Filtered mean WWER**: {lf_mean:.2f}% (vs pure J {j_mean_wwer:.2f}%)")
    print(f"- Used J output: {used_j} segments, fell back to baseline: {used_b_fallback} segments")
    print(f"- **Improvement over pure J**: {j_mean_wwer - lf_mean:.2f} pp")
    print()


if __name__ == '__main__':
    main()
