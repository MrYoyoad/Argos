# Box Evacuation — August 6, 2026

Full evacuation of the EC2 box (`i-05ae5ccb8750f002d`, account 733430125971,
eu-west-1) ahead of decommission and migration to a new AWS account
(il-central-1 — see [s3-cross-account-transfer-datasync.md](s3-cross-account-transfer-datasync.md)).
Everything irreplaceable now lives in **git (GitHub)** and/or
**`s3://yoad-vsp-transfer/vsp/box_evac_20260806/`**. Since the evac prefix is
inside `yoad-vsp-transfer`, the planned DataSync sweep carries it to the new
account automatically.

Of ~879 GB used on the box, ~95 GB was irreplaceable and moved; the rest is
regenerable (see "Explicit discards" below).

## Git — all code pushed (verified by fresh recursive clone)

> **Post-evacuation update (2026-08-08 audit):** work continued after Aug 6 — HEAD of
> each `main` supersedes the commit column below (notably: entry-37 format fix,
> client-build-004; Argos ahead of `f87d782`, auto_avsr at `94e4c86`). All later
> commits are pushed, tags `client-build-004` + `ec2-v1.2` pushed, and the S3 git
> bundles were refreshed the same day.

| Repo | Remote | Final commit | What was rescued |
|---|---|---|---|
| Argos (main, `/home/ubuntu`) | `MrYoyoad/Argos` | `f87d782` | 4 untracked binaries (3 project-brief docx + `Argos_VSP_Final.pptx`); uncommitted vsp-ui complete-screen fixes (sync item 36); 3 orphan gitlinks under `vsp_docker/galaxy_export/` removed (they broke `clone --recursive`); submodule pointers bumped |
| VSP-LLM | `MrYoyoad/VSP-LLM` | `c6d0e01` | 7 working scripts + `fairseq/fairseq/metrics/` stub; `version.py` editable-install bump reverted; 4 junk broken-redirect dirs deleted |
| auto_avsr | `MrYoyoad/auto_avsr` | `07220fa` | 9 preparation/segmentation scripts |
| av_hubert | **`MrYoyoad/av_hubert` (new fork)** | `33963c8` | 2 flat→LRS3 prep scripts; upstream `facebookresearch/av_hubert` kept as `upstream` remote. `.gitmodules` in Argos now points at the fork |

**Verification**: `git clone --recursive --depth 1 --shallow-submodules
https://github.com/MrYoyoad/Argos.git` completes with zero submodule errors;
all rescued files present in the clone.

## S3 — `s3://yoad-vsp-transfer/vsp/box_evac_20260806/`

The instance role can only Get/Put (no List/Delete) under `vsp/*`, so use
`aws s3api head-object` / `aws s3 cp` against exact keys; listing requires
portal admin credentials.

| Prefix | Contents | Size | Status |
|---|---|---|---|
| `models/vsp_checkpoints/` | `checkpoint_finetune.pt`, `checkpoint_freeze.pt`, `large_vox_iter5.pt` + `vsp_checkpoints.sha256` — THE pipeline weights, not publicly downloadable | ~11.5 GB | see sha256 below |
| `models/finetune_sweeps/r16/`, `r64/` | `checkpoint_best.pt` + `checkpoint_last.pt` per run (5 intermediate epoch snapshots per run were deliberately discarded) + `run_metadata/` (training/hydra logs, eval_sweep CSVs, checkpoint_correlation) | ~16 GB | uploaded |
| `models/small/` | `golden_weights/` (clustering baseline, irreplaceable), `face_detection/` | ~4 MB | uploaded |
| `archives/_archive/` | `_archive/` incl. `project/ron` (a repo with no remote and no commits — only copy anywhere) and `project/kaha_summary` (its `.git` excluded; remote exists) | ~23 GB | uploaded |
| `archives/flat_runs_archive/` | ~40 timestamped pipeline run dirs | ~14 GB | uploaded |
| `datasets/datasets/` | Full `datasets/` tree: **`english_data_2025_11_20` (the 1,497-segment benchmark — irreplaceable)**, `clients/egla_kafe` (+`_resolution`), `seamless_interaction` (only real copy), `lrs3orig_sync.tar`, arabic dirs | 17.9 GB | uploaded, 0 failures |
| `datasets/data/` | AVSpeech fine-tune slice (1,273 segments) | 0.97 GB | uploaded |
| `datasets/vsp_input*/` | `vsp_input` (incl. `.transcriptions/`, `.excluded/`), `vsp_input_tuning`, `vsp_input_realtalk_demo`, `vsp_input_backup` (symlinks dereferenced → real content) | ~4.7 GB | uploaded |
| `datasets/auto_avsr_tarballs/` | `english_1000_subset_hrz*.tar.gz` | 1.25 GB | uploaded |
| `results/` | `english_full_results` (incl. 1.7 GB client_outputs), `english_full_nbest_eval`, `english_full_results_2026-05-01`, `tuning_results`, `finetune_eval_baseline_sweep`, `outputs`, `logs`, `presentation_materials_20260224`, VSP-LLM working data (kmeans bins, golden_kmeans, features, labels, decode), `avhubert_flat`, `finetune_data` | ~4 GB | uploaded |
| `git-bundles/` | `Argos.bundle` (854 MB), `VSP-LLM.bundle`, `auto_avsr.bundle`, `av_hubert.bundle` — full-history belt-and-suspenders alongside GitHub | 912 MB | uploaded + size-verified |
| `payload-diffs/` | `container_payload_20260507_diffs.tar.gz` — git diffs + status + small untracked files from the two dirty payload checkouts (the container-specific code variants); the 58 GB payload itself was NOT uploaded (duplicate snapshot) | 324 MB | uploaded |
| `config/home_config_secrets.tar.gz.gpg` | Home config **and secrets** (dotfiles, `.claude-argos` memory/plans, `.claude`, `.ssh`, `.git-credentials`, `.gnupg` keyring, HF token, May-2026 claude backup). **AES-256 gpg-symmetric; passphrase held by Yoad** (delivered at evacuation time — store in password manager). Rotate the GitHub token + SSH keys after migration regardless | 305 MB | uploaded + decrypt roundtrip verified (6,043 files) |
| `misc/` | `FOR_CLIENT_OLD/` (Feb-2026 client kit found stashed inside `.gnupg` — 94 MB pipeline tarball + Arch NVIDIA offline pkgs), `Argos_VSP_Client_May2026*.zip`, `LESSONS_for_VS_Code_Claude.md`, root PNGs/log, container sha256 | ~460 MB | uploaded |

Two harmless 21-byte credential-test keys exist at `_test.txt` and
`_upload_test.txt` (DeleteObject is denied for the instance role; remove them
with admin creds if they bother you).

### sha256 of the critical checkpoints

```
174ba60785387c64edf88e3ea8ae3528bb4dddb8a4f95d493c5aef7d7b2d2843  checkpoint_finetune.pt
c3db4977ff404749116d97713a44b2312dd330faeff090c33f26e2e3140196ef  checkpoint_freeze.pt
343c9dbaa29847b8c4d0d9503c43f2877fd2efde9988d41abf14e74f28232b75  large_vox_iter5.pt
```

### Already in S3 before the evacuation (verified byte-exact, NOT re-uploaded)

- `vsp/vsp-image-client-build-003-20260513.tar.zst` (42,724,807,369 B — matches local)
- `vsp/vsp_linux_container_FINAL_20260217.tar.gz` (250,620,540 B — matches local)
- `vsp/vsp-kit-extras-client-build-003.tar.gz` (1,624,098,049 B — matches local)
- Client builds 001/002, Windows installers, teammate package, egla_kafe raw
  masters, EgoCom/RealTalk/AMI, full LRS3 + AVSpeech (see
  [s3-data-inventory-aug2026.md](s3-data-inventory-aug2026.md))

## Explicit discards — regenerable, die with the box

| Item | Size | How to regenerate |
|---|---|---|
| `/var/lib/docker` (7 images + build cache) | 349 GB | rebuild from Dockerfiles in `vsp_docker/`; exported build-003 image is in S3 |
| `vsp_docker/container_payload_20260507/` | 58 GB | duplicate snapshot of host repos + venvs; unique code captured in `payload-diffs/` |
| `~/.cache` (HF 50G, pip 32G, uv, whisper) | 91 GB | re-download (Whisper models, HF models) |
| `build_assets/` (wheels + prebuilt venvs) | 30 GB | rebuild via its scripts; needed only for air-gapped client builds |
| venvs (`vsp-llm-yoad-venv`, `pre-process-venv`, `vsp-ui/venv`) | 15 GB | rebuild per fresh-venv guide (VSP freeze needs `--no-deps`) |
| `Llama-3.1-8B`, `Llama-3.1-8B-Instruct`, `Llama-2-7b-hf` copies | ~80 GB | re-download from HuggingFace (gated — needs HF account; token is in the config tarball) |
| `face_alignment/` | 399 MB | `git clone https://github.com/ibug-group/face_alignment` (was clean + in sync) |
| `auto_avsr` preprocessed intermediates (`flat*`, `preprocess_ready*`, `preprocessed_*`) | ~1 GB | re-run preprocessing on inputs (all inputs evacuated) |
| `/tmp/finetune_smoke_*`, `/tmp/lrs3_decode` | 34 GB | throwaway smoke tests / re-derivable decode output |
| `.vscode-server`, OS caches | ~7 GB | regenerated on any new box |

## Restore on the new server

1. `git clone --recursive https://github.com/MrYoyoad/Argos.git` (or from
   `git-bundles/` if GitHub is unavailable — see below). GitHub access for a
   transfer team is granted via a **read-only fine-grained PAT** scoped to the
   four repos (Contents: Read-only), never via collaborator invites.

   **Restore from bundles without GitHub** (bundles are full-history repo
   snapshots):
   ```bash
   aws s3 cp s3://<bucket>/vsp/box_evac_20260806/git-bundles/ . --recursive
   git clone Argos.bundle /home/ubuntu && cd /home/ubuntu
   git submodule init
   git config submodule.VSP-LLM.url  ../VSP-LLM.bundle
   git config submodule.auto_avsr.url ../auto_avsr.bundle
   git config submodule.av_hubert.url ../av_hubert.bundle
   git submodule update      # checks out the pinned commits from the bundles
   ```
   (Bundles are read-only snapshots from 2026-08-08; repoint remotes to
   GitHub later if write access is ever arranged.)
2. Follow [ec2-setup-from-scratch.md](ec2-setup-from-scratch.md); wherever it
   says "old box", the source is now a `box_evac_20260806/` key.
3. Pull `models/vsp_checkpoints/*` into `VSP-LLM/checkpoints/`, verify against
   `vsp_checkpoints.sha256`; pull `models/small/golden_weights/` into
   `~/golden_weights/`; datasets/results as needed.
4. Decrypt the config tarball (`gpg -d`) for dotfiles, Claude memory, HF token;
   rotate the GitHub token and SSH keys it contains.

## Verification record (2026-08-06)

- Fresh `clone --recursive` from GitHub: PASS (zero errors, rescued files present).
- Encrypted config tarball: full S3→gpg→tar roundtrip PASS (6,043 entries).
- Datasets upload: 18,727 files / 24.78 GB, 20/20 head-object spot-checks
  byte-exact incl. Hebrew keys; egla_kafe root copy confirmed duplicate of
  `datasets/clients/egla_kafe` and skipped.
- Archives upload: `_archive` 105,377 files / 23.51 GB (24 min) + kaha_summary
  `.git` correctly excluded; `flat_runs_archive` 26,002 files / 15.13 GB
  (9 min); 37/37 head-object checks size-exact incl. Hebrew keys.
  **`project/ron` explicitly confirmed: 35,817 files / 5.44 GiB fully in S3**
  (its `.git` turned out freshly-initialized — no history existed; the working
  tree is the substance and is complete).
- Results upload: 11 trees, 4,692 files / 3.0 GiB, 40/40 spot-checks
  byte-exact. Sole failure investigated and resolved with **no data loss**:
  `VSP-LLM/labels/vsr/en/train.wrd` was a dangling symlink (target
  `auto_avsr/preprocessed_flat_seg4/433h_data/train.wrd` missing on disk);
  all 15 real label files verified in S3.
- Critical checkpoints: all three + `vsp_checkpoints.sha256` head-object
  verified in S3 (4,103,791,627 / 4,103,791,517 / 3,905,065,977 / 261 B);
  finetune-sweep best+last for r16 and r64 verified.
- `scripts/tests/test_s3_claims.sh` updated (claims 2–3 annotated as
  superseded; new check 4 head-objects the critical checkpoint in box_evac).
  Run 2026-08-06: **4 passed, 0 failed**.

## Post-evacuation audit (2026-08-08) — final sweep results

A full machine + git audit two days after the evacuation found and fixed:

**Git side** — 5 unpushed Argos commits + 1 auto_avsr commit (Aug-7 work:
entry-37 format fix, client-build-004) → pushed; tags `client-build-004` +
`ec2-v1.2` → pushed (plain `git push` never sends tags); av_hubert branch
tracking → `origin/main`; `upstream` remote restored to facebookresearch
(a `git submodule sync` had rewritten it to the fork); S3 bundles for Argos +
auto_avsr refreshed. Verified clean everywhere: no stashes, no local-only
branches with unique commits, kaha_summary pushed, all heads on GitHub via
`ls-remote`.

**Disk side** — 7 uncovered items found and uploaded (~140 MB):
`misc/generally_useful/` (the transferable style-guide hub — was in NO repo
or bucket; consider folding into the `knowledge` repo later),
`misc/decks/Argos_VSP_For_Orchard_May2026.pptx` + `Argos_VSP_Project_Review.pptx`
(shipped decks that existed only in /tmp),
`misc/windows_kits_as_shipped/vsp-{final,friend}-kit.zip` (the May-2026 kits
as actually handed to clients), `results/client_demo_report_2026-05-03/`,
`results/vspllm_working_data/whisper_txt_ar{,_txt}/`, `misc/smoke_75s.mp4`,
plus marginals (`misc/ipython_history.sqlite`, `misc/_e2e_report_preview/`,
`misc/ui_v9.png`).

**Verified needs-nothing**: `/home/ubuntu/flat` (358M — derivable from covered
`vsp_input` + `.transcriptions`), windows_kit dir (inside the S3 kit-extras
tarball), B3 confidence JSONs (inside covered results trees), no crontabs, no
custom systemd units, `/opt`//`/root`//`/usr/local/bin` stock, all dot-dirs
cache-only.

**⚠️ Last act before destruction**: the box kept receiving commits after the
Aug-6 evacuation — run one final `git status` + `git push` sweep across all
four repos (and refresh `git-bundles/` if anything moved) immediately before
terminating the instance.
