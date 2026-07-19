#!/usr/bin/env python3
"""Fable-vs-Opus judge comparison on the 1497-sample (300 judged flags).

Reuses egla_kafe_substitution_eval.py primitives (no reimplementation):
  1. agreement stats Fable vs Opus (cells, kappa, verdict agreement) + Opus vs Llama
  2. builds arms: opus_only (any), fable_opus_agree (all) via the real apply gates
  3. scores both arms fixed/broke/neutral + dWER + dRecall (+dIS if scorer loads)
  4. dumps eval_arms/fable_opus_analysis.json and prints a side-by-side table
     against the on-disk claude_only / ship_agree rows from eval_results.json.
"""
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "subeval", "/home/ubuntu/scripts/pipeline/egla_kafe_substitution_eval.py")
subeval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subeval)

ROOT = Path("/home/ubuntu/english_full_nbest_eval/substitution")
JUDGE = ROOT / "judge"
ARMS = ROOT / "eval_arms"
CFG = subeval.DATASETS["english_1497"]

F_FABLE = JUDGE / "decisions_claude.json"
F_OPUS = JUDGE / "decisions_claude_opus.json"
F_LLAMA = JUDGE / "decisions_llama.json"

if not F_OPUS.exists():
    sys.exit(f"[abort] {F_OPUS} not written yet — Opus agent still running")


def dec_map(path):
    d = json.load(open(path))
    return {(x["utt_id"], x["pos"]): x for x in d["decisions"]}


def agreement(a_map, b_map, a_name, b_name):
    joint = sorted(set(a_map) & set(b_map))
    cells = Counter()
    verdict_agree = 0
    disagreements = []
    for k in joint:
        a, b = a_map[k], b_map[k]
        if a["verdict"] == b["verdict"]:
            verdict_agree += 1
        ar, br = a["decision"] == "replace", b["decision"] == "replace"
        if ar and br:
            cells["both_replace_same" if a["chosen"] == b["chosen"]
                  else "both_replace_diff"] += 1
        elif ar:
            cells[f"{a_name}_replace_{b_name}_keep"] += 1
        elif br:
            cells[f"{b_name}_replace_{a_name}_keep"] += 1
        else:
            cells["both_keep"] += 1
        if ar != br or (ar and br and a["chosen"] != b["chosen"]):
            disagreements.append({
                "utt_id": k[0], "pos": k[1],
                a_name: [a["decision"], a.get("chosen", ""), a["verdict"]],
                b_name: [b["decision"], b.get("chosen", ""), b["verdict"]],
            })
    n = len(joint)
    a_rep = sum(1 for k in joint if a_map[k]["decision"] == "replace")
    b_rep = sum(1 for k in joint if b_map[k]["decision"] == "replace")
    po = (cells["both_replace_same"] + cells["both_replace_diff"]
          + cells["both_keep"]) / n if n else 0.0
    pe = ((a_rep / n) * (b_rep / n)
          + ((n - a_rep) / n) * ((n - b_rep) / n)) if n else 0.0
    kappa = (po - pe) / (1 - pe) if (1 - pe) > 1e-9 else None
    return {"pair": f"{a_name}_vs_{b_name}", "n_joint_keys": n,
            "cells": dict(cells),
            f"{a_name}_replace": a_rep, f"{b_name}_replace": b_rep,
            "raw_agreement": round(po, 4),
            "cohens_kappa": round(kappa, 4) if kappa is not None else None,
            "verdict_agreement": round(verdict_agree / n, 4) if n else None,
            "disagreements": disagreements}


fable, opus, llama = dec_map(F_FABLE), dec_map(F_OPUS), dec_map(F_LLAMA)
print(f"[load] fable={len(fable)} opus={len(opus)} llama={len(llama)} keys")

ag_fo = agreement(fable, opus, "fable", "opus")
ag_ol = agreement(opus, llama, "opus", "llama")

# arms through the real apply gates
ARMS.mkdir(exist_ok=True)
p_opus_only = ARMS / "substitutions_opus_only.json"
p_fable_opus = ARMS / "substitutions_fable_opus.json"
subeval.run_apply(ROOT / "candidates.json", [F_OPUS], "any", p_opus_only)
subeval.run_apply(ROOT / "candidates.json", [F_FABLE, F_OPUS], "all", p_fable_opus)

# scoring context (mirrors eval_dataset)
import spacy
from compute_word_confidence import is_numeric
nlp = spacy.load("en_core_web_sm")
refs = subeval.load_refs(CFG["refs"])
cands = subeval.load_candidates(CFG["root"])
orig_texts = {u: (cands["segments"][u]["display_text"]
                  if u in cands["segments"] else "") for u in refs}
base_wer = {u: subeval.seg_wer(refs[u], orig_texts[u]) for u in refs}
base_recall = {u: subeval.content_recall(refs[u], orig_texts[u]) for u in refs}

niv = {}
import csv as _csv
with open(CFG["report_csv"], encoding="utf-8") as f:
    for row in _csv.DictReader(f):
        try:
            s = float(row.get("is_score") or 0.0)
        except ValueError:
            continue
        niv[row["utt_id"]] = "Y" if s >= 3.80 else ("P" if s >= 2.00 else "N")
bands = {}
for u, seg in cands["segments"].items():
    p = seg.get("mean_word_prob")
    if p is not None:
        bands[u] = ("high>=0.85" if p >= 0.85 else "0.75-0.85" if p >= 0.75
                    else "0.65-0.75" if p >= 0.65 else "low<0.65")

try:
    is_scorer = subeval.ISScorer()
except Exception as e:  # noqa: BLE001
    print(f"[warn] ISScorer unavailable ({e}); dIS skipped")
    is_scorer = None

results = {}
for arm, path in (("opus_only", p_opus_only), ("fable_opus_agree", p_fable_opus)):
    touched = subeval.load_arm_subs(path)
    results[arm] = subeval.score_arm(arm, refs, orig_texts, touched, base_wer,
                                     base_recall, niv, bands, is_scorer, nlp,
                                     is_numeric)

out = {"agreement_fable_opus": ag_fo, "agreement_opus_llama": ag_ol,
       "arms": results}
with open(ARMS / "fable_opus_analysis.json", "w") as f:
    json.dump(out, f, indent=1)

# side-by-side vs on-disk rows
prior = json.load(open(ROOT / "eval_results.json"))["arms"]
print("\n=== Fable vs Opus (300 joint keys) ===")
for k, v in ag_fo.items():
    if k != "disagreements":
        print(f"  {k}: {v}")
print(f"  disagreements: {len(ag_fo['disagreements'])}")
for d in ag_fo["disagreements"]:
    print(f"    {d}")
print("\n=== Opus vs Llama ===")
for k, v in ag_ol.items():
    if k != "disagreements":
        print(f"  {k}: {v}")

print("\n=== arms (1497 sample-only engines) ===")
hdr = f"{'arm':18s} {'subs':>4s} {'fixed':>5s} {'broke':>5s} {'neut':>4s} {'dWER pp':>8s} {'dRec pp':>8s} {'n/e':>4s}"
print(hdr)
rows = [("claude_only(fable)", prior["claude_only"]),
        ("ship(fable&llama)", prior["ship_agree"]),
        ("opus_only", results["opus_only"]),
        ("fable_opus_agree", results["fable_opus_agree"])]
for name, r in rows:
    print(f"{name:18s} {r['n_subs']:4d} {r['fixed']:5d} {r['broke']:5d} "
          f"{r['neutral_both_wrong']:4d} {r['dwer_overall_pp']:+8.3f} "
          f"{r['drecall_overall_pp']:+8.3f} "
          f"{r['numeric_introductions']}/{r['entity_introductions']}")
print("\n[done] full JSON -> eval_arms/fable_opus_analysis.json")
