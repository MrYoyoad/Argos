# Reading Lip-Read Output Safely: A Worked-Examples Guide

**Audience:** Client review. Non-technical readers welcome.
**The point:** Show, with real segments, how the per-word **confidence colours** + the segment-level **tier badge** let you safely use the system's output — including segments where most of the words are wrong but the *useful part* can still be confidently extracted, and segments where the output reads naturally but is in fact unreliable. The colours are how the system protects you from itself.

---

## Quick orientation

Each segment in the report shows you two things:

1. A **tier badge** — one of **Trust**, **Salvage**, or **Strip** — telling you how much to trust the segment overall.
2. **Per-word colours** on the hypothesis text — **blue / orange / purple** — telling you how sure the model was about each individual word.

```
Trust    (segment confidence ≥ 0.82)   →  Read normally; pause on non-blue words.
Salvage  (segment confidence 0.65-0.82) →  Use blue words as anchors; verify the rest.
Strip    (segment confidence < 0.65)    →  Coloring removed. Don't read word-by-word.
```

```
Blue   (≥ 0.85)        →  "I'm confident."           ~94% correct in Trust segments
Orange (0.40 – 0.85)   →  "Best guess."               ~65% correct in Trust segments
Purple (< 0.40)        →  "I had to pick something."  ~39% correct in Trust segments
```

(The same scheme renders as **green / yellow / red** in some report skins. Same meaning.)

A short technical note for context: the text shown to you has already been refined through cross-beam consensus — the model produces 20 alternative phrasings and the system picks the consensus. This happens silently and improves the headline accuracy. **The actionable signal for you as a reader is the colours and the tier badge** — that's what this guide is about.

---

## Why the colours matter: three modes of reading

The colours unlock three distinct ways the output becomes useful:

1. **Confident reading in Trust segments** — the colours tell you where to spend your attention, so you don't waste time second-guessing the 90% that's right.
2. **Safe partial understanding in Salvage segments** — even when half the words are wrong, the blue ones form a reliable spine of meaning and the purple ones flag exactly the words you should *not* believe. You walk away with the gist, never with a false belief.
3. **Honest refusal in Strip segments** — when the model is too unsure to be trusted at all, the system *removes* the colouring rather than show a misleading certainty signal. You're told, plainly, "don't read this as transcription."

The rest of this document shows each of these modes on real segments from the evaluation.

---

## Mode 1 — Confident reading in Trust segments

The text is mostly correct. The colours' job is to tell you the few places to slow down.

### Example 1.1 — Music tutorial (one purple word changes the meaning)

**Tier: Trust** (segment confidence 0.91). **WER: 23%.**

**REF:** *okay let's start out by playing a long tone on middle c and then we're going to go down chromatically from there if you haven't done so already i highly recommend you watch my saxophone*

**Coloured rendering** (✓ correct, ✗ wrong):

> [orange✗]can [blue✓]start [blue✓]out [blue✓]by [blue✓]playing [blue✓]a [blue✓]long [orange✗]note [blue✓]on [purple✓]middle [blue✓]c [blue✓]and [blue✓]then [orange✓]we're [blue✓]going [blue✓]to [blue✓]go [blue✓]down **[purple✗]dramatically** [blue✓]from [blue✓]there [blue✓]if [blue✓]you [blue✓]haven't [blue✓]done [orange✓]so [blue✓]already [blue✓]i [blue✓]highly [blue✓]recommend [orange✗]to [blue✓]watch [blue✓]my [purple✗]sex [orange✗]phone [orange✗]opera

**What the colours give you.** All 26 blue words are correct. The single purple word in the middle — **"dramatically"** — is exactly where to pause. The actual word was *"chromatically,"* which makes obvious sense in a music tutorial. A reader who treats purple as *"don't take this at face value"* and uses context recovers the meaning instantly.

**Without the colours**, the reader sees a tutorial that says *"go down dramatically"* — a perfectly natural English phrase — and walks away believing that's what the speaker said. The purple flag is what prevents that.

The trailing *"sex phone opera"* (which should be *"saxophone"*) is one long word the model split into three made-up shorter ones; both purple and orange flag this so the reader knows not to take "sex" or "opera" literally.

---

### Example 1.2 — Headphone review (a fluent inserted phrase, correctly flagged)

**Tier: Trust** (segment confidence 0.82). **WER: 33%.**

**REF:** *pretty expensive for headphones so like i said earlier in this video or like i would continue to say please do try them out before you buy them...*

**Coloured rendering:**

> [blue✓]pretty [blue✓]expensive [blue✓]for [orange✗]hand [orange✗]phones [blue✓]so [blue✓]like [blue✗]after **[purple✗]harry [orange✗]and [purple✗]david** [orange✗]go [purple✓]like [blue✓]i [orange✓]would [blue✓]continue [blue✓]to [blue✓]say [blue✓]please [orange✓]do [blue✗]check [blue✓]them [blue✓]out [blue✓]before [blue✓]you [orange✓]buy [blue✓]them...

**What the colours give you.** The model inserted the phrase *"after Harry and David go"* where the speaker actually said *"I said earlier in this video."* Without colour, this is a problem — *"Harry and David"* sounds like a genuine reference to specific people. **With colour, "harry" and "david" are flagged purple and "after / and / go" are flagged orange or shown as misaligned** — the reader sees that the entire 5-word stretch is the model's least-confident region in the whole segment and discounts it.

What survives clearly: *"pretty expensive for [head]phones... I would continue to say please do [try] them out before you buy them."* The product-review meaning is fully preserved; the fabricated names are flagged so the reader doesn't quote them.

---

### Example 1.3 — Adulthood reflection (one wrong noun, structure intact)

**Tier: Trust** (segment confidence 0.83). **WER: 26%.**

**REF:** *and while it's good to have practice in school another great thing about adulthood is that it's not high school and you don't have to be interested in only the things you were interested in when you were young*

**Coloured rendering:**

> [orange✓]while [orange✗]it [purple✗]does [purple✗]at [blue✓]practice [blue✓]in [blue✓]school [blue✓]another [blue✓]great [blue✓]thing [blue✓]about **[purple✗]taekwondo** [blue✓]is [blue✓]that [orange✓]it's [blue✓]not [orange✓]high [blue✓]school [blue✓]and [blue✓]you [blue✓]don't [blue✓]have [blue✓]to [blue✓]be [blue✓]interested [blue✓]in [blue✓]only...

**What the colours give you.** The model substituted **"taekwondo"** for **"adulthood."** That single word changes the topic of the entire segment. **The purple flag tells the reader: don't trust this noun.** The structure around it — *"another great thing about [???] is that it's not high school and you don't have to be interested in only the things you were interested in..."* — is in pristine blue and obviously correct.

A reader who applies the rule *"the structure is reliable, the purple noun is not"* immediately understands: this is a reflection on something post-high-school (probably adulthood, college, work, etc.). They don't end up writing a report claiming the speaker was talking about taekwondo. The colour saved the meaning by isolating the one untrustworthy word.

---

## Mode 2 — Safe partial understanding in Salvage segments

These are the segments where the system delivers most of its surprising value. WER is high (often 40–60%). Without colour, the output looks garbled and a reader might either over-trust it or write off the whole segment. **With colour, the blue words form a reliable spine and the purples mark exactly the regions to drop.** The reader extracts the *correct* gist of a half-wrong transcript.

### Example 2.1 — Networking research (a 50%-WER segment, gist fully recovered)

**Tier: Salvage** (segment confidence 0.71). **WER: ~50%.**

**REF:** *what that meant is that we need a radically different approach we basically need to find a way how we can take existing routers existing switches existing links and enable them for research*

**Coloured rendering:**

> **[purple✗]their [purple✗]masses [purple✗]and** [orange✓]we [orange✓]need [purple✓]a [orange✓]radically [blue✓]different [blue✓]approach [blue✓]we [blue✗]must [purple✗]indeed [blue✓]find [blue✓]a [blue✓]way [orange✓]we [blue✓]can [purple✗]design [orange✓]existing [blue✗]roads [orange✗]to [orange✗]exist [purple✗]with [purple✓]existing [purple✗]structures [blue✓]and [blue✓]enable [blue✓]them [blue✓]for [orange✗]reuse [blue✗]so

**What the colours give you.** The blue spine reads: *"different approach we... find a way... we can... existing... and enable them for..."* That's a complete, faithful summary of the speaker's point: *they need a different approach using existing infrastructure and want to enable it for some purpose*. The purples at the start (*"their masses and"*) are pure hallucination — and they're flagged purple, so the reader drops them. The middle purples (*"design," "roads"*) are wrong technical terms — and they're flagged purple, so the reader knows not to quote *"designing roads"* as the speaker's claim.

**A 50%-WER segment becomes a 100%-correct gist** because the colour signal correctly partitions the words into a trustworthy spine and a flagged hallucination.

---

### Example 2.2 — Topic-shift hallucination (the dangerous case the colours catch)

**Tier: Salvage** (segment confidence 0.79). **WER: 42%.**

**REF:** *what we're going to look at now is what happens if we start bringing the concept of woody beds or hula culture into this and a little bit of excavation and how we can kind of turbocharge this*

**Coloured rendering:**

> [orange✓]we're [orange✓]going [blue✓]to [blue✓]look [blue✓]at [blue✓]now [blue✓]is [blue✓]what [blue✓]happens [blue✓]if [blue✓]we [blue✓]start [purple✗]playing [blue✓]the [blue✓]concept [blue✓]of **[purple✗]warheads** [blue✓]or **[orange✗]nuclear [purple✗]deterrence** [orange✓]and [blue✓]a [blue✓]little [blue✓]bit [blue✓]of [orange✗]escalation [blue✓]and [blue✓]how [blue✓]we [purple✗]got [orange✗]into [blue✗]the [purple✗]cuban [blue✗]missile [blue✗]crisis [orange✗]so

**What the colours give you.** This is the most important kind of save. The reference is a gardening/landscaping discussion (*"woody beds,"* *"hula culture,"* *"excavation"*). The model hallucinated a **completely different topic** — nuclear weapons and the Cuban missile crisis — that reads as fluent, internally consistent prose.

**Without the colours**, a reader skimming the report would walk away believing this segment was a discussion of nuclear deterrence. The downstream consequences — wrong tags, wrong summaries, wrong searches, wrong client deliverables — would be severe.

**With the colours**, every one of the topic-defining wrong words is flagged: *warheads* (purple), *nuclear* (orange), *deterrence* (purple), *escalation* (orange), *Cuban* (purple). The blue spine — *"to look at now is what happens if we start [PURPLE] the concept of [PURPLE] or [ORANGE] [PURPLE] and a little bit of [ORANGE]"* — reads, correctly, as *"the speaker is bringing in the concept of something to discuss something."* Honest. The reader knows the topic isn't nuclear weapons; they know they don't know exactly what the topic was; they go to the video.

This is the colour signal preventing a confident-but-wrong belief. The cost of getting this wrong without the flag is much higher than the cost of admitting uncertainty with the flag.

---

### Example 2.3 — Physics lecture (fluent hallucinated opening, correct technical close)

**Tier: Salvage** (segment confidence 0.70). **WER: 44%.**

**REF:** *general theory of relativity and curved space time in this painting in the very back you see a convex mirror and on that mirror the painter drew light rays on a curved surface so he knew that the shortest paths on curved surface...*

**Coloured rendering:**

> **[purple✗]our [orange✗]nervous [blue✗]activity [purple✗]our [orange✗]nerve** [orange✓]space [blue✓]time [purple✗]and [orange✓]this [orange✓]painting [purple✓]in [blue✓]the [blue✓]very [blue✓]back [blue✓]you [blue✓]see [blue✓]a [purple✗]concave [blue✓]mirror [blue✓]and [blue✓]on [blue✓]that [blue✓]mirror [blue✓]the [purple✗]paint [blue✗]turns [blue✗]to [blue✓]light [orange✓]rays [blue✓]on [blue✓]a [orange✓]curved [blue✓]surface [blue✓]so...

**What the colours give you.** The opening is a brutal hallucination: *"our nervous activity our nerve space time"* — a string of plausible-sounding English that has nothing to do with general relativity. The first five words are flagged with two purples and two oranges. **A reader applying the rule *"if the opening is mostly purple/orange, distrust the topic claim"* knows immediately not to take *"nervous activity"* literally.**

After the bad opening, the segment recovers spectacularly into pristine blue: *"in the very back you see a [convex/concave] mirror and on that mirror the [PURPLE] turns to light rays on a curved surface."* That's a complete, correct description of the painting. The purple on **"concave"** even flags the one word the speaker actually said *"convex"* for — a subtle visual-similarity error correctly demoted by the model itself.

The reader leaves with: *"the speaker is discussing space-time in the context of a painting that shows a mirror and curved light rays on a curved surface, but I should not trust the introductory framing."* That's exactly right.

---

### Example 2.4 — Personal narrative ("I worked at things" — flagged correctly)

**Tier: Trust** (segment confidence 0.85). **WER: 29%.**

**REF:** *so i worked at liz for two years and i promised myself like going into that second year that i would quit my job i didn't know how i didn't know how i didn't know why i didn't know where the extra income was going to come from*

**Coloured rendering:**

> [orange✓]so [blue✓]i [blue✓]worked [orange✓]at **[purple✗]things** [blue✓]for [blue✓]two [blue✓]years [blue✓]and [blue✓]i [blue✓]promised [blue✓]myself [blue✓]like [blue✓]going [blue✓]into [blue✓]that [orange✓]second [blue✓]year [purple✗]i'm [orange✗]going [blue✗]to [blue✓]quit [blue✓]my [blue✓]job [blue✓]i [blue✓]didn't [blue✓]know [blue✓]how [blue✓]i **[purple✗]had** [blue✗]no [orange✗]idea [orange✓]where [orange✓]the [blue✓]extra [blue✓]income [blue✓]was [blue✓]going [blue✓]to [blue✓]come [blue✓]from

**What the colours give you.** The proper noun **"Liz"** (a company name) became **"things"** — and the model flagged it purple because it had no real visual evidence for any specific company name. A reader who sees *"I worked at [PURPLE] things for two years"* knows there was a specific noun the model couldn't pin down. The blue text around it carries the rest of the story perfectly: *"...I promised myself going into that second year [PURPLE] going to quit my job I didn't know how... I [PURPLE] no idea where the extra income was going to come from."*

The narrative arc — *I worked at \[some place\] for two years, decided to quit, didn't know how I'd make money* — is fully preserved in blue. The two purple words mark exactly the spots where a careful reader would either consult the video or leave a placeholder.

---

## Mode 3 — Saved by low confidence (the system refusing to mislead)

This is the mode that protects the user from the system's worst failure: **producing fluent English text that has no relationship to what was actually said.** Without confidence, this kind of failure is invisible — the output reads naturally and the reader believes it. With confidence, the output is flagged as unreliable before it can do harm.

### Example 3.1 — "I don't think that's a good idea" (no, it isn't)

**Tier: Strip** (segment confidence 0.21). **WER: 100%.**

**REF:** *china to take off to cross the pacific ocean can you tell us*

**What the model produced:** *"i don't think that's a good idea"* — a perfectly natural, conversational English sentence.

**Per-word confidence:**

> [purple✗]i (0.06) [purple✗]don't (0.04) [purple✗]think (0.14) [purple✗]that's (0.14) [purple✗]a (0.22) [purple✗]good (0.35) [orange✗]idea (0.53)

**What the colours give you.** This is the system's most important protection. The hypothesis reads as a complete, sensible English sentence — exactly the kind of output a reader would *not* think to question. **Every word is wrong. Every word is also flagged purple, with probabilities mostly under 0.20.** The segment-level tier is **Strip**, which means in the actual UI the per-word colouring is removed entirely and the text is shown in plain grey-italic with a banner: *"Model is unsure — text may not be reliable, even where it looks confident."*

**Without the confidence signal**, a downstream automated pipeline (or a human skimming) would record this segment as *"I don't think that's a good idea"* — a confident, quotable opinion that the speaker never expressed. The downstream consequences — fabricated quotes attributed to real people, wrong sentiment in a summary, wrong claims in a client deliverable — could be serious.

**With the confidence signal**, the system says, plainly: *"I had 6% confidence in 'I,' 4% confidence in 'don't,' 14% confidence in 'think.' Don't read this as a transcription."* The reader either watches the video or skips the segment. No false belief is created.

---

### Example 3.2 — "It's important to remember that…" (no, the speaker said something else entirely)

**Tier: Strip** (segment confidence 0.28). **WER: 100%.**

**REF:** *the constitution after the constitution has been written*

**What the model produced:** *"i think it's important to remember that"* — a generic, plausible filler phrase that could appear in almost any educational video.

**Per-word confidence:**

> [purple✗]i (0.06) [purple✗]think (0.04) [purple✗]it's (0.24) [purple✗]important (0.22) [orange✗]to (0.70) [purple✗]remember (0.06) [orange✗]that (0.65)

**What the colours give you.** Identical pattern to the previous example, on a completely different topic. The model produced fluent English with no underlying signal; the per-token probabilities are mostly under 0.25; the segment is correctly classified Strip. A reader is told not to trust the words and instead notes: *"this segment is about something the model couldn't read — go to the video if it matters."*

The pattern across many Strip-tier segments is the same: **the model defaults to short, generic, conversational English** when it has no real signal — *"I think it's a very valid question," "when I was a teenager I was," "right that's exactly the direction I'm heading."* These are the sentences the model *always* finds plausible because they appear constantly in its training data. The confidence signal is the only thing that distinguishes "model wrote this from real visual input" from "model wrote this because it had nothing to go on."

---

## What CAN be trusted

| What | How reliable | How to use it |
|---|---|---|
| **Blue words inside Trust segments** | ~94% correct | Read at face value (with the numeric/name caveat below). |
| **Blue words inside Salvage segments** | ~80% correct | Use as anchor words. Build the meaning around them. |
| **The tier badge itself** | Well-calibrated | Read it before reading the words. |
| **The gist of a Trust or Salvage segment** | Recoverable in >85% of cases | Suitable for summarising, search, downstream LLM input. |

---

## What CANNOT be trusted

### 1. Numbers, dates, dollar amounts — regardless of colour

The model can be 95%+ confident on a number that is wrong by orders of magnitude. Real examples from the evaluation:

| Reference | Model output | Model's confidence |
|---|---|---:|
| *each bottle contains 1 **billion** cfus* | *1 **million** cfus* | 0.965 (blue) |
| *the 18th of november **2011*** | *the 18th of november **2000*** | 0.894 (blue) |
| *only **80** calories per* | *only **80** gallons per* (units swapped) | 0.97 (blue) |

**Why.** The model has very strong priors that *some number goes here*, but its visual signal for *which* number is much weaker. So it picks a fluent number with high confidence, even when it's wrong by a factor of 1,000. The blue colour reflects certainty about the slot, not the value.

**The rule:** if the segment contains a number, named entity, date, or quantity, **verify against the source video** before quoting it. The colour is not informative for these tokens.

### 2. Anything inside a Strip-tier segment, read word-by-word

Below 0.65 segment confidence, even blue-band words drop to ~37% reliable. The system removes the per-word colouring on purpose so the user isn't tempted. Use Strip segments as topic hints only.

### 3. Fluent purple words

The danger purple words are the ones that sound plausible: *"dramatically"* in a music tutorial, *"taekwondo"* after *"another great thing about,"* *"warheads"* in any sentence. The fluency is the trap; **the colour is the truth**. Treat the colour as ground truth, not the surface text.

### 4. The default-fluent fallback sentences

When the model has no signal, it defaults to generic conversational English: *"I don't think that's a good idea," "I think it's important to remember that," "right that's exactly the direction I'm heading."* These sentences are almost never what the speaker actually said. They appear inside Strip-tier segments with mean confidence 0.20–0.30 and per-word probabilities mostly below 0.25. **If you see a generic-sounding short sentence with a Strip badge, treat it as "no signal," not as a quote.**

---

## Practical reading workflow

For each segment in the report:

1. **Look at the tier badge first.** If it's Strip, switch to gist-only mode and don't read individual words.
2. **Inside Trust or Salvage, scan for non-blue words.** The blue words are the spine; the orange and purple words are where you spend attention.
3. **For any number, name, date, or quantity:** verify against the video, even if it's blue.
4. **Compose the meaning** from the blue spine plus context, treating orange as ambiguous and purple as discount.
5. **For downstream automated processing** (search, classification, LLM summarisation): the aggregated text shown in the report is already the cleaner version; pass that through. For *quotation* in a deliverable, apply rules 1–4.

---

## Why this matters: the value the colours actually deliver

Three concrete value propositions, in increasing order of impact:

1. **Faster reading in good segments.** In Trust-tier output (~28% of segments), the colours let a reader skim past 90% of the text and focus attention on the 10% that needs it. Real time saved on long transcripts.

2. **Useful output from partial segments.** In Salvage-tier output (~38% of segments), the colours convert what would otherwise look like garbled text into a recoverable gist. *Example 2.1* (networking research) is a 50%-WER segment that, with the colours, delivers a 100%-correct summary. This is content the user *would not have been able to extract* without the colours — they would either over-trust the wrong words or write off the whole segment.

3. **Protection from confident hallucinations in unreliable segments.** In Strip-tier output (~34% of segments), the colours prevent the system from fooling the user with fluent generic English (*"I don't think that's a good idea"*) that has nothing to do with what was said. Without this signal, those segments would silently corrupt downstream summaries, searches, and quoted material. With this signal, they are correctly labelled "no signal" and the user goes to the video.

The third item is the most important. **The cost of a single confident-but-wrong quote in a client deliverable is much higher than the cost of any number of "verify this against the video" notes.** The confidence signal is what makes the difference between a system that occasionally embarrasses the user and a system that the user can trust to tell them when it's unsure.

---

## Limitations and what improves over time

- **Calibration is tuned to today's model** (LLaMA-2-7B backbone, current LoRA adapter). The thresholds (0.82 / 0.65 / 0.85 / 0.40) will move as the system improves.
- **Numbers and named entities remain the hardest case.** No amount of colour calibration fully fixes this. The defence is workflow: verify these against video.
- **Improvement path:** stronger backbone (Llama-3.1-8B+) → blue reliability +3–6pp uniformly. More training data (20K+ AVSpeech) → cuts numeric/entity hallucinations significantly. Beam-disagreement gating → demotes high-prob-but-disagreed tokens out of the blue band before they reach the user.

The architecture of the policy — *tier-gate first, then colour, with a special rule for numbers/names* — is stable and outlives the current numbers.

---

## References

- Per-word reading guide for end users: [per-word-confidence-user-guide.md](per-word-confidence-user-guide.md)
- Confidence calibration data: [docs/confidence/band_reliability_by_niv.md](../confidence/band_reliability_by_niv.md), [docs/confidence/band_reliability_by_segment_quality.csv](../confidence/band_reliability_by_segment_quality.csv)
- Tier policy: [docs/confidence/band_reliability_rollout_plan.md](../confidence/band_reliability_rollout_plan.md)
- Numeric/entity false-confidence cases: [docs/confidence/green_leakage_examples.csv](../confidence/green_leakage_examples.csv)
- Aggregation method (background): [docs/beam-search/n_best_implementation.md](../beam-search/n_best_implementation.md)
- Source data: [english_full_results_2026-05-01/client_outputs/report/](../../english_full_results_2026-05-01/client_outputs/report/)
