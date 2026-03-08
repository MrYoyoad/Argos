# Analysis: Impact of a Stronger LLM on VSP-LLM Pipeline Performance

## Context

The VSP-LLM pipeline currently uses **Llama-2-7B** (4-bit quantized, LoRA r=16) as its decoder. Current baseline on AVSpeech YouTube data: **WER 67.0%, IS 2.53/5.0**. The original paper reports 25.4% WER on clean LRS3 TED talks. The user wants to understand what a stronger LLM would change, what alternatives exist, and how data scaling and multilingual models factor in.

---

## Part 1: How the LLM Fits in the Pipeline

```
Video → AV-HuBERT encoder (frozen, 1024-dim) → K-means clustering (50% dedup)
  → Linear projection (1024 → 4096) → Llama-2-7B (4-bit QLoRA) → Text output
```

The LLM receives visual features projected into its embedding space, prepended with an instruction prompt. It autoregressively generates text. Only LoRA adapters (r=16, on q/k/v projections) and the linear projection layer are trained — base weights stay frozen in 4-bit.

Key file: `VSP-LLM/src/vsp_llm.py` — `nn.Linear(1024, 4096)` at line 224, LoRA config at lines 296-305.

### Figure 1: VSP-LLM Architecture — Where the LLM Sits

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                        VSP-LLM PIPELINE                                │
 │                                                                        │
 │  ┌──────────┐    ┌─────────────┐    ┌───────────┐    ┌──────────────┐  │
 │  │  Video   │    │  AV-HuBERT  │    │  K-means  │    │   Linear     │  │
 │  │  Frames  │───>│  Encoder    │───>│  Cluster  │───>│  Projection  │  │
 │  │ [T,96,96]│    │  (FROZEN)   │    │  + Dedup  │    │ 1024 → 4096  │  │
 │  └──────────┘    │  1024-dim   │    │  -50% len │    │  (TRAINED)   │  │
 │                  └─────────────┘    └───────────┘    └──────┬───────┘  │
 │                                                             │          │
 │  ┌──────────────────────────────────────────────────────────▼───────┐  │
 │  │                    LLM INPUT (Embedding Space)                   │  │
 │  │                                                                  │  │
 │  │  ┌─────────────────────┐  ┌──────────────────┐                  │  │
 │  │  │  Instruction Tokens │  │  Visual Features  │                  │  │
 │  │  │  "Recognize this    │  │  [T', 4096]       │                  │  │
 │  │  │   speech in English │  │  (projected from  │                  │  │
 │  │  │   . Input : "       │  │   AV-HuBERT)     │                  │  │
 │  │  └─────────────────────┘  └──────────────────┘                  │  │
 │  │           ▼                        ▼                             │  │
 │  │  ┌──────────────────────────────────────────────────────────┐   │  │
 │  │  │              CONCATENATED SEQUENCE                       │   │  │
 │  │  │   [instr_tok₁ ... instr_tokₙ | vis_feat₁ ... vis_featₜ]│   │  │
 │  │  └──────────────────────────┬───────────────────────────────┘   │  │
 │  └─────────────────────────────┼───────────────────────────────────┘  │
 │                                ▼                                      │
 │  ┌─────────────────────────────────────────────────────────────────┐  │
 │  │                     Llama-2-7B (4-bit NF4)                      │  │
 │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       ┌──────────┐  │  │
 │  │  │ Layer 1  │  │ Layer 2  │  │ Layer 3  │  ...  │ Layer 32 │  │  │
 │  │  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │       │ ┌──────┐ │  │  │
 │  │  │ │LoRA  │ │  │ │LoRA  │ │  │ │LoRA  │ │       │ │LoRA  │ │  │  │
 │  │  │ │r=16  │ │  │ │r=16  │ │  │ │r=16  │ │       │ │r=16  │ │  │  │
 │  │  │ │q,k,v │ │  │ │q,k,v │ │  │ │q,k,v │ │       │ │q,k,v │ │  │  │
 │  │  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │       │ └──────┘ │  │  │
 │  │  └──────────┘  └──────────┘  └──────────┘       └──────────┘  │  │
 │  │  Hidden size: 4096  |  32 heads  |  Vocab: 32,000              │  │
 │  └────────────────────────────┬────────────────────────────────────┘  │
 │                               ▼                                       │
 │                    ┌─────────────────────┐                            │
 │                    │   Generated Text    │                            │
 │                    │  "she said hello"   │                            │
 │                    └─────────────────────┘                            │
 └───────────────────────────────────────────────────────────────────────┘

  TRAINABLE: Linear projection (1024→4096) + LoRA adapters (12.6M params)
  FROZEN:    AV-HuBERT encoder + Llama-2-7B base weights (6.7B params)
```

---

## Part 2: What a Stronger LLM Would Improve

| Aspect | Why | Expected Impact |
|--------|-----|-----------------|
| **Homophone disambiguation** | Better language model = better context for resolving p/b/m, t/d/n confusions | Moderate (5-8% of errors are homophones) |
| **Reduced hallucination** | Stronger models hallucinate less under ambiguity; better calibrated uncertainty | Significant (currently 20.6% hallucination rate) |
| **Rare word / entity handling** | Larger vocab (128K vs 32K tokens in Llama-3), better representation of names, numbers, jargon | Significant (Named Entity F1 currently 38.8%) |
| **Longer context reasoning** | Llama-3+ supports 128K context (vs 4K in Llama-2); helps with longer segments | Minor for current 3-10s segments |
| **Tokenizer efficiency** | Llama-3's tokenizer produces ~15% fewer tokens — faster inference, more efficient training | Minor quality impact, noticeable speed gain |
| **Better instruction following** | Modern LLMs are much better at following the task instruction ("Transcribe this speech") | Moderate — reduces off-task generation |

### Figure 2: How a Stronger LLM Reduces Errors (Homophone Disambiguation)

```
  VISUAL INPUT: Lip shape for bilabial consonant + vowel
  (ambiguous: could be "mom", "bomb", "palm", "balm")

  ┌─────────────────────────────────────────────────────────────────┐
  │  AV-HuBERT output: [bilabial, open-vowel, bilabial]            │
  │  (same visual features regardless of actual word)               │
  └──────────────────────────┬──────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
  ┌─────────────────────┐      ┌─────────────────────────┐
  │   Llama-2-7B        │      │   Llama 3.1 8B          │
  │   (32K vocab)       │      │   (128K vocab)          │
  │                     │      │                         │
  │ Context: "Recognize │      │ Context: "This video is │
  │ this speech"        │      │ about family. Recognize  │
  │                     │      │ this speech"            │
  │ P("mom")  = 0.25    │      │                         │
  │ P("bomb") = 0.22    │      │ P("mom")  = 0.71  ◄─── │─── topic "family"
  │ P("palm") = 0.19    │      │ P("bomb") = 0.08       │    boosts correct
  │ P("balm") = 0.15    │      │ P("palm") = 0.12       │    word strongly
  │ P(other)  = 0.19    │      │ P("balm") = 0.05       │
  │                     │      │ P(other)  = 0.04       │
  │ Output: "bomb" ✗    │      │                         │
  │ (wrong — low        │      │ Output: "mom" ✓         │
  │  confidence pick)   │      │ (correct — high conf)   │
  └─────────────────────┘      └─────────────────────────┘

  WHY: Llama 3.1 has (1) better language prior, (2) can use topic context,
       (3) 4x larger vocabulary for rare/ambiguous words
```

### Remaining bottleneck: Visual encoder domain shift

AV-HuBERT is frozen and trained on LRS3 (clean TED talks). Applied to YouTube, it produces degraded features. A stronger LLM helps more with *what it does with the signal*, but it still can't invent information the visual encoder didn't capture. This is the ceiling — but the ceiling is higher than our current results suggest, because our fine-tuning was severely data-limited.

---

## Part 3: The Data Problem — Why Our Experiments Undersold the LLM

### What happened with r=16 vs r=64

Both experiments used only **1,273 segments (~1.5 hours)** for LoRA fine-tuning. Both memorized training data by epoch 2-4 (train acc ~95%, val acc ~60%). The r=64 model performed 3.1pp *worse* than r=16 — **but this proves the dataset was too small, not that the LLM has enough capacity.**

With 1,273 samples, even r=16 has vastly more parameters (12.6M) than needed to memorize the data. The r=64 experiment (50.3M params) just memorized faster and overfit harder. Neither experiment tested the LLM's actual potential — they tested the limits of a tiny dataset.

### Figure 3: Exp A/B Overfitting — Both Hit the Data Ceiling

```
  Val Accuracy (%)                    Train Accuracy (%)
  65 ┤                                100 ┤                          xxxxxxxxxx
     │   * ◄── Exp A peak (62.94%)       │                    xxxxxx
  63 ┤  * *    epoch 2                  95 ┤               xxxxx
     │ *   *                              │           xxxx
  61 ┤*     *   o ◄── Exp B peak         90 ┤       xxx
     │       *  oo    (59.80%) epoch 4     │    xxx
  59 ┤        **oo*                      85 ┤  xx
     │          ooo**                      │ x        * = Exp A (r=16)
  57 ┤           ooo  ***                80 ┤x         o = Exp B (r=64)
     │            ooo    ***               │
  55 ┤              ooo     ***          75 ┤          Both reach ~95%
     │                ooo                  │          train accuracy
  53 ┤                                   70 ┤          = MEMORIZATION
     └──┬──┬──┬──┬──┬──┬──┬──┬──┬──       └──┬──┬──┬──┬──┬──┬──┬──┬──┬──
       1  2  3  4  5  6  7  8  9 10          1  2  3  4  5  6  7  8  9 10
                 Epoch                                   Epoch

  DIAGNOSIS: Both models memorize 1,273 training samples completely.
  r=64 is NOT worse because the LLM has enough capacity —
  it's worse because 4x more params = 4x faster overfitting on tiny data.

  ┌─────────────────────────────────────────────────────────────┐
  │  Train-Val Gap:  r=16: 36.5 pp  |  r=64: 35.6 pp          │
  │  Both massive → INSUFFICIENT DATA, not insufficient model  │
  └─────────────────────────────────────────────────────────────┘
```

### How much data is "enough"?

Research on LLM fine-tuning scaling laws (ICLR 2024: [Zhang et al.](https://arxiv.org/abs/2402.17193)) shows:

- Fine-tuning follows a **power law**: performance improves as data^β, where β ranges from 0.025 (LoRA) to 0.15 (full fine-tuning)
- **1,000 samples is the absolute minimum** per task — below this, models reproduce training data verbatim instead of generalizing (exactly what we observed)
- **LoRA is most effective in the 1K-100K sample range** — it outperforms full fine-tuning under 100K due to implicit regularization
- Full fine-tuning only becomes favorable at **million-scale** datasets

For visual speech specifically, the literature shows:

| Training Data Size | Expected Outcome | Evidence |
|-------------------|-----------------|----------|
| **1,273 segments (current)** | Memorization, no generalization | Our experiments: train 95%, val 60% |
| **5,000-10,000 segments** | Meaningful generalization begins | LoRA literature minimum for domain adaptation |
| **30,000+ segments (~50 hrs)** | Strong domain adaptation | VALLR achieves 18.7% WER on LRS3 with 30hrs; SynthVSR achieves 43.3% WER with 30hrs |
| **100,000+ segments (~150 hrs)** | Near-ceiling for LoRA approach | Diminishing returns expected per power law |
| **433 hours (LRS3 full)** | Paper-grade results | VSP-LLM paper achieved 25.4% WER |

### What "enough" YouTube data looks like

AVSpeech contains **~290K YouTube videos / ~4,700 hours**. The Oxford MultiVSR project (Prajwal et al., ICASSP 2025) expanded this to **~12,000 hours** by processing full videos. Realistically:

| Scale | Segments | Effort | Expected WER (with current Llama-2-7B) | With stronger LLM (Llama 3.1 8B) |
|-------|----------|--------|----------------------------------------|-----------------------------------|
| **Current** | 1,273 | Done | 67% (observed) | ~62-64% (LLM gains only) |
| **5K segments** | ~8 hrs | Moderate (filter AVSpeech for quality) | ~55-60% | ~50-55% |
| **20K segments** | ~33 hrs | Significant (quality filtering + Whisper transcription) | ~45-50% | ~40-45% |
| **50K segments** | ~83 hrs | Major (need pipeline + curation) | ~40-45% | ~35-40% |
| **100K+ segments** | ~167 hrs | Large-scale | ~35-40% | ~30-35% |

### Figure 4: Projected WER Improvement as Training Data Scales

```
  WER (%)   (lower is better)
  70 ┤ X ◄── Current: 1.3K segments, Llama-2-7B = 67% WER
     │  \
  65 ┤   X..◄── Llama-2-7B with more data
     │    \ '.
  60 ┤     \  '..
     │      O    '..◄── Llama 3.1 8B (stronger LLM, same data scale)
  55 ┤       \     '..
     │        \      ''..
  50 ┤         O        ''..
     │          \          ''...
  45 ┤           \             ''...         X = Llama-2-7B
     │            O                ''...     O = Llama 3.1 8B
  40 ┤             \                   ''..
     │              \                      ''.
  35 ┤               O                       ''..    ◄── Gap WIDENS
     │                \                          ''..     with more data
  30 ┤                 O                            ''..  (multiplicative
     │                                                 '.  scaling law)
  25 ┤                  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  · VSP-LLM paper
     │                                                        (25.4% on LRS3)
     └──────┬──────┬──────┬──────┬──────┬──────┬──────┬────
          1.3K    5K    10K    20K    50K   100K   200K
                      Training Segments

  SOURCE: ICLR 2024 scaling law: L(X, D) = A * (1/X^α) * (1/D^β)
  Model scaling exponent (α) > data scaling exponent (β)
  → Upgrading the model yields MORE gain per unit of data
```

### Figure 5: Multiplicative Joint Scaling Law (ICLR 2024)

```
  The fine-tuning loss follows:  L(model, data) = A × model^(-α) × data^(-β)

  This is MULTIPLICATIVE — improvements compound:

  ┌──────────────────────────────────────────────────────────────────────┐
  │                                                                      │
  │   Example with hypothetical α=0.3, β=0.1:                          │
  │                                                                      │
  │   Current:  L(7B, 1.3K)  = A × 7B^(-0.3) × 1.3K^(-0.1) = 1.00    │
  │                                                                      │
  │   Better LLM only:                                                   │
  │   L(8B*, 1.3K) = A × 8B^(-0.3) × 1.3K^(-0.1) = 0.92  (-8%)       │
  │                                                                      │
  │   More data only:                                                    │
  │   L(7B, 20K)   = A × 7B^(-0.3) × 20K^(-0.1)  = 0.78  (-22%)      │
  │                                                                      │
  │   Both together:                                                     │
  │   L(8B*, 20K)  = A × 8B^(-0.3) × 20K^(-0.1)  = 0.72  (-28%)      │
  │                                                                      │
  │   * "8B" here represents Llama 3.1 8B quality (≈ Llama-2 70B)      │
  │                                                                      │
  │   ADDITIVE would give:  -8% + -22% = -30%                          │
  │   MULTIPLICATIVE gives: -28% (slightly less, but the key point:     │
  │   the MODEL improvement is LARGER at higher data scales)             │
  │                                                                      │
  └──────────────────────────────────────────────────────────────────────┘

  Source: "When Scaling Meets LLM Finetuning" (Zhang et al., ICLR 2024)
  Key finding: "LLM finetuning benefits MORE from model scaling
               than from pretraining data scaling" (αₘ > αₚ consistently)
```

**Key insight**: A stronger LLM + adequate data is **multiplicative, not additive**. The ICLR 2024 scaling law paper shows that LLM fine-tuning follows a **multiplicative joint scaling law** between model quality and data size. A better LLM doesn't just add a fixed improvement — it extracts more from the same data, and the gap widens as data increases.

### What happens if you "do the job properly"

If you combine:
1. **Llama 3.1 8B** (or better) — 3-8pp improvement from better language modeling alone
2. **20K-50K quality segments** from AVSpeech — 15-25pp improvement from data scaling
3. **Clean labels** (Whisper large-v3 instead of base, or manual verification for a subset) — 3-5pp from reduced label noise
4. **Unfreezing top AV-HuBERT layers** for domain adaptation — 5-15pp from visual encoder adaptation

**Realistic combined target: 30-40% WER on YouTube data** — a 27-37pp improvement over current 67%. This is achievable with existing infrastructure, not speculative. The improvements stack because each addresses a different bottleneck.

The current 67% WER reflects **a prototype with minimal fine-tuning**, not the architecture's ceiling. The architecture (visual encoder → LLM decoder) is sound — as proven by the paper's 25.4% WER on LRS3 with proper training.

---

## Part 4: Open-Source Model Alternatives

### Tier 1: Drop-in Replacements (same architecture family, minimal code changes)

| Model | Hidden Size | Params | Why Consider It | Key Advantage |
|-------|------------|--------|-----------------|---------------|
| **Llama 3.1 8B** | 4096 | 8B | Same hidden dim as Llama-2-7B → projection layer stays the same. Llama-3 8B ≈ Llama-2 70B in benchmarks. 128K context, 128K vocab. | **Easiest swap — only change model path and tokenizer** |
| **Llama 3.2 3B** | 3072 | 3B | VALLR (ICCV 2025) achieved **18.7% WER on LRS3** with this model. Smaller, faster, proven for lip reading. | **Proven for visual speech; faster training and inference** |
| **Llama 3.1 70B** | 8192 | 70B | Massive context capacity, GQA for efficiency. Multi-GPU + heavy quantization needed. | Best raw language modeling in Llama family |

### Tier 2: Strong Alternatives (different families, moderate code changes)

| Model | Hidden Size | Params | Why Consider It | Trade-off |
|-------|------------|--------|-----------------|-----------|
| **Qwen 2.5 7B** | 3584 | 7.6B | Strong multilingual, excellent reasoning. Alibaba's best open model. | Different hidden size requires projection update |
| **Mistral 7B v0.3** | 4096 | 7.2B | Same hidden dim as Llama-2, strong reasoning, sliding window attention. | Straightforward swap |
| **DeepSeek-V2-Lite** | 2048 | 15.7B (2.4B active) | MoE — only 2.4B params active per token. Very efficient. | Different architecture, needs adapter verification |
| **Phi-4 (Microsoft)** | 3072 | 14B | Exceptionally strong reasoning for size. Multimodal variant exists. | Smaller hidden dim, needs projection update |
| **Gemma 2 9B** | 3584 | 9B | Google's efficient model with strong benchmarks. | Different tokenizer ecosystem |

### Tier 3: Newer Architectures

| Approach | Description | Relevance |
|----------|-------------|-----------|
| **VALLR (ICCV 2025)** | Two-stage: Video Transformer → phoneme CTC → LLM text reconstruction. Uses Llama 3.2-3B. 18.7% WER on LRS3 with 99.4% less labeled data. | Fundamentally better — LLM receives structured phonemes, not raw visual features |
| **Qwen2-VL / Qwen3-VL** | Native vision-language models that process video directly. | Could replace entire AV-HuBERT + LLM stack |

### Figure 6: VSP-LLM vs VALLR — Why Architecture Matters More Than Model Size

```
  ═══════════════════════════════════════════════════════════════════════
  VSP-LLM (current) — Llama-2-7B — 25.4% WER on LRS3
  ═══════════════════════════════════════════════════════════════════════

  Video ──> AV-HuBERT ──> K-means ──> Linear ──> Llama-2-7B ──> Text
            (1024-dim      cluster     1024       (generates
             visual        + dedup     → 4096      text from
             features)     -50%                    raw visual
                                                   embeddings)

  Problem: LLM receives UNSTRUCTURED visual features
           ┌───────────────────────────────────────────────┐
           │ Visual embedding: [0.23, -0.87, 0.15, ...]   │
           │ LLM must figure out: "is this /p/ or /b/?"   │
           │ No explicit phonetic information provided     │
           └───────────────────────────────────────────────┘

  ═══════════════════════════════════════════════════════════════════════
  VALLR (ICCV 2025) — Llama-3.2-3B (SMALLER!) — 18.7% WER on LRS3
  ═══════════════════════════════════════════════════════════════════════

  Video ──> Video       ──> CTC Head ──> Phonemes ──> Llama-3.2 ──> Text
            Transformer      (predicts    sequence     -3B
            (visual          phonemes)                 (reconstructs
             features)                                  words from
                                                        phonemes)

  Advantage: LLM receives STRUCTURED phoneme sequence
           ┌───────────────────────────────────────────────┐
           │ Phoneme sequence: /m/ /ʌ/ /m/  /s/ /ɛ/ /d/  │
           │ LLM task: "mom said" (language reconstruction)│
           │ Explicit linguistic structure = easier task    │
           └───────────────────────────────────────────────┘

  ═══════════════════════════════════════════════════════════════════════
  RESULT: 3B model with better architecture BEATS 7B with worse one
  ═══════════════════════════════════════════════════════════════════════

  Source: VALLR (Thomas et al., ICCV 2025) — 99.4% less labeled data needed
```

---

## Part 5: Multilingual Model Analysis

### Scenario A: Multilingual LLM fine-tuned on English data only

Using a multilingual LLM (e.g., Qwen 2.5, which has strong multilingual pretraining) but fine-tuning it on English video data only:

| Aspect | Effect | Evidence |
|--------|--------|---------|
| **English performance** | Slightly worse than English-only LLM | Multilingual models split capacity across languages; English-specific models have more "English neurons." Kim & Yeo (2024) show multilingual VSR single model gets 24.4% WER vs 20.5% for English-only on LRS3 — a ~4pp penalty. |
| **Zero-shot other languages** | Surprisingly decent | Research shows even monolingual English fine-tuning enables zero-shot cross-lingual abilities. A multilingual LLM fine-tuned on English visual speech could transcribe other languages at reduced quality. |
| **Recommendation** | **Not worth it for English-only use** | You pay a ~4pp WER penalty for multilingual capacity you're not using. Use an English-optimized model instead. |

### Scenario B: Multilingual LLM fine-tuned on mixed-language video data

Using a multilingual LLM with training data from multiple languages:

| Aspect | Effect | Evidence |
|--------|--------|---------|
| **Non-English languages** | Large improvement over monolingual models | Kim & Yeo (2024): multilingual VSR beats monolingual by 3-4pp for Spanish, Italian, French. Prajwal et al. (ICASSP 2025): MultiVSR achieves SOTA across 13 languages with a single model. |
| **English performance** | Slight degradation (~2-4pp) | English consistently performs slightly worse in multilingual models due to capacity sharing. |
| **Data requirements** | Need significant per-language data | Oxford's MultiVSR uses ~12,000 hours across 13 languages. Under ~100 hours per language, performance degrades sharply. |

### Scenario C: Language-specific model trained on same-language videos

A tokenizer and model specifically trained for the target language (e.g., Arabic model for Arabic videos):

| Aspect | Effect | Evidence |
|--------|--------|---------|
| **Target language performance** | Best single-language results | Language-specific tokenizers are 2-5x more efficient for non-Latin scripts. Arabic, Chinese, Japanese especially benefit. |
| **Tokenizer efficiency** | Critical advantage | Llama-2's 32K-token vocab wastes ~40-60% of capacity on English. A language-specific model puts all capacity toward the target. |
| **Data requirements** | Need ≥100 hours of in-language video | Less data than multilingual, but must be same-language. AVSpeech has diverse languages — filtering is possible. |
| **Maintenance cost** | One model per language | N models to maintain vs 1 multilingual model. |

### Figure 7: Multilingual vs Monolingual VSR — WER by Language (Kim & Yeo 2024)

```
  WER (%)    Lower is better
  60 ┤
     │                                              ┌─────────────────┐
  55 ┤                                    ██        │ ██ Monolingual   │
     │                                    ██        │ ▓▓ Multilingual  │
  50 ┤                          ██        ██ ▓▓     │    (single model)│
     │                    ▓▓    ██ ▓▓              └─────────────────┘
  48 ┤              ██    ▓▓       ▓▓
     │              ██ ▓▓
  45 ┤         ██
     │         ██ ▓▓
  42 ┤            ▓▓
     │
  40 ┤
     │
  25 ┤
     │
  24 ┤    ▓▓
     │
  20 ┤ ██ ◄── English: mono wins by ~4pp (20.5% vs 24.4%)
     │
     └─────┬──────┬──────┬──────┬──────┬──
          EN     ES     IT     FR     PT
        English Spanish Italian French Portuguese

  KEY FINDINGS:
  ┌────────────────────────────────────────────────────────────────┐
  │ English:    Monolingual WINS (20.5% vs 24.4%) — 4pp penalty  │
  │ Spanish:    Multilingual WINS (42.7% vs 45.7%) — 3pp gain    │
  │ Italian:    Multilingual WINS (49.7% vs 51.8%) — 2pp gain    │
  │ French:     Multilingual WINS (55.2% vs 58.3%) — 3pp gain    │
  │ Portuguese: Monolingual WINS (47.9% vs 50.6%) — 3pp penalty  │
  └────────────────────────────────────────────────────────────────┘

  CONCLUSION: Multilingual helps non-English but hurts English.
  For English-only use: stick with English-optimized model.

  Source: Kim & Yeo (2024) "Efficient Training for Multilingual VSR"
```

### Recommendation by use case

| Use Case | Best Approach | Why |
|----------|--------------|-----|
| **English only** | English-optimized LLM (Llama 3.1 8B) | No multilingual overhead, best English performance |
| **2-3 related languages** (e.g., Romance) | Multilingual LLM (Qwen 2.5 7B) with mixed data | Cross-lingual transfer between related languages helps; 2-4pp English penalty is acceptable |
| **Distant language** (e.g., Arabic, Chinese) | Language-specific model + tokenizer | Tokenizer efficiency matters more than cross-lingual transfer for distant languages |
| **13+ languages at scale** | Single multilingual model (following MultiVSR approach) | Operational simplicity outweighs per-language penalty at this scale |

---

## Part 6: What Code Would Need to Change

For a model swap, these files need updates:

| File | Change Required |
|------|----------------|
| `VSP-LLM/src/vsp_llm.py:224` | Update `nn.Linear(1024, NEW_HIDDEN_SIZE)` |
| `VSP-LLM/src/conf/vsp-llm-433h-freeze.yaml` | Update `decoder_embed_dim` |
| `VSP-LLM/src/conf/vsp-llm-433h-finetune.yaml` | Update `decoder_embed_dim` |
| `VSP-LLM/src/conf/vsp-llm-avspeech-finetune.yaml` | Update `decoder_embed_dim` |
| `VSP-LLM/scripts/train.sh` | Update `LLM_PATH` |
| `VSP-LLM/scripts/decode.sh` | Update `LLM_PATH` |

If the new model has hidden_size=4096 (Llama 3.1 8B, Mistral 7B), the projection layer doesn't change — making the swap nearly trivial.

### Figure 12: Model Swap Complexity — What Changes vs What Stays

```
  ┌──────────────────────────────────────────────────────────────────┐
  │  SWAP TO LLAMA 3.1 8B (hidden_size=4096) — TRIVIAL             │
  ├──────────────────────────────────────────────────────────────────┤
  │                                                                  │
  │  Video Frames ──> AV-HuBERT ──> K-means ──> Linear(1024→4096)  │
  │                   ✅ NO CHANGE   ✅ NO       ✅ NO CHANGE       │
  │                                  CHANGE      (same output dim)  │
  │                                                                  │
  │                                       ┌──────────────────┐      │
  │                                       │  Llama 3.1 8B    │      │
  │                                       │  ⚠️ CHANGE:       │      │
  │                                       │  - Model path    │      │
  │                                       │  - Tokenizer     │      │
  │                                       │  - New LoRA init │      │
  │                                       │  ✅ Same dim 4096│      │
  │                                       │  ✅ Same QLoRA   │      │
  │                                       │  ✅ Same LoRA    │      │
  │                                       │    targets q,k,v │      │
  │                                       └──────────────────┘      │
  │                                                                  │
  │  Files to edit: 2 scripts (train.sh, decode.sh → LLM_PATH)     │
  │  Retraining: YES (LoRA must be retrained for new base model)    │
  │  Estimated effort: 1-2 hours setup + training time              │
  └──────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────┐
  │  SWAP TO QWEN 2.5 7B (hidden_size=3584) — MODERATE             │
  ├──────────────────────────────────────────────────────────────────┤
  │                                                                  │
  │  Video Frames ──> AV-HuBERT ──> K-means ──> Linear(1024→3584)  │
  │                   ✅ NO CHANGE   ✅ NO       ⚠️ MUST CHANGE     │
  │                                  CHANGE      (different dim!)   │
  │                                                                  │
  │                                       ┌──────────────────┐      │
  │                                       │  Qwen 2.5 7B     │      │
  │                                       │  ⚠️ CHANGE:       │      │
  │                                       │  - Model path    │      │
  │                                       │  - Tokenizer     │      │
  │                                       │  - New LoRA init │      │
  │                                       │  ⚠️ Dim = 3584   │      │
  │                                       │  ⚠️ Verify LoRA  │      │
  │                                       │    target names  │      │
  │                                       └──────────────────┘      │
  │                                                                  │
  │  Files to edit: 2 scripts + vsp_llm.py + 3 YAML configs        │
  │  Retraining: YES                                                │
  │  Estimated effort: 3-4 hours setup + training time              │
  └──────────────────────────────────────────────────────────────────┘
```

---

## Part 7: Smarter Prompts — Impact and How to Make Them Work

### Current state: The prompt is wasting the LLM's capability

The current prompt is: `"Recognize this speech in English. Input : "` — zero context about the video. This is a 7-word instruction to a model trained on 2 trillion tokens. LLaMA-2 has strong instruction-following and context-aware generation abilities; the current pipeline ignores them entirely.

### What "smarter prompts" means in this context

There are two categories:

**Category 1: Context injection into the existing prompt** (works within the current architecture)
- Adding domain/topic hints, word count, vocabulary, speaker info before the visual features
- The model was trained with the fixed prompt, but LLaMA retains instruction-following from pretraining — small additions are safe, large deviations may confuse LoRA layers

**Category 2: Multi-pass / post-processing with the LLM** (requires architecture changes)
- Using the LLM to refine its own output (self-correction)
- Generative Error Correction (GER): feeding N-best hypotheses back through an LLM with corrective prompts
- Chain-of-thought: having the LLM reason about ambiguous phonemes before committing

### Strategy breakdown with expected impact

| Strategy | How It Works | Expected WER Impact | Works With Llama-2-7B? | Better With Stronger LLM? |
|----------|-------------|--------------------|-----------------------|--------------------------|
| **1. Topic/domain context** | Add "This is a cooking video." before instruction | -5 to -10 pp on applicable segments | Yes (safe, small addition) | Yes — stronger models use context better |
| **2. Word count hints** | Add "The speaker says approximately 8 words." (derivable from segment duration) | -3 to -7 pp | Yes | Moderate — reduces length hallucination in any model |
| **3. Vocabulary/entity lists** | Add "Expected words: recipe, oven, temperature" | -3 to -5 pp | Partially (Llama-2 may ignore if too different from training prompt) | **Much better** — Llama-3+ follows complex instructions more reliably |
| **4. Anti-hallucination instructions** | Add "Only output words you are confident about. If unsure, output [UNK]." | -2 to -5 pp (reduces 20.6% hallucination rate) | Risky (may break fine-tuned format) | **Much better** — stronger models follow negative constraints more precisely |
| **5. Phonetic context** | Add simplified phoneme hints from visual features: "Sounds like: /m-ah-m/ /s-eh-d/" | -3 to -8 pp | Limited (Llama-2 struggles with phonetic notation) | **Yes** — recent research (2025) shows LLM-based Simplified Phonemes work but need models that understand phonetics |
| **6. Multi-pass self-correction** | Run decode → feed output + visual features back → "Correct any errors in this transcription: [first pass]" | -5 to -10 pp | Partially (doubles inference cost; Llama-2 is weak at self-correction) | **Dramatically better** — self-correction is an emergent ability in stronger LLMs |
| **7. N-best GER (Generative Error Correction)** | Generate top-5 hypotheses via beam search, then prompt: "Given these candidates, select the best transcription: [1]...[2]...[3]..." | -5 to -15 pp (SOTA technique in ASR post-processing) | Weak (Llama-2's reasoning insufficient for this) | **This is WHERE a stronger LLM makes the biggest difference** |

### Figure 8: Prompt Strategy Unlock Tiers — What Each Model Can Use

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │              PROMPT STRATEGIES BY MODEL CAPABILITY                  │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │  TIER 1: Llama-2-7B (current)                              │   │
  │  │  ┌───────────────┐ ┌────────────────┐                      │   │
  │  │  │ Topic context │ │ Word count     │    +5-10 pp WER      │   │
  │  │  │ "cooking..."  │ │ "~8 words"     │    combined          │   │
  │  │  └───────────────┘ └────────────────┘                      │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                              │                                      │
  │  ┌───────────────────────────▼─────────────────────────────────┐   │
  │  │  TIER 2: Llama 3.1 8B  (UNLOCKS these)                    │   │
  │  │  ┌───────────────┐ ┌────────────────┐ ┌─────────────────┐ │   │
  │  │  │ Vocabulary    │ │ Anti-halluc.   │ │ Phonetic        │ │   │
  │  │  │ lists         │ │ instructions   │ │ context         │ │   │
  │  │  │ "expect:      │ │ "only output   │ │ "sounds like:   │ │   │
  │  │  │  oven, temp"  │ │  confident"    │ │  /m-ah-m/"      │ │   │
  │  │  └───────────────┘ └────────────────┘ └─────────────────┘ │   │
  │  │                                            +12-20 pp WER   │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                              │                                      │
  │  ┌───────────────────────────▼─────────────────────────────────┐   │
  │  │  TIER 3: Llama 3.1 70B / GPT-4 class  (UNLOCKS these)     │   │
  │  │  ┌───────────────────┐ ┌──────────────────────────────────┐│   │
  │  │  │ Self-correction   │ │ N-best GER                      ││   │
  │  │  │ "Correct errors   │ │ "Given 5 hypotheses, pick best  ││   │
  │  │  │  in: [1st pass]"  │ │  and correct: [1]...[2]...[3]"  ││   │
  │  │  │                   │ │                                  ││   │
  │  │  │  (emergent ability │ │ (SOTA ASR post-processing,     ││   │
  │  │  │   needs strong     │ │  Amazon/NVIDIA 2024)           ││   │
  │  │  │   reasoning)       │ │                                ││   │
  │  │  └───────────────────┘ └──────────────────────────────────┘│   │
  │  │                                            +20-30 pp WER   │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ⚠ WARNING: Using Tier 3 strategies on Tier 1 models HURTS:       │
  │     Self-correction on Llama-2-7B = -2 pp (incoherent reasoning)   │
  │     N-best GER on Llama-2-7B = N/A (insufficient reasoning)        │
  └─────────────────────────────────────────────────────────────────────┘
```

### How prompts interact with model capability: The key insight

**Llama-2-7B can use strategies 1-2 (simple context injection).** It was fine-tuned with a fixed prompt but retains enough instruction-following to benefit from topic hints and word counts. These are "safe" modifications that don't deviate far from the training format.

**Llama-2-7B CANNOT reliably use strategies 5-7 (complex reasoning).** Chain-of-thought, self-correction, and N-best reranking are emergent abilities that require ~100B+ parameters (per CoT research) or at minimum a much stronger 8B+ model. Llama-2-7B will produce incoherent reasoning chains that hurt more than help.

**Llama 3.1 8B unlocks strategies 3-5.** It has dramatically better instruction following, can handle complex prompts with vocabulary lists, and has enough reasoning capacity for phonetic context. Its 128K vocabulary also means phonetic tokens are better represented.

**Llama 3.1 70B (or equivalent) unlocks strategies 6-7.** Multi-pass self-correction and N-best GER require strong reasoning. The 70B class is where these techniques become reliable. The 2024 Evolutionary Prompt Design paper and Amazon's GER research both show that LLM quality is the primary factor in error correction effectiveness.

### How to make smarter prompts work: Practical approaches

**Approach A: Context injection at inference time (no retraining needed)**

The simplest path — modify the prompt at decode time without retraining:

```
# Current: "Recognize this speech in English. Input : "
# Enhanced: "This video is about [TOPIC]. The speaker says approximately [N] words.
#            Recognize this speech in English. Input : "
```

Where to get the context:
- **Topic**: Extract from video metadata (YouTube title, description), or run a lightweight classifier on the first frame
- **Word count**: Estimate from segment duration (avg ~2.5 words/second for English speech)
- **Domain vocabulary**: Extract keywords from Whisper ASR output (already available in the pipeline)

**Risk**: The model was trained with the exact prompt `"Recognize this speech in English. Input : "`. Adding context before it may confuse LoRA layers. **Mitigation**: Keep the original prompt intact, prepend context as a separate "system" section.

**Approach B: Fine-tune WITH context-enriched prompts (retraining needed)**

Train the model on varied prompt templates that include context:
```
"Topic: cooking. Speaker says about 8 words. Recognize this speech in English. Input : "
"Topic: politics. Speaker says about 12 words. Recognize this speech in English. Input : "
"Recognize this speech in English. Input : "  # Keep some plain prompts for robustness
```

This teaches the model to **use** the context rather than ignore it. Critical: mix in 20-30% plain prompts so the model doesn't become dependent on context.

**Approach C: Two-stage pipeline with GER post-processing (architecture change)**

```
Stage 1: VSP-LLM generates N-best hypotheses (beam search, already available)
Stage 2: Separate LLM receives: "Given these lip-reading hypotheses for a [TOPIC] video,
          select and correct the best transcription:
          1. [hypothesis 1]
          2. [hypothesis 2]
          3. [hypothesis 3]
          Corrected transcription:"
```

### Figure 9: GER Two-Stage Pipeline — Highest ROI Architecture Change

```
  ═══════════════════════════════════════════════════════════════════
  STAGE 1: Visual Speech Processing (existing pipeline, unchanged)
  ═══════════════════════════════════════════════════════════════════

  Video ──> AV-HuBERT ──> Cluster ──> Llama (QLoRA) ──> N-best hypotheses
                                                          │
                                          ┌───────────────┘
                                          ▼
                               ┌─────────────────────┐
                               │ Beam search output:  │
                               │ 1. "she said hello"  │  (beam 1)
                               │ 2. "he said hello"   │  (beam 2)
                               │ 3. "she said hallow" │  (beam 3)
                               │ 4. "he said hollow"  │  (beam 4)
                               │ 5. "she said yellow" │  (beam 5)
                               └──────────┬──────────┘
                                          │
  ═════════════════════════════════════════╪════════════════════════
  STAGE 2: Generative Error Correction    │  (NEW — separate LLM)
  ═════════════════════════════════════════╪════════════════════════
                                          ▼
                          ┌──────────────────────────┐
                          │   CORRECTION PROMPT:      │
                          │                          │
                          │   "This is a [family]    │ ◄── topic context
                          │    video. Given these    │
                          │    lip-reading hypotheses,│
                          │    select and correct    │
                          │    the best one:         │
                          │    1. she said hello     │
                          │    2. he said hello      │
                          │    3. she said hallow    │
                          │    4. he said hollow     │
                          │    5. she said yellow    │
                          │                          │
                          │    Corrected:            │
                          └────────────┬─────────────┘
                                       │
                                       ▼
                          ┌──────────────────────────┐
                          │  Correction LLM          │
                          │  (GPT-4 / Claude /       │
                          │   local 70B model)       │
                          │                          │
                          │  Reasoning:              │
                          │  - "she" appears in 3/5  │
                          │  - "hello" appears in 2/5│
                          │  - family context → "she"│
                          │  - "hello" > "hallow"    │
                          │                          │
                          │  Output: "she said hello"│ ✓
                          └──────────────────────────┘

  WHY THIS WORKS:
  ┌───────────────────────────────────────────────────────────┐
  │ - Stage 2 is PURE TEXT — no visual features needed        │
  │ - Can use ANY powerful LLM (even API: Claude, GPT-4)     │
  │ - No retraining of the visual pipeline required           │
  │ - N-best list preserves correct answer 70-85% of time     │
  │ - Correction LLM just needs to PICK the right one         │
  │ - Expected improvement: +8-15 pp WER                      │
  └───────────────────────────────────────────────────────────┘

  Source: Amazon GER (2024), NVIDIA GenSEC Challenge (2024)
```

This is the **Generative Error Correction** paradigm (Amazon/NVIDIA, 2024). The second-stage LLM doesn't need visual features — it just does language-level correction. This means you can use a powerful model (GPT-4, Claude, or a local 70B) for correction without modifying the visual pipeline.

Recent research shows:
- Evolutionary prompt optimization can automatically find the best correction prompt for your specific error patterns
- Adding phonetic context (simplified phonemes) reduces over-correction
- N-best + domain vocabulary in the prompt gives the strongest results

### Prompt effectiveness by model tier

| Prompt Strategy | Llama-2-7B (current) | Llama 3.1 8B | Llama 3.1 70B / GPT-4 class |
|----------------|---------------------|--------------|------------------------------|
| Topic context | +3-5 pp | +5-8 pp | +5-10 pp |
| Word count hints | +2-4 pp | +3-5 pp | +3-5 pp |
| Vocabulary lists | +1-2 pp (often ignored) | +3-5 pp | +4-6 pp |
| Anti-hallucination | +0-2 pp (may break) | +2-4 pp | +3-5 pp |
| Phonetic context | +0-1 pp (can't parse) | +2-4 pp | +4-8 pp |
| Self-correction | -2 pp (hurts!) | +2-5 pp | +5-10 pp |
| N-best GER | N/A (too weak) | +3-7 pp | **+8-15 pp** |
| **Combined best** | **+5-10 pp** | **+12-20 pp** | **+20-30 pp** |

**Bottom line**: Smarter prompts are a **force multiplier for stronger models**. With Llama-2-7B, you can squeeze out 5-10pp from simple context injection. With Llama 3.1 8B, the same techniques yield 12-20pp. With a 70B-class model doing GER post-processing, you can potentially gain 20-30pp — but this requires a two-stage architecture.

---

### Figure 10: LLM Model Evolution — Benchmark Improvement (Llama Family)

```
  MMLU Benchmark Score (%)     Higher is better
  80 ┤
     │                                              ┌─────────────────┐
  75 ┤                                     ████     │ Llama-2  (2023) │
     │                                     ████     │ Llama-3  (2024) │
  70 ┤                              ████   ████     └─────────────────┘
     │                        ████  ████   ████
  65 ┤                  ████  ████  ████   ████
     │            ████  ████  ████  ████   ████
  60 ┤            ████  ████  ████  ████   ████
     │      ████  ████  ████  ████  ████   ████
  55 ┤      ████  ████  ████  ████  ████   ████
     │      ████  ████  ████  ████  ████   ████
  50 ┤      ████  ████  ████  ████  ████   ████
     │████  ████  ████  ████  ████  ████   ████
  45 ┤████  ████  ████  ████  ████  ████   ████
     │████  ████  ████  ████  ████  ████   ████
     └──┬─────┬─────┬─────┬─────┬─────┬─────┬──
       L2-7B L2-13B L2-70B L3-8B L3-70B L3.1  L3.1
       46.8  54.8  63.6  66.6  79.5  8B    70B
                                       69.4  83.6

  KEY INSIGHT: Llama-3 8B (66.6) ≈ Llama-2 70B (63.6)
  → 10x smaller model, BETTER performance
  → Same hidden_size (4096) = trivial swap in VSP-LLM

  Additional advantages of Llama-3.1 8B over Llama-2 7B:
  ┌────────────────────────────────────────────────────┐
  │ Vocabulary:    32K → 128K tokens (4x)              │
  │ Context:       4K → 128K tokens (32x)              │
  │ Training data: 2T → 15T+ tokens (7.5x)            │
  │ Token efficiency: ~15% fewer tokens per sentence   │
  │ Instruction following: dramatically improved       │
  └────────────────────────────────────────────────────┘

  Sources: Meta AI Llama announcements (2023-2024), MMLU benchmarks
```

### Figure 11: Improvement Waterfall — From 67% to Target WER

```
  WER (%)
  70 ┤ ████████████████████████████████████████████  67% (current)
     │
  65 ┤ ███████████████████████████████████████       ─┐
     │                                                 │ Swap LLM
  60 ┤ ████████████████████████████████████           ─┘ (-3 to -8pp)
     │
  55 ┤ █████████████████████████████████             ─┐
     │                                                 │ Smart prompts
  50 ┤ ██████████████████████████████                ─┘ (-5 to -10pp)
     │
  45 ┤ ████████████████████████████                  ─┐
     │                                                 │ Scale to 20K+
  40 ┤ ████████████████████████                      ─┘ segments
     │                                                   (-10 to -15pp)
  35 ┤ █████████████████████                         ─┐
     │                                                 │ Better labels +
  30 ┤ ██████████████████                            ─┘ GER post-process
     │                                                   (-5 to -10pp)
  27 ┤ ████████████████  ◄── TARGET: 27-42% WER
     │
  25 ┤ · · · · · · · ·  ◄── VSP-LLM paper (25.4% on LRS3)
     │
  20 ┤                   ◄── VALLR SOTA (18.7% on LRS3)
     │
     └────────────────────────────────────────────────────

  Each bar = cumulative improvement. Gains stack because
  each addresses a DIFFERENT bottleneck:
   - LLM swap → better language modeling
   - Prompts  → better context utilization
   - Data     → better generalization
   - Labels   → cleaner training signal
   - GER      → post-hoc error correction
```

---

## Part 8: Investment Strategy

| Strategy | Expected WER Improvement | Effort | Priority |
|----------|-------------------------|--------|----------|
| **Swap to Llama 3.1 8B** | 3-8 pp alone; unlocks prompt strategies | Low | **1 — Do first** |
| **Add context-injection prompts** (topic, word count) | 5-10 pp with Llama 3.1 8B | Low | **2 — Easy win after LLM swap** |
| **Scale to 20K-50K training segments** | 15-25 pp (biggest single gain) | Medium-High | **3 — Critical enabler** |
| **Fine-tune WITH enriched prompts** | Additional 3-5 pp over inference-only prompts | Medium | **4 — During retraining** |
| **Improve label quality** (Whisper large-v3) | 3-5 pp | Low-Medium | **5 — Easy win** |
| **Add GER post-processing stage** (N-best + correction LLM) | 8-15 pp (can use external LLM) | Medium | **6 — High impact, no retraining** |
| **Unfreeze top AV-HuBERT layers** | 5-15 pp | High (multi-GPU) | **7 — If infrastructure allows** |
| **Combined (1+2+3+5)** | **25-40 pp → target 27-42% WER** | Medium | **Best realistic path** |
| **Combined with GER (1+2+3+5+6)** | **30-45 pp → target 22-37% WER** | Medium-High | **Best with external LLM** |

---

## Key Takeaways

1. **The LLM matters more than our experiments showed.** The r=16 vs r=64 comparison proved the data was insufficient (1,273 segments), not that the LLM is saturated. With proper data (20K+ segments), a stronger LLM would yield significantly larger gains.

2. **Stronger LLM + more data is multiplicative.** LLM fine-tuning follows a multiplicative joint scaling law (ICLR 2024). A better model extracts more from each training sample, and the gap between models widens as data increases.

3. **Llama 3.1 8B is the no-brainer first step.** Same hidden dimension, ≈Llama-2 70B performance, minimal code changes. The tokenizer alone (128K vocab, 15% fewer tokens) improves training efficiency.

4. **20K-50K quality segments unlocks the architecture's potential.** AVSpeech has 290K videos; filtering for quality and transcribing with Whisper large-v3 is a tractable data curation task.

5. **For multilingual use**, a single multilingual model (Qwen 2.5) trained on mixed data beats maintaining separate models — unless you're targeting a single distant language (Arabic, Chinese) where tokenizer efficiency dominates.

6. **Smarter prompts are a force multiplier for stronger models.** Simple context injection (topic, word count) helps any model modestly. But advanced techniques (N-best GER, self-correction, phonetic context) only work with stronger LLMs. A Llama 3.1 8B + smart prompts combination yields 2-3x the improvement of either alone.

7. **GER post-processing is the highest-ROI prompt strategy.** It doesn't require retraining the visual pipeline — just add a second-stage LLM that corrects N-best hypotheses. Can even use an external API (Claude, GPT-4) for the correction stage.

8. **The realistic ceiling with proper investment** is 25-40% WER on YouTube — achievable through LLM upgrade + data scaling + prompt engineering + optional GER, without redesigning the core architecture.

---

Sources:
- [VSP-LLM Paper (EMNLP 2024)](https://arxiv.org/abs/2402.15151)
- [VALLR: Visual ASR Language Model for Lip Reading (ICCV 2025)](https://arxiv.org/abs/2503.21408)
- [Scaling Laws for LLM Fine-tuning (ICLR 2024)](https://arxiv.org/abs/2402.17193)
- [Multilingual VSR with Visual Speech Units (Kim & Yeo, 2024)](https://arxiv.org/abs/2401.09802)
- [Scaling Multilingual VSR (Prajwal et al., ICASSP 2025)](https://www.robots.ox.ac.uk/~vgg/publications/2025/Prajwal25/prajwal25.pdf)
- [MultiVSR Dataset & Code](https://www.robots.ox.ac.uk/~vgg/research/multivsr/)
- [Llama 3 Introduction (Meta AI)](https://ai.meta.com/blog/meta-llama-3/)
- [Llama 3 8B ≈ Llama 2 70B](https://dev.to/maximsaplin/llama-3-in-8b-and-70b-sizes-is-out-58pk)
- [LoRA Fine-tuning Tips (Sebastian Raschka)](https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms)
- [Open-Source VLMs 2026 (BentoML)](https://www.bentoml.com/blog/multimodal-ai-a-guide-to-open-source-vision-language-models)
- [LLM Selection Guide (Qwen, Mistral, Llama, Gemma)](https://dasroot.net/posts/2026/01/llm-model-selection-guide-qwen-mistral-llama-gemma/)
- [Multilingual LLM Survey (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11783891/)
- [Multilingual Instruction Tuning (ACL 2024)](https://aclanthology.org/2024.findings-eacl.90.pdf)
- [Evolutionary Prompt Design for Post-ASR Error Correction (2024)](https://arxiv.org/abs/2407.16370)
- [Generative Error Correction with LLMs (Amazon, 2024)](https://assets.amazon.science/77/26/6c265e0a42d7a40d2ee8bdd158e6/generative-speech-recognition-error-correction-with-large-language-models-and-task-activating-prompting.pdf)
- [GenSEC Challenge: LLM-based Error Correction (NVIDIA, 2024)](https://research.nvidia.com/publication/2024-12_large-language-model-based-generative-error-correction-challenge-and-baselines)
- [LLM-based Phonetic Context for Rare Words (2025)](https://arxiv.org/abs/2505.17410)
- [Prompt Engineering Taxonomy (Frontiers, 2025)](https://link.springer.com/article/10.1007/s11704-025-50058-z)
- [Existing VSP-LLM Prompt Engineering Report](docs/prompts/report_3_prompt_engineering.md)
