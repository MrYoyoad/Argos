# Deployment Targets — `galaxy_export` vs `vsp_linux_container_FINAL_*`

Three locations look like "the deployment artifact" and they have **different roles**. Pick the wrong one to sync changes to and either new clients or existing clients miss the update.

## The three locations

| Path | Role | Audience | Update cadence |
|------|------|----------|----------------|
| `/home/ubuntu/` (EC2) | **Source of truth** — development, testing, experimentation | The team | Every commit |
| `vsp_docker/galaxy_export/` | **Full source bundle for `docker build`** | New clients (clean install) | Per release |
| `vsp_linux_container_FINAL_<date>/` | **Patch overlay for an already-running container** | Existing clients (incremental update) | Per release |

The two deploy locations are **complementary, not redundant**. They serve disjoint client populations.

## `vsp_docker/galaxy_export/` — Docker build context

This is what gets baked into a fresh Docker image.

- `vsp_docker/Dockerfile` does literally `COPY galaxy_export/ ./` into `/workspace`. Whatever sits in `galaxy_export/` becomes the running container's filesystem on first boot.
- It is a **complete self-contained bundle**: all source (lib/, vsp-ui/, VSP-LLM/, auto_avsr/, av_hubert/), all docs, **the offline pip wheels** (`offline_requirments.txt`, `spacy_wheels/`), the venvs setup, model caches (`whisper_cache/`, `is_model_cache/`), the desktop icon files. Big.
- Submodules (VSP-LLM/auto_avsr/av_hubert) are pinned to specific commits so the Docker build is reproducible.
- Built once and shipped (or rebuilt and re-shipped) when major releases happen.
- **Audience: new clients.** Anyone provisioning a fresh container from scratch gets exactly what `galaxy_export/` contains.

## `vsp_linux_container_FINAL_<date>/` — Patch overlay

This is **NOT a deploy artifact in the same sense.** It is a small, dated **diff package** that updates an already-deployed container.

- README explicitly says "What's NOT Included: Fairseq framework — already installed in container" and "Virtual environments — created during installation". ~3 MB total.
- Ships `INSTALL.sh` that copies its files into an already-running `/workspace`, alongside what's already there. Includes change-history docs (`bugs-1-to-13-installation.md`, etc.).
- Date in the directory name is the snapshot date of that bug-fix bundle.
- **Audience: existing clients.** The Docker image they have was built months ago with an older `galaxy_export/` snapshot. The overlay tarball is how we push fixes without forcing them to rebuild the image.

## Why both exist

The choice is roughly: **"would you make a new client wait for a 100 GB Docker rebuild and image transfer to fix a 1-line bug?"** No. The overlay path exists because incremental updates are 1000× cheaper to ship than full image rebuilds. New clients still get the latest because every release rolls back into `galaxy_export/`.

## Current operational practice (May 2026)

**Overlay is the primary deployment path. `galaxy_export/` is stale and is intentionally NOT updated on every change.** That is the actual practice as of May 2026, even though both paths technically exist.

Reasoning: the overlay (`vsp_linux_container_FINAL_<date>/`) ships with `INSTALL.sh` which is what every client install (existing or new) actually runs after extracting whatever Docker image they happen to have. Touching `galaxy_export/` introduces small but real risks (see Docker rebuild checklist below) that aren't worth taking on every feature merge — they're worth taking once, deliberately, when the next Docker image is being built.

So when code lands on EC2:

1. **Develop on EC2** — edit `lib/`, `VSP-LLM/...`, `docs/_research-tools/...`.
2. **Sync to the overlay** (`vsp_linux_container_FINAL_<date>/`) — copy the changed files in.
3. **Append a change-log entry** to [docs/container-sync-changelog.md](../container-sync-changelog.md).
4. **Verify with `cmp`** that EC2 and overlay are byte-identical.
5. **Skip `galaxy_export/`** — leave it alone until the next Docker image rebuild event (see below).

This means new clients who provision a fresh Docker image get a *slightly older* container than the latest overlay. They run `INSTALL.sh` from the latest overlay tarball after extraction to bring themselves current — same procedure existing clients use to update.

## When you ARE rebuilding the Docker image — careful checklist

This section is what to do when someone says "OK, time to ship a new Docker image to clients." It batches up everything that's been deferred and validates the build before it leaves the building.

**0. Snapshot first**

```bash
# Snapshot the current galaxy_export state in case a step fails and you need to roll back
cp -r vsp_docker/galaxy_export vsp_docker/galaxy_export.PRE_REBUILD_$(date +%Y%m%d)
```

**1. Sync deferred features into galaxy_export**

Run a sync script (or do it by hand from a written list). You'll need to copy across at minimum:

- `lib/*.sh` — all bash modules (decode.sh, outputs.sh, etc. are commonly modified)
- `lib/nbest_aggregate.py` (Mission 6) — copies to `galaxy_export/VSP-LLM/scripts/nbest_aggregate.py` per container convention
- Any new `docs/_research-tools/generators/*.py` we own — copies to `galaxy_export/VSP-LLM/scripts/`
- `docs/_research-tools/calibration/calibration.json` — the shipped default temperatures
- `VSP-LLM/src/vsp_llm.py`, `VSP-LLM/src/vsp_llm_decode.py`, `VSP-LLM/scripts/make_report.py` — copy directly into `galaxy_export/VSP-LLM/...` (overrides the submodule's pinned content via file edit; this is the long-standing convention because galaxy_export's VSP-LLM submodule tracks upstream `Sally-SH/VSP-LLM`, not our fork — see "Submodule remote divergence" below)
- Any other files touched in `docs/container-sync-changelog.md` since the last image was built

Verify with `cmp` after each copy. Fail loudly if any mismatch.

**2. Check venv compatibility**

The Dockerfile installs two venvs (`pre-process-venv`, `vsp-llm-yoad-venv`) with EXACT pinned package lists. New code may have new dependencies that aren't pinned.

Audit any new file you copied for `import` statements. The current pinned dependencies you can rely on:

- numpy, pandas, matplotlib, editdistance, sentence-transformers, metaphone, spacy
- torch (cu128), transformers, peft, fairseq, hydra, omegaconf, einops

If a script imports anything outside that set (Mission 6 example: `calibrate_temperature.py` uses **scipy** — verify it's in the freeze, or pin it explicitly):

```bash
grep "^scipy" vsp_docker/Dockerfile
# If missing, add `scipy==<version>` to the venv install block in the Dockerfile.
```

**3. Test the actual `docker build`**

This is the step most likely to surface problems. Don't skip it.

```bash
cd vsp_docker
docker build -t vsp-test:rebuild-$(date +%Y%m%d) . 2>&1 | tee build.log

# Look for: COPY/RUN failures, pip install errors, missing files.
# Successful build = all venvs install + COPY galaxy_export/ landed cleanly.
```

If the build fails on a missing dependency, fix the Dockerfile (don't paper over by `pip install` on the running container — that won't survive image rebuilds).

**4. Smoke-test the built image**

```bash
docker run --rm -it --gpus all vsp-test:rebuild-<date> bash -lc '
  cd /workspace
  bash lib/test_all_modules.sh                                           # 37 module tests
  source vsp-llm-yoad-venv/bin/activate
  python -c "import sys; sys.path.insert(0, \"VSP-LLM/scripts\"); import nbest_aggregate; print(\"nbest_aggregate OK\")"
  python -c "import scipy; print(scipy.__version__)"                     # if scipy was added
'
```

A failure here means the new code is in the image but the runtime can't actually exercise it.

**5. Build a fresh dated overlay snapshot**

After the new Docker image ships, the overlay's purpose resets — it becomes "the diff from THIS image's contents". Generate a new dated overlay folder (e.g., `vsp_linux_container_FINAL_<new-date>/`) populated with whatever's currently in EC2. Old dated overlay folders can stay as historical references.

**6. Update `docs/container-sync-changelog.md`**

Mark all entries since the last rebuild as "shipped in image <date>". Future entries start fresh against the new baseline.

**7. Update `CLAUDE.md`** if the active overlay folder name changed.

## Submodule remote divergence (pre-existing — explanation, not a fix)

`galaxy_export/VSP-LLM/` tracks `https://github.com/Sally-SH/VSP-LLM.git` (upstream). The EC2 fork tracks `https://github.com/MrYoyoad/VSP-LLM.git` (our fork). This means: even if you update the submodule pointer in `galaxy_export/VSP-LLM/`, fetching from `Sally-SH` won't pull our commits.

Two paths forward (out of scope for any single feature, but worth noting):

- **Re-point galaxy_export's VSP-LLM submodule to the fork** (`MrYoyoad/VSP-LLM`). Then submodule pointers become meaningful and the file-copy workaround can stop. Requires updating `vsp_docker/galaxy_export/.gitmodules` and pushing the fork's history.
- **Stop tracking VSP-LLM as a submodule in galaxy_export** — make it a regular subtree. File-level edits become the only mechanism, no submodule pointer drift.

Until that's resolved, the file-copy override pattern is the only mechanism that actually works for `VSP-LLM/src/*.py` changes reaching `galaxy_export/`.

## Why we're NOT automating galaxy_export sync today

Earlier draft of this doc proposed `scripts/build/sync_deploy_targets.sh` to mirror EC2 → both targets. **Abandoned for now** because:

- It implies running on every commit, which would touch galaxy_export on every commit — and we don't want to mutate galaxy_export without validating the resulting Docker build.
- Building + smoke-testing the Docker image takes ~hours, can't be a per-commit step.
- An untested galaxy_export accumulating "live" updates is worse than a stale one — at least with stale you know the last known-good state.

Right tool: a **release-time** procedure (the checklist above), not a per-commit hook. The checklist *is* the automation; it just runs once per planned image rebuild instead of once per commit.

## Submodule remote divergence (pre-existing)

`galaxy_export/VSP-LLM/` tracks `https://github.com/Sally-SH/VSP-LLM.git` (upstream). The EC2 fork tracks `https://github.com/MrYoyoad/VSP-LLM.git` (our fork). This means: even if you update the submodule pointer in `galaxy_export/VSP-LLM/`, fetching from `Sally-SH` won't pull our commits.

Two paths forward (out of scope for any single feature, but worth noting):

- **Re-point galaxy_export's VSP-LLM submodule to the fork** (`MrYoyoad/VSP-LLM`). Then submodule pointers become meaningful and the file-copy workaround can stop. Requires updating `vsp_docker/galaxy_export/.gitmodules` and pushing the fork's history.
- **Stop tracking VSP-LLM as a submodule in galaxy_export** — make it a regular subtree. File-level edits become the only mechanism, no submodule pointer drift.

Until that's resolved, the file-copy override pattern is the only mechanism that actually works for `VSP-LLM/src/*.py` changes reaching `galaxy_export/`.
