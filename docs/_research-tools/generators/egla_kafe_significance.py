#!/usr/bin/env python3
"""
Egla-Kafe — statistical significance + confidence-gate operating points.

Loads both eval runs (run_scene12_all, run_shaam_all) with their provenance/index,
and computes — with bootstrap 95% CIs and a Mann-Whitney U test on is_score — the
following contrasts:

  1. iPhone-4K vs client-camera   (run_shaam_all; source_type from index.json;
                                    img_* masters = iPhone-4K, shaam_* = client camera)
  2. Military (scene2) vs Emma/Jake (scene1)   on scene1+2
  3. Camera angle  front vs 30 vs 45           on scene1+2
  4. Per-speaker (person from provenance)      on scene1+2

It also recomputes the confidence-gate operating points: join the scene1+2
per-segment mean word-prob (from word_confidence.json) with the segment is_score,
then sweep conf>=0.5/0.6/0.7/0.8 -> kept%, mean IS, useful% (IS>=2).

Writes  work/eval/significance.json  and prints a readable table.

Run with the project venv:
  /home/ubuntu/vsp-llm-yoad-venv/bin/python \
    docs/_research-tools/generators/egla_kafe_significance.py
"""

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import mannwhitneyu

# ---------------------------------------------------------------- paths
EVAL = Path("/home/ubuntu/datasets/clients/egla_kafe/work/eval")
RUN_S12 = EVAL / "run_scene12_all"
RUN_SHAAM = EVAL / "run_shaam_all"
INDEX = EVAL / "index.json"
WC_S12 = Path("/home/ubuntu/flat_runs_archive/20260624_145832/client_outputs/report/word_confidence.json")
WC_SHAAM = Path("/home/ubuntu/flat_runs_archive/20260624_200135/client_outputs/report/word_confidence.json")
OUT_JSON = EVAL / "significance.json"

RNG = np.random.default_rng(20260624)
N_BOOT = 10000


# ---------------------------------------------------------------- loaders
def load_report(run_dir):
    """utt_id -> row dict (is_score float, wer_% float, nea_f1_% float).

    Skips rows with an empty reference (unaligned detected turns have no ground
    truth, hence blank is_score/wer) — they cannot enter is_score contrasts.
    """
    out = {}
    n_skipped = 0
    with open(run_dir / "report" / "report.csv", newline="") as f:
        for r in csv.DictReader(f):
            if r["is_score"].strip() == "" or r["wer_%"].strip() == "":
                n_skipped += 1
                continue
            r["is_score"] = float(r["is_score"])
            r["wer"] = float(r["wer_%"])
            r["nea_f1"] = float(r["nea_f1_%"]) if r["nea_f1_%"].strip() else 0.0
            out[r["utt_id"]] = r
    return out, n_skipped


def load_prov(run_dir):
    return json.load(open(run_dir / "provenance.json"))


def load_index():
    d = json.load(open(INDEX))
    return {e["stem"]: e for e in d["entries"]}


def load_wc(path):
    """utt_id -> mean per-word prob over the segment's words."""
    raw = json.load(open(path))
    out = {}
    for utt, rec in raw.items():
        probs = [w["prob"] for w in rec.get("words", []) if "prob" in w]
        out[utt] = float(np.mean(probs)) if probs else None
    return out


# ---------------------------------------------------------------- stats helpers
def bootstrap_ci(values, stat=np.mean, n=N_BOOT, alpha=0.05):
    """Percentile bootstrap CI for a statistic of a 1-D array."""
    a = np.asarray(values, dtype=float)
    if len(a) == 0:
        return (float("nan"), float("nan"))
    idx = RNG.integers(0, len(a), size=(n, len(a)))
    boots = stat(a[idx], axis=1)
    lo = float(np.percentile(boots, 100 * alpha / 2))
    hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
    return (lo, hi)


def group_summary(scores):
    a = np.asarray(scores, dtype=float)
    lo, hi = bootstrap_ci(a)
    return {
        "n": int(len(a)),
        "mean_is": round(float(np.mean(a)), 3) if len(a) else None,
        "median_is": round(float(np.median(a)), 3) if len(a) else None,
        "ci95": [round(lo, 3), round(hi, 3)],
    }


def two_group_test(a, b, label_a, label_b):
    """Mann-Whitney U (two-sided) on is_score + bootstrap CI of the mean diff."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    res = {
        label_a: group_summary(a),
        label_b: group_summary(b),
    }
    if len(a) >= 1 and len(b) >= 1:
        U, p = mannwhitneyu(a, b, alternative="two-sided")
        # rank-biserial effect size r = 1 - 2U/(n1*n2)
        rb = 1.0 - (2.0 * U) / (len(a) * len(b))
        # bootstrap CI on mean difference (a - b)
        ia = RNG.integers(0, len(a), size=(N_BOOT, len(a)))
        ib = RNG.integers(0, len(b), size=(N_BOOT, len(b)))
        diffs = a[ia].mean(axis=1) - b[ib].mean(axis=1)
        res["mann_whitney_u"] = round(float(U), 1)
        res["p_value"] = float(p)
        res["significant_0.05"] = bool(p < 0.05)
        res["rank_biserial"] = round(float(rb), 3)
        res["mean_diff"] = round(float(np.mean(a) - np.mean(b)), 3)
        res["mean_diff_ci95"] = [
            round(float(np.percentile(diffs, 2.5)), 3),
            round(float(np.percentile(diffs, 97.5)), 3),
        ]
    return res


def kruskal_like_pairwise(groups):
    """Pairwise Mann-Whitney U across >2 groups (for angle / speaker)."""
    names = list(groups.keys())
    pair = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            na, nb = names[i], names[j]
            a, b = np.asarray(groups[na]), np.asarray(groups[nb])
            if len(a) and len(b):
                U, p = mannwhitneyu(a, b, alternative="two-sided")
                pair[f"{na}_vs_{nb}"] = {
                    "mean_diff": round(float(np.mean(a) - np.mean(b)), 3),
                    "p_value": float(p),
                    "significant_0.05": bool(p < 0.05),
                }
    return pair


# ---------------------------------------------------------------- main
def main():
    rep_s12, skip_s12 = load_report(RUN_S12)
    rep_shaam, skip_shaam = load_report(RUN_SHAAM)
    prov_s12 = load_prov(RUN_S12)
    prov_shaam = load_prov(RUN_SHAAM)
    index = load_index()
    wc_s12 = load_wc(WC_S12)

    results = {
        "meta": {
            "n_scene12_scored": len(rep_s12),
            "n_scene12_skipped_empty_ref": skip_s12,
            "n_shaam_run_scored": len(rep_shaam),
            "n_shaam_run_skipped_empty_ref": skip_shaam,
            "n_boot": N_BOOT,
            "test": "Mann-Whitney U (two-sided) on is_score; bootstrap 95% percentile CIs",
            "note": "iPhone-4K = img_* masters in run_shaam_all (source_type=master); "
                    "client-camera = shaam_* (source_type=scene_recording).",
        }
    }

    # ---- 1. iPhone-4K vs client-camera (run_shaam_all) ----
    iphone, camera = [], []
    for utt, row in rep_shaam.items():
        stem = prov_shaam[utt]["stem"]
        src = index[stem]["source_type"]
        if src == "master":
            iphone.append(row["is_score"])
        else:
            camera.append(row["is_score"])
    results["iphone_vs_camera"] = two_group_test(
        iphone, camera, "iPhone_4K", "client_camera"
    )

    # ---- 2. Military (scene2) vs Emma/Jake (scene1) on scene1+2 ----
    mil, emma = [], []
    for utt, row in rep_s12.items():
        sc = prov_s12[utt]["scene"]
        if sc == "scene2":
            mil.append(row["is_score"])
        elif sc == "scene1":
            emma.append(row["is_score"])
    results["military_vs_emmajake"] = two_group_test(
        mil, emma, "Military_scene2", "EmmaJake_scene1"
    )

    # ---- 3. Camera angle front vs 30 vs 45 (scene1+2) ----
    angle_groups = defaultdict(list)
    for utt, row in rep_s12.items():
        angle_groups[prov_s12[utt]["angle"]].append(row["is_score"])
    angle_summary = {a: group_summary(v) for a, v in angle_groups.items()}
    results["angle_front_30_45"] = {
        "groups": angle_summary,
        "pairwise_mannwhitney": kruskal_like_pairwise(
            {k: angle_groups[k] for k in ("front", "30", "45") if k in angle_groups}
        ),
    }

    # ---- 4. Per-speaker (scene1+2) ----
    spk_groups = defaultdict(list)
    for utt, row in rep_s12.items():
        spk_groups[prov_s12[utt]["person"]].append(row["is_score"])
    # rank speakers by mean IS
    spk_summary = {s: group_summary(v) for s, v in spk_groups.items()}
    ranked = sorted(spk_summary.items(), key=lambda kv: kv[1]["mean_is"], reverse=True)
    results["per_speaker"] = {
        "groups": {s: v for s, v in ranked},
        "ranking_by_mean_is": [s for s, _ in ranked],
        "pairwise_mannwhitney": kruskal_like_pairwise(spk_groups),
    }

    # ---- 5. Confidence-gate operating points (scene1+2) ----
    # join per-segment mean word-prob with is_score
    gate_rows = []
    for utt, row in rep_s12.items():
        mp = wc_s12.get(utt)
        if mp is None:
            continue
        gate_rows.append((mp, row["is_score"], row["wer"]))
    n_total = len(gate_rows)
    gate = {"n_total": n_total, "thresholds": {}}
    for thr in (0.5, 0.6, 0.7, 0.8):
        kept = [(s, w) for (mp, s, w) in gate_rows if mp >= thr]
        n_kept = len(kept)
        if n_kept:
            mean_is = float(np.mean([s for s, _ in kept]))
            mean_wer = float(np.mean([w for _, w in kept]))
            useful = sum(1 for s, _ in kept if s >= 2.0)
            useful_pct = 100.0 * useful / n_kept
        else:
            mean_is = mean_wer = useful_pct = float("nan")
        gate["thresholds"][f"{thr:.1f}"] = {
            "kept_pct": round(100.0 * n_kept / n_total, 1),
            "n_kept": n_kept,
            "mean_is": round(mean_is, 3) if n_kept else None,
            "mean_wer": round(mean_wer, 1) if n_kept else None,
            "useful_pct_is_ge_2": round(useful_pct, 1) if n_kept else None,
        }
    # ungated baseline for reference
    all_is = [s for (_, s, _) in gate_rows]
    all_wer = [w for (_, _, w) in gate_rows]
    gate["ungated"] = {
        "kept_pct": 100.0,
        "n_kept": n_total,
        "mean_is": round(float(np.mean(all_is)), 3),
        "mean_wer": round(float(np.mean(all_wer)), 1),
        "useful_pct_is_ge_2": round(100.0 * sum(1 for s in all_is if s >= 2.0) / n_total, 1),
    }
    results["confidence_gate_scene12"] = gate

    # ---------------------------------------------------------------- write
    OUT_JSON.write_text(json.dumps(results, indent=2))

    # ---------------------------------------------------------------- print
    def fmt_grp(g):
        return f"n={g['n']:3d}  IS={g['mean_is']:.2f}  CI[{g['ci95'][0]:.2f},{g['ci95'][1]:.2f}]"

    print("=" * 78)
    print("EGLA-KAFE — SIGNIFICANCE (Mann-Whitney U on is_score, bootstrap 95% CIs)")
    print("=" * 78)

    print("\n[1] iPhone-4K vs client-camera (run_shaam_all)")
    r = results["iphone_vs_camera"]
    print(f"    iPhone-4K      {fmt_grp(r['iPhone_4K'])}")
    print(f"    client-camera  {fmt_grp(r['client_camera'])}")
    print(f"    diff={r['mean_diff']:+.2f} CI{r['mean_diff_ci95']}  U={r['mann_whitney_u']}"
          f"  p={r['p_value']:.2e}  sig={r['significant_0.05']}  rb={r['rank_biserial']}")

    print("\n[2] Military (scene2) vs Emma/Jake (scene1)")
    r = results["military_vs_emmajake"]
    print(f"    Military       {fmt_grp(r['Military_scene2'])}")
    print(f"    Emma/Jake      {fmt_grp(r['EmmaJake_scene1'])}")
    print(f"    diff={r['mean_diff']:+.2f} CI{r['mean_diff_ci95']}  U={r['mann_whitney_u']}"
          f"  p={r['p_value']:.2e}  sig={r['significant_0.05']}  rb={r['rank_biserial']}")

    print("\n[3] Camera angle (scene1+2)")
    for a in ("front", "30", "45"):
        if a in results["angle_front_30_45"]["groups"]:
            print(f"    {a:6s}        {fmt_grp(results['angle_front_30_45']['groups'][a])}")
    for k, v in results["angle_front_30_45"]["pairwise_mannwhitney"].items():
        print(f"      {k:18s} diff={v['mean_diff']:+.2f}  p={v['p_value']:.2e}  sig={v['significant_0.05']}")

    print("\n[4] Per-speaker (scene1+2), ranked best->worst by IS")
    for s in results["per_speaker"]["ranking_by_mean_is"]:
        print(f"    {s:8s}      {fmt_grp(results['per_speaker']['groups'][s])}")
    for k, v in results["per_speaker"]["pairwise_mannwhitney"].items():
        flag = "*" if v["significant_0.05"] else " "
        print(f"      {flag} {k:20s} diff={v['mean_diff']:+.2f}  p={v['p_value']:.2e}")

    print("\n[5] Confidence-gate operating points (scene1+2, model own word-prob)")
    print(f"    {'gate':>6s} {'keeps%':>7s} {'n':>5s} {'meanIS':>7s} {'WER%':>6s} {'useful%(IS>=2)':>15s}")
    u = gate["ungated"]
    print(f"    {'ALL':>6s} {u['kept_pct']:7.1f} {u['n_kept']:5d} {u['mean_is']:7.2f}"
          f" {u['mean_wer']:6.1f} {u['useful_pct_is_ge_2']:15.1f}")
    for thr in ("0.5", "0.6", "0.7", "0.8"):
        t = gate["thresholds"][thr]
        print(f"    >={thr:>4s} {t['kept_pct']:7.1f} {t['n_kept']:5d} {t['mean_is']:7.2f}"
              f" {t['mean_wer']:6.1f} {t['useful_pct_is_ge_2']:15.1f}")

    print(f"\nWrote {OUT_JSON}")


if __name__ == "__main__":
    main()
