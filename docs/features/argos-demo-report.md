# Argos Demo Report (Auto-Generated)

**Status**: Shipped May 1, 2026
**Modules**: [lib/outputs.sh](../../lib/outputs.sh), [docs/_research-tools/generators/generate_client_demo_report.py](../_research-tools/generators/generate_client_demo_report.py)
**Output**: `client_outputs/report/argos_demo.html` (inside every pipeline run's output folder, picked up by the UI's zip download)

## What it is

A polished, dark-themed, single-page HTML report — one card per segment, per-word green/yellow/red confidence coloring, hover tooltips with the underlying probability. Visually distinct from `report.html` (the analyst-facing tabular report from [VSP-LLM/scripts/make_report.py](../../VSP-LLM/scripts/make_report.py)). Both reports are produced; both go in the zip.

| | `report.html` | `argos_demo.html` |
|---|---|---|
| Audience | Analysts, debugging, QA | Clients, demos, screenshots |
| Layout | HTML table | Dark cards |
| Confidence colors | Blue / orange / purple | Green / yellow / red |
| Source data | Decode JSON + IS scores | Decode JSON + word confidence |
| Generator | `make_report.py` | `generate_client_demo_report.py` |

## How it's wired

[lib/outputs.sh](../../lib/outputs.sh) Stage 8 calls `run_argos_demo_report` after `make_report.py` succeeds. The function:

1. Resolves the generator script — prefers `${VSP_DIR}/scripts/generate_client_demo_report.py` (canonical), falls back to `${HOME}/docs/_research-tools/generators/generate_client_demo_report.py` for EC2 development.
2. Invokes `python3 <gen> --decode <hypo-NNNN.json> --out <report_dir>/argos_demo.html`.
3. Logs warning and returns non-zero on failure — does **not** abort the pipeline (it's polish, not a metric).

When a `confidence-{fid}.json` sidecar exists alongside the decode JSON (i.e. when `VSP_OUTPUT_SCORES=1` was set during decode — the default since April 30, 2026), the report uses **real per-token softmax probabilities** aggregated to per-word. Otherwise it falls back to **synthetic** confidence derived from WER alignment between REF and HYP (each segment is tagged "synthetic" so reviewers know).

## CLI

The generator is run-agnostic and has no Obama-specific defaults:

```bash
# Default: dark Argos branding, all segments, "Pipeline output" source card
python3 docs/_research-tools/generators/generate_client_demo_report.py \
    --decode path/to/hypo-NNNN.json \
    --out report.html
```

Optional flags:

| Flag | Default | Purpose |
|---|---|---|
| `--filter <substr>` | `""` (all) | Only render segments whose `utt_id` contains the substring |
| `--title <text>` | `Argos VSP — Visual Speech Recognition` | Page H1 |
| `--subtitle <text>` | `N segments` | Subtitle under H1 |
| `--source <text>` | `Pipeline output` | Value in the "Source" summary card |
| `--prefix-alias 'src=dst'` | unset | Rewrite a verbose utt_id prefix to a friendly name in segment labels |

### Re-creating the original Obama client-deck artifact

The generator was originally built for the Obama bin Laden announcement screenshot used in the client deck. To regenerate that exact artifact:

```bash
python3 docs/_research-tools/generators/generate_client_demo_report.py \
    --decode english_full_results/decode_output/hypo-84361.json \
    --filter "050111_OsamaBinLadenStatement_HD" \
    --subtitle "Client demo · Obama bin Laden announcement (May 1, 2011) · 6 segments" \
    --source "Public TV broadcast" \
    --prefix-alias "050111_OsamaBinLadenStatement_HD=Obama bin Laden speech" \
    --out presentation_materials_20260224/01_plots_for_slides/obama_demo_report.html
```

This produces a byte-identical artifact to the version in [docs/_research-tools/generators/presentation/slides_client.py](../_research-tools/generators/presentation/slides_client.py).

## Sync state

The generator is mirrored verbatim across all three deployment locations (verified by md5sum):

- [docs/_research-tools/generators/generate_client_demo_report.py](../_research-tools/generators/generate_client_demo_report.py) — canonical (EC2 development)
- [VSP-LLM/scripts/generate_client_demo_report.py](../../VSP-LLM/scripts/generate_client_demo_report.py) — EC2 runtime (resolved by `outputs.sh`)
- [vsp_docker/galaxy_export/VSP-LLM/scripts/generate_client_demo_report.py](../../vsp_docker/galaxy_export/VSP-LLM/scripts/generate_client_demo_report.py) — Docker build copy
- [vsp_linux_container_FINAL_20260217/VSP-LLM/scripts/generate_client_demo_report.py](../../vsp_linux_container_FINAL_20260217/VSP-LLM/scripts/generate_client_demo_report.py) — standalone container

Likewise [lib/outputs.sh](../../lib/outputs.sh) and [vsp_linux_container_FINAL_20260217/lib/outputs.sh](../../vsp_linux_container_FINAL_20260217/lib/outputs.sh) are byte-identical.
