# Update Manifest — May 2026 Refresh of Feb-2026 Overlay

Authoritative file-by-file diff between the Feb-2026 overlay (`v1.0.0 FINAL`,
12 fixes) and this May-2026 refresh (22 fixes). Every entry here is a concrete
change you can `cmp` after extracting the tarball.

> Skim the **Highlights** if you just want to know what's new. Read the
> **Detailed file list** if you're auditing the package before shipping.

---

## Highlights

1. **All existing 12 fixes preserved.** No regression.
2. **6 new EC2-side feature scripts** copied into `VSP-LLM/scripts/`:
   `compute_word_confidence.py`, `compute_word_agreement.py`,
   `nbest_aggregate.py`, `analyze_beam_variance.py`,
   `generate_intelligibility_scores.py`, `_alignment.py`.
3. **`lib/outputs.sh` rewritten end-to-end** (May 10 EC2 sync) — drives
   confidence, IS, n-best, agreement, MBR-default display in one pass.
4. **`lib/decode.sh` and `run_flat_english_pipeline.sh`** synced from EC2
   (auto-detect `BASE_DIR`, container venv paths preserved).
5. **`is_wheels_cp310/`** added — 38 cp310 wheels + 1 sdist for offline
   IS / confidence installs.
6. **`is_model_cache/`** added — HuggingFace MiniLM snapshot for offline
   semantic similarity.
7. **`vsp-start.sh`** refactored to a headless dispatcher; **`vsp-pipeline.desktop`**
   now uses `Terminal=false`. The "VSP PIPELINE ERROR: No terminal emulator found"
   error is gone.
8. **`VERIFY.sh`** extended from 12 to 23 checks (+11 covering the new features).
9. **`apply_update.sh` + `rollback_update.sh`** — host-side wrappers that
   `docker commit` INSTALL.sh's changes into a new image tag so wheels and the
   fairseq patch **persist across container exits and reboots**.

### Field-fix patches included in this revision (post initial Feb-2026 ship)

10. **`apply_update.sh` — `docker run` invocation fix.** The image's
    `ENTRYPOINT` is already `bash -c`. Earlier draft prepended a redundant
    `bash` to both `docker run` calls (Stage 1 install + Stage 4 smoke-test),
    producing `bash bash -c '…'` which failed with
    `/usr/bin/bash: /usr/bin/bash cannot execute binary file`. Both calls now
    pass just `-c '…'`, mirroring `vsp-start.sh`.
11. **`INSTALL.sh` [3.9b] — golden k-means models.** Previously, the
    `VSP-LLM/golden_kmeans/baseline_1396vid_20260218.bin` file sat in the
    overlay package but was never copied to `/host/galaxy_export/`. The UI's
    `/api/golden-models` endpoint then returned an empty list ("no golden
    model available"). Component [3.9b] now copies the directory contents.
12. **`vsp-ui/app/static/app.js` — drag-and-drop gate.** Earlier code gated on
    `currentScreen !== 'welcome'`, which meant once any video appeared in
    `vsp_input/`, drag-and-drop silently became a no-op while still showing
    the overlay (mis-signal to the user). Gate is now `if (isUploading)` —
    drops work on every screen except during an active upload.
13. **`VERIFY.sh` Fix 21b — golden model presence check.** Catches a missing
    `VSP-LLM/golden_kmeans/*.bin` before the UI does.
14b. **`apply_update.sh` — refuse to use the new tag as its own source.**
    Earlier draft discovered `OLD_TAG` by reading `docker.conf`. After the
    first successful run, `docker.conf` points at `vsp-llm-pipeline:may2026-update`
    — so on the **second** invocation `OLD_TAG == NEW_TAG`. The script's
    "image already exists, replacing" cleanup step then deleted its own source
    and `docker run … "$OLD_TAG"` failed with
    `Unable to find image 'vsp-llm-pipeline:may2026-update' locally`. Fix:
    `OLD_TAG` now defaults to `vsp-llm-pipeline:latest` (the original base
    image) and is no longer inferred from `docker.conf`. Two safety guards
    added — refuse if `OLD_TAG == NEW_TAG` by name OR by image-id.
14c. **`apply_update.sh` — preserve the original `docker.conf` backup across
    re-runs.** Earlier draft overwrote `docker.conf.before-may2026` on every
    run, which meant `rollback_update.sh` could only restore to the most-recent
    pre-run state (which on second+ runs was already pointing at the new tag).
    Backup is now created only on the FIRST run; later runs preserve the
    original route back to `vsp-llm-pipeline:latest`.
14d. **`lib/outputs.sh` — flip `VSP_FULL_OUTPUTS` default `0` → `1`.** Earlier
    default was "HTML-only minimal" output for fast EC2 dev iteration. On a
    client deployment this silently dropped: `burned_videos/`, `lip_crops/`,
    `intelligibility_scores.csv` (full semantic IS), `beam_analysis/` plots,
    and pruned everything except the two HTML reports. Operators received a
    tiny report set instead of the full artifact bundle. New default is full
    set; opt-out via `VSP_FULL_OUTPUTS=0` for dev-time fast iteration. Synced
    to: overlay, `container_payload_20260507`, EC2 main.
14e. **`vsp-ui/app/static/index.html` — move `#upload-progress-section` to
    body level.** Was a child of `#welcome-screen`. Welcome screen becomes
    `display:none` after the first video is detected, so drag-and-drop
    uploads on any subsequent screen ran silently with no UI feedback (the
    upload itself completed, but the progress widget was buried inside a
    hidden parent). Now it's a body-level fixed-top-right toast. Companion CSS
    `.upload-progress-floating` added in `style.css`. Combined with the
    earlier `handleDrop` / `handleDragOver` gate fixes, drag-and-drop now
    works on every screen with visible progress feedback.
14f. **`vsp-start.sh` + `vsp-ui/app/services/pipeline_runner.py` — set HF
    offline env vars at the docker-run boundary.** Earlier the offline
    `HF_HOME` / `HF_HUB_OFFLINE` / `TRANSFORMERS_OFFLINE` / `HF_DATASETS_OFFLINE`
    were set only inline in `lib/outputs.sh` around the IS-script subprocess.
    On air-gapped clients, any other `from_pretrained()` call elsewhere in
    the container's Python (sentence-transformers init path, transformers
    fallbacks, etc.) would phone home, fail, and **retry up to 5 times**
    before continuing — visible to operators as "offline" warnings during
    report generation. Setting the env vars at `docker run -e` flags
    (both foreground and headless launchers) AND in `pipeline_runner._get_env()`
    via `setdefault()` ensures every Python process in the container starts
    with offline mode enabled. The May-2026 lessons doc (Bug 13) specifically
    prescribes this two-layer placement; it was missed in the original
    overlay-port. Synced to: overlay, `container_payload_20260507`, EC2 main.
14g. **`spacy_wheels/` — replaced cp311 wheels with cp310.** Original overlay
    shipped Python-3.11 wheels for spaCy + thinc, but the Feb-2026 client's
    `vsp-llm-yoad-venv` is Python 3.10. Offline install silently failed (ABI
    mismatch); fallback to online install also failed (air-gapped); spaCy
    NEA / WWER entity metrics degraded to plain regex-based fallback with no
    operator warning. Replaced all 40 wheels with cp310 versions of the same
    packages (spacy-3.8.11, thinc-8.3.9, blis, cymem, preshed, murmurhash,
    pydantic, etc.). `en_core_web_sm-3.8.0` is py3-none-any so it works for
    any Python 3.x. numpy and setuptools deliberately omitted to avoid ABI
    breakage of the host venv. Synced to: overlay, `container_payload_20260507`.
14h. **`VSP-LLM/scripts/make_burn.py` — tight subtitle box (was a 320-px
    "dark patch").** The drawbox filter painted a black-65%-opacity box behind
    the subtitle text. Box height was `max(needed, min(args.box_h=320, h*0.45))`
    which always inflated to ≥320 px or 45% of the frame, regardless of how
    much text was actually rendered. Result: a tall dark patch dominating the
    lower portion of the video even for a one-line subtitle. Comment in the
    code said "Size the box to the ACTUAL number of wrapped lines" but the
    `max()` overrode that. Fix: `box_h = min(int(needed), int(h * 0.45))` —
    box is now exactly tall enough for the rendered text, capped at 45% of
    the frame for very long transcripts. Opacity reduced from 0.65 → 0.55
    for a less aggressive look. Synced to: overlay, `container_payload_20260507`,
    EC2 main.

14. **`VSP-LLM/scripts/decode.sh` Patches 3 + 4 — `do_sample` + `top_p` fields.**
    `vsp_llm_decode.py` reads `cfg.generation.do_sample` (line 301) and
    `cfg.generation.top_p` (line 303). The local fairseq fork at
    `/host/galaxy_export/VSP-LLM/fairseq/` (pinned via `PYTHONPATH`) doesn't
    have either field — pip-installed fairseq does, but is shadowed. Without
    these patches decode crashes with
    `omegaconf.errors.ConfigAttributeError: Key 'do_sample' is not in struct`
    at model.generate(). The existing monkey-patch (Patches 1 + 2 for
    `max_len` and `repetition_penalty`) is extended to add both fields at
    runtime, anchored on the upstream `sampling: bool` line. Idempotent —
    runs only if the field doesn't exist already.

---

## Audit — non-issues that *could* have been issues

These are dependencies we checked and confirmed work:

| Dependency | Status | Why it's fine |
|---|---|---|
| All `cfg.generation.*` fields the decoder reads | covered by Patches 1–4 | `do_sample` + `top_p` added in this revision; `max_len` + `repetition_penalty` were already patched; the rest (`beam`, `lenpen`, `lm_weight`, `max_len_a`, `max_len_b`, `min_len`, `no_repeat_ngram_size`, `temperature`) are upstream-standard |
| Per-token confidence (Mission 4) | HF-based | Driven by `VSP_OUTPUT_SCORES=1`; uses HF `model.generate(output_scores=True, return_dict_in_generate=True)`. Zero fairseq dependencies. |
| N-best aggregation (Mission 6) | HF-based | Driven by `VSP_NBEST=1`; uses HF `num_return_sequences=num_beams` + `compute_transition_scores`. Sidecar JSON written by python. Zero fairseq deps. |
| Agreement-aware bands | post-decode | `compute_word_agreement.py` reads emitted JSON, never touches fairseq. |
| Intelligibility Score | post-decode | `generate_intelligibility_scores.py` runs after make_report; uses sentence-transformers + Metaphone. HF env vars set inline in `lib/outputs.sh` (`HF_HOME`, `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`) for air-gapped offline load. |
| `VSP_NBEST` / `VSP_OUTPUT_SCORES` auto-on | default `=1` in `lib/decode.sh` | Operator doesn't need to set anything; n-best + confidence are on by default. Setting `=0` opts out. |
| HF model cache `is_model_cache/` | shipped + wired | INSTALL.sh `[3.18]` copies it; `lib/outputs.sh` exports `HF_HOME=$(dirname "$vsp_dir")/is_model_cache`. |
| IS / confidence wheels | shipped + installed | INSTALL.sh `[3.17]` pip-installs from `is_wheels_cp310/` with `--upgrade-strategy=only-if-needed`. |
| Golden k-means model | shipped + copied | INSTALL.sh `[3.9b]` (NEW, see fix 11 above). |
| Drag-and-drop on validation screen | fixed in app.js | Gate is now `if (isUploading)` only — works on every screen except during an active upload. |

---

## Detailed file list

### `lib/` (8 of 11 match EC2 main; 3 carry intentional container patches)

| File | State | Notes |
|---|---|---|
| `lib/common.sh` | SAME as EC2 | log_info / validate_directory |
| `lib/config.sh` | SAME as EC2 | EC2 vs container env detection (`ENV_TYPE`) |
| `lib/archive.sh` | SAME as EC2 | run archiving with transcription preservation |
| `lib/normalization.sh` | SAME as EC2 | NVENC silent-corruption fix |
| `lib/clustering.sh` | SAME as EC2 | golden k-means model loading |
| `lib/manifests.sh` | SAME as EC2 | manifest / TSV generation |
| `lib/decode.sh` | SAME as EC2 | Cython auto-build + segment-count log line |
| `lib/outputs.sh` | SAME as EC2 (May 10) | **all confidence/IS/N-best wiring + HF env vars** |
| `lib/asr.sh` | **CONTAINER PATCH** | `raw_dir/.transcriptions` (vs EC2's `home/vsp_input`); preserves Bug 8 fix |
| `lib/lrs3_prep.sh` | **CONTAINER PATCH** | passes `PREP_VENV` env var so flat_to_lrs3_preperation.sh activates the right venv |
| `lib/test_all_modules.sh` | **CONTAINER PATCH** | skips one EC2-only check (decode segment-count log line is EC2 SHA-specific) |

### `VSP-LLM/scripts/` — new helpers + Llama-2 patches

| File | State | Purpose |
|---|---|---|
| `compute_word_confidence.py` | **SUPERSET (May 2)** | Per-token confidence + joint conf+agreement bands. CLI: `--agreement` flag |
| `compute_word_agreement.py` | NEW | Beam-agreement score per word |
| `nbest_aggregate.py` | NEW | MBR / score-vote / conf-vote / safe / xseg-merge aggregation |
| `analyze_beam_variance.py` | NEW | Beam-variance + word-confusion analysis (plots; imports matplotlib) |
| `generate_intelligibility_scores.py` | NEW | IS computation: semantic (MiniLM), phonetic (Metaphone), WER, WWER, NEA, length |
| `_alignment.py` | NEW | Shared word-alignment helper used by 3 scripts above |
| `calibrate_temperature.py` | NEW | Per-method temperature calibration |
| `calibration.json` | NEW | Default calibration temperatures (Llama-2-7b-hf) |
| `compute_aggregated_is.py` | NEW | Method-level IS roll-up |
| `per_method_confidence_analysis.py` | NEW | Aggregated diagnostics |
| `word_confusion_conditional.py` | NEW | Conditional word-confusion analysis |
| `decode.sh` | **CONTAINER PATCH** | Auto-detect `ROOT` + Fairseq `GenerationConfig` monkey-patch for `max_len` + `repetition_penalty` (Bug 11/19/22) |
| `make_report.py` | UPDATED | NIV column + confidence wiring + agreement coloring |
| `make_burn.py` | UPDATED | Tier-badge overlay |

### `VSP-LLM/src/` — Llama-2 (NOT Llama-3) patches

| File | State | Notes |
|---|---|---|
| `vsp_llm.py` | **CONTAINER PATCH** | Holds back EC2's Llama-3 pad-token handling (the Feb client uses Llama-2). Llama-2-only behavior preserved |
| `vsp_llm_decode.py` | **CONTAINER PATCH** | Same — keeps Llama-2 tokenizer path; logger.propagate fix included |

### `run_flat_english_pipeline.sh` — container-side path discovery

`BASE_DIR` auto-detect from script location (works at `/host/galaxy_export`,
`/workspace`, or anywhere else). Hardcoded `/workspace/...` venv paths inside.
**Synced from EC2 May 10**, with these targeted container patches preserved:

- `BASE_DIR` instead of `${HOME_DIR}`
- `/workspace/auto_avsr/pre-process-venv` instead of `${AUTO_AVSR}/pre-process-venv`
- `/workspace/vsp-llm-yoad-venv` instead of `${HOME_DIR}/vsp-llm-yoad-venv`
- `source "${SCRIPT_DIR}/lib/..."` instead of `source "${HOME}/lib/..."`

### `vsp-start.sh` — headless launcher

**Replaced**: the old "find a terminal emulator and re-exec inside it" block
(15 emulator names tried, then error) is gone. Replaced by:

```bash
if [ -t 0 ] && [ -t 1 ]; then VSP_HEADLESS=0; else VSP_HEADLESS=1; fi
```

When headless:
- `docker run -d` (detached — no TTY required).
- Container logs streamed to `~/.vsp-pipeline.log`.
- `zenity --progress` polls `/api/status` for up to 90 s.
- Browser auto-opens on success; `zenity --error` shows last 30 lines of log on failure.
- Falls back to silent poll + `notify-send` if zenity isn't installed.

When TTY-attached:
- Original foreground `docker run -it` flow preserved as `do_start_foreground`.

### `vsp-pipeline.desktop` + `install-desktop-icon.sh`

- `vsp-pipeline.desktop`: `Terminal=true` → `Terminal=false`.
- `install-desktop-icon.sh`: removed the "warn if no terminal emulator" check
  (no longer needed). Added a "warn if no notifier" hint (informational only).

### `is_wheels_cp310/` — 95 MB, 39 files

| Kind | Wheels |
|---|---|
| Direct deps | sentence_transformers (5.1.2), Metaphone (0.6 sdist), doublemetaphone (1.2), matplotlib (3.9.4), scipy (1.13.1), editdistance (0.8.1) |
| Transitive | huggingface_hub, tokenizers, safetensors, regex, transformers (held-back use), hf_xet, scikit-learn, joblib, threadpoolctl, fsspec, filelock, jinja2, markupsafe, networkx, tqdm, packaging, pyyaml, requests, certifi, charset_normalizer, idna, urllib3, typing_extensions, contourpy, cycler, fonttools, kiwisolver, pillow, pyparsing, python_dateutil, six, zipp, importlib_resources |
| **Intentionally NOT included** | numpy (ABI break risk — existing 1.x must stay), torch + nvidia-cu* (already in venv, ~3 GB unnecessary) |

### `is_model_cache/` — 88 MB

Drop-in HuggingFace Hub cache for `sentence-transformers/all-MiniLM-L6-v2`:

```
is_model_cache/hub/models--sentence-transformers--all-MiniLM-L6-v2/
├── refs/main
├── blobs/
└── snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf/
    ├── config.json
    ├── pytorch_model.bin
    ├── tokenizer.json
    └── …
```

Set via env vars in `lib/outputs.sh`:

```bash
HF_HOME="$(dirname "$vsp_dir")/is_model_cache"
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
HF_DATASETS_OFFLINE=1
```

### `INSTALL.sh` — extended

- **`[3.17]` IS / confidence deps** — new component. `pip install` from
  `is_wheels_cp310/` with `--upgrade-strategy=only-if-needed` and a live
  import smoke-test of `sentence_transformers, metaphone, matplotlib, scipy,
  editdistance`.
- **`[3.18]` HF MiniLM cache** — new component. Copies `is_model_cache/`
  contents next to `galaxy_export`.

### `VERIFY.sh` — extended

Now 22 checks (was 12). New checks 13–22 cover:

| # | Check |
|---|---|
| 13 | `VSP-LLM/scripts/compute_word_confidence.py` has `classify_joint` |
| 14 | `VSP-LLM/scripts/generate_intelligibility_scores.py` has `doublemetaphone` |
| 15 | `VSP-LLM/scripts/nbest_aggregate.py` has `hyp_mbr` |
| 16 | `VSP-LLM/scripts/compute_word_agreement.py` has `_word_confs_for_utt` |
| 17 | `lib/outputs.sh` sets `HF_HUB_OFFLINE` |
| 18 | `vsp-pipeline.desktop` has `Terminal=false` |
| 19 | `vsp-start.sh` has `VSP_HEADLESS` branch |
| 20 | `is_model_cache/hub/models--…all-MiniLM-L6-v2/snapshots` exists |
| 21 | `is_wheels_cp310/sentence_transformers-5.1.2-…whl` exists |
| 22 | Live `python -c "import sentence_transformers, metaphone, matplotlib, scipy, editdistance"` succeeds |

---

## What is NOT shipped (and why)

| Skipped | Reason |
|---|---|
| Docker image rebuild | User explicit constraint: "not rebuilding the container — updating code and scripts." |
| numpy 2.x | ABI break risk vs existing numpy 1.x. |
| Llama-3 pad-token handling in `vsp_llm.py` / `vsp_llm_decode.py` | Original client uses Llama-2-7b-hf. Llama-3 would require a different checkpoint AND a new fine-tuned head — out of scope for a code-only update. |
| Wheels for spaCy 3.8.11 + en_core_web_sm | Already bundled in the Feb overlay's `spacy_wheels/` (cp311). The Feb client's INSTALL flow already handles it. |
| EC2's newer `compute_word_confidence.py` from `docs/_research-tools/generators/` | The newer copy in `VSP-LLM/scripts/` (May 2) is a strict superset (adds the joint conf+agreement rule + numeric handling). It's the canonical file. |

---

## Verification chain (what `cmp` should show after extraction)

```bash
TAR=vsp_linux_container_FINAL_20260217
tar xzf $TAR.tar.gz
cd $TAR/

# Spot-check the 6 new feature scripts
for f in compute_word_confidence.py compute_word_agreement.py \
         nbest_aggregate.py analyze_beam_variance.py \
         generate_intelligibility_scores.py _alignment.py; do
  test -f "VSP-LLM/scripts/$f" && echo "OK  $f" || echo "MISS $f"
done

# Spot-check wheels + model cache
test -f is_wheels_cp310/sentence_transformers-5.1.2-py3-none-any.whl && echo "OK  wheels"
test -d is_model_cache/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots && echo "OK  cache"

# Spot-check the headless launcher
grep -q VSP_HEADLESS vsp-start.sh && echo "OK  headless"
grep -q "Terminal=false" vsp-pipeline.desktop && echo "OK  desktop"
```

All four lines should print `OK …`.

---

## Build provenance

| | |
|---|---|
| EC2 source commit | `abb2167` (2026-05-12) |
| EC2 venv | `/home/ubuntu/vsp-llm-yoad-venv` (Python 3.9 — unused for client wheels) |
| Client target venv | `/workspace/vsp-llm-yoad-venv` (Python 3.10) |
| Wheels downloaded via | `pip download --python-version 3.10 --platform manylinux_2_17_x86_64 --only-binary=:all:` |
| HF cache copied from | `/home/ubuntu/vsp_docker/container_payload_20260507/is_model_cache/` (built into the May 2026 air-gapped image) |
