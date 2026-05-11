# Llama 2 → Llama 3.1 Migration — Progress Log

**Owner:** Yoad Oxman · **Started:** 2026-05-11 · **Status:** Code prep complete; model download in progress; training pending

This log tracks the in-flight migration from Llama-2-7b-hf to Llama-3.1-8B-Instruct as the LLM decoder for VSP-LLM. Plan of record: [.claude/plans/come-up-with-a-distributed-bunny.md](../../.claude/plans/come-up-with-a-distributed-bunny.md). Rationale: [encoder-vs-llm-bottleneck.md](encoder-vs-llm-bottleneck.md).

---

## 1. Decisions made

| Decision | Choice | Why |
|---|---|---|
| Target LLM | **Llama-3.1-8B** (BASE, not Instruct) | `hidden_size=4096` (drop-in projector), same LoRA target names, smallest `transformers` bump vs current fairseq pin. **Base over Instruct**: original paper used `Llama-2-7b-hf` (base), and every 2025 VSR paper (MMS-LLaMA, VALLR, Llama-AVSR) uses base — RLHF/instruct tuning is wasted capacity here since visual features are injected via `inputs_embeds`, not as text instructions. Instruct's chat-eos list (3 ids) is also a complication we don't need. Instruct download kept as a backup for future chat-mode experiments |
| Ruled out | Qwen 3 8B, Llama 4, Gemma 3, DeepSeek-V3 | Published LRS3 VSR ablation ([arXiv 2509.14880](https://arxiv.org/html/2509.14880v1)) shows Qwen underperforms Llama at matched scale (27.2% vs 25.7% WER); others require projector resize or are too large |
| Training data | LRS3 (433h, paper-equivalent) | Matches original VSP-LLM paper recipe; well above the ~5K-segment data floor that limited the prior AVSpeech experiments |
| Training instance | **p4d.24xlarge** (8× A100 40GB) in eu-west-1 | Matches paper hardware exactly; ~$300 for the full run; user confirmed acceptable |
| Region | eu-west-1 (Ireland) | Co-located with existing EC2 (no cross-region data transfer) |
| Realistic gain | ~1-2% absolute WER, modest IS lift | LLM-choice ceiling on LRS3 is ~1.5% WER; the real bottleneck is the visual encoder — see [encoder-vs-llm-bottleneck.md](encoder-vs-llm-bottleneck.md) |

---

## 2. Code changes applied (committed)

Two-commit pattern: submodule first, then parent submodule-pointer bump.

| VSP-LLM commit | Parent commit | What |
|---|---|---|
| `7f8f5e3` | `ae25ddd` | Initial prep: `LLM_PATH` swap in train.sh (env-overridable, default Llama 3.1), pad-token guard in vsp_llm_dataset.py + vsp_llm_decode.py, label-mask uses `decoder.config.pad_token_id` in vsp_llm.py |
| `e27b11b` | `d58b524` | Llama 3 eos quirk: `config.eos_token_id` is a list `[128001, 128008, 128009]` (`<\|end_of_text\|>` / `<\|eom_id\|>` / `<\|eot_id\|>`), not a scalar. Pick `eos[0]` as canonical pad to keep tensor comparison `llm_labels == _pad_id` valid |

**Backward-compatible:** production decode still uses Llama 2. The `decode.sh` and `lib/decode.sh` `LLM_PATH` swap is intentionally deferred until a Llama 3.1 checkpoint exists and verifies — flipping those now would break production.

### Files touched

| File | Change |
|---|---|
| [VSP-LLM/scripts/train.sh:15](../../VSP-LLM/scripts/train.sh) | `LLM_PATH` defaults to `/home/ubuntu/Llama-3.1-8B-Instruct`, env-overridable |
| [VSP-LLM/src/vsp_llm_dataset.py:188-192](../../VSP-LLM/src/vsp_llm_dataset.py) | Pad-token guard after `AutoTokenizer.from_pretrained` |
| [VSP-LLM/src/vsp_llm_decode.py:131-135](../../VSP-LLM/src/vsp_llm_decode.py) | Pad-token guard after `AutoTokenizer.from_pretrained` |
| [VSP-LLM/src/vsp_llm.py:294-301](../../VSP-LLM/src/vsp_llm.py) | `decoder.config.pad_token_id` set to `eos[0]` when None (handles list-typed eos) |
| [VSP-LLM/src/vsp_llm.py:340-345](../../VSP-LLM/src/vsp_llm.py) | Label mask uses `self.decoder.config.pad_token_id` instead of hardcoded 0 |

---

## 3. HuggingFace + model setup

| Step | Status | Notes |
|---|---|---|
| Llama 3.1 license accepted | ✅ | Submitted under user's personal HF account `MrYoyoad` (not `RonKanto`). Granted by Meta on 2026-05-11 |
| HF token swapped on EC2 | ✅ | `~/.cache/huggingface/token` now holds `MrYoyoad`'s read token. Old `RonKanto` token backed up to `~/.cache/huggingface/token.RonKanto.bak` |
| Fine-grained token gated-repo permission | ✅ | Initial token failed with "Please enable access to public gated repositories" — user enabled the toggle in HF settings, retest passed |
| Instruct download to `/home/ubuntu/Llama-3.1-8B-Instruct/` | ✅ done | 30 GB on disk (16 GB safetensors + 16 GB Meta-format `consolidated.00.pth`). Kept as backup for future chat-mode experiments |
| Base download to `/home/ubuntu/Llama-3.1-8B/` | ✅ done | 15 GB (safetensors only; the redundant 16 GB Meta-format `consolidated.00.pth` deleted post-download to recover disk) |
| Sanity-check Instruct config | ✅ (preflight) | `hidden_size=4096`, `vocab_size=128256`, `eos_token_id=[128001,128008,128009]` |
| Sanity-check Base config | ✅ | `hidden_size=4096` ✓, `vocab_size=128256` ✓, `eos_token_id=128001` (scalar int) ✓, `pad_token_id=None` (guard required) |
| Python load test ([scripts/tests/llama31_load_test.py](../../scripts/tests/llama31_load_test.py)) | ✅ PASSED | Tokenizer guard, model 4-bit BnB load (27s, 5.70 GB VRAM), LoRA wrap (9.4M trainable / 0.117%), mock forward with projected visual features. Loss ≈ ln(128256) as expected for random projector. Peak VRAM 6.85 GB on T4 — comfortable. |

---

## 4. What's still pending

1. **Llama 3.1 download completes** (background task `bgufk6ego`). Then verify with the §2.3 sanity-check Python one-liner in the plan.
2. **Smoke test: 1-step training run** on the existing 1,273-segment AVSpeech manifest. Validates the transformers/fairseq compatibility and the pad-token + eos-list fixes before committing the LRS3 + p4d budget. ~30 min on the current T4.
3. **AWS quota for p4d.24xlarge in eu-west-1** — user to file if not already in place. Can run in parallel with the smoke test.
4. **LRS3 acquisition** — auto_avsr / av_hubert Drive mirror or HF mirror preferred over Oxford VGG portal (1-3 day approval). Existing `/home/ubuntu/datasets/lrs3orig_sync.tar` is partial — usable for plumbing only.
5. **`scripts/prep_lrs3_training.sh`** — ~80-line bash wrapper to route LRS3 through `lib/` modules (normalization → .transcriptions seeding → lrs3_prep → manifests → clustering). Not started yet.
6. **Training launch** on p4d.24xlarge: 30K updates against `vsp-llm-433h-freeze.yaml` recipe, batch=1×update_freq=8 across 8 GPUs. ETA ~10h, ~$300.
7. **Verification**: LRS3 test WER within ±2pp of paper's 26.7%; full 1,497-segment YouTube re-baseline; compare to top-1 (WER 64.1%, IS 2.532) baseline.
8. **Flip decode paths** (`decode.sh`, `lib/decode.sh`) to Llama 3.1 only after step 7 passes. Mirror to `vsp_linux_container_FINAL_20260217/` overlay per the EC2↔container sync rule in [CLAUDE.md](../../CLAUDE.md).

---

## 5. Quirks encountered (lessons for future LLM swaps)

1. **Use BASE not Instruct for projector training** — VSR's visual features are injected via `inputs_embeds`, bypassing the text-instruction-following pathway entirely. RLHF/instruct alignment is wasted capacity at best, harmful interference at worst (the model has to "unlearn" its preference for "Here's the transcription:" style outputs). Every published VSR system (original VSP-LLM, MMS-LLaMA, VALLR, Llama-AVSR) uses base. Caught after we initially downloaded Instruct.
2. **Llama 3 has no pad token** — Llama 2 silently used `<unk>` (id 0) as pad in the loss mask; Llama 3's tokenizer ships with `pad_token=None`. Two places need a guard: `AutoTokenizer.from_pretrained()` callsites (set `tokenizer.pad_token = tokenizer.eos_token`) AND the model's `config.pad_token_id` (set to `eos_token_id`).
3. **Llama 3 Instruct's `config.eos_token_id` is a list** — `[128001, 128008, 128009]` for end-of-text, end-of-message, end-of-turn (chat-template artifact). Base has a scalar (`128001`). HF's tokenizer abstraction returns a scalar either way (`128009` for instruct), but the model config is the raw list for Instruct. Forward-pass tensor comparisons (`llm_labels == _pad_id`) need a scalar — pick `eos[0]` (end-of-text) as the canonical pad. With Base, this is a no-op.
4. **HF fine-grained tokens default to denying gated repos** — even after the user accepts a gated license, a fine-grained token without the explicit "Read access to public gated repos" toggle returns 403. Either toggle the permission or fall back to a classic "Read" token.
5. **HF auto-approval is account-scoped, not org-scoped** — license acceptance on one account does not propagate to other accounts even within the same org. Migration required a token swap from `RonKanto` to `MrYoyoad`.

---

## 6. References

- Plan: [.claude/plans/come-up-with-a-distributed-bunny.md](../../.claude/plans/come-up-with-a-distributed-bunny.md)
- Rationale: [encoder-vs-llm-bottleneck.md](encoder-vs-llm-bottleneck.md) ([PDF](encoder-vs-llm-bottleneck.pdf))
- Prior fine-tuning experiments: [training-research-notes.md](training-research-notes.md)
- Backlog mission: [Mission 9 (AVSpeech Fine-Tuning)](../backlog/mission-backlog.md#mission-9-avspeech-fine-tuning)
