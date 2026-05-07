# Staging Dry-Run — Layer-2 Verification

Internal guide for the Layer-2 staging procedure: simulate the client environment on your own air-gapped box BEFORE shipping to the client. This is the load-bearing safety net — fixes bugs that build-time tests can't catch.

## Why Layer 2 matters

Layer 1 (build-time `lib/test_all_modules.sh`) catches code regressions but runs on the build box, not the deploy box. Layer 3 (client `pre/post_install_check.sh`) catches deploy bugs but runs at the client where you can't iterate. Layer 2 fills the gap: deploy-bug iteration on a machine YOU control.

Skip this and you'll hit two classes of bug at the client:

1. Things that only fail air-gapped (a wheel that lazy-downloads, a cache path that needs internet)
2. Things that only fail on the actual hardware (driver/CUDA/wheel mismatches, NVENC corruption)

## Prerequisites

- A spare machine with an NVIDIA GPU (compute_cap ≥ 7.0). Same OS family as the client if possible.
- The full kit on a USB SSD (image tarball + offline_kit + checks + launcher + samples + docs).
- Network DISABLED on the staging machine for the duration of the dry-run (`nmcli networking off` on Linux, or unplug Ethernet + disable Wi-Fi).

## Procedure

### 1. Verify the box starts fresh

```bash
# On the staging machine:
nmcli networking off                   # GO OFFLINE NOW

docker rm -f $(docker ps -aq) 2>/dev/null   # remove any leftover containers
docker rmi $(docker images -q vsp-llm-pipeline) 2>/dev/null   # remove any old VSP images
sudo rm -rf /opt/vsp                   # nuke previous launcher install
rm -rf ~/Desktop/VSP-Pipeline.desktop ~/Desktop/'VSP Pipeline.sh'
```

Confirm `nvidia-smi` works (GPU + driver are kit-independent — drivers are a host concern).

### 2. Walk the CLIENT_INSTALL.md procedure exactly

Open `CLIENT_INSTALL.md` and follow every step verbatim. Time each step with a stopwatch. Record:

- Time for `offline_kit/install.sh`
- Time for `pre_install_check.sh`
- Time for `docker load` (the slow step — ~75 GB image)
- Time for `install_launcher.sh`
- Time for `post_install_check.sh` (both samples)

Total wall time should land between 30-45 min on typical SSD-backed hardware. If it's longer, document why in CLIENT_INSTALL.md so the client knows what to expect.

### 3. Run pre_install_check + verify it passes

```bash
cd checks/
./pre_install_check.sh ../vsp-image-<build-id>.tar.zst
```

Should be all green PASS. If WARN appears (e.g. RAM 30 GiB on a borderline box), confirm the WARN is appropriate — not a real config problem.

For staging on a box you trust, you can use:

```bash
VSP_NONINTERACTIVE_PROCEED=1 ./pre_install_check.sh ../vsp-image-<build-id>.tar.zst
```

This skips the prompt-on-warning behavior. **Do not document this for the client** — production installs should always be interactive.

### 4. Run docker load + post_install_check

```bash
zstd -d ../vsp-image-<build-id>.tar.zst -o ../vsp-image-<build-id>.tar
docker load -i ../vsp-image-<build-id>.tar

cd ../launcher/
sudo ./install_launcher.sh

cd ../checks/
./post_install_check.sh
```

This is where most bugs appear. Watch for:

- `lib/test_all_modules.sh` failures inside the container (different from on the build box)
- "MediaPipe model file not found" — pre-warm at build time didn't take
- `metaphone` / `sentence-transformers` import errors — IS scoring deps wrong
- "fairseq.data.data_utils_fast" import error — Cython prebake didn't catch the right fairseq tree
- Empty `aggregated.json` — VSP_NBEST default isn't actually 1
- Empty `intelligibility_scores.csv` — IS scoring not wired up
- New-palette colors missing from `report.html` — wrong make_report.py

Each of these is a build-side bug. Iterate: edit container_payload_20260507, rebuild image, re-transfer to staging, retest.

### 5. Pin the legend selector

The `post_install_check.sh` mechanism check for the report-HTML legend uses a placeholder regex. After your first decode produces a real `report.html`:

```bash
# Find the actual legend element in the smoke output:
grep -A1 -E 'class="legend"|<legend|<div[^>]*confidence' \
  ~/vsp-output/<latest>/report.html | head -20
```

Update the regex in `checks/post_install_check.sh` (the `re.search` inside the inline Python block) to match the actual element. Confirm the check passes.

### 6. Run a real-world video end-to-end

Pick a 5-minute YouTube clip you've used before for evaluation. Drop it in a folder. Double-click the desktop launcher.

Visually inspect:

- `report.html` legend uses **blue / orange / purple / teal** (NOT green/yellow/red)
- At least one segment shows non-trivial confidence variation (not all one color)
- The displayed hypothesis on the page matches what's burned into the video
- Per-segment NIV labels (Y/P/N) appear and match the IS tier
- At least one Trust-tier segment + one Salvage-tier segment present
- If the input has a number ("billion", "1024", "2026"), the number word in the report is capped at orange (not green) — proves number-cap logic fires
- Burned video plays, subtitles align with audio, color matches report

### 7. Test launcher robustness

Try input folders with:

- A space in the name: `~/test folder with spaces/`
- An apostrophe: `~/Bob's videos/`
- A read-only USB drive
- A network share
- A folder that doesn't exist (operator typo) — launcher should error cleanly, not silently exit

The space-in-folder case will catch quoting bugs in the launcher. The read-only case proves the `:ro` input mount works — outputs go to `~/vsp-output/` regardless.

### 8. Test apply_update.sh

Build a tiny patch (`client-build-002`) with one trivial change (e.g. add a comment to `lib/common.sh`). Ship it through the same kit pipeline. Apply on the staging box:

```bash
cd kit-update-client-build-002/
sudo ./apply_update.sh vsp-image-client-build-002.tar.zst vsp-llm-pipeline:client-build-002
```

Verify:

- `image.tag` now reads `vsp-llm-pipeline:client-build-002`
- `image.tag.previous` reads `vsp-llm-pipeline:client-build-001`
- Re-running the launcher uses the new image
- `rollback.sh` flips it back

### 9. Test collect_diagnostics.sh

```bash
./checks/collect_diagnostics.sh
```

Open the resulting tarball. Confirm it contains:

- `host_info.txt`, `nvidia.txt`, `sys.txt`, `docker.txt`, `dmesg.tail`
- `pre_install_check.log`, `post_install_check.log`, `INSTALL_REPORT.txt`
- `recent_outputs/<run>/` with the small text files (no big videos or models)
- `image.tag` snapshots

If anything's missing or wrong, fix the script.

### 10. Lock the timings

Record actual measured times in `CLIENT_INSTALL.md` § "Appendix — Expected timings". Don't ship with the placeholder estimates — ship with real numbers from your staging hardware.

### 11. Sign off

Before USB-handing-off the kit:

- [ ] All Layer-2 mechanism checks PASS
- [ ] Visual inspection on a 5-min real video matches expectations
- [ ] Launcher works with space + apostrophe folder names
- [ ] apply_update + rollback exercised
- [ ] collect_diagnostics produces a useful bundle
- [ ] CLIENT_INSTALL.md timings are real, not estimated

If any item is unchecked, don't ship.

## When something fails Layer 2

This is exactly what Layer 2 is for. Fix the build-side bug, rebuild the image, re-transfer, restart the dry-run. If you skip the rebuild and just patch on the staging box, you've taught the bug it can survive — it'll be back at the client.
