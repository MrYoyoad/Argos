# n-best LLM-as-a-Judge — workflow

This directory holds the in-conversation Claude judging run for Mission 6's n-best
aggregation methods (baseline, `hyp_mbr`, `hyp_vote_score`, `hyp_vote_conf`) on the
full 1,497-segment set. The judge is **Claude Opus 4.6**, judging happens **inside
fresh Claude Code conversations** (not via API), matching the prior `llm_judge/`
gold-standard protocol.

## Why this run

WER says `hyp_vote_conf` wins by 1.56 pp (62.49 %), but the project ships against
**NIV thresholds calibrated to the LLM judge** (κ=0.690 for Y, κ=0.818 for Y+P).
This run answers two open questions:

1. Does `hyp_vote_conf`'s WER win translate to more **Y** verdicts (meaning conveyed)?
2. Does `sentence_confidence` (when shown to the judge) predict Y / Y+P verdicts —
   the calibration data Mission 4.1 needs.

## Files

```
llm_judge_nbest/
├── README.md                # this file
├── batches/                 # 60 input files (4 methods × 15 batches), prep done
│   └── batch_<method>_NN.txt
├── judgments/               # YOU write these in Opus 4.6 sessions
│   └── batch_<method>_NN_judgments.txt
├── batch_index.json         # maps (batch, line) → (utt_id, method, is_duplicate)
├── auto_judgments.csv       # 280 empty/trivially-short hyps auto-classified N
├── results_long.csv         # one row per (utt_id × method) — built by analyze
├── results_wide.csv         # one row per utt_id, all 4 verdicts side-by-side
├── summary.json             # per-method Y/P/N rates, McNemar, intra-rater
├── calibration.csv          # 10 conf-bins × method → P(Y), P(Y+P)
└── llm_judge_nbest_analysis.md
```

## Batch format

Each batch file has a single header line then `---` then one row per pair:

```
BASELINE | BATCH 01/15 | 103 pairs | format: NNN|ref|hyp|conf | Y=meaning conveyed, P=partial (annotate: P:preserved/-lost), N=meaning lost | `conf` is the method's own sentence-level confidence in [0,1] (n/a if missing) — use as a soft cue, NOT as a verdict shortcut
---
001|<reference>|<hypothesis>|<conf>
002|...
```

`conf` is the method's own confidence: `sentence_confidence` for baseline, or
`hyp_<method>_mean_conf_calib` for the n-best methods. Rounded to 2 decimals.
`n/a` when missing.

## Verdict codes

Same scheme as the prior `llm_judge/` run:

- **Y** — meaning fully conveyed
- **N** — meaning lost
- **P** — partial; annotate as `P:preserved/lost` where each side is a `+`-joined
  list of tags drawn from `{key, struct, sem, phon, detail, num, entity}`. The
  `lost` side may also use `-` prefixes interchangeably (parser handles both).
  Examples: `P:key+sem/-detail`, `P:struct/key`, `P:`.

## How to run a judging session (Opus 4.6)

Each batch is independent and resumable. Spawn a fresh Opus 4.6 conversation per
session (not 4.7 — preserves comparability with the existing 1,497-pair gold
standard).

In the session, give Claude this prompt template (substitute the batch path):

> Read `/home/ubuntu/docs/evaluation/llm_judge_nbest/batches/batch_<METHOD>_<NN>.txt`.
> Each line is `NNN|ref|hyp|conf`. Judge each pair Y/P/N per the header. The `conf`
> column is the model's sentence-level confidence — use it as a soft cue (e.g., very
> low conf may make a borderline P feel more like an N) but do **not** let it override
> your reading of meaning. Stay blind: do not look at `report.csv` or any other file.
>
> Write your verdicts to
> `/home/ubuntu/docs/evaluation/llm_judge_nbest/judgments/batch_<METHOD>_<NN>_judgments.txt`,
> one line per pair in the format `NNN,JUDGMENT` (e.g., `001,Y`, `002,P:key+sem/-detail`,
> `003,N`). One pair per line, no extra commentary in the file.

A single batch is ~100 pairs and fits comfortably in one Opus 4.6 turn. 60 batches
total. Sessions can run in any order; the analysis script aggregates whatever is
present.

## Analysis

After any number of batches land, run:

```bash
python3 /home/ubuntu/docs/_research-tools/generators/analyze_nbest_judge.py
```

It will:
- Join judgments + auto-N + report.csv + segment_features.csv → `results_long.csv` / `results_wide.csv`
- Compute per-method Y/P/N counts, NIV-Y rate, NIV-Y+P rate
- Run paired McNemar (continuity-corrected) for each method vs baseline on Y and Y+P
- Build a 10-bin calibration table (conf × method → P(Y), P(Y+P))
- Compute intra-rater agreement on the 30 duplicate pairs per method
- Write `summary.json` + `llm_judge_nbest_analysis.md`
- Tolerate missing batches — partial completions are reported, not errors

## Reproducibility

- Prep: `prepare_nbest_judge_batches.py`, `SEED=42`, `BATCH_SIZE=100`, `N_DUPLICATES_PER_METHOD=30` (6 per IS tier).
- Inputs (read-only): `english_full_nbest_eval/report/report.csv`,
  `english_full_nbest_eval/conditional_analysis/segment_features.csv`.
- Pipe characters in ref / hyp are sanitized to `/` so the format stays parseable.
- Empty / trivially-short hypotheses (hyp <3 words AND ref >5 words) are auto-N
  (~70 per method) and recorded in `auto_judgments.csv`.

## Out of scope (follow-ups)

- **Context-aware re-judge** (analogous to `llm_judge/context_eval/`) — only after
  blind numbers are in.
- **Method-method joint ranking** — current run is independent per method to
  preserve comparability with the existing 1,497-pair gold standard.
- **API-based judging** — this protocol is intentionally in-conversation.
