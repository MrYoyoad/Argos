# Docs Sync Plan — Round 2 (May 2026, post-For-Orchard)

**Generated:** 2026-05-07
**Predecessor:** `docs_sync_plan.md` → executed `9ca0011`–`a1f40b6` (5 waves, 223 deletions)
**Canonical narrative:** `Argos_VSP_For_Orchard_May2026.pptx` (88 slides, 79 visible + 9 hidden)
**Canonical numbers:** `docs/evaluation/after_amosi_audit.md` + `after_amosi_audit.json` (MBR-default)
**Deliverable type:** Plan only — no edits or deletions performed here.

---

## TL;DR

The Round 1 sync was comprehensive. Since `a1f40b6` (last sync commit), the delta is small:
no new number drift, no new failed experiments. The remaining work is:

| Bucket | Files | Action |
|---|---|---|
| PPTX audit ephemera (not yet archived) | 7 | Archive to `docs/evaluation/_archive/pptx_audit_history/` |
| Research overview (skipped in R1) | 1 (319 lines) | Keep as-is — valuable review doc, add 1-line MBR header |
| Mission backlog stale numbers | 1 | Update 4 headline stats to MBR-default |
| Memory feedback (new audit lessons) | — | Add Round 5.3/5.4 lessons to memory (already in `presentation-audit-lessons.md`) |

Estimated effort: 1 wave, ~20 min.

---

## Canonical numbers reminder

From `after_amosi_audit.md` (MBR-default, production since 2026-05-02):

| Stat | MBR-default | Top-1 baseline |
|---|---|---|
| WER | 63.8% | 64.1% |
| IS mean | 2.547 | 2.532 |
| NIV-Y | 358/1497 = 23.9% | 359/1497 = 24.0% |
| NIV-Y+P | 927/1497 = 61.9% | 923/1497 = 61.7% |
| LLM Judge Y+P (MBR) | 71.1% | 68.4% (baseline) |
| Trust-gate ≥30% green | 65.2% recall / 5.6% FPR | (computed on per-word conf, method-independent) |

---

## Wave A — Archive remaining PPTX audit ephemera

**Target directory:** `docs/evaluation/_archive/pptx_audit_history/` (already exists from R1 Wave 3)

Files to move (all in `docs/evaluation/`):

| File | Lines | Notes |
|---|---|---|
| `pptx_fix_manifest.md` | 682 | Completed fix list from pre-Orchard audit — historical, keep in archive |
| `pptx_visual_audit.md` | 225 | Pre-Orchard visual audit — superseded by pass2 |
| `pptx_visual_audit.json` | — | Companion JSON — archive alongside md |
| `pptx_visual_audit_pass2.md` | 190 | Most recent pre-merge pass — archive (all issues resolved) |
| `pptx_visual_audit_pass2.json` | — | Companion JSON |
| `pptx_visual_fix_pass2.md` | 13 | Fix log for pass2 — archive |
| `pptx_text_render_audit.json` | — | Current (0-issue) render audit — keep in place (not ephemera) |

**Keep in place:** `pptx_text_render_audit.json` — this is the live readability check result (0 issues, 88 slides); it should stay at `docs/evaluation/` as the canonical audit artefact, same as before.

**Action:** `git mv` all 6 (excluding text_render) into `docs/evaluation/_archive/pptx_audit_history/`.

---

## Wave B — Research overview: add MBR header

`docs/evaluation/for_orchard_research_overview.md` (319 lines) was explicitly skipped in R1 because another agent was editing the deck in parallel. It is now stable. Content is a full peer-review of the For Orchard deck — genuinely useful as a research record.

**Action:** Add a 3-line header block after the front matter:

```
> **Numbers verified against:** MBR-default canonicals (`after_amosi_audit.md`).
> Deck reviewed at 89 slides; current deck is 88 slides (1 slide removed post-review).
> Review conclusions remain valid — no structural changes since this review.
```

No other changes needed. The review's A/B/C/D/E issue list was executed in commits `2698586` + `67bd993`.

---

## Wave C — Mission backlog: update headline numbers

`docs/backlog/mission-backlog.md` header still quotes:
- WER 64.1% — correct (top-1 baseline, keep but add MBR alongside)
- IS 2.53 → should be 2.547 (MBR) / 2.532 (top-1)
- Captured 40.1% → deprecated threshold; replace with NIV-Y+P 61.9% (MBR)
- Salvage 51.1% → legacy framing; replace with "NIV-Y+P + LLM salvage 62.3% (MBR)"
- WWER 60.5% — unchanged, correct

**Action:** Update 4 values in the header paragraph, add a 1-line MBR note.

---

## Post-sync invariants (same as R1)

1. IS mean: "2.547" (MBR) or "2.532" (top-1, labeled)
2. NIV-Y: "358/1,497 (23.9%)" (MBR) or "359" (top-1, labeled)
3. NIV-Y+P: "927/1,497 (61.9%)" (MBR) or "923" (top-1, labeled)
4. WER: "63.8%" (MBR) or "64.1%" (top-1, labeled)
5. No file in `docs/` (outside `_archive/`) should say "IS 2.52" or "Captured 40.1%" without a deprecation note
6. `pptx_text_render_audit.json` stays at `docs/evaluation/` (not archived)

---

## What to skip

- **`docs/tuning/experiments/exp_*/`** — decode_output subdirs still present (R1 Wave 2 removed them per the git diff, but the diff was relative to 9ca0011 not a1f40b6; verify with `ls` before touching)
- **`docs/finetuning/plots/`** — same caveat; verify actual disk state
- **Generator source (`docs/_research-tools/generators/`)** — changed for deck work, not docs cleanup scope
- **`docs/paper/presentation-remarks-log.md`** — already updated today

---

## Executor instructions

Run as a single-wave commit. Use `git mv` for archive moves (preserves history). Commit message: `docs sync round 2: archive For Orchard audit ephemera + update stale numbers in backlog`.

Rollback: `git revert HEAD`.
