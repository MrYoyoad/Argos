# EC2 Setup From Scratch — VSP Lip-Reading Pipeline

Complete, copy-pasteable guide for provisioning a **fresh EC2 box** that can run the full
pipeline (`run_flat_english_pipeline.sh`) end-to-end. Written 2026-08-03 from a live audit
of the production dev box (g4dn.2xlarge, Ubuntu 22.04, driver 580.105.08).

**Who this is for:** anyone standing up a new EC2 dev/eval box. For the *client Docker
container*, see `vsp_docker/Dockerfile` and [deploy-targets.md](deploy-targets.md) instead.

Validation at the end: §7 gives a three-step test ladder that confirms the box works.

---

## §1 Instance & OS

| Item | Requirement | Notes |
|------|-------------|-------|
| Instance type | `g4dn.2xlarge` or better | 8 vCPU / 32 GB RAM / Tesla T4 is the proven baseline |
| GPU | NVIDIA, ≥16 GB VRAM | T4 is **sm_75** — fine for all pipeline work, but it **cannot validate Blackwell (sm_120) client paths**; Blackwell testing needs client hardware |
| Root volume | **≥1 TB gp3** | The current box sits at 91% of 969 GB. Models ~25 GB + Docker image rebuilds (~100 GB scratch) + run archives grow fast. Do not go smaller. |
| OS | Ubuntu 22.04 LTS | Everything below assumes 22.04 (Python 3.10 system default; we add 3.9 in §3) |
| NVIDIA driver | **≥570** (audit box: 580.105.08) | ≥570 also required for Blackwell client parity; use the `nvidia-driver-580-server` package or AWS Deep Learning base AMI |

```bash
# 1.1 Verify GPU + driver first — nothing else matters until this works
nvidia-smi
# Expect: driver version >= 570 and the GPU listed (e.g. Tesla T4)

# 1.2 System packages
sudo apt-get update
sudo apt-get install -y \
  ffmpeg zstd git git-lfs \
  build-essential pkg-config software-properties-common \
  libglib2.0-0 libsm6 libxext6 libxrender1 libsndfile1 libportaudio2 \
  bc jq unzip

# Audit-box versions for reference: ffmpeg 4.4.2 (Ubuntu stock — fine), zstd 1.4.8,
# git-lfs 3.0.2. Stock apt versions are all sufficient.

# 1.3 s5cmd (S3 transfers; task-critical for model/data pulls — see §5)
curl -L https://github.com/peak/s5cmd/releases/download/v2.3.0/s5cmd_2.3.0_Linux-64bit.tar.gz \
  | sudo tar xz -C /usr/local/bin s5cmd
s5cmd version   # expect v2.3.0

# 1.4 AWS access: attach the instance IAM role with S3 read access
# (account 733430125971). NO aws configure, NO FUSE mounts — the role is the auth.
aws sts get-caller-identity
```

---

## §2 Repo clone

The main repo is `github.com/MrYoyoad/Argos` with three submodules
(from `.gitmodules`):

| Submodule | URL |
|-----------|-----|
| `VSP-LLM` | https://github.com/MrYoyoad/VSP-LLM.git |
| `auto_avsr` | https://github.com/MrYoyoad/auto_avsr.git |
| `av_hubert` | https://github.com/facebookresearch/av_hubert.git |

`MrYoyoad/*` repos are **private** — you need GitHub auth (a PAT with `repo` scope, or SSH
keys) before cloning. `facebookresearch/av_hubert` is public.

```bash
# 2.1 GitHub auth (HTTPS + PAT shown; SSH works too)
git config --global credential.helper store
# First clone will prompt: username = your GitHub user, password = the PAT

# 2.2 Clone into /home/ubuntu — the pipeline HARD-ASSUMES this path.
# lib/config.sh detects EC2 and sets BASE_PATH=/home/ubuntu; run as user `ubuntu`.
cd /home/ubuntu
git clone https://github.com/MrYoyoad/Argos.git argos_tmp
# The repo IS the home directory layout — move contents up:
shopt -s dotglob && mv argos_tmp/* /home/ubuntu/ && rmdir argos_tmp && shopt -u dotglob

# 2.3 Submodules
cd /home/ubuntu
git submodule update --init VSP-LLM auto_avsr av_hubert
# Audit-box pinned commits (for verification):
#   VSP-LLM   bdc61b351269b5c18542cc5d2594e6cdb83aec1c
#   auto_avsr 5b2502f461e569cfd935828683a6104e38e2bce6
#   av_hubert 258fb50e155134eec2c4b49c2ae8de267075fd18
# Do NOT recursively init av_hubert's own submodules — av_hubert/fairseq stays an
# EMPTY directory on the working box. The only fairseq that matters is VSP-LLM/fairseq
# (authoritative for decode; installed editable in §4.3).

# 2.4 Bootstrap the input dir (pipeline + UI expect it)
mkdir -p /home/ubuntu/vsp_input
```

**Not in git — copied separately (§5):** model checkpoints, whisper caches,
`golden_weights/`, `~/.insightface/`, and the two vendored ibug checkouts
`face_alignment/` + `face_detection/` (see §5 table).

---

## §3 Python 3.9 via deadsnakes

Ubuntu 22.04 ships Python 3.10, but **both venvs are Python 3.9.23** and several pinned
wheels are cp39-only. Install 3.9 from deadsnakes (exact steps, same as
`vsp_docker/Dockerfile`):

```bash
sudo apt-get update && sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update && sudo apt-get install -y \
  python3.9 python3.9-venv python3.9-dev python3.9-distutils
python3.9 -V   # expect Python 3.9.x (audit box: 3.9.23)
```

---

## §4 Build the two virtual environments

Two venvs run the pipeline (defined in `lib/config.sh`):

| Venv | Path | Role | Stages |
|------|------|------|--------|
| ASR venv (`ASR_VENV` = `PREP_VENV`) | `/home/ubuntu/auto_avsr/pre-process-venv` | segmentation, normalization helpers, mediapipe mouth-crop, Whisper ASR | 0.1–3 |
| VSP venv (`VSP_VENV`) | `/home/ubuntu/vsp-llm-yoad-venv` | manifests, k-means, fairseq decode, reports/IS | 5–8 |

> `vsp-ui/` needs **no venv and no third-party packages** — the UI server
> (`vsp-ui/app/server.py`) is pure Python standard library (`http.server`); it can run under
> system `python3`. (Older notes mentioning flask/opencv for the UI are wrong — verified
> against every import in `vsp-ui/app/**/*.py`, 2026-08-03.)

Use the real per-venv freezes generated 2026-08-03 from the live box:
`/home/ubuntu/requirements-asr.txt` and `/home/ubuntu/requirements-vsp.txt`.
(The root `requirements.txt` is a stale Sep-2025 freeze that matches **neither** venv —
do not use it.)

### 4.1 Create the venvs (directly from python3.9 — see trap §8.5)

```bash
python3.9 -m venv /home/ubuntu/auto_avsr/pre-process-venv
python3.9 -m venv /home/ubuntu/vsp-llm-yoad-venv
/home/ubuntu/auto_avsr/pre-process-venv/bin/pip install -U "pip==24.0" "setuptools==70.0.0" "wheel==0.43.0"
/home/ubuntu/vsp-llm-yoad-venv/bin/pip install -U "pip==24.0" "setuptools==70.0.0" "wheel==0.43.0"
```

### 4.2 ASR venv (torch 2.8.0 + cu128)

```bash
# Torch trio first, from the cu128 index (exact pins from vsp_docker/Dockerfile):
/home/ubuntu/auto_avsr/pre-process-venv/bin/pip install \
  --index-url https://download.pytorch.org/whl/cu128 \
  torch==2.8.0+cu128 torchvision==0.23.0+cu128 torchaudio==2.8.0+cu128

# Then everything else (already-satisfied torch pins are skipped):
/home/ubuntu/auto_avsr/pre-process-venv/bin/pip install -r /home/ubuntu/requirements-asr.txt
```

Key pins you should see afterwards: `openai-whisper` (git pin 20250625), `mediapipe 0.10.21`,
`pytorch-lightning 2.5.5`, **`numpy 1.26.4`**, `insightface 1.0.1`, `opencv-python 4.11`.

### 4.3 VSP venv (torch 2.5.1 + cu124, editable fairseq)

```bash
# Torch first. PyPI's torch==2.5.1 wheel IS the cu124 build; the explicit index is the
# belt-and-suspenders version (matches the Dockerfile):
/home/ubuntu/vsp-llm-yoad-venv/bin/pip install \
  --index-url https://download.pytorch.org/whl/cu124 torch==2.5.1+cu124

# Bulk install — MUST be --no-deps (freeze-restore mode; fairseq -e line is
# commented out in this file on purpose). Without --no-deps pip's resolver
# REFUSES this freeze (ResolutionImpossible): the venv carries a legacy
# requests==2.28.2 (openxlab constraint) while markdown_pdf 1.13.1 declares
# requests>=2.32.5. The live venv works because it grew incrementally; a fresh
# resolve of the full set fails. The freeze is complete, so --no-deps is safe.
# (Verified live 2026-08-03: plain -r fails, --no-deps -r succeeds, all pins land.)
/home/ubuntu/vsp-llm-yoad-venv/bin/pip install --no-deps -r /home/ubuntu/requirements-vsp.txt

# fairseq — editable, from the LOCAL checkout (NOT from PyPI, NOT re-cloned):
/home/ubuntu/vsp-llm-yoad-venv/bin/pip install -e /home/ubuntu/VSP-LLM/fairseq

# spaCy English model: installed BY the freeze (direct wheel URL line, works under
# --no-deps — verified 2026-08-03: en_core_web_sm 3.8.0 loads). Fallback if missing:
/home/ubuntu/vsp-llm-yoad-venv/bin/python -c 'import en_core_web_sm' 2>/dev/null || \
  /home/ubuntu/vsp-llm-yoad-venv/bin/python -m spacy download en_core_web_sm
```

Key pins afterwards: `transformers 4.49.0`, `hydra-core 1.0.7`, `omegaconf 2.0.6`,
**`numpy 1.23.5`** (never upgrade — §8.2), `spacy 3.8.11` + `en_core_web_sm 3.8.0`,
`sentence-transformers 5.1.2`, `sentencepiece 0.1.96`, `peft`, `bitsandbytes`.

**Cython extensions:** fairseq's compiled extensions (`fairseq.data.data_utils_fast`) are
NOT built by `pip install -e` on every platform. `lib/decode.sh` checks for them at the
start of every decode and builds them in-place if missing (one-time). **That check must
never be removed.** To pre-build now instead of on first decode:

```bash
cd /home/ubuntu/VSP-LLM/fairseq && /home/ubuntu/vsp-llm-yoad-venv/bin/python setup.py build_ext --inplace
```

---

## §5 Models & assets (~25 GB + Llama 26 GB)

None of these are in git. Sources: **HF** = Hugging Face (needs token for gated repos),
**S3** = `s3://conversation-datasets-733430125971/` via s5cmd (instance role auth),
**old box** = copy from an existing box / attached drive (fastest; everything below exists
on the current box at the listed destination path).

```bash
# HF token first (needed for gated Llama-2). Get a token with access to
# meta-llama/Llama-2-7b-hf approved, then:
/home/ubuntu/vsp-llm-yoad-venv/bin/pip show huggingface_hub >/dev/null && \
  /home/ubuntu/vsp-llm-yoad-venv/bin/huggingface-cli login   # writes ~/.cache/huggingface/token
```

| # | Asset | Size | Destination (exact) | Source / how |
|---|-------|------|---------------------|--------------|
| 1 | `checkpoint_finetune.pt` — **THE decode model** (VSP-LLM finetuned) | 4.1 GB | `/home/ubuntu/VSP-LLM/checkpoints/checkpoint_finetune.pt` | old box / S3. Not publicly downloadable. |
| 2 | `checkpoint_freeze.pt` (VSP-LLM frozen-LLM variant) | 4.1 GB | `/home/ubuntu/VSP-LLM/checkpoints/checkpoint_freeze.pt` | old box / S3 |
| 3 | `large_vox_iter5.pt` (AV-HuBERT large, feature extractor) | 3.9 GB | `/home/ubuntu/VSP-LLM/checkpoints/large_vox_iter5.pt` | old box / S3, or public AV-HuBERT release (facebookresearch) |
| 4 | Llama-2-7b-hf (gated) | 26 GB | `/home/ubuntu/VSP-LLM/checkpoints/Llama-2-7b-hf/` (full model) + config-only copy at `/home/ubuntu/Llama-2-7b-hf/` | HF: `huggingface-cli download meta-llama/Llama-2-7b-hf --local-dir /home/ubuntu/VSP-LLM/checkpoints/Llama-2-7b-hf` (requires approved access + token), or old box |
| 5 | `all-MiniLM-L6-v2` (sentence-transformers, IS scoring) | ~90 MB | `~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/` | auto-downloads on first IS run if online; pre-seed from old box for offline |
| 6 | Whisper `medium.pt` — **what the pipeline uses** (`lib/asr.sh` runs `--model medium`) | 1.5 GB | `/home/ubuntu/.cache/whisper/medium.pt` | auto-downloads on first ASR run, or old box / `vsp_docker/container_payload_20260507/whisper/medium.pt` |
| 7 | Whisper `large-v3.pt` (research/eval use) | 3.1 GB | `/home/ubuntu/.cache/whisper/large-v3.pt` | auto-downloads when requested, or old box |
| 8 | insightface `buffalo_l` (5 .onnx files) | ~330 MB | `/home/ubuntu/.insightface/models/buffalo_l/` | auto-downloads when online on first use; **must pre-seed from old box for offline/air-gapped** |
| 9 | `golden_weights/baseline_20260218/` — golden k-means (`flat_kmeans_200.bin`, cluster counts, decode params) | ~1.5 MB | `/home/ubuntu/golden_weights/baseline_20260218/` | old box / S3 — irreplaceable, back it up |
| 10 | `face_alignment/` — vendored ibug git checkout (**NOT a pip package**) | ~400 MB | `/home/ubuntu/face_alignment/` | old box, or `git clone https://github.com/hhj1897/face_alignment` (+ its weights) |
| 11 | `face_detection/` — vendored ibug git checkout (**NOT a pip package**) | ~2 MB | `/home/ubuntu/face_detection/` | old box, or `git clone https://github.com/hhj1897/face_detection`. Note: on the current box `Resnet50_Final.pth` is a **broken git-lfs pointer** (134 B) — harmless, the pipeline runs `--detector mediapipe`; only the mobilenet weight (1.8 MB) is real. Use `git lfs pull` if you ever need the retinaface/resnet path. |
| 12 | `~/vsp_input/` | — | `/home/ubuntu/vsp_input/` | `mkdir -p` (done in §2.4); drop input videos here |

S3 pull pattern (byte-exact for non-Latin keys):

```bash
export LC_ALL=C.UTF-8
s5cmd --numworkers 32 sync 's3://conversation-datasets-733430125971/<prefix>/*' /home/ubuntu/<dest>/
```

---

## §6 Data

Datasets (evaluation videos, AVSpeech, baseline results) are covered in
[teammate-briefing-aug2026.md §2](teammate-briefing-aug2026.md) (written in parallel with
this guide) — follow its S3 sync commands after §5 completes.

---

## §7 Validation ladder

Run in order; each step is a superset of the previous.

```bash
# 7.1 Environment readiness (~1 min, no GPU work beyond torch.cuda probe)
bash /home/ubuntu/scripts/tests/test_env_readiness.sh

# 7.2 Module test suite (37 tests, fast)
bash /home/ubuntu/lib/test_all_modules.sh

# 7.3 End-to-end smoke decode (5–10 min on GPU; archives current outputs/ — read its
#     warning banner; deliberately requires an explicit opt-in env var)
ALLOW_PIPELINE_RUN=1 bash /home/ubuntu/scripts/tests/test_ec2_smoke_decode.sh
```

A fresh box is "done" when 7.3 passes: the report CSV exists with a non-empty hypothesis.

---

## §8 Known traps

1. **Cython extension check in `lib/decode.sh` must never be removed.** It imports
   `fairseq.data.data_utils_fast` and builds in-place when missing. Fresh boxes/containers
   hit this on first decode; without it decode fails with an ImportError deep in fairseq.

2. **numpy is intentionally DIFFERENT per venv and must stay that way.**
   VSP venv: `1.23.5` — fairseq 1.0.0a0 uses `np.float`/`np.int` aliases removed in
   numpy 1.24 (see `VSP-LLM/fairseq/fairseq/data/indexed_dataset.py`), and the compiled
   Cython extensions are built against the 1.23 ABI. ASR venv: `1.26.4` (torch 2.8 stack).
   A stray `pip install -U numpy` in the VSP venv breaks decode.

3. **HF token gating.** `meta-llama/Llama-2-7b-hf` is gated: request access on HF first,
   then `huggingface-cli login` (token lands at `~/.cache/huggingface/token`). Without it,
   step 4 of §5 404s. The token file check in `test_env_readiness.sh` is warn-only.

4. **Transcription manager singleton.** The UI's `TranscriptionManager` persists JSON under
   `~/vsp_input/.transcriptions/` and reloads metadata on every method call; out-of-band
   writes (e.g. `lib/asr.sh` auto entries) are only safe because of that reload pattern.
   Don't "optimize" it into a load-once singleton — that historically wiped auto entries.

5. **Venv seed `pyvenv.cfg` home paths.** On the old box, the ASR venv's `pyvenv.cfg` says
   `home = /home/ubuntu/venv/bin` (a venv that no longer exists) and the VSP venv was
   seeded FROM the ASR venv (`home = /home/ubuntu/auto_avsr/pre-process-venv/bin`). They
   only work because `bin/python3` symlinks resolve to `/usr/bin/python3.9`. On a fresh box
   create both venvs directly with `python3.9 -m venv` (§4.1) so `home` points at
   `/usr/bin` — do NOT copy venv directories between boxes.

6. **Disk headroom.** Docker image rebuilds need ~100 GB scratch; run archives
   (`~/flat_runs_archive/`) grow every pipeline run (each run archives the previous run's
   outputs). Prune old archives before rebuilds; provision ≥1 TB (§1).

7. **Old `requirements.txt` at repo root is stale** (Sep-2025 freeze, matches neither
   venv). Superseded by `requirements-asr.txt` / `requirements-vsp.txt` (2026-08-03).

8. **`av_hubert/fairseq` is an empty submodule dir on the working box** — leave it empty.
   Only `VSP-LLM/fairseq` is installed and authoritative for decode.

9. **`pip install -r requirements-vsp.txt` without `--no-deps` fails** with
   ResolutionImpossible (`requests==2.28.2` vs `markdown_pdf`'s `requests>=2.32.5`
   metadata). The live venv predates that constraint; a fresh resolve of the full set
   refuses it. Always `--no-deps` for the VSP freeze (§4.3). The ASR freeze resolves
   fine either way.

10. **Never `pip install -e VSP-LLM/fairseq` from a SECOND venv on a box whose
    production venv shares the same checkout.** The isolated build re-cythonizes the
    sources with whatever Cython the build env grabs, overwriting the in-place `.so` +
    `.cpp` + `version.py` that the production venv loads — observed to half-break
    production imports (2026-08-03). Recovery: `git checkout -- <cpp/version.py>` then
    rebuild with the production venv: `cd VSP-LLM/fairseq && <prod-venv>/bin/python
    setup.py build_ext --inplace`. On a genuinely fresh box (one venv) this is a
    non-issue.
