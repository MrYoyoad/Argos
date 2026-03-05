# Development Guide

> Split from CLAUDE.md for easier navigation. See also:
> - [CLAUDE.md](../CLAUDE.md) — Project overview and rules
> - [Architecture](architecture.md) — Pipeline architecture and data flow
> - [Container Sync Changelog](container-sync-changelog.md) — EC2→Container change log

## Main Pipeline Commands

### Running the Complete Pipeline

```bash
./run_flat_english_pipeline.sh /path/to/raw_videos_dir
```

This executes all stages:
1. ASR transcription (Whisper) to generate .wrd files
2. Video preprocessing and mouth cropping (mediapipe detector, 4-second segments)
3. Manifest and TSV generation
4. K-means clustering (200 clusters) on AV-HuBERT features
5. VSP-LLM decoding for final transcription
6. Client output generation (reports and burned videos; EC2 also computes Intelligibility Scores)

**Important**: Previous run outputs are automatically archived to `~/flat_runs_archive/[timestamp]/` before each pipeline run.

### Individual Component Commands

#### Auto-AVSR Training
```bash
# Activate preprocessing environment
source ~/auto_avsr/pre-process-venv/bin/activate

# Train a model
python ~/auto_avsr/train.py \
  --exp-dir=./exp \
  --exp-name=my_experiment \
  --modality=video \
  --root-dir=/path/to/preprocessed/data \
  --train-file=train_labels.csv \
  --num-nodes=1
```

#### Auto-AVSR Evaluation
```bash
python ~/auto_avsr/eval.py \
  --modality=video \
  --root-dir=/path/to/preprocessed/data \
  --test-file=test_labels.csv \
  --pretrained-model-path=./exp/my_experiment/model_avg_10.pth
```

#### VSP-LLM Training
```bash
cd ~/VSP-LLM
source ~/vsp-llm-yoad-venv/bin/activate

# Edit scripts/train.sh to set DATA_PATH and OUT_PATH
bash scripts/train.sh
```

#### VSP-LLM Decoding
```bash
cd ~/VSP-LLM
source ~/vsp-llm-yoad-venv/bin/activate

# Edit scripts/decode.sh to set LANG, MODEL_PATH, OUT_PATH
bash scripts/decode.sh
```

#### Preprocessing Videos
```bash
source ~/auto_avsr/pre-process-venv/bin/activate
cd ~/auto_avsr/preparation

python preprocess_lrs2lrs3.py \
  --data-dir /path/to/raw/data \
  --root-dir /path/to/output \
  --dataset flat \
  --detector mediapipe \
  --gpu_type cuda \
  --subset train \
  --seg-duration 4 \
  --groups 1 \
  --job-index 0
```

## Virtual Environments

The codebase uses three separate Python virtual environments:

- **~/auto_avsr/pre-process-venv** - For ASR and preprocessing (Whisper, mediapipe, opencv)
- **~/vsp-llm-yoad-venv** - For VSP-LLM training/inference (PyTorch, transformers, fairseq)
- **~/project/ron/.venv** - For miscellaneous tools (if used)

Always activate the appropriate environment before running commands from that component.

## Testing

There are no automated test suites in this codebase. Testing is done by:

1. Running the full pipeline on sample videos
2. Inspecting decode outputs (JSON hypo files)
3. Checking WER (Word Error Rate) on evaluation sets

To test pipeline stages individually:
```bash
# Test ASR only
source ~/auto_avsr/pre-process-venv/bin/activate
python ~/auto_avsr/asr_to_words_notime.py \
  --in_videos /path/to/test/videos \
  --out_wrd /tmp/test_wrd \
  --model medium --lang en

# Test preprocessing on single video
cd ~/auto_avsr/preparation
python preprocess_lrs2lrs3.py \
  --data-dir /path/to/single/video \
  --root-dir /tmp/test_preprocess \
  --dataset flat --detector mediapipe \
  --subset train --seg-duration 4

# Test decode on small manifest
cd ~/VSP-LLM
bash scripts/decode.sh  # (after editing paths to small test set)
```

## Common Development Workflows

### Adding Support for New Languages

1. Train new SentencePiece model in `auto_avsr/spm/`
2. Update paths in `auto_avsr/preparation/transforms.py` and `auto_avsr/datamodule/transforms.py`
3. Modify `run_flat_english_pipeline.sh` LANG variable
4. Adjust Whisper model and language parameters in ASR step

### Fine-tuning VSP-LLM on New Data

1. Prepare data following LRS3 format (use auto_avsr preprocessing)
2. Generate manifests (train.tsv, train.wrd)
3. Extract features and train k-means: `bash VSP-LLM/scripts/run_flat_kmeans.sh`
4. Generate cluster_counts: `bash VSP-LLM/scripts/run_cluster_counts.sh`
5. Edit `VSP-LLM/scripts/train.sh` with DATA_PATH
6. Run: `bash VSP-LLM/scripts/train.sh`

### Debugging Pipeline Failures

- Check logs in `~/flat_runs_latest.log` (created by pipeline)
- Archived logs available in `~/flat_runs_archive/[timestamp]/`
- For preprocessing errors: check `auto_avsr/preparation/preprocess_*.log`
- For decoding errors: check `VSP-LLM/decode/` for hypo JSON files

### Modifying Preprocessing Parameters

Key parameters in `preprocess_lrs2lrs3.py`:
- `--seg-duration`: Segment length (default 4 seconds)
- `--detector`: Face detector (mediapipe, retinaface)
- `--gpu_type`: cuda or cpu
- Output resolution: 88x88 mouth crops at 25fps (hardcoded in detectors)

### Changing K-means Clusters

Currently uses 200 clusters. To change:
1. Edit `run_flat_kmeans.sh` or `VSP-LLM/scripts/run_flat_kmeans.sh`
2. Change cluster count in `learn_kmeans.py` call (line 76)
3. Retrain k-means and regenerate all labels
4. Model configs in `VSP-LLM/src/conf/` may need adjustment

## Troubleshooting

### "FileNotFoundError" in preprocessing
- Ensure input directory structure matches expected format
- Check that video files have audio tracks (or use silent audio flag)
- Verify detector weights are available (mediapipe requires specific packages)

### "No mouth detected" errors
- Try different detector (mediapipe vs retinaface)
- Check video quality and face visibility
- Adjust detection thresholds in `preparation/detectors/`

### CUDA out of memory
- Reduce batch size in training configs
- Use gradient checkpointing (if available)
- Process videos in smaller batches during preprocessing

### Decode outputs empty or incorrect
- Verify all three files exist and align: train.tsv, train.wrd, train.cluster_counts
- Check symlinks in `VSP-LLM/src/dataset/vsr/en/`
- Ensure checkpoint paths are correct in decode.sh
- Verify PYTHONPATH includes fairseq

### K-means training takes too long
- Reduce PERCENT in run_flat_kmeans.sh (default 0.1 = 10%)
- Use fewer shards (NSHARD=1 for small datasets)
- Skip retraining if k-means model already exists (TRAIN_KMEANS=0)
