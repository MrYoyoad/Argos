#!/usr/bin/env python3
"""Burn VSP-LLM MBR-aggregated subtitles onto a per-speaker face MP4 for demo decks.

Given a per-speaker face crop (the output of `split_realtalk_per_speaker.py`) and a
12-second window (start_sec, end_sec) within that crop, this slices the window with
ffmpeg and overlays the MBR-aggregated hypothesis word-by-word, colored by the
production agreement-aware trust bands (May 2 2026 rule):

    GREEN  iff top1_conf >= 0.95 AND beam_agreement >= 0.80
    YELLOW iff top1_conf >= 0.65 AND beam_agreement >= 0.50  (and not green)
    RED    otherwise
    Numeric tokens (containing a digit) are CAPPED at YELLOW — never green.

Inputs read:
    report.csv         — utt_id, hyp_mbr, sentence_confidence, is_score, is_label, ...
    aggregated.json    — { utt_id: { hyp_mbr: { text, word_confs: [[w, conf], ...] }, ... } }
    agreement-*.json   — optional sibling: { utt_id: [agreement_per_word, ...] }

When agreement data is missing, beam_agreement is treated as 0.0 — i.e. words can
never be promoted to green falsely. When aggregated.json itself is missing, falls
back to the report.csv hyp_mbr text with even-time distribution and red coloring
(no per-word conf signal available).

Output: a 12-second MP4 with libass-rendered colored subtitles on the bottom and a
top-right IS badge drawn via ffmpeg drawtext. Standalone — no Python dependencies
beyond the standard library; requires ffmpeg + ffprobe on PATH.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Production color band rule (May 2 2026, agreement_aware_bands.md). Hex colors are
# the canonical brand palette used in client-deck slides and the report HTML.
COLOR_GREEN_RGB = "00B050"
COLOR_YELLOW_RGB = "FFC000"
COLOR_RED_RGB = "C00000"
COLOR_WHITE_RGB = "EEEEEE"
COLOR_GRAY_RGB = "888888"

# IS tier thresholds (NIV calibration vs Opus, March 2026 — supersede legacy IS>=3.0)
NIV_Y_THRESHOLD = 3.80   # "Clearly conveyed"
NIV_P_THRESHOLD = 2.00   # "Any useful"

# Joint band rule thresholds
GREEN_CONF = 0.95
GREEN_AGR = 0.80
YELLOW_CONF = 0.65
YELLOW_AGR = 0.50

DIGIT_RE = re.compile(r"\d")


def rgb_to_ass_bgr(rgb_hex: str) -> str:
    """ASS color tags use &H00BBGGRR& — i.e. BGR with a leading 00 alpha byte.

    Input is a 6-char RGB hex (e.g. '00B050'); we re-pack as BGR.
    """
    rgb_hex = rgb_hex.lstrip("#")
    r, g, b = rgb_hex[0:2], rgb_hex[2:4], rgb_hex[4:6]
    return f"&H00{b}{g}{r}&".upper()


def band_for_word(word: str, top1_conf: float, beam_agreement: float) -> str:
    """Return 'green' | 'yellow' | 'red' applying the joint rule + numeric cap.

    Numbers cap at yellow because off-by-1000x errors ("billion"->"million") were
    found in green-flagged numerics during May 2026 leakage analysis.
    """
    is_numeric = bool(DIGIT_RE.search(word))
    if (not is_numeric) and top1_conf >= GREEN_CONF and beam_agreement >= GREEN_AGR:
        return "green"
    if top1_conf >= YELLOW_CONF and beam_agreement >= YELLOW_AGR:
        return "yellow"
    return "red"


def color_for_band(band: str) -> str:
    return {
        "green": COLOR_GREEN_RGB,
        "yellow": COLOR_YELLOW_RGB,
        "red": COLOR_RED_RGB,
    }[band]


def niv_tier_from_is(is_score: float | None) -> tuple[str, str]:
    """Return (letter, color_rgb) for IS-tier badge."""
    if is_score is None:
        return ("—", COLOR_GRAY_RGB)
    if is_score >= NIV_Y_THRESHOLD:
        return ("Y", COLOR_GREEN_RGB)
    if is_score >= NIV_P_THRESHOLD:
        return ("P", "1F77B4")  # blue
    return ("N", COLOR_GRAY_RGB)


def load_report_row(report_csv: Path, segment_id: str) -> dict | None:
    with report_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            if row.get("utt_id") == segment_id or row.get("segment_id") == segment_id:
                return row
    return None


def safe_float(s: str | None) -> float | None:
    if s is None or s == "":
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def load_aggregated_entry(aggregated_json: Path | None, segment_id: str) -> dict | None:
    if not aggregated_json or not aggregated_json.exists():
        return None
    with aggregated_json.open() as f:
        d = json.load(f)
    return d.get(segment_id)


def load_agreement_entry(agreement_json: Path | None, segment_id: str) -> list | None:
    if not agreement_json or not agreement_json.exists():
        return None
    with agreement_json.open() as f:
        d = json.load(f)
    val = d.get(segment_id)
    if not val:
        return None
    # Files in the wild: either a flat list of floats aligned with hyp_mbr words,
    # or a dict with a 'words' key — accept both shapes defensively.
    if isinstance(val, list):
        return val
    if isinstance(val, dict):
        if "agreement" in val and isinstance(val["agreement"], list):
            return val["agreement"]
        if "words" in val and isinstance(val["words"], list):
            return [w.get("agreement", 0.0) for w in val["words"]]
    return None


def derive_words(
    agg_entry: dict | None,
    agreement_list: list | None,
    fallback_text: str,
    window_sec: float,
) -> list[dict]:
    """Build per-word records: {word, conf, agreement, t_start, t_end} in seconds
    relative to the trimmed 12-second window.
    """
    words_confs: list[tuple[str, float]] = []
    if agg_entry and isinstance(agg_entry.get("hyp_mbr"), dict):
        wc = agg_entry["hyp_mbr"].get("word_confs") or []
        words_confs = [(w, float(c)) for w, c in wc]
    elif fallback_text.strip():
        words_confs = [(w, 0.0) for w in fallback_text.split()]

    if not words_confs:
        return []

    n = len(words_confs)
    # No per-word timing is emitted by the pipeline today; distribute evenly across
    # the trimmed window with a small head/tail margin so subs don't slam against
    # the cut edges.
    margin = min(0.25, window_sec * 0.04)
    span = max(window_sec - 2 * margin, 0.1)
    dt = span / n

    out = []
    for i, (w, c) in enumerate(words_confs):
        agr = 0.0
        if agreement_list and i < len(agreement_list):
            try:
                agr = float(agreement_list[i])
            except (TypeError, ValueError):
                agr = 0.0
        out.append({
            "word": w,
            "conf": c,
            "agreement": agr,
            "t_start": margin + i * dt,
            "t_end": margin + (i + 1) * dt,
        })
    return out


def fmt_ass_time(t: float) -> str:
    """ASS time format: H:MM:SS.cs (centiseconds)."""
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_ass(
    words: list[dict],
    play_w: int,
    play_h: int,
    reference_text: str | None,
    show_reference: bool,
    duration: float,
) -> str:
    """Generate an ASS file body. One Dialogue per word for the hypothesis (so each
    word fades in at its own time), a single Dialogue spanning the whole clip for
    the reference. Inline {\\c&H...&} sets per-word color; we keep style colors
    neutral and let inline overrides carry the band signal.
    """
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_w}
PlayResY: {play_h}
ScaledBorderAndShadow: yes
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hyp,Arial,32,&H00FFFFFF&,&H000000FF&,&H00000000&,&H80000000&,1,0,0,0,100,100,0,0,1,2,1,2,20,20,20,1
Style: Ref,Arial,22,&H00EEEEEE&,&H000000FF&,&H00000000&,&H80000000&,0,1,0,0,100,100,0,0,1,2,1,2,20,20,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events: list[str] = []

    # Build a single hypothesis line per word using cumulative reveal: at each
    # word's t_start, the line so far is rendered with that word newly added in
    # its band color. Earlier words keep their bands. A simpler approach — one
    # event per word displayed in isolation — looks jumpy; cumulative reveal
    # reads naturally during a 12-second clip.
    cumulative_segments: list[str] = []
    for i, w in enumerate(words):
        band = band_for_word(w["word"], w["conf"], w["agreement"])
        ass_color = rgb_to_ass_bgr(color_for_band(band))
        cumulative_segments.append(f"{{{chr(92)}c{ass_color}}}{w['word']}")

        text = " ".join(cumulative_segments)
        # Each word's reveal event runs from its t_start to either the next
        # word's t_start or the end of the clip.
        next_t = words[i + 1]["t_start"] if i + 1 < len(words) else duration
        events.append(
            f"Dialogue: 0,{fmt_ass_time(w['t_start'])},{fmt_ass_time(next_t)},Hyp,,0,0,0,,{text}"
        )

    if not words:
        red = rgb_to_ass_bgr(COLOR_RED_RGB)
        events.append(
            f"Dialogue: 0,{fmt_ass_time(0)},{fmt_ass_time(duration)},Hyp,,0,0,0,,"
            f"{{{chr(92)}c{red}}}[no output]"
        )

    if show_reference and reference_text:
        # ASS comma is a field separator; escape any literal commas with \, and
        # backslashes by doubling — but reference text from Whisper rarely has
        # those; keep it simple.
        ref_clean = reference_text.replace("\n", " ").strip()
        events.append(
            f"Dialogue: 0,{fmt_ass_time(0)},{fmt_ass_time(duration)},Ref,,0,0,0,,{ref_clean}"
        )

    return header + "\n".join(events) + "\n"


def probe_resolution(face_mp4: Path) -> tuple[int, int]:
    """Use ffprobe to get width/height. Falls back to 360x340 (the documented
    crop dimension from split_realtalk_per_speaker.py) if probe fails.
    """
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x",
            str(face_mp4),
        ], text=True).strip()
        w, h = out.split("x")
        return int(w), int(h)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return 360, 340


def build_drawtext_badge(is_score: float | None, play_w: int) -> str:
    """drawtext arg string for the IS badge in the top-right. Quoted so the outer
    -vf string can wrap it; commas inside drawtext params are *not* separators
    when the option string is the whole argument to one filter, but to be safe
    we use ':' separators within drawtext (as is standard).
    """
    letter, color_rgb = niv_tier_from_is(is_score)
    if is_score is None:
        text = "IS —"
    else:
        text = f"IS {is_score:.2f} · {letter}"

    # ffmpeg drawtext text quoting: single-quote and escape inner single quotes
    # as '\''. We keep the text simple here so no further escaping needed.
    box_color_rgba = f"0x{color_rgb}@0.75"
    args = (
        f"text='{text}'"
        f":fontcolor=white"
        f":fontsize=18"
        f":box=1"
        f":boxcolor={box_color_rgba}"
        f":boxborderw=8"
        f":x=w-tw-16"
        f":y=16"
    )
    return args


def build_ffmpeg_cmd(
    face_mp4: Path,
    start_sec: float,
    end_sec: float,
    ass_path: Path,
    badge_args: str,
    out_path: Path,
) -> list[str]:
    duration = max(end_sec - start_sec, 0.1)
    # -ss before -i = fast input seek; ASS timestamps then start from 0 of the
    # trimmed segment, which matches how derive_words computes t_start/t_end.
    # libass filter path needs commas/colons escaped — wrap with single quotes
    # and use the filtergraph escape conventions: backslashes for special chars
    # in filenames.
    ass_arg = str(ass_path).replace("\\", "\\\\").replace(":", "\\:").replace(",", "\\,")
    vf = f"ass='{ass_arg}',drawtext={badge_args}"
    return [
        "ffmpeg", "-y",
        "-ss", f"{start_sec:.3f}",
        "-i", str(face_mp4),
        "-t", f"{duration:.3f}",
        "-vf", vf,
        "-c:v", "libx264", "-crf", "20", "-preset", "medium",
        "-c:a", "aac", "-shortest",
        "-movflags", "+faststart",
        str(out_path),
    ]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--face-mp4", type=Path, required=True, help="Per-speaker face MP4 input")
    p.add_argument("--segment-id", type=str, required=True, help="utt_id / segment_id")
    p.add_argument("--start-sec", type=float, required=True)
    p.add_argument("--end-sec", type=float, required=True)
    p.add_argument("--report-csv", type=Path, required=True)
    p.add_argument("--aggregated-json", type=Path, default=None)
    p.add_argument("--agreement-json", type=Path, default=None,
                   help="Optional sibling agreement-*.json (per-word beam agreement). "
                        "Without this, words can never reach green.")
    p.add_argument("--reference-text", type=str, default=None)
    p.add_argument("--show-reference", action="store_true", default=False)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--dry-run", action="store_true", default=False,
                   help="Print ASS contents and ffmpeg command, do not execute.")
    args = p.parse_args()

    if not args.dry_run:
        for tool in ("ffmpeg", "ffprobe"):
            if not shutil.which(tool):
                print(f"ERROR: {tool} not on PATH", file=sys.stderr)
                return 2

    # Look up segment metadata — but in dry-run we tolerate missing CSV so the
    # caller can probe with synthetic fixtures.
    row = None
    if args.report_csv.exists():
        row = load_report_row(args.report_csv, args.segment_id)
    elif not args.dry_run:
        print(f"ERROR: report-csv not found: {args.report_csv}", file=sys.stderr)
        return 2

    is_score = safe_float(row.get("is_score")) if row else None
    hyp_mbr_text = (row.get("hyp_mbr") or row.get("hyp") or "") if row else ""

    agg_entry = load_aggregated_entry(args.aggregated_json, args.segment_id)
    agreement_list = load_agreement_entry(args.agreement_json, args.segment_id)

    duration = max(args.end_sec - args.start_sec, 0.1)
    words = derive_words(agg_entry, agreement_list, hyp_mbr_text, duration)

    if args.face_mp4.exists():
        play_w, play_h = probe_resolution(args.face_mp4)
    else:
        play_w, play_h = 360, 340

    ass_text = build_ass(
        words=words,
        play_w=play_w,
        play_h=play_h,
        reference_text=args.reference_text,
        show_reference=args.show_reference,
        duration=duration,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    ass_path = args.out.with_suffix(".ass")

    badge_args = build_drawtext_badge(is_score, play_w)
    cmd = build_ffmpeg_cmd(
        face_mp4=args.face_mp4,
        start_sec=args.start_sec,
        end_sec=args.end_sec,
        ass_path=ass_path,
        badge_args=badge_args,
        out_path=args.out,
    )

    if args.dry_run:
        print("===== ASS =====")
        print(ass_text)
        print("===== FFMPEG =====")
        print(" ".join(repr(c) if " " in c else c for c in cmd))
        return 0

    ass_path.write_text(ass_text)
    print(f"[burn] wrote {ass_path}")
    print(f"[burn] running: {' '.join(cmd)}")
    rc = subprocess.call(cmd)
    if rc != 0:
        print(f"ERROR: ffmpeg exited {rc}", file=sys.stderr)
        return rc
    print(f"[burn] wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
