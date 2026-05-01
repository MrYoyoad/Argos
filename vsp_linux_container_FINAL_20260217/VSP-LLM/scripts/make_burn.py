#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Per-word confidence colors (BGR for libass; matches the HTML report palette).
# CSS green #4caf50 → BGR 50AF4C; amber #ffc107 → BGR 07C1FF; red #e06c75 → BGR 756CE0.
ASS_COLOR_HIGH = "&H50AF4C&"   # green  (conf >= 0.85)
ASS_COLOR_MED  = "&H07C1FF&"   # amber  (0.40 <= conf < 0.85)
ASS_COLOR_LOW  = "&H756CE0&"   # red    (conf < 0.40)
ASS_COLOR_NONE = "&HFFFFFF&"   # white  (no confidence data — fallback)

# Matches the thresholds in compute_word_confidence.py and the HTML report.
SYNTH_PROBS = {"match": 0.85, "sub": 0.50, "ins": 0.20}


def _normalize_words(text: str) -> List[str]:
    if not text:
        return []
    text = text.lower()
    text = re.sub(r"[^a-z0-9'\s]", " ", text)
    return [w for w in text.split() if w]


def _conf_class(prob: Optional[float]) -> str:
    if prob is None:
        return "conf-unknown"
    if prob >= 0.85:
        return "conf-high"
    if prob >= 0.40:
        return "conf-med"
    return "conf-low"


def _ass_color_for(conf_class: str) -> str:
    return {
        "conf-high": ASS_COLOR_HIGH,
        "conf-med":  ASS_COLOR_MED,
        "conf-low":  ASS_COLOR_LOW,
    }.get(conf_class, ASS_COLOR_NONE)


def synthetic_words_from_alignment(ref: str, hyp: str) -> List[Dict[str, Any]]:
    """Build per-word confidence list from the WER alignment between REF and HYP.

    Used as a fallback when no real confidence sidecar is available — the same
    fallback path the standalone HTML demo report uses.
    """
    ref_words = _normalize_words(ref)
    hyp_words = _normalize_words(hyp)
    matcher = difflib.SequenceMatcher(a=ref_words, b=hyp_words, autojunk=False)
    out: List[Dict[str, Any]] = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            for j in range(j1, j2):
                out.append({"word": hyp_words[j], "prob": SYNTH_PROBS["match"],
                            "conf_class": "conf-high"})
        elif op == "replace":
            for j in range(j1, j2):
                out.append({"word": hyp_words[j], "prob": SYNTH_PROBS["sub"],
                            "conf_class": "conf-med"})
        elif op == "insert":
            for j in range(j1, j2):
                out.append({"word": hyp_words[j], "prob": SYNTH_PROBS["ins"],
                            "conf_class": "conf-low"})
        # 'delete' — words present in REF but missing from HYP — not rendered.
    return out


def load_word_confidence(path: Optional[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Load a word_confidence.json (output of compute_word_confidence.py).

    Returns {utt_id: [{"word", "prob", "conf_class", ...}, ...]} or {} on failure.
    """
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        print(f"[INFO] word_confidence not found at {path} — colors will use synthetic fallback")
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] Cannot read {path}: {e}")
        return {}
    out: Dict[str, List[Dict[str, Any]]] = {}
    for uid, rec in data.items():
        words = rec.get("words", []) if isinstance(rec, dict) else []
        if isinstance(words, list) and words:
            out[uid] = words
    return out


def _ass_escape(text: str) -> str:
    """Escape characters that have special meaning inside an ASS Dialogue line."""
    return (text
            .replace("\\", r"\\")
            .replace("{", r"\{")
            .replace("}", r"\}"))


def build_ass_file(words: List[Dict[str, Any]],
                   plain_text: str,
                   video_w: int, video_h: int,
                   fontsize: int, margin_v: int) -> Optional[str]:
    """Write a temporary ASS subtitle file with per-word color overrides.

    Returns the file path, or None if `words` is empty (caller should fall
    back to the plain drawtext path).
    """
    if not words:
        return None

    parts = []
    for i, w in enumerate(words):
        color = _ass_color_for(w.get("conf_class") or _conf_class(w.get("prob")))
        word = _ass_escape(str(w.get("word", "")))
        sep = " " if i < len(words) - 1 else ""
        parts.append(f"{{\\1c{color}}}{word}{sep}")
    dialogue_text = "".join(parts)

    # ASS Dialogue spans the whole clip — burned video is one segment.
    # Style: Arial, given fontsize, alignment=2 (bottom-center), MarginV in pixels.
    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_w}
PlayResY: {video_h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{fontsize},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,9:59:59.00,Default,,0,0,0,,{dialogue_text}
"""

    tf = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".ass", delete=False)
    try:
        tf.write(ass)
        tf.flush()
        return tf.name
    finally:
        tf.close()


def wrap_text(s: str, width: int, max_lines: int) -> str:
    s = (s or "").strip()
    if not s:
        return "NO AUDIO / NO TRANSCRIPT"
    s = " ".join(s.split())
    lines = textwrap.wrap(s, width=max(8, width))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if width >= 3 and lines[-1]:
            lines[-1] = lines[-1][: max(0, width - 3)] + "..."
        else:
            lines[-1] = "..."
    return "\n".join(lines)


def run_ffmpeg(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode == 0:
        return 0, ""
    err = (p.stderr or "").splitlines()
    return p.returncode, "\n".join(err[-80:])


def ffprobe_wh(path: Path) -> Tuple[int, int]:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        str(path),
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        return 0, 0
    try:
        d = json.loads(p.stdout)
        st = (d.get("streams") or [{}])[0]
        return int(st.get("width") or 0), int(st.get("height") or 0)
    except Exception:
        return 0, 0


def _loads_json_or_py(text: str) -> Any:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return ast.literal_eval(text)


def extract_base_video_id(segment_id: str) -> str:
    """
    Extract base video ID from segment ID.

    Segment format: {video_id}_{seg_idx:02d}_{start_frame:06d}_{end_frame:06d}
    Examples:
        Obama_00_000000_000300 -> Obama
        VideoA__abc12345_02_000500_000800 -> VideoA__abc12345

    Strategy: Remove the last 3 underscore-separated components if they match the pattern.
    """
    parts = segment_id.split('_')

    # Need at least 4 parts to have a segment ID (base + 3 numeric parts)
    if len(parts) < 4:
        return segment_id

    # Check if last 3 parts look like segment indices/frames (all digits)
    try:
        int(parts[-1])  # end_frame
        int(parts[-2])  # start_frame
        int(parts[-3])  # seg_idx
        # If all 3 are numeric, remove them to get base video ID
        return '_'.join(parts[:-3])
    except (ValueError, IndexError):
        # Not a segment ID pattern, return as-is
        return segment_id


def load_predictions(path: Path) -> Dict[str, str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if not raw.strip():
        return {}

    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    # JSONL
    if len(lines) >= 2 and all(ln.startswith("{") for ln in lines[:2]):
        out: Dict[str, str] = {}
        for ln in lines:
            d = _loads_json_or_py(ln)
            if not isinstance(d, dict):
                continue
            uid = d.get("utt_id") or d.get("id")
            hyp = d.get("hypo") or d.get("hyp") or d.get("text") or ""
            if uid:
                out[str(uid)] = str(hyp).strip()
        return out

    obj = _loads_json_or_py(raw)

    # list[dict]
    if isinstance(obj, list):
        out: Dict[str, str] = {}
        for rec in obj:
            if not isinstance(rec, dict):
                continue
            uid = rec.get("utt_id") or rec.get("id")
            hyp = rec.get("hypo") or rec.get("hyp") or rec.get("text") or ""
            if uid:
                out[str(uid)] = str(hyp).strip()
        return out

    # dict
    if isinstance(obj, dict):
        # columnar dict
        utts = obj.get("utt_id") or obj.get("id")
        hyps = obj.get("hypo") or obj.get("hyp") or obj.get("text")
        if isinstance(utts, list) and isinstance(hyps, list):
            out: Dict[str, str] = {}
            n = min(len(utts), len(hyps))
            for i in range(n):
                uid = utts[i]
                hyp = hyps[i]
                if uid is None:
                    continue
                out[str(uid)] = ("" if hyp is None else str(hyp)).strip()
            return out

        # avoid treating {"utt_id":..., "hypo":...} as IDs
        if any(k in obj for k in ("utt_id", "ref", "hypo", "instruction")):
            return {}

        # mapping dict {uid: hyp}
        out: Dict[str, str] = {}
        for k, v in obj.items():
            uid = str(k)
            if isinstance(v, str):
                hyp = v
            elif isinstance(v, dict):
                hyp = v.get("merged_hypo") or v.get("hypo") or v.get("hyp") or v.get("text") or ""
            else:
                hyp = str(v)
            out[uid] = str(hyp).strip()
        return out

    return {}


def load_references(path: Path) -> Dict[str, str]:
    """Load REF strings keyed by utt_id from the same JSON used for hypotheses.

    Mirrors `load_predictions` but pulls the 'ref' field. Used for the
    synthetic-confidence fallback (REF↔HYP alignment) when no real per-token
    sidecar is available. Returns {} if no refs are present.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    if not raw.strip():
        return {}

    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    if len(lines) >= 2 and all(ln.startswith("{") for ln in lines[:2]):
        out: Dict[str, str] = {}
        for ln in lines:
            d = _loads_json_or_py(ln)
            if not isinstance(d, dict):
                continue
            uid = d.get("utt_id") or d.get("id")
            ref = d.get("ref") or d.get("reference") or ""
            if uid:
                out[str(uid)] = str(ref).strip()
        return out

    obj = _loads_json_or_py(raw)

    if isinstance(obj, list):
        out: Dict[str, str] = {}
        for rec in obj:
            if not isinstance(rec, dict):
                continue
            uid = rec.get("utt_id") or rec.get("id")
            ref = rec.get("ref") or rec.get("reference") or ""
            if uid:
                out[str(uid)] = str(ref).strip()
        return out

    if isinstance(obj, dict):
        utts = obj.get("utt_id") or obj.get("id")
        refs = obj.get("ref") or obj.get("reference")
        if isinstance(utts, list) and isinstance(refs, list):
            out: Dict[str, str] = {}
            n = min(len(utts), len(refs))
            for i in range(n):
                if utts[i] is None:
                    continue
                out[str(utts[i])] = ("" if refs[i] is None else str(refs[i])).strip()
            return out
    return {}


def load_segment_metadata(metadata_path: Path) -> Dict[str, Any]:
    """Load segment metadata JSON file."""
    if not metadata_path.exists():
        return {}
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load segment metadata: {e}")
        return {}


def parse_segment_id(segment_id: str) -> Tuple[str, int, int, int]:
    """
    Parse segment ID to extract components.
    Format: {video_id}_{seg_idx:02d}_{start_frame:06d}_{end_frame:06d}

    Returns: (base_video_id, seg_idx, start_frame, end_frame)
    """
    parts = segment_id.split('_')

    if len(parts) < 4:
        return segment_id, -1, -1, -1

    try:
        end_frame = int(parts[-1])
        start_frame = int(parts[-2])
        seg_idx = int(parts[-3])
        base_video_id = '_'.join(parts[:-3])
        return base_video_id, seg_idx, start_frame, end_frame
    except (ValueError, IndexError):
        return segment_id, -1, -1, -1


def extract_segment_from_original(
    original_video: Path,
    start_sec: float,
    duration: float,
    output_path: Path,
    timeout: int = 30
) -> bool:
    """
    Extract a segment from the original video using ffmpeg.

    Args:
        original_video: Path to original full-frame video
        start_sec: Start time in seconds
        duration: Duration in seconds
        output_path: Where to save extracted segment
        timeout: Command timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    # Try codec copy first (fast, no re-encoding)
    cmd_copy = [
        "ffmpeg", "-y", "-nostdin",
        "-ss", str(start_sec),
        "-i", str(original_video),
        "-t", str(duration),
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        str(output_path)
    ]

    try:
        result = subprocess.run(
            cmd_copy,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True
        )

        if result.returncode == 0 and output_path.exists():
            return True
    except subprocess.TimeoutExpired:
        print(f"[WARN] ffmpeg codec copy timed out after {timeout}s")
    except Exception as e:
        print(f"[WARN] ffmpeg codec copy failed: {e}")

    # Fallback: re-encode (slower but more reliable)
    cmd_encode = [
        "ffmpeg", "-y", "-nostdin",
        "-ss", str(start_sec),
        "-i", str(original_video),
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        str(output_path)
    ]

    try:
        result = subprocess.run(
            cmd_encode,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True
        )

        return result.returncode == 0 and output_path.exists()
    except Exception as e:
        print(f"[ERROR] ffmpeg re-encode failed: {e}")
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True, help="decode outputs (.jsonl OR hypo-*.json)")
    ap.add_argument("--video_dir", required=True, help="folder of original mp4")
    ap.add_argument("--segment_dir", default=None, help="folder of segmented videos (fallback if original not found)")
    ap.add_argument("--segment_metadata", default=None, help="path to segment_metadata.json")
    ap.add_argument("--out_dir", required=True)

    ap.add_argument("--fontsize", type=int, default=24)
    ap.add_argument("--box_h", type=int, default=140)
    ap.add_argument("--wrap_width", type=int, default=48)
    ap.add_argument("--max_lines", type=int, default=3)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="veryfast")

    ap.add_argument("--margin", type=int, default=18)
    ap.add_argument("--pad_y", type=int, default=16)
    ap.add_argument("--line_spacing", type=int, default=6)

    ap.add_argument("--word_confidence", default=None,
                    help="optional path to word_confidence.json (output of "
                         "compute_word_confidence.py). When provided, hypotheses "
                         "are rendered with per-word green/yellow/red coloring "
                         "via libass. When absent or missing a segment, a synthetic "
                         "fallback colors words by REF vs HYP alignment.")

    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    vdir = Path(args.video_dir)
    segment_dir = Path(args.segment_dir) if args.segment_dir else None

    # Load segment metadata if provided
    segment_metadata = {}
    if args.segment_metadata:
        segment_metadata = load_segment_metadata(Path(args.segment_metadata))

    hyps = load_predictions(Path(args.jsonl))
    if not hyps:
        print(f"[WARN] No records loaded from {args.jsonl}")
        return

    # Per-word confidence sources for color coding (optional).
    # Priority per segment: real sidecar > synthetic from REF↔HYP alignment > none.
    word_conf = load_word_confidence(args.word_confidence)
    refs = load_references(Path(args.jsonl))
    if word_conf:
        print(f"[INFO] Loaded word_confidence for {len(word_conf)} segments — burned videos will be colored")
    elif refs:
        print(f"[INFO] No real word_confidence — falling back to synthetic colors from REF↔HYP alignment ({len(refs)} refs)")

    # Build display names for Part naming in output filenames
    # Group by base video ID to determine single vs multi-segment
    _groups: Dict[str, List[Tuple[int, str]]] = {}
    for uid in hyps:
        base, seg_idx, _, _ = parse_segment_id(uid)
        if base not in _groups:
            _groups[base] = []
        _groups[base].append((seg_idx, uid))

    _file_names: Dict[str, str] = {}
    for base, entries in _groups.items():
        if len(entries) == 1:
            _, uid = entries[0]
            _file_names[uid] = f"{base}_with_hyp.mp4"
        else:
            entries.sort(key=lambda x: x[0])
            for part_num, (_, uid) in enumerate(entries, 1):
                _file_names[uid] = f"{base}_Part{part_num}_with_hyp.mp4"

    for uid, hyp in hyps.items():
        src = None
        temp_extracted = None

        # Parse segment ID to get base video ID and segment info
        base_video_id, seg_idx, start_frame, end_frame = parse_segment_id(uid)

        # Strategy 1: Extract segment from original full-frame video (PREFERRED)
        if segment_metadata and base_video_id in segment_metadata:
            # Find the original video
            orig = vdir / f"{base_video_id}.mp4"
            if not orig.exists():
                # Try glob pattern
                hits = sorted(vdir.glob(f"{base_video_id}*.mp4"))
                orig = hits[0] if hits else None

            if orig and orig.exists():
                # Get segment timing from metadata
                video_meta = segment_metadata[base_video_id]
                segments = video_meta.get("segments", [])

                # Find matching segment by index
                segment_info = None
                if seg_idx == -1:
                    # Non-segmented video (whole video, no frame numbers in ID)
                    # Use the first (and only) segment
                    if segments:
                        segment_info = segments[0]
                        print(f"[INFO] {uid}: Using whole video (non-segmented)")
                else:
                    # Segmented video - find by index
                    for seg in segments:
                        if seg.get("index") == seg_idx:
                            segment_info = seg
                            break

                if segment_info:
                    start_sec = segment_info.get("start_sec", 0.0)
                    duration = segment_info.get("duration", 12.0)

                    # Create temp file for extracted segment
                    temp_extracted = out_dir / f"_temp_{uid}_extracted.mp4"

                    print(f"[EXTRACT] {uid}: Extracting {start_sec:.1f}s-{start_sec + duration:.1f}s from {orig.name}")

                    if extract_segment_from_original(orig, start_sec, duration, temp_extracted):
                        src = temp_extracted
                        print(f"[OK] Extracted segment for {uid}")
                    else:
                        print(f"[WARN] Failed to extract segment for {uid}")
                        # Clean up failed temp file
                        if temp_extracted and temp_extracted.exists():
                            temp_extracted.unlink(missing_ok=True)
                        temp_extracted = None
                else:
                    print(f"[WARN] No segment metadata found for {uid} (index {seg_idx})")
            else:
                print(f"[WARN] Original video not found for {base_video_id}")

        # Strategy 1.5: Check if pre-segmented full-frame video exists in video_dir
        # (With new pipeline: segment → normalize → mouth crop, video_dir contains full-frame segments)
        if src is None:
            segment_file = vdir / f"{uid}.mp4"
            if segment_file.exists():
                src = segment_file
                print(f"[OK] Using pre-segmented full-frame video for {uid}: {segment_file.name}")
            else:
                # Try glob pattern for segment
                hits = sorted(vdir.glob(f"{uid}*.mp4"))
                if hits:
                    src = hits[0]
                    print(f"[OK] Using pre-segmented full-frame video for {uid}: {src.name}")

        # Strategy 2: Fall back to preprocessed segment video (mouth-cropped)
        if src is None and segment_dir:
            seg = segment_dir / f"{uid}.mp4"
            if seg.exists():
                src = seg
                print(f"[FALLBACK] Using preprocessed segment for {uid}: {seg.name}")
            else:
                hits = sorted(segment_dir.glob(f"{uid}*.mp4"))
                src = hits[0] if hits else None
                if src:
                    print(f"[FALLBACK] Using preprocessed segment for {uid}: {src.name}")

        # Strategy 3: Last resort - use full original video (non-segment ID)
        if src is None:
            orig = vdir / f"{base_video_id}.mp4"
            if orig.exists():
                src = orig
                print(f"[FALLBACK] Using full original video for {uid}: {orig.name}")
            else:
                hits = sorted(vdir.glob(f"{base_video_id}*.mp4"))
                if hits:
                    src = hits[0]
                    print(f"[FALLBACK] Using full original video for {uid}: {src.name}")

        if src is None or not src.exists():
            print(f"[SKIP] no video for {uid}")
            continue

        w, h = ffprobe_wh(src)
        if w <= 0 or h <= 0:
            w, h = 1280, 720

        # scale font: allow larger on big videos, smaller on tiny
        max_fs = args.fontsize if h < 1200 else int(args.fontsize * 1.6)
        fs = max(12, min(max_fs, int(h / 18)))

        # margins scale down on small videos
        margin = min(args.margin, max(6, w // 20))
        pad_y = min(args.pad_y, max(6, h // 20))

        usable_w = max(40, w - 2 * margin)
        char_px = max(6.0, 0.55 * fs)
        wrap = max(10, min(args.wrap_width * 3, int(usable_w / char_px)))

        txt = wrap_text(hyp, width=wrap, max_lines=args.max_lines)

        line_h = fs + args.line_spacing
        needed = pad_y * 2 + (args.max_lines * line_h)
        box_h = max(int(needed), min(args.box_h, int(h * 0.45)))
        box_h = min(box_h, h - 2)

        dst = out_dir / _file_names.get(uid, f"{uid}_with_hyp.mp4")

        # Resolve per-word coloring source for this segment.
        # Priority: real word_confidence sidecar > synthetic from REF↔HYP > none.
        seg_words: List[Dict[str, Any]] = word_conf.get(uid, [])
        if not seg_words and uid in refs:
            seg_words = synthetic_words_from_alignment(refs[uid], hyp)

        tf = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False)
        try:
            tf.write(txt)
            tf.flush()
            textfile = tf.name
        finally:
            tf.close()

        # IMPORTANT: ffmpeg-4.4 friendly expressions: no parentheses
        # use h/iw/ih variables safely
        y_box = f"h-{box_h}"
        y_text = f"h-{box_h}+{pad_y}"

        # Build filter graph. Two paths:
        #   (a) per-word colored ASS subtitle via libass (when seg_words is non-empty)
        #   (b) original drawtext path (white text) — used as backward-compatible fallback
        ass_file: Optional[str] = None
        if seg_words:
            # libass measures fontsize differently than ffmpeg drawtext — scale up
            # ~30% so the colored text reads at roughly the same visual size as
            # the white drawtext fallback.
            ass_fs = max(14, int(round(fs * 1.30)))
            margin_v = max(8, box_h - pad_y - ass_fs)
            ass_file = build_ass_file(seg_words, txt, w, h,
                                      fontsize=ass_fs, margin_v=margin_v)

        textfile_for_filter = textfile.replace("'", r"\'")

        if ass_file:
            # libass needs the path single-quoted and any colon escaped.
            ass_for_filter = ass_file.replace(":", r"\:").replace("'", r"\'")
            vf = (
                f"drawbox=x=0:y={y_box}:w=iw:h={box_h}:color=black@0.65:t=fill,"
                f"subtitles='{ass_for_filter}'"
            )
        else:
            vf = (
                f"drawbox=x=0:y={y_box}:w=iw:h={box_h}:color=black@0.65:t=fill,"
                f"drawtext=textfile='{textfile_for_filter}':"
                f"expansion=none:"
                f"fontcolor=white:fontsize={fs}:"
                f"x={margin}:y={y_text}:"
                f"line_spacing={args.line_spacing}"
            )

        cmd = [
            "ffmpeg", "-y", "-nostdin",
            "-i", str(src),
            "-map", "0:v:0",
            "-map", "0:a?",
            "-vf", vf,
            "-c:v", "libx264", "-preset", str(args.preset), "-crf", str(args.crf),
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(dst),
        ]

        rc, tail = run_ffmpeg(cmd)
        if rc == 0 and dst.exists():
            print("[OK]", dst)
        else:
            print(f"[FAIL] {uid} rc={rc}")
            if tail:
                print(tail)

        try:
            Path(textfile).unlink(missing_ok=True)
        except Exception:
            pass
        if ass_file:
            try:
                Path(ass_file).unlink(missing_ok=True)
            except Exception:
                pass

        # Clean up temporary extracted segment if we created one
        if temp_extracted and temp_extracted.exists():
            try:
                temp_extracted.unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    main()