# Argos VSP — Engineering Handover (July 2026)

Written by the departing lead (Yoad Oxman) for whoever inherits this project. Everything here
is a pointer into docs that already exist — read this first, then follow the links. The single
biggest rule: **[CLAUDE.md](../../CLAUDE.md) is the hub**; when in doubt, start there.

**Aug 2026:** a compact topic briefing (IS metric, confidence, datasets + where data actually
lives, configuration, Egla-Kafe results, how-to-run) now exists at
[teammate-briefing-aug2026.md](teammate-briefing-aug2026.md) — read it right after this doc.
Environment rebuild: [ec2-setup-from-scratch.md](ec2-setup-from-scratch.md). Client redeploy:
[client-laptop-deployment-aug2026.md](client-laptop-deployment-aug2026.md).

**Reading order (day 1):** [CLAUDE.md](../../CLAUDE.md) → [docs/architecture.md](../architecture.md) →
[docs/development-guide.md](../development-guide.md) → [docs/backlog/mission-backlog.md](../backlog/mission-backlog.md) → this doc.

---

## 1. What this is

A visual speech recognition (lip-reading) pipeline: video in → per-segment English transcript
out, with per-word confidence coloring and trust tiers. Built on auto_avsr + AV-HuBERT +
VSP-LLM (Llama-2-7B + LoRA), orchestrated by `run_flat_english_pipeline.sh` over 11 `lib/`
modules, with a web UI (`vsp-ui/`) and a standalone Docker deployment for clients.

State: **working product, deployed at a client, prototype-grade model.** On 1,497 wild YouTube
segments: 71.1% of segments judged review-useful (consensus decoding, blind LLM judge),
NIV-Y+P 61.9%, mean WER 63.8%. Canonical numbers: [docs/evaluation/after_amosi_audit.md](../evaluation/after_amosi_audit.md)
(single source of truth for metric values — trust it over any slide or older doc).

## 2. Deployment reality (read before touching anything)

Three targets with different roles — full doctrine in [docs/guides/deploy-targets.md](deploy-targets.md):

| Target | Role | Sync rule |
|---|---|---|
| `/home/ubuntu/` (EC2) | source of truth, dev + eval | every commit |
| `vsp_linux_container_FINAL_20260217/` | patch overlay for running containers — **primary deploy route** | sync EVERY shipped change, byte-identical (`cmp`) |
| `vsp_docker/galaxy_export/` | Docker build context for fresh images | **intentionally stale** — sync only at a planned rebuild (checklist in deploy-targets.md) |

- Ship **one clean Docker image** per release (one tag, one tarball). No layered FROM-previous
  patches — they confuse operators.
- Client machine: Windows 11 + RTX 5090, **air-gapped**. First run JIT-compiles CUDA kernels
  (5–15 min, looks frozen — it isn't). Hard-won Windows/PowerShell traps:
  [docs/guides/container-deployment-lessons-may2026.md](container-deployment-lessons-may2026.md).
- Sync debt: [docs/container-sync-changelog.md](../container-sync-changelog.md) (~28 nominal
  pending items; many already mirrored — verify with `cmp`, the changelog numbering is messy).
- Intentional EC2-only feature: IS scoring (`--compute-is`) — heavy deps excluded from container.
- Submodule caveat: `galaxy_export/VSP-LLM` tracks upstream `Sally-SH/VSP-LLM`; EC2 tracks the
  fork `MrYoyoad/VSP-LLM`. VSP-LLM `.py` changes reach galaxy_export only via file copy.

## 3. Clients and open commitments

- **Egla-Kafe client** (the July 2026 meeting): evaluation complete —
  [docs/evaluation/egla_kafe/findings.md](../evaluation/egla_kafe/findings.md); deliverables at
  `datasets/clients/egla_kafe/deliverables/` (decks, per-video PDF, 21 subtitle videos).
  Asks made at the meeting: adopt the capture protocol, **export original camera files**
  (their footage was viewer-app screen recordings — see findings.md § File forensics),
  re-shoot pilot, data contribution, next-phase green-light.
  **If native files arrive: re-run the eval** — repeatable pipeline, guide at
  [docs/guides/client-lipread-eval.md](client-lipread-eval.md)
  (`scripts/pipeline/client_lipread_eval.py`). Days, not weeks.
- **"100 hours" group**: a second interested group handed over ~100h of real footage for
  evaluation ([docs/evaluation/Q2-2026-summary.md](../evaluation/Q2-2026-summary.md)).
- **Top client feature asks**: multi-speaker (M12) and Arabic (M11).

## 4. Open bets and their blockers

1. **Llama 3.1 8B migration** — the main in-flight engineering bet.
   Code ready and smoke-tested end-to-end on a T4 (fairseq 2-update run); both models
   downloaded (Base 15GB for training, Instruct backup). **Blocked on**: (a) LRS3 dataset no
   longer publicly downloadable — being sourced out-of-band; fallback is AVSpeech-only at
   20K+ segments (loses paper-equivalence); (b) AWS p4d.24xlarge quota, eu-west-1
   (~$300, ~10h run). Status + exact next commands: [docs/finetuning/llama3-migration.md](../finetuning/llama3-migration.md).
   Honest expectation: the swap alone is worth ~1–2pp WER; the real unlock is what it enables
   (prompt/context injection + domain-data scaling) — [docs/evaluation/llm_upgrade_analysis.md](../evaluation/llm_upgrade_analysis.md).
2. **M4.1 confidence calibration** — pending a real B3 GPU decode to produce non-synthetic
   confidence sidecars (~1 day GPU + 2h analysis).
3. **Fine-tuning**: two LoRA experiments concluded **data-limited, not model-limited**
   (1,273 segments ≪ the ~20K needed). Don't repeat small-data LoRA runs —
   [docs/finetuning/training-research-notes.md](../finetuning/training-research-notes.md) §8 has the corrected priority order.

## 5. Ready-to-assign work

Three scoped 5-day project briefs (May 2026), written as onboarding-friendly projects —
ideal first assignments for a new researcher:

- **Video-quality pre-filter** (M15, HIGH, no dependencies): [docs/backlog/training_project_video_quality.md](../backlog/training_project_video_quality.md)
- **Multi-speaker attribution** (M12, client-requested): [docs/backlog/training_project_multi_speaker.md](../backlog/training_project_multi_speaker.md)
- **Signal-additivity test** (M4.2, methodology): [docs/backlog/training_project_additivity_test.md](../backlog/training_project_additivity_test.md)

Full roadmap with phases and effort estimates: [docs/backlog/mission-backlog.md](../backlog/mission-backlog.md).

## 6. Traps that will bite you

- **`lib/decode.sh` Cython check must never be removed** — fairseq's `data_utils_fast` needs a
  build on first container run; decode fails without it.
- **Transcription manager is a disk-backed singleton** — every mutating/reading method must
  `_load_metadata()` first, or out-of-band `.wrd` writes get silently wiped.
- **Old runs vs new features**: videos decoded with `VSP_NBEST=1` can be upgraded to
  MBR-display + agreement-aware bands by re-running stage 8 (`lib/outputs.sh`) — no re-decode.
  Videos without those artifacts need a re-decode.
- **Input-boundary changes** (new file types, host paths, env vars) must be tested with real
  fixtures end-to-end before shipping — the failure mode is "not accepted at all", which no
  existing test covers.
- **Client materials discipline**: numbers follow the N1–N10 rules in
  [docs/CLIENT_MEETING_FRAMING.md](../CLIENT_MEETING_FRAMING.md) (no WER/κ/jargon on visible
  slides); tier colors green/yellow/red are reserved for TRUST/SALVAGE/STRIP; **never review a
  PPTX via PDF conversion** — PowerPoint render is authoritative, use audit scripts +
  python-pptx; deck style rules in [docs/_research-tools/generators/STYLE_GUIDE.md](../_research-tools/generators/STYLE_GUIDE.md).
- **Confidence thresholds are Llama-2-specific** (T_safe=0.82, strip<0.65, band rules) — any
  LLM swap requires re-running `diagnose_confidence_signals.py` before trusting the colors.
- **S3**: instance IAM role only (account 733430125971), no FUSE mounts; `aws` CLI or `s5cmd`;
  `export LC_ALL=C.UTF-8` when keys contain Hebrew.
- **Non-technical client vocabulary**: "restart"/"frozen"/"loading"/".mtk" map to specific UI
  states and formats — always ask "what exactly is on screen?" before diagnosing.

## 7. Environment

- EC2 box `/home/ubuntu`: venvs — `~/vsp-llm-yoad-venv` (decode, reports, pptx),
  `auto_avsr` pre-process venv (Blackwell-native cu128), ASR venv (Whisper). GPU on-box.
- Hugging Face token (Llama license) is configured in the standard HF cache/env on this box —
  verify with `huggingface-cli whoami`; it is deliberately not written down here.
- Tests: `bash lib/test_all_modules.sh` (37 tests) — run after any `lib/` change.

## 8. Successor's first week

1. Read the reading-order docs (top of this file); run `lib/test_all_modules.sh`.
2. Run one video end-to-end through `run_flat_english_pipeline.sh` on EC2; open the HTML report.
3. Read [deploy-targets.md](deploy-targets.md); `cmp` a few overlay files against EC2 to see
   the sync mechanic in practice.
4. Read the Egla-Kafe findings + the July meeting outcomes; **own the client follow-ups**
   (original-file export, re-shoot pilot, data ask).
5. Take the video-quality 5-day project (M15) as your onboarding ramp — it was scoped for
   exactly this purpose and has no dependencies.

## Update — July 16-20, 2026 (post-handover work)

Work done after the July-13 departure snapshot (details in the three 2026-07-16 entries of
[docs/sessions/HANDOVER.md](../sessions/HANDOVER.md)):

- **Guessing-game client package shipped (Jul 16)**:
  `datasets/clients/egla_kafe/deliverables/EglaKafe_guessing_game_20260716.zip` (412 MB) —
  7 videos × (clean / model_read / transcript.html) + README. MBR-anchored word confidence,
  audio stripped everywhere (`-an`), leakage-proof (QA greps clean on all .ass/.html).
- **Phonetic substitution — GO for the agreement arm only**
  ([phonetic_substitution_eval.md](../evaluation/egla_kafe/phonetic_substitution_eval.md)):
  the dual-engine agree arm shipped exactly 2 substitutions (`figured`→`forgot°`, `on`→`of°`,
  both s1_tomer_yoad_1, marked with °); all ship-gate clauses pass. The naive max-mass arm is
  actively destructive (breaks ≫ fixes) — never ship it.
- **Resolution ablation — resolution is not the lever**
  ([resolution_ablation.md](../evaluation/egla_kafe/resolution_ablation.md)): 4K → 2K → 1080p,
  same 175 segments, no significant difference on any metric (all paired tests n.s.). Mechanism:
  the affine warp normalizes every mouth to a ~45 px canonical width inside the fixed 96×96
  crop — 4K's extra pixels are discarded at input. Client guidance is **framing** (mouth ≥50 px,
  ideally ≥100 px) and capture-chain cleanliness, not resolution. Companion lip-pixel probe:
  only img_6825 reaches ≥96 px mouth width even at 4K.
- **N-best / viseme handoff (inbound cowork)**
  ([docs/nbest_viseme_handoff/HANDOFF.md](../nbest_viseme_handoff/HANDOFF.md)): oracle viseme
  snapping is safe and mildly useful on Trust-tier footage only (+8.2 pp content-word recall on
  img_6825, 0 harmful subs on the 6 best videos), useless-to-harmful on weak footage. Proposal:
  harvest the real pre-MBR N-best the decoder already generates instead of reconstructing
  candidates. Related finding
  ([overlap_consistency_analysis.md](../beam-search/overlap_consistency_analysis.md)):
  `hyp_xseg_merge` was a **silent no-op** on the 1,497 set — retire it; stream-window decode
  is a NO-GO.
- **LRS3 search exhausted (Jul 16)**: the full LRS3-TED dataset (~270 GB) is **not** on this box
  or in either account S3 bucket — only the 136 MB / 198-video sample tar
  (`datasets/lrs3orig_sync.tar`). Llama-3.1 migration remains blocked on it; next steps are
  off-box (email/Drive/colleagues). See [llama3-migration.md](../finetuning/llama3-migration.md) §4.
- **Amosi continuation deck**: `presentation_materials_20260224/Argos_VSP_v13_Amosi_2_generated.pptx`
  plus the ProjectFuture 20260720 deck (`Argos_VSP_ProjectFuture_20260720.pptx`, commit `573393b`).

Environment/deployment guides added Aug 3 2026 (see pointer at top of this doc).
