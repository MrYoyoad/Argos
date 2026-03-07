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

**NIV Thresholds** (empirically calibrated against Opus-as-a-Judge, adopted March 2026):

| Target | IS Threshold | κ | Captures | Judge rate |
|--------|-------------|------|----------|-----------|
| **Y** ("meaning clearly conveyed") | **IS >= 3.80** | 0.690 | 346 (23.1%) | 345 (23.0%) |
| **Y+P** ("any useful meaning") | **IS >= 2.00** | 0.818 | 922 (61.6%) | 971 (64.9%) |

IS beats WER at both operating points: +0.061 for Y (vs WER <= 34%), +0.041 for Y+P (vs WER <= 77%). See [threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md) for full analysis.

*Legacy: IS >= 3.0 was the original design-time threshold ("properly captured"). NIV thresholds supersede it for presentation and reporting.*

---

## 8. Failure Mode Classification

Every segment scoring IS < 3.0 is classified into its dominant failure category. This runs automatically as part of the scoring pipeline. The original 10 fine-grained modes have been consolidated into **5 academically-grounded categories** that map cleanly to remediation strategies.

| Failure Category | Constituent Modes | Detection Rules | Description |
|-----------------|-------------------|-----------------|-------------|
| **Signal Loss** | Empty Output, Truncation, Over-generation | No hypothesis text, or length ratio < 0.3 or > 1.8 | Model produced nothing, stopped too early, or ran past the content |
| **Hallucination** | Hallucination | WER > 100% (hypothesis longer than reference, fluent but fabricated) | LLM "runs ahead" of visual signal, generating plausible but invented text |
| **Wrong Topic** | Total Topic Drift, Phonetically Similar but Wrong Topic | Semantic < 0.2 (topic drift) or Semantic < 0.2 AND Phonetic >= 0.3 (phonetic wrong topic) | Output is about a completely different subject, possibly with similar-sounding words |
| **Right Topic Wrong Details** | Entity Destruction, Content Word Errors | Semantic >= 0.2 but NEA F1 < 10% and WER > 60% (entities lost) or Semantic >= 0.3 but WER > 50% (content words wrong) | General topic preserved but names, numbers, and key content words are wrong |
| **Accumulated Errors** | High Error Rate, Accumulated Small Errors | WER > 70% (high error) or default (many small errors) | Many individually small errors that compound to destroy meaning |

### Baseline Results (1497 segments, 900 failures)

| Category | Count | % of Failures |
|----------|-------|--------------|
| Wrong Topic | 284 | 31.6% |
| Accumulated Errors | 220 | 24.4% |
| Right Topic Wrong Details | 204 | 22.7% |
| Hallucination | 111 | 12.3% |
| Signal Loss | 81 | 9.0% |

### 8.1 What Each Failure Category Means (Plain English)

**Signal Loss** (81 segments, 9.0%)
- *What it looks like*: The model produced nothing (empty output, 70 segments), stopped too early (truncation, 10 segments), or ran past the content (over-generation, 1 segment).
- *Why it happens*: Visual encoder could not extract enough signal — face occluded, very short segment, poor video quality, or confidence drops below generation threshold.
- *What could fix it*: Config J (lenpen=1 + sampling) eliminates all 70 empties. N-best provides fallback candidates. Length penalty tuning handles over-generation.

**Hallucination** (111 segments, 12.3%)
- *What it looks like*: The model generated fluent, confident text that has nothing to do with what was actually said. Often longer than the reference.
- *Why it happens*: The LLM "runs ahead" of the visual signal, generating plausible text from its language model prior rather than from lip movements. This is the most dangerous failure category because the output sounds convincing.
- *What could fix it*: Stronger visual encoder (more training data), anti-hallucination prompts, GER post-processing to compare multiple hypotheses.

**Wrong Topic** (284 segments, 31.6%)
- *What it looks like*: The output is about a completely different subject. Either no connection at all (total topic drift, 143 segments — e.g., reference about weight loss, hypothesis about being a princess), or words that sound similar but belong to the wrong domain (phonetically similar wrong topic, 141 segments — similar mouth shapes but different meaning).
- *Why it happens*: Visual encoder extracted no meaningful signal (pure drift) or captured mouth shapes but the LLM decoded them into the wrong semantic domain (phonetic confusion).
- *What could fix it*: Better visual encoder (more training data, domain adaptation), topic-context prompts, stronger LLM with better disambiguation, N-best aggregation.

**Right Topic Wrong Details** (204 segments, 22.7%)
- *What it looks like*: The general topic is vaguely right, but all names, numbers, and proper nouns are wrong (entity destruction, 108 segments — e.g., "the 13th amendment" → "13th may mean something to him"), or sentence structure is intact but key nouns and verbs are substituted (content word errors, 96 segments — e.g., "before I get into that" → "the day before I get here").
- *Why it happens*: Named entities are unpredictable from lip shapes. Content words get substituted with similar-looking alternatives while structure is preserved.
- *What could fix it*: Context injection (entity lists), N-best with entity voting, stronger LLM, phonetic post-correction, domain-specific fine-tuning.

**Accumulated Errors** (220 segments, 24.4%)
- *What it looks like*: Either too many words wrong for any signal to survive (high error rate, 109 segments), or many individually small errors that compound to destroy meaning (accumulated small errors, 111 segments — e.g., "convert your body into an avatar" → "interjection to an existing body into an adjoining sentence").
- *Why it happens*: Combination of visual ambiguity, unfamiliar vocabulary, rapid speech, and many simultaneous phonetic confusions.
- *What could fix it*: N-best aggregation (ROVER voting), GER post-processing, more training data, stronger LLM, visual encoder improvements.

### 8.2 Failure Category Examples

One representative segment from each failure category:

| Category | Reference | Hypothesis | WER | IS |
|----------|-----------|-----------|-----|-----|
| **Signal Loss** | "you don't just pull it apart you're not strong enough..." | *(empty)* | 100% | 0.00 |
| **Hallucination** | "the chapter starts with a doxology..." | "so i'm going to tell you a little story about how i got..." | 172% | 0.23 |
| **Wrong Topic** | "i've made lots of videos about weight loss..." | "when i was a little girl i always wanted to be a princess" | 97% | 0.38 |
| **Right Topic Wrong Details** | "about the 13th amendment the 13th amendment is going to come..." | "13th may mean something to him because it can help him..." | 81% | 2.14 |
| **Accumulated Errors** | "and as you did those gestures it would convert your body..." | "and add to interjection to an existing body into an adjoining..." | 69% | 2.04 |

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

### 9.1 What Each Success Pattern Means (Plain English)

**Near-Perfect Output** (69 segments, 11.6%)
- *What it looks like*: Almost word-for-word correct. A human wouldn't notice the difference.
- *Why it matters*: Proves the system CAN achieve near-human accuracy under good conditions (clear speech, frontal face, good lighting, familiar vocabulary).
- *Implication*: These segments define the system's ceiling. The gap between these and the average is the improvement opportunity.

**Minor Errors, High Semantic Match** (146 segments, 24.5%)
- *What it looks like*: A few words are different (articles changed, slight restructuring) but the meaning is completely preserved. WER says 15-25% error, but a human reader understands everything.
- *Why it matters*: This is where WER is most misleading — it penalizes harmless differences. IS correctly scores these as Good (4.0+).
- *Implication*: These prove that WER systematically overstates failure. The "real" error rate is much lower than WER suggests.

**Phonetically Preserved** (248 segments, 41.5%)
- *What it looks like*: Many words are technically wrong by WER, but they SOUND like the right words. The model captures mouth shapes accurately; it just picks a similar-sounding alternative. "Respiratory system" becomes "rosetta mission" — wrong words, but the mouth movements were read correctly.
- *Why it matters*: This is the #1 success driver. It means the visual encoder IS working — the bottleneck is disambiguation, not perception.
- *Implication*: A stronger LLM or context injection could correct these phonetic near-misses, potentially recovering many "fair" tier segments.

**Entities Preserved** (74 segments, 12.4%)
- *What it looks like*: Names, numbers, and proper nouns survived even though surrounding words are wrong. The factual anchors are correct.
- *Why it matters*: For many use cases (legal, intelligence, medical), preserving key entities matters more than perfect transcription.
- *Implication*: These segments are immediately useful for entity extraction even without full transcription accuracy.

**Good Semantic + Correct Length** (45 segments, 7.5%)
- *What it looks like*: The meaning is coherent and the output is the right length, even though individual words differ.
- *Why it matters*: Shows the model understands sentence-level structure, not just individual words.
- *Implication*: These benefit most from N-best aggregation where multiple hypotheses can be merged.

**Low-Moderate WER** (13 segments, 2.2%)
- *What it looks like*: WER is in the 25-35% range with no standout signal. A mix of correct and incorrect words.
- *Why it matters*: These are borderline segments where small improvements could push them to "Good" tier.
- *Implication*: Phase 2 (N-best aggregation) and Phase 3 (prompt engineering) most likely to help.

**Combined Semantic + Phonetic Bridge** (2 segments, 0.3%)
- *What it looks like*: Neither semantic nor phonetic similarity alone is strong enough, but together they push the segment above the IS ≥ 3.0 threshold.
- *Why it matters*: Demonstrates the value of combining multiple signals rather than relying on any single metric.
- *Implication*: Validates the multi-signal IS design — no single metric captures all ways a segment can be intelligible.

### 9.2 Success Pattern Examples

One representative segment from each pattern:

| Pattern | Reference | Hypothesis | WER | IS |
|---------|-----------|-----------|-----|-----|
| **Near-Perfect** | "piece of software for anybody who's just getting started..." | "piece of software for anybody who's just getting started..." | 6% | 4.77 |
| **Minor Errors** | "mute the call that you're on it mutes and then you hear..." | "mute the call that you're on and then you hear..." | 17% | 4.63 |
| **Phonetically Preserved** | "improvements have been made to it over the eons but the respiratory system..." | "improvements have been made to it over the years but the rosetta mission..." | 32% | 3.64 |
| **Entities Preserved** | "these areas likely from mid to late afternoon through the evening hours..." | "terrorists lately from the midday afternoon through the evening hours..." | 51% | 3.28 |
| **Semantic + Length** | "welcome to lesson number two what are we going to be doing..." | "welcome to lesson number two what are we going to be doing..." | 24% | 3.79 |
| **Low-Moderate WER** | "therefore it's attractive and then the large manufacturers of soft rings..." | "is a default tracker and then the hardware manufacturers of softwares..." | 35% | 3.02 |
| **Combined Bridge** | "and they're nice to their employees because that's the kind of thing..." | "no that's really important to me because that is not the thing..." | 56% | 3.01 |

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

## 10b. Metric Mismatch Guide: When Metrics Disagree

When two metrics point in different directions, it reveals something specific about what the model got right or wrong. This guide explains the 8 most common mismatch patterns.

### Pattern 1: WER >> WWER (gap ≥ 10 percentage points)

**What you see**: WER is much higher than WWER (e.g., WER 100%, WWER 54%).

**What it means**: Most errors are on function words (the, a, is, and, to) while content words (nouns, verbs, names) are largely correct. The meaning is likely preserved despite the high WER.

**Example**: Ref: "good to help people mission accomplished" → Hyp: "her to help people but she got impatient so" (WER 100%, WWER 54%, gap 46pp). The content words "help people" survived; the errors are on structure words.

**Which IS component catches this**: WWER is lower, so Inv-WWER gives more credit than Inv-WER. These segments are LLM salvage candidates ("WER Over-Punishment" category).

### Pattern 2: WWER >> WER (rare, gap ≥ 10pp)

**What you see**: WWER is much higher than WER (e.g., WER 172%, WWER 296%).

**What it means**: The content words are MORE wrong than the function words. This is worse than it looks — the meaningful words are the ones that failed.

**Example**: Ref: "the chapter starts with a doxology..." → Hyp: "so i'm going to tell you a little story about how i got..." (WER 172%, WWER 296%). Every content word is wrong AND the model hallucinated extra text.

**Which IS component catches this**: WWER penalizes this harder than WER. Semantic similarity is also very low.

### Pattern 3: High Semantic Similarity + High WER (sem ≥ 0.5, WER ≥ 60%)

**What you see**: WER says it's terrible, but semantic similarity says the meaning is preserved.

**What it means**: The model paraphrased rather than transcribed. Different words, same meaning. This is NOT an error — it's a translation.

**Example**: Ref: "this course is all about transitions this video is all about transitions" → Hyp: "this course is all about transition in this video i'm going to talk about transi" (WER 67%, Semantic 0.89). Nearly identical meaning despite 67% word error rate.

**Which IS component catches this**: Semantic similarity (0.25 weight) gives high credit. This is why IS was created — WER cannot see meaning preservation.

### Pattern 4: Low Semantic Similarity + Low WER (sem < 0.3, WER < 40%)

**What you see**: Few words changed, but semantic similarity is very low.

**What it means**: Entity destruction — a small number of critical word substitutions changed the entire meaning. This is the most deceptive failure because WER looks fine.

**Example**: Ref: "you can actually bring the pro controller with you on the go" → Hyp: "to actually bring the broken dollar with you on the go" (WER 38%, Semantic 0.14). Only "pro controller" → "broken dollar" changed, but the meaning is destroyed.

**Which IS component catches this**: Semantic similarity drops sharply. NEA F1 also drops if named entities are lost.

### Pattern 5: High Phonetic Similarity + Low Semantic Similarity (phon ≥ 0.7, sem < 0.3)

**What you see**: Words sound alike but the meaning is completely different.

**What it means**: Classic lip-reading confusion (homophene errors). The model correctly read the mouth shapes but decoded them into wrong words.

**Example**: Ref: "it doesn't matter what the tradu" → Hyp: "it doesn't matter what the tradition" (Phonetic 0.88, Semantic 0.28). "Tradu[ction]" and "tradition" look identical on lips.

**Which IS component catches this**: Phonetic similarity is high, but semantic similarity is low. The gap between these two signals identifies homophene confusion specifically.

### Pattern 6: High NEA F1 + High WWER (NEA ≥ 50%, WWER ≥ 60%)

**What you see**: Names and numbers are correct, but overall word accuracy is poor.

**What it means**: The model captured the most important factual anchors (names, numbers, places) even though the surrounding context is garbled.

**Example**: Ref: "it's our commercial product and i've got a few slides..." → Hyp: "this morning i saw a sign on the motorway that said..." (NEA 100%, WWER 73%). Key entities survived in a sea of errors.

**Which IS component catches this**: NEA F1 provides credit even when WER and WWER are bad. These segments may be useful for entity extraction even if transcription is poor.

### Pattern 7: Length Ratio > 1.5 + High WER

**What you see**: The hypothesis is much longer than the reference.

**What it means**: Over-generation — the model hallucinated extra text beyond what was said. The LLM's language prior "ran ahead" of the visual signal.

**Example**: Ref: "very important" → Hyp: "policies that keep us out of the" (Length Ratio 3.50, WER 350%). Two words became six fabricated words.

**Which IS component catches this**: Length Ratio deviates from 1.0, and WER > 100% signals text was inserted. Both Inv-WER and Length Ratio drop.

### Pattern 8: Length Ratio < 0.5 + High WER

**What you see**: The hypothesis is much shorter than the reference.

**What it means**: Truncation — the model stopped generating early. It may have captured the beginning correctly but gave up.

**Example**: Ref: "program covering everybody admittedly with fewer drugs covered but every person..." → Hyp: "i'm going to tell you" (Length Ratio 0.14, WER 94%). A substantive policy statement truncated to a generic filler.

**Which IS component catches this**: Length Ratio drops sharply (< 0.5). WER is high because most words are simply missing.

---

## 10a. Inter-Signal Correlation & Variance Contribution

*(Added 2026-03-02. Full statistical analysis: [is_correlation_analysis.md](is_correlation_analysis.md))*

### Component Correlation with IS (N=1,497)

| Component | Pearson r | Spearman ρ | R² | Weight |
|-----------|----------|------------|-----|--------|
| Phonetic Sim | **0.943** | 0.943 | 0.888 | 0.15 |
| WWER (inverted) | **0.950** | 0.953 | 0.903 | 0.15 |
| WER (inverted) | **0.944** | 0.948 | 0.891 | 0.15 |
| Semantic Sim | **0.921** | 0.925 | 0.848 | 0.25 |
| NEA F1 | **0.864** | 0.864 | 0.747 | 0.15 |
| Length Ratio | 0.650 | 0.611 | 0.423 | 0.15 |

All top-5 signals are strongly correlated (|r| > 0.86). Length Ratio is the weakest predictor.

### Variance Contribution (Covariance Decomposition)

| Weighted Component | % of IS Variance |
|-------------------|-----------------|
| Semantic (0.25×) | **28.5%** |
| NEA F1 (0.15×) | 17.3% |
| Inv-WER (0.15×) | 15.7% |
| Inv-WWER (0.15×) | 15.2% |
| Phonetic (0.15×) | 14.2% |
| Length Ratio (0.15×) | 9.1% |

Semantic dominates variance (28.5%) due to its higher weight and substantial spread. NEA F1 contributes disproportionately (17.3%) because it has the highest variance among the 0.15-weight signals.

### Inter-Component Redundancy

|  | Semantic | Phonetic | WER | WWER | NEA F1 | Length |
|--|----------|----------|-----|------|--------|--------|
| **Semantic** | 1.00 | 0.82 | -0.73 | -0.76 | 0.75 | 0.19 |
| **Phonetic** | 0.82 | 1.00 | -0.79 | -0.85 | 0.75 | 0.36 |
| **WER** | -0.73 | -0.79 | 1.00 | 0.81 | -0.69 | 0.22 |
| **WWER** | -0.76 | -0.85 | 0.81 | 1.00 | -0.75 | -0.10 |
| **NEA F1** | 0.75 | 0.75 | -0.69 | -0.75 | 1.00 | 0.13 |
| **Length** | 0.19 | 0.36 | 0.22 | -0.10 | 0.13 | 1.00 |

**PCA reveals 2 principal components** (Kaiser criterion, eigenvalue > 1):
1. **PC1: Signal quality** (68.4% of variance) — all 5 content signals load equally (0.43–0.47). Semantic is NOT independent; it loads alongside word-accuracy signals.
2. **PC2: Output length** (19.5% of variance) — Length Ratio dominates (loading 0.91), independent of content quality.

Together: 87.9% of total variance. See [is_pca_analysis.md](is_pca_analysis.md) for full PCA results.

### Per-Tier Dominant Signals

| Tier | N | Dominant Correlate with IS | Interpretation |
|------|---|---------------------------|----------------|
| Failed (0-1) | 239 | **Phonetic (0.79)** | At the bottom, phonetic similarity differentiates "totally wrong" from "plausible sounds" |
| Poor (1-2) | 336 | Phonetic (0.52), Semantic (0.51) | Multiple signals contribute equally |
| Fair (2-3) | 325 | **WER (0.55)** | Traditional error rates separate "almost good" from "mediocre" |
| Good (3-4) | 321 | WWER (0.51), WER (0.51) | Balanced — all content signals matter |
| Excellent (4-5) | 276 | **WER (0.83)** | Small WER differences dominate ranking at the top |

### Cross-Configuration Stability

IS component correlations were validated across 16 decode configurations (13 tuning experiments + 3 full decodes). **Semantic (mean r=0.91), Phonetic (mean r=0.91), and NEA F1 (mean r=0.85) are stable across all configs** (std < 0.06). WER and WWER become unreliable when length penalty is applied (lenpen > 0 inflates WER without degrading IS). Length Ratio is the most volatile signal (sign flips across configs). Most configs produce near-identical per-segment IS rankings (r > 0.92), confirming the visual encoder — not decode parameters — is the performance bottleneck. See [is_correlation_analysis.md](is_correlation_analysis.md) Section 10 for full multi-config analysis.

### Claude-Distilled Evaluation (Design-Time LLM, No Runtime LLM Calls)

The entire IS framework — the 5-step assessment rubric (Section 4), the 6 signal weights, the tier boundaries, the failure/success classifications, and the `llm_context_prob` heuristic — was designed by Claude (Anthropic) acting as an expert judge **at design time**. This is a form of **LLM-distilled evaluation**: Claude's judgment was elicited once during metric design and encoded into deterministic, reproducible code. **No LLM API is called when computing IS or `llm_context_prob` — the implementation is pure Python math** (`difflib.SequenceMatcher`, weighted sums, threshold comparisons in a 15-rule decision tree). Evaluating all 1,497 segments takes seconds of local computation and costs $0. The `llm_context_prob` heuristic correlates at **r=0.934** (ρ=0.952) with IS on the baseline. Agreement with the IS ≥ 3.0 threshold: 88.6% (Cohen's κ = 0.773).

**Cross-config heuristic stability** (16 decode configurations): The `llm_context_prob` decision tree correlation with IS is rock-solid — **mean r=0.925** (std=0.015, range 0.910–0.973). Correlation with Semantic Similarity is equally stable (mean r=0.891, std=0.020). Cohen's κ ranges from 0.62 to 0.86 across configs (mean ~0.72). Recall is near-perfect (97.6–100.0%) while precision varies more (65–82%). Config J achieves the best agreement at scale (κ=0.791). See [is_correlation_analysis.md](is_correlation_analysis.md) Sections 7.2a–7.2b for per-config tables and Section 8 for the full LLM-as-a-Judge analysis.

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

*Sections 12-17 (topic analysis, length analysis, config variants, word count, salvage summary, LLM judge summary) have been moved to [intelligibility_extended_analysis.md](intelligibility_extended_analysis.md) for easier navigation.*

