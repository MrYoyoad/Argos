# Code-only Updates — Air-gapped VSP Image

Internal guide for shipping small code patches to an already-deployed client without re-transferring the full 40 GB image. Audience: Yoad.

## When to use this flow

- Small `lib/*.sh` fix
- Single Python script change in `VSP-LLM/scripts/`
- Hot-fix to `run_flat_english_pipeline.sh`
- Tweaks to `make_report.py` (palette, columns, layout)

When NOT to use:

- Anything that changes the venv (new Python deps, version bumps) — needs full rebuild
- Anything that changes the model weights, k-means baseline, face detection models — full rebuild
- Anything in the base CUDA / system layer

## Build the patch

The patch is a thin Docker image layered FROM the current build, with just the changed files COPYed in:

```bash
cd /home/ubuntu/vsp_docker
PREV_TAG="client-build-001"
NEW_BUILD="client-build-002"

# 1. Edit the files in galaxy_export/lib/, run_flat_english_pipeline.sh, etc.
#    (Or rsync from /home/ubuntu/lib/ if you've fixed things on EC2.)

# 2. Write a tiny patch Dockerfile:
cat > Dockerfile.patch <<EOF
FROM vsp-llm-pipeline:${PREV_TAG}
COPY galaxy_export/lib /workspace/lib
COPY galaxy_export/run_flat_english_pipeline.sh /workspace/
# Add other COPYs if other files changed (e.g. VSP-LLM/scripts/make_report.py)
EOF

# 3. Build the layer (a few seconds — tiny diff):
docker build -t "vsp-llm-pipeline:${NEW_BUILD}" -f Dockerfile.patch .

# 4. Smoke-test on EC2 before shipping:
docker run --rm "vsp-llm-pipeline:${NEW_BUILD}" bash /workspace/lib/test_all_modules.sh

# 5. Save the patched image:
docker save "vsp-llm-pipeline:${NEW_BUILD}" | zstd -19 -T0 > "vsp-image-${NEW_BUILD}.tar.zst"
sha256sum "vsp-image-${NEW_BUILD}.tar.zst" > "vsp-image-${NEW_BUILD}.tar.zst.sha256"

# Patch tarballs are typically a few MB to ~100 MB depending on what changed.
ls -lh vsp-image-${NEW_BUILD}.tar.zst
```

## Package the kit-update directory

```bash
mkdir -p kit-update-${NEW_BUILD}
cp vsp-image-${NEW_BUILD}.tar.zst         kit-update-${NEW_BUILD}/
cp vsp-image-${NEW_BUILD}.tar.zst.sha256  kit-update-${NEW_BUILD}/
cp launcher/apply_update.sh               kit-update-${NEW_BUILD}/
cp launcher/rollback.sh                   kit-update-${NEW_BUILD}/
cat > kit-update-${NEW_BUILD}/README.txt <<EOF
VSP Pipeline — Patch ${NEW_BUILD}

Apply with:
  sudo ./apply_update.sh vsp-image-${NEW_BUILD}.tar.zst vsp-llm-pipeline:${NEW_BUILD}

Rollback with:
  sudo ./rollback.sh

What changed:
  <one-paragraph description>

Compatibility:
  Requires base build vsp-llm-pipeline:${PREV_TAG} or later.
EOF

# Bundle for transfer
tar -czf kit-update-${NEW_BUILD}.tar.gz kit-update-${NEW_BUILD}/
```

## Transfer + apply

Same exfil path as the full build — S3 → laptop → USB. The patch is small (typically < 100 MB) so transfer is fast.

On the client:

```bash
tar -xzf kit-update-client-build-002.tar.gz
cd kit-update-client-build-002
sudo ./apply_update.sh vsp-image-client-build-002.tar.zst vsp-llm-pipeline:client-build-002
```

`apply_update.sh` does atomic ordering:

1. Verify the tarball (zstd integrity + SHA256).
2. `docker load`.
3. Run `lib/test_all_modules.sh` inside the new image.
4. Atomically rewrite `/opt/vsp/launcher/image.tag`. Save the previous tag at `image.tag.previous`.
5. Keep the previous image on disk for fast rollback.

If any step fails, `image.tag` stays pointing at the old tag — the launcher keeps working on the old build, no broken intermediate state.

## Rollback

```bash
sudo /opt/vsp/launcher/rollback.sh
```

This flips `image.tag` back to whatever was in `image.tag.previous`. Requires the previous image to still be loaded in Docker (it is, by default — `apply_update.sh` doesn't auto-`docker rmi` it). If the operator manually ran `docker rmi`, they'll need to re-load from a kit tarball before rollback.

## Tag scheme

Use sequential build IDs, not dates: `client-build-001`, `client-build-002`, `client-build-003`. Reasons:

- Date-based tags lie when a build slips into the next day.
- Sequential is easier to compare visually ("are we on 002 or 008?").
- The exact build date is in the commit log + the tarball filename, not the tag.

## Checklist when preparing a patch

- [ ] Bumped `BUILD_ID` (`002`, `003`, ...)
- [ ] All changed files are COPY'd in `Dockerfile.patch`
- [ ] `lib/test_all_modules.sh` smoke passes inside the new image
- [ ] If the patch touches `make_report.py`, decode end-to-end on a sample and visually inspect the report
- [ ] Wrote `README.txt` describing what changed and why
- [ ] Bundled with `apply_update.sh` + `rollback.sh` (the kit version is what gets shipped, not whatever's in /opt at the client)
- [ ] SHA256 sidecar present
- [ ] kit-update-*.tar.gz size sanity-checked (small means just the changes; if it's > 1 GB something is wrong)
