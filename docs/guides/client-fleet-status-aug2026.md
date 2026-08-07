# Client Fleet Status — versions, gaps, dependencies (Aug 2026)

**The missing fleet inventory.** Before this doc, no single place recorded which
standalone machine runs what — build-003's contents had to be reconstructed from
git, and the Feb-2026 box's state was unknown after May 12. This doc is the
living source of truth: update it after **every** build and **every** field trip.

Companion runbooks: [client-laptop-deployment-aug2026.md](client-laptop-deployment-aug2026.md)
(build + Windows delivery), [staging-dry-run.md](staging-dry-run.md),
[deploy-targets.md](deploy-targets.md),
[container-sync-changelog.md](../container-sync-changelog.md) (per-change record).

---

## 1. Machine inventory

| | **M1 — Windows client laptop** | **M2 — Feb-2026 Linux client** | **M3 — Developer standalone** |
|---|---|---|---|
| Owner / operator | Client (non-engineer, phone support) | Client (user `ds`) | Ours (developer box) |
| OS / GPU | Win 11 + RTX 5090 (Blackwell), driver 596.21 | Linux, **12 GB GPU** (11.63 GiB usable) | Linux, GPU **unrecorded — audit on next visit** |
| Air-gapped | Yes | Yes | Yes (assumed; verify) |
| Install root | `C:\vsp\` (WSL2 + Docker Desktop) | `/home/ds/Desktop/galaxy_export` | `/home/ds/Desktop/galaxy_export` |
| Image / tag | `vsp-llm-pipeline:client-build-003` (+`-bwfix`) | `vsp-llm-pipeline:may2026-update` (docker-commit lineage) | `vsp-flat-standalone:cu128-exact` |
| Code level | 2026-05-13 build (payload as of ~May 12) | 2026-05-12 overlay | **Unknown** — no deployment date or version log exists |
| Last verified in field | 2026-08-03 | 2026-05-12 (bug-17 crash report) | Never |
| Config flip file | `C:\vsp\launcher\image.tag` | `docker.conf` | `docker.conf` |
| Transfer medium | S3 → laptop → USB 3 SSD (not thumb drive) → hand-carry | USB stick or scp → hand-carry | USB / scp (ours, flexible) |

**Target for all three: `vsp-llm-pipeline:client-build-004`** (single-image
doctrine — one tag, one tarball, no layered patches; decision confirmed Aug 6 2026).

---

## 2. Feature-gap matrix

Code freeze: **2026-05-27** (`1ef78ba`). Everything after is research/docs — no
production gap accrues from June–August. Entries cited by date+title (changelog
numbering has historical duplicates).

| Feature (date, commit) | M1 build-003 | M2 may2026 | M3 cu128 |
|---|---|---|---|
| Jan–Feb 2026 fix stack (entries 1–28: transcription mgmt, seg-12s, OOM fixes, NVENC/fd fix, decode params) | ✅ | ✅ | ❓ |
| IS scoring in container reports (Mar 10) | ✅ | ✅ | ❓ |
| WWER tokenizer fix (Mar 7, `d6b443d`) | ✅ | ✅ | ❓ |
| Per-word confidence in every run (Apr 30, `3937a9e`) | ✅ | ✅ | ❓ |
| Client HTML report auto-gen (May 1, `96ed361`) | ✅ | ✅ | ❓ |
| Confidence coloring in burned videos (May 1, `87961db`) | ✅ | ✅ | ❓ |
| N-best aggregation + **MBR default display** + `VSP_NBEST=1` (May 1–2) | ✅ | ✅ | ❓ |
| Joint conf+agreement band rule (May 2, `ac17868`) | ✅ | ✅ | ❓ |
| fairseq `do_sample`/`top_p` decode-crash patch (May 12, entry 32) | ✅ | ❌ **crash risk** | ❓ |
| `VSP_FULL_OUTPUTS=1` + drag-drop visibility (May 12, entry 33) | ✅ | ❌ | ❓ |
| HF offline env vars at docker-run boundary (May 12, entry 34) | ✅ | ❌ **hang risk** | ❓ |
| spaCy cp310 wheels + make_burn dark patch (May 12, entry 35) | ✅ | ❌ **metrics risk** | ❓ |
| Client UX bundle: transcription editing, restart-loop fix, host-path, Archive/Restore, Edge drag-drop fallback (May 25, `9b4006d`) | ❌ | ❌ | ❓ |
| Trust stack + numeric/currency cap in `confidence_breakdown.html` (May 26, `da1a2ae`) | ❌ | ❌ | ❓ |
| Watch-with-CC + audio-injection UI (May 26, `1f4d72b`) + CLI (`a89a1f0`) | ❌ | ❌ | ❓ |
| 5 new input formats `.mts/.m2ts/.ts/.wmv/.flv` (May 27, `1ef78ba`) | ❌ (client remuxes .MTS by hand) | ❌ | ❓ |
| Complete-screen resilience UI fixes (Aug 6, `6d455a4`, entry 36) | ❌ | ❌ | ❓ |

✅ = present · ❌ = missing (fixed by build-004) · ❓ = unknown, M3 pre-update
audit fills this column. **build-004 closes every ❌ on every machine.**

---

## 3. Missing-dependency matrix (what breaks without it, per machine)

| Machine | Missing dependency / patch | What breaks |
|---|---|---|
| **M2** | fairseq `do_sample`/`top_p` monkey-patch (entry 32) | **Decode crashes** — the exact field crash observed 2026-05-12 (bug 17) |
| **M2** | HF offline env vars (`HF_HUB_OFFLINE` etc., entry 34) | Runtime tries to reach huggingface.co on an air-gapped box → **hang/stall** at model load |
| **M2** | spaCy **cp310** wheels (entry 35 — cp311 wheels shipped by mistake in the May kit) | spaCy import fails in the py3.10 venv → **NEA + Weighted-WER columns missing** from reports |
| **M2** | `VSP_FULL_OUTPUTS=1` default (entry 33) | Clients get the reduced output set (no full report suite) |
| **M1** | — none within build-003's scope | Gaps are feature-level only (see §2); no broken dependency |
| **M1** | *operational*: persistent JIT cache `-v %USERPROFILE%\cache:/root/.nv` + `-e HOME=/workspace` | Without them: 10–15 min CUDA JIT re-compile every container restart; `~/script.sh` lookups fail. Already in the shipped launcher — **re-verify after build-004 setup re-run** |
| **M3** | Unknown — no record of its image contents | Pre-update audit: `docker images`, `docker.conf`, `nvidia-smi`, `df -h`, run `VERIFY.sh`/`post_install_check.sh` if present |
| all | `is_model_cache/` (88 MB) + `is_wheels_cp310/` must ride inside the image | IS scoring silently absent from reports if missing — build-004 payload carries both; post-install check asserts them |

Everything build-004 needs is inside the one image (torch 2.5.1+cu124 venv,
fairseq patches, whisper cache, spaCy cp310, IS model cache). cu124 torch runs
**natively** on pre-Blackwell GPUs and via **compute_90 PTX JIT** on Blackwell
(first decode 5–15 min, then cached).

---

## 4. Update route + rollback per machine

Ship order: **M3 first** (doubles as the mandatory staging dry-run) → M1 → M2.

| | Load | Flip | Verify | Rollback |
|---|---|---|---|---|
| **M3** | `zstd -d \| docker load` | `docker.conf` → `client-build-004` (keep `cu128-exact` loaded) | full acceptance battery, network disabled (`nmcli networking off`) | revert `docker.conf` |
| **M1** | verify sha256 → `docker load` (15–30 min) | write `C:\vsp\launcher\image.tag`; re-run `vsp-setup.ps1` **as Administrator** (bump `$BwTag` fallback) | `post_install_check.ps1` → JIT warm-up **with operator watching** → 8-item acceptance | `rollback.ps1` (build-003 stays loaded) |
| **M2** | disk headroom check first (~42 GB image) → `docker load` | rewrite `docker.conf` (retires the layered `may2026-update` lineage) | adapted `post_install_check.sh` + acceptance incl. **long-segment decode on the 12 GB GPU**, two-run determinism check, NEA/WWER columns present, no startup network hang | keep `may2026-update` until acceptance passes, then optionally `docker rmi` it |

Per-machine acceptance extras: M1 — client's own `.MTS` file through the UI;
Edge drag-drop **and** file-picker fallback. M2 — the four §3 risk items each
have a named check above. All — bring back `INSTALL_REPORT.txt` (or VERIFY
output) + a copy of the flip file on the USB; paste into §6.

---

## 5. Build manifests

### client-build-003 (shipped)
- **Built**: 2026-05-13 · tarball `vsp-image-client-build-003-20260513.tar.zst` (40 GB, S3 copy at `s3://yoad-vsp-transfer/vsp/`) · tags on client: `client-build-003`, `client-build-003-bwfix`
- **Contents** (reconstructed from git — no manifest was written at ship time, which is why this section exists): payload as of ~2026-05-12, incl. MBR display default, joint bands, `VSP_NBEST=1`, `VSP_FULL_OUTPUTS=1`, HF offline vars, fairseq patches, entries 1–35.
- **Deployed to**: M1 only.

### client-build-004 (built, awaiting field deployment)
- **Built**: 2026-08-07 · image ID `268f5765d4c0` (60.9 GB) · tag `vsp-llm-pipeline:client-build-004` · git tag `client-build-004` @ `afe1f69` · tarball `vsp-image-client-build-004-20260807.tar.zst` + `.sha256` + 4 GB `part_*` splits at `s3://yoad-vsp-transfer/vsp/` _(sha256 recorded in the S3 sidecar)_.
- **Commit range**: `client-build-003` (≈`abb2167`, May 12) → `afe1f69` (Aug 7). Ships: entries 32–35 (fairseq decode-crash patch, `VSP_FULL_OUTPUTS=1`, HF offline vars, cp310 spaCy), May-25 client UX bundle, May-26 trust stack + Watch-with-CC + audio injection, May-27 five formats, Aug-6 complete-screen UI fixes (entry 36), **entry 37 format-scanner fix** (without which the five formats never worked — found by this build's `.mts` E2E), decode-counter test guard.
- **Default-EXCLUDE (research, not client-hardened)**: MBR word-confidence sidecars (`b3cbb77`), phonetic substitution (`d9e7c0a`/`c203978`), egla_kafe eval suite, Llama-3 prep (`vsp_llm.py`/`vsp_llm_decode.py` EC2 diffs stay out).
- **Gates passed**: `test_payload_sync.sh` PASS (6 expected diffs) · 201-passed unit suite (incl. new `test_format_support.py`) · in-build 37/37 module tests · post-install battery **15/15** (mechanism asserts + `--network=none` offline imports) · **raw `.mts` fixture E2E** through the full pipeline to report+IS.
- **Build cost note**: first build-004 image (`64190858248c`) was discarded pre-upload after the `.mts` E2E exposed entry 37; rebuilt same-tag with the fix.
- **Deployed to**: nowhere yet — M3 staging dry-run first, then M1, then M2 (§4).

---

## 6. Field-verification log (append after every trip)

| Date | Machine | Action | Result | Evidence |
|---|---|---|---|---|
| 2026-02-15..17 | M2 | initial deploy (~v1.0.32-35) | OK | container-update-feb2026.md |
| 2026-05-12 | M2 | May-2026 overlay applied (`apply_update.sh` → `may2026-update`) | OK, but bug-17 decode crash same day → entries 32–35 authored, **never shipped** | container-deployment-lessons-may2026.md |
| 2026-05-13 | M1 | build-003 image installed | OK | client-laptop-deployment-aug2026.md |
| 2026-08-03 | M1 | remote verification (operator, phone) | running build-003 | client-laptop-deployment-aug2026.md §1 |
| _(next)_ | M3 | pre-update audit + build-004 + staging dry-run | | |
| _(next)_ | M1 | build-004 | | |
| _(next)_ | M2 | pre-update audit + build-004 | | |

---

## 7. Lessons learned (why this doc looks the way it does)

- **No build manifest → archaeology.** build-003's contents had to be
  reconstructed from git months later. Every build now writes §5 before shipping.
- **Unverified shipments don't count.** Entries 32–35 were written *for* M2's
  field crash and then never delivered; nothing recorded that. §6 requires a
  dated, evidence-backed row per trip, with the install report carried back.
- **Layered patches erode certainty.** The overlay + `docker commit` route left
  M2 as "May overlay, probably" — single image everywhere; the tag on disk IS
  the version.
- **Staging dry-run before client trips** (bug 17 was a latent image bug): M3
  takes every new build first, network disabled.
- **Input-boundary features need real fixtures** — ".MTS not accepted" has no
  unit test; the build gate decodes a genuine camcorder file end-to-end.
- **Mechanism asserts, not exit codes** — the May-2026 cycle shipped a build
  with silently degraded features that exited 0; checks grep for the actual
  artifacts (`hyp_*` keys, `niv` column, agreement sidecar).
- **Six container-adapted files are sacred** (`run_flat_english_pipeline.sh`,
  `lib/asr.sh`, `lib/lrs3_prep.sh`, `lib/test_all_modules.sh`,
  `vsp-ui/app/config.py`, `transcription_manager.py`) — wholesale sync + hand
  merge, policed by `scripts/tests/test_payload_sync.sh`.
- **Windows field traps**: PS 5.1 em-dash corruption (never hand-edit `.ps1`
  on-site), Administrator shell required, Docker Desktop port-proxy wedging
  (restart it first), JIT "looks frozen" (warn the operator, watch the first
  decode together).
- **Operator vocabulary**: "restart" / "frozen" / ".mtk" map to specific UI
  states — ask *"what exactly is on screen?"* and *"what did you click just
  before?"* before diagnosing.
- **sha256 at every hop** — S3 upload, S3 download, USB, on-box before
  `docker load`.
