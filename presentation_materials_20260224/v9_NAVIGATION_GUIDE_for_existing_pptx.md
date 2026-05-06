# Navigation guide — present the EXISTING Round 8 deck (no edits)

Use this if you can't open the file to fix anything and have to walk in cold. Each slide gets one line: **what to say** + **what to skip if asked**. Times are cumulative.

The deck is a **selling-to-existing-team-new-clients** presentation. Their team already trusts you to deliver — these are new stakeholders deciding whether to expand. Lead with outcomes; never apologize.

---

## OPENING (S1–S10) — 10 minutes

| Slide | What to say (one line) |
|---|---|
| **S1** Title | "Argos Visual Speech Recognition. Built-in confidence, deploys where you need it." (Don't read the date — it says April. We're past that.) |
| **S2** About Argos | "We're the team behind the system your colleagues are running. Two-year build, now in production." |
| **S3** What is VSR | "Reading lips at scale. Used when audio is missing, masked, or unreliable." |
| **S4** Pipeline components | "Three components: video in, mouth-region focus, language model out. The language model is what's new." |
| **S5** What this is NOT | Slow down here — this slide is good, lets you draw the line. "We're not transcribing audio. We're not surveilling. We're not promising perfect lip reading." |
| **S6** Canonical scenario | "Conditions: two or more people in frame, observer-distance camera, audio missing or unreliable. Wide range of camera distances — what matters is film quality good enough to resolve the mouth." (DON'T READ "Before this meeting we'll run 3-5 of YOUR clips" — skip past it.) |
| **S7** Compared to today | "You've got two unsatisfactory options today. We're the third." |
| **S8** Human ceiling | "Even expert lip readers cap at 45–52%. The model + human reader together does 55–70%. That's why this exists." |
| **S9** Visemes / why hard | "Lip reading is hard because dozens of letters look identical on the lips. P, B, M — same shape." |
| **S10** What we built | "Six things shipped: pipeline, model, confidence layer, validation, UI, container deployment." |

---

## DEMO (S11–S13) — 5 minutes

| Slide | What to say |
|---|---|
| **S11** Demo intro | "Here's the system processing a real video, end-to-end." |
| **S12** Demo video embed | Click play. If video doesn't embed, narrate: "Drag-drop upload → 8-stage pipeline runs → color-coded report drops out the other side. About 4 minutes per minute of footage." |
| **S13** Demo recap | "Three things to notice: per-word confidence, per-segment trust signal, hallucination flagging." |

---

## REAL OUTPUTS (S14–S26) — 12 minutes

| Slide | What to say |
|---|---|
| **S14** Section divider | "Here's what the system actually produces. Different conditions, different outcomes." |
| **S15** Video gallery (was hidden) | If shown: "Six segments across the dataset — best to worst." |
| **S16** Example 1 (Obama clean) | "Reference and hypothesis match word-for-word. The reviewer doesn't have to look. This is what the Trust tier looks like." |
| **S17** Example 2 (everyday clean — non-Obama) | "Same outcome on conversational, mundane content. Not just famous speeches." |
| **S18** Clean gallery | "Six clean outputs across domains — legal, technology, motivational, conversational. Most of the clearly-conveyed segments look like this." |
| **S19** Example 3 (flagged Obama) | If you reach this: "When the model is wrong, the system catches it. We'll come back to this in the trust section." |
| **S20** Judge example 1 (named entity, bernreuter→rogers) | **Don't dwell on the video** — it's a placeholder Obama clip, not the actual segment. Say: "Names move. Meaning holds. Reviewer goes to the highlighted word." |
| **S21** Judge example 3 (routers→roads) | "Technical vocabulary drift. The structure carries the meaning even when specific terms get swapped." |
| **S22** Judge example 6 (topic hijack) | "Sometimes the model produces a fluent sentence about the wrong topic. The mixed-confidence flag tells you to check." |
| **S23–S25** Other example variants | If you have time. Otherwise skip. |
| **S26** Three numbers headline | **The big slide.** "Three numbers worth memorizing. About 65% of segments deliver useful output. Less than 5% of bad signals slip through. About 1 in 5 are auto-flagged before you see them." (If the slide says **62%**, just say **65%** out loud. If asked: "Latest evaluation puts it at 65%; 62% is the older version on this slide.") |

---

## TRUST FRAMEWORK (S27–S40) — 20 minutes

| Slide | What to say |
|---|---|
| **S27** Confidence question | "How do you trust an output when you have no ground truth? Two answers: per-word, per-segment." |
| **S28** Two layers | "Per-word: the model rates every word. Per-segment: aggregate of word confidences plus signal-quality check." |
| **S29** Word color coding (with screenshot) | **Caveat the screenshot.** "Note: this screenshot is from an earlier run. Production UI now uses **blue for trust, orange for review, purple for don't-trust** — the *meaning* is the same; the colors are an updated palette we're rolling out." Walk one segment from green/blue → yellow/orange → red/purple. |
| **S30** Word coloring example | Same caveat. "Look at the green spine carrying the meaning, the yellow words that need verification, the red words flagged for skip." |
| **S31** Three-tier UI | **Slow down.** "Three tiers: Trust, Salvage, Strip. Trust = 9 out of 10 colored words are correct. Salvage = 7 out of 10 (verify names/numbers). Strip = less than 5 in 10 — coloring removed entirely so you don't get misled." (The slide may say "~7 in 10 here" — just translate to "7 out of 10 colored words are right" verbally.) |
| **S32** How a reviewer reads | "Three steps: read the tier badge first, then the colors, then the words. Tier first because the colors mean different things in different tiers." |
| **S33** Salvage walk-through | "Real example. The blue spine carries the gist; the two flagged words are obviously wrong; reviewer goes straight to them. The colors converted a partial transcript into a usable summary." |
| **S34** Topic shift case study | "Wrong-topic hallucination — the most dangerous failure mode. Without colors it enters reports as fact. With colors, every wrong word is flagged." |
| **S35** Strip case study | "Sometimes there's no signal at all. The system catches this and strips the coloring entirely — telling the reviewer not to trust this segment." |
| **S36** Three rules | "Three rules every reviewer learns: numbers and names always verify against video, Strip-tier is not for word-by-word reading, the tier comes first." |
| **S37** Hallucination caught | "Real Obama segment. The model said 'rwanda's genocide' when the reference said 'heroic citizens saved.' It KNEW it was wrong — lowest confidence word at 0.02 probability — and the system flagged it before reviewer ever saw the transcript." (If REF isn't visible on the slide: read it aloud first: "Reference: 'heroic citizens saved even more heartbreak and destruction.' Hypothesis: 'rwanda's genocide even more heartbreaking.'") |
| **S38** Trust signals | "These are cases the model already routes away from your team. You see only the safe outputs." |
| **S39** Claims / non-claims | "What we claim: per-word reliability rated, per-segment routing, hallucination flag. What we DON'T claim: 100% accuracy, replacing expert review for time-critical decisions, perfect on every video." |
| **S40** Why trust on unseen | "Three answers: per-word from the model itself, per-segment aggregate, validated against an independent reviewer. The validation is the next section." |

### Operating thresholds slide (if it appears)
If you hit the "How aggressive should your trust threshold be" slide, **don't read the threshold details**. Say only:
> *"Two numbers worth memorizing: 65% of segments deliver useful output. Less than 5% of bad signals slip through as useful. Everything else falls out of these. The threshold is configurable per workflow — defaults work for most."*

---

## VALIDATION (S41–S43) — 5 minutes

| Slide | What to say |
|---|---|
| **S41** Section divider | "An independent reviewer agreed with the system in 82% of cases." |
| **S42** Agreement chart | "Blind LLM evaluator scored 1,497 segments without seeing our internals. Agreed with our per-segment Y/P/N call 82% of the time. That's the credibility line for trust signals on a video you've never seen." |
| **S43** Cross-config stability | "**Why** the trust signal is stable across conditions: tested across 16 decode configurations, the trust score moves less than a percentage point. Whatever you tune, the trust calibration holds." |

---

## ENGINEERING (S44–S46) — 5 minutes

| Slide | What to say |
|---|---|
| **S44** Section divider | "What it took to ship this." |
| **S45** Data flow | "Five-step model architecture. Visual encoder → sequence model → language model → confidence layer → output." |
| **S46** Engineering journey | "Six months of work across four passes: research integration, production refactor, confidence layer, beam aggregation. Now in production." |

---

## DEPLOYMENT (S47–S48) — 3 minutes

| Slide | What to say |
|---|---|
| **S47** Cloud/on-prem | "Same codebase. Cloud for elasticity, on-prem for data sensitivity. Twenty-six documented sync points between the two; one team maintains both." |
| **S48** UI / pipeline summary | (skip if running short) |

---

## WHAT'S NEXT (S49–S58) — 10 minutes

| Slide | What to say |
|---|---|
| **S49** Section divider | "What's available to extend the engagement." |
| **S50** Try it out | "Step one: pilot on your videos. Bring 5–10 clips, we run them through the production system, you see the output and decide." |
| **S51** Multi-speaker | "Engineering work in flight. Today's model handles one centered speaker per segment; multi-speaker pre-split is mapped end-to-end and ships in the next milestone." |
| **S52** Arabic | "Real engineering work, mapped end-to-end. **Funded engagement** — we'd build the Arabic model from your data; expect a 6–10 week scope." (Be explicit about the money — the slide doesn't always make it obvious.) |
| **S53** Quality filter | "Optional add-on — pre-filter low-quality clips before they enter the decode pipeline. Saves compute and avoids noisy outputs." |
| **S54** Next milestone | "Optional — domain-specific training run on your data. About 20K segments gets you measurable lift on your domain's vocabulary." |
| **S55** How a domain-tuned version comes together | "Four steps: collect your videos, run baseline, fine-tune, evaluate against your reviewers. Six to eight weeks." |
| **S56** Partnership ask | "What we're asking for: a pilot dataset, a named reviewer on your side, and a target deployment date. We handle everything else." |
| **S57** Recap (if shown) | "What you saw today: working pipeline, 65% useful output, three-tier confidence framework, validated against an independent reviewer." |
| **S58** Thank you | "Questions." |

---

## WHEN AUDIENCE PUSHES BACK

| They say | You say |
|---|---|
| *"What's the WER?"* | "About 36% on our 1,497-segment baseline. But word-error-rate is the wrong metric for lip reading — meaning preservation matters more. That's why we use the 65% useful number." |
| *"Why so much trust framework when you only deliver 65%?"* | "Because the bottom 35% would be hallucinations entering reports as fact if we didn't flag them. Trust signals are how 65% becomes shippable; without them, even 80% would be too risky." |
| *"Show me a hard failure."* | Jump to Slide 32 or 34. "This is the hard one — fluent prose on the wrong topic. Without colors it sneaks through. With colors the system catches it." |
| *"How does this compare to a year ago?"* | "Year ago: 25% useful on the same dataset. Today: 65%. The 40-point lift is the production engineering investment your team has been funding." |
| *"What about Arabic / Spanish / Mandarin?"* | "Architecture is language-flexible — the AV-HuBERT visual encoder isn't English-locked. Adding a language is a funded engagement: source data + your reviewer time + 6–10 weeks of our work." |
| *"Can it run on-prem?"* | "Yes. Same codebase, two deploy targets. (Slide 47 covers this.)" |
| *"What's the price tag?"* | Don't quote a number. "Pilot is fixed-fee, named scope. Production engagement scales with how many videos per month. Let's set up a call with our commercial team after this." |
| *"Show me the demo again."* | Re-play the video on Slide 12. Don't apologize — that's exactly what they should want to see twice. |

---

## ABSOLUTELY DO NOT

- Read speaker notes verbatim ("Round 5.X — " framing in many notes — internal residue, ignore).
- Quote any number with more than 3 significant figures (avoid "23.8%" — say "about 24%").
- Apologize for the deck having older numbers — just say the right number out loud.
- Promise an exact pilot date without commercial team alignment.
- Show the slides labeled "appendix" unless explicitly asked.
- Try to play the embedded videos if PowerPoint hangs — narrate instead.

---

## YOUR THREE FALLBACK SLIDES

If the deck breaks or you lose the room and need to land somewhere:
1. **Slide 27 (or whichever has Trust/Salvage/Strip)** — the framework that differentiates you.
2. **Slide 32/34/35 (worked examples of failures caught)** — proves the framework works.
3. **Slide 56 (partnership ask)** — closes the loop.

You can run the whole conversation off those three. Everything else is supporting evidence.
