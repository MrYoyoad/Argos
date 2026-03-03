#!/usr/bin/env python3
"""
Context-aware LLM evaluation analysis.
Computes transition matrix (blind→context), net upgrade rates, per-topic deltas,
hallucination detection improvement, and cross-condition reliability.
"""

import csv
import json
import os
import re
from collections import defaultdict

# --- Paths ---
JUDGE_DIR = "/home/ubuntu/docs/evaluation/llm_judge"
CONTEXT_DIR = os.path.join(JUDGE_DIR, "context_eval")
RESULTS_CSV = os.path.join(JUDGE_DIR, "llm_judge_results.csv")
BLIND_AUTO_CSV = os.path.join(JUDGE_DIR, "auto_judgments.csv")
CONTEXT_AUTO_CSV = os.path.join(CONTEXT_DIR, "context_auto_judgments.csv")
BLIND_INDEX = os.path.join(JUDGE_DIR, "batch_index.json")
CONTEXT_INDEX = os.path.join(CONTEXT_DIR, "context_batch_index.json")


def load_blind_judgments():
    """Load blind judgments from results CSV (already analyzed) + auto N's."""
    judgments = {}  # utt_id -> {"blind": "Y"/"P"/"N", "blind_full": ..., ...}

    with open(RESULTS_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row["utt_id"]
            j = row.get("llm_judge", "").strip()
            j_full = row.get("llm_judge_full", "").strip()
            judgments[uid] = {
                "blind": j if j in ("Y", "P", "N") else None,
                "blind_full": j_full,
                "wer": float(row.get("wer_%", 0) or 0),
                "is_score": float(row.get("intelligibility_score", 0) or 0),
                "topic": row.get("topic", "Other").strip(),
                "failure_mode": row.get("failure_mode", "").strip(),
                "success_pattern": row.get("success_pattern", "").strip(),
                "ref": row.get("ref", ""),
                "hyp": row.get("hyp", ""),
                "display_name": row.get("display_name", uid),
            }

    # Auto N's (empty hypothesis)
    with open(BLIND_AUTO_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row["utt_id"]
            if uid not in judgments:
                judgments[uid] = {
                    "blind": "N", "blind_full": "N", "wer": 100.0,
                    "is_score": 0.0, "topic": "Other", "failure_mode": "",
                    "success_pattern": "", "ref": "", "hyp": "", "display_name": uid,
                }
            else:
                judgments[uid]["blind"] = "N"

    return judgments


def load_batch_judgments(judgments_dir, index_path, prefix=""):
    """Load judgments from batch judgment files. Returns {utt_id: (label, full)}."""
    result = {}

    with open(index_path) as f:
        index = json.load(f)

    for batch_key, entries in index.items():
        batch_num = batch_key.split("_")[-1]  # e.g., "01"
        jfile = os.path.join(judgments_dir, f"{prefix}batch_{batch_num}_judgments.txt")
        if not os.path.exists(jfile):
            continue

        # Parse judgment file
        batch_judgments = {}
        with open(jfile) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",", 1)
                if len(parts) == 2:
                    idx = int(parts[0])
                    label_full = parts[1].strip()
                    label = label_full[0] if label_full else "N"  # Y, P, or N
                    batch_judgments[idx] = (label, label_full)

        # Map index → utt_id
        for entry in entries:
            idx = entry["index"]
            uid = entry["utt_id"]
            if idx in batch_judgments:
                result[uid] = batch_judgments[idx]

    return result


def load_context_auto_judgments():
    """Load auto-N context judgments."""
    result = {}
    with open(CONTEXT_AUTO_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row["utt_id"]
            result[uid] = ("N", "N")
    return result


def normalize_label(label_str):
    """Normalize to Y/P/N."""
    if not label_str:
        return "N"
    c = label_str[0].upper()
    if c in ("Y", "P", "N"):
        return c
    return "N"


def main():
    print("Loading blind judgments...")
    blind = load_blind_judgments()

    print("Loading context judgments...")
    context_manual = load_batch_judgments(
        os.path.join(CONTEXT_DIR, "judgments"),
        CONTEXT_INDEX,
        prefix="context_"
    )
    context_auto = load_context_auto_judgments()
    context = {**context_auto, **context_manual}  # manual takes precedence

    print(f"Blind judgments: {len(blind)}")
    print(f"Context judgments: {len(context)}")

    # Build paired dataset
    paired = []
    missing_context = []
    for uid, bdata in blind.items():
        b_label = normalize_label(bdata.get("blind", ""))
        if uid in context:
            c_label, c_full = context[uid]
            c_label = normalize_label(c_label)
            paired.append({
                "utt_id": uid,
                "blind": b_label,
                "context": c_label,
                "context_full": c_full,
                "wer": bdata["wer"],
                "is_score": bdata["is_score"],
                "topic": bdata["topic"],
                "failure_mode": bdata["failure_mode"],
                "success_pattern": bdata["success_pattern"],
                "ref": bdata["ref"],
                "hyp": bdata["hyp"],
                "display_name": bdata["display_name"],
            })
        else:
            missing_context.append(uid)

    print(f"Paired: {len(paired)} | Missing context: {len(missing_context)}")

    # ---- 1. Overall distributions ----
    blind_dist = defaultdict(int)
    context_dist = defaultdict(int)
    for r in paired:
        blind_dist[r["blind"]] += 1
        context_dist[r["context"]] += 1

    n = len(paired)
    print(f"\n=== OVERALL DISTRIBUTIONS (n={n}) ===")
    for lbl in ["Y", "P", "N"]:
        b = blind_dist[lbl]
        c = context_dist[lbl]
        print(f"  {lbl}: Blind={b} ({b/n*100:.1f}%)  Context={c} ({c/n*100:.1f}%)  Delta={c-b:+d}")

    # ---- 2. Transition matrix ----
    trans = defaultdict(lambda: defaultdict(int))
    for r in paired:
        trans[r["blind"]][r["context"]] += 1

    print(f"\n=== TRANSITION MATRIX (Blind → Context) ===")
    print(f"{'Blind\\Context':<15} {'→Y':>8} {'→P':>8} {'→N':>8} {'Total':>8}")
    for b_lbl in ["Y", "P", "N"]:
        row_total = sum(trans[b_lbl].values())
        if row_total == 0:
            continue
        y_n = trans[b_lbl]["Y"]
        p_n = trans[b_lbl]["P"]
        n_n = trans[b_lbl]["N"]
        print(f"  {b_lbl:<13} {y_n:>8} {p_n:>8} {n_n:>8} {row_total:>8}")

    # ---- 3. Net upgrades vs downgrades ----
    label_order = {"Y": 2, "P": 1, "N": 0}
    upgrades = sum(1 for r in paired if label_order[r["context"]] > label_order[r["blind"]])
    downgrades = sum(1 for r in paired if label_order[r["context"]] < label_order[r["blind"]])
    stable = n - upgrades - downgrades

    print(f"\n=== NET TRANSITIONS ===")
    print(f"  Upgrades (context > blind): {upgrades} ({upgrades/n*100:.1f}%)")
    print(f"  Stable (no change):         {stable} ({stable/n*100:.1f}%)")
    print(f"  Downgrades (context < blind): {downgrades} ({downgrades/n*100:.1f}%)")
    print(f"  Net upgrades: {upgrades-downgrades:+d} ({(upgrades-downgrades)/n*100:+.1f}%)")

    # ---- 4. Capture rates ----
    blind_captured = sum(1 for r in paired if r["blind"] in ("Y", "P"))
    context_captured = sum(1 for r in paired if r["context"] in ("Y", "P"))
    blind_full = sum(1 for r in paired if r["blind"] == "Y")
    context_full = sum(1 for r in paired if r["context"] == "Y")

    print(f"\n=== CAPTURE RATES ===")
    print(f"  Full capture (Y):  Blind={blind_full} ({blind_full/n*100:.1f}%)  Context={context_full} ({context_full/n*100:.1f}%)  Delta={context_full-blind_full:+d}")
    print(f"  Any capture (Y+P): Blind={blind_captured} ({blind_captured/n*100:.1f}%)  Context={context_captured} ({context_captured/n*100:.1f}%)  Delta={context_captured-blind_captured:+d}")

    # ---- 5. Per-topic analysis ----
    topic_data = defaultdict(lambda: {"blind_Y": 0, "blind_P": 0, "blind_N": 0,
                                       "ctx_Y": 0, "ctx_P": 0, "ctx_N": 0, "n": 0})
    for r in paired:
        t = r["topic"] or "Other"
        topic_data[t]["n"] += 1
        topic_data[t][f"blind_{r['blind']}"] += 1
        topic_data[t][f"ctx_{r['context']}"] += 1

    print(f"\n=== PER-TOPIC CONTEXT BENEFIT ===")
    print(f"{'Topic':<28} {'N':>5} {'Blind_YP':>9} {'Ctx_YP':>8} {'Delta':>7} {'Blind_Y':>8} {'Ctx_Y':>7}")
    for t, d in sorted(topic_data.items(), key=lambda x: -x[1]["n"]):
        tn = d["n"]
        b_yp = d["blind_Y"] + d["blind_P"]
        c_yp = d["ctx_Y"] + d["ctx_P"]
        b_y = d["blind_Y"]
        c_y = d["ctx_Y"]
        delta = c_yp - b_yp
        print(f"  {t:<26} {tn:>5} {b_yp:>8} ({b_yp/tn*100:4.0f}%) {c_yp:>5} ({c_yp/tn*100:4.0f}%) {delta:>+6}  {b_y:>4} ({b_y/tn*100:3.0f}%)  {c_y:>3} ({c_y/tn*100:3.0f}%)")

    # ---- 6. Hallucination detection ----
    # Hallucinated = WER >= 100 in blind eval
    hallu = [r for r in paired if r["wer"] >= 100.0]
    hallu_blind_N = sum(1 for r in hallu if r["blind"] == "N")
    hallu_ctx_N = sum(1 for r in hallu if r["context"] == "N")

    print(f"\n=== HALLUCINATION DETECTION (WER >= 100%) ===")
    print(f"  Hallucinated segments: {len(hallu)}")
    print(f"  Blind N-rate: {hallu_blind_N}/{len(hallu)} ({hallu_blind_N/len(hallu)*100:.1f}%)")
    print(f"  Context N-rate: {hallu_ctx_N}/{len(hallu)} ({hallu_ctx_N/len(hallu)*100:.1f}%)")
    print(f"  Delta: {hallu_ctx_N-hallu_blind_N:+d} ({(hallu_ctx_N-hallu_blind_N)/len(hallu)*100:+.1f}%)")

    # Hallucinations that blind missed (P or Y) but context caught (N)
    hallu_caught = [r for r in hallu if r["blind"] in ("Y","P") and r["context"] == "N"]
    print(f"  Newly caught by context: {len(hallu_caught)}")

    # ---- 7. Cross-condition reliability on duplicates ----
    # Load index to find duplicates
    with open(CONTEXT_INDEX) as f:
        ctx_index = json.load(f)

    dup_uids = set()
    for entries in ctx_index.values():
        for e in entries:
            if e.get("is_duplicate"):
                dup_uids.add(e["utt_id"])

    dups = [r for r in paired if r["utt_id"] in dup_uids]
    if dups:
        agree = sum(1 for r in dups if r["blind"] == r["context"])
        print(f"\n=== CROSS-CONDITION RELIABILITY (duplicate pairs) ===")
        print(f"  Duplicate segments in context eval: {len(dups)}")
        print(f"  Agreement (blind==context): {agree}/{len(dups)} ({agree/len(dups)*100:.1f}%)")

        # Blind intra-rater (from original analysis)
        print(f"  Blind intra-rater (from prior analysis): 86.7%")

        # Show cross-condition transition for dups
        dup_trans = defaultdict(lambda: defaultdict(int))
        for r in dups:
            dup_trans[r["blind"]][r["context"]] += 1
        print(f"  Dup transition (blind→context):")
        for b in ["Y","P","N"]:
            row = dup_trans[b]
            total = sum(row.values())
            if total > 0:
                print(f"    {b}: →Y={row['Y']}, →P={row['P']}, →N={row['N']} (n={total})")

    # ---- 8. Failure mode analysis ----
    mode_data = defaultdict(lambda: {"blind_N": 0, "ctx_N": 0, "n": 0})
    for r in paired:
        m = r["failure_mode"] or "success"
        mode_data[m]["n"] += 1
        if r["blind"] == "N":
            mode_data[m]["blind_N"] += 1
        if r["context"] == "N":
            mode_data[m]["ctx_N"] += 1

    print(f"\n=== FAILURE MODE ANALYSIS ===")
    print(f"{'Failure Mode':<35} {'N':>5} {'Blind_N':>9} {'Ctx_N':>8} {'Delta':>7}")
    for m, d in sorted(mode_data.items(), key=lambda x: -x[1]["n"]):
        mn = d["n"]
        bn = d["blind_N"]
        cn = d["ctx_N"]
        print(f"  {m:<33} {mn:>5} {bn:>8} ({bn/mn*100:4.0f}%) {cn:>5} ({cn/mn*100:4.0f}%) {cn-bn:>+6}")

    # ---- 9. Curated transition examples ----
    # N→Y and N→P upgrades (context helps most)
    n_to_y = [r for r in paired if r["blind"] == "N" and r["context"] == "Y"]
    n_to_p = [r for r in paired if r["blind"] == "N" and r["context"] == "P"]
    y_to_n = [r for r in paired if r["blind"] == "Y" and r["context"] == "N"]
    p_to_y = [r for r in paired if r["blind"] == "P" and r["context"] == "Y"]

    print(f"\n=== TRANSITION EXAMPLES ===")
    print(f"  N→Y (context rescues): {len(n_to_y)}")
    print(f"  N→P (context partially rescues): {len(n_to_p)}")
    print(f"  P→Y (context confirms full): {len(p_to_y)}")
    print(f"  Y→N (context reveals hallucination): {len(y_to_n)}")

    # Print a few examples of each
    for label, examples in [("N→Y", n_to_y[:3]), ("Y→N", y_to_n[:3])]:
        print(f"\n  --- {label} examples ---")
        for r in examples:
            print(f"    [{r['topic']}] WER={r['wer']:.0f}%")
            print(f"    REF: {r['ref'][:80]}")
            print(f"    HYP: {r['hyp'][:80]}")
            print(f"    Context: {r['context_full']}")
            print()

    # ---- 10. Save results CSV ----
    out_csv = os.path.join(CONTEXT_DIR, "context_eval_results.csv")
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "utt_id", "display_name", "topic", "wer", "is_score",
            "failure_mode", "success_pattern",
            "blind", "context", "context_full",
            "transition", "upgrade", "ref", "hyp"
        ])
        writer.writeheader()
        for r in paired:
            bord = label_order[r["blind"]]
            cord = label_order[r["context"]]
            transition = f"{r['blind']}→{r['context']}"
            upgrade = cord - bord  # +1 upgrade, 0 stable, -1 downgrade
            writer.writerow({
                "utt_id": r["utt_id"],
                "display_name": r["display_name"],
                "topic": r["topic"],
                "wer": r["wer"],
                "is_score": r["is_score"],
                "failure_mode": r["failure_mode"],
                "success_pattern": r["success_pattern"],
                "blind": r["blind"],
                "context": r["context"],
                "context_full": r["context_full"],
                "transition": transition,
                "upgrade": upgrade,
                "ref": r["ref"],
                "hyp": r["hyp"],
            })
    print(f"\nSaved results to {out_csv}")

    # ---- 11. Summary JSON ----
    summary = {
        "analysis_date": "2026-03-03",
        "total_pairs": n,
        "blind_distribution": {lbl: {"count": blind_dist[lbl], "pct": round(blind_dist[lbl]/n*100, 1)} for lbl in ["Y","P","N"]},
        "context_distribution": {lbl: {"count": context_dist[lbl], "pct": round(context_dist[lbl]/n*100, 1)} for lbl in ["Y","P","N"]},
        "capture_rates": {
            "blind_full_Y": round(blind_full/n*100, 1),
            "context_full_Y": round(context_full/n*100, 1),
            "blind_any_YP": round(blind_captured/n*100, 1),
            "context_any_YP": round(context_captured/n*100, 1),
            "delta_full_Y": round((context_full-blind_full)/n*100, 1),
            "delta_any_YP": round((context_captured-blind_captured)/n*100, 1),
        },
        "net_transitions": {
            "upgrades": upgrades,
            "upgrades_pct": round(upgrades/n*100, 1),
            "stable": stable,
            "stable_pct": round(stable/n*100, 1),
            "downgrades": downgrades,
            "downgrades_pct": round(downgrades/n*100, 1),
            "net": upgrades - downgrades,
            "net_pct": round((upgrades-downgrades)/n*100, 1),
        },
        "transition_matrix": {
            b: {c: trans[b][c] for c in ["Y","P","N"]} for b in ["Y","P","N"]
        },
        "hallucination_detection": {
            "total_hallucinated": len(hallu),
            "blind_N_rate_pct": round(hallu_blind_N/len(hallu)*100, 1) if hallu else 0,
            "context_N_rate_pct": round(hallu_ctx_N/len(hallu)*100, 1) if hallu else 0,
            "newly_caught_by_context": len(hallu_caught),
        },
        "cross_condition_reliability": {
            "duplicate_pairs": len(dups),
            "cross_condition_agreement_pct": round(agree/len(dups)*100, 1) if dups else 0,
            "blind_intra_rater_pct": 86.7,
        },
        "key_transitions": {
            "N_to_Y": len(n_to_y),
            "N_to_P": len(n_to_p),
            "P_to_Y": len(p_to_y),
            "Y_to_N": len(y_to_n),
        },
        "per_topic": {
            t: {
                "n": d["n"],
                "blind_YP_pct": round((d["blind_Y"]+d["blind_P"])/d["n"]*100, 1),
                "context_YP_pct": round((d["ctx_Y"]+d["ctx_P"])/d["n"]*100, 1),
                "delta_YP_pct": round(((d["ctx_Y"]+d["ctx_P"])-(d["blind_Y"]+d["blind_P"]))/d["n"]*100, 1),
            }
            for t, d in topic_data.items()
        }
    }

    out_json = os.path.join(CONTEXT_DIR, "context_eval_summary.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {out_json}")

    return summary


if __name__ == "__main__":
    main()
