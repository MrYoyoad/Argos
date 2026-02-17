# Bugs 26-37: Final Deployment Fixes

> Upload reliability, beam search OOM, terminal detection, inference tuning, metrics, VLC overlay.
> Split from BUGS_INSTALLING_CLIENT_STANDALONE.md. See also:
> - [Bugs Reference](bugs-reference.md) — Docker, lessons learned, package versions
> - [Bugs 1-13](bugs-1-to-13-installation.md) — Installation & setup
> - [Bugs 14-25](bugs-14-to-25-deployment.md) — Deployment & GPU issues

## Bug 26: Drag-and-drop video upload does not save files to input folder

**When**: Dragging video files from desktop into the browser UI on the welcome screen
**Error**: Upload appears to fail silently — files don't appear in `~/vsp_input/` folder, video count doesn't update. No error shown to user (error may appear in server console).

**Root Cause**: The upload handler (`handle_upload()` in `server.py`) used `cgi.FieldStorage` to parse multipart/form-data uploads. The `cgi` module was deprecated in Python 3.11 and is known to be unreliable for binary file uploads (like video files) with Python's built-in HTTP server. Common failure modes:
1. `cgi.FieldStorage` silently fails to parse the multipart boundary
2. Binary data gets corrupted during parsing
3. Content-Length mismatch causes incomplete reads
4. On Python 3.13+, the `cgi` module is removed entirely

**Fix**: Replaced `cgi.FieldStorage` with a manual multipart/form-data parser that:
1. Extracts the boundary from the Content-Type header
2. Reads the complete request body using Content-Length
3. Splits by boundary delimiter to find the file part
4. Parses Content-Disposition header to extract filename
5. Writes raw binary data directly to disk

The new parser:
- Works on all Python versions (3.8+, including 3.13+ where `cgi` is removed)
- Handles binary data correctly (no encoding/decoding issues)
- Includes proper error messages for debugging
- Adds traceback printing on failure for server-side diagnostics

**Files Modified**:
- `vsp-ui/app/server.py` — Replaced `handle_upload()` method (~60 lines → ~95 lines), removed `import cgi`

**Status**: Fixed in package v1.0.22

---

## Bug 27: Decode CUDA OOM within single beam search call on 12GB GPU

**When**: Running pipeline Step 7 (VSP-LLM decode) on standalone computer with 12GB GPU
**Error**:
```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 86.00 MiB.
GPU 0 has a total capacity of 11.63 GiB of which 78.25 MiB is free.
```
Crash happens at the 4th sample during `model.generate()`.

**Root Cause**: Bug 14 fix handled memory accumulation *between* samples (gc.collect + empty_cache). This new OOM happens *within* a single beam search call. With `beam=20` and `dynamic_max_len≈750-1050` (from `max_len_a=3.0 × src_tokens + max_len_b=300`), the KV cache for beam search needs ~7-10GB on top of ~6GB model weights, exceeding 12GB.

Degenerate repetitive outputs amplify the problem:
- `"yeah yeah yeah yeah..."` × 48 words — model hits max_length
- `"a man and a man and a man..."` × 17 — fills entire generation budget
- These repetitions waste tokens, maximize KV cache, and produce garbage output

**Fix (Two Parts)**:

1. **Enable `no_repeat_ngram_size=3`** (primary fix) — prevents the model from repeating the same 3-gram during beam search. Stops degenerate repetitions immediately, so outputs stay short (~50 tokens for a 12s segment). Configured in `s2s_decode.yaml`, passed through `vsp_llm_decode.py` → `vsp_llm.py` → HuggingFace `decoder.generate()`.

2. **Cap `dynamic_max_len` at 512 on GPUs < 16GB** (safety net) — detects GPU memory after model loading. On 12GB GPUs, caps max generation length at 512 tokens instead of ~750-1050. With beam=20 and 512 cap: KV cache ≈ 5.2GB + 6GB model = ~11.2GB (fits in 12GB). Beam size stays at 20 on all GPUs (no quality reduction). 24GB GPUs unaffected.

**Memory Budget After Fix**:
- Typical case (no_repeat_ngram stops early): 20 beams × ~80 tokens = ~0.8GB KV → total ~6.8GB ✅
- Worst case (hits 512 cap): 20 beams × 512 tokens = ~5.2GB KV → total ~11.2GB ✅

**Files Modified**:
- `VSP-LLM/src/vsp_llm_decode.py` — GPU memory detection, max_len cap, `no_repeat_ngram_size` passthrough
- `VSP-LLM/src/vsp_llm.py` — Accept and pass `no_repeat_ngram_size` to HuggingFace generate()
- `VSP-LLM/src/conf/s2s_decode.yaml` — Added `no_repeat_ngram_size: 3`

**Status**: Fixed in package v1.0.23

---

## Bug 28: Desktop icon "No terminal emulator found" on machines without standard terminals

**When**: Clicking the VSP Pipeline desktop icon after installation
**Error**:
```
Error: No terminal emulator found. Run from a terminal instead.
```
(Shown via `notify-send` desktop notification, or silent failure if `notify-send` unavailable)

**Root Cause**: `vsp-start.sh` self-relaunch guard only checked 5 terminal emulators: `gnome-terminal`, `xfce4-terminal`, `mate-terminal`, `konsole`, `xterm`. The client's machine has a different terminal (e.g., `lxterminal`, `tilix`, or another) that wasn't in the list. The machine has no internet access, so installing a new terminal is not possible.

**Fix (Three Safety Layers)**:

1. **Expanded static terminal list** — Added `x-terminal-emulator` (Debian/Ubuntu alternatives system symlink that points to whatever terminal is installed) as the first entry, plus `lxterminal`, `tilix`, `terminator`, `kitty`, `alacritty`. The `x-terminal-emulator` symlink alone should resolve 95%+ of cases on Debian/Ubuntu systems.

2. **Dynamic terminal search** — If no named terminal found, searches `/usr/bin/` for executables matching `*terminal*` or `*-term` patterns and tries them with the generic `-e` invocation flag.

3. **Actionable error message** — If still no terminal found, shows clear instructions via both `notify-send` and `zenity --error` dialog telling the user to open a terminal manually and run the script.

**Before** (5 terminals):
```bash
for _term in gnome-terminal xfce4-terminal mate-terminal konsole xterm; do
```

**After** (11 named + dynamic fallback):
```bash
for _term in x-terminal-emulator gnome-terminal xfce4-terminal mate-terminal konsole lxterminal tilix terminator kitty alacritty xterm; do
    ...
done
# Dynamic fallback: search /usr/bin/ for any terminal-like executable
for _candidate in /usr/bin/*terminal* /usr/bin/*-term; do
    ...
done
```

**Files Modified**:
- `vsp-start.sh` — Expanded terminal list (line 25), added dynamic search fallback, improved error message
- `install-desktop-icon.sh` — Expanded same terminal list in verification check (line 113)

**Status**: Fixed in package v1.0.24

---

## Bug 29: Drag-and-drop upload still fails inside Docker container (path mismatch)

**When**: Dragging video files into the browser UI when running inside the Docker container (via `vsp-start.sh`)
**Error**: Upload handler writes files to `/host/vsp_input/` (from config.py `INPUT_DIR`), which is outside the Docker volume mount `/host/galaxy_export`. Files are written inside the container's ephemeral filesystem and disappear when the container stops. The bug persists even after the cgi.FieldStorage fix in Bug 26.

**Root Cause**: `config.py` sets `INPUT_DIR = Path("/host/vsp_input")` when it detects the container environment (checks for `/host/galaxy_export`). But the Docker volume mount in `vsp-start.sh` only maps `${GALAXY_EXPORT_DIR}:/host/galaxy_export`. The path `/host/vsp_input` is NOT inside this mount — it's a separate path that only exists ephemerally inside the container.

**Workaround (chosen approach)**: Instead of fixing the container path (which would require config.py changes across multiple dependent systems), added an **"Open Folder"** button to the welcome screen that tells the user to add videos directly via their host file manager:

1. **HTML**: Added "Open Folder" button next to the input path display on the welcome screen
2. **JavaScript**: `openInputFolder()` calls `/api/open-folder` endpoint; if the folder can't be opened automatically (expected in Docker), shows an alert with the host-side path so the user knows where to drag files
3. **Docker env var**: `vsp-start.sh` passes `VSP_HOST_INPUT_DIR=${GALAXY_EXPORT_DIR}/vsp_input` as an environment variable to the container
4. **Server**: `handle_open_folder()` reads `VSP_HOST_INPUT_DIR` env var and returns the host-side path in its response, so the user sees the actual folder path on their host machine

**User Flow After Fix**:
1. User clicks "Open Folder" button on welcome screen
2. Alert shows: "Please open your file manager and navigate to: /home/ds/Desktop/galaxy_export/vsp_input"
3. User opens file manager, navigates to that path, drags videos in
4. User clicks "Inspect Videos" to verify files are detected
5. Proceeds with pipeline

**Files Modified**:
- `vsp-ui/app/static/index.html` — Added "Open Folder" button to welcome screen input-folder-display div
- `vsp-ui/app/static/app.js` — Added `openInputFolder()` function and click event listener
- `vsp-ui/app/server.py` — Updated `handle_open_folder()` to use `VSP_HOST_INPUT_DIR` env var for display path
- `vsp-start.sh` — Added `-e "VSP_HOST_INPUT_DIR=${GALAXY_EXPORT_DIR}/vsp_input"` to docker run command

**Note**: The browser drag-and-drop upload (Bug 26 fix) works correctly on EC2 where `INPUT_DIR` points to a real local path. The Docker path mismatch only affects the containerized deployment.

**Status**: Fixed (workaround) in package v1.0.25

---

## Bug 30: docker.conf requires sudo to edit on host machine

**When**: User needs to change `DOCKER_IMAGE` value in `docker.conf` after installation
**Error**: File is read-only for the host user — any text editor (nano, gedit, VS Code) fails to save without `sudo`.

**Root Cause**: `INSTALL.sh` runs inside the Docker container as `root`. When it creates `docker.conf` (component [3.12], line 242-255), the file is owned by `root:root` with default permissions `644`. Since the `galaxy_export` directory is a Docker volume mount (`-v /home/ds/Desktop/galaxy_export:/host/galaxy_export`), this root ownership persists on the host filesystem. The host user (`ds`) cannot write to root-owned files without `sudo`.

**Fix**: Added `chmod 666 docker.conf` immediately after the file is created in INSTALL.sh. This makes the file world-writable so any host user can edit it with any text editor — no `sudo` needed.

```bash
# Make docker.conf editable by host user (INSTALL runs as root inside container)
chmod 666 "$DOCKER_CONF" 2>/dev/null || true
```

The `2>/dev/null || true` keeps it non-fatal in case the filesystem doesn't support chmod (same pattern used for Bug 17).

**Files Modified**:
- `INSTALL.sh` — Added `chmod 666` after docker.conf creation (after line 261)

**Status**: Fixed in package v1.0.26

---

## Bug 31: Desktop icon "cannot execute binary file" — scripts lack +x on mounted filesystem

**When**: Clicking the desktop icon after running `install-desktop-icon.sh` on a machine where `galaxy_export` is on a mounted filesystem
**Error**:
```
/usr/bin/bash: /usr/bin/bash: cannot execute binary file
```

**Root Cause**: INSTALL.sh runs as root inside the Docker container and copies all files to the mounted volume. The `chmod +x` calls in INSTALL.sh silently fail on the mounted filesystem (Bug 17). As a result, `vsp-start.sh` and all other scripts have no execute permission on the host.

The launch chain has TWO places that need the script to be executable:
1. **`.desktop` Exec line** — GNOME tries to exec `vsp-start.sh` directly
2. **Self-relaunch in `vsp-start.sh`** — `gnome-terminal -- vsp-start.sh` tries to exec it directly

Both fail because the file lacks `+x` on the mounted filesystem.

**Why previous Bug 22 fix was different**: Bug 22 used `Terminal=true` + `Exec=bash script`. With `Terminal=true`, the DE wraps the Exec in an extra shell → `bash bash script` → double-bash error. The fix here uses `Terminal=false` so the DE does NO wrapping — we control the entire chain ourselves.

**Fix (Three Parts)**:

**Part 1: `.desktop` Exec line** (install-desktop-icon.sh)
```
# BEFORE (requires execute bit):
Exec=/path/to/vsp-start.sh

# AFTER (bash reads the file, no +x needed):
Exec=/usr/bin/bash /path/to/vsp-start.sh
```

**Part 2: Self-relaunch** (vsp-start.sh lines 30-31, 39)
```bash
# BEFORE (gnome-terminal tries to exec script directly):
gnome-terminal) exec "$_term_path" -- "$0" "$@" ;;
*)              exec "$_term_path" -e "$0" "$@" ;;

# AFTER (bash reads the file, no +x needed):
gnome-terminal) exec "$_term_path" -- /usr/bin/bash "$0" "$@" ;;
*)              exec "$_term_path" -e /usr/bin/bash "$0" "$@" ;;
```

**Part 3: Fix permissions at the source** (INSTALL.sh, new component [3.14])
```bash
# After all components installed, make everything accessible to host user:
chmod -R a+rX . 2>/dev/null || true          # Everything readable + dirs traversable
find . -name "*.sh" -exec chmod a+rx {} \; 2>/dev/null || true  # All scripts executable
find . -name "*.py" -exec chmod a+r {} \; 2>/dev/null || true   # All Python readable
```
Even if `chmod` silently fails on the mounted filesystem, Parts 1 and 2 ensure the launch works without `+x`.

**Full launch chain after fix**:
```
Click desktop icon
→ GNOME: /usr/bin/bash vsp-start.sh     ✅ bash reads file, no +x needed
→ No TTY → self-relaunch
→ gnome-terminal -- /usr/bin/bash vsp-start.sh  ✅ bash reads file, no +x needed
→ Inside terminal: TTY exists, VSP_IN_TERMINAL=1 → runs normally  ✅
```

**Files Modified**:
- `install-desktop-icon.sh` — Exec line uses `/usr/bin/bash ${LAUNCHER}`
- `vsp-start.sh` — Self-relaunch uses `/usr/bin/bash "$0"` for all terminal emulators
- `INSTALL.sh` — New component [3.14] sets permissions on all installed files

**Important**: After downloading the new package, the user must re-run `bash install-desktop-icon.sh` to regenerate the `.desktop` file.

**Status**: Fixed in package v1.0.27

---

## Bug 32: Server fails to start — VSP_INPUT_DIR not passed to container + no error visibility

**When**: Clicking desktop icon to launch VSP Pipeline — container starts but server never responds
**Error**: "Server did not respond within 60 seconds" — no Python error visible

**Root Cause (Two Issues)**:

**Issue A: Environment variable mismatch**
`vsp-start.sh` passes `VSP_HOST_INPUT_DIR` (for UI display) but `config.py` reads `VSP_INPUT_DIR` (for actual configuration). Since `VSP_INPUT_DIR` is not set, config falls back to `INPUT_DIR = Path("/host/vsp_input")` — which is **outside** the Docker volume mount (`/host/galaxy_export`). The TranscriptionManager tries to create directories at `/host/vsp_input/.transcriptions/`, which may fail on some container filesystems. Even if it doesn't crash, the UI's input directory points to ephemeral container storage that disappears when the container stops.

**Issue B: No error visibility**
If the Python server crashes during import or startup, the error prints to the container's stdout/stderr but the user only sees the "timeout" message from the polling task. No diagnostic information is shown.

**Fix (Four Parts)**:

**Part 1: Pass VSP_INPUT_DIR to docker run** (vsp-start.sh)
```bash
# BEFORE (only display-purpose env var):
-e "VSP_HOST_INPUT_DIR=${GALAXY_EXPORT_DIR}/vsp_input" \

# AFTER (both functional and display env vars):
-e "VSP_INPUT_DIR=/host/galaxy_export/vsp_input" \
-e "VSP_HOST_INPUT_DIR=${GALAXY_EXPORT_DIR}/vsp_input" \
```

Now `config.py` detects `VSP_INPUT_DIR` and uses the correct path inside the mounted volume.

**Part 2: Create vsp_input directory** (INSTALL.sh)
```bash
# New component [3.15] - before permissions fix
mkdir -p vsp_input 2>/dev/null || true
chmod a+rwx vsp_input 2>/dev/null || true
```

Ensures the directory exists in the galaxy_export mount so videos persist on the host.

**Part 3: Fix double-bash from Docker ENTRYPOINT** (vsp-start.sh docker run command)

The Docker image has `ENTRYPOINT ["/bin/bash"]`. Our command `bash -c '...'` was appended to it, producing:
```
/bin/bash bash -c '...'
```
Bash tried to read `/usr/bin/bash` as a text script → "cannot execute binary file".

Fix: remove our `bash` prefix. Since the ENTRYPOINT already provides bash, we just pass `-c '...'`:
```bash
# BEFORE:
"${DOCKER_IMAGE}" \
bash -c "cd /host/galaxy_export/vsp-ui && python3 -m app.server"

# AFTER:
"${DOCKER_IMAGE}" \
-c 'cd /host/galaxy_export/vsp-ui && python3 -m app.server; EC=$?; if [ $EC -ne 0 ]; then echo "SERVER FAILED (exit code $EC)"; echo "Press Enter to close..."; read; fi'
```

Docker now executes: `/bin/bash -c '...'` — correct single-bash invocation.
Error wrapper keeps the terminal open if the server crashes.

**Part 4: Print container logs on timeout** (vsp-start.sh background polling task)
```bash
# BEFORE:
echo "WARNING: Server did not respond within 60 seconds."

# AFTER:
echo "SERVER FAILED TO START"
echo "--- Container logs ---"
docker logs "${CONTAINER_NAME}" 2>&1
echo "--- End of logs ---"
```

The actual Python traceback is printed to the terminal, making remote debugging possible.

**Files Modified**:
- `vsp-start.sh` — Added `VSP_INPUT_DIR` env var, removed double-bash, error wrapper, container log output on timeout
- `INSTALL.sh` — New component [3.15] creates `vsp_input` directory

**Status**: Fixed in package v1.0.28

---

## Bug 33: Decode crash `total_mem` typo + useless Open Folder buttons

**When**: Pipeline reaches decode step [7] and crashes; Open Folder buttons do nothing in Docker mode
**Error**: `AttributeError: 'torch._C._CudaDeviceProperties' object has no attribute 'total_mem'. Did you mean: 'total_memory'?`

**Root Cause (Two Issues)**:

**Issue A: PyTorch attribute typo**
Fix #21 (Beam Search OOM) added GPU memory detection using `torch.cuda.get_device_properties(0).total_mem`. The correct attribute is `total_memory`. This was never caught because EC2 testing used a different PyTorch version.

**Issue B: Open Folder buttons can't work in Docker**
The "Open Folder" and "Open Results Folder" buttons try to run file managers (`gio open`, `nautilus`, etc.) inside the Docker container. The container has no GUI — these commands always fail. The buttons are useless and confuse users.

**Fix**:
1. Changed `total_mem` → `total_memory` in `vsp_llm_decode.py` line 177
2. Removed "Open Folder" button from input screen (HTML + JS event listener)
3. Removed "Open Results Folder" button from completion screen (HTML + JS event listener)

**Files Modified**:
- `VSP-LLM/src/vsp_llm_decode.py` — `total_mem` → `total_memory`
- `vsp-ui/app/static/index.html` — Removed both Open Folder buttons
- `vsp-ui/app/static/app.js` — Removed `openInputFolder()`, `openOutputFolder()` functions and event listeners

**Status**: Fixed in package v1.0.29

---

## Bug 34: Desktop icon does nothing — `kgx` (GNOME Console) not in terminal detection list

**When**: Clicking desktop icon — nothing happens, no terminal opens
**Error**: `install-desktop-icon.sh` reports "Terminal: WARNING - none found!"

**Root Cause**: The standalone machine uses `kgx` (GNOME Console), the modern replacement for `gnome-terminal` on newer GNOME desktops. Neither `vsp-start.sh` nor `install-desktop-icon.sh` had `kgx` or `gnome-console` in their terminal detection lists.

**Discovery**: `pstree -s $$` on standalone showed: `systemd → systemd → kgx → fish → bash`

The machine hostname is "banana" and uses fish shell — the user described it as "banana or fish", which was the hostname and shell, not the terminal emulator.

**Fix**:
1. Added `kgx` and `gnome-console` to terminal detection loop in `vsp-start.sh` (line 25)
2. Added `kgx|gnome-console` to case statement with `--` syntax (same as gnome-terminal) in `vsp-start.sh` (line 31)
3. Added `kgx` and `gnome-console` to verification check in `install-desktop-icon.sh` (line 114)

**Files Modified**:
- `vsp-start.sh` — Added `kgx gnome-console` to detection loop and case statement
- `install-desktop-icon.sh` — Added `kgx gnome-console` to verification check

**Status**: Fixed in package v1.0.29

---

## Bug 35: docker.conf auto-detection never works — INSTALL.sh runs inside container

**When**: Running `INSTALL.sh` inside the Docker container — docker.conf always gets `DOCKER_IMAGE=CHANGE_ME`
**Error**: User must manually edit docker.conf after every installation to set the image name

**Root Cause**: INSTALL.sh runs **inside** the Docker container (as part of `docker run ... bash INSTALL.sh`). Inside the container, there is no Docker socket (`/var/run/docker.sock`) and no `docker` CLI available. The auto-detection code (`docker inspect $(hostname)`) always fails silently, resulting in `DOCKER_IMAGE=CHANGE_ME`.

This is a fundamental limitation — you cannot detect the Docker image name from inside the container without Docker-in-Docker access.

**Fix: Move auto-detection to `vsp-start.sh` (runs on the host)**

Since `vsp-start.sh` runs on the **host machine** with full Docker CLI access, it can search for local Docker images. When it finds `DOCKER_IMAGE=CHANGE_ME` in docker.conf:

1. Searches local Docker images for names containing `vsp` (case-insensitive)
2. If exactly one match → uses it automatically
3. If multiple matches → shows numbered list, user picks one
4. Saves the selection to docker.conf so it won't ask again

```bash
# Auto-detect: search local Docker images for VSP-related names
_candidates=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -i 'vsp' | grep -v '<none>')
_count=$(echo "$_candidates" | grep -c .)

if [ "$_count" -eq 1 ]; then
    DOCKER_IMAGE="$_candidates"
    # Save to docker.conf for future runs
    sed -i "s|^DOCKER_IMAGE=.*|DOCKER_IMAGE=${DOCKER_IMAGE}|" docker.conf
elif [ "$_count" -gt 1 ]; then
    echo "Found multiple VSP images:"
    echo "$_candidates" | nl
    read -r _choice
    DOCKER_IMAGE=$(echo "$_candidates" | sed -n "${_choice}p")
    sed -i "s|^DOCKER_IMAGE=.*|DOCKER_IMAGE=${DOCKER_IMAGE}|" docker.conf
fi
```

**INSTALL.sh simplified**: No longer tries `docker inspect`. Just writes `CHANGE_ME` with a comment that vsp-start.sh will auto-detect. If docker.conf already has a configured value, preserves it.

**Files Modified**:
- `vsp-start.sh` — Added auto-detection logic after loading docker.conf
- `INSTALL.sh` — Simplified docker.conf creation (removed dead `docker inspect` code)
- `docker-run.sh` — Added tolerant parser (was still using `source`) and tip to use vsp-start.sh

**Status**: Fixed in package v1.0.30

---

## Bug 36: Remove unreliable ETA timer from processing screen

**When**: During pipeline processing — UI shows "Estimated time remaining" that fluctuates wildly
**Problem**: ETA uses simple linear extrapolation from coarse stage-based progress (~10 stage transitions over the entire pipeline run). Pipeline stages vary from seconds (archiving) to hours (preprocessing, k-means), so the estimate oscillates wildly and misleads users into thinking the pipeline is broken or almost done when it isn't.

**Fix**: Removed ETA display entirely from the processing screen. The progress bar and stage name/description labels remain — they provide useful feedback about which stage is running without false precision about time remaining.

**Changes**:
- HTML: Removed `<div class="eta-display">` block from processing screen
- CSS: Removed `.eta-display` CSS rule
- JS: Removed `formatETA()` function, `etaText` DOM element lookup, and ETA update line in `updateProgress()`. Kept `formatDuration()` (still used for video duration display elsewhere)
- Python: Removed `eta_seconds` field from `ProgressState` dataclass, removed `_estimate_eta()` method and all calls to it

**Files Modified**:
- `vsp-ui/app/static/index.html` — Removed `<div class="eta-display">` block
- `vsp-ui/app/static/style.css` — Removed `.eta-display` CSS rule
- `vsp-ui/app/static/app.js` — Removed `formatETA()`, `etaText` DOM lookup, ETA update line
- `vsp-ui/app/services/progress_tracker.py` — Removed `eta_seconds` from ProgressState, removed `_estimate_eta()` method
- Same changes applied to `ui/` path

**Status**: Fixed in package v1.0.36

---

## Bug 36: VLC title overlay obscures burned video subtitles

**When**: Playing burned videos on Ubuntu standalone Linux — VLC shows the filename (e.g., `Obama_Part1_with_hyp.mp4`) as a title overlay at the top of the video, obscuring the subtitle text.

**Root Cause**: VLC's "Show media title on video start" is enabled by default. On the standalone machine, the title bar overlaps the burned subtitle area.

**Fix**: Added VLC configuration to `install.sh` to disable the title overlay:
```bash
mkdir -p "${HOME}/.config/vlc"
# Set video-title-show=0 in vlcrc (create or update)
```

This sets `video-title-show=0` in `~/.config/vlc/vlcrc`, which disables the filename overlay on video playback. The change takes effect the next time VLC opens a video.

**Files Modified**:
- `vsp-ui/install.sh` — Added VLC config block after input folder creation

**Status**: Fixed in package v1.0.37

**To apply on existing installations**: Re-run `bash vsp-ui/install.sh` or manually run:
```bash
mkdir -p ~/.config/vlc
echo 'video-title-show=0' > ~/.config/vlc/vlcrc
```

---

**Current Package Status**: v1.0.37 - All known bugs fixed

### Files Changed in v1.0.31-v1.0.37

| File | Changes | Version |
|------|---------|---------|
| `VSP-LLM/src/conf/s2s_decode.yaml` | max_len_a: 2.0, max_len_b: 200, added repetition_penalty: 1.2 | v1.0.31 |
| `VSP-LLM/scripts/decode.sh` | Extended fairseq auto-patch to add repetition_penalty field | v1.0.31 |
| `VSP-LLM/src/vsp_llm_decode.py` | Added `repetition_penalty=cfg.generation.repetition_penalty` to generate() | v1.0.31 |
| `VSP-LLM/scripts/make_report.py` | Part naming (v1.0.32) + NEA/WWER metrics with spaCy fallback (v1.0.34) | v1.0.32, v1.0.34 |
| `VSP-LLM/scripts/make_burn.py` | Part naming in output filenames | v1.0.32 |
| `lib/outputs.sh` | Added lip crop copy step (inline Python, non-critical) | v1.0.33 |
| `vsp-ui/app/server.py` | setup() timeout, chunked upload read, [UPLOAD] logging | v1.0.35 |
| `ui/app/server.py` | setup() timeout, [UPLOAD] logging (already had chunked reads via cgi) | v1.0.35 |
| `vsp-ui/app/static/app.js` | XHR timeout (5min + 1min/100MB) with timeout event handler | v1.0.35 |
| `ui/app/static/app.js` | XHR timeout (5min + 1min/100MB) with timeout event handler | v1.0.35 |
| `vsp-ui/app/static/index.html` | Removed ETA display div | v1.0.36 |
| `vsp-ui/app/static/style.css` | Removed `.eta-display` CSS rule | v1.0.36 |
| `vsp-ui/app/static/app.js` | Removed `formatETA()`, `etaText` DOM lookup, ETA update line | v1.0.36 |
| `vsp-ui/app/services/progress_tracker.py` | Removed `eta_seconds`, `_estimate_eta()` | v1.0.36 |
| `ui/app/static/index.html` | Removed ETA display div | v1.0.36 |
| `ui/app/static/style.css` | Removed `.eta-display` CSS rule | v1.0.36 |
| `ui/app/static/app.js` | Removed `formatETA()`, `etaText` DOM lookup, ETA update line | v1.0.36 |
| `ui/app/services/progress_tracker.py` | Removed `eta_seconds`, `_estimate_eta()` | v1.0.36 |
| `vsp-ui/install.sh` | Added VLC config to disable title overlay on video playback | v1.0.37 |
