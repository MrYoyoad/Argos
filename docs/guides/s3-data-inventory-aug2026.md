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

## Bucket 2 — `s3://yoad-vsp-transfer` (NOT listable; key-by-key access only)

The role has GetObject bucket-wide and PutObject under `vsp/` only. Verified keys (HeadObject):

| Key | Size | What |
|---|---|---|
| `vsp/vsp-image-client-build-003-20260513.tar.zst` (+`.sha256`) | 42.7 GB | The shipped client Docker image (build-003 + bwfix) |
| `vsp/vsp-kit-extras-client-build-003.tar.gz` | 1.6 GB | Build-003 companion kit |
| `vsp/vsp-kit-extras-client-build-001.tar.gz` | 9.8 MB | Older kit |
| `vsp/teammate_package_20260803.zip` (+`.sha256`) | 39.8 MB | The Aug-2026 teammate onboarding package |

Probed and absent: `vsp/vsp-image-client-build-001.tar.zst`, `...-002...` (never uploaded or
differently named — not enumerable without ListBucket).

## Access rules (hard-won — do not re-probe)

- EC2 role: **read** both buckets (list only `conversation-datasets-*`), **write** only
  `yoad-vsp-transfer/vsp/`. No `ListAllMyBuckets`.
- Writing to `conversation-datasets-*`: laptop only, short-lived portal credentials
  (`conversation_datasets/refresh_aws_creds.sh` in the bucket documents the flow).
- Use `aws` CLI or `s5cmd` (`--numworkers 32`); never FUSE. `LC_ALL=C.UTF-8` for Hebrew keys.
