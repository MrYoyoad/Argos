#!/usr/bin/env python3
"""Phase 6: grouped statistical evaluation of Egla-Kafe decode results.

Joins a make_report.py report.csv with provenance.json and reports per-group means (with 95%
CI), NIV-Y / NIV-Y+P rates, and counts, grouped by: scene, character, side, camera angle,
speaker-pair, and arm (stacked-stream vs plain-crop). Compares each group to the English
baseline (WER 64.1 / IS 2.53). Paired McNemar (stream vs crop) when both arms share segments.

stdlib csv + numpy/scipy only (no pandas). Tolerant to which metric columns are present.
See work/eval/INTERFACES.md §7.
"""
import argparse
import csv
import json
import math
import os
from html import escape

import numpy as np

BASELINE = {"wer_%": 64.1, "is_score": 2.53}
NIV_Y, NIV_YP = 3.80, 2.00
METRICS = ["wer_%", "wwer_%", "nea_f1_%", "is_score", "sentence_confidence"]


def ci95(vals):
    vals = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not vals:
        return (None, None, None, 0)
    a = np.array(vals, dtype=float)
    m = float(a.mean())
    if len(a) < 2:
        return (m, m, m, len(a))
    se = a.std(ddof=1) / math.sqrt(len(a))
    try:
        from scipy import stats
        t = stats.t.ppf(0.975, len(a) - 1)
    except Exception:
        t = 1.96
    return (m, m - t * se, m + t * se, len(a))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load(report_csv, provenance):
    prov = json.load(open(provenance, encoding="utf-8")) if provenance and os.path.exists(provenance) else {}
    rows = []
    with open(report_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            uid = r.get("utt_id") or r.get("id") or r.get("display_name")
            p = prov.get(uid, {})
            row = {"utt_id": uid, **{k: fnum(r.get(k)) for k in METRICS if k in r}}
            row["is_score"] = fnum(r.get("is_score"))
            row.update({"scene": p.get("scene"), "char": p.get("char"), "side": p.get("side"),
                        "person": p.get("person") or "?",
                        "angle": p.get("angle"), "arm": p.get("arm", "?"),
                        "speakers": "+".join(sorted(p.get("speakers_in_name", []))) or "?",
                        "align_conf": p.get("align_conf")})
            rows.append(row)
    return rows


def group_stats(rows, dim):
    groups = {}
    for r in rows:
        groups.setdefault(r.get(dim), []).append(r)
    out = []
    for gv, items in sorted(groups.items(), key=lambda kv: str(kv[0])):
        rec = {"dim": dim, "value": gv, "n": len(items)}
        for mt in METRICS:
            vals = [r[mt] for r in items if r.get(mt) is not None]
            m, lo, hi, k = ci95(vals)
            rec[mt] = m; rec[mt + "_lo"] = lo; rec[mt + "_hi"] = hi; rec[mt + "_n"] = k
        iss = [r["is_score"] for r in items if r.get("is_score") is not None]
        rec["niv_y_%"] = round(100 * sum(1 for v in iss if v >= NIV_Y) / len(iss), 1) if iss else None
        rec["niv_yp_%"] = round(100 * sum(1 for v in iss if v >= NIV_YP) / len(iss), 1) if iss else None
        out.append(rec)
    return out


def mcnemar_stream_vs_crop(rows):
    """Paired NIV-Y+P: match stream vs crop segments by (scene, stem-line position). Best-effort:
    pair by utt_id base if both arms decoded the same seg ids; else by (scene, char, ref turn)."""
    by_arm = {}
    for r in rows:
        by_arm.setdefault(r["arm"], {})[r["utt_id"]] = r
    if "stream" not in by_arm or "crop" not in by_arm:
        return None
    common = set(by_arm["stream"]) & set(by_arm["crop"])
    b = c = 0
    for u in common:
        s = by_arm["stream"][u]["is_score"]; cr = by_arm["crop"][u]["is_score"]
        if s is None or cr is None:
            continue
        sy = s >= NIV_YP; cy = cr >= NIV_YP
        if sy and not cy:
            b += 1
        elif cy and not sy:
            c += 1
    if b + c == 0:
        return {"n_pairs": len(common), "stream_wins": b, "crop_wins": c, "p": 1.0}
    try:
        from scipy.stats import binomtest
        p = binomtest(b, b + c, 0.5).pvalue
    except Exception:
        p = None
    return {"n_pairs": len(common), "stream_wins": b, "crop_wins": c, "p": p}


def html_report(all_groups, overall, mcnemar, out_path):
    def cell_is(v):
        if v is None:
            return "<td>-</td>"
        col = "#d6f5d6" if v >= 3.8 else ("#fff3cd" if v >= 2.0 else "#f8d7da")
        return f"<td style='background:{col}'>{v:.2f}</td>"
    sec = []
    for dim, groups in all_groups.items():
        rows_html = []
        for g in groups:
            wer = g.get("wer_%"); is_ = g.get("is_score")
            rows_html.append(
                f"<tr><td>{escape(str(g['value']))}</td><td>{g['n']}</td>"
                f"<td>{wer:.1f}</td>" if wer is not None else f"<tr><td>{escape(str(g['value']))}</td><td>{g['n']}</td><td>-</td>")
            rows_html[-1] += (cell_is(is_) +
                f"<td>{g.get('niv_y_%')}</td><td>{g.get('niv_yp_%')}</td></tr>")
        sec.append(f"<h3>by {dim}</h3><table><tr><th>{dim}</th><th>n</th><th>WER%</th>"
                   f"<th>IS</th><th>NIV-Y%</th><th>NIV-Y+P%</th></tr>{''.join(rows_html)}</table>")
    mc = ""
    if mcnemar:
        mc = (f"<h3>Stream vs Crop (paired McNemar, NIV-Y+P)</h3>"
              f"<p>{mcnemar['n_pairs']} pairs · stream_wins={mcnemar['stream_wins']} · "
              f"crop_wins={mcnemar['crop_wins']} · p={mcnemar.get('p')}</p>")
    ov = overall
    html = f"""<!doctype html><meta charset=utf-8><title>Egla-Kafe evaluation</title>
<style>body{{font:14px system-ui;margin:24px;max-width:1000px}}table{{border-collapse:collapse;margin:8px 0}}
td,th{{border:1px solid #ccc;padding:5px 9px}}th{{background:#eee}}h3{{margin-top:22px}}</style>
<h2>Egla-Kafe — model evaluation</h2>
<p><b>Overall</b>: n={ov['n']} · WER {ov.get('wer_%') and round(ov['wer_%'],1)}% (baseline 64.1) ·
IS {ov.get('is_score') and round(ov['is_score'],3)} (baseline 2.53) ·
NIV-Y {ov.get('niv_y_%')}% · NIV-Y+P {ov.get('niv_yp_%')}% ·
mean align_conf {ov.get('align_conf') and round(ov['align_conf'],3)}</p>
{mc}{''.join(sec)}"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--provenance", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    rows = load(args.report, args.provenance)
    os.makedirs(args.out_dir, exist_ok=True)

    dims = ["arm", "scene", "person", "char", "side", "angle", "speakers"]
    all_groups = {d: group_stats(rows, d) for d in dims}
    overall = group_stats(rows, "_all")  # everything in one group
    for r in rows:
        r["_all"] = "all"
    overall = group_stats(rows, "_all")[0]
    overall["align_conf"] = (np.mean([r["align_conf"] for r in rows if r.get("align_conf") is not None])
                             if any(r.get("align_conf") is not None for r in rows) else None)
    mc = mcnemar_stream_vs_crop(rows)

    # tidy long-form CSV
    with open(os.path.join(args.out_dir, "egla_kafe_report.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dim", "value", "n", "metric", "mean", "ci_lo", "ci_hi", "metric_n"])
        for d, groups in all_groups.items():
            for g in groups:
                for mt in METRICS:
                    if g.get(mt) is not None:
                        w.writerow([d, g["value"], g["n"], mt, round(g[mt], 4),
                                    round(g[mt + "_lo"], 4) if g[mt + "_lo"] is not None else "",
                                    round(g[mt + "_hi"], 4) if g[mt + "_hi"] is not None else "",
                                    g[mt + "_n"]])
                w.writerow([d, g["value"], g["n"], "niv_y_%", g.get("niv_y_%"), "", "", ""])
                w.writerow([d, g["value"], g["n"], "niv_yp_%", g.get("niv_yp_%"), "", "", ""])
    html_report(all_groups, overall, mc, os.path.join(args.out_dir, "egla_kafe_report.html"))
    print(f"[stats] {len(rows)} segments; overall WER={overall.get('wer_%')}, IS={overall.get('is_score')}, "
          f"NIV-Y+P={overall.get('niv_yp_%')}%; McNemar={mc}")
    print(f"[stats] -> {args.out_dir}/egla_kafe_report.{{csv,html}}")


if __name__ == "__main__":
    main()
