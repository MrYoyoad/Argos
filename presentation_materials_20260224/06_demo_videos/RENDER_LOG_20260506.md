# Demo Video Re-Render Log — 2026-05-06

**Goal:** refresh the 8 academic-deck demo clips with per-word coloring under the
**May 2 2026 agreement-aware band rule** (green = `top1_conf >= 0.95 AND beam_agreement >= 0.80`,
yellow = `>= 0.65 AND >= 0.50`, red otherwise; numbers capped at yellow) and the
production **BLUE / ORANGE / PURPLE** palette (Trust / Salvage / Strip), plus a
tier badge overlay (TRUST / INSPECT / DON'T BELIEVE) at the top-right.

**Renderer:** `VSP-LLM/scripts/make_burn.py` with `--word_confidence` pointing
at the per-segment sidecar from each clip's source decode run.
**Driver script:** `/tmp/burn_workdir/run_burns.py` (filters word_confidence.json
to the single segment, builds a one-record hypo JSON, symlinks the source MP4 as
`{utt_id}.mp4` so make_burn.py's Strategy 1.5 picks it up).

**Backups:** all overwritten files are preserved under
`./_archive_pre_may6/` and `./_archive_pre_may6/realtalk/`.

## Result table

| # | Key | Source segment ID | Source MP4 | Decode artifacts | Output filename | Badge | mean_prob | Size | Duration | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `obama_perfect` | `050111_OsamaBinLadenStatement_HD_14_004195_004555` | `_archive_pre_may6/050111_OsamaBinLadenStatement_HD_14_004195_004555.mp4` | `flat_runs_archive/20260430_234843/client_outputs/report/word_confidence.json` (conf-only fallback — no n-best agreement available for this run) | `050111_OsamaBinLadenStatement_HD_14_004195_004555.mp4` | **TRUST** | 0.973 | 2.98 MB | 12.1 s | OK |
| 2 | `obama_partial` | `050111_OsamaBinLadenStatement_HD_31_009290_009650` | `_archive_pre_may6/050111_OsamaBinLadenStatement_HD_31_009290_009650.mp4` | same as #1 | `050111_OsamaBinLadenStatement_HD_31_009290_009650.mp4` | **TRUST** (spec wanted SALVAGE — see note A) | 0.920 | 2.98 MB | 12.1 s | OK |
| 3 | `obama_flagged` | `050111_OsamaBinLadenStatement_HD_05_001498_001858` | `_archive_pre_may6/050111_OsamaBinLadenStatement_HD_05_001498_001858.mp4` | same as #1 | `050111_OsamaBinLadenStatement_HD_05_001498_001858.mp4` | **INSPECT** (spec wanted STRIP — see note A) | 0.799 | 2.40 MB | 12.0 s | OK |
| 4 | `judge_entity` | `4D634qUi2BI_0__93a9f2b4_00_000000_000122` | `datasets/english_data_2025_11_20/flat_all/4D634qUi2BI_0__93a9f2b4.mp4` | `english_full_nbest_eval/word_confidence_v2.json` + `decode_output/hypo-172610.json` (full agreement-aware v2 sidecar; aggregated.json available) | `4D634qUi2BI_0__93a9f2b4_with_hyp.mp4` | **DON'T BELIEVE** (spec wanted SALVAGE — see note B) | 0.624 | 1.31 MB | 4.9 s | OK |
| 5 | `judge_router` | `c6eBrYor21I_10__70697c08_00_000000_000359` | `datasets/english_data_2025_11_20/flat_all/c6eBrYor21I_10__70697c08.mp4` | same as #4 | `c6eBrYor21I_10__70697c08_Part1_with_hyp.mp4` | **INSPECT** | 0.687 | 2.42 MB | 12.7 s | OK |
| 6 | `realtalk_trust` | `12XM5_1lyrc__p0__win0240_00_000000_000300` | `vsp_input_realtalk_demo/candidate_clips/12XM5_1lyrc__p0__win0240.mp4` | `flat_runs_archive/20260503_000805/client_outputs/report/word_confidence.json` (full agreement-aware sidecar; nbest + aggregated available in same dir) | `realtalk/12XM5_1lyrc__p0__win0240__burned.mp4` | **TRUST** | 0.900 | 0.80 MB | 12.0 s | OK |
| 7 | `realtalk_salvage` | `5M9kx6mrXrA__p0__win0070_00_000000_000300` | `vsp_input_realtalk_demo/candidate_clips/5M9kx6mrXrA__p0__win0070.mp4` | same as #6 | `realtalk/5M9kx6mrXrA__p0__win0070__burned.mp4` | **INSPECT** | 0.673 | 0.77 MB | 12.0 s | OK (clip swap — see note C) |
| 8 | `realtalk_strip` | `MkV7LSXtzkQ__p1__win0560_00_000000_000300` | `vsp_input_realtalk_demo/candidate_clips/MkV7LSXtzkQ__p1__win0560.mp4` | same as #6 | `realtalk/MkV7LSXtzkQ__p1__win0560__burned.mp4` | **DON'T BELIEVE** | 0.429 | 0.86 MB | 12.0 s | OK |

All 8 clips rendered; none are blocked.

## Notes / discrepancies vs the spec

### Note A — Obama segments cannot reach the SALVAGE / STRIP badges the spec asked for

The Obama bin Laden announcement clips were decoded **before** `VSP_NBEST=1`
became standard, so no per-token beam-agreement scores exist for them. With
agreement absent, `compute_word_confidence.classify_joint` falls back to the
old conf-only `classify` (CONF_HIGH=0.85) — exactly as documented in the
"agreement-aware bands" memory note ("Past videos without `VSP_NBEST=1`:
silent fallback to conf-only; re-decode required to upgrade").

Per the task constraint *"do NOT re-decode (that's hours on GPU)"*, we accepted
the conf-only tier each segment lands at:

| Segment | mean_word_prob | Tier (conf-only) | Tier the deck script previously assigned |
|---|---|---|---|
| seg 14 | 0.973 | **TRUST**  | TRUST  ✓ |
| seg 31 | 0.920 | **TRUST**  | SALVAGE  ✗ — actual data is too clean |
| seg 05 | 0.799 | **INSPECT/Salvage** | STRIP  ✗ — lowest-conf Obama segment in the dataset, but still above the 0.65 STRIP cutoff |

I scanned all 33 Obama segments in the available `word_confidence.json` — none
hit STRIP under the conf-only fallback (lowest mean_word_prob is 0.799). Without
n-best re-decode of the Obama corpus there is no honest STRIP-tier Obama clip to
serve. The current `obama_flagged` (seg 05) is the lowest-conf Obama segment in
the run and is the closest available match for the "hallucination caught" slide
narrative.

**Recommendation for the deck:** either (a) re-frame the Obama-flagged slide as
"SALVAGE / lowest-confidence Obama segment" rather than STRIP, or (b) replace
the source video for `obama_flagged` with one of the clean STRIP exemplars from
the wider corpus (`MkV7LSXtzkQ` / `v43L_FaHz28` already painted purple in the
realtalk set). I did not change this here because the existing deck slide
narrative is explicitly Obama-themed ("E11 Strip — hallucination flagged
(Obama)").

### Note B — `judge_entity` is now STRIP, not SALVAGE

Under the new agreement-aware rule (`top1_conf >= 0.95 AND beam_agreement >= 0.80`
for green), the segment's mean per-word prob drops to 0.624, which is below the
0.65 STRIP cutoff. Per-word colors: 6 of 11 are red (low), 3 yellow (med), only
2 green ("research", "firm" — the safe filler tokens). The "rogers / pv / will"
content tokens all land red. This is the correct production behavior and
arguably *strengthens* the named-entity-swap narrative (the model's own
confidence layer flags the entity confusion automatically), but it does change
the slide framing from "SALVAGE — partial recovery" to "STRIP — entity swap
caught."

**Recommendation:** retitle the slide to lean into the "automatic entity-swap
flagging" angle rather than re-pick the clip — the bernreuter / rogers /
PV-installations example is the textbook entity-swap demo.

### Note C — `realtalk_salvage` clip swap

Previous: `7LcWBEVtGwA__p1__win0520_00_000000_000300` (mean_prob 0.847).
Under the joint conf+agreement rule that segment lands at **TRUST tier** (mean
just over the 0.82 TRUST threshold), which contradicted the slide's "salvage /
partial recovery" framing. The deck would have shown a TRUST badge on what is
labeled the SALVAGE example.

Switched to: `5M9kx6mrXrA__p0__win0070_00_000000_000300` ("Long Island visemic
confusion" — slot 7 in `realtalk_demo_picks.md`, IS=2.80, WER=44%, mean_prob
0.673). This produces a genuine **INSPECT** badge, mostly orange/red per-word
colors, and matches the deck's slide narrative.

`config.py` IMG dict updated: `realtalk_salvage` repointed from
`7LcWBEVtGwA__p1__win0520__burned.mp4` to `5M9kx6mrXrA__p0__win0070__burned.mp4`.
The new burned MP4 was placed alongside the existing realtalk burns.

## IMG dict diff (`docs/_research-tools/generators/presentation/config.py`)

Only `realtalk_salvage` was repointed. Diff:

```diff
     "realtalk_trust":   VIDEOS / "realtalk" / "12XM5_1lyrc__p0__win0240__burned.mp4",
-    "realtalk_salvage": VIDEOS / "realtalk" / "7LcWBEVtGwA__p1__win0520__burned.mp4",
+    # realtalk_salvage repointed 2026-05-06: previous 7LcWBEVtGwA__p1__win0520
+    # had mean_prob=0.847 — just above the 0.82 TRUST threshold, so the new
+    # agreement-aware rule painted it as TRUST tier (badge=TRUST), which
+    # contradicted the slide's "salvage / partial recovery" narrative.
+    # Switched to slot-7 from realtalk_demo_picks.md ("Long Island" visemic-
+    # confusion segment, mean_prob=0.673 → genuine SALVAGE/INSPECT badge,
+    # IS=2.80, WER=44%).
+    "realtalk_salvage": VIDEOS / "realtalk" / "5M9kx6mrXrA__p0__win0070__burned.mp4",
     "realtalk_strip":   VIDEOS / "realtalk" / "MkV7LSXtzkQ__p1__win0560__burned.mp4",
```

No new keys added. All other keys (`obama_perfect`, `obama_partial`,
`obama_flagged`, `judge_entity`, `judge_router`, `realtalk_trust`,
`realtalk_strip`) already pointed at the correct filenames; their MP4 contents
were overwritten in-place so the deck picks up the new renders automatically.

## Verification

- All 8 output MP4s confirmed to exist in `06_demo_videos/` and play (ffprobe
  reports valid duration; sizes 0.77 – 2.98 MB, all well under the 15 MB limit).
- Spot-checked frames at t=2-6s for one TRUST, one INSPECT, and one DON'T-BELIEVE
  clip — confirmed:
    - Tier badge in top-right corner with correct color (blue / orange / purple)
    - Per-word colored hypothesis text in bottom black box
    - For STRIP-tier clips: per-word coloring is dropped (white text), and the
      DON'T BELIEVE badge alone signals unreliability — this matches
      `make_burn.py`'s documented behavior and the HTML report's "tier-first"
      design.

## Files touched

**New / overwritten:**
- `06_demo_videos/050111_OsamaBinLadenStatement_HD_14_004195_004555.mp4` (re-burned)
- `06_demo_videos/050111_OsamaBinLadenStatement_HD_31_009290_009650.mp4` (re-burned)
- `06_demo_videos/050111_OsamaBinLadenStatement_HD_05_001498_001858.mp4` (re-burned)
- `06_demo_videos/4D634qUi2BI_0__93a9f2b4_with_hyp.mp4` (re-burned)
- `06_demo_videos/c6eBrYor21I_10__70697c08_Part1_with_hyp.mp4` (re-burned)
- `06_demo_videos/realtalk/12XM5_1lyrc__p0__win0240__burned.mp4` (re-burned)
- `06_demo_videos/realtalk/5M9kx6mrXrA__p0__win0070__burned.mp4` (NEW; this is the new realtalk_salvage)
- `06_demo_videos/realtalk/MkV7LSXtzkQ__p1__win0560__burned.mp4` (re-burned)
- `docs/_research-tools/generators/presentation/config.py` (one repointed key)

**Backups:**
- `06_demo_videos/_archive_pre_may6/050111_OsamaBinLadenStatement_HD_05_001498_001858.mp4`
- `06_demo_videos/_archive_pre_may6/050111_OsamaBinLadenStatement_HD_14_004195_004555.mp4`
- `06_demo_videos/_archive_pre_may6/050111_OsamaBinLadenStatement_HD_19_005694_006053.mp4` (clean_obama19 — backed up but not re-burned, never had hyp overlay)
- `06_demo_videos/_archive_pre_may6/050111_OsamaBinLadenStatement_HD_31_009290_009650.mp4`
- `06_demo_videos/_archive_pre_may6/4D634qUi2BI_0__93a9f2b4_with_hyp.mp4`
- `06_demo_videos/_archive_pre_may6/c6eBrYor21I_10__70697c08_Part1_with_hyp.mp4`
- `06_demo_videos/_archive_pre_may6/realtalk/12XM5_1lyrc__p0__win0240__burned.mp4`
- `06_demo_videos/_archive_pre_may6/realtalk/7LcWBEVtGwA__p1__win0520__burned.mp4` (orphaned by clip swap; old realtalk_salvage)
- `06_demo_videos/_archive_pre_may6/realtalk/5M9kx6mrXrA__p0__win0070__burned.mp4` (prior copy of the clip we picked as new realtalk_salvage)
- `06_demo_videos/_archive_pre_may6/realtalk/MkV7LSXtzkQ__p1__win0560__burned.mp4`

**Driver / log:**
- `/tmp/burn_workdir/run_burns.py` (driver — keep around in case we need to re-render)
- `/tmp/burn_workdir/render_log.json` (machine-readable log)
- `/tmp/burn_workdir/preview_*.png` (spot-check frames — not deck assets)

---

# Demo Video Re-Render Log — 2026-05-07 (Round 2)

**Goal:** asset audit on `Argos_VSP_AFTER_AMOSI_May2026.pptx` flagged 8 of 15 video shapes as showing pre-May-6 plain captions (no tier badge, no per-word coloring). Slides 5, 20, 22, 23, 24, 63 (x3) play correctly but stylistically inconsistent with the badged renders on slides 19, 21, 64-68. This round re-renders those 8 clips with the same May-2 agreement-aware band rule and tier badge overlay used in the May-6 batch.

**Renderer:** `VSP-LLM/scripts/make_burn.py --word_confidence` (same as round 1).
**Driver:** `/tmp/burn_workdir/run_burns_round2.py` (imports helpers from `run_burns.py`).

**Decode artifacts for all 8 clips:** `english_full_nbest_eval/word_confidence_v2.json` (full agreement-aware v2 sidecar — joint conf+agreement band rule applies to every clip; no fallback was needed) plus `english_full_nbest_eval/decode_output/hypo-172610.json` for ref/hyp text.

**Source MP4s:** all 8 are AVSpeech segments under `datasets/english_data_2025_11_20/flat_all/`.

**Slide → media → utt_id mapping** (recovered by md5-hashing embedded `ppt/media/mediaN.mp4` against `06_demo_videos/`):

| Slide | media slot | IMG key (filename stem) | utt_id (segment ID) |
|------:|---|---|---|
| 5  | media1.mp4  | `IEa7qEkMvfQ_3__c5447488`  | `IEa7qEkMvfQ_3__c5447488_00_000000_000217` |
| 20 | media3.mp4  | `VfJ-6nQAmtk_22__4a7cbfd1` | `VfJ-6nQAmtk_22__4a7cbfd1_00_000000_000173` |
| 22 | media5.mp4  | `9HanJOCw2Sc_11__19c7ec4e` | `9HanJOCw2Sc_11__19c7ec4e_00_000000_000261` |
| 23 | media6.mp4  | `a2CS82VZyO4_7__a6316c95`  | `a2CS82VZyO4_7__a6316c95_00_000000_000097` |
| 24 | media7.mp4  | `tUcgHemnJiQ_0__2fc132c1`  | `tUcgHemnJiQ_0__2fc132c1_00_000000_000177` |
| 63 | media8.mp4  | `ktMebjnZiSE_3__ebdf1351`  | `ktMebjnZiSE_3__ebdf1351_00_000000_000359` |
| 63 | media9.mp4  | `2HddWQse8Mw_0__8ecb0409`  | `2HddWQse8Mw_0__8ecb0409_00_000000_000072` |
| 63 | media10.mp4 | `00MUdHQ7GGY_8__b1480c7a`  | `00MUdHQ7GGY_8__b1480c7a_00_000000_000194` |

## Result table (Round 2)

| # | Slide | IMG key (stem) | Output filename | Badge | mean_prob | Size | Duration | Status |
|---|---|---|---|---|---|---|---|---|
| 1 |  5 | `IEa7qEkMvfQ_3__c5447488`  | `IEa7qEkMvfQ_3__c5447488_with_hyp.mp4`  | **TRUST**         | 0.950 | 1.34 MB |  7.2 s | PASS |
| 2 | 20 | `VfJ-6nQAmtk_22__4a7cbfd1` | `VfJ-6nQAmtk_22__4a7cbfd1_with_hyp.mp4` | **INSPECT**       | 0.746 | 0.99 MB |  7.2 s | PASS |
| 3 | 22 | `9HanJOCw2Sc_11__19c7ec4e` | `9HanJOCw2Sc_11__19c7ec4e_with_hyp.mp4` | **INSPECT**       | 0.739 | 2.20 MB |  8.7 s | PASS |
| 4 | 23 | `a2CS82VZyO4_7__a6316c95`  | `a2CS82VZyO4_7__a6316c95_with_hyp.mp4`  | **DON'T BELIEVE** | 0.643 | 0.72 MB |  3.3 s | PASS |
| 5 | 24 | `tUcgHemnJiQ_0__2fc132c1`  | `tUcgHemnJiQ_0__2fc132c1_with_hyp.mp4`  | **INSPECT**       | 0.679 | 3.09 MB |  7.1 s | PASS |
| 6 | 63 | `ktMebjnZiSE_3__ebdf1351`  | `ktMebjnZiSE_3__ebdf1351_with_hyp.mp4`  | **TRUST**         | 0.822 | 2.53 MB | 13.5 s | PASS |
| 7 | 63 | `2HddWQse8Mw_0__8ecb0409`  | `2HddWQse8Mw_0__8ecb0409_with_hyp.mp4`  | **DON'T BELIEVE** | 0.602 | 0.44 MB |  3.0 s | PASS |
| 8 | 63 | `00MUdHQ7GGY_8__b1480c7a`  | `00MUdHQ7GGY_8__b1480c7a_with_hyp.mp4`  | **DON'T BELIEVE** | 0.468 | 1.30 MB |  6.5 s | PASS |

All 8 clips re-rendered successfully; no FALLBACK or SKIP. New durations match originals to within 0.05 s, confirming the same source segment was rendered.

## Verification (Round 2)

- All 8 outputs overwrite the originals in `06_demo_videos/` at the SAME filenames the deck's `IMG` dict references — no `presentation/config.py` or `slides_*.py` change required.
- Spot-checked frames at t=3 s for one TRUST (slide 5), one INSPECT (slide 20) and one DON'T-BELIEVE (slide 23) clip — confirmed:
    - Tier badge in top-right corner with correct color (blue / orange / purple)
    - Per-word coloring active for TRUST/INSPECT clips
    - For DON'T BELIEVE clip (slide 23, mean_prob=0.643 just below the 0.65 strip-coloring boundary): per-word coloring dropped, captions rendered white — the badge alone signals unreliability, matching `make_burn.py`'s documented strip-policy behavior.
- Preview PNGs: `/tmp/burn_workdir/preview_round2_slide05_TRUST.png`, `/tmp/burn_workdir/preview_round2_slide20_INSPECT.png`, `/tmp/burn_workdir/preview_round2_slide23_DONTBELIEVE.png`.

## Notes

- **No re-decode was performed.** Every flagged segment was already covered by `english_full_nbest_eval/word_confidence_v2.json`, so the joint conf+agreement rule applied to all 8 — no conf-only fallback like the Obama clips needed in round 1.
- ktMebjnZiSE has 2 segments in the v2 sidecar (`_00_000000_000359` and `_01_000299_000404`); the deck uses the longer one (~13.5 s duration matches `_00_000000_000359`). Verified by comparing pre-rebake duration (13.491 s) against the v2 segment lengths.
- `presentation/config.py` IMG dict was NOT modified — every IMG key already pointed at the correct filename and the new burns overwrote the existing files in place. Next deck-render will pick up the new badged videos automatically.

## Files touched (Round 2)

**New / overwritten** (in `06_demo_videos/`):
- `IEa7qEkMvfQ_3__c5447488_with_hyp.mp4`
- `VfJ-6nQAmtk_22__4a7cbfd1_with_hyp.mp4`
- `9HanJOCw2Sc_11__19c7ec4e_with_hyp.mp4`
- `a2CS82VZyO4_7__a6316c95_with_hyp.mp4`
- `tUcgHemnJiQ_0__2fc132c1_with_hyp.mp4`
- `ktMebjnZiSE_3__ebdf1351_with_hyp.mp4`
- `2HddWQse8Mw_0__8ecb0409_with_hyp.mp4`
- `00MUdHQ7GGY_8__b1480c7a_with_hyp.mp4`

**Backups** (in `06_demo_videos/_archive_pre_may6/`): same 8 filenames, copied 2026-05-07 prior to overwrite.

**Driver / log:**
- `/tmp/burn_workdir/run_burns_round2.py` (round-2 driver)
- `/tmp/burn_workdir/render_log_round2.json` (machine-readable log)
- `/tmp/burn_workdir/preview_round2_*.png` (spot-check frames)
