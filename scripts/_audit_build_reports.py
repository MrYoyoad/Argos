#!/usr/bin/env python3
"""
Build the two markdown deliverables from pptx_number_audit.csv:
   - /home/ubuntu/docs/evaluation/pptx_number_audit.md         (summary report)
   - /home/ubuntu/docs/evaluation/pptx_slides_to_update.md     (high-priority slide list)

Also writes a CSV of "high-priority slides" alongside.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

CSV_PATH = Path("/home/ubuntu/docs/evaluation/pptx_number_audit.csv")
MD_SUMMARY = Path("/home/ubuntu/docs/evaluation/pptx_number_audit.md")
MD_SLIDES = Path("/home/ubuntu/docs/evaluation/pptx_slides_to_update.md")

# Map slide-number ranges to sections of the AFTER_AMOSI March deck.
# Inferred from the deck's narrative arc; refined after spot-checking titles.
# Refined ranges from inspecting actual slide titles in the AMOSI March deck.
SECTION_RANGES_AMOSI = [
    ("Opening / Mission / TL;DR",                 (1, 6)),
    ("Problem Framing (VSP, Visemes, Reality Gap)", (7, 13)),
    ("Research Findings (LLM Judge, IS framework)", (14, 36)),
    ("Failure Modes & Real Examples",             (37, 48)),
    ("Engineering / Pipeline / Demo",             (49, 57)),
    ("Future Directions (Confidence, Roadmap)",   (58, 71)),
    ("Arabic / Closing / Appendix",               (72, 84)),
]


def section_for(slide_num: int) -> str:
    for name, (lo, hi) in SECTION_RANGES_AMOSI:
        if lo <= slide_num <= hi:
            return name
    return "Other"


def main() -> None:
    rows = list(csv.DictReader(open(CSV_PATH)))
    decks_present = sorted({r["deck"] for r in rows})

    # ---------- Per-deck stats ----------
    per_deck_total = Counter(r["deck"] for r in rows)
    per_deck_slides = defaultdict(set)
    for r in rows:
        per_deck_slides[r["deck"]].add(int(r["slide_num"]))

    per_deck_status = defaultdict(Counter)
    for r in rows:
        per_deck_status[r["deck"]][r["suggested_status"]] += 1

    # ---------- Top shifted-number frequencies (across decks) ----------
    shifted_rows = [r for r in rows if r["suggested_status"] == "NEEDS_VERIFICATION"]
    shifted_freq = Counter(r["normalized"] for r in shifted_rows)

    # ---------- High-priority slides (>=3 NEEDS_VERIFICATION) ----------
    counts_per_slide = defaultdict(Counter)  # (deck, slide) -> Counter(status)
    for r in rows:
        counts_per_slide[(r["deck"], int(r["slide_num"]))][r["suggested_status"]] += 1
    titles_per_slide = {(r["deck"], int(r["slide_num"])): r["slide_title"] for r in rows}
    hidden_per_slide = {(r["deck"], int(r["slide_num"])): r["hidden"] for r in rows}

    high_pri = []
    for (deck, slide), c in counts_per_slide.items():
        nv = c.get("NEEDS_VERIFICATION", 0)
        wf = c.get("WRONG_FRAMING_FIX", 0)
        if nv >= 3 or wf >= 1:
            high_pri.append({
                "deck": deck,
                "slide": slide,
                "title": titles_per_slide.get((deck, slide), ""),
                "hidden": hidden_per_slide.get((deck, slide), "no"),
                "needs_verification": nv,
                "wrong_framing": wf,
                "likely_hold": c.get("LIKELY_HOLD", 0),
                "metadata": c.get("METADATA", 0),
                "unclassified": c.get("UNCLASSIFIED", 0),
            })
    high_pri.sort(key=lambda x: (x["deck"], x["slide"]))

    # ---------- Slides quoting WRONG_FRAMING tokens ----------
    wrong_framing_slides = defaultdict(list)
    for r in rows:
        if r["suggested_status"] == "WRONG_FRAMING_FIX":
            key = (r["deck"], int(r["slide_num"]))
            wrong_framing_slides[key].append(r)

    # ---------- Cross-deck consistency check ----------
    # For each NEEDS_VERIFICATION number that appears in BOTH AFTER_AMOSI and Client_v9
    # surrounding the same metric noun, simply note co-occurrence. We only flag
    # *disagreement* where the same noun has different normalized numbers.
    METRIC_NOUNS = ["wer", "wwer", "is mean", "intelligibility", "salvage",
                    "hallucin", "niv", "captur", "nea"]

    def metric_for(text: str) -> str | None:
        t = text.lower()
        for n in METRIC_NOUNS:
            if n in t:
                return n
        return None

    # collect (deck, metric) -> set of normalized numbers (NEEDS_VERIFICATION only)
    deck_metric_nums = defaultdict(lambda: defaultdict(set))
    for r in rows:
        if r["suggested_status"] != "NEEDS_VERIFICATION":
            continue
        m = metric_for(r["surrounding_text"])
        if m is None:
            continue
        deck_metric_nums[m][r["deck"]].add(r["normalized"])

    consistency_issues = []
    for metric, deck_nums in sorted(deck_metric_nums.items()):
        if "AFTER_AMOSI_Mar2026" in deck_nums and "Client_v9_May2026" in deck_nums:
            a = deck_nums["AFTER_AMOSI_Mar2026"]
            c9 = deck_nums["Client_v9_May2026"]
            only_in_amosi = a - c9
            only_in_v9 = c9 - a
            if only_in_amosi or only_in_v9:
                consistency_issues.append({
                    "metric": metric,
                    "only_in_amosi": sorted(only_in_amosi),
                    "only_in_v9": sorted(only_in_v9),
                    "in_both": sorted(a & c9),
                })

    # ---------- Build summary markdown ----------
    lines = []
    lines.append("# PPTX Number Audit — Pre-MBR-Default Snapshot")
    lines.append("")
    lines.append(
        "Extraction of every numeric mention in the Argos VSP decks. Status "
        "labels (NEEDS_VERIFICATION / LIKELY_HOLD / WRONG_FRAMING_FIX / METADATA "
        "/ UNCLASSIFIED) are heuristic — the parallel MBR-default audit will "
        "confirm exact replacements."
    )
    lines.append("")
    lines.append(
        "Source CSV: `/home/ubuntu/docs/evaluation/pptx_number_audit.csv`  "
        "(extractor: `/home/ubuntu/scripts/extract_pptx_numbers.py`)."
    )
    lines.append("")
    lines.append("## Key findings")
    lines.append("")
    lines.append(
        "1. **No live deprecated framing in the AMOSI March deck or Client v9**. "
        "`IS >= 3.0` / `39.9%` / `40.1%` / `597` do not appear as live claims; the "
        "two surviving mentions of the `IS >= 3.0` phrase (slide 32 body and notes) "
        "are explicitly historical (`Old IS >= 3.0 wrongly rejected this segment.` "
        "and `Old IS >= 3.0 threshold is superseded`). The decks have already migrated "
        "to NIV-Y / NIV-Y+P language."
    )
    lines.append(
        "2. **PCA framing is correct**. Slide 27 (`Do 6 Signals Actually Measure 6 Things?`) "
        "uses `Kaiser retains 2 (87.9%)` as the headline and only mentions PC3 as "
        "`adds nuance`. No `3 dimensions` claim to retract."
    )
    lines.append(
        "3. **Client v9 and v10 are byte-identical text**. Different file checksums; "
        "extracted text identical. Update v9 once and re-name to v10, or skip v10."
    )
    lines.append(
        "4. **AMOSI deck is the heaviest target**: 84 slides, 1,852 number tokens, "
        "639 in NEEDS_VERIFICATION. ~55 of 84 slides need touching for the new academic deck."
    )
    lines.append(
        "5. **Highest-density slides** (>=15 NEEDS_VERIFICATION numbers each): "
        "AMOSI 24 (IS Signals: Word Accuracy & Length), AMOSI 27 (PCA), "
        "AMOSI 29 (Model Comparison: IS Profiles), AMOSI 30 (Where WER Lies Most), "
        "AMOSI 31 (NIV header), AMOSI 34 (hidden, Where IS and Judge Disagree), "
        "AMOSI 36 (Three Numbers That Tell the Real Story), AMOSI 60 (Roadmap, 47 NV), "
        "AMOSI 61 (IS Improvement Roadmap, 32 NV), AMOSI 68 (Stronger LLM, 19 NV), "
        "AMOSI 70 (hidden, LLM Upgrade, 25 NV), AMOSI 83 (Judge x IS Cross-Tab, 22 NV)."
    )
    lines.append("")
    lines.append("## Per-deck slide & token counts")
    lines.append("")
    lines.append("| Deck | Total slides | Hidden | Slides w/ numbers | Number tokens |")
    lines.append("|------|--------------:|-------:|------------------:|--------------:|")
    deck_meta = {
        "AFTER_AMOSI_Mar2026": (84, 10),
        "Client_v9_May2026":   (64, 0),
        "Client_v10_May2026":  (64, 0),
        "Supplementary_LLM_Judge_30": (8, 0),
    }
    for d in ["AFTER_AMOSI_Mar2026", "Client_v9_May2026",
              "Client_v10_May2026", "Supplementary_LLM_Judge_30"]:
        if d not in per_deck_total:
            continue
        n_slides, hidden = deck_meta.get(d, (0, 0))
        lines.append(f"| {d} | {n_slides} | {hidden} | {len(per_deck_slides[d])} | {per_deck_total[d]} |")
    lines.append("")

    lines.append("**Note**: `Client_v9_May2026` and `Client_v10_May2026` are textually "
                 "identical (md5sum on PPTX differs but extracted text is byte-for-byte "
                 "equal). Treat v10 as a no-op rename of v9 for audit purposes.")
    lines.append("")

    lines.append("## Status breakdown (per deck)")
    lines.append("")
    lines.append("| Deck | NEEDS_VERIFICATION | LIKELY_HOLD | WRONG_FRAMING_FIX | METADATA | UNCLASSIFIED |")
    lines.append("|------|-------------------:|------------:|------------------:|---------:|-------------:|")
    for d in ["AFTER_AMOSI_Mar2026", "Client_v9_May2026",
              "Client_v10_May2026", "Supplementary_LLM_Judge_30"]:
        if d not in per_deck_status:
            continue
        c = per_deck_status[d]
        lines.append(
            f"| {d} | {c.get('NEEDS_VERIFICATION',0)} | "
            f"{c.get('LIKELY_HOLD',0)} | {c.get('WRONG_FRAMING_FIX',0)} | "
            f"{c.get('METADATA',0)} | {c.get('UNCLASSIFIED',0)} |"
        )
    lines.append("")

    lines.append("## Top 30 NEEDS_VERIFICATION numbers by frequency (all decks)")
    lines.append("")
    lines.append("These are the numbers most likely to need rewriting under MBR-default. "
                 "Filtered to drop bare single-digit tokens (`0`-`9`) which are mostly "
                 "page numbers, list bullets, or one-off counts that aren't statistics.")
    lines.append("")
    lines.append("| Rank | Number | Total mentions | AMOSI | Client v9 | Likely meaning |")
    lines.append("|-----:|--------|---------------:|------:|----------:|----------------|")
    interp = {
        "61.6%": "NIV-Y+P capture (922/1,497)",
        "61.6":  "NIV-Y+P capture %",
        "23.1%": "NIV-Y capture (346/1,497)",
        "23.1":  "NIV-Y capture %",
        "64.1%": "Mean WER (top-1 baseline)",
        "64.1":  "Mean WER %",
        "60.5%": "Mean WWER (top-1 baseline)",
        "60.5":  "Mean WWER %",
        "38.9%": "Named-entity F1",
        "38.9":  "NEA F1 %",
        "20.5%": "Hallucination rate (307/1,497)",
        "20.5":  "Hallucination rate %",
        "51.1%": "Salvage rate incl. llm_context_prob",
        "51.1":  "Salvage %",
        "39.9%": "Legacy 'captured' (IS>=3.0) — DEPRECATED framing",
        "39.9":  "Legacy 'captured' (IS>=3.0)",
        "40.1%": "Legacy capture pre-salvage — DEPRECATED",
        "40.1":  "Legacy capture pre-salvage",
        "2.52":  "Mean Intelligibility Score",
        "2.5":   "IS mean (rounded)",
        "346":   "NIV-Y count (of 1,497)",
        "922":   "NIV-Y+P count (of 1,497)",
        "165":   "LLM-salvageable segment count",
        "307":   "Hallucinated segment count",
        "597":   "Legacy IS>=3.0 captured count — DEPRECATED",
        "276":   "IS tier 5 (Excellent) count",
        "321":   "IS tier 4 (Good) count",
        "325":   "IS tier 3 (Fair) count",
        "336":   "IS tier 2 (Poor) count",
        "239":   "IS tier 1 (Failed) count",
        "18.4%": "IS tier Excellent %",
        "21.4%": "IS tier Good %",
        "21.7%": "IS tier Fair %",
        "22.4%": "IS tier Poor %",
        "16.0%": "IS tier Failed %",
        "1497":  "Eval segment count (sample size, not shifted)",
        # Threshold values (LIKELY_HOLD by intent — but frequently appear in NV-tagged text)
        "3.80":  "NIV-Y IS threshold (LIKELY_HOLD)",
        "2.00":  "NIV-Y+P IS threshold (LIKELY_HOLD)",
        "25.4%": "Paper LRS3 WER reference (LIKELY_HOLD)",
        "25.5%": "WER-based 'capture' under top-1 baseline",
        "82%":   "IS-vs-judge agreement (band reliability) — verify under MBR",
        "65%":   "Confidence-band reliability tier (verify under MBR)",
        "70%":   "Confidence threshold figure (verify under MBR)",
        "85%":   "Confidence/agreement threshold (verify under MBR)",
        "100%":  "WER ceiling marker (often hallucination indicator)",
        "34%":   "WER NIV-Y threshold for kappa parity (LIKELY_HOLD)",
        "75%":   "Possibly: confidence band reliability target (verify)",
        "15%":   "Various - verify per slide",
        "3.1":   "Possibly: tier-3 IS reference / version number — verify",
        "5.1":   "PCA PC3 variance % (5.1%) — LIKELY_HOLD",
        "2.07":  "Possibly: per-segment IS sample value — verify",
        "1024":  "Cluster count / dim — LIKELY_HOLD",
        "4096":  "Cluster count / dim — LIKELY_HOLD",
    }
    by_deck_for_num = defaultdict(lambda: defaultdict(int))
    for r in shifted_rows:
        by_deck_for_num[r["normalized"]][r["deck"]] += 1
    # Filter out bare single-digit tokens (0-9) for this view.
    filtered = [(tok, n) for tok, n in shifted_freq.most_common()
                if not (len(tok) == 1 and tok.isdigit())]
    rank = 0
    for tok, n in filtered[:30]:
        rank += 1
        a = by_deck_for_num[tok].get("AFTER_AMOSI_Mar2026", 0)
        v9 = by_deck_for_num[tok].get("Client_v9_May2026", 0)
        # Look up meaning by raw token, normalized, and stripped %.
        meaning = (interp.get(tok)
                   or interp.get(tok + "%")
                   or interp.get(tok.rstrip("%"))
                   or "")
        lines.append(f"| {rank} | `{tok}` | {n} | {a} | {v9} | {meaning} |")
    lines.append("")

    lines.append("## High-priority slides (>=3 NEEDS_VERIFICATION numbers OR any WRONG_FRAMING_FIX)")
    lines.append("")
    lines.append(f"Total: **{len(high_pri)} slides** across all decks.")
    lines.append("")
    lines.append("| Deck | Slide # | Hidden | Title | NV | WF | LH |")
    lines.append("|------|--------:|--------|-------|---:|---:|---:|")
    for hp in high_pri:
        title = hp["title"][:90].replace("|", "/")
        lines.append(
            f"| {hp['deck']} | {hp['slide']} | {hp['hidden']} | {title} | "
            f"{hp['needs_verification']} | {hp['wrong_framing']} | {hp['likely_hold']} |"
        )
    lines.append("")

    lines.append("## Slides quoting deprecated framing (WRONG_FRAMING_FIX)")
    lines.append("")
    lines.append("These slides need **text rewrites**, not just number swaps.")
    lines.append("Replacement guidance:")
    lines.append("")
    lines.append("- `\"3 dimensions\"` / `\"three principal\"` -> `\"2 PCs\"` (PCA: PC1=68.4% signal quality, PC2=19.5% length).")
    lines.append("- `\"IS >= 3.0\"` and `\"39.9%\"` / `\"40.1%\"` -> NIV thresholds: IS>=3.80 (NIV-Y, 23.1%) or IS>=2.00 (NIV-Y+P, 61.6%).")
    lines.append("- `\"captured\"` framing -> `\"Clearly Conveyed\"` (NIV-Y) or `\"Useful Output\"` (NIV-Y+P).")
    lines.append("")
    lines.append("| Deck | Slide # | Hidden | Title | Trigger snippet |")
    lines.append("|------|--------:|--------|-------|-----------------|")
    for (deck, slide), entries in sorted(wrong_framing_slides.items()):
        title = titles_per_slide.get((deck, slide), "")[:60].replace("|", "/")
        # Use first matching surrounding text
        snippet = entries[0]["surrounding_text"][:80].replace("|", "/").replace("\n", " ")
        lines.append(f"| {deck} | {slide} | {entries[0]['hidden']} | {title} | {snippet} |")
    lines.append("")

    lines.append("## Cross-deck consistency check")
    lines.append("")
    if not consistency_issues:
        lines.append("No metric-level disagreements detected between AFTER_AMOSI March deck and Client v9 deck.")
    else:
        lines.append(
            "For each metric noun (WER / WWER / IS / NIV / Salvage / Hallucination / NEA), "
            "list NEEDS_VERIFICATION numbers seen in only one deck. **A non-empty 'only in' "
            "column flags a sync gap that the new academic deck must reconcile.**"
        )
        lines.append("")
        lines.append("| Metric | In both | Only in AMOSI March | Only in Client v9 |")
        lines.append("|--------|---------|---------------------|-------------------|")
        for issue in consistency_issues:
            both = ", ".join(issue["in_both"]) or "—"
            only_a = ", ".join(issue["only_in_amosi"]) or "—"
            only_c = ", ".join(issue["only_in_v9"]) or "—"
            lines.append(f"| {issue['metric']} | {both} | {only_a} | {only_c} |")
    lines.append("")

    MD_SUMMARY.write_text("\n".join(lines))
    print(f"[ok] wrote {MD_SUMMARY}")

    # ---------- High-priority slide list (per deck, grouped by section, AMOSI focus) ----------
    lines2 = []
    lines2.append("# PPTX Slides To Update — High-Priority List for Academic Deck")
    lines2.append("")
    lines2.append(
        "Slides flagged for the new MBR-default academic deck. Focus is the "
        "AFTER_AMOSI March 84-slide deck (the master reference); client-deck "
        "entries appear in a separate section."
    )
    lines2.append("")
    lines2.append("Legend: **NV** = NEEDS_VERIFICATION (likely shifted), **WF** = WRONG_FRAMING_FIX (needs text rewrite, not just number swap).")
    lines2.append("")

    amosi_high = [hp for hp in high_pri if hp["deck"] == "AFTER_AMOSI_Mar2026"]
    by_section = defaultdict(list)
    for hp in amosi_high:
        by_section[section_for(hp["slide"])].append(hp)

    lines2.append("## AFTER_AMOSI March 2026 deck (84 slides) — by section")
    lines2.append("")
    section_order = [name for name, _ in SECTION_RANGES_AMOSI] + ["Other"]
    for sec in section_order:
        items = by_section.get(sec, [])
        if not items:
            continue
        lines2.append(f"### {sec}")
        lines2.append("")
        lines2.append("| Slide # | Hidden | Title | NV | WF | Numbers seen (top 6) |")
        lines2.append("|--------:|--------|-------|---:|---:|----------------------|")
        for hp in items:
            slide = hp["slide"]
            # collect the actual NEEDS_VERIFICATION + WRONG_FRAMING numbers on this slide
            nums = []
            for r in rows:
                if r["deck"] != "AFTER_AMOSI_Mar2026":
                    continue
                if int(r["slide_num"]) != slide:
                    continue
                if r["suggested_status"] in ("NEEDS_VERIFICATION", "WRONG_FRAMING_FIX"):
                    nums.append(r["normalized"])
            top_nums = ", ".join(f"`{x}`" for x, _ in Counter(nums).most_common(6))
            title = (hp["title"] or "")[:80].replace("|", "/").replace("\n", " ")
            lines2.append(
                f"| {slide} | {hp['hidden']} | {title} | "
                f"{hp['needs_verification']} | {hp['wrong_framing']} | {top_nums} |"
            )
        lines2.append("")

    # WRONG_FRAMING_FIX checklist (AMOSI only)
    amosi_wf_slides = sorted({slide for (deck, slide) in wrong_framing_slides
                              if deck == "AFTER_AMOSI_Mar2026"})
    lines2.append("## WRONG_FRAMING_FIX checklist (AMOSI deck)")
    lines2.append("")
    if not amosi_wf_slides:
        lines2.append("None detected.")
    else:
        lines2.append("These slides quote PCA `\"3 dimensions\"` or `\"IS>=3.0\"` / `\"39.9%\"` framings:")
        lines2.append("")
        for slide in amosi_wf_slides:
            title = titles_per_slide.get(("AFTER_AMOSI_Mar2026", slide), "")
            lines2.append(f"- Slide {slide}: {title}")
    lines2.append("")

    # Client deck appendix (compressed)
    client_high = [hp for hp in high_pri if hp["deck"] == "Client_v9_May2026"]
    if client_high:
        lines2.append("## Client v9/v10 deck (64 slides) — high-priority touches")
        lines2.append("")
        lines2.append(
            "v9 and v10 are textually identical. Update once and re-export both names "
            "if both must remain on disk."
        )
        lines2.append("")
        lines2.append("| Slide # | Title | NV | WF | Numbers seen (top 6) |")
        lines2.append("|--------:|-------|---:|---:|----------------------|")
        for hp in client_high:
            slide = hp["slide"]
            nums = []
            for r in rows:
                if r["deck"] != "Client_v9_May2026":
                    continue
                if int(r["slide_num"]) != slide:
                    continue
                if r["suggested_status"] in ("NEEDS_VERIFICATION", "WRONG_FRAMING_FIX"):
                    nums.append(r["normalized"])
            top_nums = ", ".join(f"`{x}`" for x, _ in Counter(nums).most_common(6))
            title = (hp["title"] or "")[:80].replace("|", "/").replace("\n", " ")
            lines2.append(
                f"| {slide} | {title} | {hp['needs_verification']} | {hp['wrong_framing']} | {top_nums} |"
            )
        lines2.append("")

    MD_SLIDES.write_text("\n".join(lines2))
    print(f"[ok] wrote {MD_SLIDES}")


if __name__ == "__main__":
    main()
