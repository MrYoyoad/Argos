# Container Deployment Lessons — May 2026

A consolidated record of every bug found while building the new air-gapped VSP client image (`vsp-llm-pipeline:client-build-001`). Audience: anyone doing this kind of deployment again.

## Context

- Goal: produce ONE clean self-contained Docker image (~58–66 GB) that runs the full VSP pipeline air-gapped on a client machine. Single tag, single tarball, no layered patch flows.
- Source of truth: `/home/ubuntu/lib/`, `/home/ubuntu/run_flat_english_pipeline.sh`, `/home/ubuntu/VSP-LLM/`, `/home/ubuntu/auto_avsr/`, `/home/ubuntu/av_hubert/`, `/home/ubuntu/docs/_research-tools/generators/`, `/home/ubuntu/vsp-ui/`.
- Build context: `/home/ubuntu/vsp_docker/container_payload_20260507/` (renamed from the legacy `galaxy_export/` on 2026-05-07).
- Reference deployment: `/home/ubuntu/vsp_linux_container_FINAL_20260217/` — the previously-shipped client kit. Its `INSTALL.sh` is the canonical list of files that need container-specific patches. Use it as the path-translation gold standard.

## Architecture

| | EC2 (dev) | Container (client) |
|---|---|---|
| Pipeline lives at | `/home/ubuntu/...` | `/workspace/...` |
| Input videos | `~/vsp_input/` | `/data/in` (bind-mount, `:ro` in CLI mode, `:rw` in UI mode) |
| Output dir | alongside input | `/data/out` (bind-mount, fresh per run) |
| Transcriptions | `~/vsp_input/.transcriptions/` | `/data/transcriptions` (bind-mount, persistent across runs, host: `~/vsp-transcriptions/<dataset>/`) |
| Internet | yes | NO — must run fully offline once installed |

## Bug catalog

Each entry: **what failed**, **why**, **fix**, **what to grep for next time**.

### 1. `--download_root` vs `--whisper_cache` mismatch
**Fail:** Whisper ASR step crashed: `unrecognized arguments: --download_root /root/.cache/whisper`.
**Why:** `lib/asr.sh` was synced from EC2 main (uses `--download_root`) but `auto_avsr/asr_to_words_notime.py` in container_payload_20260507 was an older version (used `--whisper_cache`). Sync of `lib/` only is not enough — must also sync `auto_avsr/`.
**Fix:** rsync the EC2 `auto_avsr/`, `av_hubert/`, `VSP-LLM/scripts/`, `VSP-LLM/src/`, `docs/_research-tools/generators/` into container_payload_20260507. Use the previous kit's INSTALL.sh as the canonical list of patched groups.
**Grep:** `grep -rn 'whisper_cache' container_payload_20260507/auto_avsr/` should be 0 (it's `download_root` now).

### 2. `flat_to_lrs3_preperation.sh` hardcoded venv path
**Fail:** Step 4 LRS3 prep: `/home/ubuntu/auto_avsr/pre-process-venv/bin/activate: No such file or directory`.
**Why:** EC2 version has hardcoded `/home/ubuntu/auto_avsr/pre-process-venv`. Doesn't exist in container at `/workspace/`.
**Fix:** Adopt previous kit's path-translated version (multi-fallback `VENV` detect: env var → `/workspace/auto_avsr/pre-process-venv` → `${_BASE_DIR}/auto_avsr/pre-process-venv` → `$HOME/auto_avsr/pre-process-venv`). Auto-detect `_BASE_DIR` from script's own location.
**Grep:** `grep -nE '/home/ubuntu' av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh` should only match comments.

### 3. fairseq `GenerationConfig` missing `max_len` + `repetition_penalty`
**Fail:** Decode step would crash silently or use wrong defaults.
**Why:** EC2's fairseq has these patched; the editable install via `pip install -e git+...` clones a fresh fairseq that DOESN'T have them. Bug 11/19/22 from the previous kit's bug log.
**Fix:** `decode.sh` runs a runtime monkey-patch (sed) that injects `max_len: int` and `repetition_penalty: float` fields into `fairseq.dataclass.configs.GenerationConfig` if missing. Adopt the previous kit's `decode.sh` wholesale.
**Grep:** `grep -c "max_len\|repetition_penalty" VSP-LLM/scripts/decode.sh` should be ≥ 7.

### 4. `nbest_aggregate.py not found` at runtime
**Fail:** N-best aggregation skipped → no `aggregated.json`, no MBR display.
**Why:** `lib/outputs.sh` looked for the script at `${HOME}/lib/nbest_aggregate.py` — `$HOME` is `/root` in the container, not `/workspace`.
**Fix:** Add fallback to script-derived dir: `$(dirname "${BASH_SOURCE[0]}")/nbest_aggregate.py` (which resolves to `/workspace/lib/nbest_aggregate.py`).
**Grep:** `grep -nE 'nbest_aggregate' lib/outputs.sh` should show the BASH_SOURCE-based fallback.

### 5. `compute_word_agreement.py` fails with `ModuleNotFoundError: matplotlib`
**Fail:** Agreement-aware confidence bands silently degraded.
**Why:** `compute_word_agreement.py` imports `analyze_beam_variance.py`, which imports `matplotlib`. Matplotlib is in the `pre-process-venv` Dockerfile pin list but NOT in the `vsp-llm-yoad-venv` pin list. The agreement script runs in the vsp venv.
**Fix:** Add `matplotlib==3.9.4` to the Dockerfile IS-deps install (alongside sentence-transformers, Metaphone, etc.).
**Grep:** check via `docker run --rm <image> /workspace/vsp-llm-yoad-venv/bin/python -c "import matplotlib"` — must succeed.

### 6. spaCy install fails offline at runtime
**Fail:** NEA / WWER metrics degrade silently. `lib/outputs.sh` tries `pip install spacy` at runtime; fails with `Building build dependencies: error`.
**Why:** Local `spacy_wheels/` has cp311 wheels but container venv is cp39. Online fallback fails air-gapped.
**Fix:** Pre-install at build time: `RUN pip install spacy==3.8.11 thinc==8.3.9 && python -m spacy download en_core_web_sm`. Pin to 3.8.11 because 3.8.13+ requires `thinc>=8.3.12` which has no cp39 wheel.
**Grep:** `docker run --rm <image> /workspace/vsp-llm-yoad-venv/bin/python -c "import spacy; spacy.load('en_core_web_sm')"` — must succeed.
**Build cost:** ~21 min — spaCy compiles from sdist (no cp39 binary wheel), Cython phase is slow.

### 7. Whisper cache layout — extra `whisper/` subdir
**Fail:** Whisper re-downloads `medium.pt` (1.4 GB) at runtime even though cache is in the image.
**Why:** `container_payload_20260507/whisper_cache/` had layout `whisper_cache/whisper/medium.pt`. The Dockerfile copy `cp -r /workspace/whisper_cache/. /root/.cache/whisper/` produced `/root/.cache/whisper/whisper/medium.pt` — extra subdir. Whisper looks for `/root/.cache/whisper/medium.pt` (no nesting).
**Fix:** Flatten in `container_payload_20260507/whisper_cache/` so file is at `whisper_cache/medium.pt` (no extra subdir).
**Grep:** `ls container_payload_20260507/whisper_cache/` → should show `medium.pt` directly, not a `whisper/` subdir.
**Air-gapped impact:** Critical. With internet at build time it works (Whisper just re-downloads). Without internet at client install it fails.

### 8. Step 1.5 transcription save crashes on read-only input mount
**Fail:** `mkdir: cannot create directory '/data/in/.transcriptions': Read-only file system`.
**Why:** `lib/asr.sh` saves transcriptions to `${RAW_DIR}/.transcriptions/`. Launcher mounts input `:ro` for safety.
**Fix (architecturally correct):** Add `VSP_TRANSCRIPTIONS_DIR` env var. Launcher creates `~/vsp-transcriptions/<dataset>/` on host and bind-mounts as `/data/transcriptions`. `lib/asr.sh` Steps 0.6 (read) and 1.5 (save) prefer this env var over `RAW_DIR/.transcriptions`. Persistent across runs AND across container restarts.
**Grep:** `grep -c VSP_TRANSCRIPTIONS_DIR lib/asr.sh` should be ≥ 5.

### 9. `lib/outputs.sh` prune ran BEFORE export
**Fail:** Container output dir got only 2 HTML files instead of full set (report.csv, aggregated.json, IS, lip-crops...).
**Why:** Default mode prunes `report_dir` to `report.html` + `confidence_breakdown.html` only. Prune ran BEFORE the VSP_OUTPUT_DIR export hook → export got the pruned set.
**Fix:** Reorder — export first, prune second. Container always gets the full artifact set.
**Grep:** in `lib/outputs.sh`, the `Pruning intermediates` block must come AFTER the `VSP_OUTPUT_DIR` export hook. `grep -n 'Pruning\|VSP_OUTPUT_DIR.*Export' lib/outputs.sh` should show export before prune.

### 10. `vsp-ui/app/config.py` env detection misses flat layout
**Fail:** UI mode would mis-detect EC2 layout, look for `~/vsp_input/` which doesn't exist in container.
**Why:** `_detect_environment()` checks `/host/container_payload_20260507` (legacy) and `/workspace/container_payload_20260507` (legacy), but our flat layout has container_payload_20260507 contents AT `/workspace/`, not in a subdir.
**Fix:** Add a first-priority branch: `if Path("/workspace/run_flat_english_pipeline.sh").exists() and Path("/workspace/lib/config.sh").exists(): base_dir = Path("/workspace"); input_dir = Path(env_or "/data/in")`.
**Grep:** `grep -A3 'Container — flat layout' vsp-ui/app/config.py`.

### 11. `transcription_manager.py` ignores `VSP_TRANSCRIPTIONS_DIR`
**Fail:** UI's manual transcription editing would still write to `INPUT_DIR/.transcriptions` (read-only in container).
**Fix:** `_get_transcriptions_dir()` reads `os.environ.get("VSP_TRANSCRIPTIONS_DIR")` first, falls back to `INPUT_DIR/.transcriptions`.

### 12. UI server bound to 127.0.0.1 inside container
**Fail:** Even with `docker -p 8080:8080`, server isn't reachable from host because it binds localhost-only inside the container.
**Fix:** Make `SERVER_HOST` and `SERVER_PORT` env-var-overridable in `vsp-ui/app/config.py`. `vsp-start.sh` passes `-e VSP_UI_HOST=0.0.0.0 -e VSP_UI_PORT=8080`.

### 13. HuggingFace libraries phone home for model metadata
**Fail:** `AutoTokenizer/AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")` would attempt online metadata check even with cached files.
**Fix:** Set `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HF_DATASETS_OFFLINE=1` in BOTH launchers (vsp-pipeline.sh and vsp-start.sh) on the docker run command. Don't set in Dockerfile — would break `python -m spacy download` at build time.

### 14. NIV column missing from report.csv
**Fail:** `report.csv` had `is_score, is_tier, is_label` (where `is_label` is "Fair"/"Good"/etc, the tier name) but NO `niv` column with the Y/P/N verdict.
**Fix:** `make_report.py` imports `niv_label` from `generate_intelligibility_scores`, adds `"niv"` to `csv_header` when `--compute-is`, computes `niv_label(score)` per row.

### 15. Bloat in container_payload_20260507
**Fail:** Image was 66 GB. Could be smaller.
**Why:** `auto_avsr/flat/` (1.2 GB old EC2 videos), `auto_avsr/preprocess_ready_flat/` (1.2 GB), `auto_avsr/preprocessed_flat_seg4/` (305 MB), training tarballs `english_1000_subset_hrz*.tar.gz` (1.2 GB), unused `VSP-LLM/checkpoints/checkpoint_freeze.pt` (3.9 GB), `av_hubert/avhubert_flat/` duplicate (7 MB).
**Fix:** Delete from container_payload_20260507 before final build. Saves ~8 GB. Final image ~58 GB.
**Grep before final build:**
```bash
du -sh container_payload_20260507/auto_avsr/{flat,preprocess_ready_*,preprocessed_*,*.tar.gz,backups_flat} \
       container_payload_20260507/VSP-LLM/checkpoints/checkpoint_freeze.pt \
       container_payload_20260507/av_hubert/avhubert_flat 2>/dev/null
```
All should report "No such file or directory."

### 16. `segment_vid_dir` pointed at audio-stripped mouth crops
**Fail (subtle):** Whisper running on mouth crops → no audio → emits silent fillers.
**Why:** `lib/asr.sh` had `local segment_vid_dir="$prep_root/${data_name}/${data_name}_video_${dir_suffix}"` (mouth crops, no audio). Should be the normalized full-frame videos which have audio.
**Fix:** Adopt previous kit's pattern: `local segment_vid_dir="$auto_avsr_dir/${data_name}"` (full-frame, audio preserved).

### 17. Local fairseq fork missing `do_sample` / `top_p` fields
**Fail:** Decode crashes at `model.generate()` with
```
omegaconf.errors.ConfigAttributeError: Key 'do_sample' is not in struct
  full_key: generation.do_sample
File "/host/galaxy_export/VSP-LLM/src/vsp_llm_decode.py", line 301, in _main
    do_sample=cfg.generation.do_sample,
```
**Why:** `decode.sh` exports `PYTHONPATH=${ROOT}/fairseq:$PYTHONPATH`, pinning the local fairseq fork at `/host/galaxy_export/VSP-LLM/fairseq/`. That fork is older than the EC2 fork and lacks four custom fields the decoder reads:
- `max_len`, `repetition_penalty` (already patched by `decode.sh`'s monkey-patch — Patches 1 + 2)
- **`do_sample`, `top_p`** (new — needed since `vsp_llm_decode.py` calls HF `model.generate(do_sample=…, top_p=…)`)

The pip-installed fairseq in `vsp-llm-yoad-venv` *does* have all four fields, but it's shadowed by the local fork's PYTHONPATH entry.

**Fix:** Extend the runtime monkey-patch in `decode.sh` with Patches 3 + 4 — same pattern as the existing patches, anchored on upstream's `sampling: bool` line. The patch writes to the local fairseq's `configs.py` once on first decode; idempotent thereafter.

**Grep:** `grep -c "Patched: \|Patch [0-9]" VSP-LLM/scripts/decode.sh` should be ≥ 8 (four patches × ≥2 marker lines each).

**Why this hadn't shown up earlier:** Confidence + n-best aggregation are env-var-toggled HuggingFace features (`VSP_OUTPUT_SCORES`, `VSP_NBEST`) — they enable additional `model.generate()` kwargs but those flow through the existing flag. `do_sample` and `top_p` are read **unconditionally** at line 301 / 303, so any decode crashes — including the default `do_sample=False` beam-search path. The bug was latent until anyone ran decode after merging Mission 4 / Mission 6.

**Affected:**
- Feb-2026 overlay kit (`vsp_linux_container_FINAL_20260217/`) — fixed in this overlay revision
- May-2026 image source (`container_payload_20260507/`) — synced
- May-2026 image (`vsp-llm-pipeline:client-build-001` and later) — **also vulnerable** until next image rebuild. Operators running that image hit the same crash; same fix applies (patch decode.sh inside the image and `docker commit`, or wait for the next image bake).

## Online vs offline matrix

For each external resource, the rule for the air-gapped container:

| Resource | Build time (EC2 has internet) | Runtime (client offline) |
|---|---|---|
| PyTorch wheels (cu128 + cu124) | `--index-url https://download.pytorch.org/whl/...` | bundled in venvs |
| openai-whisper (git pin) | clone from GitHub | `pip install -e git+...` already installed |
| sentence-transformers package | install at build | bundled |
| Metaphone, doublemetaphone | local wheels in `is_wheels/` + PyPI fallback for transitive deps | bundled |
| matplotlib | install at build | bundled |
| spaCy + en_core_web_sm | install at build (`spacy download`) | bundled (~21 min build cost) |
| MediaPipe weights | pre-warm at build (`FaceDetection().__enter__()`) | bundled in venv site-packages |
| Whisper medium.pt | `whisper_cache/medium.pt` baked in image | `/root/.cache/whisper/medium.pt` (Dockerfile copies on layer) |
| MiniLM (HuggingFace) | `is_model_cache/hub/models--sentence-transformers--all-MiniLM-L6-v2/` | `HF_HOME=/workspace/is_model_cache` + `HF_HUB_OFFLINE=1` |
| Llama-2-7b-hf | bundled in image at `VSP-LLM/checkpoints/Llama-2-7b-hf/` | `from_pretrained(local_path)` — no HF call |
| AV-HuBERT `large_vox_iter5.pt` | bundled | local |
| VSP-LLM checkpoint_finetune.pt | bundled | local |
| fairseq Cython extensions | pre-built at build via `python setup.py build_ext --inplace` | already compiled |
| calibration.json | bundled at `docs/_research-tools/calibration/calibration.json` | local |
| dlib face detector .dat | bundled in `face_alignment/` | local |
| spaCy wheels in `spacy_wheels/` | NOT used (cp311, wrong ABI). PyPI install at build is the actual path. | bundled in venv |

**Required runtime ENV vars (set by the launchers):**
- `HF_HUB_OFFLINE=1`
- `TRANSFORMERS_OFFLINE=1`
- `HF_DATASETS_OFFLINE=1`
- `VSP_OUTPUT_DIR=/data/out`
- `VSP_TRANSCRIPTIONS_DIR=/data/transcriptions`
- (UI mode only) `VSP_INPUT_DIR=/data/in`, `VSP_UI_HOST=0.0.0.0`, `VSP_UI_PORT=8080`

**Required build-time ENV vars (Dockerfile):**
- `HF_HOME=/workspace/is_model_cache`
- `HUGGINGFACE_HUB_CACHE=/workspace/is_model_cache/hub`
- `DEBIAN_FRONTEND=noninteractive`

## UI mode patches (not in EC2 main)

| Patch | What it does | Why |
|---|---|---|
| `vsp-ui/app/config.py` env detect | First branch: detect flat `/workspace/` layout via `/workspace/run_flat_english_pipeline.sh` existence. | EC2's `_detect_environment()` knew about old container layouts only. |
| `vsp-ui/app/config.py` server settings | `SERVER_HOST = os.environ.get("VSP_UI_HOST", "127.0.0.1")` and same for PORT. | Default 127.0.0.1 doesn't expose to docker port-forward. |
| `vsp-ui/app/services/transcription_manager.py` _get_transcriptions_dir | Prefer `os.environ["VSP_TRANSCRIPTIONS_DIR"]` over `INPUT_DIR/.transcriptions`. | Input is `:ro` in container; transcriptions need writable persistent location. |

`pipeline_runner.py` did NOT need patching — `os.environ.copy()` already propagates VSP_OUTPUT_DIR / VSP_TRANSCRIPTIONS_DIR from launcher.

## Two launcher entry points

- `vsp-pipeline.sh` (CLI mode): zenity folder picker → docker run with `:ro` input → pipeline runs → zero browser. For one-shot decode runs.
- `vsp-start.sh` (UI mode): docker run with port 8080 + writable `:rw` input → starts `python3 -m app.server` → browser auto-opens to http://localhost:8080. For interactive workflow (drag-drop, transcription editing, progress bar).

Both share `image.tag` (single source of truth for which image to invoke).

## Process for next deployment

1. **Wholesale regen** `container_payload_20260507/lib/` and `run_flat_english_pipeline.sh` from EC2 main. Translate `${HOME}/HOME_DIR` → `SCRIPT_DIR` auto-detection.
2. **Audit script: walk INSTALL.sh of previous kit.** That's the canonical list of files needing container-specific patches. For each group, decide: take previous-kit version (path-tested), take EC2 version (newer features), or merge.
3. **Sync helper modules:** `docs/_research-tools/generators/{_alignment,analyze_beam_variance,generate_intelligibility_scores,compute_word_confidence}.py` go into the same path inside container_payload_20260507.
4. **Sync `vsp-ui/`** in full but apply 3 patches (config.py env detect, config.py server settings, transcription_manager.py).
5. **Bake at build time** anything that would otherwise lazy-download: matplotlib, spaCy + model, Whisper cache (right layout), MediaPipe pre-warm, fairseq Cython prebake, IS deps.
6. **Set offline env vars** in launchers (HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE, HF_DATASETS_OFFLINE).
7. **Validate** with mechanism-checks not outcome-checks: aggregated.json has 5 hyp_*, report.csv has expected columns, IS scoring ran (`intelligibility_scores.csv` produced), agreement bands fired (`agreement-{fid}.json` exists), transcriptions persisted (`metadata.json` + `*.wrd`).
8. **Cross-check** vs EC2 baseline: same input through both → diff outputs.
9. **Save** `docker save tag | zstd -19 > tarball` only after all validations pass.

## Single-image rule

The user's preference: **one Docker image, one tag, one tarball — no layered patch flows**. When source files change, sync wholesale + full rebuild + overwrite the tag. Layered FROM-previous-tag patches produce conceptual ambiguity (operator confusion at the client, `docker history` clutter). See `docs/guides/code-only-update.md` (deprecated banner there for the same reason).

## Cleanup sweep before final build

```bash
cd /home/ubuntu/vsp_docker/container_payload_20260507
# Runtime data that gets recreated by the pipeline:
rm -rf auto_avsr/flat auto_avsr/flat_prepared auto_avsr/preprocessed_* auto_avsr/preprocess_ready_* \
       auto_avsr/flat_wrd auto_avsr/flat_txt VSP-LLM/outputs/2025-* VSP-LLM/outputs/2026-* \
       VSP-LLM/decode auto_avsr/backups_flat
# Training-only data:
rm -f auto_avsr/english_1000_subset_hrz*.tar.gz
# Unused checkpoints:
rm -f VSP-LLM/checkpoints/checkpoint_freeze.pt
# Duplicate older avhubert tree:
rm -rf av_hubert/avhubert_flat
```

Saves ~8 GB. Final image ~58 GB.

## Total bug count surfaced

**17 distinct bugs** found and fixed across 3 build cycles + one in-field followup. The first build was conceptually right but had silent feature degradation (matplotlib/spaCy/prune-before-export/nbest-path/transcription-persistence). The second build picked up those fixes; the third pass added UI-mode wiring + bloat cleanup + NIV column. Bug 17 surfaced from a real client decode crash on 2026-05-12 (Feb-2026 client running the May overlay) — it had been latent since the Mission 4 / Mission 6 merge because nobody had run decode against the older local-fairseq fork after those features landed.

The biggest lesson: **`exit=0` does not mean features worked.** lib/outputs.sh has many `|| log_warn "X failed (non-critical)"` patterns. They protect the pipeline from crashing but mask feature loss. Mechanism-checks on actual artifacts (does aggregated.json exist? does it have hyp_mbr key? does report.csv have NIV column?) are the only honest validation.

The second-biggest lesson: **two fairseq installations live side-by-side** in this stack. The pip-installed one inside `vsp-llm-yoad-venv` AND the local fork at `VSP-LLM/fairseq/`. PYTHONPATH pins the local one. When EC2 main and the local fork drift (EC2 adds fields to its fork, local stays old), the runtime monkey-patch in `decode.sh` is the only thing keeping decode working. Any new field the decoder reads from cfg.generation.* needs a matching `if not hasattr…` patch added. **Audit `grep "cfg\.generation\." VSP-LLM/src/vsp_llm_decode.py | sort -u` whenever Mission code touches decode.**

---

## Client-side lessons (late May 2026)

These came out of remote walkthroughs over the phone with a non-engineer operator. Apply them upfront on the next client deployment.

### Video format support — camcorder family was missing

The client tried to upload `.MTS` (Sony / Panasonic AVCHD) files; the pipeline silently rejected them because `SUPPORTED_EXTENSIONS` only listed `mp4/mkv/webm/mov/m4v/avi`. **Most consumer / prosumer camcorders dump `.MTS` or `.m2ts`**. Production now also accepts `.ts`, `.wmv`, `.flv` (11 total). ffmpeg via `lib/normalization.sh` handles all of them — the gating is purely a user-visible whitelist. Adding a new format = update `vsp-ui/app/config.py::SUPPORTED_EXTENSIONS` + four mirror sites (app.js validExtensions, index.html `accept`, two bash globs, `find -iname` block in `lib/normalization.sh`), then run the test plan from `feedback_test_before_push.md` in memory.

### Client terminology rarely matches button labels

When a non-engineer says "restart", "loading", "the link doesn't open", "frozen", or names a file extension that doesn't exist (`.mtk`, `.mbs`), they almost never mean what the literal phrase suggests. Translation table is in memory at `client_feedback_terminology.md`. The two highest-leverage diagnostic questions are: **"What exactly is on the screen when this happens?"** and **"What did you click immediately before?"**.

### Test before push — for input-boundary changes specifically

Pushing a "we now accept 5 more video formats" change with only syntax checks (`python -c "import ast"` + `bash -n`) is **not enough**. Syntax-check passes when the failure mode is "doesn't accept this thing at all" because no existing test covers the new shape. Run the system on real fixtures — `ffmpeg -f lavfi -i testsrc=duration=2…` produces a small valid sample per container in seconds. The May-2026 11-format expansion was test-driven on 5 generated camcorder/wmv/flv fixtures (all normalised to valid h264 mp4, durations preserved). General template in memory at `feedback_test_before_push.md`.

### Document version dates explicitly

The client reading the deck thought "Roadmap" meant current state. The deck was a **February 2026** snapshot, but didn't say so on its title or in the link text. Subsequent work (MBR-as-default, agreement-aware bands, client UX bundle) lives in `/docs/`, not the slides. Always tag the date prominently on long-lived shared artifacts (Google Slides title, PPTX filename, doc front-matter), and add a one-line note in `README.md`'s link telling readers where the current state actually lives.
