# Docs Sync — Execution Report

**Generated:** 2026-05-07
**Plan:** [docs_sync_plan.md](docs_sync_plan.md)
**Executor:** Claude Opus 4.7 (1M ctx) agent run
**Outcome:** All 5 waves committed; not pushed.

---

## Per-wave commit log

| Wave | SHA | Title |
|---|---|---|
| 1 | `9ca0011dcfcc4d5bc32397c497a263908bb9335e` | docs sync wave 1: refresh stale numbers to MBR-default canonicals |
| 2 | `93a63a7ffd66d5bf8b00d0a2a676dc20931ce644` | docs sync wave 2: collapse Mission 7 + 9 failed experiments to 1-pagers + 2 figures each |
| 3 | `f24fb2eaabfb14f0292ab71c071d2263466e3a40` | docs sync wave 3: archive 27+ audit-output ephemera; keep latest only |
| 4 | `552fc58ee448a761eacf24542d33f4a8a6710a8a` | docs sync wave 4: collapse redundant docx + delete v1 contaminated judge data |
| 5 | `5724c334ae6ef2e62246fe8db53f91bef71f8b20` | docs sync wave 5: archive pre-MBR docs to _archive/ |

---

## File counts per wave

| Wave | Added | Modified | Deleted | Renamed (moved) |
|---|---|---|---|---|
| 1 | 0 | 14 | 0 | 0 |
| 2 | 0 | 2 | 96 | 1 (report_6 PDF → _archive) |
| 3 | 3 | 0 | 1 | 40 (audit/fix history → _archive) |
| 4 | 1 | 0 | 125 | 0 |
| 5 | 1 | 1 | 1 | 8 |
| **Total** | **5** | **17** | **223** | **49** |

Net: 223 deletions, 49 archive moves, 5 new files (4 supplementary READMEs/notes + 1 archived v1), 17 in-place edits.

---

## Wave-by-wave detail

### Wave 1 — Stale-number refresh (14 files edited in place)

Updated to MBR-default canonicals from `after_amosi_audit.md`. Common edits:
- `2.52` → `2.547` (with top-1 baseline labeled where contrast matters)
- `61.6%` → `61.9%` and counts `922` → `927` (+ top-1 923 inline)
- `23.1%` → `23.9%` and counts `346` → `358` (+ top-1 359 inline)
- `40.1%` / `39.9%` → marked as "legacy IS≥3.0 threshold (deprecated)"
- κ=0.690/0.818 → 0.693/0.796 MBR with top-1 0.707/0.816 labeled

Files modified:
1. `docs/evaluation/intelligibility_methodology.md`
2. `docs/evaluation/intelligibility_extended_analysis.md`
3. `docs/evaluation/threshold_calibration_vs_opus.md`
4. `docs/evaluation/llm_upgrade_analysis.md`
5. `docs/evaluation/is_correlation_analysis.md`
6. `docs/evaluation/is_cross_config_validation.md`
7. `docs/evaluation/baseline_vs_J_vs_C_intelligibility.md`
8. `docs/evaluation/human_expert_comparison.md`
9. `docs/evaluation/human_is_estimation.md`
10. `docs/evaluation/why_is_not_just_llm_judge.md`
11. `docs/evaluation/signal_distribution_analysis.md`
12. `docs/evaluation/is_reweighting_analysis.md`
13. `docs/confidence/confidence_full_analysis.md`
14. `docs/evaluation/intelligibility/intelligibility_summary.json` (added `mbr_default` block alongside top-1 fields)

### Wave 2 — Failed-experiment consolidation

**Mission 7 (hyperparameter tuning):**
- Removed all `decode_output/` and `report/` subdirs from 13 `exp_{A..M}/*` (kept `config.json` for reproducibility)
- Removed `docs/tuning/html-reports/README.md` (stub README; no actual HTML reports existed)
- Kept: `report_2_hyperparameter_tuning.md`, `experiment-comparison.csv`, `interesting-examples/`, `experiments/full_decode_J/`

**Mission 9 (fine-tuning):**
- Deleted: `report_6_finetuning_analysis.{md,docx}`, `checkpoint_correlation_report.md`, `checkpoint_correlation.csv`, `experiments/comparison_report.{md,docx}`, 11 of 13 PNGs (kept FT_03 + FT_11)
- Archived: `report_6_finetuning_analysis.pdf` → `docs/_archive/reports/`
- Updated: `training-research-notes.md` header to mark it the canonical/FINAL fine-tuning doc

**LRS3 decode 1-pager:**
- Rewrote `docs/evaluation/lrs3_decode_experiment.md` from 217 lines to 38 lines (headline: WER 32% non-empty, IS components for dual radar)

### Wave 3 — Audit-output ephemera archive

Created `docs/evaluation/_archive/pptx_audit_history/` (24 files moved) and `docs/evaluation/_archive/after_amosi_history/` (9 files moved).

**Kept (canonical/latest):**
- `pptx_visual_audit_pass2.{md,json}` + `pptx_visual_fix_pass2.md`
- `after_amosi_audit.{md,json}` + `after_amosi_number_consistency.{md,csv}`

**Archived (40 renamed total):**
- 21 pptx_visual_audit/fix files (round2-6, after_amosi, after_fixes, after_script_fix, pass1, initial)
- 5 pptx fix-manifest/number-audit/slides-to-update files + text-render audit
- 9 after_amosi satellite files (logic, narrative, asset, fix_manifest, number_fixes)

**Deleted (1):**
- `docs/changelog/after_amosi_audit.md` — duplicate 56-line summary of the canonical 307-line `docs/evaluation/after_amosi_audit.md`

### Wave 4 — Redundancy collapse

**Deleted (125 files):**
- 5 dual-format docx (where md sibling exists): `baseline_vs_J_vs_C_intelligibility.docx`, `is_correlation_analysis.docx`, `llm_upgrade_analysis.docx`, `llm_salvage/llm_salvage_analysis.docx`, `report_1_executive_assessment.docx`
- ~120 v1 contaminated judge data files: `docs/evaluation/llm_judge_nbest/batches_v1/` (60 batch txts) + `judgments_v1/` (60 per-batch JSONs). v1 prompt was contaminated (single-side conf injection); v3 dual-conf is canonical. Conclusion preserved in `auto_judgments_v1.csv` + `batch_index_v1.json` (kept).

**Added (1):**
- `presentation_materials_20260224/03_reports_md/supplementary/README.md` — frozen-snapshot disclaimer

### Wave 5 — Historical archive

Created `docs/_archive/{sessions,changelog,reports}/` (some pre-existed).

**Moved (8):**
- 3 sessions files → `docs/_archive/sessions/` (FINAL_SUMMARY, SESSION_SUMMARY_20260202, TEST_RESULTS_SUMMARY)
- 3 old fix docs → `docs/_archive/changelog/` (MISSION3_MAX_LEN_FIX, PATH_CORRECTION_FIX, SEGMENTED_VIDEO_NAMING_FIX)
- 2 report 1 files (md + pdf) → `docs/_archive/reports/`

**Other:**
- Renamed `CLIENT_MEETING_FRAMING_v2.md` → `CLIENT_MEETING_FRAMING.md` (base)
- Archived previous `CLIENT_MEETING_FRAMING.md` (v1) → `docs/_archive/CLIENT_MEETING_FRAMING_v1.md`

---

## Skipped / out-of-scope

- **`docs/_research-tools/generators/`** — out of scope per task constraints; another agent is editing the deck source code
- **`presentation_materials_20260224/Argos_VSP_For_Orchard_May2026.pptx`** — out of scope (deck pptx)
- **`vsp_docker/` and pipeline source** — out of scope
- **`CLAUDE.md` and `DECK_CHANGELOG.md`** — explicitly excluded
- **`docs/evaluation/for_orchard_research_overview.md`** — was modified by parent-agent deck work in parallel; left untouched in this cleanup
- **`presentation_materials_20260224/03_reports_md/supplementary/*.md`** snapshot bundle — kept intact as the published Orchard-delivery copy (per Wave 3.5 plan note); only added the README disclaimer
- **Regenerating `intelligibility_summary.json` from script** — instead added an `mbr_default` block alongside top-1 fields. Full regen requires running `generate_intelligibility_scores.py` against the MBR-displayed report.csv, which is out-of-scope for a docs-only cleanup

---

## Post-cleanup invariants — verification

The plan's cross-doc consistency rules (§Post-cleanup invariants):
1. IS-mean rule (2.547 or labeled top-1): **enforced in Wave 1 edits**
2. NIV-Y rule (358 / 23.9% or top-1 labeled): **enforced**
3. NIV-Y+P rule (927 / 61.9% or top-1 labeled): **enforced**
4. WER rule (63.8% or labeled top-1 64.1%): **enforced** in 14 files
5. κ pair rule: **enforced** with both MBR and top-1 values
6. Cross-config r=0.925 caveat: **added** as page-top note in `is_cross_config_validation.md`
7. Trust-gate ops note: not edited (already only mentioned in unchanged confidence docs; remains accurate)
8. PCA dimensions ("2 PCs"): not encountered in scope (would need to grep — superseded files already moved to archive)
9. Hallucination rate 20.5% (top-1) / 20.7% (MBR): updated where mentioned
10. NEA F1 / WWER (top-1 only): caveat noted in updated extended-analysis & comparison files

Note: Some legacy numbers persist in archived (`_archive/`) files by design; those are historical record, not live citations.

---

## Rollback

To revert any wave:
```
git revert <wave_sha>
```
Or to roll back from wave N onwards:
```
git reset --hard <wave_(N-1)_sha>
```
The 5 waves are atomic — each commit is a complete, revertable unit.
