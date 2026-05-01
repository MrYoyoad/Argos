# Q&A Cheat Sheet — Argos VSP Client Meeting

**Phone-readable. Memorize the bold lines. Don't read these out — internalize them.**

These are the answers to the questions the audience is most likely to ask. They're calibrated for an audience of (a) existing client team incl. high-leverage stealth buyer, (b) cold prospect, (c) technical co-partners.

The single sentence that ties the whole deck together — say this if nothing else lands:

> **"We are not asking you to trust the model. We give your reviewers the model's output, its uncertainty, its failure flags, and the evidence needed to decide what deserves human attention."**

---

## "How accurate is it?"

**"It depends heavily on clip quality: face angle, mouth visibility, lighting, distance, and whether the speaker is cleanly cropped. On our 1,497-segment real-world baseline, about 62% of segments contained recoverable meaning useful for human review, and about 23% were clearly conveyed. I would not translate that into a blanket accuracy promise for your footage before we run your clips."**

Why this works: it answers the question, names the dependence on conditions, gives the real numbers, refuses to overpromise. Don't say "62% accurate" — say "62% review-useful."

---

## "Can we trust the transcript?"

**"Not blindly. That is the point of the system. The transcript is not delivered as a flat truth claim — it comes with word-level and segment-level confidence, plus hallucination flags. The safe workflow is: trust high-confidence output faster, review yellow/red spans, exclude low-confidence segments from automatic conclusions."**

The line to land: **"Confidence is triage, not truth."** It's on slide 30. Refer back to it when this question comes up.

---

## "What happens when it hallucinates?"

**"It can hallucinate. Visual speech is ambiguous and language decoders sometimes produce fluent wrong text. We treat that as a core failure mode, not an edge case. We use token confidence and length anomalies to flag suspicious segments, so the dangerous case becomes visible instead of silently entering the report."**

The deck has a 3-slide trio on this: the problem, the real Obama "Rwanda's genocide" example, and the system catching it. Refer them to slides 32-34.

The killer line: **"A wrong fluent transcript is worse than an empty one. Our value is not that failure never happens — it's that failure is surfaced."**

---

## "Was the 'independent reviewer' a human?"

This is the question most likely to embarrass us if we're not ready.

**"No. For the full 1,497-segment calibration, we used a blind frontier-LLM evaluator with no access to our scores or reasoning. That gives us a strong development calibration signal at scale. For your deployment, the right next step is human validation on your own pilot clips, because your camera angles, distances, language, and domain vocabulary are what matter."**

Why this works: honest, doesn't apologize, explains *why* we used the method (scale), and pivots to the right next step. Do not call it "expert reviewer" if asked directly — say "blind LLM evaluator."

---

## "Can it handle two people talking?"

**"The current model works best with one centered speaker crop. For two-person footage, the next engineering step is speaker-specific cropping: track each face, generate separate mouth crops, and run each speaker independently. That is concrete preprocessing work, not a vague research hope."**

This is in the deck on slide 11 (multi-speaker today vs path). Refer them there.

---

## "Could this be used as evidence?"

**"Only with human review and confidence metadata attached. I would not present raw model output as standalone evidence. The responsible use is as an evidence-discovery and review-acceleration tool: it points reviewers to likely speech content and tells them where uncertainty is high."**

This is the answer that makes you sound serious and trustworthy. The high-leverage stealth buyer in the room (existing client's secondary team lead) is listening for this kind of restraint.

---

## "How do you know the examples aren't cherry-picked?"

**"The examples are curated for teaching — best-case to worst-case spread, so you see the range. The headline numbers (62% / 23% / 1 in 5) come from the full 1,497-segment baseline, not from selected clips. The footer on every gallery slide says exactly that."**

If pressed: "We can run your specific clips through the same pipeline before the next meeting. That's how this conversation should continue."

---

## "Why should we trust the confidence calibration?"

**"Two reasons. One: it's anchored to an independent blind evaluator (82% agreement on our 1,497 calibration set), so the threshold isn't arbitrary. Two: as your reviewers verify segments on your footage, those verdicts extend the calibration to your domain. The signal tightens around your content as you use it."**

Slide 43 has both these beats as the bottom pills ("MEANINGFUL TODAY" / "GROWS IN YOUR HANDS"). Refer them there.

---

## "What's actually different about your system vs other lip-reading work?"

**"Three things. One — we built the pipeline end-to-end on real-world video, not just LRS3 benchmarks. Two — we surface uncertainty at every level (per-word, per-segment, hallucination flag) so reviewers know where to spend attention. Three — we ship deployable infrastructure, not a research codebase. Cloud or on-prem, your choice. We integrate, not API-call."**

Slide 10 ("What we built — concretely") covers this with six deliverables. Slide 51 ("How It Works: Data Flow") and slide 52 ("Engineering journey") back it up technically.

---

## "What does the baseline look like as it gets harder / easier?"

**"The 1,497 segments are deliberately unfiltered real-world YouTube footage — varied lighting, head angles, multi-speaker scenes, no curation. Harder than most production data. On cleaner footage (frontal angle, single speaker, good lighting) the system performs noticeably better. On harder footage (profile angles, occluded mouth, noisy crowds) it fails more, but the trust signals correctly flag the failures."**

This is honest and defensible. Don't promise specific lifts on cleaner data — frame it as "noticeably better, exact gain depends on how clean."

---

## "What would a pilot look like?"

**"Three to five canonical clips from your domain — two-person conversational footage, observer-distance framing, however long you typically work with. We run them through the full pipeline, deliver the confidence-scored report, and your reviewer evaluates whether the output supports your workflow. End of pilot, we know whether this is production-grade for you. Two weeks, no infrastructure ask up front."**

This is the close. Use it when the conversation moves toward "what's next."

---

## Things NOT to say

- **"62% accurate"** — say "62% review-useful" or "62% contained recoverable meaning"
- **"Expert reviewer"** — say "independent blind evaluator"
- **"Near-zero hallucination risk"** — say "hallucinations are flagged before review" or "designed to surface, not hide, hallucinations"
- **"The system knows when it's right"** — say "the system tells you where to look first"
- **"It works on any video"** — name the conditions (mouth visible, frontal-ish, lighting OK)
- **"This replaces human review"** — say "this routes human review to the right places"
- **"AI validating AI"** if the audience asks about the validation method — pivot to "blind LLM at scale, human validation on your domain next"
- **"State of the art"** — overclaiming, sets you up for benchmarks fight

---

## If the technical co-partners want to go deep

The hidden appendix slides cover IS internals, cross-config stability, decode-parameter sensitivity, fine-tuning experiments. If the meeting goes there, jump to those slides. If they ask about runtime confidence: **"At runtime we aggregate per-token softmax probabilities and compute a length-anomaly check. The IS score is our development calibration metric, not a runtime signal — IS requires reference text, which we don't have on a fresh video."**

The Round 5.3 honesty fix on slides 30 and 43 is critical here. Don't claim IS runs at runtime.

---

## The hardest question and the hardest answer

If asked: **"Could a system like this be misused?"**

Answer with restraint:

**"Yes. That's why we ship it as a reviewable evidence stream, not as autonomous truth. The output requires human review by design. We won't deploy it in a workflow that doesn't include human verification — that's a deal-breaker for us, not a feature request from clients."**

This answer signals seriousness. Don't sidestep — say it directly. The audience is asking partly because they're testing your judgment.
