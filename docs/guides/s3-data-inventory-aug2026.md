# S3 Data Inventory — August 3, 2026

Measured live from the EC2 box (instance role `AmazonSSMRoleForInstances`, account 733430125971).
Companion to [teammate-briefing-aug2026.md](teammate-briefing-aug2026.md) §2. Guard test:
`scripts/tests/test_s3_claims.sh`.

## Bucket 1 — `s3://conversation-datasets-733430125971` (listable; read-only from EC2)

**Totals: 6,325 objects, 23.7 GB. Dates: 2026-05-02 → 2026-07-13.**
Uploads were made from the laptop with access-portal credentials (`refresh_aws_creds.sh` flow);
the EC2 role can read everything but write nothing here.

| Prefix | Size | Objects | What it actually is |
|---|---|---|---|
| `conversation_datasets/egocom/` | 14.9 GB | 18 | **EgoCom corpus** (first-person conversations): `egocom240p.tar.gz.aa–af` split archive (9.4 GB — all 175 videos at 240p, reassemble with `cat`), 4 sample 720p 20-min videos (~4.7 GB), and `annotations/` (359,535 word-level transcripts CSV + speaker labels + video_info) |
| `conversation_datasets/realtalk/` | 4.3 GB | 1,029 | **RealTalk corpus** (unscripted YouTube conversations): `data/english/videos/` 103 objects / 2.8 GB, `data/non_english/` 10 / 0.4 GB, `data/_archive/` 911 annotation files (+ `annotations.tar.gz` 241 MB), meta tars, pre-computed transcripts |
| `conversation_datasets/egla_kafe/` | 3.0 GB | 68 | **Complete raw Egla-Kafe client corpus** — more than just the masters: 5 iPhone-4K masters `IMG_6821–6825` (1.49 GB), `קטעי דוברים/` per-speaker crops (42 files, 926 MB), `שפם/` worn-mustache scenes (5 videos, 224 MB), `סצנה 1/` (6 videos, 180 MB), `סצנה 2/` (5 videos, 164 MB), plus `manifest.csv` + upload scripts. Hebrew keys — use `LC_ALL=C.UTF-8` with s5cmd |
| `conversation_datasets/ami/` | 1.1 GB | 5,176 | **AMI Meeting Corpus** slice: 14 room-view media files (0.68 GB) + full word-level annotation set (5,158 XML files + `annotations.tar`) |
| `tmp/` | 0.4 GB | 2 | **July client deliverable bundles**: `EglaKafe_full_deliverables.zip` (385 MB, Jul 8 — the said-vs-heard conversation videos package) and `egla_kafe_meeting_package_20260713.zip` (24 MB — the July-13 meeting package) |
| `conversation_datasets/seamless_interaction/` | 139 KB | 17 | **Scripts only, no data** — HF downloader for the 27 TB corpus. The real 1.9 GB sample lives only on the EC2 box (`datasets/seamless_interaction/`) |
| `conversation_datasets/` root + `_smoke_test/` | ~30 KB | 14 | Downloader/validation tooling (`run_all.sh`, `validate.py`, per-dataset download scripts) + the bucket `README.md` explaining the curation (four candidate "real conversation" datasets for multi-speaker work, download-from-Mac pattern) |

**Notable:**

- **EgoCom / RealTalk / AMI exist ONLY in S3 — they are not on the EC2 box.** These are the curated
  candidate corpora for multi-speaker work (Mission 12); the bucket README ranks them
  (RealTalk → AMI → Seamless → EgoCom).
- The Egla-Kafe S3 copy is effectively the **whole raw client corpus** (masters + scenes + mustache
  + speaker crops), not merely the 5 masters.
- Still **zero** keys matching `avspeech` / `english_data` / `lrs3` — the 1,497-segment eval set,
  the AVSpeech processed set, and the LRS3 sample remain **EC2-box-only**, as do all 37 GB of
  model checkpoints.

## Bucket 2 — `s3://yoad-vsp-transfer` — **holds the FULL LRS3 and FULL AVSpeech**

> **Major correction (2026-08-03, evening).** Enumerated with short-lived admin credentials
> (General-Admin-PS role; the "paste a temporary `transfer` profile, delete after" flow).
> Every prior "LRS3/AVSpeech not in S3" conclusion — including the July-16 sweep in
> [llama3-migration.md](../finetuning/llama3-migration.md) §4 — was wrong: the EC2 instance
> role's GetObject is scoped to `vsp/*` only (403 elsewhere), which made the rest of the
> bucket invisible from the box and earlier probes came up empty.

**Totals: ~1.47 TB, ~1.83 M objects.** This is a June-15-2026 S3-migration (see `_mig/`) of a
July-2025 AWS-Backup restore of the original Argos file server.

| Prefix | Size | Objects | What |
|---|---|---|---|
| **`argos/datasets/lrs3orig/`** | **133.8 GB** | **303,901** | **The FULL LRS3 corpus** in canonical layout: `<youtube-id>/<NNNNN>.mp4 + .txt` pairs, main (0xxxx) and pretrain (5xxxx) clips together per talk dir. ~152 K clips ≈ the complete 151,819-utterance LRS3. **This unblocks the Llama-3.1 migration.** The box's 136 MB `lrs3orig_sync.tar` was a 5-talk sample of exactly this tree |
| **`argos/datasets/avspeech/`** | **519.9 GB** | **611,352** | **The full AVSpeech download**: `videos/xaa/…xa*/<youtube-id>/…` chunked layout. The box's 938 MB `data/avspeech` (1.3 K segments) was a tiny processed slice of this |
| `argos/custom_data/` | 38.1 GB | 1,118 | The 2024 project filming days: `filming_day_2024_{07_18,10_13,10_28}`, `clean_*` variants, `*_with_25_fps` re-encodes, inference sets |
| `argos//aws-backup-restore_2025-07-28T…/` | 653.0 GB | 915,248 | The RAW backup-restore dump (note double-slash key prefix). `argos/datasets/` above is its tidied migrated copy — this dump is largely a **duplicate** of lrs3orig+avspeech; candidate for deletion to cut ~650 GB of storage cost once the tidied copy is verified |
| `vsp/` | 122.2 GB | 27 | All THREE client image builds (001/002/003, ~42.7 GB each — 001/002 exist after all, my key-guessing just missed the date suffixes), kit-extras, Windows installers (WSL msixbundle, zstd, ps1 suite), `vsp_linux_container_FINAL_20260217.tar.gz`, `EglaKafe_guessing_game_20260719.zip` (412 MB), `Argos_VSP_v13_Amosi_2.pptx`, and the Aug-2026 `teammate_package_20260803.zip` |
| **`vsp/box_evac_20260806/`** | **~95 GB** | ~35 K | **Aug-6-2026 full box evacuation** — everything that was box-only before decommission: critical VSP checkpoints (finetune/freeze/large_vox + sha256), pruned finetune-sweep best+last (r16/r64), golden_weights, all datasets (incl. the irreplaceable `english_data_2025_11_20` benchmark and seamless_interaction), results, `_archive` + `flat_runs_archive`, git bundles of all 4 repos, container-payload diffs, encrypted home-config tarball. Manifest: [box-evacuation-aug2026.md](box-evacuation-aug2026.md) |
| `_mig/` | 253 MB | 9 | Migration tooling: 125 MB `manifest.csv` mapping `il-fs-migration-bucket` backup keys → this bucket, batch-job reports |

## Access rules (hard-won — do not re-probe)

- EC2 instance role: list+read `conversation-datasets-*`; on `yoad-vsp-transfer` it can
  **Get/Put under `vsp/*` ONLY** — `argos/*` (the datasets!) returns 403, and no ListBucket
  anywhere on this bucket. No `ListAllMyBuckets`.
- **To read the LRS3/AVSpeech trees from the EC2 box**: either (a) paste short-lived portal
  credentials into a temporary profile (`aws configure --profile transfer`, region `eu-west-1`;
  **delete `~/.aws/credentials` immediately after**) — the established flow; or (b) extend the
  bucket policy to grant the instance role `s3:GetObject`+`s3:ListBucket` on `argos/*`
  (the durable fix if training work starts).
- Writing to `conversation-datasets-*`: laptop/portal credentials only.
- Use `aws` CLI or `s5cmd` (`--numworkers 32`); never FUSE. `LC_ALL=C.UTF-8` for Hebrew keys.
- Disk math before any sync: LRS3 needs 134 GB, AVSpeech 520 GB — the box currently has
  ~94 GB free. Grow the volume (or attach a data volume) first.
