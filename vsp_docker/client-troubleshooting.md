# VSP Pipeline — Client Troubleshooting

Symptom → cause → fix table for the air-gapped install. When in doubt, run `./checks/collect_diagnostics.sh` and send the resulting tarball.

## Pre-install / install issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `nvidia-smi: command not found` | NVIDIA driver not installed | Install the driver package matching the kernel (the driver script in this kit handles Arch). Reboot and retry. |
| `nvidia-smi` works but reports `Driver Version: 470.x` | Driver too old (need ≥ 525 for CUDA 12.x) | Upgrade driver. The shipped `nvidia-utils-580.x.x` package is required. |
| `pre_install_check.sh` says "compute_cap 6.1 not supported" | GPU is Pascal/Maxwell — too old for shipped wheels | Hardware change required. Volta or newer (T4 / V100 / A100 / RTX 30xx) is the practical floor. |
| `docker info` says "Cannot connect to the Docker daemon" | Docker daemon not running | `sudo systemctl start docker && sudo systemctl enable docker`. On Arch: `sudo systemctl enable --now docker`. |
| `docker run --gpus all ... nvidia-smi` returns "could not select device driver "" with capabilities: \[\[gpu]]" | NVIDIA Container Toolkit not configured | Re-run `offline_kit/install.sh`, then `sudo systemctl restart docker`. Verify `/etc/docker/daemon.json` has `"runtimes": {"nvidia": ...}`. |
| `docker load` fails with "no space left on device" | `/var/lib/docker` partition full | Either `docker system prune -a` to reclaim, or move Docker storage to a bigger disk: edit `/etc/docker/daemon.json` and set `"data-root": "/path/to/bigger/disk/docker"`. |
| `docker load` succeeds but `docker images` shows no `vsp-llm-pipeline` | Wrong tarball loaded | Verify the .tar.zst file's SHA256, decompress with `zstd -d`, then `docker load -i` the .tar (not the .zst). |
| `install_launcher.sh` says "Permission denied" placing files in /opt/vsp/launcher/ | Not running as root | `sudo ./install_launcher.sh`. |
| Desktop shortcut shows "Untrusted application launcher" instead of icon | GNOME security setting | Right-click → "Allow Launching", or run `gio set ~/Desktop/VSP-Pipeline.desktop metadata::trusted true`. |

## Pipeline-runtime issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Launcher exits silently after picking the folder | Container failed to start | Open a terminal manually: `docker run --rm --gpus all <image-tag> bash` and check the error. |
| Pipeline aborts at "step 0.5 normalization" with NVENC error | Old NVIDIA driver missing NVENC support, OR GPU doesn't have NVENC (some lower-end consumer cards) | Set `USE_GPU_NORM=0` before launching: `USE_GPU_NORM=0 /opt/vsp/launcher/vsp-pipeline.sh`. CPU-encoded normalization is slower but works on any GPU/driver. |
| Pipeline aborts at "step 7 decode" with `ImportError: cannot import name 'data_utils_fast' from 'fairseq.data'` | Cython extensions not built (would have happened automatically on build, but the build smoke would've caught this — if you see it at runtime, the build prebake failed) | Run inside the container: `docker exec vsp bash -c 'cd /workspace/VSP-LLM/fairseq && python setup.py build_ext --inplace'`. |
| Pipeline aborts with CUDA OOM during decode | GPU has < 12 GB VRAM, or another process is using GPU memory | Close other GPU apps. If still failing: `nvidia-smi` to confirm VRAM is free, then re-run. With a 12 GB GPU, the decode dynamically reduces max_length — but extreme-length videos can still OOM. |
| Pipeline runs but produces empty `hyp_*` lines in report.csv | Decode produced no output (rare — usually a checkpoint mismatch) | Check `decode.log` for fairseq errors. Most likely a model checkpoint missing or mis-pointed. |
| `report.html` shows green/yellow/red colors, not blue/orange/purple | Wrong / stale `make_report.py` got into the image | Image was built from a stale galaxy_export. Apply the latest patch via `apply_update.sh`, or rebuild the image. |
| IS scores all read 0.00 or NaN | sentence-transformers model not loading | Confirm `is_model_cache/` is in the image: `docker run --rm <tag> ls /workspace/is_model_cache/hub/`. Should list `models--sentence-transformers--all-MiniLM-L6-v2`. |
| Pipeline finishes but `$HOME/vsp-output/<ts>/` is empty | The export hook didn't fire (maybe an old image without the hook) | Check the image was built from the May 2026 galaxy_export (with the VSP_OUTPUT_DIR hook in `lib/outputs.sh`). Older images don't honor the env var. |
| Burned videos missing | `VSP_FULL_OUTPUTS=1` not set; default skips burns | Re-launch with `VSP_FULL_OUTPUTS=1 /opt/vsp/launcher/vsp-pipeline.sh`. |

## Update / rollback issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `apply_update.sh` aborts at "smoke test failed" | New image has a regression | Old image still active (apply_update is atomic). Don't apply. Report the regression with `collect_diagnostics.sh`. |
| `rollback.sh` says "previous image not loaded in Docker" | Operator ran `docker rmi` on the old image | Re-load it: `docker load -i vsp-image-<previous-build-id>.tar` from the original kit USB. Then re-run `rollback.sh`. |
| Launcher uses old tag after `apply_update.sh` succeeded | `image.tag` not updated, OR launcher shortcut points at a different tag file | Verify: `cat /opt/vsp/launcher/image.tag`. If wrong, write the right tag manually. |

## Diagnosis commands

```bash
# Quick health check
nvidia-smi
docker info | grep -E 'Server Version|Runtime'
cat /opt/vsp/launcher/image.tag
docker images vsp-llm-pipeline

# Run module tests inside the current image
docker run --rm $(cat /opt/vsp/launcher/image.tag) bash /workspace/lib/test_all_modules.sh

# Re-run post_install_check
./checks/post_install_check.sh

# Collect everything for support
./checks/collect_diagnostics.sh
```

## When all else fails — nuke and pave

```bash
docker rm -f vsp                                                     # remove any running container
docker rmi $(docker images vsp-llm-pipeline -q)                      # remove all VSP image versions
docker load -i vsp-image-<build-id>.tar                              # reload from USB
echo "vsp-llm-pipeline:<build-id>" | sudo tee /opt/vsp/launcher/image.tag
./checks/post_install_check.sh                                        # verify
```

Five commands. Don't reinstall Docker / NVIDIA toolkit unless those are also broken — those layers rarely need touching.
