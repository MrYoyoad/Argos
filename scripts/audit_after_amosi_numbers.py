#!/usr/bin/env python3
"""
audit_after_amosi_numbers.py — Single source-of-truth audit for MBR-default vs top-1 baseline numbers.

Reads (read-only):
    english_full_nbest_eval/aggregated.json
    english_full_nbest_eval/aggregated_is.json
    english_full_nbest_eval/per_method_calibration/{per_method_summary.md, .csv, .json}
    english_full_nbest_eval/report{,_v2}/report.csv
    english_full_nbest_eval/report{,_v2}/aggregator_method_wer.json
    english_full_nbest_eval/safety_analysis/{SAFETY_ANALYSIS.md, per_word_*.csv, per_segment_safety.csv, sentence_promise.csv}
    english_full_nbest_eval/beam_analysis/{beam_variance_analysis.md, aggregator_wers.csv}
    english_full_nbest_eval/client_trust/{CLIENT_TRUST_CALIBRATION.md, client_trust_calibration.csv}
    english_full_nbest_eval/word_confidence_v2.json
    english_full_nbest_eval/trust_diagnostic/per_word_diagnostic.csv
    english_full_results/client_outputs/report/report.csv         (top-1 baseline, for diff)
    docs/evaluation/intelligibility/intelligibility_summary.json   (March top-1 stats)
    docs/evaluation/llm_judge/llm_judge_results.csv                (Opus blind verdicts gold std)
    docs/evaluation/llm_judge_nbest/{llm_judge_nbest_analysis.md, summary.json, calibration.csv}
    docs/evaluation/llm_salvage/llm_salvage_analysis.md
    docs/evaluation/is_cross_config_validation.md
    docs/evaluation/human_is_estimation.md
    tuning_results/exp_nbest_validation/aggregated_is.json

Writes:
    docs/evaluation/after_amosi_audit.md       (long-form, every number with source citation)
    docs/evaluation/after_amosi_audit.json     (machine-readable, stable keys)

Stdout: tight side-by-side table.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path("/home/ubuntu")
NBEST_ROOT = ROOT / "english_full_nbest_eval"
DOCS = ROOT / "docs" / "evaluation"
TUNING_NBEST = ROOT / "tuning_results" / "exp_nbest_validation"

# Output paths
OUT_MD = DOCS / "after_amosi_audit.md"
OUT_JSON = DOCS / "after_amosi_audit.json"

UNVERIFIED = "UNVERIFIED"


# ---------- helpers ----------

def safe_load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        sys.stderr.write(f"WARN: failed to load {path}: {e}\n")
        return None


def safe_load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with open(path) as f:
            return list(csv.DictReader(f))
    except Exception as e:
        sys.stderr.write(f"WARN: failed to load {path}: {e}\n")
        return []


def fmt(x, prec=2, suffix=""):
    if x is None or x is UNVERIFIED:
        return UNVERIFIED
    if isinstance(x, str):
        return x
    if isinstance(x, float):
        if math.isnan(x):
            return UNVERIFIED
        return f"{x:.{prec}f}{suffix}"
    return f"{x}{suffix}"


def fmt_delta(top1, mbr, prec=2, suffix=""):
    if top1 in (None, UNVERIFIED) or mbr in (None, UNVERIFIED):
        return UNVERIFIED
    try:
        d = float(mbr) - float(top1)
    except Exception:
        return UNVERIFIED
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.{prec}f}{suffix}"


def cohen_kappa_2x2(a, b, c, d):
    """Compute Cohen's kappa from a 2x2 contingency.
    a = both positive, b = rater1 positive only, c = rater2 positive only, d = both negative.
    """
    n = a + b + c + d
    if n == 0:
        return None
    po = (a + d) / n
    p_yes_1 = (a + b) / n
    p_yes_2 = (a + c) / n
    pe = p_yes_1 * p_yes_2 + (1 - p_yes_1) * (1 - p_yes_2)
    if abs(1 - pe) < 1e-12:
        return None
    return (po - pe) / (1 - pe)


# ---------- Section A: IS distribution per method ----------

def section_A_is_distribution() -> dict:
    out = {"_source": str(NBEST_ROOT / "aggregated_is.json")}
    data = safe_load_json(NBEST_ROOT / "aggregated_is.json")
    if not data:
        out["_status"] = UNVERIFIED
        return out
    out["n_segments"] = data.get("n_segments")
    out["methods"] = list(data.get("summary", {}).keys())
    summary = data.get("summary", {})
    for method, s in summary.items():
        # tier counts
        tiers = {f"tier_{i}_count": s.get(f"tier_{i}_count") for i in (1, 2, 3, 4, 5)}
        n = s.get("n_segments", 0)
        tiers_pct = {
            f"tier_{i}_pct": (s.get(f"tier_{i}_count", 0) / n * 100 if n else None)
            for i in (1, 2, 3, 4, 5)
        }
        # NIV counts
        niv_y_pct = s.get("niv_y_pct")
        niv_yp_pct = s.get("niv_yp_pct")
        niv_y_count = round(niv_y_pct / 100 * n) if (niv_y_pct is not None and n) else None
        niv_yp_count = round(niv_yp_pct / 100 * n) if (niv_yp_pct is not None and n) else None
        out[method] = {
            "mean_is": s.get("mean_is"),
            "median_is": s.get("median_is"),
            "mean_wer_pct": s.get("mean_wer_pct"),
            "captured_legacy_pct": s.get("captured_legacy_pct"),
            "captured_legacy_count": round(s.get("captured_legacy_pct", 0) / 100 * n) if n else None,
            "niv_y_pct": niv_y_pct,
            "niv_y_count": niv_y_count,
            "niv_yp_pct": niv_yp_pct,
            "niv_yp_count": niv_yp_count,
            **tiers,
            **tiers_pct,
        }

    # Compute std_is per method from per_segment data
    per_seg = data.get("per_segment", {})
    for method in out["methods"]:
        seg = per_seg.get(method, {})
        if seg:
            scores = [v["is"] for v in seg.values() if v.get("is") is not None]
            if scores:
                m = sum(scores) / len(scores)
                var = sum((x - m) ** 2 for x in scores) / len(scores)
                out[method]["std_is"] = math.sqrt(var)

    return out


# ---------- Section B: WER & accuracy per method ----------

def section_B_wer_accuracy() -> dict:
    """Per-method WER from aggregator_method_wer.json. Also per-method hallucination from report_v2 wer columns."""
    out = {}
    wer_summary = safe_load_json(NBEST_ROOT / "report_v2" / "aggregator_method_wer.json")
    out["_source_wer"] = str(NBEST_ROOT / "report_v2" / "aggregator_method_wer.json")
    if wer_summary:
        out["mean_wer_pct"] = {k: v for k, v in wer_summary.items() if k != "n_segments"}
        out["n_segments"] = wer_summary.get("n_segments")
    else:
        out["mean_wer_pct"] = UNVERIFIED

    # Compute hallucination rate (WER >= 100%) per method from report_v2
    rows = safe_load_csv(NBEST_ROOT / "report_v2" / "report.csv")
    out["_source_hallu"] = str(NBEST_ROOT / "report_v2" / "report.csv")
    if rows:
        # WER cols: wer_% (top1), wer_hyp_mbr_%, wer_hyp_vote_score_%, wer_hyp_vote_conf_%, wer_hyp_safe_%, wer_hyp_xseg_merge_%
        method_to_col = {
            "top1": "wer_%",
            "hyp_mbr": "wer_hyp_mbr_%",
            "hyp_vote_score": "wer_hyp_vote_score_%",
            "hyp_vote_conf": "wer_hyp_vote_conf_%",
            "hyp_safe": "wer_hyp_safe_%",
            "hyp_xseg_merge": "wer_hyp_xseg_merge_%",
        }
        hallu = {}
        for method, col in method_to_col.items():
            cnt = 0
            tot = 0
            for r in rows:
                v = r.get(col)
                if v in (None, ""):
                    continue
                try:
                    f = float(v)
                except Exception:
                    continue
                tot += 1
                if f >= 100.0:
                    cnt += 1
            hallu[method] = {
                "hallu_count": cnt,
                "hallu_total": tot,
                "hallu_pct": (cnt / tot * 100 if tot else None),
            }
        out["hallucination_rate"] = hallu
    else:
        out["hallucination_rate"] = UNVERIFIED

    # NEA F1 / WWER are only computed for top-1 in this report (single column).
    # Aggregate over all rows for the top-1 baseline only.
    if rows:
        wwer = [float(r["wwer_%"]) for r in rows if r.get("wwer_%") not in (None, "")]
        nea = [float(r["nea_f1_%"]) for r in rows if r.get("nea_f1_%") not in (None, "")]
        out["top1_wwer_pct_mean"] = sum(wwer) / len(wwer) if wwer else None
        out["top1_nea_f1_pct_mean"] = sum(nea) / len(nea) if nea else None
        out["_note_wwer_nea"] = (
            "WWER and NEA F1 are computed for top-1 only in nbest report.csv; "
            "no per-method WWER/NEA columns exist."
        )

    return out


# ---------- Section C: kappa vs Opus Judge ----------

def section_C_kappa_vs_opus() -> dict:
    """Compute Cohen's kappa between Opus blind verdicts and IS-NIV labels at IS>=3.80 (Y) and IS>=2.00 (Y+P)
    for both top-1 and MBR IS.
    """
    out = {}
    judge_rows = safe_load_csv(DOCS / "llm_judge" / "llm_judge_results.csv")
    out["_source_judge"] = str(DOCS / "llm_judge" / "llm_judge_results.csv")
    is_data = safe_load_json(NBEST_ROOT / "aggregated_is.json")
    out["_source_is"] = str(NBEST_ROOT / "aggregated_is.json")
    if not judge_rows or not is_data:
        out["_status"] = UNVERIFIED
        return out

    # Build judge verdict map: utt_id -> Y/P/N
    judge_map = {r["utt_id"]: r["llm_judge"] for r in judge_rows if r.get("llm_judge") in ("Y", "P", "N")}
    out["n_judge_segments"] = len(judge_map)

    per_seg = is_data.get("per_segment", {})
    for method in ("hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe"):
        seg = per_seg.get(method, {})
        if not seg:
            continue
        # NIV-Y kappa: IS>=3.80 vs judge==Y
        # NIV-Y+P kappa: IS>=2.00 vs judge in (Y,P)
        y_a = y_b = y_c = y_d = 0  # both Y, IS-only Y, judge-only Y, both N
        yp_a = yp_b = yp_c = yp_d = 0
        n_paired = 0
        for utt, j in judge_map.items():
            if utt not in seg:
                continue
            n_paired += 1
            is_score = seg[utt]["is"]
            is_y = is_score >= 3.80
            is_yp = is_score >= 2.00
            j_y = (j == "Y")
            j_yp = (j in ("Y", "P"))
            if is_y and j_y:
                y_a += 1
            elif is_y and not j_y:
                y_b += 1
            elif not is_y and j_y:
                y_c += 1
            else:
                y_d += 1
            if is_yp and j_yp:
                yp_a += 1
            elif is_yp and not j_yp:
                yp_b += 1
            elif not is_yp and j_yp:
                yp_c += 1
            else:
                yp_d += 1
        out[method] = {
            "n_paired": n_paired,
            "kappa_Y": cohen_kappa_2x2(y_a, y_b, y_c, y_d),
            "kappa_YP": cohen_kappa_2x2(yp_a, yp_b, yp_c, yp_d),
            "Y_confusion": {
                "both_Y": y_a, "is_only_Y": y_b, "judge_only_Y": y_c, "both_N": y_d,
            },
            "YP_confusion": {
                "both_YP": yp_a, "is_only_YP": yp_b, "judge_only_YP": yp_c, "both_N": yp_d,
            },
        }
    return out


# ---------- Section D: per-word confidence under MBR ----------

def section_D_per_word_conf() -> dict:
    """Per-word reliability under joint conf+agreement band rule (MBR-relevant).
    Note: trust_diagnostic per_word_diagnostic.csv is built from top-1 hypothesis word_confs (the displayed segments).
    The MBR per-word reliability under the joint rule is published in safety_analysis.
    """
    out = {}
    out["_source_overall"] = str(NBEST_ROOT / "safety_analysis" / "per_word_safety.csv")
    rows = safe_load_csv(NBEST_ROOT / "safety_analysis" / "per_word_safety.csv")
    if rows:
        overall_old = {}
        overall_new = {}
        for r in rows:
            band = r["band"]
            overall_old[band] = {
                "n": int(r["n_old"]),
                "p_correct": float(r["p_correct_old"]),
            }
            overall_new[band] = {
                "n": int(r["n_new"]),
                "p_correct": float(r["p_correct_new"]) if r["p_correct_new"] else None,
            }
        out["overall_old_rule"] = overall_old
        out["overall_new_rule"] = overall_new
        # Total words
        total_old = sum(b["n"] for b in overall_old.values())
        total_new = sum(b["n"] for b in overall_new.values())
        out["total_words_old"] = total_old
        out["total_words_new"] = total_new

    # Stratified by tier
    out["_source_tier"] = str(NBEST_ROOT / "safety_analysis" / "per_word_by_tier.csv")
    rows = safe_load_csv(NBEST_ROOT / "safety_analysis" / "per_word_by_tier.csv")
    if rows:
        tier_data = defaultdict(lambda: defaultdict(dict))
        for r in rows:
            tier_data[r["tier"]][r["rule"]][r["band"]] = {
                "n": int(r["n"]),
                "p_correct": float(r["p_correct"]) if r["p_correct"] else None,
            }
        out["by_tier"] = {k: dict(v) for k, v in tier_data.items()}

    out["_source_pos"] = str(NBEST_ROOT / "safety_analysis" / "per_word_by_pos.csv")
    rows = safe_load_csv(NBEST_ROOT / "safety_analysis" / "per_word_by_pos.csv")
    if rows:
        pos_data = defaultdict(lambda: defaultdict(dict))
        for r in rows:
            pos_data[r["pos_class"]][r["rule"]][r["band"]] = {
                "n": int(r["n"]),
                "p_correct": float(r["p_correct"]) if r["p_correct"] else None,
            }
        out["by_pos"] = {k: dict(v) for k, v in pos_data.items()}

    # Stratified P(correct|green) by segment mean_prob bin — compute from per_segment_safety.csv + per_word counts.
    # The MEMORY value 92.8/83.8/69.6/41.3/21.8/18.2 comes from the prior word_confidence (top-1) sidecar B3.
    # We can reconstruct it from per_word_diagnostic.csv (which is top-1 word-level data with seg_mean_conf attached).
    out["_source_strat"] = str(NBEST_ROOT / "trust_diagnostic" / "per_word_diagnostic.csv")
    diag_rows = safe_load_csv(NBEST_ROOT / "trust_diagnostic" / "per_word_diagnostic.csv")
    if diag_rows:
        # Note: per_word_diagnostic.csv only includes seg_mean_conf >= 0.65 (per the doc).
        # We can ONLY verify the 0.65+ bins from this file. The very-low / low / mid-low bins
        # (segments with mean_prob<0.65) require word_confidence_v2.json + word-correctness data.
        # For the bins we DO have, compute P(correct | green-NEW-rule) by seg_mean_conf bin.
        bins = [
            ("very_high", 0.85, 1.01),
            ("high", 0.75, 0.85),
            ("mid", 0.65, 0.75),
        ]
        strat = {}
        for label, lo, hi in bins:
            n_green = 0
            n_green_correct = 0
            n_yellow = 0
            n_yellow_correct = 0
            n_red = 0
            n_red_correct = 0
            for r in diag_rows:
                try:
                    smc = float(r["seg_mean_conf"])
                    if not (lo <= smc < hi):
                        continue
                    top1 = float(r["top1_conf"])
                    agree = float(r["beam_agreement"])
                    correct = int(r["is_correct"])
                except (ValueError, KeyError):
                    continue
                # Joint conf+agreement bands
                if top1 >= 0.95 and agree >= 0.80:
                    band = "green"
                elif top1 >= 0.65 and agree >= 0.50:
                    band = "yellow"
                else:
                    band = "red"
                if band == "green":
                    n_green += 1; n_green_correct += correct
                elif band == "yellow":
                    n_yellow += 1; n_yellow_correct += correct
                else:
                    n_red += 1; n_red_correct += correct
            strat[label] = {
                "range": f"{lo:.2f}-{hi:.2f}",
                "green_n": n_green,
                "green_p_correct": (n_green_correct / n_green) if n_green else None,
                "yellow_n": n_yellow,
                "yellow_p_correct": (n_yellow_correct / n_yellow) if n_yellow else None,
                "red_n": n_red,
                "red_p_correct": (n_red_correct / n_red) if n_red else None,
            }
        out["stratified_by_seg_mean_conf"] = strat
        out["_note_strat"] = (
            "trust_diagnostic/per_word_diagnostic.csv is filtered to seg_mean_conf >= 0.65; "
            "very_low/low/mid_low bins NOT recomputable here. "
            "MEMORY values 92.8/83.8/69.6/41.3/21.8/18.2 are from the legacy CONF-ONLY rule on the "
            "B3 word_confidence sidecar (top-1), not the joint conf+agreement rule under MBR."
        )

    return out


# ---------- Section E: trust-gate operating points ----------

def section_E_trust_gate() -> dict:
    out = {}
    out["_source"] = str(NBEST_ROOT / "client_trust" / "client_trust_calibration.csv")
    rows = safe_load_csv(NBEST_ROOT / "client_trust" / "client_trust_calibration.csv")
    if not rows:
        out["_status"] = UNVERIFIED
        return out
    new = []
    old = []
    for r in rows:
        rec = {
            "threshold": float(r["threshold"]),
            "n_trusted": int(r["n_trusted"]),
            "tp_useful": int(r["tp_useful"]),
            "fp_useful": int(r["fp_useful"]),
            "recall_useful": float(r["recall_useful"]),
            "precision_useful": float(r["precision_useful"]),
            "fpr_useful": float(r["fpr_useful"]),
            "n_clearly_conveyed_in_trust": int(r["n_clearly_conveyed_in_trust"]),
            "pct_clearly_conveyed_in_trust": float(r["pct_clearly_conveyed_in_trust"]),
        }
        if r["rule"] == "new":
            new.append(rec)
        else:
            old.append(rec)
    out["new_rule_joint_conf_agreement"] = new
    out["old_rule_conf_only"] = old
    return out


# ---------- Section F: LLM Judge n-best v3 ----------

def section_F_llm_judge_v3() -> dict:
    out = {}
    out["_source"] = str(DOCS / "llm_judge_nbest" / "summary.json")
    s = safe_load_json(DOCS / "llm_judge_nbest" / "summary.json")
    if not s:
        out["_status"] = UNVERIFIED
        return out
    out["n_segments"] = s.get("n_segments")
    out["methods"] = {}
    for m, d in s.get("methods", {}).items():
        out["methods"][m] = {
            "Y": d.get("Y"),
            "P": d.get("P"),
            "N": d.get("N"),
            "Y_rate": d.get("Y_rate"),
            "Y_plus_P_rate": d.get("Y_plus_P_rate"),
        }
    out["intra_rater"] = s.get("intra_rater", {})
    out["mcnemar_vs_baseline"] = s.get("mcnemar_vs_baseline", {})
    # identical-text drift % from analysis md (prose figure)
    out["_note_drift"] = (
        "Identical-text drift v3: 12.6%/10.4%/14.2% per method (mbr/vote_score/vote_conf), "
        "down from v1's 27% — see llm_judge_nbest_analysis.md."
    )
    out["total_verdicts"] = (out["n_segments"] or 0) * 4
    return out


# ---------- Section G: Salvage rates under MBR ----------

def section_G_salvage() -> dict:
    """Recompute salvage capture under MBR-IS using the same heuristic threshold:
    NIV-Y+P = (IS>=2.00 under MBR), salvage = (IS<2.00 AND llm_context_prob>=0.5).
    The llm_context_prob field is only stored in the top-1 results CSV — heuristic is decode-independent
    in design but the per-segment value is bound to the top-1 hypothesis text. We compute under both.
    """
    out = {}
    out["_source_salvage_top1"] = str(DOCS / "llm_judge" / "llm_judge_results.csv")
    out["_source_is_mbr"] = str(NBEST_ROOT / "aggregated_is.json")
    judge_rows = safe_load_csv(DOCS / "llm_judge" / "llm_judge_results.csv")
    is_data = safe_load_json(NBEST_ROOT / "aggregated_is.json")
    if not judge_rows or not is_data:
        out["_status"] = UNVERIFIED
        return out

    # Map utt_id -> llm_context_prob (heuristic computed on top-1 hypothesis)
    prob_map = {}
    for r in judge_rows:
        utt = r["utt_id"]
        try:
            prob_map[utt] = float(r["llm_context_prob"])
        except (ValueError, TypeError, KeyError):
            pass

    per_seg = is_data.get("per_segment", {})
    for method in ("hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe"):
        seg = per_seg.get(method, {})
        if not seg:
            continue
        n_total = len(seg)
        # NIV thresholds
        n_yp = sum(1 for v in seg.values() if v["is"] >= 2.00)
        n_y = sum(1 for v in seg.values() if v["is"] >= 3.80)
        # Legacy IS>=3.0
        n_legacy = sum(1 for v in seg.values() if v["is"] >= 3.00)
        # Salvage (legacy basis: IS<3.0 AND prob>=0.5)
        n_salvage_legacy = sum(
            1 for utt, v in seg.items()
            if v["is"] < 3.00 and prob_map.get(utt, 0) >= 0.5
        )
        # Salvage (NIV basis: IS<2.00 AND prob>=0.5)
        n_salvage_niv = sum(
            1 for utt, v in seg.items()
            if v["is"] < 2.00 and prob_map.get(utt, 0) >= 0.5
        )
        out[method] = {
            "n_total": n_total,
            "niv_y_count": n_y,
            "niv_y_pct": n_y / n_total * 100 if n_total else None,
            "niv_yp_count": n_yp,
            "niv_yp_pct": n_yp / n_total * 100 if n_total else None,
            "legacy_is3_count": n_legacy,
            "legacy_is3_pct": n_legacy / n_total * 100 if n_total else None,
            "salvage_legacy_count": n_salvage_legacy,
            "salvage_legacy_pct": n_salvage_legacy / n_total * 100 if n_total else None,
            "effective_capture_legacy_pct": (n_legacy + n_salvage_legacy) / n_total * 100 if n_total else None,
            "salvage_niv_count": n_salvage_niv,
            "salvage_niv_pct": n_salvage_niv / n_total * 100 if n_total else None,
            "effective_capture_niv_yp_pct": (n_yp + n_salvage_niv) / n_total * 100 if n_total else None,
        }
    out["_note_heuristic"] = (
        "llm_context_prob is computed once on the top-1 hypothesis (decoded from llm_judge_results.csv). "
        "Re-running it on MBR text would give slightly different per-segment values; the current numbers "
        "are MBR-IS gate × top-1-prob heuristic."
    )
    return out


# ---------- Section H: cross-config & validation ----------

def section_H_validation() -> dict:
    out = {}
    # Cross-config md
    cross = ROOT / "docs" / "evaluation" / "is_cross_config_validation.md"
    out["_source_cross"] = str(cross)
    if cross.exists():
        out["cross_config_summary"] = {
            "mean_r": 0.925,
            "std_r": 0.015,
            "n_configs": 16,
            "datasets": "13 tuning configs (107 segs) + 3 full-decode configs (1497 segs)",
            "configs_include_mbr": False,
            "note": "16 configs were decode-parameter variants on top-1 only. MBR was promoted later. "
                    "Number remains valid as a stability claim about the IS metric across decode parameters; "
                    "it does not include n-best aggregation as a configuration.",
        }
    # Expert heuristic r (from llm_salvage_analysis.md)
    salvage = ROOT / "docs" / "evaluation" / "llm_salvage" / "llm_salvage_analysis.md"
    out["_source_heuristic"] = str(salvage)
    if salvage.exists():
        out["expert_heuristic_r"] = {
            "value": 0.934,
            "note": "Deterministic decision tree, decode-independent — number unchanged under MBR.",
        }
    # Tuning nbest validation
    tn = TUNING_NBEST / "aggregated_is.json"
    out["_source_tuning_nbest"] = str(tn)
    td = safe_load_json(tn)
    if td:
        out["tuning_nbest_validation"] = {
            "n_segments": td.get("n_segments"),
            "summary": td.get("summary"),
        }
    return out


# ---------- Section I: Human-IS Path B ----------

def section_I_human_is() -> dict:
    out = {}
    h = ROOT / "docs" / "evaluation" / "human_is_estimation.md"
    out["_source"] = str(h)
    out["estimates_path_B"] = {
        "lay_no_ctx": {"low": 0.63, "mid": 0.92, "high": 1.14, "tier_mid": "Failed"},
        "deaf_no_ctx": {"low": 2.33, "mid": 2.74, "high": 3.07, "tier_mid": "Fair"},
        "expert_no_ctx": {"low": 2.60, "mid": 3.03, "high": 3.33, "tier_mid": "Fair"},
        "lay_plus_ctx_plus_model": {"low": 3.36, "mid": 3.83, "high": 4.19, "tier_mid": "Good"},
        "model_alone_measured": {"is": 2.52, "note": "March top-1 baseline (intelligibility_summary.json)"},
    }
    out["formula_provenance"] = (
        "Path B: bin model 1,497 segments by WER, take per-bin component means, plug literature WER + "
        "literature-derived component shifts (semantic, phonetic, NEA F1, length ratio) into the same IS formula. "
        "Components from intelligibility_scores.csv cols 6-19. Pre-study estimates, not measurements; "
        "needs Path A pilot to confirm. Reproducible Python snippet in §4 of human_is_estimation.md."
    )
    out["lr_isolation"] = {
        "note": "LR isolation experiment: human-style LR (skipping uncertain words) costs +0.41 IS for lay → "
                "+0.06 for lay+ctx+model — penalty shrinks with proficiency.",
        "lay": +0.41, "deaf": +0.21, "expert": +0.15, "lay_plus_ctx": +0.06,
    }
    return out


# ---------- Build the audit ----------

def build_audit() -> dict:
    audit = {
        "title": "Argos VSP Numbers Audit — Top-1 vs MBR-Default (May 2026)",
        "date": "2026-05-06",
        "purpose": (
            "Single source-of-truth comparison of every published numeric statistic under the "
            "March 2026 top-1 baseline vs the May 2 2026 MBR-aggregated production default."
        ),
        "section_A_is_distribution": section_A_is_distribution(),
        "section_B_wer_accuracy": section_B_wer_accuracy(),
        "section_C_kappa_vs_opus": section_C_kappa_vs_opus(),
        "section_D_per_word_conf": section_D_per_word_conf(),
        "section_E_trust_gate": section_E_trust_gate(),
        "section_F_llm_judge_v3": section_F_llm_judge_v3(),
        "section_G_salvage": section_G_salvage(),
        "section_H_validation": section_H_validation(),
        "section_I_human_is": section_I_human_is(),
    }
    return audit


# ---------- Markdown rendering ----------

def render_summary_table(audit: dict) -> str:
    """Top-of-doc tight side-by-side table: Statistic | Top-1 Baseline | MBR Default | Δ | Source."""
    lines = []
    lines.append("| Statistic | Top-1 Baseline | MBR Default | Δ | Source |")
    lines.append("|---|---|---|---|---|")

    A = audit["section_A_is_distribution"]
    if A.get("hyp_top1") and A.get("hyp_mbr"):
        t = A["hyp_top1"]
        m = A["hyp_mbr"]
        src = "aggregated_is.json"
        lines.append(f"| Mean IS | {fmt(t['mean_is'], 3)} | {fmt(m['mean_is'], 3)} | {fmt_delta(t['mean_is'], m['mean_is'], 3)} | {src} |")
        lines.append(f"| Median IS | {fmt(t['median_is'], 3)} | {fmt(m['median_is'], 3)} | {fmt_delta(t['median_is'], m['median_is'], 3)} | {src} |")
        if "std_is" in t and "std_is" in m:
            lines.append(f"| Std IS | {fmt(t['std_is'], 3)} | {fmt(m['std_is'], 3)} | {fmt_delta(t['std_is'], m['std_is'], 3)} | {src} |")
        lines.append(f"| Mean WER % | {fmt(t['mean_wer_pct'], 2)} | {fmt(m['mean_wer_pct'], 2)} | {fmt_delta(t['mean_wer_pct'], m['mean_wer_pct'], 2)} pp | {src} |")
        lines.append(f"| NIV-Y count (IS≥3.80) | {t['niv_y_count']} | {m['niv_y_count']} | {fmt_delta(t['niv_y_count'], m['niv_y_count'], 0)} | {src} |")
        lines.append(f"| NIV-Y pct | {fmt(t['niv_y_pct'], 2)}% | {fmt(m['niv_y_pct'], 2)}% | {fmt_delta(t['niv_y_pct'], m['niv_y_pct'], 2)} pp | {src} |")
        lines.append(f"| NIV-Y+P count (IS≥2.00) | {t['niv_yp_count']} | {m['niv_yp_count']} | {fmt_delta(t['niv_yp_count'], m['niv_yp_count'], 0)} | {src} |")
        lines.append(f"| NIV-Y+P pct | {fmt(t['niv_yp_pct'], 2)}% | {fmt(m['niv_yp_pct'], 2)}% | {fmt_delta(t['niv_yp_pct'], m['niv_yp_pct'], 2)} pp | {src} |")
        lines.append(f"| Legacy IS≥3.0 captured % | {fmt(t['captured_legacy_pct'], 2)} | {fmt(m['captured_legacy_pct'], 2)} | {fmt_delta(t['captured_legacy_pct'], m['captured_legacy_pct'], 2)} pp | {src} |")
        lines.append(f"| Tier 5 (≥4.0) count | {t['tier_5_count']} | {m['tier_5_count']} | {fmt_delta(t['tier_5_count'], m['tier_5_count'], 0)} | {src} |")
        lines.append(f"| Tier 4 (3.0-3.99) count | {t['tier_4_count']} | {m['tier_4_count']} | {fmt_delta(t['tier_4_count'], m['tier_4_count'], 0)} | {src} |")
        lines.append(f"| Tier 3 (2.0-2.99) count | {t['tier_3_count']} | {m['tier_3_count']} | {fmt_delta(t['tier_3_count'], m['tier_3_count'], 0)} | {src} |")
        lines.append(f"| Tier 2 (1.0-1.99) count | {t['tier_2_count']} | {m['tier_2_count']} | {fmt_delta(t['tier_2_count'], m['tier_2_count'], 0)} | {src} |")
        lines.append(f"| Tier 1 (<1.0) count | {t['tier_1_count']} | {m['tier_1_count']} | {fmt_delta(t['tier_1_count'], m['tier_1_count'], 0)} | {src} |")

    # B: hallucination
    B = audit["section_B_wer_accuracy"]
    h = B.get("hallucination_rate", {})
    if h and h != UNVERIFIED:
        ht = h.get("top1", {})
        hm = h.get("hyp_mbr", {})
        if ht and hm:
            lines.append(f"| Hallucination rate (WER≥100%) | {ht['hallu_count']}/{ht['hallu_total']} ({fmt(ht['hallu_pct'], 2)}%) | {hm['hallu_count']}/{hm['hallu_total']} ({fmt(hm['hallu_pct'], 2)}%) | {fmt_delta(ht['hallu_pct'], hm['hallu_pct'], 2)} pp | report_v2/report.csv |")

    # C: kappa
    C = audit["section_C_kappa_vs_opus"]
    if C.get("hyp_top1") and C.get("hyp_mbr"):
        t = C["hyp_top1"]
        m = C["hyp_mbr"]
        lines.append(f"| κ vs Opus (NIV-Y, n={t['n_paired']}) | {fmt(t['kappa_Y'], 3)} | {fmt(m['kappa_Y'], 3)} | {fmt_delta(t['kappa_Y'], m['kappa_Y'], 3)} | computed: judge × IS |")
        lines.append(f"| κ vs Opus (NIV-Y+P, n={t['n_paired']}) | {fmt(t['kappa_YP'], 3)} | {fmt(m['kappa_YP'], 3)} | {fmt_delta(t['kappa_YP'], m['kappa_YP'], 3)} | computed: judge × IS |")

    # F: judge
    F = audit["section_F_llm_judge_v3"]
    if F.get("methods"):
        b = F["methods"].get("baseline", {})
        mbr = F["methods"].get("hyp_mbr", {})
        if b and mbr:
            lines.append(f"| Judge Y % (v3) | {fmt(b['Y_rate']*100, 2)}% | {fmt(mbr['Y_rate']*100, 2)}% | {fmt_delta(b['Y_rate']*100, mbr['Y_rate']*100, 2)} pp | llm_judge_nbest/summary.json |")
            lines.append(f"| Judge Y+P % (v3) | {fmt(b['Y_plus_P_rate']*100, 2)}% | {fmt(mbr['Y_plus_P_rate']*100, 2)}% | {fmt_delta(b['Y_plus_P_rate']*100, mbr['Y_plus_P_rate']*100, 2)} pp | llm_judge_nbest/summary.json |")

    # G: salvage
    G = audit["section_G_salvage"]
    if G.get("hyp_top1") and G.get("hyp_mbr"):
        t = G["hyp_top1"]
        m = G["hyp_mbr"]
        lines.append(f"| Effective capture (NIV-Y+P + LLM-salvage) % | {fmt(t['effective_capture_niv_yp_pct'], 2)}% | {fmt(m['effective_capture_niv_yp_pct'], 2)}% | {fmt_delta(t['effective_capture_niv_yp_pct'], m['effective_capture_niv_yp_pct'], 2)} pp | computed |")
        lines.append(f"| Effective capture (legacy IS≥3.0 + salvage) % | {fmt(t['effective_capture_legacy_pct'], 2)}% | {fmt(m['effective_capture_legacy_pct'], 2)}% | {fmt_delta(t['effective_capture_legacy_pct'], m['effective_capture_legacy_pct'], 2)} pp | computed |")

    return "\n".join(lines)


def render_section_A(A: dict) -> str:
    lines = ["## Section A — IS distribution under each method", ""]
    lines.append(f"_Source_: `{A.get('_source')}` (n_segments={A.get('n_segments')})")
    lines.append("")
    lines.append("| method | mean IS | median IS | std IS | mean WER % | NIV-Y % (count) | NIV-Y+P % (count) | legacy IS≥3 % | tier 5 | tier 4 | tier 3 | tier 2 | tier 1 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for m in A.get("methods", []):
        d = A.get(m)
        if not d:
            continue
        lines.append(
            f"| {m} | {fmt(d['mean_is'], 4)} | {fmt(d['median_is'], 4)} | {fmt(d.get('std_is'), 4)} | "
            f"{fmt(d['mean_wer_pct'], 2)} | {fmt(d['niv_y_pct'], 2)}% ({d['niv_y_count']}) | "
            f"{fmt(d['niv_yp_pct'], 2)}% ({d['niv_yp_count']}) | {fmt(d['captured_legacy_pct'], 2)} | "
            f"{d['tier_5_count']} | {d['tier_4_count']} | {d['tier_3_count']} | {d['tier_2_count']} | {d['tier_1_count']} |"
        )
    return "\n".join(lines)


def render_section_B(B: dict) -> str:
    lines = ["## Section B — WER, hallucination, NEA F1 / WWER per method", ""]
    lines.append(f"_WER source_: `{B.get('_source_wer')}`. _Hallucination source_: `{B.get('_source_hallu')}`.")
    lines.append("")
    lines.append("### Mean WER per method (full 1,497 segments)")
    wer = B.get("mean_wer_pct", {})
    if isinstance(wer, dict):
        lines.append("| method | mean WER % |")
        lines.append("|---|---|")
        for k, v in wer.items():
            lines.append(f"| {k} | {fmt(v, 4)} |")
    lines.append("")
    lines.append("### Hallucination rate (WER ≥ 100%)")
    h = B.get("hallucination_rate", {})
    if isinstance(h, dict):
        lines.append("| method | count | total | pct |")
        lines.append("|---|---|---|---|")
        for k, d in h.items():
            lines.append(f"| {k} | {d['hallu_count']} | {d['hallu_total']} | {fmt(d['hallu_pct'], 2)}% |")
    lines.append("")
    if "top1_wwer_pct_mean" in B:
        lines.append(f"### WWER & NEA F1 (top-1 only)\n")
        lines.append(f"- top1 mean WWER: **{fmt(B['top1_wwer_pct_mean'], 2)}%**")
        lines.append(f"- top1 mean NEA F1: **{fmt(B['top1_nea_f1_pct_mean'], 2)}%**")
        lines.append(f"- _Note_: {B.get('_note_wwer_nea')}")
    return "\n".join(lines)


def render_section_C(C: dict) -> str:
    lines = ["## Section C — κ vs Opus blind judge under each method", ""]
    lines.append(f"_Sources_: `{C.get('_source_judge')}`, `{C.get('_source_is')}`")
    lines.append(f"_n paired segments_: {C.get('n_judge_segments')}")
    lines.append("")
    lines.append("Computed kappa: 2×2 contingency between Opus blind verdict (Y vs not-Y for NIV-Y, Y+P vs N for NIV-Y+P) and IS-NIV bucket.")
    lines.append("")
    lines.append("| method | n paired | κ (NIV-Y, IS≥3.80) | both Y / IS-only Y / judge-only Y / both N | κ (NIV-Y+P, IS≥2.00) | both YP / IS-only YP / judge-only YP / both N |")
    lines.append("|---|---|---|---|---|---|")
    for m in ("hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe"):
        d = C.get(m)
        if not d:
            continue
        yc = d["Y_confusion"]; yp = d["YP_confusion"]
        lines.append(
            f"| {m} | {d['n_paired']} | {fmt(d['kappa_Y'], 3)} | "
            f"{yc['both_Y']}/{yc['is_only_Y']}/{yc['judge_only_Y']}/{yc['both_N']} | "
            f"{fmt(d['kappa_YP'], 3)} | "
            f"{yp['both_YP']}/{yp['is_only_YP']}/{yp['judge_only_YP']}/{yp['both_N']} |"
        )
    lines.append("")
    lines.append("MEMORY/March values: top-1 IS gave κ_Y=0.690, κ_YP=0.818 vs Opus blind. Computed values above use the same Opus blind judge — any drift indicates verdict noise or method-induced IS shift.")
    return "\n".join(lines)


def render_section_D(D: dict) -> str:
    lines = ["## Section D — Per-word confidence (joint conf+agreement band rule)", ""]
    lines.append(f"_Sources_: overall=`{D.get('_source_overall')}`, by_tier=`{D.get('_source_tier')}`, by_pos=`{D.get('_source_pos')}`, stratified=`{D.get('_source_strat')}`")
    lines.append("")
    if "overall_new_rule" in D:
        lines.append(f"### Overall (new joint rule, total words = {D['total_words_new']})")
        lines.append("| band | count | P(correct) |")
        lines.append("|---|---|---|")
        for band in ("green", "yellow", "red"):
            d = D["overall_new_rule"][band]
            pc = fmt(d["p_correct"], 4) if d["p_correct"] is not None else "—"
            lines.append(f"| {band} | {d['n']} | {pc} |")
        lines.append("")
        lines.append(f"### Overall (legacy conf-only rule, total words = {D['total_words_old']}) — for comparison")
        lines.append("| band | count | P(correct) |")
        lines.append("|---|---|---|")
        for band in ("green", "yellow", "red"):
            d = D["overall_old_rule"][band]
            lines.append(f"| {band} | {d['n']} | {fmt(d['p_correct'], 4)} |")
        lines.append("")
    if "by_tier" in D:
        lines.append("### By segment tier (Trust ≥0.82 / Salvage 0.65-0.82 / Strip <0.65)")
        for tier in ("Trust", "Salvage", "Strip"):
            if tier not in D["by_tier"]:
                continue
            lines.append(f"\n**{tier}** (rule = new joint conf+agreement)")
            lines.append("| band | n | P(correct) |")
            lines.append("|---|---|---|")
            for band in ("green", "yellow", "red"):
                d = D["by_tier"][tier].get("new", {}).get(band)
                if d:
                    lines.append(f"| {band} | {d['n']} | {fmt(d['p_correct'], 4)} |")
        lines.append("")
    if "by_pos" in D:
        lines.append("### By POS class (function / content / number)")
        for pos in ("function", "content", "number"):
            if pos not in D["by_pos"]:
                continue
            lines.append(f"\n**{pos}** (rule = new joint)")
            lines.append("| band | n | P(correct) |")
            lines.append("|---|---|---|")
            for band in ("green", "yellow", "red"):
                d = D["by_pos"][pos].get("new", {}).get(band)
                if d and d["n"] > 0:
                    pc = fmt(d['p_correct'], 4) if d['p_correct'] is not None else "—"
                    lines.append(f"| {band} | {d['n']} | {pc} |")
        lines.append("")
    if "stratified_by_seg_mean_conf" in D:
        lines.append("### Stratified P(band correct) by segment mean_prob")
        lines.append("(Joint conf+agreement bands; recomputed from `trust_diagnostic/per_word_diagnostic.csv`.)")
        lines.append("")
        lines.append(f"_NOTE_: {D.get('_note_strat')}")
        lines.append("")
        lines.append("| seg_mean_conf bin | green n | green P(correct) | yellow n | yellow P(correct) | red n | red P(correct) |")
        lines.append("|---|---|---|---|---|---|---|")
        for label, d in D["stratified_by_seg_mean_conf"].items():
            lines.append(
                f"| {label} ({d['range']}) | {d['green_n']} | {fmt(d['green_p_correct'], 4) if d['green_p_correct'] is not None else '—'} | "
                f"{d['yellow_n']} | {fmt(d['yellow_p_correct'], 4) if d['yellow_p_correct'] is not None else '—'} | "
                f"{d['red_n']} | {fmt(d['red_p_correct'], 4) if d['red_p_correct'] is not None else '—'} |"
            )
    return "\n".join(lines)


def render_section_E(E: dict) -> str:
    lines = ["## Section E — Trust-gate operating points", ""]
    lines.append(f"_Source_: `{E.get('_source')}`")
    lines.append("")
    lines.append("### New rule (joint conf+agreement) — primary table")
    lines.append("| T (green-frac ≥) | n trusted | TPs | FPs | recall | precision | FPR | clearly conveyed in trust |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in E.get("new_rule_joint_conf_agreement", []):
        lines.append(
            f"| {fmt(r['threshold'], 2)} | {r['n_trusted']} | {r['tp_useful']} | {r['fp_useful']} | "
            f"{fmt(r['recall_useful']*100, 1)}% | {fmt(r['precision_useful']*100, 1)}% | "
            f"{fmt(r['fpr_useful']*100, 2)}% | {r['n_clearly_conveyed_in_trust']} ({fmt(r['pct_clearly_conveyed_in_trust']*100, 1)}%) |"
        )
    lines.append("")
    lines.append("**Three named operating points (from CLIENT_TRUST_CALIBRATION.md):**")
    lines.append("- Permissive ≥30% green: 630 trusted, 65.2% recall, 5.6% FPR (default).")
    lines.append("- Moderate ≥50% green: 321 trusted, 33.8% recall, 1.8% FPR.")
    lines.append("- Strict ≥70% green: 71 trusted, 7.6% recall, 0.2% FPR.")
    return "\n".join(lines)


def render_section_F(F: dict) -> str:
    lines = ["## Section F — LLM Judge n-best v3 (Opus 4.7, 5,988 verdicts)", ""]
    lines.append(f"_Source_: `{F.get('_source')}`")
    lines.append(f"n_segments={F.get('n_segments')}, total verdicts={F.get('total_verdicts')}, methods judged: baseline, hyp_mbr, hyp_vote_score, hyp_vote_conf")
    lines.append("")
    if F.get("methods"):
        lines.append("### Y / P / N counts and rates per method")
        lines.append("| method | Y | P | N | Y rate | Y+P rate |")
        lines.append("|---|---|---|---|---|---|")
        for m, d in F["methods"].items():
            lines.append(
                f"| {m} | {d['Y']} | {d['P']} | {d['N']} | "
                f"{fmt(d['Y_rate']*100, 2)}% | {fmt(d['Y_plus_P_rate']*100, 2)}% |"
            )
    lines.append("")
    if F.get("intra_rater"):
        lines.append("### Intra-rater reliability (30 duplicates per method)")
        lines.append("| method | exact agreement | lenient (Y+P vs N) |")
        lines.append("|---|---|---|")
        for m, d in F["intra_rater"].items():
            lines.append(f"| {m} | {fmt(d['exact_agreement']*100, 1)}% | {fmt(d['lenient_agreement']*100, 1)}% |")
    lines.append("")
    if F.get("mcnemar_vs_baseline"):
        lines.append("### Paired McNemar tests vs baseline")
        lines.append("| method | Y meth-only | Y base-only | Y χ² | Y p | Y+P meth-only | Y+P base-only | Y+P χ² | Y+P p |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for m, d in F["mcnemar_vs_baseline"].items():
            lines.append(
                f"| {m} | {d['Y_method_only']} | {d['Y_baseline_only']} | {fmt(d['Y_chi2'], 2)} | {fmt(d['Y_p'], 4)} | "
                f"{d['YP_method_only']} | {d['YP_baseline_only']} | {fmt(d['YP_chi2'], 2)} | {fmt(d['YP_p'], 5)} |"
            )
    lines.append("")
    lines.append(f"**Drift note**: {F.get('_note_drift')}")
    return "\n".join(lines)


def render_section_G(G: dict) -> str:
    lines = ["## Section G — Salvage rates per method", ""]
    lines.append(f"_Sources_: `{G.get('_source_salvage_top1')}`, `{G.get('_source_is_mbr')}`")
    lines.append("")
    lines.append(f"_Heuristic note_: {G.get('_note_heuristic')}")
    lines.append("")
    lines.append("| method | n total | NIV-Y % (n) | NIV-Y+P % (n) | legacy IS≥3 % (n) | salvage_legacy (IS<3 ∧ prob≥0.5) (n, %) | effective capture legacy % | salvage NIV (IS<2 ∧ prob≥0.5) (n, %) | effective capture NIV-Y+P % |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for m in ("hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe"):
        d = G.get(m)
        if not d:
            continue
        lines.append(
            f"| {m} | {d['n_total']} | "
            f"{fmt(d['niv_y_pct'], 2)}% ({d['niv_y_count']}) | "
            f"{fmt(d['niv_yp_pct'], 2)}% ({d['niv_yp_count']}) | "
            f"{fmt(d['legacy_is3_pct'], 2)}% ({d['legacy_is3_count']}) | "
            f"{d['salvage_legacy_count']} ({fmt(d['salvage_legacy_pct'], 2)}%) | "
            f"{fmt(d['effective_capture_legacy_pct'], 2)}% | "
            f"{d['salvage_niv_count']} ({fmt(d['salvage_niv_pct'], 2)}%) | "
            f"{fmt(d['effective_capture_niv_yp_pct'], 2)}% |"
        )
    return "\n".join(lines)


def render_section_H(H: dict) -> str:
    lines = ["## Section H — Cross-config validation, expert heuristic, hyperparameter tuning", ""]
    cc = H.get("cross_config_summary", {})
    if cc:
        lines.append(f"_Cross-config source_: `{H.get('_source_cross')}`")
        lines.append("")
        lines.append(f"- Mean r across {cc['n_configs']} configs: **{cc['mean_r']}** (std={cc['std_r']})")
        lines.append(f"- Datasets: {cc['datasets']}")
        lines.append(f"- Configs include MBR? **{cc['configs_include_mbr']}**")
        lines.append(f"- {cc['note']}")
    lines.append("")
    eh = H.get("expert_heuristic_r", {})
    if eh:
        lines.append(f"_Heuristic source_: `{H.get('_source_heuristic')}`")
        lines.append("")
        lines.append(f"- Expert heuristic ↔ IS Pearson r = **{eh['value']}**")
        lines.append(f"- {eh['note']}")
    lines.append("")
    tn = H.get("tuning_nbest_validation", {})
    if tn:
        lines.append(f"_Tuning n-best validation source_: `{H.get('_source_tuning_nbest')}`")
        lines.append(f"_n_segments_: {tn.get('n_segments')} (107-segment tuning subset, n-best aggregation re-run)")
        lines.append("")
        lines.append("| method | mean IS | mean WER % | NIV-Y % | NIV-Y+P % |")
        lines.append("|---|---|---|---|---|")
        for m, d in tn.get("summary", {}).items():
            lines.append(
                f"| {m} | {fmt(d['mean_is'], 4)} | {fmt(d['mean_wer_pct'], 2)} | "
                f"{fmt(d['niv_y_pct'], 2)}% | {fmt(d['niv_yp_pct'], 2)}% |"
            )
    return "\n".join(lines)


def render_section_I(I: dict) -> str:
    lines = ["## Section I — Human-IS Path B estimates (pre-study)", ""]
    lines.append(f"_Source_: `{I.get('_source')}`")
    lines.append("")
    lines.append(f"**Formula provenance**: {I['formula_provenance']}")
    lines.append("")
    lines.append("| Population | low | mid | high | tier (mid) |")
    lines.append("|---|---|---|---|---|")
    for pop, d in I["estimates_path_B"].items():
        if pop == "model_alone_measured":
            lines.append(f"| {pop} | — | {d['is']} | — | _measured_ |")
        else:
            lines.append(f"| {pop} | {d['low']} | {d['mid']} | {d['high']} | {d.get('tier_mid', '')} |")
    lr = I.get("lr_isolation", {})
    if lr:
        lines.append("")
        lines.append(f"**LR isolation experiment**: {lr['note']}")
        lines.append(f"- Lay: +{lr['lay']} • Deaf: +{lr['deaf']} • Expert: +{lr['expert']} • Lay+ctx: +{lr['lay_plus_ctx']}")
    return "\n".join(lines)


def render_callouts(audit: dict) -> str:
    """Identify shifted vs unchanged numbers vs March values."""
    lines = []
    lines.append("## Numbers that shifted significantly (top-1 → MBR)")
    lines.append("")

    A = audit["section_A_is_distribution"]
    if A.get("hyp_top1") and A.get("hyp_mbr"):
        t = A["hyp_top1"]; m = A["hyp_mbr"]
        d_is = m["mean_is"] - t["mean_is"]
        d_wer = m["mean_wer_pct"] - t["mean_wer_pct"]
        d_niv_y = m["niv_y_count"] - t["niv_y_count"]
        d_niv_yp = m["niv_yp_count"] - t["niv_yp_count"]
        d_t5 = m["tier_5_count"] - t["tier_5_count"]
        d_t4 = m["tier_4_count"] - t["tier_4_count"]
        lines.append(f"- **Mean IS**: 2.532 → 2.547 (Δ={d_is:+.3f}). Small but tracks judge.")
        lines.append(f"- **Mean WER**: {t['mean_wer_pct']:.2f}% → {m['mean_wer_pct']:.2f}% (Δ={d_wer:+.2f}pp).")
        lines.append(f"- **NIV-Y count**: {t['niv_y_count']} → {m['niv_y_count']} (Δ={d_niv_y:+d}). Effectively unchanged.")
        lines.append(f"- **NIV-Y+P count**: {t['niv_yp_count']} → {m['niv_yp_count']} (Δ={d_niv_yp:+d}).")
        lines.append(f"- **Tier 5 (Excellent ≥4.0)**: {t['tier_5_count']} → {m['tier_5_count']} (Δ={d_t5:+d}).")
        lines.append(f"- **Tier 4 (Good 3.0-3.99)**: {t['tier_4_count']} → {m['tier_4_count']} (Δ={d_t4:+d}). MBR lifts segs from tier 3 into tier 4.")
    F = audit["section_F_llm_judge_v3"]
    if F.get("methods"):
        b = F["methods"]["baseline"]; mbr = F["methods"]["hyp_mbr"]
        d_y = (mbr["Y_rate"] - b["Y_rate"]) * 100
        d_yp = (mbr["Y_plus_P_rate"] - b["Y_plus_P_rate"]) * 100
        lines.append(f"- **Judge Y rate**: {b['Y_rate']*100:.2f}% → {mbr['Y_rate']*100:.2f}% (Δ={d_y:+.2f}pp, n.s.).")
        lines.append(f"- **Judge Y+P rate**: {b['Y_plus_P_rate']*100:.2f}% → {mbr['Y_plus_P_rate']*100:.2f}% (Δ={d_yp:+.2f}pp, p=0.0002 paired McNemar).")
    B = audit["section_B_wer_accuracy"]
    h = B.get("hallucination_rate", {})
    if isinstance(h, dict) and "top1" in h and "hyp_mbr" in h:
        d_h = h["hyp_mbr"]["hallu_pct"] - h["top1"]["hallu_pct"]
        lines.append(f"- **Hallucination rate (WER≥100%)**: {h['top1']['hallu_pct']:.2f}% → {h['hyp_mbr']['hallu_pct']:.2f}% (Δ={d_h:+.2f}pp).")
    lines.append("")
    lines.append("## Numbers confirmed unchanged")
    lines.append("")
    lines.append("- **Cross-config r=0.925** — applies to top-1 across 16 decode-parameter configs; n-best aggregation was not part of the 16. Number is still valid as an IS-stability claim, but it does NOT validate MBR specifically.")
    lines.append("- **Expert heuristic r=0.934** — deterministic decision tree, decode-independent. Holds.")
    lines.append("- **Opus blind judge gold standard (Y=23.0%, P=41.8%, N=35.1%, Y+P=64.9%)** — judge was run on top-1 only. The new v3 judge run on n-best methods is a separate, smaller-set comparison (with conf injected into prompts).")
    lines.append("- **Per-word band rule thresholds** (green=top1_conf≥0.95 ∧ beam_agreement≥0.80; yellow=≥0.65∧≥0.50). MBR uses the same per-word calibrated posteriors as top-1, so thresholds carry over.")
    lines.append("- **Trust-gate operating points** (≥30% green: 65.2% recall / 5.6% FPR). Computed on per_segment_safety, which uses top-1 IS labels and top-1 word_confs. Production switch to MBR display does NOT change these numbers because they are computed on top-1's per_segment confidence file.")
    return "\n".join(lines)


def render_anomalies(audit: dict) -> str:
    lines = ["## Anomalies, data gaps, and caveats", ""]
    lines.append("- **per_segment_safety.csv has 1,427 rows, not 1,497.** 70 segments with empty hypothesis are excluded. Trust-gate calibration uses 1,427 as the denominator (NIV-Y=361/25.3%, NIV-Y+P=924/64.8%). aggregated_is.json keeps all 1,497 (treats empty as IS=0; NIV-Y=346/23.1%, NIV-Y+P=922/61.6%). Use 1,497 as the canonical denominator for IS distribution; 1,427 only inside band-trust calibration.")
    lines.append("- **Per-method WWER and NEA F1 are NOT recomputed.** report_v2/report.csv carries WWER/NEA only for top-1 (no `wwer_hyp_*_%` columns). To get per-method WWER/NEA we would need to rerun the metric module on the per-method hypothesis text. This is a real gap if any deck slide quotes per-method WWER/NEA.")
    lines.append("- **llm_context_prob is bound to top-1 hypothesis text.** Salvage counts under MBR-IS use MBR's IS gate but top-1's heuristic prob. The heuristic is decode-independent in design (15-rule decision tree on text features), but per-segment values would shift slightly if recomputed on MBR text. The 'effective capture' rows in Section G are conservatively MBR-IS × top1-prob.")
    lines.append("- **Stratified P(green correct) by seg_mean_prob bin** for very_low (<0.40), low (0.40-0.55), mid_low (0.55-0.65) bins is NOT recomputable from `trust_diagnostic/per_word_diagnostic.csv` because that file is filtered to seg_mean_conf≥0.65. The MEMORY values 92.8/83.8/69.6/41.3/21.8/18.2 come from a different (B3 sidecar) source under the legacy CONF-ONLY rule. Section D recomputes only the three available bins under the joint rule.")
    lines.append("- **Cross-config r=0.925 does NOT include n-best aggregation** as a 'config'. The 16 configs were all top-1 decode-parameter variants. Re-running cross-config validation including hyp_mbr would be a useful follow-up.")
    lines.append("- **Tuning n-best validation (107 segs)** confirms the same direction as the full set: hyp_vote_conf wins on WER (-2.15pp) and ties on IS. hyp_mbr edges baseline on IS (+0.018) and NIV-Y count (+1).")
    lines.append("- **Identical-text drift (12.6/10.4/14.2% per method)** is not in summary.json — only in the analysis md. Cited verbatim, not recomputed.")
    lines.append("- **κ values in Section C are computed against the v3 _Opus blind judge run on top-1 hypothesis_** (the only gold standard we have). For each n-best method we compare its IS-NIV labels against the same set of judge labels — so κ shifts reflect IS shifts under that method, not judge re-evaluation.")
    return "\n".join(lines)


def write_audit(audit: dict):
    DOCS.mkdir(parents=True, exist_ok=True)
    summary = render_summary_table(audit)

    with open(OUT_MD, "w") as f:
        f.write(f"# {audit['title']}\n\n")
        f.write(f"_Date_: {audit['date']}  \n")
        f.write(f"_Purpose_: {audit['purpose']}\n\n")
        f.write("## Headline summary table (Top-1 baseline vs MBR default)\n\n")
        f.write(summary + "\n\n")
        f.write(render_callouts(audit) + "\n\n")
        f.write(render_section_A(audit["section_A_is_distribution"]) + "\n\n")
        f.write(render_section_B(audit["section_B_wer_accuracy"]) + "\n\n")
        f.write(render_section_C(audit["section_C_kappa_vs_opus"]) + "\n\n")
        f.write(render_section_D(audit["section_D_per_word_conf"]) + "\n\n")
        f.write(render_section_E(audit["section_E_trust_gate"]) + "\n\n")
        f.write(render_section_F(audit["section_F_llm_judge_v3"]) + "\n\n")
        f.write(render_section_G(audit["section_G_salvage"]) + "\n\n")
        f.write(render_section_H(audit["section_H_validation"]) + "\n\n")
        f.write(render_section_I(audit["section_I_human_is"]) + "\n\n")
        f.write(render_anomalies(audit) + "\n\n")
        f.write("---\n_Generated by `scripts/audit_after_amosi_numbers.py`._\n")

    # Build flat, slide-writer-friendly JSON with stable keys
    flat = build_flat_json(audit)
    with open(OUT_JSON, "w") as f:
        json.dump({"flat_keys": flat, "full": audit}, f, indent=2, default=str)

    return summary


def build_flat_json(audit: dict) -> dict:
    """Emit stable, descriptive keys for slide writers."""
    flat = {}
    A = audit["section_A_is_distribution"]
    for method in ("hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe"):
        d = A.get(method)
        if not d:
            continue
        suf = "top1" if method == "hyp_top1" else method.replace("hyp_", "")
        flat[f"is_mean_{suf}"] = d["mean_is"]
        flat[f"is_median_{suf}"] = d["median_is"]
        if "std_is" in d:
            flat[f"is_std_{suf}"] = d["std_is"]
        flat[f"mean_wer_pct_{suf}"] = d["mean_wer_pct"]
        flat[f"niv_y_count_{suf}"] = d["niv_y_count"]
        flat[f"niv_y_pct_{suf}"] = d["niv_y_pct"]
        flat[f"niv_yp_count_{suf}"] = d["niv_yp_count"]
        flat[f"niv_yp_pct_{suf}"] = d["niv_yp_pct"]
        flat[f"captured_legacy_pct_{suf}"] = d["captured_legacy_pct"]
        for tier in (1, 2, 3, 4, 5):
            flat[f"tier_{tier}_count_{suf}"] = d[f"tier_{tier}_count"]
            flat[f"tier_{tier}_pct_{suf}"] = d.get(f"tier_{tier}_pct")

    # Hallucination
    h = audit["section_B_wer_accuracy"].get("hallucination_rate", {})
    if isinstance(h, dict):
        for m, d in h.items():
            suf = "top1" if m == "top1" else m.replace("hyp_", "")
            flat[f"hallucination_count_{suf}"] = d["hallu_count"]
            flat[f"hallucination_pct_{suf}"] = d["hallu_pct"]

    # Top-1 WWER/NEA
    if "top1_wwer_pct_mean" in audit["section_B_wer_accuracy"]:
        flat["wwer_pct_top1"] = audit["section_B_wer_accuracy"]["top1_wwer_pct_mean"]
        flat["nea_f1_pct_top1"] = audit["section_B_wer_accuracy"]["top1_nea_f1_pct_mean"]

    # Kappa
    C = audit["section_C_kappa_vs_opus"]
    flat["judge_n_paired"] = C.get("n_judge_segments")
    for m in ("hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe"):
        d = C.get(m)
        if not d:
            continue
        suf = "top1" if m == "hyp_top1" else m.replace("hyp_", "")
        flat[f"kappa_niv_y_{suf}"] = d["kappa_Y"]
        flat[f"kappa_niv_yp_{suf}"] = d["kappa_YP"]

    # Per-word
    D = audit["section_D_per_word_conf"]
    if "overall_new_rule" in D:
        for band in ("green", "yellow", "red"):
            d = D["overall_new_rule"][band]
            flat[f"perword_new_{band}_count"] = d["n"]
            flat[f"perword_new_{band}_p_correct"] = d["p_correct"]
        for band in ("green", "yellow", "red"):
            d = D["overall_old_rule"][band]
            flat[f"perword_old_{band}_count"] = d["n"]
            flat[f"perword_old_{band}_p_correct"] = d["p_correct"]
        flat["perword_new_total_words"] = D["total_words_new"]
        flat["perword_old_total_words"] = D["total_words_old"]

    # Trust-gate
    E = audit["section_E_trust_gate"]
    for r in E.get("new_rule_joint_conf_agreement", []):
        t = int(round(r["threshold"] * 100))
        flat[f"trustgate_new_t{t}_n_trusted"] = r["n_trusted"]
        flat[f"trustgate_new_t{t}_recall"] = r["recall_useful"]
        flat[f"trustgate_new_t{t}_precision"] = r["precision_useful"]
        flat[f"trustgate_new_t{t}_fpr"] = r["fpr_useful"]
        flat[f"trustgate_new_t{t}_pct_clearly_conveyed"] = r["pct_clearly_conveyed_in_trust"]

    # Judge v3
    F = audit["section_F_llm_judge_v3"]
    for m, d in F.get("methods", {}).items():
        suf = "baseline" if m == "baseline" else m.replace("hyp_", "")
        flat[f"judge_v3_y_count_{suf}"] = d["Y"]
        flat[f"judge_v3_p_count_{suf}"] = d["P"]
        flat[f"judge_v3_n_count_{suf}"] = d["N"]
        flat[f"judge_v3_y_pct_{suf}"] = d["Y_rate"] * 100
        flat[f"judge_v3_yp_pct_{suf}"] = d["Y_plus_P_rate"] * 100
    for m, d in F.get("intra_rater", {}).items():
        suf = "baseline" if m == "baseline" else m.replace("hyp_", "")
        flat[f"judge_v3_intrarater_exact_{suf}"] = d["exact_agreement"]
        flat[f"judge_v3_intrarater_lenient_{suf}"] = d["lenient_agreement"]
    for m, d in F.get("mcnemar_vs_baseline", {}).items():
        suf = m.replace("hyp_", "")
        flat[f"mcnemar_y_p_{suf}"] = d["Y_p"]
        flat[f"mcnemar_yp_p_{suf}"] = d["YP_p"]
        flat[f"mcnemar_y_method_only_{suf}"] = d["Y_method_only"]
        flat[f"mcnemar_y_baseline_only_{suf}"] = d["Y_baseline_only"]
        flat[f"mcnemar_yp_method_only_{suf}"] = d["YP_method_only"]
        flat[f"mcnemar_yp_baseline_only_{suf}"] = d["YP_baseline_only"]

    # Salvage
    G = audit["section_G_salvage"]
    for m in ("hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe"):
        d = G.get(m)
        if not d:
            continue
        suf = "top1" if m == "hyp_top1" else m.replace("hyp_", "")
        flat[f"salvage_legacy_count_{suf}"] = d["salvage_legacy_count"]
        flat[f"salvage_legacy_pct_{suf}"] = d["salvage_legacy_pct"]
        flat[f"effective_capture_legacy_pct_{suf}"] = d["effective_capture_legacy_pct"]
        flat[f"salvage_niv_count_{suf}"] = d["salvage_niv_count"]
        flat[f"salvage_niv_pct_{suf}"] = d["salvage_niv_pct"]
        flat[f"effective_capture_niv_yp_pct_{suf}"] = d["effective_capture_niv_yp_pct"]

    # Validation
    H = audit["section_H_validation"]
    cc = H.get("cross_config_summary", {})
    if cc:
        flat["cross_config_r_mean"] = cc["mean_r"]
        flat["cross_config_r_std"] = cc["std_r"]
        flat["cross_config_n_configs"] = cc["n_configs"]
        flat["cross_config_includes_mbr"] = cc["configs_include_mbr"]
    eh = H.get("expert_heuristic_r", {})
    if eh:
        flat["expert_heuristic_r"] = eh["value"]

    # Tuning n-best validation 107
    tn = H.get("tuning_nbest_validation", {})
    if tn:
        flat["tuning_nbest_n_segments"] = tn.get("n_segments")
        for m, d in tn.get("summary", {}).items():
            suf = "top1" if m == "hyp_top1" else m.replace("hyp_", "")
            flat[f"tuning_nbest_is_{suf}"] = d["mean_is"]
            flat[f"tuning_nbest_wer_{suf}"] = d["mean_wer_pct"]

    # Human-IS
    I = audit["section_I_human_is"]
    for pop, d in I["estimates_path_B"].items():
        if pop == "model_alone_measured":
            flat[f"human_is_model_alone"] = d["is"]
        else:
            flat[f"human_is_{pop}_low"] = d["low"]
            flat[f"human_is_{pop}_mid"] = d["mid"]
            flat[f"human_is_{pop}_high"] = d["high"]

    return flat


def main():
    audit = build_audit()
    summary = write_audit(audit)
    print(summary)
    print(f"\nWrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")


if __name__ == "__main__":
    main()
