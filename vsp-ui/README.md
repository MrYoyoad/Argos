# VSP Pipeline UI

A web-based user interface for the Visual Speech Processing pipeline. Provides a simple, user-friendly way to process videos through ASR transcription, mouth cropping, feature extraction, clustering, and LLM-based decoding.

## Features

- **Desktop Integration**: Launch via desktop icon
- **Video Validation**: Pre-flight checks for video format, duration, and k-means viability
- **Progress Tracking**: Real-time progress bar across all 9 pipeline stages
- **Error Handling**: Robust timeout and error recovery with detailed logs
- **No Dependencies**: Uses only Python standard library (no pip install needed)

## Quick Start

### 1. Launch the UI

Double-click the desktop icon or run:

```bash
cd /home/ubuntu/vsp-ui
./launcher.sh
```

This will:
- Start the web server on `http://localhost:8765`
- Open your browser
- Open the input folder (`~/vsp_input/`)

### 2. Add Videos

Drag your `.mp4` video files into the input folder that opened.

### 3. Process

1. In the browser, click **"Scan Videos"**
2. Review validation results and warnings
3. Click **"Start Processing"**
4. Watch the progress bar (takes several hours)
5. When complete, click **"Open Results Folder"**

## Architecture

```
User
  ↓
Desktop Icon → launcher.sh
  ↓
Web Server (Python http.server)
  ↓
Browser UI (HTML/CSS/JS)
  ↓
Pipeline Runner (subprocess)
  ↓
run_flat_english_pipeline.sh
```

## File Structure

```
vsp-ui/
├── app/
│   ├── config.py              # Configuration (paths, stages, timeouts)
│   ├── server.py              # HTTP server (stdlib only)
│   ├── services/
│   │   ├── validator.py       # Video validation with ffprobe
│   │   ├── pipeline_runner.py # Subprocess management + watchdog
│   │   └── progress_tracker.py# Progress parsing and tracking
│   └── static/
│       ├── index.html         # Main UI
│       ├── style.css          # Styling
│       └── app.js             # Frontend logic
├── launcher.sh                # Desktop launcher
├── vsp-pipeline.desktop       # Desktop entry file
├── icon.svg                   # App icon
├── README.md                  # This file
└── LINUX_SETUP.md            # Setup instructions for Linux container
```

## Pipeline Stages

The UI tracks progress through these stages:

1. **Initialize** (1%) - Archive previous run
2. **ASR Transcription** (15%) - Whisper speech recognition
3. **Prepare Directories** (1%) - Directory setup
4. **Mouth Cropping** (30%) - Face detection and cropping
5. **Format Conversion** (3%) - Convert to LRS3 format
6. **Generate Manifests** (5%) - Build TSV files
7. **K-means Clustering** (20%) - Feature extraction and clustering
8. **LLM Decoding** (20%) - VSP-LLM inference
9. **Generate Outputs** (5%) - Reports and burned videos

## Configuration

### Input Folder

Default: `~/vsp_input/`

Change in `app/config.py`:
```python
INPUT_DIR = HOME_DIR / "your_folder_name"
```

### Pipeline Script

Default: `~/run_flat_english_pipeline.sh`

Change in `app/config.py`:
```python
PIPELINE_SCRIPT = HOME_DIR / "your_script.sh"
```

### Timeouts

Stage timeouts can be adjusted in `app/config.py`:

```python
PIPELINE_STAGES = [
    Stage("stage_id", "Name", "Description", timeout_seconds, weight_percent),
    ...
]
```

## Validation

The validator checks:
- ✅ Supported video formats (`.mp4`, `.mkv`, `.webm`, `.mov`, `.m4v`, `.avi`)
- ✅ Video stream present
- ✅ Valid duration
- ✅ Minimum resolution (64x64)
- ⚠️ K-means viability (minimum 200 segments estimated)

**Note**: K-means warnings are non-blocking. You can proceed, but the pipeline may fail at the clustering stage if there aren't enough videos.

## Outputs

After processing completes, outputs are saved to:

```
~/flat_runs_archive/[YYYYMMDD_HHMMSS]/client_outputs/
├── report/
│   ├── report.csv
│   ├── report.html
│   ├── report.txt
│   └── report.ansi.txt
└── burned_videos/
    └── [original_name]_burned.mp4
```

## Logs

- **Server log**: `~/.vsp-ui.log`
- **Pipeline logs**: Available via "Show Logs" toggle in UI
- **Server status**: Run `./launcher.sh status`

## Troubleshooting

### Server won't start

```bash
# Check if already running
./launcher.sh status

# Stop and restart
./launcher.sh stop
./launcher.sh
```

### Can't see logs

In the UI during processing, click the **"Show Logs"** button to expand the log viewer.

### Pipeline fails immediately

Check:
1. Videos are in the correct folder (`~/vsp_input/`)
2. Pipeline script exists (`~/run_flat_english_pipeline.sh`)
3. Server log for details: `cat ~/.vsp-ui.log`

### Progress stuck

The watchdog will automatically kill stuck stages after their timeout. If a stage exceeds its timeout, you'll see an error with details.

## Advanced Usage

### Stop the server

```bash
./launcher.sh stop
```

### View server status

```bash
./launcher.sh status
```

### Restart server

```bash
./launcher.sh restart
```

### Manual server start

```bash
cd /home/ubuntu/vsp-ui
python3 -m app.server
```

## Linux Container Setup

If you're setting this up on the standalone Linux container, see [LINUX_SETUP.md](LINUX_SETUP.md) for detailed instructions on path configuration and environment variables.

## Development

The UI is built with:
- **Backend**: Python standard library (`http.server`, `subprocess`, `threading`)
- **Frontend**: Vanilla HTML/CSS/JavaScript (no frameworks)
- **No external dependencies**: Works with any Python 3.10+

To modify:
1. Edit files in `app/` or `app/static/`
2. Restart server: `./launcher.sh restart`
3. Refresh browser

## Confidence Visualization (April 2026)

The HTML report renders per-word confidence with color coding:

- **Green** — high confidence (decoder is sure)
- **Yellow** — review (medium confidence — sanity-check before quoting)
- **Red** — likely error (low confidence — treat as unreliable)

**Confidence source**: real per-token softmax probabilities from the LLaMA decoder when `VSP_OUTPUT_SCORES=1` was set during decode (sidecar files `confidence-{fid}.json` written alongside `hypo-{fid}.json`). When no sidecar is available, the renderer falls back to **synthetic confidence derived from WER alignment** so the visualization mechanism still works for archive runs.

**Standalone demo report**: every pipeline run automatically produces an Argos-styled HTML report at `client_outputs/report/argos_demo.html` (included in the server zip download). To regenerate from a decode JSON manually:

```bash
python3 docs/_research-tools/generators/generate_client_demo_report.py \
    --decode <output_dir>/decode_output/hypo-NNNN.json \
    --out report.html
```

Optional flags: `--filter <utt_id_substring>` to restrict to a curated subset, `--title`, `--subtitle`, `--source`, and `--prefix-alias 'src=dst'` to rewrite a long utt_id prefix to a friendlier display name in segment labels.

**Aggregator**: sub-token → word aggregation (mean / min / product over BPE pieces) lives at `docs/_research-tools/generators/compute_word_confidence.py`. Both the standalone demo and the standard pipeline report import the same aggregator, so word-level scores are consistent across renders.

## License

Part of the Visual Speech Processing pipeline project.
