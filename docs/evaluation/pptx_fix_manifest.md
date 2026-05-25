# Argos VSP — PowerPoint Fix Manifest

Categorized fix list for slide-writing phase. 
Pulled from BLOCKER/MAJOR/MINOR issues across audited decks.

## Argos_VSP_For_Orchard_May2026.pptx

### BLOCKER: none

### MAJOR (257)

**Slide 5 — What is Visual Speech Processing?**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 4' overlap by 33% of smaller bbox (textA: "What is Visual Speech Processi" / textB: "A system that reads lips from ")

**Slide 6 — Live example — clean speech, perfect transcription**
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 78% of smaller bbox (textA: "…the tireless and heroic work " / textB: "Reference and prediction are i")
- [OCCLUSION] Text shape 'TextBox 10' ("…the tireless and heroic work of our cou…") is 39% covered by later shape(s).

**Slide 7 — The Invisible Problem: Visemes**
- [OCCLUSION] Text shape 'TextBox 6' ("Same Mouth Shape, Different Words…") is 36% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 8' ("Identical mouth shapes can produce diffe…") is 42% covered by later shape(s).

**Slide 9 — How It Works: Data Flow**
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 11' overlap by 50% of smaller bbox (textA: "↓" / textB: "Mouth Crop  —  96×96 pixel reg")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 16' overlap by 50% of smaller bbox (textA: "↓" / textB: "Visual Features  —  AV-HuBERT ")
- [OVERLAP] Shapes 'TextBox 17' & 'TextBox 21' overlap by 50% of smaller bbox (textA: "↓" / textB: "Projection  —  Linear layer: 1")
- [OVERLAP] Shapes 'TextBox 22' & 'TextBox 26' overlap by 50% of smaller bbox (textA: "↓" / textB: "LLM Generates Text  —  LLaMA-2")
- [OVERLAP] Shapes 'TextBox 26' & 'TextBox 27' overlap by 52% of smaller bbox (textA: "LLM Generates Text  —  LLaMA-2" / textB: "Visual encoder is frozen — onl")
- [OCCLUSION] Text shape 'TextBox 7' ("↓…") is 125% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("↓…") is 125% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 17' ("↓…") is 125% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 22' ("↓…") is 125% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 26' ("LLM Generates Text  —  LLaMA-2-7B decode…") is 36% covered by later shape(s).

**Slide 10 — 8-Stage Automated Pipeline**
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 5' overlap by 77% of smaller bbox (textA: "1. Normalize" / textB: "HDR/10-bitconversion")
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 9' overlap by 77% of smaller bbox (textA: "2. Mouth Crop" / textB: "Face detect& ROI")
- [OVERLAP] Shapes 'TextBox 13' & 'TextBox 14' overlap by 77% of smaller bbox (textA: "4. LRS3 Convert" / textB: "Flat → LRS3format")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 18' overlap by 37% of smaller bbox (textA: "▼" / textB: "3. ASR")
- [OVERLAP] Shapes 'TextBox 18' & 'TextBox 19' overlap by 77% of smaller bbox (textA: "3. ASR" / textB: "Whispertranscription")
- [OVERLAP] Shapes 'TextBox 32' & 'TextBox 33' overlap by 77% of smaller bbox (textA: "5. Manifests" / textB: "TSV + splits")
- [OVERLAP] Shapes 'TextBox 35' & 'TextBox 36' overlap by 77% of smaller bbox (textA: "6. K-means" / textB: "Featureclustering")
- [OVERLAP] Shapes 'TextBox 39' & 'TextBox 40' overlap by 77% of smaller bbox (textA: "7. LLM Decode" / textB: "AV-HuBERT +LLaMA-2")
- [OVERLAP] Shapes 'TextBox 43' & 'TextBox 44' overlap by 77% of smaller bbox (textA: "8. Outputs" / textB: "Reports &burned video")
- [OVERLAP] Shapes 'TextBox 47' & 'TextBox 54' overlap by 32% of smaller bbox (textA: "Preprocessing" / textB: "auto_avsr  ·  av_hubert  ·  VS")
- [OVERLAP] Shapes 'TextBox 49' & 'TextBox 54' overlap by 32% of smaller bbox (textA: "Feature Extraction" / textB: "auto_avsr  ·  av_hubert  ·  VS")
- [OVERLAP] Shapes 'TextBox 51' & 'TextBox 54' overlap by 32% of smaller bbox (textA: "LLM Inference" / textB: "auto_avsr  ·  av_hubert  ·  VS")
- [OVERLAP] Shapes 'TextBox 53' & 'TextBox 54' overlap by 32% of smaller bbox (textA: "Output" / textB: "auto_avsr  ·  av_hubert  ·  VS")
- [OCCLUSION] Text shape 'TextBox 4' ("1. Normalize…") is 54% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 8' ("2. Mouth Crop…") is 54% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 13' ("4. LRS3 Convert…") is 54% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 16' ("▼…") is 93% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 18' ("3. ASR…") is 54% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 30' ("Existed in academic repo…") is 68% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 32' ("5. Manifests…") is 54% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 35' ("6. K-means…") is 54% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 39' ("7. LLM Decode…") is 54% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 43' ("8. Outputs…") is 54% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 47' ("Preprocessing…") is 32% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 49' ("Feature Extraction…") is 32% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 51' ("LLM Inference…") is 32% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 53' ("Output…") is 32% covered by later shape(s).

**Slide 11 — The Benchmark: Paper vs Reality**
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 9' overlap by 30% of smaller bbox (textA: "• LRS3 benchmark: curated TED " / textB: "Different dataset, fundamental")

**Slide 13 — Same WER, Different Effects**
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 5' overlap by 35% of smaller bbox (textA: "WER: 1 substitution  •  Harmle" / textB: "Ref: "the admiral gave the ord")
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 9' overlap by 35% of smaller bbox (textA: "WER: 1 substitution  •  Destru" / textB: "Ref: "Admiral McRae gave the o")
- [OCCLUSION] Text shape 'TextBox 4' ("WER: 1 substitution  •  Harmless…") is 35% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 8' ("WER: 1 substitution  •  Destructive…") is 35% covered by later shape(s).

**Slide 14 — Diversity of Inputs — Not LRS3**
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 8' overlap by 38% of smaller bbox (textA: "Lip-reading frame — visual sig" / textB: "Every number that follows come")
- [OCCLUSION] Text shape 'TextBox 6' ("Lip-reading frame — visual signal only, …") is 68% covered by later shape(s).

**Slide 15 — WER: The Metric That Lies**
- [OCCLUSION] Text shape 'TextBox 10' ("Intelligibility Score (Excellent)…") is 45% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 13' ("▶ Reference:  i want you to remember all…") is 43% covered by later shape(s).

**Slide 17 — What the AVSR Literature Reports vs What Users Get**
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 50% of smaller bbox (textA: "WHAT END USERS ACTUALLY CONSUM" / textB: "Same WER ~50% - very different")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 11' overlap by 33% of smaller bbox (textA: "WHAT END USERS ACTUALLY CONSUM" / textB: "Partial / useful")
- [OVERLAP] Shapes 'TextBox 14' & 'TextBox 15' overlap by 40% of smaller bbox (textA: "REF: "the overhead lights are " / textB: "Same WER, very different downs")
- [OCCLUSION] Text shape 'TextBox 9' ("WHAT END USERS ACTUALLY CONSUME…") is 60% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 10' ("Same WER ~50% - very different downstrea…") is 60% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("REF: "market research firm bernreuter is…") is 32% covered by later shape(s).

**Slide 18 — LLM-as-a-Judge: Gold Standard (1,497 Pairs)**
- [OCCLUSION] Text shape 'TextBox 4' ("• Use a frontier LLM (Claude Opus) as an…") is 52% covered by later shape(s).

**Slide 20 — Judge Example 1: Named Entity Swap**
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 10' overlap by 90% of smaller bbox (textA: "“market research firm rogers r" / textB: "Named Entity Swap — meaning fu")
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 39% of smaller bbox (textA: "Named Entity Swap — meaning fu" / textB: "Only company name changed (ber")
- [OCCLUSION] Text shape 'TextBox 4' ("WER 18%   WWER 15%   IS 4.55 (Excellent)…") is 41% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 6' ("“market research firm bernreuter researc…") is 38% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 8' ("“market research firm rogers research is…") is 66% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 10' ("Named Entity Swap — meaning fully preser…") is 39% covered by later shape(s).

**Slide 21 — Judge Example 3: Technical Vocabulary Drift**
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 10' overlap by 90% of smaller bbox (textA: "“we need a radically different" / textB: "Domain Vocabulary Drift — stru")
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 39% of smaller bbox (textA: "Domain Vocabulary Drift — stru" / textB: "Argument structure perfect: 'r")
- [OCCLUSION] Text shape 'TextBox 4' ("WER 52%   WWER 47%   IS 3.02 (Good)   Ju…") is 41% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 6' ("“we need a radically different approach …") is 38% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 8' ("“we need a radically different approach …") is 66% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 10' ("Domain Vocabulary Drift — structure inta…") is 39% covered by later shape(s).

**Slide 22 — Judge Example 5: Cooking Domain Confusion**
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 10' overlap by 90% of smaller bbox (textA: "“and i have a dietary smoothie" / textB: "Domain Confusion — food contex")
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 39% of smaller bbox (textA: "Domain Confusion — food contex" / textB: "Model knows it's a cooking vid")
- [OCCLUSION] Text shape 'TextBox 4' ("WER 89%   WWER 44%   IS 2.07 (Fair)   Ju…") is 41% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 6' ("“and i have a tablespoon of jalapeno fre…") is 38% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 8' ("“and i have a dietary smoothie i've got …") is 66% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 10' ("Domain Confusion — food context right, i…") is 39% covered by later shape(s).

**Slide 23 — Judge Example 6: Topic Hijack**
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 10' overlap by 90% of smaller bbox (textA: "“i actually used the overheard" / textB: "Topic Hijack — grammatically f")
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 39% of smaller bbox (textA: "Topic Hijack — grammatically f" / textB: "Phonetic cascade: 'overhead li")
- [OCCLUSION] Text shape 'TextBox 4' ("WER 74%   WWER 69%   IS 1.79 (Poor)   Ju…") is 41% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 6' ("“i actually use the overhead lights whic…") is 38% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 8' ("“i actually used the overheard ghost whi…") is 66% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 10' ("Topic Hijack — grammatically fluent, com…") is 39% covered by later shape(s).

**Slide 24 — Where IS and the Judge Disagree**
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 6' overlap by 60% of smaller bbox (textA: "IS Too Harsh  —  19 cases (1%)" / textB: "Judge says Y (meaning conveyed")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 8' overlap by 51% of smaller bbox (textA: "Judge says Y (meaning conveyed" / textB: "REF: "one really nice thing ab")
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 9' overlap by 67% of smaller bbox (textA: "REF: "one really nice thing ab" / textB: "Paraphrases and phonetic bridg")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 64% of smaller bbox (textA: "Paraphrases and phonetic bridg" / textB: "• Harmless hallucination (extr")
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 18' overlap by 56% of smaller bbox (textA: "• Harmless hallucination (extr" / textB: "98% agreement — disagreements ")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 13' overlap by 60% of smaller bbox (textA: "IS Too Generous  —  3 cases (0" / textB: "Judge says N (meaning lost)IS")
- [OVERLAP] Shapes 'TextBox 13' & 'TextBox 15' overlap by 33% of smaller bbox (textA: "Judge says N (meaning lost)IS" / textB: "REF: "all you have to do is un")
- [OVERLAP] Shapes 'TextBox 15' & 'TextBox 16' overlap by 67% of smaller bbox (textA: "REF: "all you have to do is un" / textB: "Structural match hides semanti")
- [OVERLAP] Shapes 'TextBox 15' & 'TextBox 17' overlap by 34% of smaller bbox (textA: "REF: "all you have to do is un" / textB: "• Domain confusion (medical → ")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 17' overlap by 64% of smaller bbox (textA: "Structural match hides semanti" / textB: "• Domain confusion (medical → ")
- [OVERLAP] Shapes 'TextBox 17' & 'TextBox 18' overlap by 49% of smaller bbox (textA: "• Domain confusion (medical → " / textB: "98% agreement — disagreements ")
- [OCCLUSION] Text shape 'TextBox 5' ("IS Too Harsh  —  19 cases (1%)…") is 65% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 6' ("Judge says Y (meaning conveyed)IS says …") is 111% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 8' ("REF: "one really nice thing about this i…") is 58% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 9' ("Paraphrases and phonetic bridges preserv…") is 77% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 10' ("• Harmless hallucination (extra words, c…") is 56% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("IS Too Generous  —  3 cases (0%)…") is 65% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 13' ("Judge says N (meaning lost)IS says ≥ 3.…") is 78% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 15' ("REF: "all you have to do is unscrew"
HYP…") is 58% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 16' ("Structural match hides semantic reversal…") is 77% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 17' ("• Domain confusion (medical → wellness)…") is 49% covered by later shape(s).

**Slide 25 — Context Exposes Hidden Failures**
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 6' overlap by 71% of smaller bbox (textA: "230 downgrades vs 68 upgrades
" / textB: "• 80% stable across modes
• Co")
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 47% of smaller bbox (textA: "REF: "...because I'm a lover o" / textB: "One word reverses the meaning.")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 12' overlap by 75% of smaller bbox (textA: "One word reverses the meaning." / textB: "Full list of context false pos")
- [OCCLUSION] Text shape 'TextBox 3' ("Blind → Context Transitions…") is 50% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 5' ("230 downgrades vs 68 upgrades
Y→P domina…") is 56% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 10' ("REF: "...because I'm a lover of"
HYP: ".…") is 47% covered by later shape(s).

**Slide 27 — IS Signals: Word Accuracy & Length**
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 6' overlap by 88% of smaller bbox (textA: "IS = 6 signals (0–5).  IS ≥ 2." / textB: "Inverse WER  (15%)")
- [OCCLUSION] Text shape 'TextBox 4' ("IS = 6 signals (0–5).  IS ≥ 2.00 = "Usef…") is 64% covered by later shape(s).

**Slide 28 — IS Signals: Semantic Similarity**
- [OCCLUSION] Text shape 'TextBox 4' ("Weight: 25% — the single largest signal…") is 44% covered by later shape(s).

**Slide 30 — Do 6 Signals Actually Measure 6 Things?**
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 35% of smaller bbox (textA: "68%" / textB: "Semantic + Phonetic + WER + WW")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 8' overlap by 49% of smaller bbox (textA: "68%" / textB: "All 5 content signals load equ")
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 60% of smaller bbox (textA: "Semantic + Phonetic + WER + WW" / textB: "All 5 content signals load equ")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 12' overlap by 35% of smaller bbox (textA: "20%" / textB: "Length Ratio dominates (loadin")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 13' overlap by 49% of smaller bbox (textA: "20%" / textB: "Catches hallucination (too lon")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 13' overlap by 60% of smaller bbox (textA: "Length Ratio dominates (loadin" / textB: "Catches hallucination (too lon")
- [OVERLAP] Shapes 'TextBox 13' & 'TextBox 14' overlap by 36% of smaller bbox (textA: "Catches hallucination (too lon" / textB: "Kaiser retains 2 PCs (88% of v")
- [OCCLUSION] Text shape 'TextBox 6' ("68%…") is 157% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 7' ("Semantic + Phonetic + WER + WWER + Named…") is 60% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 8' ("All 5 content signals load equally (0.43…") is 58% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 11' ("20%…") is 100% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("Length Ratio dominates (loading 0.91) — …") is 60% covered by later shape(s).

**Slide 31 — IS in Action: Two Real Segments**
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 98% of smaller bbox (textA: "Ref: “allow you to work with t" / textB: "Semantic Sim")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 11' overlap by 49% of smaller bbox (textA: "Ref: “allow you to work with t" / textB: "Phonetic Sim")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 12' overlap by 50% of smaller bbox (textA: "Ref: “allow you to work with t" / textB: "0.89")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 13' overlap by 50% of smaller bbox (textA: "Ref: “allow you to work with t" / textB: "× 0.15")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 14' overlap by 50% of smaller bbox (textA: "Ref: “allow you to work with t" / textB: "= 0.134")
- [OVERLAP] Shapes 'TextBox 35' & 'TextBox 36' overlap by 98% of smaller bbox (textA: "Ref: “carry strap”
Hyp: “holoc" / textB: "Semantic Sim")
- [OVERLAP] Shapes 'TextBox 35' & 'TextBox 40' overlap by 49% of smaller bbox (textA: "Ref: “carry strap”
Hyp: “holoc" / textB: "Phonetic Sim")
- [OVERLAP] Shapes 'TextBox 35' & 'TextBox 41' overlap by 50% of smaller bbox (textA: "Ref: “carry strap”
Hyp: “holoc" / textB: "0.20")
- [OVERLAP] Shapes 'TextBox 35' & 'TextBox 42' overlap by 50% of smaller bbox (textA: "Ref: “carry strap”
Hyp: “holoc" / textB: "× 0.15")
- [OVERLAP] Shapes 'TextBox 35' & 'TextBox 43' overlap by 50% of smaller bbox (textA: "Ref: “carry strap”
Hyp: “holoc" / textB: "= 0.030")
- [OCCLUSION] Text shape 'TextBox 6' ("Ref: “allow you to work with the team in…") is 50% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 35' ("Ref: “carry strap”
Hyp: “holocaust denie…") is 50% covered by later shape(s).

**Slide 32 — Two Dimensions of Quality (PCA)**
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 5' overlap by 42% of smaller bbox (textA: "PCA retains 2 principal compon" / textB: "68%")
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 11' overlap by 42% of smaller bbox (textA: "PCA retains 2 principal compon" / textB: "20%")
- [OCCLUSION] Text shape 'TextBox 3' ("PCA retains 2 principal components (Kais…") is 61% covered by later shape(s).

**Slide 34 — The Gap: Where WER Lies Most**
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 5' overlap by 61% of smaller bbox (textA: "segments WER wrongly discards " / textB: "• NIV = Native Intelligibility")
- [OCCLUSION] Text shape 'TextBox 4' ("segments WER wrongly discards (NIV-calib…") is 61% covered by later shape(s).

**Slide 36 — Where It Works — and How It Fails: Oracle vs Realistic**
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 6' overlap by 64% of smaller bbox (textA: "What the model can produce on " / textB: "61.92%")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 12' overlap by 75% of smaller bbox (textA: "Realistic  (Trust-gate output)" / textB: "What the user can confidently ")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 13' overlap by 36% of smaller bbox (textA: "Realistic  (Trust-gate output)" / textB: "65.2%")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 13' overlap by 64% of smaller bbox (textA: "What the user can confidently " / textB: "65.2%")
- [OCCLUSION] Text shape 'TextBox 5' ("What the model can produce on the 1,497-…") is 56% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 11' ("Realistic  (Trust-gate output)…") is 85% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("What the user can confidently rely on (≥…") is 56% covered by later shape(s).

**Slide 39 — Failure Mode Taxonomy**
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 4' overlap by 49% of smaller bbox (textA: "574 segments below useful thre" / textB: "Wrong Topic")
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 6' overlap by 49% of smaller bbox (textA: "574 segments below useful thre" / textB: "44.4% (255)")
- [OCCLUSION] Text shape 'TextBox 3' ("574 segments below useful threshold (IS …") is 34% covered by later shape(s).

**Slide 40 — Failure Mode Taxonomy (1/2): Highest Impact First**
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 40% of smaller bbox (textA: "Rule: Semantic < 0.2 (phonetic" / textB: "▸ Ref: “weight loss and diet” ")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 13' overlap by 40% of smaller bbox (textA: "Rule: WER ≥ 100% (output longe" / textB: "▸ Ref: “carry strap” → Hyp: “h")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 19' overlap by 42% of smaller bbox (textA: "Roughly right but names/conten" / textB: "Ordered by impact — highest to")
- [OVERLAP] Shapes 'TextBox 17' & 'TextBox 18' overlap by 40% of smaller bbox (textA: "Rule: NEA F1 < 20% OR key cont" / textB: "▸ Ref: “13th amendment is goin")
- [OVERLAP] Shapes 'TextBox 18' & 'TextBox 19' overlap by 53% of smaller bbox (textA: "▸ Ref: “13th amendment is goin" / textB: "Ordered by impact — highest to")
- [OCCLUSION] Text shape 'TextBox 3' ("574 below-threshold segments (IS < 2.0) …") is 52% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 7' ("Rule: Semantic < 0.2 (phonetic-matched o…") is 40% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("Rule: WER ≥ 100% (output longer than ref…") is 40% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 16' ("Roughly right but names/content words lo…") is 40% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 17' ("Rule: NEA F1 < 20% OR key content substi…") is 40% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 18' ("▸ Ref: “13th amendment is going” → Hyp: …") is 40% covered by later shape(s).

**Slide 41 — Failure Modes: Real Examples**
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 5' overlap by 50% of smaller bbox (textA: "Hallucination  (19%)" / textB: "Reference:")
- [OVERLAP] Shapes 'TextBox 13' & 'TextBox 14' overlap by 50% of smaller bbox (textA: "Wrong Topic  (44%)" / textB: "Reference:")
- [OVERLAP] Shapes 'TextBox 22' & 'TextBox 23' overlap by 50% of smaller bbox (textA: "Right Topic, Wrong Details  (1" / textB: "Reference:")

**Slide 43 — LLM Salvage: Three Real Recoveries**
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 50% of smaller bbox (textA: "“in one sense it’s roseand ke" / textB: "How a viewer recovers this:")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 50% of smaller bbox (textA: "“moved the conceptual rulesov" / textB: "How a viewer recovers this:")
- [OVERLAP] Shapes 'TextBox 28' & 'TextBox 29' overlap by 50% of smaller bbox (textA: "“over the last 10 years we hav" / textB: "How a viewer recovers this:")

**Slide 44 — LLM Salvage: Domain Context Fills the Gaps**
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 62% of smaller bbox (textA: "“the fear of the loss complete" / textB: "How a wise viewer recovers thi")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 62% of smaller bbox (textA: "“middle east and afghanistana" / textB: "How a wise viewer recovers thi")
- [OVERLAP] Shapes 'TextBox 28' & 'TextBox 29' overlap by 62% of smaller bbox (textA: "“i have a dietary smoothiei’v" / textB: "How a wise viewer recovers thi")

**Slide 45 — Two Layers of Confidence (Per-Word + Per-Segment)**
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 55% of smaller bbox (textA: "max softmax probability per to" / textB: "p_t  =  max_v  P(token = v | x")
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 45% of smaller bbox (textA: "p_t  =  max_v  P(token = v | x" / textB: "• Aggregate sub-tokens up to w")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 12' overlap by 55% of smaller bbox (textA: "mean log-probability over the " / textB: "mean_prob  =  exp( (1/T) * sum")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 13' overlap by 45% of smaller bbox (textA: "mean_prob  =  exp( (1/T) * sum" / textB: "• Length-anomaly check (too sh")
- [OCCLUSION] Text shape 'TextBox 3' ("Both layers are derived from the LLM's o…") is 36% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 6' ("max softmax probability per token…") is 55% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 7' ("p_t  =  max_v  P(token = v | x_<=t)…") is 45% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 11' ("mean log-probability over the segment…") is 55% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("mean_prob  =  exp( (1/T) * sum_t log p_t…") is 45% covered by later shape(s).

**Slide 48 — Per-Word Confidence Bands - Distribution**
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 60% of smaller bbox (textA: "JOINT RULE - STRICTER, MORE RE" / textB: "• Green drops 33% (11,309 → 7,")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 60% of smaller bbox (textA: "LEGACY CONF-ONLY - PERMISSIVE" / textB: "• Almost half of words paint g")
- [OCCLUSION] Text shape 'TextBox 6' ("JOINT RULE - STRICTER, MORE RELIABLE…") is 60% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 9' ("LEGACY CONF-ONLY - PERMISSIVE…") is 60% covered by later shape(s).

**Slide 50 — Green Reliability Depends on Segment Quality**
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 5' overlap by 86% of smaller bbox (textA: "P(correct | green) stratified " / textB: "Stratified P(green | bin)")
- [OCCLUSION] Text shape 'TextBox 3' ("P(correct | green) stratified by segment…") is 37% covered by later shape(s).

**Slide 51 — Green Leakage - When High Confidence Misleads**
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 5' overlap by 33% of smaller bbox (textA: "2,192 wrong-and-green words ac" / textB: "Numeric scale flip")
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 11' overlap by 33% of smaller bbox (textA: "2,192 wrong-and-green words ac" / textB: "Numeric digit drop")
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 17' overlap by 33% of smaller bbox (textA: "2,192 wrong-and-green words ac" / textB: "Year drift")
- [OCCLUSION] Text shape 'TextBox 3' ("2,192 wrong-and-green words across 23,26…") is 52% covered by later shape(s).

**Slide 52 — Three Calibrated Thresholds on Segment mean_prob**
- [OCCLUSION] Text shape 'TextBox 3' ("Each threshold corresponds to a target o…") is 30% covered by later shape(s).

**Slide 53 — Three-Tier Policy - Per-Tier Counts and Reliability**
- [OCCLUSION] Text shape 'TextBox 3' ("Tiers from segment mean_prob; per-tier P…") is 31% covered by later shape(s).

**Slide 54 — Per-Word Bands Stratified by NIV Outcome**
- [OCCLUSION] Text shape 'TextBox 3' ("Within useful content (Y+P), per-word ba…") is 37% covered by later shape(s).

**Slide 55 — Joint Confidence + Beam-Agreement Band Rule**
- [OVERLAP] Shapes 'TextBox 14' & 'TextBox 15' overlap by 38% of smaller bbox (textA: "WHY ADD AGREEMENT?  Beam agree" / textB: "Llama-2-7b specific — LLM swap")

**Slide 56 — Beam Agreement Adds Independent Signal**
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 90% of smaller bbox (textA: "• 54pp P(correct) gap at SAME " / textB: "Diagnostic: diagnose_confidenc")

**Slide 57 — Trust-Gate Operating Points (per-segment)**
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 6' overlap by 45% of smaller bbox (textA: "Recommended default: 30% green" / textB: "Calibrated under joint conf+ag")

**Slide 58 — N-best Aggregation: From One to All 20 Hypotheses (Mission 6)**
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 10' overlap by 46% of smaller bbox (textA: "Previously we displayed only t" / textB: "Minimum Bayes Risk Decoding")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 65% of smaller bbox (textA: "Recognizer Output Voting Error" / textB: "• Align all 20 hypotheses word")
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 12' overlap by 31% of smaller bbox (textA: "• Align all 20 hypotheses word" / textB: "• v3 Judge: MBR Y+P 71% vs bas")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 12' overlap by 31% of smaller bbox (textA: "• Score each hypothesis agains" / textB: "• v3 Judge: MBR Y+P 71% vs bas")
- [OCCLUSION] Text shape 'TextBox 3' ("Previously we displayed only the top-1 h…") is 61% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 6' ("Recognizer Output Voting Error Reduction…") is 65% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 7' ("• Align all 20 hypotheses word-by-word
•…") is 31% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 11' ("• Score each hypothesis against ALL othe…") is 31% covered by later shape(s).

**Slide 59 — N-best Aggregation: v3 Judge Paired Tests**
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 9' overlap by 54% of smaller bbox (textA: "Below: IS distribution per met" / textB: "v3 dual-conf judge  /  Opus 4.")
- [OCCLUSION] Text shape 'TextBox 6' ("Below: IS distribution per method (top1 …") is 44% covered by later shape(s).

**Slide 61 — v1 vs v3 Judge: A Prompt-Design Lesson**
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 9' overlap by 55% of smaller bbox (textA: "v3 - dual-conf prompt (current" / textB: "• Method-conf AND baseline_con")
- [OCCLUSION] Text shape 'TextBox 8' ("v3 - dual-conf prompt (current)…") is 55% covered by later shape(s).

**Slide 63 — Demo — TRUST: AI talk, Indian-accent speaker (IS=5.00)**
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 78% of smaller bbox (textA: "to this wave of artificial int" / textB: "Every word GREEN under the joi")
- [OCCLUSION] Text shape 'TextBox 10' ("to this wave of artificial intelligence …") is 39% covered by later shape(s).

**Slide 64 — Demo — Obama: Trust Tier (conf-only fallback)**
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 78% of smaller bbox (textA: "...as president bush said amer" / textB: "Most words green. The 'preside")
- [OCCLUSION] Text shape 'TextBox 10' ("...as president bush said america will n…") is 39% covered by later shape(s).

**Slide 65 — Demo — INSPECT: structure preserved, vocabulary lost**
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 78% of smaller bbox (textA: "tells us when to make stops — " / textB: "Repeating 'tells us when to X'")
- [OCCLUSION] Text shape 'TextBox 10' ("tells us when to make stops — vs ref's c…") is 39% covered by later shape(s).

**Slide 66 — Demo - Strip: entity swap auto-flagged**
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 78% of smaller bbox (textA: "market research firm rogers re" / textB: "Entity-swap tokens 'rogers', '")
- [OCCLUSION] Text shape 'TextBox 10' ("market research firm rogers research is …") is 39% covered by later shape(s).

**Slide 67 — Demo - Salvage: technical vocabulary drift**
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 78% of smaller bbox (textA: "must indeed find a way we can " / textB: "Argument structure preserved (")
- [OCCLUSION] Text shape 'TextBox 10' ("must indeed find a way we can design exi…") is 39% covered by later shape(s).

**Slide 72 — Stronger LLM + Smart Prompts = Force Multiplier**
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 5' overlap by 45% of smaller bbox (textA: "LLM Upgrade (needs training)" / textB: "• Llama 3.1 8B: drop-in (hidde")
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 45% of smaller bbox (textA: "Smart Prompts (multiplier)" / textB: "• 7 strategies: topic, count, ")
- [OCCLUSION] Text shape 'TextBox 4' ("LLM Upgrade (needs training)…") is 45% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 7' ("Smart Prompts (multiplier)…") is 45% covered by later shape(s).

**Slide 73 — LLM Upgrade: Why It Matters**
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 86% of smaller bbox (textA: "VALLR (ICCV 2025): Llama 3.2-3" / textB: "Same hidden dim (4096) — adapt")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 35% of smaller bbox (textA: "64%" / textB: "−3–8 pp")
- [OVERLAP] Shapes 'TextBox 14' & 'TextBox 17' overlap by 35% of smaller bbox (textA: "−3–8 pp" / textB: "−5–10 pp")
- [OVERLAP] Shapes 'TextBox 17' & 'TextBox 20' overlap by 35% of smaller bbox (textA: "−5–10 pp" / textB: "−10–15 pp")
- [OVERLAP] Shapes 'TextBox 20' & 'TextBox 23' overlap by 35% of smaller bbox (textA: "−10–15 pp" / textB: "35–40%")
- [OCCLUSION] Text shape 'TextBox 6' ("VALLR (ICCV 2025): Llama 3.2-3B achieved…") is 46% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 11' ("64%…") is 80% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 14' ("−3–8 pp…") is 80% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 17' ("−5–10 pp…") is 80% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 20' ("−10–15 pp…") is 80% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 23' ("35–40%…") is 50% covered by later shape(s).

**Slide 75 — Arabic Pipeline: Replication Roadmap**
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 4' overlap by 55% of smaller bbox (textA: "What’s Needed & How We’ll Do I" / textB: "• AV-HuBERT encoder (BOTTLENEC")
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 5' overlap by 54% of smaller bbox (textA: "• AV-HuBERT encoder (BOTTLENEC" / textB: "• Arabic LLM backend
• Swap Ll")
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 6' overlap by 54% of smaller bbox (textA: "• Arabic LLM backend
• Swap Ll" / textB: "• Eval dataset (UNKNOWN)
• No ")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 54% of smaller bbox (textA: "• Eval dataset (UNKNOWN)
• No " / textB: "• Training infrastructure
• AW")
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 54% of smaller bbox (textA: "• Training infrastructure
• AW" / textB: "• RTL text & normalization
• R")
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 12' overlap by 58% of smaller bbox (textA: "• RTL text & normalization
• R" / textB: "Realistic estimate: 2–3 months")
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 13' overlap by 42% of smaller bbox (textA: "• RTL text & normalization
• R" / textB: "Pipeline code is language-agno")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 13' overlap by 90% of smaller bbox (textA: "Realistic estimate: 2–3 months" / textB: "Pipeline code is language-agno")
- [OCCLUSION] Text shape 'TextBox 3' ("What’s Needed & How We’ll Do It…") is 55% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 4' ("• AV-HuBERT encoder (BOTTLENECK)
• Arabi…") is 63% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 5' ("• Arabic LLM backend
• Swap Llama-2 for …") is 63% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 6' ("• Eval dataset (UNKNOWN)
• No Arabic lip…") is 63% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 7' ("• Training infrastructure
• AWS GPU (exi…") is 79% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 8' ("• RTL text & normalization
• RTL, spaCy …") is 127% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 12' ("Realistic estimate: 2–3 months (encoder …") is 67% covered by later shape(s).

**Slide 80 — A1: Homophenes — The Lip-Reading Problem**
- [OCCLUSION] Text shape 'TextBox 3' ("50–70% of English sounds are invisible o…") is 50% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 5' ("Confusable word pairs (identical on lips…") is 40% covered by later shape(s).

**Slide 81 — A3: IS Component Correlation**
- [OCCLUSION] Text shape 'TextBox 3' ("PCA: 6 IS signals collapse into 2 princi…") is 50% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 5' ("Cross-Config Stability (16 configs)…") is 60% covered by later shape(s).

**Slide 82 — Appendix: PCA Loadings on the 6 IS Signals**
- [OCCLUSION] Text shape 'TextBox 3' ("Kaiser criterion retains 2 components. T…") is 55% covered by later shape(s).

**Slide 85 — A5: LLM Salvage — Curated Examples**
- [OCCLUSION] Text shape 'TextBox 3' ("One real example per recovery category —…") is 40% covered by later shape(s).

**Slide 86 — A9: Context Evaluation — Transition Details**
- [OCCLUSION] Text shape 'TextBox 3' ("Blind → Context Transition Matrix…") is 46% covered by later shape(s).
- [OCCLUSION] Text shape 'TextBox 7' ("Per-Topic Y+P Delta (Blind → Context)…") is 50% covered by later shape(s).

**Slide 88 — Two Environments: Development and Production**
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 6' overlap by 93% of smaller bbox (textA: "• Full research environment
• " / textB: "Container (Production)")

### MINOR (118)

**Slide 2 — What was done? (1/2)**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 11% of smaller bbox (textA: "What was done? (1/2)" / textB: "Four months on visual speech p")

**Slide 3 — What was done? (2/2)**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 11% of smaller bbox (textA: "What was done? (2/2)" / textB: "Key findings and outcomes:")

**Slide 7 — The Invisible Problem: Visemes**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 10% of smaller bbox (textA: "The Invisible Problem: Visemes" / textB: "The Invisible Problem")
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 6' overlap by 5% of smaller bbox (textA: "The Invisible Problem: Visemes" / textB: "Same Mouth Shape, Different Wo")

**Slide 9 — How It Works: Data Flow**
- [OVERLAP] Shapes 'TextBox 25' & 'TextBox 27' overlap by 23% of smaller bbox (textA: "5" / textB: "Visual encoder is frozen — onl")

**Slide 10 — 8-Stage Automated Pipeline**
- [OVERLAP] Shapes 'TextBox 30' & 'TextBox 35' overlap by 18% of smaller bbox (textA: "Existed in academic repo" / textB: "6. K-means")
- [OVERLAP] Shapes 'TextBox 30' & 'TextBox 39' overlap by 18% of smaller bbox (textA: "Existed in academic repo" / textB: "7. LLM Decode")

**Slide 14 — Diversity of Inputs — Not LRS3**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 10% of smaller bbox (textA: "Diversity of Inputs — Not LRS3" / textB: "Real-world / observational foo")

**Slide 15 — WER: The Metric That Lies**
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 13' overlap by 25% of smaller bbox (textA: "6 insertions, 1 deletion= nea" / textB: "▶ Reference:  i want you to re")

**Slide 17 — What the AVSR Literature Reports vs What Users Get**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 10% of smaller bbox (textA: "What the AVSR Literature Repor" / textB: "AVSR / VSP papers (LRS3, LRW, ")
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 12' overlap by 30% of smaller bbox (textA: "Same WER ~50% - very different" / textB: "REF: "market research firm ber")
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 11% of smaller bbox (textA: "REF: "market research firm ber" / textB: "REF: "the overhead lights are ")
- [OVERLAP] Shapes 'TextBox 15' & 'TextBox 16' overlap by 15% of smaller bbox (textA: "Same WER, very different downs" / textB: "Therefore we built IS — the In")

**Slide 18 — LLM-as-a-Judge: Gold Standard (1,497 Pairs)**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 13% of smaller bbox (textA: "LLM-as-a-Judge: Gold Standard " / textB: "What Is LLM-as-a-Judge?")
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 7' overlap by 13% of smaller bbox (textA: "LLM-as-a-Judge: Gold Standard " / textB: "Methodology:")

**Slide 19 — LLM Judge: Deep Dive**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 14% of smaller bbox (textA: "LLM Judge: Deep Dive" / textB: "30 Representative Segments")
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 5' overlap by 14% of smaller bbox (textA: "LLM Judge: Deep Dive" / textB: "What the Sample Reveals")

**Slide 20 — Judge Example 1: Named Entity Swap**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 4' overlap by 6% of smaller bbox (textA: "Judge Example 1: Named Entity " / textB: "WER 18%   WWER 15%   IS 4.55 (")
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 6' overlap by 12% of smaller bbox (textA: "WER 18%   WWER 15%   IS 4.55 (" / textB: "“market research firm bernreut")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 8' overlap by 24% of smaller bbox (textA: "“market research firm bernreut" / textB: "“market research firm rogers r")
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 11' overlap by 11% of smaller bbox (textA: "“market research firm rogers r" / textB: "Only company name changed (ber")

**Slide 21 — Judge Example 3: Technical Vocabulary Drift**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 4' overlap by 6% of smaller bbox (textA: "Judge Example 3: Technical Voc" / textB: "WER 52%   WWER 47%   IS 3.02 (")
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 6' overlap by 12% of smaller bbox (textA: "WER 52%   WWER 47%   IS 3.02 (" / textB: "“we need a radically different")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 8' overlap by 24% of smaller bbox (textA: "“we need a radically different" / textB: "“we need a radically different")
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 11' overlap by 11% of smaller bbox (textA: "“we need a radically different" / textB: "Argument structure perfect: 'r")

**Slide 22 — Judge Example 5: Cooking Domain Confusion**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 4' overlap by 6% of smaller bbox (textA: "Judge Example 5: Cooking Domai" / textB: "WER 89%   WWER 44%   IS 2.07 (")
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 6' overlap by 12% of smaller bbox (textA: "WER 89%   WWER 44%   IS 2.07 (" / textB: "“and i have a tablespoon of ja")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 8' overlap by 24% of smaller bbox (textA: "“and i have a tablespoon of ja" / textB: "“and i have a dietary smoothie")
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 11' overlap by 11% of smaller bbox (textA: "“and i have a dietary smoothie" / textB: "Model knows it's a cooking vid")

**Slide 23 — Judge Example 6: Topic Hijack**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 4' overlap by 6% of smaller bbox (textA: "Judge Example 6: Topic Hijack" / textB: "WER 74%   WWER 69%   IS 1.79 (")
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 6' overlap by 12% of smaller bbox (textA: "WER 74%   WWER 69%   IS 1.79 (" / textB: "“i actually use the overhead l")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 8' overlap by 24% of smaller bbox (textA: "“i actually use the overhead l" / textB: "“i actually used the overheard")
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 11' overlap by 11% of smaller bbox (textA: "“i actually used the overheard" / textB: "Phonetic cascade: 'overhead li")

**Slide 24 — Where IS and the Judge Disagree**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 14% of smaller bbox (textA: "Where IS and the Judge Disagre" / textB: "22 of 1,497 segments (2%) — ra")
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 10' overlap by 26% of smaller bbox (textA: "REF: "one really nice thing ab" / textB: "• Harmless hallucination (extr")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 18' overlap by 13% of smaller bbox (textA: "Paraphrases and phonetic bridg" / textB: "98% agreement — disagreements ")
- [OVERLAP] Shapes 'TextBox 16' & 'TextBox 18' overlap by 13% of smaller bbox (textA: "Structural match hides semanti" / textB: "98% agreement — disagreements ")

**Slide 25 — Context Exposes Hidden Failures**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 5% of smaller bbox (textA: "Context Exposes Hidden Failure" / textB: "Blind → Context Transitions")
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 7' overlap by 14% of smaller bbox (textA: "Context Exposes Hidden Failure" / textB: "The IS = 4.75 False Positive")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 13' overlap by 16% of smaller bbox (textA: "• 80% stable across modes
• Co" / textB: "Domain knowledge raises the ba")

**Slide 26 — Why LLM as a Judge Is Not Enough**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 14% of smaller bbox (textA: "Why LLM as a Judge Is Not Enou" / textB: "Five reasons we built the Inte")
- [NOTES] Notes cite 3 numbers but lack any source reference (.md/.csv path).

**Slide 28 — IS Signals: Semantic Similarity**
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 6' overlap by 20% of smaller bbox (textA: "Weight: 25% — the single large" / textB: "How It Works")

**Slide 30 — Do 6 Signals Actually Measure 6 Things?**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 6% of smaller bbox (textA: "Do 6 Signals Actually Measure " / textB: "PCA on 1,497 segments reveals ")
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 5' overlap by 5% of smaller bbox (textA: "PCA on 1,497 segments reveals " / textB: "PC1: Signal Quality")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 11' overlap by 29% of smaller bbox (textA: "68%" / textB: "20%")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 12' overlap by 9% of smaller bbox (textA: "68%" / textB: "Length Ratio dominates (loadin")
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 11' overlap by 16% of smaller bbox (textA: "All 5 content signals load equ" / textB: "20%")
- [OVERLAP] Shapes 'TextBox 11' & 'TextBox 14' overlap by 15% of smaller bbox (textA: "20%" / textB: "Kaiser retains 2 PCs (88% of v")

**Slide 31 — IS in Action: Two Real Segments**
- [OVERLAP] Shapes 'TextBox 31' & 'TextBox 61' overlap by 14% of smaller bbox (textA: "Sum × 5 = 4.22 → IS 4.2 (Good)" / textB: "IS = 5 × (0.25·Sem + 0.15·(Pho")
- [OVERLAP] Shapes 'TextBox 60' & 'TextBox 61' overlap by 14% of smaller bbox (textA: "Sum × 5 = 0.81 → IS 0.8 (Faile" / textB: "IS = 5 × (0.25·Sem + 0.15·(Pho")

**Slide 32 — Two Dimensions of Quality (PCA)**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 5% of smaller bbox (textA: "Two Dimensions of Quality (PCA" / textB: "PCA retains 2 principal compon")

**Slide 33 — Model Comparison: IS Profiles**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 5% of smaller bbox (textA: "Model Comparison: IS Profiles" / textB: "How different LLM backbones wo")

**Slide 35 — A8: LLM Judge × IS Tier Cross-Tabulation**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 13% of smaller bbox (textA: "A8: LLM Judge × IS Tier Cross-" / textB: "Judge verdict distribution acr")

**Slide 39 — Failure Mode Taxonomy**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 6% of smaller bbox (textA: "Failure Mode Taxonomy" / textB: "574 segments below useful thre")

**Slide 40 — Failure Mode Taxonomy (1/2): Highest Impact First**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 6% of smaller bbox (textA: "Failure Mode Taxonomy (1/2): H" / textB: "574 below-threshold segments (")
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 5' overlap by 24% of smaller bbox (textA: "574 below-threshold segments (" / textB: "1. Wrong Topic  (44%)")
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 7' overlap by 20% of smaller bbox (textA: "574 below-threshold segments (" / textB: "Rule: Semantic < 0.2 (phonetic")
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 6' overlap by 26% of smaller bbox (textA: "1. Wrong Topic  (44%)" / textB: "Mouth shapes decoded to wrong ")
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 26% of smaller bbox (textA: "2. Hallucination  (19%)" / textB: "Model invented fake text  —  1")
- [OVERLAP] Shapes 'TextBox 15' & 'TextBox 16' overlap by 26% of smaller bbox (textA: "3. Right Topic, Wrong Details " / textB: "Roughly right but names/conten")

**Slide 43 — LLM Salvage: Three Real Recoveries**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 14% of smaller bbox (textA: "LLM Salvage: Three Real Recove" / textB: "These segments failed IS (< 3.")

**Slide 44 — LLM Salvage: Domain Context Fills the Gaps**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 14% of smaller bbox (textA: "LLM Salvage: Domain Context Fi" / textB: "A viewer who knows the topic r")

**Slide 45 — Two Layers of Confidence (Per-Word + Per-Segment)**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 6% of smaller bbox (textA: "Two Layers of Confidence (Per-" / textB: "Both layers are derived from t")
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 5' overlap by 12% of smaller bbox (textA: "Both layers are derived from t" / textB: "1. PER-WORD")
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 10' overlap by 12% of smaller bbox (textA: "Both layers are derived from t" / textB: "2. PER-SEGMENT")
- [OVERLAP] Shapes 'TextBox 13' & 'TextBox 14' overlap by 13% of smaller bbox (textA: "• Length-anomaly check (too sh" / textB: "Both layers calibrated against")

**Slide 46 — Confidence Without Ground Truth**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 5% of smaller bbox (textA: "Confidence Without Ground Trut" / textB: "All the IS / WER / Judge analy")
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 5' overlap by 13% of smaller bbox (textA: "• Goal: a per-segment and per-" / textB: "Two layers of confidence (just")
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 47 — Confidence Scoring (shipped) — Surface the Good 65%**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 14% of smaller bbox (textA: "Confidence Scoring (shipped) —" / textB: "How It Works")
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 7' overlap by 14% of smaller bbox (textA: "Confidence Scoring (shipped) —" / textB: "What It Enables")

**Slide 48 — Per-Word Confidence Bands - Distribution**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 10% of smaller bbox (textA: "Per-Word Confidence Bands - Di" / textB: "Total per-word judgments: 23,2")

**Slide 49 — Band Reliability - Overall P(correct | band)**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 10% of smaller bbox (textA: "Band Reliability - Overall P(c" / textB: "P(correct) of each band, compu")

**Slide 50 — Green Reliability Depends on Segment Quality**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 6% of smaller bbox (textA: "Green Reliability Depends on S" / textB: "P(correct | green) stratified ")

**Slide 51 — Green Leakage - When High Confidence Misleads**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 6% of smaller bbox (textA: "Green Leakage - When High Conf" / textB: "2,192 wrong-and-green words ac")

**Slide 52 — Three Calibrated Thresholds on Segment mean_prob**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 6% of smaller bbox (textA: "Three Calibrated Thresholds on" / textB: "Each threshold corresponds to ")

**Slide 53 — Three-Tier Policy - Per-Tier Counts and Reliability**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 6% of smaller bbox (textA: "Three-Tier Policy - Per-Tier C" / textB: "Tiers from segment mean_prob; ")

**Slide 54 — Per-Word Bands Stratified by NIV Outcome**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 6% of smaller bbox (textA: "Per-Word Bands Stratified by N" / textB: "Within useful content (Y+P), p")

**Slide 55 — Joint Confidence + Beam-Agreement Band Rule**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 6% of smaller bbox (textA: "Joint Confidence + Beam-Agreem" / textB: "Production rule. Two axes: per")

**Slide 56 — Beam Agreement Adds Independent Signal**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 10% of smaller bbox (textA: "Beam Agreement Adds Independen" / textB: "At top1_conf >= 0.95 the softm")

**Slide 57 — Trust-Gate Operating Points (per-segment)**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 10% of smaller bbox (textA: "Trust-Gate Operating Points (p" / textB: "Per-segment trust gate based o")

**Slide 58 — N-best Aggregation: From One to All 20 Hypotheses (Mission 6)**
- [OVERLAP] Shapes 'TextBox 3' & 'TextBox 6' overlap by 16% of smaller bbox (textA: "Previously we displayed only t" / textB: "Recognizer Output Voting Error")

**Slide 59 — N-best Aggregation: v3 Judge Paired Tests**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 10% of smaller bbox (textA: "N-best Aggregation: v3 Judge P" / textB: "Opus 4.7 dual-conf prompt, bli")

**Slide 60 — Why MBR Won the Default-Display Slot**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 11% of smaller bbox (textA: "Why MBR Won the Default-Displa" / textB: "MBR wins on intra-rater reliab")

**Slide 61 — v1 vs v3 Judge: A Prompt-Design Lesson**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 13% of smaller bbox (textA: "v1 vs v3 Judge: A Prompt-Desig" / textB: "Same n-best methods. Same judg")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 11' overlap by 9% of smaller bbox (textA: "• Method-conf only in prompt
•" / textB: "LESSON: provide BOTH sides' co")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 11' overlap by 9% of smaller bbox (textA: "• Method-conf AND baseline_con" / textB: "LESSON: provide BOTH sides' co")

**Slide 62 — Demo: OK → Almost There → Hallucination**
- [NOTES] Body shows 56% but notes only mention [0] — possible mismatch.

**Slide 70 — Five Phases — From IS 2.5 to Target IS 3.3–3.7**
- [OVERLAP] Shapes 'TextBox 12' & 'TextBox 14' overlap by 25% of smaller bbox (textA: "Phase 5  Error Correction (GER" / textB: "Target: IS 3.3-3.7 (~80-85% Y+")

**Slide 71 — IS Improvement Roadmap — From 2.5 to 3.5**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 14% of smaller bbox (textA: "IS Improvement Roadmap — From " / textB: "Projected Intelligibility Scor")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 6% of smaller bbox (textA: "Current" / textB: "IS 2.547  •  62% useful")
- [OVERLAP] Shapes 'TextBox 9' & 'TextBox 10' overlap by 6% of smaller bbox (textA: "Phase 1–2" / textB: "IS ~2.65  •  ~65% useful")
- [OVERLAP] Shapes 'TextBox 13' & 'TextBox 14' overlap by 6% of smaller bbox (textA: "+ Phase 3" / textB: "IS ~3.05  •  ~73% useful")
- [OVERLAP] Shapes 'TextBox 17' & 'TextBox 18' overlap by 6% of smaller bbox (textA: "+ Phase 4–5" / textB: "IS ~3.50  •  ~82% useful")

**Slide 73 — LLM Upgrade: Why It Matters**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 14% of smaller bbox (textA: "LLM Upgrade: Why It Matters" / textB: "Llama-2 7B → Llama 3.1 8B")
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 8' overlap by 14% of smaller bbox (textA: "LLM Upgrade: Why It Matters" / textB: "Projected Impact")
- [OVERLAP] Shapes 'TextBox 23' & 'TextBox 25' overlap by 20% of smaller bbox (textA: "35–40%" / textB: "Strongest LLM lift: entity dis")

**Slide 75 — Arabic Pipeline: Replication Roadmap**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 5% of smaller bbox (textA: "Arabic Pipeline: Replication R" / textB: "What’s Needed & How We’ll Do I")
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 9' overlap by 14% of smaller bbox (textA: "Arabic Pipeline: Replication R" / textB: "Practical Timeline")
- [OVERLAP] Shapes 'TextBox 4' & 'TextBox 6' overlap by 9% of smaller bbox (textA: "• AV-HuBERT encoder (BOTTLENEC" / textB: "• Eval dataset (UNKNOWN)
• No ")
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 7' overlap by 9% of smaller bbox (textA: "• Arabic LLM backend
• Swap Ll" / textB: "• Training infrastructure
• AW")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 8' overlap by 9% of smaller bbox (textA: "• Eval dataset (UNKNOWN)
• No " / textB: "• RTL text & normalization
• R")
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 12' overlap by 15% of smaller bbox (textA: "• Training infrastructure
• AW" / textB: "Realistic estimate: 2–3 months")

**Slide 77 — Arabic Adaptation: What Changes**
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 80 — A1: Homophenes — The Lip-Reading Problem**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 5' overlap by 5% of smaller bbox (textA: "A1: Homophenes — The Lip-Readi" / textB: "Confusable word pairs (identic")

**Slide 81 — A3: IS Component Correlation**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 5% of smaller bbox (textA: "A3: IS Component Correlation" / textB: "PCA: 6 IS signals collapse int")
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 5' overlap by 5% of smaller bbox (textA: "A3: IS Component Correlation" / textB: "Cross-Config Stability (16 con")

**Slide 82 — Appendix: PCA Loadings on the 6 IS Signals**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 5% of smaller bbox (textA: "Appendix: PCA Loadings on the " / textB: "Kaiser criterion retains 2 com")

**Slide 84 — A4: LLM Salvage — Recoverable Segments**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 17% of smaller bbox (textA: "A4: LLM Salvage — Recoverable " / textB: "Key Numbers")
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 6' overlap by 14% of smaller bbox (textA: "A4: LLM Salvage — Recoverable " / textB: "6 Recovery Categories")

**Slide 85 — A5: LLM Salvage — Curated Examples**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 5% of smaller bbox (textA: "A5: LLM Salvage — Curated Exam" / textB: "One real example per recovery ")

**Slide 86 — A9: Context Evaluation — Transition Details**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 5% of smaller bbox (textA: "A9: Context Evaluation — Trans" / textB: "Blind → Context Transition Mat")
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 7' overlap by 5% of smaller bbox (textA: "A9: Context Evaluation — Trans" / textB: "Per-Topic Y+P Delta (Blind → C")

**Slide 87 — Appendix: McNemar Tests — N-Best Methods vs Baseline**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 9% of smaller bbox (textA: "Appendix: McNemar Tests — N-Be" / textB: "Paired McNemar tests on 5,988 ")
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 10% of smaller bbox (textA: "• mbr: +40 Y+P, p=0.00017 (hig" / textB: "Caveat: identical-text drift 1")

**Slide 88 — Two Environments: Development and Production**
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 3' overlap by 13% of smaller bbox (textA: "Two Environments: Development " / textB: "EC2 (Development)")
- [OVERLAP] Shapes 'TextBox 1' & 'TextBox 9' overlap by 13% of smaller bbox (textA: "Two Environments: Development " / textB: "Synchronization Challenge")

