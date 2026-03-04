# IS Extended Analysis: Topic, Length, Config Variants & Word Count

**Parent document:** [intelligibility_methodology.md](intelligibility_methodology.md) (Sections 1-11: core IS methodology)
**Date:** 2026-02-24 (extended through March 2026)

---

## 12. Topic Analysis

Topics are assigned by keyword matching on reference text across 10 categories (Medical, Cooking, Technology, Sports, Education, Business, Politics, Entertainment, Religion, DIY) plus "Other".

### Baseline Results by Topic (sorted by Mean IS)

| Topic | N | Mean IS | WER | Captured% | Ctx Rule% | Ctx LLM% |
|-------|---|---------|-----|-----------|-----------|----------|
| Business/Finance | 46 | 3.08 | 46.8% | 56.5% | 63.0% | 67.4% |
| Sports/Fitness | 31 | 2.90 | 52.9% | 48.4% | 58.1% | 61.3% |
| Education/Academic | 86 | 2.83 | 52.4% | 47.7% | 53.5% | 59.3% |
| Politics/News | 34 | 2.81 | 56.7% | 50.0% | 50.0% | 55.9% |
| Technology | 132 | 2.70 | 56.7% | 49.2% | 50.0% | 56.8% |
| Cooking/Food | 117 | 2.66 | 59.3% | 44.4% | 50.4% | 59.8% |
| Medical/Health | 39 | 2.64 | 56.7% | 53.8% | 53.8% | 53.8% |
| Religion/Spirituality | 17 | 2.55 | 68.7% | 35.3% | 29.4% | 47.1% |
| Other | 899 | 2.42 | 68.0% | 36.2% | 39.9% | 46.7% |
| Entertainment | 69 | 2.23 | 67.3% | 30.4% | 34.8% | 47.8% |
| DIY/Home | 27 | 2.13 | 76.0% | 29.6% | 29.6% | 37.0% |

### Key Observations

- **Business/Finance performs best** (IS 3.08, 57% captured). Formal, structured speech with common vocabulary is easier to lip-read.
- **Entertainment and DIY/Home perform worst** (IS ~2.2, ~30% captured). Casual speech, slang, and technical jargon are harder.
- LLM-based context recovery consistently adds 5-15% over rule-based, especially for topics with domain-specific vocabulary.

---

## 13. Segment Length Analysis

Longer segments give the lip-reading model more visual context. Metrics vary significantly with segment length.

### Baseline Results by Length Band

| Length Band | N | Mean IS | WER | Captured% | Ctx Rule% | Ctx LLM% |
|------------|---|---------|-----|-----------|-----------|----------|
| 5-10 words | 290 | 2.31 | 74.2% | 31.7% | 35.2% | 41.4% |
| 10-15 words | 368 | 2.51 | 64.1% | 34.8% | 39.4% | 47.0% |
| 15-20 words | 270 | 2.60 | 59.4% | 41.9% | 46.3% | 54.4% |
| 20+ words | 535 | 2.68 | 55.1% | 48.6% | 51.6% | 57.6% |

### Key Observations

- **Short segments (5-10 words)** have 74% WER and only 32% captured. Brief utterances don't provide enough lip movement patterns.
- **Long segments (20+ words)** reach 49% captured and 58% LLM-recoverable.
- The improvement from short to long: +17pp captured, +16pp LLM-recoverable, -19pp WER.
- For production: filtering to >= 10 words removes the noisiest short fragments and raises capture rate.

---

## 14. Config J & C: Decode Parameter Variants

Two alternative decode configurations were evaluated on the full 1,497-segment dataset to test whether length penalty and sampling could improve over the baseline.

### Configurations

| Parameter | Baseline (A) | Config J | Config C |
|-----------|-------------|----------|----------|
| lenpen | 0 | 1.0 | 1.0 |
| do_sample | false | true | false |
| temperature | 1.0 | 0.5 | 1.0 |

All other parameters identical (beam=20, top_p=0.9, rep_penalty=1.2, no_repeat_ngram=3).

### Results

| Metric | Baseline | Config J | Config C |
|--------|----------|----------|----------|
| Mean IS | 2.52 | **2.60** | 2.57 |
| Properly Captured (IS >= 3) | 597 (39.9%) | **622 (41.5%)** | 594 (39.7%) |
| Empty Predictions | 70 (4.7%) | **0** | **0** |
| Hallucinations (WER >= 100%) | 307 (20.5%) | 348 (23.2%) | 360 (24.0%) |
| Mean WER | **64.1%** | 78.9% | 79.3% |
| Mean WWER | **61.9%** | 62.8% | 63.8% |
| NEA F1 | 38.9% | **43.4%** | 39.7% |

### What Changed

- **Empties eliminated:** lenpen=1.0 forces output for all segments. The 70 former empties (IS=0) now produce actual text.
- **Hallucinations doubled:** 111 -> 262 (J) / 270 (C). Most former empties become hallucinations -- the model generates fluent but fabricated text when visual signal is weak.
- **Net IS slightly positive:** Even hallucinated output scores IS ~0.5-1.0 (vs 0.0 for empty), and ~15% of filled empties produce fair/good quality.
- **J beats C:** Stochastic sampling (temp=0.5) finds 28 more intelligible segments and recovers 3.7pp more named entities than deterministic decoding.
- **Long segments benefit most:** 20+ word segments gain +0.25 IS and +3.4pp capture rate under J. Short segments (5-10 words) are marginally worse due to over-generation.

### Conclusion

The improvement is real but marginal (+0.08 IS, +25 captured segments). The fundamental tradeoff is silent failures (empties) vs noisy failures (hallucinations). Decode parameter tuning has reached diminishing returns; domain adaptation via fine-tuning remains the only viable path to production-grade accuracy.

Full comparison: [baseline_vs_J_vs_C_intelligibility.md](baseline_vs_J_vs_C_intelligibility.md)

---

## 15. Word Count as Context: Impact Analysis

### The Question

If the LLM decoder were given the correct word count for each segment (e.g., "The speaker says 12 words"), how would performance change across each failure mode? Would it reduce hallucinations? Would the client be able to detect when the output is fabricated?

### Architecture Context

The VSP-LLM decoder is Llama-2-7B (4-bit quantized, LoRA-adapted) that receives a fixed instruction `"Recognize this speech in English. Input : "` followed by visual features from AV-HuBERT. It generates autoregressively until EOS token or `max_new_tokens` is reached (computed as `2.0 * N_clusters + 200`). **`length_penalty=0.0`** means no length normalization in beam search. Word count could be injected by modifying the instruction to `"Recognize this speech in English. The speaker says N words. Input : "`.

Two approaches exist: (A) inject word count at inference only (no retraining), or (B) fine-tune with word count in the instruction. These produce fundamentally different outcomes.

---

### 15A. Inference-Only Word Count (No Retraining)

#### The Critical Finding: Most Failures Are Content Problems, Not Length Problems

| Failure Mode | N | Already Correct Length (0.8-1.2 ratio) | Mean length_ratio |
|---|---|---|---|
| Accumulated Small Errors | 111 | **82.0%** | 0.923 |
| Phonetically Similar but Wrong Topic | 141 | **78.0%** | 0.949 |
| Content Word Errors | 96 | **74.0%** | 0.899 |
| Entity Destruction | 108 | **63.9%** | 0.904 |
| High Error Rate | 109 | **62.4%** | 0.937 |
| Total Topic Drift | 143 | 39.2% | 0.720 |
| Hallucination | 111 | 23.4% | 1.563 |
| Truncation | 10 | 0.0% | 0.207 |
| Empty Output | 70 | 0.0% | 0.000 |
| Over-generation | 1 | 0.0% | 2.000 |

**6 out of 10 failure modes** (706/900 = 78.4% of failures) already produce approximately the correct number of words. Word count has zero effect on them — the problem is **which words** are generated, not **how many**.

#### Per-Failure-Mode Impact (Inference-Only)

**Empty Output (70 segments, mean ref_words=33.7):**
Model produces nothing. These are the LONGEST segments (mean 33.7 words, 0% have ref_words < 10). Setting `min_length=N` forces generation, but the model produced nothing because visual features for long sequences are degraded. Forced output = **pure hallucination at exactly the right length**. Impact: NEGATIVE.

**Hallucination (111 segments, mean ref_words=9.6, 57.7% on short segments):**
Fluent text unrelated to what was said. Mean length_ratio=1.56 (56% more words than reference). 23.4% already have correct length. For the 76.6% that are too long, word count truncates the fabrication but doesn't fix content. **Most importantly: removes the client's only detection signal** (see Hallucination Detectability below). Impact: MIXED/NEGATIVE.

Real examples of what the LLM hallucinates:
- REF: `"here"` (1 word) → HYP: `"i am an engineer"` (4 words, ratio=4.0)
- REF: `"very important"` (2 words) → HYP: `"policies that keep us out of the"` (7 words, ratio=3.5)
- REF: `"rotating thunderstorms with big hail"` (5 words) → HYP: `"ted turner's arms sold by hal"` (6 words, ratio=1.2 — already correct length, still hallucinated)

**Over-generation (1 segment):** Constraining to N words = direct fix. Impact: POSITIVE (trivially rare).

**Truncation (10 segments, mean ref_words=27.5):** Forcing continuation past where the model lost the visual signal produces hallucinated text for the remaining ~80%. Impact: NEGATIVE.

**All other modes (608 segments):** Already at correct length. Zero impact.

#### Summary Table (Inference-Only)

| Failure Mode | N | Would It Help? | Direction |
|---|---|---|---|
| Over-generation | 1 | YES — direct fix | Positive |
| Hallucination | 111 | PARTIALLY — reduces volume, makes detection HARDER | Mixed/Negative |
| Truncation | 10 | NO — converts to partial hallucination | Negative |
| Empty Output | 70 | NO — converts to full hallucination | Negative |
| All others | 608 | NO — already correct length | None |

**Net impact:** ~+5 segments crossing IS=3.0 (+0.3pp). Hallucination count increases from 111 to ~191 (7.4% → 12.8%) as Empty Output and Truncation are forced to generate fabricated text. All hallucinations become harder to detect.

#### Hallucination Detectability (Critical Finding)

**Current state:** A client has one weak signal — output seems suspiciously long for a short video clip. 36.9% of hallucinations have ratio > 1.5, providing this length mismatch signal.

**With word count:** This signal disappears entirely. The output is exactly the right length, fluent, and grammatically perfect. The client has zero basis to suspect fabrication.

| Scenario | REF (unknown) | HYP (client sees) | Client's Assessment |
|---|---|---|---|
| Without word count | "here" (1 word) | "i am an engineer" (4 words) | "4 words for a 0.3s clip? Suspicious." |
| **With word count** | "here" (1 word) | "engineer" (1 word) | "One word, short clip. Looks correct." |

**Conclusion for inference-only:** Net negative. The model was never trained to use word count as a conditioning signal. Primary effect is removing the client's detection heuristic while converting empty/truncated segments into undetectable hallucination.

---

### 15B. Fine-Tuning WITH Word Count (Retraining)

Fine-tuning changes the calculus fundamentally because the model **learns** the connection between word count and generation behavior through thousands of gradient updates.

#### Implementation

The modification is ~3 lines in `vsp_llm_dataset.py` `__getitem__`:
```python
word_count = len(self.label_list[0][index].split())
instruction = f"Recognize this speech in {lang_name}. The speaker says {word_count} words. Input : "
```

Word count is always trivially available — the `.wrd` label files contain ground truth text for every training sample. No additional data preparation needed. No architecture changes required — the LoRA adapters (~12.6M parameters on q_proj, k_proj, v_proj across all 32 Llama-2 layers) learn to attend to the word count tokens through standard causal attention.

#### Why Fine-Tuning Is Mechanistically Different

| Aspect | Inference-Only Prompting | Fine-Tuning With Word Count |
|--------|--------------------------|----------------------------|
| Connection to visual features | None — LLM treats "12 words" as generic text context | Direct — LoRA adapters learn word-count-to-generation patterns |
| EOS calibration | Weak — no trained association | Strong — thousands of examples teach exact EOS placement |
| Length accuracy | Unreliable — Llama-2 has poor counting ability | Reliable — explicitly trained to produce N words when told N |
| Hallucination reduction | Minimal — model still defaults to language prior | Significant — word count constrains the plausible output space |
| Train/test distribution | Mismatch — instruction format differs from training | Match — same format at training and inference |

The most important benefit: **the model learns two distinct generation strategies.** Currently, when visual signal is weak, the model cannot distinguish "this is a 3-word utterance" from "this is a 20-word utterance with degraded video." With word count:
- `P(token_i | visual_features, "3 words")` — concentrate attention on few confident visual cues
- `P(token_i | visual_features, "20 words")` — distribute attention across more features

This conditional length modeling literally cannot be learned without the word count signal.

#### Per-Failure-Mode Impact (Fine-Tuned)

**Hallucination (111 segments) — largest improvement:**
The 64 short-segment hallucinations (ref_words < 10) benefit most. With "3 words" conditioning, the model's hypothesis space shrinks dramatically — instead of exploring all possible English sentences, it focuses on 3-word hypotheses consistent with the visual features. Estimated 15-25% of short-segment hallucinations could improve. Longer-segment hallucinations: 5-10% improvement.

**Empty Output (70 segments):**
The model learns "when told 20 words, generate 20 words." Visual features are still degraded for these long segments, but training teaches the model to attempt generation rather than producing nothing. Estimated 10-15 of 70 might produce partially correct text where visual signal is merely weak rather than absent.

**Truncation (10 segments):**
The model learns to continue generating up to N words. Unlike inference-only forcing, the continuation is grounded in trained behavior, not raw forced generation. Estimated 2-3 of 10 improve.

**Total Topic Drift (143 segments):**
Modest improvement for the 60.8% that undergenerate. Word count forces the model to produce more output, giving more opportunities for correct content. Estimated 5-10% improvement.

**All other modes (424 segments):**
Already at correct length, word choice problems. ~0% improvement from word count alone.

#### Net Impact Estimate (Fine-Tuned)

| Metric | Current | Fine-Tuned w/ Word Count | Change |
|---|---|---|---|
| Properly captured (IS >= 3.0) | 597 (39.9%) | ~640-660 (42.7-44.1%) | **+43 to +63 (+3-4pp)** |
| Hallucinated segments | 111 (7.4%) | ~80-90 (5.3-6.0%) | **-21 to -31 (-1.4-2.1pp)** |
| Mean IS | 2.52 | ~2.60-2.65 | **+0.08-0.13** |
| Short segment (5-10w) captured% | 31.7% | ~38-42% | **+6-10pp** |
| Long segment (20+w) captured% | 48.6% | ~50-52% | **+1.4-3.4pp** |

Improvement concentrates on **short segments** where the model currently hallucinates due to insufficient visual context. Not transformative, but meaningful — and the implementation cost is ~3 lines of code in the dataset class.

#### Risks

1. **Word count accuracy at inference.** During training, count comes from ground truth. At inference, it must come from Whisper ASR or a separate predictor. Wrong estimates condition the model on incorrect information. **Mitigation:** Train with noisy word counts (randomly perturbed ±1-2 words) and use approximate phrasing ("about 12 words" or "10 to 14 words").

2. **Overfitting to exact counts.** The model may produce exactly N words even when content requires N±1. **Mitigation:** Perturb counts during training.

3. **Circular dependency.** Whisper errors in word count propagate to the decoder. For segments where Whisper is wrong (which is exactly where lip-reading matters most), the hint may mislead. **Mitigation:** Use Whisper word count only as approximate range, not exact target.

#### Comparison to Config J (lenpen=1.0)

Config J (Section 14) also addresses length by setting `length_penalty=1.0`, which normalizes beam scores by length. This eliminates empties and modestly improves IS. Fine-tuning with word count goes further:
- Config J: implicit length preference via beam score normalization
- Word count fine-tuning: explicit length target via conditioning signal

These are complementary — Config J's lenpen=1.0 could be combined with word count fine-tuning for strongest effect.

---

### 15C. Recommended Approach

1. **Do NOT inject word count at inference without retraining.** Net negative — camouflages hallucinations while providing negligible content improvement.

2. **Fine-tuning with word count is viable as part of domain adaptation (Mission 9).** When fine-tuning on AVSpeech data, adding word count to the instruction is a zero-cost modification (~3 lines). The estimated +3-4pp capture rate improvement is worth the negligible effort.

3. **Use noisy/approximate word counts during training** to prevent brittleness. At inference, use Whisper's word count estimate from the ASR step that already runs in the pipeline.

4. **Pair with confidence scoring (Mission 4).** Word count conditioning improves beam search calibration, which improves confidence score reliability. Word count reduces hallucination rate; confidence scoring detects the remaining hallucinations. The two features are complementary.

---

## 16. LLM Salvage Summary

*(Full analysis: [llm_salvage/llm_salvage_analysis.md](llm_salvage/llm_salvage_analysis.md))*

Traditional metrics classify 900 of 1,497 segments as failures (IS < 3.0). The LLM heuristic identifies **165 of these 900 segments (18.3%)** as having recoverable meaning, raising effective capture from 39.9% to **50.9%**.

6 recovery categories: Phonetic Bridge (93), Structure Match (74), Semantic Preservation (57), Hidden Gems (54), Entity-Preserved (44), WER Over-Punishment (27).

---

## 17. LLM-as-a-Judge Summary

*(Full analysis: [llm_judge/llm_judge_analysis.md](llm_judge/llm_judge_analysis.md))*

Claude Opus 4.6 evaluated all 1,497 pairs: Y=23.0%, P=41.8%, N=35.1%. IS correlates at r=0.850 with LLM judge. The 42% partial zone (P) is the critical boundary that IS collapses into pass/fail.

Context-aware re-evaluation: Y drops to 15.0%, P rises to 47.1%, N=37.9%. Context is STRICTER — 230 downgrades vs 68 upgrades. Full analysis: [llm_judge/context_eval/context_eval_analysis.md](llm_judge/context_eval/context_eval_analysis.md).
