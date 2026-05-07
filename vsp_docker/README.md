# vsp_docker — Air-gapped VSP Pipeline Deployment

This directory builds and packages the VSP visual-speech pipeline as a single Docker image plus an offline install kit for client deployment on an air-gapped (no-internet) machine with an NVIDIA GPU.

## Layout

```
vsp_docker/
├── Dockerfile             — defines the air-gapped image (CUDA 12.8 base + 2 venvs + prebakes)
├── .dockerignore          — excludes venvs and the regen backup; keeps samples/*.mp4 in context
├── container_payload_20260507/         — self-contained build context (43 GB, mostly weights)
│   ├── lib/               — pipeline modules (regenerated from /home/ubuntu/lib/ — not edited here)
│   ├── run_flat_english_pipeline.sh
│   ├── auto_avsr/, VSP-LLM/, av_hubert/   — source repos + checkpoints + Llama-2-7b-hf
│   ├── face_alignment/, face_detection/   — preprocessing detectors
│   ├── golden_weights/    — k-means baseline reference
│   ├── whisper_cache/     — Whisper medium.en (1.5 GB)
│   ├── is_model_cache/    — sentence-transformers MiniLM-L6-v2 (88 MB)
│   ├── is_wheels/         — sentence-transformers + Metaphone + doublemetaphone wheels
│   ├── spacy_wheels/      — spaCy + en_core_web_sm wheels
│   └── samples/           — curated smoke-test fixtures (smoke_12s.mp4, smoke_75s.mp4)
├── checks/                — host verification scripts
│   ├── pre_install_check.sh    — driver, GPU, RAM, disk, Docker, NVIDIA toolkit
│   ├── post_install_check.sh   — feature-parity gate after docker load
│   └── collect_diagnostics.sh  — bundle host state + logs for support
├── launcher/              — desktop launcher + tag-driven update flow
│   ├── vsp-pipeline.sh         — Linux launcher (zenity folder picker, terminal auto-detect)
│   ├── VSP-Pipeline.desktop    — XDG entry pointing at /opt/vsp/launcher/
│   ├── image.tag               — single source of truth for which image tag to invoke
│   ├── install_launcher.sh     — places launcher under /opt/vsp/launcher/ + desktop shortcut
│   ├── apply_update.sh         — atomic code-only update flow (load → smoke → flip tag)
│   └── rollback.sh             — flip back to image.tag.previous
├── samples/               — smoke-test fixtures (also live inside container_payload_20260507/samples/)
├── CLIENT_INSTALL.md      — operator-facing install guide (ships with the kit)
└── client-troubleshooting.md  — symptom -> fix table (ships with the kit)
```

## Build

```bash
cd /home/ubuntu/vsp_docker
BUILD_ID="client-build-001"
docker build -t "vsp-llm-pipeline:${BUILD_ID}" -f Dockerfile . 2>&1 | tee /tmp/vsp_build_${BUILD_ID}.log
```

Takes 30-60 min on c5.4xlarge-class hardware. See [docs/guides/build-and-transfer.md](/home/ubuntu/docs/guides/build-and-transfer.md).

## Save + transfer

```bash
docker save "vsp-llm-pipeline:${BUILD_ID}" | zstd -19 -T0 > "vsp-image-${BUILD_ID}.tar.zst"
sha256sum "vsp-image-${BUILD_ID}.tar.zst" > "vsp-image-${BUILD_ID}.tar.zst.sha256"
split -b 4G "vsp-image-${BUILD_ID}.tar.zst" "vsp-image-${BUILD_ID}.tar.zst.part_"
```

EC2 has no public IP — exfil via S3 + presigned URLs. See `docs/guides/build-and-transfer.md` § "Transfer off EC2".

## Stage / dry-run on your own offline box

Before shipping to the client, walk the install on a machine you control with networking off. See `docs/guides/staging-dry-run.md`.

## Ship to client

USB SSD with:
- `vsp-image-<build-id>.tar.zst` (+ .sha256, + parts if split)
- `checks/`, `launcher/`, `samples/`, `offline_kit_<distro>/`
- `CLIENT_INSTALL.md`, `client-troubleshooting.md`

The operator runs `pre_install_check.sh` → `docker load` → `install_launcher.sh` → `post_install_check.sh`. Total wall time ~30-45 min.

## Updates after shipping

Code-only patches ship as a thin layered image (a few MB). See `docs/guides/code-only-update.md`.

## Documentation map

| Doc | Audience | Purpose |
|---|---|---|
| [CLIENT_INSTALL.md](CLIENT_INSTALL.md) | Client operator | One-stop install guide |
| [client-troubleshooting.md](client-troubleshooting.md) | Client operator | Symptom -> fix table |
| [/home/ubuntu/docs/guides/build-and-transfer.md](/home/ubuntu/docs/guides/build-and-transfer.md) | Yoad (internal) | EC2 build + S3 exfil path |
| [/home/ubuntu/docs/guides/staging-dry-run.md](/home/ubuntu/docs/guides/staging-dry-run.md) | Yoad (internal) | Layer-2 verification procedure |
| [/home/ubuntu/docs/guides/code-only-update.md](/home/ubuntu/docs/guides/code-only-update.md) | Yoad (internal) | Patch flow without 40 GB re-transfer |
| [samples/README.md](samples/README.md) | Yoad (internal) | Test fixture design intent |
