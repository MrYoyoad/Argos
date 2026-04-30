#!/usr/bin/env python3
"""B3 correlation plot — Tier-2 (per-token model confidence) vs WER.

Reads the confidence-{fid}.json sidecar produced by VSP_OUTPUT_SCORES=1
decode and plots three correlations:

  1. Sequence score vs WER
  2. Mean per-word probability vs WER
  3. Min per-word probability vs WER

Output:
    presentation_materials_20260224/01_plots_for_slides/b3_correlation_plot.png

Run:
    python3 docs/_research-tools/generators/generate_b3_correlation_plot.py \
        --results-dir /tmp/vsp_b3_full_out
"""

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GENERATORS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GENERATORS_DIR))
from compute_word_confidence import aggregate_subtokens_to_words  # noqa: E402

REPO_ROOT = GENERATORS_DIR.parents[2]
OUT_PATH = REPO_ROOT / "presentation_materials_20260224" / "01_plots_for_slides" / "b3_correlation_plot.png"

# Brand palette
BG     = "#0d1b2a"
NAVY2  = "#152a40"
TEAL   = "#00b4d8"
GREEN  = "#4caf50"
GOLD   = "#ffd54f"
CORAL  = "#e06c75"
WHITE  = "#ffffff"
LGRAY  = "#aaaaaa"
MGRAY  = "#666666"


def _wer(ref: str, hyp: str) -> float:
    r = ref.lower().split()
    h = hyp.lower().split()
    if not r:
        return 100.0 if h else 0.0
    n = len(r)
    m = len(h)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): dp[i][0] = i
    for j in range(m + 1): dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if r[i - 1] == h[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1])
    return dp[n][m] / n * 100


def _pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n; my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx * dy else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    hypo_files = [p for p in sorted(args.results_dir.glob("hypo-*.json"))
                  if "merged" not in p.name]
    if not hypo_files:
        raise SystemExit(f"no hypo-*.json in {args.results_dir}")
    hypo_path = hypo_files[0]
    fid = re.search(r"hypo-(\d+)\.json", hypo_path.name).group(1)
    conf_path = args.results_dir / f"confidence-{fid}.json"
    if not conf_path.exists():
        raise SystemExit(f"sidecar not found: {conf_path}")

    hypo = json.loads(hypo_path.read_text())
    conf = json.loads(conf_path.read_text())
    ids, refs, hyps = hypo["utt_id"], hypo["ref"], hypo["hypo"]

    rows = []
    for utt, ref, hyp in zip(ids, refs, hyps):
        seg = conf.get(utt)
        if not seg: continue
        seq_score = seg.get("sequence_score")
        words = aggregate_subtokens_to_words(seg.get("tokens", []))
        probs = [w["prob"] for w in words if w.get("prob") is not None]
        if not probs: continue
        rows.append({
            "wer": _wer(ref, hyp),
            "seq": seq_score,
            "mean_p": sum(probs) / len(probs),
            "min_p": min(probs),
        })

    if not rows:
        raise SystemExit("no valid segments after parsing")

    n = len(rows)
    seqs   = [r["seq"]    for r in rows if r["seq"] is not None]
    seq_w  = [r["wer"]    for r in rows if r["seq"] is not None]
    means  = [r["mean_p"] for r in rows]
    means_w = [r["wer"]   for r in rows]
    mins   = [r["min_p"]  for r in rows]
    mins_w = [r["wer"]    for r in rows]

    r_seq  = _pearson(seqs, seq_w) if len(seqs) >= 2 else 0
    r_mean = _pearson(means, means_w)
    r_min  = _pearson(mins, mins_w)

    fig = plt.figure(figsize=(15, 5), dpi=160)
    fig.patch.set_facecolor(BG)

    panels = [
        ("Sequence score", seqs, seq_w, r_seq, TEAL),
        ("Mean word prob", means, means_w, r_mean, GOLD),
        ("Min word prob",  mins, mins_w, r_min, CORAL),
    ]
    for i, (label, xs, ys, r, color) in enumerate(panels):
        ax = fig.add_subplot(1, 3, i + 1)
        ax.set_facecolor(NAVY2)
        ax.scatter(xs, ys, c=color, s=70, alpha=0.85, edgecolor=WHITE, linewidth=0.5)
        ax.set_xlabel(label, color=WHITE, fontsize=12)
        ax.set_ylabel("WER  (%)", color=WHITE, fontsize=12)
        ax.set_title(f"{label}  vs  WER  —  r = {r:+.3f}",
                     color=WHITE, fontsize=13, fontweight="bold", pad=10)
        ax.tick_params(colors=WHITE)
        for spine in ax.spines.values():
            spine.set_color(MGRAY)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, color=MGRAY, alpha=0.25)

    fig.suptitle(
        f"Tier-2 confidence vs WER  —  n={n} Obama bin Laden segments",
        color=WHITE, fontsize=13, y=0.99,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, facecolor=BG, dpi=160, bbox_inches="tight")
    print(f"Wrote {args.out}")
    print(f"  segments: {n}")
    print(f"  Pearson r(seq_score, WER)    = {r_seq:+.3f}")
    print(f"  Pearson r(mean_word_prob, WER) = {r_mean:+.3f}")
    print(f"  Pearson r(min_word_prob, WER)  = {r_min:+.3f}")
    verdict = "KEEP Tier-2 slide" if min(r_seq, r_mean, r_min) <= -0.4 else "DROP Tier-2 slide"
    print(f"  Decision gate (Pearson r <= -0.4): {verdict}")


if __name__ == "__main__":
    main()
