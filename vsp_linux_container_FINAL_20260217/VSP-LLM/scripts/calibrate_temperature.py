"""Temperature scaling for per-method confidence calibration.

Standard binary temperature scaling (Guo et al. 2017): given (conf, correct)
pairs, find a single scalar T > 0 such that

    calibrated_p = sigmoid( logit(conf) / T )

minimizes binary cross-entropy on the held-out set. T > 1 flattens overconfident
distributions (e.g., voting methods); T < 1 sharpens underconfident ones.

5-fold cross-validation is used to estimate the fitted T robustly on small data
and to report a held-out ECE. This script answers: "for each aggregation method,
what is the calibrated reliability curve and the corrected per-word confidence?"

Usage:
  python calibrate_temperature.py \
      --aggregated <aggregated.json> \
      --hypo <hypo-{fid}.json> \
      --out <calibration.json>
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize_scalar

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
for _candidate in ("/home/ubuntu/lib", os.path.abspath(os.path.join(_HERE, "..", "..", "VSP-LLM", "scripts"))):
    if os.path.isdir(_candidate) and _candidate not in sys.path:
        sys.path.insert(0, _candidate)

from _alignment import align_word_lists, split_words  # noqa: E402

EPS = 1e-7

METHOD_GETTERS = {
    "hyp_top1":       lambda r: (r.get("hyp_top1", ""), r.get("hyp_top1_word_confs") or []),
    "hyp_mbr":        lambda r: ((r.get("hyp_mbr") or {}).get("text", ""), (r.get("hyp_mbr") or {}).get("word_confs") or []),
    "hyp_vote_score": lambda r: ((r.get("hyp_vote_score") or {}).get("text", ""), (r.get("hyp_vote_score") or {}).get("word_confs") or []),
    "hyp_vote_conf":  lambda r: ((r.get("hyp_vote_conf") or {}).get("text", ""), (r.get("hyp_vote_conf") or {}).get("word_confs") or []),
    "hyp_safe":       lambda r: ((r.get("hyp_safe") or {}).get("text", ""), (r.get("hyp_safe") or {}).get("word_confs") or []),
}


# ──────────────────────────────────────────────────────────────────────────────
# Calibration math
# ──────────────────────────────────────────────────────────────────────────────

def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def apply_temperature(confs: np.ndarray, T: float) -> np.ndarray:
    """Calibrated probability under temperature T."""
    return _sigmoid(_logit(confs) / T)


def nll(T: float, confs: np.ndarray, correct: np.ndarray) -> float:
    """Binary NLL of calibrated probabilities. T > 0."""
    if T <= 0:
        return 1e10
    p = apply_temperature(confs, T)
    p = np.clip(p, EPS, 1 - EPS)
    return -float(np.mean(correct * np.log(p) + (1 - correct) * np.log(1 - p)))


def fit_temperature(confs: np.ndarray, correct: np.ndarray) -> float:
    """Find T minimizing NLL via bounded scalar optimization."""
    if len(confs) == 0:
        return 1.0
    res = minimize_scalar(
        nll, args=(confs, correct), bounds=(0.05, 50.0), method="bounded",
        options={"xatol": 1e-4},
    )
    return float(res.x)


def ece(confs: np.ndarray, correct: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error via equal-width bins on confs."""
    if len(confs) == 0:
        return 0.0
    bins = np.linspace(0, 1, n_bins + 1)
    e = 0.0
    n = len(confs)
    for k in range(n_bins):
        lo, hi = bins[k], bins[k + 1]
        mask = (confs >= lo) & (confs < hi if k < n_bins - 1 else confs <= hi)
        if not mask.any():
            continue
        avg_p = float(confs[mask].mean())
        avg_c = float(correct[mask].mean())
        e += (mask.sum() / n) * abs(avg_p - avg_c)
    return float(e)


def reliability_table(confs: np.ndarray, correct: np.ndarray) -> List[dict]:
    """Bin-by-bin reliability — same scheme as the manual analysis."""
    bins = [(0.0, 0.4), (0.4, 0.6), (0.6, 0.7), (0.7, 0.8),
            (0.8, 0.9), (0.9, 0.95), (0.95, 0.99), (0.99, 1.001)]
    out = []
    for lo, hi in bins:
        mask = (confs >= lo) & (confs < hi)
        if not mask.any():
            continue
        n = int(mask.sum())
        out.append({
            "bin": f"[{lo:.2f},{hi:.2f})",
            "n": n,
            "mean_conf": float(confs[mask].mean()),
            "p_correct": float(correct[mask].mean()),
            "gap": float(confs[mask].mean() - correct[mask].mean()),
        })
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Build (conf, correct) pairs for one method
# ──────────────────────────────────────────────────────────────────────────────

def build_pairs(aggregated: dict, refs: dict, method: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    getter = METHOD_GETTERS[method]
    confs: List[float] = []
    correct: List[int] = []
    seg_ids: List[str] = []
    for utt_id, rec in aggregated.items():
        text, wc = getter(rec)
        method_words = split_words(text)
        confs_i = [None] * len(method_words)
        for i, (w, p) in enumerate(wc[:len(method_words)]):
            confs_i[i] = p
        ref_words = split_words(refs.get(utt_id, ""))
        ref_pairs = align_word_lists(
            [w.lower() for w in ref_words],
            [w.lower() for w in method_words],
        )
        is_correct = [0] * len(method_words)
        for ri, hi in ref_pairs:
            if ri >= 0 and hi >= 0 and ref_words[ri].lower() == method_words[hi].lower():
                is_correct[hi] = 1
        for i, p in enumerate(confs_i):
            if p is None:
                continue
            confs.append(float(p))
            correct.append(int(is_correct[i]))
            seg_ids.append(utt_id)
    return np.asarray(confs, dtype=np.float64), np.asarray(correct, dtype=np.float64), seg_ids


# ──────────────────────────────────────────────────────────────────────────────
# 5-fold CV on segments (NOT words — keeps per-segment correlations honest)
# ──────────────────────────────────────────────────────────────────────────────

def cv_temperature(confs: np.ndarray, correct: np.ndarray, seg_ids: List[str], n_folds: int = 5, seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    seg_set = sorted(set(seg_ids))
    rng.shuffle(seg_set)
    folds = [set(seg_set[i::n_folds]) for i in range(n_folds)]

    seg_to_fold = {}
    for fi, segs in enumerate(folds):
        for s in segs:
            seg_to_fold[s] = fi
    fold_idx = np.array([seg_to_fold[s] for s in seg_ids])

    Ts = []
    test_pred = np.zeros_like(confs)
    for fi in range(n_folds):
        train_mask = fold_idx != fi
        test_mask  = fold_idx == fi
        if not train_mask.any() or not test_mask.any():
            continue
        T = fit_temperature(confs[train_mask], correct[train_mask])
        Ts.append(T)
        test_pred[test_mask] = apply_temperature(confs[test_mask], T)

    return {
        "T_per_fold": [float(t) for t in Ts],
        "T_mean":     float(np.mean(Ts)) if Ts else 1.0,
        "T_median":   float(np.median(Ts)) if Ts else 1.0,
        "test_pred":  test_pred,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aggregated", required=True)
    ap.add_argument("--hypo", required=True)
    ap.add_argument("--out", default=None, help="Optional path for calibration.json")
    args = ap.parse_args()

    aggregated = json.load(open(args.aggregated))
    hypo = json.load(open(args.hypo))
    refs = {u: r for u, r in zip(hypo["utt_id"], hypo.get("ref", []))}

    out: dict = {"methods": {}}
    print(f"\n{'method':<18} {'n_words':>8} {'T (CV mean)':>12} {'ECE_uncalib':>12} {'ECE_calib_CV':>13} {'ECE_calib_pool':>15}")
    print("-" * 90)
    for method in METHOD_GETTERS:
        confs, correct, seg_ids = build_pairs(aggregated, refs, method)
        if len(confs) == 0:
            print(f"{method:<18} (no data)")
            continue
        ece_uncal = ece(confs, correct)
        cv = cv_temperature(confs, correct, seg_ids, n_folds=5, seed=1)
        ece_cv = ece(cv["test_pred"], correct)
        # Pooled fit (all data, single T) — what we'd actually deploy
        T_pool = fit_temperature(confs, correct)
        pred_pool = apply_temperature(confs, T_pool)
        ece_pool = ece(pred_pool, correct)
        rel_uncalib = reliability_table(confs, correct)
        rel_calib   = reliability_table(pred_pool, correct)
        print(f"{method:<18} {len(confs):>8} {cv['T_mean']:>12.3f} {ece_uncal:>12.3f} {ece_cv:>13.3f} {ece_pool:>15.3f}  (T_pool={T_pool:.3f})")
        out["methods"][method] = {
            "n_words":         int(len(confs)),
            "T_pool":          T_pool,
            "T_cv_mean":       cv["T_mean"],
            "T_cv_per_fold":   cv["T_per_fold"],
            "ece_uncalibrated": ece_uncal,
            "ece_calibrated_cv": ece_cv,
            "ece_calibrated_pool": ece_pool,
            "reliability_uncalibrated": rel_uncalib,
            "reliability_calibrated":   rel_calib,
            "mean_conf_uncal": float(confs.mean()),
            "mean_conf_calib": float(pred_pool.mean()),
            "mean_correct":    float(correct.mean()),
        }

    print("\nNote: T > 1 ⇒ method was over-confident; T < 1 ⇒ under-confident.")
    print("ECE_calib_CV is the held-out (5-fold) calibration error → the honest validation number.")
    print("ECE_calib_pool is what shipping a single T learned on all data would give → the deployable number.")

    print("\n--- Per-method post-calibration reliability tables ---")
    for method, info in out["methods"].items():
        print(f"\n{method}  T_pool={info['T_pool']:.3f}  ECE: {info['ece_uncalibrated']:.3f} → {info['ece_calibrated_pool']:.3f}")
        print(f"  {'bin':>14} {'n':>5} {'pre conf':>9} {'post conf':>10} {'P(correct)':>11}")
        for u, c in zip(info["reliability_uncalibrated"], info["reliability_calibrated"]):
            print(f"  {u['bin']:>14} {u['n']:>5} {u['mean_conf']:>9.3f} {c['mean_conf']:>10.3f} {u['p_correct']:>11.3f}")

    if args.out:
        json.dump(out, open(args.out, "w"), indent=2)
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
