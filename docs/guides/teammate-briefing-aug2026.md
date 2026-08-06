# VSP Lip-Reading Pipeline — Teammate Briefing (August 2026)

Date: August 3, 2026. Author: project team.
Audience: a new technical teammate with full access to this repo and EC2 box.

---

## 1. What this is

This repository is a visual speech processing (lip-reading) pipeline: `auto_avsr/` does video preprocessing (face detection, mouth cropping), `av_hubert/` extracts AV-HuBERT visual features, and `VSP-LLM/` decodes them into text with a Llama-2-7b backbone plus LoRA adapters. The main entry point is [run_flat_english_pipeline.sh](../../run_flat_english_pipeline.sh), which orchestrates 11 modular stages under [lib/](../../lib/); a web UI lives in [vsp-ui/](../../vsp-ui/). The system is deployed to a client on Windows via Docker. The honest state: the *product* works end-to-end (upload video → subtitled output with per-word confidence coloring), but the *model* is prototype-grade — WER 63.8% on the in-house benchmark, roughly 2.5× worse than the paper's LRS3 number, with fluent hallucination as the dominant failure mode. Most of the engineering effort since February 2026 has gone into measuring honestly (IS metric, LLM judge), extracting maximum value from the current model (n-best aggregation, confidence gating), and telling clients the truth about what capture conditions it needs.

Suggested reading order:

1. [CLAUDE.md](../../CLAUDE.md) — rules, architecture summary, all headline numbers
2. [docs/architecture.md](../architecture.md) — pipeline flow, segments, data formats
3. [docs/development-guide.md](../development-guide.md) — commands, venvs, troubleshooting
4. This document
5. [docs/backlog/mission-backlog.md](../backlog/mission-backlog.md) — roadmap, Missions 4–14
6. [docs/guides/project-handover-july2026.md](project-handover-july2026.md) — the departing lead's handover (client commitments, traps, first-week checklist)

## 2. Datasets — what exists and where it actually lives

Sizes measured on this box, August 3, 2026.

> **⚠️ SUPERSEDED (2026-08-06): every "box-only" claim below is now stale.** The full
> box evacuation copied all box-only artifacts (eval set, checkpoints, results,
> archives, seamless_interaction, config) to
> `s3://yoad-vsp-transfer/vsp/box_evac_20260806/` ahead of decommission, and all
> uncommitted code was pushed to the GitHub repos (av_hubert now lives at the
> `MrYoyoad/av_hubert` fork). See
> [box-evacuation-aug2026.md](box-evacuation-aug2026.md) for the full manifest.
> The rows below remain accurate as a map of what was WHERE on the box.

| Dataset | Path on this EC2 box | Size | Purpose | Copies elsewhere |
|---|---|---|---|---|
| English eval set | `datasets/english_data_2025_11_20/` | 2.4 GB | The 1,497-segment benchmark behind every headline number | **Box-only (no S3, gitignored) — irreplaceable.** Results live in `english_full_results/` (metrics CSVs are in git; the 1.7 GB `client_outputs/` is box-only) |
| AVSpeech fine-tune set | `data/` | 938 MB | The 1,273 segments used in LoRA Exp A/B | Box-only |
| Egla-Kafe processed | `datasets/clients/egla_kafe/` (inside 9.4 GB `datasets/clients/`) | — | Speaker crops, decode runs, deliverables for the live client | Box-only (raw masters have an S3 copy, see next row) |
| Egla-Kafe RAW masters | `~/egla_kafe/` (repo root) | 2.8 GB | 5 iPhone-4K originals IMG_6821–6825 + client files | **Backed up in S3** (see below) |
| LRS3 | `datasets/lrs3orig_sync.tar` (136 MB sample) on box | **133.8 GB full corpus in S3** | **FOUND 2026-08-03: the FULL LRS3** (303,901 objects, ~152K clips) at `s3://yoad-vsp-transfer/argos/datasets/lrs3orig/` — **the Llama-3.1 migration blocker is data-resolved** ([llama3-migration.md](../finetuning/llama3-migration.md) §4) | S3 needs portal creds or a bucket-policy grant to read from EC2 (instance role is 403 on `argos/*`); box needs ≥134 GB free to sync |
| AVSpeech (full) | — (only the 938 MB slice in `data/`) | **519.9 GB full corpus in S3** | **FOUND 2026-08-03**: complete AVSpeech download (611,352 objects) at `s3://yoad-vsp-transfer/argos/datasets/avspeech/` — removes the 20K-segment training-data ceiling | Same access caveats as LRS3 |
| 2024 filming days | — | 38.1 GB in S3 | Historical project footage (`argos/custom_data/`: filming days Jul/Oct 2024 + clean + 25fps variants) | S3 only |
| seamless_interaction | `datasets/seamless_interaction/` | 1.9 GB | Candidate multi-speaker data | Box copy is the only real one — the S3 upload never completed (139 KB stub) |
| Arabic samples | `datasets/arabic_raw/` (44 MB), `datasets/arabic_flat/`, `datasets/arabic_sample.tar.gz` | ~44 MB+ | Language-extension experiments | Box-only |

**Model weights** (all box-only, no S3 copy): `VSP-LLM/checkpoints/` holds `checkpoint_finetune.pt` (4.1 GB — THE decode model), `checkpoint_freeze.pt` (4.1 GB), `large_vox_iter5.pt` (3.9 GB, AV-HuBERT encoder), and `Llama-2-7b-hf/` (26 GB) — 37 GB total. (The root-level `Llama-2-7b-hf/` directory is a 12 KB config-file stub, not the model.)

### S3 reality (verified live 2026-08-03)

`s3://conversation-datasets-733430125971` is the only listable dataset bucket (instance IAM role, bucket-policy pattern; use `s5cmd`; no FUSE mounts, ever). Full object-level breakdown: [s3-data-inventory-aug2026.md](s3-data-inventory-aug2026.md). Highlights:

- `conversation_datasets/egla_kafe/` — 2.98 GB, 68 objects: the **whole raw client corpus** (5 iPhone masters IMG_6821–6825 + scene 1/2 videos + worn-mustache scenes + 42 per-speaker crops + manifest)
- **EgoCom (14.9 GB), RealTalk (4.3 GB), AMI (1.1 GB) — curated multi-speaker candidate corpora with word-level transcripts, existing ONLY in S3, not on this box** (relevant to Mission 12)
- `tmp/` — the July client deliverable bundles (`EglaKafe_full_deliverables.zip` 385 MB, `egla_kafe_meeting_package_20260713.zip` 24 MB)
- `seamless_interaction/` — 139 KB scripts-only stub (the 1.9 GB sample is box-only)
- **Zero keys matching avspeech / english_data / lrs3 in THIS bucket** — but see below: the full LRS3 and AVSpeech live in the *other* bucket, invisible to the instance role. The English eval set (`english_data_2025_11_20`) remains genuinely box-only.

**`s3://yoad-vsp-transfer` — where the real data turned out to be** (found 2026-08-03 with temporary admin credentials; the instance role gets 403 outside `vsp/*`, which is why every EC2-side probe missed it): `argos/datasets/lrs3orig/` = **full LRS3, 133.8 GB**; `argos/datasets/avspeech/` = **full AVSpeech, 519.9 GB**; `argos/custom_data/` = 2024 filming days, 38.1 GB; a 653 GB raw backup-restore dump (duplicate of the above); `vsp/` = all three client image builds + kits (122.2 GB). Full breakdown + access recipes: [s3-data-inventory-aug2026.md](s3-data-inventory-aug2026.md).

`s3://yoad-vsp-transfer` is NOT a dataset channel: it is the May-2026 Windows client delivery bucket (Docker image builds). No ListBucket; the instance role has GetObject bucket-wide and — verified 2026-08-03 — **PutObject under the `vsp/` prefix only** (that's how the image tarballs were uploaded). The role cannot `ListAllMyBuckets`; do not re-probe — the sweep is documented in [docs/sessions/HANDOVER.md](../sessions/HANDOVER.md) (2026-07-16 17:32 entry). Writes to `conversation-datasets-733430125971` are NOT possible from this box (uploads there were done from a laptop with short-lived access-portal credentials — see `conversation_datasets/refresh_aws_creds.sh` in the bucket).

**This package as a zip**: `s3://yoad-vsp-transfer/vsp/teammate_package_20260803.zip` (39.8 MB, + `.sha256`) — briefing (md+docx), the four guides, conversation scripts, requirements freezes, vocab tools, the three training-project briefs (md+docx), and `Argos_VSP_Final.pptx`, with a README manifest.

## 3. Configuration

**Decode config** — frozen since 2026-02-17: `beam=20`, `lenpen=0.0`, no sampling (`do_sample: false`). Source of truth: [VSP-LLM/src/conf/s2s_decode.yaml](../../VSP-LLM/src/conf/s2s_decode.yaml), invoked via [VSP-LLM/scripts/decode.sh](../../VSP-LLM/scripts/decode.sh). Thirteen tuning experiments failed to beat it (§7).

**Env switches** (verified in [lib/decode.sh](../../lib/decode.sh) and [lib/outputs.sh](../../lib/outputs.sh)):

- `VSP_NBEST` — n-best sidecar (20 beams × per-token probs) feeding the aggregation methods. **Default is 1** (production on); set `VSP_NBEST=0` only on memory/disk-constrained runs.
- `VSP_DISPLAY_METHOD` — which hypothesis the reports display. Defaults to `hyp_mbr` when an `aggregated.json` exists for the run, else the report falls back to top-1. Override (e.g. `top1`) for A/B or backward-compat runs.

**Virtual environments** (defined in [lib/config.sh](../../lib/config.sh)): `auto_avsr/pre-process-venv` (exported as both `ASR_VENV` and `PREP_VENV`) and `~/vsp-llm-yoad-venv` (`VSP_VENV`). Both are Python 3.9.23.

**EC2 vs container**: IS scoring (`--compute-is`) runs on EC2 by design; the container is rooted at `/workspace`. Three sync targets, in order:

1. **EC2** (`/home/ubuntu/`) — source of truth, where changes are made and tested.
2. **`vsp_linux_container_FINAL_20260217/`** — patch overlay; every EC2 change must be synced here.
3. **`vsp_docker/container_payload_20260507/`** — the Docker image build context, synced wholesale only at image-rebuild time. (`vsp_docker/galaxy_export/` is a dead stub — do not use it.)

Full setup and deployment detail: [ec2-setup-from-scratch.md](ec2-setup-from-scratch.md) and [client-laptop-deployment-aug2026.md](client-laptop-deployment-aug2026.md).

## 4. The IS metric — self-contained explanation

**Why it exists.** WER alone misjudges lip-reading output in both directions: it over-punishes harmless paraphrase, and it under-punishes the most dangerous failure mode — fluent, grammatical, entirely fabricated text. 20.7% of benchmark segments are fluent-but-fabricated (WER ≥ 100%), and a reader has no signal to distrust them.

**How it works.** The Intelligibility Score (IS) is a composite 0–5 score built from 6 deterministic signals: semantic similarity, phonetic similarity, WER, WWER (high-value words penalized 2×), named-entity accuracy, and length ratio. The rubric, signal weights, and tier boundaries were designed by Claude (Anthropic) at *design time* — an "LLM-distilled" metric. **No LLM is called at evaluation time**: scoring is fully deterministic, free, and reproducible.

| Tier | IS range | Label |
|---|---|---|
| 5 | 4.0–5.0 | Excellent |
| 4 | 3.0–3.99 | Good |
| 3 | 2.0–2.99 | Fair |
| 2 | 1.0–1.99 | Poor |
| 1 | 0.0–0.99 | Failed |

**Operating thresholds (NIV)**: NIV-Y "clearly conveyed" = IS ≥ 3.80 → 23.9% of segments (358/1,497, MBR default); NIV-Y+P "any useful" = IS ≥ 2.00 → 61.9% (927/1,497). These were calibrated against a Claude-Opus judge gold standard on all 1,497 pairs: κ = 0.693 (Y) / 0.796 (Y+P) under MBR (0.707 / 0.816 under top-1), and IS beats WER-based thresholds at both operating points (+0.061 κ for Y, +0.041 for Y+P).

**Caveats.** PCA shows the 6 signals collapse to 2 real dimensions — signal quality (68.4% of variance; all 5 content signals load equally) and output length (19.5%); semantic similarity is NOT an independent dimension. And IS misses judge-visible rescues below tier 3: n-best aggregation lifts marginal segments (judge N→P) that never cross the IS 2.0 threshold, which is why the judge sees a bigger MBR win than IS does.

Details: [intelligibility_methodology.md](../evaluation/intelligibility_methodology.md), [is_correlation_analysis.md](../evaluation/is_correlation_analysis.md), [threshold_calibration_vs_opus.md](../evaluation/threshold_calibration_vs_opus.md), [after_amosi_audit.md](../evaluation/after_amosi_audit.md).

## 5. Confidence scoring — self-contained explanation

**What is produced.** Every decode emits per-word confidences (decoder token posteriors) plus a `sentence_confidence` column in `report.csv`; `report.html` and the burned videos color words green/yellow/red.

**Band rule (production since May 2026)** — joint confidence + beam agreement: green = top-1 conf ≥ 0.95 AND beam agreement ≥ 0.80; yellow = conf ≥ 0.65 AND agreement ≥ 0.50; everything else red. Numbers are always capped at yellow, because of confident-wrong leakage on numerals ("billion"→"million" at prob 0.965). Beam agreement is ~2× more informative than raw confidence at the high end.

**Green is conditional on segment quality.** Under the legacy conf-only rule measured on the B3 sidecar, P(correct | green) is 92.8% in segments with mean_prob ≥ 0.85 but degrades monotonically to ~18% below 0.40. (Under the current joint rule the recomputable bins are 96.4% / 91.7% / 86.1% for the ≥0.65 strata — see [after_amosi_audit.md](../evaluation/after_amosi_audit.md) §D for provenance.) Hence the three-tier segment policy:

- **Trust** (segment mean_prob ≥ 0.82) — show colors, believe green.
- **Salvage** (0.65–0.82) — per-word flags do real work here: within useful content (NIV Y+P), P(correct | green/yellow/red) = 87.2% / 48.9% / 24.7%.
- **Strip** (< 0.65) — do not show word colors at all; green misleads.

**Client operating point**: trust segments with ≥ 30% green words → 65.2% recall of useful content at 5.6% false-positive rate.

**Key caveat: every threshold above is Llama-2-7b-specific.** Any LLM swap requires re-running [diagnose_confidence_signals.py](../_research-tools/generators/diagnose_confidence_signals.py) to re-derive the band rule and tier boundaries.

Details: [report_4_confidence_scoring.md](../confidence/report_4_confidence_scoring.md), [confidence_full_analysis.md](../confidence/confidence_full_analysis.md), [band_reliability_by_niv.md](../confidence/band_reliability_by_niv.md) (note: its table still uses the old conf-only rule — open follow-up), [per-word-confidence-user-guide.md](../features/per-word-confidence-user-guide.md).

## 6. Egla-Kafe: the live client engagement

**Footage.** 21 scripted two-person conversations, two capture tiers: 5 iPhone-4K masters (img_6821–6825, including 2 scenes with worn costume mustaches) versus 16 client screen-recordings (viewer-app window captures, faces ~60–90 px tall). Two scripts: Emma/Jake (airport, mis-booked flight) and Military (planning meeting). The footage has no usable audio, so speakers were identified visually (ArcFace face-ID, 19/21 videos verified) and turns detected visually.

**Results.** Conversation-level WER **86%** is the honest headline — the per-segment 122% is a short-segment scoring artifact (1-word references blow up WER). Mean IS 1.55; per-segment NIV-Y+P 24.8%, but the context-aware conversation-level judge recovers a mean **36.9% Y+P**. Best video: img_6825 at 72.7% context Y+P — the one video where "the subtitles alone tell the story" (cold-read 50.0%). Worst iPhone video: img_6821, 3.1% cold-read (1/32 turns) — worn mustaches occlude the lips and 4K cannot compensate. Statistically robust levers: iPhone-4K beats screen-recordings (IS 1.51 vs 0.88, p = 2.3e-05) and frontal beats 45° (p = 2.0e-03). Confidence gating at ≥ 0.7 keeps 10% of turns at IS 2.86 / 70% useful — i.e., a **coverage problem, not a capability problem**. Word-category trust for green words: common NOUN 82% correct … ENTITY 0% — never trust a proper noun from this model. The resolution ablation (4K→2K→1080p, 175 paired segments) found **no significant difference anywhere** — mechanism: the affine warp normalizes every mouth to a ~45 px canonical crop, so what matters is framing (mouth ≥ 50 px in frame, ideally ≥ 100 px) and clean original files, not the resolution number.

**Two-speaker layering — three distinct things; do not conflate them:**

1. **Visual active-speaker merge WORKS and is the shipped method.** [build_active_speaker_stream.py](../../scripts/pipeline/build_active_speaker_stream.py): per-crop mouth-motion variance → hysteretic state machine (min-dwell 0.4 s) → turn timeline; segments are cut AT turn boundaries and decoded per-turn; script↔turn matching uses monotonic Needleman-Wunsch with an alternation bonus (validated 45/48 turns on the reference conversation).
2. **Decoding the stacked stream as one continuous flow FAILED — NO-GO.** 12 s windows cutting across speaker changes: WER 90.6% vs 86.2%, IS 1.09 vs 1.79, entity F1 31%→9%. The July-16 re-check was worse still: 36.7% of stream windows decode to EMPTY text, 86% word disagreement where both sides exist, and the green gate inverts (green stream words 3× more likely to break than fix). Related: `hyp_xseg_merge` was retired — the shipped version was a silent no-op (metadata format mismatch → 0 neighbors), and the wired version breaks 10.7× more than it fixes.
3. **What ships as "continuous flow" is presentation-layer only**: [egla_kafe_conversation_subtitle_video.py](../../scripts/pipeline/egla_kafe_conversation_subtitle_video.py) renders the per-turn decode as subtitles on the joint two-shot.

**Shipped July 16**: the guessing-game zip (412 MB, 7 videos × clean/model-read/transcript triples, MBR-anchored, audio stripped, 2 subtly marked phonetic substitutions; reference leakage impossible by construction). Cold-read scores on the good videos run 33–56%. Client path agreed July 13: guessing game → filming round 2 → wow reel for their bosses → client tells our management. The per-video topic-hints idea is untested on this footage; naive prompt injection measured NEGATIVE in March 2026 (§7), so viable routes are constrained beam decode or vocabulary-conditioned fine-tuning.

Details: [findings.md](../evaluation/egla_kafe/findings.md), [per_video_understanding.md](../evaluation/egla_kafe/per_video_understanding.md), [resolution_ablation.md](../evaluation/egla_kafe/resolution_ablation.md), [guessing_game_answer_key.md](../evaluation/egla_kafe/guessing_game_answer_key.md), [transcription_match_method.md](../evaluation/egla_kafe/transcription_match_method.md), [overlap_consistency_analysis.md](../beam-search/overlap_consistency_analysis.md).

## 7. Attempts — what was tried

| Attempt | Outcome | Where |
|---|---|---|
| 13 decode-parameter tuning experiments | No win; baseline beam=20 / lenpen=0 most robust | [docs/tuning/](../tuning/) |
| LoRA fine-tune Exp A (r=16) / Exp B (r=64) on 1,273 AVSpeech segments | Severe overfitting, data-limited; B worse than A; no Y+P improvement | [training-research-notes.md](../finetuning/training-research-notes.md) |
| N-best aggregation (Mission 6) | **SHIPPED** — 5 methods; MBR is the production default since May 2: judge Y+P 68.4%→71.1%, McNemar p=0.0002 | [n_best_implementation.md](../beam-search/n_best_implementation.md) |
| hyp_xseg_merge (cross-segment overlap merge) | **RETIRED** — shipped version a silent no-op; wired version breaks 10.7:1 | [overlap_consistency_analysis.md](../beam-search/overlap_consistency_analysis.md) |
| Phonetic substitution (Egla-Kafe) | Dual-engine agreement arm shipped (2 substitutions, GO); naive/no-engine arms destructive | [phonetic_substitution_eval.md](../evaluation/egla_kafe/phonetic_substitution_eval.md) |
| Resolution ablation 4K→2K→1080p | All pairs n.s.; framing (mouth px in frame), not pixel count | [resolution_ablation.md](../evaluation/egla_kafe/resolution_ablation.md) |
| Viseme snapping (co-work handoff) | Oracle judge-proxy +0.6pp mean, 0 harmful substitutions on Trust-tier footage; superseded by the harvest-real-N-best proposal | [HANDOFF.md](../nbest_viseme_handoff/HANDOFF.md) |
| Topic-label prompt injection | **NEGATIVE** — WER 86.6%→87.6%, 24% of bad segments echo the instruction verbatim | [topic_label_experiment.md](../prompts/topic_label_experiment.md) |

## 8. Major results (1,497-segment benchmark, MBR production default)

All numbers verified against [after_amosi_audit.md](../evaluation/after_amosi_audit.md) (2026-05-06).

| Metric | Value | Top-1 baseline |
|---|---|---|
| Mean WER | **63.8%** | 64.1% |
| Mean IS | **2.547** | 2.532 |
| NIV-Y (clearly conveyed, IS ≥ 3.80) | **23.9%** (358) | 24.0% (359) |
| NIV-Y+P (any useful, IS ≥ 2.00) | **61.9%** (927) | 61.7% (923) |
| LLM judge Y+P (v3) | **71.1%** | 68.4% |
| Hallucination rate (WER ≥ 100%) | **20.7%** | 20.5% |
| Named-entity F1 (top-1 only; not recomputed per-method) | 38.9% | 38.9% |
| Trust gate ≥ 30% green | **65.2% recall / 5.6% FPR** | (computed on top-1 confs) |

## 9. Big artifacts NOT in git — where to get them

| Item | Size | S3 copy? | Notes |
|---|---|---|---|
| `VSP-LLM/checkpoints/checkpoint_finetune.pt` | 4.1 GB | No | THE decode model — the pipeline is dead without it |
| `VSP-LLM/checkpoints/large_vox_iter5.pt` | 3.9 GB | No | AV-HuBERT encoder; public download exists but is slow |
| `VSP-LLM/checkpoints/checkpoint_freeze.pt` | 4.1 GB | No | Frozen-encoder variant |
| `VSP-LLM/checkpoints/Llama-2-7b-hf/` | 26 GB | No | Re-downloadable from HuggingFace (gated repo, needs an approved token) |
| `datasets/english_data_2025_11_20/` | 2.4 GB | **No — irreplaceable** | The benchmark itself |
| `datasets/clients/` | 9.4 GB | Partial | Egla-Kafe masters are in S3; processed runs are not |
| `~/egla_kafe/` (raw masters) | 2.8 GB | **Yes** | `conversation_datasets/egla_kafe/`, 68 objects |
| `data/` (AVSpeech) | 938 MB | No | Fine-tune set |
| `datasets/lrs3orig_sync.tar` | 136 MB | No | The only LRS3 on the box |
| `datasets/seamless_interaction/` | 1.9 GB | No (139 KB stub only) | Upload never completed |
| `english_full_results/client_outputs/` | 1.7 GB | No | Reproducible from the benchmark set |

Transfer route for datasets: `s3://conversation-datasets-733430125971` (readable from this box; writes need laptop portal credentials). Small deliverables: `s3://yoad-vsp-transfer/vsp/` (instance role can write under that prefix).

## 10. How to run things

All commands verified against the actual scripts on 2026-08-03.

**(a) End-to-end pipeline.** The script takes one required argument — the raw videos directory:

```bash
cd /home/ubuntu
./run_flat_english_pipeline.sh ~/vsp_input
```

Venvs are activated automatically. Outputs land in `~/flat_runs_archive/<run_id>/client_outputs/` — `report/report.csv`, `report/report.html`, and `burned_videos/` (subtitled MP4s). The final console summary prints the exact paths.

**(b) N-best / display method.** `VSP_NBEST` already defaults to 1, so aggregation is on for every normal run; set `VSP_NBEST=0` only on constrained machines. The displayed hypothesis defaults to `hyp_mbr` whenever `aggregated.json` exists; override with:

```bash
VSP_DISPLAY_METHOD=top1 ./run_flat_english_pipeline.sh ~/vsp_input
```

**(c) Web UI** (verified running on this box right now):

```bash
cd /home/ubuntu/vsp-ui && ./launcher.sh
```

This starts `python3 -m app.server` on `http://localhost:8765`, opens the browser, and opens `~/vsp_input/`. `./launcher.sh stop` (or killing the PID in `~/.vsp-ui.pid`) stops it.

**(d) Container deployment.** See [client-laptop-deployment-aug2026.md](client-laptop-deployment-aug2026.md) and [deploy-targets.md](deploy-targets.md).

**(e) Re-paint an old run with current bands/MBR** (no re-decode needed if the run had `VSP_NBEST=1`). Stage 8 is a sourced function — note the name is `run_client_outputs`, with six positional args:

```bash
source ~/vsp-llm-yoad-venv/bin/activate
source ~/lib/config.sh && source ~/lib/outputs.sh
run_client_outputs "$HOME/VSP-LLM" "$HOME/flat_runs_archive/<run_id>" \
  "$HOME/auto_avsr/flat" "$HOME/auto_avsr/preprocessed_flat_seg12" "flat" "seg12s"
```

(Mirror the values the main pipeline uses — see lines 517–520 of `run_flat_english_pipeline.sh`.)

**(f) Sanity check** — 37 module tests:

```bash
bash /home/ubuntu/lib/test_all_modules.sh
```

**(g) Fresh machine setup.** See [ec2-setup-from-scratch.md](ec2-setup-from-scratch.md).

## 11. Where to start

1. The three ready-to-assign training project briefs: [training_project_video_quality.md](../backlog/training_project_video_quality.md), [training_project_multi_speaker.md](../backlog/training_project_multi_speaker.md), [training_project_additivity_test.md](../backlog/training_project_additivity_test.md).
2. [mission-backlog.md](../backlog/mission-backlog.md) for the full prioritized roadmap.
3. The "Traps that will bite you" section (§6) of [project-handover-july2026.md](project-handover-july2026.md) — read it before your first change.
