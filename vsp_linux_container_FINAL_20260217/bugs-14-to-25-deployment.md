# Bugs 14-25: Deployment & GPU Issues

> CUDA OOM, desktop launcher, Docker configuration, drag-and-drop upload.
> Split from BUGS_INSTALLING_CLIENT_STANDALONE.md. See also:
> - [Bugs Reference](bugs-reference.md) — Docker, lessons learned, package versions
> - [Bugs 1-13](bugs-1-to-13-installation.md) — Installation & setup
> - [Bugs 26-37](bugs-26-to-37-final.md) — Final fixes

## Bug 14: Decode CUDA OOM on 12GB GPU - memory accumulation across samples

**When**: Running pipeline Step 7 (VSP-LLM decode) on standalone computer with 12GB GPU
**Error**:
```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 86.00 MiB.
GPU 0 has a total capacity of 11.63 GiB of which 86.31 MiB is free.
Process 32883 has 11.53 GiB memory in use.
Of the allocated memory 11.05 GiB is allocated by PyTorch, and 164.09 MiB is reserved by PyTorch but unallocated.
```

**Root Cause**: Bug 11 fix increased `max_new_tokens` from 30 to 2048 to prevent truncated transcriptions. This worked on EC2 (24GB GPU) but caused CUDA OOM on the standalone's 12GB GPU. The crash occurred at sample 18/49 — not from one bad video, but from **GPU memory accumulating** across samples.

PyTorch showed 11.05 GiB allocated (model is only ~4.5 GB), meaning ~6.5 GB of leaked/unreleased KV caches from the previous 17 samples. With the old `max_new_tokens=30`, each leaked cache was tiny (~75 MB); with 2048, each is much larger, filling 12 GB after ~17 samples.

**Fix (Three Parts)**:

1. **Smart memory cleanup between samples** — `torch.cuda.empty_cache()` after every sample (<1ms), plus `gc.collect()` when free GPU memory drops below 2 GB. Prevents memory accumulation.

2. **Dynamic max_length per sample** — Instead of fixed `max_new_tokens=2048`, calculates per-sample limit using existing config values: `min(max_len, max_len_a × src_tokens + max_len_b)`. With `max_len_a=3.0, max_len_b=300`, typical 12s segments get ~750 max tokens (still 10× more than needed, no truncation risk). Prevents runaway generation from eating all memory.

3. **CUDA allocator optimization** — Added `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` to `decode.sh`. Reduces memory fragmentation as recommended by PyTorch.

**Files Modified**:
- `VSP-LLM/src/vsp_llm_decode.py` — Added `import gc`, dynamic max_length calculation, memory cleanup block
- `VSP-LLM/scripts/decode.sh` — Added `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`

**Status**: Fixed in package v1.0.11

---

## Bug 15: "Open Results Folder" button does nothing in UI

**When**: After pipeline completes, clicking "Open Results Folder" button on completion screen
**Error**: No visible error - button appears to do nothing. No folder opens, no feedback shown.

**Root Cause (Two Issues)**:

1. **Backend**: `open_folder()` used `subprocess.Popen()` fire-and-forget without checking if the process actually succeeded. On systems where `xdg-open` is found but fails silently (e.g., no DISPLAY, broken desktop session), the function returned `True` even though nothing opened. Also missing `gio open` which is the most reliable method on modern GNOME desktops.

2. **Frontend**: `openOutputFolder()` called the API but completely ignored the response. When `success: false` was returned, the user got no feedback at all.

**Fix**:

Backend (`server.py`):
- Added `gio open` as first method to try (most reliable on GNOME)
- After launching each command, waits 0.3s and checks exit code via `proc.poll()`
- If process exited with non-zero code, tries next command instead of returning `True`
- Only returns `True` if process is still running or exited with code 0

Frontend (`app.js`):
- `openOutputFolder()` now checks the API response
- If `success: false`, shows alert with the folder path so user can navigate manually

**Files Modified**:
- `vsp-ui/app/server.py` — Rewrote `open_folder()` with `gio open`, process exit checking
- `vsp-ui/app/static/app.js` — Added response check and user feedback in `openOutputFolder()`

**Status**: Fixed in package v1.0.12

---

## Bug 16: Desktop icon has hardcoded path and generic icon

**When**: Setting up desktop shortcut on a new machine
**Error**: Desktop icon fails to launch because `.desktop` file has `Exec=/home/ds/Desktop/galaxy_export/vsp-start.sh` hardcoded — only works for user `ds` with that exact folder location.

**Root Cause**: The `vsp-pipeline.desktop` file was created with absolute paths specific to one user's machine. The `install.sh` script copied it as-is without updating paths. Additionally, the icon was set to `video-display` (a generic system icon) instead of the project's peacock logo.

**Fix**:

1. **`vsp-pipeline.desktop`** — Changed to a template with `__INSTALL_DIR__` placeholders
2. **`install-desktop-icon.sh`** (NEW) — Host-side script that:
   - Auto-detects its own location via `BASH_SOURCE`
   - Generates `.desktop` file with correct `Exec` and `Icon` paths
   - Copies to `~/Desktop/` and `~/.local/share/applications/`
   - Marks as trusted on GNOME (`gio set metadata::trusted`)
3. **`vsp-ui/logo.png`** (NEW) — Peacock logo converted to 256x256 PNG for desktop icon
4. **`INSTALL.sh`** — Updated component [3.12] to copy the icon installer and logo

**Usage** (run on HOST, not inside container):
```bash
cd /path/to/galaxy_export
bash install-desktop-icon.sh
```

**Files Added**:
- `install-desktop-icon.sh` — Host-side desktop icon installer
- `vsp-ui/logo.png` — Peacock logo for desktop icon
- `vsp-ui/app/static/logo.jpeg` — Peacock logo for web UI header

**Files Modified**:
- `vsp-pipeline.desktop` — Changed to template with placeholders
- `INSTALL.sh` — Updated component [3.12]
- `vsp-ui/app/static/index.html` — Added logo image in header
- `vsp-ui/app/static/style.css` — Added logo styling

**Status**: Fixed in package v1.0.12

---

## Bug 17: install-desktop-icon.sh fails - chmod permission denied and wrong Desktop path

**When**: Running `bash install-desktop-icon.sh` on the host machine
**Error**:
```
chmod: changing permission of 'install-desktop-icon.sh': Operation not permitted
```
Also: Desktop icon not created because `$HOME/Desktop` doesn't match actual Desktop location (`/home/ds/Desktop`).

**Root Cause (Three Issues)**:

1. **`set -euo pipefail`** combined with `chmod +x` — the galaxy_export folder is on a filesystem that doesn't support chmod (e.g., mounted volume). With `set -e`, the script exits immediately on any error.

2. **`$HOME` not reliable** — On the standalone machine, `$HOME` may not be set to `/home/ds/` (e.g., if run via sudo or from a different context). The script used `${HOME}/Desktop` which didn't match the actual Desktop at `/home/ds/Desktop`.

3. **`.desktop` Exec line** — Used `Exec=/path/to/vsp-start.sh` which requires execute permission on the script file. On mounted filesystems where chmod fails, the icon would fail to launch.

**Fix**:

1. All `chmod` calls now have `2>/dev/null || true` — non-fatal on any filesystem
2. Desktop detection now tries multiple locations instead of trusting `$HOME`:
   - `$(getent passwd $(whoami))/Desktop` — real home from /etc/passwd
   - `$HOME/Desktop` — environment variable
   - `/home/$(whoami)/Desktop` — common Linux convention
   - `/home/ds/Desktop` — hardcoded fallback for known machine
3. `Exec=bash /path/to/vsp-start.sh` — uses `bash` prefix so execute permission isn't needed

**Files Modified**:
- `install-desktop-icon.sh` — Robust Desktop detection, non-fatal chmod, bash prefix in Exec

**Status**: Fixed in package v1.0.13

---

## Bug 18: Desktop shortcut fails - Docker detached mode kills server

**When**: Clicking the desktop icon (which runs `vsp-start.sh`) — server never becomes responsive, times out after 30 seconds
**Error**:
```
Waiting for server.............................. timeout!
ERROR: Server did not start in 30 seconds.
```
Running the same command interactively with `-it` instead of `-d` works fine.

**Root Cause**: `docker run -d` (detached mode) caused the container to exit silently. Multiple possible causes — TTY absence, ENTRYPOINT behavior, buffering, stale container name conflicts — but the exact cause could not be determined because `--rm` removed the container (and its logs) before inspection.

The user confirmed that `docker run --rm -it ... bash -c "cd /host/galaxy_export/vsp-ui && python3 -m app.server"` works perfectly — proving the server code is fine, only the Docker run mode was wrong.

**Fix: Switched from detached (`-d`) to foreground (`-it`) mode**

Since the `.desktop` file has `Terminal=true` (a terminal window is already opened), there's no need for detached mode. Running Docker in the foreground with `-it` is:
- **Proven to work** — it's the exact command the user ran manually
- **More transparent** — server output visible in the terminal window
- **Simpler** — no polling/timeout/diagnostic complexity needed
- **Self-cleaning** — closing the terminal stops the container

The browser is opened by a background task that polls for server readiness, launched before the foreground `docker run`.

```bash
# Background: wait for server then open browser
( while ! curl -s "${URL}/api/status" >/dev/null 2>&1; do sleep 1; done
  open_browser "${URL}"
) &

# Foreground: run Docker with -it (proven working)
docker run --rm -it --name vsp-pipeline --gpus all \
    -p 8765:8765 -v "${GALAXY_EXPORT_DIR}:/host/galaxy_export" \
    "${DOCKER_IMAGE}" \
    bash -c "cd /host/galaxy_export/vsp-ui && python3 -m app.server"
```

Also retained: stale container cleanup (`docker rm -f`) and port freeing (`fuser -k`) before starting.

**Files Modified**:
- `vsp-start.sh` — Replaced detached mode with foreground `-it` mode, background browser opener

**Status**: Fixed in package v1.0.14

---

## Bug 19: Fairseq max_len patch applied to wrong fairseq installation

**When**: Running pipeline Step 7 (VSP-LLM decode) on client standalone after running INSTALL.sh
**Error**:
```
Error merging 's2s_decode' with schema
Key 'max_len' not in 'GenerationConfig'
full_key: generation.max_len
reference_type=GenerationConfig
object_type=GenerationConfig
```

**Root Cause**: INSTALL.sh component [3.10] ran `patch_fairseq_max_len.py` which patches fairseq via `import fairseq` — this finds the **pip-installed** fairseq at `/workspace/vsp-llm-yoad-venv/lib/python3.10/site-packages/fairseq/`. However, `decode.sh` line 37 sets `PYTHONPATH="${ROOT}/fairseq:$PYTHONPATH"`, putting a **local** fairseq checkout at `/host/galaxy_export/VSP-LLM/fairseq/` first in the path. At decode runtime, Python imports from the local copy (which was never patched), not the pip-installed one.

**Evidence from logs**:
```
# Cython build confirms local fairseq exists:
copying build/lib.linux-x86_64-cpython-310/fairseq/data/data_utils_fast.cpython-310-x86_64-linux-gnu.so -> fairseq/data

# decode.sh PYTHONPATH puts local copy first:
export PYTHONPATH="${ROOT}/fairseq:$PYTHONPATH"
# Result: Python imports from /host/galaxy_export/VSP-LLM/fairseq/ (unpatched)
```

**Why INSTALL.sh patch didn't work**:
- INSTALL.sh activates venv, runs `python3 patch_fairseq_max_len.py`
- Without the PYTHONPATH override, `import fairseq` finds the pip-installed copy
- Patch applied to `/workspace/.../site-packages/fairseq/dataclass/configs.py`
- Decode runs with PYTHONPATH override, imports from `/host/galaxy_export/VSP-LLM/fairseq/dataclass/configs.py`
- Two different files — patch went to the wrong one

**Fix**: Added inline self-healing patch directly in `decode.sh`, **after** PYTHONPATH is set and **before** the decode command runs. This ensures the patch applies to whichever fairseq Python will actually import:

```bash
# Auto-patch fairseq GenerationConfig if max_len field is missing
# Must run AFTER PYTHONPATH is set so it patches the fairseq that decode will use
python3 -c "
import fairseq.dataclass.configs as c
if not hasattr(c.GenerationConfig, 'max_len'):
    src = c.__file__
    # ... insert max_len field before min_len ...
    print('Patched fairseq configs at: ' + src)
else:
    print('fairseq max_len field OK')
"
```

**Key design**: The patch is idempotent (safe to run multiple times) and runs with the exact same PYTHONPATH as decode, so it always patches the right file regardless of installation layout.

**Files Modified**:
- `VSP-LLM/scripts/decode.sh` — Added inline fairseq patch between PYTHONPATH setup and decode command

**Status**: Fixed in package v1.0.15

---

## Bug 20: docker.conf fails if user adds spaces around `=`

**When**: User edits `docker.conf` to set image name, types `DOCKER_IMAGE = vsp-llm-pipeline:latest` (with spaces around `=`)
**Error**:
```
/home/ds/Desktop/galaxy_export/docker.conf: line 7: DOCKER_IMAGE: command not found
```

**Root Cause**: `vsp-start.sh` used `source docker.conf` to load configuration. Bash `source` interprets each line as a command — `DOCKER_IMAGE = value` is parsed as running a command called `DOCKER_IMAGE` with `=` and `value` as arguments. Only `DOCKER_IMAGE=value` (no spaces) is valid variable assignment in bash.

Non-technical users naturally type spaces around `=` (as in most config file formats, INI files, YAML, etc.), making this a common and confusing error.

**Fix**: Replaced `source docker.conf` with a tolerant custom parser that handles:
- Spaces around `=` (e.g., `KEY = value`, `KEY =value`, `KEY= value`)
- Trailing whitespace
- Quoted values (single or double quotes)
- Comment lines (starting with `#`)
- Blank lines

```bash
# Tolerant parser using bash regex
while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue       # skip comments
    [[ -z "${line// /}" ]] && continue                  # skip blank lines
    if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*) ]]; then
        key="${BASH_REMATCH[1]}"
        val="${BASH_REMATCH[2]}"
        val="${val%"${val##*[![:space:]]}"}"             # trim trailing whitespace
        val="${val#\"}" ; val="${val%\"}"                 # strip double quotes
        val="${val#\'}" ; val="${val%\'}"                 # strip single quotes
        export "$key=$val"
    fi
done < "${SCRIPT_DIR}/docker.conf"
```

All of these formats now work identically:
```
DOCKER_IMAGE=vsp-llm-pipeline:latest
DOCKER_IMAGE = vsp-llm-pipeline:latest
DOCKER_IMAGE =vsp-llm-pipeline:latest
DOCKER_IMAGE= vsp-llm-pipeline:latest
DOCKER_IMAGE="vsp-llm-pipeline:latest"
DOCKER_IMAGE = "vsp-llm-pipeline:latest"
```

**Files Modified**:
- `vsp-start.sh` — Replaced `source docker.conf` with tolerant regex parser

**Status**: Fixed in package v1.0.16

---

## Bug 21: "Port already allocated" error when restarting desktop shortcut

**When**: Clicking the desktop icon a second time (or after a previous manual Docker run that wasn't stopped)
**Error**:
```
docker: Error response from daemon: driver failed programming external connectivity
on endpoint vsp-pipeline: Bind for 0.0.0.0:8765 failed: port is already allocated.
```

**Root Cause**: A previous Docker container (or other process) was still using port 8765. Docker refuses to start a new container if the port is already bound. This happens when:
1. User clicks the desktop icon, then closes the terminal and clicks again before the old container fully stops
2. User ran `docker run` manually in a terminal and forgot to stop it
3. A non-Docker process (e.g., another Python server) is using port 8765

Non-technical users cannot be expected to run `docker stop` or `fuser -k` commands.

**Fix**: Added comprehensive automatic cleanup before starting Docker, using three layers:

```bash
# Layer 1: Stop container by name
docker stop "${CONTAINER_NAME}" 2>/dev/null || true
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

# Layer 2: Find and stop ANY container using our port (even with different name)
PORT_CONTAINER=$(docker ps --filter "publish=${PORT}" --format '{{.Names}}' 2>/dev/null | head -1)
if [ -n "${PORT_CONTAINER}" ]; then
    docker stop "${PORT_CONTAINER}" 2>/dev/null || true
    docker rm -f "${PORT_CONTAINER}" 2>/dev/null || true
fi

# Layer 3: Kill any non-Docker process using the port (e.g., local Python server)
if command -v fuser &>/dev/null; then
    fuser -k ${PORT}/tcp 2>/dev/null || true
fi
```

**Why three layers**:
- Layer 1 handles the common case (same container name from a previous run)
- Layer 2 handles edge cases where a different container name is using the port
- Layer 3 handles non-Docker processes using the port (rare but possible)

All layers are non-fatal (`|| true`) — if nothing needs cleaning up, the script continues normally.

**Files Modified**:
- `vsp-start.sh` — Added three-layer port/container cleanup before `docker run`

**Status**: Fixed in package v1.0.16

---

## Bug 22: Desktop icon fails - "cannot execute binary file" (double bash)

**When**: Clicking the desktop icon after running `install-desktop-icon.sh`
**Error**:
```
/usr/bin/bash: /usr/bin/bash: cannot execute binary file
```

**Root Cause**: The `.desktop` file used `Terminal=true` and either `Exec=bash /path/to/vsp-start.sh` or `Exec=/path/to/vsp-start.sh`. The `Terminal=true` mechanism is handled inconsistently across desktop environments — some wrap the Exec value in an additional shell invocation, resulting in `bash bash /path/to/script`. Bash receives the literal string `bash` (i.e., `/usr/bin/bash`) as its script argument, tries to parse the bash binary as a shell script, and fails.

Both attempted fixes using `Terminal=true` failed:
- `Exec=bash /path/to/script` — double-bash from DE wrapping
- `Exec=/path/to/script` — same error persisted (DE still wrapping)

**Fix: Bypass `Terminal=true` entirely**

Instead of relying on the desktop environment to open a terminal (which is unreliable), the `.desktop` file now uses `Terminal=false` and explicitly launches the terminal emulator in the `Exec` line:

```
Exec=gnome-terminal -- /path/to/vsp-start.sh
Terminal=false
```

The `install-desktop-icon.sh` script auto-detects the available terminal emulator at install time:
1. `gnome-terminal` (Ubuntu/GNOME — most common)
2. `xfce4-terminal` (XFCE)
3. `mate-terminal` (MATE)
4. `konsole` (KDE)
5. `xterm` (fallback)

This approach gives us full control over terminal launching instead of delegating to the desktop environment's inconsistent `Terminal=true` handling.

**After fix**:
```
[Desktop Entry]
Exec=gnome-terminal -- /home/ds/Desktop/galaxy_export/vsp-start.sh
Terminal=false
```

**Important**: After downloading the new package, the user must re-run `bash install-desktop-icon.sh` to regenerate the `.desktop` file.

**Files Modified**:
- `install-desktop-icon.sh` — Auto-detect terminal emulator, use explicit `Exec=gnome-terminal -- /path`, set `Terminal=false`

**Status**: Fixed in package v1.0.18

---

## Bug 23: Desktop icon "has errors" or "points to program without permission"

**When**: Clicking the regenerated desktop icon after Bug 22 fix
**Error**: GNOME shows dialog "This desktop file has errors" or "points to a program without permission"

**Root Cause (Two Issues)**:

1. **Relative command in Exec**: The `.desktop` Exec line had `gnome-terminal` (just the command name) instead of `/usr/bin/gnome-terminal` (full path). Desktop files don't inherit the user's shell `PATH` — GNOME validates the Exec line and rejects it if the first token isn't an absolute path to an executable.

2. **Missing execute permission**: GNOME requires both the `.desktop` file itself AND the target script to be executable (`chmod +x`). If either lacks the execute bit, GNOME shows the "without permission" error.

**Fix**:

1. Resolve terminal emulator to its **full absolute path** using `command -v`:
   ```bash
   # BEFORE:
   TERM_CMD="gnome-terminal"
   EXEC_LINE="${TERM_CMD} -- ${LAUNCHER}"
   # Result: Exec=gnome-terminal -- /path/to/vsp-start.sh  ❌

   # AFTER:
   TERM_PATH="$(command -v gnome-terminal)"   # → /usr/bin/gnome-terminal
   EXEC_LINE="${TERM_PATH} -- ${LAUNCHER}"
   # Result: Exec=/usr/bin/gnome-terminal -- /path/to/vsp-start.sh  ✅
   ```

2. `chmod +x` applied to both `vsp-start.sh` and the generated `.desktop` file (already present from earlier fixes).

**Files Modified**:
- `install-desktop-icon.sh` — Resolve terminal to absolute path via `command -v`, use full path in Exec line

**Status**: Fixed in package v1.0.19

---

## Bug 24: Desktop icon shows X symbol / no icon / not trusted

**When**: After running `install-desktop-icon.sh`, the desktop shows a broken icon with an X symbol instead of the peacock logo
**Error**: GNOME shows X symbol, "untrusted application", or no icon at all

**Root Cause**: Modern GNOME (Ubuntu 22.04+) has increasingly strict validation and trust requirements for `.desktop` files on the Desktop. Even with `chmod +x` and `gio set metadata::trusted true`, GNOME may still reject the file due to:
- Trust metadata not persisting across sessions
- Desktop file validation failures (strict format checking)
- Icon path validation
- Different GNOME versions handling trust differently

The `.desktop` file approach is fundamentally fragile on the Desktop surface — it works reliably from `~/.local/share/applications/` (app menu) but the Desktop has extra trust/validation layers.

**Fix: Dual strategy — symlink + .desktop**

Instead of relying solely on `.desktop` files, the installer now creates **two** launch methods:

1. **`VSP-Pipeline.sh`** — A symlink (or copy) of `vsp-start.sh` placed directly on the Desktop. When double-clicked, GNOME's file manager prompts "Run in Terminal?" → user clicks yes → it works. No `.desktop` trust issues, no icon validation, no GNOME metadata quirks.

2. **`vsp-pipeline.desktop`** — Still installed to `~/.local/share/applications/` for the applications menu/launcher (where `.desktop` files work reliably). Also placed on Desktop as a backup.

**Three ways to launch**:
- **Option A**: Double-click `VSP-Pipeline.sh` on Desktop → "Run in Terminal" → works
- **Option B**: Search "VSP Pipeline" in applications menu → works
- **Option C**: Open terminal, run `vsp-start.sh` directly → works

**Files Modified**:
- `install-desktop-icon.sh` — Added symlink creation on Desktop alongside `.desktop` file

**Status**: Fixed in package v1.0.20

---

## Bug 25: Desktop launch unreliable — self-relaunching terminal approach

**When**: All previous desktop icon fixes (Bugs 18, 22-24) were fragile and environment-dependent
**Error**: Various — double bash, permission denied, untrusted, X symbol — depending on GNOME version and configuration

**Root Cause**: The fundamental problem was trying to control terminal launching from the `.desktop` file side. Every approach had edge cases:
- `Terminal=true` — desktop environment wraps in extra bash (Bug 22)
- `Terminal=false` with `gnome-terminal` in Exec — GNOME rejects for trust/path reasons (Bugs 23-24)
- Symlink on Desktop — file manager may open in text editor instead of executing

**Fix: Self-relaunching script**

Moved terminal detection and launching INTO `vsp-start.sh` itself. The script checks if it's running in a terminal (`-t 0` and `-t 1` test for stdin/stdout being a TTY). If not, it re-execs itself inside a detected terminal emulator:

```bash
# At the very top of vsp-start.sh:
if [ ! -t 0 ] && [ ! -t 1 ] && [ "${VSP_IN_TERMINAL:-}" != "1" ]; then
    for _term in gnome-terminal xfce4-terminal mate-terminal konsole xterm; do
        _term_path="$(command -v "$_term" 2>/dev/null || true)"
        if [ -n "$_term_path" ] && [ -x "$_term_path" ]; then
            export VSP_IN_TERMINAL=1
            case "$_term" in
                gnome-terminal) exec "$_term_path" -- "$0" "$@" ;;
                *)              exec "$_term_path" -e "$0" "$@" ;;
            esac
        fi
    done
    exit 1
fi
```

**Why this works**:
1. `.desktop` file is now dead simple: `Exec=/path/to/vsp-start.sh`, `Terminal=false`
2. When GNOME launches the script (no TTY), it detects this and runs `gnome-terminal -- /path/to/vsp-start.sh`
3. Inside gnome-terminal (with TTY), it detects the terminal and runs normally
4. `VSP_IN_TERMINAL=1` prevents infinite re-launch loops
5. When run from an existing terminal, TTY is already present → runs directly (no re-launch)

**Why this is more reliable**:
- Doesn't depend on how the DE handles `Terminal=true`
- Doesn't depend on `.desktop` file trust/validation
- Works from any launch method (icon, file manager, script)
- Single point of control (the script itself)

The installer now also prints verification checks and fallback instructions.

**Files Modified**:
- `vsp-start.sh` — Added self-relaunch guard at top of script
- `install-desktop-icon.sh` — Simplified to `Exec=/path/to/vsp-start.sh` + `Terminal=false`, added verification output

**Status**: Fixed in package v1.0.21
