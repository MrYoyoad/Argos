# VSP Transfer — Handoff for the Technical Team

*Written 2026-08-08. Contact for decisions: Yoad Oxman.*

## Where things stand (the good news first)

**All the preparation work is already done and verified.** You are not rescuing
anything and you don't need to hunt for files. Concretely:

- **All code** is pushed to private GitHub repositories, and a fresh
  `git clone --recursive` was tested — it reproduces the complete working
  system with zero errors.
- **All data that existed only on the old server** (~95 GB: model checkpoints,
  the evaluation benchmark, client datasets, results, archives) was copied to
  S3 under `s3://yoad-vsp-transfer/vsp/box_evac_20260806/`, with byte-level
  verification and SHA-256 checksums for the critical files.
- **Every step you need to perform has a written, tested guide** in the repo.
  This document only tells you which guide to use when, and why.

Your job has exactly four steps: **copy the S3 data to the new AWS account →
verify the copy → build the new server → shut down the old one.** In that
order, and order matters.

---

## What you need before starting

| Item | Why you need it | Where it comes from |
|---|---|---|
| Admin access to the **source** AWS account (`733430125971`, region `eu-west-1`) | The copy job (DataSync) is created and runs in the source account | Your team / Yoad |
| Admin access to the **destination** AWS account (region `il-central-1`) | You create the destination bucket and its access policy there | Your team |
| The **destination bucket name** | Decided by Yoad, not by the runbook | Ask Yoad |
| **The code** | To read the guides and later build the server | Included in the S3 data you're copying — see next section |
| A **HuggingFace account** with `meta-llama/Llama-2-7b-hf` access approved | The pipeline's language model is gated by Meta; approval is free and takes up to a day — request it early | huggingface.co, then the model page → "Request access" |

**What you do NOT need**: the file `config/home_config_secrets.tar.gz.gpg` in
the S3 backup is Yoad's personal encrypted configuration. It is not pipeline
material, you cannot open it, and you don't need to — just let it copy across
with everything else.

## Getting the code (read-only, by design)

The repositories live under Yoad's personal GitHub account and stay private.
You don't need GitHub at all:

**The standard way — from the S3 backup.** The bucket you are copying
contains complete snapshots of all four repositories ("git bundles") at
`vsp/box_evac_20260806/git-bundles/` — full code, full history, current as of
2026-08-08. The exact restore commands are in
[box-evacuation-aug2026.md](box-evacuation-aug2026.md), section
*"Restore on the new server"*. Clone from the bundles and you have
everything, including all the guides referenced in this document.

(If, during the work, you need a code fix or something newer than the
snapshot, ask Yoad — he can push an updated bundle to S3 or send the file
directly. There is no write access to arrange and nothing to return
afterwards.)

---

## Step 1 — Copy the data to the new account

**What this does**: copies the whole `yoad-vsp-transfer` bucket (~1.5 TB —
research datasets, deployment images, and the `box_evac_20260806/` backup)
from the old AWS account to a bucket in the new account. AWS DataSync does
this bucket-to-bucket — no server in the middle, one-time cost ≈ $60.

**How**: follow
[s3-cross-account-transfer-datasync.md](s3-cross-account-transfer-datasync.md)
**literally, top to bottom**. It is a tested runbook, and it already handles
the four traps that break naive attempts — listed here so you know they are
features, not mistakes:

1. **Region opt-in first**: `il-central-1` is an opt-in region. The *source*
   account must enable it before anything else works
   (`aws account enable-region`). The runbook covers this.
2. **The DataSync task must be created in `il-central-1`** (destination
   region), even though it lives in the source account.
3. **Task mode ENHANCED, not Basic** — Basic hits network errors on
   cross-account + cross-region jobs. Already set in the runbook's commands.
4. **The cross-account destination location can only be created by CLI**, not
   in the AWS console. The runbook gives you the exact CLI calls.

Also per the runbook: **exclude the `argos//aws-backup-restore*` prefix** —
it's a 653 GB duplicate of data that exists in tidied form elsewhere in the
bucket. Excluding it saves money and hours, and loses nothing.

There is a second, small bucket (`conversation-datasets-733430125971`,
~24 GB) — the runbook covers copying it too (second task, same pattern).

## Step 2 — Verify the copy (before deleting ANYTHING, anywhere)

**Why this step exists**: the old server will be destroyed. After that, the
new bucket is the only copy of the critical files. So we prove the copy is
good while the originals still exist.

Do all three checks in the **new** account's bucket:

1. **The single most important file exists and is intact**:
   `vsp/box_evac_20260806/models/vsp_checkpoints/checkpoint_finetune.pt`
   — about 4.1 GB. Its expected SHA-256 is recorded in
   [box-evacuation-aug2026.md](box-evacuation-aug2026.md). If this file is
   good, the pipeline can live again; without it, it can't.
2. **Object counts / total size** of the new bucket roughly match the source
   (DataSync's task report gives you this for free — keep that report).
3. From any machine with the repo: run `scripts/tests/test_s3_claims.sh`
   (adjust bucket name if prompted by its output) — it's the project's
   standing guard test for "is the data where the docs say it is".

**Green on all three = the data has safely migrated. Only now may steps 3–4
proceed.**

## Step 3 — Build the new server

**What this does**: recreates the working GPU pipeline machine in the new
account.

- Machine: a GPU instance comparable to the old one (NVIDIA T4 class or
  better), Ubuntu, a few hundred GB of disk.
- Then follow
  [ec2-setup-from-scratch.md](ec2-setup-from-scratch.md) **top to bottom** —
  it was verified against a real rebuild on 2026-08-03. It covers: cloning the
  code, creating the Python environments, downloading/placing every model
  file, and where each dataset goes.
- Wherever that guide's asset table says "**old box**" as a source, use the
  matching key under `vsp/box_evac_20260806/` in your new bucket instead —
  the guide has a banner explaining exactly this mapping.
- The HuggingFace approval from the prep table is used here (Llama-2
  download). Everything else is public or already in your bucket.

**Success check**: the guide ends with a smoke run of the pipeline; a
processed test video with a generated report = the server is alive.

## Step 4 — Decommission the old server

**Only after Step 2 is fully green** (ideally after Step 3 too, so the old
box is available for comparison if anything looks off).

On the old box (`/home/ubuntu`), as the literal last action before
termination:

```bash
for d in /home/ubuntu /home/ubuntu/VSP-LLM /home/ubuntu/auto_avsr /home/ubuntu/av_hubert; do
  git -C $d status --short --branch | head -3
  git -C $d push origin main
done
```

**Why**: the box remained in use after the evacuation and may hold commits
newer than the last push. This sweep costs one minute and closes the last
possible loss window. If it shows anything unexpected (uncommitted files,
"ahead of origin"), resolve or report before terminating.

Then terminate the instance. Done.

---

## If something is unclear

- **Big picture / project context**:
  [project-handover-july2026.md](project-handover-july2026.md)
- **What exactly is in the S3 backup and why**:
  [box-evacuation-aug2026.md](box-evacuation-aug2026.md)
- **Decisions only Yoad can make**: destination bucket name, anything about
  client data, anything requiring a change to the code.
