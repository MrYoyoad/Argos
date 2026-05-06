# Manual fix guide — Round 8 PPTX (no rebuild required)

If you need to use **`Argos_VSP_Client_Round8_May2026.pptx`** in the meeting (not the new Round 8.9), open it in PowerPoint and apply these fixes by hand. Order is by impact — do the top items first if time is tight. Estimated total: **20–30 minutes**.

All edits are clicks-and-types in PowerPoint. No video swaps, no script runs.

---

## CRITICAL — these reads will get noticed

### 1. Slide 1 (cover) — change "April 2026" → "May 2026"
- Click the date line at the bottom. Change `April` to `May`. Done.

### 2. Slide 26 (headline numbers, "Three numbers, in plain English") — 62% → 65%
- In Round 8 the big headline is **62% useful**. Update both the headline card and any speaker note to **65% useful**.
- Speak it as: *"65% of segments deliver useful output. Less than 5% of bad signals slip through."*
- If asked: 71% is the theoretical ceiling with full beam aggregation; 65% is the baseline you can quote without caveats.

### 3. Slide 27 (three-tier UI) — fix tier-card numbers
The cards show cryptic phrasing like *"Green right ~7 in 10 here —"*. Replace each with the plain version:
- TRUST card → **"9 out of 10 green words are correct"** (or BLUE if your palette is migrated)
- SALVAGE card → **"7 out of 10 green words are correct — verify names, numbers, dates against video"**
- STRIP card → **"Less than 5 in 10 would be right — coloring would mislead, so we hide it"**

### 4. Slide 30 (case_topic_shift, gardening → nuclear) — REF/HYP truncated
The hypothesis row gets clipped at the bottom of the slide. Two clicks:
- Click on the **HYPOTHESIS** text box → drag the bottom handle down by 0.5".
- Select all the HYP runs → reduce font from 13pt → 11pt.
- The full text "we're going to look at now is what happens if we start playing the concept of warheads or nuclear deterrence and a little bit of escalation and cuban missile crisis" should now fit.

### 5. Slide 32 (Example 11 — hallucination caught) — no REF visible
This slide shows the colored hallucination but the audience can't see what was actually said. Add the REF inline:
- In the LEFT column, above "DECODED HYPOTHESIS", insert a new text block:
  - Label: **WHAT THE SPEAKER ACTUALLY SAID** (11pt bold, gray)
  - Body (italic, gray, 13pt): *"heroic citizens saved even more heartbreak and destruction and yet we know that the worst images are those that were unseen to the world the empty seat at the dinner table"*
- Move the existing colored hypothesis down by ~1.5" to make room.
- Optionally relabel "DECODED HYPOTHESIS" → "WHAT THE MODEL DECODED".

### 6. Slide 35 (trust_operating_points) — REWRITE the headline
This slide currently sells the "≥30% green words" threshold. Replace with the simpler framing:
- Headline card: **"65% of segments deliver useful output"** (large, blue/teal)
- Subtitle below: **"Less than 5% of bad signals slip through as useful."**
- Bullet under: *"Two numbers worth memorizing. Everything else falls out of these."*
- Move the "≥30% trust threshold" detail into a smaller card OR speaker notes.

### 7. Slide 39 (cross-config stability) — clarify what it's saying
Title currently reads "The trust signal stays stable" — meaningless without context. Change to:
- **"Why the trust signal is stable across conditions"**
- Add a one-line subtitle: *"Tested across 16 decode configurations. Trust score moves less than a percentage point."*

### 8. Slide 7 ("What the system is built for") — DISTANCE card
Old wording mentions "6–15 m from the speaker." Replace card body with:
- **"Wide range of camera distances — close-up to far observer — as long as film quality is good enough to resolve the mouth region."**

### 9. Slide 7 — REMOVE the "Before this meeting" sentence
Same slide, bottom area. Two boxes need deleting:
- The big highlighted sentence: *"Before this meeting, we'll run 3-5 of YOUR clips through the system. The act of doing it is the commitment."*
- The follow-up: *"Bring a clip when you can — even a short one tells us what we're really up against on your data."*
- Both go. Audience already knows you'll run a pilot — don't make it a stunt.

---

## SHOULD-DO if time allows

### 10. Slide 13 ("Live UI Demo") — hide the presenter instructions
The slide currently shows: *"If video does not embed before the meeting, narrate the demo: drag-drop upload → 8-stage pipeline → color-coded report."* — this is presenter-template text that the audience shouldn't see.
- Click that text block → cut it (Ctrl+X).
- Paste into speaker notes.

### 11. Slide 14 ("Example 1 — Clean speech, perfect transcription") — title rename for consistency
Round 8.9 unified all example titles as `Example N — Tier: Headline`. If you want consistency:
- Slide 14: → **"Example 1 — Trust: clean speech (Obama)"**
- Slide 17: → **"Example 2 — Salvage: partial recovery (Obama)"** (currently "Example 2 — Partial recovery")
- Slide 20: → **"Example 5 — Salvage: named-entity swap"** (currently "Named Entity Swap")
- Slide 22: → **"Example 6 — Salvage: technical-vocabulary drift"** (currently "Technical Vocabulary Drift")
- Slide 25: → **"Example 7 — Strip-flag: topic hijack"** (currently "Topic Hijack — the dangerous mode")
- (and so on for the other example slides)

This isn't critical — but if any audience member glances at the thumbnail panel, the renumbering tells them where they are.

### 12. Slide 47 ("Claims" / Round 8 title) — drop the philosophical row
Currently has 5 ✓/✗ pairs. Drop the row about "Confidence equals factual truth" — it's the most abstract and audience drifts. Keeps the slide to 4 pairs at a comfortable read.

### 13. Slide 62 (Arabic) — make the money ask explicit
- Title: change to **"Arabic — three engineering phases (funded engagement)"**
- Any "On request" card → **"Available — funded engagement"**
- This is the real ask; don't bury it.

---

## OPTIONAL — palette migration (only if you have 30+ minutes)

The new production UI uses **blue / orange / purple** (Trust / Salvage / Strip) instead of green / yellow / red. The Round 8 PPTX still uses the old palette in 14 slides. Migrating by hand is tedious but possible:

For each example slide (14, 15, 17, 18, 19, 20, 25, 28, 29, 30, 32, 38) and the legend on each:
- Find every word/text colored green → recolor to blue (#4F8FF7)
- Find every word/text colored yellow → recolor to orange (#FF9800 — already in palette)
- Find every word/text colored red/coral → recolor to purple (#B066D9)
- Update the legend strip at the bottom from `GREEN: confident   YELLOW: review   RED: likely error` → `BLUE: trust   ORANGE: review   PURPLE: avoid   ·   numbers cap at orange`

**Skip this if you're under time pressure.** The narrative still works with the old palette as long as you say "blue / orange / purple" verbally and explain that the on-screen colors will update post-meeting.

---

## What you can SAFELY skip

- The cross-reference fixes (speaker notes pointing to wrong slide numbers) — those are notes, audience won't see them.
- The "Round 5.X — " changelog-meta in speaker notes — same reason.
- Hidden appendix slides — they don't show during the live meeting.
- The QA cheat sheet — it's broken vs Round 8.8 numbering anyway. Use this guide instead.

---

## After all the fixes

Run a quick sanity check:
1. Press F5 to start slideshow from slide 1.
2. Click through to slide 1 → check date says May.
3. Slide 26 → check headline says 65%, not 62%.
4. Slide 32 → check the REF text appears above the colored hallucination.
5. Slide 35 → check headline reads "65% of segments deliver useful output."
6. Esc, save, done.

Total time budget: 20 minutes for items 1–9; another 10 for 10–13.
