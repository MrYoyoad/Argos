#!/usr/bin/env python3
"""
Egla-Kafe — client-grade deck plots (matplotlib, Agg).

Produces five 150-dpi PNGs under
  /home/ubuntu/datasets/clients/egla_kafe/deliverables/plots/

  1. recovery_ladder.png   per-video context Y+P, horizontal bars, colored by
                           source (iPhone-4K vs client-camera), ranked best->worst.
  2. levers.png            grouped IS bars: iPhone-vs-camera AND angle (front/30/45)
                           with 95% CI error bars.
  3. category_trust.png    P(correct|green) by word category, tier-colored.
  4. confidence_gate.png   dual-axis: useful%(IS>=2) and WER vs confidence threshold.
  5. calibration.png       reliability diagram — per-word model prob bucket vs
                           empirical P(correct) (difflib align of hyp->ref words),
                           with the y=x diagonal.

Inputs: judgments/*.json, significance.json (built by egla_kafe_significance.py),
word_category_trust_ALL.json, the two report.csv files, and the two
word_confidence.json sidecars.

Conventions (STYLE_GUIDE Plot Styling, T5): fonts >=16pt, value labels, titles,
colorblind-safe palette, no top/right spines, white bar edges.

Run with the project venv:
  /home/ubuntu/vsp-llm-yoad-venv/bin/python \
    docs/_research-tools/generators/egla_kafe_deck_plots.py
"""

import csv
import difflib
import glob
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------- paths
EVAL = Path("/home/ubuntu/datasets/clients/egla_kafe/work/eval")
JUDGE = EVAL / "judge" / "judgments"
SIG = EVAL / "significance.json"
CAT = EVAL / "word_category_trust_ALL.json"
INDEX = EVAL / "index.json"
REP_S12 = EVAL / "run_scene12_all" / "report" / "report.csv"
REP_SHAAM = EVAL / "run_shaam_all" / "report" / "report.csv"
WC_S12 = Path("/home/ubuntu/flat_runs_archive/20260624_145832/client_outputs/report/word_confidence.json")
WC_SHAAM = Path("/home/ubuntu/flat_runs_archive/20260624_200135/client_outputs/report/word_confidence.json")
OUT = Path("/home/ubuntu/datasets/clients/egla_kafe/deliverables/plots")
OUT.mkdir(parents=True, exist_ok=True)

DPI = 150

# ---------------------------------------------------------------- palette (colorblind-safe)
# Okabe-Ito based — distinguishable for the common color-vision deficiencies.
C_IPHONE = "#0072B2"   # blue   — iPhone-4K (the good capture)
C_CAMERA = "#E69F00"   # orange — client camera (the weak capture)
C_USEFUL = "#0072B2"   # blue   — useful% line
C_WER = "#D55E00"      # vermillion — WER line
C_DIAG = "#999999"     # gray diagonal
C_POINT = "#0072B2"

# tier colors (TRUST / SALVAGE / STRIP, applied to category P(correct|green))
TIER_GREEN = "#2ca02c"   # >=70%  trust
TIER_YELLOW = "#E69F00"  # 50-70% salvage
TIER_RED = "#D55E00"     # <50%   strip

# ---------------------------------------------------------------- global rcParams (STYLE_GUIDE T5)
plt.rcParams.update({
    "font.size": 16,
    "axes.titlesize": 20,
    "axes.labelsize": 17,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "legend.fontsize": 15,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})


def _despine(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ---------------------------------------------------------------- shared loaders
def load_index_src():
    """stem -> source label ('iPhone-4K' | 'client-camera')."""
    d = json.load(open(INDEX))
    out = {}
    for e in d["entries"]:
        out[e["stem"]] = "iPhone-4K" if e["source_type"] == "master" else "client-camera"
    return out


_WORD_RE = re.compile(r"[a-z0-9']+")


def _tok(s):
    return _WORD_RE.findall((s or "").lower())


# ================================================================ PLOT 1
def plot_recovery_ladder():
    src = load_index_src()
    rows = []
    for f in glob.glob(str(JUDGE / "*.json")):
        d = json.load(open(f))
        stem = d["stem"]
        yp = d["overall"]["yp_pct"]
        rows.append((stem, yp, src.get(stem, "client-camera")))
    rows.sort(key=lambda r: r[1])  # ascending -> best ends up at top of barh

    stems = [r[0] for r in rows]
    yps = [r[1] for r in rows]
    colors = [C_IPHONE if r[2] == "iPhone-4K" else C_CAMERA for r in rows]

    fig, ax = plt.subplots(figsize=(12, 11))
    y = np.arange(len(stems))
    ax.barh(y, yps, color=colors, edgecolor="white", linewidth=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels(stems, fontsize=13)
    ax.set_xlabel("Context-aware understanding  (Y+P %  of turns a viewer grasps)")
    ax.set_title("Egla-Kafe — what a viewer can understand, per video\n"
                 "(context-aware LLM judge; ranked worst → best)", fontsize=19)
    ax.set_xlim(0, max(yps) * 1.18)
    for yi, v in zip(y, yps):
        ax.text(v + max(yps) * 0.01, yi, f"{v:.0f}%", va="center", ha="left",
                fontsize=12, fontweight="bold")
    _despine(ax)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=C_IPHONE),
        plt.Rectangle((0, 0), 1, 1, color=C_CAMERA),
    ]
    ax.legend(handles, ["iPhone-4K (sharp, frontal)", "client camera (380px screen-rec)"],
              loc="lower right", frameon=True)
    fig.tight_layout()
    p = OUT / "recovery_ladder.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return p


# ================================================================ PLOT 2
def plot_levers():
    sig = json.load(open(SIG))

    # left panel: iPhone vs camera
    iv = sig["iphone_vs_camera"]
    cap_groups = [
        ("iPhone-4K", iv["iPhone_4K"], C_IPHONE),
        ("client\ncamera", iv["client_camera"], C_CAMERA),
    ]
    # right panel: angle
    ag = sig["angle_front_30_45"]["groups"]
    angle_groups = [
        ("front", ag["front"], C_IPHONE),
        ("30°", ag["30"], "#56B4E9"),
        ("45°", ag["45"], C_CAMERA),
    ]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 6.5),
                                   gridspec_kw={"width_ratios": [2, 3]})

    def draw(ax, groups, title):
        xs = np.arange(len(groups))
        means = [g[1]["mean_is"] for g in groups]
        ci = [g[1]["ci95"] for g in groups]
        err_lo = [m - c[0] for m, c in zip(means, ci)]
        err_hi = [c[1] - m for m, c in zip(means, ci)]
        colors = [g[2] for g in groups]
        ns = [g[1]["n"] for g in groups]
        bars = ax.bar(xs, means, yerr=[err_lo, err_hi], capsize=7,
                      color=colors, edgecolor="white", linewidth=1.5,
                      error_kw={"elinewidth": 2, "ecolor": "#333333"})
        ax.set_xticks(xs)
        ax.set_xticklabels([g[0] for g in groups])
        ax.set_title(title, fontsize=18)
        ax.axhline(2.0, ls="--", lw=1.5, color="#888888")
        ax.text(len(groups) - 0.5, 2.04, "useful (IS≥2)", ha="right", va="bottom",
                fontsize=12, color="#666666")
        for x, m, n in zip(xs, means, ns):
            ax.text(x, m + max(means) * 0.04 + err_hi[xs.tolist().index(x)],
                    f"{m:.2f}\nn={n}", ha="center", va="bottom",
                    fontsize=13, fontweight="bold")
        ax.set_ylim(0, 2.6)
        _despine(ax)

    draw(axL, cap_groups, "Capture quality")
    draw(axR, angle_groups, "Camera angle (scene 1+2)")
    axL.set_ylabel("Intelligibility Score (0–5)")
    fig.suptitle("Egla-Kafe — the two big levers: capture quality & frontality\n"
                 "(mean IS, 95% bootstrap CIs)", fontsize=19, y=1.02)
    fig.tight_layout()
    p = OUT / "levers.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return p


# ================================================================ PLOT 3
def plot_category_trust():
    cat = json.load(open(CAT))["precision_trust"]["green"]
    order = ["NOUN", "NUMBER", "VERB", "FUNCTION", "ADJ_ADV", "ENTITY"]
    labels = {"NOUN": "NOUN\n(common)", "NUMBER": "NUMBER\n/date", "VERB": "VERB",
              "FUNCTION": "FUNCTION\nwords", "ADJ_ADV": "ADJ / ADV", "ENTITY": "ENTITY\n(names/places)"}
    vals = [(labels[c], cat[c]["p_correct"], cat[c]["n"]) for c in order if c in cat]

    def tier_color(v):
        if v >= 70:
            return TIER_GREEN
        if v >= 50:
            return TIER_YELLOW
        return TIER_RED

    fig, ax = plt.subplots(figsize=(12, 6.8))
    xs = np.arange(len(vals))
    heights = [v[1] for v in vals]
    colors = [tier_color(v[1]) for v in vals]
    ax.bar(xs, heights, color=colors, edgecolor="white", linewidth=1.5)
    ax.set_xticks(xs)
    ax.set_xticklabels([v[0] for v in vals])
    ax.set_ylabel("P(correct | high-confidence word)  %")
    ax.set_title("Egla-Kafe — what to trust in a gated output\n"
                 "accuracy of GREEN (high-confidence) words, by category", fontsize=19)
    ax.set_ylim(0, 100)
    for x, (lbl, v, n) in zip(xs, vals):
        ax.text(x, v + 2, f"{v:.0f}%\nn={n}", ha="center", va="bottom",
                fontsize=13, fontweight="bold")
    ax.axhline(70, ls="--", lw=1.2, color=TIER_GREEN, alpha=0.7)
    ax.axhline(50, ls="--", lw=1.2, color=TIER_RED, alpha=0.7)
    _despine(ax)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=TIER_GREEN),
        plt.Rectangle((0, 0), 1, 1, color=TIER_YELLOW),
        plt.Rectangle((0, 0), 1, 1, color=TIER_RED),
    ]
    ax.legend(handles, ["Trust (≥70%)", "Salvage (50–70%)", "Strip (<50%)"],
              loc="upper right", frameon=True, title="Tier")
    fig.text(0.5, -0.02,
             "Entities (names/places) are a black hole: 0% correct AND confidently hallucinated — never trust a proper noun.",
             ha="center", fontsize=12, color="#555555", style="italic")
    fig.tight_layout()
    p = OUT / "category_trust.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return p


# ================================================================ PLOT 4
def plot_confidence_gate():
    sig = json.load(open(SIG))
    gate = sig["confidence_gate_scene12"]
    thr_keys = ["0.5", "0.6", "0.7", "0.8"]
    # include ungated as left anchor at "ALL"
    xs = [0.45, 0.5, 0.6, 0.7, 0.8]
    xticklabels = ["ALL", "≥0.5", "≥0.6", "≥0.7", "≥0.8"]
    useful = [gate["ungated"]["useful_pct_is_ge_2"]] + \
             [gate["thresholds"][k]["useful_pct_is_ge_2"] for k in thr_keys]
    wer = [gate["ungated"]["mean_wer"]] + \
          [gate["thresholds"][k]["mean_wer"] for k in thr_keys]
    kept = [gate["ungated"]["kept_pct"]] + \
           [gate["thresholds"][k]["kept_pct"] for k in thr_keys]

    fig, ax1 = plt.subplots(figsize=(12, 6.8))
    ax2 = ax1.twinx()

    l1, = ax1.plot(xs, useful, "-o", color=C_USEFUL, lw=3, ms=11, label="Useful % (IS ≥ 2)")
    l2, = ax2.plot(xs, wer, "-s", color=C_WER, lw=3, ms=10, label="WER % (lower is better)")

    ax1.set_xticks(xs)
    ax1.set_xticklabels(xticklabels)
    ax1.set_xlabel("Confidence gate  (keep segments with mean word-prob ≥ threshold)")
    ax1.set_ylabel("Useful %  (IS ≥ 2)", color=C_USEFUL)
    ax2.set_ylabel("WER %", color=C_WER)
    ax1.tick_params(axis="y", colors=C_USEFUL)
    ax2.tick_params(axis="y", colors=C_WER)
    ax1.set_ylim(0, 100)
    ax2.set_ylim(0, 140)
    ax1.set_title("Egla-Kafe — confidence gate: trade coverage for quality\n"
                  "the model knows when it is right", fontsize=19)

    # value labels + kept% annotation
    for x, u, w, k in zip(xs, useful, wer, kept):
        ax1.annotate(f"{u:.0f}%", (x, u), textcoords="offset points", xytext=(0, 12),
                     ha="center", fontsize=12, fontweight="bold", color=C_USEFUL)
        ax2.annotate(f"{w:.0f}", (x, w), textcoords="offset points", xytext=(0, -20),
                     ha="center", fontsize=12, fontweight="bold", color=C_WER)
        ax1.annotate(f"keeps {k:.0f}%", (x, 2), textcoords="offset points", xytext=(0, 0),
                     ha="center", va="bottom", fontsize=10.5, color="#555555")

    _despine(ax1)
    ax2.spines["top"].set_visible(False)
    ax1.legend(handles=[l1, l2], loc="upper left", frameon=True,
               bbox_to_anchor=(0.02, 0.98))
    fig.tight_layout()
    p = OUT / "confidence_gate.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return p


# ================================================================ PLOT 5
def _correct_word_flags(hyp, ref):
    """Per hyp word -> 1 if difflib aligns it 'equal' to a ref word, else 0."""
    h, r = _tok(hyp), _tok(ref)
    flags = [0] * len(h)
    sm = difflib.SequenceMatcher(a=h, b=r, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                flags[i] = 1
    return flags


def plot_calibration():
    # build (prob, correct) pairs over all scored segments, both runs
    pairs = []
    for rep_path, wc_path in ((REP_S12, WC_S12), (REP_SHAAM, WC_SHAAM)):
        wc = json.load(open(wc_path))
        with open(rep_path, newline="") as f:
            for row in csv.DictReader(f):
                ref = row["ref"].strip()
                if ref == "":
                    continue  # no ground truth
                utt = row["utt_id"]
                words = wc.get(utt, {}).get("words", [])
                if not words:
                    continue
                hyp_words = [w["word"] for w in words]
                flags = _correct_word_flags(" ".join(hyp_words), ref)
                # SequenceMatcher tokenizes via _tok; re-tokenize hyp to align flags
                # to per-word probs. hyp_words from word_confidence may differ from
                # _tok output (punctuation etc.), so align defensively by index.
                ht = _tok(" ".join(hyp_words))
                if len(ht) != len(flags):
                    continue
                # map back: word_confidence words are already clean tokens in practice
                for w, fl in zip(words, flags):
                    pairs.append((w["prob"], fl))

    probs = np.array([p for p, _ in pairs])
    corr = np.array([c for _, c in pairs])

    # 10 equal-width buckets on [0,1]
    edges = np.linspace(0, 1, 11)
    centers, emp, counts = [], [], []
    for i in range(10):
        lo, hi = edges[i], edges[i + 1]
        m = (probs >= lo) & (probs < hi if i < 9 else probs <= hi)
        if m.sum() >= 5:
            centers.append((lo + hi) / 2)
            emp.append(corr[m].mean())
            counts.append(int(m.sum()))

    fig, ax = plt.subplots(figsize=(11, 8))
    ax.plot([0, 1], [0, 1], "--", color=C_DIAG, lw=2, label="perfect calibration")
    sizes = [40 + 4 * np.sqrt(c) * 6 for c in counts]
    ax.scatter(centers, emp, s=sizes, color=C_POINT, edgecolor="white",
               linewidth=1.5, zorder=5, label="observed")
    ax.plot(centers, emp, "-", color=C_POINT, lw=2, alpha=0.6, zorder=4)
    for x, y, c in zip(centers, emp, counts):
        ax.annotate(f"{y*100:.0f}%\nn={c}", (x, y), textcoords="offset points",
                    xytext=(0, 12), ha="center", fontsize=11, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Model word-confidence (prob bucket)")
    ax.set_ylabel("Empirical P(word correct vs reference)")
    ax.set_title("Egla-Kafe — confidence calibration (reliability diagram)\n"
                 "all scored words, both runs; bubble size ∝ word count", fontsize=19)
    ax.legend(loc="upper left", frameon=True)
    _despine(ax)
    n_total = len(pairs)
    fig.text(0.5, -0.01,
             "Confidence is well-RANKED (rises monotonically) so the gate works for selection, but raw\n"
             f"probabilities run optimistic at the exact-word level — read the gate, not the absolute number. n={n_total:,} words.",
             ha="center", fontsize=11.5, color="#555555", style="italic")
    fig.tight_layout()
    p = OUT / "calibration.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return p, n_total, list(zip(centers, [round(e, 3) for e in emp], counts))


# ---------------------------------------------------------------- main
def main():
    paths = {}
    paths["recovery_ladder"] = str(plot_recovery_ladder())
    paths["levers"] = str(plot_levers())
    paths["category_trust"] = str(plot_category_trust())
    paths["confidence_gate"] = str(plot_confidence_gate())
    calp, n_words, calib = plot_calibration()
    paths["calibration"] = str(calp)

    print("Generated plots:")
    for k, v in paths.items():
        print(f"  {k:18s} -> {v}")
    print(f"\nCalibration: {n_words:,} aligned words")
    print("  bucket_center  P(correct)  n")
    for c, e, n in calib:
        print(f"    {c:.2f}         {e*100:5.1f}%   {n}")


if __name__ == "__main__":
    main()
