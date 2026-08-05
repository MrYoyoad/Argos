# S3 → S3 Cross-Account + Cross-Region Transfer (DataSync) — Runbook

**Goal**: Copy ALL data from source account **733430125971** (eu-west-1) to a new account in
**il-central-1**, using AWS DataSync (managed, resumable, checksum-verified — no expiring-token
problem mid-transfer).

**Source buckets** (from [s3-data-inventory-aug2026.md](s3-data-inventory-aug2026.md)):

| Bucket | Size | Objects | Notes |
|---|---|---|---|
| `yoad-vsp-transfer` | ~1.47 TB | ~1.8M | includes 653 GB `argos//aws-backup-restore_2025-07-28…/` **duplicate** (exclusion candidate) |
| `conversation-datasets-733430125971` | 23.7 GB | — | EgoCom / RealTalk / AMI / Egla-Kafe |

**Design**: one destination bucket, two DataSync tasks (one per source bucket), each writing to a
top-level prefix mirroring the source bucket name. Task mode: **Enhanced** (required for reliable
cross-account + cross-region; Basic mode hits network connection errors per AWS docs).

**Key facts** (verified against the [AWS cross-account tutorial](https://docs.aws.amazon.com/datasync/latest/userguide/tutorial_s3-s3-cross-account-transfer.html), Aug 2026):

- DataSync task + IAM role live in the **SOURCE** account.
- The task must be created **in the destination region (il-central-1)** → the **source account
  must have il-central-1 opted in** (it's an opt-in region).
- Agentless cross-region transfer to opt-in regions is supported (AWS announcement July 2024).
- Destination bucket must have **ACLs disabled** (default for new buckets) so the destination
  account owns all transferred objects.
- Cross-account destination location can only be created via **CLI**, not console.

## Parameters (fill in)

```bash
SRC_ACCOUNT=733430125971
DEST_ACCOUNT=<<<DEST_ACCOUNT_ID>>>          # TODO from user
DEST_BUCKET=<<<e.g. argos-vsp-il>>>          # TODO agree on name
DEST_REGION=il-central-1
ROLE_NAME=DataSync-s3-cross-transfer
```

## Phase 1 — Destination account (admin console or a `[dest]` CLI profile)

1. **Create bucket** in il-central-1, defaults are fine (ACLs disabled = "Bucket owner enforced"
   is the default — keep it):
   ```bash
   aws s3api create-bucket --bucket $DEST_BUCKET --region il-central-1 \
     --create-bucket-configuration LocationConstraint=il-central-1 --profile dest
   ```
2. **Bucket policy** — grant the source-account DataSync role (created in Phase 2; the ARN is
   deterministic, so this can be done first):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Sid": "DataSyncCrossAccountAccess",
       "Effect": "Allow",
       "Principal": { "AWS": "arn:aws:iam::733430125971:role/DataSync-s3-cross-transfer" },
       "Action": [
         "s3:GetBucketLocation", "s3:ListBucket", "s3:ListBucketMultipartUploads",
         "s3:AbortMultipartUpload", "s3:DeleteObject", "s3:GetObject",
         "s3:ListMultipartUploadParts", "s3:PutObject",
         "s3:GetObjectTagging", "s3:PutObjectTagging"
       ],
       "Resource": [
         "arn:aws:s3:::<<<DEST_BUCKET>>>",
         "arn:aws:s3:::<<<DEST_BUCKET>>>/*"
       ]
     }]
   }
   ```

## Phase 2 — Source account (via temporary `[transfer]` profile, General-Admin-PS)

Setup only needs the token for ~15 min; the transfer itself runs under the role.

1. **Opt in il-central-1** (one-time; takes minutes to a few hours to activate):
   ```bash
   aws account get-region-opt-status --region-name il-central-1 --profile transfer
   aws account enable-region --region-name il-central-1 --profile transfer   # if DISABLED
   ```
2. **Create the DataSync IAM role** (trust = datasync.amazonaws.com):
   ```bash
   aws iam create-role --role-name $ROLE_NAME --profile transfer \
     --assume-role-policy-document '{
       "Version":"2012-10-17",
       "Statement":[{"Effect":"Allow","Principal":{"Service":"datasync.amazonaws.com"},
                     "Action":"sts:AssumeRole"}]}'
   ```
3. **Role permissions** — READ both source buckets + WRITE destination bucket (inline policy):
   read/list on `yoad-vsp-transfer`, `conversation-datasets-733430125971` and their `/*`;
   the destination-bucket statements from the tutorial (with
   `"Condition": {"StringEquals": {"aws:ResourceAccount": "<<<DEST_ACCOUNT>>>"}}`).
4. **Locations** (all created from the source account):
   ```bash
   # source locations (eu-west-1) — one per source bucket
   aws datasync create-location-s3 --region eu-west-1 --profile transfer \
     --s3-bucket-arn arn:aws:s3:::yoad-vsp-transfer \
     --s3-config "{\"BucketAccessRoleArn\":\"arn:aws:iam::$SRC_ACCOUNT:role/$ROLE_NAME\"}"
   # (repeat for conversation-datasets-733430125971)

   # destination locations (il-central-1) — one per target prefix
   aws datasync create-location-s3 --region il-central-1 --profile transfer \
     --s3-bucket-arn arn:aws:s3:::$DEST_BUCKET --subdirectory /yoad-vsp-transfer \
     --s3-config "{\"BucketAccessRoleArn\":\"arn:aws:iam::$SRC_ACCOUNT:role/$ROLE_NAME\"}"
   # (repeat with --subdirectory /conversation-datasets)
   ```
5. **Tasks** — created **in il-central-1** (destination region), **Enhanced** mode, with
   verification; optional exclude of the 653 GB duplicate:
   ```bash
   aws datasync create-task --region il-central-1 --profile transfer \
     --source-location-arn <src-loc-arn> --destination-location-arn <dst-loc-arn> \
     --name vsp-transfer-main --task-mode ENHANCED \
     --options VerifyMode=ONLY_FILES_TRANSFERRED,TransferMode=CHANGED,OverwriteMode=ALWAYS \
     --excludes FilterType=SIMPLE_PATTERN,Value='/argos//aws-backup-restore*'
   aws datasync start-task-execution --region il-central-1 --profile transfer --task-arn <task-arn>
   ```
6. **Monitor** (no creds needed once started — or re-paste a token later):
   `aws datasync describe-task-execution --region il-central-1 ...` or destination-account console
   → DataSync has no visibility there, so check bucket size:
   `aws s3 ls s3://$DEST_BUCKET --recursive --summarize` (or CloudWatch metrics in source account).

## Cost estimate (~1.5 TB, ~2.4M objects)

| Item | Est. |
|---|---|
| DataSync Enhanced (~$0.0125–0.015/GB) | ~$19–23 |
| Inter-region transfer eu-west-1 → il-central-1 (~$0.02/GB) | ~$30 |
| S3 PUT requests at destination (~2.4M) | ~$12 |
| **One-time total** | **~$60–65** |
| Ongoing il-central-1 storage (~$0.024/GB-mo) | ~$35/month |

Excluding the 653 GB backup duplicate saves ~$27 one-time and ~$16/month.

## Status

- [ ] Destination account ID + bucket name confirmed
- [ ] Decision: include or exclude 653 GB `argos//aws-backup-restore…` duplicate
- [ ] Phase 1 done (dest bucket + policy)
- [ ] il-central-1 enabled on source account
- [ ] Phase 2 role + locations + tasks created
- [ ] Transfers completed + verified
