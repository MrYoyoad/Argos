# Q&A Cheat Sheet — One Page

**The closing line — say this if nothing else lands:**
> *"We are not asking you to trust the model. We give your reviewers the model's output, its uncertainty, its failure flags, and the evidence needed to decide what deserves human attention."*

## Three anchor numbers (the headline)
**62% review-useful · 23% clearly conveyed · 1 in 5 auto-flagged.** Full 1,497-segment unfiltered real-world baseline. Never say "62% accurate" — say "62% review-useful."

## Three lines to land
1. **"Confidence is triage, not truth."** Green = review faster. Red = review first.
2. **"A wrong fluent transcript is worse than an empty one. Our value is not that failure never happens — it's that failure is surfaced."**
3. **"The model is a high-quality first draft with calibrated uncertainty. The human triages."**

## Top Q&A

| Q | A |
|---|---|
| **How accurate?** | "Depends on clip quality. On 1,497 real-world segments, ~62% review-useful, ~23% clearly conveyed. I won't promise a number on your footage before we run your clips." |
| **Can we trust the transcript?** | "Not blindly — that's the point. Word + segment confidence + hallucination flags. Trust high-confidence faster, review yellow/red, exclude low-confidence from auto-conclusions." |
| **What about hallucinations?** | "Core failure mode, not edge case. Token confidence + length anomalies flag them. The Obama 'Rwanda's genocide' case: caught at prob 0.02. *Surfaced, not hidden.*" |
| **Was the 'reviewer' a human?** | "No — blind frontier-LLM evaluator at scale. Right next step is human validation on your pilot clips. Say 'blind LLM evaluator,' never 'expert reviewer.'" |
| **Two people talking?** | "Today: one centered speaker. Path: speaker-specific cropping, decode each independently. Engineering, not research. ~3 weeks to ablation on your data." |
| **Evidence use?** | "Only with human review and confidence metadata. Evidence-discovery and review-acceleration tool — not standalone evidence." |
| **Cherry-picked examples?** | "Curated for teaching range; the headline numbers are full 1,497-segment, not selected. We can run your clips next." |
| **Is green always correct?** | "No. 92.8% reliable in high-quality segments, 21.8% in low. UI policy: ≥0.82 full coloring, 0.65–0.82 amber banner, <0.65 strip. *The UI removes coloring where it would lie.*" |
| **What's different vs other lip-reading work?** | "Real-world end-to-end pipeline (not LRS3-only); uncertainty surfaced at every level; deployable infrastructure cloud-or-on-prem — not a research codebase." |
| **Human IS comparison?** | "Lay ~0.9, deaf adult ~2.7, forensic expert ~3.0, model alone 2.52, **reviewer + model ~3.8**. Alone we tie a deaf adult; combined system beats the expert." |
| **vs 5-expert team?** | "Same quality (~3.8 IS), **50–100× cheaper** ($3–6/min vs $200–400/min), structurally more reproducible. One reviewer + Argos, not five experts." |
| **Could it be misused?** | "Yes — that's why we ship it as reviewable evidence stream, not autonomous truth. Won't deploy without human verification. Deal-breaker for us." |
| **What's a pilot?** | "3–5 canonical clips from your domain, two weeks, full pipeline + confidence-scored report, your reviewer evaluates fit. No infra ask up front." |
| **Why not Whisper / Google STT?** | "Audio-only. Returns nothing or hallucinates from noise when audio is missing or unreliable. Different problem — we operate when audio is gone or unreliable." |
| **Isn't this just AV-HuBERT / VSP-LLM (open source)?** | "The research IP is public; the productionization isn't, and that's most of the work. End-to-end pipeline, calibrated confidence, hallucination flags, deployable on-prem — none of that ships in a GitHub repo." |
| **What about Read Their Lips / LipReadPro?** | "Read Their Lips is a 2-person showcase for a Mac silent-voice-command app, 3-min clip cap, fluent hallucinations on public test clips. LipReadPro claims '95% accuracy' — published SOTA on curated benchmarks is ~27% WER; the claim is marketing, not measurement. Neither surfaces uncertainty." |
| **What do forensic experts say about AI lip-reading?** | "121 Captions (UK forensic): 'Technology doesn't do the lip reading — it provides a clearer canvas for the human expert.' They reject AI not because recognition is bad but because it can't tell you when to trust it. That's the seam our confidence layer fills." |

## Don't say → say instead
- "62% accurate" → **"62% review-useful"**
- "Expert reviewer" → **"blind LLM evaluator"**
- "Near-zero hallucination risk" → **"hallucinations flagged before review"**
- "The system knows when it's right" → **"it tells you where to look first"**
- "Replaces human review" → **"routes review to the right places"**
- "Replaces 5 experts" → **"replaces 5 experts with one reviewer + the model"**
- "State of the art" → don't claim it
- "Model beats human lip readers" → **"combined system beats unaided humans"**

## Pull-only (don't volunteer)
- **Beam aggregation**: shipped May 1, gated by env var, full 1,497 eval running. WER 59→57% on 107-segment validation; voting method has best calibration error of any method measured.
- **Runtime confidence**: per-token softmax + length-anomaly check. **IS is dev-time only — needs reference text. Never claim IS at runtime.**
