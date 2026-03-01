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
- **Status**: **EXP A COMPLETE** (Feb 27, 2026) — training done, decode evaluation pending
- **Goal**: Actually run domain adaptation fine-tuning on AVSpeech data and measure improvement over pretrained checkpoint

**Exp A Results (r=16, encoder frozen, 3,000 updates, T4 GPU)**:
- Training completed in 17.0 hours on Tesla T4
- Best val accuracy: **62.94%** at epoch 2 (320 updates)
- Severe overfitting: train-val gap widened to 36.5 pp by epoch 19
- Key finding: r=16 is capacity-limited — model memorizes but can't generalize
- Best checkpoint saved; decode evaluation on full dataset pending
- 10 diagnostic plots generated in `docs/finetuning/plots/FT_*.png`

**Remaining Items**:
  - Run decode with `checkpoint_best.pt` on full 1,497-segment test set
  - Calculate WER/WWER/NEA F1/IS and compare to baseline
  - Run Exp B: r=64 (alpha=128) with max_update=500 and early stopping
  - **Critical**: Unfreeze AV-HuBERT encoder (315M params) — this is where ~70% of improvement comes from
  - Data curation: filter by face detection confidence >0.9, remove extreme head pose >30 deg
- **Expected Impact**: WER 42-52% (15-25 point improvement). The only path to sub-50% WER
- **GPU Requirements**: T4 (16GB) very tight with encoder unfrozen; p3.16xlarge 8x GPU recommended (~$24/hr, 3-5 hours)
- **Research**: [Report 6 - Fine-Tuning Analysis](../finetuning/report_6_finetuning_analysis.md), [Training Research Notes](../finetuning/training-research-notes.md), [Comparison Report](../finetuning/experiments/comparison_report.md)

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

## How to Pick Up a Mission

1. Read this file and the linked research reports for context
2. Read the relevant doc files listed in [CLAUDE.md](../../CLAUDE.md) Documentation Map
3. Create a `MISSION<N>_<SHORT_NAME>.md` file documenting the plan, changes, and test criteria
4. Follow the EC2/container sync rules from CLAUDE.md for any code changes
5. Update this backlog when the mission status changes

## Key Research Insight

Missions 4-8 can cumulatively reach WER ~42-52% **without any training** (hyperparams + confidence filtering + N-best + prompt engineering). Mission 9 (fine-tuning) is the only path below ~40% WER but requires 8x GPU. The recommended approach is: ship Missions 4-8 first to get maximum gain at minimal cost, then invest in Mission 9 for the final push.
