#!/usr/bin/env python3
"""
Analyze the n-best LLM-as-a-Judge run (4 methods x 1497 segments).

Reads:
- docs/evaluation/llm_judge_nbest/batches/  (input)
- docs/evaluation/llm_judge_nbest/judgments/batch_<method>_NN_judgments.txt  (Claude output)
- docs/evaluation/llm_judge_nbest/batch_index.json
- docs/evaluation/llm_judge_nbest/auto_judgments.csv
- english_full_nbest_eval/report/report.csv  (for WER + per-method conf)
- english_full_nbest_eval/conditional_analysis/segment_features.csv  (for sentence_confidence + IS)

Writes:
- llm_judge_nbest/results_long.csv     (one row per (utt_id, method))
- llm_judge_nbest/results_wide.csv     (one row per utt_id, all 4 method verdicts)
- llm_judge_nbest/summary.json         (per-method Y/P/N rates, McNemar, intra-rater)
- llm_judge_nbest/calibration.csv      (confidence bins x method -> P(Y), P(Y+P))
- llm_judge_nbest/llm_judge_nbest_analysis.md  (narrative)

Tolerates partial judgment data — reports per-method completion %.

Usage:
    python3 analyze_nbest_judge.py
"""

import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

BASE_DIR = "/home/ubuntu/docs/evaluation/llm_judge_nbest"
JUDGMENTS_DIR = os.path.join(BASE_DIR, "judgments")
BATCH_INDEX = os.path.join(BASE_DIR, "batch_index.json")
AUTO_JUDGMENTS = os.path.join(BASE_DIR, "auto_judgments.csv")

REPORT_CSV = "/home/ubuntu/english_full_nbest_eval/report/report.csv"
FEATURES_CSV = "/home/ubuntu/english_full_nbest_eval/conditional_analysis/segment_features.csv"

OUTPUT_LONG = os.path.join(BASE_DIR, "results_long.csv")
OUTPUT_WIDE = os.path.join(BASE_DIR, "results_wide.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "summary.json")
OUTPUT_CALIB = os.path.join(BASE_DIR, "calibration.csv")
OUTPUT_MD = os.path.join(BASE_DIR, "llm_judge_nbest_analysis.md")

METHODS = ["baseline", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf"]

METHOD_HYP_COL = {
    "baseline": "hyp",
    "hyp_mbr": "hyp_mbr",
    "hyp_vote_score": "hyp_vote_score",
    "hyp_vote_conf": "hyp_vote_conf",
}
METHOD_WER_COL = {
    "baseline": "wer_%",
    "hyp_mbr": "wer_hyp_mbr_%",
    "hyp_vote_score": "wer_hyp_vote_score_%",
    "hyp_vote_conf": "wer_hyp_vote_conf_%",
}
METHOD_CONF_COL = {
    "baseline": None,  # comes from features.sentence_confidence
    "hyp_mbr": "hyp_mbr_mean_conf_calib",
    "hyp_vote_score": "hyp_vote_score_mean_conf_calib",
    "hyp_vote_conf": "hyp_vote_conf_mean_conf_calib",
}


# ---------- Loaders ----------
def load_csv_dict(path, key="utt_id"):
    out = {}
    with open(path, "r") as f:
        for r in csv.DictReader(f):
            out[r[key]] = r
    return out


def load_batch_index():
    with open(BATCH_INDEX, "r") as f:
        return json.load(f)


def load_auto_judgments():
    """Returns dict (utt_id, method) -> 'N'."""
    auto = {}
    if not os.path.exists(AUTO_JUDGMENTS):
        return auto
    with open(AUTO_JUDGMENTS, "r") as f:
        for r in csv.DictReader(f):
            auto[(r["utt_id"], r["method"])] = r["judgment"]
    return auto


def parse_judgment(text):
    """NNN,JUDGMENT line → (code in {Y,P,N}, preserved_tags, lost_tags, raw_full).
    Annotations: 'P:key+struct/-detail-sem' → preserved=[key,struct], lost=[detail,sem].
    """
    text = text.strip()
    if text in ("Y", "N"):
        return (text, [], [], text)
    if text.startswith("P"):
        if text == "P":
            return ("P", [], [], "P")
        if text.startswith("P:"):
            ann = text[2:]
            preserved, lost = [], []
            parts = ann.split("/")
            if parts:
                preserved = [t for t in parts[0].split("+") if t]
            for p in parts[1:]:
                lost.extend([t.lstrip("-") for t in p.split("-") if t])
            return ("P", preserved, lost, text)
    return (text, [], [], text)


def load_judgments(batch_index):
    """
    For each batch_<method>_NN file, parse and resolve to verdicts keyed by (utt_id, method).
    Duplicates: keep both for reliability stats; for the canonical verdict, prefer the original
    (non-duplicate) entry; if missing, fall back to duplicate.
    Returns:
      verdicts: dict (utt_id, method) -> (code, preserved, lost, raw)
      duplicate_pairs: list of (utt_id, method, code_original, code_duplicate)
      missing_batches: list of batch_keys with no judgment file
      partial_batches: list of (batch_key, expected_n, actual_n)
    """
    verdicts = {}
    dup_capture = defaultdict(list)  # (utt_id, method) -> [verdict, ...]
    missing_batches = []
    partial_batches = []

    for bkey in sorted(batch_index.keys()):
        # bkey = batch_<method>_NN
        m = re.match(r"batch_(.+)_(\d+)$", bkey)
        if not m:
            continue
        method, nn = m.group(1), m.group(2)
        jfile = os.path.join(JUDGMENTS_DIR, f"batch_{method}_{nn}_judgments.txt")
        if not os.path.exists(jfile):
            missing_batches.append(bkey)
            continue

        jdata = {}
        with open(jfile, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                idx_str, _, j_str = line.partition(",")
                try:
                    idx = int(idx_str.strip())
                except ValueError:
                    continue
                jdata[idx] = j_str.strip()

        expected_n = len(batch_index[bkey])
        actual_n = len(jdata)
        if actual_n < expected_n:
            partial_batches.append((bkey, expected_n, actual_n))

        for entry in batch_index[bkey]:
            idx = entry["index"]
            uid = entry["utt_id"]
            is_dup = entry["is_duplicate"]
            if idx not in jdata:
                continue
            verdict = parse_judgment(jdata[idx])
            dup_capture[(uid, method)].append((is_dup, verdict))

    # Resolve canonical verdicts
    for key, lst in dup_capture.items():
        # Prefer non-duplicate original
        original = next((v for is_dup, v in lst if not is_dup), None)
        verdicts[key] = original if original is not None else lst[0][1]

    # Build duplicate pairs for reliability
    duplicate_pairs = []
    for key, lst in dup_capture.items():
        if len(lst) >= 2:
            orig = next(((isd, v) for isd, v in lst if not isd), None)
            dup = next(((isd, v) for isd, v in lst if isd), None)
            if orig and dup:
                duplicate_pairs.append((key[0], key[1], orig[1][0], dup[1][0]))

    return verdicts, duplicate_pairs, missing_batches, partial_batches


# ---------- Stats helpers ----------
def safe_float(s, default=None):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def chi2_1df_pvalue(chi2):
    """Two-sided p-value for chi-square 1 df (= 2*(1 - Phi(sqrt(chi2)))). Pure stdlib."""
    if chi2 < 0:
        return 1.0
    z = math.sqrt(chi2)
    # 1 - Phi(z) using erfc
    p_one = 0.5 * math.erfc(z / math.sqrt(2))
    return 2 * p_one


def mcnemar_test(b, c):
    """Continuity-corrected McNemar; returns (chi2, p)."""
    n = b + c
    if n == 0:
        return (0.0, 1.0)
    chi2 = (abs(b - c) - 1) ** 2 / n
    return (chi2, chi2_1df_pvalue(chi2))


# ---------- Analysis ----------
def main():
    print("=" * 64)
    print("Analyze n-best LLM-as-a-Judge")
    print("=" * 64)

    if not os.path.exists(BATCH_INDEX):
        print(f"ERROR: {BATCH_INDEX} missing — run prepare_nbest_judge_batches.py first")
        sys.exit(1)

    print(f"\nLoading batch index ...")
    batch_index = load_batch_index()
    print(f"  {len(batch_index)} batches indexed")

    print(f"Loading auto-judgments ...")
    auto = load_auto_judgments()
    print(f"  {len(auto)} auto-N entries")

    print(f"Loading report.csv + segment_features.csv ...")
    report = load_csv_dict(REPORT_CSV)
    features = load_csv_dict(FEATURES_CSV)
    print(f"  {len(report)} report rows, {len(features)} feature rows")

    print(f"Loading judgment files ...")
    verdicts, dup_pairs, missing, partial = load_judgments(batch_index)
    print(f"  {len(verdicts)} (utt_id, method) verdicts collected")
    print(f"  {len(dup_pairs)} duplicate pairs for reliability")
    print(f"  {len(missing)} batches missing entirely")
    print(f"  {len(partial)} batches partially judged")

    # ---------- Build long results ----------
    long_rows = []
    for uid, frow in report.items():
        feat = features.get(uid, {})
        ref = frow.get("ref", "").strip()
        sentence_conf = safe_float(feat.get("sentence_confidence"))
        is_score = safe_float(feat.get("is_score"))
        is_tier = feat.get("is_tier", "")
        for method in METHODS:
            hyp = frow.get(METHOD_HYP_COL[method], "").strip()
            wer = safe_float(frow.get(METHOD_WER_COL[method]))
            if METHOD_CONF_COL[method] is None:
                conf = sentence_conf
            else:
                conf = safe_float(frow.get(METHOD_CONF_COL[method]))

            # Verdict resolution: judgment -> auto-N -> missing
            v = verdicts.get((uid, method))
            if v is not None:
                code, preserved, lost, raw = v
                source = "judged"
            elif (uid, method) in auto:
                code, preserved, lost, raw = "N", [], [], "auto-N"
                source = "auto"
            else:
                code, preserved, lost, raw = "", [], [], ""
                source = "missing"

            long_rows.append({
                "utt_id": uid,
                "method": method,
                "ref": ref,
                "hyp": hyp,
                "conf": conf if conf is not None else "",
                "wer_%": wer if wer is not None else "",
                "is_score": is_score if is_score is not None else "",
                "is_tier": is_tier,
                "verdict": code,
                "preserved": "+".join(preserved),
                "lost": "+".join(lost),
                "verdict_raw": raw,
                "source": source,
            })

    # ---------- Per-method counts ----------
    per_method = {m: Counter() for m in METHODS}
    per_method_completion = {m: {"judged": 0, "auto": 0, "missing": 0} for m in METHODS}
    for r in long_rows:
        m = r["method"]
        if r["source"] == "judged":
            per_method[m][r["verdict"]] += 1
            per_method_completion[m]["judged"] += 1
        elif r["source"] == "auto":
            per_method[m]["N"] += 1  # auto-N counts toward N for rate calculations
            per_method_completion[m]["auto"] += 1
        else:
            per_method_completion[m]["missing"] += 1

    summary = {
        "n_segments": len(report),
        "methods": {},
        "missing_batches": missing,
        "partial_batches": [{"batch": b, "expected": e, "actual": a} for (b, e, a) in partial],
        "intra_rater": {},
        "mcnemar_vs_baseline": {},
    }

    for m in METHODS:
        c = per_method[m]
        completed = per_method_completion[m]["judged"] + per_method_completion[m]["auto"]
        total = sum(per_method_completion[m].values())
        n_y = c["Y"]
        n_p = c["P"]
        n_n = c["N"]
        n_total = max(completed, 1)
        summary["methods"][m] = {
            "n_total": total,
            "n_completed": completed,
            "n_missing": per_method_completion[m]["missing"],
            "Y": n_y,
            "P": n_p,
            "N": n_n,
            "Y_rate": n_y / n_total,
            "Y_plus_P_rate": (n_y + n_p) / n_total,
            "completion_pct": completed / total if total else 0.0,
        }

    # ---------- McNemar: each method vs baseline on Y verdict and Y+P verdict ----------
    by_uid_method = defaultdict(dict)
    for r in long_rows:
        by_uid_method[r["utt_id"]][r["method"]] = r

    for m in METHODS:
        if m == "baseline":
            continue
        # paired Y verdicts
        b_y = c_y = 0  # b: m=Y bs=N ; c: m=N bs=Y
        b_yp = c_yp = 0
        n_paired = 0
        for uid, mrows in by_uid_method.items():
            base = mrows.get("baseline")
            mr = mrows.get(m)
            if not base or not mr:
                continue
            if base["verdict"] == "" or mr["verdict"] == "":
                continue
            n_paired += 1
            base_y = base["verdict"] == "Y"
            mr_y = mr["verdict"] == "Y"
            if mr_y and not base_y:
                b_y += 1
            elif base_y and not mr_y:
                c_y += 1
            base_yp = base["verdict"] in ("Y", "P")
            mr_yp = mr["verdict"] in ("Y", "P")
            if mr_yp and not base_yp:
                b_yp += 1
            elif base_yp and not mr_yp:
                c_yp += 1
        chi_y, p_y = mcnemar_test(b_y, c_y)
        chi_yp, p_yp = mcnemar_test(b_yp, c_yp)
        summary["mcnemar_vs_baseline"][m] = {
            "n_paired": n_paired,
            "Y_method_only": b_y, "Y_baseline_only": c_y,
            "Y_chi2": chi_y, "Y_p": p_y,
            "YP_method_only": b_yp, "YP_baseline_only": c_yp,
            "YP_chi2": chi_yp, "YP_p": p_yp,
        }

    # ---------- Intra-rater reliability ----------
    for m in METHODS:
        method_pairs = [(o, d) for (uid, mm, o, d) in dup_pairs if mm == m]
        n = len(method_pairs)
        exact = sum(1 for o, d in method_pairs if o == d)
        # lenient: collapse Y+P vs N
        def lenient(x): return "YP" if x in ("Y", "P") else x
        lenient_match = sum(1 for o, d in method_pairs if lenient(o) == lenient(d))
        summary["intra_rater"][m] = {
            "n": n,
            "exact_agreement": exact / n if n else None,
            "lenient_agreement": lenient_match / n if n else None,
        }

    # ---------- Calibration table: confidence bins x method -> P(Y), P(Y+P) ----------
    calib_rows = []
    bins = [(i / 10, (i + 1) / 10) for i in range(10)]
    for m in METHODS:
        for lo, hi in bins:
            ys, yps, n = 0, 0, 0
            for r in long_rows:
                if r["method"] != m:
                    continue
                if r["source"] == "missing":
                    continue
                conf = r["conf"]
                if conf == "" or conf is None:
                    continue
                cf = float(conf)
                in_bin = (cf >= lo) and (cf < hi if hi < 1.0 else cf <= hi)
                if not in_bin:
                    continue
                n += 1
                if r["verdict"] == "Y":
                    ys += 1
                if r["verdict"] in ("Y", "P"):
                    yps += 1
            calib_rows.append({
                "method": m,
                "conf_bin_lo": lo,
                "conf_bin_hi": hi,
                "n": n,
                "P_Y": ys / n if n else None,
                "P_Y_plus_P": yps / n if n else None,
            })

    # ---------- Write outputs ----------
    print(f"\nWriting {OUTPUT_LONG} ...")
    with open(OUTPUT_LONG, "w", newline="") as f:
        cols = ["utt_id", "method", "ref", "hyp", "conf", "wer_%", "is_score", "is_tier",
                "verdict", "preserved", "lost", "verdict_raw", "source"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(long_rows)

    # wide
    print(f"Writing {OUTPUT_WIDE} ...")
    wide_cols = ["utt_id", "ref"]
    for m in METHODS:
        wide_cols += [f"hyp_{m}", f"conf_{m}", f"wer_{m}", f"verdict_{m}"]
    with open(OUTPUT_WIDE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(wide_cols)
        for uid, mrows in by_uid_method.items():
            ref = next((r["ref"] for r in mrows.values()), "")
            row = [uid, ref]
            for m in METHODS:
                r = mrows.get(m, {})
                row += [r.get("hyp", ""), r.get("conf", ""), r.get("wer_%", ""), r.get("verdict", "")]
            w.writerow(row)

    print(f"Writing {OUTPUT_JSON} ...")
    with open(OUTPUT_JSON, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Writing {OUTPUT_CALIB} ...")
    with open(OUTPUT_CALIB, "w", newline="") as f:
        cols = ["method", "conf_bin_lo", "conf_bin_hi", "n", "P_Y", "P_Y_plus_P"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(calib_rows)

    # ---------- Markdown writeup ----------
    print(f"Writing {OUTPUT_MD} ...")
    write_markdown(summary, OUTPUT_MD)

    # ---------- Console summary ----------
    print("\n" + "=" * 64)
    print("PER-METHOD SUMMARY")
    print("=" * 64)
    for m in METHODS:
        s = summary["methods"][m]
        print(f"  {m:20s} | completion {s['completion_pct']*100:5.1f}% "
              f"| Y {s['Y']:4d} ({s['Y_rate']*100:5.1f}%) "
              f"| Y+P {s['Y'] + s['P']:4d} ({s['Y_plus_P_rate']*100:5.1f}%) "
              f"| N {s['N']:4d}")

    if summary["missing_batches"]:
        print(f"\n  {len(summary['missing_batches'])} batches still need judging — "
              f"re-run after they land.")


def write_markdown(summary, path):
    lines = []
    lines.append("# n-best LLM-as-a-Judge Analysis")
    lines.append("")
    lines.append(f"- Segments evaluated: {summary['n_segments']}")
    lines.append(f"- Methods judged: {', '.join(METHODS)}")
    lines.append(f"- Missing batches: {len(summary['missing_batches'])}")
    lines.append(f"- Partial batches: {len(summary['partial_batches'])}")
    lines.append("")

    lines.append("## Per-method verdict rates")
    lines.append("")
    lines.append("| method | completion | Y | P | N | NIV-Y rate | NIV-Y+P rate |")
    lines.append("|---|---|---|---|---|---|---|")
    for m in METHODS:
        s = summary["methods"][m]
        lines.append(
            f"| {m} | {s['completion_pct']*100:.1f}% | {s['Y']} | {s['P']} | {s['N']} "
            f"| {s['Y_rate']*100:.1f}% | {s['Y_plus_P_rate']*100:.1f}% |"
        )
    lines.append("")

    lines.append("## McNemar — paired Y verdict vs baseline")
    lines.append("")
    lines.append("| method vs baseline | n paired | method-only Y | baseline-only Y | chi^2 (cc) | p |")
    lines.append("|---|---|---|---|---|---|")
    for m, mc in summary["mcnemar_vs_baseline"].items():
        lines.append(
            f"| {m} | {mc['n_paired']} | {mc['Y_method_only']} | {mc['Y_baseline_only']} "
            f"| {mc['Y_chi2']:.2f} | {mc['Y_p']:.4f} |"
        )
    lines.append("")
    lines.append("## McNemar — paired Y+P verdict vs baseline")
    lines.append("")
    lines.append("| method vs baseline | n paired | method-only Y+P | baseline-only Y+P | chi^2 (cc) | p |")
    lines.append("|---|---|---|---|---|---|")
    for m, mc in summary["mcnemar_vs_baseline"].items():
        lines.append(
            f"| {m} | {mc['n_paired']} | {mc['YP_method_only']} | {mc['YP_baseline_only']} "
            f"| {mc['YP_chi2']:.2f} | {mc['YP_p']:.4f} |"
        )
    lines.append("")

    lines.append("## Intra-rater reliability (duplicate pairs)")
    lines.append("")
    lines.append("| method | n duplicates | exact agreement | lenient (Y+P vs N) |")
    lines.append("|---|---|---|---|")
    for m in METHODS:
        ir = summary["intra_rater"].get(m, {})
        ex = ir.get("exact_agreement")
        ln = ir.get("lenient_agreement")
        ex_s = f"{ex*100:.1f}%" if ex is not None else "-"
        ln_s = f"{ln*100:.1f}%" if ln is not None else "-"
        lines.append(
            f"| {m} | {ir.get('n', 0)} | {ex_s} | {ln_s} |"
        )
    lines.append("")
    lines.append("(Calibration table: see `calibration.csv`. Per-segment join: see `results_long.csv` / `results_wide.csv`.)")

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
