# Client-Laptop Deployment Guide — August 2026 (Iteration-Aware)

Audience: the teammate shipping the **next** Docker image (`client-build-004`) to the air-gapped **Windows 11 + RTX 5090** client laptop. The spine of this guide is *what each delivery round taught us* — every rule below exists because we paid for it once. Do not re-derive the process from scratch; do not resurrect a deprecated flow because it looks simpler.

Current shipped state (verified 2026-08-03):

- Image on client: **`vsp-llm-pipeline:client-build-003`** (with Blackwell fix, `client-build-003-bwfix` tag also live in [launcher/vsp-setup.ps1](../../vsp_docker/launcher/vsp-setup.ps1)); active tag in [launcher/image.tag](../../vsp_docker/launcher/image.tag)
- Tarball: `vsp_docker/vsp-image-client-build-003-20260513.tar.zst` (42.7 GB) + `.sha256`; copy in `s3://yoad-vsp-transfer/vsp/` (GetObject-only bucket); kit-extras 1.6 GB (`vsp-kit-extras-client-build-003.tar.gz`)
- Build context: `vsp_docker/container_payload_20260507/` (58 GB). **`vsp_docker/galaxy_export/` is a 67 MB dead stub** (empty submodule dirs, pre-rename leftover) — never build from it.
- Dockerfile: `FROM nvidia/cuda:12.8.0-base-ubuntu22.04`, deadsnakes python3.9, ASR stack torch 2.8.0+cu128 (Blackwell-native), `HF_HOME=/workspace/is_model_cache`
- Payload `lib/` + `run_flat_english_pipeline.sh` synced to **May 27** — already AHEAD of build-003. A rebuild today picks up the post-003 features automatically (§3).

---

## §1 Iteration history — the mistake each round taught us

| Round | When / artifact | What we did | What went wrong / why abandoned | The rule that came out of it |
|---|---|---|---|---|
| **1 — Overlay era** | Feb 2026. `vsp_linux_container_FINAL_20260217/` tar.gz patched an existing container. Docs: [container-update-feb2026.md](container-update-feb2026.md), [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md), [TRANSFER_INSTRUCTIONS.md](TRANSFER_INSTRUCTIONS.md) | Ship a ~3 MB overlay of patched files onto whatever image the client already had | 37 bugs at the client ([catalogs in §6](#§6-pointers)) because the base image and the overlay drifted independently; stale tarballs shipped ("5 files updated after packing"); nobody could say what state the client machine was actually in | **The deployed artifact must be a single, fully-described unit.** Overlay-on-unknown-base = unknowable client state. |
| **2 — Layered patches** | Early May 2026. [code-only-update.md](code-only-update.md) — **DEPRECATED** | Thin Docker images `FROM <previous-tag>` with just changed files COPYed in | Two+ tags on the client disk, `docker history` clutter, operator confusion over "which is current". The fast-iteration win did not cover the conceptual ambiguity cost at a non-engineer-operated site | **Single-image doctrine** (§2): one tag, one tarball, full rebuild, overwrite. No `FROM <previous-tag>` ever. |
| **3 — build-001** | May 7 2026. First self-contained image. Bug catalog: [container-deployment-lessons-may2026.md](container-deployment-lessons-may2026.md) (17 bugs, 3 build cycles) | Full image from the freshly-renamed `container_payload_20260507/` | The **Blackwell wall**: cu124 wheels have no sm_120 → cu128/torch 2.8.0 for the ASR stack; Whisper lazy-downloaded at runtime (fatal air-gapped, nested `whisper/` cache subdir); spaCy cp310 ABI mismatch vs bundled cp311 wheels; torch `weights_only` load default flip; silent feature degradation (`exit=0` while matplotlib/spaCy/nbest quietly missing) | **`exit=0` does not mean features worked** — validate with *mechanism-checks on artifacts* (does `aggregated.json` have 5 `hyp_*` keys? does `report.csv` have the `niv` column?). Bake **everything** at build time; nothing may lazy-download. |
| **4 — build-003 + bwfix (SHIPPED)** | May 13 2026. `vsp-image-client-build-003-20260513.tar.zst` + kit-extras (windows_kit, launcher, checks, samples) | Full kit: [CLIENT_INSTALL.md](../../vsp_docker/CLIENT_INSTALL.md), [windows_kit/INSTALL_ORDER.md](../../vsp_docker/windows_kit/INSTALL_ORDER.md), [checks/](../../vsp_docker/checks/), [launcher/](../../vsp_docker/launcher/) incl. `vsp-setup.ps1` doctor script | Field bugs were now **Windows-side**, not image-side: PS 5.1 script corruption, Docker Desktop port-proxy wedging, hardcoded server ports, 10–15 min first-run CUDA JIT reading as "frozen", Edge drag-drop regression, `.MTS` camcorder files silently rejected | **The image can be perfect and the delivery still fails on the host OS.** Windows field rules + client-vocabulary translation are part of the kit (§5). Warm the JIT in staging; tell the operator about it anyway. |

In build-003: MBR display default, joint conf+agreement bands, `VSP_NBEST=1`, `VSP_FULL_OUTPUTS=1`, HF offline env vars at the docker-run boundary, fairseq `do_sample`/`top_p` patches.

---

## §2 Current doctrine (do not renegotiate per delivery)

1. **Single image.** One clean image per delivery: one tag (`vsp-llm-pipeline:client-build-NNN`), one tarball, full payload sync + full rebuild + overwrite. No layered `FROM`-previous-tag patches — [code-only-update.md](code-only-update.md) is kept only as a tombstone. `apply_update.sh`/`rollback.sh` remain valid, but they swap *full-rebuild* images.
2. **EC2 (`/home/ubuntu/`) is the source of truth.** The payload is a *derived* copy. Never edit the payload first and forget EC2; never let the payload "improve" independently.
3. **Payload sync is wholesale, then hand-merge the 6 container-adapted files.** Six files differ from EC2 *by design* (path translation / env detection): `run_flat_english_pipeline.sh`, `lib/asr.sh`, `lib/lrs3_prep.sh`, `lib/test_all_modules.sh`, `vsp-ui/app/config.py`, `vsp-ui/app/services/transcription_manager.py`. A naive rsync clobbers the container patches; skipping them strips new EC2 features. [scripts/tests/test_payload_sync.sh](../../scripts/tests/test_payload_sync.sh) polices both failure modes (anti-clobber marker probes + byte-diff on everything else).
4. **Staging dry-run gate before client contact.** No kit reaches the client without the full [staging-dry-run.md](staging-dry-run.md) Layer-2 pass on an air-gapped box you control. Fix bugs by *rebuilding the image*, never by patching the staging box ("if you skip the rebuild and just patch on the staging box, you've taught the bug it can survive").
5. **Mechanism-checks, not exit codes.** Validation = [checks/post_install_check.sh](../../vsp_docker/checks/post_install_check.sh) artifact assertions, in-container and at the client.
6. Note: [deploy-targets.md](deploy-targets.md) describes the older overlay-primary practice and predates the May-7 `galaxy_export` → `container_payload_20260507` rename. For *image* deliveries, **this guide and the single-image doctrine win**; the overlay dir survives only as the Feb-2026 client's historical reference and path-translation gold standard.

---

## §3 What's new since build-003 (rebuild today ships all of this)

The payload was synced to May 27 — AHEAD of the shipped image. No per-build manifest existed; this list is reconstructed from git.

**Client-facing features that a build-004 delivers:**

| Date | Feature (client-facing wording) | Commits |
|---|---|---|
| 2026-05-25 | **Client UX bundle**: transcription-editing fixes, restart-loop fix, Windows host-path surfacing in the UI, Archive/Restore of runs, drag-drop hardening (file-picker fallback for the Edge regression) | `9b4006d`; deployment kit `6e2dfd9` |
| 2026-05-26 | **Confidence breakdown "trust stack"** in reports + numeric/currency confidence cap (numbers never shown green) | `da1a2ae` |
| 2026-05-26 | **"Watch with CC"** — whole-video closed-caption preview + **audio-injection UI** (inject a clean separate-audio transcript into a silent/bad-audio video) | `1f4d72b` |
| 2026-05-26 | **Audio-injection CLI** (two-offset alignment, `--audio-start`/`--video-start`); guide: [audio-injection.md](audio-injection.md) | `a89a1f0` |
| 2026-05-27 | **Five new input formats**: `.mts`/`.m2ts`/`.ts` (AVCHD camcorders — the client's ".mtk" files), `.wmv`, `.flv` — 11 containers total | `1ef78ba` |

**Decide-at-build-time items (July 2026, research-side — default EXCLUDE from the client image):**

- MBR word-confidence sidecars (`b3cbb77`) — research instrumentation
- Phonetic substitution module (`d9e7c0a` etc.) — only the agreement arm passed GO, and it ships 2 substitutions; not client-hardened
- Anything else post-May-27 under `docs/` research folders

Rule: if it wasn't exercised by the smoke fixtures and hasn't a client-facing doc, it stays out. Record the include/exclude decision in the build log and in [docs/container-sync-changelog.md](../container-sync-changelog.md).

**Already in build-003 (do not re-announce as new):** MBR display default, joint conf+agreement bands, `VSP_NBEST=1`.

---

## §4 Next-delivery procedure, step by step

### 4.0 Naming

New BUILD_ID convention (date-stamped, matching the tarball convention build-003 used):

```bash
BUILD_ID="client-build-004"
BUILD_DATE=$(date +%Y%m%d)          # tarball: vsp-image-${BUILD_ID}-${BUILD_DATE}.tar.zst
TAG="vsp-llm-pipeline:${BUILD_ID}"
```

### 4.1 Preflight

**(a) Payload sync check — run the gate:**

```bash
bash /home/ubuntu/scripts/tests/test_payload_sync.sh
```

Must print `RESULT: PASS`. The 6 `DIFF-EXPECTED` warnings are normal (container adaptations); any `FAIL` means the payload is stale or a container patch got clobbered — fix before building. Mid-development you can run with `SYNC_ALLOW_DIFF=1` to downgrade failures to warnings, but the pre-build run must be clean *without* it.

Known pending hand-merge as of 2026-08-03: EC2's `lib/test_all_modules.sh` gained a "decode segment-count log line" guard test (8 lines, commit `a350420`) that the payload copy lacks. Merge it into the payload copy (keep the payload's `LIB_DIR` auto-detect header) before build-004.

Fixture note: the historical kit-side naming mismatch (`vsp_docker/samples/smoke_35s_360p.mp4` vs the `smoke_75s.mp4` that `checksums.txt` + `post_install_check.sh` expect) was fixed on 2026-08-03 by renaming the kit-side file. The test now guards against regression; if it ever re-fires, the fix command is printed in the FAIL line.

**(b) Disk space — ⚠️ THIS BOX IS SHORT TODAY.** The build needs **≥ 200 GB free on the `/var/lib/docker` volume** (build layers + final image + save staging). As of 2026-08-03 this box has **~94 GB free** on `/` (which hosts `/var/lib/docker`). Do NOT start a build at 94 GB — it will die mid-`docker save`. Options, in order of preference:

1. **Prune old images and tarballs**: `docker system df` then `docker image rm` superseded `vsp-llm-pipeline:*` builds and `docker builder prune`; delete/archive to S3 the 42.7 GB `vsp_docker/vsp-image-client-build-003-20260513.tar.zst` (an S3 copy already exists in `s3://yoad-vsp-transfer/vsp/` — verify its SHA256 against the local `.sha256` **before** deleting the local one; the bucket is GetObject-only for this role, so the copy cannot be re-uploaded from here), and `vsp_docker/galaxy_export.pre-regen-20260506_213727/` if still present.
2. **Attach a bigger EBS volume** and point Docker at it (`/etc/docker/daemon.json` → `"data-root"`), or grow the root volume.

**(c) Standard build prereqs** — from [build-and-transfer.md](build-and-transfer.md): NVIDIA Container Toolkit works (`docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi`), internet available, and:

```bash
bash /home/ubuntu/vsp_docker/container_payload_20260507/lib/test_all_modules.sh   # must pass on EC2
```

**(d) Bloat sweep** — re-run the cleanup greps from [container-deployment-lessons-may2026.md](container-deployment-lessons-may2026.md) § "Cleanup sweep" (runtime data, training tarballs, unused checkpoints must all report "No such file or directory").

### 4.2 Build

```bash
cd /home/ubuntu/vsp_docker
docker build -t "${TAG}" -f Dockerfile . 2>&1 | tee /tmp/vsp_build_${BUILD_ID}.log
```

30–60 min. The Dockerfile runs `lib/test_all_modules.sh` in-build — a failure there is a `lib/` regression: fix on EC2, resync, rebuild. Slow steps: payload COPY (58 GB), two venv pip installs, spaCy sdist compile (~21 min), Cython prebake.

### 4.3 In-container validation (before saving anything)

Run [checks/post_install_check.sh](../../vsp_docker/checks/post_install_check.sh) logic against the fresh image — it decodes **both smoke fixtures** (`smoke_12s.mp4` sanity run + `smoke_75s.mp4` batching/n-best/tier run) and asserts mechanisms, not exit codes:

- `aggregated.json` exists with all 5 `hyp_*` methods; MBR is the displayed hypothesis
- `report.csv` has confidence columns + `niv` (Y/P/N); `intelligibility_scores.csv` non-empty
- `report.html` uses the blue/orange/purple/teal palette; number words capped at orange
- `agreement-{fid}.json` sidecars present; k-means model saved; burned video has duration
- Offline imports: `matplotlib`, `spacy.load('en_core_web_sm')`, sentence-transformers from `is_model_cache/` — all inside the image with networking disabled (`docker run --network=none`)

### 4.4 Save, split, checksum

```bash
docker save "${TAG}" | zstd -19 -T0 > "vsp-image-${BUILD_ID}-${BUILD_DATE}.tar.zst"
sha256sum "vsp-image-${BUILD_ID}-${BUILD_DATE}.tar.zst" > "vsp-image-${BUILD_ID}-${BUILD_DATE}.tar.zst.sha256"
split -b 4G "vsp-image-${BUILD_ID}-${BUILD_DATE}.tar.zst" "vsp-image-${BUILD_ID}-${BUILD_DATE}.tar.zst.part_"
```

Expect ~35–45 GB compressed. Also regenerate kit-extras (launcher + checks + samples + windows_kit) if any of those changed: `vsp-kit-extras-${BUILD_ID}.tar.gz` + `.sha256`.

### 4.5 Transfer

Per [build-and-transfer.md](build-and-transfer.md): upload parts + `.sha256` to the S3 `vsp/` prefix (note: the standing `s3://yoad-vsp-transfer` role grant is **GetObject-only** — arrange PutObject or use short-lived creds, and delete creds from the box afterward), download on your laptop, `sha256sum -c`, then copy to a **USB 3 SSD** (not a thumb drive). Kit layout on the USB is listed in [CLIENT_INSTALL.md](../../vsp_docker/CLIENT_INSTALL.md).

### 4.6 Staging dry-run (mandatory gate)

Full [staging-dry-run.md](staging-dry-run.md) pass on an offline box — ideally Windows 11 + Blackwell to match the client. Extra Windows-specific items on top of the Linux checklist:

- **Warm the CUDA JIT** during staging (first Blackwell decode JIT-compiles 10–15 min) and confirm the `%USERPROFILE%\cache → /root/.nv` mount persists it across container restarts
- Exercise drag-drop **and** the file-picker fallback in Edge
- Confirm `VSP_HOST_INPUT_DIR` renders the client-visible Windows path in the UI
- Sleep/wake the laptop, then reload the UI (port-proxy wedge check, §5)
- Feed one `.MTS` file through end-to-end

### 4.7 Windows install / update at the client

Fresh machine: follow [windows_kit/INSTALL_ORDER.md](../../vsp_docker/windows_kit/INSTALL_ORDER.md) strictly — **driver (596.21+) → reboot → WSL2 kernel msixbundle (only if asked for) → Docker Desktop (WSL2 backend) → reboot → `.wslconfig`**. Order matters; each step's verify command is in that doc.

Update on the existing laptop (the usual case for build-004):

1. Copy tarball + `.sha256` from USB; verify hash in PowerShell: `Get-FileHash -Algorithm SHA256`
2. `zstd -d` + `docker load -i` (15–30 min)
3. **Update `image.tag`**: write `vsp-llm-pipeline:client-build-004` to `C:\vsp\launcher\image.tag` — the single source of truth the launchers read. Then re-run [launcher/vsp-setup.ps1](../../vsp_docker/launcher/vsp-setup.ps1) from an **Administrator** PowerShell — it purges stale shortcuts, reinstalls launchers, sanity-starts the UI container, and prints a VERIFY block to paste back. Note: `vsp-setup.ps1` carries a fallback default tag (`$BwTag`) — bump it for build-004 before shipping the kit.
4. Old image stays loaded for rollback (`rollback.ps1` flips `image.tag` back).

**PowerShell 5.1 script rules (learned the hard way):** ASCII only — em-dashes/smart quotes corrupt via UTF-8/CP1252 round-trips; never name a function or alias `R` (collides with `Invoke-History`); never write `$var:` followed by text (drive-notation misparse — use `${var}:`).

### 4.8 Post-install checks + JIT warm-up

1. Run [checks/post_install_check.ps1](../../vsp_docker/checks/post_install_check.ps1) (or `.sh` under WSL) — both smoke decodes + mechanism asserts → `INSTALL_REPORT.txt` STATUS: READY
2. **Warm the JIT with the operator watching**: run the 12s smoke first and *say out loud* that the first run compiles for 10–15 minutes and every later run is fast. This single sentence prevents the "it's frozen" support call.
3. Verify the JIT cache mount so the compile never repeats: container runs with `-v %USERPROFILE%\cache:/root/.nv` and `-e HOME=/workspace` (so in-container `~/script.sh` lookups resolve)
4. [checks/vsp-selftest.ps1](../../vsp_docker/checks/vsp-selftest.ps1) — the operator-runnable one-button re-verification; leave it on the desktop

### 4.9 Acceptance test with the operator

Drive it *hands-off* — the operator clicks, you watch:

- [ ] Operator drags (or file-picks) a real video of their own into the UI; pipeline completes
- [ ] `report.html` opens; confidence colors + NIV labels present; one number word capped orange
- [ ] "Watch with CC" plays; per-segment players load (30 s timeout fallback exists, but note any player that needs it)
- [ ] One `.MTS` camcorder file accepted and processed
- [ ] Operator archives a run, restores it
- [ ] Operator finds the output folder using the Windows path shown in the UI (`VSP_HOST_INPUT_DIR` surfacing)
- [ ] Laptop sleep → wake → UI reload works (or operator knows the §5 fix)
- [ ] `INSTALL_REPORT.txt` STATUS: READY; copy of it + `image.tag` back on your USB

Then: git-tag the build, mark shipped entries in [container-sync-changelog.md](../container-sync-changelog.md), delete transfer creds, write the build manifest (the list of commits included — build-003's absence of one is why §3 had to be reconstructed from git).

---

## §5 Field troubleshooting — Windows client quick table

First, the two magic questions for a non-engineer operator — ask them before diagnosing anything: **"What exactly is on the screen right now?"** and **"What did you click immediately before?"** Client vocabulary rarely matches button labels: "restart" = one specific button, not a reboot; "loading"/"frozen" = usually the first-run CUDA JIT compile; ".mtk"/".mbs" = `.MTS` camcorder files.

| Symptom (as reported) | Actual cause | Fix |
|---|---|---|
| "It's frozen" / "still loading" on the first-ever run | CUDA JIT compiling for Blackwell (10–15 min, one-time) | Wait it out; verify `%USERPROFILE%\cache:/root/.nv` mount so it never repeats. Warm in staging next time. |
| UI unreachable after laptop sleep/overnight | Docker Desktop port-proxy wedged after sleep | `wsl --shutdown`, restart Docker Desktop (this restarts vpnkit); relaunch shortcut |
| "The link doesn't open" / UI on wrong port | Server ports were hardcoded historically | Launcher must pass `-e VSP_UI_HOST=0.0.0.0 -e VSP_UI_PORT=8080` and `-p`; check `image.tag` points at the current build |
| Drag-drop does nothing (Edge) | Edge drag-drop regression | Use the "Add files…" file-picker button (shipped fallback, build-004) |
| "My .mtk files are rejected" | `.MTS` (AVCHD camcorder) not in the pre-May-27 whitelist | build-004 accepts `.mts/.m2ts/.ts/.wmv/.flv`; on build-003, remux to mp4 as a stopgap |
| Per-segment video never plays | `<video>` element stall | 30 s timeout fallback shipped; if chronic, collect diagnostics |
| Script "does nothing" / prints garbage after editing a `.ps1` | PS 5.1 em-dash/smart-quote corruption, `R` alias collision, `$var:` misparse | Re-copy the pristine script from the kit; never hand-edit `.ps1` on the client in Notepad |
| `~/run_flat_english_pipeline.sh: not found` inside container | `$HOME` is `/root`, scripts live in `/workspace` | Launcher passes `-e HOME=/workspace` |
| "Restart doesn't help" | They mean the UI's restart *button*, and the run is stuck for another reason | Ask the two magic questions; then `collect_diagnostics` |
| IS scores 0.00 / wrong colors / empty output dir | Stale image or missing cache dirs | See the Linux-side table in [client-troubleshooting.md](../../vsp_docker/client-troubleshooting.md) — causes are image-side, identical on Windows |
| Anything else | — | [checks/collect_diagnostics.ps1](../../vsp_docker/checks/collect_diagnostics.ps1) → send tarball; full symptom table in [client-troubleshooting.md](../../vsp_docker/client-troubleshooting.md) |

---

## §6 Pointers

| What | Where |
|---|---|
| May-2026 image bug catalog (17 bugs, the "grep for next time" list) | [container-deployment-lessons-may2026.md](container-deployment-lessons-may2026.md) |
| Feb-2026 container bug catalogs (37 bugs) | [bugs-reference.md](../../vsp_linux_container_FINAL_20260217/bugs-reference.md), [bugs 1–13](../../vsp_linux_container_FINAL_20260217/bugs-1-to-13-installation.md), [14–25](../../vsp_linux_container_FINAL_20260217/bugs-14-to-25-deployment.md), [26–37](../../vsp_linux_container_FINAL_20260217/bugs-26-to-37-final.md) |
| Build + S3/USB transfer mechanics | [build-and-transfer.md](build-and-transfer.md) |
| Layer-2 staging dry-run (the gate) | [staging-dry-run.md](staging-dry-run.md) |
| Operator-facing install doc (ships on the USB) | [CLIENT_INSTALL.md](../../vsp_docker/CLIENT_INSTALL.md) |
| Windows air-gapped install order | [windows_kit/INSTALL_ORDER.md](../../vsp_docker/windows_kit/INSTALL_ORDER.md) |
| Payload sync gate (run before every build) | [scripts/tests/test_payload_sync.sh](../../scripts/tests/test_payload_sync.sh) |
| Sync ledger (mark entries shipped after build-004) | [container-sync-changelog.md](../container-sync-changelog.md) |
| Deploy-target roles (historical; overlay era) | [deploy-targets.md](deploy-targets.md) |
| Deprecated layered-patch flow (tombstone) | [code-only-update.md](code-only-update.md) |
| End-user pipeline guide (client-facing) | [user-guide-vsp-pipeline.md](user-guide-vsp-pipeline.md) |
| Audio-injection workflow | [audio-injection.md](audio-injection.md) |
