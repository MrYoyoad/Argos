# Analysis: Impact of a Stronger LLM on VSP-LLM Pipeline Performance

## Context

The VSP-LLM pipeline currently uses **Llama-2-7B** (4-bit quantized, LoRA r=16) as its decoder. Current baseline on AVSpeech YouTube data: **WER 64.1%, IS 2.52/5.0**. The original paper reports 25.4% WER on clean LRS3 TED talks. This analysis quantifies the expected improvement from upgrading to Llama 3.1 8B.

---

## Part 1: How the LLM Fits in the Pipeline

```
Video → AV-HuBERT encoder (frozen, 1024-dim) → K-means clustering (50% dedup)
  → Linear projection (1024 → 4096) → Llama-2-7B (4-bit QLoRA) → Text output
```

The LLM receives visual features projected into its embedding space, prepended with an instruction prompt. It autoregressively generates text. Only LoRA adapters (r=16, on q/k/v projections) and the linear projection layer are trained — base weights stay frozen in 4-bit.

Key file: `VSP-LLM/src/vsp_llm.py` — `nn.Linear(1024, 4096)` at line 224, LoRA config at lines 296-305.

The LLM's role is **disambiguation**: when the visual encoder outputs ambiguous lip movements (e.g., /p/, /b/, /m/ look identical), the LLM uses language context to pick the correct word. A stronger LLM means better disambiguation.

---

## Part 2: Llama 2 7B vs Llama 3.1 8B — The Raw Capability Gap

### Benchmark Comparison

| Benchmark | Llama 2 7B | Llama 3.1 8B | Improvement |
|-----------|-----------|-------------|-------------|
| **MMLU** (knowledge) | 45.3% | 73.0% | **+27.7 pp (+61% relative)** |
| **Vocabulary size** | 32K tokens | 128K tokens | **4x larger** |
| **Context window** | 4K tokens | 128K tokens | **32x larger** |
| **Training data** | 2T tokens | 15T+ tokens | **7.5x more** |
| **Instruction following** | Basic | Advanced (10M+ human-annotated) | Qualitative leap |
| **Hidden dimension** | 4096 | 4096 | **Same — drop-in replacement** |

Llama 3.1 8B is widely cited as roughly equivalent to Llama 2 70B on most benchmarks — a 10x parameter-equivalent improvement in the same memory footprint.

### Why These Improvements Matter for Lip Reading

1. **4x vocabulary (32K → 128K)**: Fewer subword decompositions for rare words means fewer error accumulation points in autoregressive generation. When visual signal is ambiguous, shorter token sequences = fewer chances for cascading errors.

2. **Better language prior (15T tokens vs 2T)**: The model has seen 7.5x more text, giving it much stronger priors about which words are likely in context. "Today I'm talking with [PERSON]" is a pattern it recognizes far better.

3. **Improved instruction following**: Critical for prompt-based strategies (topic injection, anti-hallucination guards, vocabulary hints) that Llama-2-7B cannot reliably use.

### Disambiguation Example

```
  Llama-2-7B (32K vocab)          Llama 3.1 8B (128K vocab)
  ─────────────────────          ─────────────────────────────
  Context: "Recognize            Context: "This video is
  this speech"                   about family. Recognize
                                 this speech"
  P("mom")  = 0.25              P("mom")  = 0.71  ◄── topic "family"
  P("bomb") = 0.22              P("bomb") = 0.08       boosts correct
  P("palm") = 0.19              P("palm") = 0.12       word strongly
  P("balm") = 0.15              P("balm") = 0.05
  P(other)  = 0.19              P(other)  = 0.04

  Output: "bomb" ✗              Output: "mom" ✓
  (wrong — low confidence)      (correct — high confidence)
```

---

## Part 3: Evidence From Our Failure Mode Data

We have detailed data on exactly what goes wrong and which failures a stronger LLM would fix.

### Failure Mode Recovery Estimates

The failure mode analysis below covers all 900 segments below the legacy IS 3.0 threshold. Under the current **NIV thresholds** (IS ≥ 2.00 for Y+P "any useful", IS ≥ 3.80 for Y "clearly conveyed"), 325 of these 900 segments are already counted as useful (the "Fair" tier, IS 2.00–2.99). The remaining **575 segments (IS < 2.00)** are truly non-useful under NIV.

| Failure Category | Count (of 900) | % | LLM Impact | Expected Recovery |
|-----------------|-------|---|------------|-------------------|
| **Wrong Topic** | 284 | 31.6% | Moderate — better language prior reduces drift | ~15-25% (~40-70 segments) |
| **Accumulated Errors** | 220 | 24.4% | High — stronger context catches small errors | ~20-30% (~45-65 segments) |
| **Right Topic Wrong Details** | 204 | 22.7% | **Highest** — entity/vocabulary disambiguation | ~25-35% (~50-70 segments) |
| **Hallucination** | 111 | 12.3% | Moderate-High — better calibration | ~15-25% (~15-25 segments) |
| **Signal Loss** | 81 | 9.0% | Low — encoder failures, not LLM failures | ~5% (~4 segments) |

**Estimated total recovery: ~155-235 segments** from the 575 truly non-useful pool (IS < 2.00), pushing the NIV Y+P useful rate from **61.6% to ~72-77%**.

### Why "Right Topic Wrong Details" Is the Sweet Spot

These 204 segments are where the visual encoder **correctly captured** the topic/domain but the LLM picked wrong words. Examples:

- "admiral McRae" → "animal migratory" (entity destruction — LLM lacks pragmatic knowledge)
- "pro controller" → "broken dollar" (content word substitution — weak vocabulary prior)
- "13th amendment" → "13th may mean something" (entity preserved but context lost)

A stronger LLM with better world knowledge and vocabulary coverage directly addresses these. The phonetic signal IS there — the decoder just needs to be smarter.

### Specific Cases From Our Data

| Case | Reference | Hypothesis | WER | How Llama 3.1 8B Helps |
|------|-----------|-----------|-----|----------------------|
| Homophene | "mom's phone" | "bomb" | 23% | 15T training tokens: "iPhone + mom" vastly more common than "iPhone + bomb" |
| Entity | "admiral McRae" | "animal migratory" | 33% | Better pragmatic understanding: "talking with [PERSON]" is a human introduction |
| Hallucination | "chapter starts with a doxology" | "I'm going to tell you a story" | 172% | Better calibration = fewer confident-but-wrong outputs |
| Topic drift | "videos about weight loss" | "wanted to be a princess" | 97% | With topic context, "health/fitness" domain constrains vocabulary |

### Success Pattern Analysis — Where Better LLM Has Most Impact

Our success patterns reveal the #1 driver of correct output:

| Success Pattern | Count | % of Successes | LLM Upgrade Impact |
|----------------|-------|---------------|-------------------|
| **Phonetically Preserved** | 248 | 41.5% | **Highest** — LLM converts phonetic near-misses to correct words |
| Minor Errors, High Semantic | 146 | 24.5% | Moderate — already working, marginal improvement |
| Entities Preserved | 74 | 12.4% | High — better entity knowledge preserves more |
| Near-Perfect Output | 69 | 11.6% | Low — already excellent |

**Key insight**: Phonetic preservation is the #1 success driver (41.5%). The visual signal preserves the phonetic structure of speech even when specific words are wrong. A stronger LLM that corrects phonetic near-misses could recover many "fair" tier segments — this is where the 128K vocabulary and better language prior have the most impact.

---

## Part 4: Hard Evidence — VALLR Paper (ICCV 2025)

The strongest direct evidence comes from the VALLR paper (Thomas et al., ICCV 2025), which tested multiple LLM backbones for lip reading on the same LRS3 benchmark:

| LLM Backbone | Parameters | WER on LRS3 |
|-------------|-----------|-------------|
| GPT-2 Small | 0.12B | 23.9% |
| Llama 3.2-1B | 1.0B | 22.8% |
| **Llama 3.2-3B** | 3.0B | **18.7%** |

**Key findings**:
1. Llama 3.2-3B (**less than half** the size of Llama-2-7B) achieved **18.7% WER**, beating VSP-LLM's 25.4% with Llama-2-7B on the same benchmark
2. The Llama 3 family is dramatically better at visual speech decoding
3. Even a smaller Llama 3 model outperforms a larger Llama 2 model
4. The improvement from GPT-2 → Llama 3.2-1B was only 1.1pp, but 1B → 3B was **4.1pp** — scale within the Llama 3 family matters

VALLR uses a different architecture (CTC phoneme head → LLM, vs VSP-LLM's direct visual features → LLM), so the absolute numbers aren't directly comparable. But the **relative LLM backbone comparison** is valid: Llama 3 family models are fundamentally better decoders for visual speech.

Extrapolating: Llama 3.1 8B (2.7x larger than 3B, same architecture family) should perform even better.

---

## Part 5: Quantified Improvement Estimates

### Scenario A: LLM Swap Only (no additional data, no prompt changes)

| Metric | Current (Llama-2-7B) | Projected (Llama 3.1 8B) | Change |
|--------|---------------------|--------------------------|--------|
| **WER** | 64.1% | ~56-61% | **-3 to -8 pp** |
| **IS** | 2.52/5.0 | ~2.7-2.9 | **+0.2-0.4** |
| **Useful rate** (NIV Y+P, IS ≥ 2.00) | 61.6% | ~66-70% | **+4-8 pp** |
| **Hallucination rate** | 20.5% | ~15-18% | **-2-5 pp** |
| **Empty outputs** | 4.7% (70 segments) | ~3-4% | **-1 pp** |

Why the LLM-only gain is modest: The visual encoder (AV-HuBERT) is the primary bottleneck. It was trained on LRS3 TED talks and produces degraded features on YouTube content. No LLM can decode information the encoder didn't capture.

### Scenario B: LLM Swap + Prompt Engineering (unlocked by stronger model)

Llama 3.1 8B **unlocks** prompt strategies that Llama-2-7B cannot reliably use:

| Strategy | Why Llama-2-7B Can't | Llama 3.1 8B Expected Gain |
|----------|---------------------|---------------------------|
| Vocabulary/entity lists | Ignores complex prompts | **-3 to -5 pp** |
| Anti-hallucination instructions | Can't follow negative constraints | **-2 to -5 pp** |
| Phonetic context hints | Doesn't understand phonetic notation | **-3 to -8 pp** |
| Topic context injection | Works partially now | **-5 to -10 pp** (better with stronger model) |

Combined Scenario B estimate: **WER ~45-52%, IS ~3.0-3.3, Useful rate (NIV Y+P) ~72-80%**

### Scenario C: LLM Swap + Data Scaling + Prompt Engineering

The ICLR 2024 scaling law paper (Zhang et al.) shows fine-tuning follows a **multiplicative joint scaling law**: `L = A × model^(-α) × data^(-β)`. A better model extracts MORE from additional data — the gap widens with scale.

| Configuration | Projected WER | Useful Rate (NIV Y+P) |
|--------------|--------------|--------------|
| Current: Llama-2-7B + 1.3K segments | 64.1% | 61.6% |
| Llama 3.1 8B + 1.3K segments | ~56-61% | ~66-70% |
| Llama 3.1 8B + 20K segments | ~40-45% | ~75-82% |
| Llama 3.1 8B + 50K segments + prompts | ~35-40% | ~82-88% |
| Llama 3.1 8B + 50K + encoder unfreeze | ~30-35% | ~88-93% |

### Summary: Where the Improvement Comes From

| Source | Mechanism | WER Reduction |
|--------|-----------|---------------|
| **Better language prior** (15T vs 2T) | Stronger word predictions when visual signal is ambiguous | -2 to -4 pp |
| **Larger vocabulary** (128K vs 32K) | Fewer subword errors on rare words | -1 to -2 pp |
| **Unlocked prompt strategies** | Model can follow complex instructions | -5 to -15 pp |
| **Better entity disambiguation** | 61% higher MMLU = better world knowledge | -2 to -3 pp |
| **Reduced hallucination** | Better calibration, follows negative constraints | -1 to -3 pp |
| **Multiplicative scaling with data** | More data + better model = superlinear gain | -5 to -15 pp (with 20K+ segments) |

**Bottom line**: The LLM swap alone gives a modest 3-8 pp improvement. The real payoff is that it removes the LLM as a bottleneck, enabling prompt strategies and data scaling that are currently impossible with Llama-2-7B. With proper data and prompts, the combined improvement could reach 20-30+ pp.

---

## Part 6: Which Failure Categories Improve Most vs Least

*Counts below are from the 900 segments below legacy IS 3.0; under NIV thresholds (IS ≥ 2.00), 575 of these are truly non-useful. Recovery estimates target this non-useful pool.*

### High Impact (LLM-dependent failures)

1. **Right Topic Wrong Details (204 segments, 22.7%)**: The sweet spot. Encoder captured the right topic, LLM picked wrong words. Stronger language prior directly fixes entity names, technical vocabulary, content words. **Expected: 25-35% recovery.**

2. **Accumulated Small Errors (220 segments, 24.4%)**: Many individually minor substitutions that compound. Better context modeling catches cascading errors. **Expected: 20-30% recovery.**

3. **Hallucination (111 segments, 12.3%)**: The LLM "runs ahead" of the visual signal. Better-calibrated model truncates sooner, follows anti-hallucination instructions. **Expected: 15-25% recovery.**

### Moderate Impact

4. **Wrong Topic, phonetically similar (141 segments)**: Mouth shapes captured but decoded into wrong semantic domain. 4x vocabulary and better contextual disambiguation help. **Expected: 10-20% recovery.**

### Low Impact (encoder-limited)

5. **Wrong Topic, total drift (143 segments)**: No visual signal. No LLM can fix this. **Expected: <5% recovery.**

6. **Signal Loss / Empty (81 segments)**: Encoder-level failures. **Expected: <5% recovery.**

---

## Part 7: The Swap Is Trivial

Because Llama 3.1 8B has the same hidden dimension (4096) as Llama-2-7B:

| Component | Change Required? |
|-----------|-----------------|
| AV-HuBERT encoder | No change |
| K-means clustering | No change |
| Linear projection (1024 → 4096) | **No change** (same output dim) |
| LLM model files | **Yes** — swap model path |
| Tokenizer | **Yes** — update to 128K vocab |
| LoRA adapters | **Yes** — retrain from scratch |

Files to edit: `VSP-LLM/scripts/train.sh` and `VSP-LLM/scripts/decode.sh` (update `LLM_PATH`).
Estimated setup effort: **1-2 hours** + training time.

---

## Part 8: Model Alternatives

### Tier 1: Drop-in Replacements (hidden_size = 4096)

| Model | Params | Key Advantage |
|-------|--------|---------------|
| **Llama 3.1 8B** | 8B | Easiest swap — only change model path and tokenizer |
| **Llama 3.2 3B** | 3B | VALLR proved 18.7% WER on LRS3 — smaller, faster, proven |
| **Mistral 7B v0.3** | 7.2B | Same hidden dim, strong reasoning |

### Tier 2: Requires projection layer update

| Model | Hidden Size | Key Advantage |
|-------|------------|---------------|
| **Qwen 2.5 7B** | 3584 | Strong multilingual, excellent reasoning |
| **Phi-4** | 3072 | Exceptionally strong reasoning for size |

---

## References

- [Meta Llama 3 announcement](https://ai.meta.com/blog/meta-llama-3/)
- [VALLR: Visual ASR Language Model for Lip Reading (Thomas et al., ICCV 2025)](https://arxiv.org/abs/2503.21408)
- [VSP-LLM: Where Visual Speech Meets Language (Yeo et al., EMNLP 2024)](https://arxiv.org/abs/2402.15151)
- [When Scaling Meets LLM Finetuning (Zhang et al., ICLR 2024)](https://arxiv.org/abs/2402.17193)
- [Llama 3.1 8B model details](https://www.myscale.com/blog/llama-3-1-405b-70b-8b-quick-comparison/)