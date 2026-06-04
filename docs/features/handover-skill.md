# `/handover` skill — cross-session & cross-account context handoff

**Status:** Shipped 2026-06-04. Available to both Claude Code accounts on this machine.

## Why

This project is worked on across many Claude Code sessions and by **two split accounts**
(`.claude-argos` and `.claude-personal`) that share the same working tree at `/home/ubuntu`.
The existing continuity surfaces each cover part of the problem but leave a gap:

- `claude --continue` (shared transcripts) replays the *entire* conversation — all-or-nothing,
  useless for a quick brief.
- Auto-memory (`MEMORY.md`) holds *durable* facts, auto-injected — not in-flight state.
- `/distill` → `~/knowledge` holds *portable, abstracted* lessons — not project working context.

None of them capture the **volatile working state** — the current goal, decisions and their
rationale, approaches that *failed* (so they aren't retried), blockers, and the immediate next
steps. `/handover` fills exactly that gap: a small, structured digest of what the next session
*cannot* reconstruct from code, `CLAUDE.md`, or memory.

The design follows current session-handoff practice: hand off (rather than `--continue`/compact)
when the next chunk of work shares little context with the current one, or before quality
degrades on a very long session; include only non-reconstructible context; keep it as a portable
markdown artifact that any agent can read.

## What it does

A single skill with two verbs, dispatched on its argument:

| Invocation | Action |
|---|---|
| `/handover` or `/handover save` | Capture current state → show you the entry for approval → prepend it to `docs/sessions/HANDOVER.md`. |
| `/handover resume` (`load`/`read`/`brief`/…) | Read the latest entry, brief the incoming session (goal, next steps, blockers), and offer to pick up the next step. |

### Storage
- Rolling **`docs/sessions/HANDOVER.md`**, newest entry on top, separated by `---`. Keeps the
  **5 most recent** entries; older ones are trimmed (working context is disposable).
- Each entry is stamped: `## <timestamp> · <account> · <branch> @ <short-commit>`.
- **Left uncommitted by default.** Both accounts read it off the shared disk at `/home/ubuntu`,
  so no commit is needed for the other account to see it. The skill offers to commit only on
  request. (This doc and the skill code *are* version-controlled; the live note is not.)

### Entry sections
Goal · Done this session · Decisions (+ rationale) · **Failed / don't retry** · Open questions ·
Blockers · Next steps (ordered) · Artifacts (paths only). Empty sections are omitted.

### Path resolution (generic, repo-aware)
1. In a git repo with `docs/sessions/` → `<root>/docs/sessions/HANDOVER.md` (canonical here).
2. In a git repo without it → `<root>/HANDOVER.md`.
3. Outside a git repo → `./HANDOVER.md` in the cwd (git fields recorded as `n/a`).

## How it reaches both accounts

`/home/ubuntu/.claude-argos/skills` and `/home/ubuntu/.claude-personal/skills` are **both
symlinks** to `/home/ubuntu/.claude/skills`. A single `handover/SKILL.md` there is auto-discovered
by both accounts — no per-account copy. `settings.json` is symlinked the same way, so the
companion hook (below) also serves both. See `~/knowledge/decisions/0001-dual-account-claude-setup.md`
for the shared-config rationale.

## Companion hook (auto-resume nudge)

An opt-in `SessionStart` hook in the shared `settings.json` prints a one-line pointer when a
handover note exists, so resume isn't forgotten:

```
📋 Handover note: <date> · <account> · <branch> @ <commit> — run /handover resume
```

It is read-only and silent (exit 0, no output) when no note exists. There is intentionally **no
auto-save** hook: `Stop` fires on every turn, not at session close, so there is no clean
"session end" event to hang an auto-save on — saving stays a deliberate manual action.

> Settings-watcher caveat: a newly added hook activates on the **next** session start. Open
> `/hooks` once (or restart) to load it in the current session.

## How it complements existing tools (no duplication)

- **`/status`** = durable project progress; `/handover` = ephemeral "where the cursor was."
- **`/distill`** = portable lessons in `~/knowledge`; `/handover` excludes these and nudges `/distill`.
- **`MEMORY.md`** = durable auto-facts; `/handover` assumes them and adds only the volatile delta.
- **`claude --continue`** = full transcript replay; `/handover resume` = the one-minute digest.

## Files

| File | Role | Versioned? |
|---|---|---|
| `~/.claude/skills/handover/SKILL.md` | The skill (source of truth) | No — `.claude/` is gitignored; full copy embedded below |
| `~/.claude/settings.json` → `hooks.SessionStart` | Auto-resume nudge | No — same reason; snippet embedded below |
| `docs/sessions/HANDOVER.md` | The rolling note | Tracked dir, but the note is left **uncommitted** by design |
| `docs/features/handover-skill.md` | This document | Yes |

---

## Appendix A — `SKILL.md` (recovery copy)

> Source of truth is `~/.claude/skills/handover/SKILL.md`. This copy exists because `.claude/` is
> gitignored; if the config dir is lost, recreate the file from here.

````markdown
---
name: handover
description: Pass working context between Claude Code sessions and between split accounts on the same project. SAVE captures the current half-finished state (goal, decisions, failed approaches, blockers, next steps) into a rolling HANDOVER.md; RESUME reads the latest entry and briefs the incoming session. Generic — works in any git repo; repo-aware for this project. Use at the end of a session, before switching accounts, or at the start of a fresh session.
argument-hint: "[save | resume]  (no arg = save)"
---

You are managing a **rolling handover note** that carries volatile working context across
Claude Code sessions and across the two split accounts that share this project.

The note's only job is to capture what the **next session cannot reconstruct on its own** from
code, git history, `CLAUDE.md`, or per-account memory: the *in-flight* state — the current goal,
what was just done, decisions and their rationale, approaches that FAILED (so they aren't
retried), open questions, blockers, and the immediate next steps. Do **not** restate durable
facts that already live elsewhere; point to them instead.

## 0. Dispatch on the verb

Read `$ARGUMENTS`, lowercased and trimmed:
- empty, `save`, `write`, `note`, `dump`  → **SAVE flow** (Section 1).
- `resume`, `load`, `read`, `continue`, `brief`, `catch up`, `catchup` → **RESUME flow** (Section 2).
- anything else → treat as SAVE, but first tell the user you interpreted it as save and how to
  invoke resume.

## 0a. Resolve the target file (both flows use this)

1. Find the repo root: `git rev-parse --show-toplevel 2>/dev/null`.
2. Choose the path, in order:
   - repo root exists **and** `<root>/docs/sessions/` exists → `<root>/docs/sessions/HANDOVER.md`.
   - else if a repo root exists → `<root>/HANDOVER.md`.
   - else (not a git repo) → `./HANDOVER.md` in cwd.
3. Remember this as **HANDOVER_PATH**, and **GIT_ROOT** (repo root, or cwd if none). Pass GIT_ROOT
   to every git command as `git -C <GIT_ROOT> …` so results don't depend on the shell's subdir.

## 1. SAVE flow

Follow a **gather → show user → write** flow (like `/distill`). Never write before the user has
seen and approved the entry.

### 1.1 Capture machine state (read-only)
Run and keep the output; never mutate the repo:
```
date "+%Y-%m-%d %H:%M %Z"                      # entry timestamp
basename "${CLAUDE_CONFIG_DIR:-unknown}"       # active account (.claude-argos/.claude-personal)
git -C <GIT_ROOT> rev-parse --abbrev-ref HEAD  # branch
git -C <GIT_ROOT> log --oneline -1             # last commit
git -C <GIT_ROOT> log --oneline -5             # recent history
git -C <GIT_ROOT> status --porcelain           # uncommitted/staged
git -C <GIT_ROOT> diff --stat                  # shape of unstaged work
git -C <GIT_ROOT> diff --stat --staged         # staged work
```
- Account: `basename "$CLAUDE_CONFIG_DIR"`; if unset, record `unknown` and don't fail.
- Files touched this session: trust what you actually edited in *this* conversation, cross-checked
  against `git status --porcelain`; note any discrepancy briefly.
- Large diffs: never paste a full diff — record only the `--stat` summary plus the few files that
  matter for the next step.

### 1.2 Synthesize the narrative (only non-reconstructible context)
- **Goal / task** — one-line objective.
- **Done this session** — what changed and why (brief; the diff has details).
- **Decisions + rationale** — so they aren't re-litigated.
- **Failed approaches** — what was tried that did NOT work, and why (highest-value section — be specific).
- **Open questions** — unresolved, needs a human or more investigation.
- **Blockers** — what's stopping progress.
- **Next steps** — ordered, concrete, the very next action first.
- **Artifacts** — *paths* to files/logs/branches/PRs — NOT their contents.

Boundaries: durable project facts → `CLAUDE.md`/memory (omit, optionally flag); portable lessons →
`~/knowledge` via `/distill` (omit, suggest at end); full conversation → `--continue`. Never include
secrets/tokens/PII — refer to them generically.

### 1.3 Show the user, then write
1. Render the proposed entry (template below) and ask for quick approval/edits; apply edits.
2. On approval, write to **HANDOVER_PATH**:
   - If absent (first run): create dirs+file, lead with one header line `# Handover log — <repo>`,
     then the entry.
   - Else **re-read the file immediately** (avoid a stale read), then **prepend** the new entry
     above existing ones: `header + new-entry + "\n---\n" + existing-entries`.
   - **Trim:** keep the 5 most-recent entries (delimited by `## ` headings / `---` rules); drop older.
3. Confirm: path written, account/branch/commit stamp, entry count, and the resolved HANDOVER_PATH
   (so a wrong-repo/wrong-cwd mistake is visible).

### 1.4 Do NOT commit; closing tips
- Leave HANDOVER.md uncommitted; both accounts read it off shared disk. Offer "Want me to commit
  it?" only if asked (then `git add` it; commit as **Yoad Oxman <yoyoad@gmail.com>**, **no
  Co-Authored-By / AI attribution**).
- Cross-account tip: to resume the *full conversation* (not just this digest) on the other account,
  relaunch it with `claude --continue` — transcripts are shared (the `cswitch` helper does this).
- If a durable, portable lesson emerged, suggest `/distill`; do **not** copy it into the handover.

## 2. RESUME flow
1. Resolve **HANDOVER_PATH** (Section 0a).
2. If missing/empty: say "No handover note found at `<HANDOVER_PATH>`." Offer to brief from
   `git log` + working-tree status instead, and suggest `/handover save`. Stop (don't error).
3. Read the file; take the **top (newest) entry only**.
4. Brief the user concisely: provenance line (timestamp · account · branch @ commit), then goal,
   open next steps, and any blockers/failed-approach warnings.
   - If the writing account differs from the current `$CLAUDE_CONFIG_DIR`, flag it explicitly.
5. Sanity-check vs reality: `git -C <GIT_ROOT> rev-parse --abbrev-ref HEAD` and `log --oneline -1`;
   if branch/commit differ from the entry, point it out.
6. Offer to pick up the **immediate next step** and continue.

## Entry template (every prepended SAVE entry)
Skimmable in under a minute; omit empty sections rather than padding. The `## ` line is the entry
delimiter and at-a-glance stamp; entries separated by `---`.
```
## <YYYY-MM-DD HH:MM TZ> · <account> · <branch> @ <short-commit>

**Goal:** <one line>

**Done this session:**
- <change> — <why, brief>

**Decisions:**
- <decision> — <rationale>

**Failed / don't retry:**
- <approach> — <why it failed>

**Open questions:**
- <question>

**Blockers:**
- <blocker>

**Next steps:**
1. <the very next action>
2. <then this>

**Artifacts:** <path>, <path>, <branch/PR>   (paths only, no contents)
```

## How this complements (not duplicates) other tools
- **`status`** = durable project progress; **handover** = ephemeral "where the cursor was." A save
  may suggest `status` but never writes its content.
- **`distill`** = portable lessons in `~/knowledge`; handover excludes these and nudges `/distill`.
- **`MEMORY.md`** = durable auto-facts; handover assumes them and adds only the volatile delta.
- **`--continue`** = full transcript replay; handover = the one-minute curated digest. Complementary.
````

## Appendix B — `SessionStart` hook (recovery copy)

Top-level `hooks` key in `~/.claude/settings.json`:

```json
"hooks": {
  "SessionStart": [
    { "hooks": [ { "type": "command",
      "command": "f=\"$CLAUDE_PROJECT_DIR/docs/sessions/HANDOVER.md\"; [ -f \"$f\" ] || f=\"$CLAUDE_PROJECT_DIR/HANDOVER.md\"; [ -f \"$f\" ] && { stamp=$(grep -m1 '^## ' \"$f\" | sed 's/^## //'); printf '📋 Handover note: %s — run /handover resume\\n' \"$stamp\"; } || true"
    } ] }
  ]
}
```
