"""Beam variance & word-level confusion analysis.

Inputs:
  - --nbest        nbest-{fid}.json from decode (all N hypotheses + per-token confidence)
  - --aggregated   aggregated-{fid}.json from lib/nbest_aggregate.py (per-method texts + WER)
  - --baseline-csv report.csv (segment-level WER/WWER/IS/sentence_confidence)
  - --refs-json    optional hypo-{fid}.json (provides ref strings if not in baseline-csv)
  - --out-dir      directory for outputs

Outputs (in --out-dir):
  - beam_variance.csv          per-segment metrics
  - word_level_confusion.csv   per-word stats (freq >= 5)
  - word_level_ne_confusion.csv per-NE-word stats (freq >= 2; spaCy required)
  - beam_variance_corr_heatmap.png
  - beam_variance_vs_confidence.png
  - word_recall_vs_conf.png
  - word_recall_vs_beam_disagree.png
  - beam_variance_analysis.md
  - word_level_confusion_analysis.md

Pure CPU; uses pandas, numpy, matplotlib. spaCy is optional (NE pass is skipped
gracefully if it's not available, matching the pipeline's offline behavior).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from _alignment import align_word_lists, hyp_word_correctness, split_words, wer  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


# ──────────────────────────────────────────────────────────────────────────────
# Per-segment beam variance metrics
# ──────────────────────────────────────────────────────────────────────────────

def pairwise_mean_wer(texts: Sequence[str]) -> float:
    """Mean WER across all (N choose 2) pairs of hypotheses (model self-disagreement)."""
    n = len(texts)
    if n < 2:
        return 0.0
    wlists = [split_words(t) for t in texts]
    total = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += wer(wlists[i], wlists[j])
            count += 1
    return total / max(count, 1)


def word_agreement_rate(texts: Sequence[str]) -> float:
    """Fraction of top-1 words that appear at the aligned position in ≥ 50% of beams."""
    if not texts:
        return 0.0
    anchor = split_words(texts[0])
    if not anchor:
        return 0.0
    n = len(texts)
    if n < 2:
        return 1.0
    # For each anchor position, count beams whose aligned word matches.
    counts = [0] * len(anchor)
    for h in range(1, n):
        hwords = split_words(texts[h])
        pairs = align_word_lists(anchor, hwords)
        for ai, hi in pairs:
            if ai < 0 or hi < 0:
                continue
            if anchor[ai].lower() == hwords[hi].lower():
                counts[ai] += 1
    threshold = max(1, math.ceil((n - 1) * 0.5))
    return sum(1 for c in counts if c >= threshold) / len(anchor)


def mean_position_entropy(texts: Sequence[str]) -> float:
    """Mean over anchor positions of token-bag entropy across the N hypotheses.

    For each anchor position, build a distribution over the words that aligned
    there (including a 'gap' bucket for deletions). Compute Shannon entropy
    over that distribution, then average over positions.
    """
    if not texts:
        return 0.0
    anchor = split_words(texts[0])
    if not anchor:
        return 0.0
    n = len(texts)
    entropies: List[float] = []
    for ai, anchor_word in enumerate(anchor):
        bag: Dict[str, int] = defaultdict(int)
        bag[anchor_word.lower()] += 1
        for h in range(1, n):
            hwords = split_words(texts[h])
            pairs = align_word_lists(anchor, hwords)
            mapped = "<gap>"
            for ax, hx in pairs:
                if ax == ai:
                    mapped = hwords[hx].lower() if hx >= 0 else "<gap>"
                    break
            bag[mapped] += 1
        total = sum(bag.values())
        ent = 0.0
        for c in bag.values():
            p = c / total
            if p > 0:
                ent -= p * math.log(p)
        entropies.append(ent)
    return float(np.mean(entropies)) if entropies else 0.0


def per_position_disagreement(anchor_words: Sequence[str], hypotheses: Sequence[Sequence[str]]) -> List[float]:
    """For each anchor position, fraction of OTHER beams whose aligned word
    differs from the anchor word (including 'gap'). Returns one disagreement
    rate per anchor position (length = len(anchor_words)).
    """
    n = len(hypotheses)
    if n <= 1 or not anchor_words:
        return [0.0] * len(anchor_words)
    rates = []
    for ai, aw in enumerate(anchor_words):
        disagree = 0
        considered = 0
        for h in range(1, n):
            pairs = align_word_lists(anchor_words, hypotheses[h])
            mapped = "<gap>"
            for ax, hx in pairs:
                if ax == ai:
                    mapped = hypotheses[h][hx].lower() if hx >= 0 else "<gap>"
                    break
            considered += 1
            if mapped != aw.lower():
                disagree += 1
        rates.append(disagree / max(considered, 1))
    return rates


# ──────────────────────────────────────────────────────────────────────────────
# Per-segment row builder
# ──────────────────────────────────────────────────────────────────────────────

def per_segment_row(utt_id: str, rec: dict) -> dict:
    hyps = rec.get("hypotheses") or []
    texts = [h.get("text", "") for h in hyps]
    seq_scores = [h.get("sequence_score") for h in hyps]
    unique_texts = sorted(set(t.strip() for t in texts if t))
    return {
        "utt_id": utt_id,
        "n_hyps": len(hyps),
        "n_unique_hyps": len(unique_texts),
        "pairwise_mean_wer": pairwise_mean_wer(texts),
        "word_agreement_rate": word_agreement_rate(texts),
        "mean_position_entropy": mean_position_entropy(texts),
        "top1_text": texts[0] if texts else "",
        "top1_seq_score": seq_scores[0] if seq_scores else None,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Aggregator-method WER vs top-1
# ──────────────────────────────────────────────────────────────────────────────

def aggregator_wers(aggregated: Dict[str, dict], refs: Dict[str, str]) -> pd.DataFrame:
    methods = ["hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe", "hyp_xseg_merge"]
    rows = []
    for utt_id, rec in aggregated.items():
        ref = refs.get(utt_id, "")
        ref_words = split_words(ref)
        row = {"utt_id": utt_id}
        for m in methods:
            v = rec.get(m)
            text = v if isinstance(v, str) else (v.get("text", "") if isinstance(v, dict) else "")
            row[f"text_{m}"] = text
            row[f"wer_{m}"] = wer(ref_words, split_words(text))
        rows.append(row)
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Word-level confusion analysis
# ──────────────────────────────────────────────────────────────────────────────

def _confidence_lookup(confidence_path: Optional[str]) -> Dict[str, dict]:
    if not confidence_path or not os.path.isfile(confidence_path):
        return {}
    try:
        with open(confidence_path) as f:
            return json.load(f)
    except Exception:
        return {}


_SPECIAL_TOKENS = frozenset({"<s>", "</s>", "<unk>", "<pad>", "<|begin_of_text|>", "<|end_of_text|>"})


def _word_confs_for_utt(conf_rec: Optional[dict]) -> List[Tuple[str, Optional[float]]]:
    """Aggregate sub-tokens of the top-1 confidence record to per-word probs.
    Mirrors the same SP-marker + special-token-filter logic as
    nbest_aggregate.words_with_conf — keep these two in sync.
    """
    if not conf_rec:
        return []
    SP = "▁"
    words: List[Tuple[str, Optional[float]]] = []
    cur_chars: List[str] = []
    cur_min: Optional[float] = None
    for rec in conf_rec.get("tokens", []):
        tstr = rec.get("token") or ""
        if not tstr:
            continue
        if tstr.lstrip(SP) in _SPECIAL_TOKENS:
            if cur_chars:
                words.append(("".join(cur_chars), cur_min))
                cur_chars = []
                cur_min = None
            continue
        if tstr.startswith(SP) and cur_chars:
            words.append(("".join(cur_chars), cur_min))
            cur_chars = []
            cur_min = None
        cur_chars.append(tstr.lstrip(SP))
        p = rec.get("prob")
        if p is not None and math.isfinite(float(p)):
            cur_min = float(p) if cur_min is None else min(cur_min, float(p))
    if cur_chars:
        words.append(("".join(cur_chars), cur_min))
    return [(w, p) for w, p in words if w.strip()]


def word_level_table(
    nbest: Dict[str, dict],
    refs: Dict[str, str],
    confidence: Dict[str, dict],
    min_freq: int = 5,
) -> pd.DataFrame:
    """Build per-word stats (cross-segment aggregation).

    Stats per unique reference word:
      - freq             : how many times it appears across all references
      - times_correct    : how many of those occurrences the model predicted correctly
      - recall           : times_correct / freq
      - mean_conf        : average top-1 confidence for the word at the *predicted*
                           positions (i.e., when hyp word matches ref word)
      - mean_beam_disagree : average per-position disagreement (across the 20 beams)
                             at the matched positions
      - n_conf_obs       : how many times we observed conf (predicted occurrences)
    """
    word_freq: Dict[str, int] = defaultdict(int)
    word_correct: Dict[str, int] = defaultdict(int)
    word_conf_sum: Dict[str, float] = defaultdict(float)
    word_conf_n: Dict[str, int] = defaultdict(int)
    word_disagree_sum: Dict[str, float] = defaultdict(float)
    word_disagree_n: Dict[str, int] = defaultdict(int)

    for utt_id, rec in nbest.items():
        hyps = rec.get("hypotheses") or []
        if not hyps:
            continue
        top1 = hyps[0].get("text", "")
        top1_words = split_words(top1)
        ref_words = split_words(refs.get(utt_id, ""))
        for rw in ref_words:
            word_freq[rw.lower()] += 1
        # hyp-side correctness flags (same length as top1_words)
        hyp_correct = hyp_word_correctness(refs.get(utt_id, ""), top1_words)

        # Confidence per top-1 word (sub-token min)
        conf_words = _word_confs_for_utt(confidence.get(utt_id))
        # Length may differ from top1_words split (BPE artifacts on punctuation, etc).
        # Best-effort positional alignment via shared length.

        # Beam disagreement per top-1 anchor word
        all_beam_words = [split_words(h.get("text", "")) for h in hyps]
        disagree_rates = per_position_disagreement(top1_words, all_beam_words) if len(all_beam_words) > 1 else [0.0] * len(top1_words)

        # Walk top-1 words; for those that match a ref word (correct=1), credit the ref word.
        ref_lower = [w.lower() for w in ref_words]
        # We need to know which ref word was matched. Use align_word_lists ref vs hyp.
        ref_pairs = align_word_lists([w.lower() for w in ref_words], [w.lower() for w in top1_words])
        for ri, hi in ref_pairs:
            if ri < 0 or hi < 0:
                continue
            if ref_words[ri].lower() != top1_words[hi].lower():
                continue  # substitution — don't credit either word
            target = ref_words[ri].lower()
            word_correct[target] += 1
            # Conf
            if hi < len(conf_words):
                w_text, w_conf = conf_words[hi]
                if w_conf is not None:
                    word_conf_sum[target] += w_conf
                    word_conf_n[target] += 1
            # Disagreement
            if hi < len(disagree_rates):
                word_disagree_sum[target] += disagree_rates[hi]
                word_disagree_n[target] += 1

    rows = []
    for word, freq in word_freq.items():
        if freq < min_freq:
            continue
        cor = word_correct.get(word, 0)
        rows.append({
            "word": word,
            "freq": int(freq),
            "times_correct": int(cor),
            "recall": cor / freq if freq else 0.0,
            "mean_conf": (word_conf_sum[word] / word_conf_n[word]) if word_conf_n.get(word) else None,
            "n_conf_obs": int(word_conf_n.get(word, 0)),
            "mean_beam_disagree": (word_disagree_sum[word] / word_disagree_n[word]) if word_disagree_n.get(word) else None,
            "n_disagree_obs": int(word_disagree_n.get(word, 0)),
        })
    df = pd.DataFrame(rows).sort_values(by=["freq"], ascending=False).reset_index(drop=True)
    return df


def named_entity_table(
    word_table: pd.DataFrame,
    refs: Dict[str, str],
    min_freq: int = 2,
) -> Optional[pd.DataFrame]:
    """Build NE-only per-word stats. Returns None if spaCy is unavailable.

    Categories kept: PERSON, ORG, GPE, PRODUCT, EVENT, WORK_OF_ART, NORP, LOC, FAC.
    """
    try:
        import spacy
    except ImportError:
        return None
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        return None

    keep_labels = {"PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "WORK_OF_ART", "NORP", "LOC", "FAC"}
    word_to_categories: Dict[str, set] = defaultdict(set)
    word_freq: Dict[str, int] = defaultdict(int)
    for utt_id, ref in refs.items():
        if not ref:
            continue
        doc = nlp(ref)
        for ent in doc.ents:
            if ent.label_ not in keep_labels:
                continue
            for tok in ent.text.split():
                w = tok.strip().lower()
                if not w:
                    continue
                word_to_categories[w].add(ent.label_)
                word_freq[w] += 1

    if not word_to_categories:
        return None

    df = word_table.set_index("word") if not word_table.empty and "word" in word_table.columns else None
    rows = []
    for word, cats in word_to_categories.items():
        if word_freq[word] < min_freq:
            continue
        if df is None or word not in df.index:
            # Word didn't pass the freq>=5 filter in the general table — recover
            # the freq from our NE counter.
            row = {
                "word": word,
                "freq": int(word_freq[word]),
                "times_correct": 0,  # unknown without re-walking
                "recall": None,
                "mean_conf": None,
                "mean_beam_disagree": None,
            }
        else:
            row = df.loc[word].to_dict()
            row["word"] = word
            row["freq"] = int(word_freq[word])  # NE-counted freq (across NEs only)
        row["ne_categories"] = ",".join(sorted(cats))
        rows.append(row)
    if not rows:
        return None
    return pd.DataFrame(rows).sort_values(by="freq", ascending=False).reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# Plots
# ──────────────────────────────────────────────────────────────────────────────

def plot_corr_heatmap(beam_df: pd.DataFrame, baseline_df: pd.DataFrame, out_path: str) -> Optional[pd.DataFrame]:
    if baseline_df.empty or "utt_id" not in baseline_df.columns:
        return None
    merged = beam_df.merge(baseline_df, on="utt_id", how="inner")
    candidate_cols = [
        "n_unique_hyps", "pairwise_mean_wer", "word_agreement_rate", "mean_position_entropy",
    ]
    target_cols_all = [
        "wer_%", "wwer_%", "is_score", "sentence_confidence", "min_word_conf", "n_low_conf_words", "nea_f1_%",
    ]
    target_cols = [c for c in target_cols_all if c in merged.columns]
    if not target_cols or merged.empty:
        return None
    M = merged[candidate_cols + target_cols].apply(pd.to_numeric, errors="coerce")
    corr = M.corr().loc[candidate_cols, target_cols]

    fig, ax = plt.subplots(figsize=(max(6, len(target_cols) * 1.2), max(4, len(candidate_cols) * 0.8)))
    im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(target_cols)))
    ax.set_xticklabels(target_cols, rotation=30, ha="right")
    ax.set_yticks(range(len(candidate_cols)))
    ax.set_yticklabels(candidate_cols)
    for i in range(len(candidate_cols)):
        for j in range(len(target_cols)):
            v = corr.values[i, j]
            ax.text(j, i, f"{v:.2f}" if not np.isnan(v) else "-", ha="center", va="center",
                    color=("white" if abs(v) > 0.5 else "black"))
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Pearson r")
    ax.set_title("Beam variance × segment quality (Pearson)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return corr


def plot_scatter(x: np.ndarray, y: np.ndarray, xl: str, yl: str, title: str, out_path: str):
    mask = ~(np.isnan(x) | np.isnan(y))
    if mask.sum() < 3:
        return
    x = x[mask]; y = y[mask]
    r = np.corrcoef(x, y)[0, 1] if mask.sum() > 1 else float("nan")
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.scatter(x, y, s=8, alpha=0.4)
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    ax.set_title(f"{title}\nPearson r = {r:.3f} (n={mask.sum()})")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def _refs_from_hypo(hypo_path: str) -> Dict[str, str]:
    """Extract {utt_id: ref} from hypo-{fid}.json (the decode dump).
    Format is {'utt_id': [...], 'ref': [...], 'hypo': [...], ...}.
    """
    with open(hypo_path) as f:
        d = json.load(f)
    if not isinstance(d, dict) or "utt_id" not in d:
        return {}
    return {u: r for u, r in zip(d["utt_id"], d.get("ref", []))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nbest", required=True)
    ap.add_argument("--aggregated", default=None)
    ap.add_argument("--baseline-csv", default=None, help="report.csv with utt_id, wer_%%, wwer_%%, is_score, sentence_confidence...")
    ap.add_argument("--hypo-json", default=None, help="hypo-{fid}.json for ref extraction (fallback if baseline-csv lacks ref column)")
    ap.add_argument("--confidence", default=None, help="confidence-{fid}.json sidecar (top-1 per-token probs)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--min-freq", type=int, default=5)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    with open(args.nbest) as f:
        nbest = json.load(f)
    aggregated = {}
    if args.aggregated and os.path.isfile(args.aggregated):
        with open(args.aggregated) as f:
            aggregated = json.load(f)

    refs: Dict[str, str] = {}
    if args.baseline_csv and os.path.isfile(args.baseline_csv):
        bdf = pd.read_csv(args.baseline_csv)
        if "ref" in bdf.columns:
            refs = dict(zip(bdf["utt_id"], bdf["ref"].fillna("")))
    if not refs and args.hypo_json:
        refs = _refs_from_hypo(args.hypo_json)

    # 1) Per-segment beam variance
    beam_rows = [per_segment_row(u, r) for u, r in nbest.items()]
    beam_df = pd.DataFrame(beam_rows)
    beam_df.to_csv(os.path.join(args.out_dir, "beam_variance.csv"), index=False)
    print(f"[beam_variance] {len(beam_df)} segments → beam_variance.csv")

    # 2) Aggregator method comparison
    if aggregated and refs:
        agg_df = aggregator_wers(aggregated, refs)
        agg_df.to_csv(os.path.join(args.out_dir, "aggregator_wers.csv"), index=False)
        method_summary = {
            f"mean_wer_{m}": float(agg_df[f"wer_{m}"].mean())
            for m in ["hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe", "hyp_xseg_merge"]
            if f"wer_{m}" in agg_df.columns
        }
        with open(os.path.join(args.out_dir, "aggregator_method_summary.json"), "w") as f:
            json.dump(method_summary, f, indent=2)
        print(f"[aggregator] mean WERs: {method_summary}")

    # 3) Correlation heatmap
    baseline_df = pd.DataFrame()
    if args.baseline_csv and os.path.isfile(args.baseline_csv):
        baseline_df = pd.read_csv(args.baseline_csv)
    corr = plot_corr_heatmap(beam_df, baseline_df, os.path.join(args.out_dir, "beam_variance_corr_heatmap.png"))

    # 4) Scatter: pairwise WER vs sentence_confidence
    if not baseline_df.empty and "sentence_confidence" in baseline_df.columns:
        merged = beam_df.merge(baseline_df[["utt_id", "sentence_confidence"]], on="utt_id", how="inner")
        plot_scatter(
            merged["pairwise_mean_wer"].to_numpy(dtype=float),
            merged["sentence_confidence"].to_numpy(dtype=float),
            "Pairwise mean WER across beams",
            "Sentence confidence (mean per-word prob)",
            "Beam disagreement vs token confidence",
            os.path.join(args.out_dir, "beam_variance_vs_confidence.png"),
        )

    # 5) Word-level confusion analysis (Pass 1: all words >= min_freq)
    confidence = _confidence_lookup(args.confidence)
    word_df = word_level_table(nbest, refs, confidence, min_freq=args.min_freq)
    word_df.to_csv(os.path.join(args.out_dir, "word_level_confusion.csv"), index=False)
    print(f"[word_level] {len(word_df)} words at freq>={args.min_freq}")

    if not word_df.empty:
        wd = word_df.dropna(subset=["mean_conf"]).copy()
        wd["confusion_rate"] = 1.0 - wd["recall"]
        plot_scatter(
            wd["mean_conf"].to_numpy(dtype=float),
            wd["confusion_rate"].to_numpy(dtype=float),
            "Mean confidence (when predicted)",
            "Confusion rate (1 − recall)",
            "Are confused words also low-confidence?",
            os.path.join(args.out_dir, "word_recall_vs_conf.png"),
        )
        wd2 = word_df.dropna(subset=["mean_beam_disagree"]).copy()
        wd2["confusion_rate"] = 1.0 - wd2["recall"]
        plot_scatter(
            wd2["mean_beam_disagree"].to_numpy(dtype=float),
            wd2["confusion_rate"].to_numpy(dtype=float),
            "Mean beam disagreement (when predicted)",
            "Confusion rate (1 − recall)",
            "Are confused words also high-disagreement?",
            os.path.join(args.out_dir, "word_recall_vs_beam_disagree.png"),
        )

    # 6) Word-level Pass 2: Named Entities
    ne_df = named_entity_table(word_df, refs, min_freq=2)
    if ne_df is not None:
        ne_df.to_csv(os.path.join(args.out_dir, "word_level_ne_confusion.csv"), index=False)
        print(f"[word_level_ne] {len(ne_df)} NE-words at freq>=2")
    else:
        print("[word_level_ne] spaCy unavailable — skipped (offline mode)")

    # 7) Markdown writeups
    _write_segment_md(beam_df, corr, args.out_dir)
    _write_word_md(word_df, ne_df, args.out_dir)

    print(f"[done] wrote outputs under {args.out_dir}")


def _write_segment_md(beam_df: pd.DataFrame, corr: Optional[pd.DataFrame], out_dir: str):
    path = os.path.join(out_dir, "beam_variance_analysis.md")
    lines = ["# Beam Variance Analysis", "", f"Per-segment metrics over {len(beam_df)} segments.", ""]
    if not beam_df.empty:
        s = beam_df[["n_unique_hyps", "pairwise_mean_wer", "word_agreement_rate", "mean_position_entropy"]].describe()
        lines.append("## Distribution of beam metrics\n")
        lines.append("```")
        lines.append(s.round(3).to_string())
        lines.append("```\n")
    if corr is not None and not corr.empty:
        lines.append("## Correlation: beam metrics × segment quality\n")
        lines.append("```")
        lines.append(corr.round(3).to_string())
        lines.append("```\n")
        lines.append("Plot: ![corr heatmap](beam_variance_corr_heatmap.png)\n")
    lines.append("Plot: ![beam disagreement vs confidence](beam_variance_vs_confidence.png)\n")
    with open(path, "w") as f:
        f.write("\n".join(lines))


def _write_word_md(word_df: pd.DataFrame, ne_df: Optional[pd.DataFrame], out_dir: str):
    path = os.path.join(out_dir, "word_level_confusion_analysis.md")
    lines = ["# Word-Level Confusion Analysis", ""]
    if not word_df.empty:
        wd = word_df.dropna(subset=["mean_conf"]).copy()
        wd["confusion_rate"] = 1.0 - wd["recall"]
        if len(wd) > 1:
            r1 = float(np.corrcoef(wd["confusion_rate"], wd["mean_conf"])[0, 1])
            lines.append(f"## Hypothesis: confused words have low confidence?\n")
            lines.append(f"Pearson r between (1 − recall) and mean per-word confidence: **{r1:.3f}** (n={len(wd)})\n")
        wd2 = word_df.dropna(subset=["mean_beam_disagree"]).copy()
        wd2["confusion_rate"] = 1.0 - wd2["recall"]
        if len(wd2) > 1:
            r2 = float(np.corrcoef(wd2["confusion_rate"], wd2["mean_beam_disagree"])[0, 1])
            lines.append(f"\n## Hypothesis: confused words have noisier beams?\n")
            lines.append(f"Pearson r between (1 − recall) and mean beam disagreement: **{r2:.3f}** (n={len(wd2)})\n")
        # Top 20 most-confused (by freq, lowest recall)
        top_conf = word_df.sort_values(["recall", "freq"], ascending=[True, False]).head(20)
        lines.append("\n## 20 most-confused words (lowest recall, freq>=5)\n")
        lines.append("```")
        lines.append(top_conf[["word", "freq", "times_correct", "recall", "mean_conf", "mean_beam_disagree"]].round(3).to_string(index=False))
        lines.append("```\n")
        # Top 20 most-confident
        top_acc = word_df.sort_values(["recall", "freq"], ascending=[False, False]).head(20)
        lines.append("\n## 20 most-recalled words (highest recall, freq>=5)\n")
        lines.append("```")
        lines.append(top_acc[["word", "freq", "times_correct", "recall", "mean_conf", "mean_beam_disagree"]].round(3).to_string(index=False))
        lines.append("```\n")
    if ne_df is not None and not ne_df.empty:
        lines.append("\n## Named-Entity word breakdown (freq>=2)\n")
        lines.append("```")
        lines.append(ne_df.head(40).round(3).to_string(index=False))
        lines.append("```\n")
    else:
        lines.append("\n*(NE pass skipped — spaCy unavailable in this environment.)*\n")
    lines.append("\n![word recall vs conf](word_recall_vs_conf.png)\n")
    lines.append("![word recall vs beam disagree](word_recall_vs_beam_disagree.png)\n")
    with open(path, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
