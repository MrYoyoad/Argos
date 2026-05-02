#!/usr/bin/env python3
"""
Prepare blind LLM-as-a-Judge batches for n-best aggregation evaluation.

Forks docs/_research-tools/generators/prepare_llm_eval_batches.py to:
- Read english_full_nbest_eval/report/report.csv (baseline + 3 n-best methods)
- Join sentence_confidence from segment_features.csv (baseline's per-segment conf)
- Inject a `conf` column into the batch format (NNN|ref|hyp|conf)
- Emit 4 method-specific batch sets (baseline, hyp_mbr, hyp_vote_score, hyp_vote_conf)

Methods judged:
- baseline           -> hyp = report.csv `hyp`,             conf = segment_features.csv `sentence_confidence`
- hyp_mbr            -> hyp = report.csv `hyp_mbr`,         conf = report.csv `hyp_mbr_mean_conf_calib`
- hyp_vote_score     -> hyp = report.csv `hyp_vote_score`,  conf = report.csv `hyp_vote_score_mean_conf_calib`
- hyp_vote_conf      -> hyp = report.csv `hyp_vote_conf`,   conf = report.csv `hyp_vote_conf_mean_conf_calib`

Output:
- docs/evaluation/llm_judge_nbest/batches/batch_<method>_NN.txt   (15 per method, 60 total)
- docs/evaluation/llm_judge_nbest/batch_index.json
- docs/evaluation/llm_judge_nbest/auto_judgments.csv

Usage:
    python3 prepare_nbest_judge_batches.py
"""

import csv
import json
import os
import random
import sys

# ---------- Configuration ----------
SEED = 42
BATCH_SIZE = 100
N_DUPLICATES_PER_METHOD = 30  # 6 per IS tier x 5 tiers (matches prior protocol)
MIN_HYP_WORDS_FOR_SHORT = 3   # auto-N if hyp has fewer words AND ref > 5 words

REPORT_CSV = "/home/ubuntu/english_full_nbest_eval/report/report.csv"
FEATURES_CSV = "/home/ubuntu/english_full_nbest_eval/conditional_analysis/segment_features.csv"
OUTPUT_DIR = "/home/ubuntu/docs/evaluation/llm_judge_nbest"
BATCHES_DIR = os.path.join(OUTPUT_DIR, "batches")

METHODS = [
    # (label, hyp_column_in_report,    conf_source,   conf_column)
    ("baseline",       "hyp",            "features",  "sentence_confidence"),
    ("hyp_mbr",        "hyp_mbr",        "report",    "hyp_mbr_mean_conf_calib"),
    ("hyp_vote_score", "hyp_vote_score", "report",    "hyp_vote_score_mean_conf_calib"),
    ("hyp_vote_conf",  "hyp_vote_conf",  "report",    "hyp_vote_conf_mean_conf_calib"),
]


# ---------- Loaders ----------
def load_csv(path):
    with open(path, "r") as f:
        return list(csv.DictReader(f))


def join_data(report_rows, features_rows):
    """Join report.csv with segment_features.csv by utt_id. Returns dict utt_id -> merged row."""
    feat_by_id = {r["utt_id"]: r for r in features_rows}
    merged = {}
    missing = 0
    for r in report_rows:
        uid = r["utt_id"]
        if uid not in feat_by_id:
            missing += 1
            continue
        m = dict(r)
        m["sentence_confidence"] = feat_by_id[uid].get("sentence_confidence", "")
        merged[uid] = m
    if missing:
        print(f"  WARN: {missing} utt_ids in report.csv not found in segment_features.csv")
    return merged


# ---------- Per-method extraction ----------
def fmt_conf(conf_str):
    """Format a confidence value to 2 decimals; return 'n/a' if empty/non-numeric."""
    if conf_str is None or conf_str == "":
        return "n/a"
    try:
        return f"{float(conf_str):.2f}"
    except ValueError:
        return "n/a"


def extract_method_rows(merged, method_label, hyp_col, conf_source, conf_col):
    """
    For one method, build a list of dicts: utt_id, ref, hyp, conf, is_tier.
    is_tier preserved for tier-stratified duplicate selection.
    """
    out = []
    for uid, row in merged.items():
        ref = row.get("ref", "").strip()
        hyp = row.get(hyp_col, "").strip()
        if conf_source == "features":
            conf_raw = row.get("sentence_confidence", "")
        else:
            conf_raw = row.get(conf_col, "")
        conf = fmt_conf(conf_raw)
        is_tier = row.get("is_tier", "0")
        out.append({
            "utt_id": uid,
            "ref": ref,
            "hyp": hyp,
            "conf": conf,
            "is_tier": is_tier,
        })
    return out


# ---------- Auto-classify ----------
def auto_classify(method_rows):
    """Auto-N empty or trivially-short hypotheses. Returns (auto_n, remaining)."""
    auto_n, remaining = [], []
    for r in method_rows:
        ref_words = len(r["ref"].split()) if r["ref"] else 0
        hyp_words = len(r["hyp"].split()) if r["hyp"] else 0
        if not r["hyp"] or hyp_words == 0:
            auto_n.append((r["utt_id"], "empty_hypothesis"))
        elif hyp_words < MIN_HYP_WORDS_FOR_SHORT and ref_words > 5:
            auto_n.append((r["utt_id"], "trivially_short"))
        else:
            remaining.append(r)
    return auto_n, remaining


# ---------- Duplicate selection ----------
def select_duplicates(rows, n_per_tier=6, seed_offset=1):
    """Select n_per_tier from each IS tier (1-5) for intra-rater reliability."""
    by_tier = {str(t): [] for t in range(1, 6)}
    for r in rows:
        if r["is_tier"] in by_tier:
            by_tier[r["is_tier"]].append(r)

    rng = random.Random(SEED + seed_offset)
    duplicates = []
    for tier in sorted(by_tier.keys()):
        pool = by_tier[tier]
        n = min(n_per_tier, len(pool))
        if n:
            duplicates.extend(rng.sample(pool, n))
    return duplicates


# ---------- Batch creation ----------
def create_batches(rows, duplicates, batch_size, seed_offset_main=0, seed_offset_dup=2):
    """Shuffle rows, split into batches, then insert duplicates into different batches."""
    rng = random.Random(SEED + seed_offset_main)
    items = [(r["utt_id"], r["ref"], r["hyp"], r["conf"], False) for r in rows]
    rng.shuffle(items)

    batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

    rng2 = random.Random(SEED + seed_offset_dup)
    for d in duplicates:
        dup = (d["utt_id"], d["ref"], d["hyp"], d["conf"], True)
        # find original batch
        orig_idx = None
        for bi, b in enumerate(batches):
            if any(it[0] == dup[0] for it in b):
                orig_idx = bi
                break
        candidates = [i for i in range(len(batches)) if i != orig_idx]
        if candidates:
            target = rng2.choice(candidates)
            pos = rng2.randint(0, len(batches[target]))
            batches[target].insert(pos, dup)

    return batches


# ---------- Writers ----------
HEADER_LINE = (
    "{label} | BATCH {n:02d}/{total:02d} | {pairs} pairs | format: NNN|ref|hyp|conf "
    "| Y=meaning conveyed, P=partial (annotate: P:preserved/-lost), N=meaning lost "
    "| `conf` is the method's own sentence-level confidence in [0,1] (n/a if missing) — "
    "use as a soft cue, NOT as a verdict shortcut"
)


def write_batch_files(method_label, batches, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    n = len(batches)
    for bi, batch in enumerate(batches):
        bn = bi + 1
        path = os.path.join(out_dir, f"batch_{method_label}_{bn:02d}.txt")
        with open(path, "w") as f:
            f.write(HEADER_LINE.format(label=method_label.upper(), n=bn, total=n, pairs=len(batch)) + "\n")
            f.write("---\n")
            for idx, (uid, ref, hyp, conf, _is_dup) in enumerate(batch):
                # Sanitize: replace pipe in ref/hyp to avoid breaking the format
                ref_s = ref.replace("|", "/")
                hyp_s = hyp.replace("|", "/")
                f.write(f"{idx + 1:03d}|{ref_s}|{hyp_s}|{conf}\n")


def write_batch_index(all_method_batches, out_dir):
    """all_method_batches: dict method_label -> list of batches."""
    index = {}
    for method, batches in all_method_batches.items():
        for bi, batch in enumerate(batches):
            key = f"batch_{method}_{bi+1:02d}"
            index[key] = []
            for idx, (uid, ref, hyp, conf, is_dup) in enumerate(batch):
                index[key].append({
                    "index": idx + 1,
                    "utt_id": uid,
                    "method": method,
                    "is_duplicate": is_dup,
                })
    path = os.path.join(out_dir, "batch_index.json")
    with open(path, "w") as f:
        json.dump(index, f, indent=2)
    return path


def write_auto_judgments(all_auto, out_dir):
    """all_auto: list of (utt_id, method, reason)."""
    path = os.path.join(out_dir, "auto_judgments.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["utt_id", "method", "judgment", "reason"])
        for uid, method, reason in all_auto:
            w.writerow([uid, method, "N", reason])
    return path


# ---------- Main ----------
def main():
    print("=" * 64)
    print("LLM-as-a-Judge Batch Prep — n-best aggregation (4 methods)")
    print("=" * 64)

    print(f"\nLoading {REPORT_CSV} ...")
    report_rows = load_csv(REPORT_CSV)
    print(f"  Loaded {len(report_rows)} rows")

    print(f"Loading {FEATURES_CSV} ...")
    features_rows = load_csv(FEATURES_CSV)
    print(f"  Loaded {len(features_rows)} rows")

    merged = join_data(report_rows, features_rows)
    print(f"\nJoined: {len(merged)} segments with both report + features data")

    if not merged:
        print("ERROR: no rows after join", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_method_batches = {}
    all_auto = []

    for label, hyp_col, conf_source, conf_col in METHODS:
        print(f"\n--- Method: {label} ---")
        rows = extract_method_rows(merged, label, hyp_col, conf_source, conf_col)
        auto_n, remaining = auto_classify(rows)
        print(f"  Auto-N: {len(auto_n)} (empty/trivially short)")
        print(f"  Remaining for judgment: {len(remaining)}")

        duplicates = select_duplicates(remaining, n_per_tier=6)
        print(f"  Duplicates: {len(duplicates)} (across IS tiers)")

        batches = create_batches(remaining, duplicates, BATCH_SIZE)
        total_items = sum(len(b) for b in batches)
        print(f"  Batches: {len(batches)} | total items: {total_items}")

        write_batch_files(label, batches, BATCHES_DIR)
        all_method_batches[label] = batches
        all_auto.extend((uid, label, reason) for uid, reason in auto_n)

    print(f"\nWriting batch index ...")
    idx_path = write_batch_index(all_method_batches, OUTPUT_DIR)
    print(f"  {idx_path}")

    print(f"\nWriting auto-judgments ...")
    auto_path = write_auto_judgments(all_auto, OUTPUT_DIR)
    print(f"  {auto_path} ({len(all_auto)} auto-N entries)")

    # Summary
    print("\n" + "=" * 64)
    print("SUMMARY")
    print("=" * 64)
    total_batches = sum(len(b) for b in all_method_batches.values())
    total_items = sum(len(batch) for b in all_method_batches.values() for batch in b)
    print(f"  Methods:         {len(METHODS)}")
    print(f"  Total batches:   {total_batches}")
    print(f"  Total items:     {total_items}  (incl. ~{N_DUPLICATES_PER_METHOD * len(METHODS)} duplicates)")
    print(f"  Auto-N rows:     {len(all_auto)}")
    print(f"  Output dir:      {OUTPUT_DIR}")
    print(f"\nNext: spawn fresh Opus 4.6 conversations to read each batch and write")
    print(f"  {OUTPUT_DIR}/judgments/batch_<method>_NN_judgments.txt with `NNN,JUDGMENT` lines.")


if __name__ == "__main__":
    main()
