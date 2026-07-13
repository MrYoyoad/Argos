# Handover log — VSP-LLM project

## 2026-07-13 · .claude-argos · main — DEPARTURE HANDOVER + July client-meeting package

**Goal:** Prepare the final Egla-Kafe client meeting (~1h, within 2 weeks) and package the
engineering handover — the lead (Yoad) leaves the project in a few weeks; succession undecided.

**Done this session:**
- **Engineering handover doc written**: [docs/guides/project-handover-july2026.md](../guides/project-handover-july2026.md)
  — successor onboarding: system state, deployment doctrine, client commitments, open bets
  (Llama 3.1 blockers), ready-to-assign 5-day projects, traps, first-week checklist. **This is
  the entry point for whoever inherits the project.**
- July meeting two-deck package built, audited, committed: `Argos_VSP_EglaKafe_20260713.pptx`
  (data story, 10 slides) + `Argos_VSP_EglaKafe_Roadmap_20260713.pptx` (roadmap/ask, 12 slides),
  QA_CHEAT_SHEET.md Egla-Kafe section, PRE_MEETING_CHECKLIST_JULY2026.md.
- **File forensics finding**: the client's "camera" footage is viewer-app *screen recordings*
  (odd varying resolutions, zoom-slider UI in pixels, 7× lower bitrate) — the camera's native
  output has never been seen. Documented in findings.md § File forensics; first ask is now
  "export original files" (re-shoot pilot is plan B).

**Decisions:**
- Meeting = two artifacts (data-story deck + roadmap/ask deck), Egla-Kafe client only in the room.
- Succession deliberately part of the partnership ask (Deck 2 "Built to continue" slide).

**Blockers / pending (user-side):**
- Dry-run both decks in real PowerPoint; customize Deck 2 slide 11 cards.
- Email client asking for original camera-system exports (before the meeting if possible).
- Align with Amosi/managers on who states the succession plan.

**Next steps (for any session picking this up):**
1. If client sends native camera files → re-run eval per docs/guides/client-lipread-eval.md.
2. After the meeting → log outcomes in presentation-remarks-log.md + findings.md; record
   answers to the six questions (in PRE_MEETING_CHECKLIST_JULY2026.md).
3. Keep [project-handover-july2026.md](../guides/project-handover-july2026.md) current until departure.

---

## 2026-06-04 15:10 UTC · .claude-argos · main @ f3865bb

**Goal:** Add a `/handover` skill to pass working context between sessions and between the two split accounts (`.claude-argos` / `.claude-personal`) on this project.

**Done this session:**
- Created `/home/ubuntu/.claude/skills/handover/SKILL.md` — save + resume skill; reaches both accounts via the symlinked `skills/` dir.
- Added an opt-in `SessionStart` hook to the shared `/home/ubuntu/.claude/settings.json` that prints a one-line pointer when this file exists (read-only, silent when absent).
- Wrote the plan at `/home/ubuntu/.claude-argos/plans/help-me-create-a-peaceful-sphinx.md`.

**Decisions:**
- Storage = rolling `docs/sessions/HANDOVER.md`, newest entry on top, keep last 5 — git-tracked, visible to humans + both accounts.
- Do NOT auto-commit — both accounts read it off shared disk; commit only on request.
- One shared skill file serves both accounts (`skills/` is symlinked); no per-account copy.
- Skill is generic but repo-aware: `docs/sessions/` here, else `<repo-root>/HANDOVER.md`, else cwd.

**Failed / don't retry:**
- Auto-save on the `Stop` hook — `Stop` fires every turn, not at session close, so there's no clean "session end" event; auto-save would be noisy/wrong. Only the *resume* side is automated (SessionStart).
- `allowed-tools` frontmatter was dropped — the on-disk skills (`distill`/`sleep-timer`) don't set it and it risks over-restricting the procedural body.

**Open questions:**
- Whether to `/distill` the generic "cross-account handover skill" pattern into `~/knowledge` (optional; pairs with `decisions/0001-dual-account-claude-setup.md`).

**Blockers:**
- SessionStart hook only activates on the *next* session start (settings-watcher caveat) — open `/hooks` or restart to load it now. The skill itself works immediately.

**Next steps:**
1. Cross-account test: run `/handover resume` from `.claude-personal` and confirm it reads this entry and shows the account-mismatch flag.
2. Optionally `/distill` the portable pattern.
3. Optionally commit the new skill + settings change if you want them versioned.

**Artifacts:** /home/ubuntu/.claude/skills/handover/SKILL.md, /home/ubuntu/.claude/settings.json (hooks.SessionStart), /home/ubuntu/.claude-argos/plans/help-me-create-a-peaceful-sphinx.md
