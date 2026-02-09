# Bugs Found Installing on Client's Standalone Linux Container

**Date**: February 8, 2026
**Package**: vsp_linux_container_FINAL v1.0.0

This document tracks all issues encountered during installation and testing on the client's standalone Linux container.

---

## Bug 1: INSTALL.sh fails - "lib/ directory not found"

**When**: Running INSTALL.sh for the first time
**Error**:
```
[1/6] Checking prerequisites...
ERROR: lib/ directory not found
This directory needs existing VSP installation
```

**Root Cause**: INSTALL.sh had prerequisite checks that required `lib/`, `VSP-LLM/`, and `vsp-ui/` directories to already exist. On a fresh or first-time installation, these directories don't exist yet because the installer is supposed to CREATE them.

**Fix**: Changed INSTALL.sh to create missing directories with `mkdir -p` instead of exiting with an error.

**Before**:
```bash
if [ ! -d "lib" ]; then
    echo "ERROR: lib/ directory not found"
    exit 1
fi
```

**After**:
```bash
if [ ! -d "lib" ]; then
    echo "lib/ not found - creating (fresh installation)"
    mkdir -p lib
fi
```

**Status**: Fixed in package v1.0.1

---

## Bug 2: Pipeline fails - "fast_segment.py: No such file or directory"

**When**: Running pipeline with segmentation enabled (default)
**Error**:
```
python3: can't open file '/host/galaxy_export/auto_avsr/preparation/fast_segment.py': No such file or directory
```

**Root Cause**: `fast_segment.py` is a newer script added as part of the segment-first normalization architecture (Feb 2026). It was not included in the original deployment package because the package only shipped `lib/`, `VSP-LLM/`, `vsp-ui/`, and the pipeline script. The `auto_avsr/` directory was assumed to already exist in the container.

The client's standalone container was built from an older image that predates the segment-first architecture and does not have this file.

**Fix**: Added `fast_segment.py` and `preprocess_with_overlap.py` to the package under `auto_avsr/preparation/`. Updated INSTALL.sh to copy these files during installation.

**Files Added**:
- `auto_avsr/preparation/fast_segment.py` - Ultra-fast video segmentation using ffmpeg codec copy
- `auto_avsr/preparation/preprocess_with_overlap.py` - Preprocessing with overlap support

**Status**: Fixed in package v1.0.1

---

## Bug 3: Pipeline would fail at Steps 3-6 - Missing processing scripts

**When**: Would fail after fixing Bug 2, at ASR (Step 3), LRS3 conversion (Step 4), manifest generation (Step 5), and clustering (Step 6)

**Root Cause**: Same as Bug 2 - the package assumed the container had all processing scripts, but the client's standalone container was missing several newer files.

**Missing files identified**:

| File | Used In | Purpose |
|------|---------|---------|
| `auto_avsr/asr_to_words_notime.py` | Step 3 (ASR) | Whisper ASR transcription |
| `auto_avsr/make_simple_manifest.py` | Step 5 (Manifests) | Generate manifest files |
| `auto_avsr/generate_segment_timing.py` | Step 5 (Manifests) | Segment timing metadata |
| `av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh` | Step 4 (LRS3) | LRS3 format conversion |
| `av_hubert/avhubert/preparation/split_flat_dataset.py` | Step 4 (LRS3) | Dataset splitting |
| `VSP-LLM/src/clustering/dump_hubert_feature.py` | Step 6 (K-means) | HuBERT feature extraction |
| `VSP-LLM/src/clustering/learn_kmeans.py` | Step 6 (K-means) | K-means model training |
| `VSP-LLM/src/clustering/dump_km_label.py` | Step 6 (K-means) | Cluster label generation |
| `VSP-LLM/src/clustering/cluster_counts.py` | Step 6 (K-means) | Cluster count computation |

**Fix**: Added all missing scripts to the package. Updated INSTALL.sh with components 7 (auto_avsr), 8 (av_hubert), and 9 (VSP-LLM clustering).

**Status**: Fixed in package v1.0.1

---

## Bug 4: Pipeline fails at Step 2 - "No module named 'overlapping_segmentation'"

**When**: Running pipeline Step 2 (mouth cropping / preprocessing)
**Error**:
```
ModuleNotFoundError: No module named 'overlapping_segmentation'
```

**Root Cause**: `preprocess_with_overlap.py` imports from 4 local modules that were never included in the package:
1. `overlapping_segmentation` - Core segmentation logic (split_video_by_time, generate_segment_metadata)
2. `data.data_module` - AVSRDataLoader for loading video/audio during mouth cropping
3. `transforms` - TextTransform for text preprocessing
4. `utils` - save_vid_aud_txt for saving processed outputs

Additionally, the face detector modules (`detectors/mediapipe/` and `detectors/retinaface/`) and their data files were missing. These are imported dynamically by `data_module.py` based on the `--detector` argument.

**Missing Files (11 total)**:

| File | Imported By | Purpose |
|------|------------|---------|
| `auto_avsr/preparation/overlapping_segmentation.py` | `preprocess_with_overlap.py` | Video segmentation with overlap |
| `auto_avsr/preparation/data/data_module.py` | `preprocess_with_overlap.py` | AVSRDataLoader (video/audio loading) |
| `auto_avsr/preparation/transforms.py` | `preprocess_with_overlap.py` | TextTransform (text normalization) |
| `auto_avsr/preparation/utils.py` | `preprocess_with_overlap.py` | save_vid_aud_txt (output saving) |
| `auto_avsr/preparation/preprocess_lrs2lrs3.py` | Pipeline (fallback) | Non-overlap preprocessing |
| `auto_avsr/preparation/detectors/mediapipe/detector.py` | `data_module.py` | MediaPipe face detection |
| `auto_avsr/preparation/detectors/mediapipe/video_process.py` | `data_module.py` | MediaPipe video processing |
| `auto_avsr/preparation/detectors/mediapipe/20words_mean_face.npy` | `video_process.py` | Mean face landmarks data |
| `auto_avsr/preparation/detectors/retinaface/detector.py` | `data_module.py` | RetinaFace detection (alternative) |
| `auto_avsr/preparation/detectors/retinaface/video_process.py` | `data_module.py` | RetinaFace video processing |
| `auto_avsr/preparation/detectors/retinaface/20words_mean_face.npy` | `video_process.py` | Mean face landmarks data |

**Fix**: Added all 11 files to the package. Updated INSTALL.sh component [3.7] to copy `data/`, `detectors/`, and subdirectories.

**Status**: Fixed in package v1.0.2

---

## Bug 5: Pipeline would fail at Step 2 - Missing SentencePiece model files

**When**: Would fail during preprocessing when TextTransform initializes
**Error**:
```
FileNotFoundError: [Errno 2] No such file or directory: '.../auto_avsr/spm/unigram/unigram5000.model'
```

**Root Cause**: `transforms.py` computes the SentencePiece model path as `../../spm/unigram/unigram5000.model` relative to its own location. These model files (327KB + 74KB) were never included in the package.

**Missing Files**:

| File | Size | Purpose |
|------|------|---------|
| `auto_avsr/spm/unigram/unigram5000.model` | 327KB | SentencePiece tokenization model |
| `auto_avsr/spm/unigram/unigram5000_units.txt` | 74KB | Token vocabulary units |

**Fix**: Added both files to the package. Updated INSTALL.sh to create `auto_avsr/spm/unigram/` and copy model files.

**Status**: Fixed in package v1.0.2

---

## Bug 6: Pipeline would fail at Step 4 - Missing count_frames.py

**When**: Would fail during LRS3 format conversion (Step 4)
**Error**:
```
python: can't open file 'count_frames.py': [Errno 2] No such file or directory
```

**Root Cause**: `flat_to_lrs3_preperation.sh` line 63 calls `python count_frames.py` but this file was not included in the package under `av_hubert/avhubert/preparation/`.

**Fix**: Added `count_frames.py` to the package.

**Status**: Fixed in package v1.0.2

---

## Bug 7: flat_to_lrs3_preperation.sh has hardcoded EC2 paths

**When**: Would fail on any container where the base directory is not `/home/ubuntu/`
**Error**:
```
bash: /home/ubuntu/auto_avsr/pre-process-venv/bin/activate: No such file or directory
```

**Root Cause**: Lines 11-12 had hardcoded paths:
```bash
PREP_DIR="/home/ubuntu/av_hubert/avhubert/preparation"
VENV="/home/ubuntu/auto_avsr/pre-process-venv"
```

**Fix**: Changed to auto-detect paths from script location using `BASH_SOURCE`:
```bash
PREP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_BASE_DIR="$(cd "${PREP_DIR}/../../.." && pwd)"
VENV="${_BASE_DIR}/auto_avsr/pre-process-venv"
```

This works regardless of install location (`/home/ubuntu/`, `/workspace/`, `/host/galaxy_export/`, etc.)

**Status**: Fixed in package v1.0.2

---

## Bug 8: Whisper tries to download model instead of using local weights

**When**: Running pipeline Step 3 (ASR / Whisper transcription)
**Error**:
```
urllib.error.URLError: <urlopen error [Errno -3] Temporary failure in name resolution>
```
or similar network error when Whisper tries to download `medium.pt` from the internet.

**Root Cause**: `asr_to_words_notime.py` called `whisper.load_model("medium")` without passing the `download_root` parameter. Whisper defaults to `~/.cache/whisper/` and if the model isn't there, it tries to download from the internet. The container has no internet access, causing the error. The model already existed at `/host/galaxy_export/whisper/medium.pt` but the code didn't know to look there.

**Fix**: Added `--download_root` CLI argument to `asr_to_words_notime.py` and auto-detection logic in `lib/asr.sh` to find the whisper cache directory.

**Auto-detection priority**:
1. `$(dirname $AUTO_AVSR)/whisper/` — Container: `/host/galaxy_export/whisper/`
2. `$HOME/.cache/whisper/` — EC2 default location
3. If neither found, Whisper uses its built-in default

**Files Modified**:
- `auto_avsr/asr_to_words_notime.py` — Added `--download_root` argument, passed to `whisper.load_model()`
- `lib/asr.sh` — Added whisper cache auto-detection before calling the Python script

**Status**: Fixed in package v1.0.3

---

## Bug 9: `python: command not found` in multiple scripts

**When**: Running pipeline Step 4 (LRS3 conversion) and potentially other steps
**Error**:
```
flat_to_lrs3_preperation.sh: line 30: python: command not found
```

**Root Cause**: The container only has `python3`, not `python`. Multiple scripts used `python` instead of `python3` in executable calls and shebangs.

**Affected files (11 total)**:

| File | Line | Issue |
|------|------|-------|
| `av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh` | 30, 66 | `python` executable calls |
| `VSP-LLM/scripts/decode.sh` | 38 | `python -B` executable call |
| `auto_avsr/make_simple_manifest.py` | 1 | `#!/usr/bin/env python` shebang |
| `auto_avsr/preparation/transforms.py` | 1 | `#!/usr/bin/env python` shebang |
| `auto_avsr/preparation/data/data_module.py` | 1 | `#!/usr/bin/env python` shebang |
| `auto_avsr/preparation/detectors/mediapipe/detector.py` | 1 | `#!/usr/bin/env python` shebang |
| `auto_avsr/preparation/detectors/mediapipe/video_process.py` | 1 | `#!/usr/bin/env python` shebang |
| `auto_avsr/preparation/detectors/retinaface/detector.py` | 1 | `#!/usr/bin/env python` shebang |
| `auto_avsr/preparation/detectors/retinaface/video_process.py` | 1 | `#!/usr/bin/env python` shebang |
| `VSP-LLM/scripts/build_flat_cluster_counts.py` | 1 | `#!/usr/bin/env python` shebang |

**Fix**: Changed all `python` → `python3` in executable calls and shebangs across the entire package.

**Status**: Fixed in package v1.0.5

---

## Bug 10: count_frames.py fails - "No module named 'cv2'"

**When**: Running pipeline Step 4 (LRS3 conversion) - `count_frames.py` called by `flat_to_lrs3_preperation.sh`
**Error**:
```
ModuleNotFoundError: No module named 'cv2'
```

**Root Cause**: `flat_to_lrs3_preperation.sh` activates the wrong virtual environment. After the Bug 7 fix, the script auto-detects paths from its own location:
```bash
_BASE_DIR="$(cd "${PREP_DIR}/../../.." && pwd)"
VENV="${_BASE_DIR}/auto_avsr/pre-process-venv"
```

On the container, the script is at `/host/galaxy_export/av_hubert/avhubert/preparation/`, so `_BASE_DIR` resolves to `/host/galaxy_export/`. But the actual venv with cv2/scipy is at `/workspace/auto_avsr/pre-process-venv` — **code and venvs are in different directories** on this container.

The old working pipeline solved this differently — it used `sed -i` to patch the hardcoded paths at runtime:
```bash
sed -i "s#/home/ubuntu/auto_avsr/pre-process-venv#${AUTO_AVSR}/pre-process-venv#g" "${FLT_SH}"
```

**Additional complication**: Auto-detection alone was insufficient because a `pre-process-venv` directory EXISTS at `${_BASE_DIR}/auto_avsr/` (the code location) but it's incomplete — it doesn't have cv2/scipy installed. The auto-detection found this directory first and used it, even though the working venv is at `/workspace/`.

**Fix (v1.0.7)**: Pass the known-good venv path from the pipeline instead of guessing. Two changes:

1. `lib/lrs3_prep.sh` — passes `VENV="${PREP_VENV:-}"` as an environment variable to `flat_to_lrs3_preperation.sh`. The pipeline already knows the correct path (`PREP_VENV="/workspace/auto_avsr/pre-process-venv"`) because it works for Step 2.

2. `flat_to_lrs3_preperation.sh` — if `VENV` is already set by the caller, uses it directly (skips auto-detection). Only falls back to auto-detection if called standalone:
```bash
if [ -z "${VENV:-}" ]; then
    # auto-detect from known locations...
fi
```

This is the same approach the old working pipeline used (it patched the path via `sed -i`), but cleaner.

**Files Modified**:
- `lib/lrs3_prep.sh` — Added `VENV="${PREP_VENV:-}"` to env vars passed to subprocess
- `av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh` — Accept VENV from caller, skip auto-detection if provided

**Note**: `count_frames.py` itself is unchanged — it's the original from the av_hubert paper repository and works correctly when the right venv (with cv2/scipy) is activated.

**Status**: Fixed in package v1.0.7

---

## Bug 11: Decode fails - "Key 'max_len' not in 'GenerationConfig'"

**When**: Running pipeline Step 7 (VSP-LLM decode)
**Error**:
```
omegaconf.errors.ConfigAttributeError: Key 'max_len' not in 'GenerationConfig'
```

**Root Cause**: The decode config `s2s_decode.yaml` sets `generation.max_len: 2048`, but the container's fairseq installation doesn't have a `max_len` field in the `GenerationConfig` dataclass (`fairseq/dataclass/configs.py`). Hydra validates configs against the dataclass schema, and the missing field causes schema validation to fail before decode even starts.

The EC2 environment had this field added manually, but the container's fairseq was never patched. The package doesn't ship fairseq itself (it's pip-installed in the container's venv), so the field was missing.

**Why max_len matters**:
- Controls maximum output sequence length for LLaMA decoder
- Without it, model uses hardcoded default of 30 tokens — truncating long transcriptions
- Config wants 2048 to handle long video segments

**Fix**: Added `patch_fairseq_max_len.py` to the package. This script:
1. Finds the container's fairseq `configs.py` via Python import
2. Checks if `max_len` field already exists (idempotent)
3. Inserts the field between `max_len_b` and `min_len` in `GenerationConfig`
4. Verifies the patch by reloading the module

INSTALL.sh component [3.10] now runs this patch automatically using the VSP venv.

**Files Added**:
- `patch_fairseq_max_len.py` — Idempotent patch script for fairseq GenerationConfig

**Files Modified**:
- `INSTALL.sh` — Added component [3.10] to run patch, added verification check #13

**Status**: Fixed in package v1.0.8

---

## Bug 12: UI not accessible from host machine

**When**: Starting the VSP UI server inside the container and trying to access it from the host browser
**Error**: Browser shows "connection refused" or "site can't be reached" at `https://127.0.0.1:8765`

**Root Cause**: The UI server was binding to `127.0.0.1` (localhost only), which only accepts connections from within the container itself. Since the browser runs on the host machine (outside the container), it cannot connect to the container's loopback interface.

**Fix**: Changed `SERVER_HOST` from `127.0.0.1` to `0.0.0.0` so the server accepts connections from any network interface, including from the host machine.

**Files Modified**:
- `vsp-ui/app/config.py` — Changed `SERVER_HOST = "127.0.0.1"` → `SERVER_HOST = "0.0.0.0"`
- `vsp-ui/launcher.sh` — Changed `HOST="127.0.0.1"` → `HOST="0.0.0.0"`

**How to access**: After restarting the server, find the container's IP (`hostname -I`) and open `https://<container-ip>:8765` in the host browser.

**Status**: Fixed in package v1.0.9

---

## Bug 13: Docker container started without port mapping

**When**: Starting the Docker container manually and trying to access UI from host browser
**Error**: `http://172.17.0.2:8765` and `http://localhost:8765` both unreachable from host

**Root Cause**: The `docker run` command was missing `-p 8765:8765` port mapping. Without it, the container's port 8765 is not forwarded to the host, even with `SERVER_HOST=0.0.0.0` binding.

**Fix**: Created `vsp-start.sh` — a host-side launcher script that handles everything:
1. Starts Docker with correct flags (`--gpus all -p 8765:8765 -v ...`)
2. Runs the UI server inside the container
3. Waits for server to be ready
4. Opens the browser to `http://localhost:8765`

Also created `vsp-pipeline.desktop` for a one-click desktop icon.

**Files Added**:
- `vsp-start.sh` — Host-side launcher (start/stop/status)
- `vsp-pipeline.desktop` — Linux desktop entry pointing to vsp-start.sh

**Usage from host**:
```bash
# Start (opens browser automatically):
bash /home/ds/Desktop/galaxy_export/vsp-start.sh

# Stop:
bash /home/ds/Desktop/galaxy_export/vsp-start.sh stop

# Desktop icon:
cp /home/ds/Desktop/galaxy_export/vsp-pipeline.desktop ~/Desktop/
chmod +x ~/Desktop/vsp-pipeline.desktop
```

**Status**: Fixed in package v1.0.10

---

## Lessons Learned

1. **Don't assume existing installations**: The package was designed as an "update" to an existing installation, but the client's container was older than expected. All scripts referenced by the pipeline should be included.

2. **Test on a clean environment**: The package was verified on EC2 where all files already existed. Testing on a clean container would have caught all missing file issues immediately.

3. **Include all executable dependencies**: If `run_flat_english_pipeline.sh` calls a script, that script must either already exist in the target environment OR be included in the package.

4. **Always use `python3`**: Never assume `python` is available — many systems only have `python3`. Use `python3` in all executable calls and shebangs.

5. **Code and venvs may be in different directories**: Don't assume the venv is co-located with the code. On containers, code at `/host/galaxy_export/` but venvs at `/workspace/`. Always try multiple locations when auto-detecting venv paths.

---

## Package Versions

| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | Feb 3, 2026 | Initial package - 12 fixes, docs, scripts |
| v1.0.1 | Feb 8, 2026 | Fixed INSTALL.sh directory checks, added missing auto_avsr/av_hubert/clustering scripts |
| v1.0.2 | Feb 8, 2026 | Added 14 missing preprocessing files: overlapping_segmentation, data_module, transforms, utils, detectors (mediapipe+retinaface), SentencePiece models, count_frames.py. Fixed hardcoded EC2 paths in flat_to_lrs3_preperation.sh |
| v1.0.3 | Feb 8, 2026 | Fixed Whisper offline model loading - added --download_root auto-detection for container whisper cache |
| v1.0.4 | Feb 8, 2026 | Added comprehensive E2E test suite (58 tests across 12 categories) |
| v1.0.5 | Feb 8, 2026 | Fixed `python` → `python3` in all shell scripts (3 executable calls) and Python shebangs (8 files) |
| v1.0.6 | Feb 8, 2026 | Fixed venv auto-detection in flat_to_lrs3_preperation.sh - tries multiple locations (code dir, /workspace/, $HOME/) |
| v1.0.7 | Feb 8, 2026 | Fixed venv pass-through: pipeline passes known-good PREP_VENV to flat_to_lrs3_preperation.sh via lrs3_prep.sh, skips auto-detection when caller provides VENV |
| v1.0.8 | Feb 8, 2026 | Fixed fairseq max_len: added patch_fairseq_max_len.py to add missing GenerationConfig field, INSTALL.sh runs it automatically |
| v1.0.9 | Feb 8, 2026 | Fixed UI server binding: changed 127.0.0.1 → 0.0.0.0 so host browser can reach container UI |
| v1.0.10 | Feb 9, 2026 | Added host-side launcher: vsp-start.sh handles Docker startup with port mapping, desktop icon for one-click launch |

---

**Current Package Status**: v1.0.10 - All known bugs fixed, host launcher + desktop icon included
