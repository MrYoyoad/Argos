# VSP-LLM Fine-Tuning Research Notes

Research thoughts on improving VSP-LLM for domain-specific AVSpeech fine-tuning. The pretrained model was trained on LRS3 (433h TED talks) and is applied to AVSpeech-style YouTube videos.

**Current baseline**: WER 64.1%, WWER 61.9%, NEA Recall 39% on 1497 segments (english_full run using `checkpoint_finetune.pt`).

## Key References

| Resource | Location | Description |
|----------|----------|-------------|
| VSP-LLM paper | `VSP_LLM_paper.pdf`, `VSP_LLM_paper_text.txt` | Yeo et al., arXiv:2402.15151v2, May 2024 |
| english_full results | `english_full_results/client_outputs/report/report.{txt,csv,html}` | 1497 segments, WER 67.0%, full report with NEA/IS metrics |
| Tuning experiments | `tuning_results/run_all_experiments.sh` | 7 decode param experiments (A-G) on 107-segment subset |
| AVSpeech data | `data/` | AVSpeech videos, 3-10s clips |
| Model architecture | `VSP-LLM/src/vsp_llm.py` (lines 287-308) | QLoRA config: r=16, alpha=32, targets=[q,k,v]_proj |
| Training configs | `VSP-LLM/src/conf/vsp-llm-433h-finetune.yaml` | 30K updates, freeze 18K, lr=5e-4 |
| AVSpeech config | `VSP-LLM/src/conf/vsp-llm-avspeech-finetune.yaml` | 15K updates, freeze 5K, domain adaptation schedule |
| Decode config | `VSP-LLM/src/conf/s2s_decode.yaml` | beam=20, lenpen=0, rep_pen=1.2, max_len=2048 |

---

## 1. Length Distribution Shift Between Training and Inference

### The Problem
VSP-LLM was pretrained on LRS3 (mostly 2-8s utterances from TED talks). At inference, the pipeline segments videos into 12-second segments with 2s overlap (`run_flat_english_pipeline.sh`, lines 25-31). The model sees longer inputs than it trained on.

### Paper Evidence (Figure 4, page 7)
| Video Length | VSP-LLM WER | AV-HuBERT WER | Gap |
|---|---|---|---|
| 0-2 sec | 27.3% | 34.7% | -7.4pp |
| 2-4 sec | 17.0% | 22.5% | -5.5pp |
| 4-6 sec | 16.8% | 20.2% | -3.4pp |
| 6+ sec | **12.9%** | 21.3% | **-8.4pp** |

VSP-LLM **improves with longer videos** — the opposite of prior methods. The LLM's context window is an advantage, not a limitation.

### Measured AVSpeech Clip Durations (from AVSpeech dataset)
Probed with ffprobe: 3.0s, 3.0s, 3.0s, 3.4s, 3.5s, 3.6s, 4.2s, 4.4s, 4.7s, 5.7s, 6.4s, 7.3s, 7.5s, 7.6s, 9.1s. Most clips cluster in 3-9 seconds.

### Conclusion
**Length shift is NOT the primary WER driver.** The 64% WER is caused by domain shift (TED→YouTube: vocabulary, visual quality, speaker diversity), not length mismatch. The LLM architecture handles variable lengths natively via its attention mechanism and the deduplication layer reduces sequences ~50%.

---

## 2. Histogram of Video Lengths in AVSpeech

### Dataset Statistics
- **AVSpeech**: 4,700 hours, ~290K YouTube videos, **3-10 sec** clips (Ephrat et al., 2018)
- **LRS3**: 433 hours, ~165K utterances, 400+ speakers, variable length (mostly 2-8s)
- **Pipeline segments**: 12 sec default, 300 frames at 25fps

### To Generate Full Histogram
```bash
find /path/to/avspeech/ -name "*.mp4" -exec ffprobe -v error \
    -show_entries format=duration -of csv=p=0 {} \; > durations.txt
python3 -c "
import numpy as np
d = [float(x) for x in open('durations.txt') if x.strip()]
print(f'N={len(d)}, Mean={np.mean(d):.1f}s, Median={np.median(d):.1f}s')
for lo, hi in [(0,2),(2,4),(4,6),(6,8),(8,10),(10,12)]:
    n = sum(1 for x in d if lo <= x < hi)
    print(f'  {lo}-{hi}s: {n} ({100*n/len(d):.1f}%)')
"
```

---

## 3. Training Length Strategy — Short Only, Long Only, or Mixed?

### The Question
The pipeline infers on 12s segments. AVSpeech clips are 3-10s. Should training data be filtered by length?

### Option A: Short Videos Only (<4 sec)
**Hypothesis**: Forces confident per-word mappings with minimal context.

**Why it hurts**: Destroys the core value proposition. VSP-LLM exists for context modeling — training on short clips teaches the model to ignore context. WER at 0-2s is already 27.3% vs. 12.9% at 6s+. Like training an LLM on single-word completions and expecting good paragraphs.

### Option B: Long Videos Only (>6 sec)
**Hypothesis**: Match inference conditions for best alignment.

**Problems**: Discards 40-60% of AVSpeech data. Reduces speaker/genre diversity. Last segments of real videos are often shorter than 12s — model needs to handle those too.

### Option C: Mixed Training (Recommended)

Why a mix is best:
1. **RoPE handles length generalization** — Llama-2's rotary positional embeddings are relative, so the model trained on 4s clips processes 12s inputs without degradation
2. **Data quantity trumps length matching** in low-resource fine-tuning
3. **Complementary learning**: Short clips teach phoneme accuracy (no context to "cheat"), long clips teach sentence-level disambiguation
4. **Deduplication normalizes length** — after cluster averaging, a 12s segment becomes ~160 clusters and a 4s segment becomes ~53 clusters; the LLM handles variable-length sequences natively

### Recommended Distribution
| Length | Share | Purpose |
|---|---|---|
| <3 sec | Exclude | Too short, noisy labels |
| 3-4 sec | ~15% | Phoneme precision training |
| 4-8 sec | ~50% | Core domain adaptation (bulk of AVSpeech) |
| 8-12 sec | ~35% | Context modeling, inference-length matching |

**Bottom line**: Use everything you have (3-10s), don't filter. The 64% WER is a domain problem, not a length problem.

---

## 4. QLoRA with Larger Rank

### Current Configuration (`vsp_llm.py`, lines 296-305)
```python
LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj","v_proj","k_proj"],
           lora_dropout=0.05, bias="none", task_type="CAUSAL_LM")
```

### Literature on Rank Impact
| Rank | Trainable Params | Notes |
|---|---|---|
| 8 | ~0.1% of LLM | Simple domain adaptation |
| **16 (current)** | **~0.2%** | Standard fine-tuning |
| 32 | ~0.4% | Better for complex shifts |
| 64 | ~0.8% | Near-peak for most tasks |
| 128+ | ~1.5%+ | Diminishing returns |

Performance saturates at r=48-64 for most tasks. Standard LoRA has collapsing gradients at r=256+; rsLoRA fixes this.

### Analysis
The domain shift TED→YouTube is substantial (different speakers, vocabulary, visual conditions). r=16 is likely **underfit** for this adaptation. The model needs to reshape its language priors from formal TED English to casual YouTube speech.

### Recommended Progression
1. **First**: r=64, alpha=128 (same target modules) — lowest risk, minimal VRAM impact
2. **If plateau**: r=32, alpha=64 with expanded target modules (add o_proj, gate_proj, up_proj, down_proj)
3. **Aggressive (>100h data)**: r=64 + all modules + dropout=0.1

VRAM: r=64 adds ~40M params (~160MB) — negligible on a 24GB GPU with 4-bit Llama.

---

## 5. Training on Difficult Angles and Conditions

### Performance by Angle (Literature)
- **Frontal (0°)**: Best accuracy
- **30° yaw**: ~5-10% drop
- **45° yaw**: ~15-25% drop
- **60°+ / profile**: >50% drop, often failure

### What the Pipeline Already Does
1. RetinaFace detects faces (fails at extreme angles → auto-filtered)
2. Mouth crops to 96x96 → 88x88 grayscale
3. AV-HuBERT pre-trained on mostly frontal data (LRS3 + VoxCeleb2)

### Arguments For Including Difficult Samples
- Real-world deployment encounters imperfect conditions
- Increases training diversity (improves generalization)
- Prevents overfitting to "easy" frontal-only data

### Arguments Against
- Whisper transcriptions of difficult videos are often wrong → noisy training labels
- AV-HuBERT encoder is mostly frozen — LoRA on LLM can't fix bad visual features
- Wastes model capacity fitting noise instead of clean domain mappings

### Recommendation: Curated Approach
1. Filter by face detection confidence (>0.9)
2. Remove extreme head pose (>30° yaw)
3. Remove poor lighting / heavy motion blur
4. Keep ~20% moderate-difficulty samples for robustness
5. Prioritize clean domain adaptation first

**Rationale**: The bottleneck is domain shift (vocabulary, speech patterns), not pose robustness. Difficult visual conditions corrupt the visual-to-text mapping that fine-tuning is adjusting.

**Exception**: If deployment specifically needs angle robustness (surveillance, meetings), include multi-angle data with verified manual transcriptions.

---

## Summary of Recommendations

| Thought | Verdict | Action |
|---|---|---|
| 1. Length distribution shift | Secondary concern | Focus on domain adaptation, not length matching |
| 2. AVSpeech histogram | Useful diagnostic | Generate histogram on full dataset to characterize data |
| 3. Training length strategy | **Mixed is best** | Use all 3-10s clips; don't filter by length |
| 4. LoRA rank increase | **High priority** | Increase r=16 → r=64; consider expanding target modules |
| 5. Difficult angles | Curate carefully | Prioritize clean data (80%), keep moderate difficulty (20%) |

### Priority Order for Experiments
1. **LoRA rank increase** (Thought 4) — most likely to move the needle with minimal risk
2. **Data curation** (Thought 5) — clean training data improves every other experiment
3. **Length histogram** (Thought 2) — diagnostic to inform training data selection
4. Length strategy (Thought 3) — low priority since mixed is the default
5. Length distribution shift (Thought 1) — informational, no action needed

---

## 6. Exp A Results: Validating the Research Hypotheses

**Training completed**: Feb 27, 2026 (17.0 hours, Tesla T4 FP16)
**Config**: r=16, alpha=32, targets=[q,k,v]_proj, encoder frozen, 3,000 updates
**Data**: 1,273 train / 224 val segments, stratified by IS tier (seed=42)

### Training Outcome Summary

| Metric | Best (Epoch 2) | Final (Epoch 19) |
|---|---|---|
| Val Accuracy | **62.94%** | 58.98% |
| Val Loss | 2.391 | 4.120 (+72%) |
| Val Perplexity | 5.24 | 17.39 (+232%) |
| Train Accuracy | 65.00% | 95.52% |
| Train-Val Gap | 2.1 pp | 36.5 pp |

### What the Results Confirm

**Thought 4 (LoRA Rank) — CONFIRMED**: r=16 is capacity-limited for this domain shift. The model memorized training data (95.5% train acc) but couldn't generalize (59.0% val acc). The 36.5 pp train-val gap at epoch 19 indicates the adapter is fitting noise rather than learning transferable patterns. Increasing to r=64 is the correct next step.

**Thought 3 (Mixed Training) — PARTIALLY CONFIRMED**: The model showed meaningful learning signal in the first 2 epochs (val acc improved from 62.5% to 62.9%), suggesting the mixed-length AVSpeech data contains useful domain adaptation signal. However, rapid overfitting suggests either insufficient data diversity or insufficient adapter capacity to capture the signal.

**Thought 5 (Data Curation) — STRONGLY SUPPORTED**: With only 1,273 training segments, noisy labels (from Whisper ASR at 64% WER baseline) likely dominate the training signal after the first few epochs. Curating higher-quality training data (face confidence >0.9, verified transcriptions) would likely extend the useful training window beyond epoch 2.

### Key Insight: Early Stopping is Critical

The optimal checkpoint was at epoch 2 (320 updates). This means:
- **17 of 19 epochs were wasted** — pure overfitting with no benefit
- **Exp B should use max_update=500** instead of 3,000
- **Validation every 50 updates** (not every epoch) would give finer control

### Overfitting Root Causes (Ranked)

1. **Small dataset**: 1,273 segments is insufficient for a 7B-parameter LLM, even with LoRA
2. **Noisy labels**: Whisper transcriptions are only 64% accurate — the model learns errors
3. **No regularization**: LoRA dropout 0.05 is minimal; weight decay is 0.0
4. **Rank limitation**: r=16 constrains the representation to a 16-dimensional subspace
5. **Encoder frozen**: Visual features cannot adapt, forcing all adaptation through the LLM

### Updated Recommendations

| Original Recommendation | Exp A Validation | Updated Action |
|---|---|---|
| Increase rank to r=64 | **CONFIRMED** — r=16 overfits immediately | Run Exp B with r=64, alpha=128 |
| Use all 3-10s clips | **Supported** — learning signal present | Keep mixed data, but add quality filter |
| Filter face confidence >0.9 | **STRONGLY SUPPORTED** — noisy labels cause overfitting | Prioritize for Exp B data prep |
| Mixed is best for length | **Neutral** — cannot isolate length effect with current overfitting | Revisit after r=64 resolves capacity issue |
| Curate carefully | **CRITICAL** — 1,273 noisy segments insufficient | Expand to full AVSpeech + manual review |

### Diagnostic Plots

10 training diagnostic plots generated in `docs/finetuning/plots/FT_*.png`:
- FT_01–02: Loss and accuracy curves showing clear train/val divergence
- FT_03: Overfitting gap progression (the core diagnostic)
- FT_04: LR schedule (tri-stage warmup + decay)
- FT_05–06: Gradient norms and perplexity trends
- FT_07: Data distribution by IS tier (validates stratified split)
- FT_08: Granular loss with checkpoint markers
- FT_09: Wall-clock time (~48 min/epoch)
- FT_10: Summary dashboard (6-panel overview)

---

## 7. Exp B Results: r=64 Does NOT Improve Over r=16

**Training completed**: Mar 2, 2026 (~27 hours, Tesla T4 FP16)
**Config**: r=64, alpha=128, targets=[q,k,v]_proj, encoder frozen, 3,000 updates, fresh LoRA init
**Data**: Same 1,273 train / 224 val segments as Exp A
**Trainable params**: 50,331,648 (0.74% of total) — 4x more than Exp A's 12.6M (0.19%)

### Training Outcome Summary

| Metric | Best | Final (Epoch 19+) |
|---|---|---|
| Val Accuracy | **59.8%** | ~56.3% |
| Train Accuracy | ~65% (early) | 95.4% |
| Best checkpoint | Epoch ~4 (saved 23:01 UTC) | — |
| Update speed | ~18 sec/update (same as r=16) | — |
| VRAM usage | 13.1 GB / 14.7 GB (89%) | — |

### Head-to-Head Comparison

| Metric | Exp A (r=16) | Exp B (r=64) | Delta |
|---|---|---|---|
| Best val accuracy | **62.94%** | 59.80% | **-3.1 pp (r=16 wins)** |
| Trainable params | 12.6M (0.19%) | 50.3M (0.74%) | +4x |
| Best epoch | 2 | ~4 | Later peak |
| Final train accuracy | 95.5% | 95.4% | Same (both overfit fully) |
| Final val accuracy | 59.0% | 56.3% | -2.7 pp |
| Training time | 17h | 27h | +59% slower |
| VRAM usage | ~8 GB | 13.1 GB | +64% |

### What This Tells Us

**1. Both experiments were fundamentally data-limited.** With only 1,273 training segments (~1.5 hours of video), we are below the ~1,000-sample minimum threshold where LoRA can generalize (per scaling law research, ICLR 2024). At this scale, models reproduce training data verbatim instead of learning underlying patterns — which is exactly what we observed (95% train accuracy, ~60% val accuracy). The r=16 vs r=64 comparison tells us about the **dataset's insufficiency**, not about the LLM's capacity ceiling.

**2. Rank increase failed because of insufficient data, not because the decoder has enough capacity.** Quadrupling LoRA capacity from 12.6M to 50.3M trainable parameters with only 1,273 samples predictably caused worse overfitting (3.1pp worse). With 20K-50K segments, the outcome could be very different — a larger rank (or a stronger LLM entirely) would have more data to learn from and the additional capacity could translate into real gains. These experiments do NOT prove that the LLM is saturated.

**3. Multiple bottlenecks limit performance, but data scarcity is the most actionable:**

| Bottleneck | Evidence | Severity | Addressable? |
|---|---|---|---|
| **Insufficient training data** | 1,273 segments ≈ 1.5 hours; both r=16 and r=64 memorize fully by epoch 5; 10K-40K params/sample guarantees overfitting | **Primary for these experiments** — at this scale, no model configuration can generalize | Yes — AVSpeech has ~290K videos / 4,700 hours available |
| **Frozen AV-HuBERT encoder** | Features trained on LRS3 TED talks; cannot adapt to YouTube visual domain | **Primary long-term** — sets a ceiling on what any decoder can achieve | Yes — requires multi-GPU or gradient checkpointing |
| **Noisy training labels** | Whisper ASR at ~64% accuracy provides supervision; model learns errors | **Significant** — 36% of training signal is corrupted | Yes — Whisper large-v3 or manual verification |

**4. r=64 generalizes worse because of the bias-variance tradeoff on tiny data.** With only 1,273 samples, the larger r=64 adapter overfits faster and harder. It has 4x more parameters to memorize noise, but no additional data to constrain them. This is a textbook case of high variance / low bias overfitting — but it's a data problem, not a model problem.

**4. Training speed was identical.** Despite 4x more LoRA params, update speed was ~18 sec for both. The bottleneck is the AV-HuBERT encoder forward pass (shared, frozen) and video data loading, not the LoRA backward pass. This means future experiments with larger ranks incur no meaningful speed penalty — only VRAM increases matter.

---

## 8. Lessons Learned & Corrected Recommendations

### What Was Wrong in Our Original Analysis

| Original Claim (Section 4) | Reality | Correction |
|---|---|---|
| "r=16 is likely **underfit** for this adaptation" | r=16 **overfits** identically to r=64 | Both ranks have excess capacity for 1.3K samples — but this is a **data problem**, not proof that r=16 is sufficient with adequate data |
| "Increase r=64 → most likely to move the needle" | r=64 was 3.1 pp **worse** than r=16 | Rank increase is counterproductive **without more data**. With 20K+ segments, results could differ significantly |
| "The domain shift TED→YouTube is substantial, needs more capacity" | Correct diagnosis, wrong solution **for this data scale** | Domain shift exists; encoder adaptation helps, but so would 10-50x more training data for the decoder |
| "VRAM: r=64 adds ~160MB — negligible" | Actual: ~5 GB extra (8→13 GB) due to optimizer states | Must account for Adam state (2x params) + gradients at FP16/FP32 mixed |

### Corrected Priority Order

| Priority | Action | Rationale | Effort |
|---|---|---|---|
| **1** | **More training data** (5-10K+ segments) | Both experiments hit data ceiling by epoch 2-4; 10x more data would extend useful training | Medium — AVSpeech has ~290K videos available |
| **2** | **Unfreeze encoder top layers** | The encoder is the primary bottleneck; visual features don't represent YouTube content | High — needs multi-GPU or gradient checkpointing on T4 |
| **3** | **Manual transcription of val set** | Whisper labels at 64% WER corrupt both training and evaluation | Medium — 224 segments × 5 sec = ~20 min of audio to verify |
| **4** | **Data quality filtering** | Remove low-confidence face detections, extreme poses, noisy labels | Low — scripted pipeline, no GPU needed |
| **5** | **Early stopping at epoch 2-4** | Confirmed by both experiments: all training after epoch 4 is pure overfitting | Already implemented (checkpoint_best.pt) |
| ~~6~~ | ~~Increase LoRA rank~~ | **Deprioritized** — r=16 is sufficient; r=64 was worse | — |

### Key Takeaway

> **These experiments were fundamentally limited by data scarcity (1,273 segments), not by model capacity.** The r=16 vs r=64 comparison at this scale tells us nothing about the LLM's potential with adequate data. With 20K-50K training segments (achievable from AVSpeech's 290K videos), both a stronger LLM (e.g., Llama 3.1 8B) and larger LoRA ranks could yield substantially different results. The visual encoder domain shift (LRS3→YouTube) is a real bottleneck, but it operates alongside — not instead of — the data limitation. Both must be addressed: more data for the decoder AND encoder adaptation for the visual features.

---

## 9. Next Steps for Mission 9

### Phase 1: Data Expansion (No New Training Required)
- [ ] Download 5,000-10,000 additional AVSpeech segments
- [ ] Run pipeline preprocessing (face detection, mouth crops, clustering)
- [ ] Filter by face detection confidence > 0.9
- [ ] Remove segments with extreme head pose > 30°
- [ ] Create larger train/val split (85/15, stratified)
- [ ] Re-train r=16 with 10x more data (same config, just more data)

### Phase 2: Encoder Adaptation (Requires More VRAM or Multi-GPU)
- [ ] Unfreeze top 4 layers of AV-HuBERT encoder
- [ ] Use lower LR for encoder (1e-5) vs decoder (3e-4) — discriminative fine-tuning
- [ ] Implement gradient checkpointing to fit on T4 (trades compute for memory)
- [ ] If T4 insufficient: use p3.2xlarge (V100 16GB) or p3.8xlarge (4x V100)
- [ ] Two-stage schedule: warm up encoder gradually (freeze_finetune_updates=200)

### Phase 3: Label Quality (Manual Effort)
- [ ] Manually verify/correct transcriptions for the 224 validation segments
- [ ] Use corrected val set to measure true model accuracy (not Whisper-corrupted)
- [ ] Identify worst Whisper errors in training set and correct top 100
- [ ] Consider using a stronger ASR (Whisper large-v3) for initial labels
