# Build and Transfer Guide — Air-gapped VSP Image

Internal guide for building the VSP Docker image on EC2 and getting it to the client laptop. Audience: Yoad. Companion to [CLIENT_INSTALL.md](/home/ubuntu/vsp_docker/CLIENT_INSTALL.md), which is the operator-facing doc.

## Build prerequisites

Run on the EC2 build box (`/home/ubuntu/`):

- `docker` working with NVIDIA Container Toolkit (verify: `docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi`)
- ≥ 200 GB free on `/var/lib/docker` (build artifacts + final image + pre-build cache)
- Internet access (for `apt-get`, PyTorch wheels, openai-whisper git checkout, fairseq git clone)
- Up-to-date `vsp_docker/galaxy_export/` matching latest EC2 main (run the regen procedure in `Chunk 1` of the plan if it's stale)

Verify before kicking off a build:

```bash
df -h /var/lib/docker
docker system df
ls -la vsp_docker/galaxy_export/face_alignment vsp_docker/galaxy_export/golden_weights vsp_docker/galaxy_export/is_wheels
bash vsp_docker/galaxy_export/lib/test_all_modules.sh   # Should pass on EC2
```

## Build

```bash
cd /home/ubuntu/vsp_docker
BUILD_ID="client-build-001"   # Bump per build
docker build -t "vsp-llm-pipeline:${BUILD_ID}" -f Dockerfile . 2>&1 | tee /tmp/vsp_build_${BUILD_ID}.log
```

Build takes 30-60 min on a c5.4xlarge-class box. The slow steps are:

- Step 1: `apt-get install` — ~1 min
- Step 4: `COPY galaxy_export/ ./` — 1-3 min for 43 GB
- Steps 6-7: pip install for `pre-process-venv` (cu128 PyTorch + Whisper + ASR deps) — 5-10 min
- Steps 11-13: pip install for `vsp-llm-yoad-venv` (cu124 PyTorch + transformers + fairseq + IS deps) — 10-20 min
- Step 15: Cython prebake — 1-3 min
- Step 17: in-build smoke test (`lib/test_all_modules.sh`) — 1 min

Smoke test failures during build mean `lib/` regressions — fix and rebuild.

## Save and split

```bash
docker save "vsp-llm-pipeline:${BUILD_ID}" | zstd -19 -T0 > "vsp-image-${BUILD_ID}.tar.zst"
sha256sum "vsp-image-${BUILD_ID}.tar.zst" > "vsp-image-${BUILD_ID}.tar.zst.sha256"
split -b 4G "vsp-image-${BUILD_ID}.tar.zst" "vsp-image-${BUILD_ID}.tar.zst.part_"
ls -la vsp-image-*
```

Expect ~35-45 GB compressed. zstd -19 maxes the ratio; -T0 uses all cores. Splitting at 4 GB gives resumable downloads on flaky links.

## Transfer off EC2 (no public IP)

This EC2 has no public IP. The exfil paths in order of practicality:

### Option 1 — S3 + presigned URLs (recommended)

Confirmed: VPC has Gateway endpoint to S3 (network reaches; permissions still need attaching).

**Permission setup** (one-time): the `AmazonSSMRoleForInstances` role attached to this EC2 lacks `s3:PutObject`. Either:
- Attach a bucket policy on a target bucket allowing this role write, or
- Add an inline policy on the role granting `s3:PutObject`+`s3:GetObject` to one bucket prefix, or
- Use short-lived credentials from a separate IAM user via `aws configure --profile transfer` — and **delete `~/.aws/credentials` immediately after the upload**, don't leave creds on the box.

**Upload**:
```bash
aws s3 cp "vsp-image-${BUILD_ID}.tar.zst.sha256" "s3://<bucket>/vsp/"
for f in vsp-image-${BUILD_ID}.tar.zst.part_*; do
  aws s3 cp "$f" "s3://<bucket>/vsp/parts/" --storage-class STANDARD_IA
done
# Optionally upload the unsplit copy too:
aws s3 cp "vsp-image-${BUILD_ID}.tar.zst" "s3://<bucket>/vsp/" --storage-class STANDARD_IA
```

**Download from your laptop**:
```bash
aws s3 cp "s3://<bucket>/vsp/" . --recursive
cat vsp-image-${BUILD_ID}.tar.zst.part_* > vsp-image-${BUILD_ID}.tar.zst
sha256sum -c "vsp-image-${BUILD_ID}.tar.zst.sha256"   # must print "OK"
```

Cost: ~$1 in S3 storage + egress for one transfer. **Delete the prefix after the client install completes** — don't leave 40 GB sitting in S3.

### Option 2 — Bastion + scp via ProxyJump

If a bastion host with a public IP can reach this EC2:

```bash
scp -o ProxyJump=<bastion-user>@<bastion-public-ip> \
  ec2-user@<this-ec2-private-ip>:/home/ubuntu/vsp_docker/vsp-image-${BUILD_ID}.tar.zst* \
  ./
```

Slower than S3 in most cases (single TCP stream, no parallel parts).

### Option 3 — VPN

If you have an always-on VPN to your VPC, just `scp` directly from EC2 to laptop. Same speed considerations as Option 2.

### Not viable

- AWS SSM Session Manager port-forward — works for small files, not 40 GB.
- Direct upload to a sharing service (Dropbox, GitHub Releases) — EC2 has no internet.

## USB to client

```bash
# On laptop (after S3 download + reassemble):
sha256sum -c vsp-image-${BUILD_ID}.tar.zst.sha256
cp vsp-image-${BUILD_ID}.tar.zst /Volumes/USB-SSD/      # or wherever your kit lives
cp vsp-image-${BUILD_ID}.tar.zst.sha256 /Volumes/USB-SSD/
```

Use a USB 3 SSD (≥ 128 GB), not a thumb drive. Cheap thumb drives at this size are usually slow flash that takes hours to write.

The full kit on the USB:

```
USB-SSD/
├── vsp-image-<build-id>.tar.zst
├── vsp-image-<build-id>.tar.zst.sha256
├── checks/
├── launcher/
├── samples/
├── offline_kit_<distro>/         # populated once OS confirmed
├── CLIENT_INSTALL.md
└── client-troubleshooting.md
```

## After the client is installed

1. Confirm the install report (`INSTALL_REPORT.txt`) shows STATUS: READY.
2. Delete the S3 bucket prefix (`aws s3 rm s3://<bucket>/vsp/ --recursive`).
3. If you used `--profile transfer` for short-lived creds, delete `~/.aws/credentials` on EC2.
4. Tag the build in git: `git tag -a "client-build-${BUILD_ID#client-build-}" -m "Shipped to <client>"`.

## Code-only patches (no full rebuild)

For small `lib/` fixes, see [code-only-update.md](code-only-update.md). The artifact is a few-MB layered image, not another 40 GB transfer.
