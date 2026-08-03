# Handoff: N-best homophene arbitration experiment (Egla-Kafe)

**From:** Cowork session on Yoad's machine (analysis of rendered deliverables only — no repo access)
**To:** Claude on the research machine (repo with `scripts/pipeline/*egla_kafe*`, `work/eval/`)
**Date:** 2026-07-15

## TL;DR
Post-hoc viseme snapping of "nonsense" spans was tested against an oracle domain phrase bank on
all 21 conversation videos. It is safe and mildly useful on Trust-tier footage (+8.2pp content-word
recall on img_6825, zero harmful substitutions across the 6 best videos) and useless-to-harmful on
weak footage. The main proposal for the research side: **stop reconstructing alternatives — harvest
the pre-MBR N-best that the decoder already generates and discards**, and arbitrate flagged spans
among those real candidates. No prompting changes.

## What was measured here (and its limits)
- Per-turn (said, read) pairs were extracted by **OCR of the burned-in subtitles** in
  `EglaKafe_full_deliverables/conversation_videos/*__said_vs_heard.mp4` (turn tables in
  `turns/*.json`, ~25-42 turns/video). OCR junk tokens inflate substitution counts — redo with
  real per-turn hyp/ref from `work/eval/` alignment artifacts before trusting exact numbers.
- Scoring proxy: per-turn content-word recall (stopword-filtered, fuzzy≥0.87). The doc Y+P
  calibration (MAE 7.6pp vs the context judge) is NOT well calibrated — treat all judge-proxy
  deltas as indicative. Recall numbers stand on their own.

## Findings
1. All 21 videos, oracle snapping (sim≥0.78 on viseme strings, nonsense-gated):
   mean judge-proxy delta +0.6pp; 5 improved / 1 regressed. Substitution quality ≈ 40% genuine
   fix / 30% lateral / 30% noise→plausible-wrong fabrication (fabrication only on weak footage).
2. Decent videos only (calibration-free recall):
   img_6825 39.2→47.4 (+8.2) · s1_tomer_yoad_1 34.1→38.5 · img_6824 41.5→43.5 ·
   s2_yoad_tomer_2 +0.8 · s2_tomer_ido_1 and s2_yoad_tal_1 unchanged.
   Substitutions: 18 good / 30 neutral / **0 harmful**. Gains track capture quality
   (Trust-tier enhancer, not a rescue tool).
3. Failure mode that caps post-hoc snapping: cross-word re-segmentation.
   "body knows this planet" should become "nobody notices planning" — word boundaries move,
   short-span replacement finds "buses / notices when" instead. A lattice/N-best has this for free.
4. Key context facts (from findings.md, confirmed here): green common nouns ~82% correct,
   entities 0%, numbers 73% but confident-wrong leaks; confidence well-ranked, optimistic in
   absolute terms (0.95 bucket → ~45% exact-correct).

## Proposed experiment (research side)
1. In the decode path, dump the pre-MBR N-best (it exists — output is currently MBR consensus
   1-best). Per turn: N candidate strings + per-word probs.
2. Make-sense gate on the 1-best: flag spans with words outside the scene lexicon
   (or low LM fit — no prompt changes, separate scorer).
3. For each flagged span, collect what the N candidates say for that region (align by viseme
   string or timestamps). Arbitrate: candidate variant wins if (a) in-domain lexicon,
   (b) viseme-consistent with the 1-best span (map below), (c) appears in ≥k candidates.
4. Evaluate against 1-best: content-word recall per turn, context-judge Y+P, and fabrication
   rate (substitutions that reduce ref overlap). Split by source tier (iPhone-4K / camera-screenrec).
   Hypothesis: beats the oracle-phrase-bank numbers above because segmentation is real;
   expect gains concentrated on iPhone-4K + confidence-gated segments.
5. Guardrail for product: substituted words rendered as marked suggestions, never inheriting
   green; keep unfixable noise visible (it is honest "no signal" information).

## Viseme map used (CMU phonemes → classes)
P/B/M→p · F/V→f · TH/DH→T · T/D/S/Z/N/L→t · SH/ZH/CH/JH→S · K/G/NG/HH→k · W/R→w · Y→y ·
UW/UH/OW/AO/OY→O · AA/AE/AH/AY/AW→A · IY/IH/EY/EH/ER→E
Span similarity: difflib ratio on concatenated viseme strings, threshold 0.78 (words via CMUdict/
`pronouncing`). See `snap.py` for the reference implementation (gate, phrase bank, scoring).

## Files in this bundle
- `snap.py` — snapping + scoring reference implementation (OCR-input variant)
- `snap_results.json` — per-video results + full substitution logs
- `turns/*.json` — OCR-extracted turn tables for all 21 videos (said/hyp/speaker/sample-range)
- `viseme_snapping_experiment.md` — the writeup as delivered to Yoad
