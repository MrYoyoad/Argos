# Presentation Design Plan

> **STATUS (March 4, 2026)**: **COMPLETE** — both Beamer (75 slides) and PPTX (~47 slides) are fully built with all research integrated through March 4. The design below served as the blueprint; actual implementation is in `generate_presentation.py` and `docs/paper/beamer-presentation/`. See `README.md` for current status and `BUILD_STATUS.md` for content coverage.
>
> Container update instructions moved to [docs/guides/container-update-feb2026.md](/docs/guides/container-update-feb2026.md).

## Presentation Plan

### Story Arc: "From Paper to Production — Bridging the Reality Gap in Visual Speech Processing"

**Audience**: Manager / supervisor project review (internal).
**Central narrative**: Took a state-of-the-art research model, deployed on real-world data, rigorously characterized a 2.5x performance gap, developed the Intelligibility Score showing WER dramatically overstates failure (40% properly captured vs 11% by WER), classified 5 failure categories and 7 success patterns to understand WHY segments succeed or fail, analyzed performance by topic (Business best at 57%, DIY worst at 30%) and segment length (short 32% vs long 49%), built a complete production system, and have a principled plan where each phase targets specific failure categories — with clear resource requirements.

> **Client version**: See `CLIENT_ADAPTATION_GUIDE.md` for how to adapt this deck for client/external audiences.

---

### Slide Structure (45 min + 15 min Q&A)

#### Section 1: Opening & Context (5 min, 4 slides)

**Upload 3 images with Prompt 1** (prompts reference each file by name for insertion):

| # | File | Slide | Placement |
|---|------|-------|-----------|
| 1 | `08_branding/BlackLogo300x300-W-BG.png` | 1 | Top-right logo |
| 2 | `09_pipeline_diagram/pipeline_architecture.png` | 3 | Full-width architecture diagram |
| 3 | `01_plots_for_slides/P2_paper_vs_reality.png` | 4 | Right half bar chart |

| # | Slide | Key Content | Graph/Visual |
|---|-------|-------------|-------------|
| 1 | **Title** | "Argos VSP: Research Findings and Production Roadmap" | Branding from `docs/branding/` |
| 2 | **What is Lip Reading?** | Video of face → text, no audio needed. Hook: play the 33-word perfect burned video | **Demo video**: `IEa7qEkMvfQ_3__c5447488_with_hyp.mp4` |
| 3 | **Model Architecture** | 3-block diagram: Video → AV-HuBERT (visual encoder, frozen, 1024-dim) → Linear projection (1024→4096) → LLaMA-2-7B (4-bit QLoRA, r=16). Note: LLM is **swappable** — Llama 3.1 8B has same hidden_size (4096), trivial swap (1-2 hours setup). Only LoRA adapters (12.6M params, 0.19%) + projection layer are trained. | Custom diagram |
| 4 | **The Benchmark** | Paper: 25.4% WER on LRS3 (curated TED talks). Our question: "How does this perform on real-world video?" And: "Is WER even the right metric?" | **NEW graph: Paper vs Reality bar chart** |

#### Section 2: Research Findings (18 min, 12 slides) — 40%

**Upload 7 images with Prompt 2** (images only — .md reports are in supplementary/ for reference):

| # | File | Slide | Placement |
|---|------|-------|-----------|
| 1 | `01_plots_for_slides/P1_quality_tiers.png` | 5 | Right half — quality tiers |
| 2 | `01_plots_for_slides/09_boxplot_wwer_all_experiments.png` | 9 | Center — WWER boxplot |
| 3 | `01_plots_for_slides/01_wer_vs_duration.png` | 10 | Right half — WER vs duration |
| 4 | `01_plots_for_slides/14_nea_vs_wwer_scatter.png` | 11 | Right half — NEA scatter |
| 5 | `01_plots_for_slides/10_empty_and_hallucination_rates.png` | 12 | Right half — empty/halluc rates |
| 6 | `01_plots_for_slides/P4_lenpen_sensitivity.png` | 13 | Right half — lenpen sensitivity |
| 7 | `01_plots_for_slides/P5_tuning_before_after.png` | 12 | Left half — baseline vs Config J |

| # | Slide | Key Content | Graph/Visual |
|---|-------|-------------|-------------|
| 5 | **The Reality Gap** | 25.4% → 64.1% WER = 2.5x worse. WER quality tiers: only 11.4% "usable". Headline: "9 out of 10 segments need verification — or do they?" | **NEW graph: Quality tier pie/bar chart** |
| 6 | **WER Is Blind** | **QUICK SETUP (30 sec)**: Two examples both ~30% WER: "work with the team" (WER 29%, IS 4.3, intelligible) vs "admiral mcrae"→"animal migratory" (WER 33%, IS 3.0, unintelligible). One line: "We've discussed this — same WER, opposite meaning. So we built a metric to fix it." → transition to next slide | Side-by-side text, 2 boxes (green/red) |
| 7 | **The Intelligibility Score** | **KEY SLIDE**: **LLM-distilled evaluation** — Claude designed the rubric, selected 6 signals/weights, defined tiers, classified failure/success patterns. Encoded into deterministic, free, decomposable metrics. Properly captured (IS >= 3.0): **39.9%** — 3.5x more than WER's 11.4%. IS tiers: 18.4% excellent, 21.4% good, 21.7% fair, 22.4% poor, 16.0% failed. **Cross-config validation (16 configs)**: Semantic/Phonetic/NEA stable (std<0.06); WER/LR volatile — proves IS more robust than WER. Claude-designed `llm_context_prob` heuristic (deterministic, no runtime LLM) r=0.925 across 16 configs (std=0.015), 88.6% agreement, 99.2% recall. Config J highest IS (2.571) despite +14.8pp WER. Rankings stable (r>0.92) — encoder-limited. **Success patterns**: phonetic preservation #1 driver (41.5%, also #1 IS correlate r=0.943). This is the main research contribution. | IS tier distribution chart (new) |
| 8 | **Failure Mode Taxonomy** | **UPDATED**: 5 failure categories across 900 failed segments: Wrong Topic 31.6%, Accumulated Errors 24.4%, Right Topic Wrong Details 22.7%, Hallucination 12.3%, Signal Loss 9.0%. **Key insight**: failures are diverse — no single fix. Each roadmap phase targets specific failure categories. | Failure mode bar chart |
| 9 | **Performance Distribution** | The spread — most segments at 50-80% WER, long tail of catastrophic failures | Existing: `09_boxplot_wwer_all_experiments.png` |
| 10 | **Why the Gap** | 3 root causes: domain mismatch (TED vs YouTube), hallucination, short-segment failure. **Topic analysis**: Business/Finance best (IS 3.08, 57% captured) — formal vocabulary helps. DIY/Home worst (IS 2.13, 30% captured) — casual speech harder. **Length analysis**: 5-10 words only 32% captured, 20+ words 49% captured (+17pp). Short segments don't provide enough visual context. | Existing: `01_wer_vs_duration.png` |
| 11 | **Named Entity Accuracy** | NEA F1: 38.8% — misses 61% of names/numbers. These are the words context can't recover. **Signal comparison confirms**: NEA F1 is the largest success/failure differentiator (74.0% vs 15.7%, gap 58.3pp). **Correlation insight**: NEA contributes 17.3% of IS variance (disproportionate to its 15% weight) due to high per-segment variance | Existing: `14_nea_vs_wwer_scatter.png` |
| 12 | **13 Tuning Experiments** | Parameter sweep: beam, lenpen, sampling, temperature. **Full-dataset Config J results (1497 segments)**: IS 2.60 vs 2.52 baseline, 622 vs 597 captured (+25), empties 0 vs 70 baseline, but hallucinations 348 vs 307 (+41). J beats C: stochastic sampling (temp=0.5) recovers 3.7pp more named entities. do_sample=True on standalone, False on EC2 — to be unified. | Existing: `10_empty_and_hallucination_rates.png` + `16_improvement_J_vs_A.png` |
| 13 | **Limits of Tuning** | Tuning = mitigation, not cure. **Config J trade-off**: eliminates empties but doubles hallucinations (111→262). Net IS gain only +0.08. The fundamental tradeoff is silent failures (empties) vs noisy failures (hallucinations). **Cross-config proof**: per-segment IS rankings stable across all 16 configs (r>0.92) — "hard" and "easy" segments stay the same regardless of decode parameters. Bottleneck is the visual encoder, not decode strategy. **Data scarcity (1,273 segments) was the real bottleneck** — not model capacity or decode parameters. Three levers remain: (1) scale training data to 20K-50K segments, (2) swap to stronger LLM (Llama 3.1 8B, drop-in), (3) smart prompts as force multiplier. | **NEW graph: Hyperparameter sensitivity tornado** |
| 14 | **Curated Examples** | Side-by-side ref vs hyp with IS scores (see examples section below) | Formatted text table |
| 15 | **Live Demo** | Play 2-3 burned videos (see demo videos section below) | Video playback |
| 16 | **Research Breadth** | One-liner per report (8 reports): evaluation, tuning, prompts, confidence, beam search, fine-tuning, **intelligibility**, **LLM upgrade analysis** | Simple list |

#### Section 3: Engineering Achievements (12 min, 7 slides) — 25%

**Upload 2 images with Prompt 3** (images only):

| # | File | Slide | Placement |
|---|------|-------|-----------|
| 1 | _(programmatic — no image file)_ | 17 | Programmatic 2-row layout with 8 color-coded stage boxes and click-reveal |
| 2 | `01_plots_for_slides/15_cdf_wwer_curated.png` | 22 | Right half — CDF thresholds |

| # | Slide | Key Content | Graph/Visual |
|---|-------|-------------|-------------|
| 17 | **Pipeline Architecture** | 8-stage flow: Normalize → ASR → LRS3 → Manifests → Clustering → Decode → Reports → Burns | Pipeline flow diagram |
| 18 | **Why Engineering Was Hard** | Research code → production. 37 bugs. HDR video, GPU encoding, Cython, fairseq patching, NVENC corruption | Bug count timeline or categories |
| 19 | **Modular Refactoring** | 823→393 lines, 11 modules, 37 tests. Before/after comparison | Side-by-side code structure |
| 20 | **Deployed Product** | Standalone container, desktop icon, web UI, drag-and-drop. "Runs on a standalone Linux machine, no cloud" | UI screenshot |
| 21 | **Smart Features** | Transcription reuse, golden k-means, video segmentation with overlap | Feature diagram |
| 22 | **Evaluation Infrastructure** | 16 analytical plots, per-segment HTML reports, CSV exports, custom NEA metric, **IS pipeline** (LLM-distilled: Claude-designed rubric → 6 deterministic signals, per-segment scoring, tier classification), **IS cross-config validation** (16 configs: Semantic/Phonetic/NEA stable, WER volatile; Claude-designed heuristic r=0.925, no runtime LLM; segment rankings r>0.92), automated failure mode classification (5 categories) and success pattern analysis (7 patterns), topic/length analysis (11 categories), fine-tuning diagnostics (10 training plots) | Sample report screenshot |
| 23 | **Quality Process** | Git tags, EC2/container sync protocol, **8** research reports, comprehensive docs | Process diagram |

#### Section 4: Future Directions (10 min, 8 slides) — 35%

**Upload 6 images with Prompt 4** (images only):

| # | File | Slide | Placement |
|---|------|-------|-----------|
| 1 | `01_plots_for_slides/P1_quality_tiers.png` | 24 | Right half — IS vs WER tiers |
| 2 | `01_plots_for_slides/P3_wer_trajectory.png` | 26 | Right half — WER trajectory |
| 3 | `01_plots_for_slides/finetune/FT_10_summary_dashboard.png` | 29 | Top half — Exp A dashboard |
| 4 | `01_plots_for_slides/finetune/FT_01_loss_curves.png` | 29 | Backup (speaker notes ref) |
| 5 | `01_plots_for_slides/finetune/FT_02_accuracy_curves.png` | 29 | Backup (speaker notes ref) |
| 6 | `01_plots_for_slides/finetune/FT_03_overfitting_gap.png` | 29 | Backup (speaker notes ref) |

| # | Slide | Key Content | Graph/Visual |
|---|-------|-------------|-------------|
| 24 | **The Starting Point Is Better Than WER Says** | **KEY TRANSITION**: WER says 11.4% usable. IS says 39.9% properly captured. **Cross-config proof**: IS tested across 16 configs — stable (Semantic r=0.914, std=0.017). WER is MISLEADING: Config J has highest IS (2.571) despite +14.8pp WER — more words = more errors but MORE meaning. Claude-designed `llm_context_prob` heuristic (deterministic decision tree, no runtime LLM calls) agrees 88.6% across all configs (r=0.925, recall 97.6-100%). Rankings stable (r>0.92) — encoder-limited. **Success**: 41.5% phonetically preserved (Phonetic Sim #1 IS correlate r=0.943). "40% works. IS is validated across 16 configurations. We know WHY — phonetic preservation." | WER tiers vs IS tiers side-by-side |
| 25 | **LLM Salvage: 1 in 2 Segments Delivers Value** | 165 of 900 metric-failed segments (18.3%) have meaning that LLM heuristic identifies as recoverable (llm_context_prob >= 0.5, IS < 3.0). Including these, effective capture rate rises from 39.9% to **50.9%** — 1 in 2 segments delivers useful output. 6 recovery types: hidden gems (54), semantic preservation (57), phonetic bridge (93), entity-preserved (44), structure match (74), WER over-punishment (27). Key insight: metrics systematically undercount value — half the output is usable. | LLM salvage waterfall or tier comparison chart |
| 26 | **Improvement Roadmap** | Phased, mapped to failure modes + investment strategy. **Phase 1**: Confidence scoring → surfaces the good 40% (flag quality, 2-4 hours). **Phase 2**: N-best aggregation → addresses Accumulated Small Errors (12.3%) and Content Word Errors (10.7%). **Phase 3**: LLM swap to Llama 3.1 8B (drop-in, same hidden_size 4096, 1-2 hours setup) + context-injection prompts → -8 to -18pp combined (force multiplier: stronger LLM unlocks prompt strategies). **Phase 4**: Scale training data to 20K-50K segments + fine-tune with enriched prompts → biggest single gain (-15 to -25pp). **Phase 5**: GER post-processing (N-best + correction LLM, no retraining) → -8 to -15pp. **Realistic combined target: IS 3.5-4.0** (from current 2.52, ~55-65% captured). Multiplicative scaling law (ICLR 2024): LLM + data improvements compound. | **WER trajectory line chart** + **Improvement waterfall** |
| 27 | **Phase 1: Confidence Scoring** | IS already proves 40% is good. Now extract beam scores to FLAG it automatically. No additional inference needed. 2-4 hours effort. **Priority by topic**: Business/Finance segments (57% captured) are most likely reliable — flag these first. Short segments (<10 words, 32% captured) need lower confidence thresholds. | Annotated pipeline showing where scores exist |
| 28 | **Phase 2: N-Best Aggregation** | ROVER/MBR — currently discarding 19/20 beam candidates. 5-15% relative improvement. Targets failure modes: Accumulated Small Errors (12.3%), Content Word Errors (10.7%) — these have partial correct words across multiple hypotheses. Moves "fair" tier segments up to "good". | Before/after diagram |
| 29 | **Fine-Tuning + Data Scaling** | **Exp A results**: r=16 LoRA, 1,273 segments, 17h Tesla T4. Best val accuracy **62.94% at epoch 2**. Severe overfitting: 36.5pp gap by epoch 19. **Key reframe**: r=64 performed 3.1pp *worse* — not because LLM is saturated, but because 4x params = faster overfitting on tiny data. **1,273 segments is below the ~1K minimum** for LoRA generalization (ICLR 2024 scaling laws). Both experiments proved DATA SCARCITY is the bottleneck. **Data scaling projections**: 5K segments → 55-60% WER, 20K → 45-50%, 50K → 40-45% (with Llama-2-7B). With Llama 3.1 8B: 20K → 40-45%, 50K → 35-40%. AVSpeech has 290K videos available. **Multiplicative scaling law**: stronger LLM extracts MORE from same data — gap widens as data increases. Targets: Topic Drift (15.9%), Entity Destruction (12.0%). | `finetune/FT_01_loss_curves.png`, `finetune/FT_02_accuracy_curves.png`, `finetune/FT_10_summary_dashboard.png` |
| 30 | **LLM Upgrade + Advanced Capabilities** | **LLM swap to Llama 3.1 8B**: drop-in replacement (same hidden_size 4096), Llama-3 8B ≈ Llama-2 70B quality, 128K vocab (4x), 128K context (32x). Setup: 1-2 hours, just change model path. **Smart prompts (force multiplier)**: 7 strategies — topic context (-5 to -10pp), word count hints, vocabulary lists, anti-hallucination, phonetic context, self-correction, **N-best GER** (-8 to -15pp, SOTA). Stronger models unlock more strategies: Llama-2-7B = +5-10pp, Llama 3.1 8B = +12-20pp, 70B class = +20-30pp. **GER post-processing**: Two-stage pipeline — visual pipeline generates N-best hypotheses, separate correction LLM (even external API: Claude/GPT-4) picks and corrects best one. No retraining needed. **Model alternatives**: VALLR (ICCV 2025) achieves 18.7% WER on LRS3 with 3B model — architecture innovation > model size. **Future**: Arabic, multi-speaker, streaming. | Feature roadmap + improvement waterfall |
| 31 | **Key Takeaways** | (1) Rigorous assessment: 2.5x WER gap on 1,497 segments, novel IS metric reveals 40% properly captured (50.9% with LLM salvage), 5 failure categories classified, topic/length analysis. (2) Production system delivered: standalone container, 37 bugs fixed, 8-stage pipeline, 37 tests, 8 research reports. (3) Data is the bottleneck: Exp A/B proved 1,273 segments too small — 20K-50K segments is the critical enabler. Multiplicative scaling law: stronger LLM + more data compounds. (4) Actionable roadmap to IS 3.5–4.0 (from 2.52): confidence scoring + N-best aggregation + LLM upgrade + data scaling + GER. Each phase targets a different failure category. | 4-point summary |

#### Appendix / Backup Slides

| # | Slide | Key Content | When to use |
|---|-------|-------------|-------------|
| A1 | **Homophenes: The Lip-Reading Problem** | 50-70% of English sounds invisible on lips. Groups: p/b/m identical, t/d/n/s/z/l identical. Examples: "mom"↔"bomb", "collar"↔"color", "pads"↔"pants" | If someone asks "why does it confuse those words?" |
| A2 | **Exp A Fine-Tuning Deep Dive** | Full training dynamics: LR schedule (FT_04), gradient norms (FT_05), perplexity explosion (FT_06), data distribution (FT_07), granular loss with checkpoints (FT_08), wall-clock time (FT_09). Root causes: small dataset, noisy labels, rank limitation, encoder frozen. Recommendation: r=64 + early stopping + data curation | Boss deep-dive only |
| A3 | **Catastrophic lenpen=2.0** | Experiment H: mean WER 171.5%, model generates paragraphs of hallucinated text | Boss deep-dive only |
| A3 | **Segment Stability Heatmap** | Which segments are always good/bad across all 13 configs | Boss deep-dive only |
| A4 | **Full Experiment Table** | All 13 experiments A-M with full metrics | Boss deep-dive only |
| A5 | **Topic Analysis Detail** | Full 11-topic table: Business/Finance (IS 3.08, 57% captured) → DIY/Home (IS 2.13, 30%). LLM context recovery adds 5-15% over rule-based per topic | If asked about domain-specific performance |
| A6 | **Signal Comparison: Success vs Failure** | Full signal table: semantic 0.74 vs 0.24, phonetic 0.81 vs 0.38, NEA F1 74% vs 16%, WER 30% vs 87%. Length ratio NOT a strong differentiator (0.97 vs 0.89) | If asked about what makes IS work |
| A8 | **IS Correlation & Cross-Config Analysis** | Component correlation matrix (6x6), variance decomposition, 3 independent dimensions. **Cross-config (16 configs)**: Semantic/Phonetic/NEA stable (std<0.06), WER/LR volatile. Claude-designed heuristic r=0.925 (std=0.015) across configs, recall 97.6-100%. Inter-config rankings r>0.92. **Claude Designed the Judge (at design time only)**: IS is LLM-distilled evaluation — Claude designed rubric, weights, tiers, failure modes once; no LLM is called per sample at runtime. Full decode: Config J IS 2.571 despite +14.8pp WER (proves IS > WER). Variance contribution stability across configs. | If asked about IS methodology rigor, statistical validation, or cross-config stability |
| A7 | **Config J Full-Dataset Comparison** | Baseline vs Config J vs Config C on 1,497 segments: IS 2.52→2.60, empties 70→0, hallucinations 307→348. Trade-off: silent failures vs noisy failures. J wins by +0.08 IS, +25 captured segments. Long segments benefit most (+0.25 IS for 20+ words) | If asked about tuning details |
| A9 | **LLM Upgrade Analysis Deep Dive** | Tier 1 models: Llama 3.1 8B (drop-in, same hidden 4096, ≈Llama-2 70B), Llama 3.2 3B (VALLR proved 18.7% WER). Tier 2: Qwen 2.5 7B, Mistral 7B, DeepSeek-V2-Lite, Phi-4, Gemma 2. Data scaling projections table (1.3K→100K segments × Llama-2 vs Llama-3.1). 7 prompt strategies by model tier: topic context, word count, vocabulary, anti-hallucination, phonetic, self-correction, N-best GER. Improvement waterfall: IS 2.52 → confidence scoring → N-best → LLM swap → data scaling → GER → target IS 3.5-4.0. Multilingual analysis: English-only → use Llama 3.1 8B, Arabic → language-specific model. Code changes: only vsp_llm.py:224, 2 YAML configs, 2 scripts for same-dim swap. | If asked about LLM alternatives, data scaling, or prompt strategies |
| A11 | **LLM Salvage Taxonomy** | 6 recovery types with counts and definitions: hidden gems (54), semantic preservation (57), phonetic bridge (93), entity-preserved (44), structure match (74), WER over-punishment (27). How each type preserves meaning despite metric failure. | If asked about salvage methodology or recovery type details |
| A12 | **Success Pattern Examples** | Curated examples of segments where the model preserves meaning despite high WER — phonetic near-misses, semantic paraphrases, entity preservation cases with IS scores and llm_context_prob values | If asked for concrete examples of what "good" looks like |
| A13 | **Failure Mode Examples** | Curated examples of each failure mode — hallucination, topic drift, entity destruction, empty output, truncation — with reference text, hypothesis, WER, and IS scores | If asked for concrete examples of what "bad" looks like |
| A14 | **Metric Mismatch Guide** | Cases where WER and IS disagree: high WER + high IS (paraphrased but meaningful), low WER + low IS (lucky word overlap but wrong meaning). Explains why IS is needed alongside WER and when each metric is appropriate | If asked about metric disagreements or why WER is insufficient |

**PPTX Appendix Mapping** (PPTX uses sequential A1-A9, Beamer uses A1-A17):

| PPTX | Beamer | Content |
|------|--------|---------|
| A1 | A1 | Homophenes |
| A2 | A3 | Catastrophic lenpen=2.0 |
| A3 | A8 | IS Correlation & Cross-Config |
| A4 | A11 | LLM Salvage Taxonomy |
| A5 | A11b | LLM Salvage Curated Examples |
| A6 | A13 | Failure Mode Examples |
| A7 | A15 | Video Gallery |
| A8 | A16 | LLM Judge Cross-Tabulation |
| A9 | A17 | Context Evaluation Transitions |

---

### Examples: What to Show and Why

Each example demonstrates a specific point about the system's behavior.

**1. Perfect transcription — open with this (Slide 2)**
- `IEa7qEkMvfQ_3__c5447488` — 33 words about insurance policies (WER 0%, IS 5.0)
- Shows the technology fundamentally works on complex domain-specific content.

**2. Hallucination — the core failure mode (Slide 13)**
- `00MUdHQ7GGY_8__b1480c7a` — REF: "carry strap" → HYP: "holocaust denier" (WER 100%, IS 0.7)
- The model fabricates coherent but fictional text. Shows why confidence scoring matters — the output reads fluently but is entirely fabricated.

**3. Phonetic near-misses — demonstrates why lip reading is hard (Slide 13)**
- `-POZpyVCN8k_9__c7b26ea8` — "admiral mcrae" → "animal migratory" (WER 33%, IS 3.0)
- `-WQZsfHcPDM_7__5210cac1` — "bottle/probiotics" → "monitor/permafrost" (WER 58%, IS 2.7)
- Lip shapes for "admiral/animal" are genuinely similar. These are NOT model errors — they're inherent visual ambiguities.

**4. Tuning trade-off — shows why hyperparameters aren't enough (Slide 13)**
- `DBhaa45mAro_2__07d05c7a` — Baseline: EMPTY → Config J: partial transcription (WER 73%)
- `eLS1vcpGVHQ_12__e9dd9adc` — Baseline: partial → Config J: 40-word hallucination (WER 400%)
- Same config change fixes one segment and destroys another. No simple knob to turn.

---

### Demo Video Sequence

**Slide 2 (opening):** Play `IEa7qEkMvfQ_3__c5447488_with_hyp.mp4` — 33-word perfect transcription. Play first, explain after.

**Slide 15 (demo):** Three videos in sequence:
1. `d8BR6hsvzoY_31__2e9546df_with_hyp.mp4` — "buy one get one free" (WER 0%, short)
2. `-POZpyVCN8k_9__c7b26ea8_with_hyp.mp4` — "admiral mcrae" → "animal migratory" (near-miss)
3. `00MUdHQ7GGY_8__b1480c7a_with_hyp.mp4` — David Irving hallucination (total fabrication)

Sequence: Good → Funny → Failure. Transition: "This is why confidence scoring is the immediate next step."

All burned videos: `english_full_results/client_outputs/burned_videos/`

---

### Graphs: What to Use, What to Generate

#### Existing plots to use (from `docs/evaluation/plots/`):

| Plot | Use on Slide | Why | Audience |
|------|-------------|-----|----------|
| `01_wer_vs_duration.png` | 10 (Why the Gap) | Shows short segments fail catastrophically — the most actionable finding | Both |
| `09_boxplot_wwer_all_experiments.png` | 9 (Distribution) | Shows the spread across experiments — bosses want this, clients get the headline | Both (simplified for clients) |
| `10_empty_and_hallucination_rates.png` | 12 (Tuning) | Empty vs hallucination trade-off per config — intuitive failure mode comparison | Both |
| `14_nea_vs_wwer_scatter.png` | 11 (NEA) | Shows entity accuracy correlation — technical validation of NEA metric | Bosses |
| `16_improvement_J_vs_A.png` | 12 (Tuning) | Per-segment improvement from best config — shows tuning is real but limited | Both |
| `15_cdf_wwer_curated.png` | Appendix | "X% of segments below Y% WER" — actionable for quality thresholds | Clients |

#### Existing plots for boss-only deep dive:

| Plot | Why |
|------|-----|
| `11_wer_vs_wwer_scatter.png` | The lenpen paradox — higher corpus WER but better segment WER |
| `12_segment_stability_heatmap.png` | Which segments are always good/bad across configs |
| `03_wwer_vs_duration.png` | Weighted WER by duration — more nuanced than WER vs duration |
| `05_nea_recall_vs_duration.png` | Named entity recall drops with short segments — validates minimum length |

#### NEW graphs to generate:

| Graph | Use on Slide | What it shows | Data source |
|-------|-------------|---------------|-------------|
| **Quality Tier Pie/Bar Chart** | 5 (Reality Gap) | 5 colored tiers: 11.4% usable / 17.4% marginal / 17.8% poor / 32.8% unusable / 20.6% hallucinated | Report 1 data |
| **Paper vs Reality Bar Chart** | 4 (Benchmark) | Two bars: LRS3 25.4% vs Real-world 64.1%, with "2.5x" annotation | Report 1 data |
| **Failure Mode Bar Chart** | 8 (Failure Modes) | 5 categories: Wrong Topic 31.6%, Accumulated Errors 24.4%, Right Topic Wrong Details 22.7%, Hallucination 12.3%, Signal Loss 9.0% | IS failure_mode_distribution |
| **WER Trajectory Line Chart** | 26 (Roadmap) | Line: Current 64% → Phase 1: 55% → Phase 2: 45% → Phase 3: 42%, with mission labels | `docs/backlog/mission-backlog.md` |
| **Hyperparameter Sensitivity Tornado** | 13 (Limits) | lenpen from -0.5 to 2.0: empty rate (44.9% → 0%) vs hallucination rate (opposite) | Experiment comparison data |
| **Before/After Tuning Paired Bars** | 12 (Tuning) | Baseline vs Config J (full 1497 segments): IS, captured%, empty%, hallucination% | IS Config J comparison |

Script to extend: `docs/evaluation/plots/generate_experiment_plots.py` (existing 643-line generator)

---

### Manager Audience: What They Want to See

- **Methodology rigor**: Did you explore the space systematically? (13 experiments, 1497-segment evaluation, 5 failure categories classified, topic/length analysis)
- **Reproducibility**: Can these results be reproduced? (golden k-means, fixed configs, version-tagged code)
- **Novel contributions**: IS metric, failure mode taxonomy, success pattern analysis, topic-specific performance — explain why this goes beyond standard WER
- **Technical details**: do_sample divergence, beam=20 rationale, hallucination mechanism, Config J full-dataset trade-offs, phonetic preservation as #1 success driver
- **Actionable insights**: Business/Finance already at 57% captured → confidence scoring most impactful there. Short segments (<10 words) drag down metrics → minimum length filter. Each roadmap phase targets specific failure modes.
- **Resource needs**: What do you need to continue? (GPU budget for fine-tuning, time allocation per phase)
- **Key takeaway**: "We've systematically characterized the gap at every level — per-segment, per-topic, per-length, per-failure-mode — built the infrastructure, and have a principled plan where each phase targets specific failure categories"

### Key Materials Reference

| Material | Path |
|----------|------|
| 16 analytical plots | `docs/evaluation/plots/` |
| Plot generator script | `docs/evaluation/plots/generate_experiment_plots.py` |
| Experiment comparison | `docs/tuning/experiment-comparison.csv` |
| Curated examples JSON | `tuning_results/interesting_examples/metadata.json` |
| Full results CSV (1497 rows) | `english_full_results/client_outputs/report/report.csv` |
| Full results report | `english_full_results/client_outputs/report/report.txt` |
| HTML reports (per-experiment) | `docs/tuning/html-reports/` |
| Burned videos (1497 demos) | `english_full_results/client_outputs/burned_videos/` |
| Report 1 (evaluation) | `docs/evaluation/report_1_executive_assessment.md` |
| Reports 3-6 | `docs/{prompts,confidence,beam-search,finetuning}/` |
| **Exp A training plots (10)** | `docs/finetuning/plots/FT_*.png` |
| **Exp A comparison report** | `docs/finetuning/experiments/comparison_report.md` |
| **Exp A training research** | `docs/finetuning/training-research-notes.md` (Section 6) |
| **Intelligibility methodology** | `docs/evaluation/intelligibility_methodology.md` |
| **Intelligibility scores (1497 rows)** | `docs/evaluation/intelligibility/intelligibility_scores.csv` |
| **Intelligibility summary** | `docs/evaluation/intelligibility/intelligibility_summary.json` |
| **Intelligibility report (docx)** | `docs/evaluation/intelligibility/intelligibility_report.docx` |
| Mission backlog | `docs/backlog/mission-backlog.md` |
| Existing 2025 pptx | `docs/paper/Presentation_2025.pptx` |
| Branding | `docs/branding/` |
| Pipeline architecture | `docs/architecture.md` |
| Segment metadata | `english_full_results/segment_metadata.json` |
