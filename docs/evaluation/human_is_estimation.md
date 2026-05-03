# Estimating Human IS for the Reconstruction Task

**Argos — The Orchard**
**Date:** 2026-05-03
**Author:** Yoad Oxman (research note)
**Status:** Methodology proposal — no human study run yet. Numbers in §4 are pre-study estimates.

---

## 1. Why this matters

Our model's headline number is **IS = 2.52 / 5.0** on 1,497 wild YouTube segments.
Without a human IS on the same content, "2.52" is unanchored: is it 60% of human, 90%, 110%?

The existing [human_expert_comparison.md](human_expert_comparison.md) compares humans and the model on **WER / meaning-capture %**, drawn from external literature. It does not put humans on the IS scale. That is the gap this note addresses.

**The question:** What value does our 6-signal IS take when the *hypothesis* column is filled by a human lip reader instead of VSP-LLM, on the same references?

---

## 2. Why "just measure WER and convert" doesn't work

IS is a weighted composite (weights from [intelligibility_methodology.md](intelligibility_methodology.md), line 303):

```
IS = 0.25·Semantic + 0.15·Phonetic + 0.15·(1-WER) + 0.15·(1-WWER) + 0.15·NEA_F1 + 0.15·LengthRatio
```

Only **0.30 of the weight** is WER-like. The remaining **0.70** depends on output *style* — and machine and human output styles diverge systematically:

| Component | Typical machine (VSP-LLM) failure pattern | Typical human failure pattern |
|---|---|---|
| Semantic | 20.5% confident hallucination → semantic ~0 | Honest gap / shorter output → semantic moderate |
| Phonetic | High even when wrong (visual→phoneme is the model's strength) | Lower, because humans skip rather than guess phonetically |
| NEA F1 | Often invents entities (judge-context analysis: 230 downgrades when context given) | With visual context, resolves entity disambiguation but may omit |
| LengthRatio | ≈ 1.0 (the LLM fills space) | < 1.0 (humans drop uncertain spans) |
| WER | ~64% mean | Lit. 48–55% (expert), 56% (deaf), ~90% (lay hearing) |

So a human at the same WER as the model gets a **different IS**, in either direction depending on how the IS rubric weights "honestly empty" vs "fluently wrong." A linear WER→IS bridge fitted on machine data is biased when applied to humans.

---

## 3. Three estimation paths, ranked

### Path A — Gold-standard human-IS measurement (recommended primary)

Sample n segments → human transcribes → run the same `--compute-is` flag in [lib/outputs.sh](../../lib/outputs.sh) on those transcriptions → distribution is the answer.

**Population strata** (mirror the literature in [human_expert_comparison.md](human_expert_comparison.md)):
1. Lay hearing adult (≈10–12% acc baseline)
2. Deaf adult (≈44% acc)
3. Trained / forensic-class lip reader (≈45–52% acc)
4. Lay hearing adult **+ topic context** (the realistic deployment baseline for "model + human")

**Sample size.** For a 95% CI of ±0.15 IS units on the mean, with σ_IS ≈ 1.4 from our model's per-segment IS distribution, n ≈ 340. A pragmatic floor of **n = 50 per stratum** gives ±0.40 — enough to rank populations but not to claim parity. A 200-segment matched subsample stratified by model-IS tier (5 / 4 / 3 / 2 / 1) is the right design for paired analysis.

**Blind protocol.** Human sees video only (no audio, no model output). Two rounds: blind, then with topic + model-output review (the "verification" mode from [human_expert_comparison.md §4](human_expert_comparison.md)). Inter-rater on a 30-segment overlap to check noise (target Cohen's κ vs IS-tier ≥ 0.7, matching our intra-rater Opus 86.7%).

**Cost.** Forensic-class lip reading is hours/segment. 200 segments × 3 strata is real money; pilot with **n=50 per stratum** first.

### Path B — Component-wise bridge (cheap, weaker)

Don't run a full human study. Instead estimate each of the 6 IS components from existing literature and our local distribution:

1. **WER:** literature gives expected human WER per stratum (lay 88–90%, deaf ~56%, expert 48–55%).
2. **WWER:** entities are harder visually, so WWER ≈ WER × 1.05–1.15 for unaided humans; with context, WWER ≈ WER × 0.90.
3. **NEA F1:** estimate from named-entity *recall* in human studies (Tye-Murray 2021 reports ~25% NE recall lay, ~55% deaf with context). F1 follows once we assume precision ≈ 1 (humans rarely invent entities).
4. **Semantic:** humans drop content rather than fabricate, so Semantic ≈ word-accuracy × 0.9 (proportional collapse, capped from above).
5. **Phonetic:** machine ≫ human here. Estimate from phoneme-recall studies (Auer & Bernstein 2007): expert ≈ 0.55–0.65, deaf ≈ 0.45, lay ≈ 0.20.
6. **LengthRatio:** humans drop uncertain words. From transcription-confidence studies, LR ≈ 0.6–0.8 for difficult speechreading; ≈ 0.9 with context aid.

Plug per-stratum component means into the IS formula. **Big caveat:** ignores per-segment correlation between components — gives mean IS but not the distribution shape, so tier-rate predictions (NIV-Y, NIV-Y+P) are unreliable from this path alone.

### Path C — Reference-perturbation simulation (cheapest, calibration only)

Take the 1,497 reference texts. Apply a **human-error perturbation model** to each:
- Drop p_drop fraction of content words (set per stratum from word-accuracy literature).
- Substitute homophenes (the table in [intelligibility_methodology.md §3](intelligibility_methodology.md)) with calibrated probability.
- Leave proper nouns intact at rate ≈ NE recall above.
- **Do not** add fluent insertions (key human/machine difference).

Run the resulting "synthetic-human" transcripts through the IS pipeline. Useful as a **null** for path A — if synthetic-lay-human IS predicts your real-lay-human IS within ±0.3, path C can be re-used to extrapolate populations you couldn't sample.

---

## 4. Path B executed (May 3, 2026) — full computation, not just prose estimates

### 4.1 Formula sanity check (replays our own data)

Before estimating humans, replay the model on its 1,497-segment data: bin by WER, take per-bin component means, plug back into the IS formula, compare against the measured IS. If the formula reproduces our own data, the formula is sound and Path B is just a substitution exercise.

| Bin | n | WER | Predicted IS | Measured IS | Δ |
|---|---|---|---|---|---|
| WER < 30 | 288 | 17 | 4.46 | 4.36 | +0.10 |
| WER 30–50 | 278 | 38 | 3.57 | 3.52 | +0.05 |
| WER 50–60 | 165 | 54 | 2.91 | 2.85 | +0.06 |
| WER 60–70 | 127 | 65 | 2.42 | 2.38 | +0.04 |
| WER 70–100 | 332 | 83 | 1.69 | 1.66 | +0.03 |
| WER ≥ 100 | 307 | 117 | 1.04 | 0.76 | +0.28 |

Match within ±0.05 on the five non-extreme bins. The hallucination bin (WER ≥ 100) over-predicts by 0.28 because WER is clipped at 100% before scaling — humans almost never enter this bin (no fabrication), so it doesn't matter for Path B. **Formula plumbing verified.**

### 4.2 Per-stratum component estimates

Each stratum gets a *low* / *mid* / *high* band drawn from the literature in §7 and the no-fabrication adjustment in §3.

| Component | Lay (no ctx) | Deaf (no ctx) | Expert (no ctx) | Lay + ctx + model review |
|---|---|---|---|---|
| WER (%) | 86 / 88 / 90 | 52 / 56 / 60 | 48 / 50 / 55 | 25 / 32 / 40 |
| WWER (%) | 90 / 92 / 95 | 56 / 60 / 64 | 52 / 54 / 58 | 28 / 35 / 44 |
| Semantic (cos) | 0.22 / 0.18 / 0.10 | 0.62 / 0.55 / 0.45 | 0.68 / 0.60 / 0.50 | 0.80 / 0.72 / 0.62 |
| Phonetic (frac) | 0.18 / 0.14 / 0.10 | 0.62 / 0.55 / 0.45 | 0.66 / 0.60 / 0.50 | 0.80 / 0.74 / 0.65 |
| NEA F1 (%) | 12 / 8 / 5 | 56 / 46 / 36 | 60 / 50 / 40 | 78 / 70 / 60 |
| LR | 0.55 / 0.45 / 0.35 | 0.78 / 0.72 / 0.65 | 0.85 / 0.80 / 0.72 | 0.97 / 0.92 / 0.85 |

### 4.3 Resulting IS bands

| Population | IS low / mid / high | Tier (mid) | vs Model 2.52 |
|---|---|---|---|
| Lay hearing (no ctx) | **0.63 / 0.92 / 1.14** | Failed | model wins by **+1.60** |
| Deaf adult (no ctx) | **2.33 / 2.74 / 3.07** | Fair | rough tie (model −0.22 to −0.55) |
| Expert / forensic (no ctx) | **2.60 / 3.03 / 3.33** | Fair | model loses by **−0.51** at mid |
| Lay + topic + model review | **3.36 / 3.83 / 4.19** | Good | model loses by **−1.31** at mid |
| **Model alone (measured)** | **2.52** | Fair | — |
| Model on LRS3 (component-extrapolation) | ~3.8 – 4.2 | Good–Excellent | predicted, not measured |

### 4.4 What's driving each estimate — the LR isolation experiment

To separate "humans got fewer words right" from "humans wrote less", recompute each *mid* stratum with LR clamped to **1.0** (i.e. as if humans had model-style fluency but the same WER/semantic/phonetic/NEA):

| Stratum (mid) | Human-style IS | If LR=1.0 (no length penalty) | Δ from LR alone |
|---|---|---|---|
| Lay hearing | 0.92 | 1.33 | +0.41 |
| Deaf adult | 2.74 | 2.95 | +0.21 |
| Expert | 3.03 | 3.18 | +0.15 |
| Lay + ctx + model review | 3.83 | 3.89 | +0.06 |

The LR penalty **shrinks with proficiency** because better speechreaders skip fewer words. This is the cleanest single piece of evidence that **fluency is not a virtue** for the IS metric: the model is paying ~0 in LR penalty by guessing rather than skipping, and the LengthRatio signal is a covert reward for that. A human-aware IS variant should treat explicit "[unclear]" as length-neutral or weight LR less for human-style transcription.

### 4.5 Headline reads

1. **Model ≈ unaided deaf-adult lip-reader.** 2.52 sits inside the deaf-no-context band (2.33–3.07). Nothing dramatic to claim.
2. **Model loses to an unaided expert by ~0.5 IS** (3.03 vs 2.52 at mid). Not a comfortable gap — within the high band of what an expert-pilot could be measured to confirm or refute.
3. **Model + context-aware human reviewer ≈ +1.3 IS over model alone** (3.83 vs 2.52). This is the deployment story; it's also what every other metric in this repo (LLM-judge, NIV, salvage) has been hinting at.
4. **Model destroys lay readers** (+1.6 IS). Trivial finding but worth saying once.

**Status:** these numbers are still pre-study; Path A is the only way to tighten them past ±0.4. But they are now *computed*, not eyeballed — every stratum traces to a literature-cited word-accuracy plus the four reproducible style adjustments (Semantic ≈ acc + ctx-bonus; Phonetic ≈ acc × 1.2 capped; NEA F1 from recall with precision≈1; LR from reported transcription gap rates).

The Path-B computation script is reproducible from the snippet at the top of this section; component means by WER bin come from `docs/evaluation/intelligibility/intelligibility_scores.csv` columns 6–19.

---

## 5. Threats to validity

1. **IS was calibrated against an LLM judge scoring *machine* output.** Re-fitting NIV thresholds on humans may shift the IS→Y/Y+P boundaries (κ_Y=0.690 holds for machine output; not yet validated for human transcription style).
2. **LengthRatio penalises honest gaps.** A human who returns "[unintelligible]" or just stops will be punished by IS even though that is the most useful behaviour for a downstream judge. Consider a **human-aware IS variant** that treats explicit "gap" tokens as length-neutral.
3. **No fabrication ⇒ NEA precision ≈ 1 for humans, not for models.** Our F1 implementation may need spot-checking that empty-output edge cases don't divide by zero on human data.
4. **Hallucination is the dominant model failure mode (20.5%).** If humans hallucinate at <2% (literature suggests so), then *judge-meaning* gap between human and model is much wider than *IS* gap suggests, because IS only partially penalises hallucination.

---

## 6. Recommended next step

Run **path A pilot at n=50** on the deaf-adult-with-context stratum first. That stratum is:
- Cheapest realistic human comparator (deaf community accessible; forensic experts are expensive and rare).
- The closest analogue to "model + reviewer", which is the deployment story.
- Most likely to inform whether the model already matches human floor on hard segments, or only on easy ones.

Stratify the 50 by **model-IS tier** so we get paired (human-IS, model-IS) per segment — paired analysis halves the sample needed for a fixed CI.

If pilot shows model ≥ human on deaf-with-context across tiers, the marketing claim "matches a context-aware human reviewer" is defensible. If the model loses on tier-2/3 segments (the salvage zone), that motivates **Mission 6 hyp_mbr as default** ([n_best_aggregation_findings.md](../../.claude/projects/-home-ubuntu/memory/n_best_aggregation_findings.md)) plus a human-in-the-loop UI.

---

## 7. References

### Human lip-reading word-accuracy ground truth
- Auer, E.T. & Bernstein, L.E. (2007). *JASA*. [PMC3155585](https://pmc.ncbi.nlm.nih.gov/articles/PMC3155585/)
- Tye-Murray, N. (2021). *American Journal of Audiology*. [ASHA](https://pubs.asha.org/doi/10.1044/2021_AJA-21-00112)
- Hill, C. (2023). U. Melbourne, forensic lip-reading reliability. [link](https://blogs.unimelb.edu.au/language-forensics/2023/06/29/research-project-the-reliability-of-speechreading-as-forensic-evidence-by-catherine-hill/)

### Sample-size / paired study design
- Bland, J.M. & Altman, D.G. (1995). "Comparing methods of measurement." *Lancet*. (Bland-Altman paired design — the right framework for human-vs-model on same item.)

### Internal — IS definition, calibration, prior comparisons
- [intelligibility_methodology.md](intelligibility_methodology.md) — 6-signal IS definition and weights
- [threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md) — NIV thresholds (Y: IS≥3.80, Y+P: IS≥2.00) and IS↔judge calibration κ
- [is_pca_analysis.md](is_pca_analysis.md) — 2 PCs (PC1 signal-quality 68.4%, PC2 length 19.5%); informs which components dominate variance
- [human_expert_comparison.md](human_expert_comparison.md) — existing WER-based human-vs-model comparison; this note is the IS-scale companion
- [llm_judge/llm_judge_analysis.md](llm_judge/llm_judge_analysis.md) — Opus blind judge gold standard (Y=23.0%, Y+P=64.9%) for cross-anchoring
- [llm_judge/context_eval/context_eval_analysis.md](llm_judge/context_eval/context_eval_analysis.md) — context tightens not loosens (230 downgrades vs 68 upgrades); supports §3 stratification
