# Updating the Original Client (Feb-2026 Docker) — May 2026 Refresh

This guide updates the **original client's standalone** (the one running the
Feb 2026 Docker image `vsp-llm-pipeline:latest` ~v1.0.32-35) with everything
that landed on the EC2 dev environment since then, **without rebuilding the
Docker image**. Code, scripts, wheels, and the HuggingFace model cache are
laid down on top of the existing image via the overlay's `INSTALL.sh`.

> **Audience:** the operator who is physically at the client machine with a
> USB stick or SCP path. Internet on the client is NOT required.

---

## What this update adds

| Feature | Status before | Status after |
|---|---|---|
| All 12 critical Feb-2026 fixes (NVENC, Cython, transcriptions, segment naming, …) | partly missing | installed + verified |
| **Per-token confidence coloring** (Mission 4) — blue/orange/purple `Confidence:` line in `report.html`, `sentence_confidence` column in `report.csv` | not present | installed |
| **Intelligibility Score (IS)** — `is_score`, `is_tier`, `niv` columns; tier badges in burned videos | not present | installed (offline) |
| **N-best aggregation + MBR-default display** (Mission 6) — `aggregated.json`, `hyp_mbr` becomes the displayed transcript | not present | installed (set `VSP_NBEST=1` at decode) |
| **Agreement-aware band coloring** — green = `top1_conf ≥ 0.95 AND beam_agreement ≥ 0.80` | not present | installed |
| **Desktop icon fixed** — no more "No terminal emulator found" error | broken | fixed (headless launcher) |

---

## What is in this overlay package

```
vsp_linux_container_FINAL_20260217/
├── INSTALL.sh                          # Run this — applies everything.
├── VERIFY.sh                           # 22-fix smoke test. Run after INSTALL.
├── UPDATE_GUIDE_MAY2026.md             # This file.
├── UPDATE_MANIFEST_MAY2026.md          # Authoritative file-by-file diff list.
├── COMPLETE_CHANGELOG.md               # Bug-by-bug history.
├── BUGS_INSTALLING_CLIENT_STANDALONE.md
│
├── lib/                                # 11 pipeline modules (same as EC2)
│   ├── outputs.sh                      # ← Confidence + IS + N-best + HF env vars
│   ├── decode.sh                       # ← Cython auto-build
│   ├── normalization.sh                # ← NVENC silent-corruption fix
│   ├── asr.sh                          # ← raw_dir/.transcriptions (container-safe)
│   └── …
│
├── VSP-LLM/
│   ├── src/                            # Llama-2 patches (vsp_llm.py, vsp_llm_decode.py)
│   └── scripts/
│       ├── compute_word_confidence.py  # ← Mission 4
│       ├── compute_word_agreement.py   # ← Joint conf+agreement bands
│       ├── nbest_aggregate.py          # ← Mission 6 (MBR/vote/score)
│       ├── generate_intelligibility_scores.py
│       ├── analyze_beam_variance.py
│       ├── _alignment.py
│       ├── calibration.json            # default temperatures
│       ├── calibrate_temperature.py
│       ├── make_report.py              # NIV column + confidence wiring
│       ├── make_burn.py                # tier-badge overlay
│       └── decode.sh                   # ← Fairseq GenerationConfig monkey-patch
│
├── vsp-ui/                             # Headless-safe UI launcher
├── auto_avsr/                          # preparation/ + face detectors
├── av_hubert/                          # LRS3 prep
│
├── vsp-start.sh                        # ← Headless docker launcher (zenity progress)
├── vsp-pipeline.desktop                # ← Terminal=false
├── install-desktop-icon.sh             # ← Verifies notifier instead of terminal
│
├── is_wheels_cp310/                    # ← NEW — 95 MB cp310 wheels for IS / confidence
│   ├── sentence_transformers-5.1.2-py3-none-any.whl
│   ├── Metaphone-0.6.tar.gz
│   ├── doublemetaphone-1.2-cp310-…whl
│   ├── matplotlib-3.9.4-cp310-…whl
│   ├── scipy-1.13.1-cp310-…whl
│   ├── editdistance-0.8.1-cp310-…whl
│   └── transitive deps (37 wheels total)
│
├── is_model_cache/                     # ← NEW — 88 MB HuggingFace MiniLM snapshot
│   └── hub/models--sentence-transformers--all-MiniLM-L6-v2/
│
└── spacy_wheels/                       # Existing — spaCy entity-metrics wheels
```

---

## Persistence model (READ THIS FIRST)

A docker container is *ephemeral by default*. `docker run --rm` deletes the
container's filesystem on exit, including any `pip install` we did inside it
and any in-place edits (the fairseq `GenerationConfig` patch).

Things that **persist** on their own (because they land on a host mount):

- `lib/*.sh`, `VSP-LLM/scripts/*.py`, `vsp-ui/*` — live in `~/Desktop/galaxy_export/`.
- The HF MiniLM model cache — copied to `~/Desktop/galaxy_export/is_model_cache/`.
- `vsp-start.sh`, `vsp-pipeline.desktop`, `docker.conf`, `install-desktop-icon.sh`.

Things that **do NOT persist** without help — these live inside the container:

- IS / confidence pip wheels (sentence-transformers, Metaphone, doublemetaphone, matplotlib, scipy, editdistance).
- The fairseq `GenerationConfig` patch (Component [3.10]).

`apply_update.sh` wraps INSTALL.sh in a **`docker commit`** flow: it runs
INSTALL.sh inside a named container, snapshots that container into a *new
image tag* (`vsp-llm-pipeline:may2026-update`), updates `docker.conf` to point
at the new tag, and removes the temp container. The new tag is durable — the
client can power off, the docker daemon can restart, and the wheels / patch
remain baked in.

Rollback is one command (`rollback_update.sh`) — it restores the previous
`docker.conf` from a backup. The old image is never deleted, so flipping back
is instant.

---

## Step-by-step runbook

### 1. Transfer the overlay to the client machine

On EC2 (or wherever this overlay was built):

```bash
cd /home/ubuntu
tar czf vsp_linux_container_FINAL_20260217.tar.gz vsp_linux_container_FINAL_20260217/
sha256sum vsp_linux_container_FINAL_20260217.tar.gz > vsp_linux_container_FINAL_20260217.sha256
```

Move both files to a USB stick (or `scp` to the client).

### 2. On the client — verify the tarball, extract

```bash
cd /home/ds/Desktop/                     # or wherever the client keeps install kits
sha256sum -c vsp_linux_container_FINAL_20260217.sha256       # MUST print "OK"
tar xzf vsp_linux_container_FINAL_20260217.tar.gz
```

### 3. Stop any running pipeline container

```bash
docker stop vsp-pipeline 2>/dev/null
```

### 4. Run **apply_update.sh** from the host (this is the only install command you type)

```bash
cd /home/ds/Desktop/vsp_linux_container_FINAL_20260217
bash apply_update.sh
```

What `apply_update.sh` does (3 stages, all automated):

1. **Stage 1**: `docker run --name vsp-install-tmp` (no `--rm`) and runs INSTALL.sh inside it.
   INSTALL.sh copies code to `/host/galaxy_export/`, pip-installs IS wheels into the venv,
   patches fairseq, copies the HF model cache, and runs the 22-check VERIFY pass.
2. **Stage 2**: `docker commit vsp-install-tmp vsp-llm-pipeline:may2026-update` —
   snapshots the container's state into a new image tag. `docker rm` the temp container.
3. **Stage 3**: rewrites `~/Desktop/galaxy_export/docker.conf` to `DOCKER_IMAGE=vsp-llm-pipeline:may2026-update`.
   The old `docker.conf` is saved as `docker.conf.before-may2026`.

Then `apply_update.sh` runs a final smoke-test: `docker run --rm <new-tag>` and
imports `sentence_transformers, metaphone, matplotlib, scipy, editdistance`. If the
imports succeed, the wheels are baked into the new image.

Final output should be:

```
════════════════════════════════════════════════════════════
  ✅ Update applied and persisted
════════════════════════════════════════════════════════════
  Source image  : vsp-llm-pipeline:latest
  New image     : vsp-llm-pipeline:may2026-update
  Active config : DOCKER_IMAGE=vsp-llm-pipeline:may2026-update  (in docker.conf)
```

If any stage prints `❌` or exits non-zero, **stop and read the error**.
Common failure modes:

| Error                                                     | Cause / fix |
|---|---|
| `Source image '…' not found locally`                     | Check `docker images` and pass `OLD_TAG=<your_actual_tag> bash apply_update.sh`. |
| `Fix 22: IS deps importable` ❌ inside INSTALL.sh        | venv `pip install` failed. The temp container will be discarded; no commit happens. Inspect `/tmp/_vsp_is_check` from the temp container by re-running without commit: `docker run --rm … bash`. |
| `[3.10] Fairseq max_len patch failed`                    | `vsp-llm-yoad-venv` is at an unexpected path. Set `PATCH_VENV=/path/to/venv` and re-run. |
| `Smoke-test FAILED. The committed image is missing …`    | The commit happened but the venv is broken. Run `rollback_update.sh` and report the failure. |

### 5. From the host — install the desktop icon

```bash
cd /home/ds/Desktop/galaxy_export
bash install-desktop-icon.sh
```

This now uses `Terminal=false` and verifies a **notifier** (zenity / notify-send),
not a terminal emulator. Even if no notifier is found, the launcher will still
work; it just won't show a progress dialog.

### 6. Smoke-test the icon

Double-click "VSP Pipeline" on the Desktop. Expect:

1. A zenity "Starting…" progress bar fills 0→100% over ~30–60 s.
2. Browser auto-opens at `http://localhost:8765`.
3. UI shows the VSP web app.

If the icon fails silently, check `~/.vsp-pipeline.log` — that's where
the headless launcher streams the container's stdout/stderr.

### 7. Smoke-test the pipeline (5 minutes)

Drop one short MP4 (~10 s) in `vsp_input/`, run from the UI, and verify the
output report:

```bash
cd /home/ds/Desktop/galaxy_export
ls flat_runs_archive/*/client_outputs/report/
# Expect:
#   report.html           — Confidence: line should be present (blue/orange/purple)
#   report.csv            — columns sentence_confidence, is_score, is_tier, niv
#   aggregated.json       — present iff VSP_NBEST=1 was set
#   intelligibility_scores.csv  — IS per segment
```

Read one of the HTML reports: under the segment's accuracy line you should
see a coloured `Confidence:` line. That's the per-token confidence feature.
If you set `VSP_NBEST=1` before launching the pipeline, the **displayed
transcript itself** is the MBR consensus (Mission 6 default).

---

## Per-feature acceptance checklist

After running a real test video:

- [ ] **Per-token confidence**: `report.csv` has `sentence_confidence`. `report.html` shows `Confidence:` line with coloured words.
- [ ] **Intelligibility Score**: `report.csv` has `is_score`, `is_tier`, `is_label`, `niv`. Tier 5/4/3/2/1 distribution looks reasonable.
- [ ] **N-best / MBR display**: `aggregated.json` exists with key `hyp_mbr`. Burned video subtitle text matches `hyp_mbr`, not `hyp_top1`.
- [ ] **Agreement-aware bands**: `agreement-*.json` exists; HTML `Confidence:` line shows agreement-flagged words in green only when `top1_conf ≥ 0.95 AND beam_agreement ≥ 0.80`.
- [ ] **Desktop icon**: double-click works without "No terminal emulator found".

If any of these fail, run `bash VERIFY.sh` from inside the container — it'll
tell you which fix is missing.

---

## Rollback

**One command** (preferred):

```bash
cd ~/Desktop/vsp_linux_container_FINAL_20260217
bash rollback_update.sh
```

This restores `docker.conf` from the backup `apply_update.sh` made
(`docker.conf.before-may2026`) so `DOCKER_IMAGE` points at the previous tag
(e.g. `vsp-llm-pipeline:latest`) again. Next pipeline launch uses the old image
— the new image stays on disk, so flipping back is one more `apply_update.sh`.

To also delete the new image:

```bash
bash rollback_update.sh --purge
```

**File-level rollback** (for `lib/*.sh` and other host-side files):

`INSTALL.sh` snapshots `galaxy_export` before writing changes:

```bash
cd /home/ds/Desktop/
tar xzf galaxy_export_backup_YYYYMMDD_HHMMSS.tar.gz
```

---

## Known issues / non-issues

| | |
|---|---|
| **`numpy` is NOT in `is_wheels_cp310/`** | Intentional. The existing venv has numpy 1.x; bundling numpy 2.x would risk an ABI break. If `import numpy` fails after install, the venv is broken in a way that pre-dates this update. |
| **`transformers` 4.57.6 is in `is_wheels_cp310/`** | Bundled because `sentence-transformers 5.1.2` needs `transformers >= 4.41`. `--upgrade-strategy=only-if-needed` leaves the existing version alone if it's already ≥ 4.41. |
| **Headless launcher requires zenity for progress UI** | If zenity isn't installed, the launcher still works — just silently waits. The browser still auto-opens when the server is ready. |
| **`~/.vsp-pipeline.log` grows over time** | Truncated to empty on each launch. No rotation needed. |
| **Confidence/agreement bands are Llama-2 calibrated** | Thresholds (0.95 / 0.80 green, 0.65 / 0.50 yellow) were diagnosed against Llama-2-7b-hf. If the LLM is ever swapped, re-run `diagnose_confidence_signals.py`. |

---

## Reference

- **Build date**: 2026-05-12
- **Source**: `/home/ubuntu/` EC2 (commit `abb2167` "argos v13: dual-mode generator").
- **Target image**: `vsp-llm-pipeline:latest` (Feb-2026 build).
- **Target Python**: 3.10 (cp310 wheels).
- **Tarball size**: ~200 MB (Feb baseline ~40 MB + IS wheels 95 MB + HF cache 88 MB).
