# Manual Segment Transcription Guide

This guide explains how to manually transcribe video segments after they've been split by the preprocessing step.

## Overview

With the segment-level architecture, videos are split into 12-second segments with 2-second overlap. This allows you to:
1. Split long videos into manageable segments
2. Manually transcribe each segment individually
3. Process segments through the pipeline

**Why manual transcription?**
- Whisper may make errors, especially with technical terms or accents
- Domain-specific vocabulary may require human correction
- Some videos may have poor audio quality where human transcription is more accurate

## Workflow

### Option 1: Full Pipeline with Whisper (Automatic)

Run the complete pipeline - Whisper will transcribe all segments automatically:

```bash
./run_flat_english_pipeline.sh /path/to/videos
```

Then manually edit any incorrect transcriptions afterward.

### Option 2: Manual Transcription Before ASR

**Step 1: Run preprocessing only**

```bash
PREPROCESS_ONLY=1 ./run_flat_english_pipeline.sh /path/to/videos
```

This will:
- Split videos into 12s segments with 2s overlap
- Stop before running ASR
- Print the location of segmented videos

**Step 2: Manually transcribe segments**

Use the interactive transcription tool:

```bash
python /home/ubuntu/VSP-LLM/scripts/transcribe_segments.py \
    --segment-dir /home/ubuntu/auto_avsr/preprocessed_flat_seg12/flat/flat_video_seg12s \
    --output-dir /home/ubuntu/auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s
```

The tool will:
- Show each segment video
- Prompt you to type the transcription
- Automatically normalize to pipeline format
- Save transcriptions as .txt files
- Resume from where you left off if interrupted

**Step 3: Continue pipeline from ASR**

```bash
PREPROCESS_ONLY=0 ./run_flat_english_pipeline.sh /path/to/videos
```

This will:
- Skip preprocessing (already done)
- Run ASR on segments WITHOUT transcriptions (Whisper skips existing .txt files)
- Continue with manifests, k-means, decoding, and output generation

## Interactive Transcription Tool

### Basic Usage

```bash
python /home/ubuntu/VSP-LLM/scripts/transcribe_segments.py \
    --segment-dir <path-to-segments> \
    --output-dir <path-to-save-transcriptions>
```

### List Segments

Check which segments need transcription:

```bash
python /home/ubuntu/VSP-LLM/scripts/transcribe_segments.py \
    --segment-dir <path-to-segments> \
    --output-dir <path-to-transcriptions> \
    --list
```

Output:
```
Total segments: 6
Transcribed: 2
Untranscribed: 4

Untranscribed segments:
  ✗ Obama_00_000000_000300
  ✗ Obama_02_000500_000800
  ✗ Obama_03_000750_001050
  ✗ Obama_05_001250_001500
```

### Transcription Format

**Input (flexible)**: Type words separated by spaces or newlines

```
Hello world this is a test
transcription with multiple words
```

**Output (pipeline format)**: One word per line, lowercase, alphanumeric only

```
hello
world
this
is
a
test
transcription
with
multiple
words
```

The tool automatically normalizes your input to match this format.

### Resume Support

The tool automatically skips segments that already have transcriptions. To re-transcribe segments:

```bash
# Delete existing transcriptions
rm /path/to/flat_text_seg12s/Obama_00_000000_000300.txt

# Run tool again - it will prompt for that segment
python /home/ubuntu/VSP-LLM/scripts/transcribe_segments.py ...
```

Or use `--no-resume` to transcribe all segments:

```bash
python /home/ubuntu/VSP-LLM/scripts/transcribe_segments.py \
    --segment-dir <path> \
    --output-dir <path> \
    --no-resume
```

## Manual File Creation

If you prefer not to use the interactive tool, you can create transcription files manually:

**File location**: `~/auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s/`

**Filename**: `{segment_id}.txt` (e.g., `Obama_00_000000_000300.txt`)

**Format**: One word per line, lowercase, alphanumeric + apostrophes only

**Example** (`Obama_00_000000_000300.txt`):
```
we
made
great
strides
in
our
efforts
to
improve
```

**Validation**:
- Only lowercase letters (a-z)
- Only digits (0-9)
- Only apostrophes (') for contractions like "don't"
- No punctuation, no special characters
- One word per line
- No empty lines

## Overlap Handling

**Important**: Segments overlap by 2 seconds (frames 250-300 of segment 0 = frames 0-50 of segment 1).

**How to transcribe overlap regions:**

1. **Transcribe the full segment including overlap**
   - For segment 0 (0-12s): transcribe everything you hear from 0s to 12s
   - For segment 1 (10-22s): transcribe everything you hear from 10s to 22s
   - Yes, this means the 10-12s region appears in BOTH transcriptions

2. **The pipeline handles deduplication automatically**
   - When calculating WER per-video, the pipeline skips ~17% of words at segment boundaries
   - This removes the duplicate words from the overlap region

**Example**:
```
Segment 0 (0-12s):  "we made great strides in our efforts"
Segment 1 (10-22s): "in our efforts to improve the quality of life"
                     ^^^^^^^^^ overlap region

After deduplication (for WER calculation):
"we made great strides in our efforts to improve the quality of life"
```

## Tips for Manual Transcription

1. **Watch the video multiple times**
   - First pass: Get the gist
   - Second pass: Write down words
   - Third pass: Verify accuracy

2. **Use context from overlap**
   - The 2s overlap helps verify word boundaries
   - Check if the last words of segment N match the first words of segment N+1

3. **Handle unclear audio**
   - If you can't understand a word, make your best guess
   - The model will still learn from the visual features
   - Mark uncertain segments for review

4. **Consistency matters**
   - Use consistent spelling (e.g., "okay" vs "ok")
   - Follow the normalization rules (lowercase, alphanumeric)
   - The tool helps by auto-normalizing your input

5. **Use transcription shortcuts**
   - Type 'skip' to skip a segment
   - Type 'quit' to exit early
   - Press Ctrl+D when done typing to submit

## Verifying Transcriptions

After transcribing, verify that all segments have transcriptions:

```bash
python /home/ubuntu/VSP-LLM/scripts/transcribe_segments.py \
    --segment-dir ~/auto_avsr/preprocessed_flat_seg12/flat/flat_video_seg12s \
    --output-dir ~/auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s \
    --list --show-all
```

Output:
```
Total segments: 6
Transcribed: 6
Untranscribed: 0

All segments:
  ✓ Obama_00_000000_000300
  ✓ Obama_01_000250_000550
  ✓ Obama_02_000500_000800
  ✓ Obama_03_000750_001050
  ✓ Obama_04_001000_001300
  ✓ Obama_05_001250_001500
```

## Troubleshooting

**Problem**: Tool says "No segments found"

**Solution**: Check that you provided the correct path to the segment video directory:
```bash
ls ~/auto_avsr/preprocessed_flat_seg12/flat/flat_video_seg12s/*.mp4
```

**Problem**: ASR runs on manually transcribed segments

**Solution**: Whisper only skips segments that have BOTH:
1. A .txt file in `flat_text_seg12s/`
2. A .wrd file in the segment wrd temp directory

To force skip, create both files or ensure .txt files exist before running ASR.

**Problem**: Transcription format error in pipeline

**Solution**: Verify your .txt files match the format:
- One word per line
- Lowercase only
- No empty lines
- No special characters (except apostrophes)

**Problem**: Want to re-transcribe a segment

**Solution**: Delete the .txt file and run the tool again:
```bash
rm ~/auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s/Obama_00_000000_000300.txt
python /home/ubuntu/VSP-LLM/scripts/transcribe_segments.py ...
```

## Example: Complete Manual Transcription Workflow

```bash
# Step 1: Run preprocessing only
cd /home/ubuntu
PREPROCESS_ONLY=1 ./run_flat_english_pipeline.sh ~/vsp_input

# Output shows:
# >>> [INFO] Segmented videos are in: /home/ubuntu/auto_avsr/preprocessed_flat_seg12/flat/flat_video_seg12s

# Step 2: Check which segments need transcription
python VSP-LLM/scripts/transcribe_segments.py \
    --segment-dir auto_avsr/preprocessed_flat_seg12/flat/flat_video_seg12s \
    --output-dir auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s \
    --list

# Output shows: 6 segments, 0 transcribed, 6 untranscribed

# Step 3: Interactively transcribe segments
python VSP-LLM/scripts/transcribe_segments.py \
    --segment-dir auto_avsr/preprocessed_flat_seg12/flat/flat_video_seg12s \
    --output-dir auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s

# Tool prompts for each segment:
# Segment 1 of 6: Obama_00_000000_000300
# Duration: 12.0s | Resolution: 640x480
# Enter transcription (Ctrl+D when done):
# [user types transcription]
# Normalized: we made great strides in our efforts
# Save this transcription? [Y/n]: y
# ✓ Saved: .../flat_text_seg12s/Obama_00_000000_000300.txt

# Step 4: Verify all segments transcribed
python VSP-LLM/scripts/transcribe_segments.py \
    --segment-dir auto_avsr/preprocessed_flat_seg12/flat/flat_video_seg12s \
    --output-dir auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s \
    --list

# Output shows: 6 segments, 6 transcribed, 0 untranscribed

# Step 5: Continue pipeline from ASR
./run_flat_english_pipeline.sh ~/vsp_input

# Pipeline will:
# - Skip preprocessing (already done)
# - Skip ASR on manually transcribed segments
# - Run k-means, decode, and generate outputs
```

## See Also

- [CLAUDE.md](CLAUDE.md) - Full pipeline documentation
- [Segment-Level Architecture](CLAUDE.md#segment-level-architecture-since-jan-2026) - Architecture overview
- [calculate_per_video_wer.py](VSP-LLM/scripts/calculate_per_video_wer.py) - WER calculation with overlap deduplication
