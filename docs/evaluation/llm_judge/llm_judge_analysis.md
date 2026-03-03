# LLM-as-a-Judge Gold Standard Evaluation

## Section 1: Methodology

### Judgment Protocol

Claude Opus 4.6 evaluated 1,497 hypothesis-reference pairs from the baseline VSP model 
using a 3-level scale:

| Code | Label | Definition |
|------|-------|------------|
| **Y** | Yes | Meaning clearly conveyed |
| **P** | Partial | Some meaning preserved, but key info lost or distorted |
| **N** | No | Wrong topic, hallucination, empty, or misleading |

**Blind evaluation:** Batch files contained only reference + hypothesis text. No WER, IS, 
tier, or other metrics were visible during judging to prevent anchoring bias.

**Conservative tie-breaking:** Y vs P -> P; P vs N -> N.

**Pre-classification:** 70 empty-hypothesis pairs auto-classified as N.

**Batches:** 15 batches of ~100 pairs each, shuffled with fixed seed (42).

### Intra-Rater Reliability

30 duplicate pairs were embedded across batches (6 per IS tier).

- **Exact agreement:** 86.7% (26/30)
- **Lenient agreement (Y+P vs N):** 100.0% (30/30)

## Section 2: Gold Standard Capture Rate

| Metric | Count | Rate |
|--------|-------|------|
| **LLM Judge: Y (strict)** | 345 | **23.0%** |
| **LLM Judge: Y+P (lenient)** | 971 | **64.9%** |
| IS >= 3.0 | 597 | 39.9% |
| IS + salvage (llm_prob >= 0.5) | 762 | 50.9% |

### Judgment Distribution

| Judgment | Count | % |
|----------|-------|-----|
| Y (meaning conveyed) | 345 | 23.0% |
| P (partial) | 626 | 41.8% |
| N (meaning lost) | 526 | 35.1% |

## Section 3: Agreement with IS Framework

### Strict: LLM Y vs IS >= 3.0

|  | IS >= 3.0 | IS < 3.0 |
|--|-----------|----------|
| **LLM Y** | 326 | 19 |
| **LLM P+N** | 271 | 881 |

- Accuracy: 0.806
- Precision: 0.945
- Recall: 0.546
- F1: 0.692
- Cohen's kappa: 0.5651

### Lenient: LLM Y+P vs IS >= 3.0

|  | IS >= 3.0 | IS < 3.0 |
|--|-----------|----------|
| **LLM Y+P** | 594 | 377 |
| **LLM N** | 3 | 523 |

- Accuracy: 0.746
- Precision: 0.612
- Recall: 0.995
- F1: 0.758
- Cohen's kappa: 0.5211

### 3x5 Breakdown: LLM Judge x IS Tier

| LLM | Tier 1 (Failed) | Tier 2 (Poor) | Tier 3 (Fair) | Tier 4 (Good) | Tier 5 (Excellent) |
|-----|-----------------|---------------|---------------|---------------|-------------------|
| **Y** | 0 | 2 | 17 | 100 | 226 |
| **P** | 5 | 81 | 272 | 218 | 50 |
| **N** | 234 | 253 | 36 | 3 | 0 |

## Section 4: Agreement with llm_context_prob Heuristic

|  | Heuristic >= 0.5 | Heuristic < 0.5 |
|--|------------------|-----------------|
| **LLM Y** | 343 | 2 |
| **LLM P+N** | 414 | 738 |

- Accuracy: 0.722
- Cohen's kappa: 0.4476

## Section 5: Correlation Analysis

LLM judge encoded as Y=1, P=0.5, N=0.

| Metric | Pearson r | Spearman rho |
|--------|-----------|-------------|
| IS | 0.8495 | 0.8575 |
| Semantic Sim | 0.8459 | 0.8455 |
| Phonetic Sim | 0.8057 | 0.8216 |
| WER | -0.7143 | -0.8108 |
| WWER | -0.7408 | -0.7978 |
| llm_context_prob | 0.8225 | 0.8336 |

## Section 6: Partial Judgment Analysis

Total P judgments: 626

### Preservation Frequency

| Tag | Count | % of P |
|-----|-------|--------|
| struct | 556 | 88.8% |
| key | 417 | 66.6% |
| sem | 163 | 26.0% |
| phon | 104 | 16.6% |
| topic | 40 | 6.4% |
| names | 4 | 0.6% |

### Loss Frequency

| Tag | Count | % of P |
|-----|-------|--------|
| detail | 347 | 55.4% |
| sem | 345 | 55.1% |
| key | 160 | 25.6% |
| names | 129 | 20.6% |
| topic | 19 | 3.0% |
| struct | 4 | 0.6% |

### Most Common P Profiles

| Profile | Count |
|---------|-------|
| `P:key+struct/detail-sem` | 84 |
| `P:key+sem+struct/detail` | 80 |
| `P:key+struct/sem` | 47 |
| `P:key+struct/detail` | 41 |
| `P:struct/key-sem` | 33 |
| `P:phon+struct/key-sem` | 32 |
| `P:key+struct/names-sem` | 25 |
| `P:key+sem+struct/names` | 17 |
| `P:key/detail-sem` | 14 |
| `P:struct/key-names-sem` | 13 |

## Section 7: Disagreement Deep Dive

- **LLM=Y but IS<3.0** (salvage validated): 19 segments
- **LLM=N but IS>=3.0** (IS false positives): 3 segments

See `examples/` directory for curated disagreement examples:
- `disagreement_llm_yes_is_fail.md` — model output is useful despite bad metrics
- `disagreement_llm_no_is_pass.md` — metrics are too generous
- `partial_judgment_showcase.md` — the boundary zone
- `agreement_showcase.md` — validation of IS framework

## Section 8: Topic-Level Analysis

| Topic | Y% | P% | N% | n |
|-------|----|----|----|---|
| Business/Finance | 30.4 | 45.7 | 23.9 | 46 |
| Cooking/Food | 28.2 | 41.9 | 29.9 | 117 |
| DIY/Home | 25.9 | 22.2 | 51.9 | 27 |
| Education/Academic | 33.7 | 43.0 | 23.3 | 86 |
| Entertainment | 15.9 | 44.9 | 39.1 | 69 |
| Medical/Health | 23.1 | 43.6 | 33.3 | 39 |
| Other | 20.1 | 41.6 | 38.3 | 899 |
| Politics/News | 23.5 | 50.0 | 26.5 | 34 |
| Religion/Spirituality | 29.4 | 23.5 | 47.1 | 17 |
| Sports/Fitness | 29.0 | 45.2 | 25.8 | 31 |
| Technology | 29.5 | 42.4 | 28.0 | 132 |

## Section 9: Implications

### IS Threshold Calibration

The IS >= 3.0 threshold captures 39.9% of segments as 'properly captured.' 
The LLM judge assigns Y (clear meaning) to 23.0% and Y+P to 64.9%.

The LLM strict rate is **lower** than IS >= 3.0, suggesting IS may be slightly generous 
at the boundary. However, including P judgments (lenient) likely aligns more closely.

### Effective Capture Rate

The gold standard LLM lenient capture rate of 64.9% compares with:
- IS >= 3.0: 39.9%
- IS + salvage: 50.9%

## Section 10: Visual and Topic Context Analysis

**Question:** Would visual context from the source videos or general topic context have helped the LLM judge make better interpretations of ambiguous hypothesis text?

**Answer:** Yes — both visual context and topic context would substantially help. The evidence falls into two complementary categories.

### 10.1 Topic/Domain Context

The model correctly lip-reads the phonetic shape of domain-specific words but resolves them to the wrong vocabulary domain. ~284 segments (19% of all data) show topic drift or wrong-domain confusion patterns where a simple topic label ("this is a cooking video") would constrain the LLM decoder.

**Examples of domain vocabulary confusion:**
- REF "costal cartilages" → HYP "cause our hormones" (Medical: phonetically close, wrong domain)
- REF "probiotics and 2 tablespoons of apple cider vinegar" → HYP "permafrost at two tablespoons per square foot" (Cooking: preserves "tablespoons" but swaps food→geology)
- REF "interchangeable lens" → HYP "judicial landscape" (Technology: phonetically plausible, total domain swap)
- REF "oxidation rates of these carbohydrates" → HYP "art to action strides of this non profit" (Education: fluent but wrong topic)

**Failure mode breakdown confirming topic context need:**
- In N-coded segments: 27.0% show Total Topic Drift, 18.8% show Phonetically Similar but Wrong Topic
- In P-coded segments: 6.7% show explicit domain confusion (phonetically close, wrong topic)

### 10.2 Visual/Spatial Context

48+ videos contained segments with deictic references ("this", "here", "look at this") — language that inherently depends on visual context. The model cannot resolve these without seeing what the speaker is pointing at.

**DIY/Home content** is the most affected topic: 51.9% N-rate (vs 35.1% overall) because DIY is inherently visual ("attach this piece here", "sand along the grain"). Without seeing the physical demonstration, the speech is uninterpretable.

### 10.3 Judgment Rates by Visually-Rich Topic

| Topic | Total | Y% | P% | N% | Context Need |
|-------|-------|----|----|----|--------------|
| DIY/Home | 27 | 25.9 | 22.2 | **51.9** | Highest — physical demonstrations |
| Religion/Spirituality | 17 | 29.4 | 23.5 | **47.1** | Specialized vocabulary |
| Entertainment | 69 | 15.9 | 44.9 | **39.1** | Scene-dependent dialogue |
| Medical/Health | 39 | 23.1 | 43.6 | 33.3 | Anatomy, procedures |
| Cooking/Food | 117 | 28.2 | 41.9 | 29.9 | Ingredients, visible actions |
| Technology | 132 | 29.5 | 42.4 | 28.0 | Product names, screens |
| Sports/Fitness | 31 | 29.0 | **45.2** | 25.8 | Highest P — close but missing sport-specific vocab |

### 10.4 Plausible-but-Wrong-Context Outputs

90 segments produced fluent, grammatically correct output that was plausible in *some* context but completely wrong for the actual video. These are the most dangerous because they could fool a reader:

- REF "overhead lights which are mostly fluorescent" → HYP "overheard ghost whisperer music for that scene"
- REF "glucose and the glucose in maltose" → HYP "girls aged 10 to 12 years" (nutrition→demographics)

Visual context would instantly disambiguate these — seeing a lab, studio, or food would constrain the model's output space.

### 10.5 Implications for System Improvement

1. **Topic context injection** (easiest win): Providing a topic label at decode time ("cooking", "medical", "technology") would constrain the LLM's vocabulary priors. This aligns with Mission 8 (Prompt Engineering) — topic hints in the system prompt could convert many P→Y and some N→P.

2. **Visual scene context** (harder but higher ceiling): Incorporating scene-level features (object detection, scene classification) could provide grounding that pure lip-reading cannot. This is a longer-term architectural change.

3. **Expected impact**: Topic context alone could improve ~284 segments (19%); visual grounding could additionally help DIY/Home (51.9% N-rate) and other visually-dependent content.

---

## Section 11: Context-Aware Re-Evaluation Results

> Full standalone analysis: [context_eval/context_eval_analysis.md](context_eval/context_eval_analysis.md)

### 11.1 Protocol

All 1,497 pairs were re-evaluated in context-aware mode. The judgment instruction changed from a pure blind comparison to: *"Consider the likely topic/domain of each reference. Judge whether a viewer with that domain context would understand the hypothesis."* No explicit topic labels were injected — the judge was asked to infer topic from the reference text, simulating how a human viewer who knows the video type would interpret the transcript. The same 3-level Y/P/N scale and conservative tie-breaking rules applied. 30 duplicate pairs (same as blind pass) were included for cross-condition reliability.

**Coverage:** 71 auto-N (empty hypothesis) + 1,426 unique LLM-judged + 30 duplicates = 1,456 batch entries.

### 11.2 Key Finding: Context Mode Is Stricter, Not More Lenient

| Judgment | Blind (1,497) | Context (1,497) | Delta |
|----------|---------------|-----------------|-------|
| **Y (full success)** | 345 (23.0%) | 225 (15.0%) | **−8.0pp** |
| **P (partial)** | 626 (41.8%) | 705 (47.1%) | **+5.3pp** |
| **N (failure)** | 526 (35.1%) | 567 (37.9%) | +2.8pp |
| **Y+P** | 971 (64.9%) | 930 (62.1%) | **−2.7pp** |

Context awareness made the judge **more conservative** — applying domain knowledge raised the bar for what counts as "full success". A hypothesis that seemed adequate without domain context often revealed vocabulary mismatches when the judge knew the subject.

**Net transitions:** 230 downgrades vs 68 upgrades → net −162 (−10.8%). 80.1% of pairs received the same judgment in both conditions.

### 11.3 Transition Matrix

| Blind→Context | →Y | →P | →N |
|---|---|---|---|
| **Y** | 207 | **138** | 0 |
| **P** | 17 | 517 | **92** |
| **N** | 1 | 50 | 475 |

The dominant off-diagonal transition is **Y→P (138 cases)**: pairs that blind evaluation called "full success" were downgraded to "partial" once domain context was applied. These are typically pairs where the overall meaning is approximately right but domain-specific vocabulary is wrong — invisible without knowing the topic. The next largest is **P→N (92 cases)**: partial successes that revealed deeper content failures under scrutiny.

Context rescued only **1 N→Y** and **50 N→P** — confirming that context does not conjure meaning from genuinely failed transcriptions.

### 11.4 Per-Topic Analysis

| Topic | N | Blind Y+P | Context Y+P | Delta |
|-------|---|-----------|-------------|-------|
| Sports/Fitness | 31 | 74% | **77%** | **+3pp** |
| DIY/Home | 27 | 48% | **56%** | **+8pp** |
| Religion/Spirituality | 17 | 53% | **59%** | **+6pp** |
| Politics/News | 34 | 74% | 76% | +2pp |
| Business/Finance | 46 | 76% | 76% | 0pp |
| Technology | 132 | 72% | 69% | −3pp |
| Cooking/Food | 117 | 70% | 65% | −5pp |
| Education/Academic | 86 | 77% | 72% | −5pp |

DIY/Home (+8pp), Religion/Spirituality (+6pp), and Sports/Fitness (+3pp) benefited from context — these are domains where knowing the topic helps interpret phonetically similar but visually grounded content. Technology, Cooking, and Education showed slight declines because domain knowledge also raised expectations for correct terminology.

### 11.5 Hallucination Detection

Hallucinated segments (WER ≥ 100%) were already caught at a very high blind rate (91.9% N). Context improved this only marginally: **4 additional hallucinations caught** that blind evaluation missed. Context mode detected fluent hallucinations from wrong domains (e.g., tech review yielding celebrity quotes). Total hallucinated N-rate: 89.3% (slightly lower due to a few re-classified P→N corrections).

### 11.6 Cross-Condition Reliability

The 30 duplicate pairs yielded **80.0% cross-condition agreement** (blind vs context for the same pair). This is slightly below the blind intra-rater rate of 86.7%, confirming that context-aware evaluation applies a meaningfully different (stricter) standard rather than being a simple re-run. Lenient agreement (Y+P vs N boundary) remains high.

### 11.7 Implications

1. **Context-aware evaluation is a quality tool, not a rescue tool.** It reveals hidden vocabulary failures in segments that appear adequate at first glance. The primary effect is downgrading shallow "close enough" blind Y calls to P — making the gold standard stricter.

2. **Domain-visual content benefits most.** DIY/Home, sports, and religious contexts each show small positive deltas, suggesting that when topic knowledge lets the judge correctly accept phonetically-approximate but semantically-adequate hypotheses, it helps. For these domains, 15-rule decision tree (llm_context_prob) and topic injection are the right fix.

3. **Context does not rescue complete failures.** Only 1 N→Y transition occurred across 1,497 pairs. Segments with total topic drift or hallucination are not recoverable by contextual reasoning alone.

4. **Effective capture rate revision:** Using blind as the primary standard (conservative, domain-agnostic), the gold standard capture rates remain Y=23.0%, Y+P=64.9%. Context-aware figures (Y=15.0%, Y+P=62.1%) represent a more stringent domain-expert benchmark. Both are valid reference points for different use cases.
