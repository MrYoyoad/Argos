# Client Meeting Framing & Key Concepts

Working reference for the 2-hour client meeting. Anchored in real numbers and real artifacts from the 84-slide academic deck (AFTER_AMOSI.pptx) and the demo recording. Update as your read of the room evolves.

---

## TL;DR

**Product:** Argos VSP — visual speech recognition (lip-reading from video, no audio).
**Meeting:** 2 hours, ~12 people in the room, mixed audience.
**Use case being sold:** surveillance lip-reading. Two friends in a coffee shop, observer 30 feet away, iPhone footage, no audio. Indoor and outdoor. English now, Arabic later.
**Deck status:** ~50 slides, narrative restructured (Round 4), needs surgical depth additions.
**Core insight:** the deck has the right material but needs to be re-framed around what's been *achieved* — concrete, dated, validated — rather than what's been *researched*.

---

## Use case reframe (still the most important single thing)

The deck has been implicitly framed as media transcription / accessibility / broadcast. **It is none of those.**

The actual use case: **surveillance lip-reading for security/intelligence-adjacent work.** Recovering speech from footage where audio doesn't exist or can't be obtained. Indoor and outdoor. Lengths from 20 seconds to an hour. Usually not selfie framing.

Slides 2 ("who it's for") and 18 ("what that 62% is up against") need rewrites to match this framing.

---

## Compared to today (the comparative anchor)

The client doesn't have a "current vendor" — they have two unsatisfactory options:

### Option 1 — Manual lip-reading by human experts

Real numbers from the academic deck (slide 7):
- **Expert human lip-readers: 45–52% word accuracy.**
- **System + human reviewer: 55–70% word accuracy, with near-zero hallucination risk.**

The system *plus* a human reviewer using the colored confidence report outperforms expert humans alone. And critically — the human reviewer using Argos can audit the work in minutes per video, where an expert lip-reader does the entire decoding from scratch.

This is a real, concrete comparative claim, anchored in published data on expert human performance. **It belongs on a slide in Section 1.**

### Option 2 — Don't do it at all

For most footage, expert lip-reading is too marginal in accuracy and too expensive in expert time to bother with. The result: **the speech in the video is simply not recovered**. The information sits in the footage, inaccessible.

This is the more common reality for the client. Argos converts unrecoverable footage into reviewable text with calibrated trust signals.

### Suggested comparison slide structure

A 3-row × 3-column table fits this story tightly:

| Approach | Word accuracy | Time per hour of video | Hallucination risk |
|---|---|---|---|
| Expert human lip-reader | 45–52% | hours of expert time | varies, hard to audit |
| Don't do it at all | — | 0 (information is lost) | — |
| **Argos (system + reviewer)** | **55–70%** | minutes of reviewer time | **near-zero, flagged** |

Place this in Section 1, immediately after "what this is" and before the demo. It anchors everything that follows.

---

## What we have — the achievement inventory

Everything below is real, dated, validated, and pulled from AFTER_AMOSI.pptx or the live UI demo. **No fabrication.** Frame these as what's been accomplished in four months — *not* what's still aspirational.

### Working product (visible in the live demo)

- **Live UI, browser-based.** Drag-and-drop upload, no command line, no scripting. Recorded demo video shows real end-to-end use, ~4–5 min.
- **Eight-stage automatic pipeline.** Face detection → mouth crop → visual encoding → projection → language decoding → confidence scoring → report generation. Visible to the user as it runs.
- **Standalone deployment.** Containerized, runs on the client's hardware. No internet required at runtime. AWS deployment validated end-to-end against the same container — same code, same outputs.
- **HTML report output.** Per-word color coding (green/yellow/red), per-segment trust score, downloadable, shareable with reviewers.
- **Per-word confidence layer (Tier 2 — just shipped this round).** Every predicted word carries a probability the model assigned it, surfaced visually in the report.

### Validated capabilities (1,497 real-world segments, not curated benchmark)

- **62% useful output.** Six of every ten segments deliver usable text on unfiltered real-world YouTube video. (vs. 25% if measured by WER alone — the standard metric understates real-world quality by ~2.4×.)
- **23% clearly conveyed.** About 1 in 4 segments needs no review.
- **1 in 5 segments auto-flagged.** The system detects its own low-confidence outputs before they reach the reviewer. This is the dangerous-failure-detection layer.
- **82% agreement with an independent expert reviewer.** 1,497 reference+hypothesis pairs, blind, three-level verdict (preserved / partial / not preserved). Intra-rater reliability 86.7% on a 30-pair duplicate sample.
- **Trust signal stable across configurations.** Tested across 16 different decode settings on the same 1,497 segments; the trust signal moved less than a percentage point.
- **100% precision on segments rated "clearly conveyed."** When the system says clearly conveyed, the expert agrees in every case tested.
- **System + human reviewer outperforms expert lip-readers.** 55–70% accuracy vs. 45–52% for expert humans alone. Near-zero hallucination risk because the system flags its own uncertainty.

### Trust framework (the differentiator)

- **Per-segment Intelligibility Score (IS).** 0–5 score combining word accuracy, meaning preservation, and named-entity recovery into one number. Calibrated against the independent expert reviewer.
- **Per-word color coding.** Green = high confidence, yellow = review, red = likely error.
- **Hallucination flagging.** When the model produces fluent text it isn't sure about, the system catches it via length anomaly detection + per-token confidence.
- **Failure mode taxonomy.** Five categorized modes with real frequencies on the 574 below-threshold segments:
  - Wrong Topic — 44.4% (255 segments) — mouth shapes decoded to wrong domain
  - Hallucination — 18.8% (108) — model invented fake text
  - Signal Loss — 13.9% (80) — empty or near-empty output
  - Right Topic, Wrong Details — 13.8% (79) — gist right, names/content lost
  - Accumulated Errors — 9.1% (52) — many small errors compound

### Concrete examples available (already rendered in academic deck)

These are gold for richness — pull them directly into the client deck. **Existing builders, just relabel per N1–N10.**

- **6 judge examples** with side-by-side ref/hyp panels: Bernreuter→Rogers (named entity swap, meaning preserved), Admiral McRae→animal migration (destructive substitution), the cooking-jalapeno example, the religious sermon, the topic-hijack, the technical vocabulary drift. Each is a 30-second story.
- **3 salvage examples** — segments the system flagged as low-confidence that a domain-aware viewer would still recover meaning from. The "system errs toward review, not fluent fabrication" story.
- **3 failure mode worked examples** with full ref/hyp/score panels.

### Engineering credibility (for the partner audience)

- **Built on three open-source codebases** (auto_avsr, av_hubert, VSP-LLM). Integrated, not reinvented.
- **37 bugs fixed and documented** during the engineering pass. We keep an open changelog.
- **Dual-environment validation.** Same code, AWS and on-premise. Git-tag history: refactor-v1.0 → ec2-v1.1 → container-v1.1.
- **Eight comprehensive research reports** documenting the work.
- **Reproducible container build.** Verified working on standalone hardware.

### What's planned but not built (be honest about these)

- **Multi-speaker handling** — entity-split preprocessing (face detection + tracker for per-speaker crops). Planned ablation. **This is the gap to flag honestly because it's their canonical use case.**
- **Quality pre-filter** — frame-level CV checks for head pose, mouth visibility, lighting. Planned ablation.
- **Stronger language model** — drop-in upgrade requires retraining. Needs investment.
- **Training on more domain data** — current model trained on a small slice. Needs investment + client data.
- **Arabic implementation** — roadmap mapped, work not started. Realistic timeline 2–3 months from green-light, encoder pre-training is the bottleneck.

---

## 2-hour meeting structure (timed)

Audiences zone out around 40 minutes. Three acts with planned pauses. The deck supports the conversation; it doesn't drive it.

### Act 1 — "It works" (0:00–0:30)

**The point of this act:** prove the product is real before discussing anything else.

| Time | Content | Anchored in |
|------|---------|-------------|
| 0:00–0:05 | Title, hello, brief intros around the room | — |
| 0:05–0:08 | What visual speech recognition is + the surveillance use case framing | Background slide |
| 0:08–0:12 | **Compared to today** — expert lip-readers 45–52%, no-audio = unrecoverable, Argos+reviewer = 55–70% with near-zero hallucination | New comparison slide |
| 0:12–0:14 | Why hard — visemes (50–70% of English sounds invisible on lips) | Visemes slide from academic deck |
| 0:14–0:17 | Basic idea — three components end-to-end | Pipeline components slide |
| 0:17–0:20 | What we built — engineering journey, 37 bugs fixed, dual environments | Engineering journey slide |
| 0:20–0:25 | **Live UI demo video** — drag-drop, 8 stages, color-coded report | Recorded demo |
| 0:25–0:30 | Output gallery — narrate 5–6 real examples across domains | Pull from 6 judge examples |

**Pause around 0:30:** *"What questions are coming up so far?"* Wait for actual answers. Eight minutes of unstructured discussion is not a problem — it's the meeting working.

### Act 2 — "You can trust it" (0:38–1:18)

**The point of this act:** build the trust story. This is the dominant theme for this audience and gets the most time.

| Time | Content | Anchored in |
|------|---------|-------------|
| 0:38–0:42 | Headline numbers — 62% useful, 23% clearly conveyed, 1 in 5 auto-flagged. Lands as summary, not opening claim. | Round-4 reorder |
| 0:42–0:45 | "How do you know when to trust an output?" — problem statement | Confidence question slide |
| 0:45–0:50 | Two layers of confidence: per-word + per-segment | Two-layer confidence slide |
| 0:50–0:55 | Per-word color coding with screenshot from UI | New screenshot from Tier 2 work |
| 0:55–1:02 | **Hallucination case study trio** — "model can confabulate" → "real example" → "system caught it" | Pull hallucination example from academic deck |
| 1:02–1:08 | **Failure mode taxonomy** — all 5 modes with real frequencies and one example each | Failure-mode slides from academic deck |
| 1:08–1:13 | Validation: 1,497 segments, blind protocol, independent expert reviewer agreed in 82% of cases. **Name the protocol.** | Validation slide + reviewer specifics |
| 1:13–1:18 | What this means for your workflow — review only flagged segments | Workflow slide |

**Pause around 1:18:** *"Where are you imagining this fitting into your workflow?"* Let them answer for 8–10 minutes. You'll learn what to skip in Act 3.

### Act 3 — "Path forward" (1:25–2:00)

**The point of this act:** show engineering credibility (for partners), set up the multi-speaker capability (their canonical case), make the partnership ask.

| Time | Content | Anchored in |
|------|---------|-------------|
| 1:25–1:30 | Engineering receipts — three open-source codebases integrated, 37 bugs fixed, dual environments | Engineering credibility slide |
| 1:30–1:35 | **Multi-speaker capability** — your canonical use case. Honest: today single-speaker; here's the entity-split path | Entity-split slide (moved up) |
| 1:35–1:40 | Pre-processing roadmap — entity split + quality filter as planned ablations | Pre-processing slides |
| 1:40–1:43 | Arabic adaptation — high-level, "the path is mapped, specifics on request" | Arabic roadmap slide (one slide only) |
| 1:43–1:50 | Data ask + Investment ask — partnership framing, no line items | data_ask + investment_ask slides |
| 1:50–1:55 | Integration commitment — we deploy on your infrastructure, end-to-end | Integration slide |
| 1:55–2:00 | Recap (three emotional beats), next steps, thank you | Closing slides |

**Buffer (last 10 minutes or after formal close):** Q&A overflow, individual conversations, scheduling.

---

## Audience composition

Roughly 12 people:

- **You + 3 managers + a rookie** — your side
- **Existing client:** team lead + 2 workers + a secondary team lead from a different team in the same company
- **2 technical people from a peer company** — **co-partners, not competitors.** Collaborators on this engagement.
- **2 reps from a new prospective client**

### What this means

**The secondary team lead from your existing client is the highest-leverage person you didn't realize is the highest-leverage person.** They represent expansion within the existing relationship. If they leave saying "I want this for my team," your existing relationship doubles.

**Co-partners change the engineering ceiling.** Engineering depth is welcome, not a risk. Architecture specificity is OK — partners want to see real choices for integration. Keep model names visible. Still scrub LoRA-specific implementation details per the plan's N9 rule.

**New clients are cold.** First 10 minutes do most of the work for them. Opening must answer "why am I in this room?" in 15 seconds. **The "compared to today" slide is critical for this group** — it tells them what problem you're solving in concrete terms.

**Existing client is warm.** They can move fast through foundational slides. Real time should go to the new material — Tier 2 confidence, multi-speaker capability, validation specifics.

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
- Language detection (they know who they're watching)

**The investment ask is the exception.** Training money is the actual ask. Money matters there, but specifics don't.

---

## Trust story (the dominant theme)

In their world, an unflagged hallucination isn't an inconvenience — it's a wrong belief about a real conversation that they may act on. **The confidence story isn't a feature, it's the entire product.**

- **Hallucination flagging gets three slides, not one.** "The model can confabulate fluent text" → "here's a real example" → "here's the system catching it." Make them feel the failure, then feel the catch.
- **Failure mode taxonomy is required.** All five categories with real frequencies. Honest disclosure builds trust; hiding failure modes reads as marketing.
- **Validation slide needs reviewer specifics.** Don't say "independent expert reviewer" with no anchor. Name the protocol — "an independent automated reviewer with no access to our scores or reasoning, asked to judge whether the message was conveyed in three levels: preserved, partial, not preserved." Specificity = trust.

---

## Investment ask framing

They're not price-sensitive. The slide doesn't justify cost — it sizes the unlock.

**Three beats, no line items:**

1. **What they don't have today:** "Today's model is trained on a small slice of public data, not your domain. It works, but it's a prototype, not a production model on your content."
2. **The unlock as partnership:** "We're proposing we go from prototype to production *together* — your data, our pipeline, a shared training run on your domain."
3. **Concrete-but-not-priced ask:** "Specifics in follow-up." No dollar amount on slide. No compute/data/engineering breakdown.

**Connection to data_ask slide that precedes it:**
> "Data without a training budget is a folder. Budget without data is a wishlist. Both together is a model trained on your content."

**Title should carry the partnership frame, not the budget frame.** "The next milestone is a partnership" or "What we'd build with you" — not "What it takes to ship the next model."

---

## What's been decided (don't re-litigate)

- **WER:** not visible on client slides anywhere. Speaker notes only.
- **IS:** one definition, no decomposition. Suggested copy: "a 0–5 score per segment that predicts whether a viewer will understand the output. Combines word accuracy, meaning preservation, and named-entity recovery into one number, calibrated against an independent expert reviewer." Deep IS slides hidden in appendix.
- **Funding ask slide stays** but reframed as partnership, no line items.
- **Architecture overview OK** (model names like LLaMA, AV-HuBERT can be visible) because of partner audience. Training-specific numbers (LoRA r-values) still scrubbed per N9.
- **No fabrication rule.** All depth comes from existing material — academic deck builders, real reports, real bug history, the live demo recording.
- **Language detection question is not a concern** for this use case. One-sentence answer if it comes up; no roadmap commitment.
- **Demo video stays embedded, not linked.** Plays offline. Section 2.
- **Slide redos OK if needed**, but utilize existing slide builders where they exist. Borrow, don't rewrite.

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
- Expert human lip-readers: 45–52% word accuracy
- System + human reviewer: 55–70% word accuracy

### Numbers explicitly NOT on visible client slides

LoRA r-values, "1,273 vs 20,000+ segments," PCA component percentages, cross-config Pearson r, raw WER/WWER, hallucination 20.5% (use "1 in 5" instead), salvage 51.1%, fine-tuning IS comparison.

---

## Working prompt fragments to reuse with the agent

### When asking the agent to make changes
> "Propose a slide-by-slide diff against the current deck before executing. Wait for go-ahead."

### When the agent might fabricate
> "No fabrication. Pull from existing slides, reports, academic deck (AFTER_AMOSI.pptx), and the demo recording. If a beat needs new copy, flag it for me — don't invent."

### When invoking the audit chain
> "Run all 7 audits + visual QA subagent before declaring done. Append to DECK_CHANGELOG.md."

### When invoking the borrow rule
> "Borrow, don't rewrite. Import existing builders from presentation/slides_*.py. Only the new content gets new builders. Slide redos are fine if needed, but check for an existing builder first."

### When pulling from the academic deck for examples
> "Pull from the existing slide_judge_ex1-6, slide_failure_modes, slide_llm_salvage builders. Translate score labels per N1-N10. Keep ref/hyp panel structure intact."

### When adding the comparison slide
> "Add a 'compared to today' comparison slide in Section 1. Three rows: expert human lip-reading (45–52% accuracy, hours of expert time, hallucination risk), don't-do-it-at-all (0%, 0 time, information lost), Argos + reviewer (55–70% accuracy, minutes of reviewer time, near-zero hallucination because flagged). Numbers from academic deck slide 7."

---

## Meta-note

The questions worth preparing for are the ones your specific clients have actually asked or hinted at — not the ones an outside observer would predict. When outside-observer predictions don't match your read, trust your read. You've been talking to these people.

The achievements above are real, dated, and validated. The deck's job is to present them clearly enough that the audience reaches the conclusion you want them to reach — not to teach them what an Intelligibility Score is.
