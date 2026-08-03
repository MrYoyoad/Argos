# End-of-Training-Phase Project — Pre-Decode Video Quality Score

**5-day project**  ·  **Author:** Yoad Oxman

---

## Goal

Build a fast, lightweight tool that looks at a silent video clip and outputs a 0-to-1 score: *"this clip is likely readable"* vs. *"this clip is hopeless."* It runs **before** our main lip-reading model, in milliseconds, using nothing but classical computer vision — no GPU, no neural network. Today the system happily spends 30 seconds of GPU time on clips it has no chance of decoding.

## Why it matters

- **Arabic training-data filter.** We're building an Arabic version of the system. No public Arabic lip-reading dataset exists, so we'll be scraping YouTube at 10,000+ scale. An automated quality gate is the only realistic way to reject bad clips before they pollute the training set.
- **Measuring whether a new model or fine-tune actually helped, and where.** Today when we fine-tune or swap the LLM, we get a single average accuracy number and have to guess whether the change helped. With a per-clip quality score, we can stratify the evaluation set into quality tiers (high / medium / low footage) and measure the gain — or regression — *per tier*. That tells us things the average can't: *"the fine-tune lifted medium-quality footage by 8 points but didn't move the high-quality tier"* or *"the new LLM is better on low-quality clips but worse on high"*. The same stratified view also lets us tell prospective clients whether their typical footage falls in a tier we currently work well on.
- **Concrete filming guidance for clients.** Once we know which visual properties matter and by how much, we can tell clients up front what kind of shooting works (frontal angles, even lighting, minimum mouth-pixel width) and what doesn't (sharp side profiles, harsh backlight, hand or microphone near the mouth). Today we can only handwave; the ablation gives us actual numbers to recommend.

## The work

Two parts, run on a dataset the researcher builds — the existing 1,497 labeled clips plus stratified samples plucked from our AVSpeech S3 archive to fill gaps in the parameter space:

- **(A) Ablation.** Compute candidate visual features — head pose, lip-region brightness / contrast / sharpness, mouth visibility, motion blur, resolution, etc. (the list is open-ended; the researcher decides what to test). Rank them by how strongly they predict the per-clip quality signal.
- **(B) Score.** Combine the top features into a single 0-to-1 score with a logistic regression. Pick reject and warn thresholds from the data. Ship as an optional pipeline stage behind a feature flag.

## What the researcher learns

- How to design and run a real ablation — picking the variables, *shaping the dataset so every variable has enough coverage to be measured*, ranking by effect size.
- Classical computer vision for video — head pose from landmarks, sharpness and brightness metrics, optical flow, lip-region analysis.
- How to integrate a new stage into a multi-stage production pipeline, behind a feature flag, the way the rest of the system already works.

---

## Schedule (5 days, balanced)

| Day | Task |
|---|---|
| 1 | Read the repo. Run the pipeline end-to-end on one small video. Set up the feature-extraction skeleton. Implement the first 3–4 features. |
| 2 | Implement the remaining candidate features. Compute all features on the existing 1,497 clips. Plot parameter-space coverage and propose the stratification scheme — review with the team. |
| 3 | Pull AVSpeech clips from S3. Pluck stratified samples from under-represented regions. Run them through the pipeline offline. Compute features on the augmented set. |
| 4 | Correlation and ranking analysis on the full stratified dataset. Fit the score. Pick the reject and warn thresholds. |
| 5 | Wire the score in as an optional pipeline stage with tests. Short write-up in `docs/evaluation/`. |
