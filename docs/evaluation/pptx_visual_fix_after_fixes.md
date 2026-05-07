# Argos VSP — PowerPoint Fix Manifest

Categorized fix list for slide-writing phase. 
Pulled from BLOCKER/MAJOR/MINOR issues across audited decks.

## Argos_VSP_AFTER_AMOSI_May2026.pptx

### BLOCKER: none

### MAJOR (177)

**Slide 5 — What is Visual Speech Processing?**
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 7' overlap by 84% of smaller bbox (textA: "System + human reader outperfo" / textB: "5")

**Slide 8 — How It Works: Data Flow**
- [OCCLUSION] Text shape 'TextBox 7' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 17' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 22' ("↓…") is 33% covered by later shape(s).

**Slide 9 — 8-Stage Automated Pipeline**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 11', text "▶…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 16', text "▼…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 20', text "evaluation only…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 24', text "▼…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 28', text "▼…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 45', text "Preprocessing…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 47', text "Feature Extraction…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 49', text "LLM Inference…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 51', text "Output…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 52', text "auto_avsr  ·  av_hubert  ·  VSP-LLM…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 54', text "Existed in academic repo…")
- [OVERLAP] Shapes 'TextBox 20' & 'TextBox 54' overlap by 86% of smaller bbox (textA: "evaluation only" / textB: "Existed in academic repo")
- [OCCLUSION] Text shape 'TextBox 20' ("evaluation only…") is 86% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 33' ("6. K-means…") is 100% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 34' ("Featureclustering…") is 100% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 37' ("7. LLM Decode…") is 100% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 38' ("AV-HuBERT +LLaMA-2…") is 100% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 39' ("→…") is 100% covered by later shape(s).
- [ANIMATION] Slide has 10 click-step animation groups (>8 risks audience disengagement).

**Slide 10 — The Benchmark: Paper vs Reality**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 10', text "Note: Our best LRS3 reproduction achieve…")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 10' overlap by 33% of smaller bbox (textA: "Different dataset, fundamental" / textB: "Note: Our best LRS3 reproducti")

**Slide 13 — Diversity of Inputs — Not LRS3**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "Sample lip-reading frame — visual signal…")

**Slide 16 — What the AVSR Literature Reports vs What Users Get**
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 36% of smaller bbox (textA: "• WER (Word Error Rate) - prim" / textB: "All three failure modes (gibbe")

**Slide 17 — LLM-as-a-Judge: Gold Standard (1,497 Pairs)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "v1 blind judge   /   Opus 4.6   /   1,49…")

**Slide 19 — Judge Example 1: Named Entity Swap**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Named Entity Swap — meaning fully preser…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "Only the company name changed (bernreute…")
- [VIDEO] Embedded media (media2.mp4, 1375351 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media2.mp4, 1375351 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.

**Slide 20 — Judge Example 2: Truncated but Core Preserved**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Truncation — beginning and end lost, cor…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "The opening context ('home video market …")

**Slide 21 — Judge Example 3: Technical Vocabulary Drift**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Domain Vocabulary Drift — structure inta…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "The argument structure is perfect: 'radi…")
- [VIDEO] Embedded media (media4.mp4, 2540214 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media4.mp4, 2540214 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.

**Slide 22 — Judge Example 4: Scientific Vocabulary Lost**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Scientific Terms Lost — repetitive struc…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "The 'tells us when to X' pattern is capt…")

**Slide 23 — Judge Example 5: Cooking Domain Confusion**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Domain Confusion — food context right, i…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "The model knows it's a cooking video: 'd…")

**Slide 24 — Judge Example 6: Topic Hijack**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Topic Hijack — grammatically fluent, com…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "'Overhead lights' → 'overheard ghost whi…")

**Slide 25 — Where IS and the Judge Disagree**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "REF: "one really nice thing about this i…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 10', text "• Harmless hallucination (extra words, c…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "REF: "all you have to do is unscrew"
HYP…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 17', text "• Domain confusion (medical → wellness)…")

**Slide 26 — Context Exposes Hidden Failures**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "REF: "...because I'm a lover of"
HYP: ".…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "More context false positives:• "lazy na…")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 13' overlap by 39% of smaller bbox (textA: "• 80.1% of judgments stable ac" / textB: "Domain knowledge raises the ba")

**Slide 28 — IS Signals: Word Accuracy & Length**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 8', text "▸ Treats all words equally — every error…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "▸ Example: "Admiral McRae" wrong = 2× pe…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 16', text "▸ Hallucinated segments average ratio 2.…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 17', text "IS = 0.25×Semantic + 0.15×(Phonetic + In…")

**Slide 30 — IS Signals: Phonetic & Named Entities**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "▸ Example: "Admiral McRae" vs "animal mi…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "▸ Mean F1 = 38.9% — entities missed in 8…")

**Slide 35 — The Gap: Where WER Lies Most**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "WER correlates with IS (r≈−0.7) but not …")

**Slide 37 — Where the System Works: Oracle vs Realistic**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "What the model can produce on the 1,497-…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "LLM Judge v3 Y+P: 71.08%  (baseline 68.4…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "What the user can confidently rely on (≥…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 16', text "Joint conf+beam-agreement bands  •  oper…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 17', text "Oracle metrics evaluate all 1,497 segmen…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 18', text "Tier 5 — Excellent (IS ≥ 4.0)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 20', text "291  (19.4%)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 21', text "Tier 4 — Good (3.0–3.99)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 23', text "324  (21.6%)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 24', text "Tier 3 — Fair (2.0–2.99)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 26', text "312  (20.8%)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 27', text "Tier 2 — Poor (1.0–1.99)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 29', text "329  (22.0%)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 30', text "Tier 1 — Failed (< 1.0)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 32', text "241  (16.1%)…")

**Slide 38 — From Literature Metric to User-Trusted Output**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 18', text "Cards 1–3 are computed across all 1,497 …")

**Slide 40 — Failure Mode Taxonomy (1/2): Highest Impact First**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 4', text "Grounded in ASR error taxonomy (Fosler-L…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 20', text "Ordered by impact — highest to lowest (c…")

**Slide 42 — Failure Modes: Real Examples**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 6', text "“carry strap”…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 8', text "“holocaust denier explanationof the fin…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "WER 100%  |  IS 0.1…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 10', text "Why this category?…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 11', text "The model generated 8 words froma 2-wor…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 14', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 15', text "“i’ve made lots of videosabout weight l…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 16', text "Prediction:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 17', text "“when i was a little girl ialways wante…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 18', text "WER 97%  |  IS 0.38…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 19', text "Why this category?…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 20', text "Output is similar LENGTH toreference (n…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 23', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 24', text "“about the 13th amendmentthe 13th amend…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 25', text "Prediction:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 26', text "“13th may mean something tohim because …")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 27', text "WER 81%  |  IS 2.14…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 28', text "Why this category?…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 29', text "The word “13th” survived but“amendment”…")

**Slide 50 — Band Reliability - Overall P(correct | band)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "All numbers from audit JSON keys perword…")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 48% of smaller bbox (textA: "Joint rule's biggest reliabili" / textB: "All numbers from audit JSON ke")

**Slide 51 — Green Reliability Depends on Segment Quality**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "Below 0.65 (legacy rule only):0.55-0.65…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 8', text "Caveat: stratified P(correct|green) unde…")

**Slide 52 — Green Leakage - When High Confidence Misleads**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "Off by 1000x. Confident, fluent, wrong.…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "Token tokenisation mis-merge.…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 21', text "Visually similar mouth shapes.…")

**Slide 53 — Three Calibrated Thresholds on Segment mean_prob**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "Thresholds are Llama-2-7b specific. Any …")

**Slide 55 — Per-Word Bands Stratified by NIV Outcome**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "• 62.5pp green->red spread inside Y+P - …")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "Per-word flag is genuine signal inside S…")

**Slide 56 — Joint Confidence + Beam-Agreement Band Rule**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "Llama-2-7b specific. Any LLM swap forces…")
- [OVERLAP] Shapes 'TextBox 14' & 'TextBox 15' overlap by 48% of smaller bbox (textA: "WHY ADD AGREEMENT?  Beam agree" / textB: "Llama-2-7b specific. Any LLM s")

**Slide 57 — Beam Agreement Adds Independent Signal**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "Diagnostic script: diagnose_confidence_s…")

**Slide 58 — Trust-Gate Operating Points (per-segment)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "Audit keys: trustgate_new_t{10,20,30,40,…")

**Slide 59 — N-best Aggregation: From One to All 20 Hypotheses (Mission 6)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "Recognizer Output Voting Error Reduction…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Minimum Bayes Risk Decoding…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 13', text "ROVER: Fiscus (1997), NIST  |  MBR Decod…")

**Slide 60 — N-best Aggregation: v3 Judge Paired Tests**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "• Y verdict tied across all methods (no …")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "v3 dual-conf judge   /   Opus 4.7   /   …")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 45% of smaller bbox (textA: "• Y verdict tied across all me" / textB: "v3 dual-conf judge   /   Opus ")

**Slide 64 — Demo - Obama Trust Tier**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS  (per-word band observation)…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 13' overlap by 72% of smaller bbox (textA: "Research observation: 27/29 pe" / textB: "64")
- [VIDEO] Embedded media (media11.mp4, 3119635 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media11.mp4, 3119635 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.

**Slide 65 — Demo - Obama: TRUST under conf-only fallback (no n-best sidecar - partial recovery still narrated)**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS  (per-word band observation)…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 13' overlap by 72% of smaller bbox (textA: "Research observation: most wor" / textB: "65")
- [VIDEO] Embedded media (media12.mp4, 3128275 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media12.mp4, 3128275 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.

**Slide 66 — Demo - INSPECT (closest to STRIP in the Obama set; lowest mean_prob = 0.799)**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS  (per-word band observation)…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 13' overlap by 72% of smaller bbox (textA: "Research observation: the mode" / textB: "66")
- [VIDEO] Embedded media (media13.mp4, 2520000 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media13.mp4, 2520000 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.

**Slide 67 — Demo - Strip: entity swap auto-flagged**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS  (per-word band observation)…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 13' overlap by 72% of smaller bbox (textA: "Research observation: the enti" / textB: "67")
- [VIDEO] Embedded media (media2.mp4, 1375351 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media2.mp4, 1375351 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.

**Slide 68 — Demo - Salvage: technical vocabulary drift**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS  (per-word band observation)…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 13' overlap by 72% of smaller bbox (textA: "Research observation: argument" / textB: "68")
- [VIDEO] Embedded media (media4.mp4, 2540214 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media4.mp4, 2540214 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.

**Slide 71 — Five Phases — From IS 2.5 to Target IS 3.3–3.7**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 4', text "Phase 1 (shipped)  Surface the good 62%
…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "Phase 2 (shipped)  Fix small & content e…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "Phase 3  Better world knowledge
Llama 3.…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Phase 4  Scale data 20K–50K
Fine-tune vi…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "Phase 5  Error Correction (GER)
Second L…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 15', text "References: ROVER (Fiscus 1997)  |  GER …")

**Slide 72 — IS Improvement Roadmap — From 2.5 to 3.5**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "+0.10  |  Fixes: Accum (52) + Details (7…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "+0.50  |  Fixes: Halluc (108) + Wrong To…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 19', text "+0.95  |  Fixes: all remaining via data …")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 86% of smaller bbox (textA: "+0.95  |  Fixes: all remaining" / textB: "Conversion: ~0.033 IS per pp W")
- [OCCLUSION] Text shape 'TextBox 19' ("+0.95  |  Fixes: all remaining via data …") is 86% covered by later shape(s).

**Slide 73 — Stronger LLM + Smart Prompts = Force Multiplier**
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 12', text "GER: Chen et al. (2024), ICASSP  |  Scal…")

**Slide 76 — Arabic Pipeline: Replication Roadmap**
- [OCCLUSION] Text shape 'TextBox 8' ("• RTL text & normalization
• RTL handlin…") is 63% covered by later shape(s).

**Slide 81 — A1: Homophenes — The Lip-Reading Problem**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 9', text "A1…")

**Slide 83 — Appendix: PCA Loadings on the 6 IS Signals**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "• PC1 (68.4%) = signal quality — all 5 c…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "Source: docs/evaluation/is_pca_analysis.…")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 11' overlap by 72% of smaller bbox (textA: "Source: docs/evaluation/is_pca" / textB: "A3")

**Slide 84 — Appendix: Human-IS Path B (Pre-Study Estimates)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "Caveat: Path B is pre-study. Reproducibl…")

**Slide 85 — A4: LLM Salvage — Recoverable Segments**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "58% of salvageable have moderate WER (50…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "Categories overlap — segments can exhibi…")

**Slide 88 — Appendix: McNemar Tests — N-Best Methods vs Baseline**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "Caveat: identical-text drift varies (12.…")
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 9' overlap by 92% of smaller bbox (textA: "Caveat: identical-text drift v" / textB: "A8")

### MINOR (166)

**Slide 2 — What was done? (1/2)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 3 — What was done? (2/2)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 4 — Presentation Overview**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 5 — What is Visual Speech Processing?**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 6 — The Invisible Problem: Visemes**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 7 — How It Works: Three Components**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 8 — How It Works: Data Flow**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 9 — 8-Stage Automated Pipeline**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 25% of smaller bbox (textA: "Whispertranscription" / textB: "evaluation only")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 54' overlap by 5% of smaller bbox (textA: "Whispertranscription" / textB: "Existed in academic repo")

**Slide 10 — The Benchmark: Paper vs Reality**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 12% of smaller bbox (textA: "10" / textB: "Note: Our best LRS3 reproducti")

**Slide 11 — The Reality Gap**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Body shows 17% but notes only mention [20, 25, 30, 34, 63, 64] — possible mismatch.

**Slide 12 — Same WER, Different Effects**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 13 — Diversity of Inputs — Not LRS3**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 14 — WER: The Metric That Lies**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 15 — RESEARCH FINDINGS**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 16 — What the AVSR Literature Reports vs What Users Get**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 14' & 'TextBox 15' overlap by 30% of smaller bbox (textA: "REF: "the overhead lights are " / textB: "Same WER. Same paper score. On")
- [NOTES] Body shows 25% but notes only mention [50] — possible mismatch.

**Slide 17 — LLM-as-a-Judge: Gold Standard (1,497 Pairs)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 18 numbers but lack any source reference (.md/.csv path).

**Slide 18 — LLM Judge: Deep Dive**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 9 numbers but lack any source reference (.md/.csv path).

**Slide 19 — Judge Example 1: Named Entity Swap**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 15% but notes only mention [18] — possible mismatch.

**Slide 20 — Judge Example 2: Truncated but Core Preserved**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 41% but notes only mention [48] — possible mismatch.

**Slide 21 — Judge Example 3: Technical Vocabulary Drift**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 22 — Judge Example 4: Scientific Vocabulary Lost**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 23 — Judge Example 5: Cooking Domain Confusion**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 43% but notes only mention [89] — possible mismatch.

**Slide 24 — Judge Example 6: Topic Hijack**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 25 — Where IS and the Judge Disagree**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 17% of smaller bbox (textA: "Paraphrases and phonetic bridg" / textB: "• Harmless hallucination (extr")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 17' overlap by 17% of smaller bbox (textA: "Structural match hides semanti" / textB: "• Domain confusion (medical → ")
- [NOTES] Notes cite 14 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 71% but notes only mention [0, 1, 100, 111] — possible mismatch.

**Slide 26 — Context Exposes Hidden Failures**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 13' overlap by 28% of smaller bbox (textA: "More context false positives:" / textB: "Domain knowledge raises the ba")
- [NOTES] Notes cite 7 numbers but lack any source reference (.md/.csv path).

**Slide 27 — Why LLM as a Judge Is Not Enough**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 28 — IS Signals: Word Accuracy & Length**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 29 — IS Signals: Semantic Similarity**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 80% but notes only mention [25] — possible mismatch.

**Slide 30 — IS Signals: Phonetic & Named Entities**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 5 numbers but lack any source reference (.md/.csv path).

**Slide 31 — Do 6 Signals Actually Measure 6 Things?**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 32 — IS in Action: Two Real Segments**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 33 — Two Dimensions of Quality (PCA)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 34 — Model Comparison: IS Profiles**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 14 numbers but lack any source reference (.md/.csv path).

**Slide 35 — The Gap: Where WER Lies Most**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 36 — A8: LLM Judge × IS Tier Cross-Tabulation**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 10 numbers but lack any source reference (.md/.csv path).

**Slide 37 — Where the System Works: Oracle vs Realistic**
- [LAYOUT] Shape 'TextBox 29' within 0.1in of slide edge (left=11.30, top=5.90, right_gap=0.03, bot_gap=1.28)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Body shows 19% but notes only mention [5, 23, 30, 61, 65, 68, 71] — possible mismatch.

**Slide 38 — From Literature Metric to User-Trusted Output**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 39 — Failure Mode Taxonomy**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 8 numbers but lack any source reference (.md/.csv path).

**Slide 40 — Failure Mode Taxonomy (1/2): Highest Impact First**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 100% but notes only mention [13, 18, 44] — possible mismatch.

**Slide 41 — Failure Mode Taxonomy (2/2): Accumulated → Signal Loss**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 42 — Failure Modes: Real Examples**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 6' overlap by 9% of smaller bbox (textA: "Reference:" / textB: "“carry strap”")
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 9% of smaller bbox (textA: "Prediction:" / textB: "“holocaust denier explanation")
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 9% of smaller bbox (textA: "Why this category?" / textB: "The model generated 8 words fr")
- [OVERLAP] Shapes 'TextBox 14' & 'TextBox 15' overlap by 9% of smaller bbox (textA: "Reference:" / textB: "“i’ve made lots of videosabou")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 17' overlap by 9% of smaller bbox (textA: "Prediction:" / textB: "“when i was a little girl ial")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 9% of smaller bbox (textA: "Why this category?" / textB: "Output is similar LENGTH tore")
- [OVERLAP] Shapes 'TextBox 23' & 'TextBox 24' overlap by 9% of smaller bbox (textA: "Reference:" / textB: "“about the 13th amendmentthe ")
- [OVERLAP] Shapes 'TextBox 25' & 'TextBox 26' overlap by 9% of smaller bbox (textA: "Prediction:" / textB: "“13th may mean something tohi")
- [OVERLAP] Shapes 'TextBox 28' & 'TextBox 29' overlap by 9% of smaller bbox (textA: "Why this category?" / textB: "The word “13th” survived but“")
- [NOTES] Body shows 18% but notes only mention [100] — possible mismatch.

**Slide 43 — LLM Salvage: Three Real Recoveries**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 32' overlap by 6% of smaller bbox (textA: "A wise viewer watching a relig" / textB: "43")
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 44 — LLM Salvage: Domain Context Fills the Gaps**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 32' overlap by 6% of smaller bbox (textA: "A viewer watching a religious " / textB: "44")
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 45 — A6: Failure Mode Examples**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 46 — Confidence Without Ground Truth**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 47 — Two Layers of Confidence (Per-Word + Per-Segment)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 48 — Confidence Scoring (shipped April 30 2026) — Surface the Good 65%**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 65% but notes only mention [20, 60] — possible mismatch.

**Slide 49 — Per-Word Confidence Bands - Distribution**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Body shows 33% but notes only mention [80, 89] — possible mismatch.

**Slide 50 — Band Reliability - Overall P(correct | band)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 6 numbers but lack any source reference (.md/.csv path).

**Slide 51 — Green Reliability Depends on Segment Quality**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 9' overlap by 15% of smaller bbox (textA: "Caveat: stratified P(correct|g" / textB: "Headline: green-band reliabili")
- [NOTES] Body shows 96% but notes only mention [50] — possible mismatch.

**Slide 52 — Green Leakage - When High Confidence Misleads**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 53 — Three Calibrated Thresholds on Segment mean_prob**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 24% of smaller bbox (textA: "• Keeps 28% of segment volume
" / textB: "Thresholds are Llama-2-7b spec")
- [NOTES] Body shows 28% but notes only mention [50] — possible mismatch.

**Slide 54 — Three-Tier Policy - Per-Tier Counts and Reliability**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Body shows 95% but notes only mention [60] — possible mismatch.

**Slide 55 — Per-Word Bands Stratified by NIV Outcome**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 27% of smaller bbox (textA: "• 62.5pp green->red spread ins" / textB: "Per-word flag is genuine signa")

**Slide 56 — Joint Confidence + Beam-Agreement Band Rule**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 57 — Beam Agreement Adds Independent Signal**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 58 — Trust-Gate Operating Points (per-segment)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 59 — N-best Aggregation: From One to All 20 Hypotheses (Mission 6)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 60 — N-best Aggregation: v3 Judge Paired Tests**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 61 — Why MBR Won the Default-Display Slot**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 62 — v1 vs v3 Judge: A Prompt-Design Lesson**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 63 — Demo: OK → Almost There → Hallucination**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 64 — Demo - Obama Trust Tier**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 6 numbers but lack any source reference (.md/.csv path).

**Slide 65 — Demo - Obama: TRUST under conf-only fallback (no n-best sidecar - partial recovery still narrated)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 8 numbers but lack any source reference (.md/.csv path).

**Slide 66 — Demo - INSPECT (closest to STRIP in the Obama set; lowest mean_prob = 0.799)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 7 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 45% but notes only mention [37] — possible mismatch.

**Slide 67 — Demo - Strip: entity swap auto-flagged**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 68 — Demo - Salvage: technical vocabulary drift**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 69 — FUTURE DIRECTIONS**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 70 — Starting from 61.9%, Not 25%**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Body shows 41% but notes only mention [25, 30, 61, 64] — possible mismatch.

**Slide 71 — Five Phases — From IS 2.5 to Target IS 3.3–3.7**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 15' & 'TextBox 17' overlap by 20% of smaller bbox (textA: "References: ROVER (Fiscus 1997" / textB: "71")
- [NOTES] Body shows 62% but notes only mention [8, 26, 85] — possible mismatch.

**Slide 72 — IS Improvement Roadmap — From 2.5 to 3.5**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 73 — Stronger LLM + Smart Prompts = Force Multiplier**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 5 numbers but lack any source reference (.md/.csv path).

**Slide 74 — LLM Upgrade: Why It Matters**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 8% of smaller bbox (textA: "Current WER" / textB: "64%")
- [OVERLAP] Shapes 'TextBox 13' & 'TextBox 14' overlap by 8% of smaller bbox (textA: "LLM swap alone" / textB: "−3–8 pp")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 17' overlap by 8% of smaller bbox (textA: "+ Smart prompts" / textB: "−5–10 pp")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 8% of smaller bbox (textA: "+ 20K segments" / textB: "−10–15 pp")
- [OVERLAP] Shapes 'TextBox 22' & 'TextBox 23' overlap by 8% of smaller bbox (textA: "Target WER" / textB: "35–40%")
- [NOTES] Notes cite 32 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 64% but notes only mention [5, 18, 20, 25, 30, 35, 40, 44, 61] — possible mismatch.

**Slide 75 — Fine-Tuning: Limited Data, Limited Gains**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 9 numbers but lack any source reference (.md/.csv path).

**Slide 76 — Arabic Pipeline: Replication Roadmap**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 12' overlap by 28% of smaller bbox (textA: "• RTL text & normalization
• R" / textB: "Realistic estimate: 2–3 months")

**Slide 77 — AV-HuBERT: Why It’s Not Language-Locked**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 78 — Arabic Adaptation: What Changes**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 79 — Key Takeaways**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Body shows 64% but notes only mention [61, 71] — possible mismatch.

**Slide 80 — Thank You**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 81 — A1: Homophenes — The Lip-Reading Problem**
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 82 — A3: IS Component Correlation**
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 5' overlap by 13% of smaller bbox (textA: "PCA: 6 IS signals collapse int" / textB: "Cross-Config Stability (16 con")
- [NOTES] Notes cite 6 numbers but lack any source reference (.md/.csv path).

**Slide 87 — A9: Context Evaluation — Transition Details**
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 40% but notes only mention [80] — possible mismatch.

**Slide 88 — Appendix: McNemar Tests — N-Best Methods vs Baseline**
- [NOTES] Notes cite 15 numbers but lack any source reference (.md/.csv path).

