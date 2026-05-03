# Client Deck — Pre-Meeting Checklist

**Deck:** `Argos_VSP_Client_Round8_May2026.pptx` (70 slides total, 56 visible during presentation; ~32 slides with bullet-by-bullet click-reveal animations)
**Q&A cheat sheet:** [QA_CHEAT_SHEET.md](QA_CHEAT_SHEET.md)
**Detailed instructions:** [docs/guides/client-deck-powerpoint-checklist.md](../docs/guides/client-deck-powerpoint-checklist.md)
**OOXML compat scan:** [PP_COMPAT_REPORT.txt](PP_COMPAT_REPORT.txt) in this folder
**Changelog:** [DECK_CHANGELOG.md](DECK_CHANGELOG.md)

Phone-friendly version. Two passes: at home/office before you leave, then again at the venue right before the meeting starts.

---

## ✅ CHECK BEFORE LEAVING (allow 30 min)

These need access to your dev machine and the deck source, so do them before walking out the door.

### Embed the demo video (slide 13 post Round 5.5)
- [ ] Recorded the UI walkthrough following `docs/guides/client-demo-recording-guide.md`
- [ ] Saved as MP4 / **H.264** codec (the OOXML compat scan flags HEVC — re-encode if needed)
- [ ] In PowerPoint, slide 13 → Insert → Video → **Video on My PC** (NOT "Online Video")
- [ ] Resized to fill the placeholder card
- [ ] Playback tab → confirmed Start setting (Automatically vs On Click) you want
- [ ] Pressed F5 → tested the video plays from inside presentation mode
- [ ] Heard audio through laptop speakers (not just headphones)

### Customize the next-steps slide (slide 67 post Round 5.10)
- [ ] Pilot dataset card — replaced "Size, content type, sample source" with client-specific text
- [ ] Integration scope card — replaced with actual systems to wire into
- [ ] Timeline card — replaced with realistic weeks/dates
- [ ] Success criteria card — replaced with what "good" looks like for this client

### Title slide (slide 1)
- [ ] Date is current (currently April 2026)
- [ ] Optional: client name added on a line above "Yoad Oxman · Argos / The Orchard"

### Click-through dry run
- [ ] Opened the deck in **real PowerPoint** (not LibreOffice / web preview)
- [ ] Stepped through all 68 slides at full screen (F5)
- [ ] Slides where I want extra eyes (Round 5.10 indices):
  - [ ] **Slide 13** — Live UI demo placeholder — your video embedded?
  - [ ] **Slide 11** — multi-speaker (today vs path) — both columns balanced?
  - [ ] **Slide 8** — visemes (pat/bat/mat) — three columns balanced?
  - [ ] **Slides 17, 19** — Obama examples (perfect / partial) — clickable lip-crop video on each, REF/HYP green/yellow/red readable? (Round 5.10 dropped the "flagged" slide; the Obama-flagged segment 5 lives on slide 38 in the hallucination trio.)
  - [ ] **Slide 18** — clean-outputs gallery (6 video tiles + label/quote) — videos play?
  - [ ] **Slides 20-25** — six judge examples with verdict tags — verdict line clear?
  - [ ] **Slide 26** (was 27) — Three numbers (62% review-useful / 23% / 1 in 5) — language reads cleanly?
  - [ ] **Slide 29** (was 30) — "Confidence is triage, not truth" visible at top?
  - [ ] **Slide 30** (was 31) — per-word color coding screenshot — real B3 confidence — crisp at full screen?
  - [ ] **Slide 31** (was 32) — three-tier UI (Trust / Salvage / Strip) — three cards balanced, percentages 22.7 / 35.7 / 36.9 visible?
  - [ ] **Slide 32** (was 33) — Round 5.9: "How a reviewer actually reads the output" — three numbered cards (1/2/3) readable?
  - [ ] **Slide 33** (was 34) — Round 5.9: Salvage worked example (networking) — REF/HYP color-coded, READER'S VIEW pill readable?
  - [ ] **Slide 34** — NEW Round 5.10: topic-shift hallucination (gardening → nuclear weapons) — video poster on right, READER'S VIEW pill readable?
  - [ ] **Slide 35** — NEW Round 5.10: Strip catches fluent fabrication — video poster + per-word confidence numbers readable?
  - [ ] **Slide 36** (was 35) — Round 5.9: "Three rules every reviewer learns" — three coral/gold/teal cards balanced; new "1 million CFUs" example in first card readable?
  - [ ] **Slide 39** (was 39) — IS confidence-gate plot — annotation legible?
  - [ ] **Slide 47** (was 46) — claims/non-claims — both columns + bottom anchor readable?
  - [ ] **Slide 48** (was 47) — trust without ground truth — four cards + meaningful/grows pills readable?
  - [ ] **Slide 55** (was 54) — 8-stage operational pipeline diagram — color-coded stages crisp?
  - [ ] **Slide 57** (was 56) — engineering journey (4 milestones) — M1-M4 cards balanced?
  - [ ] **Slide 58** (was 57) — Cloud / On-premise cards — borders crisp?
  - [ ] **Slide 60** (was 59) — quality-filter funnel + "credible system must know when NOT to decode" tagline visible?
  - [ ] **Slide 63** (was 62) — "What the next milestone changes" — Smarter Model / Trained On Your Content cards readable?
  - [ ] **Slide 64** (was 63) — partnership ask — bridge pill readable?

### Timing
- [ ] Out-loud read-through with stopwatch
- [ ] Total time noted: ___ min (target: 30–45 min for the deep-dive version)
- [ ] Any single slide >90 sec? → mark for trimming or splitting

### Travel
- [ ] Deck saved to a USB stick as backup (in case the client laptop has no email/network)
- [ ] **Phone has this checklist open** so you can re-check at the venue

---

## 🟡 PRE-MEETING PREP (4 ITEMS — DO 1 WEEK OUT)

These are not last-minute checks. They need lead time — a system run, a 5-min call, a speaker-notes edit. Block 1-2 hours about a week before the meeting and knock them out together. Sourced from [`docs/CLIENT_MEETING_FRAMING_v2.md`](../docs/CLIENT_MEETING_FRAMING_v2.md) § "Things to do before the meeting".

### Run client-shaped segments through the system
- [ ] Pick 3-5 video clips that match the client's actual use case: two-person conversational footage, observer-distance framing (not selfie / not studio), iPhone-quality, 20s-60s each
- [ ] Run them through the full pipeline (`run_flat_english_pipeline.sh`)
- [ ] Generate the report HTML — even mixed results are fine, the *act of having done it* is what signals seriousness
- [ ] Screenshot the best result and the worst result
- [ ] Either attach to the deck (replace one of the gallery videos) OR have the screenshots open in a tab to pull up if asked
- [ ] Note: "we ran your scenario through the day before our meeting" is a strong opener if it lands naturally

### Coordinate with the co-partners (5-min call)
- [ ] Schedule a quick call with the 2 technical co-partners attending
- [ ] Pick ONE of these modes — don't leave it ambiguous:
  - [ ] **Solo-drive with chime-ins** — you present, they answer questions in their domain
  - [ ] **Solo-drive with co-partners on 1-2 slides** — they own a specific section (e.g. infra, integration)
  - [ ] **Joint walkthrough** — you trade off section by section
- [ ] Confirm the choice in writing (Slack / email) so nobody freelances mid-meeting

### Cheat sheet for hidden appendix slides
- [ ] Open the .pptx and edit the speaker notes of the **last visible slide** (slide 45 or 46 depending on build)
- [ ] Add a one-line index — example:
  - "If asked about IS internals → slide 47"
  - "If asked about cross-config stability → slide 49"
  - "If asked about LLM-as-judge methodology → slide 48"
- [ ] You will fumble in the meeting without this. The cheat sheet is for you, not the audience.

### Three questions to ASK in the meeting (don't promise on a slide)
- [ ] Memorize these — write them on a sticky note inside the laptop lid if needed:
  - [ ] "Which Arabic? MSA, Levantine, Egyptian, or Gulf?"
  - [ ] "What does your canonical video actually look like — duration, environment, speakers?"
  - [ ] "What does 'good enough' look like for your workflow?"
- [ ] Their answers reframe the entire follow-up conversation. Don't preempt them on a slide; let them tell you.

---

## ✅ CHECK AT THE VENUE (allow 10 min before audience arrives)

Everything that depends on the actual presentation environment.

### Hardware & cables
- [ ] Laptop plugged into power (not battery — a dropped session mid-demo is the worst look)
- [ ] HDMI / USB-C / display adapter connected and projector mirroring confirmed
- [ ] Audio output set to projector / room speakers (not internal laptop speakers if room is large)

### OS preparation
- [ ] Do Not Disturb / Focus mode **ON**
- [ ] Slack, email, calendar, Teams notifications silenced
- [ ] Screen saver disabled OR delayed to >60 minutes
- [ ] Laptop battery / power notifications dismissed
- [ ] Browser closed (or windows minimized) — no stray YouTube tabs

### PowerPoint sanity
- [ ] Deck opens without errors / "missing fonts" warnings
- [ ] If a font-substitution warning appears: cancel, install Calibri if absent, or accept knowing some slides may shift slightly
- [ ] **F5 → first slide displays** — check no empty / black slide
- [ ] Click forward to slide 13 → press play once — **video plays AND audio is audible in the room**
- [ ] Click back to slide 1, ready to start

### Demo video safety net
- [ ] If the embedded video fails on the venue laptop:
  - Plan A: open the .mp4 directly from a backup USB or local folder
  - Plan B: skip slide 13 verbally — describe the demo in 30 sec, then jump to slide 14

### Timing
- [ ] Phone or watch on silent in your line of sight (not on the table — distracting)
- [ ] Wallclock noted: target end time = start + planned duration

---

## 🔴 IF SOMETHING IS BROKEN MID-MEETING

- Misspelled / wrong number on a slide → **acknowledge briefly, don't dwell.** "That should read 62%, not 64% — sorry, post-meeting fix."
- Embedded video won't play → **describe verbally in 30 seconds**, jump forward.
- Slide layout broken → step past, return after the meeting and re-render with `python3 docs/_research-tools/generators/generate_client_presentation.py`.
- Audio not working → unplug HDMI/USB-C, replug, retry. If still broken: continue with subtitles ("turn on captions in PowerPoint").

---

## After the meeting

- [ ] Note what went well / what to change in the deck for the next client.
- [ ] Update [docs/paper/presentation-remarks-log.md](../docs/paper/presentation-remarks-log.md) with feedback or surprises.
- [ ] If a number changed during the meeting (e.g., a new pilot dataset size came up) → update `MEMORY.md` > Key Project Numbers.
