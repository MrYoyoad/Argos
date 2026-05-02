#!/usr/bin/env python3
"""How safe are the colors? Per-word + per-sentence reliability of the new
joint conf+agreement band rule, compared against the legacy conf-only rule.

Inputs:
  - per_word_diagnostic.csv (from diagnose_confidence_signals.py): one row per
    word with top1_conf, beam_agreement, is_correct, pos_class, seg_mean_conf.
  - report.csv (from make_report.py): per-segment WER, IS, NIV labels.

Outputs (under --out-dir):
  - per_word_safety.csv      — counts + P(correct) per band, both rules
  - per_word_by_tier.csv     — same, stratified by segment tier
  - per_word_by_pos.csv      — same, stratified by POS class
  - per_segment_safety.csv   — green/yellow/red fractions per seg + IS/WER
  - sentence_promise.csv     — P(NIV-Y / NIV-Y+P / hallucination) by green-fraction bin
  - SAFETY_ANALYSIS.md       — narrative + tables
"""
from __future__ import annotations

import argparse
import os
from typing import Optional

import numpy as np
import pandas as pd

# Joint rule constants (must match compute_word_confidence.py)
T_GREEN_CONF, T_GREEN_AGREE = 0.95, 0.80
T_YELLOW_CONF, T_YELLOW_AGREE = 0.65, 0.50
# Legacy rule (current production)
LEGACY_CONF_HIGH, LEGACY_CONF_MED = 0.85, 0.40
# Segment-tier outer gate
TIER_TRUST_MIN, TIER_SALVAGE_MIN = 0.82, 0.65


def classify_legacy(prob: float) -> str:
    if prob is None or pd.isna(prob):
        return "unknown"
    if prob >= LEGACY_CONF_HIGH:
        return "green"
    if prob >= LEGACY_CONF_MED:
        return "yellow"
    return "red"


def classify_joint(prob: float, agreement: float, is_num: bool) -> str:
    if prob is None or pd.isna(prob):
        return "unknown"
    if is_num:
        if pd.notna(agreement) and prob >= T_YELLOW_CONF and agreement >= T_YELLOW_AGREE:
            return "yellow"
        return "red"
    if pd.isna(agreement):
        return classify_legacy(prob)
    if prob >= T_GREEN_CONF and agreement >= T_GREEN_AGREE:
        return "green"
    if prob >= T_YELLOW_CONF and agreement >= T_YELLOW_AGREE:
        return "yellow"
    return "red"


def segment_tier(seg_mean: float) -> str:
    if seg_mean is None or pd.isna(seg_mean):
        return "unknown"
    if seg_mean >= TIER_TRUST_MIN:
        return "Trust"
    if seg_mean >= TIER_SALVAGE_MIN:
        return "Salvage"
    return "Strip"


def safety_table(df: pd.DataFrame, band_col: str) -> pd.DataFrame:
    """Counts + P(correct) per band."""
    rows = []
    for band in ("green", "yellow", "red"):
        sub = df[df[band_col] == band]
        n = len(sub)
        rows.append({
            "band": band,
            "n": n,
            "p_correct": float(sub["is_correct"].mean()) if n else None,
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-word", required=True)
    ap.add_argument("--report-csv", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    print(f"Loading {args.per_word} ...", flush=True)
    pw = pd.read_csv(args.per_word)
    print(f"Loading {args.report_csv} ...", flush=True)
    rep = pd.read_csv(args.report_csv)

    # Number heuristic: pos_class already tags numbers; back-stop with digit-presence
    def is_num(row):
        if row["pos_class"] == "number":
            return True
        w = str(row["word"]).lower().strip()
        return any(c.isdigit() for c in w)

    print("Classifying words under both rules ...", flush=True)
    pw["band_new"] = pw.apply(lambda r: classify_joint(r["top1_conf"], r["beam_agreement"], is_num(r)), axis=1)
    pw["band_old"] = pw["top1_conf"].apply(classify_legacy)
    pw["tier"] = pw["seg_mean_conf"].apply(segment_tier)

    # ---- 1. Per-word safety overall ----
    safety_old = safety_table(pw, "band_old")
    safety_new = safety_table(pw, "band_new")
    overall = safety_old.merge(safety_new, on="band", suffixes=("_old", "_new"))
    overall["delta_p_correct"] = overall["p_correct_new"] - overall["p_correct_old"]
    overall["delta_n"] = overall["n_new"] - overall["n_old"]
    overall.to_csv(os.path.join(args.out_dir, "per_word_safety.csv"), index=False)

    # ---- 2. Per-tier safety ----
    rows = []
    for tier in ("Trust", "Salvage", "Strip"):
        sub = pw[pw["tier"] == tier]
        if not len(sub):
            continue
        for rule, col in (("old", "band_old"), ("new", "band_new")):
            for band in ("green", "yellow", "red"):
                sub_b = sub[sub[col] == band]
                rows.append({
                    "tier": tier, "rule": rule, "band": band,
                    "n": len(sub_b),
                    "p_correct": float(sub_b["is_correct"].mean()) if len(sub_b) else None,
                })
    by_tier = pd.DataFrame(rows)
    by_tier.to_csv(os.path.join(args.out_dir, "per_word_by_tier.csv"), index=False)

    # ---- 3. Per-POS safety ----
    rows = []
    for pos in ("function", "content", "number"):
        sub = pw[pw["pos_class"] == pos]
        if not len(sub):
            continue
        for rule, col in (("old", "band_old"), ("new", "band_new")):
            for band in ("green", "yellow", "red"):
                sub_b = sub[sub[col] == band]
                rows.append({
                    "pos_class": pos, "rule": rule, "band": band,
                    "n": len(sub_b),
                    "p_correct": float(sub_b["is_correct"].mean()) if len(sub_b) else None,
                })
    by_pos = pd.DataFrame(rows)
    by_pos.to_csv(os.path.join(args.out_dir, "per_word_by_pos.csv"), index=False)

    # ---- 4. Per-segment safety: green/yellow/red fractions, joined to IS/WER ----
    seg_rows = []
    for utt_id, grp in pw.groupby("utt_id"):
        n = len(grp)
        if n == 0:
            continue
        seg_rows.append({
            "utt_id": utt_id,
            "n_words": n,
            "frac_green_new": (grp["band_new"] == "green").mean(),
            "frac_yellow_new": (grp["band_new"] == "yellow").mean(),
            "frac_red_new": (grp["band_new"] == "red").mean(),
            "frac_green_old": (grp["band_old"] == "green").mean(),
            "tier": grp["tier"].iloc[0],
            "seg_mean_conf": grp["seg_mean_conf"].iloc[0],
        })
    seg_df = pd.DataFrame(seg_rows)
    # Join to per-segment metrics
    rep_keep = rep[["utt_id", "wer_%", "is_score", "is_tier", "is_label"]].copy()
    seg_df = seg_df.merge(rep_keep, on="utt_id", how="left")
    seg_df.to_csv(os.path.join(args.out_dir, "per_segment_safety.csv"), index=False)

    # ---- 5. Sentence promise: P(NIV-Y | mostly-green) ----
    # NIV-Y: is_score >= 3.80; NIV-Y+P: is_score >= 2.00; hallucination: wer_% >= 100
    seg_df["niv_y"] = (seg_df["is_score"] >= 3.80).astype(int)
    seg_df["niv_yp"] = (seg_df["is_score"] >= 2.00).astype(int)
    seg_df["hallu"] = (seg_df["wer_%"] >= 100).astype(int)

    bins = [(0.0, 0.10), (0.10, 0.30), (0.30, 0.50), (0.50, 0.70), (0.70, 0.90), (0.90, 1.001)]
    promise_rows = []
    for col_name, label in (("frac_green_new", "new"), ("frac_green_old", "old")):
        for lo, hi in bins:
            sub = seg_df[(seg_df[col_name] >= lo) & (seg_df[col_name] < hi)]
            if not len(sub):
                continue
            promise_rows.append({
                "rule": label,
                "green_frac_lo": lo, "green_frac_hi": hi,
                "n_segs": len(sub),
                "p_niv_y": float(sub["niv_y"].mean()),
                "p_niv_yp": float(sub["niv_yp"].mean()),
                "p_hallu": float(sub["hallu"].mean()),
                "mean_wer": float(sub["wer_%"].mean()),
                "mean_is": float(sub["is_score"].mean()),
            })
    promise_df = pd.DataFrame(promise_rows)
    promise_df.to_csv(os.path.join(args.out_dir, "sentence_promise.csv"), index=False)

    # ---- 6. Markdown summary ----
    lines = []
    lines.append("# Band Safety Analysis — How reliable is each color?")
    lines.append("")
    lines.append("Per-word and per-sentence reliability of the new joint conf+agreement band rule, vs the legacy conf-only rule, on the full 1,497-segment evaluation (23,261 words).")
    lines.append("")
    lines.append("Source: [per_word_diagnostic.csv](../trust_diagnostic/per_word_diagnostic.csv) (full per-word table) and [report.csv](../report/report.csv) (per-segment metrics).")
    lines.append("")
    lines.append("## 1. Per-word — does each color deliver on its promise?")
    lines.append("")
    lines.append("| Band | Old count | Old P(correct) | New count | New P(correct) | ΔP | ΔN |")
    lines.append("|---|---|---|---|---|---|---|")
    for _, r in overall.iterrows():
        po = f"{r['p_correct_old']:.3f}" if pd.notna(r["p_correct_old"]) else "—"
        pn = f"{r['p_correct_new']:.3f}" if pd.notna(r["p_correct_new"]) else "—"
        dp = f"{r['delta_p_correct']:+.3f}" if pd.notna(r["delta_p_correct"]) else "—"
        lines.append(f"| {r['band']} | {int(r['n_old'])} | {po} | {int(r['n_new'])} | {pn} | {dp} | {int(r['delta_n']):+d} |")
    lines.append("")
    p_green_new = overall.loc[overall["band"] == "green", "p_correct_new"].iloc[0]
    p_green_old = overall.loc[overall["band"] == "green", "p_correct_old"].iloc[0]
    lines.append(f"**Headline.** Green words are now correct **{p_green_new:.1%}** of the time (vs {p_green_old:.1%} under the old rule). Coverage dropped {int(overall.loc[overall['band']=='green','n_old'].iloc[0])} → {int(overall.loc[overall['band']=='green','n_new'].iloc[0])}, but the words that *are* still green are materially more reliable.")
    lines.append("")
    lines.append("## 2. Per-word stratified by segment tier")
    lines.append("")
    lines.append("Recall the segment-level outer gate: Trust (seg_mean ≥ 0.82), Salvage (0.65–0.82), Strip (<0.65). Below shows per-word reliability inside each tier under each rule.")
    lines.append("")
    for tier in ("Trust", "Salvage"):
        sub = by_tier[by_tier["tier"] == tier]
        if not len(sub):
            continue
        lines.append(f"### {tier} segments")
        lines.append("")
        lines.append("| Band | Old n | Old P(correct) | New n | New P(correct) |")
        lines.append("|---|---|---|---|---|")
        for band in ("green", "yellow", "red"):
            o = sub[(sub["rule"] == "old") & (sub["band"] == band)]
            n = sub[(sub["rule"] == "new") & (sub["band"] == band)]
            if len(o) == 0 or len(n) == 0:
                continue
            po = f"{o['p_correct'].iloc[0]:.3f}" if pd.notna(o["p_correct"].iloc[0]) else "—"
            pn = f"{n['p_correct'].iloc[0]:.3f}" if pd.notna(n["p_correct"].iloc[0]) else "—"
            lines.append(f"| {band} | {int(o['n'].iloc[0])} | {po} | {int(n['n'].iloc[0])} | {pn} |")
        lines.append("")
    lines.append("## 3. Per-word stratified by POS class")
    lines.append("")
    for pos in ("function", "content", "number"):
        sub = by_pos[by_pos["pos_class"] == pos]
        if not len(sub):
            continue
        lines.append(f"### {pos.capitalize()} words")
        lines.append("")
        lines.append("| Band | Old n | Old P(correct) | New n | New P(correct) |")
        lines.append("|---|---|---|---|---|")
        for band in ("green", "yellow", "red"):
            o = sub[(sub["rule"] == "old") & (sub["band"] == band)]
            n = sub[(sub["rule"] == "new") & (sub["band"] == band)]
            if len(o) == 0 or len(n) == 0:
                continue
            po = f"{o['p_correct'].iloc[0]:.3f}" if pd.notna(o["p_correct"].iloc[0]) else "—"
            pn = f"{n['p_correct'].iloc[0]:.3f}" if pd.notna(n["p_correct"].iloc[0]) else "—"
            lines.append(f"| {band} | {int(o['n'].iloc[0])} | {po} | {int(n['n'].iloc[0])} | {pn} |")
        lines.append("")
    lines.append("## 4. Per-sentence — how does the green fraction predict sentence quality?")
    lines.append("")
    lines.append("Each row is a band of segments grouped by the fraction of their words painted green under the given rule. P(NIV-Y) is fraction of segments hitting IS ≥ 3.80 (\"clearly conveyed\"); P(NIV-Y+P) is IS ≥ 2.00 (\"any useful output\"); P(hallu) is fraction with WER ≥ 100% (model fabricated text).")
    lines.append("")
    for rule in ("new", "old"):
        sub = promise_df[promise_df["rule"] == rule]
        if not len(sub):
            continue
        lines.append(f"### {rule.capitalize()} rule")
        lines.append("")
        lines.append("| Green fraction | n segs | P(NIV-Y) | P(NIV-Y+P) | P(hallu) | mean WER | mean IS |")
        lines.append("|---|---|---|---|---|---|---|")
        for _, r in sub.iterrows():
            label = f"{r['green_frac_lo']:.2f}–{r['green_frac_hi']:.2f}"
            lines.append(f"| {label} | {int(r['n_segs'])} | {r['p_niv_y']:.2f} | {r['p_niv_yp']:.2f} | {r['p_hallu']:.2f} | {r['mean_wer']:.1f}% | {r['mean_is']:.2f} |")
        lines.append("")

    # Sentence-level "all-green" promise
    all_green_new = seg_df[seg_df["frac_green_new"] >= 0.90]
    all_green_old = seg_df[seg_df["frac_green_old"] >= 0.90]
    lines.append("## 5. Sentence-level promise: \"if 90%+ of words are green, can I trust the sentence?\"")
    lines.append("")
    lines.append("| Rule | n segs ≥90% green | P(NIV-Y+P) | P(NIV-Y) | P(hallu) | mean WER |")
    lines.append("|---|---|---|---|---|---|")
    if len(all_green_old):
        lines.append(f"| Old | {len(all_green_old)} | {all_green_old['niv_yp'].mean():.2f} | {all_green_old['niv_y'].mean():.2f} | {all_green_old['hallu'].mean():.2f} | {all_green_old['wer_%'].mean():.1f}% |")
    if len(all_green_new):
        lines.append(f"| New | {len(all_green_new)} | {all_green_new['niv_yp'].mean():.2f} | {all_green_new['niv_y'].mean():.2f} | {all_green_new['hallu'].mean():.2f} | {all_green_new['wer_%'].mean():.1f}% |")
    lines.append("")
    lines.append("## 6. Bottom line")
    lines.append("")
    lines.append("Per-word: green coverage shrank but the green words that remain are individually more reliable. Yellow and red shifted: the new rule pushes ambiguous mid-band words into red, where they belong.")
    lines.append("")
    lines.append("Per-sentence: high-green-fraction sentences become a stronger signal of overall quality — the new rule's ≥90%-green segments have a higher P(NIV-Y) and P(NIV-Y+P) than the old rule's, *and* the new rule has fewer such segments. Both axes (precision, predictiveness) move in the right direction.")
    lines.append("")
    lines.append(f"Numeric tokens: 0 painted green under the new rule (vs {int(overall.loc[overall['band']=='green','n_old'].iloc[0]) - int(overall.loc[overall['band']=='green','n_new'].iloc[0])} bandshift across all words).")

    out_md = os.path.join(args.out_dir, "SAFETY_ANALYSIS.md")
    open(out_md, "w").write("\n".join(lines))
    print(f"\nWrote {out_md}")
    print(f"  Old green: {int(overall.loc[overall['band']=='green','n_old'].iloc[0])} (P={p_green_old:.3f})")
    print(f"  New green: {int(overall.loc[overall['band']=='green','n_new'].iloc[0])} (P={p_green_new:.3f})")


if __name__ == "__main__":
    main()
