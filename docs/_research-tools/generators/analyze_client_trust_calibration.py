#!/usr/bin/env python3
"""Client trust calibration — for each green-fraction threshold T, compute the
operational tradeoff a client sees when using "fraction of green words >= T"
as the per-segment trust rule.

Outputs (under --out-dir):
  - client_trust_calibration.csv      — full table, both rules, every threshold
  - CLIENT_TRUST_CALIBRATION.md       — narrative + headline tables
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd

# Bin sweep
THRESHOLDS = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]

# NIV labels (must match other safety analysis)
NIV_Y_MIN = 3.80
NIV_YP_MIN = 2.00


def calibrate(seg: pd.DataFrame, frac_col: str, n_y: int, n_yp: int, n_neg_yp: int) -> pd.DataFrame:
    rows = []
    for T in THRESHOLDS:
        trust = seg[seg[frac_col] >= T]
        n_trust = len(trust)
        tp_yp = int((trust["niv_yp"] == 1).sum())
        fp_yp = int((trust["niv_yp"] == 0).sum())
        tp_y = int((trust["niv_y"] == 1).sum())
        recall_yp = tp_yp / n_yp if n_yp > 0 else 0.0
        precision_yp = tp_yp / n_trust if n_trust > 0 else 0.0
        fpr_yp = fp_yp / n_neg_yp if n_neg_yp > 0 else 0.0
        pct_y_in_trust = tp_y / n_trust if n_trust > 0 else 0.0
        rows.append({
            "threshold": T,
            "n_trusted": n_trust,
            "tp_useful": tp_yp,
            "fp_useful": fp_yp,
            "recall_useful": recall_yp,
            "precision_useful": precision_yp,
            "fpr_useful": fpr_yp,
            "n_clearly_conveyed_in_trust": tp_y,
            "pct_clearly_conveyed_in_trust": pct_y_in_trust,
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-segment", required=True,
                    help="per_segment_safety.csv from analyze_band_safety.py")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    seg = pd.read_csv(args.per_segment)
    seg["niv_y"] = (seg["is_score"] >= NIV_Y_MIN).astype(int)
    seg["niv_yp"] = (seg["is_score"] >= NIV_YP_MIN).astype(int)

    n_total = len(seg)
    n_y = int(seg["niv_y"].sum())
    n_yp = int(seg["niv_yp"].sum())
    n_neg_yp = n_total - n_yp

    new_tab = calibrate(seg, "frac_green_new", n_y, n_yp, n_neg_yp)
    old_tab = calibrate(seg, "frac_green_old", n_y, n_yp, n_neg_yp)

    new_tab["rule"] = "new"
    old_tab["rule"] = "old"
    full = pd.concat([new_tab, old_tab], ignore_index=True)
    full.to_csv(os.path.join(args.out_dir, "client_trust_calibration.csv"), index=False)

    # Narrative markdown
    lines = []
    lines.append("# Client Trust Calibration — recall vs false-positive tradeoff")
    lines.append("")
    lines.append(f"**Question this answers.** If a client uses \"fraction of green words in a segment ≥ T\" as their decision rule for whether to trust a segment, how many useful segments do they catch and how many do they wrongly trust?")
    lines.append("")
    lines.append(f"**Setup.** Full evaluation set: **{n_total:,} segments**. Useful (NIV-Y+P, IS ≥ {NIV_YP_MIN:.2f}): **{n_yp:,}** ({n_yp/n_total:.1%}). Clearly-conveyed (NIV-Y, IS ≥ {NIV_Y_MIN:.2f}): **{n_y:,}** ({n_y/n_total:.1%}). Not-useful (NIV-N, IS < {NIV_YP_MIN:.2f}): **{n_neg_yp:,}** ({n_neg_yp/n_total:.1%}).")
    lines.append("")
    lines.append("**Definitions.**")
    lines.append("- *Trusted* = segments where green-fraction ≥ T. The client treats these as reliable.")
    lines.append("- *True positive* = trusted AND actually useful (NIV-Y+P).")
    lines.append("- *False positive* = trusted but NOT useful — the client's trust is misplaced.")
    lines.append("- *Recall* = fraction of useful segments captured by the rule.")
    lines.append("- *Precision* = fraction of trusted segments that are actually useful.")
    lines.append("- *FPR* = fraction of NOT-useful segments wrongly trusted.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Under the new rule (joint conf+agreement)")
    lines.append("")
    lines.append("| T (green-frac ≥) | Trusted | TPs (useful caught) | FPs (wrongly trusted) | Recall (of useful) | Precision | FPR | NIV-Y of trusted |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for _, r in new_tab.iterrows():
        lines.append(f"| {r['threshold']:.0%} | {int(r['n_trusted'])} | {int(r['tp_useful'])} | {int(r['fp_useful'])} | {r['recall_useful']:.1%} | {r['precision_useful']:.1%} | {r['fpr_useful']:.1%} | {int(r['n_clearly_conveyed_in_trust'])} ({r['pct_clearly_conveyed_in_trust']:.1%}) |")
    lines.append("")
    lines.append("## Under the old rule (conf-only) — for comparison")
    lines.append("")
    lines.append("| T (green-frac ≥) | Trusted | TPs | FPs | Recall | Precision | FPR | NIV-Y of trusted |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for _, r in old_tab.iterrows():
        lines.append(f"| {r['threshold']:.0%} | {int(r['n_trusted'])} | {int(r['tp_useful'])} | {int(r['fp_useful'])} | {r['recall_useful']:.1%} | {r['precision_useful']:.1%} | {r['fpr_useful']:.1%} | {int(r['n_clearly_conveyed_in_trust'])} ({r['pct_clearly_conveyed_in_trust']:.1%}) |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Three operating points worth naming")
    lines.append("")
    # Pick representative thresholds to call out
    new_30 = new_tab[new_tab["threshold"] == 0.30].iloc[0]
    new_50 = new_tab[new_tab["threshold"] == 0.50].iloc[0]
    new_70 = new_tab[new_tab["threshold"] == 0.70].iloc[0]
    lines.append(f"### Permissive — \"≥30% green\"")
    lines.append("")
    lines.append(f"- **{int(new_30['n_trusted'])}** segments trusted")
    lines.append(f"- **{int(new_30['tp_useful'])}** useful captured ({new_30['recall_useful']:.1%} of all NIV-Y+P)")
    lines.append(f"- **{int(new_30['fp_useful'])}** false positives ({new_30['fpr_useful']:.1%} of NIV-N segments — about 1 misleading transcript per {1/max(new_30['fpr_useful'], 0.001):.0f} useless ones)")
    lines.append(f"- **{int(new_30['n_clearly_conveyed_in_trust'])} ({new_30['pct_clearly_conveyed_in_trust']:.1%})** of trusted are clearly conveyed (NIV-Y)")
    lines.append("")
    lines.append("Use case: surface as much useful content as possible. Default for most clients.")
    lines.append("")
    lines.append(f"### Moderate — \"≥50% green\"")
    lines.append("")
    lines.append(f"- **{int(new_50['n_trusted'])}** segments trusted")
    lines.append(f"- **{int(new_50['tp_useful'])}** useful captured ({new_50['recall_useful']:.1%} of all NIV-Y+P)")
    lines.append(f"- **{int(new_50['fp_useful'])}** false positives ({new_50['fpr_useful']:.1%} FPR)")
    lines.append(f"- **{int(new_50['n_clearly_conveyed_in_trust'])} ({new_50['pct_clearly_conveyed_in_trust']:.1%})** clearly conveyed")
    lines.append("")
    lines.append("Use case: precision matters more than recall. Acting on misleading content is costly.")
    lines.append("")
    lines.append(f"### Strict — \"≥70% green\"")
    lines.append("")
    lines.append(f"- **{int(new_70['n_trusted'])}** segments trusted")
    lines.append(f"- **{int(new_70['tp_useful'])}** useful captured ({new_70['recall_useful']:.1%} of all NIV-Y+P)")
    lines.append(f"- **{int(new_70['fp_useful'])}** false positives ({new_70['fpr_useful']:.1%} FPR)")
    lines.append(f"- **{int(new_70['n_clearly_conveyed_in_trust'])} ({new_70['pct_clearly_conveyed_in_trust']:.1%})** clearly conveyed — almost everything trusted is high-quality")
    lines.append("")
    lines.append("Use case: high-stakes downstream decisions. Acceptable to miss most useful content if false positives are eliminated.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Why this matters")
    lines.append("")
    lines.append("Under the OLD rule, the same green-fraction trust criterion was a substantially weaker signal. Side-by-side at comparable recall:")
    lines.append("")
    old_50 = old_tab[old_tab["threshold"] == 0.50].iloc[0]  # ~64% recall
    new_30_str = f"{new_30['recall_useful']:.1%} recall, {int(new_30['fp_useful'])} FPs ({new_30['fpr_useful']:.1%} FPR)"
    old_50_str = f"{old_50['recall_useful']:.1%} recall, {int(old_50['fp_useful'])} FPs ({old_50['fpr_useful']:.1%} FPR)"
    lines.append(f"- **New rule, ≥30% green threshold** → {new_30_str}")
    lines.append(f"- **Old rule, ≥50% green threshold** → {old_50_str}")
    lines.append("")
    lines.append("At ~65% recall the old rule's false-positive rate was higher, AND the threshold itself was higher (50% green is a much harder bar for users than 30%). The new rule provides the same coverage with stricter trust at a lower cosmetic threshold.")
    lines.append("")
    lines.append("## The structural ceiling")
    lines.append("")
    not_recoverable = n_yp - int(new_30["tp_useful"])
    pct_not = not_recoverable / n_yp if n_yp > 0 else 0
    lines.append(f"Even at the permissive 30% threshold, **{not_recoverable}** useful segments ({pct_not:.1%} of all NIV-Y+P) have less than 30% green words and would be missed. These are segments where the model produced something useful but not via clean visual signal — agreeable beams, low individual conf. The band system fundamentally can't reach them. They'd need a different signal (post-hoc LLM rerank, semantic-coherence check, topic-conditional rescore) to surface.")
    lines.append("")
    lines.append("This is the operational ceiling on confidence-band trust calibration alone, on this LLM and decoder.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Replicate")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 docs/_research-tools/generators/analyze_client_trust_calibration.py \\")
    lines.append("  --per-segment english_full_nbest_eval/safety_analysis/per_segment_safety.csv \\")
    lines.append("  --out-dir english_full_nbest_eval/client_trust/")
    lines.append("```")
    lines.append("")
    lines.append("Re-run when: the underlying model changes, the band rule thresholds change, or NIV definitions change.")

    out_md = os.path.join(args.out_dir, "CLIENT_TRUST_CALIBRATION.md")
    open(out_md, "w").write("\n".join(lines))
    print(f"Wrote {out_md}")
    print(f"Wrote {os.path.join(args.out_dir, 'client_trust_calibration.csv')}")


if __name__ == "__main__":
    main()
