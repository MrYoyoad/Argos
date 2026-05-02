# n-best LLM-as-a-Judge — workflow (v2, blind, no conf in prompt)

This directory holds the in-conversation Claude judging run for Mission 6's n-best
aggregation methods (baseline, `hyp_mbr`, `hyp_vote_score`, `hyp_vote_conf`) on the
full 1,497-segment set.

> **v1 was contaminated and is now archived.** v1 injected sentence + per-word
> confidence numbers into the judge prompt. On 27 % of identical-text segments,
> verdicts split anyway — the judge let conf drive the call. Archived under
> `batches_v1/`, `judgments_v1/`, `batch_index_v1.json`, `auto_judgments_v1.csv`.
> See `llm_judge_nbest_analysis.md` for the v1 contamination analysis.
>
> **v2 is blind on text only.** Format is `NNN|ref|hyp` — same protocol as the
> prior `llm_judge/` gold standard.

## Why this run

WER says `hyp_vote_conf` wins by 1.56 pp (62.49 %). IS (the project's deterministic
semantic metric) says all four methods are tied within 0.015 IS, with paired
McNemar p ≈ 1.0 on IS-NIV-Y. v1 judge said `hyp_vote_conf` significantly lost on
NIV-Y (p=0.0005) but was contaminated. v2 is the deciding test: do n-best
aggregation methods change *meaning* delivery vs the 1-best baseline, when the
judge sees nothing but ref + hyp text?

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

## Batch format (v2)

Each batch file has a single header line then `---` then one row per pair. The
hypothesis column is **plain text only** — no confidence annotations.

```
BASELINE | BATCH 01/15 | 103 pairs | format: NNN|ref|hyp | Y=meaning conveyed, P=partial (annotate: P:preserved/-lost), N=meaning lost
---
001|we will give up some of our individual choice for the sake of the community decision|will give up some of our individual choices for the sake of the community and
002|...
```

This matches the prior `llm_judge/` gold-standard protocol exactly. Confidence is
NOT shown to the judge during judging; if a confidence-vs-verdict calibration table
is wanted, it's built post-hoc from `report.csv` after judging completes.

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

In the session, give Claude this prompt template (paste verbatim — it self-selects
the next un-judged batch):

> I need you to judge reference-vs-hypothesis pairs for an n-best aggregation evaluation.
> The job is resumable — pick any batch that has not been judged yet and process it.
>
> **Step 1 — pick a batch.** List the files in
> `/home/ubuntu/docs/evaluation/llm_judge_nbest/batches/` (60 files named
> `batch_<method>_NN.txt`). For each one, check whether the matching judgments file
> exists at `/home/ubuntu/docs/evaluation/llm_judge_nbest/judgments/batch_<method>_NN_judgments.txt`.
> Pick the first batch that does **not** yet have a judgments file. If all 60 are
> done, stop and tell me.
>
> **Step 2 — read it.** The first line is a header (skip it), then `---`, then one
> segment per line in the format `NNN|ref|hyp`:
> - `NNN` — 3-digit index
> - `ref` — ground-truth transcript (plain text)
> - `hyp` — hypothesis text (plain text)
>
> **Step 3 — judge each line.** Decide whether the hypothesis conveys the meaning of
> the reference:
> - **Y** — meaning fully conveyed (small wording differences are fine)
> - **N** — meaning lost (wrong topic, fluent garbage, hallucinated content, key
>   information replaced or absent)
> - **P** — partial. Annotate as `P:preserved/-lost` where each side is a `+`-joined
>   subset of `{key, struct, sem, phon, detail, num, entity}`. Examples:
>   `P:key+sem/-detail`, `P:struct/-key`. Plain `P:` is allowed.
>
> Stay strictly blind: do **not** open `report.csv`, `segment_features.csv`, or
> anything else in `english_full_nbest_eval/` or `docs/evaluation/`. Judge on
> reference-vs-hypothesis text only. Be conservative on ties (Y vs P → P;
> P vs N → N).
>
> If two hypotheses you've seen in this session look essentially identical, give
> them the same verdict — don't second-guess. The aggregation methods often produce
> matching text on easy segments and we want intra-rater stability there.
>
> **Step 4 — write the output.** Write
> `/home/ubuntu/docs/evaluation/llm_judge_nbest/judgments/batch_<method>_NN_judgments.txt`
> (matching the batch filename, with `_judgments.txt` instead of `.txt`). One line
> per pair in the format `NNN,JUDGMENT`. No commentary, no blank lines, no header.
> Cover every `NNN` in the batch — no skips. Examples:
> ```
> 001,Y
> 002,P:key+sem/-detail
> 003,N
> ```
>
> **Step 5 — repeat.** Go back to Step 1 and judge the next un-done batch. Continue
> until all 60 are done or you run out of room. When you stop, report which batches
> are now complete.

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
