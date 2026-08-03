# End-of-Training-Phase Project — Reusable Additivity Test for Quality Signals

**5-day project**  ·  **Author:** Yoad Oxman

---

## Goal

We're adding new quality signals to the pipeline — a pre-decode visual quality score, post-decode model confidence, possibly more. For each new signal we need to answer one question: **does it actually add value beyond what we already have, or are we already getting this information for free?**

Build the test that answers this — *and build it as a re-runnable procedure* that takes any model's outputs and any candidate signal and produces a clean answer. The same script then re-runs on the next fine-tune, the next checkpoint, and the Arabic model when it ships.

## Why it matters

- Without this test, we ship quality signals on intuition. We have no objective way to say *"yes, this new signal adds real information"* vs. *"this is redundant with what we already have."*
- Models change. Every retrain, every fine-tune, every new language extension can change the answer. A re-runnable procedure means we don't have to rebuild the test each time.
- The procedure becomes the template for evaluating **every** future quality signal we add — broader than just the pre-decode score.

## The work

The researcher designs the methodology, not just runs it:

- **Pick the comparison protocol.** Stratified train / held-out split, choice of comparison model (logistic regression is the sensible default at this scale; more is overkill), choice of metrics.
- **Build it as a single script.** Inputs: a model's outputs, the AI-judge labels, the candidate signal. Output: the additivity result — a likelihood-ratio test p-value and an AUC lift. No manual rebuilding step.
- **Verify reproducibility.** Run on the current pipeline. Run again on a second checkpoint snapshot. Confirm the script handles both cleanly.
- **Document the procedure** so any team member can re-run it on a new signal or a new model without help.

The test runs on the same stratified dataset built by the video-quality project (existing 1,497 labeled clips plus AVSpeech augmentation).

## What the researcher learns

- How to evaluate whether a new signal adds value beyond an existing baseline — the *"does this actually help, or are we already getting it for free?"* question that every new ML feature has to answer.
- How to build an evaluation as a reusable script, not a one-shot notebook — the pattern that lets a team re-ask the same question every time the model changes.
- Statistical model comparison in practice — likelihood-ratio tests, AUC lift, held-out validation.

---

## Schedule (5 days, balanced)

| Day | Task |
|---|---|
| 1 | Read the repo. Read the video-quality project's score module and outputs. Understand the data formats. |
| 2 | Design the test methodology. Build the stratified train / held-out split. Sanity-check on toy data. |
| 3 | Implement the comparison: fit baseline-signal-only and combined-signal models. Implement the likelihood-ratio test and AUC-lift calculation. |
| 4 | Run on the current model. Run again on a second checkpoint snapshot. Debug, harden the script. |
| 5 | Document the procedure (a short doc + a working example). Short write-up in `docs/evaluation/`. |
