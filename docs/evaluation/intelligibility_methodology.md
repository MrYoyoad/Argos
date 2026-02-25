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

## 4. Claude's Assessment Process

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
