FROM nvidia/cuda:12.8.0-base-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

# --- System deps ---
# build-essential needed for packages that build from source (e.g., editdistance in your vsp env)
RUN apt-get update && apt-get install -y \
    python3 python3-venv python3-pip python3-dev \
    git ffmpeg \
    build-essential pkg-config \
    libglib2.0-0 libsm6 libxext6 libxrender1 \
    libsndfile1 libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# Copy your standalone bundle (code + configs + models, but not venvs/mp4)
COPY galaxy_export/ ./

# ---------- CREATE TWO VIRTUAL ENVS ----------
RUN python3 -m venv /workspace/auto_avsr/pre-process-venv && \
    python3 -m venv /workspace/vsp-llm-yoad-venv

######################################################################
# pre-process-venv  (EXACTLY as your freeze)
######################################################################

# Pin pip to a known stable version (optional, but makes builds reproducible)
# (Your pre-process list doesn't depend on omegaconf metadata, but pinning helps determinism.)
RUN /workspace/auto_avsr/pre-process-venv/bin/python -m pip install -U "pip==24.0" "setuptools==70.0.0" "wheel==0.43.0"

# Install EXACT torch stack for this env (cu128) + EXACT nvidia runtime pkgs + triton==3.4.0
# Use cu128 index because your EC2 env was torch/vision/audio +cu128.
RUN /workspace/auto_avsr/pre-process-venv/bin/pip install \
  --index-url https://download.pytorch.org/whl/cu128 \
  torch==2.8.0+cu128 \
  torchvision==0.23.0+cu128 \
  torchaudio==2.8.0+cu128 \
  triton==3.4.0 \
  nvidia-cublas-cu12==12.8.4.1 \
  nvidia-cuda-cupti-cu12==12.8.90 \
  nvidia-cuda-nvrtc-cu12==12.8.93 \
  nvidia-cuda-runtime-cu12==12.8.90 \
  nvidia-cudnn-cu12==9.10.2.21 \
  nvidia-cufft-cu12==11.3.3.83 \
  nvidia-cufile-cu12==1.13.1.3 \
  nvidia-curand-cu12==10.3.9.90 \
  nvidia-cusolver-cu12==11.7.3.90 \
  nvidia-cusparse-cu12==12.5.8.93 \
  nvidia-cusparselt-cu12==0.7.1 \
  nvidia-nccl-cu12==2.27.3 \
  nvidia-nvjitlink-cu12==12.8.93 \
  nvidia-nvtx-cu12==12.8.90

# Then install the rest of your exact pre-process-venv packages.
# Note: openai-whisper pinned to exact git commit as in your freeze.
RUN /workspace/auto_avsr/pre-process-venv/bin/pip install \
  absl-py==2.3.1 \
  aiohappyeyeballs==2.6.1 \
  aiohttp==3.13.2 \
  aiosignal==1.4.0 \
  async-timeout==5.0.1 \
  attrs==25.4.0 \
  av==15.1.0 \
  certifi==2025.11.12 \
  cffi==2.0.0 \
  charset-normalizer==3.4.4 \
  contourpy==1.3.0 \
  cycler==0.12.1 \
  Cython==3.2.1 \
  ffmpeg-python==0.2.0 \
  filelock==3.19.1 \
  flatbuffers==25.9.23 \
  fonttools==4.60.1 \
  frozenlist==1.8.0 \
  fsspec==2025.10.0 \
  future==1.0.0 \
  idna==3.11 \
  ImageIO==2.37.2 \
  importlib_metadata==8.7.0 \
  importlib_resources==6.5.2 \
  jax==0.4.30 \
  jaxlib==0.4.30 \
  Jinja2==3.1.6 \
  joblib==1.5.2 \
  kiwisolver==1.4.7 \
  lazy_loader==0.4 \
  lightning-utilities==0.15.2 \
  llvmlite==0.43.0 \
  MarkupSafe==3.0.3 \
  matplotlib==3.9.4 \
  mediapipe==0.10.21 \
  ml_dtypes==0.5.3 \
  more-itertools==10.8.0 \
  mpmath==1.3.0 \
  multidict==6.7.0 \
  networkx==3.2.1 \
  numba==0.60.0 \
  numpy==1.26.4 \
  "openai-whisper @ git+https://github.com/openai/whisper@c0d2f624c09dc18e709e37c2ad90c039a4eb72a2" \
  opencv-contrib-python==4.11.0.86 \
  opencv-python==4.11.0.86 \
  opt_einsum==3.4.0 \
  packaging==25.0 \
  pandas==2.3.3 \
  pillow==11.3.0 \
  propcache==0.4.1 \
  protobuf==4.25.8 \
  pycparser==2.23 \
  pydub==0.25.1 \
  pyparsing==3.2.5 \
  python-dateutil==2.9.0.post0 \
  pytorch-lightning==2.5.5 \
  pytz==2025.2 \
  PyYAML==6.0.3 \
  regex==2025.11.3 \
  requests==2.32.5 \
  scikit-image==0.24.0 \
  scikit-learn==1.6.1 \
  scipy==1.13.1 \
  sentencepiece==0.2.1 \
  six==1.17.0 \
  sounddevice==0.5.3 \
  sympy==1.14.0 \
  threadpoolctl==3.6.0 \
  tifffile==2024.8.30 \
  tiktoken==0.12.0 \
  torchmetrics==1.8.2 \
  tqdm==4.67.1 \
  typing_extensions==4.15.0 \
  tzdata==2025.2 \
  uncertainty-toolbox==0.1.1 \
  urllib3==2.5.0 \
  xgboost==2.1.4 \
  yarl==1.22.0 \
  zipp==3.23.0


######################################################################
# vsp-llm-yoad-venv  (EXACTLY as your freeze, incl. old pip for omegaconf)
######################################################################

# This is the “old pip” you asked for to allow omegaconf==2.0.6 metadata.
RUN /workspace/vsp-llm-yoad-venv/bin/python -m pip install -U "pip==24.0" "setuptools==70.0.0" "wheel==0.43.0"

# Install torch stack for this env as in your freeze:
# torch==2.5.1 + triton==3.1.0 + the nvidia 12.4.* runtime pins.
# These correspond to cu124 wheels, so use the cu124 index to actually match your pinned nvidia-* versions.
RUN /workspace/vsp-llm-yoad-venv/bin/pip install \
  --index-url https://download.pytorch.org/whl/cu124 \
  torch==2.5.1+cu124 \
  triton==3.1.0 \
  nvidia-cublas-cu12==12.4.5.8 \
  nvidia-cuda-cupti-cu12==12.4.127 \
  nvidia-cuda-nvrtc-cu12==12.4.127 \
  nvidia-cuda-runtime-cu12==12.4.127 \
  nvidia-cudnn-cu12==9.1.0.70 \
  nvidia-cufft-cu12==11.2.1.3 \
  nvidia-curand-cu12==10.3.5.147 \
  nvidia-cusolver-cu12==11.6.1.9 \
  nvidia-cusparse-cu12==12.3.1.170 \
  nvidia-nccl-cu12==2.21.5 \
  nvidia-nvjitlink-cu12==12.4.127 \
  nvidia-nvtx-cu12==12.4.127

# Install the rest of vsp-llm env exactly (including your editable fairseq from that repo+hash)
RUN /workspace/vsp-llm-yoad-venv/bin/pip install \
  accelerate==0.33.0 \
  aiohappyeyeballs==2.6.1 \
  aiohttp==3.13.2 \
  aiosignal==1.4.0 \
  antlr4-python3-runtime==4.8 \
  async-timeout==5.0.1 \
  attrs==25.4.0 \
  audioread==3.1.0 \
  beautifulsoup4==4.14.2 \
  bitsandbytes==0.48.2 \
  certifi==2025.10.5 \
  cffi==2.0.0 \
  charset-normalizer==3.4.4 \
  colorama==0.4.6 \
  Cython==3.0.8 \
  datasets==2.17.0 \
  decorator==5.2.1 \
  dill==0.3.8 \
  editdistance==0.6.0 \
  einops==0.7.0 \
  filelock==3.19.1 \
  frozenlist==1.8.0 \
  fsspec==2023.10.0 \
  gdown==5.2.0 \
  hf-xet==1.2.0 \
  huggingface-hub==0.36.0 \
  hydra-core==1.0.7 \
  idna==3.11 \
  importlib-metadata==7.0.1 \
  inquirerpy==0.3.4 \
  Jinja2==3.1.6 \
  joblib==1.3.2 \
  lazy_loader==0.4 \
  librosa==0.10.1 \
  llvmlite==0.42.0 \
  lxml==6.0.2 \
  MarkupSafe==3.0.3 \
  mpmath==1.3.0 \
  msgpack==1.1.2 \
  multidict==6.0.5 \
  multiprocess==0.70.16 \
  networkx==3.2.1 \
  npy-append-array==0.9.16 \
  numba==0.59.0 \
  numpy==1.23.5 \
  oauthlib==3.2.2 \
  omegaconf==2.0.6 \
  opencv-python==4.5.4.60 \
  packaging==23.2 \
  pandas==2.2.0 \
  peft==0.17.1 \
  pfzy==0.3.4 \
  platformdirs==4.4.0 \
  pooch==1.8.2 \
  portalocker==3.2.0 \
  prompt_toolkit==3.0.52 \
  propcache==0.4.1 \
  psutil==5.9.8 \
  pyarrow==21.0.0 \
  pyarrow-hotfix==0.7 \
  pycparser==2.23 \
  PySocks==1.7.1 \
  python-dateutil==2.8.2 \
  python_speech_features==0.6 \
  pytz==2025.2 \
  PyYAML==6.0.3 \
  regex==2025.11.3 \
  requests==2.32.5 \
  sacrebleu==2.4.0 \
  safetensors==0.4.2 \
  scikit-learn==1.4.0 \
  scipy==1.10.0 \
  sentencepiece==0.1.96 \
  six==1.17.0 \
  soundfile==0.13.1 \
  soupsieve==2.8 \
  soxr==1.0.0 \
  sympy==1.13.1 \
  tabulate==0.9.0 \
  threadpoolctl==3.6.0 \
  tokenizers==0.21.4 \
  tqdm==4.67.1 \
  transformers==4.49.0 \
  typing_extensions==4.9.0 \
  tzdata==2025.2 \
  urllib3==2.5.0 \
  wcwidth==0.2.14 \
  xxhash==3.6.0 \
  yarl==1.22.0 \
  zipp==3.23.0

# Editable fairseq exactly as in your freeze
RUN /workspace/vsp-llm-yoad-venv/bin/pip install -e \
  "git+https://github.com/Sally-SH/VSP-LLM.git@91c4f3d4418ac9cd0f6328f043de5e48e1d091b2#egg=fairseq&subdirectory=fairseq"

ENTRYPOINT ["/bin/bash"]