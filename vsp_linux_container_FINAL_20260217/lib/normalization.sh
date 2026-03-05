#!/usr/bin/env bash
# ==================================================
# Video Normalization Module
# ==================================================
# Handles video normalization, HDR/10-bit conversion, GPU encoding
# Works on EC2 and Linux container

# Source common utilities for logging
MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${MODULE_DIR}/common.sh"

# Helper function: Copy raw video without processing
copy_raw() {
  local src="$1"
  local dst_dir="$2"
  local bn dst
  bn="$(basename "$src")"
  dst="${dst_dir}/${bn%.*}.mp4"
  cp -f -- "$src" "$dst"
}

# Helper function: Check if video needs HDR/10-bit tone mapping
needs_tonemap() {
  local _nt_file="$1"
  local probe_out

  probe_out=$(ffprobe -v quiet -print_format json -show_streams "$_nt_file" 2>/dev/null || echo "")

  # Check for 10-bit pixel format (yuv420p10le, yuv420p10be, etc.)
  if echo "$probe_out" | grep -q '"pix_fmt".*10le\|10be'; then
    return 0  # true - needs tonemap
  fi

  # Check for HDR color space (bt2020)
  if echo "$probe_out" | grep -q '"color_space".*"bt2020'; then
    return 0  # true - needs tonemap
  fi

  return 1  # false - standard 8-bit SDR
}

# Main normalization function
# Parameters:
#   $1 - Input directory (raw videos)
#   $2 - Output directory (normalized videos)
#   $3 - Skip normalization (0 or 1, default 0)
#   $4 - Max dimension (0 = keep original, or 720/1080/etc, default 0)
#   $5 - Output FPS (default 25)
#   $6 - Use GPU (0 or 1, default 1)
#   $7 - Timeout in seconds (default 600)
run_normalization() {
  local raw_dir="$1"
  local output_dir="$2"
  local skip_norm="${3:-0}"
  local max_dim="${4:-0}"
  local fps_out="${5:-25}"
  local use_gpu="${6:-1}"
  local timeout_sec="${7:-600}"

  log_info "Normalizing videos (SKIP=${skip_norm}, GPU=${use_gpu}, MAX_DIM=${max_dim}, FPS=${fps_out}, TIMEOUT=${timeout_sec}s)"

  # Create output directory
  rm -rf "${output_dir}" || true
  mkdir -p "${output_dir}"

  # Check for timeout command
  local timeout_bin
  timeout_bin="$(command -v timeout || true)"
  local fflog="error"

  # Check for NVENC and scale_cuda availability
  local nvenc_ok=0
  ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_nvenc" && nvenc_ok=1
  local scale_cuda_ok=0
  ffmpeg -hide_banner -filters 2>/dev/null | grep -q "scale_cuda" && scale_cuda_ok=1

  log_info "NVENC available: ${nvenc_ok} | scale_cuda available: ${scale_cuda_ok}"

  # Statistics counters
  local norm_ok=0
  local norm_fail=0
  local norm_timeout=0
  local fallback_copy=0

  # Build scale filter based on MAX_DIM
  local scale_filter=""
  local scale_cuda_filter=""
  if [ "${max_dim}" -gt 0 ]; then
    local scale_w="w='if(gt(iw,ih),${max_dim},-2)'"
    local scale_h="h='if(gt(iw,ih),-2,${max_dim})'"
    scale_filter="scale=${scale_w}:${scale_h},"
    scale_cuda_filter="scale_cuda=${scale_w}:${scale_h},"
  fi

  # Process each video file (use fd 3 so ffmpeg redirects don't interfere with the loop)
  while IFS= read -r -d '' f <&3; do
    local bn
    bn="$(basename "$f")"
    local out="${output_dir}/${bn%.*}.mp4"

    echo "    [VID] ${bn}"

    if [ ! -f "$f" ]; then
      norm_fail=$((norm_fail+1))
      continue
    fi

    # Skip normalization if requested
    if [ "${skip_norm}" = "1" ]; then
      if copy_raw "$f" "${output_dir}" >/dev/null 2>&1; then
        fallback_copy=$((fallback_copy+1))
      else
        norm_fail=$((norm_fail+1))
      fi
      continue
    fi

    # Check if video needs HDR/10-bit tone mapping
    local format_filter
    if needs_tonemap "$f"; then
      # Use zscale with tonemap for 10-bit/HDR -> 8-bit SDR conversion
      local tonemap_filter="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
      format_filter="${tonemap_filter}"
    else
      # Standard 8-bit conversion
      format_filter="format=yuv420p"
    fi

    # Build ffmpeg command based on GPU availability and video type
    local cmd=()
    if [ "${use_gpu}" = "1" ] && [ "${nvenc_ok}" = "1" ] && [ "${scale_cuda_ok}" = "1" ]; then
      # Note: GPU path doesn't support zscale tonemap, so we fall back to CPU for HDR videos
      if needs_tonemap "$f"; then
        cmd=(ffmpeg -y -nostdin -hide_banner -loglevel "${fflog}"
             -fflags +genpts+discardcorrupt -err_detect ignore_err
             -probesize 10M -analyzeduration 10M
             -i "$f"
             -vf "${scale_filter}fps=${fps_out},${format_filter}"
             -c:v libx264 -preset slow -crf 18
             -c:a aac -ac 1 -ar 16000
             -max_muxing_queue_size 2048
             -movflags +faststart
             "$out")
      else
        cmd=(ffmpeg -y -nostdin -hide_banner -loglevel "${fflog}"
             -hwaccel cuda -hwaccel_output_format cuda
             -fflags +genpts+discardcorrupt -err_detect ignore_err
             -probesize 10M -analyzeduration 10M
             -i "$f"
             -vf "${scale_cuda_filter}fps=${fps_out}"
             -c:v h264_nvenc -preset p7 -rc vbr -cq 18 -b:v 0
             -c:a aac -ac 1 -ar 16000
             -max_muxing_queue_size 2048
             -movflags +faststart
             "$out")
      fi
    elif [ "${use_gpu}" = "1" ] && [ "${nvenc_ok}" = "1" ]; then
      # GPU encoding without scale_cuda
      cmd=(ffmpeg -y -nostdin -hide_banner -loglevel "${fflog}"
           -fflags +genpts+discardcorrupt -err_detect ignore_err
           -probesize 10M -analyzeduration 10M
           -i "$f"
           -vf "${scale_filter}fps=${fps_out},${format_filter}"
           -c:v h264_nvenc -preset p7 -rc vbr -cq 18 -b:v 0
           -c:a aac -ac 1 -ar 16000
           -max_muxing_queue_size 2048
           -movflags +faststart
           "$out")
    else
      # CPU encoding
      cmd=(ffmpeg -y -nostdin -hide_banner -loglevel "${fflog}"
           -fflags +genpts+discardcorrupt -err_detect ignore_err
           -probesize 10M -analyzeduration 10M
           -i "$f"
           -vf "${scale_filter}fps=${fps_out},${format_filter}"
           -c:v libx264 -preset slow -crf 18
           -c:a aac -ac 1 -ar 16000
           -max_muxing_queue_size 2048
           -movflags +faststart
           "$out")
    fi

    # Run ffmpeg with optional timeout
    local run_one_result=0
    if [ -n "${timeout_bin}" ]; then
      "${timeout_bin}" -k 5 "${timeout_sec}" "${cmd[@]}" >/dev/null 2>/dev/null || run_one_result=$?
    else
      "${cmd[@]}" >/dev/null 2>/dev/null || run_one_result=$?
    fi

    if [ "$run_one_result" -eq 0 ]; then
      # Validate output is decodable (catches silent NVENC corruption)
      if ! ffmpeg -v error -i "$out" -vframes 1 -f null - 2>/dev/null; then
        log_warn "Corrupt output detected for ${bn}, falling back to raw copy"
        rm -f "$out"
        if copy_raw "$f" "${output_dir}" >/dev/null 2>&1; then
          fallback_copy=$((fallback_copy+1))
        else
          norm_fail=$((norm_fail+1))
        fi
      else
        norm_ok=$((norm_ok+1))
      fi
    else
      rm -f -- "$out" || true
      if [ "$run_one_result" -eq 124 ] || [ "$run_one_result" -eq 137 ]; then
        norm_timeout=$((norm_timeout+1))
      else
        norm_fail=$((norm_fail+1))
      fi

      # Fallback: copy raw video if normalization failed
      if copy_raw "$f" "${output_dir}" >/dev/null 2>&1; then
        fallback_copy=$((fallback_copy+1))
      fi
    fi
  done 3< <(find "$raw_dir" -maxdepth 1 -type f \( -iname "*.mp4" -o -iname "*.MP4" \) -print0)

  log_info "Summary: ok=${norm_ok}, failed=${norm_fail}, timeout=${norm_timeout}, fallback_copy=${fallback_copy}"

  # Verify at least some videos were processed
  local num_processed
  num_processed="$(find "$output_dir" -maxdepth 1 -type f -name "*.mp4" | wc -l | tr -d ' ')"
  if [ "$num_processed" -eq 0 ]; then
    log_error "No videos available after normalize/copy"
    return 1
  fi

  log_info "Processed ${num_processed} video(s)"
  return 0
}

export -f run_normalization
export -f copy_raw
export -f needs_tonemap
