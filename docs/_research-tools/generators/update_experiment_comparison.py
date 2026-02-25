#!/usr/bin/env python3
"""Regenerate experiment-comparison.csv with all 13 experiments (A-M)."""
import csv
import os
from pathlib import Path
from collections import OrderedDict

BASE = Path("/home/ubuntu/tuning_results")
OUT = Path("/home/ubuntu/docs/tuning/experiment-comparison.csv")

EXPERIMENTS = OrderedDict([
    ("exp_A_baseline",          ("A", "")),
    ("exp_B_no_rep_pen",        ("B", "generation.repetition_penalty=1.0")),
    ("exp_C_lenpen_pos1",       ("C", "generation.lenpen=1.0")),
    ("exp_D_lenpen_neg05",      ("D", "generation.lenpen=-0.5")),
    ("exp_E_sampling_low_temp", ("E", "generation.do_sample=true generation.temperature=0.5 generation.top_p=0.9")),
    ("exp_F_sampling_original", ("F", "generation.do_sample=true generation.temperature=1.0 generation.top_p=0.9")),
    ("exp_G_greedy",            ("G", "generation.beam=1")),
    ("exp_H_lenpen_pos2",       ("H", "generation.lenpen=2.0")),
    ("exp_I_lenpen1_sample",    ("I", "generation.lenpen=1.0 generation.do_sample=true generation.temperature=1.0")),
    ("exp_J_lenpen1_temp05",    ("J", "generation.lenpen=1.0 generation.do_sample=true generation.temperature=0.5")),
    ("exp_K_sampling_temp15",   ("K", "generation.do_sample=true generation.temperature=1.5 generation.top_p=0.9")),
    ("exp_L_sampling_temp03",   ("L", "generation.do_sample=true generation.temperature=0.3 generation.top_p=0.9")),
    ("exp_M_lenpen1_temp03",    ("M", "generation.lenpen=1.0 generation.do_sample=true generation.temperature=0.3")),
])

rows = []
for exp_dir, (label, overrides) in EXPERIMENTS.items():
    csv_path = BASE / exp_dir / "report" / "report.csv"
    if not csv_path.exists():
        print(f"  SKIP {exp_dir} (no report.csv)")
        continue
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        data = list(reader)
    n = len(data)
    empty = sum(1 for r in data if r.get("hyp", "").strip() == "")
    empty_pct = round(100 * empty / n, 1) if n else 0
    wwers = [float(r["wwer_%"]) for r in data]
    nea_rs = [float(r["nea_recall_%"]) for r in data]
    nea_f1s = [float(r["nea_f1_%"]) for r in data]
    wers = [float(r["wer_%"]) for r in data]
    mean_wwer = round(sum(wwers) / len(wwers), 1)
    med_wwer = round(sorted(wwers)[len(wwers) // 2], 1)
    mean_nea_r = round(sum(nea_rs) / len(nea_rs), 1)
    mean_nea_f1 = round(sum(nea_f1s) / len(nea_f1s), 1)
    mean_wer = round(sum(wers) / len(wers), 1)
    med_wer = round(sorted(wers)[len(wers) // 2], 1)
    rows.append({
        "exp": exp_dir, "label": label, "overrides": overrides,
        "n": n, "empty": empty, "empty_pct": empty_pct,
        "mean_wer": mean_wer, "med_wer": med_wer,
        "mean_wwer": mean_wwer, "med_wwer": med_wwer,
        "mean_nea_r": mean_nea_r, "mean_nea_f1": mean_nea_f1
    })

fields = ["exp", "label", "overrides", "n", "empty", "empty_pct",
          "mean_wer", "med_wer", "mean_wwer", "med_wwer", "mean_nea_r", "mean_nea_f1"]
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print(f"Written {len(rows)} experiments to {OUT}")
for r in rows:
    print(f"  {r['label']:2s}: WWER={r['mean_wwer']:5.1f}  med={r['med_wwer']:5.1f}  "
          f"empty={r['empty_pct']:4.1f}%  NEA_F1={r['mean_nea_f1']:4.1f}")
