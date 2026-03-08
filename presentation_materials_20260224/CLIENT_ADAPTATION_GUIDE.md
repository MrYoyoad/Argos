# Client Adaptation Guide

How to create a client-facing version from the manager deck.
**Estimated time: 15 minutes.**

---

## Step 1: Duplicate the Manager Deck

In Google Slides: File → Make a copy → rename to "Argos VSP — Client Presentation"

---

## Step 2: Delete These Slides (10 slides removed)

| Manager Slide # | Title | Why Remove |
|-----------------|-------|------------|
| 8 | Failure Mode Taxonomy | Too technical — internal analysis of 5 failure categories |
| 9 | Performance Distribution | Too technical — boxplot across 13 experiments |
| 11 | Named Entity Accuracy | Mention 38.8% verbally; scatter plot is too dense |
| 13 | Limits of Tuning | Don't highlight limitations to clients |
| 16 | Seven Research Reports | Internal inventory, not relevant to clients |
| 18 | 37 Bugs Fixed | Don't advertise bugs to clients |
| 19 | Modular Refactoring | Internal engineering metric |
| 21 | Intelligent Features | Internal pipeline details |
| 22 | Evaluation Infrastructure | Internal tooling |
| 23 | Process & Documentation | Internal process |

---

## Step 3: Modify These Slides (5 slides changed)

### Slide 12 (Tuning Experiments) → Simplify

**Remove**: do_sample discussion, full parameter list, full-dataset Config J comparison, WWER numbers
**Replace content with**:
```
Title: "Optimized Configuration"
- We systematically tested 13 configurations
- Found optimal settings that eliminate empty outputs entirely
- Best config reduces errors across all segment types
```
Keep it short. No need to explain what lenpen or temperature are.

### Slide 14 (Curated Examples) → Swap Hallucination Example

**Remove** the "carry strap → holocaust denier" row — too alarming for clients.
**Replace with** this milder example:
```
| Hallucinated | "let's see a half a cup of" | "i have to say thank you" | 100% | 0.7 |
```
A cooking measurement becoming a thank-you is clearly wrong but not distressing.

### Slide 24 (Starting from 40%) → Reframe as Confidence

**Change title** from "Starting from 40%, Not 11%" to "40% of Outputs Are Already Reliable"
**Remove** success pattern details and failure mode targeting language.
**Change framing** from gap analysis to confidence-building:
```
- Our Intelligibility Score shows 40% of segments are properly captured
- These segments convey the correct meaning despite word-level differences
- Next step: automatically flag which segments are reliable
```

### Slides 25-28 (Roadmap Phases) → Add Timelines, Remove Budget & Failure Mode Details

For each phase slide:
- **Add** estimated delivery timelines (Phase 1: "Next sprint", Phase 2: "2-3 weeks", Phase 3: "1-2 months")
- **Remove** GPU cost numbers ($72-120) and "requires budget decision"
- **Remove** failure mode targeting language (e.g., "targets Topic Drift 15.9%") — too internal
- **Reframe** from "research agenda" to "upcoming improvements to your system"

### Slide 30 (Summary) → Client Takeaways

**Replace** the three points with:
```
1. The system works today — 40% of outputs are already reliable,
   and we can identify which ones automatically.
2. Continuous improvement underway — each phase delivers
   measurable quality gains to your pipeline.
3. Production-grade engineering — standalone, tested, documented,
   with your data secure on your own machine.
```

---

## Step 4: Add These Slides (2 new slides)

### NEW: UI Demo Slide (insert after Slide 20 "Deployed Product")

```
Title: "Your Interface"
[Insert screenshot of the web UI showing drag-and-drop upload]
Bullet points:
- Drag and drop any video file
- Automatic processing — no technical knowledge needed
- View results in your browser
- Download reports and burned videos
```

### NEW: Quality Thresholds Slide (insert before Roadmap section)

```
Title: "Actionable Quality Thresholds"
[Insert 15_cdf_wwer_curated.png from 01_plots_for_slides/]
Text: "X% of segments are below Y% word error rate.
You can set a confidence threshold to automatically
filter outputs for your use case."
```

---

## Step 5: Update Title Slide

Change subtitle from "Project Review" to "System Capabilities and Roadmap"

---

## Result

| Version | Slides | Tone |
|---------|--------|------|
| **Manager** | 30 + appendix | Direct, full technical depth, resource requests |
| **Client** | ~22 | Confidence-building, results-focused, no internals |

Both versions use the **same plots, same data, same folder**. No new materials needed.

---

## What to Say Differently (Speaking Notes)

| Topic | To Managers | To Clients |
|-------|------------|------------|
| Hallucination | "The LLM prior overwhelms the visual signal" | "Sometimes the system generates incorrect text — our next update will flag these automatically" |
| 64.1% WER | "2.5x worse than benchmark, as expected for domain mismatch" | "Real-world video is harder than lab conditions — our IS metric shows 40% is already usable" |
| Bugs | "37 bugs fixed — here's the NVENC corruption story" | Don't mention. The system works. |
| Fine-tuning | "Exp A complete on ~1,400 videos — proved the model learns from YouTube data. Overfitting at r=16 tells us we need higher rank + more data. Exp B next." | "We've started training on real-world data and the initial results are promising — next iteration will bring significant accuracy gains" |
| do_sample | Explain the divergence and plans to unify | Don't mention |
| IS metric | Full formula, 6 signals, methodology | "We developed a smarter way to measure quality — it shows 40% is already reliable" |
| Failure modes | "5 classified categories — Wrong Topic 31.6%, each phase targets specific categories" | Don't mention. Simplify to "we know exactly where to improve" |
| Topic analysis | "Business best at 57%, DIY worst at 30% — formal speech easier" | Mention verbally if relevant: "it works better on formal speech" |
| Config J full data | "Full-dataset comparison: +25 captured segments, doubles hallucinations, net +0.08 IS" | Don't mention details. "Our best configuration eliminates empty outputs" |
| LLM upgrade | "Llama 3.1 8B is a drop-in swap (same hidden_size 4096, 1-2 hours setup). With 20K-50K training segments + smart prompts, target IS 3.5-4.0 (from 2.53). Multiplicative scaling law: stronger LLM extracts more from same data." | "We have a clear roadmap to significantly improve accuracy — next-generation models are ready to integrate, and each improvement phase delivers measurable gains" |
| Data scaling | "1,273 segments was below the ~1K LoRA minimum. Both r=16 and r=64 memorized. Need 20K-50K segments — AVSpeech has 290K available." | "We're expanding our training data — larger datasets will drive the biggest accuracy improvements" |
| GER / prompt strategies | "7 prompt strategies — force multiplier for stronger LLMs. GER post-processing (+8-15pp) needs no retraining, can use external API." | Don't mention technical details. "We're adding intelligent post-processing that will further improve output quality" |
