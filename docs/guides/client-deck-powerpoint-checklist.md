# Client Deck — PowerPoint Pre-Meeting Checklist

The deck was authored on Linux via `python-pptx` and rendered for QA via
LibreOffice → PDF → PNG. **Real PowerPoint may render some things slightly
differently.** Walk through this checklist when you open the deck in
PowerPoint on your machine, ideally on the actual hardware you'll present
from.

**Deck file:**
`presentation_materials_20260224/Argos_VSP_Client_46slides_Apr2026.pptx`

---

## 1. Open and click through every slide (10 min)

Open in PowerPoint and click through all 46 slides at full screen. Look
for:

- **Text overflow.** Any text running past the slide edge that looked fine
  in the LibreOffice render. PowerPoint and LibreOffice handle Calibri
  kerning slightly differently — a long line that fits in one may wrap in
  the other.
- **Missing characters.** Calibri supports the Unicode used here, but if
  PowerPoint substitutes a font (e.g., on a presentation laptop with
  Calibri uninstalled), some glyphs may render as boxes. Specific things
  to verify:
  - Slide 6: the **▶ play triangle** in the demo placeholder. If it shows
    as a square/box, manually edit and replace with text "Play below" or
    just delete — slide still works without it.
  - Slides 11, 12: the **·** middle-dot in the segment subtitle line
    ("Obama bin Laden announcement · segment #14 · …"). Should render as
    a centered dot.
  - Slide 30: arrows or other special characters in the bullets.
- **Color rendering.** Navy background should be `#0d1b2a` everywhere.
  Per-word green/yellow/red on slides 11/12 should look distinct.
- **Image clarity.** Five embedded PNGs across the deck. Verify each is
  crisp (not blurry) at full screen:
  - Slide 17 — Obama report screenshot.
  - Slide 18 — IS confidence-gate plot (two-panel chart).
  - Slide 33 — entity-split diagram.
  - Slide 34 — quality-filter funnel.
  - (Whichever slide carries the trust dashboard plot, if used.)

If anything is broken: **fix it directly in PowerPoint** (right-click →
edit). Don't try to round-trip through python-pptx for one-off polish —
PowerPoint is the source of truth from here on.

---

## 2. Embed the demo video (5 min) — slide 6

This is the only slide that is intentionally incomplete in the
generator output:

1. Record the UI walkthrough using `docs/guides/client-demo-recording-guide.md`.
2. In PowerPoint, go to slide 6 ("Live UI Demo").
3. **Insert → Video → Video on My PC**, choose your `.mp4`. **Don't use
   the "Online Video" option** — clients often present from a room with
   no internet.
4. Resize the video to fill the placeholder card. Right-click → Send to
   Back if it covers the heading text.
5. Click the video, then **Playback tab → Start: Automatically** so it
   plays as soon as you click into the slide. If you'd rather click to
   play, leave on **On Click**.
6. Test by entering presentation mode (F5) and stepping to slide 6 — the
   video should play in place. **Verify audio plays** through the
   meeting room speakers, not just headphones.

---

## 3. Customize the next-steps slide (3 min) — slide 45

Slide 45 has four placeholder cards (Pilot dataset / Integration scope /
Timeline / Success criteria) with generic prompts. Edit each card body in
PowerPoint with client-specific language:

- **Pilot dataset**: "X hours of [content type] from [source] in [language]"
- **Integration scope**: "Wire into [your CMS / Slack / Looker / S3 bucket]"
- **Timeline**: "First end-to-end run in [N] weeks. Pilot complete by [date]."
- **Success criteria**: "Capture rate ≥ [X]% on [domain]. Reviewer time
  reduced by [Y]%."

Generic = forgettable. Specific lands.

---

## 4. Test on the actual presenter hardware (5 min)

If you'll present from a laptop other than the one you're authoring on:

- Copy the deck to that machine and open it in PowerPoint there.
- Re-check fonts (Calibri must be installed; it usually is by default on
  Windows and Mac).
- Step through slides 1, 6, 17, 18, 28, 33, 34, 45 specifically (the
  ones with images, embedded video, or special characters).
- Confirm the embedded video plays from the local file path on the
  presenter machine.

---

## 5. Set the title slide's client/date (1 min) — slide 1

Slide 1 currently reads:
> Yoad Oxman · Argos / The Orchard · April 2026

Update the date if the meeting slips, and add the client's name above
your name if you want a personal touch:
> [CLIENT NAME] · [DATE]
>
> Yoad Oxman · Argos / The Orchard

---

## 6. Time the dry-run (15 min)

Read the deck top-to-bottom **out loud** with a stopwatch. Note slides
where you ran over budget (>90 sec on a single slide is a sign the slide
is doing too much and should be split or trimmed).

Target totals:

- 5-min lightning version: hit slides 1, 3, 6, 17, 18, 33, 41, 43, 44.
- 20-min standard: every slide once with brief commentary.
- 45-min deep dive: every slide with full speaker notes (notes are in
  the speaker-notes pane, click View → Notes Page in PowerPoint).

---

## Known LibreOffice → PowerPoint divergence to watch for

These are things our LibreOffice render may show differently than what
PowerPoint will show:

| Pattern | LibreOffice render | PowerPoint expected |
|---------|--------------------|--------------------|
| Unicode play triangle (▶) | Often invisible | Usually renders |
| Long Calibri lines | May wrap one way | May wrap differently — verify titles & long bullets |
| `add_picture` aspect locking | LibreOffice respects | PowerPoint usually respects, but double-check the 5 embedded plots are not stretched |
| Animations | None — static render | We don't use animations on the client deck. If you see any unexpected animation, it's an artifact of an old layout — delete in PowerPoint |
| Embedded video poster frame | Shown as static | Plays on click in presentation mode |

---

## If something is genuinely broken

The deck source lives in:
- `docs/_research-tools/generators/generate_client_presentation.py` (orchestrator)
- `docs/_research-tools/generators/presentation/slides_client.py` (client builders)

Re-render with:

```
python3 docs/_research-tools/generators/generate_client_presentation.py
```

Audit with:

```
pytest tests/unit/test_number_audit.py tests/unit/test_style_compliance.py
```

But for one-off pre-meeting polish, **edit in PowerPoint directly** —
faster and less likely to break something else.
