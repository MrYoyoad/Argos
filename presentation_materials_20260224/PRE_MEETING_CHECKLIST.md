# Client Deck — Pre-Meeting Checklist

**Deck:** `Argos_VSP_Client_46slides_Apr2026.pptx`
**Detailed instructions:** [docs/guides/client-deck-powerpoint-checklist.md](../docs/guides/client-deck-powerpoint-checklist.md)
**OOXML compat scan:** [PP_COMPAT_REPORT.txt](PP_COMPAT_REPORT.txt) in this folder

Phone-friendly version. Two passes: at home/office before you leave, then again at the venue right before the meeting starts.

---

## ✅ CHECK BEFORE LEAVING (allow 30 min)

These need access to your dev machine and the deck source, so do them before walking out the door.

### Embed the demo video (slide 6)
- [ ] Recorded the UI walkthrough following `docs/guides/client-demo-recording-guide.md`
- [ ] Saved as MP4 / **H.264** codec (the OOXML compat scan flags HEVC — re-encode if needed)
- [ ] In PowerPoint, slide 6 → Insert → Video → **Video on My PC** (NOT "Online Video")
- [ ] Resized to fill the placeholder card
- [ ] Playback tab → confirmed Start setting (Automatically vs On Click) you want
- [ ] Pressed F5 → tested the video plays from inside presentation mode
- [ ] Heard audio through laptop speakers (not just headphones)

### Customize the next-steps slide (slide 45)
- [ ] Pilot dataset card — replaced "Size, content type, sample source" with client-specific text
- [ ] Integration scope card — replaced with actual systems to wire into
- [ ] Timeline card — replaced with realistic weeks/dates
- [ ] Success criteria card — replaced with what "good" looks like for this client

### Title slide (slide 1)
- [ ] Date is current (currently April 2026)
- [ ] Optional: client name added on a line above "Yoad Oxman · Argos / The Orchard"

### Click-through dry run
- [ ] Opened the deck in **real PowerPoint** (not LibreOffice / web preview)
- [ ] Stepped through all 46 slides at full screen (F5)
- [ ] Slides where I want extra eyes:
  - [ ] **Slide 6** — does the ▶ play triangle render? If it shows as a square/box, edit and replace with text
  - [ ] **Slides 10–12** — Obama examples — green/yellow/red colors visible? Legend at bottom readable?
  - [ ] **Slides 17, 18** — embedded chart PNGs — crisp, not blurry?
  - [ ] **Slide 28** — pat/bat/mat cards — three columns balanced?
  - [ ] **Slide 30** — Cloud / On-premise cards — borders crisp?
  - [ ] **Slides 33, 34** — entity-split + quality-filter diagrams — readable at full screen?

### Timing
- [ ] Out-loud read-through with stopwatch
- [ ] Total time noted: ___ min (target: 30–45 min for the deep-dive version)
- [ ] Any single slide >90 sec? → mark for trimming or splitting

### Travel
- [ ] Deck saved to a USB stick as backup (in case the client laptop has no email/network)
- [ ] **Phone has this checklist open** so you can re-check at the venue

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
- [ ] If a font-substitution warning appears: cancel, install Calibri if absent, or accept knowing slides 6/28 may shift slightly
- [ ] **F5 → first slide displays** — check no empty / black slide
- [ ] Click forward to slide 6 → press play once — **video plays AND audio is audible in the room**
- [ ] Click back to slide 1, ready to start

### Demo video safety net
- [ ] If the embedded video fails on the venue laptop:
  - Plan A: open the .mp4 directly from a backup USB or local folder
  - Plan B: skip slide 6 verbally — describe the demo in 30 sec, then jump to slide 7

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
