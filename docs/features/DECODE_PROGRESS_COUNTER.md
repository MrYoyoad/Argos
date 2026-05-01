# Decode Progress Counter

Adds an "X / N segments decoded" line to the UI's processing screen during pipeline stage 7 (LLM decoding). Shipped 2026-05-01.

## Why

Stage 7 takes ~30s per segment of inference, so a 1,497-segment run sits on the wait banner for ~12.7h. The progress bar advances only on stage transitions, so it appears frozen for the bulk of that time. A previous attempt at an ETA estimate was abandoned — stage-weight extrapolation is too noisy to be useful.

This counter avoids estimation entirely. It shows ground truth: how many segments fairseq has actually finished, out of how many it loaded.

## How it works

Two backend signals feed `decode_total` and `decode_done` on `ProgressState`:

**Total N** comes from two log lines, with the python value overriding the bash value:

| Source | When | What | Why |
|--------|------|------|-----|
| `lib/decode.sh` | Right after `>>> [7]` | `Decoding ${segment_count} segments...` (from manifest line count) | Visible immediately — model load takes 30–60s before the python override arrives. |
| `VSP-LLM/src/vsp_llm_decode.py` | After dataset loads, before the decode loop | `Decode dataset loaded: ${len(dataset)} samples` | Authoritative — uses fairseq's loaded sample count, not a TSV line count. |

**Per-segment increment** uses two signals to balance smoothness and reliability:

| Signal | Cadence | Reliability |
|--------|---------|-------------|
| `^HYP:` line ([vsp_llm_decode.py:409](../../VSP-LLM/src/vsp_llm_decode.py#L409)) | One per sample | Smooth +1, but depends on the embedded-`\n` log format — could break silently if logging is reformatted. |
| `Incremental flush at N samples` | Every `VSP_FLUSH_EVERY=25` samples | Absolute checkpoint. Self-heals if any `HYP:` line is dropped under load. |

`decode_done` increments on each `HYP:` and is `max(decode_done, N)` on each flush — never decrements.

## Stage guard

Bash and Python emit to the same pipe but as separate processes. `>>> [7]` (bash) can in principle arrive after the first `HYP:` (python) under unusual buffering. The tracker only counts `HYP:`/flush signals while `current_stage_id == "decode"`, and the counters reset on entry to the decode stage. This also handles re-runs and the `segment_only` mode (counter never activates if stage 7 is skipped).

## What this is not

- Not an ETA. The frontend renders only "X / N", no remaining-time estimate.
- Not a replacement for the existing percent bar — it's an additional line that appears only during stage 7.

## Files

| Layer | Path |
|-------|------|
| Tracker | [vsp-ui/app/services/progress_tracker.py](../../vsp-ui/app/services/progress_tracker.py) — `decode_total`, `decode_done`, `_update_decode_counter`, reset on stage entry |
| Bash | [lib/decode.sh](../../lib/decode.sh) — emits `Decoding N segments...` from manifest |
| Python | [VSP-LLM/src/vsp_llm_decode.py](../../VSP-LLM/src/vsp_llm_decode.py) — emits `Decode dataset loaded: N samples` |
| HTML | [vsp-ui/app/static/index.html](../../vsp-ui/app/static/index.html) — `#decode-counter` |
| JS | [vsp-ui/app/static/app.js](../../vsp-ui/app/static/app.js) — `updateProgress()` show/hide |
| CSS | [vsp-ui/app/static/style.css](../../vsp-ui/app/static/style.css) — `.decode-counter` |

The same edits are applied in `vsp_linux_container_FINAL_20260217/` and `vsp_docker/galaxy_export/` — see [docs/container-sync-changelog.md](../container-sync-changelog.md).

## Tests

- [tests/unit/test_progress_tracker_decode_counter.py](../../tests/unit/test_progress_tracker_decode_counter.py) — 17 pytest cases covering total parsing, increment, flush reconciliation, stage guards, reset on entry, serialization, and a full end-to-end lifecycle.
- [lib/test_all_modules.sh](../../lib/test_all_modules.sh) — TEST 10 grep-asserts that `lib/decode.sh` still contains the bash log line. Without it, the counter has no early denominator.

Run:

```bash
pytest tests/unit/test_progress_tracker_decode_counter.py -v
bash lib/test_all_modules.sh
```
