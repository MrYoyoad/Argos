# Client Meeting Framing & Key Concepts

Working reference document. Generated from the 48-hour-plan conversation. Update as your read of the room evolves.

---

## TL;DR

**Product:** Argos VSP — visual speech recognition (lip-reading from video, no audio).
**Meeting:** 2 hours, ~12 people in the room, mixed audience.
**Deck status:** ~49–50 slides, narrative restructured (Round 4), needs surgical depth additions.
**Core diagnosis from earlier:** the deck has the right material but lands hollow because there are 3 worked examples where the academic deck had ~18, and the *use case the deck implies* (broadcast/accessibility) isn't the *use case being sold* (surveillance).

---

## Use case reframe (the most important single thing)

The deck has been implicitly framed as media transcription / accessibility / broadcast. **It is none of those.**

The actual use case: **surveillance lip-reading for security/intelligence-adjacent work.** Two friends having coffee, observer 30 feet away with a high-quality iPhone, no audio. Recovering speech from footage where audio doesn't exist or can't be obtained. Indoor and outdoor. English now, Arabic later. Lengths from 20 seconds to an hour. Usually not selfie framing.

**This means the "compared to today" anchor is not "manual transcription is slow" or "auto-captions are inaccurate." It is "today, this information is not recoverable at all."** They don't get the speech today because lip-reading by humans is too marginal to bother with. You're not selling a faster horse; you're selling a capability they don't currently have.

Slides 2 ("who it's for") and 18 ("what that 62% is up against") need rewrites to match this framing.

---

## Audience composition

Roughly 12 people:

- **You + 3 managers + a rookie** — your side
- **Existing client:** team lead + 2 workers + a secondary team lead from a different team in the same company
- **2 technical people from a peer company** — these are **co-partners, not competitors.** They're collaborators on this engagement.
- **2 reps from a new prospective client**

### What this means

**The secondary team lead from your existing client is the highest-leverage person you didn't realize is the highest-leverage person.** They represent expansion within the existing relationship. If they leave saying "I want this for my team," your existing relationship doubles.

**Co-partners change the engineering ceiling.** Engineering depth is welcome, not a risk. Restore the engineering credibility material (bug changelog, dual-environment validation, git-tag history, "we built on three open-source codebases and integrated them" story). Architecture specificity is OK — partners want to see real choices. Still scrub LoRA-specific implementation details per the plan's N9 rule, but keep the architecture overview visible.

**New clients are cold.** First 10 minutes of the meeting do most of the work for them. Opening must answer "why am I in this room?" in 15 seconds.

**Existing client is warm.** They can move fast through foundational slides. Real time should go to the new material — confidence, multi-speaker, validation.

---

## Client's concerns, ranked

In order of how hard they pushed in sales conversations:

1. **Trust / truthfulness** — can they believe the output, will they catch hallucinations
2. **Multi-speaker** — their canonical use case is two-person conversational footage
3. **Multi-language** — Arabic eventually; specifics unknown (MSA vs. dialect — ask in the meeting)
4. **Ease of use technically** — non-technical client, UI matters

**Not concerns:**
- Inference cost (zero — standalone deployment)
- Latency (no problem at their use case)
- Per-minute pricing (they're not price-sensitive on operations)

**The investment ask is the exception.** Training money is the actual ask. Money matters there, but specifics don't.

---

## Trust story (the dominant theme)

In their world, an unflagged hallucination isn't an inconvenience — it's a wrong belief about a real conversation that they may act on. **The confidence story isn't a feature, it's the entire product.** This means:

- **Hallucination flagging gets three slides, not one.** "The model can confabulate fluent text" → "here's a real example" → "here's the system catching it." Make them feel the failure mode, then feel the catch.
- **Failure mode taxonomy is required.** All five categories with one real example and frequency each. Honest disclosure builds trust; hiding failure modes reads as marketing.
- **Validation slide needs reviewer specifics.** Don't say "independent expert reviewer" with no anchor. Name the protocol — "an independent automated reviewer with no access to our scores or reasoning, asked to judge whether the message was conveyed." Specificity = trust.

---

## Investment ask framing

They're not price-sensitive. The slide doesn't justify cost — it sizes the unlock.

**Three beats, no line items:**

1. **What they don't have today:** "Today's model is trained on a small slice of public data, not your domain. It works, but it's a prototype, not a production model on your content."
2. **The unlock as partnership:** "We're proposing we go from prototype to production *together* — your data, our pipeline, a shared training run on your domain."
3. **Concrete-but-not-priced ask:** "Specifics in follow-up." No dollar amount on slide. No compute/data/engineering breakdown.

**Connection to the data_ask slide that precedes it:**
> "Data without a training budget is a folder. Budget without data is a wishlist. Both together is a model trained on your content."

**Title should carry the partnership frame, not the budget frame.** Something like "The next milestone is a partnership" or "What we'd build with you" — not "What it takes to ship the next model."

---

## What "content rich" actually means here

The earlier "hollow" feeling came from low evidence-density per claim, not low slide count. Richness = **claim → evidence → example → implication**, repeated.

### Concrete additions (priority order)

**Critical:**
1. **Output gallery expanded from 3 to 8–10 examples** spanning domains. At least 2 should visually resemble the surveillance use case (two-person conversational, indoor, no audio). Pull from the existing judge examples in the academic deck.
2. **Failure mode taxonomy** — all five modes, real examples, real frequencies.
3. **Hallucination case study trio** — three consecutive slides on the failure-then-catch arc.
4. **Multi-speaker slide moved up** from section 12 to section 4 or 5. The entity_split work isn't a future ablation — it's the answer to their primary scenario. Frame honestly: "today the model handles single-speaker centered video; here's how we extend to multi-speaker, which is how most real-world surveillance footage looks."
5. **Validation specifics** — who the reviewer was, blind protocol, what was asked.

**Important:**
6. **Operational workflow slide for non-technical viewers** — "receive video → drag onto UI → wait → reviewer reads flagged segments." Five boxes, no jargon. For the managers in the room.
7. **Honest current limits slide** — extreme angles, very low light, multi-speaker without entity-split, named entities, non-English. Each item paired with "here's our path on it."

**Restored for partner audience:**
8. **Engineering journey slide** — bug-changelog, git-tag history, dual-environment validation, "built on three open-source codebases" story.

### What to NOT add

- The data-cost / GPU-time slide (they don't care)
- A dataset-diversity slide (useful but not central)
- Anything fabricated. **Pull from existing material — academic deck, reports, real history. If a beat needs new copy, flag it.**

---

## What's been decided (don't re-litigate)

- **WER:** not visible on client slides anywhere. Speaker notes only.
- **IS:** one definition, no decomposition. Suggested copy: "a 0–5 score per segment that predicts whether a viewer will understand the output. Combines word accuracy, meaning preservation, and named-entity recovery into one number, calibrated against an independent expert reviewer." The deep IS slides (slide_is_intro_a/b/c, slide_is_calc_examples, slide_is_deep_dive) live in **hidden appendix** — accessible live in 2 clicks if asked.
- **Funding ask slide stays** but reframed as partnership, no line items.
- **Architecture overview OK** (model names like LLaMA, AV-HuBERT can be visible) because of partner audience. Training-specific numbers (LoRA r-values) still scrubbed per N9.
- **No fabrication rule.** All depth comes from existing material — academic deck builders, real reports, real bug history.
- **Language-detection question is not a concern** for this use case — language is known at decode time in surveillance work. One sentence answer if it comes up; no roadmap commitment.

---

## Meeting structure (2 hours)

Audiences zone out around 40 minutes. Plan three acts with planned pauses.

**Act 1 (30 min) — "It works"**
Title → what it is → why hard → basic idea → demo video → output gallery (5–6 examples narrated live).
Pause: *"What questions are coming up so far?"* Wait for actual responses.

**Act 2 (40 min) — "You can trust it"**
Failure modes shown honestly → confidence story → hallucination trio → validation → confidence-conditional accuracy → reviewer workflow.
Pause: *"Where are you imagining this fitting into your workflow?"* Let them answer for 10 minutes; you'll learn what to skip in Act 3.

**Act 3 (40 min) — "Here's the path"**
Engineering credibility (bug history, dual environments) → multi-speaker capability → pre-processing roadmap → data ask → investment ask → integration commitment → next steps.

**Buffer (10 min)** — wrap, Q&A overflow, scheduling next steps.

Each planned pause turns a presentation into a conversation. The deck supports the conversation; it doesn't drive it.

---

## Things to do before the meeting

1. **Run 3–5 segments through the system that look like their actual use case** — two-person conversational footage from across a room. Show them "we ran your scenario through the day before our meeting." Even mixed results work; that's what the confidence layer is for. The *act of doing it* signals you take their problem seriously.

2. **Coordinate with the co-partners.** Five-minute call. Pick one of:
   - You drive the deck, they chime in on questions in their domain
   - You drive, they present 1–2 slides on their piece
   - Joint walkthrough trading off by section
   This conversation is more important than any deck change.

3. **Ask in the meeting (don't promise on a slide):**
   - Which Arabic? MSA vs. Levantine vs. Egyptian vs. Gulf.
   - What does their canonical video actually look like — duration, environment, speakers?
   - What does "good enough" look like for their workflow?

4. **Cheat sheet for hidden appendix slides.** One line in PRE_MEETING_CHECKLIST.md or speaker notes of the last visible slide: "If asked about IS internals → slide 47. If asked about cross-config stability → slide 49." You'll fumble in the meeting without this.

---

## Number Clarity Rules (reference)

Every number on every slide must follow these. The number_audit test enforces it.

- **N1 — Translate jargon.** "κ=0.818" → "agrees with an independent expert reviewer in 82% of cases."
- **N2 — Define on first use.** Plain English before acronyms.
- **N3 — Always pair % with what it's a % of.**
- **N4 — Use "1 in N" framing for client-facing rates.**
- **N5 — Round to one decimal max on slide.**
- **N6 — Include the n wherever a percentage is reported.**
- **N7 — No contradictions of magnitude.**
- **N8 — Single source of truth (MEMORY.md > Key Project Numbers).**
- **N9 — No κ / kappa / PCA / NIV / LoRA-r labels visible.**
- **N10 — Comparable numbers stay comparable.**

### Canonical numbers for visible client slides

- 62% useful output (1,497 segments)
- 23% clearly conveyed (about 1 in 4)
- 1 in 5 segments auto-flagged (20.5%)
- 82% agreement with independent expert reviewer
- Average IS: 2.5 / 5 (used once, headline-numbers slide only)

### Numbers explicitly NOT on visible client slides

LoRA r-values, "1,273 vs 20,000+ segments," PCA component percentages, cross-config Pearson r, raw WER/WWER, hallucination 20.5% (use "1 in 5" instead), salvage 51.1%, fine-tuning IS comparison.

---

## Working prompt fragments to reuse with the agent

### When asking the agent to make changes
> "Propose a slide-by-slide diff against the current deck before executing. Wait for go-ahead."

### When the agent might fabricate
> "No fabrication. Pull from existing slides, reports, and academic deck. If a beat needs new copy, flag it for me — don't invent."

### When invoking the audit chain
> "Run all 7 audits + visual QA subagent before declaring done. Append to DECK_CHANGELOG.md."

### When invoking the borrow rule
> "Borrow, don't rewrite. Import existing builders from presentation/slides_*.py. Only the new content gets new builders."

---

## Meta-note

The questions worth preparing for are the ones your specific clients have actually asked or hinted at — not the ones an outside observer would predict. When outside-observer predictions don't match your read, trust your read. You've been talking to these people; outside framing is pattern-matching from outside.
