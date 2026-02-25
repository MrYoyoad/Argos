# Plan: Container Update + Presentation Design

## Context

Two tasks:
1. **Container update**: The client machine is running ~v1.0.32-35 (~Feb 15-17), last deployed right before the experiments started. The FINAL directory on EC2 has v1.0.39+ with all fixes applied, including the critical NVENC silent corruption fix (v1.0.36-39). The current tarball is stale (5 files updated after packing). We need to rebuild the tarball and deploy to the client via INSTALL.sh. **No code changes needed** — just repack and ship.
2. **Presentation**: Design a 45-60 minute presentation for client demo + supervisor project review + potential new clients. Research findings (40%), engineering achievements (25%), future directions (35%).

---

## Task 1: Container Update

### The Version Gap

| | Version | Date | Status |
|---|---------|------|--------|
| **Client machine** | ~v1.0.32-35 | ~Feb 15-17 | Last deployed before experiments started |
| **FINAL directory (EC2)** | v1.0.39+ | Feb 17-18 | All fixes + golden k-means + report params |
| **Current tarball** | **STALE** | Feb 17 16:55 | Missing 5 files added after packing |

### What the client is missing (~v1.0.36 → v1.0.39+)

| Version | Fix | Impact |
|---------|-----|--------|
| v1.0.36-39 | **NVENC silent corruption fix + bash fd isolation** | **Critical: destroys 43% of videos without this** |
| v1.0.36 | ETA removal from progress display | Cosmetic |
| v1.0.37 | VLC configuration | Usability |
| post-v1.0.39 | Golden k-means baseline update (1396-video model) | Better clustering baseline |
| post-v1.0.39 | Report decode parameters feature (make_report.py, outputs.sh, vsp_llm_decode.py) | Reports show which decode params were used |

### Why Just Rebuilding the Tarball + INSTALL.sh Works

The FINAL directory (`vsp_linux_container_FINAL_20260217/`) already contains ALL these fixes. The INSTALL.sh inside it:
- Copies `lib/` modules (step 3.1) — includes the NVENC fix in normalization.sh
- Copies pipeline script (step 3.2)
- Copies VSP-LLM config (step 3.3), Python source (step 3.4), scripts (step 3.5)
- Copies entire `vsp-ui/` tree (step 3.6) — includes the drag-and-drop fix
- Copies auto_avsr, av_hubert, clustering (steps 3.7-3.9)
- Runs fairseq patch (step 3.10)
- Copies tests (step 3.11)
- Sets up Docker config, host launcher, permissions, vsp_input, spaCy (steps 3.12-3.16)
- Runs verification (13 checks) and module tests (37 tests)
- Creates automatic backup before installing (rollback available)

**No code changes needed to the FINAL directory. Just repack the tarball.**

### Steps

**Step 1**: Fix minor bug in `scripts/build/verify_container_sync.sh` line 21
- Missing trailing `/` in glob pattern — causes it to match the `.tar.gz` file instead of directory
- File: `/home/ubuntu/scripts/build/verify_container_sync.sh`

**Step 2**: Run verification to confirm FINAL directory integrity
```bash
bash scripts/build/verify_container_sync.sh
```
- Path-agnostic files should show OK
- The 3 VSP-LLM sampling files will show DIFF — this is expected (keeping baseline on standalone)

**Step 3**: Rebuild tarball (includes the 5 files that are newer than the old tarball)
```bash
cd /home/ubuntu
tar czf vsp_linux_container_FINAL_20260217.tar.gz vsp_linux_container_FINAL_20260217/
sha256sum vsp_linux_container_FINAL_20260217.tar.gz > vsp_linux_container_FINAL_20260217.sha256
```

**Step 4**: Transfer to client machine
- SCP/S3/USB both `.tar.gz` and `.sha256` to `/home/ds/Desktop/`

**Step 5**: On client machine — extract and install
```bash
cd /home/ds/Desktop/
sha256sum -c vsp_linux_container_FINAL_20260217.sha256   # verify integrity
tar xzf vsp_linux_container_FINAL_20260217.tar.gz        # extract overlay

# Start Docker container with galaxy_export mounted
# (use vsp-start.sh or docker run manually)

# Inside Docker container:
cd /host/galaxy_export
bash ../vsp_linux_container_FINAL_20260217/INSTALL.sh
```

INSTALL.sh automatically: creates backup → installs all components → verifies → runs tests → reports status.

**Step 6**: Post-install verification on client
- INSTALL.sh's built-in VERIFY phase runs 13 checks automatically
- Module tests (37 tests) run automatically
- Optional: run a test video through the pipeline to confirm end-to-end

### Rollback
INSTALL.sh creates `galaxy_export_backup_{timestamp}.tar.gz` before installing. To rollback:
```bash
cd /home/ds/Desktop/
tar xzf galaxy_export_backup_*.tar.gz
```

### Documentation Note (to add to container-sync-changelog.md)
- Standalone runs baseline decode config with `do_sample=True` (stochastic beam search)
- EC2 has `do_sample=False` (deterministic beam search) — to be synced in future update along with lenpen option
- The stochastic vs deterministic difference is minor for beam=20 but should be unified eventually

### Critical files (read-only, no changes except verify script)
- `/home/ubuntu/scripts/build/verify_container_sync.sh` — glob fix on line 21
- `/home/ubuntu/docs/container-sync-changelog.md` — add documentation note
- `/home/ubuntu/vsp_linux_container_FINAL_20260217/INSTALL.sh` — reference (no changes)
- `/home/ubuntu/vsp_linux_container_FINAL_20260217/VERIFY.sh` — reference (no changes)

---

## Task 2: Presentation Plan

### Story Arc: "From Paper to Production — Bridging the Reality Gap in Visual Speech Processing"

**Audience**: Client demo + supervisor project review + potential new clients.
**Central narrative**: Took a state-of-the-art research model, deployed on real-world data, rigorously measured a 2.5x performance gap, developed the Intelligibility Score to prove WER dramatically overstates failure (40% properly captured vs 11% by WER), built production infrastructure, and identified a concrete path to close the remaining gap.

---

### Slide Structure (45 min + 15 min Q&A)

#### Section 1: Opening & Context (5 min, 4 slides)

| # | Slide | Key Content | Graph/Visual |
|---|-------|-------------|-------------|
| 1 | **Title** | "Argos VSP: Research Findings and Production Roadmap" | Branding from `docs/branding/` |
| 2 | **What is Lip Reading?** | Video of face → text. Use cases: surveillance, accessibility, noisy environments. Hook: play the 33-word perfect burned video | **Demo video**: `IEa7qEkMvfQ_3__c5447488_with_hyp.mp4` |
| 3 | **Model Architecture** | 3-block diagram: Video → AV-HuBERT (visual encoder) → LLaMA-2 (language model) → Text | Custom diagram |
| 4 | **The Benchmark** | Paper: 25.4% WER on LRS3 (curated TED talks). Our question: "How does this perform on real-world video?" And: "Is WER even the right metric?" | **NEW graph: Paper vs Reality bar chart** |

#### Section 2: Research Findings (18 min, 11 slides) — 40%

| # | Slide | Key Content | Graph/Visual |
|---|-------|-------------|-------------|
| 5 | **The Reality Gap** | 25.4% → 64.1% WER = 2.5x worse. WER quality tiers: only 11.4% "usable". Headline: "9 out of 10 segments need verification — or do they?" | **NEW graph: Quality tier pie/bar chart** |
| 6 | **WER Is Blind** | **QUICK SETUP (30 sec)**: Two examples both ~30% WER: "work with the team" (WER 29%, IS 4.3, intelligible) vs "admiral mcrae"→"animal migratory" (WER 33%, IS 3.0, unintelligible). One line: "We've discussed this — same WER, opposite meaning. So we built a metric to fix it." → transition to next slide | Side-by-side text, 2 boxes (green/red) |
| 7 | **The Intelligibility Score** | **KEY SLIDE**: 6-signal composite metric. Properly captured (IS >= 3.0): **39.9%** — 3.5x more than WER's 11.4%. IS tiers: 18.4% excellent, 21.4% good, 21.7% fair, 22.4% poor, 16.0% failed. This is the main research contribution. | IS tier distribution chart (new) |
| 8 | **Performance Distribution** | The spread — most segments at 50-80% WER, long tail of catastrophic failures | Existing: `09_boxplot_wwer_all_experiments.png` |
| 9 | **Why the Gap** | 3 root causes: domain mismatch (TED vs YouTube), hallucination, short-segment failure | Existing: `01_wer_vs_duration.png` |
| 10 | **Named Entity Accuracy** | NEA F1: 38.8% — misses 61% of names/numbers. These are the words context can't recover | Existing: `14_nea_vs_wwer_scatter.png` |
| 11 | **13 Tuning Experiments** | Parameter sweep: beam, lenpen, sampling, temperature. lenpen=1.0 eliminates empty outputs | Existing: `10_empty_and_hallucination_rates.png` + `16_improvement_J_vs_A.png` |
| 12 | **Limits of Tuning** | Tuning = mitigation, not cure. Core domain mismatch remains | **NEW graph: Hyperparameter sensitivity tornado** |
| 13 | **Curated Examples** | Side-by-side ref vs hyp with IS scores (see examples section below) | Formatted text table |
| 14 | **Live Demo** | Play 2-3 burned videos (see demo videos section below) | Video playback |
| 15 | **Research Breadth** | One-liner per report (7 reports): evaluation, tuning, prompts, confidence, beam search, fine-tuning, **intelligibility** | Simple list |

#### Section 3: Engineering Achievements (12 min, 7 slides) — 25%

| # | Slide | Key Content | Graph/Visual |
|---|-------|-------------|-------------|
| 16 | **Pipeline Architecture** | 8-stage flow: Normalize → ASR → LRS3 → Manifests → Clustering → Decode → Reports → Burns | Pipeline flow diagram |
| 17 | **Why Engineering Was Hard** | Research code → production. 37 bugs. HDR video, GPU encoding, Cython, fairseq patching, NVENC corruption | Bug count timeline or categories |
| 18 | **Modular Refactoring** | 823→393 lines, 11 modules, 37 tests. Before/after comparison | Side-by-side code structure |
| 19 | **Deployed Product** | Standalone container, desktop icon, web UI, drag-and-drop. "Runs on a standalone Linux machine, no cloud" | UI screenshot |
| 20 | **Smart Features** | Transcription reuse, golden k-means, video segmentation with overlap | Feature diagram |
| 21 | **Evaluation Infrastructure** | 16 analytical plots, per-segment HTML reports, CSV exports, custom NEA metric, **Intelligibility Score pipeline** (6-signal composite metric, per-segment IS scoring, automated IS classification) | Sample report screenshot |
| 22 | **Quality Process** | Git tags, EC2/container sync protocol, **7** research reports, comprehensive docs | Process diagram |

#### Section 4: Future Directions (10 min, 7 slides) — 35%

| # | Slide | Key Content | Graph/Visual |
|---|-------|-------------|-------------|
| 23 | **The Starting Point Is Better Than WER Says** | **KEY TRANSITION**: WER says 11.4% usable. IS says 39.9% properly captured. Context recovery analysis: 43.6-50.6% recoverable with context. "We're not starting from 11% — we're starting from 40%." This reframes the entire roadmap. | WER tiers vs IS tiers side-by-side |
| 24 | **Improvement Roadmap** | Phased: starting from IS 39.9% properly captured → Phase 1: confidence scoring to surface the good 40% → Phase 2: N-best to improve the fair 22% → Phase 3: fine-tuning to rescue the poor 22% | **WER trajectory line chart** |
| 25 | **Phase 1: Confidence Scoring** | IS already proves 40% is good. Now extract beam scores to FLAG it automatically. No additional model inference. 2-4 hours effort. | Annotated pipeline showing where scores exist |
| 26 | **Phase 2: N-Best Aggregation** | ROVER/MBR — currently discarding 19/20 beam candidates. 5-15% relative improvement. Moves "fair" tier segments up to "good". | Before/after diagram |
| 27 | **Phase 3: Fine-Tuning** | AVSpeech domain adaptation. 15-25 WER point reduction. ~$72-120 GPU cost. Attacks the core domain mismatch. | Training data comparison diagram |
| 28 | **Phase 4-5: Production** | Arabic (k-means model exists), multi-speaker, streaming, auto-tuning | Feature roadmap icons |
| 29 | **Key Takeaways** | (1) 2.5x WER gap measured, but IS shows 40% is already usable (2) Production system built with novel evaluation metrics (3) Clear path: surface the good, improve the fair, rescue the poor | 3-point summary |

#### Appendix / Backup Slides

| # | Slide | Key Content | When to use |
|---|-------|-------------|-------------|
| A1 | **Homophenes: The Lip-Reading Problem** | 50-70% of English sounds invisible on lips. Groups: p/b/m identical, t/d/n/s/z/l identical. Examples: "mom"↔"bomb", "collar"↔"color", "pads"↔"pants" | If someone asks "why does it confuse those words?" |
| A2 | **Catastrophic lenpen=2.0** | Experiment H: mean WER 171.5%, model generates paragraphs of hallucinated text | Boss deep-dive only |
| A3 | **Segment Stability Heatmap** | Which segments are always good/bad across all 13 configs | Boss deep-dive only |
| A4 | **Full Experiment Table** | All 13 experiments A-M with full metrics | Boss deep-dive only |

---

### Examples: What to Show and Why

The examples are the emotional core of the presentation. Each one should make a specific point.

#### For the main presentation (slides 2, 11, 12):

**1. "When it works, it's magic" — open with this**
- `IEa7qEkMvfQ_3__c5447488` — 33 words perfectly lip-read about insurance policies (WER 0%)
- **Why this one**: It's the longest perfect transcription. It includes domain-specific terms ("insurance company", "out of pocket expense"). It proves the technology fundamentally works. Open the presentation by playing this burned video — let the audience see it before explaining anything.

**2. "The hallucination problem" — the core research finding**
- `00MUdHQ7GGY_8__b1480c7a` — REF: "it doesn't have a carry strap..." → HYP: "this is david irving he's a holocaust denier..." (WER 100%)
- **Why this one**: It's the most dramatic example of hallucination. The model fabricates a coherent but completely fictional narrative. It shows the audience WHY this problem is hard — the output LOOKS correct, reads fluently, but is entirely made up. This is the slide that makes executives understand why confidence scoring matters.

**3. "Entertaining near-misses" — show visual ambiguity is real**
- `-POZpyVCN8k_9__c7b26ea8` — "admiral mcrae" → "animal migratory" (WER 33.3%)
- `-WQZsfHcPDM_7__5210cac1` — "each bottle contains 1 billion cfus of probiotics" → "each monitor has 1 million cfus of permafrost" (WER 57.9%)
- **Why these**: They're funny, memorable, and scientifically important. They show that lip shapes for "admiral/animal" and "bottle/monitor" are genuinely similar visually. This makes the audience appreciate that lip reading is inherently ambiguous — it's not just a bad model, it's a hard problem. The humor makes the point stick.

**4. "Tuning helps but has limits" — show the trade-off**
- `DBhaa45mAro_2__07d05c7a` — Baseline: EMPTY output (WER 100%) → Config J: partial transcription (WER 73.3%)
- `eLS1vcpGVHQ_12__e9dd9adc` — Baseline: "years ago when i was" (WER 90%) → Config J: 40-word TED talk hallucination (WER 400%)
- **Why these two together**: They're the yin and yang of hyperparameter tuning. Same config change fixes one segment and destroys another. This is the slide that makes technical bosses understand why there's no simple knob to turn — and why the roadmap matters.

#### What NOT to show in the main presentation (save for bosses):

- The catastrophic lenpen=2.0 examples (6833% WER) — too extreme, might make the audience question the entire approach
- The full experiment comparison table with 13 rows — too much data, use the summary instead
- The segment stability heatmap — fascinating for researchers but dense for mixed audience
- NEA vs WWER scatter plot in detail — mention the number (38.8% F1), don't dwell on the metric definition

#### For a separate boss deep-dive (technical session):

Your bosses will want to see the full picture. Prepare these as backup slides or a separate 20-minute session:

**Graphs for bosses (very technical):**
1. `09_boxplot_wwer_all_experiments.png` — full experiment comparison, they'll want to see all 13 configs
2. `12_segment_stability_heatmap.png` — which segments are consistently good/bad across configs (shows there's a stable core of ~11% always-good segments)
3. `01_wer_vs_duration.png` + `03_wwer_vs_duration.png` — the duration effect in detail
4. `11_wer_vs_wwer_scatter.png` — the lenpen paradox (higher corpus WER but lower segment WER)
5. `16_improvement_J_vs_A.png` — per-segment improvement analysis
6. Full experiment comparison table from `docs/tuning/experiment-comparison.csv`
7. The catastrophic lenpen=2.0 examples — they'll appreciate the systematic exploration
8. Report 6 fine-tuning analysis details — LoRA rank analysis, unfreezing strategy

**What bosses care about that clients don't:**
- Methodology rigor (did you explore the space systematically?)
- Reproducibility (can you reproduce these results?)
- The `do_sample=True` vs `False` difference and what it means
- Why you chose beam=20 over alternatives
- The exact mechanism of hallucination (LLM prior overwhelming visual signal)

#### For clients (results-driven):

**Graphs for clients:**
1. **Quality tier pie chart** (NEW) — immediately shows "11.4% usable" — they understand this
2. **CDF WWER** (`15_cdf_wwer_curated.png`) — "X% of segments are below Y% error" = actionable threshold
3. **Empty and hallucination rates** (`10_empty_and_hallucination_rates.png`) — shows failure modes
4. **WER trajectory roadmap** (NEW) — "here's where we are, here's where we're going"
5. Duration histogram (`13_duration_histogram.png`) — context on what the data looks like

**What clients care about that bosses don't:**
- "Can I trust the output?" — confidence scoring pitch
- "Does it work on MY videos?" — domain relevance
- "What do I get for my money?" — roadmap with cost/benefit per phase
- The UI demo — they want to see themselves using it
- Burned video demos — seeing is believing

---

### Demo Video Selection

**For Slide 2 (opening hook):** Play `IEa7qEkMvfQ_3__c5447488_with_hyp.mp4` — the 33-word perfect transcription. Start with the video, let the audience read along, THEN explain what they just saw. Maximum impact.

**For Slide 12 (live demo):** Play 3 videos in sequence:
1. `d8BR6hsvzoY_31__2e9546df_with_hyp.mp4` — "buy one get one free" (WER 0%, commercial-style, short, punchy)
2. `-POZpyVCN8k_9__c7b26ea8_with_hyp.mp4` — "admiral mcrae" → "animal migratory" (funny near-miss, audience will laugh)
3. `00MUdHQ7GGY_8__b1480c7a_with_hyp.mp4` — the David Irving hallucination (dramatic failure, audience gasps)

**Why this sequence**: Good → Funny → Bad. You start by reinforcing that the system works, make the audience laugh with a relatable error, then hit them with the hallucination problem. By the time you show the hallucination, they're engaged enough to understand why it matters. End with: "This is why our roadmap focuses on confidence scoring — knowing WHEN to trust the output."

All burned videos are at: `english_full_results/client_outputs/burned_videos/`

---

### Graphs: What to Use, What to Generate

#### Existing plots to use (from `docs/evaluation/plots/`):

| Plot | Use on Slide | Why | Audience |
|------|-------------|-----|----------|
| `01_wer_vs_duration.png` | 7 (Why the Gap) | Shows short segments fail catastrophically — the most actionable finding | Both |
| `09_boxplot_wwer_all_experiments.png` | 6 (Distribution) | Shows the spread across experiments — bosses want this, clients get the headline | Both (simplified for clients) |
| `10_empty_and_hallucination_rates.png` | 9 (Tuning) | Empty vs hallucination trade-off per config — intuitive failure mode comparison | Both |
| `14_nea_vs_wwer_scatter.png` | 8 (NEA) | Shows entity accuracy correlation — technical validation of NEA metric | Bosses |
| `16_improvement_J_vs_A.png` | 9 (Tuning) | Per-segment improvement from best config — shows tuning is real but limited | Both |
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
| **WER Trajectory Line Chart** | 21 (Roadmap) | Line: Current 64% → Phase 1: 55% → Phase 2: 45% → Phase 3: 42%, with mission labels | `docs/backlog/mission-backlog.md` |
| **Hyperparameter Sensitivity Tornado** | 10 (Limits) | lenpen from -0.5 to 2.0: empty rate (44.9% → 0%) vs hallucination rate (opposite) | Experiment comparison data |
| **Before/After Tuning Paired Bars** | 9 (Tuning) | Baseline vs best config: WER, WWER, empty%, hallucination% side by side | Experiment CSV |

Script to extend: `docs/evaluation/plots/generate_experiment_plots.py` (existing 643-line generator)

---

### Dual-Audience Strategy

**Structure each slide as a newspaper**: Headline tells the story for execs/clients, body provides evidence for technical team.

| Aspect | Clients / Potential Clients | Technical Bosses |
|--------|----------------------------|-----------------|
| **What they want to know** | Does it work? Can I trust it? What do I get next? | Is the methodology sound? What are the limits? What resources do you need? |
| **Language** | "The model makes up text" not "hallucination" | Full technical vocabulary OK |
| **Metrics** | Quality tiers (% usable), burned video demos | WER/WWER/NEA with statistical context |
| **Graphs** | Pie charts, bar charts, roadmap trajectory | Scatter plots, heatmaps, boxplots, CDFs |
| **Examples** | Good → Funny → Bad sequence | Full experiment table + catastrophic edge cases |
| **Roadmap framing** | "Investment → return" (cost per phase → improvement) | "Research agenda" (what's novel, what's engineering) |
| **Key takeaway** | "This works today, and here's how it gets better" | "We've systematically characterized the gap and have a principled plan" |

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
| **Intelligibility methodology** | `docs/evaluation/intelligibility_methodology.md` |
| **Intelligibility scores (1497 rows)** | `docs/evaluation/intelligibility/intelligibility_scores.csv` |
| **Intelligibility summary** | `docs/evaluation/intelligibility/intelligibility_summary.json` |
| **Intelligibility report (docx)** | `docs/evaluation/intelligibility/intelligibility_report.docx` |
| Mission backlog | `docs/backlog/mission-backlog.md` |
| Existing 2025 pptx | `docs/paper/Presentation_2025.pptx` |
| Branding | `docs/branding/` |
| Pipeline architecture | `docs/architecture.md` |
| Segment metadata | `english_full_results/segment_metadata.json` |
