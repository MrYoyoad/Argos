# Mission Backlog

Tracking completed missions and the prioritized backlog of future work for the Argos VSP pipeline. Backlog items are informed by the 6 research reports (in `docs/evaluation/`, `docs/tuning/`, `docs/prompts/`, `docs/confidence/`, `docs/beam-search/`, `docs/finetuning/`) and operational experience.

**Current baseline** (english_full run, 1497 segments): WER 67.0%, Corpus WER 125.5%, NEA F1 38.8%

---

## Completed Missions

### Mission 1: Modular Pipeline Refactoring
- **Status**: COMPLETE (January 2026)
- **Summary**: Refactored monolithic 823-line pipeline into 11 reusable modules under `lib/`
- **Result**: 52% line reduction, 37 tests, environment-aware EC2/container detection
- **Tag**: `refactor-v1.0`

### Mission 2: EC2/Container Sync
- **Status**: ONGOING
- **Summary**: Synchronize all EC2 changes to the Linux container production environment
- **Tracking**: [container-sync-changelog.md](../container-sync-changelog.md) (28 pending items)

### Mission 3: VSP-LLM Max Length Fix
- **Status**: COMPLETE / EXPERIMENTAL (January 29, 2026)
- **Summary**: Fixed early prediction cutoff by adjusting `max_len_a` (1.0 -> 2.0) and `max_len_b` (0 -> 200)
- **Detail**: [MISSION3_MAX_LEN_FIX.md](../changelog/MISSION3_MAX_LEN_FIX.md)

---

## Phased Roadmap

| Phase | Missions | Theme | Expected Cumulative WER |
|-------|----------|-------|------------------------|
| **1 - Quick Wins** | 4, 5, 7 | Confidence scores, metrics, hyperparams | ~55-60% |
| **2 - Medium Effort** | 6, 8 | N-best aggregation, prompt engineering | ~45-55% |
| **3 - Training** | 9 | AVSpeech fine-tuning (biggest single gain) | ~42-52% |
| **4 - Deployment** | 10, 11 | Horizon container, Arabic support | — |
| **5 - Advanced** | 12, 13, 14 | Multi-speaker, streaming, auto-tuning | — |

---

## Backlog

### Mission 4: Confidence Scoring & Quality Filtering
- **Priority**: CRITICAL
- **Goal**: Surface model confidence scores so we can separate good predictions from bad — currently impossible without ground truth (best heuristic: 24% precision)
- **Items**:
  - Extract sequence-level log-probabilities from fairseq sequence generator during decode
  - `fairseq/sequence_generator.py` already tracks `positional_scores` — need to propagate to report stage
  - Add `output_scores=True` to `decoder.generate()` call
  - Compute segment-level confidence (mean/min token probability, beam score)
  - Add confidence field to JSON report output (`report.json`)
  - Flag low-confidence segments in client report (HTML/CSV) for human review
  - Enable quality filtering: discard segments below confidence threshold
- **Expected Impact**: Sequence score correlation with WER: r = -0.4 to -0.6 (vs. current 0.17 from heuristics). Directly solves the "can we trust this output?" problem
- **Effort**: Phase 1 (sequence-level): 2-4 hours; Phase 2 (token-level with color-coded words): 1-2 days
- **Research**: [Report 4 - Confidence Scoring](../confidence/report_4_confidence_scoring.md)

---

### Mission 5: Expanded Metrics & Evaluation
- **Priority**: HIGH
- **Goal**: Add richer evaluation metrics beyond WER/WWER/NEA to better understand model behavior and track improvement across missions
- **Items**:
  - Character Error Rate (CER) — captures partial-word correctness missed by WER
  - BLEU / METEOR scores — n-gram overlap metrics, useful for fluency assessment
  - Per-phoneme / per-viseme accuracy — measure lip-reading at the visual unit level
  - Confidence distribution histograms — show how "sure" the model is across segments
  - Length ratio analysis — compare hypothesis vs reference token counts per segment
  - Silence / empty-prediction rate tracking (currently 20.6% of segments are catastrophic WER >= 100%)
  - Quality tier distribution (perfect/good/fair/poor/catastrophic) as a dashboard metric
- **Baseline**: WER 67.0%, WWER 61.9%, NEA Recall 39%, NEA F1 38.8%. Quality: 53.4% poor, 20.6% catastrophic
- **LLM Salvage Finding** (March 2026): 165 of 900 metric-failed segments (18.3%) are LLM-salvageable — effective capture rate is 50.9% (not 39.9%). See [LLM Salvage Analysis](../evaluation/llm_salvage/llm_salvage_analysis.md)
- **Research**: [Report 1 - Executive Assessment](../evaluation/report_1_executive_assessment.md) (baseline analysis)

---

### Mission 6: N-Best / Beam Aggregation (ROVER & MBR)
- **Priority**: HIGH
- **Goal**: Stop discarding 19 of 20 beam candidates — use them for consensus voting and confidence estimation
- **Items**:
  - Save top-N hypotheses + scores from beam search (currently only top-1 saved)
  - Implement MBR (Minimum Bayes Risk) decoding — select hypothesis with lowest expected WER against all others
  - Implement ROVER (Recognizer Output Voting Error Reduction) — word-level alignment and voting across N-best
  - Beam diversity analysis: agreement across beams as a quality signal
  - Confidence-weighted word selection from N-best list
- **Expected Impact**: 5-15% relative WER reduction (conservative). MBR/ROVER well-established in ASR literature (Fiscus 1997)
- **Dependencies**: Mission 4 (confidence scores needed for weighted voting)
- **Research**: [Report 5 - Beam Search Aggregation](../beam-search/report_5_beam_search_aggregation.md)

---

### Mission 7: Hyperparameter Optimization
- **Priority**: HIGH
- **Goal**: Find optimal decode parameters — length penalty is the single biggest tuning lever identified
- **Items**:
  - Test lenpen=0.5, 1.0 (Report 2 identifies this as highest-impact: -5 to -15 WER points)
  - Test beam=5, 10 (speed + quality balance; beam=20 may be overkill)
  - Validate max_len settings from Mission 3 against new lenpen values
  - Build on existing 13 experiments (A-M) in `tuning_results/`
  - Establish per-domain optimal configs
- **Expected Impact**: WER ~55-60% (down from 67%) with hyperparameter tuning alone
- **Effort**: Low — infrastructure already exists in `tuning_results/run_all_experiments.sh`
- **Research**: [Report 2 - Hyperparameter Tuning](../tuning/report_2_hyperparameter_tuning.md)

---

### Mission 8: Prompt Engineering & Context Injection
- **Priority**: MEDIUM
- **Goal**: Use LLM's text capabilities to constrain hallucination via context priming and output hints
- **Items**:
  - Word count hints from segment duration (derivable without ground truth) — constrains hallucination length
  - Topic/domain context injection — prime LLM vocabulary toward expected domain
  - Anti-hallucination instructions ("output only words spoken")
  - Vocabulary lists for known named entities
  - Speaker description context
- **Expected Impact**: -5 to -15 WER points combined (word count hints: -3 to -7, topic context: -5 to -10)
- **Caveat**: Model was fine-tuned with specific prompt format; large deviations may break fine-tuning. Test on small subset first
- **Research**: [Report 3 - Prompt Engineering](../prompts/report_3_prompt_engineering.md)

---

### Mission 9: AVSpeech Fine-Tuning
- **Priority**: HIGH (biggest single WER improvement, but highest effort)
- **Status**: **EXP A+B COMPLETE** (Mar 2, 2026) — both LoRA-only experiments done, decode sweep in progress
- **Goal**: Domain adaptation fine-tuning on AVSpeech data to improve over pretrained checkpoint

**Experiment Results Summary**:

| Experiment | Config | Best Val Acc | Train Time | Verdict |
|---|---|---|---|---|
| **Exp A** (r=16) | Existing LoRA, encoder frozen | **62.94%** | 17h | Best result |
| **Exp B** (r=64) | Fresh LoRA 4x larger, encoder frozen | 59.80% | 27h | Worse (-3.1 pp) |
| Baseline | No fine-tuning | ~60% (estimated) | — | Reference |

**Key Findings**:
- **Both experiments were data-limited** — 1,273 segments is below the ~1K minimum for LoRA generalization (ICLR 2024 scaling laws). At this scale, any model configuration memorizes rather than generalizes
- r=64 was 3.1 pp worse than r=16 due to overfitting on tiny data — this does NOT prove the LLM has enough capacity with adequate data
- Both experiments overfit severely: 95% train vs ~59-63% val accuracy
- Best checkpoints at epoch 2-4; remaining 15+ epochs were wasted
- Training speed identical (~18 sec/update) despite 4x more LoRA params

**Root Cause Analysis — Three Bottlenecks (data scarcity is most actionable)**:
1. **Insufficient training data** (PRIMARY for these experiments) — 1,273 segments (1.5h) guarantees memorization. With 20K-50K segments, results could be dramatically different. AVSpeech has 290K videos available
2. **Frozen AV-HuBERT encoder** (PRIMARY long-term) — visual features trained on LRS3 TED talks don't represent YouTube content. Sets a ceiling that decoder tuning alone can't break
3. **Noisy labels** — Whisper ASR at ~64% accuracy provides corrupted supervision

**Remaining Items (Updated Priority)**:
  - ~~Increase LoRA rank~~ DEPRIORITIZED — experimentally disproven
  - Run decode evaluation sweep on Exp A/B/Baseline with 6 hyperparameter configs (automated, in progress)
  - **Phase 1: More data** — expand from 1.3K to 5-10K segments from AVSpeech (most impactful, lowest risk)
  - **Phase 2: Unfreeze encoder** — adapt top AV-HuBERT layers with discriminative LR (needs gradient checkpointing or multi-GPU)
  - **Phase 3: Label quality** — manually verify 224 val transcriptions; use Whisper large-v3 for better training labels
  - Data curation: filter face detection confidence >0.9, remove extreme head pose >30°
- **Expected Impact**: With proper data scaling (20K-50K segments) + stronger LLM (Llama 3.1 8B) + smart prompts, target 30-40% WER is realistic. Encoder adaptation for sub-30% WER
- **GPU Requirements**: Data expansion works on T4; encoder unfreezing needs V100+ or gradient checkpointing
- **Research**: [Report 6 - Fine-Tuning Analysis](../finetuning/report_6_finetuning_analysis.md), [Training Research Notes](../finetuning/training-research-notes.md) (Sections 6-9), [Comparison Report](../finetuning/experiments/comparison_report.md)

---

### Mission 10: Horizon Container
- **Priority**: MEDIUM
- **Goal**: Create a dedicated container build targeting the Horizon deployment platform
- **Items**:
  - Define Horizon-specific Dockerfile based on current Linux container (`vsp_docker/Dockerfile`)
  - Adapt paths, environment variables, and entrypoints for Horizon runtime
  - Handle Horizon-specific GPU driver / CUDA compatibility
  - Integrate with Horizon's job scheduling and storage APIs
  - Package model weights, k-means binaries, and spaCy wheels
  - Validate full pipeline end-to-end on Horizon infrastructure
  - Document deployment procedure and troubleshooting
- **Dependencies**: Mission 2 (container sync) should be substantially complete first

---

### Mission 11: Arabic Language Support
- **Priority**: MEDIUM
- **Goal**: Extend pipeline to support Arabic lip-reading
- **Items**:
  - Arabic k-means model already exists (`VSP-LLM/arabic_flat_kmeans_200.bin`)
  - Add language selection flag to pipeline (`run_flat_english_pipeline.sh`) and UI
  - Prepare Arabic test data and evaluation benchmarks
  - Validate Arabic-specific text normalization (RTL, diacritics removal)
  - Evaluate WER on Arabic test set
  - Update reports to handle Arabic text direction

---

### Mission 12: Multi-Speaker & Overlapping Speech
- **Priority**: LOW
- **Goal**: Handle videos with multiple visible speakers or speaker transitions
- **Items**:
  - Detect multiple faces per frame and track across segments
  - Associate mouth crops with speaker identity (speaker diarization)
  - Handle overlapping speech regions (pipeline currently assumes single speaker)
  - Per-speaker output tracks in reports
- **Research**: Known limitation noted in [Report 1](../evaluation/report_1_executive_assessment.md)

---

### Mission 13: Real-Time / Streaming Processing
- **Priority**: LOW
- **Goal**: Enable near-real-time lip-reading on live video feeds
- **Items**:
  - Streaming segmentation (sliding window instead of batch)
  - Optimize mouth cropping for per-frame latency
  - Investigate lighter decode configurations (beam=1 greedy already benchmarked: `tuning_results/exp_G_greedy/`)
  - Quantized model inference (INT8/FP16)
  - WebSocket/gRPC API for streaming results to UI

---

### Mission 14: Decode Parameter Auto-Tuning
- **Priority**: LOW
- **Goal**: Automate finding optimal decode parameters per-domain instead of manual experiments
- **Items**:
  - Build on existing 13 experiments (A-M) in `tuning_results/`
  - Implement grid/Bayesian search over beam, lenpen, temperature, rep_pen
  - Auto-select best config per-language or per-domain
  - Integrate winning config back into pipeline defaults
- **Dependencies**: Mission 7 (manual optimization provides search space bounds)

---

## Lessons Learned (March 2026 Training Weekend)

### What Worked
- **Stratified train/val split** by IS tier gave representative validation
- **Early checkpoint saving** (checkpoint_best.pt) captured the only useful training window
- **Automated eval pipeline** (eval_finetune.sh → make_report.py → IS scoring) — ready to run on any checkpoint with any decode params
- **Smoke testing** (50-update test runs) caught issues before committing to 17h runs

### What Didn't Work
- **Increasing LoRA rank** from 16→64 **on 1,273 samples**: 3.1 pp worse, 59% slower, 64% more VRAM — but this is a data scarcity problem, not proof that the LLM has sufficient capacity
- **Long training schedules** (3,000 updates): peak was at update 320 (Exp A) / ~640 (Exp B); 85%+ of training was wasted overfitting
- **Training on only 1,273 segments**: below the ~1K-sample minimum for LoRA generalization. Both experiments tested dataset limits, not model limits

### What We Got Wrong
- Predicted r=16 was "capacity-limited" and r=64 would help — **wrong at this data scale**, both overfit identically on 1.3K samples
- Predicted ~160MB VRAM increase for r=64 — **wrong**, actual was +5GB due to optimizer states
- Assumed decoder adaptation could compensate for encoder domain mismatch with tiny data — **wrong**, need both more data AND encoder adaptation
- **Overstated "encoder is THE bottleneck"** — the encoder domain shift is real, but equally important was the data insufficiency. With 20K-50K segments, the decoder (and a stronger LLM) could contribute much more

### Key Insight
> **These experiments were fundamentally data-limited.** The r=16 vs r=64 comparison on 1,273 samples tells us about the dataset's insufficiency, not the LLM's capacity ceiling. With proper data (20K-50K segments from AVSpeech), a stronger LLM (e.g., Llama 3.1 8B), and smart prompts, the architecture's potential is far higher than what we observed. Both data scaling and encoder adaptation are needed — they address different bottlenecks and their effects are multiplicative.

### Corrected Strategic Priorities
1. **More data** (20K-50K segments) — most impactful, unlocks the decoder's potential
2. **Stronger LLM** (Llama 3.1 8B) — better language modeling, 128K vocab, enables advanced prompting
3. **Smart prompts** (topic context, word count, GER post-processing) — force multiplier for stronger models
4. **Label quality** (Whisper large-v3, manual verification) — removes noise floor
5. **Encoder adaptation** (unfreeze top layers) — addresses visual domain shift ceiling
6. ~~LoRA rank increase on small data~~ — **deprioritized** (counterproductive without more data)

---

## How to Pick Up a Mission

1. Read this file and the linked research reports for context
2. Read the relevant doc files listed in [CLAUDE.md](../../CLAUDE.md) Documentation Map
3. Create a `MISSION<N>_<SHORT_NAME>.md` file documenting the plan, changes, and test criteria
4. Follow the EC2/container sync rules from CLAUDE.md for any code changes
5. Update this backlog when the mission status changes

## Key Research Insight

Missions 4-8 can cumulatively reach WER ~42-52% **without any training** (hyperparams + confidence filtering + N-best + prompt engineering). Mission 9 (fine-tuning) is the only path below ~40% WER but requires 8x GPU. The recommended approach is: ship Missions 4-8 first to get maximum gain at minimal cost, then invest in Mission 9 for the final push.
