# Argos VSP — PowerPoint Fix Manifest

Categorized fix list for slide-writing phase. 
Pulled from BLOCKER/MAJOR/MINOR issues across audited decks.

## Argos_VSP_AFTER_AMOSI_May2026.pptx

### BLOCKER: none

### MAJOR (43)

**Slide 9 — 8-Stage Automated Pipeline**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 11', text "▶…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 16', text "▼…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 20', text "evaluation only…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 24', text "▼…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 28', text "▼…")
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 30', text "Existed in academic repo…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 47', text "Preprocessing…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 49', text "Feature Extraction…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 51', text "LLM Inference…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 53', text "Output…")
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 54', text "auto_avsr  ·  av_hubert  ·  VSP-LLM…")
- [OVERLAP] Shapes 'TextBox 20' & 'TextBox 30' overlap by 86% of smaller bbox (textA: "evaluation only" / textB: "Existed in academic repo")
- [OCCLUSION] Text shape 'TextBox 20' ("evaluation only…") is 86% covered by later shape(s).

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

**Slide 59 — N-best Aggregation: From One to All 20 Hypotheses (Mission 6)**
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 13', text "ROVER: Fiscus (1997), NIST  |  MBR Decod…")

**Slide 60 — N-best Aggregation: v3 Judge Paired Tests**
- [STYLE] Body font 10pt below 12pt readability floor (shape 'TextBox 7', text "v3 dual-conf judge   /   Opus 4.7   /   …")

**Slide 64 — Demo - Obama Trust Tier**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "Research observation: 27/29 per-word ban…")

**Slide 65 — Demo - Obama: TRUST under conf-only fallback (no n-best sidecar - partial recovery still narrated)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "Research observation: most words green; …")

**Slide 66 — Demo - INSPECT (closest to STRIP in the Obama set; lowest mean_prob = 0.799)**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "Research observation: the model fabricat…")

**Slide 67 — Demo - Strip: entity swap auto-flagged**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "Research observation: the entity-swap to…")

**Slide 68 — Demo - Salvage: technical vocabulary drift**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "Research observation: argument structure…")

**Slide 71 — Five Phases — From IS 2.5 to Target IS 3.3–3.7**
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 15', text "References: ROVER (Fiscus 1997)  |  GER …")

**Slide 72 — IS Improvement Roadmap — From 2.5 to 3.5**
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 11', text "+0.10  |  Fixes: Accum (52) + Details (7…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 15', text "+0.50  |  Fixes: Halluc (108) + Wrong To…")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 19', text "+0.95  |  Fixes: all remaining via data …")
- [STYLE] Body font 11pt below 12pt readability floor (shape 'TextBox 20', text "Conversion: ~0.033 IS per pp WER (empiri…")

**Slide 73 — Stronger LLM + Smart Prompts = Force Multiplier**
- [STYLE] Body font 8pt below 12pt readability floor (shape 'TextBox 12', text "GER: Chen et al. (2024), ICASSP  |  Scal…")

**Slide 81 — A1: Homophenes — The Lip-Reading Problem**
- [STYLE] Body font 9pt below 12pt readability floor (shape 'TextBox 9', text "A1…")

**Slide 88 — Appendix: McNemar Tests — N-Best Methods vs Baseline**
- [OVERLAP] Shapes 'TextBox 6' & 'TextBox 7' overlap by 50% of smaller bbox (textA: "• hyp_mbr: +40 net Y+P wins, p" / textB: "Caveat: identical-text drift v")

### MINOR (22)

**Slide 8 — How It Works: Data Flow**
- [NOTES] Notes cite 4 numbers but lack any source reference (.md/.csv path).

**Slide 9 — 8-Stage Automated Pipeline**
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 20' overlap by 25% of smaller bbox (textA: "Whispertranscription" / textB: "evaluation only")
- [OVERLAP] Shapes 'TextBox 19' & 'TextBox 30' overlap by 5% of smaller bbox (textA: "Whispertranscription" / textB: "Existed in academic repo")

**Slide 10 — The Benchmark: Paper vs Reality**
- [OVERLAP] Shapes 'TextBox 5' & 'TextBox 9' overlap by 18% of smaller bbox (textA: "• LRS3 benchmark: curated TED " / textB: "Different dataset, fundamental")

**Slide 25 — Where IS and the Judge Disagree**
- [NOTES] Body shows 71% but notes only mention [0, 1, 98, 100, 111] — possible mismatch.

**Slide 26 — Context Exposes Hidden Failures**
- [OVERLAP] Shapes 'TextBox 10' & 'TextBox 11' overlap by 6% of smaller bbox (textA: "REF: "...because I'm a lover o" / textB: "One word reverses the meaning.")
- [NOTES] Body shows 10% but notes only mention [80] — possible mismatch.

**Slide 28 — IS Signals: Word Accuracy & Length**
- [OVERLAP] Shapes 'TextBox 7' & 'TextBox 8' overlap by 5% of smaller bbox (textA: "Standard Word Error Rate (subs" / textB: "▸ Treats all words equally — e")

**Slide 37 — Where the System Works: Oracle vs Realistic**
- [NOTES] Body shows 19% but notes only mention [5, 23, 30, 61, 65, 68, 71] — possible mismatch.

**Slide 42 — Failure Modes: Real Examples**
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.
- [NOTES] Body shows 97% but notes only mention [13, 18, 44, 100] — possible mismatch.

**Slide 48 — Confidence Scoring (shipped April 30 2026) — Surface the Good 65%**
- [NOTES] Body shows 85% but notes only mention [5, 20, 30, 60, 65] — possible mismatch.

**Slide 49 — Per-Word Confidence Bands - Distribution**
- [NOTES] Notes reference 'next/previous slide' — fragile if reordered.

**Slide 51 — Green Reliability Depends on Segment Quality**
- [NOTES] Body shows 50% but notes only mention [18, 21, 41, 86, 91, 96] — possible mismatch.

**Slide 64 — Demo - Obama Trust Tier**
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 9' overlap by 8% of smaller bbox (textA: "(see speaker notes; Obama bin " / textB: "HYPOTHESIS  (per-word band obs")

**Slide 65 — Demo - Obama: TRUST under conf-only fallback (no n-best sidecar - partial recovery still narrated)**
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 9' overlap by 8% of smaller bbox (textA: "(see speaker notes; Obama bin " / textB: "HYPOTHESIS  (per-word band obs")

**Slide 66 — Demo - INSPECT (closest to STRIP in the Obama set; lowest mean_prob = 0.799)**
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 9' overlap by 8% of smaller bbox (textA: "heroic citizens saved even mor" / textB: "HYPOTHESIS  (per-word band obs")

**Slide 67 — Demo - Strip: entity swap auto-flagged**
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 9' overlap by 8% of smaller bbox (textA: "market research firm bernreute" / textB: "HYPOTHESIS  (per-word band obs")

**Slide 68 — Demo - Salvage: technical vocabulary drift**
- [OVERLAP] Shapes 'TextBox 8' & 'TextBox 9' overlap by 8% of smaller bbox (textA: "we need a radically different " / textB: "HYPOTHESIS  (per-word band obs")

**Slide 71 — Five Phases — From IS 2.5 to Target IS 3.3–3.7**
- [NOTES] Body shows 13% but notes only mention [8, 26, 38, 62, 85] — possible mismatch.

**Slide 79 — Key Takeaways**
- [NOTES] Body shows 68% but notes only mention [61, 64, 71] — possible mismatch.

**Slide 84 — Appendix: Human-IS Path B (Pre-Study Estimates)**
- [LAYOUT] Shape 'TextBox 9' within 0.1in of slide edge (left=0.60, top=6.90, right_gap=0.60, bot_gap=0.10)

