# N-Best Beam Aggregation — Implementation

Mission 6 implementation notes (May 1, 2026). Companion to [Report 5](report_5_beam_search_aggregation.md), which describes the techniques in the abstract; this document describes what actually shipped.

## What landed

**Two missions in one PR**, gated behind `VSP_NBEST=1` (default 0 — pipeline behavior unchanged when off):

1. **Improvement** — the decoder now keeps all 20 surviving beam hypotheses and runs five offline aggregation methods over them. Each adds a column to `report.csv` plus its own per-segment WER, so the user can see directly whether any method beats top-1.
2. **Evaluation** — a beam-variance analyzer emits per-segment metrics (pairwise WER across beams, agreement rate, position entropy), correlates them with WER/IS/sentence_confidence, and runs a word-level confusion analysis testing the hypothesis "do confused words have low confidence?".

**Bug fix included**: the existing `step_scores[::n_beams]` extraction in `vsp_llm_decode.py` was silently picking the wrong beam after HF beam-reordering. Fixed by gathering rows via `gen_out.beam_indices`. Top-1 entropy/top-3 in the existing `confidence-{fid}.json` may shift on hard cases — the new values are the correct ones.

## How to run

```bash
# 1. Decode with n-best capture enabled
VSP_NBEST=1 bash run_flat_english_pipeline.sh         # auto-forces VSP_OUTPUT_SCORES=1

# Outputs (per-fid; fid is the deterministic Hydra-config hash):
#   decode/<task>/<lang>/hypo-{fid}.json         (top-1 — unchanged)
#   decode/<task>/<lang>/confidence-{fid}.json   (top-1 per-token probs)
#   decode/<task>/<lang>/nbest-{fid}.json        (NEW — all 20 beams + per-token probs)

# 2. Reports run automatically via lib/outputs.sh:
#   client_outputs/.../aggregated.json           (5 aggregated hyps per segment)
#   client_outputs/.../report.csv                (5 new hyp_* + wer_*_% columns)
#   client_outputs/.../beam_analysis/            (variance + word-confusion bundle)
```

## The five aggregation methods

All are pure-Python, CPU-only, container-compatible. Implemented in [lib/nbest_aggregate.py](../../lib/nbest_aggregate.py) (EC2) and mirrored to [VSP-LLM/scripts/nbest_aggregate.py](../../VSP-LLM/scripts/nbest_aggregate.py) (container).

| Method | Idea | When it should help |
|--------|------|---------------------|
| `hyp_mbr` | Pick `argmin_i E_j[ WER(hyp_i, hyp_j) ]` under softmax-of-sequence-score weights. Dedupes duplicate hypotheses first. | Hallucinated outliers with high confidence: consensus dominates. |
| `hyp_vote_score` | Multi-way ROVER vote anchored on top-1, position-aligned via Levenshtein. Weight = `softmax(seq_score)`. | Single-word substitution errors where most beams have the right word. |
| `hyp_vote_conf` | Same voter, weight = `softmax(seq_score) × per-word-confidence` from each beam's own token probs. | Tests whether word-level confidence carries information beyond raw sequence score. |
| `hyp_safe` | Start from top-1; swap a word only when its confidence < 0.40 **and** ≥60% of other beams agree on a different word at the aligned position. | Conservative production drop-in — should never make output dramatically worse. |
| `hyp_xseg_merge` | Cross-segment overlap fusion: when adjacent segments from the same source video share ≥3 LCS-matching words at their edge, replace each disagreeing word with the higher-confidence side. | Long videos with overlapping segmentation — exploits physical redundancy in the data. No-op on datasets without configured overlap. |

Each method also emits a debug field (`rank_chosen`, `vote_breakdown`, `swaps`) so spot-checking is straightforward.

## What the variance analysis answers

[docs/_research-tools/generators/analyze_beam_variance.py](../_research-tools/generators/analyze_beam_variance.py) runs four analyses on a completed decode:

1. **Per-segment beam variance** (`beam_variance.csv`) — `pairwise_mean_wer`, `n_unique_hyps`, `word_agreement_rate`, `mean_position_entropy`. These are direct measures of model self-disagreement.
2. **Correlation heatmap** — beam variance metrics × `{wer_%, wwer_%, is_score, sentence_confidence, min_word_conf, n_low_conf_words, nea_f1_%}`. Tests whether beam variance is redundant with token-level confidence or independent.
3. **Aggregator method comparison** (`aggregator_wers.csv` + `aggregator_method_summary.json`) — per-segment WER for each of the five methods plus mean over the dataset.
4. **Word-level confusion** — two passes:
   - Pass 1 (all words ≥5 occurrences): for each unique reference word, compute (recall, mean confidence when predicted, mean beam disagreement when predicted). Pearson r between (1 − recall) and confidence answers the user's specific hypothesis.
   - Pass 2 (Named Entities only, ≥2 occurrences): same stats restricted to PERSON / ORG / GPE / PRODUCT / EVENT / WORK_OF_ART / NORP / LOC / FAC. NEs are the dominant failure mode per Report 1 — separating them surfaces signal that pass 1 dilutes.

## Costs and constraints

- **GPU**: zero additional. HuggingFace beam search already explores 20 beams internally; we just stop discarding 19. Wall-clock unchanged.
- **CPU/disk**: `nbest-{fid}.json` is ~20× larger than `confidence-{fid}.json`. For the 1,497-segment baseline, expect ~300 MB total. Aggregator + variance analyzer add ~minutes of CPU (no GPU needed).
- **Memory**: identical during decode. The aggregator and analyzer hold one segment's records at a time.
- **Container**: byte-identical files in EC2 and standalone (`cmp` verified). Zero new dependencies. spaCy NER pass degrades gracefully when offline.

## Tests

48 new pytest cases under `tests/unit/`:
- `test_alignment_helper.py` — Levenshtein alignment primitives, edge cases, case-insensitivity.
- `test_nbest_aggregate.py` — each method on synthetic hand-crafted hypotheses, N=1 equivalence to top-1, determinism, empty / all-identical edge cases, cross-segment merge with and without overlap.
- `test_beam_variance.py` — pairwise WER on known distances, agreement rate at known thresholds, entropy on uniform vs peaked distributions, per-position disagreement.

Run: `pytest tests/unit/test_alignment_helper.py tests/unit/test_nbest_aggregate.py tests/unit/test_beam_variance.py -v`.

## What is NOT in this PR

- **GPU smoke-test on the 107-segment tuning set** was attempted but blocked: the preprocessed videos referenced by `tuning_results/decode_dataset/test.tsv` no longer exist on disk (`preprocessed_flat_seg12/video/`). Same disk-state issue affects the pre-existing `test_video_files_exist` unit test. The raw videos are still present in `vsp_input_tuning/` and `datasets/english_data_2025_11_20/flat_all/`, so re-preprocessing will recover the inputs — but that's a separate ~30 min preprocessing run, not a Mission 6 task.
- Full 1,497-segment evaluation run (deferred to Phase 7b — same disk dependency: needs `preprocessed_flat_seg4/` or whichever directory the full TSV references).
- Per-method WER deltas vs top-1 baseline — pending the evaluation run.
- Word-level confusion findings (Pearson r values, top confused words) — pending the evaluation run.
- Cross-segment merge effectiveness numbers — pending check of whether the 1,497-segment baseline was decoded with overlap configured.

The post-processing code (aggregator, variance analyzer, alignment helper) **is fully tested** via 48 unit tests on synthetic n-best inputs. The decode-side code (vsp_llm.py, vsp_llm_decode.py) is syntactically verified and the logic was reviewed against HuggingFace's `compute_transition_scores` + `beam_indices` semantics. What remains is one real GPU run on a dataset with intact preprocessed videos to confirm the wire-level integration.

To run the smoke test once the videos are restored: `bash scripts/tests/test_nbest_decode_smoke.sh`. It executes the full chain (decode → nbest sidecar → aggregator → variance analyzer → report) and prints aggregator method WERs at the end.

These results will be added to this document and to [docs/beam-search/beam_variance_analysis.md](beam_variance_analysis.md) + [docs/beam-search/word_level_confusion_analysis.md](word_level_confusion_analysis.md) (auto-emitted by the analyzer) once the run completes.
