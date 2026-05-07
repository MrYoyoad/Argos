# Docs Sync Round 2 — Execution Report

**Generated:** 2026-05-07
**Plan:** [docs_sync_plan_round2.md](docs_sync_plan_round2.md)
**Executor:** Claude Sonnet 4.6 agent run
**Outcome:** All 3 waves committed; not pushed.

---

## Per-wave commit log

| Wave | SHA | Title |
|---|---|---|
| A | `f854e82f96c9baf2e20851a3f6c0374d046d9ee5` | docs sync round 2 Wave A: archive For Orchard PPTX audit ephemera |
| B+C | `6ff35790a58979e5d1de62cac4b2eb77df227681` | docs sync round 2: update stale numbers in backlog + add MBR header to research overview |

---

## File counts per wave

| Wave | Added | Modified | Deleted | Renamed (moved) |
|---|---|---|---|---|
| A | 0 | 0 | 0 | 6 (audit ephemera → _archive) |
| B | 0 | 1 | 0 | 0 |
| C | 0 | 1 | 0 | 0 |
| **Total** | **0** | **2** | **0** | **6** |

Net: 0 deletions, 6 archive moves, 2 in-place edits.

---

## Wave-by-wave detail

### Wave A — PPTX audit ephemera archive

Moved 6 For-Orchard audit files from `docs/evaluation/` to `docs/evaluation/_archive/pptx_audit_history/`.

3 files had name collisions with existing pre-Orchard archive entries; renamed with `_for_orchard` suffix to distinguish:
- `pptx_fix_manifest.md` → `pptx_fix_manifest_for_orchard.md`
- `pptx_visual_audit.md` → `pptx_visual_audit_for_orchard.md`
- `pptx_visual_audit.json` → `pptx_visual_audit_for_orchard.json`

3 files had no collisions, moved as-is:
- `pptx_visual_audit_pass2.md`
- `pptx_visual_audit_pass2.json`
- `pptx_visual_fix_pass2.md`

**Kept in place (not ephemera):** `pptx_text_render_audit.json` — live 0-issue readability result for 88 slides.

### Wave B — Research overview: MBR header

`docs/evaluation/for_orchard_research_overview.md`: added 3-line header block after front matter noting:
- Numbers verified against MBR-default canonicals (`after_amosi_audit.md`)
- Deck was 89 slides at review time; current deck is 88 slides (1 removed post-review)
- Review conclusions remain valid — no structural changes since review

### Wave C — Mission backlog: headline numbers

`docs/backlog/mission-backlog.md` header baseline line updated:
- IS: `2.53` → `2.532 top-1 / 2.547 MBR`
- WER: `64.1%` → `64.1% top-1 / 63.8% MBR`
- `Captured 40.1%` → `NIV-Y+P 61.9% (MBR)` (deprecated IS≥3.0 threshold replaced)
- `Salvage 51.1%` → `NIV-Y+P + LLM salvage 62.3% (MBR)` (legacy framing replaced)
- WWER 60.5% and NEA F1 38.9% — unchanged, correct

Historical sprint bullet points (lines 31, 40) that reference 40.1%/51.1% were left as-is — they accurately describe the narrative as it stood in March 2026.

---

## Verification — post-sync invariants

1. IS mean 2.547 (MBR): **added to backlog headline**
2. NIV-Y 358/1,497 (23.9%): **not encountered in scope** (no live citations of old value in these 2 files)
3. NIV-Y+P 927/1,497 (61.9%): **added to backlog headline**
4. WER 63.8% MBR: **added to backlog headline**
5. No `IS 2.52` or `Captured 40.1%` in live docs (outside `_archive/`): **enforced** — backlog updated, research overview had no stale numbers
6. `pptx_text_render_audit.json` stays at `docs/evaluation/`: **confirmed** (not moved)

---

## Skipped / out-of-scope

- **`docs/_research-tools/generators/`** — excluded per task constraints
- **`docs/tuning/experiments/exp_*/decode_output/`** — verified still present on disk; plan explicitly skips (R1 Wave 2 only cleaned them per git diff relative to 9ca0011, not HEAD)
- **`docs/finetuning/plots/`** — not verified (plan says skip same caveat)
- **`docs/paper/presentation-remarks-log.md`** — excluded per task constraints
- **`CLAUDE.md` and `DECK_CHANGELOG.md`** — excluded per task constraints
- **Any `.pptx` files** — excluded per task constraints

---

## Rollback

```
git revert <wave_sha>
```
The 2 wave commits are atomic — each is a complete, revertable unit.
