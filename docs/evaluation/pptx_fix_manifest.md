# Argos VSP — PowerPoint Fix Manifest

Categorized fix list for slide-writing phase. 
Pulled from BLOCKER/MAJOR/MINOR issues across audited decks.

## Argos_VSP_Final_84slides_Mar2026.pptx

### BLOCKER (4)

**Slide 7 — What is Visual Speech Processing?**
- [ANIMATION] Animation references 1 non-existent shape id(s): ['4']

**Slide 47 — Curated Examples — Video Gallery**
- [ANIMATION] Animation references 6 non-existent shape id(s): ['11', '13', '15', '5', '7']

**Slide 48 — Demo: OK → Almost There → Hallucination**
- [ANIMATION] Animation references 3 non-existent shape id(s): ['10', '4', '7']

**Slide 52 — 8-Stage Automated Pipeline**
- [LAYOUT] Shape 'Picture 3' extends outside slide canvas (bbox left=0.60 top=1.45 right=12.73 bottom=9.23; canvas 13.33x7.50)

### MAJOR (183)

**Slide 7 — What is Visual Speech Processing?**
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 7' overlap by 84% of smaller bbox (textA: "System + human reader outperfo" / textB: "7")

**Slide 10 — How It Works: Data Flow**
- [OCCLUSION] Text shape 'TextBox 7' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 17' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 22' ("↓…") is 33% covered by later shape(s).

**Slide 11 — The Benchmark: Paper vs Reality**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 10', text "Note: Our best LRS3 reproduction achieve…")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 10' overlap by 33% of smaller bbox (textA: "Different dataset, fundamental" / textB: "Note: Our best LRS3 reproducti")

**Slide 17 — Judge Example 1: Named Entity Swap**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Named Entity Swap — meaning fully preser…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "Only the company name changed (bernreute…")

**Slide 18 — Judge Example 2: Truncated but Core Preserved**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Truncation — beginning and end lost, cor…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "The opening context ('home video market …")

**Slide 19 — Judge Example 3: Technical Vocabulary Drift**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Domain Vocabulary Drift — structure inta…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "The argument structure is perfect: 'radi…")

**Slide 20 — Judge Example 4: Scientific Vocabulary Lost**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Scientific Terms Lost — repetitive struc…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "The 'tells us when to X' pattern is capt…")

**Slide 21 — Judge Example 5: Cooking Domain Confusion**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Domain Confusion — food context right, i…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "The model knows it's a cooking video: 'd…")

**Slide 22 — Judge Example 6: Topic Hijack**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Prediction:…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Topic Hijack — grammatically fluent, com…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "'Overhead lights' → 'overheard ghost whi…")

**Slide 24 — IS Signals: Word Accuracy & Length**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 8', text "▸ Treats all words equally — every error…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "▸ Example: "Admiral McRae" wrong = 2× pe…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 16', text "▸ Hallucinated segments average ratio 2.…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 17', text "IS = 0.25×Semantic + 0.15×(Phonetic + In…")

**Slide 26 — IS Signals: Phonetic & Named Entities**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "▸ Example: "Admiral McRae" vs "animal mi…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "▸ Mean F1 = 38.9% — entities missed in 8…")

**Slide 30 — The Gap: Where WER Lies Most**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "IS WER correlates with IS (r≈−0.7) but n…")

**Slide 31 — Intelligibility Score: 61.6% Useful Output**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 4', text "SemanticSim(25%)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "PhoneticSim(15%)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "Inv.WER(15%)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Inv.WWER(15%)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "NEAF1(15%)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 14', text "LengthRatio(15%)…")

**Slide 32 — Two Evaluation Systems, One Framework**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 14', text "Ref: "what does this chord sound like to…")

**Slide 34 — Where IS and the Judge Disagree**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "REF: "one really nice thing about this i…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 10', text "• Harmless hallucination (extra words, c…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "REF: "all you have to do is unscrew"
HYP…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 17', text "• Domain confusion (medical → wellness)…")

**Slide 35 — Context Exposes Hidden Failures**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "REF: "...because I'm a lover of"
HYP: ".…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "More context false positives:• "lazy na…")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 13' overlap by 39% of smaller bbox (textA: "• 80.1% of judgments stable ac" / textB: "Domain knowledge raises the ba")

**Slide 38 — Failure Mode Taxonomy (1/2): Highest Impact First**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 4', text "Grounded in ASR error taxonomy (Fosler-L…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 20', text "Ordered by impact — highest to lowest (c…")

**Slide 40 — Failure Modes: Real Examples**
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

**Slide 42 — When Metrics Disagree: What It Tells Us**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text ""the team discussed quarterly" → "team d…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text ""Dr. Chen presented Q3 results" → "Dr. C…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text ""reduce spending" → "cut the budget"WER…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text ""the alliance was formed" → "the lions w…")

**Slide 43 — When Metrics Disagree: More Patterns**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "Ref: "the thirteenth amendment abolished…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "Ref: "carry strap" → Hyp: 3 paragraphs a…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text ""the 13th amendment" → "the important de…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "Every signal is mediocre, none catastrop…")

**Slide 45 — LLM Salvage: Three Real Recoveries**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 6', text "IS 1.29  |  WER 150%  |  Prob 0.55…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 7', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 8', text "“when jesus rose again”…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 9', text "Prediction:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 10', text "“in one sense it’s roseand kennedy”…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 11', text "How a viewer recovers this:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "A wise viewer watching a religious progr…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 15', text "IS 2.18  |  WER 75%  |  Prob 0.90…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 16', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 17', text "“moving conceptual surface dataover to …")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 18', text "Prediction:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 19', text "“moved the conceptual rulesover to engi…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 20', text "How a viewer recovers this:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 21', text "Core meaning intact: “moving concepts → …")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 24', text "IS 2.55  |  WER 40%  |  Prob 0.95…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 25', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 26', text "“over the last 10 years we havehad 8,61…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 27', text "Prediction:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 28', text "“over the last 10 years we havehad 1,60…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 29', text "How a viewer recovers this:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 30', text "Grammar and word order are perfect. Only…")

**Slide 46 — LLM Salvage: Domain Context Fills the Gaps**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 6', text "IS 2.75  |  WER 43%  |  Prob 0.90…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 7', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 8', text "“the fear of allah is completelygone … …")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 9', text "Prediction:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 10', text "“the fear of the loss complete… no more…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 11', text "How a wise viewer recovers this:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "A viewer watching a religious sermon rec…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 15', text "IS 2.86  |  WER 72%  |  Prob 0.90…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 16', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 17', text "“india china afghanistan allthese diffe…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 18', text "Prediction:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 19', text "“middle east and afghanistanall these d…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 20', text "How a wise viewer recovers this:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 21', text "WER is 72% because country names changed…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 24', text "IS 2.07  |  WER 89%  |  Prob 0.80…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 25', text "Reference:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 26', text "“i have a tablespoon ofjalapeno fresh j…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 27', text "Prediction:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 28', text "“i have a dietary smoothiei’ve got the …")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 29', text "How a wise viewer recovers this:…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 30', text "IS rates this a near-total failure (2.07…")

**Slide 47 — Curated Examples — Video Gallery**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 5', text "Convention & books — meaning fully captu…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 7', text "Marilyn Monroe wallpaper — proper nouns …")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 9', text "Music discussion — gist preserved, phras…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 11', text "Spelling → smelling — phonetic confusion…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 13', text "Admiral McRae → animal migratory — class…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 15', text "Doxology → fabricated story — total hall…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 17' overlap by 68% of smaller bbox (textA: "Spelling → smelling — phonetic" / textB: "47")

**Slide 48 — Demo: OK → Almost There → Hallucination**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text ""consumers want a bigger smartphone"→ "…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text ""james and will talk about street photog…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text ""carry strap" → "holocaust denier"…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "Click each video to play.…")

**Slide 51 — 8-Stage Automated Pipeline**
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

**Slide 53 — Building the Pipeline: The Engineering Journey**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "• 3 independent repos with no docs
• Har…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "• EC2 → Docker container
• Missing NVIDI…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 14', text "• 37+ bugs found and fixed
• NVENC silen…")

**Slide 55 — Live Demo**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "No command line…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 13', text "Fully automatic…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 17', text "Per-segment quality…")

**Slide 60 — Five Phases — From IS 2.5 to Target IS 3.3–3.7**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 4', text "Phase 1  Surface the good 62%
Confidence…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "Phase 2  Fix small & content errors
N-be…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "Phase 3  Better world knowledge
Llama 3.…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Phase 4  Scale data 20K–50K
Fine-tune vi…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "Phase 5  Error Correction (GER)
Second L…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 15', text "References: ROVER (Fiscus 1997)  |  GER …")

**Slide 61 — IS Improvement Roadmap — From 2.5 to 3.5**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "+0.13  |  Fixes: Accum (52) + Details (7…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "+0.53  |  Fixes: Halluc (108) + Wrong To…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 19', text "+0.98  |  Fixes: all remaining via data …")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 86% of smaller bbox (textA: "+0.98  |  Fixes: all remaining" / textB: "Conversion: ~0.033 IS per pp W")
- [OCCLUSION] Text shape 'TextBox 19' ("+0.98  |  Fixes: all remaining via data …") is 86% covered by later shape(s).

**Slide 64 — Phase 2: Exploit All 20 Hypotheses**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "Recognizer Output Voting Error Reduction…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "Minimum Bayes Risk Decoding…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 13', text "ROVER: Fiscus (1997), NIST  |  MBR Decod…")

**Slide 65 — Data Scaling: The Path to IS 3.5–4.0**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 10', text "Timelines assume realistic training: bug…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 11', text "LoRA Scaling: Biderman et al. (2024), IC…")

**Slide 68 — Stronger LLM + Smart Prompts = Force Multiplier**
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 12', text "GER: Chen et al. (2024), ICASSP  |  Scal…")

**Slide 72 — Arabic Pipeline: Replication Roadmap**
- [OCCLUSION] Text shape 'TextBox 8' ("• RTL text & normalization
• RTL handlin…") is 63% covered by later shape(s).

**Slide 77 — A1: Homophenes — The Lip-Reading Problem**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 9', text "A1…")

**Slide 79 — A4: LLM Salvage — Recoverable Segments**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "58% of salvageable have moderate WER (50…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "Categories overlap — segments can exhibi…")

**Slide 82 — A7: Video Gallery — All Example Segments**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 3', text "★ = video embedded on a slide   ─ = avai…")

### MINOR (193)

**Slide 2 — What was done? (1/2)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 3 — What was done? (2/2)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 4 — Executive Summary**
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 64% but notes only mention [25, 61] — possible mismatch.

**Slide 5 — WER: The Metric That Lies**
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 6 — Presentation Overview**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 7 — What is Visual Speech Processing?**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 10 numbers but lack any source reference (.md/.csv path).

**Slide 8 — The Invisible Problem: Visemes**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 9 — How It Works: Three Components**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 10 — How It Works: Data Flow**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 11 — The Benchmark: Paper vs Reality**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 12% of smaller bbox (textA: "11" / textB: "Note: Our best LRS3 reproducti")
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 12 — The Reality Gap**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 6 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 30% but notes only mention [20, 25, 34, 64] — possible mismatch.

**Slide 13 — Same WER, Different Effects**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 14 — RESEARCH FINDINGS**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 15 — LLM-as-a-Judge: Gold Standard (1,497 Pairs)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 17 numbers but lack any source reference (.md/.csv path).

**Slide 16 — LLM Judge: Deep Dive**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 9 numbers but lack any source reference (.md/.csv path).

**Slide 17 — Judge Example 1: Named Entity Swap**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 15% but notes only mention [18] — possible mismatch.

**Slide 18 — Judge Example 2: Truncated but Core Preserved**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 41% but notes only mention [48] — possible mismatch.

**Slide 19 — Judge Example 3: Technical Vocabulary Drift**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 20 — Judge Example 4: Scientific Vocabulary Lost**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 21 — Judge Example 5: Cooking Domain Confusion**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 43% but notes only mention [89] — possible mismatch.

**Slide 22 — Judge Example 6: Topic Hijack**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 23 — Why LLM as a Judge Is Not Enough**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 24 — IS Signals: Word Accuracy & Length**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 25 — IS Signals: Semantic Similarity**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 80% but notes only mention [25] — possible mismatch.

**Slide 26 — IS Signals: Phonetic & Named Entities**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 5 numbers but lack any source reference (.md/.csv path).

**Slide 27 — Do 6 Signals Actually Measure 6 Things?**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 8 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 87% but notes only mention [5, 19, 68, 93] — possible mismatch.

**Slide 28 — IS in Action: Two Real Segments**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 29 — Model Comparison: IS Profiles**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 14 numbers but lack any source reference (.md/.csv path).

**Slide 30 — The Gap: Where WER Lies Most**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 17 numbers but lack any source reference (.md/.csv path).

**Slide 31 — Intelligibility Score: 61.6% Useful Output**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 6 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 15% but notes only mention [25, 61] — possible mismatch.

**Slide 32 — Two Evaluation Systems, One Framework**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 11 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 12% but notes only mention [23, 61, 64] — possible mismatch.

**Slide 33 — IS: A Calibrated Surrogate Metric**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 5' overlap by 14% of smaller bbox (textA: "IS says 61.6%" / textB: "of segments deliver useful out")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 14% of smaller bbox (textA: "LLM Judge says 64.9%" / textB: "deliver useful output (Y + P)")
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 34 — Where IS and the Judge Disagree**
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 17% of smaller bbox (textA: "Paraphrases and phonetic bridg" / textB: "• Harmless hallucination (extr")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 17' overlap by 17% of smaller bbox (textA: "Structural match hides semanti" / textB: "• Domain confusion (medical → ")
- [NOTES] Notes cite 14 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 71% but notes only mention [0, 1, 100, 111] — possible mismatch.

**Slide 35 — Context Exposes Hidden Failures**
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 13' overlap by 28% of smaller bbox (textA: "More context false positives:" / textB: "Domain knowledge raises the ba")
- [NOTES] Notes cite 7 numbers but lack any source reference (.md/.csv path).

**Slide 36 — Three Numbers That Tell the Real Story**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 11 numbers but lack any source reference (.md/.csv path).

**Slide 37 — Failure Mode Taxonomy**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 8 numbers but lack any source reference (.md/.csv path).

**Slide 38 — Failure Mode Taxonomy (1/2): Highest Impact First**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 100% but notes only mention [13, 18, 44] — possible mismatch.

**Slide 39 — Failure Mode Taxonomy (2/2): Accumulated → Signal Loss**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 40 — Failure Modes: Real Examples**
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

**Slide 41 — IS Validation: What Did We Learn?**
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 44 — IS: A Calibrated Surrogate for LLM Judgment**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 5' overlap by 14% of smaller bbox (textA: "IS says 61.6%" / textB: "of segments pass (IS ≥ 2.00)")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 14% of smaller bbox (textA: "LLM Judge says 64.9%" / textB: "deliver useful output (Y + P)")
- [NOTES] Notes cite 5 numbers but lack any source reference (.md/.csv path).

**Slide 45 — LLM Salvage: Three Real Recoveries**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 10% of smaller bbox (textA: "Reference:" / textB: "“when jesus rose again”")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 10% of smaller bbox (textA: "Prediction:" / textB: "“in one sense it’s roseand ke")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 17' overlap by 10% of smaller bbox (textA: "Reference:" / textB: "“moving conceptual surface dat")
- [OVERLAP] Shapes 'TextBox 18' & 'TextBox 19' overlap by 10% of smaller bbox (textA: "Prediction:" / textB: "“moved the conceptual rulesov")
- [OVERLAP] Shapes 'TextBox 25' & 'TextBox 26' overlap by 10% of smaller bbox (textA: "Reference:" / textB: "“over the last 10 years we hav")
- [OVERLAP] Shapes 'TextBox 27' & 'TextBox 28' overlap by 10% of smaller bbox (textA: "Prediction:" / textB: "“over the last 10 years we hav")
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 150% but notes only mention [75] — possible mismatch.

**Slide 46 — LLM Salvage: Domain Context Fills the Gaps**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 10% of smaller bbox (textA: "Reference:" / textB: "“the fear of allah is complete")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 10% of smaller bbox (textA: "Prediction:" / textB: "“the fear of the loss complete")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 17' overlap by 10% of smaller bbox (textA: "Reference:" / textB: "“india china afghanistan allt")
- [OVERLAP] Shapes 'TextBox 18' & 'TextBox 19' overlap by 10% of smaller bbox (textA: "Prediction:" / textB: "“middle east and afghanistana")
- [OVERLAP] Shapes 'TextBox 25' & 'TextBox 26' overlap by 10% of smaller bbox (textA: "Reference:" / textB: "“i have a tablespoon ofjalape")
- [OVERLAP] Shapes 'TextBox 27' & 'TextBox 28' overlap by 10% of smaller bbox (textA: "Prediction:" / textB: "“i have a dietary smoothiei’v")
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 47 — Curated Examples — Video Gallery**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 48 — Demo: OK → Almost There → Hallucination**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 49 — ENGINEERING**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 50 — Starting Point: Three Research Codebases**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 51 — 8-Stage Automated Pipeline**
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 25% of smaller bbox (textA: "Whispertranscription" / textB: "evaluation only")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 54' overlap by 5% of smaller bbox (textA: "Whispertranscription" / textB: "Existed in academic repo")

**Slide 52 — 8-Stage Automated Pipeline**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [STRUCTURE] Adjacent duplicate title with slide 51 ('8-Stage Automated Pipeline') — possible leftover.

**Slide 53 — Building the Pipeline: The Engineering Journey**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 54 — Standalone Container — No Cloud Required**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 55 — Live Demo**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 56 — Pipeline Intelligence**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 5 numbers but lack any source reference (.md/.csv path).

**Slide 57 — Two Environments: Development and Production**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 58 — FUTURE DIRECTIONS**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 59 — Starting from 61.6%, Not 25%**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 7 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 41% but notes only mention [25, 61, 64, 85] — possible mismatch.

**Slide 60 — Five Phases — From IS 2.5 to Target IS 3.3–3.7**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Body shows 62% but notes only mention [8, 26, 85] — possible mismatch.

**Slide 61 — IS Improvement Roadmap — From 2.5 to 3.5**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 31 numbers but lack any source reference (.md/.csv path).

**Slide 62 — Phase 1: Confidence Scoring — Surface the Good 65%**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 65% but notes only mention [20, 60] — possible mismatch.

**Slide 63 — Confidence Scoring — Summary**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 13% but notes only mention [20, 60] — possible mismatch.

**Slide 64 — Phase 2: Exploit All 20 Hypotheses**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 65 — Data Scaling: The Path to IS 3.5–4.0**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 6 numbers but lack any source reference (.md/.csv path).

**Slide 66 — The Price Tag: What It Costs to Improve**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 16 numbers but lack any source reference (.md/.csv path).

**Slide 67 — Fine-Tuning: Limited Data, Limited Gains**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 9 numbers but lack any source reference (.md/.csv path).

**Slide 68 — Stronger LLM + Smart Prompts = Force Multiplier**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 5 numbers but lack any source reference (.md/.csv path).

**Slide 69 — The LLM Is a Context Engine**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 70 — LLM Upgrade: Why It Matters**
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 8% of smaller bbox (textA: "Current WER" / textB: "64%")
- [OVERLAP] Shapes 'TextBox 13' & 'TextBox 14' overlap by 8% of smaller bbox (textA: "LLM swap alone" / textB: "−3–8 pp")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 17' overlap by 8% of smaller bbox (textA: "+ Smart prompts" / textB: "−5–10 pp")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 8% of smaller bbox (textA: "+ 20K segments" / textB: "−10–15 pp")
- [OVERLAP] Shapes 'TextBox 22' & 'TextBox 23' overlap by 8% of smaller bbox (textA: "Target WER" / textB: "35–40%")
- [NOTES] Notes cite 32 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 64% but notes only mention [5, 18, 20, 25, 30, 35, 40, 44, 61] — possible mismatch.

**Slide 71 — Failure Modes: Impact & What Fixes Them**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 72 — Arabic Pipeline: Replication Roadmap**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 12' overlap by 28% of smaller bbox (textA: "• RTL text & normalization
• R" / textB: "Realistic estimate: 2–3 months")

**Slide 73 — AV-HuBERT: Why It’s Not Language-Locked**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 74 — Arabic Adaptation: What Changes**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 75 — Key Takeaways**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Body shows 61% but notes only mention [65] — possible mismatch.

**Slide 76 — Thank You**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 77 — A1: Homophenes — The Lip-Reading Problem**
- [LAYOUT] No slide-number label detected in bottom-left area (expected per add_slide_num convention).
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 78 — A3: IS Component Correlation**
- [LAYOUT] No slide-number label detected in bottom-left area (expected per add_slide_num convention).
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 5' overlap by 13% of smaller bbox (textA: "PCA: 6 IS signals collapse int" / textB: "Cross-Config Stability (16 con")
- [NOTES] Notes cite 6 numbers but lack any source reference (.md/.csv path).

**Slide 79 — A4: LLM Salvage — Recoverable Segments**
- [LAYOUT] No slide-number label detected in bottom-left area (expected per add_slide_num convention).
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 6 numbers but lack any source reference (.md/.csv path).

**Slide 81 — A6: Failure Mode Examples**
- [LAYOUT] No slide-number label detected in bottom-left area (expected per add_slide_num convention).
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 82 — A7: Video Gallery — All Example Segments**
- [LAYOUT] No slide-number label detected in bottom-left area (expected per add_slide_num convention).
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 83 — A8: LLM Judge × IS Tier Cross-Tabulation**
- [LAYOUT] No slide-number label detected in bottom-left area (expected per add_slide_num convention).
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 10 numbers but lack any source reference (.md/.csv path).

**Slide 84 — A9: Context Evaluation — Transition Details**
- [LAYOUT] No slide-number label detected in bottom-left area (expected per add_slide_num convention).
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 40% but notes only mention [80] — possible mismatch.


## Argos_VSP_Client_v9_May2026.pptx

### BLOCKER: none

### MAJOR (195)

**Slide 2 — Argos**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "Argos / The Orchard.…")

**Slide 3 — What is visual speech recognition?**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 18', text "We've shipped this end-to-end. The next …")

**Slide 7 — Compared to today**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 4', text "APPROACH…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "WORD ACCURACY…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "TIME PER HOUR…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "HALLUCINATION RISK…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 23', text "Word accuracy figures from published lip…")

**Slide 8 — Why even expert humans cap at 45–52%**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 13', text "Range from trained-human lip-reading stu…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 14', text "The model adds language priors and domai…")

**Slide 9 — What we built — concretely**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 22', text "Deployable today. Domain-specific upgrad…")

**Slide 12 — Live UI Demo**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "If video does not embed before the meeti…")

**Slide 14 — Three numbers, in plain English**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "Measured on 1,497 segments of unfiltered…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 16', text "Validated against an independent blind e…")

**Slide 15 — Example 1 — Trust: clean speech (Obama)**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 5', text "Click to play in PowerPoint…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "REFERENCE…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "HYPOTHESIS…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "Confidence: high…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 13', text "BLUE: trust   ORANGE: review   PURPLE: a…")

**Slide 16 — Example 2 — Real conversations: all three outcomes**
- [STYLE] Body font 7pt below 12pt readability floor (shape 'TextBox 8', text "▶  click to play in PowerPoint…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 9', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 10', text "in the united states i just think that y…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 11', text "HYPOTHESIS…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "in the united states i just think that y…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 13', text "Reference = hypothesis, word for word. R…")
- [STYLE] Body font 7pt below 12pt readability floor (shape 'TextBox 18', text "▶  click to play in PowerPoint…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 19', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 20', text "that's god too and you're the one that i…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 21', text "HYPOTHESIS…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 22', text "that's god too when you're the one that …")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 23', text "Two minor swaps (and→when, faith→cradle)…")
- [STYLE] Body font 7pt below 12pt readability floor (shape 'TextBox 28', text "▶  click to play in PowerPoint…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 29', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 30', text "you'd buy something and say thanks marty…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 31', text "HYPOTHESIS…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 32', text "when he died my daughter's tutor said to…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 33', text "Strip tier — coloring removed by policy.…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 34', text "Source: RealTalk conversational dataset.…")
- [OVERLAP] Shapes 'TextBox 34' & 'TextBox 36' overlap by 88% of smaller bbox (textA: "Source: RealTalk conversationa" / textB: "16")
- [VIDEO] Embedded media (media2.mp4, 717081 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media2.mp4, 717081 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media3.mp4, 695397 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media3.mp4, 695397 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media4.mp4, 844449 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media4.mp4, 844449 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.

**Slide 20 — Per-word color coding on a real example**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 3', text "The actual report. Per-word coloring is …")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "Per-word confidence  —…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "BLUE: trust — confident AND alternatives…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "ORANGE: review — some signal…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "PURPLE: avoid · numbers cap at orange…")

**Slide 21 — How the report handles uncertainty**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "overall confidence  ≥  82%…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "9 out of 10 blue words are correct…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "(measured 85–93% across this tier)…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 11', text "of segments…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 14', text "overall confidence  65 – 82%…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 16', text "7 out of 10 blue words are correct…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 17', text "verify names, numbers, dates against vid…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 19', text "of segments…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 22', text "overall confidence  <  65%…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 24', text "Fewer than half would be right…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 25', text "coloring would mislead — so we hide it…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 27', text "of segments…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 28', text "Measured on 23,261 words from 1,427 segm…")
- [OVERLAP] Shapes 'TextBox 28' & 'TextBox 30' overlap by 72% of smaller bbox (textA: "Measured on 23,261 words from " / textB: "21")

**Slide 22 — How a reviewer actually reads the output**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 18', text "A detailed reviewer guide ships with eve…")
- [OVERLAP] Shapes 'TextBox 18' & 'TextBox 20' overlap by 72% of smaller bbox (textA: "A detailed reviewer guide ship" / textB: "22")

**Slide 23 — Example 3 — Trust: gallery of six clean outputs**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 6', text "Conversational…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text ""I'm always open to new ideas and new th…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 10', text "Legal…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text ""It enabled me to find my voice in the c…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 14', text "Public address…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text ""Next week I will be making my debut"…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 18', text "Technology…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 19', text ""To this wave of artificial intelligence…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 22', text "Motivational…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 23', text ""You've got to get back up again because…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 26', text "Historical speech (Obama, seg 19)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 27', text ""Office, I directed Leon Panetta, the di…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 28', text "All six clean — reference equals hypothe…")

**Slide 24 — Example 4 — Salvage: partial recovery (Obama)**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 5', text "Click to play in PowerPoint…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "REFERENCE…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "HYPOTHESIS…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "Confidence: mixed…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 13', text "BLUE: trust   ORANGE: review   PURPLE: a…")

**Slide 25 — Example 5 — Salvage: named-entity swap**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Names move. Meaning holds. The" / textB: "25")

**Slide 26 — Example 6 — Salvage: technical-vocabulary drift**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Structure carries the meaning." / textB: "26")

**Slide 27 — Example 7 — Strip-flag: topic hijack**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "The dangerous mode: fluent pro" / textB: "27")

**Slide 28 — Example 8 — Salvage: reading the colors (walk-through)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "Banner shown to the reviewer: "Reading c…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "REFERENCE…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "HYPOTHESIS…")

**Slide 29 — Example 9 — Strip: topic invented**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "we're going to look at now is what happe…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "Without colors, the wrong topic enters r…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: good   ORANGE: mid   PURPLE: bad…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Without colors, the wrong topi" / textB: "29")

**Slide 30 — Example 10 — Strip: fluent fabrication caught**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS (Strip tier — coloring remove…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Without Strip, a fabricated qu" / textB: "30")

**Slide 31 — Example 11 — Strip: hallucination flagged (Obama)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "WHAT THE SPEAKER ACTUALLY SAID…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "WHAT THE MODEL DECODED…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "WHAT THE SYSTEM DID…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 11', text "LOW CONFIDENCE…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "Lowest-confidence word at probability 0.…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 13', text "AUTO-EXCLUDED…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 14', text "Segment classified Strip — dropped from …")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 15', text "YOU NEVER SAW THIS…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 16', text "Reviewer queue skipped this segment. The…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 18', text "▶  Obama segment 5 — click to play…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 20', text "BLUE: trust   ORANGE: review   PURPLE: a…")

**Slide 33 — Why trust it on a video you've never seen**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "PER-WORD…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "PER-SEGMENT…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "WILD VIDEOS…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "MEANINGFUL TODAY…")

**Slide 34 — How aggressive should your trust threshold be**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "630 of 1,497 baseline…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 14', text "the meaning came through…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 18', text "trusted output that wasn't useful…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 22', text "Reviewer can ignore individual low-confi…")

**Slide 36 — How we validated the trust signals**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "The runtime confidence signal — the per-…")

**Slide 37 — Agrees with the blind evaluator 82% of the time**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "DISAGREES…")

**Slide 38 — Why the trust signal is stable across conditions**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Tested across 16 different decode config…")

**Slide 40 — How It Works: Data Flow**
- [OCCLUSION] Text shape 'TextBox 7' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 17' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 22' ("↓…") is 33% covered by later shape(s).

**Slide 41 — What it actually took — four passes, six months**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 24', text "Every problem solved is documented. Ever…")
- [OVERLAP] Shapes 'TextBox 24' & 'TextBox 26' overlap by 52% of smaller bbox (textA: "Every problem solved is docume" / textB: "41")

**Slide 44 — Multi-speaker — engineering work, in flight**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "one centered crop…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 19', text "two speakers → two crops…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 20', text "Engineering work, not a research bet. Pa…")

**Slide 45 — Arabic — real engineering work, mapped end-to-end**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "the longest phase…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "retrain on Arabic mouths…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 17', text "fine-tune on Arabic text…")

**Slide 46 — Optional add-on — pre-filter low-quality clips before decode**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 4', text "Each row = clips remaining after that ga…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 11', text "10 of 100 rejected — face too profile…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "viseme accuracy drops past 30°…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 16', text "8 of 100 rejected — mouth occluded…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 17', text "lower face must be unoccluded…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 21', text "7 of 100 rejected — too dark / washed ou…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 22', text "lip-region contrast within range  →  REA…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 24', text "Three frame-level CV checks, all running…")

**Slide 47 — Optional — domain-specific training run on your data**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 6', text "TODAY…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 8', text "PATH…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "TODAY…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 14', text "PATH…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 18', text "Today's 65% review-useful is real and de…")
- [OVERLAP] Shapes 'TextBox 18' & 'TextBox 20' overlap by 72% of smaller bbox (textA: "Today's 65% review-useful is r" / textB: "47")

**Slide 48 — How a domain-tuned version comes together**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 15', text "A pilot's worth of analyst-hours, end-to…")

**Slide 52 — Appendix Example A — Salvage: truncation, core preserved**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Edges lost, core preserved. Th" / textB: "52")

**Slide 53 — Appendix Example B — Salvage: scientific vocabulary lost**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Pattern survives. Scientific w" / textB: "53")

**Slide 54 — Appendix Example C — Salvage: ingredient confusion (cooking)**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Domain right. Ingredient wrong" / textB: "54")

**Slide 56 — Appendix Example E — Strip: hallucination duplicate (Obama)**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 5', text "Click to play in PowerPoint…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "REFERENCE…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [NOTES] Body slide has no speaker notes (academic talk requires 1-2 sentences min).

**Slide 57 — 65% useful — on real-world video, not benchmark data**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "On segments the system flags as high-con…")

**Slide 58 — Five failure modes, all detected**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 24', text "Frequencies on the 574 segments the syst…")

**Slide 59 — When the model fabricates, the system flags it**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Detection combines length-anomaly rules …")

**Slide 61 — The full pipeline — 8 automated stages**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 4', text "Whisper ASR runs as a side-branch for ev…")

**Slide 63 — Appendix Example F — Trust/Salvage/Strip spread (six playable tiles)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 3', text "Quality spread across the dataset — not …")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "PERFECT…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 8', text "Clean visual, clean output…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "ALMOST PERFECT…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "Near-verbatim transcription…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "PARTIAL…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 16', text "Right gist, wrong specifics…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 19', text "NEAR MISS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 20', text "Off by a phrase, recoverable with contex…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 23', text "HALLUCINATION…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 24', text "Fluent but wrong — auto-flagged…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 27', text "TOPIC DRIFT…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 28', text "Model lost the thread, system flags it…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 29', text "These six are a deliberate spread — best…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 30', text "Examples are illustrative. Headline numb…")
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 4' overlap by 75% of smaller bbox (textA: "Quality spread across the data" / textB: "Six real segments decoded by t")
- [OCCLUSION] Text shape 'TextBox 3' ("Quality spread across the dataset — not …") is 75% covered by later shape(s).

### MINOR (167)

**Slide 2 — Argos**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 3 — What is visual speech recognition?**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [ANIMATION] Multi-card layout (4 large shapes) but no click animations defined — cards appear all at once.

**Slide 4 — Three components, end-to-end**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 5 — What this is NOT**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 6 — What the system is built for**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 7 — Compared to today**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 8 — Why even expert humans cap at 45–52%**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 14' & 'TextBox 16' overlap by 12% of smaller bbox (textA: "The model adds language priors" / textB: "8")
- [NOTES] Notes cite 6 numbers but lack any source reference (.md/.csv path).

**Slide 9 — What we built — concretely**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 10 — Deploys where you need it**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 11 — Watch the system process a real video**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 12 — Live UI Demo**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 13 — REAL OUTPUTS**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 14 — Three numbers, in plain English**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 15' & 'TextBox 16' overlap by 12% of smaller bbox (textA: "Measured on 1,497 segments of " / textB: "Validated against an independe")
- [NOTES] Notes cite 26 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 65% but notes only mention [20, 23, 24, 37, 38, 68, 71, 85] — possible mismatch.

**Slide 15 — Example 1 — Trust: clean speech (Obama)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 16 — Example 2 — Real conversations: all three outcomes**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 17 — WHY YOU CAN TRUST IT**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 18 — How do you know when to trust an output?**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 19 — Two layers of confidence**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 20 — Per-word color coding on a real example**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.
- [NOTES] Notes cite 9 numbers but lack any source reference (.md/.csv path).

**Slide 21 — How the report handles uncertainty**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 14% of smaller bbox (textA: "(measured 85–93% across this t" / textB: "24%")
- [OVERLAP] Shapes 'TextBox 17' & 'TextBox 18' overlap by 14% of smaller bbox (textA: "verify names, numbers, dates a" / textB: "38%")
- [OVERLAP] Shapes 'TextBox 25' & 'TextBox 26' overlap by 14% of smaller bbox (textA: "coloring would mislead — so we" / textB: "39%")
- [NOTES] Body shows 24% but notes only mention [15, 18, 21, 38, 41, 50, 65, 69, 83, 85, 92, 93] — possible mismatch.

**Slide 22 — How a reviewer actually reads the output**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 23 — Example 3 — Trust: gallery of six clean outputs**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [ANIMATION] Multi-card layout (6 large shapes) but no click animations defined — cards appear all at once.
- [NOTES] Body shows 24% but notes only mention [0] — possible mismatch.

**Slide 24 — Example 4 — Salvage: partial recovery (Obama)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 25 — Example 5 — Salvage: named-entity swap**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "market research firm bernreute")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "market research firm rogers re")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "25")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 26 — Example 6 — Salvage: technical-vocabulary drift**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "we need a radically different ")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "we need a radically different ")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "26")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 27 — Example 7 — Strip-flag: topic hijack**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "i actually use the overhead li")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "i actually used the overheard ")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "27")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.

**Slide 28 — Example 8 — Salvage: reading the colors (walk-through)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 29 — Example 9 — Strip: topic invented**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.32, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 20% of smaller bbox (textA: "we're going to look at now is " / textB: "Without colors, the wrong topi")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 20% of smaller bbox (textA: "BLUE: good   ORANGE: mid   PUR" / textB: "29")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.

**Slide 30 — Example 10 — Strip: fluent fabrication caught**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: ""china to take off to cross th")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS (Strip tier — color" / textB: ""i don't think that's a good i")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "30")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.
- [NOTES] Body shows 25% but notes only mention [100] — possible mismatch.

**Slide 31 — Example 11 — Strip: hallucination flagged (Obama)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 32 — What we claim — and what we do not claim**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 33 — Why trust it on a video you've never seen**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 15' & 'TextBox 16' overlap by 7% of smaller bbox (textA: "MEANINGFUL TODAY" / textB: "The runtime signal is anchored")
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 34 — How aggressive should your trust threshold be**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Body shows 42% but notes only mention [0, 1, 5, 7, 8, 30, 33, 34, 35, 50, 52, 65, 70, 72, 88, 95, 97, 98] — possible mismatch.

**Slide 35 — VALIDATION**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 36 — How we validated the trust signals**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 37 — Agrees with the blind evaluator 82% of the time**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 13 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 18% but notes only mention [65, 82, 85, 95, 100] — possible mismatch.

**Slide 38 — Why the trust signal is stable across conditions**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 8 numbers but lack any source reference (.md/.csv path).

**Slide 39 — ENGINEERING UNDER THE HOOD**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 40 — How It Works: Data Flow**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 41 — What it actually took — four passes, six months**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 5% of smaller bbox (textA: "Research integration — three o" / textB: "auto_avsr + av_hubert + VSP-LL")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 13' overlap by 5% of smaller bbox (textA: "Production refactor — monolith" / textB: "823-line script → 11 modules +")
- [OVERLAP] Shapes 'TextBox 17' & 'TextBox 18' overlap by 5% of smaller bbox (textA: "Confidence layer — per-word an" / textB: "Token-level softmax extracted ")
- [OVERLAP] Shapes 'TextBox 22' & 'TextBox 23' overlap by 5% of smaller bbox (textA: "Beam-aggregation pipeline buil" / textB: "Beam-aggregation pipeline buil")

**Slide 42 — WHAT'S NEXT**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 43 — Step one — pilot on your videos**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 44 — Multi-speaker — engineering work, in flight**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 6' overlap by 10% of smaller bbox (textA: "TODAY" / textB: "Single-speaker mode")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 12' overlap by 10% of smaller bbox (textA: "PATH" / textB: "Entity-split preprocessing")

**Slide 45 — Arabic — real engineering work, mapped end-to-end**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 46 — Optional add-on — pre-filter low-quality clips before decode**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 12' overlap by 10% of smaller bbox (textA: "10 of 100 rejected — face too " / textB: "viseme accuracy drops past 30°")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 17' overlap by 10% of smaller bbox (textA: "8 of 100 rejected — mouth occl" / textB: "lower face must be unoccluded")
- [OVERLAP] Shapes 'TextBox 21' & 'TextBox 22' overlap by 10% of smaller bbox (textA: "7 of 100 rejected — too dark /" / textB: "lip-region contrast within ran")
- [NOTES] Notes cite 16 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 100% but notes only mention [70, 82] — possible mismatch.

**Slide 47 — Optional — domain-specific training run on your data**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.
- [NOTES] Body shows 65% but notes only mention [60, 62, 95] — possible mismatch.

**Slide 48 — How a domain-tuned version comes together**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 49 — Going to production — the partnership**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 50 — Thank You**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 11 numbers but lack any source reference (.md/.csv path).

**Slide 51 — What you just saw**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 52 — Appendix Example A — Salvage: truncation, core preserved**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "as this new home video market ")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "in the 1980s when film compani")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "52")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 53 — Appendix Example B — Salvage: scientific vocabulary lost**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "couples us to light cycles in ")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "takes into account our environ")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "53")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 54 — Appendix Example C — Salvage: ingredient confusion (cooking)**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "and i have a tablespoon of jal")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "and i have a dietary smoothie ")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "54")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.

**Slide 55 — Appendix Example D — Strip: dangerous-failure setup**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 56 — Appendix Example E — Strip: hallucination duplicate (Obama)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 57 — 65% useful — on real-world video, not benchmark data**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 5 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 65% but notes only mention [38, 39, 61, 62] — possible mismatch.

**Slide 58 — Five failure modes, all detected**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 44% but notes only mention [9] — possible mismatch.

**Slide 59 — When the model fabricates, the system flags it**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 60 — What this means for your workflow**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 61 — The full pipeline — 8 automated stages**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 6' overlap by 12% of smaller bbox (textA: "Whisper ASR runs as a side-bra" / textB: "61")
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 62 — Three things to take with you**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 63 — Appendix Example F — Trust/Salvage/Strip spread (six playable tiles)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 15% of smaller bbox (textA: "PERFECT" / textB: "Clean visual, clean output")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 12' overlap by 15% of smaller bbox (textA: "ALMOST PERFECT" / textB: "Near-verbatim transcription")
- [OVERLAP] Shapes 'TextBox 15' & 'TextBox 16' overlap by 15% of smaller bbox (textA: "PARTIAL" / textB: "Right gist, wrong specifics")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 15% of smaller bbox (textA: "NEAR MISS" / textB: "Off by a phrase, recoverable w")
- [OVERLAP] Shapes 'TextBox 23' & 'TextBox 24' overlap by 15% of smaller bbox (textA: "HALLUCINATION" / textB: "Fluent but wrong — auto-flagge")
- [OVERLAP] Shapes 'TextBox 27' & 'TextBox 28' overlap by 15% of smaller bbox (textA: "TOPIC DRIFT" / textB: "Model lost the thread, system ")

**Slide 64 — 8-Stage Automated Pipeline (appendix)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.


## Argos_VSP_Client_v10_May2026.pptx

### BLOCKER: none

### MAJOR (195)

**Slide 2 — Argos**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "Argos / The Orchard.…")

**Slide 3 — What is visual speech recognition?**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 18', text "We've shipped this end-to-end. The next …")

**Slide 7 — Compared to today**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 4', text "APPROACH…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "WORD ACCURACY…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "TIME PER HOUR…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "HALLUCINATION RISK…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 23', text "Word accuracy figures from published lip…")

**Slide 8 — Why even expert humans cap at 45–52%**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 13', text "Range from trained-human lip-reading stu…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 14', text "The model adds language priors and domai…")

**Slide 9 — What we built — concretely**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 22', text "Deployable today. Domain-specific upgrad…")

**Slide 12 — Live UI Demo**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "If video does not embed before the meeti…")

**Slide 14 — Three numbers, in plain English**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "Measured on 1,497 segments of unfiltered…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 16', text "Validated against an independent blind e…")

**Slide 15 — Example 1 — Trust: clean speech (Obama)**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 5', text "Click to play in PowerPoint…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "REFERENCE…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "HYPOTHESIS…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "Confidence: high…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 13', text "BLUE: trust   ORANGE: review   PURPLE: a…")

**Slide 16 — Example 2 — Real conversations: all three outcomes**
- [STYLE] Body font 7pt below 12pt readability floor (shape 'TextBox 8', text "▶  click to play in PowerPoint…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 9', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 10', text "in the united states i just think that y…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 11', text "HYPOTHESIS…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "in the united states i just think that y…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 13', text "Reference = hypothesis, word for word. R…")
- [STYLE] Body font 7pt below 12pt readability floor (shape 'TextBox 18', text "▶  click to play in PowerPoint…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 19', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 20', text "that's god too and you're the one that i…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 21', text "HYPOTHESIS…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 22', text "that's god too when you're the one that …")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 23', text "Two minor swaps (and→when, faith→cradle)…")
- [STYLE] Body font 7pt below 12pt readability floor (shape 'TextBox 28', text "▶  click to play in PowerPoint…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 29', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 30', text "you'd buy something and say thanks marty…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 31', text "HYPOTHESIS…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 32', text "when he died my daughter's tutor said to…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 33', text "Strip tier — coloring removed by policy.…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 34', text "Source: RealTalk conversational dataset.…")
- [OVERLAP] Shapes 'TextBox 34' & 'TextBox 36' overlap by 88% of smaller bbox (textA: "Source: RealTalk conversationa" / textB: "16")
- [VIDEO] Embedded media (media2.mp4, 717081 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media2.mp4, 717081 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media3.mp4, 695397 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media3.mp4, 695397 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media4.mp4, 844449 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.
- [VIDEO] Embedded media (media4.mp4, 844449 bytes) does not match any file in 06_demo_videos/ by size — likely orphaned or renamed source.

**Slide 20 — Per-word color coding on a real example**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 3', text "The actual report. Per-word coloring is …")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "Per-word confidence  —…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "BLUE: trust — confident AND alternatives…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "ORANGE: review — some signal…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "PURPLE: avoid · numbers cap at orange…")

**Slide 21 — How the report handles uncertainty**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "overall confidence  ≥  82%…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "9 out of 10 blue words are correct…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "(measured 85–93% across this tier)…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 11', text "of segments…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 14', text "overall confidence  65 – 82%…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 16', text "7 out of 10 blue words are correct…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 17', text "verify names, numbers, dates against vid…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 19', text "of segments…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 22', text "overall confidence  <  65%…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 24', text "Fewer than half would be right…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 25', text "coloring would mislead — so we hide it…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 27', text "of segments…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 28', text "Measured on 23,261 words from 1,427 segm…")
- [OVERLAP] Shapes 'TextBox 28' & 'TextBox 30' overlap by 72% of smaller bbox (textA: "Measured on 23,261 words from " / textB: "21")

**Slide 22 — How a reviewer actually reads the output**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 18', text "A detailed reviewer guide ships with eve…")
- [OVERLAP] Shapes 'TextBox 18' & 'TextBox 20' overlap by 72% of smaller bbox (textA: "A detailed reviewer guide ship" / textB: "22")

**Slide 23 — Example 3 — Trust: gallery of six clean outputs**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 6', text "Conversational…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text ""I'm always open to new ideas and new th…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 10', text "Legal…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text ""It enabled me to find my voice in the c…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 14', text "Public address…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text ""Next week I will be making my debut"…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 18', text "Technology…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 19', text ""To this wave of artificial intelligence…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 22', text "Motivational…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 23', text ""You've got to get back up again because…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 26', text "Historical speech (Obama, seg 19)…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 27', text ""Office, I directed Leon Panetta, the di…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 28', text "All six clean — reference equals hypothe…")

**Slide 24 — Example 4 — Salvage: partial recovery (Obama)**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 5', text "Click to play in PowerPoint…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "REFERENCE…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "HYPOTHESIS…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "Confidence: mixed…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 13', text "BLUE: trust   ORANGE: review   PURPLE: a…")

**Slide 25 — Example 5 — Salvage: named-entity swap**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Names move. Meaning holds. The" / textB: "25")

**Slide 26 — Example 6 — Salvage: technical-vocabulary drift**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Structure carries the meaning." / textB: "26")

**Slide 27 — Example 7 — Strip-flag: topic hijack**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "The dangerous mode: fluent pro" / textB: "27")

**Slide 28 — Example 8 — Salvage: reading the colors (walk-through)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "Banner shown to the reviewer: "Reading c…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "REFERENCE…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "HYPOTHESIS…")

**Slide 29 — Example 9 — Strip: topic invented**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "we're going to look at now is what happe…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "Without colors, the wrong topic enters r…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: good   ORANGE: mid   PURPLE: bad…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Without colors, the wrong topi" / textB: "29")

**Slide 30 — Example 10 — Strip: fluent fabrication caught**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS (Strip tier — coloring remove…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Without Strip, a fabricated qu" / textB: "30")

**Slide 31 — Example 11 — Strip: hallucination flagged (Obama)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "WHAT THE SPEAKER ACTUALLY SAID…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "WHAT THE MODEL DECODED…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "WHAT THE SYSTEM DID…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 11', text "LOW CONFIDENCE…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "Lowest-confidence word at probability 0.…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 13', text "AUTO-EXCLUDED…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 14', text "Segment classified Strip — dropped from …")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 15', text "YOU NEVER SAW THIS…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 16', text "Reviewer queue skipped this segment. The…")
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 18', text "▶  Obama segment 5 — click to play…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 20', text "BLUE: trust   ORANGE: review   PURPLE: a…")

**Slide 33 — Why trust it on a video you've never seen**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "PER-WORD…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "PER-SEGMENT…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "WILD VIDEOS…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "MEANINGFUL TODAY…")

**Slide 34 — How aggressive should your trust threshold be**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "630 of 1,497 baseline…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 14', text "the meaning came through…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 18', text "trusted output that wasn't useful…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 22', text "Reviewer can ignore individual low-confi…")

**Slide 36 — How we validated the trust signals**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 5', text "The runtime confidence signal — the per-…")

**Slide 37 — Agrees with the blind evaluator 82% of the time**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "DISAGREES…")

**Slide 38 — Why the trust signal is stable across conditions**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 5', text "Tested across 16 different decode config…")

**Slide 40 — How It Works: Data Flow**
- [OCCLUSION] Text shape 'TextBox 7' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 17' ("↓…") is 33% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 22' ("↓…") is 33% covered by later shape(s).

**Slide 41 — What it actually took — four passes, six months**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 24', text "Every problem solved is documented. Ever…")
- [OVERLAP] Shapes 'TextBox 24' & 'TextBox 26' overlap by 52% of smaller bbox (textA: "Every problem solved is docume" / textB: "41")

**Slide 44 — Multi-speaker — engineering work, in flight**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 9', text "one centered crop…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 19', text "two speakers → two crops…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 20', text "Engineering work, not a research bet. Pa…")

**Slide 45 — Arabic — real engineering work, mapped end-to-end**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "the longest phase…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 12', text "retrain on Arabic mouths…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 17', text "fine-tune on Arabic text…")

**Slide 46 — Optional add-on — pre-filter low-quality clips before decode**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 4', text "Each row = clips remaining after that ga…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 11', text "10 of 100 rejected — face too profile…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "viseme accuracy drops past 30°…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 16', text "8 of 100 rejected — mouth occluded…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 17', text "lower face must be unoccluded…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 21', text "7 of 100 rejected — too dark / washed ou…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 22', text "lip-region contrast within range  →  REA…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 24', text "Three frame-level CV checks, all running…")

**Slide 47 — Optional — domain-specific training run on your data**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 6', text "TODAY…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 8', text "PATH…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 12', text "TODAY…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 14', text "PATH…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 18', text "Today's 65% review-useful is real and de…")
- [OVERLAP] Shapes 'TextBox 18' & 'TextBox 20' overlap by 72% of smaller bbox (textA: "Today's 65% review-useful is r" / textB: "47")

**Slide 48 — How a domain-tuned version comes together**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 15', text "A pilot's worth of analyst-hours, end-to…")

**Slide 52 — Appendix Example A — Salvage: truncation, core preserved**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Edges lost, core preserved. Th" / textB: "52")

**Slide 53 — Appendix Example B — Salvage: scientific vocabulary lost**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Pattern survives. Scientific w" / textB: "53")

**Slide 54 — Appendix Example C — Salvage: ingredient confusion (cooking)**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "REFERENCE…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 9', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 72% of smaller bbox (textA: "Domain right. Ingredient wrong" / textB: "54")

**Slide 56 — Appendix Example E — Strip: hallucination duplicate (Obama)**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 5', text "Click to play in PowerPoint…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 6', text "REFERENCE…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 8', text "HYPOTHESIS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "BLUE: trust   ORANGE: review   PURPLE: a…")
- [NOTES] Body slide has no speaker notes (academic talk requires 1-2 sentences min).

**Slide 57 — 65% useful — on real-world video, not benchmark data**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 10', text "On segments the system flags as high-con…")

**Slide 58 — Five failure modes, all detected**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 24', text "Frequencies on the 574 segments the syst…")

**Slide 59 — When the model fabricates, the system flags it**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "Detection combines length-anomaly rules …")

**Slide 61 — The full pipeline — 8 automated stages**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 4', text "Whisper ASR runs as a side-branch for ev…")

**Slide 63 — Appendix Example F — Trust/Salvage/Strip spread (six playable tiles)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 3', text "Quality spread across the dataset — not …")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 7', text "PERFECT…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 8', text "Clean visual, clean output…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "ALMOST PERFECT…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 12', text "Near-verbatim transcription…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "PARTIAL…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 16', text "Right gist, wrong specifics…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 19', text "NEAR MISS…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 20', text "Off by a phrase, recoverable with contex…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 23', text "HALLUCINATION…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 24', text "Fluent but wrong — auto-flagged…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 27', text "TOPIC DRIFT…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 28', text "Model lost the thread, system flags it…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 29', text "These six are a deliberate spread — best…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 30', text "Examples are illustrative. Headline numb…")
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 4' overlap by 75% of smaller bbox (textA: "Quality spread across the data" / textB: "Six real segments decoded by t")
- [OCCLUSION] Text shape 'TextBox 3' ("Quality spread across the dataset — not …") is 75% covered by later shape(s).

### MINOR (167)

**Slide 2 — Argos**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 3 — What is visual speech recognition?**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [ANIMATION] Multi-card layout (4 large shapes) but no click animations defined — cards appear all at once.

**Slide 4 — Three components, end-to-end**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 5 — What this is NOT**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 6 — What the system is built for**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 7 — Compared to today**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 8 — Why even expert humans cap at 45–52%**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 14' & 'TextBox 16' overlap by 12% of smaller bbox (textA: "The model adds language priors" / textB: "8")
- [NOTES] Notes cite 6 numbers but lack any source reference (.md/.csv path).

**Slide 9 — What we built — concretely**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 10 — Deploys where you need it**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 11 — Watch the system process a real video**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 12 — Live UI Demo**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 13 — REAL OUTPUTS**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 14 — Three numbers, in plain English**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 15' & 'TextBox 16' overlap by 12% of smaller bbox (textA: "Measured on 1,497 segments of " / textB: "Validated against an independe")
- [NOTES] Notes cite 26 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 65% but notes only mention [20, 23, 24, 37, 38, 68, 71, 85] — possible mismatch.

**Slide 15 — Example 1 — Trust: clean speech (Obama)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 16 — Example 2 — Real conversations: all three outcomes**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 17 — WHY YOU CAN TRUST IT**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 18 — How do you know when to trust an output?**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 19 — Two layers of confidence**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 20 — Per-word color coding on a real example**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.
- [NOTES] Notes cite 9 numbers but lack any source reference (.md/.csv path).

**Slide 21 — How the report handles uncertainty**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 14% of smaller bbox (textA: "(measured 85–93% across this t" / textB: "24%")
- [OVERLAP] Shapes 'TextBox 17' & 'TextBox 18' overlap by 14% of smaller bbox (textA: "verify names, numbers, dates a" / textB: "38%")
- [OVERLAP] Shapes 'TextBox 25' & 'TextBox 26' overlap by 14% of smaller bbox (textA: "coloring would mislead — so we" / textB: "39%")
- [NOTES] Body shows 24% but notes only mention [15, 18, 21, 38, 41, 50, 65, 69, 83, 85, 92, 93] — possible mismatch.

**Slide 22 — How a reviewer actually reads the output**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 23 — Example 3 — Trust: gallery of six clean outputs**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [ANIMATION] Multi-card layout (6 large shapes) but no click animations defined — cards appear all at once.
- [NOTES] Body shows 24% but notes only mention [0] — possible mismatch.

**Slide 24 — Example 4 — Salvage: partial recovery (Obama)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 25 — Example 5 — Salvage: named-entity swap**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "market research firm bernreute")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "market research firm rogers re")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "25")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 26 — Example 6 — Salvage: technical-vocabulary drift**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "we need a radically different ")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "we need a radically different ")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "26")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 27 — Example 7 — Strip-flag: topic hijack**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "i actually use the overhead li")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "i actually used the overheard ")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "27")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.

**Slide 28 — Example 8 — Salvage: reading the colors (walk-through)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 29 — Example 9 — Strip: topic invented**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.32, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 20% of smaller bbox (textA: "we're going to look at now is " / textB: "Without colors, the wrong topi")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 20% of smaller bbox (textA: "BLUE: good   ORANGE: mid   PUR" / textB: "29")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.

**Slide 30 — Example 10 — Strip: fluent fabrication caught**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: ""china to take off to cross th")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS (Strip tier — color" / textB: ""i don't think that's a good i")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "30")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.
- [NOTES] Body shows 25% but notes only mention [100] — possible mismatch.

**Slide 31 — Example 11 — Strip: hallucination flagged (Obama)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 32 — What we claim — and what we do not claim**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 33 — Why trust it on a video you've never seen**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 15' & 'TextBox 16' overlap by 7% of smaller bbox (textA: "MEANINGFUL TODAY" / textB: "The runtime signal is anchored")
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 34 — How aggressive should your trust threshold be**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Body shows 42% but notes only mention [0, 1, 5, 7, 8, 30, 33, 34, 35, 50, 52, 65, 70, 72, 88, 95, 97, 98] — possible mismatch.

**Slide 35 — VALIDATION**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 36 — How we validated the trust signals**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 37 — Agrees with the blind evaluator 82% of the time**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 13 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 18% but notes only mention [65, 82, 85, 95, 100] — possible mismatch.

**Slide 38 — Why the trust signal is stable across conditions**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 8 numbers but lack any source reference (.md/.csv path).

**Slide 39 — ENGINEERING UNDER THE HOOD**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 40 — How It Works: Data Flow**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 41 — What it actually took — four passes, six months**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 5% of smaller bbox (textA: "Research integration — three o" / textB: "auto_avsr + av_hubert + VSP-LL")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 13' overlap by 5% of smaller bbox (textA: "Production refactor — monolith" / textB: "823-line script → 11 modules +")
- [OVERLAP] Shapes 'TextBox 17' & 'TextBox 18' overlap by 5% of smaller bbox (textA: "Confidence layer — per-word an" / textB: "Token-level softmax extracted ")
- [OVERLAP] Shapes 'TextBox 22' & 'TextBox 23' overlap by 5% of smaller bbox (textA: "Beam-aggregation pipeline buil" / textB: "Beam-aggregation pipeline buil")

**Slide 42 — WHAT'S NEXT**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 43 — Step one — pilot on your videos**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 44 — Multi-speaker — engineering work, in flight**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 6' overlap by 10% of smaller bbox (textA: "TODAY" / textB: "Single-speaker mode")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 12' overlap by 10% of smaller bbox (textA: "PATH" / textB: "Entity-split preprocessing")

**Slide 45 — Arabic — real engineering work, mapped end-to-end**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 46 — Optional add-on — pre-filter low-quality clips before decode**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 12' overlap by 10% of smaller bbox (textA: "10 of 100 rejected — face too " / textB: "viseme accuracy drops past 30°")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 17' overlap by 10% of smaller bbox (textA: "8 of 100 rejected — mouth occl" / textB: "lower face must be unoccluded")
- [OVERLAP] Shapes 'TextBox 21' & 'TextBox 22' overlap by 10% of smaller bbox (textA: "7 of 100 rejected — too dark /" / textB: "lip-region contrast within ran")
- [NOTES] Notes cite 16 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 100% but notes only mention [70, 82] — possible mismatch.

**Slide 47 — Optional — domain-specific training run on your data**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.
- [NOTES] Body shows 65% but notes only mention [60, 62, 95] — possible mismatch.

**Slide 48 — How a domain-tuned version comes together**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 49 — Going to production — the partnership**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 50 — Thank You**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 11 numbers but lack any source reference (.md/.csv path).

**Slide 51 — What you just saw**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 52 — Appendix Example A — Salvage: truncation, core preserved**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "as this new home video market ")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "in the 1980s when film compani")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "52")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 53 — Appendix Example B — Salvage: scientific vocabulary lost**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "couples us to light cycles in ")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "takes into account our environ")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "53")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 54 — Appendix Example C — Salvage: ingredient confusion (cooking)**
- [LAYOUT] Shape 'TextBox 12' within 0.1in of slide edge (left=0.60, top=7.30, right_gap=0.60, bot_gap=0.00)
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 8% of smaller bbox (textA: "REFERENCE" / textB: "and i have a tablespoon of jal")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 8% of smaller bbox (textA: "HYPOTHESIS" / textB: "and i have a dietary smoothie ")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 28% of smaller bbox (textA: "BLUE: trust   ORANGE: review  " / textB: "54")
- [VIDEO] Video tile lacks 'click to play' / play-indicator caption within reasonable proximity.

**Slide 55 — Appendix Example D — Strip: dangerous-failure setup**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 56 — Appendix Example E — Strip: hallucination duplicate (Obama)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 57 — 65% useful — on real-world video, not benchmark data**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 5 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 65% but notes only mention [38, 39, 61, 62] — possible mismatch.

**Slide 58 — Five failure modes, all detected**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).
- [NOTES] Body shows 44% but notes only mention [9] — possible mismatch.

**Slide 59 — When the model fabricates, the system flags it**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 60 — What this means for your workflow**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 61 — The full pipeline — 8 automated stages**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 6' overlap by 12% of smaller bbox (textA: "Whisper ASR runs as a side-bra" / textB: "61")
- [NOTES] Notes cite 2 numbers but lack any source reference (.md/.csv path).

**Slide 62 — Three things to take with you**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

**Slide 63 — Appendix Example F — Trust/Salvage/Strip spread (six playable tiles)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 15% of smaller bbox (textA: "PERFECT" / textB: "Clean visual, clean output")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 12' overlap by 15% of smaller bbox (textA: "ALMOST PERFECT" / textB: "Near-verbatim transcription")
- [OVERLAP] Shapes 'TextBox 15' & 'TextBox 16' overlap by 15% of smaller bbox (textA: "PARTIAL" / textB: "Right gist, wrong specifics")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 15% of smaller bbox (textA: "NEAR MISS" / textB: "Off by a phrase, recoverable w")
- [OVERLAP] Shapes 'TextBox 23' & 'TextBox 24' overlap by 15% of smaller bbox (textA: "HALLUCINATION" / textB: "Fluent but wrong — auto-flagge")
- [OVERLAP] Shapes 'TextBox 27' & 'TextBox 28' overlap by 15% of smaller bbox (textA: "TOPIC DRIFT" / textB: "Model lost the thread, system ")

**Slide 64 — 8-Stage Automated Pipeline (appendix)**
- [BRAND] No corner logo (~0.35in) detected; expected per add_logo helper.

