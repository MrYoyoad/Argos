# Paper & Demo Kit — index for a future publication

Curated map of everything needed to write and demonstrate a paper on this work,
independent of any employer infrastructure. A frozen self-contained snapshot of
all of it exists as **`vsp_paper_kit_20260808.zip`** —
S3: `s3://yoad-vsp-transfer/vsp/box_evac_20260806/paper_kit/vsp_paper_kit_20260808.zip`
(also left at `/home/ubuntu/vsp_paper_kit_20260808.zip` for direct download).
745 MB (780,980,618 bytes), sha256
`434d7492f7ad1a2b099d1a29a8eec0203923c96f2fcf81810ba7cca4fa11d4f4`;
demo videos are a stratified pick of 5 per IS tier from 25 distinct parent
videos (reproducible from `results_key_data/report.csv`).

**Confidentiality rule**: everything under `CONFIDENTIAL_client_demos/` (Egla-Kafe
material) is client data — usable for private demonstrations only, NEVER in a
publication or public talk. Everything else derives from public datasets
(YouTube benchmark, LRS3, AVSpeech) or is our own analysis.

## Headline numbers (full 1,497-segment YouTube benchmark, Feb–May 2026)

| Metric | Baseline | MBR production default |
|---|---|---|
| Mean WER | 64.1% | 63.8% |
| Mean IS (0–5) | 2.52 | 2.547 |
| NIV Y "clearly conveyed" (IS ≥ 3.80) | 23.1% | 23.9% |
| NIV Y+P "any useful" (IS ≥ 2.00) | 61.6% | 61.9% |
| LLM-judge Y+P | 68.4% | 71.1% (McNemar p=0.0002) |
| Hallucinated (WER ≥ 100%) | 20.5% | — |

Effective capture incl. LLM-salvage: 51.1%. Paper's LRS3 reference WER: 25.4%
(ours is in-the-wild YouTube — the 2.5× gap is itself a finding).
Canonical source for ALL numbers: `docs/evaluation/` + `docs/tuning/experiment-comparison.csv`.

## Suggested paper skeleton → existing material

| Paper section | Source material (repo paths) |
|---|---|
| Method / system | `docs/architecture.md`, VSP-LLM paper (`docs/paper/`), pipeline diagram generator (`docs/_research-tools/generators/`) |
| Evaluation metric (IS) design | `docs/evaluation/intelligibility_methodology.md`, `is_pca_analysis.md`, `is_correlation_analysis.md`, `is_cross_config_validation.md` — the design-time-LLM-distilled, runtime-deterministic metric is a publishable contribution on its own |
| LLM-as-judge validation | `docs/evaluation/llm_judge/` (1,497 gold pairs, Y/P/N, κ calibration, context-eval finding that context makes judges STRICTER), `threshold_calibration_vs_opus.md` |
| Salvage / failure taxonomy | `docs/evaluation/llm_salvage/` (6 recovery types + example gallery), hallucination analysis |
| Decoding / aggregation | `docs/beam-search/n_best_implementation.md` (MBR ships in prod; full paired eval), `docs/tuning/` (13-experiment sweep: baseline robustness) |
| Confidence | `docs/confidence/` (per-token confidence, band reliability by NIV, agreement-aware bands) |
| Fine-tuning limits | `docs/finetuning/training-research-notes.md` (data-limited LoRA result, r16 vs r64, encoder-vs-LLM bottleneck) |
| Human comparison | `docs/evaluation/human_expert_comparison.md` |
| Figures | generators in `docs/_research-tools/generators/` (regenerate any plot); rendered plots inside `presentation_materials_20260224/` |

## Kit zip contents

```
vsp_paper_kit_20260808/
├── README.md                    # this file
├── paper/                       # VSP-LLM paper PDF+text, 2025 presentation
├── reports/                     # docs/{evaluation,tuning,confidence,beam-search,prompts,finetuning}/ wholesale
├── figures_and_generators/      # docs/_research-tools/generators/ (plot+report+diagram generators, STYLE_GUIDE)
├── decks/                       # all PPTX from presentation_materials_20260224/ + Orchard + Project_Review decks
├── results_key_data/            # report.csv + summaries from english_full_results, experiment-comparison.csv, intelligibility_summary.json
├── demos_public/                # representative burned/CC demo videos from the YouTube benchmark + report.html + salvage example gallery
├── CONFIDENTIAL_client_demos/   # Egla-Kafe guessing-game package — private demos ONLY, never publish
└── lessons_and_style/           # universal style guide, doc-generation lessons, evacuation playbook (from the knowledge repo)
```

## Where the big raw material lives (not in the zip)

- Full results incl. all burned videos: `s3://yoad-vsp-transfer/vsp/box_evac_20260806/results/`
- Benchmark input set (1,497 segments): `.../datasets/datasets/english_data_2025_11_20/`
- Model checkpoints (+sha256): `.../models/vsp_checkpoints/`
- Full LRS3 / AVSpeech: `s3://yoad-vsp-transfer/argos/datasets/`
- All client material (confidential): `.../datasets/datasets/clients/` + `s3://conversation-datasets-733430125971/conversation_datasets/egla_kafe/`
