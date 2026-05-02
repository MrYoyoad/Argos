#!/usr/bin/env python3
"""Trust-check for the proposed POS-aware + beam-agreement band rule.

Produces three outputs that together decide whether the proposed
implementation is worth doing:

  1. Per-word-occurrence table (long form) with the columns the production
     fitter would consume.
  2. POS-stratified reliability curve: does conf still discriminate
     correctness at high values, separately for function vs content words?
  3. (top1_conf x beam_agreement) 2D table for content words: does the
     agreement axis carry signal that the conf axis alone misses, in the
     high-top1 regime where the content-word calibration is flat?

A short verdict markdown summarizes whether the experiment passes the
trust criteria. Run before writing any production code.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from _alignment import align_word_lists, split_words  # noqa: E402
from analyze_beam_variance import _word_confs_for_utt  # noqa: E402

FUNCTION_WORDS = frozenset(
    "the a an and or but if in on at to for of is am are was were be been being "
    "have has had do does did will would shall should may might can could "
    "i me my we us our you your he him his she her it its they them their "
    "that this these those who whom which what where when how not no nor "
    "so very too also just than more most such as with from by about between "
    "into through during before after above below up down out off over under "
    "again then once here there all each every both few many much some any "
    "other another same different new old don't didn't won't can't isn't aren't wasn't weren't "
    "i'm i've i'll you're you've you'll he's she's it's we're they're".split()
)


def pos_class(word: str) -> str:
    w = word.lower().strip()
    if not w:
        return "other"
    if w in FUNCTION_WORDS:
        return "function"
    if any(c.isdigit() for c in w):
        return "number"
    if len(w) <= 1:
        return "other"
    return "content"


def beam_agreement_per_position(top1_words: List[str], beam_words_list: List[List[str]]) -> List[float]:
    """For each position i in top1_words, fraction of 19 other beams whose
    aligned position emits the same word as top1.

    Aligns each beam to top1 once, then reads off the matched-pair counts.
    """
    n = len(top1_words)
    if n == 0:
        return []
    counts = [0] * n
    other_beams = beam_words_list[1:]  # skip top-1 itself
    n_beams = len(other_beams)
    if n_beams == 0:
        return [1.0] * n  # only one beam → trivially "agreed"

    top1_lc = [w.lower() for w in top1_words]
    for beam in other_beams:
        if not beam:
            continue
        pairs = align_word_lists(top1_lc, [w.lower() for w in beam])
        for ti, bi in pairs:
            if ti < 0 or bi < 0:
                continue
            if top1_lc[ti] == beam[bi].lower():
                counts[ti] += 1
    return [c / n_beams for c in counts]


def build_per_word_table(nbest, hypo, conf):
    """One row per top-1 word in the full set."""
    refs = {u: r for u, r in zip(hypo["utt_id"], hypo.get("ref", []))}

    rows = []
    n_segs = 0
    n_skipped = 0
    for utt_id, rec in nbest.items():
        hyps = rec.get("hypotheses") or []
        if not hyps:
            n_skipped += 1
            continue
        top1_words = split_words(hyps[0].get("text", ""))
        ref_words = split_words(refs.get(utt_id, ""))
        if not top1_words:
            n_skipped += 1
            continue

        # Per-word top-1 confidences (sub-token aggregated min)
        conf_words = _word_confs_for_utt(conf.get(utt_id))

        # Beam agreement per top-1 position
        beam_words_list = [split_words(h.get("text", "")) for h in hyps]
        agreement = beam_agreement_per_position(top1_words, beam_words_list)

        # Correctness via top1<->ref alignment
        correct_flags = [0] * len(top1_words)
        ref_lc = [w.lower() for w in ref_words]
        top1_lc = [w.lower() for w in top1_words]
        pairs = align_word_lists(ref_lc, top1_lc)
        for ri, hi in pairs:
            if ri < 0 or hi < 0:
                continue
            if ref_lc[ri] == top1_lc[hi]:
                correct_flags[hi] = 1

        # Segment-level mean conf (for stratification)
        seg_confs = [p for _, p in conf_words if p is not None]
        seg_mean = float(np.mean(seg_confs)) if seg_confs else None

        for i, w in enumerate(top1_words):
            cw = conf_words[i] if i < len(conf_words) else (w, None)
            top1_conf = cw[1]
            if top1_conf is None:
                continue
            agree = agreement[i] if i < len(agreement) else None
            rows.append({
                "utt_id": utt_id,
                "position": i,
                "word": w.lower(),
                "top1_conf": top1_conf,
                "beam_agreement": agree,
                "is_correct": correct_flags[i],
                "pos_class": pos_class(w),
                "seg_mean_conf": seg_mean,
            })
        n_segs += 1
    return pd.DataFrame(rows), n_segs, n_skipped


def reliability_curve(df: pd.DataFrame, bins: List[float]) -> pd.DataFrame:
    """P(correct) by conf bin, with N. Caller filters df by pos_class."""
    out = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        sub = df[(df["top1_conf"] >= lo) & (df["top1_conf"] < hi)]
        out.append({
            "bin_lo": lo,
            "bin_hi": hi,
            "n": int(len(sub)),
            "p_correct": float(sub["is_correct"].mean()) if len(sub) else None,
        })
    # Final closed bin
    sub = df[df["top1_conf"] >= bins[-1]]
    if len(sub):
        out.append({"bin_lo": bins[-1], "bin_hi": 1.001, "n": int(len(sub)),
                    "p_correct": float(sub["is_correct"].mean())})
    return pd.DataFrame(out)


def two_d_table(df: pd.DataFrame, conf_bins: List[float], agree_bins: List[float]) -> pd.DataFrame:
    """Cells: P(correct) and N at each (conf_bin, agree_bin).

    Bin boundaries are interpreted as left-edges; a closing right-edge of 1.001
    is appended automatically so the highest bin ([last_value, 1.001)) is always
    materialised. With conf_bins=[0, 0.65, 0.82, 0.90, 0.95] this yields five
    bins ending at [0.95, 1.001).
    """
    conf_edges = list(conf_bins) + [1.001]
    agree_edges = list(agree_bins) + [1.001]
    rows = []
    for clo, chi in zip(conf_edges[:-1], conf_edges[1:]):
        for alo, ahi in zip(agree_edges[:-1], agree_edges[1:]):
            sub = df[(df["top1_conf"] >= clo) & (df["top1_conf"] < chi)
                     & (df["beam_agreement"] >= alo) & (df["beam_agreement"] < ahi)]
            rows.append({
                "conf_lo": clo, "conf_hi": chi,
                "agree_lo": alo, "agree_hi": ahi,
                "n": int(len(sub)),
                "p_correct": float(sub["is_correct"].mean()) if len(sub) else None,
            })
    return pd.DataFrame(rows)


def fit_threshold(curve: pd.DataFrame, target_p_correct: float, min_n: int = 50):
    """Lowest bin_lo where p_correct >= target and n >= min_n."""
    qualifying = curve[(curve["p_correct"] >= target_p_correct) & (curve["n"] >= min_n)]
    if qualifying.empty:
        return None
    return float(qualifying["bin_lo"].iloc[0])


def render_2d_md(table: pd.DataFrame, title: str) -> str:
    """Pretty-print the 2D table as markdown."""
    pivot_p = table.pivot(index="conf_lo", columns="agree_lo", values="p_correct")
    pivot_n = table.pivot(index="conf_lo", columns="agree_lo", values="n")
    lines = [f"### {title}", "", "P(correct) (N in parens):", ""]
    cols = sorted(pivot_p.columns)
    header = "| top1_conf \\ agree | " + " | ".join(f"{c:.2f}+" for c in cols) + " |"
    sep = "|" + "---|" * (len(cols) + 1)
    lines.append(header)
    lines.append(sep)
    for idx in sorted(pivot_p.index):
        row = [f"**{idx:.2f}+**"]
        for c in cols:
            p = pivot_p.loc[idx, c] if c in pivot_p.columns else None
            n = pivot_n.loc[idx, c] if c in pivot_n.columns else 0
            if pd.isna(p) or n == 0:
                row.append(f"— (n=0)")
            else:
                row.append(f"{p:.2f} (n={int(n)})")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nbest", required=True)
    ap.add_argument("--hypo", required=True)
    ap.add_argument("--confidence", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    print(f"Loading {args.nbest} ...", flush=True)
    nbest = json.load(open(args.nbest))
    print(f"Loading {args.hypo} ...", flush=True)
    hypo = json.load(open(args.hypo))
    print(f"Loading {args.confidence} ...", flush=True)
    conf = json.load(open(args.confidence))

    print("Building per-word table (alignment-heavy, ~5-10 min) ...", flush=True)
    df, n_segs, n_skipped = build_per_word_table(nbest, hypo, conf)
    df.to_csv(os.path.join(args.out_dir, "per_word_diagnostic.csv"), index=False)
    print(f"Wrote per_word_diagnostic.csv: {len(df)} word-rows, {n_segs} segments, {n_skipped} skipped.", flush=True)

    # Filter to high-quality segments (segment mean >= 0.65 — below this, no policy applies)
    df_q = df[df["seg_mean_conf"] >= 0.65].dropna(subset=["top1_conf", "beam_agreement"])
    df_func = df_q[df_q["pos_class"] == "function"]
    df_cont = df_q[df_q["pos_class"] == "content"]

    # ---- 1. Independence check ----
    r_overall = float(np.corrcoef(df_q["top1_conf"], df_q["beam_agreement"])[0, 1])
    r_func = float(np.corrcoef(df_func["top1_conf"], df_func["beam_agreement"])[0, 1]) if len(df_func) > 1 else None
    r_cont = float(np.corrcoef(df_cont["top1_conf"], df_cont["beam_agreement"])[0, 1]) if len(df_cont) > 1 else None

    # ---- 2. Reliability curves ----
    bins = [0.0, 0.40, 0.55, 0.65, 0.75, 0.82, 0.89, 0.95, 0.98]
    cur_func = reliability_curve(df_func, bins)
    cur_cont = reliability_curve(df_cont, bins)
    cur_func.to_csv(os.path.join(args.out_dir, "reliability_curve_function.csv"), index=False)
    cur_cont.to_csv(os.path.join(args.out_dir, "reliability_curve_content.csv"), index=False)

    # Fitted thresholds for P(correct) >= 0.85
    t_func = fit_threshold(cur_func, 0.85)
    t_cont = fit_threshold(cur_cont, 0.85)

    # ---- 3. 2D table for content words ----
    conf_bins_2d = [0.0, 0.65, 0.82, 0.90, 0.95]
    agree_bins_2d = [0.0, 0.50, 0.80, 0.95]
    tab_cont = two_d_table(df_cont, conf_bins_2d, agree_bins_2d)
    tab_func = two_d_table(df_func, conf_bins_2d, agree_bins_2d)
    tab_cont.to_csv(os.path.join(args.out_dir, "agreement_x_conf_content.csv"), index=False)
    tab_func.to_csv(os.path.join(args.out_dir, "agreement_x_conf_function.csv"), index=False)

    # ---- 4. Trust verdict ----
    # Pass criteria:
    # A. r(top1_conf, beam_agreement) is < 0.85 (signals not redundant)
    # B. Content reliability curve is monotone-ish (T_content fittable for P>=0.85)
    # C. In content 2D: high-conf + high-agree is materially better than high-conf + low-agree (>= 15pp)
    pass_a = r_cont is not None and abs(r_cont) < 0.85
    pass_b = t_cont is not None
    # For C: take conf>=0.95 row, compare agreement<0.5 vs agreement>=0.95
    cell_high_high = tab_cont[(tab_cont["conf_lo"] >= 0.95) & (tab_cont["agree_lo"] >= 0.95)]
    cell_high_low = tab_cont[(tab_cont["conf_lo"] >= 0.95) & (tab_cont["agree_lo"] < 0.50)]
    delta_c = None
    pass_c = False
    if not cell_high_high.empty and not cell_high_low.empty:
        p_hh = cell_high_high["p_correct"].iloc[0]
        p_hl = cell_high_low["p_correct"].iloc[0]
        n_hh = cell_high_high["n"].iloc[0]
        n_hl = cell_high_low["n"].iloc[0]
        if pd.notna(p_hh) and pd.notna(p_hl) and n_hh >= 30 and n_hl >= 30:
            delta_c = p_hh - p_hl
            pass_c = delta_c >= 0.15

    # Markdown summary
    lines = []
    lines.append("# Confidence Signals — Trust Diagnostic")
    lines.append("")
    lines.append(f"Run on full-set n-best evaluation. Filtered to segments with seg_mean_conf >= 0.65 (below this no per-word policy applies).")
    lines.append("")
    lines.append(f"- Total word-rows kept: **{len(df_q)}** (function: {len(df_func)}, content: {len(df_cont)}, others dropped)")
    lines.append("")
    lines.append("## Test A — Independence: are top1_conf and beam_agreement redundant?")
    lines.append("")
    lines.append(f"- Pearson r overall: **{r_overall:+.3f}**")
    lines.append(f"- Pearson r within function words: **{r_func:+.3f}**" if r_func is not None else "")
    lines.append(f"- Pearson r within content words: **{r_cont:+.3f}**" if r_cont is not None else "")
    lines.append(f"- **Verdict: {'PASS' if pass_a else 'FAIL'}** (criterion: |r_cont| < 0.85; redundancy would mean adding agreement gives no new info)")
    lines.append("")
    lines.append("## Test B — Reliability curves: can we fit POS-aware thresholds at P(correct) >= 0.85?")
    lines.append("")
    lines.append("### Function words")
    lines.append("| top1_conf bin | n | P(correct) |")
    lines.append("|---|---|---|")
    for _, r in cur_func.iterrows():
        p = f"{r['p_correct']:.3f}" if pd.notna(r['p_correct']) else "—"
        lines.append(f"| {r['bin_lo']:.2f} – {r['bin_hi']:.2f} | {int(r['n'])} | {p} |")
    lines.append(f"\nFitted T_function (P>=0.85, n>=50): **{t_func if t_func is not None else 'NOT FITTABLE'}**")
    lines.append("")
    lines.append("### Content words")
    lines.append("| top1_conf bin | n | P(correct) |")
    lines.append("|---|---|---|")
    for _, r in cur_cont.iterrows():
        p = f"{r['p_correct']:.3f}" if pd.notna(r['p_correct']) else "—"
        lines.append(f"| {r['bin_lo']:.2f} – {r['bin_hi']:.2f} | {int(r['n'])} | {p} |")
    lines.append(f"\nFitted T_content (P>=0.85, n>=50): **{t_cont if t_cont is not None else 'NOT FITTABLE'}**")
    lines.append("")
    lines.append(f"**Verdict: {'PASS' if pass_b else 'FAIL'}** (criterion: a content threshold exists where P(correct) >= 0.85 with n >= 50)")
    lines.append("")
    lines.append("## Test C — 2D rescue: does beam-agreement add lift in the high-conf regime for content words?")
    lines.append("")
    lines.append(render_2d_md(tab_cont, "Content"))
    lines.append("")
    lines.append(render_2d_md(tab_func, "Function (for reference)"))
    lines.append("")
    if delta_c is not None:
        lines.append(f"P(correct | conf>=0.95 & agree>=0.95) − P(correct | conf>=0.95 & agree<0.50) = **{delta_c:+.2%}** "
                     f"(n_hh={int(cell_high_high['n'].iloc[0])}, n_hl={int(cell_high_low['n'].iloc[0])})")
    else:
        lines.append("Comparison cells did not have sufficient data (n>=30 each).")
    lines.append("")
    lines.append(f"**Verdict: {'PASS' if pass_c else 'FAIL'}** (criterion: >=15pp lift, n>=30 each cell)")
    lines.append("")
    lines.append("---")
    lines.append("")
    overall = pass_a and pass_b and pass_c
    lines.append(f"## Overall verdict: {'**PASS — proceed to implementation**' if overall else '**FAIL — kill or rescope**'}")
    lines.append("")
    if not overall:
        failed = []
        if not pass_a: failed.append("A (independence)")
        if not pass_b: failed.append("B (reliability)")
        if not pass_c: failed.append("C (2D rescue)")
        lines.append(f"Failed tests: {', '.join(failed)}.")

    summary_path = os.path.join(args.out_dir, "TRUST_DIAGNOSTIC.md")
    open(summary_path, "w").write("\n".join(lines))
    print(f"\nWrote {summary_path}")
    print(f"Overall verdict: {'PASS' if overall else 'FAIL'} (A={pass_a}, B={pass_b}, C={pass_c})")


if __name__ == "__main__":
    main()
