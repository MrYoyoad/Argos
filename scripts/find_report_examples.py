#!/usr/bin/env python3
"""Find compelling positive examples from intelligibility_scores.csv for report use."""

import csv

CSV_PATH = "/home/ubuntu/docs/evaluation/intelligibility/intelligibility_scores.csv"


def load_data():
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            for k in ["wer_%", "wwer_%", "nea_f1_%", "semantic_sim", "phonetic_sim",
                       "length_ratio", "intelligibility_score", "llm_context_prob"]:
                try:
                    r[k] = float(r[k])
                except (ValueError, KeyError):
                    r[k] = None
            r["context_recoverable"] = r.get("context_recoverable", "").strip().lower() == "true"
            rows.append(r)
    return rows


def print_example(i, r):
    print(f"\n  --- Example {i} ---")
    print(f"  utt_id:              {r['utt_id']}")
    print(f"  display_name:        {r['display_name']}")
    print(f"  REF: {r['ref']}")
    print(f"  HYP: {r['hyp']}")
    print(f"  WER:  {r['wer_%']:.1f}%   WWER: {r['wwer_%']:.1f}%")
    print(f"  Semantic Sim:        {r['semantic_sim']:.4f}")
    print(f"  Phonetic Sim:        {r['phonetic_sim']:.4f}")
    print(f"  NEA F1:              {r['nea_f1_%']:.1f}%")
    print(f"  Length Ratio:        {r['length_ratio']:.3f}")
    print(f"  IS:                  {r['intelligibility_score']:.3f}  ({r['intelligibility_label']})")
    print(f"  context_recoverable: {r['context_recoverable']}")
    print(f"  context_reason:      {r['context_reason']}")
    print(f"  llm_context_prob:    {r['llm_context_prob']:.3f}")
    print(f"  llm_context_reason:  {r['llm_context_reason']}")
    print()


def interest_score_llm(r):
    sem = r["semantic_sim"] or 0
    phon = r["phonetic_sim"] or 0
    llm_p = r["llm_context_prob"] or 0
    wer = r["wer_%"] or 0
    ref_words = len(r["ref"].split())
    return (sem * 3.0) + (phon * 1.5) + (llm_p * 1.0) + (min(wer, 100) / 100 * 1.0) + (min(ref_words, 20) / 20 * 1.0)


def interest_score_rule(r):
    sem = r["semantic_sim"] or 0
    phon = r["phonetic_sim"] or 0
    wer = r["wer_%"] or 0
    IS = r["intelligibility_score"] or 0
    ref_words = len(r["ref"].split())
    return (sem * 3.0) + (phon * 1.5) + (IS * 0.5) + (min(wer, 100) / 100 * 1.0) + (min(ref_words, 20) / 20 * 1.0)


def main():
    rows = load_data()
    print(f"Loaded {len(rows)} rows from CSV.\n")

    # =========================================================================
    # CATEGORY A: LLM-salvage examples
    # =========================================================================
    cat_a = [r for r in rows
             if r["llm_context_prob"] is not None and r["llm_context_prob"] >= 0.7
             and (r["wer_%"] is not None and r["wer_%"] >= 50
                  or r["wwer_%"] is not None and r["wwer_%"] >= 50)]
    cat_a.sort(key=interest_score_llm, reverse=True)

    print("=" * 100)
    print(f"CATEGORY A: LLM-Salvage Examples  (total candidates: {len(cat_a)})")
    print("  Filter: llm_context_prob >= 0.7 AND (WER >= 50% OR WWER >= 50%)")
    print("  These are cases where WER says 'bad' but LLM approach says 'recoverable'.")
    print("=" * 100)
    for i, r in enumerate(cat_a[:6], 1):
        print_example(i, r)

    # =========================================================================
    # CATEGORY B: Rule-based salvage examples
    # =========================================================================
    cat_b = [r for r in rows
             if r["context_recoverable"]
             and (r["wer_%"] is not None and r["wer_%"] >= 50
                  or r["wwer_%"] is not None and r["wwer_%"] >= 50)]
    cat_b.sort(key=interest_score_rule, reverse=True)

    print("\n" + "=" * 100)
    print(f"CATEGORY B: Rule-Based Salvage Examples  (total candidates: {len(cat_b)})")
    print("  Filter: context_recoverable == True AND (WER >= 50% OR WWER >= 50%)")
    print("=" * 100)
    for i, r in enumerate(cat_b[:6], 1):
        print_example(i, r)

    # =========================================================================
    # CATEGORY C: LLM saves but rule-based misses
    # =========================================================================
    cat_c = [r for r in rows
             if r["llm_context_prob"] is not None and r["llm_context_prob"] >= 0.7
             and not r["context_recoverable"]]
    cat_c.sort(key=interest_score_llm, reverse=True)

    print("\n" + "=" * 100)
    print(f"CATEGORY C: LLM Saves but Rule-Based Misses  (total candidates: {len(cat_c)})")
    print("  Filter: llm_context_prob >= 0.7 AND context_recoverable == False")
    print("  These highlight the LLM approach's advantage over rule-based methods.")
    print("=" * 100)
    for i, r in enumerate(cat_c[:4], 1):
        print_example(i, r)

    # =========================================================================
    # CATEGORY D: Rule-based saves over high WWER specifically
    # =========================================================================
    cat_d = [r for r in rows
             if r["context_recoverable"]
             and r["wwer_%"] is not None and r["wwer_%"] >= 50]
    cat_d.sort(key=interest_score_rule, reverse=True)

    print("\n" + "=" * 100)
    print(f"CATEGORY D: Rule-Based Saves Over High WWER  (total candidates: {len(cat_d)})")
    print("  Filter: context_recoverable == True AND WWER >= 50%")
    print("=" * 100)
    for i, r in enumerate(cat_d[:4], 1):
        print_example(i, r)

    # =========================================================================
    # SUMMARY STATISTICS
    # =========================================================================
    print("\n" + "=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)

    total = len(rows)
    llm_recoverable = sum(1 for r in rows if r["llm_context_prob"] is not None and r["llm_context_prob"] >= 0.7)
    rule_recoverable = sum(1 for r in rows if r["context_recoverable"])
    both = sum(1 for r in rows if r["context_recoverable"] and r["llm_context_prob"] is not None and r["llm_context_prob"] >= 0.7)
    llm_only = sum(1 for r in rows if not r["context_recoverable"] and r["llm_context_prob"] is not None and r["llm_context_prob"] >= 0.7)
    rule_only = sum(1 for r in rows if r["context_recoverable"] and (r["llm_context_prob"] is None or r["llm_context_prob"] < 0.7))

    high_wer = sum(1 for r in rows if r["wer_%"] is not None and r["wer_%"] >= 50)
    high_wer_llm_save = sum(1 for r in rows if r["wer_%"] is not None and r["wer_%"] >= 50 and r["llm_context_prob"] is not None and r["llm_context_prob"] >= 0.7)
    high_wer_rule_save = sum(1 for r in rows if r["wer_%"] is not None and r["wer_%"] >= 50 and r["context_recoverable"])

    print(f"  Total segments:                   {total}")
    print(f"  LLM recoverable (prob >= 0.7):    {llm_recoverable}  ({100*llm_recoverable/total:.1f}%)")
    print(f"  Rule-based recoverable:           {rule_recoverable}  ({100*rule_recoverable/total:.1f}%)")
    print(f"  Both agree recoverable:           {both}  ({100*both/total:.1f}%)")
    print(f"  LLM-only recoverable:             {llm_only}  ({100*llm_only/total:.1f}%)")
    print(f"  Rule-only recoverable:            {rule_only}  ({100*rule_only/total:.1f}%)")
    print(f"  High WER (>= 50%):                {high_wer}  ({100*high_wer/total:.1f}%)")
    if high_wer > 0:
        print(f"  High WER + LLM saves:             {high_wer_llm_save}  ({100*high_wer_llm_save/high_wer:.1f}% of high-WER)")
        print(f"  High WER + Rule saves:            {high_wer_rule_save}  ({100*high_wer_rule_save/high_wer:.1f}% of high-WER)")

    cat_a_ids = set(r["utt_id"] for r in cat_a)
    cat_b_ids = set(r["utt_id"] for r in cat_b)
    overlap_ab = cat_a_ids & cat_b_ids
    print(f"\n  Cat A candidates (LLM salvage):   {len(cat_a)}")
    print(f"  Cat B candidates (Rule salvage):  {len(cat_b)}")
    print(f"  Overlap (in both A and B):        {len(overlap_ab)}")
    print(f"  Cat C candidates (LLM only):      {len(cat_c)}")
    print(f"  Cat D candidates (Rule+WWER):     {len(cat_d)}")

    print("\n  LLM Context Probability Distribution:")
    for lo, hi, label in [(0.0, 0.3, "low (0.0-0.3)"),
                           (0.3, 0.5, "marginal (0.3-0.5)"),
                           (0.5, 0.7, "moderate (0.5-0.7)"),
                           (0.7, 0.9, "high (0.7-0.9)"),
                           (0.9, 1.01, "very high (0.9-1.0)")]:
        count = sum(1 for r in rows if r["llm_context_prob"] is not None and lo <= r["llm_context_prob"] < hi)
        print(f"    {label:25s}  {count:5d}  ({100*count/total:.1f}%)")


if __name__ == "__main__":
    main()
