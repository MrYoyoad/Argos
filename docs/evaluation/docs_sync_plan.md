# Docs Sync Plan — May 2026 Post-Deck Cleanup

**Generated:** 2026-05-07
**Scope:** `docs/` tree + `presentation_materials_20260224/{03_reports_md,04_reports_docx,01_plots_for_slides}`
**Canonical narrative:** `Argos_VSP_For_Orchard_May2026.pptx` (89 slides, 80 visible + 9 hidden)
**Canonical numbers (source of truth):** `docs/evaluation/after_amosi_audit.md` + `after_amosi_audit.json`
**Deliverable type:** Plan only — no edits or deletions performed.

---

## TL;DR

| Bucket | Count |
|---|---|
| Total files surveyed under `docs/` | 345 (135 md, 66 json, 51 png, ~93 other) |
| Plus `presentation_materials_20260224/{03,04,01}` | ~80 (12 md reports + 14 docx + ~50 plots) |
| **AUTHORITATIVE** (keep, may need 1-3 line update) | ~26 |
| **OUT-OF-DATE** (in-place find/replace, 5–10 lines) | 14 |
| **CONTRADICTS-DECK** (rewrite needed, narrative shift) | 3 |
| **REDUNDANT** (consolidate/delete) | ~38 (audit rounds, v1 nbest batches, dual-format docx, pptx fix manifests) |
| **FAILED-EXPERIMENT-VERBOSE** (reduce to 1-pager + 1–2 figures) | 2 mission folders + 1 LRS3 doc |
| **HISTORICAL** (move to `_archive/`) | ~22 |
| **AUDIT-OUTPUT-EPHEMERAL** (keep latest, archive rest) | 16 |
| **NOTES-WORTH-KEEPING** (keep, possibly consolidate) | ~14 |
| **Estimated total cleanup time** | ~3–4 hours |
| **Files slated for deletion / archival** | ~95 |
| **Files slated for in-place update** | ~17 |
| **Files slated for consolidation summary** | 6 (replace folders/multi-doc with 1-pagers) |

The cleanup is dominated by audit-output ephemera (pptx_visual_audit rounds × 9, pptx_visual_fix rounds × 8, after_amosi_* × 13) that already accomplished their job and now bloat search results. Almost no docs need rewriting; most need either a 1-line MBR caveat or archival.

---

## Canonical numbers (apply find/replace from these everywhere flagged "OUT-OF-DATE")

These are the production-default values per `after_amosi_audit.md`:

| Statistic | Old (top-1, March 2026) | New (MBR-default, May 2026) |
|---|---|---|
| Mean IS | 2.52 | **2.547** |
| Median IS | 2.559 | **2.600** |
| Mean WER | 64.1% | **63.84%** (display "63.8%") |
| NIV-Y count | 346 (23.1%) | **358 (23.91%)** — display "358 (23.9%)" |
| NIV-Y+P count | 922 (61.6%) | **927 (61.92%)** — display "927 (61.9%)" |
| Legacy IS≥3.0 count | 597–601 (39.9–40.1%) | **615 (41.1%)** |
| Hallucination rate | 307 (20.5%) | **310 (20.71%)** |
| κ vs Opus (NIV-Y) | 0.690 | **0.693** (top-1: 0.707) |
| κ vs Opus (NIV-Y+P) | 0.818 | **0.796** (top-1: 0.816) |
| Judge Y+P (v3) | 68.40% | **71.08%** |
| Tier 5 / 4 / 3 / 2 / 1 | 288 / 313 / 322 / 337 / 237 | **291 / 324 / 312 / 329 / 241** |

**Important display rule** (from MEMORY): every IS-mean number must equal **2.547** OR be qualified as "top-1 baseline 2.532". WER, hallucination, κ values are paired similarly.

**Numbers that did NOT change** (do not touch these):
- Cross-config r=0.925 — still valid as IS-stability claim (top-1 only; not MBR validation).
- Expert heuristic r=0.934 — decode-independent.
- Opus blind judge gold standard (Y=23.0%, P=41.8%, N=35.1%, Y+P=64.9%) — judge was top-1.
- Per-word band-rule thresholds (green ≥0.95∧≥0.80, yellow ≥0.65∧≥0.50). MBR uses the same per-word posteriors.
- Trust-gate operating points (≥30% green: 65.2% recall / 5.6% FPR). Computed on top-1 per_segment confidence.
- WWER 60.51%, NEA F1 38.94% (top-1 only — not recomputed per method).

---

## Action plan (ordered by efficiency)

### Wave 1 — Authoritative numbers refresh (~30 min, 14 files, ~50 line edits)

For each file below, add a **single page-top notice** linking to `after_amosi_audit.md` and either (a) update inline numbers OR (b) add a one-line "March 2026 top-1 baseline; current MBR-default in audit" caveat. The MEMORY entry already lists which files cite which numbers.

| File | Action | Edits |
|---|---|---|
| `docs/evaluation/intelligibility_methodology.md` | Update Section 7 (Examples + threshold table line 312–313): `346 → 358`, `922 → 927`, `61.6% → 61.92%`. Add MBR caveat header. | ~6 |
| `docs/evaluation/intelligibility_extended_analysis.md` | Lines 26, 80–82, 234–237, 277: per-topic table + summary stats. Replace `2.52 → 2.547`, `922 (61.6%) → 927 (61.9%)`, `597 (39.9%) → 615 (41.1%)`, `601 (40.1%) → 615 (41.1%)`. | ~10 |
| `docs/evaluation/threshold_calibration_vs_opus.md` | Lines 21, 25, 42, 104, 116, 133, 268, 270: every `346` → `358`, every `922` → `927`, `61.6%` → `61.9%`, `23.1%` → `23.9%`. Re-state κ at MBR-default (0.693 / 0.796) **and** keep top-1 (0.707 / 0.816) labeled. | ~10 |
| `docs/evaluation/llm_upgrade_analysis.md` | Lines 5, 83, 154, 155, 180: replace `WER 64.1%, IS 2.52` → `WER 63.8%, IS 2.547`; `61.6%` → `61.9%`. | ~6 |
| `docs/evaluation/is_correlation_analysis.md` | Lines 449, 459: `2.520 → 2.547`, `2.538 → 2.600` (median), `922 (61.6%) → 927 (61.9%)`. | ~3 |
| `docs/evaluation/is_cross_config_validation.md` | Lines 44, 95–96, 132–134, 143, 181: NIV table + agreement summary. **Caveat: cross-config r=0.925 is top-1 across 16 configs — n-best NOT included. Add this footnote.** | ~7 |
| `docs/evaluation/baseline_vs_J_vs_C_intelligibility.md` | Line 35, 267: update legacy capture table; add MBR-default row to comparison. | ~3 |
| `docs/evaluation/human_expert_comparison.md` | Lines 46, 76: `61.6% → 61.9%`, `922 → 927`. | ~2 |
| `docs/evaluation/human_is_estimation.md` | Lines 12, 13, 118, 124, 142–144: `2.52 → 2.547` (8 occurrences in Path B summary). Headline conclusions hold. | ~6 |
| `docs/evaluation/why_is_not_just_llm_judge.md` | Line 3 caveat: update to MBR-default numbers. | ~1 |
| `docs/evaluation/intelligibility/intelligibility_summary.json` | **Regenerate** from latest aggregated_is.json. Currently has `mean_is: 2.532, niv_clearly_conveyed_count: 346, niv_useful_pct: 61.6` — all top-1. | regen via existing script |
| `docs/evaluation/signal_distribution_analysis.md` | Line 323: IS table `2.52 → 2.547`. Section 8 already current. | ~1 |
| `docs/evaluation/is_reweighting_analysis.md` | Line 45: original IS `3.70` and counts table — verify against MBR run; the *re-weighting* analysis is method-comparison, label both axes "(top-1)". | ~2 |
| `docs/confidence/confidence_full_analysis.md` | Line 11: `2.52 → 2.547`. | ~1 |

**Cumulative: ~58 line edits across 14 files.**

After Wave 1 the docs are numerically consistent with the deck.

---

### Wave 2 — Failed-experiment consolidation (~1 hour, save ~25 files / ~270 KB)

Three projects that deck doesn't sell as wins (and shouldn't carry full report verbosity):

#### 2.1 Hyperparameter tuning experiments (Mission 7 — "baseline robust")

**Current footprint:** `docs/tuning/experiments/exp_{A..M,full_decode_J}/` = 14 directories, ~1.1 MB. Each has `decode_output/` (decode.log, hypo.json, decode_params.json, wer.txxxxx) + `report/` (report.csv, report.txt, ansi.txt) + `config.json`.

**Deck claim** (Slide 4 + speaker notes): Exhaustive sweep across beam, lenpen, sampling, greedy on 107 segs found **no parameter combo improves WER meaningfully**; baseline (beam=20, lenpen=0) is most robust.

**Action:**
- **KEEP**: `docs/tuning/report_2_hyperparameter_tuning.md` (the synthesis), `docs/tuning/experiments/full_decode_J/` (the only experiment we ran on the full set, ~60K), `docs/tuning/interesting-examples/cross_experiment_comparison.csv`.
- **KEEP**: One summary table (`finetune_comparison.csv` analog): collapse all 13 exp's headline metrics into a single CSV (`docs/tuning/experiments/all_configs_summary.csv`) covering config + WER + IS. **This already exists** (`docs/tuning/experiment-comparison.csv` referenced in CLAUDE.md).
- **KEEP**: 2 representative figures: `01_wer_vs_duration.png` and `09_boxplot_wwer_all_experiments.png` (already in `docs/evaluation/plots/`).
- **DELETE**: All `exp_{A..M}/decode_output/` and `exp_{A..M}/report/` subdirectories (13 × ~80 KB ≈ 1 MB). Keep `config.json` in each so the param sweep is reproducible.
- **DELETE**: `docs/tuning/html-reports/README.md` if no actual HTML reports exist (verify; folder may be a stub).

**Result:** Folder shrinks from ~1.1 MB to ~150 KB. Synthesis report carries the conclusion; configs preserved for reproducibility.

#### 2.2 Fine-tuning experiments (Mission 9 — "data-limited at 1.3K")

**Current footprint:** `docs/finetuning/` = 5 .md files (1,118 lines), 13 PNG plots, 2 experiment subdirs (just `config.json` each), 1 docx, 1 pdf, 1 docx report, 1 markdown comparison, 1 csv, 1 csv. Total ~3 MB.

**Deck claim** (Slide 75): A and B both data-limited at 1.3K segs; both *worse than baseline* (IS 2.487 → 2.312 / 2.023). One bullet in body, full failure analysis in speaker notes.

**Action:**
- **KEEP** (1-page synthesis): `docs/finetuning/training-research-notes.md` (419 lines — this *is* the lessons-learned doc; update header to "FINAL: data ceiling, not model capacity").
- **KEEP** (2 figures): `FT_03_overfitting_gap.png` (the load-bearing visual; train-vs-val divergence) and `FT_11_clean_summary.png` (single-image dashboard).
- **KEEP** (one comparison table): `docs/finetuning/experiments/finetune_comparison.csv`.
- **KEEP** (the LLM-judge eval, since deck claims +0pp from FT): `docs/finetuning/llm_judge/finetune_llm_judge_comparison.md` + `.csv`.
- **DELETE**: `report_6_finetuning_analysis.{md,docx,pdf}` (365 lines + dual-format) — superseded by `training-research-notes.md`. Keep one summary in the research-overview, retire the formal "Report 6".
- **DELETE**: `checkpoint_correlation_report.md` + `checkpoint_correlation.csv` — internal diagnostic, conclusion absorbed into research notes ("validation accuracy doesn't predict IS").
- **DELETE**: 11 of 13 PNG plots — keep only the 2 above. The detailed loss curves (FT_01, FT_02, FT_04–10, FT_11a, FT_11b) tell the same overfitting story as FT_03 + FT_11.
- **DELETE**: `docs/finetuning/experiments/comparison_report.{md,docx}` — 113 lines; replaced by the CSV.
- **PRESERVE in `_archive/`**: `report_6_finetuning_analysis.pdf` only (the published version).

**Result:** Folder shrinks from ~3 MB / 5 docs to ~800 KB / 2 docs + 2 figures. Single source of truth: `training-research-notes.md`.

#### 2.3 LRS3 decode experiment (one-off measurement)

**Current footprint:** `docs/evaluation/lrs3_decode_experiment.md` (217 lines).

**Deck claim** (Slide 10 footer + speaker notes): "LRS3 reproduction reaches 32% WER — pretrain split differences." That is the only deck-facing fact from this experiment.

**Action:**
- **REWRITE-AS-1-PAGER**: collapse to 30–40 lines: (a) what was decoded, (b) WER 32%, (c) the 6 IS components measured (used by `generate_dual_radar.py`), (d) link to dual-radar plot. Drop methodology prose.
- The full doc is fine to leave as-is if no one reads it; high priority to update only the headline.

---

### Wave 3 — Redundancy collapse (~30 min, save ~30 files)

#### 3.1 PPTX visual audit / fix files (16 files, ~140 KB of md)

**The redundancy:** Every audit run produced a `pptx_visual_audit_<round>.{md,json}` and a `pptx_visual_fix_<round>.md`. Each round is a snapshot of the deck-at-time-T. Once a later round supersedes it, prior rounds add nothing.

| File | Date | Status |
|---|---|---|
| `pptx_visual_audit_pass1.{md,json}` | May 7 11:30 | ARCHIVE |
| `pptx_visual_audit_pass2.{md,json}` | May 7 11:50 | **KEEP — latest** |
| `pptx_visual_audit_round2..6.{md,json}` | May 7 01:03–10:34 | ARCHIVE (all 5 rounds) |
| `pptx_visual_audit.{md,json}` | (initial) | ARCHIVE |
| `pptx_visual_audit_after_fixes.{md,json}` | May 7 00:27 | ARCHIVE |
| `pptx_visual_audit_after_script_fix.{md,json}` | May 7 00:36 | ARCHIVE |
| `pptx_visual_audit_after_amosi.{md,json}` + `_diff.md` | May 6 23:49 | ARCHIVE |
| `pptx_visual_fix_pass1.md` | May 7 11:30 | ARCHIVE |
| `pptx_visual_fix_pass2.md` | May 7 11:50 | **KEEP — latest** |
| `pptx_visual_fix_round2..6.md` | May 7 01:03–10:34 | ARCHIVE (all 5 rounds) |
| `pptx_visual_fix_after_fixes.md` | May 7 00:27 | ARCHIVE |

**Action:**
- **KEEP**: `pptx_visual_audit_pass2.{md,json}` + `pptx_visual_fix_pass2.md` (latest run).
- **MOVE TO `docs/evaluation/_archive/pptx_audit_history/`**: the other 14 audit md/json + 6 fix md.
- **KEEP** the audit script `scripts/audit_pptx_visual_structure.py` and `scripts/audit_pptx_text_render.py` — those are tools, not artifacts.

#### 3.2 PPTX number/fix-manifest files (5 files, ~3.8 KB)

| File | Status |
|---|---|
| `pptx_number_audit.{csv,md}` | ARCHIVE — superseded by after_amosi_number_consistency |
| `pptx_slides_to_update.md` | ARCHIVE — sweep complete (all done per remarks log) |
| `pptx_fix_manifest.md` (1,807 lines!) | ARCHIVE — pre-AFTER_AMOSI fixes, complete |
| `pptx_fix_manifest_after_amosi.md` (717 lines) | ARCHIVE — fixes done |
| `pptx_text_render_audit.json` | ARCHIVE — text-render audit complete |

**Action:** Move all 5 to `docs/evaluation/_archive/pptx_audit_history/`.

#### 3.3 After-Amosi audit suite (13 files, ~4.5K lines)

The Mar 6 → May 6 audit produced 13 sibling files. Most have done their job and only need to be retained as historical record.

| File | Status |
|---|---|
| `after_amosi_audit.{md,json}` | **KEEP — canonical numbers source** |
| `after_amosi_number_consistency.{md,csv}` | KEEP — cross-doc matrix; useful for next audit |
| `after_amosi_logic_audit.md` + `after_amosi_logic_fixes.md` | ARCHIVE — fixes done |
| `after_amosi_narrative_audit.md` + `after_amosi_narrative_actions.md` | ARCHIVE — actions done |
| `after_amosi_asset_integrity.md` + `after_amosi_asset_fixes.md` + `after_amosi_asset_inventory.csv` | ARCHIVE — fixes done |
| `after_amosi_fix_manifest.md` + `after_amosi_number_fixes.md` | ARCHIVE — fixes done |
| `docs/changelog/after_amosi_audit.md` (56 lines, summary subset of evaluation/after_amosi_audit.md) | **DELETE** — duplicate; keep only the 307-line evaluation/ version |

**Action:** Move 8 files to `docs/evaluation/_archive/after_amosi_history/`. Delete `docs/changelog/after_amosi_audit.md`.

#### 3.4 Dual-format docx/md duplicates (12 files)

For every research report there's an md, a docx, and sometimes a pdf. The deck story is now the canonical narrative — most reports are reference-only, so dual format adds no value past the publication snapshot.

| Report | md | docx | pdf | Status |
|---|---|---|---|---|
| Report 1 (Executive) | docs/evaluation/report_1_executive_assessment.md (HISTORICAL — supersededl 860-seg) | .docx | .pdf | KEEP md (with HISTORICAL header it has), DELETE .docx (duplicate) — **but KEEP .pdf as published version** |
| Report 2 (Tuning) | docs/tuning/report_2_hyperparameter_tuning.md | docs/tuning/report_2_*.docx + tuning-experiments.docx + metrics-explainer.docx | (none in docs/) | KEEP md only; .docx in `presentation_materials_20260224/04_reports_docx/` is the published version |
| Report 3 (Prompts) | docs/prompts/report_3_*.md | .docx | (PDF in 04_reports_docx) | KEEP md; .docx local copy in docs/prompts/ is duplicate of 04_reports_docx/ |
| Report 4 (Confidence) | docs/confidence/report_4_*.md | .docx | (PDF in 04_reports_docx) | Same |
| Report 5 (Beam) | docs/beam-search/report_5_*.md | .docx | (PDF in 04) | Same |
| Report 6 (Finetune) | docs/finetuning/report_6_*.md (DELETED in Wave 2) | .docx (DELETED in Wave 2) | .pdf (KEEP archived) | per Wave 2 |
| `docs/evaluation/intelligibility_methodology.docx` | (md exists) | KEEP | — | KEEP both — methodology is canonical |
| `docs/evaluation/baseline_vs_J_analysis.docx` | (no md sibling — has md `baseline_vs_J_vs_C_intelligibility.md`) | KEEP | — | KEEP |
| `docs/evaluation/baseline_vs_J_vs_C_intelligibility.docx` | (md sibling) | DELETE — duplicate | — | |
| `docs/evaluation/is_correlation_analysis.docx` | (md sibling) | DELETE — duplicate | — | |
| `docs/evaluation/llm_upgrade_analysis.docx` | (md sibling) | DELETE — duplicate | — | |
| `docs/evaluation/research-journal.docx` | (no md sibling — generated via generate_research_journal.py) | KEEP | — | KEEP — reference doc |
| `docs/evaluation/project-summary.docx` | (no md sibling) | KEEP — published | — | KEEP |
| `docs/evaluation/llm_judge/disagreement_analysis.docx` | (no md sibling) | KEEP — published | — | KEEP |
| `docs/evaluation/llm_salvage/llm_salvage_analysis.docx` | (md sibling) | DELETE — duplicate | — | |
| `docs/evaluation/intelligibility/intelligibility_report.docx` | (no md sibling) | KEEP — published | — | |
| `docs/finetuning/experiments/comparison_report.docx` | (md DELETED in Wave 2) | DELETE | — | |

**Action:** Delete 5 duplicate `.docx` files (the ones with md siblings + dual content). Keep PDFs as published snapshots.

#### 3.5 Reports md folder duplication

`presentation_materials_20260224/03_reports_md/supplementary/` contains md copies of Reports 1–6 plus 3 analysis md files. These shadow `docs/{evaluation,tuning,confidence,prompts,finetuning,beam-search}/report_N_*.md`.

**Action:**
- **KEEP** these as the "published bundle" delivered to The Orchard. Add a 2-line README at `03_reports_md/supplementary/README.md` saying "frozen snapshot at deck delivery; canonical living docs at `docs/<topic>/report_N_*.md`".
- Do NOT delete — they're part of the deliverable bundle.
- Verify they're consistent with current md (likely diverged after Wave 1 number updates — that's fine; they are the snapshot).

#### 3.6 nbest v1 batches (1.7 MB redundant batch files)

`docs/evaluation/llm_judge_nbest/batches_v1/` (1.7 MB) and `judgments_v1/` (244 KB) — the v1 prompt run was archived in MEMORY as "CONTAMINATED, archived; do not use".

**Action:**
- **KEEP**: `auto_judgments_v1.csv` and `batch_index_v1.json` as evidence of the contaminated run.
- **DELETE**: `batches_v1/` (60 batch txt files) and `judgments_v1/` (per-batch JSON). The contamination conclusion is documented; raw batches are reproducible from prepare_nbest_judge_batches.py.

**Result:** Save ~2 MB. Conclusion preserved in summary CSV.

#### 3.7 Client framing duplicate

`docs/CLIENT_MEETING_FRAMING.md` and `docs/CLIENT_MEETING_FRAMING_v2.md` — v1 superseded by v2.

**Action:** Move v1 to `_archive/`; rename v2 → `CLIENT_MEETING_FRAMING.md`.

---

### Wave 4 — Audit-output ephemera archive (~10 min)

Already covered by Wave 3 §3.1–3.3 above. Net effect:

- Create `docs/evaluation/_archive/pptx_audit_history/` and move 27 files.
- Create `docs/evaluation/_archive/after_amosi_history/` and move 8 files.
- Net: ~35 files moved, 0 deleted, 4 retained as canonical.

---

### Wave 5 — Historical archive (~15 min)

Pre-MBR, pre-current-narrative documents that are still useful as record but should not be in the live tree.

| File | Why archive |
|---|---|
| `docs/sessions/SESSION_SUMMARY_20260202.md` | February session record; pre-Mission-1 refactor. Move to `docs/_archive/sessions/`. |
| `docs/sessions/FINAL_SUMMARY.md` | Old "final" summary, now superseded. Archive. |
| `docs/sessions/TEST_RESULTS_SUMMARY.md` | Test summary from refactor; tests live in `lib/test_all_modules.sh`. Archive. |
| `docs/archived/MODULE_TEST_RESULTS.md` | Already in archived/. KEEP location. |
| `docs/archived/PREPROCESSING_ONLY_FIX_SUMMARY.md` | Already in archived/. KEEP location. |
| `docs/changelog/MISSION3_MAX_LEN_FIX.md` | Old mission-3 fix doc. Move to `_archive/changelog/`. |
| `docs/changelog/PATH_CORRECTION_FIX.md` | Old path-correction fix. Archive. |
| `docs/changelog/SEGMENTED_VIDEO_NAMING_FIX.md` | Old fix. Archive. |
| `docs/changelog/COMPLETE_CHANGELOG.md` | Older changelog; verify whether after_amosi changes already integrated. Likely keep. |
| `docs/changelog/FIX_INVENTORY.md` | Inventory of fixes; keep until next major milestone. |
| `docs/evaluation/report_1_executive_assessment.{md,docx,pdf}` | Already labeled HISTORICAL header. Move all 3 to `docs/_archive/reports/`. The current "executive assessment" role is filled by `for_orchard_research_overview.md`. |

---

## Per-directory action table (by directory; uniform actions)

| Directory | Total files | KEEP | UPDATE | DELETE | ARCHIVE | Notes |
|---|---|---|---|---|---|---|
| `docs/` (top level: CLAUDE.md handled separately) | 4 | architecture, dev-guide, container-sync-changelog, CLIENT_MEETING_FRAMING_v2 | — | CLIENT_MEETING_FRAMING.md (v1) | — | Rename v2→base after delete |
| `docs/_research-tools/generators/` | 73 | All | — | — | — | These are the source of numbers; auditing them needs separate Mission. STYLE_GUIDE.md is AUTHORITATIVE. |
| `docs/_research-tools/scripts/` | ~10 | All | — | — | — | Active research scripts |
| `docs/_research-tools/data/` (decode_dataset, subset_data) | 11 | All | — | — | — | ~268 KB, reproducible inputs |
| `docs/_research-tools/calibration/` | 1 | calibration.json | — | — | — | Active |
| `docs/_research-tools/assets/` | 3 | logo.png, peacock.{jpg,png} | — | — | — | Branding |
| `docs/archived/` | 2 | All | — | — | — | Already archived |
| `docs/backlog/` | 2 | mission-backlog.md, cleanup-log.md | — | — | — | AUTHORITATIVE |
| `docs/beam-search/` | 3 | n_best_implementation.md (AUTHORITATIVE), report_5_*.md, report_5_*.docx (delete docx as Wave 3.4 says? — actually KEEP since published) | — | — | — | n_best_implementation MEMORY says "shipped final"; sync with deck §4 |
| `docs/branding/` | (logo files) | All | — | — | — | Branding |
| `docs/changelog/` | 6 | COMPLETE_CHANGELOG, FIX_INVENTORY | — | after_amosi_audit.md (dup) | 3 fix docs | See Wave 3.3 + Wave 5 |
| `docs/confidence/` | 11 | report_4 (AUTHORITATIVE), threshold_design (AUTH), band_reliability_by_niv (AUTH), client_trust_calibration (AUTH), llama2_*_review, lessons_learned_band_rule_v2 (notes), confidence_followups, confidence_full_analysis (UPDATE line 11), confidence_shape*, threshold_design, word_confidence_distribution, band_reliability_rollout_plan | confidence_full_analysis.md | — | — | All ~current; one number update |
| `docs/evaluation/` (top-level files only) | ~70 md/json/csv/docx | per Wave 1 + Wave 3 + Wave 5 | 14 files | 5 docx + 1 changelog dup | ~35 audit/manifest files | See Wave 1, 3.1, 3.2, 3.3, 3.4 |
| `docs/evaluation/intelligibility/` | 4 | intelligibility_scores.{csv,html}, intelligibility_report.docx | intelligibility_summary.json (regen) | — | — | Numbers stale; regen from latest |
| `docs/evaluation/llm_judge/` (top + subdirs) | many | All in main folder; KEEP llm_judge_analysis.md, llm_judge_results.csv, summary.json, examples/, batches/, judgments/ | — | — | — | AUTHORITATIVE — Opus blind-judge gold standard |
| `docs/evaluation/llm_judge/context_eval/` | All | All | — | — | — | AUTHORITATIVE |
| `docs/evaluation/llm_judge_nbest/` | All | KEEP main run; figures/ | — | batches_v1/, judgments_v1/ (1.9 MB) | — | Wave 3.6 |
| `docs/evaluation/llm_salvage/` | 4 | llm_salvage_analysis.md, llm_salvage_segments.json, salvage_example_gallery.md | — | llm_salvage_analysis.docx (dup) | — | Wave 3.4 |
| `docs/evaluation/plots/` | 30 PNGs | Most KEEP (used by reports) | — | — | — | Verify usage; some duplicates with 01_plots_for_slides/ |
| `docs/features/` | ~10 | All current | — | — | — | All documenting shipped features |
| `docs/finetuning/` | per Wave 2.2 | training-research-notes.md (AUTH), llm_judge/ subdir | — | report_6 docx/md, checkpoint_correlation*, comparison_report.{md,docx}, 11 of 13 PNGs | report_6.pdf | Wave 2.2 — major reduction |
| `docs/finetuning/experiments/finetune_{A_r16,B_r64}/` | 1 config.json each | KEEP both configs | — | — | — | Reproducibility |
| `docs/guides/` | ~17 | All current | — | — | — | Operations docs; distinct from research |
| `docs/licenses/` | (license files) | All | — | — | — | Legal |
| `docs/paper/` | 3 | arabic-vsp-adaptation.md, presentation-remarks-log.md (AUTH per CLAUDE.md), beamer/ | — | — | — | All current |
| `docs/prompts/` | 3 | report_3 md, topic_label_experiment.md | — | report_3.docx (dup) | — | Wave 3.4 |
| `docs/sessions/` | 3 | — | — | — | All 3 | Wave 5 |
| `docs/tuning/` | per Wave 2.1 | report_2_*.md, html-reports/, interesting-examples/ | — | exp_{A..M}/decode_output/ + report/ subdirs (~1 MB) | — | Wave 2.1 — keep configs only |

---

## Cross-doc consistency rules (post-cleanup invariants)

After the cleanup, any new edit MUST satisfy:

1. **IS-mean rule.** Every IS-mean number is either **2.547** (MBR-default) or labeled "(top-1 baseline 2.532)". Never bare 2.52 or 2.53.
2. **NIV-Y rule.** Every NIV-Y count is either **358 (23.9%)** or labeled "(top-1 359, 24.0%)". The pre-MBR `346 / 23.1%` is dead.
3. **NIV-Y+P rule.** Every NIV-Y+P count is either **927 (61.9%)** or labeled "(top-1 923, 61.7%)". The pre-MBR `922 / 61.6%` is dead.
4. **WER rule.** Mean WER is **63.8%** (production) or labeled "(top-1 baseline 64.05%, displayed 64.1%)". When the deck says 64.1%, that's the *user-facing* round figure of top-1; the MBR-default is the *production* figure.
5. **κ pair rule.** Whenever κ is quoted, both top-1 and MBR values should be shown OR a single value labeled. Top-1: 0.707 / 0.816 (Y / Y+P); MBR: 0.693 / 0.796.
6. **Cross-config r=0.925 caveat.** Whenever cited, must include "across 16 decode-parameter configs (top-1 only — n-best aggregation NOT in the 16)".
7. **Trust-gate ops.** 65.2% recall / 5.6% FPR: always note "computed on top-1 per_segment confidence — display-method swap to MBR does not change these".
8. **PCA dimensions.** **2 PCs (Kaiser)** is canonical. Old "3 dimensions" is dead — present only in 4 files for *historical* context (after_amosi audit/fix files), already in archive list.
9. **Hallucination rate.** 20.5% (top-1) / 20.7% (MBR) — both are fine; 20.5% is the deck-facing "current" number for backward compat.
10. **NEA F1 / WWER.** 38.94% / 60.51% — top-1 only; not recomputed per method. State this explicitly when referenced.

---

## Conceptual narrative gaps the docs should close

Per `for_orchard_research_overview.md` items 30–40, the deck makes claims that don't have a backing doc. Fixes (none require new long docs):

| Gap | Where to add (existing doc) |
|---|---|
| **C5 — Closed-form IS formula.** "IS = 5 × (0.25·Sem + 0.15·(Phon + InvWER + InvWWER + NEA + LR))" | `docs/evaluation/intelligibility_methodology.md` Section 4 already has this — verify and pin location for slide reference. |
| **C10 — McNemar contingency cells.** | `docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md` — add a §X "McNemar contingencies" with the (b, c) cells per method. |
| **C14 — F1-max sweep methodology** for T_safe = 0.82. | `docs/confidence/threshold_design.md` should already cover; verify it explicitly says "argmax F1 on NIV-Y class via mean_prob". |
| **C15 + C16 — Joint band rule construction.** | `docs/confidence/band_reliability_by_niv.md` is the correct home; add 2 lines defining the (conf, agreement) joint sweep methodology. |
| **C18 — MBR posterior per word definition.** | `docs/beam-search/n_best_implementation.md` — add a 1-line explanation of what `mbr_posterior` outputs per word. |
| **C21 — r=0.925 cross-config caveat.** | Already addressed in Wave 1 `is_cross_config_validation.md`. |
| **C22 — Phase IS deltas methodology.** | `docs/evaluation/llm_upgrade_analysis.md` Part 3 — already references signal-distribution-based derivation per remarks log #256. Verify and pin. |
| **Limitations callout (item 39).** | `docs/evaluation/for_orchard_research_overview.md` already covers; this doc IS the limitations register. No new file needed. |
| **A4/A5 Salvage discoverability.** | `docs/evaluation/llm_salvage/salvage_example_gallery.md` is fine — verify links from analysis md. |

**Net adds:** ~10 paragraph-level additions to existing AUTHORITATIVE docs. Zero new files.

---

## What NOT to do

- **Do not regenerate the Reports 1–6 docx/pdf** as part of this cleanup. The published bundle (`presentation_materials_20260224/04_reports_docx/`) is a frozen snapshot for The Orchard. Updating the docx pipeline is a separate, larger Mission.
- **Do not modify generator Python files** in this pass. Source-of-numbers regeneration is its own task; this plan touches only output md/json/docx/png.
- **Do not delete `presentation_materials_20260224/01_plots_for_slides/_archive_march2026/`**. The 7 PNGs there are the pre-regeneration visuals; deck builders may reference. Already correctly archived.
- **Do not consolidate confidence docs** — even though they overlap, each `docs/confidence/*.md` covers a different operating point (band rule, trust gate, threshold design, NIV stratification). Each is referenced from a different deck slide. Consolidation would lose granularity.
- **Do not remove `docs/evaluation/llm_judge/examples/` markdown files** — these are referenced by judge-analysis.md and provide concrete pair examples.
- **Do not touch container-sync-changelog.md** — that's the Linux-container deployment register, separate from research-narrative sync.

---

## Execution checklist (operator-facing)

- [ ] **Wave 1**: 14 files, ~58 line edits (use the find/replace pairs above). Verify with `grep -n "346\|2\.52\|39\.9%\|40\.1%" docs/evaluation/*.md` returns zero hits in non-archived docs.
- [ ] **Wave 2.1**: `rm -rf docs/tuning/experiments/exp_{A..M}/{decode_output,report}` (preserve `config.json`).
- [ ] **Wave 2.2**: Delete `docs/finetuning/{report_6_finetuning_analysis.{md,docx,pdf if not archived},checkpoint_correlation_report.md,checkpoint_correlation.csv}`. Delete 11 of 13 PNGs in `docs/finetuning/plots/`. Delete `docs/finetuning/experiments/comparison_report.{md,docx}`.
- [ ] **Wave 2.3**: Trim `docs/evaluation/lrs3_decode_experiment.md` to ~40 lines.
- [ ] **Wave 3.1**: `mkdir docs/evaluation/_archive/pptx_audit_history && git mv` 27 audit/fix files.
- [ ] **Wave 3.2**: Move 5 pptx-fix-manifest files into the same `_archive/`.
- [ ] **Wave 3.3**: Delete `docs/changelog/after_amosi_audit.md`. `mkdir docs/evaluation/_archive/after_amosi_history && git mv` 8 audit-suite files.
- [ ] **Wave 3.4**: Delete 5 duplicate .docx files.
- [ ] **Wave 3.5**: Add `presentation_materials_20260224/03_reports_md/supplementary/README.md` (2 lines).
- [ ] **Wave 3.6**: `rm -rf docs/evaluation/llm_judge_nbest/{batches_v1,judgments_v1}`.
- [ ] **Wave 3.7**: `mv docs/CLIENT_MEETING_FRAMING.md docs/_archive/CLIENT_MEETING_FRAMING_v1.md && mv docs/CLIENT_MEETING_FRAMING_v2.md docs/CLIENT_MEETING_FRAMING.md`.
- [ ] **Wave 5**: `mkdir -p docs/_archive/{sessions,changelog,reports} && git mv` ~10 historical files.
- [ ] **Verify invariants**: run `grep -rn "346 (23.1%)\|922 (61.6%)\|3 dimensions\|3 PCA" docs/` — expect zero hits outside `_archive/`.
- [ ] **Commit**: One commit per Wave for clean revert capability.

---

## Source citations

- **Deck**: `presentation_materials_20260224/Argos_VSP_For_Orchard_May2026.pptx` (89 slides, 80 visible + 9 hidden)
- **Canonical numbers**: `docs/evaluation/after_amosi_audit.md` + `after_amosi_audit.json`
- **Pacing/structural review**: `docs/evaluation/for_orchard_research_overview.md`
- **Per-file old-number map**: `grep -n "346\|2\.52\|61\.6%\|39\.9%\|40\.1%" docs/evaluation/*.md docs/confidence/*.md docs/finetuning/*.md docs/beam-search/*.md docs/prompts/*.md`
- **MEMORY canonical numbers**: `~/.claude/projects/-home-ubuntu/memory/MEMORY.md`
