# Handover log — VSP-LLM project

## 2026-08-08 · .claude-argos · main — BOX EVACUATED for decommission; migration to new AWS account pending DataSync

**The EC2 box is fully evacuated (Aug 6, audited Aug 8).** All code pushed to GitHub —
av_hubert now lives at the private `MrYoyoad/av_hubert` fork (2 rescued prep scripts;
`.gitmodules` updated); fresh `clone --recursive` verified. All box-only data (~95 GB:
critical checkpoints + sha256, 1,497-segment benchmark, client datasets, results,
archives incl. the `ron` sole-copy, git bundles, encrypted config/secrets tarball) is at
`s3://yoad-vsp-transfer/vsp/box_evac_20260806/` — full manifest + restore:
`docs/guides/box-evacuation-aug2026.md`. Secrets-tarball gpg passphrase held by Yoad.
Since the July entries below: entry-37 five-format fix shipped (`tests/unit/test_format_support.py`),
**client-build-004 built + uploaded to S3** (see `docs/guides/client-fleet-status-aug2026.md`),
tags `client-build-004` + `ec2-v1.2` pushed. **Remaining**: DataSync to the new account
(dest account ID + bucket + il-central-1 opt-in — runbook TODOs in
`docs/guides/s3-cross-account-transfer-datasync.md`), then decommission only after
destination verification. The entries below are historical (pre-evacuation).

## 2026-07-16 ~20:00 UTC · .claude-argos · main — guessing-game client package DONE; only the resolution sweep + report remain

**Package SHIPPED**: `datasets/clients/egla_kafe/deliverables/EglaKafe_guessing_game_20260716.zip`
(+ unpacked in `deliverables/guessing_game/`) — 7 videos (img_6825/6824/6822 iPhone-4K,
img_6821/6823 mustache, s2_tomer_ido_1/s1_tomer_yoad_1 camera) × (clean / model_read /
transcript.html) + README. MBR-anchored (`word_confidence_mbr.json`), side labels, `-an`
everywhere. Substitution **GO** (see `docs/evaluation/egla_kafe/phonetic_substitution_eval.md`):
2 agreement-arm corrections shipped, both s1_tomer_yoad_1 (`figured`→`forgot°`, `on`→`of°`,
orange + degree mark, ° legend only in that transcript). QA passed: 14/14 mp4s 1 video +
0 audio streams; zero leaks (said:/Emma/Jake/Tom/Dan/script-lines/http/src=/<script) in all
.ass + .html; frame spot-check shows the marked word. `findings.md` gained a
"July 2026 follow-up package" section.

**Zip built + committed** (~22:16 UTC): `EglaKafe_guessing_game_20260716.zip` = 412 MB, 22 files
(README + 7×{clean, model_read, transcript.html}; no .ass in zip). QA re-run by the parent: 14/14
streams pass, all leak greps 0 (every bare-'said' hit verified model-derived: the model's own word
or beam-alternative tooltips), substitution marks exactly `forgot°`/`of°` + legend only in
s1_tomer_yoad_1. findings.md committed `1a4b459`.

**Resolution sweep DONE** (exit 0, all 3 gates PASS, 175 rows/condition; archives
20260716_* recorded in each condition's prep_manifest.json). **Lip-pixel probe**
(`scripts/pipeline/egla_kafe_measure_lips.py`, committed `6f183d7`; results in
work/eval/lip_pixel_measurements.txt): model input is a fixed 96×96 mouth crop; measured mouth
widths — only img_6825 ≥96px (~104-111) even at 4K; img_6821-24 are 55-69px; res2k 39-75; res1080
30-56; screen-rec 20-40. Distance-to-camera dominates resolution.

**Resolution ablation DONE (`dbeeb57`)**: docs/evaluation/egla_kafe/resolution_ablation.md + 2 plots
+ comparator. **Verdict: 4K→2K→1080p — no significant difference on any metric** (IS 1.51/1.56/1.59,
all Wilcoxon n.s.; the re-encode CONTROL had the largest, still-n.s. effect; fixed-ref WER
directionally LOWER at 1080p). Mechanism: the affine warp normalizes every mouth to ~45px canonical
width inside the 96×96 crop — 4K's extra pixels are discarded at input. Client answer: framing
(mouth ≥50px, ideally ≥100px) ≫ original camera exports ≫ resolution (last). Text churn caveat:
74–84% of segment texts change between ANY two arms (76.6% under pure re-encode) while quality is
flat — never compare runs by diffing texts. ALL FOUR July-16 workstreams complete; nothing open.

---

## 2026-07-16 ~18:40 UTC · .claude-argos · main — MID-FLIGHT: guessing-game package + resolution ablation + phonetic substitution (instance-type change pause)

**Goal:** Post-meeting client package (plan: `~/.claude-argos/plans/i-need-to-send-golden-hellman.md` — READ IT):
hyp-only "guessing game" videos + colored transcripts (MBR-anchored, no reference leak), phonetic-substitution
module (beam-evidence candidates + dual LLM engines), 4K→2K→1080 resolution ablation, overlap-consistency analysis.

**Done + committed:** P0 MBR sidecars (`b3cbb77`), overlap analysis + egla addendum (`9f4789d`,`f2e972c` — 1497: green-gated neighbor precision 50.6%, L4 narrow-GO; egla turn-vs-stream NO-GO; xseg_merge was a silent no-op, would break 10:1 if wired — retire), P1 candidate generator (`d9e7c0a`), V video modes (`1e9887b`, drafts in deliverables/guessing_game/draft/), T transcript HTML (`abd34ec`), judge script (`0f7d76d`).
**Judging done (0 dropped):** egla decisions_claude.json — scene12 72 flags/2 replace, shaam 19/0; 1497 sample 300/12 replace. Paths: work/eval/substitution/{scene12,shaam}/judge/, english_full_nbest_eval/substitution/judge/.

**P2 DONE too (`c203978`)** — Llama engine (4-bit, 5.6GiB, ran egla BEFORE the hold: scene12 11 replace / shaam 2), apply + agreement arm (26/26 adversarial tests), heuristic (0 everywhere, verified genuine), L4 injector (58 green-gated overlap candidates → candidates_l4.json). **Egla ship arm (agree-mode=all) applied: scene12 = 2 subs ('figured'→'forgot', 'on'→'of', both s1_tomer_yoad_1), shaam = 0** → `work/eval/substitution/*/substitutions.json` (+ per-engine arms). P2's final report has the exact PENDING GPU commands (Llama full-1497 ~5-10 min warm + optional L4 arm, then CPU applies) — also mirrored in the P2 section of the agent transcript; commands start `substitution_engine_llama.py --candidates /home/ubuntu/english_full_nbest_eval/substitution/candidates.json ...`.

**In flight at pause:** ONLY Agent R (resolution prep: all 30 crops encoded under datasets/clients/egla_kafe_resolution/{res4k_ctrl,res2k,res1080}; dry validation + commit + final report pending; runner: scripts/pipeline/run_resolution_conditions.sh — 3 serial GPU decodes ~70 min each, NOT started).

**Next steps after restart:** (1) resume/relaunch R → dry-validate → launch runner in background (GPU priority #1); (2) after decodes: Llama-1497 runs + applies (commands in P2 report / above); (3) P3 validation vs refs (all arms incl. span, L4, oracle row from docs/nbest_viseme_handoff/snap_results.json) → GO/NO-GO (gate: fixed≥3×broke, ΔWER≤0, 0 entities, ≤5% rate); (4) A: resolution compare report; (5) F: selection (img_6825/6824/6822 + img_6821 [+6823] + s2_tomer_ido_1 + s1_tomer_yoad_1), final renders --label-source side + --wconf word_confidence_mbr.json [+ --substitutions on GO], package zip + README, docs update. GPU needed: NVIDIA ≥16GB VRAM.

---

## 2026-07-16 17:32 UTC · .claude-argos · main @ bb67ecf

**Goal:** Locate the full LRS3-TED dataset (~270 GB, ~165K utterances, pretrain/trainval/test)
— user may have downloaded or been given a copy in 2025–2026; needed to unblock the Llama 3.1
training run (see [llama3-migration.md](../finetuning/llama3-migration.md) §4).

**Done this session:**
- Exhaustive search of this EC2 box + reachable AWS: **full LRS3 is NOT here.** Only copy is the
  136 MB / 198-video flat sample `datasets/lrs3orig_sync.tar` (5 speakers, pretrain-split, no
  split layout). Swept: name match on all filesystems, all dirs ≥20 GB, ~165K-file-count
  signature, `pretrain/trainval` dir names, shell/download histories (no lrs3 URLs, no
  rclone/gdown), `s3://conversation-datasets-733430125971` (no lrs3 keys).
- Finding recorded + committed: bb67ecf in llama3-migration.md §4.
- Console screenshot revealed a **second bucket: `s3://yoad-vsp-transfer`** — now **RESOLVED,
  not LRS3**: it's the May-2026 Windows-client delivery bucket. All transcript-known keys are
  under `vsp/` (Docker images `.tar.zst` builds 001–003, install `.ps1`s, WSL msixbundle, kit
  zips); HeadObject verified `vsp-image-client-build-003-20260513.tar.zst` = 42.7 GB. Role has
  GetObject but not ListBucket (missing keys 403 as Forbidden — that masked earlier probes).

**Failed / don't retry:**
- `aws s3 ls` (ListAllMyBuckets), `backup list-backup-vaults`, `glacier list-vaults`,
  `get-bucket-policy` — all AccessDenied for the instance role. Don't re-probe from this box.
- Adding an inline policy to `AmazonSSMRoleForInstances` via user's console — **denied** (user
  lacks IAM write). The working pattern for `conversation-datasets-*` was a **bucket policy**,
  not a role policy.

**Blockers:**
- **Everything reachable from this box is now exhausted — LRS3 is confirmed absent** from this
  EC2 (all disks) and from both account buckets. IAM edits by the user's console identity were
  denied, but they're no longer needed for the search.

**Next steps (all off-box):**
1. User's email / Drive / Slack: search "LRS3" — VGG (Afouras / Joon Son Chung / Zisserman)
   or colleague share from the May-2026 out-of-band sourcing. Comms connectors were
   unauthenticated this session; authorize claude.ai connectors or search manually.
2. Other machines and other AWS accounts/profiles (a bucket outside account 733430125971 is
   the most likely S3 win — this account only has the two known buckets).
3. If found → transfer plan: same-region S3 + `s5cmd --numworkers 32 sync`; **root disk has
   only ~102 GB free** — attach/grow EBS (~400 GB gp3) before pulling 270 GB. Training plan
   ready to resume: session 9b07e9d9 (2026-07-16) drafted the two-stage Llama-3.1 + topic-label
   plan, Phase 0 blocked on exactly this dataset.
4. Fallback stays: AVSpeech-only at 20K+ segments (loses paper-equivalence).

**Artifacts:** docs/finetuning/llama3-migration.md §4 (commit bb67ecf),
datasets/lrs3orig_sync.tar (the sample), docs/guides/project-handover-july2026.md §4 (open bets).

---

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
