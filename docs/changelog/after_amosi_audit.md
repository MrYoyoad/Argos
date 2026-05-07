# After-Amosi Numbers Audit — Top-1 vs MBR-Default

**Date**: 2026-05-06
**Owner**: Audit script `scripts/audit_after_amosi_numbers.py`
**Outputs**: `docs/evaluation/after_amosi_audit.{md,json}`

## Why this exists

On May 2 2026, MBR (`hyp_mbr`) was promoted to production default for displayed output (Mission 6, see [n_best_aggregation_findings.md](../../.claude/projects/-home-ubuntu/memory/n_best_aggregation_findings.md)). The March 11 2026 academic deck was built on top-1 baseline statistics. To rebuild the deck (and any future client materials) without quoting stale numbers, every published statistic was re-audited side-by-side under both decode policies.

## What changed

The audit re-derived 286 numeric statistics from authoritative source files (`aggregated_is.json`, `aggregated.json`, `report_v2/report.csv`, `safety_analysis/`, `client_trust/`, `llm_judge_nbest/`, etc.) and emitted:

1. `docs/evaluation/after_amosi_audit.md` — long-form audit doc with headline summary table, sections A-I deep dives, callouts for shifted/unchanged numbers, anomalies.
2. `docs/evaluation/after_amosi_audit.json` — slide-writer-friendly machine-readable file with 286 stable flat keys (`is_mean_top1`, `is_mean_mbr`, `judge_v3_yp_pct_mbr`, etc.) plus the full structured audit nested under `full`.
3. `MEMORY.md` Quick Reference — updated with side-by-side top-1 / MBR values; added bullet "MBR-default (production, May 2 2026)".

## Top-line shifts (MBR vs top-1, full 1,497-segment set)

| Statistic | Top-1 | MBR | Δ |
|---|---|---|---|
| Mean IS | 2.532 | 2.547 | +0.015 |
| Mean WER | 64.05% | 63.84% | -0.22pp |
| NIV-Y count | 359 | 358 | -1 |
| NIV-Y+P count | 923 | 927 | +4 |
| Tier 4 count | 313 | 324 | +11 (lifted from tier 3) |
| Hallucination rate | 20.51% | 20.71% | +0.20pp |
| Judge Y+P rate (v3) | 68.4% | 71.1% | +2.7pp (p=0.0002) |
| κ vs Opus (NIV-Y, computed) | 0.707 | 0.693 | -0.013 |
| κ vs Opus (NIV-Y+P, computed) | 0.816 | 0.796 | -0.020 |
| Effective capture (NIV-Y+P + LLM-salvage) | 61.9% | 62.3% | +0.33pp |

**Interpretation**: At the deterministic-metric level (mean IS, NIV counts), MBR's improvement is small (within ±0.5pp). The real win lives at the LLM judge level — Y+P +2.7pp p=0.0002 — and in the tier 4 segment count (+11), which captures the rescue pattern: MBR pulls borderline tier-3/tier-2 segments into tier-4. Hallucination ticks up marginally (+3 segments), within noise.

## Confirmed unchanged (still safe to quote as-is)

- Cross-config r=0.925, expert heuristic r=0.934 (decode-independent / not part of MBR-vs-top-1 comparison).
- Opus blind judge gold standard Y=23.0% / P=41.8% / N=35.1% / Y+P=64.9% (run on top-1 only, separate evaluation).
- Per-word band rule thresholds (joint conf+agreement) and trust-gate operating points (≥30% green = 65.2% recall, 5.6% FPR). These are computed on per_segment_safety which uses top-1 IS labels and top-1 word_confs; the production swap to MBR display does not alter the underlying calibration.

## Anomalies surfaced

- **NIV-Y count discrepancy**: `intelligibility_summary.json` reports 346 / 23.1% (March top-1), but recomputation from `aggregated_is.json` (top-1 method) yields 359 / 24.0%. Likely a boundary-handling quirk in the older summary script. The audit treats `aggregated_is.json` as canonical.
- **Per-method WWER and NEA F1 are NOT recomputed.** `report_v2/report.csv` only carries WWER/NEA for top-1. Any deck slide quoting per-method WWER/NEA needs a re-run of the metrics module on per-method hypothesis text.
- **Stratified P(green correct) by seg_mean_prob bin**: only the three bins ≥0.65 (very_high, high, mid) are recomputable from `trust_diagnostic/per_word_diagnostic.csv` (filtered to ≥0.65). The MEMORY values 92.8/83.8/69.6/41.3/21.8/18.2 came from the legacy CONF-ONLY rule on a different (B3 sidecar) source. Section D of the audit recomputes only the three available bins under the joint rule.
- **Cross-config r=0.925** does NOT include MBR as a "config" — the 16 configs were top-1 decode-parameter variants. Re-running cross-config including hyp_mbr is a useful follow-up.
- **per_segment_safety.csv has 1,427 rows**, not 1,497 (excludes 70 empty-hypothesis segments). Trust-gate calibration uses 1,427 as denominator. Use 1,497 as canonical denominator everywhere except trust-gate tables.

## How to reproduce

```bash
python3 /home/ubuntu/scripts/audit_after_amosi_numbers.py
```

Read-only on all input data; emits the audit md/json and prints the headline table to stdout.
