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

Slide 44 has both these beats as the bottom pills ("MEANINGFUL TODAY" / "GROWS IN YOUR HANDS"). Refer them there.

---

## "Is there more you can do to improve accuracy beyond the current numbers?"

**"Yes — beam aggregation is the next gain we're shipping. Beam search internally produces 20 candidate hypotheses per segment, and currently only the top-1 is kept. Voting across the 20 candidates, weighted by per-word confidence, recovers errors top-1 misses. On a 107-segment evaluation, this dropped WER from 59 percent to 57 percent — about 3.6 percent relative — and lifted intelligibility scores too. Code shipped May 1; it's gated behind an environment variable while we run the full 1,497-segment evaluation. The honest caveat is that the agreement scores from voting need a one-time temperature calibration to act as proper confidence numbers — that experiment ran cleanly and the calibrated voting method has the best calibration error of any method we've measured."**

If pressed: "After full evaluation, we'd ship the voting method as the default decoder for transcript output, while keeping the simpler top-1 confidence path for the trust signal. Both are real, both are validated, both are in code today."

Sources for follow-up: `docs/beam-search/n_best_implementation.md`, `tuning_results/exp_nbest_validation/`. Don't volunteer this answer — it's a pull-question response only.

---

## "How reliable is the green coloring? Is green always correct?"

**"No. Green is high-confidence, not guaranteed correct. We measured this across 23,261 words: green is 92.8% reliable in high-quality segments and 21.8% reliable in low-quality ones. That range is exactly why our UI runs a three-tier policy. Above segment confidence 0.82, we show full coloring — green is ≥85% reliable there. Between 0.65 and 0.82, we show coloring with an amber 'verify names and numbers' banner. Below 0.65, we strip the coloring entirely — keeping it would mislead the reviewer."**

Slide 32 lands this. Refer them there if asked. The honest framing: *"the UI removes coloring where it would lie."* If pressed for the math: 9.4% of all green words are wrong; 605 of those 2,192 wrong-greens sit in segments below 0.65 — which is exactly the band we now strip.

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

---

# Per-slide talking points

The lines to land when each slide is up. Slides not listed don't have a specific cue — let them speak for themselves or transition through.

## Opening

### Slide 1 — Title
**Land:** *"Thanks for having us. We're going to walk through what this is, what it isn't, and where it goes from here together. Two hours, with a pause around the halfway mark."*

### Slide 2 — About Argos
**Land:** *"We build production-grade visual speech recognition. Not research code — a deployable pipeline."*

## Framing the problem (slides 3–7)

### Slide 4 — What this is NOT
**Land:** *"Three things to clear up first. This is NOT audio transcription. NOT closed captioning. NOT face recognition. We do one specific thing: visual speech recognition, on cases where audio failed."*
**Note:** Land this firmly. Most audiences arrive with one of those three mental models and you need to evict it before slide 5 makes sense.

### Slide 5 — Canonical scenario
**Land:** *"Two friends in a coffee shop. Observer thirty feet away. iPhone footage. No usable audio. That's the problem we're solving — and it's your problem too."*

### Slide 6 — Compared to today (THE ANCHOR)
**Land:** *"Three rows on this slide. Expert human lip readers — 45 to 52 percent word accuracy, hours of work per video. Don't do it at all — zero, the information's lost. Argos plus a reviewer — 55 to 70 percent in minutes, with hallucinations flagged. That's the deal."*
**Note:** This is the most important slide in Act 1. Don't rush it. Pause after each row. Let the comparison register.

### Slide 7 — Human ceiling
**Land:** *"Why even experts cap at 45–52 percent? Half of English phonemes are visually invisible — 'p', 'b', 'm' look identical on the lips. There's a hard floor here, even for humans."*

## Why hard / basic idea (slides 8–9)

### Slide 8 — Visemes
**Land:** *"Pat, bat, mat. Try saying them in a mirror with no sound — they look the same. That's what the model is up against on every word."*

## What we built (slides 10–11)

### Slide 10 — What we built, concretely
**Land:** *"Six things we built. Pipeline. Web UI. Model. Confidence layer. Evaluation. Integration. We deploy this on your infrastructure end-to-end."*
**Note:** Don't dwell on each. Read across, move on.

### Slide 11 — Multi-speaker today vs path
**Land:** *"The honest gap. Today's model assumes one centered face. Two-person footage needs entity-split preprocessing — track each face, generate separate mouth crops, decode each speaker separately. That's engineering work, about three weeks to a working ablation on your data. Not research, not vague."*
**Note:** This slide is for the audience that came specifically about two-person footage. Land it crisply — concrete plan, concrete timeline.

## Demo (slides 12–14)

### Slide 13 — Live UI demo
**Land:** *"Watch this. Drag in a video, walk away, come back to a confidence-scored report."*
**Note:** Play 90 seconds, max 2 minutes. Don't narrate everything; let the colors speak. Pause briefly on a flagged segment so the audience sees the trust signal in action.

## Real outputs (slides 15–26)

### Slide 16 — Video gallery
**Land:** *"Six real videos. Three best-case, three failure modes. The point isn't to convince you with one demo — it's to show you the range. Click any tile."*
**Note:** Pre-pick which tile to click. Recommend the perfect one (sets the bar) then jump to the hallucination one (shows the system catches the bad ones). Don't play all six.

### Slides 17, 19, 20 — Obama trio (perfect / partial / flagged)
**Land:** *"Same speaker, same speech, three different outputs. Clean — green confidence, the reviewer doesn't have to look. Partial — model knows where it slipped, yellow on the substitutions. Flagged — model fabricated 'Rwanda's genocide' and the system caught it. That's the spread."*
**Note:** Each slide has the actual lip-crop video on the right; click to play in PowerPoint if asked.

## The headline (slide 27)

### Slide 27 — Three numbers
**Land:** *"Three numbers, in plain English. Sixty-two percent review-useful — six of every ten segments contain enough recoverable meaning to be useful for human review. Twenty-three percent clearly conveyed. One in five auto-flagged. These are on the full 1,497-segment baseline, unfiltered real-world video. Not curated."*
**Note:** This is your number-anchor for the meeting. Memorize the exact phrasing — "review-useful," "recoverable meaning useful for human review." Don't slip into "62% accurate."

## Trust section (slides 28–44) — the most important segment

### Slide 30 — Two layers of confidence
**Land:** *"Confidence is triage, not truth. Green doesn't mean correct — green means review faster. Red doesn't mean wrong — red means review first."*
**Note:** This is the cleanest credibility line in the deck. Say it slowly, and reinforce — the line is on screen.

### Slide 31 — Per-word color coding
**Land:** *"Every word the model outputs carries its own probability. Green, yellow, red. You see exactly where the model was unsure."*

### Slide 32 — Three-tier UI: Trust / Salvage / Strip (NEW Round 5.6)
**Land:** *"Green's reliability isn't uniform. We measured it across 23,261 words. In high-quality segments green is 93% correct; in low-quality ones it drops to 22%. So we built the UI around that finding. Above 0.82 segment confidence, full coloring — green is 85%+ reliable. Between 0.65 and 0.82, full coloring plus an amber 'verify names and numbers' banner. Below 0.65, we strip the coloring. Coloring would lie there. The UI itself enforces the asymmetric-cost policy: wrong-and-green is the only unrecoverable cell."*
**Note:** Don't read out every percentage. Land the structure (Trust/Salvage/Strip) and the principle (UI removes coloring where it would lie). The 1,497-segment distribution (22.7 / 35.7 / 36.9) is on the slide if a co-partner pulls on it.

### Slide 33 — How a reviewer actually reads the output (NEW Round 5.9)
**Land:** *"Three steps. Thirty seconds per segment. One: check the tier. Trust, Salvage, or Strip — that tells you how to read what's below. Two: read the colors. Blue means confident, orange means best guess, purple means uncertain. Three: override for numbers and names. Whenever a segment has a number, name, date, or amount, verify against the video — even when blue. The model's confidence on these isn't well-calibrated."*
**Note:** This is the operational instruction. Land it as practical, not theoretical. *"Reading the output well is using both signals — tier first, colors second."*

### Slide 34 — Worked example: how Salvage works in practice (NEW Round 5.9)
**Land:** *"Salvage tier. The reviewer sees this banner: 'verify names, numbers, critical details.' The blue spine — different approach… find a way… existing… enable them — carries the meaning. Two of the red words, design and roads, are wrong; the original was 'routers' and 'switches'. But a reviewer who treats red as 'discount' recovers a faithful gist: a new approach that uses existing components for research. The colors converted a 50%-WER segment into a usable summary. This is what 'review-useful' means in practice."*
**Note:** Don't dwell on the network-infrastructure topic — the topic is incidental. The point is the colors did the work. If asked WHY this looks good: 50% per-word WER, but the reviewer extracts a faithful gist anyway.

### Slide 35 — Three rules every reviewer learns (NEW Round 5.9)
**Land:** *"Three rules. Numbers and names always need the video — even when blue. Strip-tier segments aren't for word-by-word reading — use them as topic hints, not transcripts. And the tier comes first, before the colors — a blue word in a Strip segment is half as reliable as a blue word in a Trust segment. These ship with every pilot. Reviewers learn them in the first hour."*
**Note:** This signals the system has a real workflow, not just confidence theater. Co-partners will appreciate this slide in particular — it shows we've thought about how the output gets used, not just how it gets produced.

### Slides 36–38 — Hallucination case study (the centerpiece)
**Land on 36:** *"The dangerous failure mode. The model can produce confident, fluent text that's completely wrong."*
**Land on 37:** *"Real example. Reference says 'heroic citizens.' Model says 'Rwanda's genocide.' A wrong fluent transcript is worse than an empty one, because people may act on it."*
**Land on 38:** *"And the system caught it. Lowest-confidence word at probability 0.02. Length anomaly. Routed to review before a reviewer ever sees the line. Our value isn't that this never happens — it's that this is flagged."*
**Note:** This is the strongest credibility moment in the deck. Don't rush it. Use the full 90 seconds.

### Slide 45 — Hallucination flag (1 in 5)
**Land:** *"One in five segments is auto-flagged before it reaches you. The system finds the bad ones for you."*

### Slide 46 — What we claim / what we do not claim (NEW Round 5.5)
**Land:** *"Where the line is. So you know what you're buying. Six things we claim. Six things we don't. Closing line: Not blind automation. Reviewable visual-speech intelligence with uncertainty attached."*
**Note:** Read down both columns side by side, two beats per row. This is the credibility-anchor slide — don't rush it.

### Slide 47 — Why trust it on a video you've never seen
**Land:** *"You don't have ground truth on a fresh video. So how can you trust this? Four runtime signals — per word, per segment, hallucination flag, config stability. Calibration is anchored to expert review today. It grows tighter for your domain as your reviewers verify segments."*
**Note:** The two pills at the bottom — "MEANINGFUL TODAY" and "GROWS IN YOUR HANDS" — are the message. If asked about the validation method, refer to slide 51.

## Validation (slides 45–48)

### Slide 51 — Agreement chart
**Land:** *"An independent blind evaluator agreed with our scores in eighty-two percent of cases. Across all 1,497 segments. Blind to our reasoning."*
**Note:** If asked "was that human?" — answer the Q&A line above. Do NOT say "expert reviewer." Say "blind evaluator" or "blind evaluation pass."

### Slide 52 — Cross-config stability
**Land:** *"Sixteen different decode configurations on the same data. The trust signal moves less than a percentage point. It's a property of the model, not the run."*

## Engineering (slides 54–57)

### Slide 54 — The full pipeline
**Land:** *"Eight automated stages. Drop in a video, walk away."*

### Slide 56 — What it actually took
**Land:** *"Four months, four passes. Integration of three research repos. Production refactor — 823-line script into 11 modules, 37 tests. Confidence layer. Dual-environment shipping. Real engineering, real shipped code."*

### Slide 57 — Deployment options
**Land:** *"Cloud or on-prem. We deploy and integrate. You're not buying an API call — you're buying a working pipeline that runs in your environment."*

## What's next (slides 58–63)

### Slide 59 — Quality pre-filter
**Land:** *"A credible system must know when NOT to decode. Three frame-level checks before the model runs. Out of a hundred uploaded clips, seventy-five reach the model."*

### Slide 61 — Beyond English — Arabic
**Land:** *"Same architecture, same pipeline, different LLM and different visual model. The path is mapped. Specifics in follow-up."*
**Note:** Three questions to ASK on this slide (write them on a sticky note inside your laptop lid):
- "Which Arabic? MSA, Levantine, Egyptian, or Gulf?"
- "What does your canonical video actually look like?"
- "What does 'good enough' look like for your workflow?"

### Slide 62 — What the next milestone changes (Round 5.8)
**Land:** *"Today works — the 62% review-useful you saw is real. Two things make it noticeably better. One: a smarter model. The brain that turns lip-reading signals into text is a few years old; we swap in a newer one. Same plumbing, better text out the other end — especially stronger on names and uncommon words. Two: train it on your content. Right now the model has only seen public video — none of it looks like yours. Train on your footage and it gets meaningfully better at the work you actually do. We've already tested smaller versions of both. Both work. The data path matters most. Tomorrow's number is bigger than today's. The gap is the partnership."*
**Note:** Plain English throughout — no parameter counts, no "empirical floor," no "drop-in upgrade." Don't put a specific lift number anywhere. If a co-partner asks WHICH model specifically: speaker notes name Llama 3.1 8B / 3.3 70B / current SOTA — say it in voice if asked, never on the slide. Tie to slide 63: *this slide says WHAT improves; next slide says HOW the partnership runs.*

### Slide 63 — Partnership ask
**Land:** *"Today's model is trained on a small slice of public data. Going from prototype to production on your content — that's a partnership. Your data, our pipeline, a shared training run on your domain. Specifics in follow-up — no dollar amounts on the slide on purpose."*

## Close (slides 64–67)

### Slide 64 — Recap
**Land:** *"Three things we came to show you. It works. You can trust it. There's a clear path forward together."*

### Slide 65 — We deploy this on your infrastructure
**Land:** *"On-premise install, integration with your existing systems, training and handoff. End-to-end."*

### Slide 66 — Next steps
**Land:** *"A pilot looks like this — three to five canonical clips from your domain, two weeks, end-to-end run, your reviewer evaluates whether the output supports your workflow. No infrastructure ask up front."*
**Note:** This slide has placeholder text you customize per client before the meeting. Make sure dataset / integration scope / timeline / success criteria are all filled in.

### Slide 67 — Thank you
**Land:** *"Questions."*
**Note:** That's it. Don't keep talking. Wait.

---

# The closing line

Memorize this. If nothing else lands all meeting, land this:

> **"We are not asking you to trust the model. We give your reviewers the model's output, its uncertainty, its failure flags, and the evidence needed to decide what deserves human attention."**
