# Client Demo Recording Guide

**Purpose:** Self-record the UI walkthrough that goes into the client deck. Target length **4–5 minutes**.

This is the centerpiece of Section 2 in [Argos_VSP_Client_52slides_Apr2026.pptx](../../presentation_materials_20260224/). When you finish, save the source `.mp4` at:

```
presentation_materials_20260224/06_demo_videos/_ui_walkthrough_clientpitch.mp4
```

---

## 1. Equipment & Setup

### Recorder
- **Loom** (https://www.loom.com/) — free tier is enough; auto-uploads, click highlighting, easy trim. **Recommended.**
- **macOS QuickTime Player** — File → New Screen Recording. Built-in, no install.
- **OBS Studio** — most control, free. Install the "Highlight Cursor" plugin separately.
- **Avoid Zoom recordings** — quality is too low for an embedded slide.

### Microphone
- USB headset mic or external USB mic preferred (Blue Yeti / Snowball / similar).
- The MacBook built-in mic is acceptable in a quiet room — but **do a 30-second test recording first** and listen back with headphones. If you hear any room echo or fan noise, switch to a headset mic.

### Camera (optional)
- A picture-in-picture of your face in a corner can help, but it's not required and can be distracting.
- Default to no camera unless you're confident on camera.

### Browser
- Fresh **Chrome** window — no extensions visible.
- Full-screen.
- **Bookmarks bar hidden** (`Cmd+Shift+B` on macOS to toggle).
- No other tabs open.

### Resolution
- **1920×1080 minimum.** In Loom, set "HD 1080p" before starting.
- In QuickTime, click the down-arrow next to the record button → make sure microphone is selected.

### Cursor highlighting
- **On.** Loom does this automatically.
- OBS: install the "Highlight Cursor" plugin.
- QuickTime: shows a click ring by default if "Show Mouse Clicks" is enabled in the recording dropdown.

---

## 2. Pre-Record Checklist (10 min)

Don't skip these. The most expensive thing in this 48 hours is a recording where the demo crashed.

1. **Pre-run the pipeline once** end-to-end on the same input video you're about to record with. Confirm nothing crashes. Confirm the report opens. Confirm the word-level color coding renders.
2. **Stage the input video** — pick one with clear speech and one or two named entities. Confirm it produces a high-IS, mostly-green output. **Do not gamble on a fresh clip during the recording.**
3. **Clear the output folder** so the Complete screen looks fresh during the demo.
4. **Close Slack, email, calendar, notifications.** macOS Do Not Disturb on. Quit anything that might pop up.
5. **Set browser zoom 110–125%** so text is readable in the recorded video.
6. **One full dry-run aloud, with a timer.** Aim under 5 minutes. If you go over, cut something.

---

## 3. The Script — 4 Scenes, ~1 Min Each

Read these out loud while you click. **Pause 1–2 seconds between scenes** to make editing easy later.

### Scene 1 — The setup (0:00–0:45)
> "This is the visual speech recognition pipeline. The whole product runs in your browser. I'm going to take a video, drop it in, and walk you through what comes out the other end. Nothing's pre-cached — this is the real thing running live."
>
> *(Drag-drop your test video onto the page. Let the validation animation play.)*
>
> "The system has detected the video, validated it, and is showing me how many segments it'll process."

### Scene 2 — The pipeline running (0:45–2:00)
> *(Click "Start Processing." Let the progress bar run.)*
>
> "It's now running through nine automatic stages — face detection, mouth cropping, ASR, LLM-based decoding. You can watch progress in real time. For your content this would take roughly N minutes per hour of video."
>
> *(Edit out long waits when you cut. You don't need to show all 9 stages live; cut to "almost done" and show the final stages.)*

### Scene 3 — The report (2:00–3:30) — *most important scene*
> *(Click "Open Results." Open the HTML report.)*
>
> "Here's the part most clients care about. Each segment has the decoded transcript with **per-word confidence color-coding**. Green words are high confidence. Yellow are worth a quick review. Red flags potential errors."
>
> *(Scroll slowly. Hover over a green word, then a yellow word, then a red word. Don't rush — let the viewer's eye land on each one.)*
>
> "On the right, you'll see the segment-level Intelligibility Score. This is calibrated against expert judgment — segments above 3.8 are clearly conveyed, between 2 and 3.8 are useful with context, below 2 we flag for review."

### Scene 4 — The trust message (3:30–4:30)
> *(Scroll to a hallucinated / red-flagged segment. Or pull up the dashboard.)*
>
> "Here's a segment the system flagged as low-confidence. The model knew it wasn't sure — it's marked red, low IS, pulled out of the 'usable' bucket automatically. **You don't have to review every segment to find the bad ones; the system finds them for you.** That's the difference between this and a black-box transcript."
>
> *(Pause. End on the dashboard or Complete screen.)*
>
> "That's the whole pipeline. Drag in, walk away, come back to color-coded results you can trust."

---

## 4. Common Pitfalls

- **Don't apologize** for anything that's working. If a stage takes 30 seconds, *say* "this stage takes 30 seconds" — don't say "sorry this is slow." Confidence is contagious.
- **Don't read out the technical names** ("VSP-LLM decoder," "k-means clustering") to a non-technical client. Say what those things *do*.
- **Cut, don't restart.** If you flub a sentence, pause for 2 seconds, then say it again cleanly. You'll edit out the mistake.
- **Speak ~20% slower than feels natural.** Watch a previous recording — almost everyone speaks too fast on the first take.
- **Hover, don't just click.** Move your cursor *to* a word *before* clicking. The viewer's eye follows your cursor; help them.
- **End on a still frame**, not mid-click. The last thing the client sees should be a clean Complete or report screen.

---

## 5. Editing & Embedding

- **Trim** dead air at the start/end and between scenes. Loom has a built-in trim. iMovie or DaVinci Resolve (free) for anything more complex.
- **Export** as **MP4 / H.264 / 1080p**.
- **Embed in PowerPoint** with **Insert → Video → Video on My PC**, *not* a link — clients may not have internet during the meeting.
- **Save the source `.mp4`** at `presentation_materials_20260224/06_demo_videos/_ui_walkthrough_clientpitch.mp4` so it's tracked alongside the example clips.

---

## 6. Quality Checklist Before Embedding

- Audio levels consistent across scenes (no sudden volume jumps).
- Cursor visible and highlighted throughout.
- No notification pop-ups visible in the recording.
- Total length under 5 minutes.
- Plays at 1080p when previewed full-screen.
- Embeds (not links) into the PPTX — plays offline.
