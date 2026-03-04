# Intelligibility Score (IS) — Methodology & Examples

**Argos — The Orchard**
**Date:** 2026-02-24
**Author:** Yoad Oxman

---

## 1. Why WER Isn't Enough

Word Error Rate (WER) counts how many words differ between what was said (reference) and what the lip-reading model predicted (hypothesis). But it treats all errors equally — it doesn't know whether the errors destroy meaning or not.

### The Problem: Same WER, Opposite Intelligibility

Consider these two predictions, both with ~30% WER:

**Prediction A — WER 29%, FULLY INTELLIGIBLE:**
> **Reference:** "that are going to allow you to work with the team in a more"
> **Predicted:** "are going to allow you to work with a team and more"
>
> A human reading the prediction completely understands: the speaker is talking about working with a team. Minor articles changed ("the"→"a"), trivial restructuring. WER penalizes this heavily (29%) but a human wouldn't even notice the differences.

**Prediction B — WER 33%, COMPLETELY UNINTELLIGIBLE:**
> **Reference:** "today i'm talking with admiral mcrae"
> **Predicted:** "today i'm talking with animal migratory"
>
> The structure is similar but the meaning is destroyed. "Admiral McRae" (a person) became "animal migratory" (a biology concept). A human reading the prediction would think the speaker is discussing animal migration patterns, not introducing a military officer.

WER says these are almost equally good (29% vs 33%). A human says one is perfect and the other is nonsense.

---

## 2. The 10 Proof Examples

These examples from our 1497-segment baseline demonstrate WER's blindspots:

### Examples Where WER Over-Penalizes (High WER, Still Intelligible)

| # | WER | Reference | Predicted | Assessment |
|---|-----|-----------|-----------|------------|
| 1 | 10% | "wellness is 100 in our control simply by thinking positive" | "is 100 in our control simply by thinking positive" | Only "wellness" missing. Fully clear. |
| 2 | 22% | "a friend of mine was recently diagnosed with and died of stage 4 breast cancer and she described" | "friend of mine was recently diagnosed and died of stage four breast cancer and since she described" | Perfect meaning. "Stage 4"→"stage four" is identical. |
| 3 | 29% | "that are going to allow you to work with the team in a more" | "are going to allow you to work with a team and more" | Same idea — working with a team. Minor articles changed. |

### Examples Where WER Under-Penalizes (Low WER, Unintelligible)

| # | WER | Reference | Predicted | Assessment |
|---|-----|-----------|-----------|------------|
| 4 | 33% | "today i'm talking with admiral mcrae" | "today i'm talking with animal migratory" | Entity destroyed. Completely wrong frame of reference. |
| 5 | 23% | "ad where they tried to suggest that the iphone was your mom's phone" | "where they tried to suggest that the iphone was your bomb" | "mom's phone"→"bomb". Meaning goes from marketing to explosives. |

### Examples of Total Hallucination

| # | WER | Reference | Predicted | Assessment |
|---|-----|-----------|-----------|------------|
| 6 | 100% | "let's see a half a cup of" | "i have to say thank you" | A cooking measurement became a thank-you. |
| 7 | 100% | "it doesn't have a carry strap but you can put it on your shoulder" | "this is david irving he's a holocaust denier and a computer hacker" | A product review became a statement about a Holocaust denier. Harmful. |
| 8 | 100% | "so there's different sizes of different boards" | "i'm going to tell you" | 25-word sentence about hardware → 5-word nothing. |

### Examples Where Meaning Is Partially Preserved

| # | WER | Reference | Predicted | Assessment |
|---|-----|-----------|-----------|------------|
| 9 | 27% | "more fabulous queens from around the globe first the lebanese comedian" | "more fabulous tweets from around the globe first lebanese community" | Structure intact, gist clear (something fabulous + global + Lebanese), but "queens/comedian" → "tweets/community" loses the specific subject. |
| 10 | 50% | "in the creation of these children or in the making" | "in the creation of these children's orders and then in the making of" | Core concept ("creation of children" + "making") survives despite extra words. |

---

## 3. Homophene Confusions: The Lip-Reading Problem

### What Are Homophenes?

Homophenes are words that look identical on a person's lips. A lip-reading system (and deaf individuals) struggle to distinguish these because the mouth makes the same shape.

### The Confusion Groups

| Lip Shape | Sounds That Look Identical | Example Words |
|-----------|---------------------------|---------------|
| **Both lips close** | p, b, m | "pads"↔"pants", "mom"↔"bomb", "pill"↔"bill"↔"mill" |
| **Upper teeth on lower lip** | f, v | "fine"↔"vine", "few"↔"view" |
| **Tongue behind top teeth** | t, d, n, s, z, l | "collar"↔"color", "time"↔"dime", "ten"↔"den" |
| **Back of throat (invisible)** | k, g, h, ng | "could"↔"good"↔"hood" |
| **Rounded lips** | w, r | "win"↔"rim" |
| **Jaw drop (vowels)** | Many vowels look similar | "bit"↔"bet"↔"bat" |

**About 50-70% of English sounds are invisible or ambiguous on lips.** This is why lip-reading is fundamentally hard — even expert human lip-readers achieve only ~30-40% word accuracy on unrestricted speech.

### Real Examples from Our Data

**Type 1: Phonetic Near-Misses (words sound alike)**

| Reference | Predicted | Phonetic Explanation | Meaning Preserved? |
|-----------|-----------|---------------------|-------------------|
| collar | color | Identical lip shape (KLR=KLR in Metaphone). t/d/n group. | YES — "blue collar"≈"blue color" in context |
| dilating | dilation | Same root word, morphological variant. Nearly identical on lips. | YES — same medical concept |
| pads | pants | Both start with lips closing (p), followed by open vowel (a). Only final consonant differs (d→nts), which is barely visible. | PARTIALLY — "pads"≈"pants" could be recovered in context |
| coping | hope | Similar vowel sound, p visible on lips. The "k" in coping is invisible. | PARTIALLY — related psychological concepts |

**Type 2: Same Meaning, Different Words**

| Reference | Predicted | Why Different | Meaning Preserved? |
|-----------|-----------|--------------|-------------------|
| psychological | significant | Completely different words and sounds, but BOTH mean "important/meaningful" in context. The model substituted a synonym. | YES — "psychological benefit"≈"significant benefit" |
| giving | given | Morphological variant — same word, different tense. | YES |
| results based seminars | resorts and symposiums | "results"≈"resorts" (phonetically close). "seminars"≈"symposiums" (semantically synonymous). | PARTIALLY — sense of events/meetings preserved |

**Type 3: Entity Corruption (critical information destroyed)**

| Reference | Predicted | Lip Explanation | Meaning Preserved? |
|-----------|-----------|----------------|-------------------|
| admiral mcrae | animal migratory | "admiral"→"animal": similar lip patterns (bilabial 'm' in both). "mcrae"→"migratory": both start with 'm' lip closure. | NO — person became biology concept |
| mom's phone | bomb | "mom" and "bomb" are homophones on lips (bilabial closure). Context lost. | NO — marketing became explosives |
| bernreuter | rogers | Both proper names, lip shapes are unrelated. Model hallucinated a different name. | NO — wrong entity entirely |
| purim | monkey square | Foreign word → nonsense. Model had no visual reference for this word. | NO — holiday name destroyed |

---

## 4. Claude's Assessment Process (Design-Time Only)

> **Clarification**: The 5-step process below describes how Claude (Anthropic) **designed** the evaluation rubric — not a per-sample runtime process. Claude analyzed real ref/hyp pairs during metric design to determine what signals matter and how to weight them. The resulting IS formula and `llm_context_prob` decision tree are **fully deterministic Python code with zero LLM API calls**. Evaluating all 1,497 segments takes seconds of local computation and costs $0.

When acting as an "LLM judge" for each ref/hyp pair, the assessment follows five steps:

### Step 1: Phonetic Bridge Test
> Do the wrong words SOUND LIKE the right words?
> "collar"→"color": YES (both KLR). "admiral"→"animal": NO (ATMRL≠ANML).

If yes, the error may be a natural lip-reading confusion that preserves the acoustic structure of the sentence.

### Step 2: Context Recovery Test
> If I read ONLY the hypothesis — does it make sense as a standalone sentence?
> Then reveal the reference — can I see HOW the model got from one to the other?

"Blue color and white color" makes sense standalone AND the bridge to "blue collar" is obvious. "Today I'm talking with animal migratory" makes grammatical sense but the bridge to "admiral mcrae" is invisible without context.

### Step 3: Semantic Equivalence Test
> Do both sentences convey the same ACTION, TOPIC, and SENTIMENT?
> - Action: What is happening? (talking, describing, measuring...)
> - Topic: What about? (business, health, people, cooking...)
> - Sentiment: Positive, negative, neutral?

"Psychological benefit" → "significant benefit": Same action (stating a benefit), same topic (photography), same sentiment (positive). PASS.
"Admiral McRae" → "animal migratory": Different action (introducing person vs. discussing biology), different topic, neutral→neutral. FAIL.

### Step 4: Harmful Hallucination Check
> Is the hypothesis not just wrong, but potentially HARMFUL or MISLEADING?

Levels of harm:
- **Benign wrong:** "tweets from around the globe" (harmless substitution)
- **Confusing wrong:** "animal migratory" (confusing but not dangerous)
- **Harmful wrong:** "your bomb" instead of "your mom's phone" (alarming content)
- **Dangerous wrong:** "holocaust denier" instead of "carry strap" (defamatory fabrication)

### Step 5: Final Score (0-5)

| Score | Criteria |
|-------|----------|
| **5 — Excellent** | Meaning fully preserved. Minor word differences (articles, morphological variants). A human would not notice errors in casual reading. |
| **4 — Good** | Meaning clearly preserved. Some wrong words but recoverable through phonetic similarity or context. Topic, action, and sentiment all correct. |
| **3 — Fair** | Gist recoverable. The general topic is correct and some key details survive, but important specifics are lost or wrong. |
| **2 — Poor** | Only fragments of meaning survive. Some correct words but the overall sentence conveys a different message. |
| **1 — Bad** | No meaningful connection between reference and hypothesis. Completely different topic or fabricated content. |
| **0 — Hallucinated/Harmful** | Output is fabricated AND potentially harmful or misleading. The model generated confidently wrong content that could cause confusion or harm. |

---

## 5. The 6 Signals Explained

The Intelligibility Score (IS) combines six automated signals that collectively approximate the judgment process described above:

### Signal 1: Semantic Similarity (weight: 0.25)
**What it does:** Compares the MEANING of the entire reference and hypothesis sentences using AI sentence embeddings (all-MiniLM-L6-v2 model).

**How:** Both sentences are converted to 384-dimensional vectors that encode meaning. The cosine similarity between vectors measures how similar the meanings are (0=unrelated, 1=identical meaning).

**What it catches:** "Psychological benefit"≈"significant benefit" would score high because both vectors point in similar semantic directions, even though the words differ.

**What it misses:** Short sentences where a single wrong word changes everything. "Talking with admiral" and "talking with animal" might have moderately similar vectors because the sentence structure is similar.

### Signal 2: Phonetic Similarity (weight: 0.15)
**What it does:** Checks whether substituted words SOUND alike using Double Metaphone phonetic encoding.

**How:** Each word in the reference and hypothesis is encoded phonetically. Words that sound alike get the same code ("collar"→KLR, "color"→KLR). The metric counts what fraction of word pairs are phonetically equivalent or nearly so.

**What it catches:** Natural lip-reading confusions where the mouth shape was correctly read but the specific consonant was wrong (p/b/m confusions, t/d/n confusions).

**What it misses:** Cases where words sound similar but mean completely different things ("mom's"→"bomb" — phonetically close but semantically destructive).

### Signal 3: Inverse WER (weight: 0.15)
**What it does:** The traditional word error rate, inverted (so higher = better). Measures raw structural correctness.

**How:** Counts substitutions, insertions, and deletions between reference and hypothesis. IS uses (1 - WER/100) scaled to 0-5.

**What it catches:** Overall word-level accuracy.

**What it misses:** Doesn't know if errors are on important words or trivial ones. Doesn't know if substitutions preserve meaning.

### Signal 4: Inverse WWER (weight: 0.15)
**What it does:** Weighted WER that treats content words (nouns, verbs, adjectives) as more important than function words (the, a, is, and).

**How:** Named entities and proper nouns have 2x error weight. Content words have 1x. Function words (articles, prepositions) have 0.5x. This means getting "the" wrong costs half as much as getting "cancer" wrong.

**What it catches:** Whether the meaningful content words survived, regardless of filler word accuracy.

### Signal 5: Named Entity Accuracy F1 (weight: 0.15)
**What it does:** Specifically checks whether proper nouns, numbers, and named entities survived decoding.

**How:** Extracts entities from both reference and hypothesis (names like "McRae", numbers like "25", organizations like "Samsung"), computes precision and recall.

**What it catches:** The factual anchors — the specific names, numbers, and proper nouns that a human cannot infer from context. If someone said "Admiral McRae" and the model output "animal migratory", the NEA score is 0% because the entity was completely lost.

**Why it matters:** These are precisely the words humans cannot recover from context. You can guess a missing article ("the"→"a") but you cannot guess a missing name.

### Signal 6: Length Ratio (weight: 0.15)
**What it does:** Checks whether the hypothesis is roughly the same length as the reference.

**How:** Ratio = len(hypothesis words) / len(reference words). A ratio near 1.0 is ideal. Too long (>1.5) suggests hallucination (the model invented extra words). Too short (<0.5) suggests truncation (the model gave up).

**What it catches:** Extreme hallucinations where the model generates paragraphs of fluent but fabricated text, or truncations where it outputs just a few words.

---

## 6. Tier Classification with Examples

### Tier 5: Excellent (IS 4.0-5.0) — "Human fully understands"

> **Example:** WER 3%
> Reference: "you're smart enough to realize that you need a plan"
> Predicted: "smart enough to realize that you need a plan"
> Missing only "you're" at the start. Perfect comprehension.

> **Example:** WER 6%
> Reference: "encourage a little bit of a deeper thought process about the calories and the weight loss"
> Predicted: "encourage a little bit of a deeper thought process about the calories in the weight loss"
> One preposition changed ("and"→"in"). Meaning identical.

### Tier 4: Good (IS 3.0-3.99) — "Intelligible, meaning preserved"

> **Example:** WER 23%
> Reference: "on today's the doctor is in the topic is hypertension there is no ideal blood pressure reading"
> Predicted: "today as the doctor says the topic is hypertension there is no ideal blood pressure reading"
> Structure reshuffled but meaning perfectly clear: doctor's show about hypertension and blood pressure.

> **Example:** WER 29%
> Reference: "return books taken from the main library to the king's manor library and vice versa"
> Predicted: "term booked down from the main library to his local library and vice versa"
> "king's manor"→"his local" loses the specific name but preserves the concept (returning books between libraries). A human understands the process.

### Tier 3: Fair (IS 2.0-2.99) — "Gist recoverable, details wrong"

> **Example:** WER 27%
> Reference: "more fabulous queens from around the globe first the lebanese comedian"
> Predicted: "more fabulous tweets from around the globe first lebanese community"
> Topic area preserved (something fabulous, global, Lebanese) but the specific subject (drag queens? comedian?) is lost.

> **Example:** WER 35%
> Reference: "for the sweetest and most all encompassing celebration of this great holiday of purim"
> Predicted: "for the swedish and most norwegian campus in celebration of this great holiday of jul"
> Structure of "celebration of a holiday" preserved, but "purim"→"jul" and "sweetest"→"swedish" change the cultural context entirely.

### Tier 2: Poor (IS 1.0-1.99) — "Fragments only"

> **Example:** WER 69%
> Reference: "then we have the costal cartilages costal always refers to ribs"
> Predicted: "that we have they cause our hormones to go haywire"
> An anatomy lesson became a statement about hormones. No meaningful overlap. A few structural words match ("we have", "they") but the content is completely wrong.

### Tier 1: Failed (IS 0.0-0.99) — "Unintelligible or hallucinated"

> **Example:** WER 100%
> Reference: "let's see a half a cup of"
> Predicted: "i have to say thank you"
> Zero connection. Cooking → gratitude.

> **Example:** WER 100% (harmful)
> Reference: "it doesn't have a carry strap but you can put it on your shoulder"
> Predicted: "this is david irving he's a holocaust denier"
> Not just wrong — actively harmful fabrication. The LLM generated confident, fluent text about a completely unrelated and sensitive topic.

---

## 7. The Composite Formula

```
IS = 0.25 x Semantic_Sim + 0.15 x Phonetic_Sim + 0.15 x (1-WER) + 0.15 x (1-WWER) + 0.15 x NEA_F1 + 0.15 x Length_Ratio
```

All signals scaled to 0-5 before combining. Final IS range: 0.0 to 5.0.

**"Properly captured" = IS >= 3.0** (Tier 4: Good + Tier 5: Excellent)

These are the segments where a human could understand what was actually said from the lip-reading output.

---

## 8. Failure Mode Classification

Every segment scoring IS < 3.0 is classified into its dominant failure mode. This runs automatically as part of the scoring pipeline.

| Failure Mode | Criteria | Description |
|-------------|----------|-------------|
| **Empty Output** | No hypothesis text | Model produced nothing |
| **Hallucination** | WER > 100% | Fluent but completely fabricated text, longer than reference |
| **Over-generation** | Length ratio > 1.8 | Hypothesis much longer than reference |
| **Truncation** | Length ratio < 0.3 | Hypothesis much shorter than reference |
| **Total Topic Drift** | Semantic < 0.2 AND Phonetic < 0.3 | No connection to reference at all |
| **Phonetically Similar but Wrong Topic** | Semantic < 0.2 AND Phonetic >= 0.3 | Words sound right but mean something different |
| **Entity Destruction** | Semantic >= 0.2, NEA F1 < 10%, WER > 60% | Topic vaguely right but all names/numbers lost |
| **High Error Rate** | WER > 70% | Too many wrong words for any signal to survive |
| **Content Word Errors** | Semantic >= 0.3, WER > 50% | Structure intact but key nouns/verbs wrong |
| **Accumulated Small Errors** | Default | Many minor errors collectively destroy meaning |

### Baseline Results (1497 segments, 900 failures)

| Mode | Count | % of Failures |
|------|-------|--------------|
| Total Topic Drift | 143 | 15.9% |
| Phonetically Similar but Wrong Topic | 141 | 15.7% |
| Accumulated Small Errors | 111 | 12.3% |
| Hallucination | 111 | 12.3% |
| High Error Rate | 109 | 12.1% |
| Entity Destruction | 108 | 12.0% |
| Content Word Errors | 96 | 10.7% |
| Empty Output | 70 | 7.8% |
| Truncation | 10 | 1.1% |
| Over-generation | 1 | 0.1% |

---

## 9. Success Pattern Classification

Every segment scoring IS >= 3.0 is classified by what made it succeed.

| Success Pattern | Criteria | Description |
|----------------|----------|-------------|
| **Near-Perfect Output** | WER <= 10% | Almost no errors |
| **Minor Errors, High Semantic Match** | WER <= 25%, Semantic > 0.6 | Few errors, meaning strongly preserved |
| **Phonetically Preserved** | Phonetic > 0.7, WER > 25% | Words sound right despite WER |
| **Entities Preserved** | NEA F1 > 60%, WER > 25% | Names and numbers survived |
| **Good Semantic + Correct Length** | Semantic > 0.5, length ratio 0.7-1.3 | Meaning coherent, right length |
| **Low-Moderate WER** | WER <= 35% | Moderate errors, no standout signal |
| **Combined Semantic + Phonetic Bridge** | Semantic > 0.4, Phonetic > 0.5 | Both signals combine |
| **Multiple Partial Signals** | Default | No single strong signal, but enough combined |

### Baseline Results (1497 segments, 597 successes)

| Pattern | Count | % of Successes |
|---------|-------|---------------|
| Phonetically Preserved | 248 | 41.5% |
| Minor Errors, High Semantic Match | 146 | 24.5% |
| Entities Preserved | 74 | 12.4% |
| Near-Perfect Output | 69 | 11.6% |
| Good Semantic + Correct Length | 45 | 7.5% |
| Low-Moderate WER | 13 | 2.2% |
| Combined Semantic + Phonetic Bridge | 2 | 0.3% |

**Key Insight:** Phonetic preservation is the #1 success driver (41.5%). The visual signal preserves the phonetic structure of speech even when specific words are wrong. A system that corrects phonetic near-misses could potentially recover many more segments.

---

## 10. Signal Comparison: Success vs Failure

| Signal | Success Mean | Failure Mean | Gap |
|--------|-------------|-------------|-----|
| Semantic Similarity | 0.736 | 0.238 | +0.498 |
| Phonetic Similarity | 0.809 | 0.382 | +0.427 |
| WER (%) | 30.2 | 86.5 | -56.3 |
| WWER (%) | 31.1 | 82.3 | -51.2 |
| NEA F1 (%) | 74.0 | 15.7 | +58.3 |
| Length Ratio | 0.974 | 0.892 | +0.082 |

The largest differentiators are NEA F1 (entity preservation), WER, and semantic similarity. Length ratio is similar between groups, confirming it is not a strong solo predictor.

---

## 11. Context Recovery Estimation

Two independent approaches estimate whether a viewer with topic context could understand each segment:

### Rule-Based (Decision Tree)
Simple thresholds on semantic similarity, WER, WWER, and length ratio. Conservative estimate.

### LLM-Knowledge-Based (Multi-Factor)
Approximates expert judgment using content word overlap, sequence preservation, phonetic plausibility, length sanity, semantic domain coherence, and information density. Returns a probability (0-1).

### Baseline Results

| Method | Recoverable | Percentage |
|--------|-------------|------------|
| Rule-Based | 652 / 1497 | 43.6% |
| LLM-Knowledge | 757 / 1497 | 50.6% |

The LLM approach recovers ~105 more segments by detecting structural matches and phonetic bridges that hard thresholds miss.

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

**3 out of 5 failure categories** (708/900 = 78.7% of failures) already produce approximately the correct number of words. Word count has zero effect on them — the problem is **which words** are generated, not **how many**.

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
