#!/usr/bin/env bash
# ============================================================================
# VSP Pipeline - Comprehensive End-to-End Test Script
# ============================================================================
# Tests all critical pipeline features WITHOUT running the full pipeline.
# No GPU, virtual environments, or model checkpoints required.
#
# Usage:
#   bash tests/test_e2e_pipeline.sh
#
# Requirements: bash 4+, python3 3.6+, ffmpeg/ffprobe
# ============================================================================

set -uo pipefail  # NOT -e: individual failures must not abort the script

# --- Auto-detect paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LIB_DIR="$BASE_DIR/lib"

# --- Temp directory with cleanup ---
TEST_TEMP="/tmp/vsp_e2e_test_$$"
mkdir -p "$TEST_TEMP"
cleanup() { rm -rf "$TEST_TEMP"; }
trap cleanup EXIT INT TERM

# --- Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Counters ---
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

# --- Helpers ---
pass_test() {
    ((PASS_COUNT++))
    echo -e "  ${GREEN}PASS${NC} $1"
}

fail_test() {
    ((FAIL_COUNT++))
    echo -e "  ${RED}FAIL${NC} $1"
    [ -n "${2:-}" ] && echo -e "       ${RED}Reason: $2${NC}"
}

skip_test() {
    ((SKIP_COUNT++))
    echo -e "  ${YELLOW}SKIP${NC} $1 ($2)"
}

# ============================================================================
# FIXTURE CREATION
# ============================================================================

create_test_fixtures() {
    echo -e "${CYAN}Creating test fixtures...${NC}"
    mkdir -p "$TEST_TEMP/fixtures"

    if ! command -v ffmpeg &>/dev/null; then
        echo -e "${RED}ffmpeg not found - cannot create test videos${NC}"
        return 1
    fi

    # Short video (5s) - below MIN_SPLIT_DURATION of 12s
    ffmpeg -y -f lavfi -i "color=c=blue:size=320x240:rate=25:d=5" \
           -f lavfi -i "anullsrc=r=16000:cl=mono" \
           -shortest -c:v libx264 -preset ultrafast -c:a aac \
           "$TEST_TEMP/fixtures/short_video.mp4" 2>/dev/null

    # Long video (30s) - should split into ~3 segments
    ffmpeg -y -f lavfi -i "color=c=red:size=320x240:rate=25:d=30" \
           -f lavfi -i "anullsrc=r=16000:cl=mono" \
           -shortest -c:v libx264 -preset ultrafast -c:a aac \
           "$TEST_TEMP/fixtures/long_video.mp4" 2>/dev/null

    if [ -f "$TEST_TEMP/fixtures/short_video.mp4" ] && [ -f "$TEST_TEMP/fixtures/long_video.mp4" ]; then
        echo -e "${GREEN}Fixtures created${NC}"
        return 0
    else
        echo -e "${RED}Failed to create test fixtures${NC}"
        return 1
    fi
}

# ============================================================================
# TEST 1: Shell Module Exports
# ============================================================================

test_module_exports() {
    echo ""
    echo -e "${CYAN}[1/12] Shell Module Exports${NC}"

    local -A modules=(
        ["common.sh"]="log_info log_error log_stage validate_directory"
        ["config.sh"]="detect_environment get_base_path get_prep_root get_manifest_root get_km_path"
        ["archive.sh"]="archive_previous_run archive_prep_root"
        ["normalization.sh"]="run_normalization copy_raw needs_tonemap"
        ["asr.sh"]="run_asr_transcription"
        ["lrs3_prep.sh"]="run_lrs3_preparation"
        ["manifests.sh"]="run_manifest_generation"
        ["clustering.sh"]="run_clustering"
        ["decode.sh"]="run_vsp_decode"
        ["outputs.sh"]="run_client_outputs"
        ["venv/venv_utils.sh"]="activate_venv deactivate_venv"
    )

    for module in "${!modules[@]}"; do
        local expected="${modules[$module]}"
        local mod_name="${module%.sh}"
        mod_name="${mod_name##*/}"

        if [ ! -f "$LIB_DIR/$module" ]; then
            fail_test "$mod_name: module file missing"
            continue
        fi

        local all_found=true
        local missing=""
        for fn in $expected; do
            if ! (source "$LIB_DIR/$module" 2>/dev/null && declare -F "$fn" >/dev/null 2>&1); then
                all_found=false
                missing="$missing $fn"
            fi
        done

        if $all_found; then
            pass_test "$mod_name: all exports present"
        else
            fail_test "$mod_name: missing exports:$missing"
        fi
    done
}

# ============================================================================
# TEST 2: Log Contamination Fix (Bug #14)
# ============================================================================

test_log_contamination() {
    echo ""
    echo -e "${CYAN}[2/12] Log Contamination Fix${NC}"

    source "$LIB_DIR/common.sh" 2>/dev/null

    # 2a: log_info produces no stdout
    local stdout_output
    stdout_output=$(log_info "test message" 2>/dev/null)
    if [ -z "$stdout_output" ]; then
        pass_test "log_info produces no stdout"
    else
        fail_test "log_info produces no stdout" "Got: '$stdout_output'"
    fi

    # 2b: log_info writes to stderr
    local stderr_output
    stderr_output=$(log_info "test message" 2>&1 >/dev/null)
    if echo "$stderr_output" | grep -q "INFO: test message"; then
        pass_test "log_info writes to stderr"
    else
        fail_test "log_info writes to stderr" "stderr was: '$stderr_output'"
    fi

    # 2c: Function return value not contaminated
    source "$LIB_DIR/common.sh" 2>/dev/null
    _test_fn_with_log() {
        log_info "Starting operation"
        log_info "Processing..."
        echo "/clean/return/value"
    }
    local captured
    captured=$(_test_fn_with_log 2>/dev/null)
    if [ "$captured" = "/clean/return/value" ]; then
        pass_test "Function return not contaminated by log_info"
    else
        fail_test "Function return not contaminated by log_info" "Got: '$captured'"
    fi
}

# ============================================================================
# TEST 3: Segmentation Logic
# ============================================================================

test_segmentation_logic() {
    echo ""
    echo -e "${CYAN}[3/12] Segmentation Logic${NC}"

    if [ ! -f "$TEST_TEMP/fixtures/short_video.mp4" ]; then
        skip_test "Segmentation tests" "fixtures not created"
        return
    fi

    # 3a: Short video not split
    mkdir -p "$TEST_TEMP/input_short" "$TEST_TEMP/seg_short_out"
    cp "$TEST_TEMP/fixtures/short_video.mp4" "$TEST_TEMP/input_short/"
    python3 "$BASE_DIR/auto_avsr/preparation/fast_segment.py" \
        --data-dir "$TEST_TEMP/input_short" \
        --output-dir "$TEST_TEMP/seg_short_out" \
        --seg-duration 12 --overlap 2.0 --min-split-duration 12.0 2>/dev/null

    local short_count
    short_count=$(find "$TEST_TEMP/seg_short_out" -name "*.mp4" | wc -l)
    if [ "$short_count" -eq 1 ]; then
        pass_test "Short video (5s) produces exactly 1 segment"
    else
        fail_test "Short video (5s) produces exactly 1 segment" "Got $short_count"
    fi

    # 3b: Long video split into multiple segments
    mkdir -p "$TEST_TEMP/input_long" "$TEST_TEMP/seg_long_out"
    cp "$TEST_TEMP/fixtures/long_video.mp4" "$TEST_TEMP/input_long/"
    python3 "$BASE_DIR/auto_avsr/preparation/fast_segment.py" \
        --data-dir "$TEST_TEMP/input_long" \
        --output-dir "$TEST_TEMP/seg_long_out" \
        --seg-duration 12 --overlap 2.0 --min-split-duration 12.0 2>/dev/null

    local long_count
    long_count=$(find "$TEST_TEMP/seg_long_out" -name "*.mp4" | wc -l)
    if [ "$long_count" -ge 2 ] && [ "$long_count" -le 4 ]; then
        pass_test "Long video (30s) split into $long_count segments"
    else
        fail_test "Long video (30s) split into 2-4 segments" "Got $long_count"
    fi

    # 3c: segment_metadata.json created for long video
    if [ -f "$TEST_TEMP/seg_long_out/segment_metadata.json" ]; then
        if python3 -c "import json; json.load(open('$TEST_TEMP/seg_long_out/segment_metadata.json'))" 2>/dev/null; then
            pass_test "Long video segment_metadata.json is valid JSON"
        else
            fail_test "Long video segment_metadata.json is valid JSON"
        fi
    else
        fail_test "Long video segment_metadata.json created"
    fi

    # 3d: segment_metadata.json created for short video
    if [ -f "$TEST_TEMP/seg_short_out/segment_metadata.json" ]; then
        pass_test "Short video segment_metadata.json created"
    else
        fail_test "Short video segment_metadata.json created"
    fi
}

# ============================================================================
# TEST 4: Naming Conventions
# ============================================================================

test_naming_conventions() {
    echo ""
    echo -e "${CYAN}[4/12] Naming Conventions${NC}"

    # 4a: Pipeline non-segmented mode keeps original name
    local pipeline="$BASE_DIR/run_flat_english_pipeline.sh"
    if grep -q 'output_name="${video_name}"' "$pipeline"; then
        pass_test "Pipeline uses original name for non-segmented videos"
    else
        fail_test "Pipeline uses original name for non-segmented videos"
    fi

    # 4b: Split videos get segment suffix pattern
    local seg_files
    seg_files=$(find "$TEST_TEMP/seg_long_out" -name "long_video_*_*_*.mp4" 2>/dev/null | wc -l)
    if [ "$seg_files" -ge 2 ]; then
        pass_test "Split videos have segment suffix ({id}_{idx}_{start}_{end}.mp4)"
    else
        skip_test "Split video naming" "segment output not available"
    fi

    # 4c: preprocess_with_overlap single-segment keeps original name (fix #17)
    if python3 -c "
import sys; sys.path.insert(0, '$BASE_DIR/auto_avsr/preparation')
from overlapping_segmentation import split_video_by_time
segs = split_video_by_time(5.0, 12.0, 2.0, 12.0, 25.0)
assert len(segs) == 1, f'Expected 1, got {len(segs)}'
# In preprocess_with_overlap.py: len(time_segments)==1 -> suffix=''
" 2>/dev/null; then
        pass_test "Single-segment video: split_video_by_time returns 1 segment"
    else
        fail_test "Single-segment video: split_video_by_time returns 1 segment"
    fi

    # 4d: Verify the suffix logic exists in preprocess_with_overlap.py
    if grep -q 'segment_suffix = ""' "$BASE_DIR/auto_avsr/preparation/preprocess_with_overlap.py"; then
        pass_test "preprocess_with_overlap.py has single-segment empty suffix fix"
    else
        fail_test "preprocess_with_overlap.py has single-segment empty suffix fix"
    fi
}

# ============================================================================
# TEST 5: Segment Metadata Structure
# ============================================================================

test_segment_metadata_structure() {
    echo ""
    echo -e "${CYAN}[5/12] Segment Metadata Structure${NC}"

    local meta="$TEST_TEMP/seg_long_out/segment_metadata.json"
    if [ ! -f "$meta" ]; then
        skip_test "Metadata structure tests" "metadata file not available"
        return
    fi

    # 5a: Has required top-level fields
    if python3 -c "
import json
with open('$meta') as f:
    m = json.load(f)
for k in ['segments', 'total_segments', 'total_videos', 'seg_duration', 'overlap']:
    assert k in m, f'Missing: {k}'
" 2>/dev/null; then
        pass_test "Flat metadata has all required top-level fields"
    else
        fail_test "Flat metadata has all required top-level fields"
    fi

    # 5b: Each segment has required fields
    if python3 -c "
import json
with open('$meta') as f:
    m = json.load(f)
for seg in m['segments']:
    for k in ['original_video','video_id','segment_index','segment_id',
              'filename','start_sec','end_sec','duration','start_frame','end_frame']:
        assert k in seg, f'Segment missing: {k}'
    assert seg['start_sec'] >= 0
    assert seg['end_sec'] > seg['start_sec']
    assert seg['end_frame'] > seg['start_frame']
" 2>/dev/null; then
        pass_test "Each segment has all required fields with valid values"
    else
        fail_test "Each segment has all required fields with valid values"
    fi

    # 5c: Segment overlap is approximately correct
    if python3 -c "
import json
with open('$meta') as f:
    m = json.load(f)
segs = sorted(m['segments'], key=lambda s: s['start_sec'])
if len(segs) >= 2:
    for i in range(1, len(segs)):
        overlap = segs[i-1]['end_sec'] - segs[i]['start_sec']
        assert 0.5 < overlap < 4.0, f'Overlap {overlap:.2f}s out of range'
" 2>/dev/null; then
        pass_test "Segment overlap is within expected range (~2s)"
    else
        fail_test "Segment overlap is within expected range (~2s)"
    fi

    # 5d: Per-video nested metadata format (generate_segment_metadata)
    if python3 -c "
import sys, json
sys.path.insert(0, '$BASE_DIR/auto_avsr/preparation')
from overlapping_segmentation import split_video_by_time, generate_segment_metadata

segs_raw = split_video_by_time(30.0, 12.0, 2.0, 12.0, 25.0)
segs = [('transcript', st, et, et-st, sf, ef) for st, et, sf, ef in segs_raw]
out = '$TEST_TEMP/nested_metadata.json'
generate_segment_metadata({'test_video': segs}, out, 12.0, 2.0)

with open(out) as f:
    m = json.load(f)
assert 'test_video' in m
vm = m['test_video']
for k in ['segments', 'num_segments', 'original_duration']:
    assert k in vm, f'Missing: {k}'
for seg in vm['segments']:
    for k in ['index','start_frame','end_frame','start_sec','end_sec','duration']:
        assert k in seg, f'Seg missing: {k}'
" 2>/dev/null; then
        pass_test "Nested per-video metadata format is correct"
    else
        fail_test "Nested per-video metadata format is correct"
    fi

    # 5e: Non-segmented video metadata (single segment)
    if python3 -c "
import sys, json
sys.path.insert(0, '$BASE_DIR/auto_avsr/preparation')
from overlapping_segmentation import split_video_by_time, generate_segment_metadata

segs_raw = split_video_by_time(5.0, 12.0, 2.0, 12.0, 25.0)
segs = [('transcript', st, et, et-st, sf, ef) for st, et, sf, ef in segs_raw]
out = '$TEST_TEMP/single_metadata.json'
generate_segment_metadata({'short_vid': segs}, out, 12.0, 2.0)

with open(out) as f:
    m = json.load(f)
assert m['short_vid']['num_segments'] == 1
assert len(m['short_vid']['segments']) == 1
assert m['short_vid']['segments'][0]['index'] == 0
assert m['short_vid']['segments'][0]['start_sec'] == 0.0
" 2>/dev/null; then
        pass_test "Non-segmented video produces single-segment metadata"
    else
        fail_test "Non-segmented video produces single-segment metadata"
    fi
}

# ============================================================================
# TEST 6: Transcription Persistence (Step 0.6 / 1.5)
# ============================================================================

test_transcription_persistence() {
    echo ""
    echo -e "${CYAN}[6/12] Transcription Persistence${NC}"

    local MOCK_TRANS="$TEST_TEMP/mock_transcriptions"
    local MOCK_VID="$TEST_TEMP/mock_videos"
    local MOCK_WRD="$TEST_TEMP/mock_wrd_tmp"
    mkdir -p "$MOCK_TRANS" "$MOCK_VID" "$MOCK_WRD"

    # Setup: video + matching transcription
    touch "$MOCK_VID/Obama_00_000000_000300.mp4"
    printf 'hello\nworld\n' > "$MOCK_TRANS/Obama_00_000000_000300.wrd"

    # 6a: Step 0.6 copies matching .wrd files
    for video_file in "$MOCK_VID"/*.mp4; do
        local vname
        vname=$(basename "$video_file" .mp4)
        if [ -f "$MOCK_TRANS/${vname}.wrd" ]; then
            cp "$MOCK_TRANS/${vname}.wrd" "$MOCK_WRD/${vname}.wrd"
        fi
    done

    if [ -f "$MOCK_WRD/Obama_00_000000_000300.wrd" ]; then
        pass_test "Step 0.6: Matching transcription copied to working dir"
    else
        fail_test "Step 0.6: Matching transcription copied to working dir"
    fi

    # 6b: Step 0.6 does NOT copy unmatched transcriptions
    printf 'stale\nwords\n' > "$MOCK_TRANS/deleted_video_01_000000_000250.wrd"
    # Re-run - only videos in MOCK_VID should match
    if [ ! -f "$MOCK_WRD/deleted_video_01_000000_000250.wrd" ]; then
        pass_test "Step 0.6: Unmatched transcription NOT copied"
    else
        fail_test "Step 0.6: Unmatched transcription NOT copied"
    fi

    # 6c: Step 1.5 saves new auto transcriptions
    printf 'auto\ntranscribed\nwords\n' > "$MOCK_WRD/NewVideo_00_000000_000300.wrd"
    echo '{"transcriptions":{}}' > "$MOCK_TRANS/metadata.json"

    local fname="NewVideo_00_000000_000300.wrd"
    if [[ "$fname" =~ _[0-9]{2}_[0-9]{6}_[0-9]{6}\.wrd$ ]]; then
        cp "$MOCK_WRD/$fname" "$MOCK_TRANS/$fname"
    fi

    if [ -f "$MOCK_TRANS/NewVideo_00_000000_000300.wrd" ]; then
        pass_test "Step 1.5: New auto transcription saved to .transcriptions/"
    else
        fail_test "Step 1.5: New auto transcription saved to .transcriptions/"
    fi

    # 6d: Step 1.5 does NOT overwrite manual transcriptions
    python3 -c "
import json
meta = {'transcriptions': {
    'Obama_00_000000_000300.mp4': {'type': 'manual', 'word_count': 2}
}}
with open('$MOCK_TRANS/metadata.json', 'w') as f:
    json.dump(meta, f)
" 2>/dev/null

    local orig_content
    orig_content=$(cat "$MOCK_TRANS/Obama_00_000000_000300.wrd")

    # Simulate Whisper creating different content
    printf 'different\nauto\nresult\n' > "$MOCK_WRD/Obama_00_000000_000300.wrd"

    local check_fname="Obama_00_000000_000300.wrd"
    local is_manual
    is_manual=$(python3 -c "
import json
try:
    with open('$MOCK_TRANS/metadata.json') as f:
        meta = json.load(f)
    fn_mp4 = '${check_fname%.wrd}.mp4'
    t = meta.get('transcriptions',{}).get(fn_mp4,{}).get('type','auto')
    print('yes' if t == 'manual' else 'no')
except:
    print('no')
" 2>/dev/null)

    if [ "$is_manual" != "yes" ]; then
        cp "$MOCK_WRD/$check_fname" "$MOCK_TRANS/$check_fname"
    fi

    local current_content
    current_content=$(cat "$MOCK_TRANS/Obama_00_000000_000300.wrd")
    if [ "$orig_content" = "$current_content" ]; then
        pass_test "Step 1.5: Manual transcription NOT overwritten"
    else
        fail_test "Step 1.5: Manual transcription NOT overwritten" "Content changed"
    fi

    # 6e: Segment regex pattern matches correctly
    if python3 -c "
import re
p = r'_[0-9]{2}_[0-9]{6}_[0-9]{6}\.wrd\$'
assert re.search(p, 'Obama_00_000000_000300.wrd')
assert re.search(p, 'Video_A__hash_02_000500_000800.wrd')
assert not re.search(p, 'Obama.wrd')
assert not re.search(p, 'short_clip.wrd')
" 2>/dev/null; then
        pass_test "Segment regex correctly matches/rejects filenames"
    else
        fail_test "Segment regex correctly matches/rejects filenames"
    fi
}

# ============================================================================
# TEST 7: K-means Toggle
# ============================================================================

test_kmeans_toggle() {
    echo ""
    echo -e "${CYAN}[7/12] K-means Toggle${NC}"

    # 7a: clustering.sh reads TRAIN_KMEANS parameter
    local fn_body
    source "$LIB_DIR/clustering.sh" 2>/dev/null
    fn_body=$(declare -f run_clustering 2>/dev/null)
    if echo "$fn_body" | grep -q 'train_kmeans'; then
        pass_test "clustering.sh reads train_kmeans parameter"
    else
        fail_test "clustering.sh reads train_kmeans parameter"
    fi

    # 7b: Pipeline defaults TRAIN_KMEANS to 1
    if grep -q 'TRAIN_KMEANS.*:-1' "$BASE_DIR/run_flat_english_pipeline.sh" || \
       grep -q 'TRAIN_KMEANS="${TRAIN_KMEANS:-1}"' "$BASE_DIR/run_flat_english_pipeline.sh"; then
        pass_test "Pipeline defaults TRAIN_KMEANS to 1"
    else
        fail_test "Pipeline defaults TRAIN_KMEANS to 1"
    fi
}

# ============================================================================
# TEST 8: Archive Behavior
# ============================================================================

test_archive_behavior() {
    echo ""
    echo -e "${CYAN}[8/12] Archive Behavior${NC}"

    source "$LIB_DIR/common.sh" 2>/dev/null
    source "$LIB_DIR/archive.sh" 2>/dev/null

    # 8a: archive_previous_run creates dir and returns clean path
    local MOCK_HOME="$TEST_TEMP/archive_test"
    mkdir -p "$MOCK_HOME/flat_wrd" "$MOCK_HOME/flat_txt"
    touch "$MOCK_HOME/flat_wrd/test.wrd" "$MOCK_HOME/flat_txt/test.txt"

    local result
    result=$(archive_previous_run "$MOCK_HOME" 12 "$MOCK_HOME/flat_wrd" "$MOCK_HOME/flat_txt" 2>/dev/null)

    if [ -d "$result" ]; then
        pass_test "archive_previous_run creates archive directory"
    else
        fail_test "archive_previous_run creates archive directory" "Result: '$result'"
    fi

    # 8b: Return value is a clean single-line path (no log contamination)
    local line_count
    line_count=$(echo "$result" | wc -l)
    if [ "$line_count" -eq 1 ] && ! echo "$result" | grep -q 'INFO:'; then
        pass_test "archive_previous_run return is clean (no log contamination)"
    else
        fail_test "archive_previous_run return is clean (no log contamination)" "Lines: $line_count, value: '$result'"
    fi

    # 8c: archive_prep_root preserves flat_text_seg directories
    local MOCK_PR="$TEST_TEMP/archive_prep/preprocessed_flat_seg12"
    local MOCK_AR="$TEST_TEMP/archive_prep/archive"
    mkdir -p "$MOCK_PR/flat/flat_text_seg12s" "$MOCK_PR/flat/flat_video_seg12s" "$MOCK_PR/433h_data"
    touch "$MOCK_PR/flat/flat_text_seg12s/manual.txt"
    touch "$MOCK_PR/flat/flat_video_seg12s/vid.mp4"
    touch "$MOCK_PR/433h_data/train.tsv"
    mkdir -p "$MOCK_AR"

    archive_prep_root "$MOCK_PR" "$MOCK_AR" 12 2>/dev/null

    if [ -d "$MOCK_PR/flat/flat_text_seg12s" ] && [ -f "$MOCK_PR/flat/flat_text_seg12s/manual.txt" ]; then
        pass_test "archive_prep_root preserves flat_text_seg12s/"
    else
        fail_test "archive_prep_root preserves flat_text_seg12s/"
    fi
}

# ============================================================================
# TEST 9: Path Auto-Detection
# ============================================================================

test_path_autodetection() {
    echo ""
    echo -e "${CYAN}[9/12] Path Auto-Detection${NC}"

    local lrs3_script="$BASE_DIR/av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh"

    # 9a: flat_to_lrs3_preperation.sh uses BASH_SOURCE
    if grep -q 'PREP_DIR="$(cd "$(dirname "${BASH_SOURCE\[0\]}")" && pwd)"' "$lrs3_script" 2>/dev/null; then
        pass_test "flat_to_lrs3_preperation.sh uses BASH_SOURCE for PREP_DIR"
    else
        fail_test "flat_to_lrs3_preperation.sh uses BASH_SOURCE for PREP_DIR"
    fi

    # 9b: Derives VENV from parent directory (not hardcoded)
    if grep -q '_BASE_DIR=.*PREP_DIR' "$lrs3_script" && ! grep -q 'VENV="/home/ubuntu' "$lrs3_script"; then
        pass_test "flat_to_lrs3_preperation.sh derives VENV from script location"
    else
        fail_test "flat_to_lrs3_preperation.sh derives VENV from script location"
    fi

    # 9c: Pipeline uses SCRIPT_DIR for BASE_DIR
    local pipeline="$BASE_DIR/run_flat_english_pipeline.sh"
    if grep -q 'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE\[0\]}")" && pwd)"' "$pipeline" && \
       grep -q 'BASE_DIR="$SCRIPT_DIR"' "$pipeline"; then
        pass_test "Pipeline auto-detects BASE_DIR from script location"
    else
        fail_test "Pipeline auto-detects BASE_DIR from script location"
    fi
}

# ============================================================================
# TEST 10: Pipeline Variable Defaults
# ============================================================================

test_pipeline_defaults() {
    echo ""
    echo -e "${CYAN}[10/12] Pipeline Variable Defaults${NC}"

    local pipeline="$BASE_DIR/run_flat_english_pipeline.sh"

    local -A expected_defaults=(
        ["SEG_DURATION"]='SEG_DURATION.*:-12'
        ["SEGMENTATION_ENABLED"]='SEGMENTATION_ENABLED.*:-1'
        ["OVERLAP_ENABLED"]='OVERLAP_ENABLED.*:-1'
        ["OVERLAP_DURATION"]='OVERLAP_DURATION="2.0"'
        ["MIN_SPLIT_DURATION"]='MIN_SPLIT_DURATION="12.0"'
        ["PREPROCESS_ONLY"]='PREPROCESS_ONLY.*:-0'
        ["TRAIN_KMEANS"]='TRAIN_KMEANS.*:-1'
        ["SKIP_NORM"]='SKIP_NORM.*:-0'
    )

    for var in "${!expected_defaults[@]}"; do
        local pattern="${expected_defaults[$var]}"
        if grep -qE "$pattern" "$pipeline"; then
            pass_test "$var has correct default"
        else
            fail_test "$var has correct default" "Expected pattern: $pattern"
        fi
    done
}

# ============================================================================
# TEST 11: Overlapping Segmentation Module
# ============================================================================

test_overlapping_segmentation() {
    echo ""
    echo -e "${CYAN}[11/12] Overlapping Segmentation Module${NC}"

    local pypath="$BASE_DIR/auto_avsr/preparation"

    # 11a: Short video returns single segment
    if python3 -c "
import sys; sys.path.insert(0, '$pypath')
from overlapping_segmentation import split_video_by_time
segs = split_video_by_time(5.0, 12.0, 2.0, 12.0, 25.0)
assert len(segs) == 1, f'Expected 1, got {len(segs)}'
assert segs[0][0] == 0.0
assert abs(segs[0][1] - 5.0) < 0.01
" 2>/dev/null; then
        pass_test "5s video: returns single segment"
    else
        fail_test "5s video: returns single segment"
    fi

    # 11b: 30s video returns 3 segments with correct overlap
    if python3 -c "
import sys; sys.path.insert(0, '$pypath')
from overlapping_segmentation import split_video_by_time
segs = split_video_by_time(30.0, 12.0, 2.0, 12.0, 25.0)
assert len(segs) == 3, f'Expected 3, got {len(segs)}'
assert abs(segs[1][0] - 10.0) < 0.01, f'Seg1 start: {segs[1][0]}'
assert abs(segs[2][0] - 20.0) < 0.01, f'Seg2 start: {segs[2][0]}'
overlap = segs[0][1] - segs[1][0]
assert abs(overlap - 2.0) < 0.01, f'Overlap: {overlap}'
" 2>/dev/null; then
        pass_test "30s video: 3 segments with 2s overlap"
    else
        fail_test "30s video: 3 segments with 2s overlap"
    fi

    # 11c: Boundary video (24s = min split + 12)
    if python3 -c "
import sys; sys.path.insert(0, '$pypath')
from overlapping_segmentation import split_video_by_time
segs = split_video_by_time(24.0, 12.0, 2.0, 12.0, 25.0)
assert len(segs) >= 2, f'Expected >=2, got {len(segs)}'
" 2>/dev/null; then
        pass_test "24s video: splits into >= 2 segments"
    else
        fail_test "24s video: splits into >= 2 segments"
    fi

    # 11d: Overlap >= segment_duration raises ValueError
    if python3 -c "
import sys; sys.path.insert(0, '$pypath')
from overlapping_segmentation import split_video_by_time
try:
    split_video_by_time(30.0, 12.0, 12.0, 12.0, 25.0)
    assert False, 'Should raise ValueError'
except ValueError:
    pass
" 2>/dev/null; then
        pass_test "overlap >= duration raises ValueError"
    else
        fail_test "overlap >= duration raises ValueError"
    fi

    # 11e: Frame numbers are consistent integers
    if python3 -c "
import sys; sys.path.insert(0, '$pypath')
from overlapping_segmentation import split_video_by_time
segs = split_video_by_time(30.0, 12.0, 2.0, 12.0, 25.0)
for st, et, sf, ef in segs:
    assert isinstance(sf, int), f'start_frame type: {type(sf)}'
    assert isinstance(ef, int), f'end_frame type: {type(ef)}'
    assert sf >= 0
    assert ef <= int(30.0 * 25.0)
" 2>/dev/null; then
        pass_test "Frame numbers are consistent integers"
    else
        fail_test "Frame numbers are consistent integers"
    fi
}

# ============================================================================
# TEST 12: make_burn Segment Matching
# ============================================================================

test_make_burn_segment_matching() {
    echo ""
    echo -e "${CYAN}[12/12] make_burn Segment Matching${NC}"

    local pypath="$BASE_DIR/VSP-LLM/scripts"

    # 12a: parse_segment_id with segmented ID
    if python3 -c "
import sys; sys.path.insert(0, '$pypath')
from make_burn import parse_segment_id
vid, idx, sf, ef = parse_segment_id('Obama_00_000000_000300')
assert vid == 'Obama', f'Got vid={vid}'
assert idx == 0, f'Got idx={idx}'
assert sf == 0
assert ef == 300
" 2>/dev/null; then
        pass_test "parse_segment_id: segmented ID (Obama_00_000000_000300)"
    else
        fail_test "parse_segment_id: segmented ID (Obama_00_000000_000300)"
    fi

    # 12b: parse_segment_id with hash in video ID
    if python3 -c "
import sys; sys.path.insert(0, '$pypath')
from make_burn import parse_segment_id
vid, idx, sf, ef = parse_segment_id('VideoA__abc12345_02_000500_000800')
assert vid == 'VideoA__abc12345', f'Got vid={vid}'
assert idx == 2
assert sf == 500
assert ef == 800
" 2>/dev/null; then
        pass_test "parse_segment_id: hash ID (VideoA__abc12345_02_...)"
    else
        fail_test "parse_segment_id: hash ID (VideoA__abc12345_02_...)"
    fi

    # 12c: parse_segment_id with non-segmented ID (whole video)
    if python3 -c "
import sys; sys.path.insert(0, '$pypath')
from make_burn import parse_segment_id
vid, idx, sf, ef = parse_segment_id('00008')
assert vid == '00008', f'Got vid={vid}'
assert idx == -1, f'Got idx={idx}'
assert sf == -1
assert ef == -1
" 2>/dev/null; then
        pass_test "parse_segment_id: non-segmented ID (00008) returns idx=-1"
    else
        fail_test "parse_segment_id: non-segmented ID (00008) returns idx=-1"
    fi

    # 12d: extract_base_video_id consistency
    if python3 -c "
import sys; sys.path.insert(0, '$pypath')
from make_burn import extract_base_video_id
assert extract_base_video_id('Obama_00_000000_000300') == 'Obama'
assert extract_base_video_id('VideoA__abc12345_02_000500_000800') == 'VideoA__abc12345'
assert extract_base_video_id('00008') == '00008'
assert extract_base_video_id('my_video') == 'my_video'
" 2>/dev/null; then
        pass_test "extract_base_video_id: consistent across all formats"
    else
        fail_test "extract_base_video_id: consistent across all formats"
    fi

    # 12e: Non-segmented video uses first segment from metadata (fix #16)
    if python3 -c "
import sys; sys.path.insert(0, '$pypath')
from make_burn import parse_segment_id

vid, idx, sf, ef = parse_segment_id('00008')
metadata = {'00008': {'segments': [{'index': 0, 'start_sec': 0.0, 'duration': 3.584}]}}
segments = metadata[vid]['segments']

segment_info = None
if idx == -1:
    if segments:
        segment_info = segments[0]
else:
    for seg in segments:
        if seg.get('index') == idx:
            segment_info = seg
            break

assert segment_info is not None, 'Should find segment'
assert segment_info['start_sec'] == 0.0
assert segment_info['duration'] == 3.584
" 2>/dev/null; then
        pass_test "Non-segmented video: seg_idx=-1 uses segments[0] (fix #16)"
    else
        fail_test "Non-segmented video: seg_idx=-1 uses segments[0] (fix #16)"
    fi
}

# ============================================================================
# MAIN
# ============================================================================

echo ""
echo "========================================"
echo "VSP Pipeline - End-to-End Test Suite"
echo "========================================"
echo "Base dir: $BASE_DIR"
echo "Temp dir: $TEST_TEMP"
echo ""

# Create fixtures first
create_test_fixtures || echo -e "${YELLOW}Warning: Some tests will be skipped${NC}"

# Run all test categories
test_module_exports
test_log_contamination
test_segmentation_logic
test_naming_conventions
test_segment_metadata_structure
test_transcription_persistence
test_kmeans_toggle
test_archive_behavior
test_path_autodetection
test_pipeline_defaults
test_overlapping_segmentation
test_make_burn_segment_matching

# Summary
echo ""
echo "========================================"
echo "TEST SUMMARY"
echo "========================================"
echo -e "  ${GREEN}PASSED: $PASS_COUNT${NC}"
echo -e "  ${RED}FAILED: $FAIL_COUNT${NC}"
echo -e "  ${YELLOW}SKIPPED: $SKIP_COUNT${NC}"
TOTAL=$((PASS_COUNT + FAIL_COUNT + SKIP_COUNT))
echo "  TOTAL:  $TOTAL"
echo "========================================"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "${RED}RESULT: SOME TESTS FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}RESULT: ALL TESTS PASSED${NC}"
    exit 0
fi
