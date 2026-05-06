# VSP Pipeline — Client Installation Guide

This guide walks through a clean install on an air-gapped (no-internet) machine with an NVIDIA GPU.

## What you should have

The kit USB / SSD should contain:

- `vsp-image-<build-id>.tar.zst` (or split into `.part_aa`, `.part_ab`, ...)  — the Docker image, ~35-45 GB
- `vsp-image-<build-id>.tar.zst.sha256` — checksum file
- `offline_kit_<distro>/` — Docker engine + NVIDIA Container Toolkit installer
- `checks/` — pre/post install verification scripts
- `launcher/` — desktop launcher + shortcut + apply_update.sh
- `samples/` — two short test videos (`smoke_12s.mp4`, `smoke_75s.mp4`)
- `CLIENT_INSTALL.md` (this file)
- `client-troubleshooting.md` — symptom → fix table

Total kit size on disk: ~40-50 GB. Use a USB 3 SSD, not a thumb drive.

## Hardware requirements

| Component | Required | Recommended |
|---|---|---|
| GPU | NVIDIA, compute capability ≥ 7.0 (Volta or newer) | T4 / V100 / A100 / RTX 30xx+ |
| GPU VRAM | 12 GB | 16+ GB |
| NVIDIA Driver | 525.x or newer | latest stable |
| RAM | 16 GB (host) | 32 GB+ |
| CPU | 4 cores | 8+ cores |
| Disk free (Docker storage, e.g. `/var/lib/docker`) | 150 GB | 200+ GB |
| Disk free (output partition, e.g. `$HOME/vsp-output/`) | 20 GB | 100+ GB |
| Internet | Not required after initial install — pipeline runs fully offline | — |

If the GPU has compute capability below 7.0 (Maxwell or Pascal), the pipeline will load but be unacceptably slow. Volta+ is the practical floor.

---

## Step 1 — Reassemble the image (if split)

If the image was split into parts on the USB, reassemble it first:

```bash
cat vsp-image-<build-id>.tar.zst.part_* > vsp-image-<build-id>.tar.zst
sha256sum -c vsp-image-<build-id>.tar.zst.sha256   # should print "OK"
```

If the SHA256 fails, the file is corrupt — re-copy from the USB.

## Step 2 — Install Docker + NVIDIA Container Toolkit (offline)

The `offline_kit_<distro>/` directory contains everything needed. Open a terminal in that directory and run:

```bash
sudo ./install.sh
```

This installs Docker engine, runc, and the NVIDIA Container Toolkit from the bundled `.deb` / `.pkg` files — no internet required. It also configures the Docker daemon to use the NVIDIA runtime and starts the daemon.

Verify by running:

```bash
docker info
nvidia-smi
docker run --rm --gpus all <kit-image-tag-for-toolkit-test> nvidia-smi
```

The third command must print the GPU info from inside a container. If it doesn't, the NVIDIA Container Toolkit isn't wired up — see `client-troubleshooting.md`.

## Step 3 — Pre-install host check

```bash
cd checks/
./pre_install_check.sh ../vsp-image-<build-id>.tar.zst
```

This validates the host one final time (driver version, GPU compute capability, VRAM, RAM, disk free, Docker daemon, NVIDIA Container Toolkit, image tarball SHA256). It writes to `pre_install_check.log` and prints a clear PASS / FAIL summary.

If it FAILS, fix the items listed before continuing. Don't skip checks.

## Step 4 — Load the image

```bash
zstd -d ../vsp-image-<build-id>.tar.zst -o ../vsp-image-<build-id>.tar
docker load -i ../vsp-image-<build-id>.tar
```

This takes 15-30 minutes on a typical SSD because Docker writes ~75 GB of image layers. Be patient. When it returns, verify:

```bash
docker images vsp-llm-pipeline
```

You should see one image with a tag like `client-build-001`.

## Step 5 — Install the launcher + desktop shortcut

```bash
cd ../launcher/
sudo ./install_launcher.sh
```

This places the launcher under `/opt/vsp/launcher/` (system-wide) and drops a desktop shortcut on the current user's Desktop. The shortcut is "VSP Pipeline".

It also writes `/opt/vsp/launcher/image.tag` — the single source of truth for which image tag the launcher invokes. Future code-only updates change just this file (see `code-only-update.md`); the launcher itself stays put.

## Step 6 — Post-install verification

```bash
cd ../checks/
./post_install_check.sh
```

This runs both curated samples through the full pipeline and confirms feature parity (n-best aggregation produced 5 hypothesis methods, MBR is the displayed hypothesis, IS scoring ran, NIV labels appear, the new confidence palette is in `report.html`, k-means model was saved, burned video has duration). It takes ~5-10 minutes.

When it finishes you'll get `INSTALL_REPORT.txt` summarizing PASS/FAIL. If anything fails, run `./collect_diagnostics.sh` and send the resulting tarball to support.

## Step 7 — Use the pipeline

Double-click "VSP Pipeline" on the Desktop. A folder picker appears — pick the folder containing the videos to process. A terminal opens and the pipeline runs.

When it finishes, the outputs land in `$HOME/vsp-output/<timestamp>/`:

- `report.html` — open in any browser; per-segment confidence-colored transcripts
- `report.csv` — raw data
- `intelligibility_scores.csv` — IS scores per segment
- `aggregated.json` — n-best hypothesis aggregation (MBR is the default displayed)
- `burned_videos/` — videos with subtitles burned in (if VSP_FULL_OUTPUTS=1)
- `*_kmeans_200.bin` — the trained k-means model from this run
- `pipeline.log`, `decode.log` — diagnostic logs

## Updating the pipeline (code-only patches)

When a small code patch arrives on USB (e.g. `kit-update-build-002/`):

```bash
cd kit-update-build-002/
sudo ./apply_update.sh vsp-image-build-002.tar.zst vsp-llm-pipeline:client-build-002
```

This loads the new image, smoke-tests it, and atomically swaps `image.tag` so the next launch uses the new build. The old image stays on disk for fast rollback. If anything misbehaves:

```bash
sudo /opt/vsp/launcher/rollback.sh
```

## When something goes wrong

1. Run `./checks/collect_diagnostics.sh` — produces a tarball with logs + state.
2. Check `client-troubleshooting.md` for the top-10 symptoms.
3. Send the diagnostics tarball to support via USB.

## Reinstalling cleanly (nuke and pave)

If the install ends up wedged:

```bash
docker rm -f vsp 2>/dev/null
docker rmi vsp-llm-pipeline:$(cat /opt/vsp/launcher/image.tag | cut -d: -f2) 2>/dev/null
docker load -i vsp-image-<build-id>.tar
echo "vsp-llm-pipeline:<build-id>" | sudo tee /opt/vsp/launcher/image.tag
```

Three commands. The launcher and desktop shortcut don't need touching — they read the tag from the file.

## Appendix — Expected timings (from staging dry-run)

| Step | Wall time |
|---|---|
| `offline_kit/install.sh` | ~5 min |
| `pre_install_check.sh` | <1 min |
| `docker load` (~75 GB image) | 15-30 min |
| `install_launcher.sh` | <1 min |
| `post_install_check.sh` (both samples) | 5-10 min |
| **Total fresh install** | **~30-45 min** |

Lock these numbers from the Layer-2 staging dry-run on the actual target hardware before shipping to the client.
